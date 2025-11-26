"""
Router para gestionar operaciones CRUD en la tabla Turno - PostgreSQL Directo
Endpoints para crear, listar, actualizar y eliminar turnos de trabajo.
"""

from fastapi import APIRouter, HTTPException, Query
from datetime import date
from ..schemas.schemas import (
    TurnoCreate,
    TurnoUpdate,
    TurnoResponse
)
from ..service.turno_service import TurnoService
from ..service.camion_service import CamionService

router = APIRouter(prefix="/turnos", tags=["Turnos"])


@router.get("/", response_model=dict, summary="Listar todos los turnos con paginación y filtros")
async def get_turnos(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    estado: str = Query(None),
    id_camion: int = Query(None),
    fecha_desde: date = Query(None),
    fecha_hasta: date = Query(None),
):
    """Obtiene una lista paginada de turnos con filtros opcionales."""
    try:
        turnos, total = TurnoService.obtener_turnos(
            estado=estado,
            id_camion=id_camion,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            skip=skip,
            limit=limit
        )
        return {"data": turnos, "total": total, "skip": skip, "limit": limit}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar turnos: {str(e)}")


@router.get("/{turno_id}", response_model=TurnoResponse, summary="Obtener un turno por ID")
async def get_turno(turno_id: int):
    """Obtiene los detalles de un turno específico por su ID."""
    try:
        turno = TurnoService.obtener_turno(turno_id)
        if not turno:
            raise HTTPException(status_code=404, detail=f"Turno con ID {turno_id} no encontrado")
        return turno
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener turno: {str(e)}")


@router.post("/", response_model=TurnoResponse, status_code=201, summary="Crear un nuevo turno")
async def create_turno(turno: TurnoCreate):
    """Crea un nuevo turno de trabajo."""
    try:
        # Validar que el camión existe
        camion = CamionService.obtener_camion(turno.id_camion)
        if not camion:
            raise HTTPException(status_code=400, detail=f"Camión con ID {turno.id_camion} no existe")
        
        # Validar que hora_inicio < hora_fin
        if turno.hora_inicio >= turno.hora_fin:
            raise HTTPException(status_code=400, detail="Hora inicio debe ser menor que hora fin")
        
        nuevo_turno = TurnoService.crear_turno(
            id_camion=turno.id_camion,
            fecha=turno.fecha,
            hora_inicio=turno.hora_inicio,
            hora_fin=turno.hora_fin,
            operador=turno.operador,
            estado=turno.estado
        )
        if not nuevo_turno:
            raise HTTPException(status_code=500, detail="Error al crear turno")
        return nuevo_turno
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear turno: {str(e)}")


@router.put("/{turno_id}", response_model=TurnoResponse, summary="Actualizar un turno")
async def update_turno(turno_id: int, turno_data: TurnoUpdate):
    """Actualiza un turno existente."""
    try:
        turno = TurnoService.obtener_turno(turno_id)
        if not turno:
            raise HTTPException(status_code=404, detail=f"Turno con ID {turno_id} no encontrado")
        
        # Si se cambia el camión, validar que existe
        if turno_data.id_camion and turno_data.id_camion != turno['id_camion']:
            camion = CamionService.obtener_camion(turno_data.id_camion)
            if not camion:
                raise HTTPException(status_code=400, detail=f"Camión con ID {turno_data.id_camion} no existe")
        
        # Si se actualizan horas, validar
        hora_inicio = turno_data.hora_inicio or turno.get('hora_inicio')
        hora_fin = turno_data.hora_fin or turno.get('hora_fin')
        if hora_inicio and hora_fin and hora_inicio >= hora_fin:
            raise HTTPException(status_code=400, detail="Hora inicio debe ser menor que hora fin")
        
        datos = {k: v for k, v in turno_data.dict(exclude_unset=True).items() if v is not None}
        resultado = TurnoService.actualizar_turno(turno_id, datos)
        if not resultado:
            raise HTTPException(status_code=500, detail="Error al actualizar turno")
        return resultado
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar turno: {str(e)}")


@router.delete("/{turno_id}", status_code=204, summary="Eliminar un turno")
async def delete_turno(turno_id: int):
    """Elimina un turno existente."""
    try:
        turno = TurnoService.obtener_turno(turno_id)
        if not turno:
            raise HTTPException(status_code=404, detail=f"Turno con ID {turno_id} no encontrado")
        
        exito = TurnoService.eliminar_turno(turno_id)
        if not exito:
            raise HTTPException(status_code=500, detail="Error al eliminar turno")
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar turno: {str(e)}")


@router.patch("/{turno_id}/estado", response_model=TurnoResponse, summary="Cambiar estado del turno")
async def update_turno_estado(
    turno_id: int,
    nuevo_estado: str = Query(..., description="Nuevo estado (activo, inactivo, completado)"),
):
    """Cambia el estado de un turno."""
    estados_validos = ["activo", "inactivo", "completado"]
    
    if nuevo_estado not in estados_validos:
        raise HTTPException(
            status_code=400,
            detail=f"Estado no válido. Debe ser uno de: {', '.join(estados_validos)}"
        )
    
    try:
        turno = TurnoService.obtener_turno(turno_id)
        if not turno:
            raise HTTPException(status_code=404, detail=f"Turno con ID {turno_id} no encontrado")
        
        resultado = TurnoService.cambiar_estado_turno(turno_id, nuevo_estado)
        if not resultado:
            raise HTTPException(status_code=500, detail="Error al actualizar estado")
        return resultado
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar estado del turno: {str(e)}")


@router.get("/{turno_id}/camion", summary="Obtener información del camión del turno")
async def get_turno_camion(turno_id: int):
    """Obtiene la información completa del camión asignado a un turno."""
    try:
        turno = TurnoService.obtener_turno(turno_id)
        if not turno:
            raise HTTPException(status_code=404, detail=f"Turno con ID {turno_id} no encontrado")
        
        camion = CamionService.obtener_camion(turno.get('id_camion'))
        if not camion:
            raise HTTPException(status_code=404, detail="Este turno no tiene camión asignado")
        
        return {
            "id_camion": camion.get('id_camion'),
            "patente": camion.get('patente'),
            "capacidad_kg": camion.get('capacidad_kg'),
            "tipo_combustible": camion.get('tipo_combustible'),
            "estado_operativo": camion.get('estado_operativo')
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener información del camión: {str(e)}")
