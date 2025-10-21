"""
routers/ruta_planificada_router.py

Endpoints CRUD completos para la tabla RutaPlanificada
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from ..database.db import get_db
from ..models.models import RutaPlanificada
from ..schemas.schemas import RutaPlanificadaCreate, RutaPlanificadaUpdate, RutaPlanificadaResponse
from ..service.ruta_planificada_service import RutaPlanificadaService

router = APIRouter(
    prefix="/rutas-planificadas",
    tags=["Rutas Planificadas"],
)

ruta_service = RutaPlanificadaService()


@router.get("/", response_model=List[RutaPlanificadaResponse], summary="Obtener todas las rutas planificadas")
def get_rutas_planificadas(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    zona_id: Optional[int] = None,
    camion_id: Optional[int] = None,
    estado: Optional[str] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
):
    """
    Obtiene todas las rutas planificadas con paginación y filtros.
    
    **Query Parameters:**
    - `skip`: Número de registros a saltar
    - `limit`: Número máximo de registros
    - `zona_id`: Filtrar por zona
    - `camion_id`: Filtrar por camión asignado
    - `estado`: Filtrar por estado (planificada, en_ejecucion, completada, etc.)
    - `fecha_desde`: Filtrar por fecha inicial (YYYY-MM-DD)
    - `fecha_hasta`: Filtrar por fecha final (YYYY-MM-DD)
    """
    query = db.query(RutaPlanificada)
    
    if zona_id is not None:
        query = query.filter(RutaPlanificada.id_zona == zona_id)
    if camion_id is not None:
        query = query.filter(RutaPlanificada.id_camion == camion_id)
    if estado:
        query = query.filter(RutaPlanificada.estado == estado)
    if fecha_desde:
        query = query.filter(RutaPlanificada.fecha_planificacion >= fecha_desde)
    if fecha_hasta:
        query = query.filter(RutaPlanificada.fecha_planificacion <= fecha_hasta)
    
    rutas = query.offset(skip).limit(limit).all()
    return rutas


@router.get("/{ruta_id}", response_model=RutaPlanificadaResponse, summary="Obtener ruta por ID")
def get_ruta_planificada(ruta_id: int, db: Session = Depends(get_db)):
    """Obtiene una ruta planificada específica."""
    ruta = db.query(RutaPlanificada).filter(RutaPlanificada.id_ruta_planificada == ruta_id).first()
    if not ruta:
        raise HTTPException(status_code=404, detail=f"Ruta con ID {ruta_id} no encontrada")
    return ruta


@router.post("/", response_model=RutaPlanificadaResponse, status_code=201, summary="Crear nueva ruta planificada")
def create_ruta_planificada(ruta: RutaPlanificadaCreate, db: Session = Depends(get_db)):
    """
    Crea una nueva ruta planificada.
    
    **Campos requeridos:**
    - `id_zona`: ID de la zona
    - `fecha_planificacion`: Fecha de planificación (YYYY-MM-DD)
    - `secuencia_puntos`: Lista de IDs de puntos en orden
    
    **Campos opcionales:**
    - `id_camion`: ID del camión asignado
    - `distancia_planificada_km`: Distancia planificada
    - `duracion_estimada_minutos`: Duración estimada
    - `algoritmo_vrp`: Algoritmo usado (default: 2opt)
    """
    db_ruta = RutaPlanificada(**ruta.dict())
    db.add(db_ruta)
    db.commit()
    db.refresh(db_ruta)
    return db_ruta


@router.put("/{ruta_id}", response_model=RutaPlanificadaResponse, summary="Actualizar ruta planificada")
def update_ruta_planificada(ruta_id: int, ruta: RutaPlanificadaUpdate, db: Session = Depends(get_db)):
    """Actualiza una ruta planificada existente."""
    db_ruta = db.query(RutaPlanificada).filter(RutaPlanificada.id_ruta_planificada == ruta_id).first()
    if not db_ruta:
        raise HTTPException(status_code=404, detail=f"Ruta con ID {ruta_id} no encontrada")
    
    update_data = ruta.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_ruta, field, value)
    
    db.add(db_ruta)
    db.commit()
    db.refresh(db_ruta)
    return db_ruta


@router.delete("/{ruta_id}", status_code=204, summary="Eliminar ruta planificada")
def delete_ruta_planificada(ruta_id: int, db: Session = Depends(get_db)):
    """Elimina una ruta planificada."""
    db_ruta = db.query(RutaPlanificada).filter(RutaPlanificada.id_ruta_planificada == ruta_id).first()
    if not db_ruta:
        raise HTTPException(status_code=404, detail=f"Ruta con ID {ruta_id} no encontrada")
    
    db.delete(db_ruta)
    db.commit()
    return None


@router.patch("/{ruta_id}/estado", response_model=RutaPlanificadaResponse, summary="Cambiar estado de ruta")
def update_estado_ruta(
    ruta_id: int,
    nuevo_estado: str = Query(..., description="Nuevo estado"),
    db: Session = Depends(get_db),
):
    """
    Actualiza el estado de una ruta planificada.
    
    **Estados válidos:**
    - `planificada`: Recién creada
    - `en_ejecucion`: En progreso
    - `completada`: Finalizada
    - `cancelada`: Cancelada
    """
    db_ruta = db.query(RutaPlanificada).filter(RutaPlanificada.id_ruta_planificada == ruta_id).first()
    if not db_ruta:
        raise HTTPException(status_code=404, detail=f"Ruta con ID {ruta_id} no encontrada")
    
    estados_validos = ["planificada", "en_ejecucion", "completada", "cancelada"]
    if nuevo_estado not in estados_validos:
        raise HTTPException(
            status_code=400,
            detail=f"Estado inválido. Válidos: {', '.join(estados_validos)}"
        )
    
    db_ruta.estado = nuevo_estado
    db.add(db_ruta)
    db.commit()
    db.refresh(db_ruta)
    return db_ruta


@router.get("/{ruta_id}/detalles", summary="Obtener detalles completos de ruta")
def get_detalles_ruta(ruta_id: int, db: Session = Depends(get_db)):
    """
    Obtiene detalles completos de una ruta incluyendo zona, camión y puntos.
    """
    ruta = db.query(RutaPlanificada).filter(RutaPlanificada.id_ruta_planificada == ruta_id).first()
    if not ruta:
        raise HTTPException(status_code=404, detail=f"Ruta con ID {ruta_id} no encontrada")
    
    return {
        "ruta_id": ruta_id,
        "zona": {"id": ruta.id_zona, "nombre": ruta.zona.nombre if ruta.zona else None},
        "camion": {"id": ruta.id_camion, "numero": ruta.camion.numero_interno if ruta.camion else None},
        "estado": ruta.estado,
        "fecha_planificacion": ruta.fecha_planificacion,
        "distancia_km": ruta.distancia_planificada_km,
        "duracion_minutos": ruta.duracion_estimada_minutos,
        "algoritmo": ruta.algoritmo_vrp,
        "secuencia_puntos": ruta.secuencia_puntos,
    }
