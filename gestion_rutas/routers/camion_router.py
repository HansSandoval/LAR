"""
routers/camion_router.py

Endpoints CRUD completos para la tabla Camion - PostgreSQL Directo
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

from ..schemas.schemas import CamionCreate, CamionUpdate, CamionResponse
from ..service.camion_service import CamionService

router = APIRouter(
    prefix="/camiones",
    tags=["Vehículos"],
)


@router.get("/", response_model=List[CamionResponse], summary="Obtener todos los camiones")
def get_camiones(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    estado: Optional[str] = None,
):
    """
    Obtiene todos los camiones con paginación y filtros.
    
    **Query Parameters:**
    - `skip`: Número de registros a saltar
    - `limit`: Número máximo de registros
    - `estado`: Filtrar por estado (disponible, en_servicio, mantenimiento, etc.)
    """
    try:
        camiones, total = CamionService.obtener_camiones(estado=estado, skip=skip, limit=limit)
        return camiones
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{camion_id}", response_model=CamionResponse, summary="Obtener camión por ID")
def get_camion(camion_id: int):
    """Obtiene un camión específico por su ID."""
    try:
        camion = CamionService.obtener_camion(camion_id)
        if not camion:
            raise HTTPException(status_code=404, detail=f"Camión con ID {camion_id} no encontrado")
        return camion
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=CamionResponse, status_code=201, summary="Crear nuevo camión")
def create_camion(camion: CamionCreate):
    """
    Crea un nuevo camión.
    
    **Campos requeridos:**
    - `patente`: Patente del vehículo
    - `capacidad_kg`: Capacidad de carga en kg
    - `tipo_combustible`: Tipo de combustible
    """
    try:
        nuevo_camion = CamionService.crear_camion(
            patente=camion.patente,
            capacidad_kg=camion.capacidad_kg,
            consumo_km_l=camion.consumo_km_l,
            tipo_combustible=camion.tipo_combustible,
            gps_id=camion.gps_id
        )
        if not nuevo_camion:
            raise HTTPException(status_code=500, detail="Error al crear camión")
        return nuevo_camion
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{camion_id}", response_model=CamionResponse, summary="Actualizar camión")
def update_camion(camion_id: int, camion: CamionUpdate):
    """Actualiza un camión existente."""
    try:
        camion_existente = CamionService.obtener_camion(camion_id)
        if not camion_existente:
            raise HTTPException(status_code=404, detail=f"Camión con ID {camion_id} no encontrado")
        
        datos_actualizados = {k: v for k, v in camion.dict(exclude_unset=True).items() if v is not None}
        resultado = CamionService.actualizar_camion(camion_id, datos_actualizados)
        
        if not resultado:
            raise HTTPException(status_code=500, detail="Error al actualizar camión")
        return resultado
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{camion_id}", status_code=204, summary="Eliminar camión")
def delete_camion(camion_id: int):
    """Elimina un camión."""
    try:
        camion = CamionService.obtener_camion(camion_id)
        if not camion:
            raise HTTPException(status_code=404, detail=f"Camión con ID {camion_id} no encontrado")
        
        exito = CamionService.eliminar_camion(camion_id)
        if not exito:
            raise HTTPException(status_code=500, detail="Error al eliminar camión")
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{camion_id}/estado", response_model=CamionResponse, summary="Cambiar estado del camión")
def update_estado_camion(
    camion_id: int,
    nuevo_estado: str = Query(..., description="Nuevo estado: disponible, en_servicio, mantenimiento"),
):
    """
    Actualiza el estado de un camión.
    
    **Estados válidos:**
    - `disponible`: Listo para asignación
    - `en_servicio`: Ejecutando ruta
    - `mantenimiento`: En mantenimiento
    """
    try:
        camion = CamionService.obtener_camion(camion_id)
        if not camion:
            raise HTTPException(status_code=404, detail=f"Camión con ID {camion_id} no encontrado")
        
        estados_validos = ["disponible", "en_servicio", "mantenimiento"]
        if nuevo_estado not in estados_validos:
            raise HTTPException(
                status_code=400, 
                detail=f"Estado inválido. Válidos: {', '.join(estados_validos)}"
            )
        
        resultado = CamionService.cambiar_estado_camion(camion_id, nuevo_estado)
        if not resultado:
            raise HTTPException(status_code=500, detail="Error al actualizar estado")
        return resultado
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{camion_id}/estadisticas", summary="Obtener estadísticas del camión")
def get_estadisticas_camion(camion_id: int):
    """
    Obtiene estadísticas de un camión.
    
    **Retorna:**
    - Número de rutas asignadas
    - Distancia total recorrida
    - Carga promedio utilizada
    - Estado actual
    """
    try:
        camion = CamionService.obtener_camion(camion_id)
        if not camion:
            raise HTTPException(status_code=404, detail=f"Camión con ID {camion_id} no encontrado")
        
        metricas = CamionService.calcular_metricas_camion(camion_id)
        return metricas
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
