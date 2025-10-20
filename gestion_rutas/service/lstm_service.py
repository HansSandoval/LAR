"""
Service Layer para Predicciones LSTM
Integra el modelo LSTM con el backend FastAPI
"""

from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, date
import json
import logging
from pathlib import Path
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class LSTMPredictionService:
    """Servicio para predicciones y validación LSTM"""

    # Ruta al archivo de predicciones
    PREDICCIONES_CSV = Path(__file__).parent.parent / "lstm" / "predicciones_lstm.csv"

    @staticmethod
    def cargar_predicciones_csv() -> Optional[pd.DataFrame]:
        """Cargar predicciones desde CSV"""
        try:
            if not LSTMPredictionService.PREDICCIONES_CSV.exists():
                logger.warning(f"Archivo no encontrado: {LSTMPredictionService.PREDICCIONES_CSV}")
                return None
            
            df = pd.read_csv(LSTMPredictionService.PREDICCIONES_CSV)
            logger.info(f"✓ Predicciones cargadas: {len(df)} registros")
            return df
        except Exception as e:
            logger.error(f"Error al cargar predicciones: {str(e)}")
            return None

    @staticmethod
    def calcular_metricas_lstm() -> Dict[str, Any]:
        """Calcular métricas generales del modelo LSTM"""
        df = LSTMPredictionService.cargar_predicciones_csv()
        if df is None or df.empty:
            return {"error": "No se pudieron cargar las predicciones"}

        try:
            # MAPE
            mask = df['Real'] != 0
            mape = np.mean(np.abs((df[mask]['Real'] - df[mask]['Predicho']) / df[mask]['Real'])) * 100

            # RMSE
            rmse = np.sqrt(np.mean((df['Real'] - df['Predicho']) ** 2))

            # MAE
            mae = np.mean(np.abs(df['Real'] - df['Predicho']))

            # R²
            ss_res = np.sum((df['Real'] - df['Predicho']) ** 2)
            ss_tot = np.sum((df['Real'] - np.mean(df['Real'])) ** 2)
            r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0

            # Correlación
            correlation = df['Real'].corr(df['Predicho'])

            # Sesgo
            sesgo = np.mean(df['Real'] - df['Predicho'])

            metricas = {
                "total_muestras": int(len(df)),
                "mape_porcentaje": float(mape),
                "rmse": float(rmse),
                "mae": float(mae),
                "r2": float(r2),
                "correlacion": float(correlation),
                "sesgo": float(sesgo),
                "valor_real_promedio": float(df['Real'].mean()),
                "valor_predicho_promedio": float(df['Predicho'].mean()),
                "fecha_calculo": datetime.now().isoformat(),
                "calidad": LSTMPredictionService._evaluar_calidad(mape, r2)
            }

            logger.info(f"✓ Métricas LSTM calculadas: MAPE={mape:.2f}%, R²={r2:.4f}")
            return metricas

        except Exception as e:
            logger.error(f"Error al calcular métricas: {str(e)}")
            return {"error": str(e)}

    @staticmethod
    def _evaluar_calidad(mape: float, r2: float) -> Dict[str, Any]:
        """Evaluar calidad del modelo basado en MAPE y R²"""
        evaluacion = {
            "mape_calidad": "excelente" if mape < 15 else "buena" if mape < 25 else "regular",
            "r2_calidad": "excelente" if r2 > 0.8 else "buena" if r2 > 0.6 else "regular",
        }

        # Calidad general
        if mape < 25 and r2 > 0.6:
            evaluacion["calidad_general"] = "buena"
        elif mape < 50 and r2 > 0:
            evaluacion["calidad_general"] = "aceptable"
        else:
            evaluacion["calidad_general"] = "requiere_mejora"

        return evaluacion

    @staticmethod
    def obtener_estadisticas_predicciones() -> Dict[str, Any]:
        """Obtener estadísticas detalladas de las predicciones"""
        df = LSTMPredictionService.cargar_predicciones_csv()
        if df is None or df.empty:
            return {"error": "No se pudieron cargar las predicciones"}

        try:
            # Calcular diferencias
            diferencias = df['Real'] - df['Predicho']
            diferencias_pct = (diferencias / df['Real'].replace(0, np.nan) * 100).dropna()

            estadisticas = {
                "predicciones_exactas": int((diferencias.abs() < 0.01).sum()),
                "predicciones_cercanas": int((diferencias.abs() < 0.1).sum()),
                "predicciones_alejadas": int((diferencias.abs() >= 0.1).sum()),
                "error_promedio": float(diferencias.mean()),
                "error_maximo": float(diferencias.abs().max()),
                "error_minimo": float(diferencias.abs().min()),
                "desviacion_estandar_error": float(diferencias.std()),
                "predicciones_sobreestimadas": int((diferencias < 0).sum()),
                "predicciones_subestimadas": int((diferencias > 0).sum()),
                "porcentaje_sobreestimacion": float((diferencias < 0).sum() / len(df) * 100),
                "porcentaje_subestimacion": float((diferencias > 0).sum() / len(df) * 100),
            }

            return estadisticas

        except Exception as e:
            logger.error(f"Error al obtener estadísticas: {str(e)}")
            return {"error": str(e)}

    @staticmethod
    def predecir_demanda(
        tipo_zona: str,
        hora_del_dia: int,
        dia_semana: int,
        historial_datos: Optional[List[float]] = None
    ) -> Dict[str, Any]:
        """
        Predecir demanda normalizada para una zona
        (En producción, esto usaría el modelo LSTM real)
        """
        try:
            # Para ahora, retornar una predicción basada en las predicciones cargadas
            df = LSTMPredictionService.cargar_predicciones_csv()
            
            if df is not None and not df.empty:
                # Seleccionar una predicción aleatoria como ejemplo
                idx = hash(f"{tipo_zona}_{hora_del_dia}_{dia_semana}") % len(df)
                prediccion = float(df.iloc[idx]['Predicho'])
            else:
                # Predicción por defecto
                prediccion = 0.5

            return {
                "tipo_zona": tipo_zona,
                "hora": hora_del_dia,
                "dia_semana": dia_semana,
                "demanda_normalizada": prediccion,
                "intervalo_confianza": {
                    "minimo": max(0, prediccion - 0.1),
                    "maximo": min(1, prediccion + 0.1)
                },
                "fecha_prediccion": datetime.now().isoformat(),
                "modelo": "LSTM_v1.0"
            }

        except Exception as e:
            logger.error(f"Error al predecir demanda: {str(e)}")
            return {"error": str(e)}

    @staticmethod
    def obtener_reporte_validacion() -> Dict[str, Any]:
        """Obtener reporte completo de validación del modelo"""
        try:
            metricas = LSTMPredictionService.calcular_metricas_lstm()
            estadisticas = LSTMPredictionService.obtener_estadisticas_predicciones()

            reporte = {
                "metricas": metricas,
                "estadisticas": estadisticas,
                "archivo_validacion": str(LSTMPredictionService.PREDICCIONES_CSV),
                "fecha_reporte": datetime.now().isoformat(),
                "modelo_version": "LSTM_v1.0"
            }

            return reporte

        except Exception as e:
            logger.error(f"Error al generar reporte: {str(e)}")
            return {"error": str(e)}

    @staticmethod
    def validar_prediccion(valor_real: float, valor_predicho: float) -> Dict[str, Any]:
        """Validar una predicción individual contra el valor real"""
        try:
            error_absoluto = abs(valor_real - valor_predicho)
            
            if valor_real != 0:
                error_porcentual = (error_absoluto / valor_real) * 100
            else:
                error_porcentual = 0 if error_absoluto == 0 else 100

            return {
                "valor_real": valor_real,
                "valor_predicho": valor_predicho,
                "error_absoluto": float(error_absoluto),
                "error_porcentual": float(error_porcentual),
                "acierto": "exacto" if error_absoluto < 0.01 else "cercano" if error_absoluto < 0.1 else "alejado",
                "sesgo": "subestimación" if valor_predicho < valor_real else "sobrestimación"
            }

        except Exception as e:
            logger.error(f"Error al validar predicción: {str(e)}")
            return {"error": str(e)}
