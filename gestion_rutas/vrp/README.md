# Módulo VRP - Vehicle Routing Problem

Planificador de rutas con optimización 2-opt para problemas de recolección de residuos con restricciones de capacidad.

##  Arquitectura

```
┌────────────────────────────┐
│   schemas.py               │  ← Modelos Pydantic (VRPInput, VRPOutput)
└────────────────────────────┘
         ↓
┌────────────────────────────┐
│   planificador.py          │  ← Pipeline: validación → construcción inicial → 2-opt
└────────────────────────────┘
         ↓
┌────────────────────────────┐
│   optimizacion.py          │  ← Búsqueda local: 2-opt
└────────────────────────────┘
         ↓
┌────────────────────────────┐
│   API FastAPI              │  ← Endpoint POST /rutas/planificar
│   (routers/ruta.py)        │
└────────────────────────────┘
```

##  Archivos

| Archivo | Descripción |
|---------|-------------|
| `schemas.py` | Modelos Pydantic para entrada/salida |
| `planificador.py` | Heurística constructiva (NN) + pipeline |
| `optimizacion.py` | Búsqueda local (2-opt, Or-opt) |
| `test_vrp.py` | Tests básicos del planificador |
| `test_2opt.py` | Tests de 2-opt con comparativas |
| `test_api.py` | Tests del endpoint FastAPI |
| `README.md` | Este archivo |
| `API_INTEGRATION.md` | Guía de uso del endpoint |
| `OPTIMIZACION_2OPT.md` | Documentación técnica de 2-opt |

##  Uso Rápido

### 1. Instalación

```bash
# Ya incluida en el proyecto
# Dependencias: fastapi, pydantic
```

### 2. Uso directo en Python

```python
from vrp import VRPInput, NodeCoordinate, planificar_vrp_api

# Crear nodos (primer nodo = depósito)
nodos = [
    NodeCoordinate(id='D', x=50, y=50, demand=0),     # Depósito
    NodeCoordinate(id=1, x=45, y=68, demand=10),      # Zona 1
    NodeCoordinate(id=2, x=42, y=70, demand=7),       # Zona 2
]

# Crear entrada
entrada = VRPInput(candidates=nodos, vehicle_count=2, capacity=20)

# Resolver con 2-opt (por defecto)
salida = planificar_vrp_api(entrada, aplicar_2opt=True, timeout_2opt=30.0)

# Resultado
print(f"Rutas: {salida.routes}")          # [['D', 1, 'D'], ['D', 2, 'D']]
print(f"No asignados: {salida.unassigned}") # []
print(f"Distancia: {salida.total_distance}") # 57.8 km
```

### 3. Uso vía API FastAPI

```bash
# Iniciar servidor
python -m uvicorn main:app --reload

# Request
curl -X POST "http://localhost:8000/rutas/planificar" \
  -H "Content-Type: application/json" \
  -d '{
    "candidates": [
      {"id": "D", "x": 50, "y": 50, "demand": 0},
      {"id": 1, "x": 45, "y": 68, "demand": 10}
    ],
    "vehicle_count": 2,
    "capacity": 20
  }'

# Response
{
  "routes": [["D", 1, "D"]],
  "unassigned": [],
  "total_distance": 57.8
}
```

##  Características

### Construcción de Ruta Inicial
- Distribución secuencial de nodos respetando capacidad
- Tiempo: O(n)

### Búsqueda Local
- **2-opt**: Intercambio de aristas para optimización
- Mejora típica: hasta 30%
- Tiempo: segundos para <200 nodos
````

### Restricciones
-  Capacidad por vehículo
-  Múltiples vehículos
-  Depósito único
-  (Extensible: ventanas de tiempo, descarga intermedia)

##  Resultados Empíricos

### Test con 9 nodos, 2 vehículos

| Métrica | NN Puro | NN + 2-opt | Mejora |
|---------|---------|-----------|--------|
| Distancia | 249.12 km | 233.70 km | **6.2%** ↓ |
| Tiempo | <0.001s | ~0.01s | +0.009s |
| Solución | Inicial | Local óptimo |  |

##  Extensiones Futuras (Según documento de trabajo)

### Heurísticas adicionales
1. **Or-opt**: Ya implementado en `optimizacion.py`
2. **3-opt**: Intercambio de 3 aristas
3. **Tabu Search**: Evitar soluciones recientes
4. **LNS (Large Neighborhood Search)**: Búsqueda de vecindario amplio

### Restricciones
- **Ventanas de tiempo** (time windows)
- **Tiempos de servicio** en cada punto
- **Retornos a disposición** (descarga intermedia)
- **Múltiples depósitos**

### Integración
- **Map-matching**: Ajustar rutas a la red vial real
- **GNSS tracking**: Posicionamiento en tiempo real
- **Predicción de demanda**: Integración con LSTM
- **Indicadores**: Energía consumida, emisiones, cumplimiento horario

##  Referencias

- Document: "2.3 Plataformas, datos y articulación con VRP"
- VRP Classic: Toth & Vigo (2002)
- 2-opt: Croes (1958)
- Implementación: Helsgaun (2000)

##  Notas

- El primer nodo siempre es el **depósito** (warehouse)
- La demanda del depósito **debe ser 0**
- Distancias: métrica euclidiana por defecto
- Para instancias >500 nodos, considerar algoritmos avanzados
- 2-opt es determinista (siempre el mismo resultado)

##  Estado

-  Construcción de ruta inicial
-  2-opt (búsqueda local)
-  API FastAPI integrada
-  Tests completos
-  Ventanas de tiempo (TODO)
-  LNS / Tabu Search (TODO)

##  Tests Disponibles

```bash
# Test de 2-opt con comparativas
python vrp/test_2opt.py
# Test del endpoint API
python test_api.py
```

**Resultado esperado en test_2opt.py:**
- NN: 249.12 km
- NN+2-opt: 233.70 km
- Mejora: **6.2%** 
