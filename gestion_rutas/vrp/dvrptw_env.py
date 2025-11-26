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
import time

logger = logging.getLogger(__name__)

# ==================== OSRM SERVICE INTERNO ====================
class OSRMService:
    """Servicio OSRM simplificado integrado para evitar problemas de imports"""
    
    OSRM_URL = "https://routing.openstreetmap.de/routed-car/route/v1/driving"
    _route_cache: Dict[str, Dict] = {}
    _osrm_available = True
    _consecutive_failures = 0
    MAX_FAILURES = 50  # Aumentado para insistir en rutas reales
    
    @staticmethod
    def _generar_ruta_lineal(lat1: float, lon1: float, lat2: float, lon2: float) -> Dict:
        """Genera una ruta lineal de respaldo (Haversine)"""
        # Calcular distancia Haversine
        R = 6371.0
        lat1_rad, lon1_rad = np.radians(lat1), np.radians(lon1)
        lat2_rad, lon2_rad = np.radians(lat2), np.radians(lon2)
        dlat, dlon = lat2_rad - lat1_rad, lon2_rad - lon1_rad
        a = np.sin(dlat / 2)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon / 2)**2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
        distancia_km = R * c
        
        return {
            "geometry": [[lat1, lon1], [lat2, lon2]], # Línea recta
            "distancia_km": round(distancia_km, 3),
            "duracion_minutos": round(distancia_km * 2, 2) # Estimación: 30km/h = 0.5km/min -> 2 min/km
        }

    @staticmethod
    def obtener_ruta(lat1: float, lon1: float, lat2: float, lon2: float) -> Optional[Dict]:
        """
        Obtener ruta real por calles entre dos puntos usando OSRM.
        """
        # Optimización: Si los puntos son casi idénticos, retornar distancia 0 sin llamar a API
        if abs(lat1 - lat2) < 0.0001 and abs(lon1 - lon2) < 0.0001:
            return {
                "geometry": [[lat1, lon1], [lat2, lon2]],
                "distancia_km": 0.0,
                "duracion_minutos": 0.0
            }

        # Si OSRM falló demasiadas veces, usar fallback lineal
        if not OSRMService._osrm_available:
            return OSRMService._generar_ruta_lineal(lat1, lon1, lat2, lon2)

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
            
            # Añadir User-Agent para evitar bloqueos
            headers = {
                'User-Agent': 'LAR-VRP-Simulation/1.0 (Educational Project)'
            }
            
            logger.debug(f"🌐 Consultando OSRM: {coords}")
            
            # ⚠️ DELAY PARA EVITAR RATE LIMITING (REDUCIDO)
            time.sleep(0.1) 
            
            # Timeout aumentado para asegurar respuesta de OSRM
            response = requests.get(
                f"{OSRMService.OSRM_URL}/{coords}", 
                params=params, 
                headers=headers,
                timeout=5  # Aumentado a 5s
            )
            
            if response.status_code == 200:
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
                    
                    # Guardar en caché y resetear contador de fallos
                    OSRMService._route_cache[cache_key] = result
                    OSRMService._consecutive_failures = 0
                    return result
            
            # Si falla la respuesta pero no es excepción, retornar lineal
            return OSRMService._generar_ruta_lineal(lat1, lon1, lat2, lon2)
            
        except Exception as e:
            OSRMService._consecutive_failures += 1
            logger.warning(f"⚠️ Error OSRM ({OSRMService._consecutive_failures}/{OSRMService.MAX_FAILURES}): {str(e)[:100]}...")
            
            if OSRMService._consecutive_failures >= OSRMService.MAX_FAILURES:
                logger.error("❌ OSRM desactivado por múltiples fallos. Usando distancia Haversine.")
                OSRMService._osrm_available = False
            
            # Retornar ruta lineal en caso de error
            return OSRMService._generar_ruta_lineal(lat1, lon1, lat2, lon2)


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
    ruta_geometria: List[List[float]] = field(default_factory=list)  # Geometría real ACUMULADA de la ruta
    geometria_actual: List[List[float]] = field(default_factory=list)  # Geometría del ÚLTIMO tramo (para animación)
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
        usar_routing_real: bool = True,
        seed: int = None,
        modo_marl: bool = False
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
            modo_marl: Si True, usa espacios de observación/acción fijos para entrenamiento RL
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
        self.usar_routing_real = usar_routing_real
        self.modo_marl = modo_marl
        
        # Configuración MARL
        self.max_clientes_visibles = 10  # K vecinos más cercanos
        
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
        """
        if self.modo_marl:
            # MODO MARL: Espacios fijos y normalizados
            # Observación: 
            # - Camión (3): [lat_norm, lon_norm, carga_norm]
            # - K Clientes (K*4): [dist_norm, demanda_norm, prioridad_norm, servido]
            obs_size = 3 + (self.max_clientes_visibles * 4)
            
            self.observation_space = spaces.Box(
                low=0.0,
                high=1.0,
                shape=(obs_size,),
                dtype=np.float32
            )
            
            # Acción: Elegir entre los K clientes más cercanos o Depot
            # 0 = Depot
            # 1..K = Cliente k-ésimo más cercano
            self.action_space = spaces.Discrete(self.max_clientes_visibles + 1)
            
        else:
            # MODO LEGACY (Compatible con mas_cooperativo.py)
            # Observación variable (aunque definida como Box grande)
            obs_size = 3 + (self.num_clientes * 4)
            
            self.observation_space = spaces.Box(
                low=-np.inf,
                high=np.inf,
                shape=(obs_size,),
                dtype=np.float32
            )
            
            # Acción: ID absoluto del cliente
            self.action_space = spaces.Discrete(self.num_clientes + 1)
    
    def reset(self, seed=None, options=None):
        """Reinicia el entorno para un nuevo episodio"""
        super().reset(seed=seed)
        
        if seed is not None:
            np.random.seed(seed)
            
        # Reiniciar clientes
        for cliente in self.clientes:
            cliente.servido = False
        
        # Reiniciar camiones
        self.camiones = self._inicializar_camiones()
        
        # Reiniciar estado
        self.current_step = 0
        self.total_reward = 0.0
        self.clientes_servidos = 0
        
        return self._get_observation(), {}
    
    def _get_observation(self) -> np.ndarray:
        """
        Obtiene observación del estado actual.
        Soporta modo MARL (K vecinos) y modo Legacy (todos los clientes).
        """
        # Buscar primer camión activo (para compatibilidad single-agent)
        camion = next((c for c in self.camiones if c.activo), self.camiones[0])
        
        if self.modo_marl:
            # --- MODO MARL: K VECINOS MÁS CERCANOS ---
            
            # 1. Estado del camión (Normalizado aprox)
            # Normalizamos lat/lon relativo al depot para que sea agnóstico a la ubicación global
            # Usamos tanh para asegurar rango [-1, 1] o similar, pero el espacio dice [0, 1]
            # Ajuste: Usar coordenadas relativas normalizadas + 0.5 para centrar en 0.5
            lat_rel = (camion.latitud - self.depot_lat) * 10.0 # Escalar
            lon_rel = (camion.longitud - self.depot_lon) * 10.0
            
            # Clampear entre 0 y 1 (0.5 es el centro/depot)
            lat_norm = np.clip(lat_rel + 0.5, 0.0, 1.0)
            lon_norm = np.clip(lon_rel + 0.5, 0.0, 1.0)
            
            obs = [lat_norm, lon_norm, camion.porcentaje_carga / 100.0]
            
            # 2. Calcular distancias a TODOS los clientes no servidos
            clientes_info = []
            for cliente in self.clientes:
                if not cliente.servido:
                    dist = self._calcular_distancia_haversine(
                        camion.latitud, camion.longitud,
                        cliente.latitud, cliente.longitud
                    )
                    clientes_info.append({
                        'dist': dist,
                        'cliente': cliente
                    })
            
            # 3. Ordenar por distancia y tomar los K mejores
            clientes_info.sort(key=lambda x: x['dist'])
            vecinos = clientes_info[:self.max_clientes_visibles]
            
            # 4. Rellenar observación
            for info in vecinos:
                c = info['cliente']
                obs.extend([
                    info['dist'] / 10.0,  # Distancia norm
                    c.demanda_kg / self.capacidad_camion_kg, # Demanda norm
                    c.prioridad / 3.0, # Prioridad norm
                    0.0 # No servido (siempre 0 porque filtramos los servidos)
                ])
            
            # 5. Padding (Rellenar con ceros si hay menos de K clientes)
            faltantes = self.max_clientes_visibles - len(vecinos)
            for _ in range(faltantes):
                obs.extend([0.0, 0.0, 0.0, 1.0]) # 1.0 en 'servido' indica slot vacío/dummy
                
            return np.array(obs, dtype=np.float32)
            
        else:
            # --- MODO LEGACY: TODOS LOS CLIENTES ---
            obs = [
                camion.latitud,
                camion.longitud,
                camion.porcentaje_carga / 100.0
            ]
            
            for cliente in self.clientes:
                distancia = self._calcular_distancia_haversine(
                    camion.latitud, camion.longitud,
                    cliente.latitud, cliente.longitud
                )
                obs.extend([
                    distancia / 10.0,
                    cliente.demanda_kg / self.capacidad_camion_kg,
                    cliente.prioridad / 3.0,
                    1.0 if cliente.servido else 0.0
                ])
            
            return np.array(obs, dtype=np.float32)
    
    def step(self, action) -> Tuple[np.ndarray, float, bool, dict]:
        """
        Ejecuta un paso de simulación.
        Soporta lista de acciones (Multi-Agent) o entero (Single-Agent).
        """
        self.current_step += 1
        total_reward = 0.0
        info = {'eventos': [], 'detalles_camiones': []}
        
        # Normalizar acción a lista
        acciones_lista = []
        
        # Si es un array de numpy de dimensión 0 (escalar), convertir a int
        if isinstance(action, np.ndarray) and action.ndim == 0:
            action = int(action)
            
        if isinstance(action, list):
            acciones_lista = action
        elif isinstance(action, np.ndarray) and action.ndim > 0:
            acciones_lista = action.tolist()
        else:
            # Single agent: aplicar al primer camión activo
            acciones_lista = [0] * self.num_camiones
            camion_activo = next((c for c in self.camiones if c.activo), None)
            if camion_activo:
                acciones_lista[camion_activo.id] = int(action)
        
        logger.info(f"👣 STEP {self.current_step} | Acciones: {acciones_lista}")
        
        # Ejecutar acciones para cada camión
        for i, accion in enumerate(acciones_lista):
            if i >= len(self.camiones):
                break
                
            camion = self.camiones[i]
            if not camion.activo:
                continue
                
            # Ejecutar lógica para este camión
            r, evt = self._ejecutar_accion_camion(camion, int(accion))
            total_reward += r
            if evt:
                info['eventos'].append(evt)
                
        # Verificar terminación
        terminated = (
            self.clientes_servidos >= self.num_clientes
        )
        truncated = (
            self.current_step >= self.max_steps
        )
        
        self.total_reward += total_reward
        info['total_reward'] = self.total_reward
        info['clientes_servidos'] = self.clientes_servidos
        info['step'] = self.current_step
        
        logger.info(f"🏁 STEP {self.current_step} completado. Eventos: {len(info['eventos'])}")
        
        return self._get_observation(), total_reward, terminated, truncated, info

    def _ejecutar_accion_camion(self, camion: Camion, action: int) -> Tuple[float, Optional[str]]:
        """Ejecuta una acción para un camión específico y retorna (reward, evento)"""
        reward = 0.0
        evento = None
        
        logger.debug(f"🔧 Procesando acción {action} para Camión {camion.id}") # LOG INICIO
        
        try:
            # Acción 0: Volver al depósito
            if action == 0:
                logger.debug(f"🏠 Camión {camion.id} retornando a depot") # LOG DEPOT
                distancia = self._calcular_distancia(
                    camion.latitud, camion.longitud,
                    self.depot_lat, self.depot_lon
                )
                logger.debug(f"📏 Distancia calculada: {distancia}") # LOG DISTANCIA
                
                # Obtener geometría de ruta si está disponible
                if self.usar_routing_real:
                    logger.debug(f"🗺️ Camión {camion.id}: Calculando ruta al depot")
                    ruta_info = self._obtener_ruta_completa(
                        camion.latitud, camion.longitud,
                        self.depot_lat, self.depot_lon
                    )
                    if ruta_info and 'geometry' in ruta_info:
                        camion.geometria_actual = ruta_info['geometry']
                        if not hasattr(camion, 'ruta_geometria') or not camion.ruta_geometria:
                            camion.ruta_geometria = []
                        camion.ruta_geometria.extend(ruta_info['geometry'])
                    else:
                        camion.geometria_actual = []
                
                camion.latitud = self.depot_lat
                camion.longitud = self.depot_lon
                camion.distancia_recorrida_km += distancia
                camion.carga_actual_kg = 0.0
                camion.ruta_geometria = [] # Reset al llegar al depot
                
                reward -= distancia * self.penalizacion_distancia
                evento = f"Camión {camion.id} retornó al depot"
            
            # Acción 1-N: Visitar cliente
            elif 1 <= action <= self.num_clientes:
                cliente_id = action - 1
                cliente = self.clientes[cliente_id]
                
                if cliente.servido:
                    reward -= 5.0
                    evento = f"Camión {camion.id} visitó cliente ya servido {cliente.id}"
                elif cliente.demanda_kg > camion.capacidad_disponible:
                    reward -= 3.0
                    evento = f"Camión {camion.id} sin capacidad para {cliente.id}"
                else:
                    distancia = self._calcular_distancia(
                        camion.latitud, camion.longitud,
                        cliente.latitud, cliente.longitud
                    )
                    
                    if self.usar_routing_real:
                        logger.debug(f"🗺️ Camión {camion.id}: Calculando ruta a cliente {cliente.id}")
                        ruta_info = self._obtener_ruta_completa(
                            camion.latitud, camion.longitud,
                            cliente.latitud, cliente.longitud
                        )
                        if ruta_info and 'geometry' in ruta_info:
                            camion.geometria_actual = ruta_info['geometry']
                            # NO acumular historial para evitar sobrecarga visual y de datos
                            # El frontend se encarga de dibujar el rastro si es necesario
                            camion.ruta_geometria = ruta_info['geometry']
                        else:
                            camion.geometria_actual = []
                            camion.ruta_geometria = []
                    
                    camion.latitud = cliente.latitud
                    camion.longitud = cliente.longitud
                    camion.distancia_recorrida_km += distancia
                    camion.carga_actual_kg += cliente.demanda_kg
                    cliente.servido = True
                    self.clientes_servidos += 1
                    
                    recompensa_base = self.recompensa_servicio * cliente.prioridad
                    penalizacion_dist = distancia * self.penalizacion_distancia
                    reward = recompensa_base - penalizacion_dist
                    
                    evento = f"Camión {camion.id} sirvió a cliente {cliente.id}"
                    logger.info(f"🚛 Camión {camion.id} → Cliente '{cliente.nombre}' ({distancia:.2f} km)")
            
            return reward, evento
            
        except Exception as e:
            logger.error(f"❌ Error ejecutando acción camión {camion.id}: {e}")
            return 0.0, f"Error camión {camion.id}"

    def step_agent(self, action: int, camion_id: int) -> Tuple[np.ndarray, float, bool, dict]:
        """
        Ejecuta una acción para un camión específico.
        Método corregido para soportar Multi-Agent System correctamente.
        """
        info = {'eventos': []}
        total_reward = 0.0
        
        if 0 <= camion_id < len(self.camiones):
            camion = self.camiones[camion_id]
            if camion.activo:
                # Log para verificar que se está moviendo el camión correcto
                logger.debug(f"🤖 Agente {camion_id} ejecutando acción {action}")
                
                reward, evt = self._ejecutar_accion_camion(camion, int(action))
                total_reward += reward
                if evt:
                    info['eventos'].append(evt)
        else:
            logger.error(f"❌ ID de camión inválido en step_agent: {camion_id}")
        
        # Verificar terminación global
        done = (
            self.clientes_servidos >= self.num_clientes
        )
        
        return self._get_observation(), total_reward, done, info
    
    def get_agent_observation(self, camion_id: int) -> np.ndarray:
        """
        Obtiene la observación específica para un agente (camión).
        Usado por el sistema MAS para inferencia PPO individual.
        """
        # Buscar el camión específico
        camion = next((c for c in self.camiones if c.id == camion_id), None)
        if not camion:
            # Fallback si no se encuentra (no debería pasar)
            return np.zeros(self.observation_space.shape, dtype=np.float32)
            
        # --- MODO MARL: K VECINOS MÁS CERCANOS ---
        
        # 1. Estado del camión (Normalizado aprox)
        lat_rel = (camion.latitud - self.depot_lat) * 10.0
        lon_rel = (camion.longitud - self.depot_lon) * 10.0
        
        lat_norm = np.clip(lat_rel + 0.5, 0.0, 1.0)
        lon_norm = np.clip(lon_rel + 0.5, 0.0, 1.0)
        
        obs = [lat_norm, lon_norm, camion.porcentaje_carga / 100.0]
        
        # 2. Calcular distancias a TODOS los clientes no servidos
        clientes_info = []
        for cliente in self.clientes:
            if not cliente.servido:
                dist = self._calcular_distancia_haversine(
                    camion.latitud, camion.longitud,
                    cliente.latitud, cliente.longitud
                )
                clientes_info.append({
                    'dist': dist,
                    'cliente': cliente
                })
        
        # 3. Ordenar por distancia y tomar los K mejores
        clientes_info.sort(key=lambda x: x['dist'])
        vecinos = clientes_info[:self.max_clientes_visibles]
        
        # 4. Rellenar observación
        for info in vecinos:
            c = info['cliente']
            obs.extend([
                info['dist'] / 10.0,  # Distancia norm
                c.demanda_kg / self.capacidad_camion_kg, # Demanda norm
                c.prioridad / 3.0, # Prioridad norm
                0.0 # No servido
            ])
        
        # 5. Padding
        faltantes = self.max_clientes_visibles - len(vecinos)
        for _ in range(faltantes):
            obs.extend([0.0, 0.0, 0.0, 1.0]) # 1.0 en 'servido' indica slot vacío
            
        return np.array(obs, dtype=np.float32)

    def _calcular_distancia_haversine(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calcula distancia Haversine (línea recta) entre dos puntos."""
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
                    # Solo loguear warning si OSRM debería estar disponible
                    if OSRMService._osrm_available:
                        logger.warning("OSRM falló, usando haversine")
                    
            except Exception as e:
                if OSRMService._osrm_available:
                    logger.warning(f"Error al usar OSRM: {str(e)}, usando haversine")
        
        # Fallback: Distancia haversine (línea recta)
        return self._calcular_distancia_haversine(lat1, lon1, lat2, lon2)
    
    def _obtener_ruta_completa(self, lat1: float, lon1: float, lat2: float, lon2: float) -> Optional[Dict]:
        """
        Obtiene la ruta COMPLETA con geometría de OSRM.
        
        Returns:
            Dict con 'geometry', 'distancia_km', 'duracion_minutos'
        """
        # Si no se usa routing real, retornar lineal directamente
        if not self.usar_routing_real:
            return OSRMService._generar_ruta_lineal(lat1, lon1, lat2, lon2)
        
        try:
            # Buscar en caché primero
            cache_key = (round(lat1, 6), round(lon1, 6), round(lat2, 6), round(lon2, 6))
            
            if cache_key in self._routing_cache:
                return self._routing_cache[cache_key]
            
            # Usar servicio OSRM interno (que ya maneja fallbacks)
            ruta = OSRMService.obtener_ruta(lat1, lon1, lat2, lon2)
            
            if ruta:
                # Guardar en caché
                self._routing_cache[cache_key] = ruta
                logger.info(f"🗺️ Ruta: {ruta['distancia_km']} km, {len(ruta['geometry'])} puntos")
                return ruta
            else:
                # Fallback final (no debería llegar aquí con la nueva lógica)
                return OSRMService._generar_ruta_lineal(lat1, lon1, lat2, lon2)
                
        except Exception as e:
            logger.warning(f"Error al obtener ruta completa: {str(e)}")
            return OSRMService._generar_ruta_lineal(lat1, lon1, lat2, lon2)
    
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
