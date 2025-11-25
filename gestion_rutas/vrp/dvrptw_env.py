"""
Entorno DVRPTW (Dynamic Vehicle Routing Problem with Time Windows)
Adaptado para recolección de residuos SIN restricciones de ventanas de tiempo.

Los camiones son agentes autónomos que cooperan para recolectar residuos
basándose en predicciones LSTM y demanda real.

ACTUALIZACIÓN: Usa routing por calles reales con OSRM.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
import gymnasium as gym
from gymnasium import spaces
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
import requests

logger = logging.getLogger(__name__)

# ==================== OSRM SERVICE INTERNO ====================
class OSRMService:
    """Servicio OSRM simplificado integrado para evitar problemas de imports"""
    
    OSRM_URL = "http://router.project-osrm.org/route/v1/driving"
    _route_cache: Dict[str, Dict] = {}
    
    @staticmethod
    def obtener_ruta(lat1: float, lon1: float, lat2: float, lon2: float) -> Optional[Dict]:
        """
        Obtener ruta real por calles entre dos puntos usando OSRM.
        
        Returns:
            Dict con:
                - geometry: Lista de coordenadas [[lat, lon], ...] (convertidas para Leaflet)
                - distancia_km: Distancia real en kilómetros
                - duracion_minutos: Tiempo estimado en minutos
        """
        try:
            coords = f"{lon1},{lat1};{lon2},{lat2}"
            cache_key = f"{lat1:.6f},{lon1:.6f}-{lat2:.6f},{lon2:.6f}"
            
            # Verificar caché
            if cache_key in OSRMService._route_cache:
                return OSRMService._route_cache[cache_key]
            
            params = {
                "geometries": "geojson",
                "overview": "full"
            }
            
            response = requests.get(
                f"{OSRMService.OSRM_URL}/{coords}", 
                params=params, 
                timeout=5
            )
            data = response.json()
            
            if data.get("code") == "Ok" and data.get("routes"):
                ruta = data["routes"][0]
                # Convertir geometría de [lon, lat] a [lat, lon] para Leaflet
                geometry_leaflet = [[coord[1], coord[0]] for coord in ruta["geometry"]["coordinates"]]
                
                result = {
                    "geometry": geometry_leaflet,
                    "distancia_km": round(ruta["distance"] / 1000, 2),
                    "duracion_minutos": round(ruta["duration"] / 60, 2)
                }
                
                # Guardar en caché
                OSRMService._route_cache[cache_key] = result
                return result
            
            return None
        except Exception as e:
            logger.warning(f"Error OSRM: {e}")
            return None


@dataclass
class Cliente:
    """Representa un punto de recolección (cliente)"""
    id: int
    nombre: str
    latitud: float
    longitud: float
    demanda_kg: float  # Demanda de residuos predicha por LSTM
    prioridad: int = 1  # 1=normal, 2=alto, 3=urgente
    servido: bool = False
    tiempo_servicio: float = 10.0  # Minutos para recolectar
    
    # SIN RESTRICCIONES DE TIME WINDOWS
    ventana_inicio: float = 0.0  # Sin límite inferior
    ventana_fin: float = float('inf')  # Sin límite superior


@dataclass
class Camion:
    """Representa un camión de recolección (agente autónomo)"""
    id: int
    capacidad_kg: float
    carga_actual_kg: float = 0.0
    latitud: float = -20.2693  # Posición inicial (centro Sector Sur)
    longitud: float = -70.1703
    tiempo_actual: float = 0.0
    ruta_actual: List[int] = field(default_factory=list)  # IDs de clientes a visitar
    ruta_geometria: List[List[float]] = field(default_factory=list)  # Geometría real de la ruta [lon, lat]
    distancia_recorrida_km: float = 0.0
    activo: bool = True
    
    @property
    def capacidad_disponible(self) -> float:
        return self.capacidad_kg - self.carga_actual_kg
    
    @property
    def porcentaje_carga(self) -> float:
        return (self.carga_actual_kg / self.capacidad_kg) * 100 if self.capacidad_kg > 0 else 0


class DVRPTWEnv(gym.Env):
    """
    Entorno para Dynamic Vehicle Routing Problem WITHOUT Time Windows
    
    Características:
    - Sin restricciones de ventanas de tiempo (valores infinitos)
    - Múltiples camiones cooperativos
    - Demanda dinámica basada en predicciones LSTM
    - Recolección de residuos en Sector Sur de Iquique
    """
    
    metadata = {'render.modes': ['human', 'rgb_array']}
    
    def __init__(
        self,
        num_camiones: int = 3,
        capacidad_camion_kg: float = 3500.0,
        clientes: Optional[List[Dict]] = None,
        depot_lat: float = -20.2693,
        depot_lon: float = -70.1703,
        max_steps: int = 500,
        penalizacion_distancia: float = 0.1,
        recompensa_servicio: float = 10.0,
        usar_routing_real: bool = True,  # NUEVO: Usar OSRM para rutas reales
        seed: int = None
    ):
        """
        Args:
            num_camiones: Número de camiones (agentes)
            capacidad_camion_kg: Capacidad máxima de cada camión
            clientes: Lista de puntos de recolección con demandas
            depot_lat/lon: Ubicación del depósito central
            max_steps: Máximo de pasos por episodio
            penalizacion_distancia: Penalización por km recorrido
            recompensa_servicio: Recompensa por cliente servido
            usar_routing_real: Si True, usa OSRM para calcular rutas por calles reales
            seed: Semilla para reproducibilidad
        """
        super().__init__()
        
        if seed is not None:
            np.random.seed(seed)
        
        self.num_camiones = num_camiones
        self.capacidad_camion_kg = capacidad_camion_kg
        self.depot_lat = depot_lat
        self.depot_lon = depot_lon
        self.max_steps = max_steps
        self.penalizacion_distancia = penalizacion_distancia
        self.recompensa_servicio = recompensa_servicio
        self.usar_routing_real = usar_routing_real  # NUEVO
        
        # Caché para rutas OSRM ya calculadas (mejora rendimiento)
        self._routing_cache: Dict[Tuple[float, float, float, float], Dict] = {}
        
        # Inicializar clientes
        self.clientes = self._inicializar_clientes(clientes)
        self.num_clientes = len(self.clientes)
        
        # Inicializar camiones
        self.camiones = self._inicializar_camiones()
        
        # Estado del episodio
        self.current_step = 0
        self.total_reward = 0.0
        self.clientes_servidos = 0
        
        # Espacios de observación y acción
        self._setup_spaces()
    
    def _inicializar_clientes(self, clientes_data: Optional[List[Dict]]) -> List[Cliente]:
        """Inicializa clientes SIN restricciones de time windows"""
        if clientes_data is None:
            # Generar clientes de ejemplo (deberías cargar desde predicciones LSTM)
            clientes_data = []
            for i in range(50):
                clientes_data.append({
                    'id': i,
                    'nombre': f'Punto_{i}',
                    'latitud': -20.2693 + np.random.uniform(-0.02, 0.02),
                    'longitud': -70.1703 + np.random.uniform(-0.02, 0.02),
                    'demanda_kg': np.random.uniform(20, 150),
                    'prioridad': np.random.choice([1, 2, 3], p=[0.7, 0.2, 0.1])
                })
        
        clientes = []
        for data in clientes_data:
            cliente = Cliente(
                id=data['id'],
                nombre=data.get('nombre', f"Cliente_{data['id']}"),
                latitud=data['latitud'],
                longitud=data['longitud'],
                demanda_kg=data['demanda_kg'],
                prioridad=data.get('prioridad', 1),
                servido=False,
                tiempo_servicio=data.get('tiempo_servicio', 10.0),
                ventana_inicio=0.0,  # ⚠️ SIN LÍMITE INFERIOR
                ventana_fin=float('inf')  # ⚠️ SIN LÍMITE SUPERIOR (INFINITO)
            )
            clientes.append(cliente)
        
        return clientes
    
    def _inicializar_camiones(self) -> List[Camion]:
        """Inicializa flota de camiones"""
        camiones = []
        for i in range(self.num_camiones):
            camion = Camion(
                id=i,
                capacidad_kg=self.capacidad_camion_kg,
                latitud=self.depot_lat,
                longitud=self.depot_lon
            )
            camiones.append(camion)
        return camiones
    
    def _setup_spaces(self):
        """
        Define espacios de observación y acción
        
        Observación (por camión):
        - Posición actual (lat, lon)
        - Carga actual / capacidad
        - Distancia y demanda a cada cliente no servido
        - Prioridad de cada cliente
        
        Acción:
        - ID del próximo cliente a visitar (0 = volver al depósito)
        """
        # Observación: [camion_lat, camion_lon, carga_porcentaje, 
        #               cliente1_dist, cliente1_demanda, cliente1_prioridad, cliente1_servido, ...]
        obs_size = 3 + (self.num_clientes * 4)  # 3 datos camión + 4 datos por cliente
        
        self.observation_space = spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=(obs_size,),
            dtype=np.float32
        )
        
        # Acción: índice del cliente a visitar (0 = depot, 1-N = clientes)
        self.action_space = spaces.Discrete(self.num_clientes + 1)
    
    def reset(self):
        """Reinicia el entorno para un nuevo episodio"""
        # Reiniciar clientes
        for cliente in self.clientes:
            cliente.servido = False
        
        # Reiniciar camiones
        self.camiones = self._inicializar_camiones()
        
        # Reiniciar estado
        self.current_step = 0
        self.total_reward = 0.0
        self.clientes_servidos = 0
        
        return self._get_observation()
    
    def _get_observation(self) -> np.ndarray:
        """
        Obtiene observación del estado actual
        
        Para simplificar, retorna observación del primer camión activo.
        En implementación completa, cada agente tendría su observación.
        """
        # Buscar primer camión activo
        camion = next((c for c in self.camiones if c.activo), self.camiones[0])
        
        obs = [
            camion.latitud,
            camion.longitud,
            camion.porcentaje_carga / 100.0  # Normalizado
        ]
        
        # Información de cada cliente
        for cliente in self.clientes:
            distancia = self._calcular_distancia(
                camion.latitud, camion.longitud,
                cliente.latitud, cliente.longitud
            )
            obs.extend([
                distancia / 10.0,  # Normalizar (asumiendo max 10km)
                cliente.demanda_kg / self.capacidad_camion_kg,  # Normalizar
                cliente.prioridad / 3.0,  # Normalizar (max prioridad = 3)
                1.0 if cliente.servido else 0.0
            ])
        
        return np.array(obs, dtype=np.float32)
    
    def step(self, action: int) -> Tuple[np.ndarray, float, bool, dict]:
        """
        Ejecuta una acción en el entorno
        
        Args:
            action: ID del cliente a visitar (0 = depot)
        
        Returns:
            observation, reward, done, info
        """
        self.current_step += 1
        reward = 0.0
        info = {'evento': None}
        
        # Buscar camión activo (simplificado: usar primer activo)
        camion = next((c for c in self.camiones if c.activo), None)
        
        if camion is None:
            # No hay camiones activos
            return self._get_observation(), 0.0, True, {'evento': 'sin_camiones_activos'}
        
        # Acción 0: Volver al depósito
        if action == 0:
            distancia = self._calcular_distancia(
                camion.latitud, camion.longitud,
                self.depot_lat, self.depot_lon
            )
            
                # Obtener geometría de ruta si está disponible
            if self.usar_routing_real:
                logger.info(f"🗺️ Intentando obtener ruta OSRM de ({camion.latitud}, {camion.longitud}) al depot ({self.depot_lat}, {self.depot_lon})")
                ruta_info = self._obtener_ruta_completa(
                    camion.latitud, camion.longitud,
                    self.depot_lat, self.depot_lon
                )
                if ruta_info and 'geometry' in ruta_info:
                    # ACUMULAR geometría en lugar de sobrescribir
                    if not hasattr(camion, 'ruta_geometria') or not camion.ruta_geometria:
                        camion.ruta_geometria = []
                    camion.ruta_geometria.extend(ruta_info['geometry'])
                    logger.info(f"✅ Geometría OSRM obtenida: {len(ruta_info['geometry'])} puntos (total acumulado: {len(camion.ruta_geometria)})")
                else:
                    logger.warning(f"⚠️ OSRM falló para ruta al depot")
            
            camion.latitud = self.depot_lat
            camion.longitud = self.depot_lon
            camion.distancia_recorrida_km += distancia
            camion.carga_actual_kg = 0.0  # Descargar
            
            # Limpiar geometría acumulada para el próximo ciclo
            camion.ruta_geometria = []
            
            reward -= distancia * self.penalizacion_distancia
            info['evento'] = 'retorno_depot'
        
        # Acción 1-N: Visitar cliente
        elif 1 <= action <= self.num_clientes:
            cliente_id = action - 1
            cliente = self.clientes[cliente_id]
            
            # Validar si el cliente ya fue servido
            if cliente.servido:
                reward -= 5.0  # Penalización por intentar visitar cliente ya servido
                info['evento'] = 'cliente_ya_servido'
            
            # Validar si el camión tiene capacidad
            elif cliente.demanda_kg > camion.capacidad_disponible:
                reward -= 3.0  # Penalización por falta de capacidad
                info['evento'] = 'sin_capacidad'
            
            # Servir al cliente
            else:
                distancia = self._calcular_distancia(
                    camion.latitud, camion.longitud,
                    cliente.latitud, cliente.longitud
                )
                
                # Obtener geometría de ruta real si está disponible
                if self.usar_routing_real:
                    ruta_info = self._obtener_ruta_completa(
                        camion.latitud, camion.longitud,
                        cliente.latitud, cliente.longitud
                    )
                    if ruta_info and 'geometry' in ruta_info:
                        # ACUMULAR geometría en lugar de sobrescribir
                        if not hasattr(camion, 'ruta_geometria') or not camion.ruta_geometria:
                            camion.ruta_geometria = []
                        camion.ruta_geometria.extend(ruta_info['geometry'])
                        logger.debug(f"Ruta a cliente {cliente_id}: {len(ruta_info['geometry'])} puntos (total: {len(camion.ruta_geometria)})")
                
                # Mover camión
                camion.latitud = cliente.latitud
                camion.longitud = cliente.longitud
                camion.distancia_recorrida_km += distancia
                
                # VALIDACIÓN: Verificar que las coordenadas sean válidas (Iquique)
                if not (-20.35 <= camion.latitud <= -20.15):
                    logger.error(f"⚠️ LATITUD FUERA DE RANGO: {camion.latitud} (cliente {cliente.nombre})")
                if not (-70.25 <= camion.longitud <= -70.05):
                    logger.error(f"⚠️ LONGITUD FUERA DE RANGO: {camion.longitud} (cliente {cliente.nombre})")
                
                logger.info(f"🚛 Camión {camion.id} → Cliente '{cliente.nombre}' en ({cliente.latitud:.6f}, {cliente.longitud:.6f}), distancia: {distancia:.2f} km")
                
                # Recolectar residuos
                camion.carga_actual_kg += cliente.demanda_kg
                cliente.servido = True
                self.clientes_servidos += 1
                
                # Calcular recompensa
                recompensa_base = self.recompensa_servicio * cliente.prioridad
                penalizacion_dist = distancia * self.penalizacion_distancia
                reward = recompensa_base - penalizacion_dist
                
                info['evento'] = 'cliente_servido'
                info['cliente_id'] = cliente.id
                info['demanda_recolectada'] = cliente.demanda_kg
        
        # Verificar si el episodio terminó
        done = (
            self.current_step >= self.max_steps or
            self.clientes_servidos >= self.num_clientes
        )
        
        self.total_reward += reward
        info['total_reward'] = self.total_reward
        info['clientes_servidos'] = self.clientes_servidos
        info['step'] = self.current_step
        
        return self._get_observation(), reward, done, info
    
    def _calcular_distancia(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calcula distancia entre dos puntos.
        
        Si usar_routing_real=True, usa OSRM para obtener distancia real por calles.
        Si False o hay error, usa distancia haversine (línea recta).
        
        Returns:
            Distancia en kilómetros
        """
        if self.usar_routing_real:
            try:
                # Buscar en caché primero
                cache_key = (round(lat1, 6), round(lon1, 6), round(lat2, 6), round(lon2, 6))
                
                if cache_key in self._routing_cache:
                    return self._routing_cache[cache_key]['distancia_km']
                
                # Usar servicio OSRM interno
                ruta = OSRMService.obtener_ruta(lat1, lon1, lat2, lon2)
                
                if ruta:
                    # Guardar en caché
                    self._routing_cache[cache_key] = ruta
                    logger.debug(f"Distancia OSRM: {ruta['distancia_km']:.2f} km")
                    return ruta['distancia_km']
                else:
                    logger.warning("OSRM falló, usando haversine")
                    
            except Exception as e:
                logger.warning(f"Error al usar OSRM: {str(e)}, usando haversine")
        
        # Fallback: Distancia haversine (línea recta)
        R = 6371.0  # Radio de la Tierra en km
        
        lat1_rad = np.radians(lat1)
        lon1_rad = np.radians(lon1)
        lat2_rad = np.radians(lat2)
        lon2_rad = np.radians(lon2)
        
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = np.sin(dlat / 2)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon / 2)**2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
        
        return R * c
    
    def _obtener_ruta_completa(self, lat1: float, lon1: float, lat2: float, lon2: float) -> Optional[Dict]:
        """
        Obtiene la ruta COMPLETA con geometría de OSRM.
        
        Returns:
            Dict con 'geometry', 'distancia_km', 'duracion_minutos'
        """
        if not self.usar_routing_real:
            return None
        
        try:
            # Buscar en caché primero
            cache_key = (round(lat1, 6), round(lon1, 6), round(lat2, 6), round(lon2, 6))
            
            if cache_key in self._routing_cache:
                return self._routing_cache[cache_key]
            
            # Usar servicio OSRM interno
            ruta = OSRMService.obtener_ruta(lat1, lon1, lat2, lon2)
            
            if ruta:
                # Guardar en caché
                self._routing_cache[cache_key] = ruta
                logger.info(f"🗺️ Ruta OSRM: {ruta['distancia_km']} km, {len(ruta['geometry'])} puntos")
                return ruta
            else:
                logger.warning("OSRM no pudo calcular ruta")
                return None
                
        except Exception as e:
            logger.warning(f"Error al obtener ruta completa: {str(e)}")
            return None
    
    def render(self, mode='human'):
        """Renderiza el estado actual del entorno"""
        if mode == 'human':
            print(f"\n{'='*60}")
            print(f"PASO {self.current_step}/{self.max_steps}")
            print(f"{'='*60}")
            print(f"Clientes servidos: {self.clientes_servidos}/{self.num_clientes}")
            print(f"Recompensa total: {self.total_reward:.2f}")
            print(f"\nEstado de camiones:")
            for camion in self.camiones:
                print(f"  Camión {camion.id}: Carga {camion.porcentaje_carga:.1f}%, "
                      f"Distancia {camion.distancia_recorrida_km:.2f}km")
    
    def get_info(self) -> Dict:
        """Obtiene información detallada del estado actual"""
        return {
            'step': self.current_step,
            'clientes_servidos': self.clientes_servidos,
            'total_clientes': self.num_clientes,
            'porcentaje_completado': (self.clientes_servidos / self.num_clientes) * 100,
            'total_reward': self.total_reward,
            'camiones': [
                {
                    'id': c.id,
                    'carga_kg': c.carga_actual_kg,
                    'capacidad_kg': c.capacidad_kg,
                    'porcentaje_carga': c.porcentaje_carga,
                    'distancia_km': c.distancia_recorrida_km,
                    'posicion': {'lat': c.latitud, 'lon': c.longitud},
                    'activo': c.activo
                }
                for c in self.camiones
            ],
            'clientes': [
                {
                    'id': cl.id,
                    'nombre': cl.nombre,
                    'demanda_kg': cl.demanda_kg,
                    'prioridad': cl.prioridad,
                    'servido': cl.servido,
                    'posicion': {'lat': cl.latitud, 'lon': cl.longitud}
                }
                for cl in self.clientes
            ]
        }
    
    def close(self):
        """Limpia recursos del entorno"""
        pass


# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

def cargar_predicciones_lstm(csv_path: str, fecha: str) -> List[Dict]:
    """
    Carga predicciones LSTM desde CSV para una fecha específica
    
    Args:
        csv_path: Ruta al CSV con predicciones
        fecha: Fecha en formato 'YYYY-MM-DD'
    
    Returns:
        Lista de diccionarios con clientes y sus demandas
    """
    import pandas as pd
    
    df = pd.read_csv(csv_path)
    df_fecha = df[df['fecha'] == fecha].copy()
    
    clientes = []
    for idx, row in df_fecha.iterrows():
        clientes.append({
            'id': idx,
            'nombre': row['punto_recoleccion'],
            'latitud': row['latitud_punto_recoleccion'],
            'longitud': row['longitud_punto_recoleccion'],
            'demanda_kg': row.get('residuos_kg', row.get('prediccion_kg', 100)),
            'prioridad': 2 if row.get('residuos_kg', 100) > 100 else 1
        })
    
    return clientes


if __name__ == '__main__':
    """
    Ejemplo de uso del entorno DVRPTW sin time windows
    """
    print("="*70)
    print("ENTORNO DVRPTW - Recolección de Residuos sin Time Windows")
    print("="*70)
    
    # Crear entorno
    env = DVRPTWEnv(
        num_camiones=3,
        capacidad_camion_kg=3500.0,
        max_steps=100,
        seed=42
    )
    
    # Episodio de prueba con política aleatoria
    obs = env.reset()
    done = False
    step = 0
    
    print("\nEjecutando episodio de prueba con política aleatoria...")
    
    while not done and step < 20:
        # Acción aleatoria
        action = env.action_space.sample()
        obs, reward, done, info = env.step(action)
        
        print(f"\nStep {step+1}: Acción={action}, Reward={reward:.2f}, Evento={info.get('evento')}")
        
        step += 1
    
    # Mostrar resumen final
    env.render()
    info_final = env.get_info()
    
    print(f"\n{'='*70}")
    print("RESUMEN FINAL")
    print(f"{'='*70}")
    print(f"Clientes servidos: {info_final['clientes_servidos']}/{info_final['total_clientes']}")
    print(f"Porcentaje completado: {info_final['porcentaje_completado']:.1f}%")
    print(f"Recompensa total: {info_final['total_reward']:.2f}")
    print(f"\nDistancia total recorrida por camión:")
    for camion in info_final['camiones']:
        print(f"  Camión {camion['id']}: {camion['distancia_km']:.2f} km")
    
    env.close()
