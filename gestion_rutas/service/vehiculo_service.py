"""
Service Layer para Vehículos
"""

from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date
from ..models.base import Vehiculo, EstadoVehiculo
from ..schemas.schemas import VehiculoCreate, VehiculoUpdate
import logging

logger = logging.getLogger(__name__)


class VehiculoService:
    """Servicio para operaciones con Vehículos"""

    @staticmethod
    def crear_vehiculo(db: Session, vehiculo_data: VehiculoCreate) -> Vehiculo:
        """Crear un nuevo vehículo"""
        try:
            nuevo_vehiculo = Vehiculo(
                placa=vehiculo_data.placa,
                marca=vehiculo_data.marca,
                modelo=vehiculo_data.modelo,
                anio=vehiculo_data.anio,
                capacidad_kg=vehiculo_data.capacidad_kg,
                combustible_km_litro=vehiculo_data.combustible_km_litro,
                conductor_asignado=vehiculo_data.conductor_asignado,
                ultimo_mantenimiento=vehiculo_data.ultimo_mantenimiento,
                proximo_mantenimiento=vehiculo_data.proximo_mantenimiento,
                estado=EstadoVehiculo.DISPONIBLE
            )
            db.add(nuevo_vehiculo)
            db.commit()
            db.refresh(nuevo_vehiculo)
            logger.info(f"Vehículo {nuevo_vehiculo.id} creado: {nuevo_vehiculo.placa}")
            return nuevo_vehiculo
        except Exception as e:
            db.rollback()
            logger.error(f"Error al crear vehículo: {str(e)}")
            raise

    @staticmethod
    def obtener_vehiculo(db: Session, vehiculo_id: int) -> Optional[Vehiculo]:
        """Obtener vehículo por ID"""
        return db.query(Vehiculo).filter(Vehiculo.id == vehiculo_id).first()

    @staticmethod
    def obtener_vehiculo_por_placa(db: Session, placa: str) -> Optional[Vehiculo]:
        """Obtener vehículo por placa"""
        return db.query(Vehiculo).filter(Vehiculo.placa == placa).first()

    @staticmethod
    def obtener_vehiculos(
        db: Session,
        estado: Optional[str] = None,
        skip: int = 0,
        limit: int = 10
    ) -> tuple[List[Vehiculo], int]:
        """Obtener vehículos con filtros opcionales"""
        query = db.query(Vehiculo)

        if estado:
            query = query.filter(Vehiculo.estado == estado)

        total = query.count()
        vehiculos = query.offset(skip).limit(limit).all()
        return vehiculos, total

    @staticmethod
    def actualizar_vehiculo(db: Session, vehiculo_id: int, vehiculo_data: VehiculoUpdate) -> Optional[Vehiculo]:
        """Actualizar vehículo"""
        try:
            vehiculo = db.query(Vehiculo).filter(Vehiculo.id == vehiculo_id).first()
            if not vehiculo:
                return None

            for campo, valor in vehiculo_data.dict(exclude_unset=True).items():
                setattr(vehiculo, campo, valor)

            vehiculo.fecha_actualizacion = datetime.utcnow()
            db.commit()
            db.refresh(vehiculo)
            logger.info(f"Vehículo {vehiculo_id} actualizado")
            return vehiculo
        except Exception as e:
            db.rollback()
            logger.error(f"Error al actualizar vehículo: {str(e)}")
            raise

    @staticmethod
    def obtener_vehiculos_disponibles(db: Session) -> List[Vehiculo]:
        """Obtener vehículos disponibles para asignación"""
        return db.query(Vehiculo).filter(Vehiculo.estado == EstadoVehiculo.DISPONIBLE).all()

    @staticmethod
    def obtener_vehiculos_en_servicio(db: Session) -> List[Vehiculo]:
        """Obtener vehículos actualmente en servicio"""
        return db.query(Vehiculo).filter(Vehiculo.estado == EstadoVehiculo.EN_SERVICIO).all()

    @staticmethod
    def cambiar_estado_vehiculo(
        db: Session,
        vehiculo_id: int,
        nuevo_estado: EstadoVehiculo
    ) -> Optional[Vehiculo]:
        """Cambiar estado del vehículo"""
        try:
            vehiculo = db.query(Vehiculo).filter(Vehiculo.id == vehiculo_id).first()
            if not vehiculo:
                return None

            vehiculo.estado = nuevo_estado
            vehiculo.fecha_actualizacion = datetime.utcnow()
            db.commit()
            db.refresh(vehiculo)
            logger.info(f"Vehículo {vehiculo_id} cambió a estado {nuevo_estado}")
            return vehiculo
        except Exception as e:
            db.rollback()
            logger.error(f"Error al cambiar estado: {str(e)}")
            raise

    @staticmethod
    def actualizar_ubicacion_vehiculo(
        db: Session,
        vehiculo_id: int,
        x: float,
        y: float
    ) -> Optional[Vehiculo]:
        """Actualizar ubicación GPS del vehículo"""
        try:
            vehiculo = db.query(Vehiculo).filter(Vehiculo.id == vehiculo_id).first()
            if not vehiculo:
                return None

            vehiculo.ubicacion_actual_x = x
            vehiculo.ubicacion_actual_y = y
            vehiculo.fecha_actualizacion = datetime.utcnow()
            db.commit()
            db.refresh(vehiculo)
            logger.info(f"Ubicación de vehículo {vehiculo_id} actualizada: ({x}, {y})")
            return vehiculo
        except Exception as e:
            db.rollback()
            logger.error(f"Error al actualizar ubicación: {str(e)}")
            raise

    @staticmethod
    def programar_mantenimiento(
        db: Session,
        vehiculo_id: int,
        proximo_mantenimiento: date
    ) -> Optional[Vehiculo]:
        """Programar próximo mantenimiento del vehículo"""
        try:
            vehiculo = db.query(Vehiculo).filter(Vehiculo.id == vehiculo_id).first()
            if not vehiculo:
                return None

            vehiculo.proximo_mantenimiento = proximo_mantenimiento
            vehiculo.fecha_actualizacion = datetime.utcnow()
            db.commit()
            db.refresh(vehiculo)
            logger.info(f"Mantenimiento programado para vehículo {vehiculo_id}: {proximo_mantenimiento}")
            return vehiculo
        except Exception as e:
            db.rollback()
            logger.error(f"Error al programar mantenimiento: {str(e)}")
            raise
