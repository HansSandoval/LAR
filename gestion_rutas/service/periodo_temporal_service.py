"""
Service Layer para Periodos Temporales - PostgreSQL Directo
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from ..database.db import execute_query, execute_query_one, execute_insert_returning, execute_insert_update_delete
import logging

logger = logging.getLogger(__name__)


class PeriodoTemporalService:
    """Servicio para operaciones con Periodos Temporales"""

    @staticmethod
    def crear_periodo(
        fecha_inicio: datetime,
        fecha_fin: datetime,
        tipo_granularidad: str,
        estacionalidad: str = "general"
    ) -> Optional[Dict]:
        """Crear nuevo periodo temporal"""
        try:
            query = """
                INSERT INTO periodo_temporal (fecha_inicio, fecha_fin, tipo_granularidad, estacionalidad)
                VALUES (%s, %s, %s, %s)
                RETURNING *
            """
            resultado = execute_insert_returning(query, (fecha_inicio, fecha_fin, tipo_granularidad, estacionalidad))
            if resultado:
                logger.info(f"Período {resultado.get('id_periodo')} creado")
            return resultado
        except Exception as e:
            logger.error(f"Error al crear período: {str(e)}")
            raise

    @staticmethod
    def obtener_periodo(periodo_id: int) -> Optional[Dict]:
        """Obtener período temporal por ID"""
        query = "SELECT * FROM periodo_temporal WHERE id_periodo = %s"
        return execute_query_one(query, (periodo_id,))

    @staticmethod
    def obtener_periodos(
        tipo_granularidad: Optional[str] = None,
        estacionalidad: Optional[str] = None,
        skip: int = 0,
        limit: int = 10
    ) -> tuple[List[Dict], int]:
        """Obtener períodos temporales con filtros"""
        conditions = []
        params = []
        
        if tipo_granularidad:
            conditions.append("tipo_granularidad = %s")
            params.append(tipo_granularidad)
        if estacionalidad:
            conditions.append("estacionalidad = %s")
            params.append(estacionalidad)
        
        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
        
        params.extend([skip, limit])
        query = f"SELECT * FROM periodo_temporal{where_clause} ORDER BY fecha_inicio DESC OFFSET %s LIMIT %s"
        periodos = execute_query(query, tuple(params))
        
        count_query = f"SELECT COUNT(*) as total FROM periodo_temporal{where_clause}"
        count_result = execute_query_one(count_query, tuple(params[:-2]) if conditions else ())
        total = count_result['total'] if count_result else 0
        
        return periodos, total

    @staticmethod
    def actualizar_periodo(periodo_id: int, datos: Dict[str, Any]) -> Optional[Dict]:
        """Actualizar datos de un período"""
        campos = []
        valores = []
        for key, value in datos.items():
            if value is not None:
                campos.append(f"{key} = %s")
                valores.append(value)
        
        if not campos:
            return PeriodoTemporalService.obtener_periodo(periodo_id)
        
        valores.append(periodo_id)
        query = f"UPDATE periodo_temporal SET {', '.join(campos)} WHERE id_periodo = %s RETURNING *"
        return execute_insert_returning(query, tuple(valores))

    @staticmethod
    def eliminar_periodo(periodo_id: int) -> bool:
        """Eliminar un período temporal"""
        query = "DELETE FROM periodo_temporal WHERE id_periodo = %s"
        resultado = execute_insert_update_delete(query, (periodo_id,))
        return resultado > 0

    @staticmethod
    def obtener_periodos_por_granularidad(tipo_granularidad: str) -> List[Dict]:
        """Obtener todos los períodos de una granularidad específica"""
        query = "SELECT * FROM periodo_temporal WHERE tipo_granularidad = %s ORDER BY fecha_inicio DESC"
        return execute_query(query, (tipo_granularidad,))

    @staticmethod
    def obtener_periodos_por_estacionalidad(estacionalidad: str) -> List[Dict]:
        """Obtener todos los períodos de una estacionalidad específica"""
        query = "SELECT * FROM periodo_temporal WHERE estacionalidad = %s ORDER BY fecha_inicio DESC"
        return execute_query(query, (estacionalidad,))
