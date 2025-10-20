"""
Service Layer para Clientes
"""

from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from models.base import Cliente
from schemas.schemas import ClienteCreate, ClienteUpdate
import logging

logger = logging.getLogger(__name__)


class ClienteService:
    """Servicio para operaciones con Clientes"""

    @staticmethod
    def crear_cliente(db: Session, cliente_data: ClienteCreate) -> Cliente:
        """Crear un nuevo cliente"""
        try:
            nuevo_cliente = Cliente(
                nombre=cliente_data.nombre,
                email=cliente_data.email,
                telefono=cliente_data.telefono,
                empresa=cliente_data.empresa,
                direccion=cliente_data.direccion,
                ciudad=cliente_data.ciudad,
                estado_activo=cliente_data.estado_activo
            )
            db.add(nuevo_cliente)
            db.commit()
            db.refresh(nuevo_cliente)
            logger.info(f"Cliente {nuevo_cliente.id} creado: {nuevo_cliente.email}")
            return nuevo_cliente
        except Exception as e:
            db.rollback()
            logger.error(f"Error al crear cliente: {str(e)}")
            raise

    @staticmethod
    def obtener_cliente(db: Session, cliente_id: int) -> Optional[Cliente]:
        """Obtener cliente por ID"""
        return db.query(Cliente).filter(Cliente.id == cliente_id).first()

    @staticmethod
    def obtener_cliente_por_email(db: Session, email: str) -> Optional[Cliente]:
        """Obtener cliente por email"""
        return db.query(Cliente).filter(Cliente.email == email).first()

    @staticmethod
    def obtener_clientes(
        db: Session,
        estado_activo: Optional[bool] = None,
        ciudad: Optional[str] = None,
        skip: int = 0,
        limit: int = 10
    ) -> tuple[List[Cliente], int]:
        """Obtener clientes con filtros opcionales"""
        query = db.query(Cliente)

        if estado_activo is not None:
            query = query.filter(Cliente.estado_activo == estado_activo)
        if ciudad:
            query = query.filter(Cliente.ciudad.ilike(f"%{ciudad}%"))

        total = query.count()
        clientes = query.offset(skip).limit(limit).all()
        return clientes, total

    @staticmethod
    def actualizar_cliente(db: Session, cliente_id: int, cliente_data: ClienteUpdate) -> Optional[Cliente]:
        """Actualizar cliente existente"""
        try:
            cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
            if not cliente:
                return None

            for campo, valor in cliente_data.dict(exclude_unset=True).items():
                setattr(cliente, campo, valor)

            cliente.fecha_actualizacion = datetime.utcnow()
            db.commit()
            db.refresh(cliente)
            logger.info(f"Cliente {cliente_id} actualizado")
            return cliente
        except Exception as e:
            db.rollback()
            logger.error(f"Error al actualizar cliente: {str(e)}")
            raise

    @staticmethod
    def desactivar_cliente(db: Session, cliente_id: int) -> Optional[Cliente]:
        """Desactivar cliente (soft delete)"""
        try:
            cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
            if not cliente:
                return None

            cliente.estado_activo = False
            cliente.fecha_actualizacion = datetime.utcnow()
            db.commit()
            db.refresh(cliente)
            logger.info(f"Cliente {cliente_id} desactivado")
            return cliente
        except Exception as e:
            db.rollback()
            logger.error(f"Error al desactivar cliente: {str(e)}")
            raise

    @staticmethod
    def obtener_clientes_activos(db: Session, limit: int = 10) -> List[Cliente]:
        """Obtener solo clientes activos"""
        return db.query(Cliente).filter(Cliente.estado_activo == True).limit(limit).all()
