"""
Router para endpoints de predicción LSTM
"""

from fastapi import APIRouter, HTTPException, Query, File, UploadFile, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
from datetime import datetime, timedelta
from ..service.lstm_service import LSTMPredictionService
from ..service.prediccion_mapa_service import PrediccionMapaService
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/lstm",
    tags=["LSTM - Predicción de Demanda"]
)

# Templates
templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))


@router.get("/test", response_class=HTMLResponse, include_in_schema=False)
async def test_page():
    """Endpoint de prueba simple"""
    return HTMLResponse(content="<h1>El servidor funciona correctamente!</h1>")


@router.get("/trainer", response_class=HTMLResponse, include_in_schema=False)
async def lstm_trainer_page(request: Request):
    """Página web para entrenar el modelo LSTM"""
    return templates.TemplateResponse("lstm_trainer.html", {"request": request})


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


@router.get(
    "/predicciones-fecha",
    summary="Obtener predicciones LSTM para una fecha específica",
    description="Retorna todos los puntos de recolección con predicciones para la fecha indicada"
)
def obtener_predicciones_fecha(
    fecha: Optional[str] = Query(None, description="Fecha predicción (YYYY-MM-DD). Default: mañana")
):
    """
    Obtener predicciones LSTM con coordenadas geográficas para una fecha
    
    Retorna lista de puntos con:
    - ID del punto
    - Nombre del punto
    - Coordenadas (latitud, longitud)
    - Predicción de demanda en kg
    - Fecha de la predicción
    - Método usado (LSTM o sintético)
    """
    try:
        # Parsear fecha
        if fecha:
            try:
                fecha_prediccion = datetime.strptime(fecha, '%Y-%m-%d')
            except ValueError:
                raise HTTPException(status_code=400, detail="Formato de fecha inválido. Usar YYYY-MM-DD")
        else:
            fecha_prediccion = datetime.now() + timedelta(days=1)
        
        # Generar predicciones usando el servicio de mapa
        servicio = PrediccionMapaService()
        predicciones = servicio.generar_predicciones_completas(fecha_prediccion)
        
        if not predicciones or len(predicciones) == 0:
            # Si no hay predicciones LSTM, retornar error descriptivo
            logger.warning("No se pudieron cargar predicciones LSTM")
            raise HTTPException(
                status_code=503,
                detail="No hay predicciones disponibles. Verifica que existan datos históricos."
            )
        
        return {
            "success": True,
            "fecha": fecha_prediccion.strftime('%Y-%m-%d'),
            "total_puntos": len(predicciones),
            "predicciones": predicciones,
            "total_kg_estimado": sum(p['prediccion_kg'] for p in predicciones)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener predicciones por fecha: {str(e)}")
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


@router.post(
    "/train",
    summary="Entrenar modelo LSTM con CSV",
    description="Entrena el modelo LSTM con datos CSV de residuos"
)
async def train_lstm(file: UploadFile = File(...), epochs: int = Query(200, ge=10, le=1000)):
    """
    Entrena el modelo LSTM con un archivo CSV
    
    Parámetros:
    - file: Archivo CSV con columnas 'fecha' y 'residuos_kg'
    - epochs: Número de épocas de entrenamiento (10-1000, default 200)
    
    Retorna:
    - Métricas de evaluación (R², RMSE, MAE, MAPE)
    - Rutas a archivos generados (modelo, gráfico, reporte)
    """
    try:
        from ..lstm.lstm_api_service_v5 import LSTMTrainer
        from pathlib import Path
        
        # Leer contenido del CSV
        content = await file.read()
        
        # Directorio temporal para archivos LSTM
        temp_dir = Path(__file__).parent.parent / "lstm" / "lstm_temp"
        temp_dir.mkdir(exist_ok=True)
        
        # Crear trainer con directorio temporal
        trainer = LSTMTrainer(content, temp_dir=str(temp_dir))
        
        # Preprocesar
        trainer.preprocess()
        
        # Construir modelo
        trainer.build_model()
        
        # Entrenar
        trainer.train(epochs=epochs)
        
        # Evaluar
        trainer.evaluate()
        
        # Predecir futuro
        trainer.predict_future(days_ahead=30)
        
        # Generar gráfico
        graph_path = trainer.generate_graph()
        
        # Guardar modelo
        model_path = trainer.save_model()
        
        # Guardar reporte
        report_path = trainer.save_report()
        
        return {
            "success": True,
            "metrics": trainer.metrics,
            "files": {
                "model": str(model_path),
                "graph": str(graph_path),
                "report": str(report_path)
            },
            "message": "Modelo entrenado exitosamente"
        }
        
    except Exception as e:
        logger.error(f"Error al entrenar modelo: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
