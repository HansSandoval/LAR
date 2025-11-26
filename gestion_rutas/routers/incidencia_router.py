"""
Router para gestionar operaciones CRUD en la tabla Incidencia - PostgreSQL Directo
Endpoints para crear, listar, actualizar y eliminar registros de incidencias/problemas.
"""

from fastapi import APIRouter, HTTPException, Query
from datetime import datetime
from ..schemas.schemas import (
    IncidenciaCreate,
    IncidenciaUpdate,
    IncidenciaResponse
)
from ..service.incidencia_service import IncidenciaService
from ..service.zona_service import ZonaService
from ..service.camion_service import CamionService
from ..service.ruta_ejecutada_service import RutaEjecutadaService

router = APIRouter(prefix="/incidencias", tags=["Incidencias"])


@router.get("/", response_model=dict, summary="Listar todas las incidencias")
async def get_incidencias(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    tipo: str = Query(None),
    severidad_min: int = Query(None, ge=1, le=5),
    severidad_max: int = Query(None, ge=1, le=5),
    id_zona: int = Query(None),
    id_camion: int = Query(None),
    fecha_desde: datetime = Query(None),
    fecha_hasta: datetime = Query(None),
):
    """Obtiene una lista paginada de incidencias con filtros opcionales."""
    try:
        incidencias, total = IncidenciaService.obtener_incidencias(
            tipo=tipo,
            severidad_min=severidad_min,
            severidad_max=severidad_max,
            id_zona=id_zona,
            id_camion=id_camion,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            skip=skip,
            limit=limit
        )
        return {"data": incidencias, "total": total, "skip": skip, "limit": limit}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar incidencias: {str(e)}")


@router.get("/{incidencia_id}", response_model=IncidenciaResponse, summary="Obtener una incidencia por ID")
async def get_incidencia(incidencia_id: int):
    """Obtiene los detalles de una incidencia específica por su ID."""
    try:
        incidencia = IncidenciaService.obtener_incidencia(incidencia_id)
        if not incidencia:
            raise HTTPException(status_code=404, detail=f"Incidencia con ID {incidencia_id} no encontrada")
        return incidencia
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener incidencia: {str(e)}")


@router.post("/", response_model=IncidenciaResponse, status_code=201, summary="Crear una nueva incidencia")
async def create_incidencia(incidencia: IncidenciaCreate):
    """Crea un nuevo registro de incidencia."""
    try:
        # Validar severidad
        if not (1 <= incidencia.severidad <= 5):
            raise HTTPException(status_code=400, detail="Severidad debe estar entre 1 y 5")
        
        # Validar que la ruta ejecutada existe (si se proporciona)
        if incidencia.id_ruta_exec:
            ruta = RutaEjecutadaService.obtener_ruta_ejecutada(incidencia.id_ruta_exec)
            if not ruta:
                raise HTTPException(status_code=400, detail=f"Ruta ejecutada con ID {incidencia.id_ruta_exec} no existe")
        
        # Validar que la zona existe
        zona = ZonaService.obtener_zona(incidencia.id_zona)
        if not zona:
            raise HTTPException(status_code=400, detail=f"Zona con ID {incidencia.id_zona} no existe")
        
        # Validar que el camión existe
        camion = CamionService.obtener_camion(incidencia.id_camion)
        if not camion:
            raise HTTPException(status_code=400, detail=f"Camión con ID {incidencia.id_camion} no existe")
        
        nueva_incidencia = IncidenciaService.crear_incidencia(
            id_ruta_exec=incidencia.id_ruta_exec,
            id_zona=incidencia.id_zona,
            id_camion=incidencia.id_camion,
            tipo=incidencia.tipo,
            descripcion=incidencia.descripcion,
            fecha_hora=incidencia.fecha_hora,
            severidad=incidencia.severidad
        )
        if not nueva_incidencia:
            raise HTTPException(status_code=500, detail="Error al crear incidencia")
        return nueva_incidencia
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear incidencia: {str(e)}")


