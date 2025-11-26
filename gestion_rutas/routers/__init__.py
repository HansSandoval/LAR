"""Routers - Módulo de rutas"""

from . import ruta
from . import mapa_router
from . import zona_router
from . import punto_router
from . import camion_router
from . import ruta_planificada_router
from . import turno_router
from . import usuario_router
from . import punto_disposicion_router
from . import lstm_router
from . import mas_router

# Routers pendientes de conversión a PostgreSQL directo (comentados por ahora)
# from . import mapa_predicciones_router
# from . import ruta_ejecutada_router
# from . import incidencia_router
# from . import prediccion_demanda_router
# from . import periodo_temporal_router

__all__ = [
    'ruta',
    'lstm_router',
    'mapa_router',
    'mapa_predicciones_router',
    'mas_router',
    'zona_router',
    'punto_router',
    'camion_router',
    'ruta_planificada_router',
    'turno_router',
    'ruta_ejecutada_router',
    'incidencia_router',
    'prediccion_demanda_router',
    'usuario_router',
    'punto_disposicion_router',
    'periodo_temporal_router',
]
