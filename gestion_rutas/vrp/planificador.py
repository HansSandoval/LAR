"""planificador.py

Planificador VRP con optimización local 2-opt.

Pipeline:
1. Validación de entrada (Pydantic)
2. Construcción de matriz de distancias
3. Construcción de ruta inicial (simple orden secuencial)
4. Búsqueda local: 2-opt (mejora iterativa de rutas)
5. Conversión a IDs y devolución de resultado

Contiene:
- Construcción de ruta inicial
- Búsqueda local (2-opt)
- Gestión de capacidad y restricciones
"""

from math import hypot
from typing import List, Dict, Tuple, Optional

from .schemas import VRPInput, VRPOutput, NodeCoordinate
from .optimizacion import optimiza_rutas_2opt, calcula_distancia_ruta


def euclidean(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    return hypot(a[0] - b[0], a[1] - b[1])


def build_distance_matrix_from_coords(coords: List[Tuple[float, float]]) -> List[List[float]]:
    n = len(coords)
    dist = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i != j:
                dist[i][j] = euclidean(coords[i], coords[j])
    return dist


def validate_and_prepare(input_data: VRPInput) -> Dict:
    """Valida y prepara estructuras internas a partir del modelo Pydantic.

    Retorna un dict con keys: nodes (lista de NodeCoordinate), dist_matrix, vehicle_count, capacity
    """
    nodes = input_data.candidates
    coords = [(n.x, n.y) for n in nodes]
    if input_data.distance_matrix:
        dist_matrix = input_data.distance_matrix
    else:
        dist_matrix = build_distance_matrix_from_coords(coords)

    return {
        'nodes': nodes,
        'coords': coords,
        'dist_matrix': dist_matrix,
        'vehicle_count': input_data.vehicle_count,
        'capacity': input_data.capacity,
    }


def build_initial_routes(n_nodes: int, demands: List[float], vehicle_count: int, capacity: float) -> Dict:
    """Construye rutas iniciales distribuyendo nodos secuencialmente entre vehículos.
    
    Respeta capacidad y devuelve rutas iniciales para posterior optimización 2-opt.
    """
    if n_nodes == 0:
        return {'routes': [], 'unassigned': [], 'total_distance': 0.0}
    
    routes: List[List[int]] = []
    unassigned: List[int] = []
    assigned = [False] * n_nodes
    assigned[0] = True  # depósito siempre asignado
    
    vehicle_idx = 0
    for node_idx in range(1, n_nodes):
        if vehicle_idx >= vehicle_count:
            unassigned.append(node_idx)
            continue
            
        if not routes or sum(demands[i] for i in routes[-1]) + demands[node_idx] > capacity:
            # Nueva ruta si capacidad se excede
            if vehicle_idx > 0 and routes[-1]:
                routes[-1].append(0)  # retorno al depósito
            if vehicle_idx < vehicle_count:
                routes.append([0])  # nuevo inicio
                vehicle_idx += 1
            else:
                unassigned.append(node_idx)
                continue
        
        routes[-1].append(node_idx)
        assigned[node_idx] = True
    
    # Cerrar rutas con retorno al depósito
    for route in routes:
        if route[-1] != 0:
            route.append(0)
    
    return {'routes': routes, 'unassigned': unassigned, 'total_distance': 0.0}


def nearest_neighbor_vrp(dist_matrix: List[List[float]], demands: List[float], vehicle_count: int, capacity: float) -> Dict:
    """
    Implementación de VRP usando heurística de Vecino Más Cercano (Nearest Neighbor).
    """
    n_nodes = len(dist_matrix)
    unvisited = set(range(1, n_nodes)) # 0 es depot
    routes = []
    total_distance = 0.0
    
    for _ in range(vehicle_count):
        if not unvisited:
            break
            
        current_route = [0]
        current_load = 0.0
        current_node = 0
        
        while True:
            # Buscar vecino más cercano no visitado que quepa
            best_node = None
            min_dist = float('inf')
            
            for node in unvisited:
                if current_load + demands[node] <= capacity:
                    dist = dist_matrix[current_node][node]
                    if dist < min_dist:
                        min_dist = dist
                        best_node = node
            
            if best_node is not None:
                current_route.append(best_node)
                current_load += demands[best_node]
                total_distance += min_dist
                current_node = best_node
                unvisited.remove(best_node)
            else:
                break
        
        # Volver al depósito
        if len(current_route) > 1:
            total_distance += dist_matrix[current_node][0]
            current_route.append(0)
            routes.append(current_route)
            
    return {
        'routes': routes,
        'total_distance': total_distance,
        'unassigned': list(unvisited)
    }


def planificar_vrp_api(input_model: VRPInput, aplicar_2opt: bool = True, timeout_2opt: float = 30.0) -> VRPOutput:
    """Wrapper que recibe el Pydantic model y devuelve el Pydantic output.

    Pipeline: Construcción inicial (NN) → 2-opt (Opcional)
    
    Parámetros:
    - input_model: VRPInput con candidatos y restricciones
    - aplicar_2opt: Si True, aplica optimización local
    - timeout_2opt: tiempo máximo en segundos para 2-opt

    Retorna VRPOutput con rutas optimizadas.
    """
    prep = validate_and_prepare(input_model)
    nodes: List[NodeCoordinate] = prep['nodes']
    dist_matrix = prep['dist_matrix']
    vehicle_count = prep['vehicle_count']
    capacity = prep['capacity']
    demands = [float(n.demand or 0.0) for n in nodes]

    # Paso 1: Construcción de ruta inicial usando Nearest Neighbor (mejor que secuencial)
    result = nearest_neighbor_vrp(dist_matrix, demands, vehicle_count, capacity)
    routes = result['routes']
    distancia_final = result['total_distance']
    unassigned_indices = result['unassigned']
    
    # Paso 2: Búsqueda local (2-opt)
    if aplicar_2opt and len(routes) > 0:
        print(f"DEBUG: Iniciando 2-opt con {len(routes)} rutas. Distancia pre-opt: {distancia_final}")
        opt_result = optimiza_rutas_2opt(routes, dist_matrix, timeout=timeout_2opt)
        routes = opt_result['routes']
        distancia_final = opt_result['distancia_final']
        print(f"DEBUG: Fin 2-opt. Distancia post-opt: {distancia_final}")
    else:
        print("DEBUG: Saltando 2-opt")

    # Conversión a IDs
    def idx_to_id(idx: int):
        node = nodes[idx]
        return node.id if node.id is not None else idx

    routes_ids = [[idx_to_id(i) for i in r] for r in routes]
    unassigned_ids = [idx_to_id(i) for i in unassigned_indices]

    return VRPOutput(routes=routes_ids, unassigned=unassigned_ids, total_distance=distancia_final)


if __name__ == '__main__':

    ejemplo_nodes = [
        NodeCoordinate(id='D', x=50, y=50, demand=0),
        NodeCoordinate(id=1, x=45, y=68, demand=10),
        NodeCoordinate(id=2, x=42, y=70, demand=7),
        NodeCoordinate(id=3, x=60, y=60, demand=12),
        NodeCoordinate(id=4, x=30, y=40, demand=5),
        NodeCoordinate(id=5, x=55, y=20, demand=9),
    ]

    from .schemas import VRPInput

    inp = VRPInput(candidates=ejemplo_nodes, vehicle_count=2, capacity=20)
    out = planificar_vrp_api(inp)
    print(out.json(indent=2, ensure_ascii=False))
