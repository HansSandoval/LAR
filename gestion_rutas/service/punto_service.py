"""
Service Layer para Puntos de Entrega
"""

from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from models.base import Punto
from schemas.schemas import PuntoCreate, PuntoUpdate
import logging

logger = logging.getLogger(__name__)


class PuntoService:
    """Servicio para operaciones con Puntos de Entrega"""

    @staticmethod
    def crear_punto(db: Session, punto_data: PuntoCreate) -> Punto:
        """Crear un nuevo punto de entrega"""
        try:
            nuevo_punto = Punto(
                nombre=punto_data.nombre,
                descripcion=punto_data.descripcion,
                latitud=punto_data.latitud,
                longitud=punto_data.longitud,
                tipo_punto=punto_data.tipo_punto,
                estado_activo=punto_data.estado_activo
            )
            db.add(nuevo_punto)
            db.commit()
            db.refresh(nuevo_punto)
            logger.info(f"Punto {nuevo_punto.id} creado: {nuevo_punto.nombre}")
            return nuevo_punto
        except Exception as e:
            db.rollback()
            logger.error(f"Error al crear punto: {str(e)}")
            raise

    @staticmethod
    def obtener_punto(db: Session, punto_id: int) -> Optional[Punto]:
        """Obtener punto por ID"""
        return db.query(Punto).filter(Punto.id == punto_id).first()

    @staticmethod
    def obtener_puntos(
        db: Session,
        tipo_punto: Optional[str] = None,
        estado_activo: Optional[bool] = None,
        skip: int = 0,
        limit: int = 10
    ) -> tuple[List[Punto], int]:
        """Obtener puntos con filtros opcionales"""
        query = db.query(Punto)

        if tipo_punto:
            query = query.filter(Punto.tipo_punto == tipo_punto)
        if estado_activo is not None:
            query = query.filter(Punto.estado_activo == estado_activo)

        total = query.count()
        puntos = query.offset(skip).limit(limit).all()
        return puntos, total

    @staticmethod
    def actualizar_punto(db: Session, punto_id: int, punto_data: PuntoUpdate) -> Optional[Punto]:
        """Actualizar punto de entrega"""
        try:
            punto = db.query(Punto).filter(Punto.id == punto_id).first()
            if not punto:
                return None

            for campo, valor in punto_data.dict(exclude_unset=True).items():
                setattr(punto, campo, valor)

            punto.fecha_actualizacion = datetime.utcnow()
            db.commit()
            db.refresh(punto)
            logger.info(f"Punto {punto_id} actualizado")
            return punto
        except Exception as e:
            db.rollback()
            logger.error(f"Error al actualizar punto: {str(e)}")
            raise

    @staticmethod
    def obtener_puntos_activos(db: Session) -> List[Punto]:
        """Obtener solo puntos activos"""
        return db.query(Punto).filter(Punto.estado_activo == True).all()

    @staticmethod
    def calcular_distancia(
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float
    ) -> float:
        """
        Calcular distancia entre dos puntos usando fórmula Haversine
        Retorna distancia en kilómetros
        """
        import math
        
        R = 6371  # Radio de la Tierra en km
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)

        a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
        c = 2 * math.asin(math.sqrt(a))

        return R * c

    @staticmethod
    def obtener_puntos_cercanos(
        db: Session,
        latitud: float,
        longitud: float,
        radio_km: float = 5.0
    ) -> List[Punto]:
        """Obtener puntos cercanos a una coordenada (aproximado)"""
        puntos_activos = PuntoService.obtener_puntos_activos(db)
        puntos_cercanos = []

        for punto in puntos_activos:
            distancia = PuntoService.calcular_distancia(
                latitud, longitud,
                punto.latitud, punto.longitud
            )
            if distancia <= radio_km:
                puntos_cercanos.append(punto)

        return sorted(puntos_cercanos, key=lambda p: PuntoService.calcular_distancia(
            latitud, longitud, p.latitud, p.longitud
        ))
