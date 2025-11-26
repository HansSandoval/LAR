"""
Service Layer para Predicciones de Demanda - PostgreSQL Directo
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from ..database.db import execute_query, execute_query_one, execute_insert_returning, execute_insert_update_delete
import logging

logger = logging.getLogger(__name__)


class PrediccionDemandaService:
    """Servicio para operaciones con Predicciones de Demanda"""

    @staticmethod
    def crear_prediccion(
        id_zona: int,
        horizonte_horas: int,
        fecha_prediccion: datetime,
        valor_predicho_kg: float,
        valor_real_kg: Optional[float] = None,
        modelo_lstm_version: str = "v1.0",
        error_rmse: Optional[float] = None,
        error_mape: Optional[float] = None
    ) -> Optional[Dict]:
        """Crear nueva predicción de demanda"""
        try:
            query = """
                INSERT INTO prediccion_demanda 
                (id_zona, horizonte_horas, fecha_prediccion, valor_predicho_kg, valor_real_kg, 
                 modelo_lstm_version, error_rmse, error_mape)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING *
            """
            resultado = execute_insert_returning(query, (id_zona, horizonte_horas, fecha_prediccion, 
                                                         valor_predicho_kg, valor_real_kg, 
                                                         modelo_lstm_version, error_rmse, error_mape))
            if resultado:
                logger.info(f"Predicción {resultado.get('id_prediccion')} creada")
            return resultado
        except Exception as e:
            logger.error(f"Error al crear predicción: {str(e)}")
            raise

    @staticmethod
    def obtener_prediccion(prediccion_id: int) -> Optional[Dict]:
        """Obtener predicción por ID"""
        query = "SELECT * FROM prediccion_demanda WHERE id_prediccion = %s"
        return execute_query_one(query, (prediccion_id,))

    @staticmethod
    def obtener_predicciones(
        id_zona: Optional[int] = None,
        horizonte_horas: Optional[int] = None,
        fecha_desde: Optional[datetime] = None,
        fecha_hasta: Optional[datetime] = None,
        modelo_version: Optional[str] = None,
        skip: int = 0,
        limit: int = 10
    ) -> tuple[List[Dict], int]:
        """Obtener predicciones con filtros"""
        conditions = []
        params = []
        
        if id_zona:
            conditions.append("id_zona = %s")
            params.append(id_zona)
        if horizonte_horas:
            conditions.append("horizonte_horas = %s")
            params.append(horizonte_horas)
        if fecha_desde:
            conditions.append("fecha_prediccion >= %s")
            params.append(fecha_desde)
        if fecha_hasta:
            conditions.append("fecha_prediccion <= %s")
            params.append(fecha_hasta)
        if modelo_version:
            conditions.append("modelo_lstm_version = %s")
            params.append(modelo_version)
        
        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
        
        params.extend([skip, limit])
        query = f"SELECT * FROM prediccion_demanda{where_clause} ORDER BY fecha_prediccion DESC OFFSET %s LIMIT %s"
        predicciones = execute_query(query, tuple(params))
        
        count_query = f"SELECT COUNT(*) as total FROM prediccion_demanda{where_clause}"
        count_result = execute_query_one(count_query, tuple(params[:-2]) if conditions else ())
        total = count_result['total'] if count_result else 0
        
        return predicciones, total

    @staticmethod
    def actualizar_prediccion(prediccion_id: int, datos: Dict[str, Any]) -> Optional[Dict]:
        """Actualizar datos de una predicción"""
        campos = []
        valores = []
        for key, value in datos.items():
            if value is not None:
                campos.append(f"{key} = %s")
                valores.append(value)
        
        if not campos:
            return PrediccionDemandaService.obtener_prediccion(prediccion_id)
        
        valores.append(prediccion_id)
        query = f"UPDATE prediccion_demanda SET {', '.join(campos)} WHERE id_prediccion = %s RETURNING *"
        return execute_insert_returning(query, tuple(valores))

    @staticmethod
    def eliminar_prediccion(prediccion_id: int) -> bool:
        """Eliminar una predicción"""
        query = "DELETE FROM prediccion_demanda WHERE id_prediccion = %s"
        resultado = execute_insert_update_delete(query, (prediccion_id,))
        return resultado > 0

    @staticmethod
    def obtener_predicciones_por_zona(id_zona: int) -> List[Dict]:
        """Obtener todas las predicciones de una zona"""
        query = "SELECT * FROM prediccion_demanda WHERE id_zona = %s ORDER BY fecha_prediccion DESC"
        return execute_query(query, (id_zona,))
