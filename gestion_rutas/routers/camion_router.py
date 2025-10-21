"""
routers/camion_router.py

Endpoints CRUD completos para la tabla Camion
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from ..database.db import get_db
from ..models.models import Camion
from ..schemas.schemas import CamionCreate, CamionUpdate, CamionResponse
from ..service.vehiculo_service import VehiculoService

router = APIRouter(
    prefix="/camiones",
    tags=["Vehículos"],
)

camion_service = VehiculoService()


@router.get("/", response_model=List[CamionResponse], summary="Obtener todos los camiones")
def get_camiones(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    estado: Optional[str] = None,
    tipo: Optional[str] = None,
):
    """
    Obtiene todos los camiones con paginación y filtros.
    
    **Query Parameters:**
    - `skip`: Número de registros a saltar
    - `limit`: Número máximo de registros
    - `estado`: Filtrar por estado (disponible, en_servicio, mantenimiento, etc.)
    - `tipo`: Filtrar por tipo (camión, furgón, etc.)
    """
    query = db.query(Camion)
    
    if estado:
        query = query.filter(Camion.estado == estado)
    if tipo:
        query = query.filter(Camion.tipo == tipo)
    
    camiones = query.offset(skip).limit(limit).all()
    return camiones


@router.get("/{camion_id}", response_model=CamionResponse, summary="Obtener camión por ID")
def get_camion(camion_id: int, db: Session = Depends(get_db)):
    """Obtiene un camión específico por su ID."""
    camion = db.query(Camion).filter(Camion.id_camion == camion_id).first()
    if not camion:
        raise HTTPException(status_code=404, detail=f"Camión con ID {camion_id} no encontrado")
    return camion


@router.post("/", response_model=CamionResponse, status_code=201, summary="Crear nuevo camión")
def create_camion(camion: CamionCreate, db: Session = Depends(get_db)):
    """
    Crea un nuevo camión.
    
    **Campos requeridos:**
    - `numero_interno`: Identificador interno del camión
    - `capacidad_kg`: Capacidad de carga en kg
    - `tipo`: Tipo de vehículo
    
    **Campos opcionales:**
    - `placa`: Placa del vehículo
    - `año_compra`: Año de compra
    - `estado`: Estado del vehículo (default: disponible)
    - `ubicacion_actual`: Ubicación GPS actual
    """
    db_camion = Camion(**camion.dict())
    db.add(db_camion)
    db.commit()
    db.refresh(db_camion)
    return db_camion


@router.put("/{camion_id}", response_model=CamionResponse, summary="Actualizar camión")
def update_camion(camion_id: int, camion: CamionUpdate, db: Session = Depends(get_db)):
    """Actualiza un camión existente."""
    db_camion = db.query(Camion).filter(Camion.id_camion == camion_id).first()
    if not db_camion:
        raise HTTPException(status_code=404, detail=f"Camión con ID {camion_id} no encontrado")
    
    update_data = camion.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_camion, field, value)
    
    db.add(db_camion)
    db.commit()
    db.refresh(db_camion)
    return db_camion


@router.delete("/{camion_id}", status_code=204, summary="Eliminar camión")
def delete_camion(camion_id: int, db: Session = Depends(get_db)):
    """Elimina un camión."""
    db_camion = db.query(Camion).filter(Camion.id_camion == camion_id).first()
    if not db_camion:
        raise HTTPException(status_code=404, detail=f"Camión con ID {camion_id} no encontrado")
    
    db.delete(db_camion)
    db.commit()
    return None


@router.patch("/{camion_id}/estado", response_model=CamionResponse, summary="Cambiar estado del camión")
def update_estado_camion(
    camion_id: int,
    nuevo_estado: str = Query(..., description="Nuevo estado: disponible, en_servicio, mantenimiento"),
    db: Session = Depends(get_db),
):
    """
    Actualiza el estado de un camión.
    
    **Estados válidos:**
    - `disponible`: Listo para asignación
    - `en_servicio`: Ejecutando ruta
    - `mantenimiento`: En mantenimiento
    """
    db_camion = db.query(Camion).filter(Camion.id_camion == camion_id).first()
    if not db_camion:
        raise HTTPException(status_code=404, detail=f"Camión con ID {camion_id} no encontrado")
    
    estados_validos = ["disponible", "en_servicio", "mantenimiento"]
    if nuevo_estado not in estados_validos:
        raise HTTPException(
            status_code=400, 
            detail=f"Estado inválido. Válidos: {', '.join(estados_validos)}"
        )
    
    db_camion.estado = nuevo_estado
    db.add(db_camion)
    db.commit()
    db.refresh(db_camion)
    return db_camion


@router.get("/{camion_id}/estadisticas", summary="Obtener estadísticas del camión")
def get_estadisticas_camion(camion_id: int, db: Session = Depends(get_db)):
    """
    Obtiene estadísticas de un camión.
    
    **Retorna:**
    - Número de rutas asignadas
    - Distancia total recorrida
    - Carga promedio utilizada
    - Estado actual
    """
    camion = db.query(Camion).filter(Camion.id_camion == camion_id).first()
    if not camion:
        raise HTTPException(status_code=404, detail=f"Camión con ID {camion_id} no encontrado")
    
    return {
        "camion_id": camion_id,
        "numero_interno": camion.numero_interno,
        "estado": camion.estado,
        "capacidad_kg": camion.capacidad_kg,
        "rutas_asignadas": len(camion.rutas_planificadas) if hasattr(camion, 'rutas_planificadas') else 0,
        "rutas_ejecutadas": len(camion.rutas_ejecutadas) if hasattr(camion, 'rutas_ejecutadas') else 0,
    }
