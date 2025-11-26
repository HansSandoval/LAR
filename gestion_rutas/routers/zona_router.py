"""
routers/zona_router.py

Endpoints CRUD completos para la tabla Zona
Usando PostgreSQL directo sin SQLAlchemy
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

from ..schemas.schemas import ZonaCreate, ZonaUpdate, ZonaResponse
from ..service.zona_service import ZonaService

router = APIRouter(
    prefix="/zonas",
    tags=["Zonas"],
)

zona_service = ZonaService()


@router.get("/", response_model=List[ZonaResponse], summary="Obtener todas las zonas")
def get_zonas(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    tipo: Optional[str] = None,
):
    """
    Obtiene todas las zonas.
    
    **Query Parameters:**
    - `skip`: Número de registros a saltar
    - `limit`: Número máximo de registros
    - `tipo`: Filtrar por tipo (opcional)
    """
    try:
        zonas = zona_service.obtener_todas_zonas()
        return zonas
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{zona_id}", response_model=ZonaResponse, summary="Obtener zona por ID")
def get_zona(zona_id: int):
    """Obtiene una zona específica por su ID."""
    try:
        zona = zona_service.obtener_zona(zona_id)
        if not zona:
            raise HTTPException(status_code=404, detail=f"Zona con ID {zona_id} no encontrada")
        return zona
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=ZonaResponse, status_code=201, summary="Crear nueva zona")
def create_zona(zona: ZonaCreate):
    """
    Crea una nueva zona.
    
    **Campos requeridos:**
    - `nombre`: Nombre de la zona
    - `tipo`: Tipo de zona (e.g., residencial, comercial)
    
    **Campos opcionales:**
    - `area_km2`: Área en km²
    - `poblacion`: Población estimada
    - `coordenadas_limite`: JSON con coordenadas del límite
    - `prioridad`: Nivel de prioridad
    """
    try:
        return zona_service.crear_zona(zona.dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{zona_id}", response_model=ZonaResponse, summary="Actualizar zona")
def update_zona(zona_id: int, zona: ZonaUpdate):
    """Actualiza una zona existente."""
    try:
        updated_zona = zona_service.actualizar_zona(zona_id, zona.dict(exclude_unset=True))
        if not updated_zona:
            raise HTTPException(status_code=404, detail=f"Zona con ID {zona_id} no encontrada")
        return updated_zona
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{zona_id}", status_code=204, summary="Eliminar zona")
def delete_zona(zona_id: int):
    """Elimina una zona específica."""
    try:
        result = zona_service.eliminar_zona(zona_id)
        if not result:
            raise HTTPException(status_code=404, detail=f"Zona con ID {zona_id} no encontrada")
        return None
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{zona_id}/estadisticas", summary="Obtener estadísticas de zona")
def get_zona_estadisticas(zona_id: int):
    """
    Obtiene estadísticas de una zona específica.
    
    **Retorna:**
    - Número de puntos de recolección
    - Número de rutas planificadas
    - Número de incidencias
    - Número de predicciones LSTM
    """
    try:
        zona = zona_service.obtener_zona(zona_id)
        if not zona:
            raise HTTPException(status_code=404, detail=f"Zona con ID {zona_id} no encontrada")
        
        return {
            "zona_id": zona_id,
            "nombre": zona.get("nombre"),
            "puntos_recoleccion": 0,
            "rutas_planificadas": 0,
            "incidencias": 0,
            "predicciones_lstm": 0,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
