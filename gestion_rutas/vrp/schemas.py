from typing import List, Optional, Union
from pydantic import BaseModel, Field


class NodeCoordinate(BaseModel):
    """Representa una zona candidata por coordenadas y demanda estimada."""
    id: Optional[Union[int, str]] = Field(None, description="ID opcional de la zona")
    x: float = Field(..., description="Coordenada X / longitud")
    y: float = Field(..., description="Coordenada Y / latitud")
    demand: Optional[float] = Field(0.0, description="Demanda estimada (kg)")


class VRPInput(BaseModel):
    """
    Entrada para el planificador VRP.

    - candidates: lista de zonas candidatas (coordenadas y demanda). El primer elemento se
      considera el depósito (depot).
    - distance_matrix: opcionalmente, una matriz precomputada de distancias (nxn).
    - vehicle_count y capacity: parámetros del problema.
    """
    candidates: List[NodeCoordinate]
    distance_matrix: Optional[List[List[float]]] = None
    vehicle_count: int = Field(1, gt=0)
    capacity: float = Field(..., gt=0)


class VRPOutput(BaseModel):
    """Salida del planificador VRP."""
    routes: List[List[Union[int, str]]] = Field(..., description="Rutas: listas de IDs o índices (incluye depósito al inicio y fin)")
    unassigned: List[Union[int, str]] = Field([], description="IDs o índices no asignados")
    total_distance: float = Field(0.0, description="Distancia total aproximada")
