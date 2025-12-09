from fastapi import APIRouter, HTTPException, Body
from typing import List, Dict, Any
import logging
import random
import math
import time
import asyncio
import requests
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

# Importar servicios reales
from ..service.camion_service import CamionService
from ..service.punto_service import PuntoService
from ..service.ruta_planificada_service import RutaPlanificadaService
from ..service.lstm_service import LSTMPredictionService
from ..service.prediccion_mapa_service import PrediccionMapaService

# Configuración de logger
logger = logging.getLogger(__name__)

# Executor para llamadas bloqueantes (OSRM)
executor = ThreadPoolExecutor(max_workers=3)

router = APIRouter(
    prefix="/bridge",
    tags=["JADE-Bridge"],
    responses={404: {"description": "Not found"}},
)

# --- CONSTANTES ---
VERTEDERO_COORDS = [-20.19767564535899, -70.06207963576485]

# --- ESTADO DE SIMULACIÓN (Overlay sobre la BD) ---
# Mantiene los datos dinámicos que no están en la BD estática (Ubicación en tiempo real, Carga actual)
simulation_state = {
    "camiones": {},
    "puntos_pendientes": [], # Puntos cargados para la simulación actual
    "puntos_servidos": [],   # IDs de puntos ya recolectados
    "last_update": datetime.now()
}

def _osrm_request_sync(url):
    """Función sincrónica para ejecutar en thread pool"""
    return requests.get(url, timeout=10)

async def get_osrm_route_batch(points):
    """
    Obtiene la ruta completa pasando por múltiples puntos.
    points: Lista de tuplas/listas [lat, lon]
    """
    if not points or len(points) < 2:
        return points

    # Construir string de coordenadas: lon,lat;lon,lat...
    coords_str = ";".join([f"{p[1]},{p[0]}" for p in points])
    
    loop = asyncio.get_event_loop()
    
    for attempt in range(3):
        try:
            url = f"http://router.project-osrm.org/route/v1/driving/{coords_str}?overview=full&geometries=geojson"
            
            # Ejecutar request bloqueante en un hilo separado para no congelar FastAPI
            response = await loop.run_in_executor(executor, _osrm_request_sync, url)
            
            if response.status_code == 200:
                data = response.json()
                if data["routes"]:
                    coords = data["routes"][0]["geometry"]["coordinates"]
                    return [[c[1], c[0]] for c in coords]
        except Exception as e:
            logger.warning(f"Error OSRM Batch (Intento {attempt+1}): {e}")
            await asyncio.sleep(1) # Sleep no bloqueante
            
    logger.warning("OSRM Batch falló. Intentando ruta punto a punto (fallback lento)...")
    
    # Fallback: Intentar construir la ruta segmento por segmento
    # Esto es más lento pero respeta las calles, evitando "líneas rectas"
    full_fallback_path = []
    for i in range(len(points) - 1):
        p1 = points[i]
        p2 = points[i+1]
        try:
            # Reutilizar la lógica de request individual
            url = f"http://router.project-osrm.org/route/v1/driving/{p1[1]},{p1[0]};{p2[1]},{p2[0]}?overview=full&geometries=geojson"
            response = await loop.run_in_executor(executor, _osrm_request_sync, url)
            if response.status_code == 200:
                data = response.json()
                if data["routes"]:
                    coords = data["routes"][0]["geometry"]["coordinates"]
                    segment = [[c[1], c[0]] for c in coords]
                    full_fallback_path.extend(segment)
                else:
                    full_fallback_path.append(p2) # Fallback del fallback
            else:
                full_fallback_path.append(p2)
        except:
            full_fallback_path.append(p2)
            
    if full_fallback_path:
        return full_fallback_path

    logger.error("OSRM Total Failure. Usando líneas rectas.")
    return points # Último recurso

async def get_osrm_route(start_lat, start_lon, end_lat, end_lon):
    """Wrapper simple para compatibilidad"""
    return await get_osrm_route_batch([[start_lat, start_lon], [end_lat, end_lon]])

