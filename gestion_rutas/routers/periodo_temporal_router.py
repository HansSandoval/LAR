"""
Router para gestionar operaciones CRUD en la tabla PeriodoTemporal.
Endpoints para crear, listar, actualizar y eliminar periodos temporales.
Usando PostgreSQL directo sin SQLAlchemy
"""

from fastapi import APIRouter, HTTPException, Query
from datetime import datetime
from typing import Optional

from ..schemas.schemas import (
    PeriodoTemporalCreate,
    PeriodoTemporalUpdate,
    PeriodoTemporalResponse
)
from ..service.periodo_temporal_service import PeriodoTemporalService

router = APIRouter(prefix="/periodos-temporales", tags=["Periodos Temporales"])

periodo_service = PeriodoTemporalService()


@router.get(
    "/",
    response_model=dict,
    summary="Listar todos los periodos temporales con paginación y filtros",
    description="Retorna una lista paginada de periodos temporales"
)
async def get_periodos_temporales(
    skip: int = Query(0, ge=0, description="Número de registros a saltar"),
    limit: int = Query(10, ge=1, le=100, description="Número máximo de registros a retornar"),
    tipo_granularidad: Optional[str] = Query(None, description="Filtrar por granularidad (diario, semanal, mensual, anual)"),
    estacionalidad: Optional[str] = Query(None, description="Filtrar por estacionalidad (verano, invierno, primavera, otoño, general)"),
):
    """
    Obtiene una lista paginada de periodos temporales con filtros opcionales.
    
    **Parámetros de filtrado:**
    - `tipo_granularidad`: Filtra por granularidad temporal (diario, semanal, mensual, anual)
    - `estacionalidad`: Filtra por estacionalidad (verano, invierno, primavera, otoño, general)
    
    **Ejemplo de uso:**
    ```
    GET /periodos-temporales/?skip=0&limit=10&tipo_granularidad=mensual
    ```
    """
    try:
        periodos, total = periodo_service.obtener_periodos(tipo_granularidad, estacionalidad, skip, limit)
        return {
            "data": periodos,
            "total": total,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar periodos temporales: {str(e)}")


@router.get(
    "/{periodo_id}",
    response_model=PeriodoTemporalResponse,
    summary="Obtener un periodo temporal por ID",
    description="Retorna los detalles de un periodo temporal específico"
)
async def get_periodo_temporal(periodo_id: int):
    """
    Obtiene los detalles de un periodo temporal específico por su ID.
    
    **Ejemplo de uso:**
    ```
    GET /periodos-temporales/1
    ```
    """
    try:
        periodo = periodo_service.obtener_periodo(periodo_id)
        if not periodo:
            raise HTTPException(status_code=404, detail=f"Periodo temporal con ID {periodo_id} no encontrado")
        return periodo
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener periodo temporal: {str(e)}")


@router.post(
    "/",
    response_model=PeriodoTemporalResponse,
    status_code=201,
    summary="Crear un nuevo periodo temporal",
    description="Crea un nuevo registro de periodo temporal"
)
async def create_periodo_temporal(periodo: PeriodoTemporalCreate):
    """
    Crea un nuevo periodo temporal.
    
    **Validaciones:**
    - La fecha de inicio debe ser menor que la fecha de fin
    - El tipo de granularidad debe ser válido
    
    **Tipos de granularidad válidos:** diario, semanal, mensual, anual
    **Estacionalidades válidas:** verano, invierno, primavera, otoño, general
    
    **Ejemplo de payload:**
    ```json
    {
        "fecha_inicio": "2024-01-01T00:00:00",
        "fecha_fin": "2024-01-31T23:59:59",
        "tipo_granularidad": "diario",
        "estacionalidad": "verano"
    }
    ```
    """
    try:
        return periodo_service.crear_periodo(periodo.dict())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear periodo temporal: {str(e)}")


@router.put(
    "/{periodo_id}",
    response_model=PeriodoTemporalResponse,
    summary="Actualizar un periodo temporal",
    description="Actualiza los datos de un periodo temporal existente"
)
async def update_periodo_temporal(
    periodo_id: int,
    periodo_data: PeriodoTemporalUpdate,
):
    """
    Actualiza un periodo temporal existente.
    
    **Ejemplo de uso:**
    ```
    PUT /periodos-temporales/1
    ```
    
    **Ejemplo de payload:**
    ```json
    {
        "estacionalidad": "invierno",
        "fecha_fin": "2024-02-29T23:59:59"
    }
    ```
    """
    try:
        periodo = periodo_service.obtener_periodo(periodo_id)
        if not periodo:
            raise HTTPException(status_code=404, detail=f"Periodo temporal con ID {periodo_id} no encontrado")
        
        return periodo_service.actualizar_periodo(periodo_id, periodo_data.dict(exclude_unset=True))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar periodo temporal: {str(e)}")


@router.delete(
    "/{periodo_id}",
    status_code=204,
    summary="Eliminar un periodo temporal",
    description="Elimina un periodo temporal de la base de datos"
)
async def delete_periodo_temporal(periodo_id: int):
    """
    Elimina un periodo temporal existente.
    
    **Advertencia:** Esta operación no se puede deshacer.
    
    **Ejemplo de uso:**
    ```
    DELETE /periodos-temporales/1
    ```
    """
    try:
        resultado = periodo_service.eliminar_periodo(periodo_id)
        if not resultado:
            raise HTTPException(status_code=404, detail=f"Periodo temporal con ID {periodo_id} no encontrado")
        return None
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar periodo temporal: {str(e)}")


@router.get(
    "/activos/en-rango",
    response_model=dict,
    summary="Obtener periodos activos en un rango de fechas",
    description="Retorna periodos temporales que se solapan con el rango especificado"
)
async def get_periodos_activos(
    fecha_inicio: datetime = Query(..., description="Fecha inicio del rango"),
    fecha_fin: datetime = Query(..., description="Fecha fin del rango"),
):
    """
    Obtiene los periodos que están activos en un rango de fechas específico.
    
    Un periodo se considera activo si se solapa con el rango especificado.
    
    **Ejemplo de uso:**
    ```
    GET /periodos-temporales/activos/en-rango?fecha_inicio=2024-01-01T00:00:00&fecha_fin=2024-01-31T23:59:59
    ```
    """
    try:
        if fecha_inicio >= fecha_fin:
            raise HTTPException(status_code=400, detail="Fecha inicio debe ser menor que fecha fin")
        
        periodos = periodo_service.obtener_periodos_activos(fecha_inicio, fecha_fin)
        
        return {
            "rango_consultado": {
                "fecha_inicio": fecha_inicio,
                "fecha_fin": fecha_fin
            },
            "periodos_activos": periodos,
            "cantidad": len(periodos)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener periodos activos: {str(e)}")


@router.get(
    "/por-estacionalidad/{estacionalidad}",
    response_model=dict,
    summary="Obtener periodos por estacionalidad",
    description="Retorna todos los periodos de una estacionalidad específica"
)
async def get_periodos_por_estacionalidad(
    estacionalidad: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
):
    """
    Obtiene todos los periodos de una estacionalidad específica.
    
    **Estacionalidades válidas:** verano, invierno, primavera, otoño, general
    
    **Ejemplo de uso:**
    ```
    GET /periodos-temporales/por-estacionalidad/verano?skip=0&limit=10
    ```
    """
    try:
        periodos, total = periodo_service.obtener_periodos_por_estacionalidad(estacionalidad, skip, limit)
        
        return {
            "estacionalidad": estacionalidad,
            "data": periodos,
            "total": total,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{periodo_id}", summary="Eliminar periodo temporal")
def delete_periodo_temporal(periodo_id: int):
    """
    Elimina un periodo temporal existente.
    
    **Advertencia:** Esta operación no se puede deshacer.
    
    **Ejemplo de uso:**
    ```
    DELETE /periodos-temporales/1
    ```
    """
    try:
        success = periodo_service.eliminar_periodo(periodo_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Periodo temporal con ID {periodo_id} no encontrado")
        return {"mensaje": f"Periodo {periodo_id} eliminado exitosamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/activos/en-rango",
    response_model=dict,
    summary="Obtener periodos activos en un rango de fechas",
    description="Retorna periodos temporales que se solapan con el rango especificado"
)
def get_periodos_activos(
    fecha_inicio: str = Query(..., description="Fecha inicio del rango (YYYY-MM-DD)"),
    fecha_fin: str = Query(..., description="Fecha fin del rango (YYYY-MM-DD)")
):
    """
    Obtiene los periodos que están activos en un rango de fechas específico.
    
    Un periodo se considera activo si se solapa con el rango especificado.
    
    **Ejemplo de uso:**
    ```
    GET /periodos-temporales/activos/en-rango?fecha_inicio=2024-01-01&fecha_fin=2024-01-31
    ```
    """
    try:
        from datetime import datetime
        f_inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d")
        f_fin = datetime.strptime(fecha_fin, "%Y-%m-%d")
        
        if f_inicio >= f_fin:
            raise HTTPException(status_code=400, detail="Fecha inicio debe ser menor que fecha fin")
        
        periodos = periodo_service.obtener_periodos_por_rango(f_inicio, f_fin)
        
        return {
            "rango_consultado": {
                "fecha_inicio": fecha_inicio,
                "fecha_fin": fecha_fin
            },
            "periodos_activos": periodos,
            "cantidad": len(periodos)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
