"""
Service Layer para Entregas
"""

from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date
from models.base import Entrega, EstadoEntrega
from schemas.schemas import EntregaCreate, EntregaUpdate
import logging

logger = logging.getLogger(__name__)


class EntregaService:
    """Servicio para operaciones con Entregas"""

    @staticmethod
    def crear_entrega(db: Session, entrega_data: EntregaCreate) -> Entrega:
        """Crear una nueva entrega"""
        try:
            nueva_entrega = Entrega(
                id_cliente=entrega_data.id_cliente,
                id_punto=entrega_data.id_punto,
                descripcion=entrega_data.descripcion,
                peso_kg=entrega_data.peso_kg,
                volumen_m3=entrega_data.volumen_m3,
                prioridad=entrega_data.prioridad,
                fecha_programada=entrega_data.fecha_programada,
                ventana_inicio=entrega_data.ventana_inicio,
                ventana_fin=entrega_data.ventana_fin,
                observaciones=entrega_data.observaciones,
                estado=EstadoEntrega.PENDIENTE
            )
            db.add(nueva_entrega)
            db.commit()
            db.refresh(nueva_entrega)
            logger.info(f"Entrega {nueva_entrega.id} creada para cliente {entrega_data.id_cliente}")
            return nueva_entrega
        except Exception as e:
            db.rollback()
            logger.error(f"Error al crear entrega: {str(e)}")
            raise

    @staticmethod
    def obtener_entrega(db: Session, entrega_id: int) -> Optional[Entrega]:
        """Obtener entrega por ID"""
        return db.query(Entrega).filter(Entrega.id == entrega_id).first()

    @staticmethod
    def obtener_entregas(
        db: Session,
        cliente_id: Optional[int] = None,
        ruta_id: Optional[int] = None,
        estado: Optional[str] = None,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
        skip: int = 0,
        limit: int = 10
    ) -> tuple[List[Entrega], int]:
        """Obtener entregas con filtros opcionales"""
        query = db.query(Entrega)

        if cliente_id:
            query = query.filter(Entrega.id_cliente == cliente_id)
        if ruta_id:
            query = query.filter(Entrega.id_ruta == ruta_id)
        if estado:
            query = query.filter(Entrega.estado == estado)
        if fecha_desde:
            query = query.filter(Entrega.fecha_programada >= fecha_desde)
        if fecha_hasta:
            query = query.filter(Entrega.fecha_programada <= fecha_hasta)

        total = query.count()
        entregas = query.offset(skip).limit(limit).all()
        return entregas, total

    @staticmethod
    def actualizar_entrega(db: Session, entrega_id: int, entrega_data: EntregaUpdate) -> Optional[Entrega]:
        """Actualizar entrega"""
        try:
            entrega = db.query(Entrega).filter(Entrega.id == entrega_id).first()
            if not entrega:
                return None

            for campo, valor in entrega_data.dict(exclude_unset=True).items():
                setattr(entrega, campo, valor)

            entrega.fecha_actualizacion = datetime.utcnow()
            db.commit()
            db.refresh(entrega)
            logger.info(f"Entrega {entrega_id} actualizada")
            return entrega
        except Exception as e:
            db.rollback()
            logger.error(f"Error al actualizar entrega: {str(e)}")
            raise

    @staticmethod
    def cambiar_estado_entrega(
        db: Session,
        entrega_id: int,
        nuevo_estado: EstadoEntrega
    ) -> Optional[Entrega]:
        """Cambiar estado de una entrega"""
        try:
            entrega = db.query(Entrega).filter(Entrega.id == entrega_id).first()
            if not entrega:
                return None

            entrega.estado = nuevo_estado
            
            if nuevo_estado == EstadoEntrega.ENTREGADA:
                entrega.fecha_entrega_real = datetime.utcnow()

            entrega.fecha_actualizacion = datetime.utcnow()
            db.commit()
            db.refresh(entrega)
            logger.info(f"Entrega {entrega_id} cambió a estado {nuevo_estado}")
            return entrega
        except Exception as e:
            db.rollback()
            logger.error(f"Error al cambiar estado de entrega: {str(e)}")
            raise

    @staticmethod
    def obtener_entregas_pendientes(db: Session, cliente_id: Optional[int] = None) -> List[Entrega]:
        """Obtener entregas pendientes"""
        query = db.query(Entrega).filter(Entrega.estado == EstadoEntrega.PENDIENTE)
        
        if cliente_id:
            query = query.filter(Entrega.id_cliente == cliente_id)
        
        return query.all()

    @staticmethod
    def obtener_entregas_por_ruta(db: Session, ruta_id: int) -> List[Entrega]:
        """Obtener todas las entregas de una ruta"""
        return db.query(Entrega).filter(Entrega.id_ruta == ruta_id).all()

    @staticmethod
    def asignar_entrega_a_ruta(
        db: Session,
        entrega_id: int,
        ruta_id: int
    ) -> Optional[Entrega]:
        """Asignar una entrega a una ruta"""
        try:
            entrega = db.query(Entrega).filter(Entrega.id == entrega_id).first()
            if not entrega:
                return None

            entrega.id_ruta = ruta_id
            entrega.estado = EstadoEntrega.EN_TRANSITO
            entrega.fecha_actualizacion = datetime.utcnow()
            db.commit()
            db.refresh(entrega)
            logger.info(f"Entrega {entrega_id} asignada a ruta {ruta_id}")
            return entrega
        except Exception as e:
            db.rollback()
            logger.error(f"Error al asignar entrega a ruta: {str(e)}")
            raise

    @staticmethod
    def obtener_entregas_por_prioridad(
        db: Session,
        fecha: date,
        prioridad: int = 3
    ) -> List[Entrega]:
        """Obtener entregas de alta prioridad para una fecha"""
        return db.query(Entrega).filter(
            Entrega.fecha_programada == fecha,
            Entrega.prioridad >= prioridad,
            Entrega.estado == EstadoEntrega.PENDIENTE
        ).all()

    @staticmethod
    def calcular_peso_entregas(entregas: List[Entrega]) -> float:
        """Calcular peso total de una lista de entregas"""
        return sum(e.peso_kg for e in entregas)
