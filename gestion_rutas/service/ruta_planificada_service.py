"""
Service Layer para Rutas Planificadas
Adaptado a los modelos existentes del proyecto
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional, Dict, Any
from datetime import date, datetime
from ..models.models import RutaPlanificada, RutaEjecutada, Zona, Turno, Camion
import logging

logger = logging.getLogger(__name__)


class RutaPlanificadaService:
    """Servicio para operaciones de Rutas Planificadas"""

    @staticmethod
    def crear_ruta(
        db: Session,
        id_zona: int,
        id_turno: int,
        fecha: date,
        secuencia_puntos: List[int],
        distancia_km: Optional[float] = None,
        duracion_min: Optional[float] = None,
        version_vrp: str = "v1.0"
    ) -> RutaPlanificada:
        """Crear una nueva ruta planificada"""
        try:
            nueva_ruta = RutaPlanificada(
                id_zona=id_zona,
                id_turno=id_turno,
                fecha=fecha,
                secuencia_puntos=secuencia_puntos,
                distancia_planificada_km=distancia_km,
                duracion_planificada_min=duracion_min,
                version_modelo_vrp=version_vrp
            )
            db.add(nueva_ruta)
            db.commit()
            db.refresh(nueva_ruta)
            logger.info(f"Ruta {nueva_ruta.id_ruta} creada exitosamente")
            return nueva_ruta
        except Exception as e:
            db.rollback()
            logger.error(f"Error al crear ruta: {str(e)}")
            raise

    @staticmethod
    def obtener_ruta(db: Session, ruta_id: int) -> Optional[RutaPlanificada]:
        """Obtener ruta planificada por ID"""
        return db.query(RutaPlanificada).filter(RutaPlanificada.id_ruta == ruta_id).first()

    @staticmethod
    def obtener_rutas(
        db: Session,
        zona_id: Optional[int] = None,
        turno_id: Optional[int] = None,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
        skip: int = 0,
        limit: int = 10
    ) -> tuple[List[RutaPlanificada], int]:
        """Obtener rutas planificadas con filtros"""
        query = db.query(RutaPlanificada)

        if zona_id:
            query = query.filter(RutaPlanificada.id_zona == zona_id)
        if turno_id:
            query = query.filter(RutaPlanificada.id_turno == turno_id)
        if fecha_desde:
            query = query.filter(RutaPlanificada.fecha >= fecha_desde)
        if fecha_hasta:
            query = query.filter(RutaPlanificada.fecha <= fecha_hasta)

        total = query.count()
        rutas = query.offset(skip).limit(limit).all()
        return rutas, total

    @staticmethod
    def obtener_rutas_por_fecha(db: Session, fecha: date) -> List[RutaPlanificada]:
        """Obtener todas las rutas planificadas para una fecha"""
        return db.query(RutaPlanificada).filter(RutaPlanificada.fecha == fecha).all()

    @staticmethod
    def obtener_rutas_por_zona(db: Session, zona_id: int) -> List[RutaPlanificada]:
        """Obtener rutas de una zona específica"""
        return db.query(RutaPlanificada).filter(RutaPlanificada.id_zona == zona_id).all()

    @staticmethod
    def obtener_rutas_ejecutadas(db: Session, ruta_id: int) -> List[RutaEjecutada]:
        """Obtener todas las ejecuciones de una ruta planificada"""
        return db.query(RutaEjecutada).filter(RutaEjecutada.id_ruta == ruta_id).all()

    @staticmethod
    def calcular_metricas_ruta(db: Session, ruta_id: int) -> Dict[str, Any]:
        """Calcular métricas de una ruta planificada"""
        ruta = RutaPlanificadaService.obtener_ruta(db, ruta_id)
        if not ruta:
            return {}

        ejecuciones = RutaPlanificadaService.obtener_rutas_ejecutadas(db, ruta_id)
        
        metricas = {
            "ruta_id": ruta_id,
            "zona_id": ruta.id_zona,
            "total_ejecuciones": len(ejecuciones),
            "distancia_planificada_km": ruta.distancia_planificada_km or 0,
            "duracion_planificada_min": ruta.duracion_planificada_min or 0,
            "puntos_en_ruta": len(ruta.secuencia_puntos) if ruta.secuencia_puntos else 0,
        }

        if ejecuciones:
            distancias_reales = [e.distancia_real_km for e in ejecuciones if e.distancia_real_km]
            duraciones_reales = [e.duracion_real_min for e in ejecuciones if e.duracion_real_min]
            
            if distancias_reales:
                metricas["distancia_real_promedio"] = sum(distancias_reales) / len(distancias_reales)
                metricas["desviacion_distancia_promedio_km"] = (
                    sum(e.desviacion_km for e in ejecuciones if e.desviacion_km) / len(ejecuciones)
                    if any(e.desviacion_km for e in ejecuciones) else 0
                )
            
            if duraciones_reales:
                metricas["duracion_real_promedio_min"] = sum(duraciones_reales) / len(duraciones_reales)
            
            cumplimientos = [e.cumplimiento_horario_pct for e in ejecuciones if e.cumplimiento_horario_pct]
            if cumplimientos:
                metricas["cumplimiento_horario_promedio_pct"] = sum(cumplimientos) / len(cumplimientos)

        return metricas

    @staticmethod
    def obtener_rutas_proximas(db: Session, dias: int = 7) -> List[RutaPlanificada]:
        """Obtener rutas programadas para los próximos N días"""
        from datetime import timedelta
        hoy = date.today()
        fecha_limite = hoy + timedelta(days=dias)

        return db.query(RutaPlanificada).filter(
            and_(
                RutaPlanificada.fecha >= hoy,
                RutaPlanificada.fecha <= fecha_limite
            )
        ).all()

    @staticmethod
    def actualizar_metricas_ruta(
        db: Session,
        ruta_id: int,
        distancia_km: Optional[float] = None,
        duracion_min: Optional[float] = None
    ) -> Optional[RutaPlanificada]:
        """Actualizar métricas planificadas de una ruta"""
        try:
            ruta = db.query(RutaPlanificada).filter(RutaPlanificada.id_ruta == ruta_id).first()
            if not ruta:
                return None

            if distancia_km is not None:
                ruta.distancia_planificada_km = distancia_km
            if duracion_min is not None:
                ruta.duracion_planificada_min = duracion_min

            db.commit()
            db.refresh(ruta)
            logger.info(f"Métricas de ruta {ruta_id} actualizadas")
            return ruta
        except Exception as e:
            db.rollback()
            logger.error(f"Error al actualizar métricas: {str(e)}")
            raise
