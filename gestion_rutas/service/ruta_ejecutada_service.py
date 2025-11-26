"""
Service Layer para Rutas Ejecutadas - PostgreSQL Directo
"""

from typing import List, Optional, Dict, Any
from datetime import date
from ..database.db import execute_query, execute_query_one, execute_insert_returning, execute_insert_update_delete
import logging

logger = logging.getLogger(__name__)


class RutaEjecutadaService:
    """Servicio para operaciones con Rutas Ejecutadas"""

    @staticmethod
    def crear_ruta_ejecutada(
        id_ruta: int,
        id_camion: int,
        fecha: date,
        distancia_real_km: float,
        duracion_real_min: int,
        cumplimiento_horario_pct: float,
        desviacion_km: Optional[float] = None,
        telemetria_json: Optional[Dict] = None
    ) -> Optional[Dict]:
        """Crear nuevo registro de ruta ejecutada"""
        try:
            query = """
                INSERT INTO ruta_ejecutada (id_ruta, id_camion, fecha, distancia_real_km, duracion_real_min, 
                                           cumplimiento_horario_pct, desviacion_km, telemetria_json)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING *
            """
            resultado = execute_insert_returning(query, (id_ruta, id_camion, fecha, distancia_real_km, 
                                                         duracion_real_min, cumplimiento_horario_pct, 
                                                         desviacion_km, telemetria_json))
            if resultado:
                logger.info(f"Ruta ejecutada {resultado.get('id_ruta_exec')} creada")
            return resultado
        except Exception as e:
            logger.error(f"Error al crear ruta ejecutada: {str(e)}")
            raise

    @staticmethod
    def obtener_ruta_ejecutada(ruta_exec_id: int) -> Optional[Dict]:
        """Obtener ruta ejecutada por ID"""
        query = "SELECT * FROM ruta_ejecutada WHERE id_ruta_exec = %s"
        return execute_query_one(query, (ruta_exec_id,))

    @staticmethod
    def obtener_rutas_ejecutadas(
        id_ruta: Optional[int] = None,
        id_camion: Optional[int] = None,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
        skip: int = 0,
        limit: int = 10
    ) -> tuple[List[Dict], int]:
        """Obtener rutas ejecutadas con filtros"""
        conditions = []
        params = []
        
        if id_ruta:
            conditions.append("id_ruta = %s")
            params.append(id_ruta)
        if id_camion:
            conditions.append("id_camion = %s")
            params.append(id_camion)
        if fecha_desde:
            conditions.append("fecha >= %s")
            params.append(fecha_desde)
        if fecha_hasta:
            conditions.append("fecha <= %s")
            params.append(fecha_hasta)
        
        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
        
        params.extend([skip, limit])
        query = f"SELECT * FROM ruta_ejecutada{where_clause} ORDER BY fecha DESC OFFSET %s LIMIT %s"
        rutas = execute_query(query, tuple(params))
        
        count_query = f"SELECT COUNT(*) as total FROM ruta_ejecutada{where_clause}"
        count_result = execute_query_one(count_query, tuple(params[:-2]) if conditions else ())
        total = count_result['total'] if count_result else 0
        
        return rutas, total

    @staticmethod
    def actualizar_ruta_ejecutada(ruta_exec_id: int, datos: Dict[str, Any]) -> Optional[Dict]:
        """Actualizar datos de una ruta ejecutada"""
        campos = []
        valores = []
        for key, value in datos.items():
            if value is not None:
                campos.append(f"{key} = %s")
                valores.append(value)
        
        if not campos:
            return RutaEjecutadaService.obtener_ruta_ejecutada(ruta_exec_id)
        
        valores.append(ruta_exec_id)
        query = f"UPDATE ruta_ejecutada SET {', '.join(campos)} WHERE id_ruta_exec = %s RETURNING *"
        return execute_insert_returning(query, tuple(valores))

    @staticmethod
    def eliminar_ruta_ejecutada(ruta_exec_id: int) -> bool:
        """Eliminar una ruta ejecutada"""
        query = "DELETE FROM ruta_ejecutada WHERE id_ruta_exec = %s"
        resultado = execute_insert_update_delete(query, (ruta_exec_id,))
        return resultado > 0

    @staticmethod
    def obtener_rutas_por_camion(id_camion: int) -> List[Dict]:
        """Obtener historial de rutas ejecutadas por un camión"""
        query = "SELECT * FROM ruta_ejecutada WHERE id_camion = %s ORDER BY fecha DESC"
        return execute_query(query, (id_camion,))
