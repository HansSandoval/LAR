"""
routers/zona_router.py

Endpoints CRUD completos para la tabla Zona
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from ..database.db import get_db
from ..models.models import Zona
from ..schemas.schemas import ZonaCreate, ZonaUpdate, ZonaResponse
from ..service.zona_service import ZonaService

router = APIRouter(
    prefix="/zonas",
    tags=["Zonas"],
)

zona_service = ZonaService()


@router.get("/", response_model=List[ZonaResponse], summary="Obtener todas las zonas")
def get_zonas(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    tipo: Optional[str] = None,
    nombre: Optional[str] = None,
):
    """
    Obtiene todas las zonas con paginación y filtros opcionales.
    
    **Query Parameters:**
    - `skip`: Número de registros a saltar (default: 0)
    - `limit`: Número máximo de registros a retornar (default: 10, máx: 100)
    - `tipo`: Filtrar por tipo de zona (opcional)
    - `nombre`: Filtrar por nombre (búsqueda parcial, opcional)
    """
    query = db.query(Zona)
    
    if tipo:
        query = query.filter(Zona.tipo == tipo)
    if nombre:
        query = query.filter(Zona.nombre.ilike(f"%{nombre}%"))
    
    zonas = query.offset(skip).limit(limit).all()
    return zonas


@router.get("/{zona_id}", response_model=ZonaResponse, summary="Obtener zona por ID")
def get_zona(zona_id: int, db: Session = Depends(get_db)):
    """Obtiene una zona específica por su ID."""
    zona = db.query(Zona).filter(Zona.id_zona == zona_id).first()
    if not zona:
        raise HTTPException(status_code=404, detail=f"Zona con ID {zona_id} no encontrada")
    return zona


@router.post("/", response_model=ZonaResponse, status_code=201, summary="Crear nueva zona")
def create_zona(zona: ZonaCreate, db: Session = Depends(get_db)):
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
    db_zona = Zona(**zona.dict())
    db.add(db_zona)
    db.commit()
    db.refresh(db_zona)
    return db_zona


@router.put("/{zona_id}", response_model=ZonaResponse, summary="Actualizar zona")
def update_zona(zona_id: int, zona: ZonaUpdate, db: Session = Depends(get_db)):
    """Actualiza una zona existente."""
    db_zona = db.query(Zona).filter(Zona.id_zona == zona_id).first()
    if not db_zona:
        raise HTTPException(status_code=404, detail=f"Zona con ID {zona_id} no encontrada")
    
    update_data = zona.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_zona, field, value)
    
    db.add(db_zona)
    db.commit()
    db.refresh(db_zona)
    return db_zona


@router.delete("/{zona_id}", status_code=204, summary="Eliminar zona")
def delete_zona(zona_id: int, db: Session = Depends(get_db)):
    """Elimina una zona específica."""
    db_zona = db.query(Zona).filter(Zona.id_zona == zona_id).first()
    if not db_zona:
        raise HTTPException(status_code=404, detail=f"Zona con ID {zona_id} no encontrada")
    
    db.delete(db_zona)
    db.commit()
    return None


@router.get("/{zona_id}/estadisticas", summary="Obtener estadísticas de zona")
def get_zona_estadisticas(zona_id: int, db: Session = Depends(get_db)):
    """
    Obtiene estadísticas de una zona específica.
    
    **Retorna:**
    - Número de puntos de recolección
    - Número de rutas planificadas
    - Número de incidencias
    - Número de predicciones LSTM
    """
    zona = db.query(Zona).filter(Zona.id_zona == zona_id).first()
    if not zona:
        raise HTTPException(status_code=404, detail=f"Zona con ID {zona_id} no encontrada")
    
    return {
        "zona_id": zona_id,
        "nombre": zona.nombre,
        "puntos_recoleccion": len(zona.puntos) if hasattr(zona, 'puntos') else 0,
        "rutas_planificadas": len(zona.rutas) if hasattr(zona, 'rutas') else 0,
        "incidencias": len(zona.incidencias) if hasattr(zona, 'incidencias') else 0,
        "predicciones_lstm": len(zona.predicciones) if hasattr(zona, 'predicciones') else 0,
    }
