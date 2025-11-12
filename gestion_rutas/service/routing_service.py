"""
Service Layer para Enrutamiento
Utiliza OSRM (Open Source Routing Machine) para calcular rutas reales por calles.

OSRM proporciona:
- Rutas siguiendo calles reales
- Optimización de distancia y tiempo
- Soporte para múltiples waypoints
- Cálculo de matriz de distancias
"""

import requests
from typing import List, Dict, Optional, Tuple
from ..models.base import Punto
import logging
from functools import lru_cache
import json

logger = logging.getLogger(__name__)


class RoutingService:
    """Servicio para enrutamiento usando OSRM (calles reales de OpenStreetMap)"""
    
    OSRM_URL = "http://router.project-osrm.org/route/v1/driving"
    OSRM_TABLE_URL = "http://router.project-osrm.org/table/v1/driving"
    OSRM_TRIP_URL = "http://router.project-osrm.org/trip/v1/driving"
    
    # Caché para rutas ya calculadas
    _route_cache: Dict[str, Dict] = {}
    _distance_cache: Dict[str, float] = {}
    
    @staticmethod
    def _make_cache_key(coords: str) -> str:
        """Genera clave para caché"""
        return coords
    
    @staticmethod
    def obtener_ruta_entre_puntos(punto_origen: Punto, punto_destino: Punto) -> Optional[Dict]:
        """
        Obtener ruta real por calles entre dos puntos usando OSRM.
        La ruta sigue las calles y carreteras reales.
        
        Args:
            punto_origen: Punto de inicio
            punto_destino: Punto de destino
            
        Returns:
            Dict con:
                - geometry: Lista de coordenadas [lon, lat] de la ruta completa
                - distancia_km: Distancia real en kilómetros
                - duracion_minutos: Tiempo estimado en minutos
                - waypoints: Puntos de paso
        """
        try:
            coords = f"{punto_origen.longitud},{punto_origen.latitud};{punto_destino.longitud},{punto_destino.latitud}"
            
            # Verificar caché
            cache_key = coords
            if cache_key in RoutingService._route_cache:
                logger.debug("Ruta obtenida del caché")
                return RoutingService._route_cache[cache_key]
            
            params = {
                "steps": "true",
                "geometries": "geojson",
                "overview": "full",
                "annotations": "true"
            }
            
            response = requests.get(
                f"{RoutingService.OSRM_URL}/{coords}", 
                params=params, 
                timeout=10
            )
            data = response.json()
            
            if data.get("code") == "Ok" and data.get("routes"):
                ruta = data["routes"][0]
                result = {
                    "geometry": ruta["geometry"]["coordinates"],  # Lista de [lon, lat]
                    "distancia_km": round(ruta["distance"] / 1000, 2),
                    "duracion_minutos": round(ruta["duration"] / 60, 2),
                    "waypoints": data.get("waypoints", [])
                }
                
                # Guardar en caché
                RoutingService._route_cache[cache_key] = result
                return result
            
            logger.warning(f"OSRM no pudo calcular ruta: {data.get('message', 'Unknown')}")
            return None
        except Exception as e:
            logger.error(f"Error en enrutamiento entre puntos: {str(e)}")
            return None
    
    @staticmethod
    def obtener_ruta_optimizada(puntos: List[Punto]) -> Optional[Dict]:
        """
        Obtener ruta optimizada visitando múltiples puntos (TSP con calles reales).
        OSRM calculará el orden óptimo para minimizar distancia.
        
        Args:
            puntos: Lista de puntos a visitar
            
        Returns:
            Dict con:
                - geometry: Ruta completa por calles reales
                - distancia_km: Distancia total
                - duracion_minutos: Tiempo total
                - orden_optimizado: Orden en que deben visitarse los puntos
        """
        if not puntos or len(puntos) < 2:
            logger.warning("Se necesitan al menos 2 puntos para optimizar")
            return None
        
        try:
            coords = ";".join([f"{p.longitud},{p.latitud}" for p in puntos])
            
            # Usar el endpoint 'trip' de OSRM para optimización TSP
            params = {
                "steps": "true",
                "geometries": "geojson",
                "overview": "full",
                "source": "first",
                "destination": "last",
                "roundtrip": "false"
            }
            
            url = f"{RoutingService.OSRM_TRIP_URL}/{coords}"
            logger.info(f"🚀 Optimizando ruta con {len(puntos)} puntos")
            
            response = requests.get(url, params=params, timeout=30)
            logger.info(f"📦 Respuesta OSRM: Status {response.status_code}")
            
            data = response.json()
            logger.info(f"📋 Código OSRM: {data.get('code')}")
            
            if data.get('code') != 'Ok':
                logger.warning(f"⚠️  OSRM Error - {data.get('message')}")
                return None
            
            if data.get("trips"):
                trip = data["trips"][0]
                waypoints = data.get("waypoints", [])
                orden_optimizado = [wp.get("waypoint_index", i) for i, wp in enumerate(waypoints)]
                
                result = {
                    "geometry": trip["geometry"]["coordinates"],
                    "distancia_km": round(trip["distance"] / 1000, 2),
                    "duracion_minutos": round(trip["duration"] / 60, 2),
                    "orden_optimizado": orden_optimizado,
                    "num_puntos": len(puntos)
                }
                
                logger.info(f"✅ Ruta optimizada: {result['distancia_km']} km")
                return result
            
            return None
        except Exception as e:
            logger.error(f"❌ Error en optimización de ruta: {str(e)}")
            return None
    
    # @staticmethod
    # async def obtener_ruta_async(punto_origen: Punto, punto_destino: Punto) -> Optional[Dict]:
    #     """Versión asíncrona para obtener ruta (mejor rendimiento)"""
    #     # Requiere aiohttp: pip install aiohttp
    #     pass
    
    @staticmethod
    def obtener_matriz_distancias(puntos: List[Punto]) -> Optional[List[List[float]]]:
        """
        Calcula matriz de distancias REALES por calles entre todos los puntos.
        """
        if not puntos:
            return None
        
        try:
            coords = ";".join([f"{p.longitud},{p.latitud}" for p in puntos])
            params = {"annotations": "distance,duration"}
            url = f"{RoutingService.OSRM_TABLE_URL}/{coords}"
            
            logger.info(f"📊 Calculando matriz para {len(puntos)} puntos")
            response = requests.get(url, params=params, timeout=60)
            data = response.json()
            
            if data.get("code") == "Ok" and data.get("distances"):
                distancias_m = data["distances"]
                distancias_km = [[d / 1000 if d else 0 for d in fila] for fila in distancias_m]
                logger.info(f"✅ Matriz calculada: {len(distancias_km)}x{len(distancias_km[0])}")
                return distancias_km
            
            return None
        except Exception as e:
            logger.error(f"Error matriz: {str(e)}")
            return None
    
    @staticmethod
    def clear_cache():
        """Limpia el caché de rutas"""
        RoutingService._route_cache.clear()
        RoutingService._distance_cache.clear()
        logger.info("Caché limpiado")
