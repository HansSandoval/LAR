# Integración FastAPI - Planificador VRP

## ✅ Endpoint integrado: `POST /rutas/planificar`

El planificador VRP ha sido integrado en FastAPI. El endpoint acepta una entrada JSON y devuelve rutas optimizadas.

---

## 📍 Ubicación del Endpoint

- **Ruta**: `/rutas/planificar`
- **Método**: `POST`
- **Router**: `gestion_rutas/routers/ruta.py`
- **Función**: `planificar_rutas()`

---

## 📤 Entrada (VRPInput)

```json
{
  "candidates": [
    {
      "id": "D",
      "x": 50,
      "y": 50,
      "demand": 0
    },
    {
      "id": 1,
      "x": 45,
      "y": 68,
      "demand": 10
    },
    {
      "id": 2,
      "x": 42,
      "y": 70,
      "demand": 7
    },
    {
      "id": 3,
      "x": 60,
      "y": 60,
      "demand": 12
    }
  ],
  "vehicle_count": 2,
  "capacity": 20,
  "distance_matrix": null
}
```

### Campos de entrada:
- **candidates** (requerido): Lista de zonas/puntos
  - `id`: Identificador (opcional, por defecto usa índice)
  - `x`, `y`: Coordenadas (requeridas)
  - `demand`: Demanda en kg (opcional, por defecto 0)
- **vehicle_count** (requerido): Número de vehículos disponibles
- **capacity** (requerido): Capacidad por vehículo en kg
- **distance_matrix** (opcional): Matriz de distancias precomputada (nxn)

---

## 📥 Salida (VRPOutput)

```json
{
  "routes": [
    ["D", 3, 2, "D"],
    ["D", 1, "D"]
  ],
  "unassigned": [],
  "total_distance": 129.08
}
```

### Campos de salida:
- **routes**: Rutas optimizadas (cada ruta comienza y termina en depósito "D")
- **unassigned**: Zonas que no pudieron asignarse por restricción de capacidad
- **total_distance**: Distancia total aproximada de todas las rutas

---

## 🧪 Ejemplos de uso

### Con cURL

```bash
curl -X POST "http://localhost:8000/rutas/planificar" \
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

### Con Python (requests)

```python
import requests

url = "http://localhost:8000/rutas/planificar"

payload = {
    "candidates": [
        {"id": "D", "x": 50, "y": 50, "demand": 0},
        {"id": 1, "x": 45, "y": 68, "demand": 10},
        {"id": 2, "x": 42, "y": 70, "demand": 7}
    ],
    "vehicle_count": 2,
    "capacity": 20
}

response = requests.post(url, json=payload)
print(response.json())
```

### Con Python (VRPInput directo)

```python
from vrp import VRPInput, NodeCoordinate, planificar_vrp_api

nodos = [
    NodeCoordinate(id="D", x=50, y=50, demand=0),
    NodeCoordinate(id=1, x=45, y=68, demand=10),
    NodeCoordinate(id=2, x=42, y=70, demand=7),
]

entrada = VRPInput(candidates=nodos, vehicle_count=2, capacity=20)
salida = planificar_vrp_api(entrada)

print(f"Rutas: {salida.routes}")
print(f"Distancia: {salida.total_distance}")
```

---

## 🚀 Ejecutar el servidor FastAPI

```bash
cd c:\Users\hanss\Desktop\LAR\gestion_rutas

# Opción 1: Con uvicorn (recomendado)
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Opción 2: Con uvicorn directo
uvicorn main:app --reload
```

Luego acceder a:
- **API**: http://localhost:8000/rutas/planificar (POST)
- **Swagger Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## ✅ Tests

Se incluye `test_api.py` que verifica:
1. Endpoint raíz GET `/`
2. Endpoint GET `/rutas/{id}`
3. Endpoint POST `/rutas/planificar` (entrada simple)
4. Endpoint POST `/rutas/planificar` (con matriz personalizada)

Ejecutar:
```bash
python test_api.py
```

---

## 📋 Notas

- El primer nodo siempre se trata como **depósito** (warehouse)
- La demanda del depósito debe ser 0
- Heurística: vecino más cercano con restricción de capacidad
- Para instancias pequeñas (<100 nodos) funciona bien
- Para instancias grandes, considerar algoritmos avanzados
