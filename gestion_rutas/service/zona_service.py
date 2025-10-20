"""
Service Layer para Zonas y Puntos de Recolección
"""

from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from models.models import Zona, PuntoRecoleccion, RutaPlanificada
import logging
import math

logger = logging.getLogger(__name__)


class ZonaService:
    """Servicio para operaciones con Zonas"""

    @staticmethod
    def crear_zona(
        db: Session,
        nombre: str,
        tipo: str,
        area_km2: float,
        poblacion: int,
        prioridad: int = 1
    ) -> Zona:
        """Crear nueva zona"""
        try:
            nueva_zona = Zona(
                nombre=nombre,
                tipo=tipo,
                area_km2=area_km2,
                poblacion=poblacion,
                prioridad=prioridad
            )
            db.add(nueva_zona)
            db.commit()
            db.refresh(nueva_zona)
            logger.info(f"Zona {nueva_zona.id_zona} creada: {nombre}")
            return nueva_zona
        except Exception as e:
            db.rollback()
            logger.error(f"Error al crear zona: {str(e)}")
            raise

    @staticmethod
    def obtener_zona(db: Session, zona_id: int) -> Optional[Zona]:
        """Obtener zona por ID"""
        return db.query(Zona).filter(Zona.id_zona == zona_id).first()

    @staticmethod
    def obtener_zonas(
        db: Session,
        tipo: Optional[str] = None,
        skip: int = 0,
        limit: int = 10
    ) -> tuple[List[Zona], int]:
        """Obtener zonas con filtros"""
        query = db.query(Zona)

        if tipo:
            query = query.filter(Zona.tipo == tipo)

        total = query.count()
        zonas = query.offset(skip).limit(limit).all()
        return zonas, total

    @staticmethod
    def obtener_zonas_por_prioridad(db: Session) -> List[Zona]:
        """Obtener zonas ordenadas por prioridad (mayor primero)"""
        return db.query(Zona).order_by(Zona.prioridad.desc()).all()

    @staticmethod
    def obtener_puntos_zona(db: Session, zona_id: int) -> List[PuntoRecoleccion]:
        """Obtener todos los puntos de una zona"""
        return db.query(PuntoRecoleccion).filter(PuntoRecoleccion.id_zona == zona_id).all()

    @staticmethod
    def obtener_rutas_zona(db: Session, zona_id: int) -> List[RutaPlanificada]:
        """Obtener todas las rutas planificadas de una zona"""
        return db.query(RutaPlanificada).filter(RutaPlanificada.id_zona == zona_id).all()

    @staticmethod
    def calcular_metricas_zona(db: Session, zona_id: int) -> Dict[str, Any]:
        """Calcular métricas de una zona"""
        zona = ZonaService.obtener_zona(db, zona_id)
        if not zona:
            return {}

        puntos = ZonaService.obtener_puntos_zona(db, zona_id)
        rutas = ZonaService.obtener_rutas_zona(db, zona_id)

        metricas = {
            "zona_id": zona_id,
            "nombre": zona.nombre,
            "tipo": zona.tipo,
            "area_km2": zona.area_km2,
            "poblacion": zona.poblacion,
            "prioridad": zona.prioridad,
            "total_puntos": len(puntos),
            "total_rutas_planificadas": len(rutas),
        }

        if puntos:
            capacidades = [p.capacidad_kg for p in puntos if p.capacidad_kg]
            metricas["capacidad_total_kg"] = sum(capacidades)
            metricas["capacidad_promedio_kg"] = sum(capacidades) / len(capacidades) if capacidades else 0

        return metricas


