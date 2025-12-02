"""
Esquemas Pydantic para validación y serialización
Define requests/responses de la API REST
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime, date, time
from enum import Enum


# ============================================================================
# ENUMS
# ============================================================================

class EstadoRutaSchema(str, Enum):
    PLANIFICADA = "planificada"
    EN_PROGRESO = "en_progreso"
    COMPLETADA = "completada"
    CANCELADA = "cancelada"


class EstadoVehiculoSchema(str, Enum):
    DISPONIBLE = "disponible"
    EN_SERVICIO = "en_servicio"
    MANTENIMIENTO = "mantenimiento"
    INACTIVO = "inactivo"


class EstadoEntregaSchema(str, Enum):
    PENDIENTE = "pendiente"
    EN_TRANSITO = "en_transito"
    ENTREGADA = "entregada"
    FALLIDA = "fallida"


# ============================================================================
# CLIENTE - SCHEMAS
# ============================================================================

class ClienteBase(BaseModel):
    """Base schema para Cliente"""
    nombre: str = Field(..., min_length=1, max_length=255)
    email: str
    telefono: Optional[str] = Field(None, max_length=20)
    empresa: Optional[str] = Field(None, max_length=255)
    direccion: Optional[str] = Field(None, max_length=500)
    ciudad: Optional[str] = Field(None, max_length=100)
    estado_activo: bool = True


class ClienteCreate(ClienteBase):
    """Schema para crear Cliente"""
    pass


class ClienteUpdate(BaseModel):
    """Schema para actualizar Cliente"""
    nombre: Optional[str] = None
    email: Optional[str] = None
    telefono: Optional[str] = None
    empresa: Optional[str] = None
    direccion: Optional[str] = None
    ciudad: Optional[str] = None
    estado_activo: Optional[bool] = None


class ClienteResponse(ClienteBase):
    """Schema para respuesta de Cliente"""
    id: int
    fecha_registro: datetime
    fecha_actualizacion: datetime

    class Config:
        from_attributes = True


# ============================================================================
# VEHÍCULO - SCHEMAS
# ============================================================================

class VehiculoBase(BaseModel):
    """Base schema para Vehículo"""
    placa: str = Field(..., min_length=1, max_length=20)
    marca: Optional[str] = Field(None, max_length=100)
    modelo: Optional[str] = Field(None, max_length=100)
    anio: Optional[int] = None
    capacidad_kg: float = Field(..., gt=0)
    combustible_km_litro: float = Field(10.0, gt=0)
    conductor_asignado: Optional[str] = None
    ultimo_mantenimiento: Optional[date] = None
    proximo_mantenimiento: Optional[date] = None

    @validator('anio')
    def validar_anio(cls, v):
        if v and (v < 1990 or v > 2100):
            raise ValueError('Año debe estar entre 1990 y 2100')
        return v


class VehiculoCreate(VehiculoBase):
    """Schema para crear Vehículo"""
    pass


class VehiculoUpdate(BaseModel):
    """Schema para actualizar Vehículo"""
    placa: Optional[str] = None
    marca: Optional[str] = None
    modelo: Optional[str] = None
    anio: Optional[int] = None
    capacidad_kg: Optional[float] = None
    combustible_km_litro: Optional[float] = None
    estado: Optional[EstadoVehiculoSchema] = None
    conductor_asignado: Optional[str] = None
    ubicacion_actual_x: Optional[float] = None
    ubicacion_actual_y: Optional[float] = None


class VehiculoResponse(VehiculoBase):
    """Schema para respuesta de Vehículo"""
    id: int
    tipo: str
    estado: EstadoVehiculoSchema
    ubicacion_actual_x: Optional[float]
    ubicacion_actual_y: Optional[float]
    fecha_registro: datetime
    fecha_actualizacion: datetime

    class Config:
        from_attributes = True


# ============================================================================
# PUNTO - SCHEMAS
# ============================================================================

class PuntoBase(BaseModel):
    """Base schema para Punto"""
    nombre: str = Field(..., min_length=1, max_length=255)
    descripcion: Optional[str] = Field(None, max_length=500)
    latitud: float = Field(..., ge=-90, le=90)
    longitud: float = Field(..., ge=-180, le=180)
    tipo_punto: Optional[str] = Field(None, max_length=50)
    estado_activo: bool = True


class PuntoCreate(PuntoBase):
    """Schema para crear Punto"""
    pass


class PuntoUpdate(BaseModel):
    """Schema para actualizar Punto"""
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    latitud: Optional[float] = None
    longitud: Optional[float] = None
    tipo_punto: Optional[str] = None
    estado_activo: Optional[bool] = None


class PuntoResponse(PuntoBase):
    """Schema para respuesta de Punto"""
    id: int
    fecha_registro: datetime
    fecha_actualizacion: datetime

    class Config:
        from_attributes = True


# ============================================================================
# ENTREGA - SCHEMAS
# ============================================================================

class EntregaBase(BaseModel):
    """Base schema para Entrega"""
    id_cliente: int
    id_punto: int
    descripcion: Optional[str] = None
    peso_kg: float = Field(..., gt=0)
    volumen_m3: Optional[float] = Field(None, gt=0)
    prioridad: int = Field(1, ge=1, le=3)
    fecha_programada: date
    ventana_inicio: Optional[time] = None
    ventana_fin: Optional[time] = None
    observaciones: Optional[str] = None


class EntregaCreate(EntregaBase):
    """Schema para crear Entrega"""
    pass


class EntregaUpdate(BaseModel):
    """Schema para actualizar Entrega"""
    id_cliente: Optional[int] = None
    id_punto: Optional[int] = None
    descripcion: Optional[str] = None
    peso_kg: Optional[float] = None
    volumen_m3: Optional[float] = None
    estado: Optional[EstadoEntregaSchema] = None
    prioridad: Optional[int] = None
    fecha_programada: Optional[date] = None
    ventana_inicio: Optional[time] = None
    ventana_fin: Optional[time] = None
    observaciones: Optional[str] = None


class EntregaResponse(EntregaBase):
    """Schema para respuesta de Entrega"""
    id: int
    id_ruta: Optional[int]
    id_vehiculo: Optional[int]
    estado: EstadoEntregaSchema
    fecha_creacion: datetime
    fecha_entrega_real: Optional[datetime]
    tiempo_transito_minutos: Optional[float]
    fecha_actualizacion: datetime

    class Config:
        from_attributes = True


# ============================================================================
# RUTA - SCHEMAS
# ============================================================================

class RutaBase(BaseModel):
    """Base schema para Ruta"""
    id_cliente: int
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    fecha_planificacion: date
    secuencia_puntos: List[int] = Field(..., min_items=1)
    algoritmo_vrp: Optional[str] = "2opt"


class RutaCreate(RutaBase):
    """Schema para crear Ruta"""
    id_vehiculo: Optional[int] = None


class RutaUpdate(BaseModel):
    """Schema para actualizar Ruta"""
    id_cliente: Optional[int] = None
    id_vehiculo: Optional[int] = None
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    estado: Optional[EstadoRutaSchema] = None
    secuencia_puntos: Optional[List[int]] = None


class RutaResponse(RutaBase):
    """Schema para respuesta de Ruta"""
    id: int
    id_vehiculo: Optional[int]
    fecha_ejecucion: Optional[date]
    estado: EstadoRutaSchema
    distancia_planificada_km: Optional[float]
    duracion_planificada_minutos: Optional[float]
    distancia_real_km: Optional[float]
    duracion_real_minutos: Optional[float]
    desviacion_distancia: Optional[float]
    desviacion_tiempo: Optional[float]
    version_algoritmo: Optional[str]
    fecha_creacion: datetime
    fecha_actualizacion: datetime

    class Config:
        from_attributes = True


class RutaConEntregas(RutaResponse):
    """Schema de Ruta con detalles de entregas"""
    entregas: List[EntregaResponse] = []


# ============================================================================
# RESPUESTAS GENERALES
# ============================================================================

class PaginationParams(BaseModel):
    """Parámetros para paginación"""
    skip: int = Field(0, ge=0)
    limit: int = Field(10, ge=1, le=100)


class PaginatedResponse(BaseModel):
    """Respuesta paginada genérica"""
    total: int
    skip: int
    limit: int
    items: List[Any]


class ErrorResponse(BaseModel):
    """Schema para respuesta de error"""
    detail: str
    code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SuccessResponse(BaseModel):
    """Schema para respuesta exitosa"""
    message: str
    data: Optional[Any] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# ZONA - SCHEMAS
# ============================================================================

class ZonaBase(BaseModel):
    """Base schema para Zona"""
    nombre: str = Field(..., min_length=1, max_length=255)
    tipo: Optional[str] = Field(None, max_length=50)
    area_km2: Optional[float] = Field(None, gt=0)
    poblacion: Optional[int] = Field(None, ge=0)
    coordenadas_limite: Optional[str] = None
    prioridad: Optional[int] = None


class ZonaCreate(ZonaBase):
    """Schema para crear Zona"""
    pass


class ZonaUpdate(BaseModel):
    """Schema para actualizar Zona"""
    nombre: Optional[str] = None
    tipo: Optional[str] = None
    area_km2: Optional[float] = None
    poblacion: Optional[int] = None
    coordenadas_limite: Optional[str] = None
    prioridad: Optional[int] = None


class ZonaResponse(ZonaBase):
    """Schema para respuesta de Zona"""
    id_zona: int

    class Config:
        from_attributes = True


# ============================================================================
# PUNTO DE RECOLECCIÓN - SCHEMAS
# ============================================================================

class PuntoRecoleccionBase(BaseModel):
    """Base schema para PuntoRecoleccion"""
    id_zona: int
    nombre: str = Field(..., min_length=1, max_length=255)
    tipo: Optional[str] = Field(None, max_length=50)
    latitud: float
    longitud: float
    capacidad_kg: Optional[float] = Field(None, gt=0)
    estado: Optional[str] = Field("activo", max_length=50)


class PuntoRecoleccionCreate(PuntoRecoleccionBase):
    """Schema para crear PuntoRecoleccion"""
    pass


class PuntoRecoleccionUpdate(BaseModel):
    """Schema para actualizar PuntoRecoleccion"""
    id_zona: Optional[int] = None
    nombre: Optional[str] = None
    tipo: Optional[str] = None
    latitud: Optional[float] = None
    longitud: Optional[float] = None
    capacidad_kg: Optional[float] = None
    estado: Optional[str] = None


class PuntoRecoleccionResponse(PuntoRecoleccionBase):
    """Schema para respuesta de PuntoRecoleccion"""
    id_punto: int

    class Config:
        from_attributes = True


# ============================================================================
# CAMIÓN - SCHEMAS
# ============================================================================

class CamionBase(BaseModel):
    """Base schema para Camion"""
    patente: Optional[str] = Field(None, max_length=20)
    capacidad_kg: float = Field(..., gt=0)
    consumo_km_l: Optional[float] = Field(None, ge=0)
    tipo_combustible: Optional[str] = Field(None, max_length=50)
    estado_operativo: Optional[str] = Field(None, max_length=50)
    gps_id: Optional[str] = Field(None, max_length=50)


class CamionCreate(CamionBase):
    """Schema para crear Camion"""
    pass


class CamionUpdate(BaseModel):
    """Schema para actualizar Camion"""
    patente: Optional[str] = None
    capacidad_kg: Optional[float] = None
    consumo_km_l: Optional[float] = None
    tipo_combustible: Optional[str] = None
    estado_operativo: Optional[str] = None
    gps_id: Optional[str] = None


class CamionResponse(CamionBase):
    """Schema para respuesta de Camion"""
    id_camion: int

    class Config:
        from_attributes = True


# ============================================================================
# RUTA PLANIFICADA - SCHEMAS
# ============================================================================

class RutaPlanificadaBase(BaseModel):
    """Base schema para RutaPlanificada"""
    id_zona: Optional[int] = None
    id_turno: Optional[int] = None
    id_camion: Optional[int] = None
    fecha: Optional[date] = None
    secuencia_puntos: Optional[List[int]] = None
    estado: Optional[str] = Field("planificada", max_length=50)
    distancia_km: Optional[float] = Field(None, ge=0)
    tiempo_estimado_min: Optional[float] = Field(None, ge=0)
    version_modelo_vrp: Optional[str] = Field("2opt", max_length=100)
    geometria_json: Optional[List[List[float]]] = None # [[lat,lon], ...]


class RutaPlanificadaCreate(RutaPlanificadaBase):
    """Schema para crear RutaPlanificada"""
    pass


class RutaPlanificadaUpdate(BaseModel):
    """Schema para actualizar RutaPlanificada"""
    id_zona: Optional[int] = None
    id_turno: Optional[int] = None
    id_camion: Optional[int] = None
    fecha: Optional[date] = None
    secuencia_puntos: Optional[List[int]] = None
    estado: Optional[str] = None
    distancia_km: Optional[float] = None
    tiempo_estimado_min: Optional[float] = None
    version_modelo_vrp: Optional[str] = None
    geometria_json: Optional[List[List[float]]] = None


class RutaPlanificadaResponse(RutaPlanificadaBase):
    """Schema para respuesta de RutaPlanificada"""
    id_ruta: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================================
# TURNO - SCHEMAS
# ============================================================================

class TurnoBase(BaseModel):
    """Base schema para Turno"""
    id_camion: int
    fecha: date
    hora_inicio: time
    hora_fin: time
    operador: str = Field(..., min_length=1, max_length=255)
    estado: Optional[str] = Field("activo", max_length=50)


class TurnoCreate(TurnoBase):
    """Schema para crear Turno"""
    pass


class TurnoUpdate(BaseModel):
    """Schema para actualizar Turno"""
    id_camion: Optional[int] = None
    fecha: Optional[date] = None
    hora_inicio: Optional[time] = None
    hora_fin: Optional[time] = None
    operador: Optional[str] = None
    estado: Optional[str] = None


class TurnoResponse(TurnoBase):
    """Schema para respuesta de Turno"""
    id_turno: int

    class Config:
        from_attributes = True


# ============================================================================
# RUTA EJECUTADA - SCHEMAS
# ============================================================================

class RutaEjecutadaBase(BaseModel):
    """Base schema para RutaEjecutada"""
    id_ruta: int
    id_camion: int
    fecha: date
    distancia_real_km: float = Field(..., ge=0)
    duracion_real_min: float = Field(..., ge=0)
    cumplimiento_horario_pct: float = Field(..., ge=0, le=100)
    desviacion_km: Optional[float] = Field(None, ge=0)
    telemetria_json: Optional[Dict[str, Any]] = None


class RutaEjecutadaCreate(RutaEjecutadaBase):
    """Schema para crear RutaEjecutada"""
    pass


class RutaEjecutadaUpdate(BaseModel):
    """Schema para actualizar RutaEjecutada"""
    id_ruta: Optional[int] = None
    id_camion: Optional[int] = None
    fecha: Optional[date] = None
    distancia_real_km: Optional[float] = None
    duracion_real_min: Optional[float] = None
    cumplimiento_horario_pct: Optional[float] = None
    desviacion_km: Optional[float] = None
    telemetria_json: Optional[Dict[str, Any]] = None


class RutaEjecutadaResponse(RutaEjecutadaBase):
    """Schema para respuesta de RutaEjecutada"""
    id_ruta_exec: int

    class Config:
        from_attributes = True


# ============================================================================
# INCIDENCIA - SCHEMAS
# ============================================================================

class IncidenciaBase(BaseModel):
    """Base schema para Incidencia"""
    id_ruta_exec: Optional[int] = None
    id_zona: int
    id_camion: int
    tipo: str = Field(..., min_length=1, max_length=100)
    descripcion: str = Field(..., min_length=1, max_length=1000)
    fecha_hora: datetime
    severidad: int = Field(..., ge=1, le=5)


class IncidenciaCreate(IncidenciaBase):
    """Schema para crear Incidencia"""
    pass


class IncidenciaUpdate(BaseModel):
    """Schema para actualizar Incidencia"""
    id_ruta_exec: Optional[int] = None
    id_zona: Optional[int] = None
    id_camion: Optional[int] = None
    tipo: Optional[str] = None
    descripcion: Optional[str] = None
    fecha_hora: Optional[datetime] = None
    severidad: Optional[int] = None


class IncidenciaResponse(IncidenciaBase):
    """Schema para respuesta de Incidencia"""
    id_incidencia: int

    class Config:
        from_attributes = True


# ============================================================================
# PREDICCION DEMANDA - SCHEMAS
# ============================================================================

class PrediccionDemandaBase(BaseModel):
    """Base schema para PrediccionDemanda"""
    id_zona: int
    horizonte_horas: int = Field(..., ge=1)
    fecha_prediccion: datetime
    valor_predicho_kg: float = Field(..., ge=0)
    valor_real_kg: Optional[float] = Field(None, ge=0)
    modelo_lstm_version: str = Field(..., min_length=1, max_length=50)
    error_rmse: Optional[float] = Field(None, ge=0)
    error_mape: Optional[float] = Field(None, ge=0)


class PrediccionDemandaCreate(PrediccionDemandaBase):
    """Schema para crear PrediccionDemanda"""
    pass


class PrediccionDemandaUpdate(BaseModel):
    """Schema para actualizar PrediccionDemanda"""
    id_zona: Optional[int] = None
    horizonte_horas: Optional[int] = None
    fecha_prediccion: Optional[datetime] = None
    valor_predicho_kg: Optional[float] = None
    valor_real_kg: Optional[float] = None
    modelo_lstm_version: Optional[str] = None
    error_rmse: Optional[float] = None
    error_mape: Optional[float] = None


class PrediccionDemandaResponse(PrediccionDemandaBase):
    """Schema para respuesta de PrediccionDemanda"""
    id_prediccion: int

    class Config:
        from_attributes = True


# ============================================================================
# USUARIO - SCHEMAS
# ============================================================================

class UsuarioBase(BaseModel):
    """Base schema para Usuario"""
    nombre: str = Field(..., min_length=1, max_length=255)
    correo: str
    rol: str = Field(..., max_length=50)
    activo: bool = True


class UsuarioCreate(UsuarioBase):
    """Schema para crear Usuario"""
    password: str = Field(..., min_length=8, max_length=255)


class UsuarioUpdate(BaseModel):
    """Schema para actualizar Usuario"""
    nombre: Optional[str] = None
    correo: Optional[str] = None
    rol: Optional[str] = None
    activo: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=8, max_length=255)


class UsuarioResponse(UsuarioBase):
    """Schema para respuesta de Usuario"""
    id_usuario: int

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    """Schema para login"""
    correo: str
    password: str



# ============================================================================
# PUNTO DISPOSICION - SCHEMAS
# ============================================================================

class PuntoDisposicionBase(BaseModel):
    """Base schema para PuntoDisposicion"""
    nombre: str = Field(..., min_length=1, max_length=255)
    tipo: str = Field(..., min_length=1, max_length=100)
    latitud: float = Field(..., ge=-90, le=90)
    longitud: float = Field(..., ge=-180, le=180)
    capacidad_diaria_ton: float = Field(..., ge=0)


class PuntoDisposicionCreate(PuntoDisposicionBase):
    """Schema para crear PuntoDisposicion"""
    pass


class PuntoDisposicionUpdate(BaseModel):
    """Schema para actualizar PuntoDisposicion"""
    nombre: Optional[str] = None
    tipo: Optional[str] = None
    latitud: Optional[float] = None
    longitud: Optional[float] = None
    capacidad_diaria_ton: Optional[float] = None


class PuntoDisposicionResponse(PuntoDisposicionBase):
    """Schema para respuesta de PuntoDisposicion"""
    id_punto_disp: int

    class Config:
        from_attributes = True


# ============================================================================
# PERIODO TEMPORAL - SCHEMAS
# ============================================================================

class PeriodoTemporalBase(BaseModel):
    """Base schema para PeriodoTemporal"""
    fecha_inicio: datetime
    fecha_fin: datetime
    tipo_granularidad: str = Field(..., max_length=50)
    estacionalidad: Optional[str] = Field("general", max_length=50)


class PeriodoTemporalCreate(PeriodoTemporalBase):
    """Schema para crear PeriodoTemporal"""
    pass


class PeriodoTemporalUpdate(BaseModel):
    """Schema para actualizar PeriodoTemporal"""
    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None
    tipo_granularidad: Optional[str] = None
    estacionalidad: Optional[str] = None


class PeriodoTemporalResponse(PeriodoTemporalBase):
    """Schema para respuesta de PeriodoTemporal"""
    id_periodo: int

    class Config:
        from_attributes = True


# ============================================================================
# OPERADOR - SCHEMAS
# ============================================================================

class OperadorBase(BaseModel):
    """Base schema para Operador"""
    nombre: str = Field(..., min_length=1, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    telefono: Optional[str] = Field(None, max_length=50)
    estado: Optional[str] = Field("activo", max_length=50)
    id_usuario: Optional[int] = None

class OperadorCreate(OperadorBase):
    """Schema para crear Operador"""
    pass

class OperadorUpdate(BaseModel):
    """Schema para actualizar Operador"""
    nombre: Optional[str] = None
    email: Optional[str] = None
    telefono: Optional[str] = None
    estado: Optional[str] = None
    id_usuario: Optional[int] = None

class OperadorResponse(OperadorBase):
    """Schema para respuesta de Operador"""
    id_operador: int
    
    class Config:
        from_attributes = True