def get_or_init_camion_state(camion_id_str: str, db_camion: Dict):
    """Inicializa el estado simulado de un camión si no existe"""
    if camion_id_str not in simulation_state["camiones"]:
        # Asignar un cluster ID basado en el orden de llegada (o hash del ID)
        # Suponemos IDs como "camion_1", "camion_2" -> cluster 0, 1...
        try:
            c_idx = int(camion_id_str.split("_")[1]) - 1
        except:
            c_idx = 0
            
        # Asegurar que el índice esté dentro del rango de clusters (ej: 3 camiones)
        num_clusters = simulation_state.get("active_trucks_limit", 3)
        cluster_assigned = c_idx % num_clusters

        simulation_state["camiones"][camion_id_str] = {
            "lat": -20.29305111963256, # Base de Operaciones (Inicio)
            "lon": -70.12295105323292,
            "carga": 0,
            "ruta_actual": [], 
            "cola_movimiento": [], 
            "cola_destinos": [],
            "cluster_id": cluster_assigned, # NUEVO: Sector asignado
            "last_move_time": datetime.now(), # Para detectar bloqueos
            "last_pos": (-20.29305111963256, -70.12295105323292)
        }
    return simulation_state["camiones"][camion_id_str]

async def update_simulation():
    """Actualiza la posición de los camiones basado en el tiempo transcurrido"""
    try:
        now = datetime.now()
        delta_seconds = (now - simulation_state["last_update"]).total_seconds()
        simulation_state["last_update"] = now
        
        # Velocidad simulada: 0.0005 grados por segundo (~50m/s muy rápido para visualización)
        SPEED = 0.0002 * max(1, delta_seconds * 10) 

        # 1. MOVER EL CAMIÓN
        for c_id, truck in simulation_state["camiones"].items():
            try:
                # DETECCIÓN DE BLOQUEO (STUCK DETECTION)
                # Si tiene ruta pero no se ha movido significativamente en 15 segundos, resetear movimiento
                if truck["ruta_actual"] and truck.get("last_pos"):
                    d_moved = math.sqrt((truck["lat"] - truck["last_pos"][0])**2 + (truck["lon"] - truck["last_pos"][1])**2)
                    if d_moved > 0.0001: # Se movió ~10 metros
                        truck["last_move_time"] = now
                        truck["last_pos"] = (truck["lat"], truck["lon"])
                    else:
                        time_stuck = (now - truck.get("last_move_time", now)).total_seconds()
                        if time_stuck > 15:
                            logger.warning(f"⚠️ {c_id} parece atascado por {time_stuck}s. Forzando salto al siguiente punto.")
                            truck["cola_movimiento"] = [] # Limpiar cola física
                            truck["last_move_time"] = now # Reset timer
                            # El bloque 'elif truck["cola_destinos"]' abajo se encargará de regenerar el movimiento

                # 1. MOVER EL CAMIÓN
                if truck["cola_movimiento"]:
                    target = truck["cola_movimiento"][0]
                    
                    # Calcular distancia
                    d_lat = target[0] - truck["lat"]
                    d_lon = target[1] - truck["lon"]
                    dist = math.sqrt(d_lat**2 + d_lon**2)
                    
                    if dist < SPEED:
                        # Llegamos al nodo intermedio
                        truck["lat"] = target[0]
                        truck["lon"] = target[1]
                        truck["cola_movimiento"].pop(0)
                    else:
                        # Mover hacia el objetivo
                        ratio = SPEED / dist
                        truck["lat"] += d_lat * ratio
                        truck["lon"] += d_lon * ratio
                
                # FIX: Si no hay movimiento pero hay destinos, estamos estancados. Forzar movimiento.
                elif truck["cola_destinos"]:
                    next_dest_id = truck["cola_destinos"][0]
                    target_lat, target_lon = None, None
                    
                    if next_dest_id == "DESCARGA_VERTEDERO":
                        target_lat, target_lon = VERTEDERO_COORDS
                    else:
                        # Usar str() para asegurar comparación
                        dest_point = next((p for p in truck["ruta_actual"] if str(p["id"]) == str(next_dest_id)), None)
                        if dest_point:
                            target_lat, target_lon = dest_point["lat"], dest_point["lon"]
                        else:
                            # El punto no existe en la ruta actual (error de estado), lo saltamos
                            truck["cola_destinos"].pop(0)
                    
                    if target_lat is not None:
                        # FIX CRÍTICO: NO llamar a OSRM (await) dentro del loop de actualización física.
                        # Si estamos atascados, usar línea recta para salir del paso y no congelar la simulación.
                        truck["cola_movimiento"] = [[target_lat, target_lon]]
            except Exception as e:
                logger.error(f"Error moviendo camión {c_id}: {e}")
                continue # Importante: Si un camión falla, los otros siguen

        # 2. VERIFICAR RECOLECCIÓN (OPORTUNISTA GLOBAL)
        # Permitimos que CUALQUIER camión recoja CUALQUIER basura si pasa cerca.
        
        puntos_globales = simulation_state.get("puntos_pendientes", [])
        servidos_set = set(simulation_state.get("puntos_servidos", []))
        
        for c_id, truck in simulation_state["camiones"].items():
            try:
                # Verificar descarga en vertedero
                if truck["cola_destinos"] and truck["cola_destinos"][0] == "DESCARGA_VERTEDERO":
                    d_vert = math.sqrt((VERTEDERO_COORDS[0] - truck["lat"])**2 + (VERTEDERO_COORDS[1] - truck["lon"])**2)
                    if d_vert < 0.003: 
                        logger.info(f"♻️ {c_id} descargando en Vertedero. Carga reseteada.")
                        truck["carga"] = 0
                        truck["cola_destinos"].pop(0)
                        truck["ruta_actual"] = []
                    continue

                # Recolección Oportunista
                # Iteramos sobre TODOS los puntos pendientes, no solo los de mi ruta
                for p in puntos_globales:
                    p_id = p["id"]
                    
                    # Si ya está servido, ignorar
                    if p_id in servidos_set:
                        continue

                    d_dest = math.sqrt((p["lat"] - truck["lat"])**2 + (p["lon"] - truck["lon"])**2)
                    
                    # Radio de recolección: ~50 metros (0.0005 grados)
                    if d_dest < 0.0005: 
                        # MARCAR COMO SERVIDO
                        simulation_state["puntos_servidos"].append(p_id)
                        servidos_set.add(p_id) # Actualizar set local para evitar doble conteo en este loop
                        
                        truck["carga"] += p["demanda"]
                        logger.info(f"✅ Punto {p_id} recolectado por {c_id} (Oportunista). Carga: {truck['carga']:.2f}")
                        
                        # Limpieza de estados:
                        # 1. Si estaba en MI cola de destinos, sacarlo
                        if p_id in truck["cola_destinos"]:
                            truck["cola_destinos"].remove(p_id)
                        
                        # 2. Si estaba en MI ruta visual, sacarlo
                        truck["ruta_actual"] = [rp for rp in truck["ruta_actual"] if str(rp["id"]) != str(p_id)]
            except Exception as e:
                logger.error(f"Error recolección camión {c_id}: {e}")
                continue
                    
    except Exception as e:
        logger.error(f"Error en update_simulation: {e}")

