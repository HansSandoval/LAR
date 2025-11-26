"""
Service Layer para Rutas Planificadas - PostgreSQL Directo
"""

from typing import List, Optional, Dict, Any
from datetime import date
import logging
from ..database.db import execute_query, execute_query_one, execute_insert_returning, execute_insert_update_delete

logger = logging.getLogger(__name__)


class RutaPlanificadaService:
    """Servicio para operaciones de Rutas Planificadas"""

    @staticmethod
    def crear_ruta(
        id_zona: int,
        id_turno: int,
        fecha: date,
        secuencia_puntos: List[int],
        distancia_km: Optional[float] = None,
        duracion_min: Optional[float] = None,
        version_vrp: str = "v1.0"
    ) -> Dict:
        """Crear una nueva ruta planificada"""
        try:
            query = """
                INSERT INTO ruta_planificada 
                (id_zona, id_turno, fecha, secuencia_puntos, 
                 distancia_planificada_km, duracion_planificada_min, version_modelo_vrp)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id_ruta, id_zona, id_turno, fecha, secuencia_puntos,
                          distancia_planificada_km, duracion_planificada_min, version_modelo_vrp
            """
            
            resultado = execute_insert_returning(query, (
                id_zona, id_turno, fecha, secuencia_puntos,
                distancia_km, duracion_min, version_vrp
            ))
            
            logger.info(f"Ruta {resultado['id_ruta']} creada exitosamente")
            return resultado
        except Exception as e:
            logger.error(f"Error al crear ruta: {str(e)}")
            raise

    @staticmethod
    def obtener_ruta(ruta_id: int) -> Optional[Dict]:
        """Obtener ruta planificada por ID"""
        query = """
            SELECT id_ruta, id_zona, id_turno, fecha, secuencia_puntos,
                   distancia_planificada_km, duracion_planificada_min, version_modelo_vrp
            FROM ruta_planificada
            WHERE id_ruta = %s
        """
        
        resultado = execute_query_one(query, (ruta_id,))
        if not resultado:
            logger.warning(f"Ruta {ruta_id} no encontrada")
        return resultado

    @staticmethod
    def obtener_rutas(
        zona_id: Optional[int] = None,
        turno_id: Optional[int] = None,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
        skip: int = 0,
        limit: int = 10
    ) -> tuple:
        """Obtener rutas planificadas con filtros"""
        query = "SELECT * FROM ruta_planificada WHERE 1=1"
        params = []
        
        if zona_id:
            query += " AND id_zona = %s"
            params.append(zona_id)
        if turno_id:
            query += " AND id_turno = %s"
            params.append(turno_id)
        if fecha_desde:
            query += " AND fecha >= %s"
            params.append(fecha_desde)
        if fecha_hasta:
            query += " AND fecha <= %s"
            params.append(fecha_hasta)
        
        # Contar total
        count_query = f"SELECT COUNT(*) as total FROM ({query}) as t"
        count_result = execute_query(count_query, params)
        total = count_result[0]['total'] if count_result else 0
        
        # Obtener paginados
        query += " ORDER BY fecha DESC OFFSET %s LIMIT %s"
        params.extend([skip, limit])
        
        rutas = execute_query(query, params)
        logger.info(f"Obtenidas {len(rutas)} rutas")
        return rutas, total

    @staticmethod
    def actualizar_ruta(ruta_id: int, **kwargs) -> Optional[Dict]:
        """Actualizar ruta planificada"""
        if not kwargs:
            return None
        
        set_clause = ", ".join([f"{key} = %s" for key in kwargs.keys()])
        query = f"""
            UPDATE ruta_planificada
            SET {set_clause}
            WHERE id_ruta = %s
            RETURNING *
        """
        
        valores = list(kwargs.values()) + [ruta_id]
        resultado = execute_insert_returning(query, valores)
        
        if not resultado:
            logger.warning(f"No se pudo actualizar ruta {ruta_id}")
            return None
        
        logger.info(f"Ruta {ruta_id} actualizada")
        return resultado

    @staticmethod
    def eliminar_ruta(ruta_id: int) -> bool:
        """Eliminar ruta planificada"""
        try:
            query = "DELETE FROM ruta_planificada WHERE id_ruta = %s"
            filas = execute_insert_update_delete(query, (ruta_id,))
            logger.info(f"Ruta {ruta_id} eliminada ({filas} filas)")
            return filas > 0
        except Exception as e:
            logger.error(f"Error eliminando ruta {ruta_id}: {str(e)}")
            return False

    @staticmethod
    def obtener_rutas_por_fecha(fecha: date) -> List[Dict]:
        """Obtener todas las rutas planificadas para una fecha"""
        query = "SELECT * FROM ruta_planificada WHERE fecha = %s ORDER BY id_ruta"
        return execute_query(query, (fecha,))

    @staticmethod
    def obtener_rutas_por_zona(zona_id: int) -> List[Dict]:
        """Obtener rutas de una zona específica"""
        query = "SELECT * FROM ruta_planificada WHERE id_zona = %s ORDER BY fecha DESC"
        return execute_query(query, (zona_id,))

    @staticmethod
    def obtener_rutas_ejecutadas(ruta_id: int) -> List[Dict]:
        """Obtener todas las ejecuciones de una ruta planificada"""
        query = "SELECT * FROM ruta_ejecutada WHERE id_ruta = %s ORDER BY fecha DESC"
        return execute_query(query, (ruta_id,))

    @staticmethod
    def calcular_metricas_ruta(ruta_id: int) -> Dict[str, Any]:
        """Calcular métricas de una ruta planificada"""
        ruta = RutaPlanificadaService.obtener_ruta(ruta_id)
        if not ruta:
            return {}

        ejecuciones = RutaPlanificadaService.obtener_rutas_ejecutadas(ruta_id)
        
        metricas = {
            "ruta_id": ruta_id,
            "zona_id": ruta.get('id_zona'),
            "total_ejecuciones": len(ejecuciones),
            "distancia_planificada_km": ruta.get('distancia_planificada_km') or 0,
            "duracion_planificada_min": ruta.get('duracion_planificada_min') or 0,
            "puntos_en_ruta": len(ruta.get('secuencia_puntos', [])) if ruta.get('secuencia_puntos') else 0,
        }

        if ejecuciones:
            distancias_reales = [e.get('distancia_real_km') for e in ejecuciones if e.get('distancia_real_km')]
            duraciones_reales = [e.get('duracion_real_min') for e in ejecuciones if e.get('duracion_real_min')]
            
            if distancias_reales:
                metricas["distancia_real_promedio"] = sum(distancias_reales) / len(distancias_reales)
                desviaciones = [e.get('desviacion_km') for e in ejecuciones if e.get('desviacion_km')]
                metricas["desviacion_distancia_promedio_km"] = sum(desviaciones) / len(desviaciones) if desviaciones else 0
            
            if duraciones_reales:
                metricas["duracion_real_promedio_min"] = sum(duraciones_reales) / len(duraciones_reales)
            
            cumplimientos = [e.get('cumplimiento_horario_pct') for e in ejecuciones if e.get('cumplimiento_horario_pct')]
            if cumplimientos:
                metricas["cumplimiento_horario_promedio_pct"] = sum(cumplimientos) / len(cumplimientos)

        return metricas

    @staticmethod
    def obtener_rutas_proximas(dias: int = 7) -> List[Dict]:
        """Obtener rutas programadas para los próximos N días"""
        from datetime import timedelta
        hoy = date.today()
        fecha_limite = hoy + timedelta(days=dias)
        
        query = """
            SELECT * FROM ruta_planificada 
            WHERE fecha >= %s AND fecha <= %s 
            ORDER BY fecha ASC
        """
        return execute_query(query, (hoy, fecha_limite))

    @staticmethod
    def actualizar_metricas_ruta(
        ruta_id: int,
        distancia_km: Optional[float] = None,
        duracion_min: Optional[float] = None
    ) -> Optional[Dict]:
        """Actualizar métricas planificadas de una ruta"""
        try:
            updates = {}
            if distancia_km is not None:
                updates['distancia_planificada_km'] = distancia_km
            if duracion_min is not None:
                updates['duracion_planificada_min'] = duracion_min
            
            if not updates:
                return RutaPlanificadaService.obtener_ruta(ruta_id)
            
            return RutaPlanificadaService.actualizar_ruta(ruta_id, **updates)
        except Exception as e:
            logger.error(f"Error al actualizar métricas: {str(e)}")
            raise
