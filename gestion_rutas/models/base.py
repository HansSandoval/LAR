"""
Modelos base ORM con SQLAlchemy 2.0
Define todas las tablas principales para el sistema de gestión de rutas
"""

from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Float, Date, Time, DateTime, ForeignKey, Boolean, JSON, Enum
from sqlalchemy.orm import relationship
from database.db import Base
import enum


class EstadoRuta(str, enum.Enum):
    """Estados posibles de una ruta"""
    PLANIFICADA = "planificada"
    EN_PROGRESO = "en_progreso"
    COMPLETADA = "completada"
    CANCELADA = "cancelada"


class EstadoVehiculo(str, enum.Enum):
    """Estados posibles de un vehículo"""
    DISPONIBLE = "disponible"
    EN_SERVICIO = "en_servicio"
    MANTENIMIENTO = "mantenimiento"
    INACTIVO = "inactivo"


class EstadoEntrega(str, enum.Enum):
    """Estados de una entrega"""
    PENDIENTE = "pendiente"
    EN_TRANSITO = "en_transito"
    ENTREGADA = "entregada"
    FALLIDA = "fallida"


class TipoVehiculo(str, enum.Enum):
    """Tipos de vehículos disponibles"""
    MOTO = "moto"
    AUTO = "auto"
    CAMIONETA = "camioneta"
    CAMION = "camion"


# ============================================================================
# MODELO: CLIENTE
# ============================================================================

