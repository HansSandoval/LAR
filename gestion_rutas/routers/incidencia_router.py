"""
Router para gestionar operaciones CRUD en la tabla Incidencia.
Endpoints para crear, listar, actualizar y eliminar registros de incidencias/problemas.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from ..database.db import get_db
from ..models.models import Incidencia, RutaEjecutada, Zona, Camion
from ..schemas.schemas import (
    IncidenciaCreate,
    IncidenciaUpdate,
    IncidenciaResponse
)

router = APIRouter(prefix="/incidencias", tags=["Incidencias"])


@router.get(
    "/",
    response_model=dict,
    summary="Listar todas las incidencias con paginación y filtros",
    description="Retorna una lista paginada de incidencias con opciones de filtrado por severidad, tipo y fecha"
)
async def get_incidencias(
    skip: int = Query(0, ge=0, description="Número de registros a saltar"),
    limit: int = Query(10, ge=1, le=100, description="Número máximo de registros a retornar"),
    tipo: str = Query(None, description="Filtrar por tipo de incidencia"),
    severidad_min: int = Query(None, ge=1, le=5, description="Filtrar por severidad mínima (1-5)"),
    severidad_max: int = Query(None, ge=1, le=5, description="Filtrar por severidad máxima (1-5)"),
    id_zona: int = Query(None, description="Filtrar por ID de zona"),
    id_camion: int = Query(None, description="Filtrar por ID de camión"),
    fecha_desde: datetime = Query(None, description="Filtrar desde esta fecha"),
    fecha_hasta: datetime = Query(None, description="Filtrar hasta esta fecha"),
    db: Session = Depends(get_db)
):
    """
    Obtiene una lista paginada de incidencias con filtros opcionales.
    
    **Parámetros de filtrado:**
    - `tipo`: Filtra por tipo de incidencia (accidente, avería, retraso, etc.)
    - `severidad_min`: Severidad mínima (1=baja, 5=crítica)
    - `severidad_max`: Severidad máxima
    - `id_zona`: Filtra incidencias en una zona específica
    - `id_camion`: Filtra incidencias de un camión específico
    - `fecha_desde`: Filtra desde una fecha específica
    - `fecha_hasta`: Filtra hasta una fecha específica
    
    **Ejemplo de uso:**
    ```
    GET /incidencias/?skip=0&limit=10&severidad_min=4&tipo=accidente
    ```
    """
    try:
        query = db.query(Incidencia)
        
        # Aplicar filtros
        if tipo:
            query = query.filter(Incidencia.tipo == tipo)
        if severidad_min:
            query = query.filter(Incidencia.severidad >= severidad_min)
        if severidad_max:
            query = query.filter(Incidencia.severidad <= severidad_max)
        if id_zona:
            query = query.filter(Incidencia.id_zona == id_zona)
        if id_camion:
            query = query.filter(Incidencia.id_camion == id_camion)
        if fecha_desde:
            query = query.filter(Incidencia.fecha_hora >= fecha_desde)
        if fecha_hasta:
            query = query.filter(Incidencia.fecha_hora <= fecha_hasta)
        
        # Obtener total
        total = query.count()
        
        # Aplicar paginación y ordenar por fecha descendente
        incidencias = query.order_by(Incidencia.fecha_hora.desc()).offset(skip).limit(limit).all()
        
        return {
            "data": [IncidenciaResponse.from_orm(i) for i in incidencias],
            "total": total,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar incidencias: {str(e)}")


@router.get(
    "/{incidencia_id}",
    response_model=IncidenciaResponse,
    summary="Obtener una incidencia por ID",
    description="Retorna los detalles de una incidencia específica"
)
async def get_incidencia(incidencia_id: int, db: Session = Depends(get_db)):
    """
    Obtiene los detalles de una incidencia específica por su ID.
    
    **Ejemplo de uso:**
    ```
    GET /incidencias/1
    ```
    """
    try:
        incidencia = db.query(Incidencia).filter(Incidencia.id_incidencia == incidencia_id).first()
        if not incidencia:
            raise HTTPException(status_code=404, detail=f"Incidencia con ID {incidencia_id} no encontrada")
        return IncidenciaResponse.from_orm(incidencia)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener incidencia: {str(e)}")


@router.post(
    "/",
    response_model=IncidenciaResponse,
    status_code=201,
    summary="Crear una nueva incidencia",
    description="Crea un nuevo registro de incidencia"
)
async def create_incidencia(incidencia: IncidenciaCreate, db: Session = Depends(get_db)):
    """
    Crea un nuevo registro de incidencia.
    
    **Validaciones:**
    - La ruta ejecutada debe existir (si se proporciona)
    - La zona debe existir
    - El camión debe existir
    - La severidad debe estar entre 1 y 5
    
    **Ejemplo de payload:**
    ```json
    {
        "id_ruta_exec": 1,
        "id_zona": 1,
        "id_camion": 1,
        "tipo": "accidente",
        "descripcion": "Colisión menor en calle Principal",
        "fecha_hora": "2024-01-15T14:30:00",
        "severidad": 3
    }
    ```
    
    **Niveles de severidad:**
    - 1: Baja
    - 2: Media
    - 3: Normal
    - 4: Alta
    - 5: Crítica
    """
    try:
        # Validar severidad
        if not (1 <= incidencia.severidad <= 5):
            raise HTTPException(status_code=400, detail="Severidad debe estar entre 1 y 5")
        
        # Validar que la ruta ejecutada existe (si se proporciona)
        if incidencia.id_ruta_exec:
            ruta = db.query(RutaEjecutada).filter(RutaEjecutada.id_ruta_exec == incidencia.id_ruta_exec).first()
            if not ruta:
                raise HTTPException(status_code=400, detail=f"Ruta ejecutada con ID {incidencia.id_ruta_exec} no existe")
        
        # Validar que la zona existe
        zona = db.query(Zona).filter(Zona.id_zona == incidencia.id_zona).first()
        if not zona:
            raise HTTPException(status_code=400, detail=f"Zona con ID {incidencia.id_zona} no existe")
        
        # Validar que el camión existe
        camion = db.query(Camion).filter(Camion.id_camion == incidencia.id_camion).first()
        if not camion:
            raise HTTPException(status_code=400, detail=f"Camión con ID {incidencia.id_camion} no existe")
        
        nueva_incidencia = Incidencia(
            id_ruta_exec=incidencia.id_ruta_exec,
            id_zona=incidencia.id_zona,
            id_camion=incidencia.id_camion,
            tipo=incidencia.tipo,
            descripcion=incidencia.descripcion,
            fecha_hora=incidencia.fecha_hora,
            severidad=incidencia.severidad
        )
        db.add(nueva_incidencia)
        db.commit()
        db.refresh(nueva_incidencia)
        return IncidenciaResponse.from_orm(nueva_incidencia)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al crear incidencia: {str(e)}")


@router.put(
    "/{incidencia_id}",
    response_model=IncidenciaResponse,
    summary="Actualizar una incidencia",
    description="Actualiza los datos de una incidencia existente"
)
async def update_incidencia(
    incidencia_id: int,
    incidencia_data: IncidenciaUpdate,
    db: Session = Depends(get_db)
):
    """
    Actualiza una incidencia existente.
    
    **Ejemplo de uso:**
    ```
    PUT /incidencias/1
    ```
    
    **Ejemplo de payload:**
    ```json
    {
        "descripcion": "Descripción actualizada del incidente",
        "severidad": 4
    }
    ```
    """
    try:
        incidencia = db.query(Incidencia).filter(Incidencia.id_incidencia == incidencia_id).first()
        if not incidencia:
            raise HTTPException(status_code=404, detail=f"Incidencia con ID {incidencia_id} no encontrada")
        
        # Validar severidad si se actualiza
        if incidencia_data.severidad is not None:
            if not (1 <= incidencia_data.severidad <= 5):
                raise HTTPException(status_code=400, detail="Severidad debe estar entre 1 y 5")
        
        # Validar zona si se cambia
        if incidencia_data.id_zona and incidencia_data.id_zona != incidencia.id_zona:
            zona = db.query(Zona).filter(Zona.id_zona == incidencia_data.id_zona).first()
            if not zona:
                raise HTTPException(status_code=400, detail=f"Zona con ID {incidencia_data.id_zona} no existe")
        
        # Validar camión si se cambia
        if incidencia_data.id_camion and incidencia_data.id_camion != incidencia.id_camion:
            camion = db.query(Camion).filter(Camion.id_camion == incidencia_data.id_camion).first()
            if not camion:
                raise HTTPException(status_code=400, detail=f"Camión con ID {incidencia_data.id_camion} no existe")
        
        # Actualizar campos
        datos = incidencia_data.dict(exclude_unset=True)
        for campo, valor in datos.items():
            setattr(incidencia, campo, valor)
        
        db.commit()
        db.refresh(incidencia)
        return IncidenciaResponse.from_orm(incidencia)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al actualizar incidencia: {str(e)}")


@router.delete(
    "/{incidencia_id}",
    status_code=204,
    summary="Eliminar una incidencia",
    description="Elimina un registro de incidencia de la base de datos"
)
async def delete_incidencia(incidencia_id: int, db: Session = Depends(get_db)):
    """
    Elimina un registro de incidencia existente.
    
    **Advertencia:** Esta operación no se puede deshacer.
    
    **Ejemplo de uso:**
    ```
    DELETE /incidencias/1
    ```
    """
    try:
        incidencia = db.query(Incidencia).filter(Incidencia.id_incidencia == incidencia_id).first()
        if not incidencia:
            raise HTTPException(status_code=404, detail=f"Incidencia con ID {incidencia_id} no encontrada")
        
        db.delete(incidencia)
        db.commit()
        return None
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al eliminar incidencia: {str(e)}")


@router.get(
    "/estadisticas/por-tipo",
    summary="Obtener estadísticas de incidencias por tipo",
    description="Retorna el conteo de incidencias agrupadas por tipo"
)
async def get_incidencias_por_tipo(db: Session = Depends(get_db)):
    """
    Obtiene estadísticas de incidencias agrupadas por tipo.
    
    **Ejemplo de uso:**
    ```
    GET /incidencias/estadisticas/por-tipo
    ```
    """
    try:
        incidencias = db.query(Incidencia.tipo, func.count(Incidencia.id_incidencia)).group_by(Incidencia.tipo).all()
        
        return {
            "estadisticas": [
                {"tipo": tipo, "cantidad": cantidad}
                for tipo, cantidad in incidencias
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener estadísticas: {str(e)}")


@router.get(
    "/estadisticas/por-severidad",
    summary="Obtener estadísticas de incidencias por severidad",
    description="Retorna el conteo de incidencias agrupadas por nivel de severidad"
)
async def get_incidencias_por_severidad(db: Session = Depends(get_db)):
    """
    Obtiene estadísticas de incidencias agrupadas por severidad.
    
    **Ejemplo de uso:**
    ```
    GET /incidencias/estadisticas/por-severidad
    ```
    """
    try:
        incidencias = db.query(Incidencia.severidad, func.count(Incidencia.id_incidencia)).group_by(Incidencia.severidad).all()
        
        severidad_map = {1: "Baja", 2: "Media", 3: "Normal", 4: "Alta", 5: "Crítica"}
        
        return {
            "estadisticas": [
                {"severidad": severidad_map.get(severidad, str(severidad)), "cantidad": cantidad}
                for severidad, cantidad in incidencias
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener estadísticas: {str(e)}")


@router.get(
    "/criticas",
    response_model=dict,
    summary="Listar incidencias críticas",
    description="Retorna las incidencias con severidad crítica (nivel 5)"
)
async def get_incidencias_criticas(
    skip: int = Query(0, ge=0, description="Número de registros a saltar"),
    limit: int = Query(10, ge=1, le=100, description="Número máximo de registros a retornar"),
    db: Session = Depends(get_db)
):
    """
    Obtiene todas las incidencias críticas (severidad = 5).
    
    **Ejemplo de uso:**
    ```
    GET /incidencias/criticas?skip=0&limit=10
    ```
    """
    try:
        query = db.query(Incidencia).filter(Incidencia.severidad == 5).order_by(Incidencia.fecha_hora.desc())
        total = query.count()
        incidencias = query.offset(skip).limit(limit).all()
        
        return {
            "data": [IncidenciaResponse.from_orm(i) for i in incidencias],
            "total": total,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar incidencias críticas: {str(e)}")
