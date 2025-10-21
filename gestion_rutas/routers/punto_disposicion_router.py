"""
Router para gestionar operaciones CRUD en la tabla PuntoDisposicion.
Endpoints para crear, listar, actualizar y eliminar puntos de disposición de residuos.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database.db import get_db
from ..models.models import PuntoDisposicion
from ..schemas.schemas import (
    PuntoDisposicionCreate,
    PuntoDisposicionUpdate,
    PuntoDisposicionResponse
)
router = APIRouter(prefix="/puntos-disposicion", tags=["Puntos de Disposición"])


@router.get(
    "/",
    response_model=dict,
    summary="Listar todos los puntos de disposición con paginación y filtros",
    description="Retorna una lista paginada de puntos de disposición"
)
async def get_puntos_disposicion(
    skip: int = Query(0, ge=0, description="Número de registros a saltar"),
    limit: int = Query(10, ge=1, le=100, description="Número máximo de registros a retornar"),
    tipo: str = Query(None, description="Filtrar por tipo (relleno, reciclaje, compostaje, etc.)"),
    nombre: str = Query(None, description="Filtrar por nombre (búsqueda parcial)"),
    db: Session = Depends(get_db)
):
    """
    Obtiene una lista paginada de puntos de disposición con filtros opcionales.
    
    **Parámetros de filtrado:**
    - `tipo`: Filtra por tipo de punto (relleno, reciclaje, compostaje, etc.)
    - `nombre`: Busca puntos cuyo nombre contenga el texto especificado
    
    **Ejemplo de uso:**
    ```
    GET /puntos-disposicion/?skip=0&limit=10&tipo=relleno
    ```
    """
    try:
        query = db.query(PuntoDisposicion)
        
        # Aplicar filtros
        if tipo:
            query = query.filter(PuntoDisposicion.tipo == tipo)
        if nombre:
            query = query.filter(PuntoDisposicion.nombre.ilike(f"%{nombre}%"))
        
        # Obtener total
        total = query.count()
        
        # Aplicar paginación
        puntos = query.offset(skip).limit(limit).all()
        
        return {
            "data": [PuntoDisposicionResponse.from_orm(p) for p in puntos],
            "total": total,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar puntos de disposición: {str(e)}")


@router.get(
    "/{punto_id}",
    response_model=PuntoDisposicionResponse,
    summary="Obtener un punto de disposición por ID",
    description="Retorna los detalles de un punto de disposición específico"
)
async def get_punto_disposicion(punto_id: int, db: Session = Depends(get_db)):
    """
    Obtiene los detalles de un punto de disposición específico por su ID.
    
    **Ejemplo de uso:**
    ```
    GET /puntos-disposicion/1
    ```
    """
    try:
        punto = db.query(PuntoDisposicion).filter(PuntoDisposicion.id_disposicion == punto_id).first()
        if not punto:
            raise HTTPException(status_code=404, detail=f"Punto de disposición con ID {punto_id} no encontrado")
        return PuntoDisposicionResponse.from_orm(punto)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener punto de disposición: {str(e)}")


@router.post(
    "/",
    response_model=PuntoDisposicionResponse,
    status_code=201,
    summary="Crear un nuevo punto de disposición",
    description="Crea un nuevo registro de punto de disposición"
)
async def create_punto_disposicion(punto: PuntoDisposicionCreate, db: Session = Depends(get_db)):
    """
    Crea un nuevo punto de disposición.
    
    **Validaciones:**
    - Nombre no puede estar vacío
    - Latitud debe estar entre -90 y 90
    - Longitud debe estar entre -180 y 180
    - Capacidad debe ser positiva
    
    **Ejemplo de payload:**
    ```json
    {
        "nombre": "Relleno Sanitario Norte",
        "tipo": "relleno",
        "latitud": -20.2558,
        "longitud": -70.1402,
        "capacidad_diaria_ton": 500.0
    }
    ```
    """
    try:
        # Validar coordenadas
        if not (-90 <= punto.latitud <= 90):
            raise HTTPException(status_code=400, detail="Latitud debe estar entre -90 y 90")
        
        if not (-180 <= punto.longitud <= 180):
            raise HTTPException(status_code=400, detail="Longitud debe estar entre -180 y 180")
        
        # Validar capacidad
        if punto.capacidad_diaria_ton <= 0:
            raise HTTPException(status_code=400, detail="Capacidad diaria debe ser positiva")
        
        nuevo_punto = PuntoDisposicion(
            nombre=punto.nombre,
            tipo=punto.tipo,
            latitud=punto.latitud,
            longitud=punto.longitud,
            capacidad_diaria_ton=punto.capacidad_diaria_ton
        )
        db.add(nuevo_punto)
        db.commit()
        db.refresh(nuevo_punto)
        return PuntoDisposicionResponse.from_orm(nuevo_punto)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al crear punto de disposición: {str(e)}")


@router.put(
    "/{punto_id}",
    response_model=PuntoDisposicionResponse,
    summary="Actualizar un punto de disposición",
    description="Actualiza los datos de un punto de disposición existente"
)
async def update_punto_disposicion(
    punto_id: int,
    punto_data: PuntoDisposicionUpdate,
    db: Session = Depends(get_db)
):
    """
    Actualiza un punto de disposición existente.
    
    **Ejemplo de uso:**
    ```
    PUT /puntos-disposicion/1
    ```
    
    **Ejemplo de payload:**
    ```json
    {
        "capacidad_diaria_ton": 550.0,
        "nombre": "Relleno Sanitario Norte - Ampliación"
    }
    ```
    """
    try:
        punto = db.query(PuntoDisposicion).filter(PuntoDisposicion.id_disposicion == punto_id).first()
        if not punto:
            raise HTTPException(status_code=404, detail=f"Punto de disposición con ID {punto_id} no encontrado")
        
        # Validar coordenadas si se actualizan
        if punto_data.latitud is not None and not (-90 <= punto_data.latitud <= 90):
            raise HTTPException(status_code=400, detail="Latitud debe estar entre -90 y 90")
        
        if punto_data.longitud is not None and not (-180 <= punto_data.longitud <= 180):
            raise HTTPException(status_code=400, detail="Longitud debe estar entre -180 y 180")
        
        # Validar capacidad si se actualiza
        if punto_data.capacidad_diaria_ton is not None and punto_data.capacidad_diaria_ton <= 0:
            raise HTTPException(status_code=400, detail="Capacidad diaria debe ser positiva")
        
        # Actualizar campos
        datos = punto_data.dict(exclude_unset=True)
        for campo, valor in datos.items():
            setattr(punto, campo, valor)
        
        db.commit()
        db.refresh(punto)
        return PuntoDisposicionResponse.from_orm(punto)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al actualizar punto de disposición: {str(e)}")


@router.delete(
    "/{punto_id}",
    status_code=204,
    summary="Eliminar un punto de disposición",
    description="Elimina un punto de disposición de la base de datos"
)
async def delete_punto_disposicion(punto_id: int, db: Session = Depends(get_db)):
    """
    Elimina un punto de disposición existente.
    
    **Advertencia:** Esta operación no se puede deshacer.
    
    **Ejemplo de uso:**
    ```
    DELETE /puntos-disposicion/1
    ```
    """
    try:
        punto = db.query(PuntoDisposicion).filter(PuntoDisposicion.id_disposicion == punto_id).first()
        if not punto:
            raise HTTPException(status_code=404, detail=f"Punto de disposición con ID {punto_id} no encontrado")
        
        db.delete(punto)
        db.commit()
        return None
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al eliminar punto de disposición: {str(e)}")


@router.get(
    "/proximidad/por-coordenadas",
    summary="Buscar puntos de disposición cercanos",
    description="Retorna puntos de disposición dentro de un radio especificado"
)
async def get_puntos_por_proximidad(
    latitud: float = Query(..., description="Latitud del punto de referencia"),
    longitud: float = Query(..., description="Longitud del punto de referencia"),
    radio_km: float = Query(50, gt=0, description="Radio de búsqueda en kilómetros"),
    db: Session = Depends(get_db)
):
    """
    Busca puntos de disposición cercanos a unas coordenadas específicas.
    
    Utiliza la fórmula de Haversine para calcular distancias.
    
    **Ejemplo de uso:**
    ```
    GET /puntos-disposicion/proximidad/por-coordenadas?latitud=-20.25&longitud=-70.14&radio_km=50
    ```
    """
    try:
        from math import radians, sin, cos, sqrt, atan2
        
        def calcular_distancia(lat1, lon1, lat2, lon2):
            """Calcula distancia en km entre dos puntos usando Haversine."""
            R = 6371  # Radio de la Tierra en km
            lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
            c = 2 * atan2(sqrt(a), sqrt(1 - a))
            return R * c
        
        todos_los_puntos = db.query(PuntoDisposicion).all()
        
        puntos_cercanos = []
        for punto in todos_los_puntos:
            distancia = calcular_distancia(latitud, longitud, punto.latitud, punto.longitud)
            if distancia <= radio_km:
                punto_dict = PuntoDisposicionResponse.from_orm(punto).dict()
                punto_dict["distancia_km"] = round(distancia, 2)
                puntos_cercanos.append(punto_dict)
        
        # Ordenar por distancia
        puntos_cercanos.sort(key=lambda x: x["distancia_km"])
        
        return {
            "punto_referencia": {"latitud": latitud, "longitud": longitud},
            "radio_km": radio_km,
            "puntos_encontrados": len(puntos_cercanos),
            "puntos": puntos_cercanos
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al buscar puntos cercanos: {str(e)}")


@router.get(
    "/estadisticas/por-tipo",
    summary="Obtener estadísticas por tipo de disposición",
    description="Retorna conteo y capacidad promedio agrupada por tipo"
)
async def get_estadisticas_por_tipo(db: Session = Depends(get_db)):
    """
    Obtiene estadísticas de puntos de disposición agrupadas por tipo.
    
    **Ejemplo de uso:**
    ```
    GET /puntos-disposicion/estadisticas/por-tipo
    ```
    """
    try:
        from sqlalchemy import func
        
        estadisticas = db.query(
            PuntoDisposicion.tipo,
            func.count(PuntoDisposicion.id_disposicion).label("cantidad"),
            func.avg(PuntoDisposicion.capacidad_diaria_ton).label("capacidad_promedio"),
            func.sum(PuntoDisposicion.capacidad_diaria_ton).label("capacidad_total")
        ).group_by(PuntoDisposicion.tipo).all()
        
        return {
            "estadisticas": [
                {
                    "tipo": tipo,
                    "cantidad_puntos": cantidad,
                    "capacidad_promedio_ton": round(capacidad_promedio, 2) if capacidad_promedio else 0,
                    "capacidad_total_ton": round(capacidad_total, 2) if capacidad_total else 0
                }
                for tipo, cantidad, capacidad_promedio, capacidad_total in estadisticas
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener estadísticas: {str(e)}")
