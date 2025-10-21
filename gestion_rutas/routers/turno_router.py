"""
Router para gestionar operaciones CRUD en la tabla Turno.
Endpoints para crear, listar, actualizar y eliminar turnos de trabajo.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import date
from ..database.db import get_db
from ..models.models import Turno, Camion
from ..schemas.schemas import (
    TurnoCreate,
    TurnoUpdate,
    TurnoResponse
)

router = APIRouter(prefix="/turnos", tags=["Turnos"])


@router.get(
    "/",
    response_model=dict,
    summary="Listar todos los turnos con paginación y filtros",
    description="Retorna una lista paginada de turnos con opciones de filtrado por estado, camión y rango de fechas"
)
async def get_turnos(
    skip: int = Query(0, ge=0, description="Número de registros a saltar"),
    limit: int = Query(10, ge=1, le=100, description="Número máximo de registros a retornar"),
    estado: str = Query(None, description="Filtrar por estado (activo, inactivo, completado)"),
    id_camion: int = Query(None, description="Filtrar por ID del camión"),
    fecha_desde: date = Query(None, description="Filtrar desde esta fecha (YYYY-MM-DD)"),
    fecha_hasta: date = Query(None, description="Filtrar hasta esta fecha (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """
    Obtiene una lista paginada de turnos con filtros opcionales.
    
    **Parámetros de filtrado:**
    - `estado`: Filtra por estado del turno (activo, inactivo, completado)
    - `id_camion`: Filtra turnos asignados a un camión específico
    - `fecha_desde`: Filtra turnos desde una fecha específica
    - `fecha_hasta`: Filtra turnos hasta una fecha específica
    
    **Ejemplo de uso:**
    ```
    GET /turnos/?skip=0&limit=10&estado=activo&id_camion=1
    ```
    """
    try:
        query = db.query(Turno)
        
        # Aplicar filtros
        if estado:
            query = query.filter(Turno.estado == estado)
        if id_camion:
            query = query.filter(Turno.id_camion == id_camion)
        if fecha_desde:
            query = query.filter(Turno.fecha >= fecha_desde)
        if fecha_hasta:
            query = query.filter(Turno.fecha <= fecha_hasta)
        
        # Obtener total
        total = query.count()
        
        # Aplicar paginación
        turnos = query.offset(skip).limit(limit).all()
        
        return {
            "data": [TurnoResponse.from_orm(t) for t in turnos],
            "total": total,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar turnos: {str(e)}")


@router.get(
    "/{turno_id}",
    response_model=TurnoResponse,
    summary="Obtener un turno por ID",
    description="Retorna los detalles de un turno específico"
)
async def get_turno(turno_id: int, db: Session = Depends(get_db)):
    """
    Obtiene los detalles de un turno específico por su ID.
    
    **Ejemplo de uso:**
    ```
    GET /turnos/1
    ```
    """
    try:
        turno = db.query(Turno).filter(Turno.id_turno == turno_id).first()
        if not turno:
            raise HTTPException(status_code=404, detail=f"Turno con ID {turno_id} no encontrado")
        return TurnoResponse.from_orm(turno)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener turno: {str(e)}")


@router.post(
    "/",
    response_model=TurnoResponse,
    status_code=201,
    summary="Crear un nuevo turno",
    description="Crea un nuevo registro de turno asociado a un camión"
)
async def create_turno(turno: TurnoCreate, db: Session = Depends(get_db)):
    """
    Crea un nuevo turno de trabajo.
    
    **Validaciones:**
    - El camión debe existir en la base de datos
    - La fecha debe ser válida
    - Hora inicio debe ser menor que hora fin
    
    **Ejemplo de payload:**
    ```json
    {
        "id_camion": 1,
        "fecha": "2024-01-15",
        "hora_inicio": "08:00:00",
        "hora_fin": "16:00:00",
        "operador": "Juan Pérez",
        "estado": "activo"
    }
    ```
    """
    try:
        # Validar que el camión existe
        camion = db.query(Camion).filter(Camion.id_camion == turno.id_camion).first()
        if not camion:
            raise HTTPException(status_code=400, detail=f"Camión con ID {turno.id_camion} no existe")
        
        # Validar que hora_inicio < hora_fin
        if turno.hora_inicio >= turno.hora_fin:
            raise HTTPException(status_code=400, detail="Hora inicio debe ser menor que hora fin")
        
        nuevo_turno = Turno(
            id_camion=turno.id_camion,
            fecha=turno.fecha,
            hora_inicio=turno.hora_inicio,
            hora_fin=turno.hora_fin,
            operador=turno.operador,
            estado=turno.estado
        )
        db.add(nuevo_turno)
        db.commit()
        db.refresh(nuevo_turno)
        return TurnoResponse.from_orm(nuevo_turno)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al crear turno: {str(e)}")


@router.put(
    "/{turno_id}",
    response_model=TurnoResponse,
    summary="Actualizar un turno",
    description="Actualiza los datos de un turno existente"
)
async def update_turno(turno_id: int, turno_data: TurnoUpdate, db: Session = Depends(get_db)):
    """
    Actualiza un turno existente.
    
    **Ejemplo de uso:**
    ```
    PUT /turnos/1
    ```
    
    **Ejemplo de payload:**
    ```json
    {
        "estado": "completado",
        "operador": "Pedro González"
    }
    ```
    """
    try:
        turno = db.query(Turno).filter(Turno.id_turno == turno_id).first()
        if not turno:
            raise HTTPException(status_code=404, detail=f"Turno con ID {turno_id} no encontrado")
        
        # Si se cambia el camión, validar que existe
        if turno_data.id_camion and turno_data.id_camion != turno.id_camion:
            camion = db.query(Camion).filter(Camion.id_camion == turno_data.id_camion).first()
            if not camion:
                raise HTTPException(status_code=400, detail=f"Camión con ID {turno_data.id_camion} no existe")
        
        # Si se actualizan horas, validar
        hora_inicio = turno_data.hora_inicio or turno.hora_inicio
        hora_fin = turno_data.hora_fin or turno.hora_fin
        if hora_inicio >= hora_fin:
            raise HTTPException(status_code=400, detail="Hora inicio debe ser menor que hora fin")
        
        # Actualizar campos
        datos = turno_data.dict(exclude_unset=True)
        for campo, valor in datos.items():
            setattr(turno, campo, valor)
        
        db.commit()
        db.refresh(turno)
        return TurnoResponse.from_orm(turno)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al actualizar turno: {str(e)}")


@router.delete(
    "/{turno_id}",
    status_code=204,
    summary="Eliminar un turno",
    description="Elimina un turno de la base de datos"
)
async def delete_turno(turno_id: int, db: Session = Depends(get_db)):
    """
    Elimina un turno existente.
    
    **Advertencia:** Esta operación no se puede deshacer.
    
    **Ejemplo de uso:**
    ```
    DELETE /turnos/1
    ```
    """
    try:
        turno = db.query(Turno).filter(Turno.id_turno == turno_id).first()
        if not turno:
            raise HTTPException(status_code=404, detail=f"Turno con ID {turno_id} no encontrado")
        
        db.delete(turno)
        db.commit()
        return None
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al eliminar turno: {str(e)}")


@router.patch(
    "/{turno_id}/estado",
    response_model=TurnoResponse,
    summary="Cambiar estado del turno",
    description="Actualiza solo el estado del turno a uno de los valores válidos"
)
async def update_turno_estado(
    turno_id: int,
    nuevo_estado: str = Query(..., description="Nuevo estado (activo, inactivo, completado)"),
    db: Session = Depends(get_db)
):
    """
    Cambia el estado de un turno.
    
    **Estados válidos:** activo, inactivo, completado
    
    **Ejemplo de uso:**
    ```
    PATCH /turnos/1/estado?nuevo_estado=completado
    ```
    """
    estados_validos = ["activo", "inactivo", "completado"]
    
    if nuevo_estado not in estados_validos:
        raise HTTPException(
            status_code=400,
            detail=f"Estado no válido. Debe ser uno de: {', '.join(estados_validos)}"
        )
    
    try:
        turno = db.query(Turno).filter(Turno.id_turno == turno_id).first()
        if not turno:
            raise HTTPException(status_code=404, detail=f"Turno con ID {turno_id} no encontrado")
        
        turno.estado = nuevo_estado
        db.commit()
        db.refresh(turno)
        return TurnoResponse.from_orm(turno)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al actualizar estado del turno: {str(e)}")


@router.get(
    "/{turno_id}/camion",
    summary="Obtener información del camión del turno",
    description="Retorna los detalles del camión asignado a este turno"
)
async def get_turno_camion(turno_id: int, db: Session = Depends(get_db)):
    """
    Obtiene la información completa del camión asignado a un turno.
    
    **Ejemplo de uso:**
    ```
    GET /turnos/1/camion
    ```
    """
    try:
        turno = db.query(Turno).filter(Turno.id_turno == turno_id).first()
        if not turno:
            raise HTTPException(status_code=404, detail=f"Turno con ID {turno_id} no encontrado")
        
        if not turno.camion:
            raise HTTPException(status_code=404, detail="Este turno no tiene camión asignado")
        
        return {
            "id_camion": turno.camion.id_camion,
            "patente": turno.camion.patente,
            "capacidad_kg": turno.camion.capacidad_kg,
            "tipo_combustible": turno.camion.tipo_combustible,
            "estado_operativo": turno.camion.estado_operativo
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener información del camión: {str(e)}")
