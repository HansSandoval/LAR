"""
Service Layer para Rutas
Contiene la lógica de negocio relacionada con rutas
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional, Dict, Any
from datetime import date, datetime
from ..models.base import Ruta, Entrega, Vehiculo, Punto, EstadoRuta, EstadoEntrega
from ..schemas.schemas import RutaCreate, RutaUpdate
from .routing_service import RoutingService
import logging

logger = logging.getLogger(__name__)


class RutaService:
    """Servicio para operaciones de Rutas"""

    @staticmethod
    def crear_ruta(db: Session, ruta_data: RutaCreate) -> Ruta:
        """
        Crear una nueva ruta
        
        Args:
            db: Sesión de base de datos
            ruta_data: Datos de la ruta a crear
            
        Returns:
            Ruta creada
        """
        try:
            nueva_ruta = Ruta(
                id_cliente=ruta_data.id_cliente,
                nombre=ruta_data.nombre,
                descripcion=ruta_data.descripcion,
                fecha_planificacion=ruta_data.fecha_planificacion,
                secuencia_puntos=ruta_data.secuencia_puntos,
                algoritmo_vrp=ruta_data.algoritmo_vrp,
                id_vehiculo=ruta_data.id_vehiculo,
                estado=EstadoRuta.PLANIFICADA
            )
            db.add(nueva_ruta)
            db.commit()
            db.refresh(nueva_ruta)
            logger.info(f"Ruta {nueva_ruta.id} creada exitosamente")
            return nueva_ruta
        except Exception as e:
            db.rollback()
            logger.error(f"Error al crear ruta: {str(e)}")
            raise

    @staticmethod
    def obtener_ruta(db: Session, ruta_id: int) -> Optional[Ruta]:
        """Obtener una ruta por ID"""
        return db.query(Ruta).filter(Ruta.id == ruta_id).first()

    @staticmethod
    def obtener_rutas(
        db: Session,
        cliente_id: Optional[int] = None,
        vehiculo_id: Optional[int] = None,
        estado: Optional[str] = None,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
        skip: int = 0,
        limit: int = 10
    ) -> tuple[List[Ruta], int]:
        """
        Obtener rutas con filtros opcionales
        
        Returns:
            Tupla (lista de rutas, total de registros)
        """
        query = db.query(Ruta)

        if cliente_id:
            query = query.filter(Ruta.id_cliente == cliente_id)
        if vehiculo_id:
            query = query.filter(Ruta.id_vehiculo == vehiculo_id)
        if estado:
            query = query.filter(Ruta.estado == estado)
        if fecha_desde:
            query = query.filter(Ruta.fecha_planificacion >= fecha_desde)
        if fecha_hasta:
            query = query.filter(Ruta.fecha_planificacion <= fecha_hasta)

        total = query.count()
        rutas = query.offset(skip).limit(limit).all()
        return rutas, total

    @staticmethod
    def actualizar_ruta(db: Session, ruta_id: int, ruta_data: RutaUpdate) -> Optional[Ruta]:
        """Actualizar una ruta existente"""
        try:
            ruta = db.query(Ruta).filter(Ruta.id == ruta_id).first()
            if not ruta:
                return None

            # Actualizar solo los campos proporcionados
            for campo, valor in ruta_data.dict(exclude_unset=True).items():
                setattr(ruta, campo, valor)

            ruta.fecha_actualizacion = datetime.utcnow()
            db.commit()
            db.refresh(ruta)
            logger.info(f"Ruta {ruta_id} actualizada exitosamente")
            return ruta
        except Exception as e:
            db.rollback()
            logger.error(f"Error al actualizar ruta {ruta_id}: {str(e)}")
            raise

    @staticmethod
    def eliminar_ruta(db: Session, ruta_id: int) -> bool:
        """Eliminar una ruta (soft delete - solo marca como cancelada)"""
        try:
            ruta = db.query(Ruta).filter(Ruta.id == ruta_id).first()
            if not ruta:
                return False

            ruta.estado = EstadoRuta.CANCELADA
            ruta.fecha_actualizacion = datetime.utcnow()
            db.commit()
            logger.info(f"Ruta {ruta_id} cancelada")
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Error al eliminar ruta {ruta_id}: {str(e)}")
            raise

    @staticmethod
    def asignar_vehiculo(db: Session, ruta_id: int, vehiculo_id: int) -> Optional[Ruta]:
        """Asignar un vehículo a una ruta"""
        try:
            ruta = db.query(Ruta).filter(Ruta.id == ruta_id).first()
            if not ruta:
                return None

            # Validar que el vehículo exista
            vehiculo = db.query(Vehiculo).filter(Vehiculo.id == vehiculo_id).first()
            if not vehiculo:
                raise ValueError(f"Vehículo {vehiculo_id} no existe")

            ruta.id_vehiculo = vehiculo_id
            ruta.fecha_actualizacion = datetime.utcnow()
            db.commit()
            db.refresh(ruta)
            logger.info(f"Vehículo {vehiculo_id} asignado a ruta {ruta_id}")
            return ruta
        except Exception as e:
            db.rollback()
            logger.error(f"Error al asignar vehículo: {str(e)}")
            raise

    @staticmethod
    def obtener_entregas_ruta(db: Session, ruta_id: int) -> List[Entrega]:
        """Obtener todas las entregas de una ruta"""
        return db.query(Entrega).filter(Entrega.id_ruta == ruta_id).all()

    @staticmethod
    def cambiar_estado_ruta(
        db: Session,
        ruta_id: int,
        nuevo_estado: EstadoRuta
    ) -> Optional[Ruta]:
        """Cambiar el estado de una ruta"""
        try:
            ruta = db.query(Ruta).filter(Ruta.id == ruta_id).first()
            if not ruta:
                return None

            ruta.estado = nuevo_estado
            if nuevo_estado == EstadoRuta.COMPLETADA:
                ruta.fecha_ejecucion = date.today()
            ruta.fecha_actualizacion = datetime.utcnow()
            db.commit()
            db.refresh(ruta)
            logger.info(f"Ruta {ruta_id} cambió a estado {nuevo_estado}")
            return ruta
        except Exception as e:
            db.rollback()
            logger.error(f"Error al cambiar estado de ruta: {str(e)}")
            raise

    @staticmethod
    def calcular_metricas_ruta(db: Session, ruta_id: int) -> Dict[str, Any]:
        """
        Calcular métricas de una ruta (distancia, duración, etc)
        """
        ruta = db.query(Ruta).filter(Ruta.id == ruta_id).first()
        if not ruta:
            return {}

        entregas = RutaService.obtener_entregas_ruta(db, ruta_id)
        
        metricas = {
            "ruta_id": ruta_id,
            "total_entregas": len(entregas),
            "peso_total_kg": sum(e.peso_kg for e in entregas),
            "volumen_total_m3": sum(e.volumen_m3 or 0 for e in entregas),
            "distancia_planificada_km": ruta.distancia_planificada_km or 0,
            "duracion_planificada_minutos": ruta.duracion_planificada_minutos or 0,
        }
        
        if ruta.distancia_real_km:
            metricas["desviacion_distancia_pct"] = (
                (ruta.distancia_real_km - ruta.distancia_planificada_km) 
                / ruta.distancia_planificada_km * 100
            ) if ruta.distancia_planificada_km > 0 else 0

        return metricas

    @staticmethod
    def rutas_proximas_vencer(db: Session, dias_previo: int = 7) -> List[Ruta]:
        """Obtener rutas próximas a ejecutarse"""
        from datetime import timedelta
        hoy = date.today()
        fecha_limite = hoy + timedelta(days=dias_previo)

        return db.query(Ruta).filter(
            and_(
                Ruta.estado == EstadoRuta.PLANIFICADA,
                Ruta.fecha_planificacion >= hoy,
                Ruta.fecha_planificacion <= fecha_limite
            )
        ).all()

    @staticmethod
    def calcular_ruta_con_calles(db: Session, ruta_id: int) -> Dict[str, Any]:
        """
        Calcular ruta mostrando las calles exactas usando OSRM
        
        Args:
            db: Sesión de base de datos
            ruta_id: ID de la ruta
            
        Returns:
            Dict con información de la ruta y geometría de calles
        """
        try:
            ruta = RutaService.obtener_ruta(db, ruta_id)
            if not ruta:
                return {"error": "Ruta no encontrada"}
            
            entregas = RutaService.obtener_entregas_ruta(db, ruta_id)
            if not entregas:
                return {"error": "No hay entregas en la ruta"}
            
            # Obtener puntos en orden
            puntos = []
            for entrega in entregas:
                punto = db.query(Punto).filter(Punto.id == entrega.id_punto).first()
                if punto:
                    puntos.append(punto)
            
            if len(puntos) < 2:
                return {"error": "Se necesitan al menos 2 puntos para calcular ruta"}
            
            # Obtener ruta optimizada con calles
            ruta_info = RoutingService.obtener_ruta_optimizada(puntos)
            
            if not ruta_info:
                return {"error": "No se pudo calcular la ruta con OSRM"}
            
            return {
                "ruta_id": ruta_id,
                "nombre": ruta.nombre,
                "puntos_totales": len(puntos),
                "distancia_km": ruta_info["distancia_km"],
                "duracion_minutos": ruta_info["duracion_minutos"],
                "geometry": ruta_info["geometry"],
                "orden_optimizado": ruta_info["orden_optimizado"],
                "puntos": [
                    {
                        "id": p.id,
                        "latitud": p.latitud,
                        "longitud": p.longitud,
                        "nombre": p.nombre,
                        "descripcion": p.descripcion
                    } 
                    for p in puntos
                ]
            }
        except Exception as e:
            logger.error(f"Error al calcular ruta con calles: {str(e)}")
            return {"error": str(e)}
