"""
Service Layer para Turnos - PostgreSQL Directo
"""

from typing import List, Optional, Dict, Any
from datetime import date
from ..database.db import execute_query, execute_query_one, execute_insert_returning, execute_insert_update_delete
import logging

logger = logging.getLogger(__name__)


class TurnoService:
    """Servicio para operaciones con Turnos"""

    @staticmethod
    def crear_turno(
        id_camion: int,
        fecha: date,
        hora_inicio: str,
        hora_fin: str,
        operador: str,
        estado: str = "activo"
    ) -> Optional[Dict]:
        """Crear nuevo turno"""
        try:
            query = """
                INSERT INTO turno (id_camion, fecha, hora_inicio, hora_fin, operador, estado)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING *
            """
            resultado = execute_insert_returning(query, (id_camion, fecha, hora_inicio, hora_fin, operador, estado))
            if resultado:
                logger.info(f"Turno {resultado.get('id_turno')} creado")
            return resultado
        except Exception as e:
            logger.error(f"Error al crear turno: {str(e)}")
            raise

    @staticmethod
    def obtener_turno(turno_id: int) -> Optional[Dict]:
        """Obtener turno por ID"""
        query = "SELECT * FROM turno WHERE id_turno = %s"
        return execute_query_one(query, (turno_id,))

    @staticmethod
    def obtener_turnos(
        estado: Optional[str] = None,
        id_camion: Optional[int] = None,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
        skip: int = 0,
        limit: int = 10
    ) -> tuple[List[Dict], int]:
        """Obtener turnos con filtros"""
        conditions = []
        params = []
        
        if estado:
            conditions.append("estado = %s")
            params.append(estado)
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
        query = f"SELECT * FROM turno{where_clause} ORDER BY fecha DESC OFFSET %s LIMIT %s"
        turnos = execute_query(query, tuple(params))
        
        count_query = f"SELECT COUNT(*) as total FROM turno{where_clause}"
        count_result = execute_query_one(count_query, tuple(params[:-2]) if conditions else ())
        total = count_result['total'] if count_result else 0
        
        return turnos, total

    @staticmethod
    def obtener_turnos_por_camion(id_camion: int) -> List[Dict]:
        """Obtener todos los turnos de un camión"""
        query = "SELECT * FROM turno WHERE id_camion = %s ORDER BY fecha DESC"
        return execute_query(query, (id_camion,))

    @staticmethod
    def cambiar_estado_turno(turno_id: int, nuevo_estado: str) -> Optional[Dict]:
        """Cambiar estado del turno"""
        try:
            estados_validos = ["activo", "inactivo", "completado"]
            if nuevo_estado not in estados_validos:
                raise ValueError(f"Estado no válido. Debe ser uno de: {estados_validos}")

            query = "UPDATE turno SET estado = %s WHERE id_turno = %s RETURNING *"
            resultado = execute_insert_returning(query, (nuevo_estado, turno_id))
            if resultado:
                logger.info(f"Turno {turno_id} cambió a estado {nuevo_estado}")
            return resultado
        except Exception as e:
            logger.error(f"Error al cambiar estado: {str(e)}")
            raise

    @staticmethod
    def actualizar_turno(turno_id: int, datos: Dict[str, Any]) -> Optional[Dict]:
        """Actualizar datos de un turno"""
        campos = []
        valores = []
        for key, value in datos.items():
            if value is not None:
                campos.append(f"{key} = %s")
                valores.append(value)
        
        if not campos:
            return TurnoService.obtener_turno(turno_id)
        
        valores.append(turno_id)
        query = f"UPDATE turno SET {', '.join(campos)} WHERE id_turno = %s RETURNING *"
        return execute_insert_returning(query, tuple(valores))

    @staticmethod
    def eliminar_turno(turno_id: int) -> bool:
        """Eliminar un turno"""
        query = "DELETE FROM turno WHERE id_turno = %s"
        resultado = execute_insert_update_delete(query, (turno_id,))
        return resultado > 0
