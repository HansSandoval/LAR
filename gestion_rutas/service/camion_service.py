"""
Service Layer para Camiones (Vehículos)
"""

from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from models.models import Camion, RutaEjecutada
import logging

logger = logging.getLogger(__name__)


class CamionService:
    """Servicio para operaciones con Camiones"""

    @staticmethod
    def crear_camion(
        db: Session,
        patente: str,
        capacidad_kg: float,
        consumo_km_l: float = 10.0,
        tipo_combustible: str = "diesel",
        gps_id: Optional[str] = None
    ) -> Camion:
        """Crear nuevo camión"""
        try:
            nuevo_camion = Camion(
                patente=patente,
                capacidad_kg=capacidad_kg,
                consumo_km_l=consumo_km_l,
                tipo_combustible=tipo_combustible,
                estado_operativo="disponible",
                gps_id=gps_id
            )
            db.add(nuevo_camion)
            db.commit()
            db.refresh(nuevo_camion)
            logger.info(f"Camión {nuevo_camion.id_camion} creado: {patente}")
            return nuevo_camion
        except Exception as e:
            db.rollback()
            logger.error(f"Error al crear camión: {str(e)}")
            raise

    @staticmethod
    def obtener_camion(db: Session, camion_id: int) -> Optional[Camion]:
        """Obtener camión por ID"""
        return db.query(Camion).filter(Camion.id_camion == camion_id).first()

    @staticmethod
    def obtener_camion_por_patente(db: Session, patente: str) -> Optional[Camion]:
        """Obtener camión por patente"""
        return db.query(Camion).filter(Camion.patente == patente).first()

    @staticmethod
    def obtener_camiones(
        db: Session,
        estado: Optional[str] = None,
        skip: int = 0,
        limit: int = 10
    ) -> tuple[List[Camion], int]:
        """Obtener camiones con filtros"""
        query = db.query(Camion)

        if estado:
            query = query.filter(Camion.estado_operativo == estado)

        total = query.count()
        camiones = query.offset(skip).limit(limit).all()
        return camiones, total

    @staticmethod
    def obtener_camiones_disponibles(db: Session) -> List[Camion]:
        """Obtener camiones disponibles"""
        return db.query(Camion).filter(Camion.estado_operativo == "disponible").all()

    @staticmethod
    def obtener_camiones_en_servicio(db: Session) -> List[Camion]:
        """Obtener camiones actualmente en servicio"""
        return db.query(Camion).filter(Camion.estado_operativo == "en_servicio").all()

    @staticmethod
    def cambiar_estado_camion(
        db: Session,
        camion_id: int,
        nuevo_estado: str
    ) -> Optional[Camion]:
        """Cambiar estado del camión"""
        try:
            camion = db.query(Camion).filter(Camion.id_camion == camion_id).first()
            if not camion:
                return None

            estados_validos = ["disponible", "en_servicio", "mantenimiento", "inactivo"]
            if nuevo_estado not in estados_validos:
                raise ValueError(f"Estado no válido. Debe ser uno de: {estados_validos}")

            camion.estado_operativo = nuevo_estado
            db.commit()
            db.refresh(camion)
            logger.info(f"Camión {camion_id} cambió a estado {nuevo_estado}")
            return camion
        except Exception as e:
            db.rollback()
            logger.error(f"Error al cambiar estado: {str(e)}")
            raise

    @staticmethod
    def obtener_rutas_ejecutadas_camion(db: Session, camion_id: int) -> List[RutaEjecutada]:
        """Obtener historial de rutas ejecutadas por un camión"""
        return db.query(RutaEjecutada).filter(RutaEjecutada.id_camion == camion_id).all()

    @staticmethod
    def calcular_metricas_camion(db: Session, camion_id: int) -> Dict[str, Any]:
        """Calcular métricas de desempeño del camión"""
        camion = CamionService.obtener_camion(db, camion_id)
        if not camion:
            return {}

        rutas = CamionService.obtener_rutas_ejecutadas_camion(db, camion_id)
        
        metricas = {
            "camion_id": camion_id,
            "patente": camion.patente,
            "capacidad_kg": camion.capacidad_kg,
            "estado": camion.estado_operativo,
            "total_rutas_ejecutadas": len(rutas),
        }

        if rutas:
            distancias = [r.distancia_real_km for r in rutas if r.distancia_real_km]
            duraciones = [r.duracion_real_min for r in rutas if r.duracion_real_min]
            
            if distancias:
                metricas["distancia_total_km"] = sum(distancias)
                metricas["distancia_promedio_km"] = sum(distancias) / len(distancias)
                metricas["distancia_maxima_km"] = max(distancias)
                
                # Estimar costo de combustible
                consumo_total_litros = metricas["distancia_total_km"] / camion.consumo_km_l
                metricas["consumo_total_litros"] = consumo_total_litros
                metricas["costo_combustible_estimado"] = consumo_total_litros * 700  # $700/litro
            
            if duraciones:
                metricas["duracion_total_minutos"] = sum(duraciones)
                metricas["duracion_promedio_minutos"] = sum(duraciones) / len(duraciones)
            
            cumplimientos = [r.cumplimiento_horario_pct for r in rutas if r.cumplimiento_horario_pct]
            if cumplimientos:
                metricas["cumplimiento_horario_promedio_pct"] = sum(cumplimientos) / len(cumplimientos)

        return metricas

    @staticmethod
    def obtener_carga_promedio_camion(db: Session, camion_id: int, dias: int = 30) -> Dict[str, Any]:
        """Obtener carga promedio del camión en últimos N días"""
        from datetime import timedelta
        fecha_limite = date.today() - timedelta(days=dias)
        
        rutas = db.query(RutaEjecutada).filter(
            RutaEjecutada.id_camion == camion_id,
            RutaEjecutada.fecha >= fecha_limite
        ).all()

        if not rutas:
            return {"camion_id": camion_id, "carga_promedio": 0}

        cargas = [r.telemetria_json.get("carga_kg", 0) if r.telemetria_json else 0 for r in rutas]
        
        return {
            "camion_id": camion_id,
            "periodo_dias": dias,
            "rutas_analizadas": len(rutas),
            "carga_promedio_kg": sum(cargas) / len(cargas) if cargas else 0,
            "carga_maxima_kg": max(cargas) if cargas else 0,
            "utilidad_promedio_pct": (sum(cargas) / len(cargas) / 
                                     CamionService.obtener_camion(db, camion_id).capacidad_kg * 100) if cargas else 0
        }
