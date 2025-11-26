"""
Service Layer para Incidencias - PostgreSQL Directo
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from ..database.db import execute_query, execute_query_one, execute_insert_returning, execute_insert_update_delete
import logging

logger = logging.getLogger(__name__)


class IncidenciaService:
    """Servicio para operaciones con Incidencias"""

    @staticmethod
    def crear_incidencia(
        id_ruta_exec: Optional[int],
        id_zona: int,
        id_camion: int,
        tipo: str,
        descripcion: str,
        fecha_hora: datetime,
        severidad: int
    ) -> Optional[Dict]:
        """Crear nueva incidencia"""
        try:
            query = """
                INSERT INTO incidencia (id_ruta_exec, id_zona, id_camion, tipo, descripcion, fecha_hora, severidad)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING *
            """
            resultado = execute_insert_returning(query, (id_ruta_exec, id_zona, id_camion, tipo, descripcion, fecha_hora, severidad))
            if resultado:
                logger.info(f"Incidencia {resultado.get('id_incidencia')} creada")
            return resultado
        except Exception as e:
            logger.error(f"Error al crear incidencia: {str(e)}")
            raise

    @staticmethod
    def obtener_incidencia(incidencia_id: int) -> Optional[Dict]:
        """Obtener incidencia por ID"""
        query = "SELECT * FROM incidencia WHERE id_incidencia = %s"
        return execute_query_one(query, (incidencia_id,))

    @staticmethod
    def obtener_incidencias(
        tipo: Optional[str] = None,
        severidad_min: Optional[int] = None,
        severidad_max: Optional[int] = None,
        id_zona: Optional[int] = None,
        id_camion: Optional[int] = None,
        fecha_desde: Optional[datetime] = None,
        fecha_hasta: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 10
    ) -> tuple[List[Dict], int]:
        """Obtener incidencias con filtros"""
        conditions = []
        params = []
        
        if tipo:
            conditions.append("tipo = %s")
            params.append(tipo)
        if severidad_min:
            conditions.append("severidad >= %s")
            params.append(severidad_min)
        if severidad_max:
            conditions.append("severidad <= %s")
            params.append(severidad_max)
        if id_zona:
            conditions.append("id_zona = %s")
            params.append(id_zona)
        if id_camion:
            conditions.append("id_camion = %s")
            params.append(id_camion)
        if fecha_desde:
            conditions.append("fecha_hora >= %s")
            params.append(fecha_desde)
        if fecha_hasta:
            conditions.append("fecha_hora <= %s")
            params.append(fecha_hasta)
        
        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
        
        params.extend([skip, limit])
        query = f"SELECT * FROM incidencia{where_clause} ORDER BY fecha_hora DESC OFFSET %s LIMIT %s"
        incidencias = execute_query(query, tuple(params))
        
        count_query = f"SELECT COUNT(*) as total FROM incidencia{where_clause}"
        count_result = execute_query_one(count_query, tuple(params[:-2]) if conditions else ())
        total = count_result['total'] if count_result else 0
        
        return incidencias, total

    @staticmethod
    def actualizar_incidencia(incidencia_id: int, datos: Dict[str, Any]) -> Optional[Dict]:
        """Actualizar datos de una incidencia"""
        campos = []
        valores = []
        for key, value in datos.items():
            if value is not None:
                campos.append(f"{key} = %s")
                valores.append(value)
        
        if not campos:
            return IncidenciaService.obtener_incidencia(incidencia_id)
        
        valores.append(incidencia_id)
        query = f"UPDATE incidencia SET {', '.join(campos)} WHERE id_incidencia = %s RETURNING *"
        return execute_insert_returning(query, tuple(valores))

    @staticmethod
    def eliminar_incidencia(incidencia_id: int) -> bool:
        """Eliminar una incidencia"""
        query = "DELETE FROM incidencia WHERE id_incidencia = %s"
        resultado = execute_insert_update_delete(query, (incidencia_id,))
        return resultado > 0

    @staticmethod
    def obtener_incidencias_criticas() -> List[Dict]:
        """Obtener incidencias críticas (severidad = 5)"""
        query = "SELECT * FROM incidencia WHERE severidad = %s ORDER BY fecha_hora DESC"
        return execute_query(query, (5,))

    @staticmethod
    def obtener_estadisticas_por_tipo() -> List[Dict]:
        """Obtener estadísticas de incidencias por tipo"""
        query = "SELECT tipo, COUNT(*) as cantidad FROM incidencia GROUP BY tipo ORDER BY cantidad DESC"
        return execute_query(query, ())

    @staticmethod
    def obtener_estadisticas_por_severidad() -> List[Dict]:
        """Obtener estadísticas de incidencias por severidad"""
        query = "SELECT severidad, COUNT(*) as cantidad FROM incidencia GROUP BY severidad ORDER BY severidad"
        return execute_query(query, ())