@router.put("/{incidencia_id}", response_model=IncidenciaResponse, summary="Actualizar una incidencia")
async def update_incidencia(incidencia_id: int, incidencia_data: IncidenciaUpdate):
    """Actualiza una incidencia existente."""
    try:
        incidencia = IncidenciaService.obtener_incidencia(incidencia_id)
        if not incidencia:
            raise HTTPException(status_code=404, detail=f"Incidencia con ID {incidencia_id} no encontrada")
        
        # Validar severidad si se actualiza
        if incidencia_data.severidad is not None:
            if not (1 <= incidencia_data.severidad <= 5):
                raise HTTPException(status_code=400, detail="Severidad debe estar entre 1 y 5")
        
        # Validar zona si se cambia
        if incidencia_data.id_zona and incidencia_data.id_zona != incidencia.get('id_zona'):
            zona = ZonaService.obtener_zona(incidencia_data.id_zona)
            if not zona:
                raise HTTPException(status_code=400, detail=f"Zona con ID {incidencia_data.id_zona} no existe")
        
        # Validar camión si se cambia
        if incidencia_data.id_camion and incidencia_data.id_camion != incidencia.get('id_camion'):
            camion = CamionService.obtener_camion(incidencia_data.id_camion)
            if not camion:
                raise HTTPException(status_code=400, detail=f"Camión con ID {incidencia_data.id_camion} no existe")
        
        datos = {k: v for k, v in incidencia_data.dict(exclude_unset=True).items() if v is not None}
        resultado = IncidenciaService.actualizar_incidencia(incidencia_id, datos)
        if not resultado:
            raise HTTPException(status_code=500, detail="Error al actualizar incidencia")
        return resultado
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar incidencia: {str(e)}")


@router.delete("/{incidencia_id}", status_code=204, summary="Eliminar una incidencia")
async def delete_incidencia(incidencia_id: int):
    """Elimina un registro de incidencia existente."""
    try:
        incidencia = IncidenciaService.obtener_incidencia(incidencia_id)
        if not incidencia:
            raise HTTPException(status_code=404, detail=f"Incidencia con ID {incidencia_id} no encontrada")
        
        exito = IncidenciaService.eliminar_incidencia(incidencia_id)
        if not exito:
            raise HTTPException(status_code=500, detail="Error al eliminar incidencia")
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar incidencia: {str(e)}")


@router.get("/estadisticas/por-tipo", summary="Obtener estadísticas de incidencias por tipo")
async def get_incidencias_por_tipo():
    """Obtiene estadísticas de incidencias agrupadas por tipo."""
    try:
        estadisticas = IncidenciaService.obtener_estadisticas_por_tipo()
        return {"estadisticas": estadisticas}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener estadísticas: {str(e)}")


@router.get("/estadisticas/por-severidad", summary="Obtener estadísticas por severidad")
async def get_incidencias_por_severidad():
    """Obtiene estadísticas de incidencias agrupadas por severidad."""
    try:
        estadisticas = IncidenciaService.obtener_estadisticas_por_severidad()
        severidad_map = {1: "Baja", 2: "Media", 3: "Normal", 4: "Alta", 5: "Crítica"}
        
        resultado = []
        for stat in estadisticas:
            severidad_num = stat.get('severidad')
            resultado.append({
                "severidad": severidad_map.get(severidad_num, str(severidad_num)),
                "cantidad": stat.get('cantidad')
            })
        
        return {"estadisticas": resultado}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener estadísticas: {str(e)}")


@router.get("/criticas", response_model=dict, summary="Listar incidencias críticas")
async def get_incidencias_criticas(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
):
    """Obtiene todas las incidencias críticas (severidad = 5)."""
    try:
        criticas = IncidenciaService.obtener_incidencias_criticas()
        total = len(criticas)
        data = criticas[skip:skip+limit]
        
        return {"data": data, "total": total, "skip": skip, "limit": limit}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar incidencias críticas: {str(e)}")
