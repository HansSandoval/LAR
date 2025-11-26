import numpy as np
from stable_baselines3 import PPO
from .dvrptw_env import DVRPTWEnv
from .schemas import NodeCoordinate

def planificar_con_ppo(nodos: list[NodeCoordinate], num_vehiculos: int, capacidad: float, modelo_path: str = "gestion_rutas/vrp/modelo_ppo_vrp.zip"):
    """
    Planifica rutas utilizando un modelo PPO entrenado.
    """
    # 1. Convertir NodeCoordinate a diccionarios para DVRPTWEnv
    clientes_data = []
    depot = None
    
    # Mapeo de ID original a ID interno (1..N)
    id_map = {}
    reverse_id_map = {0: 'D'} # 0 es siempre depot
    
    cliente_idx = 1
    for nodo in nodos:
        if str(nodo.id) == 'D' or nodo.demand == 0: # Asumimos D o demanda 0 es depot
            depot = nodo
            continue
            
        # ID interno secuencial para el entorno
        internal_id = cliente_idx
        id_map[nodo.id] = internal_id
        reverse_id_map[internal_id] = nodo.id
        
        clientes_data.append({
            'id': internal_id,
            'nombre': str(nodo.id),
            'latitud': nodo.x, # Usamos X como latitud
            'longitud': nodo.y, # Usamos Y como longitud
            'demanda_kg': nodo.demand,
            'prioridad': 1
        })
        cliente_idx += 1
        
    if not depot:
        depot_lat = 0
        depot_lon = 0
    else:
        depot_lat = depot.x
        depot_lon = depot.y

    # 2. Inicializar entorno
    # Nota: Para coordenadas cartesianas simples, OSRM fallará y usará fallback lineal (Haversine).
    # Si las coordenadas son pequeñas (0-100), Haversine dará distancias muy pequeñas en km.
    # Pero para efectos de visualización de la secuencia, debería servir.
    env = DVRPTWEnv(
        num_camiones=num_vehiculos,
        capacidad_camion_kg=capacidad,
        clientes=clientes_data,
        depot_lat=depot_lat,
        depot_lon=depot_lon,
        modo_marl=True
    )
    
    # 3. Cargar modelo
    try:
        model = PPO.load(modelo_path)
    except Exception as e:
        print(f"Error cargando modelo: {e}")
        return None

    # 4. Ejecutar episodio
    obs, _ = env.reset()
    done = False
    
    max_steps = len(clientes_data) * 2 + 100 # Safety break
    steps = 0
    
    while not done and steps < max_steps:
        action, _states = model.predict(obs, deterministic=True)
        obs, reward, terminated, truncated, info = env.step(action)
        done = terminated or truncated
        steps += 1

    # 5. Extraer rutas y convertir a IDs originales
    rutas_finales = []
    for camion in env.camiones:
        ruta_ids_originales = ['D'] # Inicio en Depot
        for internal_id in camion.ruta_actual:
            if internal_id in reverse_id_map:
                ruta_ids_originales.append(reverse_id_map[internal_id])
            else:
                ruta_ids_originales.append(internal_id)
        
        # Si la ruta no termina en D, agregar D (retorno)
        if ruta_ids_originales[-1] != 'D':
            ruta_ids_originales.append('D')
            
        rutas_finales.append(ruta_ids_originales)
        
    return rutas_finales