class Cliente(Base):
    """Modelo para clientes/usuarios que usan el servicio"""
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    telefono = Column(String(20))
    empresa = Column(String(255))
    direccion = Column(String(500))
    ciudad = Column(String(100))
    estado_activo = Column(Boolean, default=True)
    fecha_registro = Column(DateTime, default=datetime.utcnow)
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    entregas = relationship("Entrega", back_populates="cliente", cascade="all, delete-orphan")
    rutas = relationship("Ruta", back_populates="cliente", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Cliente(id={self.id}, nombre={self.nombre}, email={self.email})>"


# ============================================================================
# MODELO: VEHÍCULO
# ============================================================================

class Vehiculo(Base):
    """Modelo para vehículos de la flota"""
    __tablename__ = "vehiculos"

    id = Column(Integer, primary_key=True, index=True)
    placa = Column(String(20), unique=True, nullable=False, index=True)
    tipo = Column(Enum(TipoVehiculo), default=TipoVehiculo.AUTO)
    marca = Column(String(100))
    modelo = Column(String(100))
    anio = Column(Integer)
    capacidad_kg = Column(Float, nullable=False, default=1000.0)  # Capacidad máxima en kg
    combustible_km_litro = Column(Float, default=10.0)  # Consumo
    estado = Column(Enum(EstadoVehiculo), default=EstadoVehiculo.DISPONIBLE)
    conductor_asignado = Column(String(255))  # Nombre del conductor
    ubicacion_actual_x = Column(Float)  # Coordenada X actual
    ubicacion_actual_y = Column(Float)  # Coordenada Y actual
    ultimo_mantenimiento = Column(Date)
    proximo_mantenimiento = Column(Date)
    fecha_registro = Column(DateTime, default=datetime.utcnow)
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    rutas = relationship("Ruta", back_populates="vehiculo", cascade="all, delete-orphan")
    entregas = relationship("Entrega", back_populates="vehiculo")

    def __repr__(self):
        return f"<Vehiculo(id={self.id}, placa={self.placa}, estado={self.estado})>"


# ============================================================================
# MODELO: PUNTO DE ENTREGA
# ============================================================================

class Punto(Base):
    """Modelo para puntos de entrega/recolección"""
    __tablename__ = "puntos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(255), nullable=False)
    descripcion = Column(String(500))
    latitud = Column(Float, nullable=False)  # Coordenada Y
    longitud = Column(Float, nullable=False)  # Coordenada X
    tipo_punto = Column(String(50))  # Ej: entrega, recolección, depósito
    estado_activo = Column(Boolean, default=True)
    fecha_registro = Column(DateTime, default=datetime.utcnow)
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    entregas = relationship("Entrega", back_populates="punto", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Punto(id={self.id}, nombre={self.nombre}, lat={self.latitud}, lon={self.longitud})>"


# ============================================================================
# MODELO: ENTREGA
# ============================================================================

class Entrega(Base):
    """Modelo para entregas individuales"""
    __tablename__ = "entregas"

    id = Column(Integer, primary_key=True, index=True)
    id_cliente = Column(Integer, ForeignKey("clientes.id"), nullable=False)
    id_punto = Column(Integer, ForeignKey("puntos.id"), nullable=False)
    id_ruta = Column(Integer, ForeignKey("rutas.id"), nullable=True)
    id_vehiculo = Column(Integer, ForeignKey("vehiculos.id"), nullable=True)
    
    # Datos de la entrega
    descripcion = Column(String(500))
    peso_kg = Column(Float, nullable=False)
    volumen_m3 = Column(Float)
    estado = Column(Enum(EstadoEntrega), default=EstadoEntrega.PENDIENTE)
    prioridad = Column(Integer, default=1)  # 1=baja, 2=normal, 3=alta
    fecha_programada = Column(Date, nullable=False)
    ventana_inicio = Column(Time)  # Hora de inicio de ventana de entrega
    ventana_fin = Column(Time)  # Hora de fin de ventana de entrega
    
    # Tracking
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_entrega_real = Column(DateTime)
    tiempo_transito_minutos = Column(Float)
    observaciones = Column(String(1000))
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    cliente = relationship("Cliente", back_populates="entregas")
    punto = relationship("Punto", back_populates="entregas")
    ruta = relationship("Ruta", back_populates="entregas")
    vehiculo = relationship("Vehiculo", back_populates="entregas")

    def __repr__(self):
        return f"<Entrega(id={self.id}, cliente_id={self.id_cliente}, estado={self.estado})>"


# ============================================================================
# MODELO: RUTA
# ============================================================================

class Ruta(Base):
    """Modelo para rutas planificadas/ejecutadas"""
    __tablename__ = "rutas"

    id = Column(Integer, primary_key=True, index=True)
    id_cliente = Column(Integer, ForeignKey("clientes.id"), nullable=False)
    id_vehiculo = Column(Integer, ForeignKey("vehiculos.id"), nullable=True)
    
    # Información de la ruta
    nombre = Column(String(255))
    descripcion = Column(String(500))
    fecha_planificacion = Column(Date, nullable=False)
    fecha_ejecucion = Column(Date)
    estado = Column(Enum(EstadoRuta), default=EstadoRuta.PLANIFICADA)
    
    # Secuencia y puntos (almacenado como JSON)
    secuencia_puntos = Column(JSON)  # Ej: [1, 3, 5, 2] - IDs de puntos en orden
    
    # Métricas planificadas
    distancia_planificada_km = Column(Float)
    duracion_planificada_minutos = Column(Float)
    costo_combustible_estimado = Column(Float)
    
    # Métricas reales (se actualizan durante/después de ejecución)
    distancia_real_km = Column(Float)
    duracion_real_minutos = Column(Float)
    costo_combustible_real = Column(Float)
    desviacion_distancia = Column(Float)  # Diferencia entre real y planificado
    desviacion_tiempo = Column(Float)  # Diferencia en minutos
    
    # Algoritmo VRP usado
    algoritmo_vrp = Column(String(100))  # Ej: nearest_neighbor, nearest_neighbor_2opt
    version_algoritmo = Column(String(50))  # Ej: v1.0
    
    # Metadata
    datos_extra = Column(JSON)  # Para almacenar data adicional
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    cliente = relationship("Cliente", back_populates="rutas")
    vehiculo = relationship("Vehiculo", back_populates="rutas")
    entregas = relationship("Entrega", back_populates="ruta", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Ruta(id={self.id}, nombre={self.nombre}, estado={self.estado})>"


# ============================================================================
# MODELO: HISTÓRICO DE RUTAS
# ============================================================================

class HistoricoRuta(Base):
    """Modelo para mantener historial de cambios en rutas (auditoría)"""
    __tablename__ = "historico_rutas"

    id = Column(Integer, primary_key=True, index=True)
    id_ruta = Column(Integer, ForeignKey("rutas.id"), nullable=False)
    
    accion = Column(String(50))  # Ej: creada, modificada, ejecutada, cancelada
    descripcion_cambio = Column(String(500))
    
    # Estado anterior y nuevo (almacenados como JSON para auditoria)
    estado_anterior = Column(JSON)
    estado_nuevo = Column(JSON)
    
    usuario_realizador = Column(String(255))  # Usuario que hizo el cambio
    fecha_cambio = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<HistoricoRuta(id={self.id}, ruta_id={self.id_ruta}, accion={self.accion})>"


# ============================================================================
# MODELO: PREDICCIÓN DE DEMANDA (para LSTM)
# ============================================================================

class PrediccionDemanda(Base):
    """Modelo para almacenar predicciones del LSTM"""
    __tablename__ = "predicciones_demanda"

    id = Column(Integer, primary_key=True, index=True)
    
    # Punto que se predice
    fecha_prediccion = Column(Date, nullable=False)
    cantidad_entregas_predichas = Column(Integer)
    peso_total_predicho_kg = Column(Float)
    
    # Precisión del modelo
    confianza = Column(Float)  # 0.0 a 1.0
    error_mape = Column(Float)  # Error porcentual absoluto medio
    
    # Metadata del modelo
    version_modelo = Column(String(50))  # Versión del LSTM usado
    fecha_generacion = Column(DateTime, default=datetime.utcnow)
    datos_extra = Column(JSON)

    def __repr__(self):
        return f"<PrediccionDemanda(id={self.id}, fecha={self.fecha_prediccion}, confianza={self.confianza})>"
