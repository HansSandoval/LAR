"""
routers/punto_router.py

Endpoints CRUD completos para la tabla PuntoRecoleccion
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from ..database.db import get_db
from ..models.models import PuntoRecoleccion
from ..schemas.schemas import PuntoRecoleccionCreate, PuntoRecoleccionUpdate, PuntoRecoleccionResponse
from ..service.punto_service import PuntoService

router = APIRouter(
    prefix="/puntos",
    tags=["Puntos de Recolección"],
)

punto_service = PuntoService()


@router.get("/", response_model=List[PuntoRecoleccionResponse], summary="Obtener todos los puntos")
def get_puntos(
    db: Session = Depends(get_db),
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
    query = db.query(PuntoRecoleccion)
    
    if zona_id is not None:
        query = query.filter(PuntoRecoleccion.id_zona == zona_id)
    if tipo:
        query = query.filter(PuntoRecoleccion.tipo == tipo)
    if estado:
        query = query.filter(PuntoRecoleccion.estado == estado)
    
    puntos = query.offset(skip).limit(limit).all()
    return puntos


@router.get("/{punto_id}", response_model=PuntoRecoleccionResponse, summary="Obtener punto por ID")
def get_punto(punto_id: int, db: Session = Depends(get_db)):
    """Obtiene un punto de recolección específico."""
    punto = db.query(PuntoRecoleccion).filter(PuntoRecoleccion.id_punto == punto_id).first()
    if not punto:
        raise HTTPException(status_code=404, detail=f"Punto con ID {punto_id} no encontrado")
    return punto


@router.post("/", response_model=PuntoRecoleccionResponse, status_code=201, summary="Crear nuevo punto")
def create_punto(punto: PuntoRecoleccionCreate, db: Session = Depends(get_db)):
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
    db_punto = PuntoRecoleccion(**punto.dict())
    db.add(db_punto)
    db.commit()
    db.refresh(db_punto)
    return db_punto


@router.put("/{punto_id}", response_model=PuntoRecoleccionResponse, summary="Actualizar punto")
def update_punto(punto_id: int, punto: PuntoRecoleccionUpdate, db: Session = Depends(get_db)):
    """Actualiza un punto de recolección existente."""
    db_punto = db.query(PuntoRecoleccion).filter(PuntoRecoleccion.id_punto == punto_id).first()
    if not db_punto:
        raise HTTPException(status_code=404, detail=f"Punto con ID {punto_id} no encontrado")
    
    update_data = punto.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_punto, field, value)
    
    db.add(db_punto)
    db.commit()
    db.refresh(db_punto)
    return db_punto


@router.delete("/{punto_id}", status_code=204, summary="Eliminar punto")
def delete_punto(punto_id: int, db: Session = Depends(get_db)):
    """Elimina un punto de recolección."""
    db_punto = db.query(PuntoRecoleccion).filter(PuntoRecoleccion.id_punto == punto_id).first()
    if not db_punto:
        raise HTTPException(status_code=404, detail=f"Punto con ID {punto_id} no encontrado")
    
    db.delete(db_punto)
    db.commit()
    return None


@router.get("/{punto_id}/proximidad", summary="Obtener puntos cercanos")
def get_puntos_proximidad(
    punto_id: int,
    radio_km: float = Query(5.0, gt=0),
    db: Session = Depends(get_db),
):
    """
    Obtiene puntos de recolección cercanos a un punto específico.
    
    **Query Parameters:**
    - `radio_km`: Radio de búsqueda en km (default: 5.0)
    
    **Calcula distancia euclidiana entre coordenadas.**
    """
    punto = db.query(PuntoRecoleccion).filter(PuntoRecoleccion.id_punto == punto_id).first()
    if not punto:
        raise HTTPException(status_code=404, detail=f"Punto con ID {punto_id} no encontrado")
    
    # Convertir radio de km a grados (aproximación)
    radio_grados = radio_km / 111  # 1 grado ≈ 111 km
    
    puntos_cercanos = db.query(PuntoRecoleccion).filter(
        (PuntoRecoleccion.latitud.between(punto.latitud - radio_grados, punto.latitud + radio_grados)) &
        (PuntoRecoleccion.longitud.between(punto.longitud - radio_grados, punto.longitud + radio_grados)) &
        (PuntoRecoleccion.id_punto != punto_id)
    ).all()
    
    return {
        "punto_referencia": punto_id,
        "radio_km": radio_km,
        "puntos_encontrados": len(puntos_cercanos),
        "puntos": puntos_cercanos,
    }
