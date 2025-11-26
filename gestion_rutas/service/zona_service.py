"""
Service Layer para Zonas - PostgreSQL Directo
"""

from typing import List, Optional, Dict
import logging
from ..database.db import execute_query, execute_query_one, execute_insert_returning, execute_insert_update_delete

logger = logging.getLogger(__name__)


class ZonaService:
    """Servicio para operaciones con Zonas"""

    @staticmethod
    def crear_zona(
        nombre: str,
        tipo: str,
        area_km2: float,
        poblacion: int,
        prioridad: int = 1
    ) -> Dict:
        """Crear nueva zona"""
        try:
            query = """
                INSERT INTO zona (nombre, tipo, area_km2, poblacion, prioridad)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id_zona, nombre, tipo, area_km2, poblacion, prioridad
            """
            
            resultado = execute_insert_returning(query, (
                nombre, tipo, area_km2, poblacion, prioridad
            ))
            
            logger.info(f"Zona {resultado['id_zona']} creada exitosamente")
            return resultado
        except Exception as e:
            logger.error(f"Error al crear zona: {str(e)}")
            raise

    @staticmethod
    def obtener_zona(zona_id: int) -> Optional[Dict]:
        """Obtener zona por ID"""
        query = "SELECT id_zona, nombre, tipo, area_km2, poblacion, prioridad FROM zona WHERE id_zona = %s"
        resultado = execute_query_one(query, (zona_id,))
        if not resultado:
            logger.warning(f"Zona {zona_id} no encontrada")
        return resultado

    @staticmethod
    def obtener_todas_zonas() -> List[Dict]:
        """Obtener todas las zonas"""
        query = "SELECT id_zona, nombre, tipo, area_km2, poblacion, prioridad FROM zona ORDER BY prioridad, nombre"
        resultados = execute_query(query)
        logger.info(f"Obtenidas {len(resultados)} zonas")
        return resultados

    @staticmethod
    def actualizar_zona(zona_id: int, **kwargs) -> Optional[Dict]:
        """Actualizar zona"""
        if not kwargs:
            return None
        
        set_clause = ", ".join([f"{key} = %s" for key in kwargs.keys()])
        query = f"""
            UPDATE zona
            SET {set_clause}
            WHERE id_zona = %s
            RETURNING *
        """
        
        valores = list(kwargs.values()) + [zona_id]
        resultado = execute_insert_returning(query, valores)
        
        if not resultado:
            logger.warning(f"No se pudo actualizar zona {zona_id}")
            return None
        
        logger.info(f"Zona {zona_id} actualizada")
        return resultado

    @staticmethod
    def eliminar_zona(zona_id: int) -> bool:
        """Eliminar zona"""
        try:
            query = "DELETE FROM zona WHERE id_zona = %s"
            filas = execute_insert_update_delete(query, (zona_id,))
            logger.info(f"Zona {zona_id} eliminada ({filas} filas)")
            return filas > 0
        except Exception as e:
            logger.error(f"Error eliminando zona {zona_id}: {str(e)}")
            return False

    @staticmethod
    def obtener_zonas_por_prioridad() -> List[Dict]:
        """Obtener zonas ordenadas por prioridad (mayor primero)"""
        query = "SELECT id_zona, nombre, tipo, area_km2, poblacion, prioridad FROM zona ORDER BY prioridad DESC, nombre"
        return execute_query(query)

    @staticmethod
    def obtener_zonas_con_filtro(tipo: Optional[str] = None, skip: int = 0, limit: int = 10) -> tuple[List[Dict], int]:
        """Obtener zonas con filtros"""
        if tipo:
            query_count = "SELECT COUNT(*) as total FROM zona WHERE tipo = %s"
            query = "SELECT id_zona, nombre, tipo, area_km2, poblacion, prioridad FROM zona WHERE tipo = %s ORDER BY prioridad LIMIT %s OFFSET %s"
            total = execute_query_one(query_count, (tipo,))
            resultados = execute_query(query, (tipo, limit, skip))
        else:
            query_count = "SELECT COUNT(*) as total FROM zona"
            query = "SELECT id_zona, nombre, tipo, area_km2, poblacion, prioridad FROM zona ORDER BY prioridad LIMIT %s OFFSET %s"
            total = execute_query_one(query_count, ())
            resultados = execute_query(query, (limit, skip))
        
        total_count = total['total'] if total else 0
        return resultados, total_count

    @staticmethod
    def calcular_metricas_zona(zona_id: int) -> Dict:
        """Calcular métricas de una zona"""
        zona_query = "SELECT * FROM zona WHERE id_zona = %s"
        zona = execute_query_one(zona_query, (zona_id,))
        
        if not zona:
            return {}

        puntos_query = "SELECT COUNT(*) as total FROM punto_recoleccion WHERE id_zona = %s"
        puntos_count = execute_query_one(puntos_query, (zona_id,))
        
        rutas_query = "SELECT COUNT(*) as total FROM ruta_planificada WHERE id_zona = %s"
        rutas_count = execute_query_one(rutas_query, (zona_id,))
        
        capacidad_query = "SELECT SUM(capacidad_kg) as total FROM punto_recoleccion WHERE id_zona = %s AND estado_activo = true"
        capacidad_data = execute_query_one(capacidad_query, (zona_id,))
        capacidad_total = capacidad_data['total'] if capacidad_data and capacidad_data['total'] else 0

        metricas = {
            "zona_id": zona_id,
            "nombre": zona.get('nombre'),
            "tipo": zona.get('tipo'),
            "area_km2": zona.get('area_km2'),
            "poblacion": zona.get('poblacion'),
            "prioridad": zona.get('prioridad'),
            "total_puntos": puntos_count.get('total', 0) if puntos_count else 0,
            "total_rutas_planificadas": rutas_count.get('total', 0) if rutas_count else 0,
            "capacidad_total_kg": capacidad_total
        }

        return metricas
