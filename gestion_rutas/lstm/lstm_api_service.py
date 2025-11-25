"""
Servicio LSTM para entrenar modelos interactivamente desde CSV
Maneja preprocesamiento, entrenamiento, predicciones y generación de reportes
"""

import pandas as pd
import numpy as np
import json
import pickle
import io
from datetime import datetime
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

from sklearn.preprocessing import MinMaxScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout, BatchNormalization
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau, ModelCheckpoint
from tensorflow.keras.optimizers import Adam

import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Backend no interactivo para servidor


class LSTMTrainer:
    """Clase que maneja todo el pipeline LSTM: preprocesamiento, entrenamiento, predicción"""
    
    def __init__(self, csv_content, temp_dir='./lstm_temp'):
        """
        Args:
            csv_content: contenido del CSV (string o bytes)
            temp_dir: directorio temporal para guardar archivos intermedios
        """
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(exist_ok=True)
        
        # Cargar CSV
        if isinstance(csv_content, bytes):
            csv_content = csv_content.decode('utf-8')
        
        self.df = pd.read_csv(io.StringIO(csv_content))
        self.sequence_length = 14
        
        # Scalers y encoders (se guardarán después de preprocesar)
        self.scaler_input = None
        self.scaler_target = None
        self.encoders = {}
        self.input_features = []
        
        # Datos preprocesados
        self.X = None
        self.y = None
        self.X_train = None
        self.X_val = None
        self.X_test = None
        self.y_train = None
        self.y_val = None
        self.y_test = None
        
        # Modelo
        self.model = None
        self.history = None
        self.metrics = {}
        
        # Predicciones
        self.y_pred_train = None
        self.y_pred_val = None
        self.y_pred_test = None
    
    def preprocess(self):
        """
        Preprocesamiento mejorado: feature engineering, normalización, creación de secuencias
        """
        print("\n[PREPROCESAMIENTO] Iniciando...")
        
        # Convertir fecha a datetime
        if 'fecha' in self.df.columns:
            self.df['fecha'] = pd.to_datetime(self.df['fecha'])
        
        # Ordenar por punto y fecha
        if 'punto_recoleccion' in self.df.columns and 'fecha' in self.df.columns:
            self.df = self.df.sort_values(by=['punto_recoleccion', 'fecha']).reset_index(drop=True)
        
        # Feature engineering temporal
        if 'fecha' in self.df.columns:
            self.df['dia_mes'] = self.df['fecha'].dt.day
            self.df['mes'] = self.df['fecha'].dt.month
            self.df['semana_año'] = self.df['fecha'].dt.isocalendar().week
            self.df['dia_semana_num'] = self.df['fecha'].dt.dayofweek
        
        # Codificar variables categóricas
        categorical_cols = self.df.select_dtypes(include='object').columns.tolist()
        categorical_cols = [c for c in categorical_cols if c != 'fecha']
        
        for col in categorical_cols:
            le = LabelEncoder()
            self.df[f'{col}_encoded'] = le.fit_transform(self.df[col].astype(str))
            self.encoders[col] = le
        
        print(f"   ✓ Codificadas {len(categorical_cols)} variables categóricas")
        
        # Identificar columna target
        target_col = None
        for col in ['residuos_kg', 'residuos', 'cantidad', 'volumen']:
            if col in self.df.columns:
                target_col = col
                break
        
        if target_col is None:
            raise ValueError("No se encontró columna target")
        
        # Features de entrada
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()
        self.input_features = [c for c in numeric_cols if c != target_col]
        
        print(f"   ✓ Features de entrada: {len(self.input_features)}")
        
        # MEJORA: Remover outliers ANTES de normalizar
        print("   ✓ Removiendo outliers agresivos...")
        y_data = self.df[target_col].values
        
        # Usar percentiles más estrictos
        Q1 = np.percentile(y_data, 10)
        Q3 = np.percentile(y_data, 90)
        IQR = Q3 - Q1
        
        lower_bound = Q1 - 0.5 * IQR
        upper_bound = Q3 + 0.5 * IQR
        
        mask = (self.df[target_col] >= lower_bound) & (self.df[target_col] <= upper_bound)
        self.df = self.df[mask].reset_index(drop=True)
        
        print(f"   ✓ Muestras después de remover outliers: {len(self.df)}")
        
        # Normalizar inputs y target
        self.scaler_input = MinMaxScaler(feature_range=(0, 1))
        self.df[self.input_features] = self.scaler_input.fit_transform(self.df[self.input_features])
        
        self.scaler_target = MinMaxScaler(feature_range=(0, 1))
        self.df[target_col] = self.scaler_target.fit_transform(self.df[[target_col]]).flatten()
        
        print(f"   ✓ Features normalizados (min-max scaler)")
        
        # Crear secuencias
        data_input = self.df[self.input_features].values
        y_target = self.df[target_col].values
        
        xs = []
        ys = []
        for i in range(len(data_input) - self.sequence_length):
            x = data_input[i:i + self.sequence_length]
            y = y_target[i + self.sequence_length]
            xs.append(x)
            ys.append(y)
        
        self.X = np.array(xs, dtype=np.float32)
        self.y = np.array(ys, dtype=np.float32)
        
        print(f"   ✓ Secuencias creadas: X {self.X.shape}, y {self.y.shape}")
        
        # Verificar si tenemos suficientes datos
        min_samples = 30
        if len(self.y) < min_samples:
            raise ValueError(f"Insuficientes datos. Se necesitan al menos {min_samples} muestras, pero se tienen {len(self.y)}")
        
        # Dividir en train/val/test con proporciones adaptadas
        test_size = max(0.15, int(len(self.y) * 0.15) / len(self.y))
        val_size = max(0.2, int(len(self.y) * 0.2) / len(self.y))
        
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            self.X, self.y, test_size=test_size, random_state=42, shuffle=False
        )
        self.X_train, self.X_val, self.y_train, self.y_val = train_test_split(
            self.X_train, self.y_train, test_size=val_size, random_state=42, shuffle=False
        )
        
        print(f"   ✓ Train: {len(self.y_train)}, Val: {len(self.y_val)}, Test: {len(self.y_test)}")
        print("[PREPROCESAMIENTO] Completado ✓\n")
    
    def build_model(self):
        """Construir modelo LSTM - Versión simplificada y más robusta"""
        print("[MODELO] Construyendo arquitectura LSTM...")
        
        # Modelo más simple y robusto
        self.model = Sequential([
            LSTM(64, activation='relu', return_sequences=True, 
                 input_shape=(self.X.shape[1], self.X.shape[2])),
            Dropout(0.2),
            
            LSTM(32, activation='relu', return_sequences=False),
            Dropout(0.2),
            
            Dense(16, activation='relu'),
            Dropout(0.1),
            
            Dense(1)  # Salida sin activación para regresión
        ])
        
        optimizer = Adam(learning_rate=0.001)
        self.model.compile(optimizer=optimizer, loss='mse', metrics=['mae', 'mse'])
        
        print("[MODELO] Compilado ✓\n")
    
    def train(self, epochs=100, batch_size=16):
        """Entrenar modelo con configuración mejorada"""
        print("[ENTRENAMIENTO] Iniciando entrenamiento...")
        
        # Callbacks mejorados
        early_stop = EarlyStopping(
            monitor='val_loss', 
            patience=20,  # Más paciente
            restore_best_weights=True, 
            verbose=0
        )
        reduce_lr = ReduceLROnPlateau(
            monitor='val_loss', 
            factor=0.5, 
            patience=10, 
            min_lr=0.00001, 
            verbose=0
        )
        
        # Entrenar con batch size pequeño para mejor convergencia
        self.history = self.model.fit(
            self.X_train, self.y_train,
            validation_data=(self.X_val, self.y_val),
            epochs=epochs,
            batch_size=batch_size,
            callbacks=[early_stop, reduce_lr],
            verbose=0
        )
        
        print(f"[ENTRENAMIENTO] Completado: {len(self.history.history['loss'])} épocas ✓\n")
    
    def evaluate(self):
        """Evaluar modelo y calcular métricas"""
        print("[EVALUACIÓN] Calculando métricas...")
        
        self.y_pred_train = self.model.predict(self.X_train, verbose=0).flatten()
        self.y_pred_val = self.model.predict(self.X_val, verbose=0).flatten()
        self.y_pred_test = self.model.predict(self.X_test, verbose=0).flatten()
        
        def calc_metrics(y_true, y_pred, name):
            mse = mean_squared_error(y_true, y_pred)
            rmse = np.sqrt(mse)
            mae = mean_absolute_error(y_true, y_pred)
            r2 = r2_score(y_true, y_pred)
            mape = np.mean(np.abs((y_true - y_pred) / (y_true + 1e-8))) * 100
            return {'mse': float(mse), 'rmse': float(rmse), 'mae': float(mae), 
                    'r2': float(r2), 'mape': float(mape)}
        
        self.metrics['train'] = calc_metrics(self.y_train, self.y_pred_train, 'Train')
        self.metrics['val'] = calc_metrics(self.y_val, self.y_pred_val, 'Val')
        self.metrics['test'] = calc_metrics(self.y_test, self.y_pred_test, 'Test')
        
        print(f"   Train R²: {self.metrics['train']['r2']:.4f}")
        print(f"   Val R²:   {self.metrics['val']['r2']:.4f}")
        print(f"   Test R²:  {self.metrics['test']['r2']:.4f} ✓\n")
    
    def generate_visualization(self, output_path='predicciones.png'):
        """Generar gráfico de predicciones vs reales"""
        print("[VISUALIZACIÓN] Generando gráfico...")
        
        fig, ax = plt.subplots(figsize=(14, 6))
        
        x_range = np.arange(min(100, len(self.y_test)))
        ax.plot(x_range, self.y_test[:100], 'o-', label='Demanda Real', 
                linewidth=2.5, markersize=5, alpha=0.8, color='#2E86AB')
        ax.plot(x_range, self.y_pred_test[:100], 's-', label='Demanda Predicha', 
                linewidth=2.5, markersize=5, alpha=0.8, color='#A23B72')
        
        ax.set_title('Predicción vs Demanda Real', fontsize=14, fontweight='bold', pad=20)
        ax.set_xlabel('Predicción # (1 a 100)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Valor Normalizado', fontsize=12, fontweight='bold')
        ax.legend(fontsize=11, loc='best', framealpha=0.95, shadow=True)
        ax.grid(True, alpha=0.3, linestyle='--')
        
        textstr = f'R² = {self.metrics["test"]["r2"]:.4f}\nRMSE = {self.metrics["test"]["rmse"]:.4f}'
        ax.text(0.98, 0.97, textstr, transform=ax.transAxes, fontsize=11,
                verticalalignment='top', horizontalalignment='right',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"   ✓ Gráfico guardado: {output_path}\n")
        return output_path
    
    def save_model(self, output_path='modelo_lstm.keras'):
        """Guardar modelo entrenado"""
        self.model.save(output_path)
        print(f"[GUARDADO] Modelo guardado: {output_path} ✓\n")
        return output_path
    
    def save_report(self, output_path='reporte_lstm.json'):
        """Guardar reporte de métricas"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'arquitectura': {
                'tipo': 'LSTM 3-capas',
                'capas': [128, 64, 32],
                'parametros': 'BatchNorm + Dropout'
            },
            'datos': {
                'muestras_totales': int(len(self.y)),
                'train': int(len(self.y_train)),
                'val': int(len(self.y_val)),
                'test': int(len(self.y_test)),
                'sequence_length': self.sequence_length,
                'features': len(self.input_features)
            },
            'metricas': self.metrics
        }
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"[GUARDADO] Reporte guardado: {output_path} ✓\n")
        return output_path
    
    def get_results_dict(self):
        """Retorna diccionario con resultados para API"""
        return {
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'metricas': self.metrics,
            'datos': {
                'muestras': len(self.y),
                'train': len(self.y_train),
                'test': len(self.y_test)
            }
        }


def train_from_csv(csv_content, epochs=100):
    """
    Función principal que ejecuta todo el pipeline LSTM
    
    Args:
        csv_content: contenido del CSV (bytes o string)
        epochs: número de épocas para entrenar
    
    Returns:
        dict con rutas de archivos generados y métricas
    """
    try:
        trainer = LSTMTrainer(csv_content)
        trainer.preprocess()
        trainer.build_model()
        trainer.train(epochs=epochs)
        trainer.evaluate()
        
        # Generar outputs
        model_path = trainer.save_model('./lstm_temp/modelo_lstm.keras')
        viz_path = trainer.generate_visualization('./lstm_temp/predicciones.png')
        report_path = trainer.save_report('./lstm_temp/reporte_lstm.json')
        
        results = trainer.get_results_dict()
        results.update({
            'model_path': str(model_path),
            'visualization_path': str(viz_path),
            'report_path': str(report_path)
        })
        
        return results
    
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        return {
            'status': 'error',
            'message': str(e)
        }


if __name__ == '__main__':
    # Test: entrenar con CSV de ejemplo
    print("Módulo lstm_api_service cargado correctamente")
    print("Uso: trainer = LSTMTrainer(csv_content)")
