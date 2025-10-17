"""planificador.py

Planificador VRP con optimización local.

Pipeline:
1. Validación de entrada (Pydantic)
2. Construcción de matriz de distancias
3. Heurística constructiva: vecino más cercano
4. Búsqueda local: 2-opt (mejora iterativa de rutas)
5. Conversión a IDs y devolución de resultado

Contiene:
- Heurística constructiva (nearest neighbor)
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


def nearest_neighbor_vrp(dist_matrix: List[List[float]], demands: List[float], vehicle_count: int, capacity: float) -> Dict:
    """Heurística vecino más cercano que trabaja sobre índices.

    Entrada:
    - dist_matrix: matriz nxn
    - demands: lista de demandas (len n)
    - vehicle_count: número de vehículos
    - capacity: capacidad por vehículo

    Retorna dict con 'routes' (listas de índices), 'unassigned' y 'total_distance'
    """
    n = len(dist_matrix)
    if n == 0:
        return {'routes': [], 'unassigned': [], 'total_distance': 0.0}

    visited = [False] * n
    visited[0] = True  # depósito
    routes: List[List[int]] = []
    total_distance = 0.0

    for _ in range(vehicle_count):
        route = [0]
        load_remaining = capacity
        current = 0

        while True:
            nearest = None
            nearest_d = float('inf')
            for j in range(1, n):
                if not visited[j] and demands[j] <= load_remaining:
                    d = dist_matrix[current][j]
                    if d < nearest_d:
                        nearest_d = d
                        nearest = j
            if nearest is None:
                break
            visited[nearest] = True
            route.append(nearest)
            load_remaining -= demands[nearest]
            total_distance += nearest_d
            current = nearest

        total_distance += dist_matrix[current][0]
        route.append(0)
        routes.append(route)

    unassigned = [i for i in range(1, n) if not visited[i]]
    return {'routes': routes, 'unassigned': unassigned, 'total_distance': total_distance}


def planificar_vrp_api(input_model: VRPInput, aplicar_2opt: bool = True, timeout_2opt: float = 30.0) -> VRPOutput:
    """Wrapper que recibe el Pydantic model y devuelve el Pydantic output.

    Pipeline: Nearest Neighbor → 2-opt (opcional)
    
    Parámetros:
    - input_model: VRPInput con candidatos y restricciones
    - aplicar_2opt: si True, aplica búsqueda local 2-opt
    - timeout_2opt: tiempo máximo en segundos para 2-opt

    Retorna VRPOutput con rutas optimizadas.
    """
    prep = validate_and_prepare(input_model)
    nodes: List[NodeCoordinate] = prep['nodes']
    dist_matrix = prep['dist_matrix']
    vehicle_count = prep['vehicle_count']
    capacity = prep['capacity']
    demands = [float(n.demand or 0.0) for n in nodes]

    # Paso 1: Heurística constructiva (Nearest Neighbor)
    result = nearest_neighbor_vrp(dist_matrix, demands, vehicle_count, capacity)
    routes = result['routes']
    distancia_nn = result['total_distance']
    
    # Paso 2: Búsqueda local (2-opt)
    if aplicar_2opt and len(routes) > 0:
        opt_result = optimiza_rutas_2opt(routes, dist_matrix, timeout=timeout_2opt)
        routes = opt_result['routes']
        distancia_final = opt_result['distancia_final']
        mejora = opt_result['mejora_pct']
    else:
        distancia_final = distancia_nn
        mejora = 0.0

    # Conversión a IDs
    def idx_to_id(idx: int):
        node = nodes[idx]
        return node.id if node.id is not None else idx

    routes_ids = [[idx_to_id(i) for i in r] for r in routes]
    unassigned_ids = [idx_to_id(i) for i in result['unassigned']]

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
