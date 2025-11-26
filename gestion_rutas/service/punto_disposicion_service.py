"""
Service Layer para Puntos de Disposición - PostgreSQL Directo
"""

from typing import List, Optional, Dict, Any
from ..database.db import execute_query, execute_query_one, execute_insert_returning, execute_insert_update_delete
import logging

logger = logging.getLogger(__name__)


class PuntoDisposicionService:
    """Servicio para operaciones con Puntos de Disposición"""

    @staticmethod
    def crear_punto(
        nombre: str,
        tipo: str,
        latitud: float,
        longitud: float,
        capacidad_diaria_ton: float
    ) -> Optional[Dict]:
        """Crear nuevo punto de disposición"""
        try:
            query = """
                INSERT INTO punto_disposicion (nombre, tipo, latitud, longitud, capacidad_diaria_ton)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING *
            """
            resultado = execute_insert_returning(query, (nombre, tipo, latitud, longitud, capacidad_diaria_ton))
            if resultado:
                logger.info(f"Punto disposición {resultado.get('id_disposicion')} creado: {nombre}")
            return resultado
        except Exception as e:
            logger.error(f"Error al crear punto: {str(e)}")
            raise

    @staticmethod
    def obtener_punto(punto_id: int) -> Optional[Dict]:
        """Obtener punto de disposición por ID"""
        query = "SELECT * FROM punto_disposicion WHERE id_disposicion = %s"
        return execute_query_one(query, (punto_id,))

    @staticmethod
    def obtener_puntos(
        tipo: Optional[str] = None,
        nombre: Optional[str] = None,
        skip: int = 0,
        limit: int = 10
    ) -> tuple[List[Dict], int]:
        """Obtener puntos de disposición con filtros"""
        conditions = []
        params = []
        
        if tipo:
            conditions.append("tipo = %s")
            params.append(tipo)
        if nombre:
            conditions.append("nombre ILIKE %s")
            params.append(f"%{nombre}%")
        
        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
        
        params.extend([skip, limit])
        query = f"SELECT * FROM punto_disposicion{where_clause} ORDER BY id_disposicion OFFSET %s LIMIT %s"
        puntos = execute_query(query, tuple(params))
        
        count_query = f"SELECT COUNT(*) as total FROM punto_disposicion{where_clause}"
        count_result = execute_query_one(count_query, tuple(params[:-2]) if conditions else ())
        total = count_result['total'] if count_result else 0
        
        return puntos, total

    @staticmethod
    def actualizar_punto(punto_id: int, datos: Dict[str, Any]) -> Optional[Dict]:
        """Actualizar datos de un punto"""
        campos = []
        valores = []
        for key, value in datos.items():
            if value is not None:
                campos.append(f"{key} = %s")
                valores.append(value)
        
        if not campos:
            return PuntoDisposicionService.obtener_punto(punto_id)
        
        valores.append(punto_id)
        query = f"UPDATE punto_disposicion SET {', '.join(campos)} WHERE id_disposicion = %s RETURNING *"
        return execute_insert_returning(query, tuple(valores))

    @staticmethod
    def eliminar_punto(punto_id: int) -> bool:
        """Eliminar un punto de disposición"""
        query = "DELETE FROM punto_disposicion WHERE id_disposicion = %s"
        resultado = execute_insert_update_delete(query, (punto_id,))
        return resultado > 0

    @staticmethod
    def obtener_puntos_por_tipo(tipo: str) -> List[Dict]:
        """Obtener todos los puntos de un tipo específico"""
        query = "SELECT * FROM punto_disposicion WHERE tipo = %s ORDER BY nombre"
        return execute_query(query, (tipo,))
