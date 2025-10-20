"""
Router para endpoints de predicción LSTM
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from service.lstm_service import LSTMPredictionService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/lstm",
    tags=["LSTM - Predicción de Demanda"]
)


@router.get(
    "/metricas",
    summary="Obtener métricas del modelo LSTM",
    description="Retorna las métricas de desempeño del modelo LSTM"
)
def obtener_metricas_lstm():
    """
    Obtener métricas de validación del modelo LSTM
    
    Retorna:
    - MAPE: Error porcentual absoluto medio
    - RMSE: Raíz del error cuadrático medio
    - R²: Coeficiente de determinación
    - Correlación: Coeficiente de correlación de Pearson
    """
    try:
        metricas = LSTMPredictionService.calcular_metricas_lstm()
        if "error" in metricas:
            raise HTTPException(status_code=500, detail=metricas["error"])
        return {"success": True, "data": metricas}
    except Exception as e:
        logger.error(f"Error al obtener métricas: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/estadisticas",
    summary="Obtener estadísticas de predicciones",
    description="Retorna estadísticas detalladas de los errores de predicción"
)
def obtener_estadisticas():
    """
    Obtener estadísticas de las predicciones
    
    Retorna:
    - Predicciones exactas, cercanas y alejadas
    - Errores máximos, mínimos y promedio
    - Porcentaje de sobreestimación/subestimación
    """
    try:
        estadisticas = LSTMPredictionService.obtener_estadisticas_predicciones()
        if "error" in estadisticas:
            raise HTTPException(status_code=500, detail=estadisticas["error"])
        return {"success": True, "data": estadisticas}
    except Exception as e:
        logger.error(f"Error al obtener estadísticas: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/reporte",
    summary="Obtener reporte completo de validación",
    description="Retorna un reporte completo con métricas y estadísticas"
)
def obtener_reporte_validacion():
    """
    Obtener reporte completo de validación del modelo LSTM
    
    Incluye:
    - Métricas de error (MAPE, RMSE, MAE, R²)
    - Estadísticas de predicciones
    - Evaluación de calidad
    - Información del modelo
    """
    try:
        reporte = LSTMPredictionService.obtener_reporte_validacion()
        if "error" in reporte:
            raise HTTPException(status_code=500, detail=reporte["error"])
        return {"success": True, "data": reporte}
    except Exception as e:
        logger.error(f"Error al obtener reporte: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/predecir",
    summary="Realizar predicción de demanda",
    description="Predice la demanda normalizada para una zona y horario"
)
def predecir_demanda(
    tipo_zona: str = Query(..., description="Tipo de zona (ej: industrial, comercial, residencial)"),
    hora_del_dia: int = Query(..., ge=0, le=23, description="Hora del día (0-23)"),
    dia_semana: int = Query(..., ge=0, le=6, description="Día de la semana (0=lunes, 6=domingo)"),
    historial_datos: Optional[str] = Query(None, description="Datos históricos en formato JSON")
):
    """
    Realizar una predicción de demanda
    
    Parámetros:
    - tipo_zona: Categoría de la zona
    - hora_del_dia: Hora (0-23)
    - dia_semana: Día (0=lunes, 6=domingo)
    - historial_datos: (Opcional) Datos históricos en JSON
    
    Retorna:
    - Predicción normalizada (0-1)
    - Intervalo de confianza
    - Información del modelo
    """
    try:
        prediccion = LSTMPredictionService.predecir_demanda(
            tipo_zona=tipo_zona,
            hora_del_dia=hora_del_dia,
            dia_semana=dia_semana,
            historial_datos=historial_datos
        )
        if "error" in prediccion:
            raise HTTPException(status_code=500, detail=prediccion["error"])
        return {"success": True, "data": prediccion}
    except Exception as e:
        logger.error(f"Error al realizar predicción: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/validar",
    summary="Validar predicción contra valor real",
    description="Compara una predicción con el valor real y calcula el error"
)
def validar_prediccion(
    valor_real: float = Query(..., ge=0, le=1, description="Valor real normalizado"),
    valor_predicho: float = Query(..., ge=0, le=1, description="Valor predicho normalizado")
):
    """
    Validar una predicción individual
    
    Parámetros:
    - valor_real: Valor real observado (0-1)
    - valor_predicho: Valor predicho por el modelo (0-1)
    
    Retorna:
    - Error absoluto y porcentual
    - Clasificación del acierto (exacto, cercano, alejado)
    - Tipo de sesgo (sobreestimación/subestimación)
    """
    try:
        validacion = LSTMPredictionService.validar_prediccion(valor_real, valor_predicho)
        if "error" in validacion:
            raise HTTPException(status_code=500, detail=validacion["error"])
        return {"success": True, "data": validacion}
    except Exception as e:
        logger.error(f"Error al validar: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/health",
    summary="Verificar salud del modelo LSTM",
    description="Verifica que el modelo LSTM esté disponible y funcional"
)
def health_check_lstm():
    """
    Verificar disponibilidad del modelo LSTM
    
    Retorna:
    - Estado del modelo (healthy/degraded)
    - Disponibilidad del archivo de predicciones
    - Cantidad de registros de validación
    """
    try:
        metricas = LSTMPredictionService.calcular_metricas_lstm()
        
        if "error" in metricas:
            return {
                "status": "degraded",
                "error": metricas["error"],
                "mensaje": "Modelo no disponible"
            }
        
        return {
            "status": "healthy",
            "modelo": "LSTM_v1.0",
            "total_muestras": metricas.get("total_muestras", 0),
            "calidad": metricas.get("calidad", {}).get("calidad_general", "desconocida"),
            "mensaje": "Modelo LSTM funcional"
        }
    except Exception as e:
        return {
            "status": "degraded",
            "error": str(e),
            "mensaje": "Error al verificar modelo LSTM"
        }
