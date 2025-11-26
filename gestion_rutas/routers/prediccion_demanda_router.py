"""
Router para gestionar operaciones CRUD en la tabla PrediccionDemanda.
Endpoints para crear, listar, actualizar y eliminar predicciones de demanda LSTM.
Usando PostgreSQL directo sin SQLAlchemy
"""

from fastapi import APIRouter, HTTPException, Query
from datetime import datetime
from typing import Optional

from ..schemas.schemas import (
    PrediccionDemandaCreate,
    PrediccionDemandaUpdate,
    PrediccionDemandaResponse
)
from ..service.prediccion_demanda_service import PrediccionDemandaService

router = APIRouter(prefix="/predicciones-demanda", tags=["Predicciones de Demanda"])

prediccion_service = PrediccionDemandaService()


@router.get(
    "/",
    response_model=dict,
    summary="Listar todas las predicciones de demanda con paginación y filtros",
    description="Retorna una lista paginada de predicciones LSTM con opciones de filtrado"
)
async def get_predicciones_demanda(
    skip: int = Query(0, ge=0, description="Número de registros a saltar"),
    limit: int = Query(10, ge=1, le=100, description="Número máximo de registros a retornar"),
    id_zona: Optional[int] = Query(None, description="Filtrar por ID de zona"),
    horizonte_horas: Optional[int] = Query(None, description="Filtrar por horizonte de predicción (horas)"),
    fecha_desde: Optional[datetime] = Query(None, description="Filtrar desde esta fecha"),
    fecha_hasta: Optional[datetime] = Query(None, description="Filtrar hasta esta fecha"),
    modelo_version: Optional[str] = Query(None, description="Filtrar por versión del modelo LSTM"),
):
    """
    Obtiene una lista paginada de predicciones de demanda con filtros opcionales.
    
    **Parámetros de filtrado:**
    - `id_zona`: Filtra predicciones por zona específica
    - `horizonte_horas`: Filtra por horizonte de predicción (ej: 24, 48)
    - `fecha_desde`: Filtra predicciones desde una fecha específica
    - `fecha_hasta`: Filtra predicciones hasta una fecha específica
    - `modelo_version`: Filtra por versión del modelo LSTM
    
    **Ejemplo de uso:**
    ```
    GET /predicciones-demanda/?skip=0&limit=10&id_zona=1&horizonte_horas=24
    ```
    """
    try:
        predicciones, total = prediccion_service.obtener_predicciones(
            id_zona=id_zona,
            horizonte_horas=horizonte_horas,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            modelo_version=modelo_version,
            skip=skip,
            limit=limit
        )
        return {
            "data": predicciones,
            "total": total,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar predicciones: {str(e)}")


@router.get(
    "/{prediccion_id}",
    response_model=PrediccionDemandaResponse,
    summary="Obtener una predicción por ID",
    description="Retorna los detalles de una predicción de demanda específica"
)
async def get_prediccion_demanda(prediccion_id: int):
    """
    Obtiene los detalles de una predicción específica por su ID.
    
    **Ejemplo de uso:**
    ```
    GET /predicciones-demanda/1
    ```
    """
    try:
        prediccion = prediccion_service.obtener_prediccion(prediccion_id)
        if not prediccion:
            raise HTTPException(status_code=404, detail=f"Predicción con ID {prediccion_id} no encontrada")
        return prediccion
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener predicción: {str(e)}")


@router.post(
    "/",
    response_model=PrediccionDemandaResponse,
    status_code=201,
    summary="Crear una nueva predicción de demanda",
    description="Crea un nuevo registro de predicción LSTM"
)
async def create_prediccion_demanda(prediccion: PrediccionDemandaCreate):
    """
    Crea un nuevo registro de predicción de demanda.
    
    **Validaciones:**
    - La zona debe existir
    - Horizonte debe ser positivo
    - Valores predichos deben ser positivos
    - Error RMSE y MAPE deben ser no negativos
    
    **Ejemplo de payload:**
    ```json
    {
        "id_zona": 1,
        "horizonte_horas": 24,
        "fecha_prediccion": "2024-01-15T10:30:00",
        "valor_predicho_kg": 2500.5,
        "valor_real_kg": 2450.0,
        "modelo_lstm_version": "v2.0",
        "error_rmse": 125.3,
        "error_mape": 5.2
    }
    ```
    """
    try:
        return prediccion_service.crear_prediccion(prediccion.dict())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear predicción: {str(e)}")


@router.put(
    "/{prediccion_id}",
    response_model=PrediccionDemandaResponse,
    summary="Actualizar una predicción de demanda",
    description="Actualiza los datos de una predicción existente"
)
async def update_prediccion_demanda(
    prediccion_id: int,
    prediccion_data: PrediccionDemandaUpdate,
):
    """
    Actualiza una predicción existente.
    
    **Ejemplo de uso:**
    ```
    PUT /predicciones-demanda/1
    ```
    
    **Ejemplo de payload:**
    ```json
    {
        "valor_real_kg": 2480.0,
        "error_rmse": 118.5,
        "error_mape": 4.8
    }
    ```
    """
    try:
        prediccion = prediccion_service.obtener_prediccion(prediccion_id)
        if not prediccion:
            raise HTTPException(status_code=404, detail=f"Predicción con ID {prediccion_id} no encontrada")
        
        return prediccion_service.actualizar_prediccion(prediccion_id, prediccion_data.dict(exclude_unset=True))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar predicción: {str(e)}")


@router.delete(
    "/{prediccion_id}",
    status_code=204,
    summary="Eliminar una predicción de demanda",
    description="Elimina un registro de predicción de la base de datos"
)
async def delete_prediccion_demanda(prediccion_id: int):
    """
    Elimina un registro de predicción existente.
    
    **Advertencia:** Esta operación no se puede deshacer.
    
    **Ejemplo de uso:**
    ```
    DELETE /predicciones-demanda/1
    ```
    """
    try:
        prediccion = prediccion_service.obtener_prediccion(prediccion_id)
        if not prediccion:
            raise HTTPException(status_code=404, detail=f"Predicción con ID {prediccion_id} no encontrada")
        
        prediccion_service.eliminar_prediccion(prediccion_id)
        return None
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar predicción: {str(e)}")


@router.get(
    "/zona/{id_zona}/ultimas",
    response_model=dict,
    summary="Obtener últimas predicciones por zona",
    description="Retorna las predicciones más recientes para una zona específica"
)
async def get_ultimas_predicciones_zona(
    id_zona: int,
    horizonte_horas: int = Query(24, description="Horizonte de horas a buscar"),
    limite: int = Query(5, ge=1, le=20, description="Número de predicciones a retornar"),
):
    """
    Obtiene las predicciones más recientes para una zona específica.
    
    **Ejemplo de uso:**
    ```
    GET /predicciones-demanda/zona/1/ultimas?horizonte_horas=24&limite=5
    ```
    """
    try:
        return prediccion_service.obtener_ultimas_predicciones_zona(id_zona, horizonte_horas, limite)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener predicciones: {str(e)}")


@router.get(
    "/estadisticas/precision-modelo",
    summary="Obtener estadísticas de precisión por versión de modelo",
    description="Retorna error promedio (RMSE y MAPE) por versión de modelo LSTM"
)
async def get_estadisticas_precision():
    """
    Obtiene estadísticas de precisión agrupadas por versión del modelo.
    
    **Ejemplo de uso:**
    ```
    GET /predicciones-demanda/estadisticas/precision-modelo
    ```
    """
    try:
        return prediccion_service.obtener_estadisticas_precision()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener estadísticas: {str(e)}")


@router.get(
    "/{prediccion_id}",
    response_model=PrediccionDemandaResponse,
    summary="Obtener una predicción por ID",
    description="Retorna los detalles de una predicción de demanda específica"
)
async def get_prediccion_demanda(prediccion_id: int, db: Session = Depends(get_db)):
    """
    Obtiene los detalles de una predicción específica por su ID.
    
    **Ejemplo de uso:**
    ```
    GET /predicciones-demanda/1
    ```
    """
    try:
        prediccion = db.query(PrediccionDemanda).filter(PrediccionDemanda.id_prediccion == prediccion_id).first()
        if not prediccion:
            raise HTTPException(status_code=404, detail=f"Predicción con ID {prediccion_id} no encontrada")
        return PrediccionDemandaResponse.from_orm(prediccion)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener predicción: {str(e)}")


@router.post(
    "/",
    response_model=PrediccionDemandaResponse,
    status_code=201,
    summary="Crear una nueva predicción de demanda",
    description="Crea un nuevo registro de predicción LSTM"
)
async def create_prediccion_demanda(prediccion: PrediccionDemandaCreate, db: Session = Depends(get_db)):
    """
    Crea un nuevo registro de predicción de demanda.
    
    **Validaciones:**
    - La zona debe existir
    - Horizonte debe ser positivo
    - Valores predichos deben ser positivos
    - Error RMSE y MAPE deben ser no negativos
    
    **Ejemplo de payload:**
    ```json
    {
        "id_zona": 1,
        "horizonte_horas": 24,
        "fecha_prediccion": "2024-01-15T10:30:00",
        "valor_predicho_kg": 2500.5,
        "valor_real_kg": 2450.0,
        "modelo_lstm_version": "v2.0",
        "error_rmse": 125.3,
        "error_mape": 5.2
    }
    ```
    """
    try:
        # Validar que la zona existe
        zona = db.query(Zona).filter(Zona.id_zona == prediccion.id_zona).first()
        if not zona:
            raise HTTPException(status_code=400, detail=f"Zona con ID {prediccion.id_zona} no existe")
        
        # Validar horizonte
        if prediccion.horizonte_horas <= 0:
            raise HTTPException(status_code=400, detail="Horizonte de horas debe ser positivo")
        
        # Validar valor predicho
        if prediccion.valor_predicho_kg < 0:
            raise HTTPException(status_code=400, detail="Valor predicho no puede ser negativo")
        
        # Validar valor real si se proporciona
        if prediccion.valor_real_kg and prediccion.valor_real_kg < 0:
            raise HTTPException(status_code=400, detail="Valor real no puede ser negativo")
        
        # Validar errores
        if prediccion.error_rmse and prediccion.error_rmse < 0:
            raise HTTPException(status_code=400, detail="Error RMSE no puede ser negativo")
        
        if prediccion.error_mape and prediccion.error_mape < 0:
            raise HTTPException(status_code=400, detail="Error MAPE no puede ser negativo")
        
        nueva_prediccion = PrediccionDemanda(
            id_zona=prediccion.id_zona,
            horizonte_horas=prediccion.horizonte_horas,
            fecha_prediccion=prediccion.fecha_prediccion,
            valor_predicho_kg=prediccion.valor_predicho_kg,
            valor_real_kg=prediccion.valor_real_kg,
            modelo_lstm_version=prediccion.modelo_lstm_version,
            error_rmse=prediccion.error_rmse,
            error_mape=prediccion.error_mape
        )
        db.add(nueva_prediccion)
        db.commit()
        db.refresh(nueva_prediccion)
        return PrediccionDemandaResponse.from_orm(nueva_prediccion)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al crear predicción: {str(e)}")


@router.put(
    "/{prediccion_id}",
    response_model=PrediccionDemandaResponse,
    summary="Actualizar una predicción de demanda",
    description="Actualiza los datos de una predicción existente"
)
async def update_prediccion_demanda(
    prediccion_id: int,
    prediccion_data: PrediccionDemandaUpdate,
    db: Session = Depends(get_db)
):
    """
    Actualiza una predicción existente.
    
    **Ejemplo de uso:**
    ```
    PUT /predicciones-demanda/1
    ```
    
    **Ejemplo de payload:**
    ```json
    {
        "valor_real_kg": 2480.0,
        "error_rmse": 118.5,
        "error_mape": 4.8
    }
    ```
    """
    try:
        prediccion = db.query(PrediccionDemanda).filter(PrediccionDemanda.id_prediccion == prediccion_id).first()
        if not prediccion:
            raise HTTPException(status_code=404, detail=f"Predicción con ID {prediccion_id} no encontrada")
        
        # Validar valor real si se actualiza
        if prediccion_data.valor_real_kg is not None and prediccion_data.valor_real_kg < 0:
            raise HTTPException(status_code=400, detail="Valor real no puede ser negativo")
        
        # Validar valor predicho si se actualiza
        if prediccion_data.valor_predicho_kg is not None and prediccion_data.valor_predicho_kg < 0:
            raise HTTPException(status_code=400, detail="Valor predicho no puede ser negativo")
        
        # Validar errores si se actualizan
        if prediccion_data.error_rmse is not None and prediccion_data.error_rmse < 0:
            raise HTTPException(status_code=400, detail="Error RMSE no puede ser negativo")
        
        if prediccion_data.error_mape is not None and prediccion_data.error_mape < 0:
            raise HTTPException(status_code=400, detail="Error MAPE no puede ser negativo")
        
        # Actualizar campos
        datos = prediccion_data.dict(exclude_unset=True)
        for campo, valor in datos.items():
            setattr(prediccion, campo, valor)
        
        db.commit()
        db.refresh(prediccion)
        return PrediccionDemandaResponse.from_orm(prediccion)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al actualizar predicción: {str(e)}")


@router.delete(
    "/{prediccion_id}",
    status_code=204,
    summary="Eliminar una predicción de demanda",
    description="Elimina un registro de predicción de la base de datos"
)
async def delete_prediccion_demanda(prediccion_id: int, db: Session = Depends(get_db)):
    """
    Elimina un registro de predicción existente.
    
    **Advertencia:** Esta operación no se puede deshacer.
    
    **Ejemplo de uso:**
    ```
    DELETE /predicciones-demanda/1
    ```
    """
    try:
        prediccion = db.query(PrediccionDemanda).filter(PrediccionDemanda.id_prediccion == prediccion_id).first()
        if not prediccion:
            raise HTTPException(status_code=404, detail=f"Predicción con ID {prediccion_id} no encontrada")
        
        db.delete(prediccion)
        db.commit()
        return None
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al eliminar predicción: {str(e)}")


@router.get(
    "/zona/{id_zona}/ultimas",
    response_model=dict,
    summary="Obtener últimas predicciones por zona",
    description="Retorna las predicciones más recientes para una zona específica"
)
async def get_ultimas_predicciones_zona(
    id_zona: int,
    horizonte_horas: int = Query(24, description="Horizonte de horas a buscar"),
    limite: int = Query(5, ge=1, le=20, description="Número de predicciones a retornar"),
    db: Session = Depends(get_db)
):
    """
    Obtiene las predicciones más recientes para una zona específica.
    
    **Ejemplo de uso:**
    ```
    GET /predicciones-demanda/zona/1/ultimas?horizonte_horas=24&limite=5
    ```
    """
    try:
        # Validar que la zona existe
        zona = db.query(Zona).filter(Zona.id_zona == id_zona).first()
        if not zona:
            raise HTTPException(status_code=404, detail=f"Zona con ID {id_zona} no encontrada")
        
        predicciones = db.query(PrediccionDemanda).filter(
            PrediccionDemanda.id_zona == id_zona,
            PrediccionDemanda.horizonte_horas == horizonte_horas
        ).order_by(PrediccionDemanda.fecha_prediccion.desc()).limit(limite).all()
        
        return {
            "zona_id": id_zona,
            "zona_nombre": zona.nombre,
            "horizonte_horas": horizonte_horas,
            "predicciones": [PrediccionDemandaResponse.from_orm(p) for p in predicciones]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener predicciones: {str(e)}")


@router.get(
    "/estadisticas/precision-modelo",
    summary="Obtener estadísticas de precisión por versión de modelo",
    description="Retorna error promedio (RMSE y MAPE) por versión de modelo LSTM"
)
async def get_estadisticas_precision(db: Session = Depends(get_db)):
    """
    Obtiene estadísticas de precisión agrupadas por versión del modelo.
    
    **Ejemplo de uso:**
    ```
    GET /predicciones-demanda/estadisticas/precision-modelo
    ```
    """
    try:
        estadisticas = db.query(
            PrediccionDemanda.modelo_lstm_version,
            func.count(PrediccionDemanda.id_prediccion).label("cantidad"),
            func.avg(PrediccionDemanda.error_rmse).label("promedio_rmse"),
            func.avg(PrediccionDemanda.error_mape).label("promedio_mape"),
            func.min(PrediccionDemanda.error_rmse).label("min_rmse"),
            func.max(PrediccionDemanda.error_rmse).label("max_rmse")
        ).group_by(PrediccionDemanda.modelo_lstm_version).all()
        
        return {
            "estadisticas": [
                {
                    "modelo_version": modelo,
                    "cantidad_predicciones": cantidad,
                    "promedio_rmse": round(promedio_rmse, 2) if promedio_rmse else None,
                    "promedio_mape": round(promedio_mape, 2) if promedio_mape else None,
                    "rmse_minimo": round(min_rmse, 2) if min_rmse else None,
                    "rmse_maximo": round(max_rmse, 2) if max_rmse else None
                }
                for modelo, cantidad, promedio_rmse, promedio_mape, min_rmse, max_rmse in estadisticas
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener estadísticas: {str(e)}")
