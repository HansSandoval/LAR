"""
Service Layer para Camiones (Vehículos) - PostgreSQL Directo
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, date
from ..database.db import execute_query, execute_query_one, execute_insert_returning, execute_insert_update_delete
import logging

logger = logging.getLogger(__name__)


class CamionService:
    """Servicio para operaciones con Camiones - PostgreSQL Directo"""

    @staticmethod
    def crear_camion(
        patente: str,
        capacidad_kg: float,
        consumo_km_l: float = 10.0,
        tipo_combustible: str = "diesel",
        gps_id: Optional[str] = None
    ) -> Optional[Dict]:
        """Crear nuevo camión"""
        try:
            query = """
                INSERT INTO camion (patente, capacidad_kg, consumo_km_l, tipo_combustible, estado_operativo, gps_id)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id_camion, patente, capacidad_kg, consumo_km_l, tipo_combustible, estado_operativo, gps_id
            """
            resultado = execute_insert_returning(query, (patente, capacidad_kg, consumo_km_l, tipo_combustible, "disponible", gps_id))
            if resultado:
                logger.info(f"Camión {resultado['id_camion']} creado: {patente}")
            return resultado
        except Exception as e:
            logger.error(f"Error al crear camión: {str(e)}")
            raise

    @staticmethod
    def obtener_camion(camion_id: int) -> Optional[Dict]:
        """Obtener camión por ID"""
        query = "SELECT * FROM camion WHERE id_camion = %s"
        return execute_query_one(query, (camion_id,))

    @staticmethod
    def obtener_camion_por_patente(patente: str) -> Optional[Dict]:
        """Obtener camión por patente"""
        query = "SELECT * FROM camion WHERE patente = %s"
        return execute_query_one(query, (patente,))

    @staticmethod
    def obtener_camiones(
        estado: Optional[str] = None,
        skip: int = 0,
        limit: int = 10
    ) -> tuple[List[Dict], int]:
        """Obtener camiones con filtros"""
        if estado:
            # FIX: SQLite syntax compatibility
            # Postgres: OFFSET %s LIMIT %s
            # SQLite: LIMIT %s OFFSET %s
            # We use a neutral placeholder that db.py will intercept and rewrite correctly
            query = "SELECT * FROM camion WHERE estado_operativo = %s ORDER BY id_camion OFFSET %s LIMIT %s"
            params = (estado, skip, limit)
            count_query = "SELECT COUNT(*) as total FROM camion WHERE estado_operativo = %s"
            count_result = execute_query_one(count_query, (estado,))
        else:
            # FIX: SQLite syntax compatibility
            query = "SELECT * FROM camion ORDER BY id_camion OFFSET %s LIMIT %s"
            params = (skip, limit)
            count_query = "SELECT COUNT(*) as total FROM camion"
            count_result = execute_query_one(count_query, ())
        
        camiones = execute_query(query, params)
        total = count_result['total'] if count_result else 0
        return camiones, total

    @staticmethod
    def obtener_camiones_disponibles() -> List[Dict]:
        """Obtener camiones disponibles"""
        query = "SELECT * FROM camion WHERE estado_operativo = %s ORDER BY id_camion"
        return execute_query(query, ("disponible",))

    @staticmethod
    def obtener_camiones_en_servicio() -> List[Dict]:
        """Obtener camiones actualmente en servicio"""
        query = "SELECT * FROM camion WHERE estado_operativo = %s ORDER BY id_camion"
        return execute_query(query, ("en_servicio",))

    @staticmethod
    def cambiar_estado_camion(camion_id: int, nuevo_estado: str) -> Optional[Dict]:
        """Cambiar estado del camión"""
        try:
            estados_validos = ["disponible", "en_servicio", "mantenimiento", "inactivo"]
            if nuevo_estado not in estados_validos:
                raise ValueError(f"Estado no válido. Debe ser uno de: {estados_validos}")

            query = "UPDATE camion SET estado_operativo = %s WHERE id_camion = %s RETURNING *"
            resultado = execute_insert_returning(query, (nuevo_estado, camion_id))
            if resultado:
                logger.info(f"Camión {camion_id} cambió a estado {nuevo_estado}")
            return resultado
        except Exception as e:
            logger.error(f"Error al cambiar estado: {str(e)}")
            raise

    @staticmethod
    def obtener_rutas_ejecutadas_camion(camion_id: int) -> List[Dict]:
        """Obtener historial de rutas ejecutadas por un camión"""
        query = "SELECT * FROM ruta_ejecutada WHERE id_camion = %s ORDER BY fecha DESC"
        return execute_query(query, (camion_id,))

    @staticmethod
    def calcular_metricas_camion(camion_id: int) -> Dict[str, Any]:
        """Calcular métricas de desempeño del camión"""
        camion = CamionService.obtener_camion(camion_id)
        if not camion:
            return {}

        rutas = CamionService.obtener_rutas_ejecutadas_camion(camion_id)
        
        metricas = {
            "camion_id": camion_id,
            "patente": camion.get('patente'),
            "capacidad_kg": camion.get('capacidad_kg'),
            "estado": camion.get('estado_operativo'),
            "total_rutas_ejecutadas": len(rutas),
        }

        if rutas:
            distancias = [r.get('distancia_real_km') for r in rutas if r.get('distancia_real_km')]
            duraciones = [r.get('duracion_real_min') for r in rutas if r.get('duracion_real_min')]
            
            if distancias:
                metricas["distancia_total_km"] = sum(distancias)
                metricas["distancia_promedio_km"] = sum(distancias) / len(distancias)
                metricas["distancia_maxima_km"] = max(distancias)
                
                consumo_km_l = camion.get('consumo_km_l', 10.0)
                consumo_total_litros = metricas["distancia_total_km"] / consumo_km_l
                metricas["consumo_total_litros"] = consumo_total_litros
                metricas["costo_combustible_estimado"] = consumo_total_litros * 700
            
            if duraciones:
                metricas["duracion_total_minutos"] = sum(duraciones)
                metricas["duracion_promedio_minutos"] = sum(duraciones) / len(duraciones)
            
            cumplimientos = [r.get('cumplimiento_horario_pct') for r in rutas if r.get('cumplimiento_horario_pct')]
            if cumplimientos:
                metricas["cumplimiento_horario_promedio_pct"] = sum(cumplimientos) / len(cumplimientos)

        return metricas

    @staticmethod
    def obtener_carga_promedio_camion(camion_id: int, dias: int = 30) -> Dict[str, Any]:
        """Obtener carga promedio del camión en últimos N días"""
        from datetime import timedelta
        fecha_limite = date.today() - timedelta(days=dias)
        
        query = "SELECT * FROM ruta_ejecutada WHERE id_camion = %s AND fecha >= %s ORDER BY fecha DESC"
        rutas = execute_query(query, (camion_id, fecha_limite))

        if not rutas:
            return {"camion_id": camion_id, "carga_promedio": 0}

        # Nota: se asume que telemetria_json es JSON en PostgreSQL
        # Si está como string, necesitarías parsearlo
        cargas = []
        for r in rutas:
            try:
                telemetria = r.get('telemetria_json', {})
                if isinstance(telemetria, str):
                    import json
                    telemetria = json.loads(telemetria)
                cargas.append(telemetria.get("carga_kg", 0) if telemetria else 0)
            except:
                cargas.append(0)
        
        camion = CamionService.obtener_camion(camion_id)
        capacidad = camion.get('capacidad_kg', 1) if camion else 1
        
        return {
            "camion_id": camion_id,
            "periodo_dias": dias,
            "rutas_analizadas": len(rutas),
            "carga_promedio_kg": sum(cargas) / len(cargas) if cargas else 0,
            "carga_maxima_kg": max(cargas) if cargas else 0,
            "utilidad_promedio_pct": (sum(cargas) / len(cargas) / capacidad * 100) if cargas else 0
        }

    @staticmethod
    def actualizar_camion(camion_id: int, datos: Dict[str, Any]) -> Optional[Dict]:
        """Actualizar datos de un camión"""
        campos = []
        valores = []
        for key, value in datos.items():
            if value is not None:
                campos.append(f"{key} = %s")
                valores.append(value)
        
        if not campos:
            return CamionService.obtener_camion(camion_id)
        
        valores.append(camion_id)
        query = f"UPDATE camion SET {', '.join(campos)} WHERE id_camion = %s RETURNING *"
        return execute_insert_returning(query, tuple(valores))

    @staticmethod
    def eliminar_camion(camion_id: int) -> bool:
        """Eliminar un camión"""
        query = "DELETE FROM camion WHERE id_camion = %s"
        resultado = execute_insert_update_delete(query, (camion_id,))
        return resultado > 0
