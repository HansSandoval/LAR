"""
routers/ruta_planificada_router.py

Endpoints CRUD completos para la tabla RutaPlanificada
Usando PostgreSQL directo sin SQLAlchemy
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import date

from ..schemas.schemas import RutaPlanificadaCreate, RutaPlanificadaUpdate, RutaPlanificadaResponse
from ..service.ruta_planificada_service import RutaPlanificadaService

router = APIRouter(
    prefix="/rutas-planificadas",
    tags=["Rutas Planificadas"],
)

ruta_service = RutaPlanificadaService()


@router.get("/", response_model=List[RutaPlanificadaResponse], summary="Obtener todas las rutas planificadas")
def get_rutas_planificadas(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    zona_id: Optional[int] = None,
    turno_id: Optional[int] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
):
    """
    Obtiene todas las rutas planificadas con paginación y filtros.
    
    **Query Parameters:**
    - `skip`: Número de registros a saltar
    - `limit`: Número máximo de registros
    - `zona_id`: Filtrar por zona
    - `turno_id`: Filtrar por turno
    - `fecha_desde`: Filtrar por fecha inicial (YYYY-MM-DD)
    - `fecha_hasta`: Filtrar por fecha final (YYYY-MM-DD)
    """
    try:
        rutas, total = ruta_service.obtener_rutas(
            zona_id=zona_id,
            turno_id=turno_id,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            skip=skip,
            limit=limit
        )
        return rutas
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{ruta_id}", response_model=RutaPlanificadaResponse, summary="Obtener ruta por ID")
def get_ruta_planificada(ruta_id: int):
    """Obtiene una ruta planificada específica."""
    try:
        ruta = ruta_service.obtener_ruta(ruta_id)
        if not ruta:
            raise HTTPException(status_code=404, detail=f"Ruta con ID {ruta_id} no encontrada")
        return ruta
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=RutaPlanificadaResponse, status_code=201, summary="Crear nueva ruta planificada")
def create_ruta_planificada(ruta: RutaPlanificadaCreate):
    """
    Crea una nueva ruta planificada.
    
    **Campos requeridos:**
    - `id_zona`: ID de la zona
    - `id_turno`: ID del turno
    - `fecha`: Fecha de planificación (YYYY-MM-DD)
    - `secuencia_puntos`: Lista de IDs de puntos en orden
    """
    try:
        nueva_ruta = ruta_service.crear_ruta(
            id_zona=ruta.id_zona,
            id_turno=ruta.id_turno,
            fecha=ruta.fecha,
            secuencia_puntos=ruta.secuencia_puntos,
            distancia_km=ruta.distancia_km,
            duracion_min=ruta.tiempo_estimado_min
        )
        return nueva_ruta
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{ruta_id}", response_model=RutaPlanificadaResponse, summary="Actualizar ruta planificada")
def update_ruta_planificada(ruta_id: int, ruta: RutaPlanificadaUpdate):
    """Actualiza una ruta planificada existente."""
    try:
        datos = {k: v for k, v in ruta.dict().items() if v is not None}
        if not datos:
            raise HTTPException(status_code=400, detail="No hay campos para actualizar")
        
        ruta_actualizada = ruta_service.actualizar_ruta(ruta_id, **datos)
        if not ruta_actualizada:
            raise HTTPException(status_code=404, detail=f"Ruta con ID {ruta_id} no encontrada")
        return ruta_actualizada
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{ruta_id}", summary="Eliminar ruta planificada")
def delete_ruta_planificada(ruta_id: int):
    """Elimina una ruta planificada existente."""
    try:
        success = ruta_service.eliminar_ruta(ruta_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Ruta con ID {ruta_id} no encontrada")
        return {"mensaje": f"Ruta {ruta_id} eliminada exitosamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/proximas", response_model=List[RutaPlanificadaResponse], summary="Obtener rutas próximas")
def get_rutas_proximas(dias: int = Query(7, description="Días hacia el futuro")):
    """Obtiene las rutas planificadas para los próximos N días."""
    try:
        rutas = ruta_service.obtener_rutas_proximas(dias)
        return rutas
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{ruta_id}/detalles", summary="Obtener detalles completos de ruta")
def get_detalles_ruta(ruta_id: int):
    """Obtiene detalles completos de una ruta incluyendo zona y puntos."""
    try:
        ruta = ruta_service.obtener_ruta(ruta_id)
        if not ruta:
            raise HTTPException(status_code=404, detail=f"Ruta con ID {ruta_id} no encontrada")
        
        metricas = ruta_service.calcular_metricas_ruta(ruta_id)
        return {
            **ruta,
            "metricas": metricas
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
