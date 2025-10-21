"""
Service Layer para Enrutamiento
Utiliza OSRM (Open Source Routing Machine) para calcular rutas
"""

import requests
from typing import List, Dict, Optional
from ..models.base import Punto
import logging

logger = logging.getLogger(__name__)


class RoutingService:
    """Servicio para enrutamiento usando OSRM"""
    
    OSRM_URL = "http://router.project-osrm.org/route/v1/driving"
    
    @staticmethod
    def obtener_ruta_entre_puntos(punto_origen: Punto, punto_destino: Punto) -> Optional[Dict]:
        """
        Obtener ruta entre dos puntos usando OSRM
        
        Args:
            punto_origen: Punto de inicio
            punto_destino: Punto de destino
            
        Returns:
            Dict con geometry, distancia y duración o None si falla
        """
        try:
            coords = f"{punto_origen.longitud},{punto_origen.latitud};{punto_destino.longitud},{punto_destino.latitud}"
            
            params = {
                "steps": "true",
                "geometries": "geojson",
                "overview": "full"
            }
            
            response = requests.get(
                f"{RoutingService.OSRM_URL}/{coords}", 
                params=params, 
                timeout=10
            )
            data = response.json()
            
            if data.get("code") == "Ok" and data.get("routes"):
                ruta = data["routes"][0]
                return {
                    "geometry": ruta["geometry"],
                    "distancia_km": round(ruta["distance"] / 1000, 2),
                    "duracion_minutos": round(ruta["duration"] / 60, 2)
                }
            return None
        except Exception as e:
            logger.error(f"Error en enrutamiento entre puntos: {str(e)}")
            return None
    
    @staticmethod
    def obtener_ruta_optimizada(puntos: List[Punto]) -> Optional[Dict]:
        """
        Obtener ruta optimizada para múltiples puntos (TSP)
        
        Args:
            puntos: Lista de puntos a visitar
            
        Returns:
            Dict con geometry, distancia, duración y orden optimizado
        """
        if not puntos or len(puntos) < 2:
            logger.warning("Se necesitan al menos 2 puntos para optimizar")
            return None
        
        try:
            coords = ";".join([f"{p.longitud},{p.latitud}" for p in puntos])
            
            # Nota: OSRM no tiene parámetro 'optimize', puede usarse 'service=trip'
            # Para TSP real, se recomienda usar un endpoint de OSRM diferente
            params = {
                "steps": "true",
                "geometries": "geojson",
                "overview": "full"
            }
            
            url = f"{RoutingService.OSRM_URL}/{coords}"
            logger.info(f"🚀 Llamando a OSRM: {url}")
            
            response = requests.get(
                url, 
                params=params, 
                timeout=30
            )
            
            logger.info(f"📦 Respuesta OSRM: Status {response.status_code}")
            
            data = response.json()
            
            logger.info(f"📋 Código OSRM: {data.get('code')}")
            if data.get('code') != 'Ok':
                logger.warning(f"⚠️  OSRM Error - Código: {data.get('code')}, Mensaje: {data.get('message')}")
            
            if data.get("code") == "Ok" and data.get("routes"):
                ruta = data["routes"][0]
                return {
                    "geometry": ruta["geometry"],
                    "distancia_km": round(ruta["distance"] / 1000, 2),
                    "duracion_minutos": round(ruta["duration"] / 60, 2),
                    "orden_optimizado": data.get("waypoint_order", list(range(len(puntos))))
                }
            logger.warning(f"❌ OSRM no retornó rutas válidas")
            return None
        except requests.exceptions.Timeout:
            logger.error("❌ Timeout al conectar con OSRM")
            return None
        except requests.exceptions.ConnectionError:
            logger.error("❌ Error de conexión con OSRM")
            return None
        except Exception as e:
            logger.error(f"❌ Error en enrutamiento optimizado: {str(e)}")
            return None