@router.post("/init")
async def init_simulation(
    fecha: str = Body(..., embed=True),
    num_camiones: int = Body(3, embed=True),
    capacidad_kg: int = Body(1000, embed=True) # Nuevo parámetro de capacidad
):
    """
    Inicializa la simulación cargando puntos desde el servicio LSTM/Mapa.
    """
    try:
        fecha_dt = datetime.strptime(fecha, '%Y-%m-%d')
    except ValueError:
        fecha_dt = datetime.now()

    # 1. Cargar predicciones usando el servicio existente
    servicio = PrediccionMapaService()
    predicciones = servicio.generar_predicciones_completas(fecha_dt)
    
    if not predicciones:
        return {"status": "warning", "message": "No se encontraron predicciones", "puntos": 0}

    # 2. Resetear estado de simulación
    simulation_state["camiones"] = {}
    simulation_state["puntos_pendientes"] = []
    simulation_state["puntos_servidos"] = []
    simulation_state["last_update"] = datetime.now()
    simulation_state["active_trucks_limit"] = num_camiones 
    simulation_state["global_capacity"] = capacidad_kg # Guardar capacidad global

    # 3. Transformar y guardar puntos
    for i, p in enumerate(predicciones):
        # Generar ID único si no existe
        p_id = p.get('id_punto', p.get('id'))
        if not p_id:
            p_id = i + 1 # ID secuencial simple partiendo de 1
            
        simulation_state["puntos_pendientes"].append({
            "id": p_id,
            "nombre": p.get('punto', f'Punto {p_id}'),
            "lat": p['latitud'],
            "lon": p['longitud'],
            "demanda": p['prediccion_kg']
        })
    
    # --- CLUSTERIZACIÓN ESTÁTICA INICIAL ---
    # Ordenar por Latitud (Norte -> Sur) para asignar sectores fijos
    # Añadir un poco de aleatoriedad al orden para que las fronteras de los sectores varíen ligeramente
    random.shuffle(simulation_state["puntos_pendientes"]) # Mezclar primero
    simulation_state["puntos_pendientes"].sort(key=lambda p: p['lat'] + random.uniform(-0.001, 0.001), reverse=True)
    
    total_pts = len(simulation_state["puntos_pendientes"])
    if total_pts > 0 and num_camiones > 0:
        chunk_size = math.ceil(total_pts / num_camiones)
        for idx, point in enumerate(simulation_state["puntos_pendientes"]):
            # Asignar cluster_id basado en la posición en la lista ordenada
            # 0: Norte, 1: Centro, 2: Sur (aprox)
            point['cluster_id'] = min(idx // chunk_size, num_camiones - 1)
            
    logger.info(f"Simulación inicializada con {total_pts} puntos para {fecha}. Sectores asignados.")
    
    return {
        "status": "success", 
        "message": "Simulación inicializada", 
        "puntos": len(simulation_state["puntos_pendientes"])
    }

def calcular_demanda_lstm(punto_id: int, lat: float, lon: float) -> float:
    """
    Calcula la demanda estimada usando el servicio LSTM.
    """
    # Factores temporales actuales
    now = datetime.now()
    hora = now.hour
    dia = now.weekday()
    
    # Obtener predicción normalizada (0.0 - 1.0)
    # Usamos 'urbana' como tipo genérico por ahora
    prediccion_data = LSTMPredictionService.predecir_demanda("urbana", hora, dia)
    valor_normalizado = prediccion_data.get("demanda_normalizada", 0.5)
    
    # Desnormalizar: Asumimos que 1.0 = 200kg (Capacidad máxima de un contenedor típico)
    demanda_kg = valor_normalizado * 200.0
    
    # Añadir un poco de aleatoriedad determinista basada en el ID del punto para variar entre puntos
    random.seed(punto_id + hora) 
    variacion = random.uniform(0.8, 1.2)
    
    return round(demanda_kg * variacion, 2)

@router.get("/ping")
async def ping():
    """Endpoint de prueba para verificar conexión desde Java"""
    return {"status": "Python listening", "message": "Conexión exitosa JADE <-> FastAPI"}

@router.get("/world/state")
async def get_world_state():
    """
    Retorna el estado actual combinando BD (Estructura) + Simulación (Dinámica) + LSTM (Predicción)
    """
    # Actualizar física de la simulación
    await update_simulation()

    # 1. Obtener Camiones Reales de la BD
    # Usar el límite configurado en init, o default 3
    limit_camiones = simulation_state.get("active_trucks_limit", 3)
    global_cap = simulation_state.get("global_capacity", 1000) # Obtener capacidad configurada

    camiones_db, _ = CamionService.obtener_camiones(limit=limit_camiones)
    
    camiones_response = {}
    
    for c in camiones_db:
        c_id_str = f"camion_{c['id_camion']}"
        
        # Obtener o inicializar estado dinámico
        sim_state = get_or_init_camion_state(c_id_str, c)
        
        camiones_response[c_id_str] = {
            "id_db": c['id_camion'],
            "patente": c['patente'],
            "capacidad": global_cap, # Usar la capacidad de la simulación, no la de BD
            "lat": sim_state["lat"],
            "lon": sim_state["lon"],
            "carga": sim_state["carga"],
            "ruta": sim_state["ruta_actual"]
        }

    # 2. Obtener Puntos Pendientes de la Simulación
    # Si no se ha inicializado, devolver lista vacía (o intentar cargar por defecto, pero mejor esperar init)
    puntos_pendientes = simulation_state.get("puntos_pendientes", [])
    
    # Filtrar puntos que ya están asignados a algún camión en la simulación actual
    puntos_asignados_ids = set()
    for c_state in simulation_state["camiones"].values():
        for p in c_state["ruta_actual"]:
            puntos_asignados_ids.add(p["id"])

    # Retornar solo los no asignados Y no servidos
    servidos_set = set(simulation_state.get("puntos_servidos", []))
    puntos_filtrados = [p for p in puntos_pendientes if p["id"] not in puntos_asignados_ids and p["id"] not in servidos_set]

    return {
        "camiones": camiones_response,
        "puntos_pendientes": puntos_filtrados,
        "puntos_servidos": simulation_state.get("puntos_servidos", [])
    }

@router.post("/agent/action")
async def receive_agent_action(
    agent_id: str = Body(..., embed=True),
    action_type: str = Body(..., embed=True),
    parameters: Dict[str, Any] = Body(..., embed=True)
):
    """
    Recibe una decisión de un agente JADE y la ejecuta en el entorno.
    """
    logger.info(f"Recibida acción de {agent_id}: {action_type} - {parameters}")
    
    if action_type == "DESCARGAR":
        if agent_id in simulation_state["camiones"]:
             sim_camion = simulation_state["camiones"][agent_id]
             # Planificar ruta al vertedero
             start_lat, start_lon = sim_camion["lat"], sim_camion["lon"]
             
             # Usar await para no bloquear
             path_vertedero = await get_osrm_route(start_lat, start_lon, VERTEDERO_COORDS[0], VERTEDERO_COORDS[1])
             
             # Sobrescribir movimiento actual para ir directo al vertedero
             sim_camion["cola_movimiento"] = path_vertedero
             sim_camion["cola_destinos"] = ["DESCARGA_VERTEDERO"]
             
             return {"status": "accepted", "result": "Yendo a vertedero a descargar"}
        else:
             return {"status": "failed", "reason": "Agente no encontrado"}

    if action_type == "SOLICITAR_RUTA":
        # Verificar si el camión existe en la simulación
        if agent_id in simulation_state["camiones"]:
            sim_camion = simulation_state["camiones"][agent_id]
            
            # Obtener capacidad configurada en la simulación
            capacidad = simulation_state.get("global_capacity", 1000)
            
            # Extraer ID numérico para BD
            try:
                db_id = int(agent_id.split("_")[1])
            except:
                db_id = 1 # Fallback

            # Obtener puntos pendientes de la simulación
            all_pendientes = simulation_state.get("puntos_pendientes", [])
            
            # Filtrar asignados
            puntos_asignados_ids = set()
            for c_state in simulation_state["camiones"].values():
                for p in c_state["ruta_actual"]:
                    puntos_asignados_ids.add(p["id"])
            
            pendientes = [p for p in all_pendientes if p["id"] not in puntos_asignados_ids]

            if not pendientes:
                return {
                    "status": "failed",
                    "agent_id": agent_id,
                    "reason": "No hay pedidos pendientes en la simulación"
                }

            # --- LÓGICA DE ASIGNACIÓN: SECTORIZACIÓN ESTÁTICA ---
            # Cada camión solo ve puntos de su 'cluster_id' pre-asignado.
            
            num_camiones = simulation_state.get("active_trucks_limit", 3)
            my_cluster_id = sim_camion.get("cluster_id", 0)
            
            # Filtrar por mi sector
            mis_puntos = [p for p in pendientes if p.get('cluster_id') == my_cluster_id]
            
            # Fallback: Si mi sector está vacío, ayudar a sectores adyacentes
            if not mis_puntos and pendientes:
                 logger.info(f"⚠️ Sector {my_cluster_id} vacío. Buscando trabajo extra (Smart Balancing).")
                 
                 # ESTRATEGIA INTELIGENTE: Buscar el sector más cargado y ayudar
                 # Contar puntos por cluster
                 counts = {}
                 for p in pendientes:
                     cid = p.get('cluster_id', -1)
                     counts[cid] = counts.get(cid, 0) + 1
                 
                 if counts:
                     # Encontrar cluster con más trabajo
                     busiest_cluster = max(counts, key=counts.get)
                     logger.info(f"🚛 {agent_id} ayudando al sector {busiest_cluster} ({counts[busiest_cluster]} pts)")
                     mis_puntos = [p for p in pendientes if p.get('cluster_id') == busiest_cluster]
                 else:
                     # Si no hay clusters definidos, tomar cualquiera
                     mis_puntos = pendientes

            # 4. Ordenar mis puntos por cercanía (Greedy dentro del sector)
            mis_puntos.sort(key=lambda p: math.sqrt((p['lat'] - sim_camion['lat'])**2 + (p['lon'] - sim_camion['lon'])**2))
            
            # Reemplazamos la lista 'pendientes' original con nuestra lista filtrada
            pendientes = mis_puntos
            
            # Calcular carga planificada
            carga_planificada = sim_camion["carga"]
            for p in sim_camion["ruta_actual"]:
                 if p["id"] not in simulation_state.get("puntos_servidos", []):
                     carga_planificada += p["demanda"]

            candidatos = []
            # Batch dinámico con aleatoriedad para evitar rutas idénticas
            # A veces tomamos 5, a veces 8. Esto desincroniza a los agentes.
            BATCH_SIZE = random.randint(5, 8)
            
            for p in pendientes:
                if carga_planificada + p["demanda"] <= capacidad:
                    carga_planificada += p["demanda"]
                    candidatos.append(p)
                    
                    # BLOQUEO PREVENTIVO: Marcar como "asignado" temporalmente en memoria
                    # para que si otro camión entra en este milisegundo no lo tome.
                    # (Aunque con partición estricta esto es redundante, es doble seguridad)
                    # simulation_state["puntos_servidos"].append(p["id"]) # No, esto lo borraría del mapa. Mejor confiar en la partición.
                    
                    if len(candidatos) >= BATCH_SIZE: 
                        break
            
            if candidatos:
                # 2. ROUTING: Ordenar los candidatos usando Greedy Nearest Neighbor (TSP Heurístico)
                # Optimizamos el orden de visita para minimizar la distancia total recorrida en este lote
                ruta_ordenada = []
                current_lat, current_lon = sim_camion["lat"], sim_camion["lon"]
                
                # Copia para no modificar la lista original mientras iteramos
                pool_candidatos = candidatos.copy()
                
                while pool_candidatos:
                    # Buscar el más cercano al punto actual
                    nearest = min(pool_candidatos, key=lambda p: math.sqrt((p['lat'] - current_lat)**2 + (p['lon'] - current_lon)**2))
                    ruta_ordenada.append(nearest)
                    pool_candidatos.remove(nearest)
                    current_lat, current_lon = nearest['lat'], nearest['lon']

                nuevos_puntos = ruta_ordenada

                # 1. Actualizar Simulación
                # IMPORTANTE: Asegurar que ruta_actual esté limpia si estaba vacía
                if not sim_camion["ruta_actual"]:
                    sim_camion["ruta_actual"] = []
                
                sim_camion["ruta_actual"].extend(nuevos_puntos)
                
                # --- NUEVO: Planificar movimiento físico (BATCH OSRM) ---
                # Construir lista de puntos para OSRM: [Inicio, P1, P2, ..., Pn]
                puntos_para_osrm = []
                
                # Punto de partida
                if not sim_camion["cola_movimiento"]:
                    start_lat, start_lon = sim_camion["lat"], sim_camion["lon"]
                else:
                    # Si ya se mueve, partimos del último punto de la cola actual
                    last = sim_camion["cola_movimiento"][-1]
                    start_lat, start_lon = last[0], last[1]
                
                puntos_para_osrm.append([start_lat, start_lon])
                
                # Agregar destinos
                for p in nuevos_puntos:
                    puntos_para_osrm.append([p["lat"], p["lon"]])
                
                # Obtener ruta completa de una sola vez
                full_path = await get_osrm_route_batch(puntos_para_osrm)
                
                # Agregar a la cola de movimiento
                sim_camion["cola_movimiento"].extend(full_path)
                
                # Actualizar cola de destinos lógicos
                sim_camion["cola_destinos"].extend([p["id"] for p in nuevos_puntos])

                # 2. Persistir en BD (Crear Ruta Planificada)
                # Esto deja registro real en la base de datos
                try:
                    secuencia_ids = [p["id"] for p in nuevos_puntos]
                    RutaPlanificadaService.crear_ruta(
                        id_zona=1, # Default
                        id_turno=1, # Default
                        fecha=parameters.get("fecha", "2025-12-07"),
                        secuencia_puntos=secuencia_ids,
                        id_camion=db_id
                    )
                    logger.info(f"💾 Ruta guardada en BD para {agent_id}")
                except Exception as e:
                    logger.error(f"Error guardando ruta en BD: {e}")

                return {
                    "status": "accepted",
                    "agent_id": agent_id,
                    "result": f"Ruta asignada con {len(nuevos_puntos)} puntos. Carga: {sim_camion['carga']}"
                }
            else:
                 return {
                    "status": "failed",
                    "agent_id": agent_id,
                    "reason": "Capacidad insuficiente"
                }

    return {
        "status": "accepted",
        "agent_id": agent_id,
        "result": "Action processed"
    }