class PuntoRecoleccionService:
    """Servicio para operaciones con Puntos de Recolección"""

    @staticmethod
    def crear_punto(
        db: Session,
        id_zona: int,
        nombre: str,
        tipo: str,
        latitud: float,
        longitud: float,
        capacidad_kg: float
    ) -> PuntoRecoleccion:
        """Crear nuevo punto de recolección"""
        try:
            nuevo_punto = PuntoRecoleccion(
                id_zona=id_zona,
                nombre=nombre,
                tipo=tipo,
                latitud=latitud,
                longitud=longitud,
                capacidad_kg=capacidad_kg,
                estado="activo"
            )
            db.add(nuevo_punto)
            db.commit()
            db.refresh(nuevo_punto)
            logger.info(f"Punto {nuevo_punto.id_punto} creado: {nombre}")
            return nuevo_punto
        except Exception as e:
            db.rollback()
            logger.error(f"Error al crear punto: {str(e)}")
            raise

    @staticmethod
    def obtener_punto(db: Session, punto_id: int) -> Optional[PuntoRecoleccion]:
        """Obtener punto por ID"""
        return db.query(PuntoRecoleccion).filter(PuntoRecoleccion.id_punto == punto_id).first()

    @staticmethod
    def obtener_puntos(
        db: Session,
        zona_id: Optional[int] = None,
        tipo: Optional[str] = None,
        estado: Optional[str] = None,
        skip: int = 0,
        limit: int = 10
    ) -> tuple[List[PuntoRecoleccion], int]:
        """Obtener puntos con filtros"""
        query = db.query(PuntoRecoleccion)

        if zona_id:
            query = query.filter(PuntoRecoleccion.id_zona == zona_id)
        if tipo:
            query = query.filter(PuntoRecoleccion.tipo == tipo)
        if estado:
            query = query.filter(PuntoRecoleccion.estado == estado)

        total = query.count()
        puntos = query.offset(skip).limit(limit).all()
        return puntos, total

    @staticmethod
    def obtener_puntos_activos(db: Session) -> List[PuntoRecoleccion]:
        """Obtener solo puntos activos"""
        return db.query(PuntoRecoleccion).filter(PuntoRecoleccion.estado == "activo").all()

    @staticmethod
    def cambiar_estado_punto(
        db: Session,
        punto_id: int,
        nuevo_estado: str
    ) -> Optional[PuntoRecoleccion]:
        """Cambiar estado de un punto"""
        try:
            punto = db.query(PuntoRecoleccion).filter(PuntoRecoleccion.id_punto == punto_id).first()
            if not punto:
                return None

            estados_validos = ["activo", "inactivo", "mantenimiento"]
            if nuevo_estado not in estados_validos:
                raise ValueError(f"Estado no válido. Debe ser uno de: {estados_validos}")

            punto.estado = nuevo_estado
            db.commit()
            db.refresh(punto)
            logger.info(f"Punto {punto_id} cambió a estado {nuevo_estado}")
            return punto
        except Exception as e:
            db.rollback()
            logger.error(f"Error al cambiar estado: {str(e)}")
            raise

    @staticmethod
    def calcular_distancia_haversine(
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float
    ) -> float:
        """Calcular distancia entre dos puntos (fórmula Haversine)"""
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
        radio_km: float = 5.0,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Obtener puntos cercanos a una coordenada"""
        puntos_activos = PuntoRecoleccionService.obtener_puntos_activos(db)
        puntos_cercanos = []

        for punto in puntos_activos:
            distancia = PuntoRecoleccionService.calcular_distancia_haversine(
                latitud, longitud,
                punto.latitud, punto.longitud
            )
            if distancia <= radio_km:
                puntos_cercanos.append({
                    "punto_id": punto.id_punto,
                    "nombre": punto.nombre,
                    "tipo": punto.tipo,
                    "latitud": punto.latitud,
                    "longitud": punto.longitud,
                    "capacidad_kg": punto.capacidad_kg,
                    "distancia_km": round(distancia, 2)
                })

        # Ordenar por distancia y limitar resultados
        puntos_cercanos.sort(key=lambda x: x["distancia_km"])
        return puntos_cercanos[:limit]

    @staticmethod
    def obtener_matriz_distancias(db: Session, punto_ids: List[int]) -> Dict[tuple, float]:
        """Generar matriz de distancias entre puntos"""
        puntos = db.query(PuntoRecoleccion).filter(PuntoRecoleccion.id_punto.in_(punto_ids)).all()
        
        matriz = {}
        for i, punto1 in enumerate(puntos):
            for j, punto2 in enumerate(puntos):
                if i != j:
                    distancia = PuntoRecoleccionService.calcular_distancia_haversine(
                        punto1.latitud, punto1.longitud,
                        punto2.latitud, punto2.longitud
                    )
                    matriz[(punto1.id_punto, punto2.id_punto)] = distancia

        return matriz
