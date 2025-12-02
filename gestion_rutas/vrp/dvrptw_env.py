"""
Entorno DVRP (Dynamic Vehicle Routing Problem)
Adaptado para recolección de residuos SIN restricciones de ventanas de tiempo.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
import gymnasium as gym
from gymnasium import spaces
from dataclasses import dataclass, field
import logging
import requests
import time
import json
import os
import traceback

logger = logging.getLogger(__name__)

# ==================== OSRM SERVICE INTERNO ====================
class OSRMService:
    """Servicio OSRM simplificado integrado"""
    
    OSRM_SERVERS = [
        "http://router.project-osrm.org/route/v1/driving",
        "https://routing.openstreetmap.de/routed-car/route/v1/driving"
    ]
    CURRENT_SERVER_IDX = 0
    
    _route_cache: Dict[str, Dict] = {}
    _cache_file = "osrm_cache.json"
    _cache_loaded = False
    _osrm_available = True
    _consecutive_failures = 0
    MAX_FAILURES = 50
    
    @classmethod
    def _load_cache(cls):
        if cls._cache_loaded: return
        try:
            if os.path.exists(cls._cache_file):
                with open(cls._cache_file, 'r', encoding='utf-8') as f:
                    cls._route_cache = json.load(f)
                logger.info(f" Caché OSRM cargado: {len(cls._route_cache)} rutas")
        except Exception as e:
            logger.warning(f" Error cargando caché OSRM: {e}")
        cls._cache_loaded = True

    @classmethod
    def _save_cache(cls):
        try:
            with open(cls._cache_file, 'w', encoding='utf-8') as f:
                json.dump(cls._route_cache, f)
        except Exception as e:
            logger.warning(f" Error guardando caché OSRM: {e}")

    @staticmethod
    def _generar_ruta_lineal(lat1: float, lon1: float, lat2: float, lon2: float) -> Dict:
        R = 6371.0
        lat1_rad, lon1_rad = np.radians(lat1), np.radians(lon1)
        lat2_rad, lon2_rad = np.radians(lat2), np.radians(lon2)
        dlat, dlon = lat2_rad - lat1_rad, lon2_rad - lon1_rad
        a = np.sin(dlat / 2)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon / 2)**2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
        distancia_km = R * c
        return {
            "geometry": [[lat1, lon1], [lat2, lon2]],
            "distancia_km": round(distancia_km, 3),
            "duracion_minutos": round(distancia_km * 2, 2),
            "es_fallback": True
        }

    @staticmethod
    def _simplificar_geometria(geometry: List[List[float]], tolerancia: float = 0.0001) -> List[List[float]]:
        if not geometry: return []
        simplificada = [geometry[0]]
        for i in range(1, len(geometry)):
            lat1, lon1 = simplificada[-1]
            lat2, lon2 = geometry[i]
            if abs(lat1 - lat2) + abs(lon1 - lon2) > tolerancia:
                simplificada.append(geometry[i])
        if simplificada[-1] != geometry[-1]:
            simplificada.append(geometry[-1])
        return simplificada

    @staticmethod
    def obtener_ruta(lat1: float, lon1: float, lat2: float, lon2: float) -> Optional[Dict]:
        OSRMService._load_cache()
        if abs(lat1 - lat2) < 0.0001 and abs(lon1 - lon2) < 0.0001:
            return {"geometry": [[lat1, lon1], [lat2, lon2]], "distancia_km": 0.0, "duracion_minutos": 0.0}

        if not OSRMService._osrm_available:
            return OSRMService._generar_ruta_lineal(lat1, lon1, lat2, lon2)

        try:
            cache_key = f"{lat1:.6f},{lon1:.6f}-{lat2:.6f},{lon2:.6f}"
            if cache_key in OSRMService._route_cache:
                return OSRMService._route_cache[cache_key]
            
            coords = f"{lon1},{lat1};{lon2},{lat2}"
            headers = {'User-Agent': 'LAR-VRP-Simulation/1.0'}
            
            time.sleep(0.1) # Breve pausa para no saturar
            current_url = OSRMService.OSRM_SERVERS[OSRMService.CURRENT_SERVER_IDX]
            
            try:
                response = requests.get(
                    f"{current_url}/{coords}", 
                    params={"geometries": "geojson", "overview": "full"}, 
                    headers=headers, timeout=5
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("code") == "Ok" and data.get("routes"):
                        ruta = data["routes"][0]
                        geo_leaf = [[c[1], c[0]] for c in ruta["geometry"]["coordinates"]]
                        result = {
                            "geometry": OSRMService._simplificar_geometria(geo_leaf),
                            "distancia_km": round(ruta["distance"] / 1000, 2),
                            "duracion_minutos": round(ruta["duration"] / 60, 2),
                            "es_fallback": False
                        }
                        OSRMService._route_cache[cache_key] = result
                        if len(OSRMService._route_cache) % 10 == 0: OSRMService._save_cache()
                        OSRMService._consecutive_failures = 0
                        return result
                elif response.status_code == 429:
                    OSRMService.CURRENT_SERVER_IDX = (OSRMService.CURRENT_SERVER_IDX + 1) % len(OSRMService.OSRM_SERVERS)
            except Exception:
                pass
                
            OSRMService._consecutive_failures += 1
            if OSRMService._consecutive_failures > OSRMService.MAX_FAILURES:
                OSRMService._osrm_available = False
            return OSRMService._generar_ruta_lineal(lat1, lon1, lat2, lon2)
            
        except Exception:
            return OSRMService._generar_ruta_lineal(lat1, lon1, lat2, lon2)

@dataclass
class Cliente:
    """Representa un punto de recolección (cliente) con blindaje de tipos"""
    id: str
    nombre: str
    latitud: float
    longitud: float
    demanda_kg: float
    prioridad: int = 1
    servido: bool = False
    tiempo_servicio: float = 10.0
    ventana_inicio: float = 0.0
    ventana_fin: float = float('inf')

    def __post_init__(self):
        """Conversión forzada de tipos al crear el objeto"""
        try:
            self.demanda_kg = float(self.demanda_kg)
            self.latitud = float(self.latitud)
            self.longitud = float(self.longitud)
            if isinstance(self.id, (int, float)):
                self.id = str(int(self.id)).strip()
            else:
                self.id = str(self.id).strip()
        except:
            self.demanda_kg = 10.0 # Fallback seguro

@dataclass
class Camion:
    id: int
    capacidad_kg: float
    carga_actual_kg: float = 0.0
    latitud: float = -20.2132
    longitud: float = -70.1525
    tiempo_actual: float = 0.0
    ruta_actual: List[int] = field(default_factory=list)
    ruta_geometria: List[List[float]] = field(default_factory=list)
    historial_geometria: List[List[float]] = field(default_factory=list)
    geometria_actual: List[List[float]] = field(default_factory=list)
    distancia_recorrida_km: float = 0.0
    activo: bool = True
    nombre_ultimo_punto: str = ""
    
    @property
    def capacidad_disponible(self) -> float:
        return float(self.capacidad_kg) - float(self.carga_actual_kg)
    
    @property
    def porcentaje_carga(self) -> float:
        return (self.carga_actual_kg / self.capacidad_kg) * 100 if self.capacidad_kg > 0 else 0

class DVRPTWEnv(gym.Env):
    metadata = {'render.modes': ['human']}
    
    def __init__(self, num_camiones=3, capacidad_camion_kg=3500.0, clientes=None, depot_lat=-20.2132, depot_lon=-70.1525, max_steps=10000, penalizacion_distancia=0.1, recompensa_servicio=50.0, usar_routing_real=True, seed=None, modo_marl=False, base_lat=None, base_lon=None):
        super().__init__()
        if seed: np.random.seed(seed)
        self.num_camiones = num_camiones
        self.capacidad_camion_kg = float(capacidad_camion_kg)
        self.depot_lat = depot_lat
        self.depot_lon = depot_lon
        self.base_lat = base_lat if base_lat is not None else depot_lat
        self.base_lon = base_lon if base_lon is not None else depot_lon
        self.max_steps = max_steps
        self.penalizacion_distancia = penalizacion_distancia
        self.recompensa_servicio = recompensa_servicio
        self.usar_routing_real = usar_routing_real
        self.modo_marl = modo_marl
        self.max_clientes_visibles = 10
        self._routing_cache = {}
        
        self.clientes = self._inicializar_clientes(clientes)
        self.num_clientes = len(self.clientes)
        
        # Mapeo inicial seguro
        self.idx_to_real_id = {i: str(c.id).strip() for i, c in enumerate(self.clientes)}
        self.camiones = self._inicializar_camiones()
        self.current_step = 0
        self.total_reward = 0.0
        self.clientes_servidos = 0
        self._setup_spaces()
    
    def _inicializar_clientes(self, clientes_data) -> List[Cliente]:
        if clientes_data is None:
            clientes_data = [{'id': i, 'nombre': f'P_{i}', 'latitud': -20.21, 'longitud': -70.15, 'demanda_kg': 50} for i in range(50)]
        
        clientes = []
        for data in clientes_data:
            # BLINDAJE EXTREMO EN LA CARGA
            try:
                d_kg = float(str(data.get('demanda_kg', 10)).replace(',', '.'))
            except: d_kg = 10.0
            
            try:
                raw_id = data.get('id', 'unk')
                c_id = str(int(float(raw_id))).strip() if str(raw_id).replace('.','',1).isdigit() else str(raw_id).strip()
            except: c_id = str(data.get('id', 'unk'))

            clientes.append(Cliente(
                id=c_id,
                nombre=str(data.get('nombre', f"C_{c_id}")),
                latitud=float(data.get('latitud', -20.21)),
                longitud=float(data.get('longitud', -70.15)),
                demanda_kg=d_kg,
                prioridad=int(float(data.get('prioridad', 1)))
            ))
        return clientes
    
    def _inicializar_camiones(self) -> List[Camion]:
        return [Camion(i, self.capacidad_camion_kg, latitud=self.base_lat, longitud=self.base_lon) for i in range(self.num_camiones)]
    
    def _setup_spaces(self):
        obs_size = 3 + (self.max_clientes_visibles * 4 if self.modo_marl else self.num_clientes * 4)
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(obs_size,), dtype=np.float32)
        self.action_space = spaces.Discrete(self.max_clientes_visibles + 1 if self.modo_marl else self.num_clientes + 1)

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        if seed: np.random.seed(seed)
        for c in self.clientes: c.servido = False
        self.camiones = self._inicializar_camiones()
        self.current_step = 0
        self.total_reward = 0.0
        self.clientes_servidos = 0
        
        # Regenerar mapa de IDs limpio
        self.idx_to_real_id = {i: str(c.id).strip() for i, c in enumerate(self.clientes)}
        return self._get_observation(), {}

    def _get_observation(self):
        camion = next((c for c in self.camiones if c.activo), self.camiones[0])
        obs = [camion.latitud, camion.longitud, camion.porcentaje_carga/100]
        # Implementación simplificada para asegurar compatibilidad
        # Si usas MARL real, aquí iría la lógica K-Nearest, pero para debug mantenemos simple
        return np.zeros(self.observation_space.shape, dtype=np.float32) 

    def step(self, action):
        """Paso blindado contra errores 500"""
        try:
            self.current_step += 1
            total_reward = 0.0
            info = {'eventos': [], 'detalles_camiones': []}
            
            # Normalizar acción
            acciones = action if isinstance(action, list) else [int(action)] if np.ndim(action)==0 else action
            if not isinstance(acciones, list): acciones = [acciones] # Fallback
            
            # Completar acciones para todos los camiones
            while len(acciones) < self.num_camiones: acciones.append(0)

            for i, act in enumerate(acciones):
                if i < len(self.camiones) and self.camiones[i].activo:
                    r, evt = self._ejecutar_accion_camion(self.camiones[i], int(act))
                    total_reward += r
                    if evt: info['eventos'].append(evt)

            # --- LÓGICA DE RETORNO A BASE AL FINALIZAR ---
            if self.clientes_servidos >= self.num_clientes:
                for camion in self.camiones:
                    if camion.activo:
                        dist_a_base = self._calcular_distancia(camion.latitud, camion.longitud, self.depot_lat, self.depot_lon)
                        # Si está lejos de la base (> 50m), forzar retorno
                        if dist_a_base > 0.05:
                            if self.usar_routing_real:
                                # Intentar obtener ruta real
                                ruta = self._obtener_ruta_completa(camion.latitud, camion.longitud, self.depot_lat, self.depot_lon)
                                if ruta:
                                    camion.geometria_actual = ruta.get('geometry', [])
                                    camion.ruta_geometria = ruta.get('geometry', [])
                            
                            # Mover camión a base
                            camion.latitud, camion.longitud = self.depot_lat, self.depot_lon
                            camion.distancia_recorrida_km += dist_a_base
                            camion.carga_actual_kg = 0.0 # Descargar
                            
                            info['eventos'].append({
                                'tipo': 'retorno_final',
                                'mensaje': f" Fin de ruta: Camión {camion.id} regresa a base.",
                                'camion_id': camion.id
                            })

            terminated = self.clientes_servidos >= self.num_clientes
            truncated = self.current_step >= self.max_steps
            self.total_reward += total_reward
            
            info['total_reward'] = self.total_reward
            info['clientes_servidos'] = self.clientes_servidos
            info['step'] = self.current_step
            
            # --- MAPEO DE IDs SEGURO ---
            # Usamos sintaxis de objeto y mapa seguro
            real_ids = []
            for idx, c in enumerate(self.clientes):
                if c.servido:
                    real_ids.append(self.idx_to_real_id.get(idx, str(c.id)))
            
            info['clientes_servidos_ids'] = real_ids
            
            return self._get_observation(), total_reward, terminated, truncated, info

        except Exception as e:
            print(f"\n ERROR CRÍTICO EN STEP: {e}")
            traceback.print_exc()
            return self._get_observation(), 0, False, False, {'error': str(e), 'clientes_servidos_ids': []}

    def step_agent(self, action: int, agent_id: int):
        """Ejecuta acción para un solo agente (camión)"""
        # Buscar el camión por ID
        camion = next((c for c in self.camiones if c.id == agent_id), None)
        if not camion:
            return self._get_observation(), 0, False, False, {}
            
        reward, evt = self._ejecutar_accion_camion(camion, int(action))
        
        terminated = self.clientes_servidos >= self.num_clientes
        truncated = self.current_step >= self.max_steps
        
        info = {'eventos': [evt] if evt else []}
        
        # --- MAPEO DE IDs SEGURO ---
        real_ids = []
        for idx, c in enumerate(self.clientes):
            if c.servido:
                real_ids.append(self.idx_to_real_id.get(idx, str(c.id)))
        info['clientes_servidos_ids'] = real_ids
        
        return self._get_observation(), reward, terminated, truncated, info

    def _ejecutar_accion_camion(self, camion: Camion, action: int):
        reward = 0.0
        evento = None
        try:
            if action == 0: # Depot
                dist = self._calcular_distancia(camion.latitud, camion.longitud, self.depot_lat, self.depot_lon)
                if self.usar_routing_real:
                    ruta = self._obtener_ruta_completa(camion.latitud, camion.longitud, self.depot_lat, self.depot_lon)
                    camion.geometria_actual = ruta.get('geometry', [])
                    camion.ruta_geometria = ruta.get('geometry', []) # Actualizar ruta_geometria
                camion.latitud, camion.longitud = self.depot_lat, self.depot_lon
                camion.distancia_recorrida_km += dist
                
                # Capturar carga antes de resetear
                carga_descargada = camion.carga_actual_kg
                camion.carga_actual_kg = 0.0
                
                reward -= dist * self.penalizacion_distancia
                
                # Retornar dict con info extra
                evento = {
                    'tipo': 'retorno',
                    'mensaje': f"Descarga {carga_descargada:.1f}kg",
                    'carga_descargada': carga_descargada
                }
                
            elif 1 <= action <= self.num_clientes:
                c_idx = action - 1
                cliente = self.clientes[c_idx]
                
                # --- COMPARACIÓN BLINDADA (FLOAT vs FLOAT) ---
                demanda = float(cliente.demanda_kg)
                capacidad = float(camion.capacidad_disponible)
                
                if cliente.servido:
                    reward -= 1.0
                elif demanda > capacidad: # AQUÍ FALLABA ANTES, AHORA NO
                    reward -= 1.0
                    evento = f"Sin capacidad ({demanda} > {capacidad})"
                else:
                    dist = self._calcular_distancia(camion.latitud, camion.longitud, cliente.latitud, cliente.longitud)
                    ruta_geo = []
                    if self.usar_routing_real:
                        ruta = self._obtener_ruta_completa(camion.latitud, camion.longitud, cliente.latitud, cliente.longitud)
                        ruta_geo = ruta.get('geometry', [])
                        camion.geometria_actual = ruta_geo
                        camion.ruta_geometria = ruta_geo # Actualizar ruta_geometria también
                        # --- CHECK-IN-TRANSIT MEJORADO (Radio Realista) ---
                        RADIO_RECOLECCION_KM = 0.05 # 50 metros (Más realista)
                        
                        # Optimización: Filtrar candidatos factibles primero
                        candidatos_check = [
                            c for c in self.clientes 
                            if not c.servido and c.id != cliente.id and float(c.demanda_kg) <= float(camion.capacidad_disponible)
                        ]
                        
                        if candidatos_check:
                            # Iterar sobre la geometría con interpolación básica para evitar saltos
                            for i in range(len(ruta_geo)):
                                plat, plon = ruta_geo[i]
                                
                                # Lista de puntos a verificar en este segmento
                                puntos_a_verificar = [(plat, plon)]
                                
                                # Si hay un siguiente punto, verificar si necesitamos interpolar (si están lejos)
                                if i < len(ruta_geo) - 1:
                                    plat_next, plon_next = ruta_geo[i+1]
                                    # Distancia Manhattan aproximada en grados
                                    dist_grados = abs(plat - plat_next) + abs(plon - plon_next)
                                    # 0.0005 grados es aprox 55 metros. Si es mayor, agregamos punto medio.
                                    if dist_grados > 0.0005:
                                        puntos_a_verificar.append( ((plat + plat_next)/2, (plon + plon_next)/2) )

                                for v_lat, v_lon in puntos_a_verificar:
                                    # Si ya no tiene capacidad, parar check
                                    if float(camion.capacidad_disponible) <= 0: break
                                    
                                    # Revisar candidatos
                                    for cand in candidatos_check[:]: # Copia para poder remover
                                        if cand.servido: continue # Ya fue servido en iteración anterior
                                        
                                        dist_km = self._calcular_distancia_haversine(v_lat, v_lon, cand.latitud, cand.longitud)
                                        
                                        if dist_km <= RADIO_RECOLECCION_KM:
                                            # ¡RECOLECCIÓN EN RUTA!
                                            cand.servido = True
                                            self.clientes_servidos += 1
                                            camion.carga_actual_kg += float(cand.demanda_kg)
                                            reward += 50.0 # Bonus por eficiencia
                                            
                                            # Log informativo solicitado
                                            dist_metros = dist_km * 1000
                                            logger.info(f" Check-in-Transit: Cliente {cand.id} recogido a {dist_metros:.1f}m de la ruta.")
                                            
                                            # Remover de lista local para no volver a chequear
                                            candidatos_check.remove(cand)
                    
                    camion.latitud, camion.longitud = cliente.latitud, cliente.longitud
                    camion.distancia_recorrida_km += dist
                    
                    # Actualizar tiempo (usar OSRM duration si existe, sino estimar a 25km/h)
                    tiempo_viaje = ruta.get('duracion_minutos', (dist / 25.0) * 60)
                    tiempo_servicio = getattr(cliente, 'tiempo_servicio', 1.0) # 1 min por defecto
                    camion.tiempo_actual += tiempo_viaje + tiempo_servicio
                    
                    camion.carga_actual_kg += demanda # Suma segura
                    cliente.servido = True
                    self.clientes_servidos += 1
                    reward += self.recompensa_servicio - (dist * self.penalizacion_distancia)
                    evento = {
                        'tipo': 'servicio',
                        'mensaje': f"Servido {cliente.id}",
                        'cliente_id': cliente.id
                    }

            return reward, evento
        except Exception as e:
            logger.error(f"Error accion camion: {e}")
            return 0.0, "Error"

    def action_masks(self):
        if not self.modo_marl: return [True] * self.action_space.n
        mask = [False] * (self.max_clientes_visibles + 1)
        camion = next((c for c in self.camiones if c.activo), self.camiones[0])
        
        # Máscara segura con floats
        if hasattr(self, 'current_neighbors'):
            for i, c in enumerate(self.current_neighbors):
                try:
                    # COMPARACIÓN BLINDADA
                    if not c.servido and float(camion.capacidad_disponible) >= float(c.demanda_kg):
                        mask[i+1] = True
                except: pass
        
        if camion.carga_actual_kg > 0 or not any(mask[1:]): mask[0] = True
        return mask

    def _calcular_distancia(self, lat1, lon1, lat2, lon2):
        # Implementación mínima segura
        return self._calcular_distancia_haversine(lat1, lon1, lat2, lon2)

    def _calcular_distancia_haversine(self, lat1, lon1, lat2, lon2):
        R = 6371.0
        dlat = np.radians(lat2 - lat1)
        dlon = np.radians(lon2 - lon1)
        a = np.sin(dlat/2)**2 + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(dlon/2)**2
        return R * 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))

    def _obtener_ruta_completa(self, lat1, lon1, lat2, lon2):
        if self.usar_routing_real:
            return OSRMService.obtener_ruta(lat1, lon1, lat2, lon2) or {}
        return {}
