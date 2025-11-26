"""
routers/punto_router.py

Endpoints CRUD completos para la tabla PuntoRecoleccion
Usando PostgreSQL directo sin SQLAlchemy
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

from ..schemas.schemas import PuntoRecoleccionCreate, PuntoRecoleccionUpdate, PuntoRecoleccionResponse
from ..service.punto_service import PuntoService

router = APIRouter(
    prefix="/puntos",
    tags=["Puntos de Recolección"],
)

punto_service = PuntoService()


@router.get("/", response_model=List[PuntoRecoleccionResponse], summary="Obtener todos los puntos")
def get_puntos(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    zona_id: Optional[int] = None,
    tipo: Optional[str] = None,
    estado: Optional[str] = None,
):
    """
    Obtiene todos los puntos de recolección con paginación y filtros.
    
    **Query Parameters:**
    - `skip`: Número de registros a saltar
    - `limit`: Número máximo de registros
    - `zona_id`: Filtrar por zona específica
    - `tipo`: Filtrar por tipo (residencial, comercial, etc.)
    - `estado`: Filtrar por estado (activo, inactivo, etc.)
    """
    try:
        puntos, total = punto_service.obtener_puntos(tipo_punto=tipo, estado_activo=(estado == 'activo') if estado else None, skip=skip, limit=limit)
        return puntos
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{punto_id}", response_model=PuntoRecoleccionResponse, summary="Obtener punto por ID")
def get_punto(punto_id: int):
    """Obtiene un punto de recolección específico."""
    try:
        punto = punto_service.obtener_punto(punto_id)
        if not punto:
            raise HTTPException(status_code=404, detail=f"Punto con ID {punto_id} no encontrado")
        return punto
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=PuntoRecoleccionResponse, status_code=201, summary="Crear nuevo punto")
def create_punto(punto: PuntoRecoleccionCreate):
    """
    Crea un nuevo punto de recolección.
    
    **Campos requeridos:**
    - `id_zona`: ID de la zona
    - `nombre`: Nombre del punto
    - `latitud`: Coordenada de latitud
    - `longitud`: Coordenada de longitud
    
    **Campos opcionales:**
    - `tipo`: Tipo de punto (residencial, comercial, etc.)
    - `capacidad_kg`: Capacidad máxima en kg
    - `estado`: Estado del punto (activo, inactivo, etc.)
    """
    try:
        return punto_service.crear_punto(punto.dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{punto_id}", response_model=PuntoRecoleccionResponse, summary="Actualizar punto")
def update_punto(punto_id: int, punto: PuntoRecoleccionUpdate):
    """Actualiza un punto de recolección existente."""
    try:
        updated_punto = punto_service.actualizar_punto(punto_id, punto.dict(exclude_unset=True))
        if not updated_punto:
            raise HTTPException(status_code=404, detail=f"Punto con ID {punto_id} no encontrado")
        return updated_punto
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{punto_id}", status_code=204, summary="Eliminar punto")
def delete_punto(punto_id: int):
    """Elimina un punto de recolección."""
    try:
        result = punto_service.eliminar_punto(punto_id)
        if not result:
            raise HTTPException(status_code=404, detail=f"Punto con ID {punto_id} no encontrado")
        return None
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{punto_id}/proximidad", summary="Obtener puntos cercanos")
def get_puntos_proximidad(
    punto_id: int,
    radio_km: float = Query(5.0, gt=0),
):
    """
    Obtiene puntos de recolección cercanos a un punto específico.
    
    **Query Parameters:**
    - `radio_km`: Radio de búsqueda en km (default: 5.0)
    
    **Calcula distancia euclidiana entre coordenadas.**
    """
    try:
        punto = punto_service.obtener_punto(punto_id)
        if not punto:
            raise HTTPException(status_code=404, detail=f"Punto con ID {punto_id} no encontrado")
        
        puntos_cercanos = punto_service.obtener_puntos_cercanos(
            punto['latitud'],
            punto['longitud'],
            radio_km
        )
        
        return {
            "punto_referencia": punto_id,
            "radio_km": radio_km,
            "puntos_encontrados": len(puntos_cercanos),
            "puntos": puntos_cercanos,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
