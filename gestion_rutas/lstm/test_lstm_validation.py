"""
Script de prueba para validar el modelo LSTM
Usa el archivo predicciones_lstm.csv para calcular métricas de desempeño
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LSTMValidator:
    """Validador de predicciones LSTM"""

    def __init__(self, csv_path: str):
        """Inicializar validador con archivo CSV"""
        self.csv_path = Path(csv_path)
        self.data = None
        self.metrics = {}
        
        if not self.csv_path.exists():
            raise FileNotFoundError(f"Archivo no encontrado: {csv_path}")
        
        self.load_data()

    def load_data(self):
        """Cargar datos del CSV"""
        try:
            self.data = pd.read_csv(self.csv_path)
            logger.info(f"✓ Datos cargados: {len(self.data)} registros")
            logger.info(f"  Columnas: {list(self.data.columns)}")
        except Exception as e:
            logger.error(f"✗ Error al cargar datos: {str(e)}")
            raise

    def calcular_mape(self) -> float:
        """
        Calcular Mean Absolute Percentage Error
        MAPE = (1/n) * Σ|((Real - Predicho) / Real)| * 100
        """
        # Evitar división por cero
        mask = self.data['Real'] != 0
        datos_validos = self.data[mask]
        
        if len(datos_validos) == 0:
            return np.inf
        
        mape = np.mean(np.abs((datos_validos['Real'] - datos_validos['Predicho']) / datos_validos['Real'])) * 100
        return mape

    def calcular_rmse(self) -> float:
        """
        Calcular Root Mean Squared Error
        RMSE = √(1/n * Σ(Real - Predicho)²)
        """
        rmse = np.sqrt(np.mean((self.data['Real'] - self.data['Predicho']) ** 2))
        return rmse

    def calcular_mae(self) -> float:
        """
        Calcular Mean Absolute Error
        MAE = (1/n) * Σ|Real - Predicho|
        """
        mae = np.mean(np.abs(self.data['Real'] - self.data['Predicho']))
        return mae

    def calcular_r2(self) -> float:
        """
        Calcular Coeficiente de Determinación (R²)
        R² = 1 - (SS_res / SS_tot)
        """
        ss_res = np.sum((self.data['Real'] - self.data['Predicho']) ** 2)
        ss_tot = np.sum((self.data['Real'] - np.mean(self.data['Real'])) ** 2)
        r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        return r2

    def calcular_correlacion(self) -> float:
        """Calcular coeficiente de correlación de Pearson"""
        correlation = self.data['Real'].corr(self.data['Predicho'])
        return correlation

    def calcular_sesgo(self) -> float:
        """
        Calcular sesgo del modelo
        Sesgo = Media(Real - Predicho)
        """
        sesgo = np.mean(self.data['Real'] - self.data['Predicho'])
        return sesgo

    def validar_todas_metricas(self) -> dict:
        """Calcular todas las métricas"""
        try:
            self.metrics = {
                'total_muestras': len(self.data),
                'mape': self.calcular_mape(),
                'rmse': self.calcular_rmse(),
                'mae': self.calcular_mae(),
                'r2': self.calcular_r2(),
                'correlacion': self.calcular_correlacion(),
                'sesgo': self.calcular_sesgo(),
                'valor_real_promedio': self.data['Real'].mean(),
                'valor_predicho_promedio': self.data['Predicho'].mean(),
                'valor_real_min': self.data['Real'].min(),
                'valor_real_max': self.data['Real'].max(),
                'valor_predicho_min': self.data['Predicho'].min(),
                'valor_predicho_max': self.data['Predicho'].max(),
            }
            return self.metrics
        except Exception as e:
            logger.error(f"✗ Error al calcular métricas: {str(e)}")
            raise

    def imprimir_reporte(self):
        """Imprimir reporte detallado de validación"""
        if not self.metrics:
            self.validar_todas_metricas()

        logger.info("\n" + "=" * 70)
        logger.info("📊 REPORTE DE VALIDACIÓN MODELO LSTM")
        logger.info("=" * 70)
        
        logger.info(f"\n📈 DATOS GENERALES:")
        logger.info(f"  Total de muestras: {self.metrics['total_muestras']}")
        logger.info(f"  Fecha de validación: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        logger.info(f"\n📊 MÉTRICAS DE ERROR:")
        logger.info(f"  MAPE (Mean Absolute Percentage Error): {self.metrics['mape']:.2f}%")
        logger.info(f"  RMSE (Root Mean Squared Error): {self.metrics['rmse']:.6f}")
        logger.info(f"  MAE (Mean Absolute Error): {self.metrics['mae']:.6f}")
        
        logger.info(f"\n🎯 MÉTRICAS DE BONDAD DE AJUSTE:")
        logger.info(f"  R² (Coeficiente de Determinación): {self.metrics['r2']:.4f}")
        logger.info(f"  Correlación de Pearson: {self.metrics['correlacion']:.4f}")
        
        logger.info(f"\n⚖️  ANÁLISIS DE SESGO:")
        logger.info(f"  Sesgo del modelo: {self.metrics['sesgo']:.6f}")
        
        logger.info(f"\n📐 ESTADÍSTICAS DE VALORES REALES:")
        logger.info(f"  Media: {self.metrics['valor_real_promedio']:.4f}")
        logger.info(f"  Mínimo: {self.metrics['valor_real_min']:.4f}")
        logger.info(f"  Máximo: {self.metrics['valor_real_max']:.4f}")
        
        logger.info(f"\n🔮 ESTADÍSTICAS DE PREDICCIONES:")
        logger.info(f"  Media: {self.metrics['valor_predicho_promedio']:.4f}")
        logger.info(f"  Mínimo: {self.metrics['valor_predicho_min']:.4f}")
        logger.info(f"  Máximo: {self.metrics['valor_predicho_max']:.4f}")
        
        logger.info("\n" + "=" * 70)
        
        # Evaluación de calidad
        logger.info(f"\n✅ EVALUACIÓN DE CALIDAD:")
        if self.metrics['mape'] < 15:
            logger.info(f"  ✓ MAPE excelente (<15%)")
        elif self.metrics['mape'] < 25:
            logger.info(f"  ⚠ MAPE bueno (15-25%)")
        else:
            logger.info(f"  ✗ MAPE regular (>25%)")
        
        if self.metrics['r2'] > 0.8:
            logger.info(f"  ✓ R² excelente (>0.8)")
        elif self.metrics['r2'] > 0.6:
            logger.info(f"  ⚠ R² bueno (0.6-0.8)")
        else:
            logger.info(f"  ✗ R² regular (<0.6)")
        
        logger.info("\n" + "=" * 70 + "\n")

    def generar_visualizaciones(self, output_dir: str = None):
        """Generar gráficos de validación"""
        if output_dir is None:
            output_dir = Path(self.csv_path).parent / "validacion_graficos"
        
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)
        
        try:
            # Gráfico 1: Real vs Predicho (scatter)
            fig, axes = plt.subplots(2, 2, figsize=(14, 10))
            
            # Scatter plot
            axes[0, 0].scatter(self.data['Real'], self.data['Predicho'], alpha=0.6, s=20)
            axes[0, 0].plot([self.data['Real'].min(), self.data['Real'].max()], 
                           [self.data['Real'].min(), self.data['Real'].max()], 
                           'r--', lw=2, label='Línea perfecta')
            axes[0, 0].set_xlabel('Valores Reales')
            axes[0, 0].set_ylabel('Valores Predichos')
            axes[0, 0].set_title('Real vs Predicho (Scatter)')
            axes[0, 0].legend()
            axes[0, 0].grid(True, alpha=0.3)
            
            # Residuos
            residuos = self.data['Real'] - self.data['Predicho']
            axes[0, 1].scatter(self.data['Predicho'], residuos, alpha=0.6, s=20)
            axes[0, 1].axhline(y=0, color='r', linestyle='--', lw=2)
            axes[0, 1].set_xlabel('Valores Predichos')
            axes[0, 1].set_ylabel('Residuos')
            axes[0, 1].set_title('Análisis de Residuos')
            axes[0, 1].grid(True, alpha=0.3)
            
            # Histograma de residuos
            axes[1, 0].hist(residuos, bins=30, edgecolor='black', alpha=0.7)
            axes[1, 0].set_xlabel('Residuos')
            axes[1, 0].set_ylabel('Frecuencia')
            axes[1, 0].set_title(f'Distribución de Residuos (Media={residuos.mean():.6f})')
            axes[1, 0].grid(True, alpha=0.3)
            
            # Series de tiempo
            axes[1, 1].plot(self.data.index, self.data['Real'], label='Real', marker='o', markersize=3)
            axes[1, 1].plot(self.data.index, self.data['Predicho'], label='Predicho', marker='s', markersize=3)
            axes[1, 1].set_xlabel('Índice de Muestra')
            axes[1, 1].set_ylabel('Valor')
            axes[1, 1].set_title('Serie de Tiempo: Real vs Predicho')
            axes[1, 1].legend()
            axes[1, 1].grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # Guardar figura
            output_file = output_dir / f"validacion_lstm_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            plt.savefig(output_file, dpi=150, bbox_inches='tight')
            logger.info(f"✓ Gráficos guardados en: {output_file}")
            
            return output_file
            
        except Exception as e:
            logger.error(f"✗ Error al generar visualizaciones: {str(e)}")
            return None

    def exportar_reporte_json(self, output_path: str = None):
        """Exportar métricas a JSON"""
        if output_path is None:
            output_path = Path(self.csv_path).parent / f"reporte_lstm_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        output_path = Path(output_path)
        
        try:
            import json
            
            # Convertir numpy types a tipos nativos de Python
            metrics_json = {}
            for key, value in self.metrics.items():
                if isinstance(value, (np.floating, np.integer)):
                    metrics_json[key] = float(value)
                else:
                    metrics_json[key] = value
            
            metrics_json['fecha_validacion'] = datetime.now().isoformat()
            metrics_json['archivo_csv'] = str(self.csv_path)
            
            with open(output_path, 'w') as f:
                json.dump(metrics_json, f, indent=2)
            
            logger.info(f"✓ Reporte JSON exportado a: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"✗ Error al exportar reporte: {str(e)}")
            return None


def main():
    """Función principal"""
    csv_path = Path(__file__).parent / "predicciones_lstm.csv"
    
    try:
        # Inicializar validador
        validator = LSTMValidator(str(csv_path))
        
        # Calcular todas las métricas
        validator.validar_todas_metricas()
        
        # Imprimir reporte
        validator.imprimir_reporte()
        
        # Generar visualizaciones
        validator.generar_visualizaciones()
        
        # Exportar reporte JSON
        validator.exportar_reporte_json()
        
        logger.info("\n✓ Validación completada exitosamente\n")
        
    except Exception as e:
        logger.error(f"\n✗ Error en validación: {str(e)}\n")
        raise


if __name__ == "__main__":
    main()
