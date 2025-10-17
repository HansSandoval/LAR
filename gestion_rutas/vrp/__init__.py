"""vrp - Módulo para planificación de rutas con Vehicle Routing Problem (VRP)

Exporta:
- schemas: modelos Pydantic para entrada/salida
- planificador: heurística y funciones para resolver VRP
- optimizacion: búsqueda local (2-opt, Or-opt)
"""

from .schemas import VRPInput, VRPOutput, NodeCoordinate
from .planificador import planificar_vrp_api, nearest_neighbor_vrp
from .optimizacion import optimiza_rutas_2opt, or_opt_single

__all__ = [
    'VRPInput',
    'VRPOutput',
    'NodeCoordinate',
    'planificar_vrp_api',
    'nearest_neighbor_vrp',
    'optimiza_rutas_2opt',
    'or_opt_single',
]
