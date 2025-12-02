from sqlalchemy import Column, Integer, String, Float, Date, Time, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Zona(Base):
    __tablename__ = 'zona'
    id_zona = Column(Integer, primary_key=True)
    nombre = Column(String, nullable=False)
    tipo = Column(String)
    area_km2 = Column(Float)
    poblacion = Column(Integer)
    coordenadas_limite = Column(String)  # JSON string con coordenadas
    prioridad = Column(Integer)
    puntos = relationship('PuntoRecoleccion', back_populates='zona')
    rutas = relationship('RutaPlanificada', back_populates='zona')
    incidencias = relationship('Incidencia', back_populates='zona')
    predicciones = relationship('PrediccionDemanda', back_populates='zona')

class PuntoRecoleccion(Base):
    __tablename__ = 'punto_recoleccion'
    id_punto = Column(Integer, primary_key=True)
    id_zona = Column(Integer, ForeignKey('zona.id_zona'))
    nombre = Column(String)
    tipo = Column(String)
    latitud = Column(Float)
    longitud = Column(Float)
    capacidad_kg = Column(Float)
    estado = Column(String)
    zona = relationship('Zona', back_populates='puntos')

class Camion(Base):
    __tablename__ = 'camion'
    id_camion = Column(Integer, primary_key=True)
    patente = Column(String)
    capacidad_kg = Column(Float)
    consumo_km_l = Column(Float)
    tipo_combustible = Column(String)
    estado_operativo = Column(String)
    gps_id = Column(String)
    rutas_ejecutadas = relationship('RutaEjecutada', back_populates='camion')
    turnos = relationship('Turno', back_populates='camion')
    incidencias = relationship('Incidencia', back_populates='camion')

class Turno(Base):
    __tablename__ = 'turno'
    id_turno = Column(Integer, primary_key=True)
    id_camion = Column(Integer, ForeignKey('camion.id_camion'))
    fecha = Column(Date)
    hora_inicio = Column(Time)
    hora_fin = Column(Time)
    operador = Column(String)
    estado = Column(String)
    camion = relationship('Camion', back_populates='turnos')
    rutas = relationship('RutaPlanificada', back_populates='turno')

class RutaPlanificada(Base):
    __tablename__ = 'ruta_planificada'
    id_ruta = Column(Integer, primary_key=True)
    id_zona = Column(Integer, ForeignKey('zona.id_zona'))
    id_turno = Column(Integer, ForeignKey('turno.id_turno'))
    fecha = Column(Date)
    distancia_planificada_km = Column(Float)
    duracion_planificada_min = Column(Float)
    secuencia_puntos = Column(JSON)  # Lista de IDs de puntos
    geometria_json = Column(JSON)    # Geometría completa de la ruta [[lat,lon],...]
    version_modelo_vrp = Column(String)
    zona = relationship('Zona', back_populates='rutas')
    turno = relationship('Turno', back_populates='rutas')
    rutas_ejecutadas = relationship('RutaEjecutada', back_populates='ruta_planificada')

class RutaEjecutada(Base):
    __tablename__ = 'ruta_ejecutada'
    id_ruta_exec = Column(Integer, primary_key=True)
    id_ruta = Column(Integer, ForeignKey('ruta_planificada.id_ruta'))
    id_camion = Column(Integer, ForeignKey('camion.id_camion'))
    fecha = Column(Date)
    distancia_real_km = Column(Float)
    duracion_real_min = Column(Float)
    cumplimiento_horario_pct = Column(Float)
    desviacion_km = Column(Float)
    telemetria_json = Column(JSON)
    ruta_planificada = relationship('RutaPlanificada', back_populates='rutas_ejecutadas')
    camion = relationship('Camion', back_populates='rutas_ejecutadas')
    incidencias = relationship('Incidencia', back_populates='ruta_ejecutada')

class Incidencia(Base):
    __tablename__ = 'incidencia'
    id_incidencia = Column(Integer, primary_key=True)
    id_ruta_exec = Column(Integer, ForeignKey('ruta_ejecutada.id_ruta_exec'))
    id_zona = Column(Integer, ForeignKey('zona.id_zona'))
    id_camion = Column(Integer, ForeignKey('camion.id_camion'))
    tipo = Column(String)
    descripcion = Column(String)
    fecha_hora = Column(DateTime)
    severidad = Column(Integer)
    ruta_ejecutada = relationship('RutaEjecutada', back_populates='incidencias')
    zona = relationship('Zona', back_populates='incidencias')
    camion = relationship('Camion', back_populates='incidencias')

class PrediccionDemanda(Base):
    __tablename__ = 'prediccion_demanda'
    id_prediccion = Column(Integer, primary_key=True)
    id_zona = Column(Integer, ForeignKey('zona.id_zona'))
    horizonte_horas = Column(Integer)
    fecha_prediccion = Column(DateTime)
    valor_predicho_kg = Column(Float)
    valor_real_kg = Column(Float)
    modelo_lstm_version = Column(String)
    error_rmse = Column(Float)
    error_mape = Column(Float)
    zona = relationship('Zona', back_populates='predicciones')

class Operador(Base):
    __tablename__ = 'operador'
    id_operador = Column(Integer, primary_key=True)
    id_usuario = Column(Integer, ForeignKey('usuario.id_usuario'))
    nombre = Column(String, nullable=False)
    email = Column(String)
    telefono = Column(String)
    estado = Column(String)
    usuario = relationship('Usuario')

class PuntoDisposicion(Base):
    __tablename__ = 'punto_disposicion'
    id_punto_disp = Column(Integer, primary_key=True)
    nombre = Column(String)
    tipo = Column(String)
    latitud = Column(Float)
    longitud = Column(Float)
    capacidad_diaria_ton = Column(Float)

class Usuario(Base):
    __tablename__ = 'usuario'
    id_usuario = Column(Integer, primary_key=True)
    nombre = Column(String)
    correo = Column(String)
    rol = Column(String)
    hash_password = Column(String)
    activo = Column(Boolean)

class PeriodoTemporal(Base):
    __tablename__ = 'periodo_temporal'
    id_periodo = Column(Integer, primary_key=True)
    fecha_inicio = Column(DateTime)
    fecha_fin = Column(DateTime)
    tipo_granularidad = Column(String)
    estacionalidad = Column(String)
