"""
Service Layer para Puntos de Entrega
Usando PostgreSQL directo sin SQLAlchemy
"""

from typing import List, Optional, Dict
from datetime import datetime
from ..database.db import execute_query, execute_query_one, execute_insert_returning, execute_insert_update_delete
import logging
import math

logger = logging.getLogger(__name__)


class PuntoService:
    """Servicio para operaciones con Puntos de Entrega"""

    @staticmethod
    def crear_punto(punto_data: Dict) -> Optional[Dict]:
        """Crear un nuevo punto de entrega"""
        try:
            query = """
                INSERT INTO punto_recoleccion 
                (nombre, descripcion, latitud, longitud, tipo_punto, estado_activo)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id, nombre, descripcion, latitud, longitud, tipo_punto, estado_activo, fecha_creacion
            """
            params = (
                punto_data.get('nombre'),
                punto_data.get('descripcion'),
                punto_data.get('latitud'),
                punto_data.get('longitud'),
                punto_data.get('tipo_punto', 'recoleccion'),
                punto_data.get('estado_activo', True)
            )
            resultado = execute_insert_returning(query, params)
            logger.info(f"Punto creado: {resultado.get('nombre')}")
            return resultado
        except Exception as e:
            logger.error(f"Error al crear punto: {str(e)}")
            raise

    @staticmethod
    def obtener_punto(punto_id: int) -> Optional[Dict]:
        """Obtener punto por ID"""
        query = "SELECT * FROM punto_recoleccion WHERE id = %s"
        return execute_query_one(query, (punto_id,))

    @staticmethod
    def obtener_puntos(
        tipo_punto: Optional[str] = None,
        estado_activo: Optional[bool] = None,
        skip: int = 0,
        limit: int = 10
    ) -> tuple[List[Dict], int]:
        """Obtener puntos con filtros opcionales"""
        where_conditions = []
        params = []

        if tipo_punto:
            where_conditions.append("tipo = %s")
            params.append(tipo_punto)
        if estado_activo is not None:
            # Mapear booleano a estado string si es necesario, o usar la columna correcta
            estado_str = 'activo' if estado_activo else 'inactivo'
            where_conditions.append("estado = %s")
            params.append(estado_str)

        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

        count_query = f"SELECT COUNT(*) as total FROM punto_recoleccion WHERE {where_clause}"
        total_result = execute_query_one(count_query, tuple(params))
        
        # FIX: Usar nombres de columnas correctos según models.py
        query = f"SELECT * FROM punto_recoleccion WHERE {where_clause} ORDER BY id_punto OFFSET %s LIMIT %s"
        params.extend([skip, limit])
        
        puntos = execute_query(query, tuple(params))
        total = total_result['total'] if total_result else 0
        
        return puntos, total
        total = total_result.get('total', 0) if total_result else 0

        query = f"SELECT * FROM punto_recoleccion WHERE {where_clause} LIMIT %s OFFSET %s"
        params.extend([limit, skip])
        puntos = execute_query(query, tuple(params))
        return puntos, total

    @staticmethod
    def actualizar_punto(punto_id: int, punto_data: Dict) -> Optional[Dict]:
        """Actualizar punto de entrega"""
        try:
            if not punto_data:
                return PuntoService.obtener_punto(punto_id)

            set_clauses = []
            params = []
            for key, value in punto_data.items():
                if key not in ['id', 'fecha_creacion']:
                    set_clauses.append(f"{key} = %s")
                    params.append(value)

            if not set_clauses:
                return PuntoService.obtener_punto(punto_id)

            params.append(datetime.utcnow())
            params.append(punto_id)

            query = f"UPDATE punto_recoleccion SET {', '.join(set_clauses)}, fecha_actualizacion = %s WHERE id = %s RETURNING *"
            resultado = execute_insert_returning(query, tuple(params))
            logger.info(f"Punto {punto_id} actualizado")
            return resultado
        except Exception as e:
            logger.error(f"Error al actualizar punto: {str(e)}")
            raise

    @staticmethod
    def eliminar_punto(punto_id: int) -> bool:
        """Eliminar punto de entrega"""
        try:
            query = "DELETE FROM punto_recoleccion WHERE id = %s"
            rowcount = execute_insert_update_delete(query, (punto_id,))
            logger.info(f"Punto {punto_id} eliminado")
            return rowcount > 0
        except Exception as e:
            logger.error(f"Error al eliminar punto: {str(e)}")
            raise

    @staticmethod
    def obtener_puntos_activos() -> List[Dict]:
        """Obtener solo puntos activos"""
        query = "SELECT * FROM punto_recoleccion WHERE estado_activo = TRUE ORDER BY nombre"
        return execute_query(query, ())

    @staticmethod
    def calcular_distancia(
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float
    ) -> float:
        """
        Calcular distancia entre dos puntos usando fórmula Haversine
        Retorna distancia en kilómetros
        """
        R = 6371  # Radio de la Tierra en km
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)

        a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
        c = 2 * math.asin(math.sqrt(a))

        return R * c

    @staticmethod
    def obtener_puntos_cercanos(
        latitud: float,
        longitud: float,
        radio_km: float = 5.0
    ) -> List[Dict]:
        """Obtener puntos cercanos a una coordenada (aproximado)"""
        puntos_activos = PuntoService.obtener_puntos_activos()
        puntos_cercanos = []

        for punto in puntos_activos:
            distancia = PuntoService.calcular_distancia(
                latitud, longitud,
                punto['latitud'], punto['longitud']
            )
            if distancia <= radio_km:
                puntos_cercanos.append(punto)

        return sorted(puntos_cercanos, key=lambda p: PuntoService.calcular_distancia(
            latitud, longitud, p['latitud'], p['longitud']
        ))
