"""
Service Layer para Operadores - PostgreSQL Directo
"""

from typing import List, Optional, Dict, Any
from ..database.db import execute_query, execute_query_one, execute_insert_returning, execute_insert_update_delete
import logging

logger = logging.getLogger(__name__)

class OperadorService:
    """Servicio para operaciones con Operadores - PostgreSQL Directo"""

    @staticmethod
    def crear_operador(
        nombre: str,
        email: Optional[str] = None,
        telefono: Optional[str] = None,
        estado: Optional[str] = "activo",
        id_usuario: Optional[int] = None
    ) -> Optional[Dict]:
        """Crear nuevo operador"""
        try:
            query = """
                INSERT INTO operador (nombre, email, telefono, estado, id_usuario)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id_operador, nombre, email, telefono, estado, id_usuario
            """
            resultado = execute_insert_returning(query, (nombre, email, telefono, estado, id_usuario))
            if resultado:
                logger.info(f"Operador {resultado['id_operador']} creado: {nombre}")
            return resultado
        except Exception as e:
            logger.error(f"Error al crear operador: {str(e)}")
            raise

    @staticmethod
    def obtener_operador(operador_id: int) -> Optional[Dict]:
        """Obtener operador por ID"""
        query = "SELECT * FROM operador WHERE id_operador = %s"
        return execute_query_one(query, (operador_id,))

    @staticmethod
    def obtener_operador_por_email(email: str) -> Optional[Dict]:
        """Obtener operador por email"""
        query = "SELECT * FROM operador WHERE email = %s"
        return execute_query_one(query, (email,))

    @staticmethod
    def listar_operadores(skip: int = 0, limit: int = 100) -> List[Dict]:
        """Listar operadores"""
        query = "SELECT * FROM operador ORDER BY id_operador LIMIT %s OFFSET %s"
        return execute_query(query, (limit, skip))

    @staticmethod
    def actualizar_operador(operador_id: int, datos: Dict[str, Any]) -> Optional[Dict]:
        """Actualizar operador"""
        if not datos:
            return OperadorService.obtener_operador(operador_id)
        
        set_clauses = []
        values = []
        for key, value in datos.items():
            set_clauses.append(f"{key} = %s")
            values.append(value)
        
        values.append(operador_id)
        query = f"""
            UPDATE operador
            SET {', '.join(set_clauses)}
            WHERE id_operador = %s
            RETURNING *
        """
        return execute_query_one(query, tuple(values))

    @staticmethod
    def eliminar_operador(operador_id: int) -> bool:
        """Eliminar operador"""
        try:
            query = "DELETE FROM operador WHERE id_operador = %s"
            return execute_insert_update_delete(query, (operador_id,))
        except Exception as e:
            logger.error(f"Error al eliminar operador {operador_id}: {e}")
            raise
