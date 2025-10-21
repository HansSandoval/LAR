"""
Router para gestionar operaciones CRUD en la tabla PeriodoTemporal.
Endpoints para crear, listar, actualizar y eliminar periodos temporales.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime
from ..database.db import get_db
from ..models.models import PeriodoTemporal
from ..schemas.schemas import (
    PeriodoTemporalCreate,
    PeriodoTemporalUpdate,
    PeriodoTemporalResponse
)

router = APIRouter(prefix="/periodos-temporales", tags=["Periodos Temporales"])


@router.get(
    "/",
    response_model=dict,
    summary="Listar todos los periodos temporales con paginación y filtros",
    description="Retorna una lista paginada de periodos temporales"
)
async def get_periodos_temporales(
    skip: int = Query(0, ge=0, description="Número de registros a saltar"),
    limit: int = Query(10, ge=1, le=100, description="Número máximo de registros a retornar"),
    tipo_granularidad: str = Query(None, description="Filtrar por granularidad (diario, semanal, mensual, anual)"),
    estacionalidad: str = Query(None, description="Filtrar por estacionalidad (verano, invierno, primavera, otoño, general)"),
    db: Session = Depends(get_db)
):
    """
    Obtiene una lista paginada de periodos temporales con filtros opcionales.
    
    **Parámetros de filtrado:**
    - `tipo_granularidad`: Filtra por granularidad temporal (diario, semanal, mensual, anual)
    - `estacionalidad`: Filtra por estacionalidad (verano, invierno, primavera, otoño, general)
    
    **Ejemplo de uso:**
    ```
    GET /periodos-temporales/?skip=0&limit=10&tipo_granularidad=mensual
    ```
    """
    try:
        query = db.query(PeriodoTemporal)
        
        # Aplicar filtros
        if tipo_granularidad:
            query = query.filter(PeriodoTemporal.tipo_granularidad == tipo_granularidad)
        if estacionalidad:
            query = query.filter(PeriodoTemporal.estacionalidad == estacionalidad)
        
        # Obtener total
        total = query.count()
        
        # Aplicar paginación
        periodos = query.offset(skip).limit(limit).all()
        
        return {
            "data": [PeriodoTemporalResponse.from_orm(p) for p in periodos],
            "total": total,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar periodos temporales: {str(e)}")


@router.get(
    "/{periodo_id}",
    response_model=PeriodoTemporalResponse,
    summary="Obtener un periodo temporal por ID",
    description="Retorna los detalles de un periodo temporal específico"
)
async def get_periodo_temporal(periodo_id: int, db: Session = Depends(get_db)):
    """
    Obtiene los detalles de un periodo temporal específico por su ID.
    
    **Ejemplo de uso:**
    ```
    GET /periodos-temporales/1
    ```
    """
    try:
        periodo = db.query(PeriodoTemporal).filter(PeriodoTemporal.id_periodo == periodo_id).first()
        if not periodo:
            raise HTTPException(status_code=404, detail=f"Periodo temporal con ID {periodo_id} no encontrado")
        return PeriodoTemporalResponse.from_orm(periodo)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener periodo temporal: {str(e)}")


@router.post(
    "/",
    response_model=PeriodoTemporalResponse,
    status_code=201,
    summary="Crear un nuevo periodo temporal",
    description="Crea un nuevo registro de periodo temporal"
)
async def create_periodo_temporal(periodo: PeriodoTemporalCreate, db: Session = Depends(get_db)):
    """
    Crea un nuevo periodo temporal.
    
    **Validaciones:**
    - La fecha de inicio debe ser menor que la fecha de fin
    - El tipo de granularidad debe ser válido
    
    **Tipos de granularidad válidos:** diario, semanal, mensual, anual
    **Estacionalidades válidas:** verano, invierno, primavera, otoño, general
    
    **Ejemplo de payload:**
    ```json
    {
        "fecha_inicio": "2024-01-01T00:00:00",
        "fecha_fin": "2024-01-31T23:59:59",
        "tipo_granularidad": "diario",
        "estacionalidad": "verano"
    }
    ```
    """
    try:
        # Validar que fecha_inicio < fecha_fin
        if periodo.fecha_inicio >= periodo.fecha_fin:
            raise HTTPException(status_code=400, detail="Fecha inicio debe ser menor que fecha fin")
        
        # Validar tipo de granularidad
        granularidades_validas = ["diario", "semanal", "mensual", "anual"]
        if periodo.tipo_granularidad not in granularidades_validas:
            raise HTTPException(
                status_code=400,
                detail=f"Tipo de granularidad inválido. Debe ser uno de: {', '.join(granularidades_validas)}"
            )
        
        # Validar estacionalidad (opcional)
        if periodo.estacionalidad:
            estacionalidades_validas = ["verano", "invierno", "primavera", "otoño", "general"]
            if periodo.estacionalidad not in estacionalidades_validas:
                raise HTTPException(
                    status_code=400,
                    detail=f"Estacionalidad inválida. Debe ser una de: {', '.join(estacionalidades_validas)}"
                )
        
        nuevo_periodo = PeriodoTemporal(
            fecha_inicio=periodo.fecha_inicio,
            fecha_fin=periodo.fecha_fin,
            tipo_granularidad=periodo.tipo_granularidad,
            estacionalidad=periodo.estacionalidad or "general"
        )
        db.add(nuevo_periodo)
        db.commit()
        db.refresh(nuevo_periodo)
        return PeriodoTemporalResponse.from_orm(nuevo_periodo)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al crear periodo temporal: {str(e)}")


@router.put(
    "/{periodo_id}",
    response_model=PeriodoTemporalResponse,
    summary="Actualizar un periodo temporal",
    description="Actualiza los datos de un periodo temporal existente"
)
async def update_periodo_temporal(
    periodo_id: int,
    periodo_data: PeriodoTemporalUpdate,
    db: Session = Depends(get_db)
):
    """
    Actualiza un periodo temporal existente.
    
    **Ejemplo de uso:**
    ```
    PUT /periodos-temporales/1
    ```
    
    **Ejemplo de payload:**
    ```json
    {
        "estacionalidad": "invierno",
        "fecha_fin": "2024-02-29T23:59:59"
    }
    ```
    """
    try:
        periodo = db.query(PeriodoTemporal).filter(PeriodoTemporal.id_periodo == periodo_id).first()
        if not periodo:
            raise HTTPException(status_code=404, detail=f"Periodo temporal con ID {periodo_id} no encontrado")
        
        # Validar fechas si se actualizan
        fecha_inicio = periodo_data.fecha_inicio or periodo.fecha_inicio
        fecha_fin = periodo_data.fecha_fin or periodo.fecha_fin
        
        if fecha_inicio >= fecha_fin:
            raise HTTPException(status_code=400, detail="Fecha inicio debe ser menor que fecha fin")
        
        # Validar granularidad si se actualiza
        if periodo_data.tipo_granularidad:
            granularidades_validas = ["diario", "semanal", "mensual", "anual"]
            if periodo_data.tipo_granularidad not in granularidades_validas:
                raise HTTPException(
                    status_code=400,
                    detail=f"Tipo de granularidad inválido. Debe ser uno de: {', '.join(granularidades_validas)}"
                )
        
        # Validar estacionalidad si se actualiza
        if periodo_data.estacionalidad:
            estacionalidades_validas = ["verano", "invierno", "primavera", "otoño", "general"]
            if periodo_data.estacionalidad not in estacionalidades_validas:
                raise HTTPException(
                    status_code=400,
                    detail=f"Estacionalidad inválida. Debe ser una de: {', '.join(estacionalidades_validas)}"
                )
        
        # Actualizar campos
        datos = periodo_data.dict(exclude_unset=True)
        for campo, valor in datos.items():
            setattr(periodo, campo, valor)
        
        db.commit()
        db.refresh(periodo)
        return PeriodoTemporalResponse.from_orm(periodo)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al actualizar periodo temporal: {str(e)}")


@router.delete(
    "/{periodo_id}",
    status_code=204,
    summary="Eliminar un periodo temporal",
    description="Elimina un periodo temporal de la base de datos"
)
async def delete_periodo_temporal(periodo_id: int, db: Session = Depends(get_db)):
    """
    Elimina un periodo temporal existente.
    
    **Advertencia:** Esta operación no se puede deshacer.
    
    **Ejemplo de uso:**
    ```
    DELETE /periodos-temporales/1
    ```
    """
    try:
        periodo = db.query(PeriodoTemporal).filter(PeriodoTemporal.id_periodo == periodo_id).first()
        if not periodo:
            raise HTTPException(status_code=404, detail=f"Periodo temporal con ID {periodo_id} no encontrado")
        
        db.delete(periodo)
        db.commit()
        return None
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al eliminar periodo temporal: {str(e)}")


@router.get(
    "/activos/en-rango",
    response_model=dict,
    summary="Obtener periodos activos en un rango de fechas",
    description="Retorna periodos temporales que se solapan con el rango especificado"
)
async def get_periodos_activos(
    fecha_inicio: datetime = Query(..., description="Fecha inicio del rango"),
    fecha_fin: datetime = Query(..., description="Fecha fin del rango"),
    db: Session = Depends(get_db)
):
    """
    Obtiene los periodos que están activos en un rango de fechas específico.
    
    Un periodo se considera activo si se solapa con el rango especificado.
    
    **Ejemplo de uso:**
    ```
    GET /periodos-temporales/activos/en-rango?fecha_inicio=2024-01-01T00:00:00&fecha_fin=2024-01-31T23:59:59
    ```
    """
    try:
        if fecha_inicio >= fecha_fin:
            raise HTTPException(status_code=400, detail="Fecha inicio debe ser menor que fecha fin")
        
        # Buscar periodos que se solapan
        periodos = db.query(PeriodoTemporal).filter(
            PeriodoTemporal.fecha_inicio <= fecha_fin,
            PeriodoTemporal.fecha_fin >= fecha_inicio
        ).all()
        
        return {
            "rango_consultado": {
                "fecha_inicio": fecha_inicio,
                "fecha_fin": fecha_fin
            },
            "periodos_activos": [PeriodoTemporalResponse.from_orm(p) for p in periodos],
            "cantidad": len(periodos)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener periodos activos: {str(e)}")


@router.get(
    "/por-estacionalidad/{estacionalidad}",
    response_model=dict,
    summary="Obtener periodos por estacionalidad",
    description="Retorna todos los periodos de una estacionalidad específica"
)
async def get_periodos_por_estacionalidad(
    estacionalidad: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Obtiene todos los periodos de una estacionalidad específica.
    
    **Estacionalidades válidas:** verano, invierno, primavera, otoño, general
    
    **Ejemplo de uso:**
    ```
    GET /periodos-temporales/por-estacionalidad/verano?skip=0&limit=10
    ```
    """
    try:
        estacionalidades_validas = ["verano", "invierno", "primavera", "otoño", "general"]
        if estacionalidad not in estacionalidades_validas:
            raise HTTPException(
                status_code=400,
                detail=f"Estacionalidad inválida. Debe ser una de: {', '.join(estacionalidades_validas)}"
            )
        
        query = db.query(PeriodoTemporal).filter(PeriodoTemporal.estacionalidad == estacionalidad)
        total = query.count()
        periodos = query.offset(skip).limit(limit).all()
        
        return {
            "estacionalidad": estacionalidad,
            "data": [PeriodoTemporalResponse.from_orm(p) for p in periodos],
            "total": total,
            "skip": skip,
            "limit": limit
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar periodos por estacionalidad: {str(e)}")
