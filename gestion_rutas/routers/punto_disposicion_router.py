"""
Router para gestionar operaciones CRUD en la tabla PuntoDisposicion.
Endpoints para crear, listar, actualizar y eliminar puntos de disposición de residuos.
Usando PostgreSQL directo sin SQLAlchemy
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from ..schemas.schemas import (
    PuntoDisposicionCreate,
    PuntoDisposicionUpdate,
    PuntoDisposicionResponse
)
from ..service.punto_disposicion_service import PuntoDisposicionService

router = APIRouter(prefix="/puntos-disposicion", tags=["Puntos de Disposición"])

punto_disposicion_service = PuntoDisposicionService()


@router.get(
    "/",
    response_model=dict,
    summary="Listar todos los puntos de disposición con paginación y filtros",
    description="Retorna una lista paginada de puntos de disposición"
)
async def get_puntos_disposicion(
    skip: int = Query(0, ge=0, description="Número de registros a saltar"),
    limit: int = Query(10, ge=1, le=100, description="Número máximo de registros a retornar"),
    tipo: Optional[str] = Query(None, description="Filtrar por tipo (relleno, reciclaje, compostaje, etc.)"),
    nombre: Optional[str] = Query(None, description="Filtrar por nombre (búsqueda parcial)"),
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
        puntos, total = punto_disposicion_service.obtener_puntos_disposicion(tipo, nombre, skip, limit)
        return {
            "data": puntos,
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
async def get_punto_disposicion(punto_id: int):
    """
    Obtiene los detalles de un punto de disposición específico por su ID.
    
    **Ejemplo de uso:**
    ```
    GET /puntos-disposicion/1
    ```
    """
    try:
        punto = punto_disposicion_service.obtener_punto_disposicion(punto_id)
        if not punto:
            raise HTTPException(status_code=404, detail=f"Punto de disposición con ID {punto_id} no encontrado")
        return punto
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener punto de disposición: {str(e)}")


@router.post(
    "/",
    response_model=PuntoDisposicionResponse,
    status_code=201,
    summary="Crear un nuevo punto de disposición",
    description="Crea un nuevo registro de punto de disposición"
)
async def create_punto_disposicion(punto: PuntoDisposicionCreate):
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
        return punto_disposicion_service.crear_punto_disposicion(punto.dict())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
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
        punto = punto_disposicion_service.obtener_punto_disposicion(punto_id)
        if not punto:
            raise HTTPException(status_code=404, detail=f"Punto de disposición con ID {punto_id} no encontrado")
        
        return punto_disposicion_service.actualizar_punto_disposicion(punto_id, punto_data.dict(exclude_unset=True))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar punto de disposición: {str(e)}")


@router.delete(
    "/{punto_id}",
    status_code=204,
    summary="Eliminar un punto de disposición",
    description="Elimina un punto de disposición de la base de datos"
)
async def delete_punto_disposicion(punto_id: int):
    """
    Elimina un punto de disposición existente.
    
    **Advertencia:** Esta operación no se puede deshacer.
    
    **Ejemplo de uso:**
    ```
    DELETE /puntos-disposicion/1
    ```
    """
    try:
        resultado = punto_disposicion_service.eliminar_punto_disposicion(punto_id)
        if not resultado:
            raise HTTPException(status_code=404, detail=f"Punto de disposición con ID {punto_id} no encontrado")
        return None
    except Exception as e:
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
        return punto_disposicion_service.obtener_puntos_proximidad(latitud, longitud, radio_km)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al buscar puntos cercanos: {str(e)}")


@router.get(
    "/estadisticas/por-tipo",
    summary="Obtener estadísticas por tipo de disposición",
    description="Retorna conteo y capacidad promedio agrupada por tipo"
)
async def get_estadisticas_por_tipo():
    """
    Obtiene estadísticas de puntos de disposición agrupadas por tipo.
    
    **Ejemplo de uso:**
    ```
    GET /puntos-disposicion/estadisticas/por-tipo
    ```
    """
    try:
        return punto_disposicion_service.obtener_estadisticas_por_tipo()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener estadísticas: {str(e)}")
