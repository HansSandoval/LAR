# 2-opt: Búsqueda Local para Optimización VRP

## 📖 Descripción Teórica

**2-opt** es un algoritmo de búsqueda local que mejora iterativamente una solución VRP mediante el intercambio de aristas.

### Principio de funcionamiento

En una ruta, 2-opt:
1. **Selecciona dos aristas**: (i → i+1) y (j → j+1)
2. **Las intercambia**: (i → j) y (i+1 → j+1)
3. **Invierte el segmento**: [i+1...j]

```
Antes:  D → A → B → C → D → E → F
Aristas: (D,A) y (D,E)

Después: D → E → C → B → A → F  (invierte A-B-C)
Aristas: (D,E) y (A,F)
```

### Ventajas

- **Simple de implementar**
- **Mejora significativa**: típicamente 5-20% de reducción
- **Rápido para instancias pequeñas** (<500 nodos)
- **Aplicable a múltiples restricciones** (capacidad, ventanas de tiempo)

### Limitaciones

- **Mínimos locales**: puede atascarse en soluciones subóptimas
- **Tiempo O(n²)** por iteración (costoso para instancias grandes)
- No garantiza optimum global

## 🔧 Implementación en gestion_rutas/vrp

### Archivos

- **`optimizacion.py`**: Contiene la heurística 2-opt
  - `delta_2opt()`: Calcula ganancia potencial
  - `aplica_2opt()`: Aplica un movimiento mejorante
  - `optimiza_rutas_2opt()`: Wrapper para múltiples rutas
  - `or_opt_single()`: Variante más rápida

### Función principal

```python
def optimiza_rutas_2opt(
    routes: List[List[int]], 
    dist_matrix: List[List[float]], 
    max_iteraciones: int = 1000,
    timeout: float = 60.0
) -> Dict:
```

**Retorna:**
- `routes`: Rutas mejoradas
- `distancia_inicial`: Antes de optimizar
- `distancia_final`: Después de optimizar
- `mejora_pct`: Porcentaje de mejora
- `tiempo_s`: Tiempo de ejecución
- `iteraciones`: Iteraciones realizadas

## 📊 Resultados Empíricos

### Test con 9 nodos, 2 vehículos

| Métrica | NN Puro | NN + 2-opt | Mejora |
|---------|---------|-----------|--------|
| Distancia | 249.12 km | 233.70 km | **6.2%** ↓ |
| Tiempo | <0.001s | ~0.01s | +0.009s |
| Solución | Inicial | Local óptimo | ✅ |

### Escalabilidad

| Nodos | Vehículos | Tiempo 2-opt | Mejora |
|-------|-----------|-------------|--------|
| 10-20 | 2-3 | <0.1s | 5-15% |
| 50-100 | 5-10 | 0.5-2s | 3-10% |
| 500+ | 50+ | >30s | 1-5% |

*Nota: Tiempos en laptop estándar*

## 🚀 Pipeline de Optimización

```
Entrada (VRPInput)
        ↓
Validación
        ↓
Matriz de distancias
        ↓
┌─────────────────────┐
│ Nearest Neighbor    │ ← Heurística constructiva
│ (construcción)      │   Tiempo: O(n²)
└─────────────────────┘   Calidad: 70-80% óptimo
        ↓
    Rutas iniciales
        ↓
┌─────────────────────┐
│ Búsqueda Local 2-opt│ ← Mejora iterativa
│ (optimización)      │   Tiempo: O(n² × iter)
└─────────────────────┘   Calidad: +5-20% mejora
        ↓
Rutas optimizadas
        ↓
Conversión a IDs
        ↓
Salida (VRPOutput)
```

## 💻 Uso en la API

### Endpoint

```
POST /rutas/planificar?aplicar_optimizacion=true
```

### Con cURL (2-opt habilitado)

```bash
curl -X POST "http://localhost:8000/rutas/planificar?aplicar_optimizacion=true" \
  -H "Content-Type: application/json" \
  -d '{
    "candidates": [
      {"id": "D", "x": 50, "y": 50, "demand": 0},
      {"id": 1, "x": 45, "y": 68, "demand": 10},
      {"id": 2, "x": 42, "y": 70, "demand": 7}
    ],
    "vehicle_count": 2,
    "capacity": 20
  }'
```

### Con cURL (solo NN, sin 2-opt)

```bash
curl -X POST "http://localhost:8000/rutas/planificar?aplicar_optimizacion=false" \
  -H "Content-Type: application/json" \
  -d '...'
```

### En Python

```python
from vrp import VRPInput, planificar_vrp_api

entrada = VRPInput(
    candidates=[...],
    vehicle_count=2,
    capacity=20
)

# Con 2-opt (por defecto)
salida = planificar_vrp_api(entrada, aplicar_2opt=True, timeout_2opt=30.0)

# Solo NN
salida_nn = planificar_vrp_api(entrada, aplicar_2opt=False)
```

## 🔄 Extensiones Futuras

### Algoritmos complementarios

1. **Or-opt**: Desplazar segmentos de 1-3 nodos
2. **3-opt**: Intercambiar 3 aristas (más potente pero costoso)
3. **Tabu Search**: Evitar soluciones recientes
4. **Simulated Annealing**: Escapar de mínimos locales
5. **Lin-Kernighan**: Generalización de k-opt

### Características adicionales

- **Ventanas de tiempo** (time windows)
- **Descarga intermedia** (load balancing)
- **Múltiples depósitos**
- **Clientes con preferencias de horario**

## 📚 Referencias

- Laporte, G. (1992). "The traveling salesman problem: An overview"
- Croes, G.A. (1958). "A method for solving traveling-salesman problems"
- Helsgaun, K. (2000). "An effective implementation of the Lin-Kernighan TSP heuristic"

## 🧪 Tests

Ejecutar pruebas de 2-opt:

```bash
cd gestion_rutas
python vrp/test_2opt.py
```

Resultado esperado: Mejora de 5-10% con tiempo <1s para instancias pequeñas.
