from fastapi import APIRouter
from vrp.schemas import VRPInput, VRPOutput
from vrp.planificador import planificar_vrp_api

router = APIRouter(
    prefix="/rutas",      
    tags=["Rutas"]        
)

@router.get("/{id}")
def obtener_ruta(id: int):
    return {"ruta_id": id, "detalle": "Aquí irán los datos de la ruta"}


@router.post("/planificar", response_model=VRPOutput, summary="Planificar rutas VRP con 2-opt")
def planificar_rutas(input_vrp: VRPInput, aplicar_optimizacion: bool = True):
    """
    Endpoint para planificar rutas usando heurística de vecino más cercano + 2-opt.
    
    **Pipeline de optimización:**
    1. Nearest Neighbor: construcción inicial de rutas
    2. 2-opt: búsqueda local para mejorar rutas
    
    **Entrada:**
    - `candidates`: Lista de zonas candidatas con coordenadas (x, y) y demanda
    - `vehicle_count`: Número de vehículos disponibles
    - `capacity`: Capacidad por vehículo (kg)
    - `distance_matrix`: (Opcional) Matriz de distancias precomputada
    - `aplicar_optimizacion`: (Opcional, default=true) Aplica 2-opt
    
    **Salida:**
    - `routes`: Rutas optimizadas (listas de IDs de zonas, incluye depósito al inicio y fin)
    - `unassigned`: Zonas no asignadas por restricción de capacidad
    - `total_distance`: Distancia total aproximada
    
    **Ejemplo de entrada:**
    ```json
    {
      "candidates": [
        {"id": "D", "x": 50, "y": 50, "demand": 0},
        {"id": 1, "x": 45, "y": 68, "demand": 10},
        {"id": 2, "x": 42, "y": 70, "demand": 7}
      ],
      "vehicle_count": 2,
      "capacity": 20,
      "distance_matrix": null
    }
    ```
    
    **Ejemplo de salida:**
    ```json
    {
      "routes": [
        ["D", 1, "D"],
        ["D", 2, "D"]
      ],
      "unassigned": [],
      "total_distance": 57.8
    }
    ```
    """
    return planificar_vrp_api(input_vrp, aplicar_2opt=aplicar_optimizacion, timeout_2opt=30.0)
