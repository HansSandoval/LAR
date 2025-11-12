"""
Servicio LSTM Simplificado y Determinístico
- Determinismo GARANTIZADO
- Sin complejidades innecesarias
- Datos reales solo: Devuelve R² real sin engaños
"""

import pandas as pd
import numpy as np
import json
import io
import os
from datetime import datetime, timedelta
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Establecer seeds ANTES de importar TensorFlow
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
np.random.seed(42)

import tensorflow as tf
tf.random.set_seed(42)
tf.compat.v1.set_random_seed(42)

from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from tensorflow.keras.regularizers import l2

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


def setup_seeds():
    """Establece todos los seeds para determinismo COMPLETO"""
    os.environ['PYTHONHASHSEED'] = '42'
    np.random.seed(42)
    tf.random.set_seed(42)
    tf.compat.v1.set_random_seed(42)


class LSTMTrainer:
    """LSTM simple, real y determinístico"""
    
    def __init__(self, csv_content, temp_dir='./lstm_temp'):
        setup_seeds()
        
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(exist_ok=True)
        
        if isinstance(csv_content, bytes):
            csv_content = csv_content.decode('utf-8')
        
        self.df = pd.read_csv(io.StringIO(csv_content))
        self.sequence_length = 3  # REDUCIR a 3 días - tienes muy pocos datos
        
        self.scaler = None
        self.X_train = self.y_train = None
        self.X_val = self.y_val = None
        self.X_test = self.y_test = None
        self.model = None
        self.history = None
        self.metrics = {}
        
        self.dates_test = None
        self.y_actual_test = None
        self.y_pred_test = None
        self.future_predictions = None
        self.dates_future = None
    
    def preprocess(self):
        """Preprocesamiento simple y claro"""
        print("[PREPROCESAMIENTO] Iniciando...")
        
        # Validar que tenemos residuos_kg
        if 'residuos_kg' not in self.df.columns:
            raise ValueError("Falta columna 'residuos_kg'")
        
        # Si hay columna fecha, AGREGAR por fecha (múltiples registros por día)
        if 'fecha' in self.df.columns:
            self.df['fecha'] = pd.to_datetime(self.df['fecha'])
            # Agrupar por fecha y sumar residuos
            df_daily = self.df.groupby('fecha')['residuos_kg'].sum().reset_index()
            df_daily.columns = ['fecha', 'residuos_kg']
            df_daily = df_daily.sort_values('fecha').reset_index(drop=True)
            
            dates = df_daily['fecha'].values
            y_data = df_daily['residuos_kg'].values.astype(np.float32)
            
            print(f"   Datos agregados por fecha: {len(df_daily)} días únicos")
        else:
            dates = pd.date_range(start='2024-01-01', periods=len(self.df), freq='D').values
            y_data = self.df['residuos_kg'].values.astype(np.float32)
        
        print(f"   Muestras: {len(y_data)}, Rango: {y_data.min():.1f} - {y_data.max():.1f} kg")
        
        if len(y_data) < self.sequence_length + 5:
            raise ValueError(f"Insuficientes datos: necesitas al menos {self.sequence_length + 5}")
        
        # Normalizar
        self.scaler = MinMaxScaler()
        y_norm = self.scaler.fit_transform(y_data.reshape(-1, 1)).flatten()
        
        # Crear secuencias
        X, y, dates_seq = [], [], []
        for i in range(len(y_norm) - self.sequence_length):
            X.append(y_norm[i:i+self.sequence_length])
            y.append(y_norm[i+self.sequence_length])
            dates_seq.append(dates[i+self.sequence_length])
        
        X = np.array(X, dtype=np.float32)
        y = np.array(y, dtype=np.float32)
        dates_seq = np.array(dates_seq)
        
        # Split: 80% train, 10% val, 10% test - necesitas más datos de entrenamiento
        n_samples = len(X)
        train_end = int(0.80 * n_samples)
        val_end = int(0.90 * n_samples)
        
        self.X_train = X[:train_end]
        self.y_train = y[:train_end]
        self.X_val = X[train_end:val_end]
        self.y_val = y[train_end:val_end]
        self.X_test = X[val_end:]
        self.y_test = y[val_end:]
        
        self.dates_test = dates_seq[val_end:]
        self.y_actual_test = self.scaler.inverse_transform(self.y_test.reshape(-1, 1)).flatten()
        
        print(f"   Secuencias: {len(X)}, Train: {len(self.X_train)}, Val: {len(self.X_val)}, Test: {len(self.X_test)}")
        print("[PREPROCESAMIENTO] OK\n")
    
    def build_model(self):
        """Modelo MUY SIMPLE para pocos datos (65 muestras totales)"""
        print("[MODELO] Construyendo modelo simple para pocos datos...")
        
        # Reshape para LSTM: necesita (samples, timesteps, features)
        self.X_train = self.X_train.reshape((self.X_train.shape[0], self.X_train.shape[1], 1))
        self.X_val = self.X_val.reshape((self.X_val.shape[0], self.X_val.shape[1], 1))
        self.X_test = self.X_test.reshape((self.X_test.shape[0], self.X_test.shape[1], 1))
        
        self.model = Sequential([
            LSTM(32, activation='tanh', input_shape=(self.sequence_length, 1)),
            Dense(16, activation='relu'),
            Dense(1)
        ])
        
        self.model.compile(
            optimizer=Adam(learning_rate=0.01),
            loss='mse',
            metrics=['mae']
        )
        
        print("[MODELO] OK - LSTM MUY SIMPLE: 32->16->1\n")
    
    def train(self, epochs=100):
        """Entrenar con configuración para POCOS DATOS"""
        print(f"[ENTRENAMIENTO] {epochs} épocas para dataset pequeño...")
        
        callbacks = [
            EarlyStopping(
                monitor='val_loss',
                patience=30,
                restore_best_weights=True,
                verbose=0
            )
        ]
        
        self.history = self.model.fit(
            self.X_train, self.y_train,
            validation_data=(self.X_val, self.y_val),
            epochs=epochs,
            batch_size=4,
            callbacks=callbacks,
            verbose=0
        )
        
        actual_epochs = len(self.history.history['loss'])
        final_train_loss = self.history.history['loss'][-1]
        final_val_loss = self.history.history['val_loss'][-1]
        print(f"[ENTRENAMIENTO] {actual_epochs} épocas")
        print(f"   Train loss: {final_train_loss:.6f}, Val loss: {final_val_loss:.6f}\n")
    
    def evaluate(self):
        """Calcular métricas (TEST SET SOLO)"""
        print("[EVALUACIÓN] Calculando...")
        
        print(f"   Test set size: {len(self.X_test)} muestras")
        print(f"   Y_actual min/max: {self.y_actual_test.min():.1f} / {self.y_actual_test.max():.1f} kg")
        
        y_pred_test_norm = self.model.predict(self.X_test, verbose=0).flatten()
        print(f"   Predicciones norm min/max: {y_pred_test_norm.min():.4f} / {y_pred_test_norm.max():.4f}")
        
        self.y_pred_test = self.scaler.inverse_transform(y_pred_test_norm.reshape(-1, 1)).flatten()
        print(f"   Y_pred min/max: {self.y_pred_test.min():.1f} / {self.y_pred_test.max():.1f} kg")
        
        # Validar que no hay NaN o inf
        if np.any(np.isnan(self.y_actual_test)) or np.any(np.isinf(self.y_actual_test)):
            print("   ADVERTENCIA: NaN/inf en y_actual_test")
        if np.any(np.isnan(self.y_pred_test)) or np.any(np.isinf(self.y_pred_test)):
            print("   ADVERTENCIA: NaN/inf en y_pred_test")
        
        # Métricas reales
        mse = mean_squared_error(self.y_actual_test, self.y_pred_test)
        rmse = np.sqrt(mse)
        mae = mean_absolute_error(self.y_actual_test, self.y_pred_test)
        r2 = r2_score(self.y_actual_test, self.y_pred_test)
        mape = np.mean(np.abs((self.y_actual_test - self.y_pred_test) / np.maximum(np.abs(self.y_actual_test), 1e-8))) * 100
        
        self.metrics = {
            'mse': float(mse),
            'rmse': float(rmse),
            'mae': float(mae),
            'r2': float(r2),
            'mape': float(mape)
        }
        
        print(f"   MSE: {mse:.2f}")
        print(f"   R²: {r2:.4f}")
        print(f"   RMSE: {rmse:.2f} kg")
        print(f"   MAE: {mae:.2f} kg")
        print(f"   MAPE: {mape:.2f}%")
        print("[EVALUACIÓN] OK\n")
    
    def predict_future(self, days_ahead=30):
        """Predicción futura usando LSTM"""
        print(f"[FUTURO] Prediciendo {days_ahead} días...")
        
        # Última secuencia ya está en formato 3D (samples, timesteps, features)
        last_seq = self.X_test[-1].copy()  # Shape: (sequence_length, 1)
        preds = []
        
        last_date = pd.to_datetime(self.dates_test[-1])
        dates = []
        
        for i in range(days_ahead):
            # Reshape para predicción: (1, sequence_length, 1)
            pred_norm = self.model.predict(last_seq.reshape(1, self.sequence_length, 1), verbose=0)[0, 0]
            pred_real = self.scaler.inverse_transform([[pred_norm]])[0, 0]
            
            preds.append(pred_real)
            last_date += timedelta(days=1)
            dates.append(last_date)
            
            # Actualizar ventana: eliminar primera, agregar predicción normalizada
            last_seq = np.append(last_seq[1:], [[pred_norm]], axis=0)
        
        self.future_predictions = np.array(preds)
        self.dates_future = np.array([d.strftime('%Y-%m-%d') for d in dates])
        
        print(f"[FUTURO] OK\n")
    
    def generate_graph(self, output_path=None):
        """Generar gráfico real"""
        print("[GRÁFICO] Generando...")
        
        if output_path is None:
            output_path = self.temp_dir / 'grafico.png'
        
        fig, ax = plt.subplots(figsize=(14, 6))
        
        dates = pd.to_datetime(self.dates_test)
        
        # Líneas
        ax.plot(dates, self.y_actual_test, 'o-', label='Demanda Real', 
                linewidth=2, markersize=5, color='#2E86AB', alpha=0.8)
        ax.plot(dates, self.y_pred_test, 's-', label='Predicción', 
                linewidth=2, markersize=5, color='#A23B72', alpha=0.8)
        
        if self.future_predictions is not None:
            future_dates = pd.to_datetime(self.dates_future)
            ax.plot(future_dates, self.future_predictions, '^--', label='Futuro',
                    linewidth=2, markersize=5, color='#F18F01', alpha=0.8)
            ax.axvline(x=dates[-1], color='gray', linestyle=':', alpha=0.5)
        
        # Formato
        ax.set_title('Predicción de Demanda de Residuos', fontsize=14, fontweight='bold')
        ax.set_xlabel('Fecha', fontsize=12)
        ax.set_ylabel('Residuos (kg)', fontsize=12)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        plt.xticks(rotation=45, ha='right')
        ax.legend(fontsize=11)
        ax.grid(True, alpha=0.3)
        
        # Info
        info = f"R²={self.metrics['r2']:.4f} | RMSE={self.metrics['rmse']:.2f}kg | MAE={self.metrics['mae']:.2f}kg"
        ax.text(0.98, 0.03, info, transform=ax.transAxes, fontsize=10,
                ha='right', va='bottom', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        plt.tight_layout()
        plt.savefig(str(output_path), dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"[GRÁFICO] {output_path}\n")
        return str(output_path)
    
    def save_model(self, path=None):
        """Guardar modelo"""
        if path is None:
            path = self.temp_dir / 'modelo.keras'
        self.model.save(str(path))
        print(f"[MODELO] Guardado: {path}\n")
        return str(path)
    
    def save_report(self, path=None):
        """Guardar reporte"""
        if path is None:
            path = self.temp_dir / 'reporte.json'
            
        report = {
            'timestamp': datetime.now().isoformat(),
            'metricas': self.metrics,
            'muestras': {
                'train': len(self.y_train),
                'test': len(self.y_test)
            }
        }
        
        with open(str(path), 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"[REPORTE] Guardado: {path}\n")
        return str(path)
        return path


def train_from_csv(csv_content, epochs=100):
    """Función principal - SIMPLE Y DETERMINÍSTICA"""
    try:
        trainer = LSTMTrainer(csv_content)
        trainer.preprocess()
        trainer.build_model()
        trainer.train(epochs=epochs)
        trainer.evaluate()
        trainer.predict_future(days_ahead=30)
        
        model_path = trainer.save_model('./lstm_temp/modelo.keras')
        graph_path = trainer.generate_graph('./lstm_temp/grafico.png')
        report_path = trainer.save_report('./lstm_temp/reporte.json')
        
        return {
            'status': 'success',
            'metricas': trainer.metrics,
            'model_path': str(model_path),
            'graph_path': str(graph_path),
            'report_path': str(report_path),
            'predicciones_futuras': {
                'fechas': list(trainer.dates_future),
                'valores': [float(v) for v in trainer.future_predictions]
            }
        }
    
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        return {
            'status': 'error',
            'message': str(e)
        }


if __name__ == '__main__':
    print("LSTM Simplificado v5 - Determinístico")
