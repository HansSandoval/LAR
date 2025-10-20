"""
Esquemas Pydantic para validación y serialización
Define requests/responses de la API REST
"""

from pydantic import BaseModel, Field, EmailStr, validator
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
    email: EmailStr
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
    email: Optional[EmailStr] = None
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
    algoritmo_vrp: Optional[str] = "nearest_neighbor"


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
