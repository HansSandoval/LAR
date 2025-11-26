"""
Router para gestionar operaciones CRUD en la tabla RutaEjecutada - PostgreSQL Directo
Endpoints para crear, listar, actualizar y eliminar registros de rutas ejecutadas.
"""

from fastapi import APIRouter, HTTPException, Query
from datetime import date
from ..schemas.schemas import (
    RutaEjecutadaCreate,
    RutaEjecutadaUpdate,
    RutaEjecutadaResponse
)
from ..service.ruta_ejecutada_service import RutaEjecutadaService
from ..service.ruta_planificada_service import RutaPlanificadaService
from ..service.camion_service import CamionService

router = APIRouter(prefix="/rutas-ejecutadas", tags=["Rutas Ejecutadas"])


@router.get(
    "/",
    response_model=dict,
    summary="Listar todas las rutas ejecutadas con paginación y filtros",
    description="Retorna una lista paginada de rutas ejecutadas con opciones de filtrado"
)
async def get_rutas_ejecutadas(
    skip: int = Query(0, ge=0, description="Número de registros a saltar"),
    limit: int = Query(10, ge=1, le=100, description="Número máximo de registros a retornar"),
    id_ruta: int = Query(None, description="Filtrar por ID de ruta planificada"),
    id_camion: int = Query(None, description="Filtrar por ID del camión"),
    fecha_desde: date = Query(None, description="Filtrar desde esta fecha (YYYY-MM-DD)"),
    fecha_hasta: date = Query(None, description="Filtrar hasta esta fecha (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """
    Obtiene una lista paginada de rutas ejecutadas con filtros opcionales.
    
    **Parámetros de filtrado:**
    - `id_ruta`: Filtra por ID de ruta planificada
    - `id_camion`: Filtra rutas ejecutadas por un camión específico
    - `fecha_desde`: Filtra rutas desde una fecha específica
    - `fecha_hasta`: Filtra rutas hasta una fecha específica
    
    **Ejemplo de uso:**
    ```
    GET /rutas-ejecutadas/?skip=0&limit=10&id_camion=1&fecha_desde=2024-01-01
    ```
    """
    try:
        query = db.query(RutaEjecutada)
        
        # Aplicar filtros
        if id_ruta:
            query = query.filter(RutaEjecutada.id_ruta == id_ruta)
        if id_camion:
            query = query.filter(RutaEjecutada.id_camion == id_camion)
        if fecha_desde:
            query = query.filter(RutaEjecutada.fecha >= fecha_desde)
        if fecha_hasta:
            query = query.filter(RutaEjecutada.fecha <= fecha_hasta)
        
        # Obtener total
        total = query.count()
        
        # Aplicar paginación
        rutas = query.offset(skip).limit(limit).all()
        
        return {
            "data": [RutaEjecutadaResponse.from_orm(r) for r in rutas],
            "total": total,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar rutas ejecutadas: {str(e)}")


@router.get(
    "/{ruta_exec_id}",
    response_model=RutaEjecutadaResponse,
    summary="Obtener una ruta ejecutada por ID",
    description="Retorna los detalles de una ruta ejecutada específica"
)
async def get_ruta_ejecutada(ruta_exec_id: int, db: Session = Depends(get_db)):
    """
    Obtiene los detalles de una ruta ejecutada específica por su ID.
    
    **Ejemplo de uso:**
    ```
    GET /rutas-ejecutadas/1
    ```
    """
    try:
        ruta = db.query(RutaEjecutada).filter(RutaEjecutada.id_ruta_exec == ruta_exec_id).first()
        if not ruta:
            raise HTTPException(status_code=404, detail=f"Ruta ejecutada con ID {ruta_exec_id} no encontrada")
        return RutaEjecutadaResponse.from_orm(ruta)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener ruta ejecutada: {str(e)}")


@router.post(
    "/",
    response_model=RutaEjecutadaResponse,
    status_code=201,
    summary="Crear un nuevo registro de ruta ejecutada",
    description="Crea un nuevo registro de ruta ejecutada"
)
async def create_ruta_ejecutada(ruta: RutaEjecutadaCreate, db: Session = Depends(get_db)):
    """
    Crea un nuevo registro de ruta ejecutada.
    
    **Validaciones:**
    - La ruta planificada debe existir
    - El camión debe existir
    - La duración real debe ser positiva
    - El cumplimiento debe estar entre 0 y 100
    
    **Ejemplo de payload:**
    ```json
    {
        "id_ruta": 1,
        "id_camion": 1,
        "fecha": "2024-01-15",
        "distancia_real_km": 45.5,
        "duracion_real_min": 120,
        "cumplimiento_horario_pct": 95.5,
        "desviacion_km": 2.3,
        "telemetria_json": "{}"
    }
    ```
    """
    try:
        # Validar que la ruta planificada existe
        ruta_planificada = db.query(RutaPlanificada).filter(RutaPlanificada.id_ruta == ruta.id_ruta).first()
        if not ruta_planificada:
            raise HTTPException(status_code=400, detail=f"Ruta planificada con ID {ruta.id_ruta} no existe")
        
        # Validar que el camión existe
        camion = db.query(Camion).filter(Camion.id_camion == ruta.id_camion).first()
        if not camion:
            raise HTTPException(status_code=400, detail=f"Camión con ID {ruta.id_camion} no existe")
        
        # Validar duración
        if ruta.duracion_real_min <= 0:
            raise HTTPException(status_code=400, detail="Duración real debe ser mayor a 0")
        
        # Validar cumplimiento
        if not (0 <= ruta.cumplimiento_horario_pct <= 100):
            raise HTTPException(status_code=400, detail="Cumplimiento horario debe estar entre 0 y 100")
        
        nueva_ruta = RutaEjecutada(
            id_ruta=ruta.id_ruta,
            id_camion=ruta.id_camion,
            fecha=ruta.fecha,
            distancia_real_km=ruta.distancia_real_km,
            duracion_real_min=ruta.duracion_real_min,
            cumplimiento_horario_pct=ruta.cumplimiento_horario_pct,
            desviacion_km=ruta.desviacion_km,
            telemetria_json=ruta.telemetria_json
        )
        db.add(nueva_ruta)
        db.commit()
        db.refresh(nueva_ruta)
        return RutaEjecutadaResponse.from_orm(nueva_ruta)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al crear ruta ejecutada: {str(e)}")


@router.put(
    "/{ruta_exec_id}",
    response_model=RutaEjecutadaResponse,
    summary="Actualizar una ruta ejecutada",
    description="Actualiza los datos de una ruta ejecutada existente"
)
async def update_ruta_ejecutada(
    ruta_exec_id: int,
    ruta_data: RutaEjecutadaUpdate,
    db: Session = Depends(get_db)
):
    """
    Actualiza una ruta ejecutada existente.
    
    **Ejemplo de uso:**
    ```
    PUT /rutas-ejecutadas/1
    ```
    
    **Ejemplo de payload:**
    ```json
    {
        "cumplimiento_horario_pct": 98.0,
        "distancia_real_km": 46.0
    }
    ```
    """
    try:
        ruta = db.query(RutaEjecutada).filter(RutaEjecutada.id_ruta_exec == ruta_exec_id).first()
        if not ruta:
            raise HTTPException(status_code=404, detail=f"Ruta ejecutada con ID {ruta_exec_id} no encontrada")
        
        # Validar si cambia el camión
        if ruta_data.id_camion and ruta_data.id_camion != ruta.id_camion:
            camion = db.query(Camion).filter(Camion.id_camion == ruta_data.id_camion).first()
            if not camion:
                raise HTTPException(status_code=400, detail=f"Camión con ID {ruta_data.id_camion} no existe")
        
        # Validar duración si se actualiza
        if ruta_data.duracion_real_min and ruta_data.duracion_real_min <= 0:
            raise HTTPException(status_code=400, detail="Duración real debe ser mayor a 0")
        
        # Validar cumplimiento si se actualiza
        if ruta_data.cumplimiento_horario_pct is not None:
            if not (0 <= ruta_data.cumplimiento_horario_pct <= 100):
                raise HTTPException(status_code=400, detail="Cumplimiento horario debe estar entre 0 y 100")
        
        # Actualizar campos
        datos = ruta_data.dict(exclude_unset=True)
        for campo, valor in datos.items():
            setattr(ruta, campo, valor)
        
        db.commit()
        db.refresh(ruta)
        return RutaEjecutadaResponse.from_orm(ruta)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al actualizar ruta ejecutada: {str(e)}")


@router.delete(
    "/{ruta_exec_id}",
    status_code=204,
    summary="Eliminar una ruta ejecutada",
    description="Elimina un registro de ruta ejecutada de la base de datos"
)
async def delete_ruta_ejecutada(ruta_exec_id: int, db: Session = Depends(get_db)):
    """
    Elimina un registro de ruta ejecutada existente.
    
    **Advertencia:** Esta operación no se puede deshacer.
    
    **Ejemplo de uso:**
    ```
    DELETE /rutas-ejecutadas/1
    ```
    """
    try:
        ruta = db.query(RutaEjecutada).filter(RutaEjecutada.id_ruta_exec == ruta_exec_id).first()
        if not ruta:
            raise HTTPException(status_code=404, detail=f"Ruta ejecutada con ID {ruta_exec_id} no encontrada")
        
        db.delete(ruta)
        db.commit()
        return None
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al eliminar ruta ejecutada: {str(e)}")


@router.get(
    "/{ruta_exec_id}/detalles-completos",
    summary="Obtener detalles completos de una ruta ejecutada",
    description="Retorna información completa incluyendo ruta planificada, camión y estadísticas"
)
async def get_ruta_ejecutada_detalles(ruta_exec_id: int, db: Session = Depends(get_db)):
    """
    Obtiene todos los detalles de una ruta ejecutada incluyendo información relacionada.
    
    **Ejemplo de uso:**
    ```
    GET /rutas-ejecutadas/1/detalles-completos
    ```
    """
    try:
        ruta = db.query(RutaEjecutada).filter(RutaEjecutada.id_ruta_exec == ruta_exec_id).first()
        if not ruta:
            raise HTTPException(status_code=404, detail=f"Ruta ejecutada con ID {ruta_exec_id} no encontrada")
        
        return {
            "id_ruta_exec": ruta.id_ruta_exec,
            "fecha": ruta.fecha,
            "distancia_real_km": ruta.distancia_real_km,
            "duracion_real_min": ruta.duracion_real_min,
            "cumplimiento_horario_pct": ruta.cumplimiento_horario_pct,
            "desviacion_km": ruta.desviacion_km,
            "ruta_planificada": {
                "id_ruta": ruta.ruta_planificada.id_ruta if ruta.ruta_planificada else None,
                "distancia_planificada_km": ruta.ruta_planificada.distancia_planificada_km if ruta.ruta_planificada else None,
                "duracion_planificada_min": ruta.ruta_planificada.duracion_planificada_min if ruta.ruta_planificada else None
            },
            "camion": {
                "id_camion": ruta.camion.id_camion if ruta.camion else None,
                "patente": ruta.camion.patente if ruta.camion else None,
                "capacidad_kg": ruta.camion.capacidad_kg if ruta.camion else None,
                "estado_operativo": ruta.camion.estado_operativo if ruta.camion else None
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener detalles: {str(e)}")


@router.get(
    "/{ruta_exec_id}/desviacion",
    summary="Obtener desviación de ruta",
    description="Calcula y retorna la desviación entre planificado y ejecutado"
)
async def get_ruta_desviacion(ruta_exec_id: int, db: Session = Depends(get_db)):
    """
    Calcula la desviación entre la ruta planificada y la ejecutada.
    
    **Métricas:**
    - Desviación en distancia (km)
    - Desviación en duración (minutos)
    - Porcentaje de cumplimiento horario
    
    **Ejemplo de uso:**
    ```
    GET /rutas-ejecutadas/1/desviacion
    ```
    """
    try:
        ruta = db.query(RutaEjecutada).filter(RutaEjecutada.id_ruta_exec == ruta_exec_id).first()
        if not ruta:
            raise HTTPException(status_code=404, detail=f"Ruta ejecutada con ID {ruta_exec_id} no encontrada")
        
        if not ruta.ruta_planificada:
            raise HTTPException(status_code=404, detail="Esta ruta ejecutada no tiene ruta planificada asociada")
        
        desviacion_distancia = ruta.distancia_real_km - ruta.ruta_planificada.distancia_planificada_km
        desviacion_duracion = ruta.duracion_real_min - ruta.ruta_planificada.duracion_planificada_min
        
        return {
            "desviacion_distancia_km": desviacion_distancia,
            "desviacion_duracion_min": desviacion_duracion,
            "cumplimiento_horario_pct": ruta.cumplimiento_horario_pct,
            "distancia_planificada_km": ruta.ruta_planificada.distancia_planificada_km,
            "distancia_real_km": ruta.distancia_real_km,
            "duracion_planificada_min": ruta.ruta_planificada.duracion_planificada_min,
            "duracion_real_min": ruta.duracion_real_min
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al calcular desviación: {str(e)}")
