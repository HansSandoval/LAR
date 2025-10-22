# 🏗️ ARQUITECTURA DEL SISTEMA - BACKEND FASTAPI

## Diagrama General

```
┌─────────────────────────────────────────────────────────────────────┐
│                      CLIENTE / NAVEGADOR                             │
│                                                                      │
│  ✅ Mapa Interactivo (Leaflet)                                      │
│  ├─ 675 Puntos azules (Recolección)                                 │
│  ├─ 3 Puntos rojos (Disposición)                                    │
│  ├─ Zoom, cluster, búsqueda                                         │
│  └─ Rutas visualizadas (PRÓXIMO)                                    │
│                                                                      │
│  ✅ Documentación Swagger/OpenAPI                                   │
│  ├─ GET/POST/PUT/DELETE de todos los recursos                      │
│  ├─ Try it out en navegador                                         │
│  └─ Schema validation en tiempo real                                │
│                                                                      │
└─────────────────────┬──────────────────────────────────────────────┘
                      │
                      │ HTTP (REST API)
                      │ JSON/HTML Responses
                      │
┌─────────────────────▼──────────────────────────────────────────────┐
│                    FASTAPI SERVER (Port 8001)                       │
│                                                                     │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │ MAIN APPLICATION (main.py - 87 líneas)                    │   │
│  ├─ FastAPI() instance                                        │   │
│  ├─ CORS middleware (cualquier origen)                        │   │
│  ├─ Static files (/static)                                   │   │
│  ├─ Template files (/templates)                              │   │
│  └─ Router imports (14 total)                                │   │
│  │                                                            │   │
│  └───────────────┬──────────────────────────────────────────┘   │
│                  │                                               │
│  ┌───────────────▼──────────────────────────────────────────┐   │
│  │ ROUTERS LAYER (1,500+ líneas)                            │   │
│  │                                                          │   │
│  │ 📍 Mapa Router (mapa_router.py - 142 líneas)           │   │
│  │    └─ GET /mapa/rutas → HTML con Leaflet              │   │
│  │                                                          │   │
│  │ 📍 Puntos Router (punto_router.py - 150 líneas)        │   │
│  │    ├─ GET    /puntos/         → Lista (675)            │   │
│  │    ├─ GET    /puntos/{id}     → Detalle               │   │
│  │    ├─ POST   /puntos/         → Crear                  │   │
│  │    ├─ PUT    /puntos/{id}     → Actualizar            │   │
│  │    └─ DELETE /puntos/{id}     → Eliminar              │   │
│  │                                                          │   │
│  │ 📍 Camión Router (camion_router.py - 130 líneas)       │   │
│  │    ├─ GET    /camiones/                                 │   │
│  │    ├─ POST   /camiones/                                 │   │
│  │    ├─ PUT    /camiones/{id}                             │   │
│  │    └─ DELETE /camiones/{id}                             │   │
│  │                                                          │   │
│  │ [13 ROUTERS MÁS... todos con CRUD completo]            │   │
│  │ ├─ Zona, PuntoDisposicion, Operador                    │   │
│  │ ├─ RutaPlanificada, RutaEjecutada, Turno              │   │
│  │ ├─ Incidencia, Usuario, PrediccionDemanda             │   │
│  │ ├─ PeriodoTemporal, VRP, LSTM                          │   │
│  │ └─ Status: ✅ 59 ENDPOINTS TOTALES                     │   │
│  │                                                          │   │
│  └───────────────┬──────────────────────────────────────────┘   │
│                  │                                               │
│  ┌───────────────▼──────────────────────────────────────────┐   │
│  │ SCHEMAS LAYER (Validación Pydantic)                     │   │
│  │ (schemas.py - 400+ líneas)                              │   │
│  │                                                          │   │
│  │ 28 Clases Pydantic:                                     │   │
│  │ ├─ PuntoRecoleccionCreate      (POST request)           │   │
│  │ ├─ PuntoRecoleccionUpdate      (PUT request)            │   │
│  │ ├─ PuntoRecoleccionResponse    (GET response)           │   │
│  │ ├─ CamionCreate, CamionResponse, ...                    │   │
│  │ ├─ Validaciones automáticas (ranges, patterns)          │   │
│  │ ├─ Conversión JSON ↔ Python objects                     │   │
│  │ └─ Documentación automática en /docs                    │   │
│  │                                                          │   │
│  └───────────────┬──────────────────────────────────────────┘   │
│                  │                                               │
│  ┌───────────────▼──────────────────────────────────────────┐   │
│  │ SERVICES LAYER (Lógica de Negocio)                      │   │
│  │ (service/ - 850+ líneas)                                │   │
│  │                                                          │   │
│  │ Servicios:                                              │   │
│  │ ├─ PuntoService         (búsqueda, filtrado)           │   │
│  │ ├─ CamionService        (disponibilidad)               │   │
│  │ ├─ ZonaService          (estadísticas)                 │   │
│  │ ├─ RutaService          (cálculos)                     │   │
│  │ ├─ LSTMService          (predicciones)                 │   │
│  │ └─ Métodos reutilizables (CRUD, validaciones)         │   │
│  │                                                          │   │
│  └───────────────┬──────────────────────────────────────────┘   │
│                  │                                               │
│  ┌───────────────▼──────────────────────────────────────────┐   │
│  │ DATABASE LAYER (SQLAlchemy ORM)                         │   │
│  │ (database/db.py - 57 líneas)                            │   │
│  │                                                          │   │
│  ├─ Engine: PostgreSQL 17 (localhost:5432/gestion_rutas)   │   │
│  ├─ SessionLocal factory                                 │   │
│  ├─ get_db() dependency injection                        │   │
│  ├─ Connection pooling (psycopg2)                        │   │
│  └─ UTF-8 encoding + ACID transactions                   │   │
│  │                                                          │   │
│  └───────────────┬──────────────────────────────────────────┘   │
│                  │                                               │
│  ┌───────────────▼──────────────────────────────────────────┐   │
│  │ MODELS LAYER (ORM Definitions)                          │   │
│  │ (models/models.py - 145 líneas)                         │   │
│  │                                                          │   │
│  │ 8 Modelos SQLAlchemy:                                   │   │
│  │ ├─ Zona              (1 registro)                        │   │
│  │ ├─ PuntoRecoleccion  (675 registros)  ✅ POBLADA        │   │
│  │ ├─ PuntoDisposicion  (3 registros)    ✅ POBLADA        │   │
│  │ ├─ Camion            (5 registros)    ✅ POBLADA        │   │
│  │ ├─ Operador          (8 registros)    ✅ POBLADA        │   │
│  │ ├─ RutaPlanificada   (vacía - a llenar con VRP)         │   │
│  │ ├─ RutaEjecutada     (vacía - a llenar con tracking)    │   │
│  │ ├─ Turno             (vacía - a llenar con scheduling)  │   │
│  │ └─ Foreign keys, índices, timestamps automáticos       │   │
│  │                                                          │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────┬──────────────────────────────────────────────┘
                      │
                      │ SQLAlchemy ORM
                      │ SQL Queries
                      │
┌─────────────────────▼──────────────────────────────────────────────┐
│              DATABASE LAYER (PostgreSQL 17)                               │
│                                                                    │
│  📁 PostgreSQL Database (192.168.1.100:5432/gestion_rutas) │
│                                                                    │
│  🗂️  Tablas (8 total):                                            │
│  ├─ zona                    1 fila                               │
│  ├─ punto_recoleccion       675 filas  ✅                        │
│  ├─ punto_disposicion       3 filas    ✅                        │
│  ├─ camion                  5 filas    ✅                        │
│  ├─ operador                8 filas    ✅                        │
│  ├─ ruta_planificada        0 filas    (a llenar)               │
│  ├─ ruta_ejecutada          0 filas    (a llenar)               │
│  ├─ turno                   0 filas    (a llenar)               │
│  ├─ incidencia              0 filas    (a llenar)               │
│  ├─ usuario                 0 filas    (a llenar)               │
│  ├─ periodo_temporal        0 filas    (a llenar)               │
│  ├─ prediccion_demanda      0 filas    (a llenar)               │
│  │                                                               │
│  🔑 Índices:                                                     │
│  ├─ PRIMARY KEY en todas                                        │
│  ├─ FOREIGN KEY relaciones                                      │
│  └─ Índices de búsqueda                                         │
│                                                                    │
│  💾 Características:                                              │
│  ├─ ACID transactions                                            │
│  ├─ Stored procedures (NULL)                                    │
│  ├─ Triggers (NULL)                                             │
│  └─ Constraints (NOT NULL, UNIQUE donde aplique)               │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

---

## Flujo de Datos - Ejemplo: Crear un nuevo punto

```
1. CLIENTE (Navegador)
   └─ POST http://127.0.0.1:8001/puntos/
   └─ Content-Type: application/json
   └─ Body:
      {
        "nombre": "Calle Principal con Avda Central",
        "latitud": -20.27543,
        "longitud": -70.12891,
        "capacidad_kg": 500,
        "zona_id": 1
      }

2. FASTAPI ROUTER (punto_router.py)
   └─ @router.post("/")
   └─ Recibe: PuntoRecoleccionCreate (Pydantic model)
   └─ Dependencia: db: Session = Depends(get_db)
   
3. VALIDACIÓN PYDANTIC (schemas.py)
   └─ PuntoRecoleccionCreate
   ├─ nombre: str (1-200 chars, required)
   ├─ latitud: float (-20.3 to -20.2, required)
   ├─ longitud: float (-70.14 to -70.11, required)
   ├─ capacidad_kg: Optional[float]
   ├─ zona_id: int (foreign key)
   └─ ✅ Si válido, continúa; si no → 422 Unprocessable Entity

4. SERVICIOS (punto_service.py)
   └─ punto_service.create_punto(db, punto_data)
   ├─ Validación adicional de negocio
   ├─ Cálculos si aplican
   ├─ Verificar duplicados
   └─ ✅ Retorna datos validados

5. DATABASE ACCESS (models.py)
   └─ db.add(PuntoRecoleccion(**punto_data))
   ├─ ORM convierte Python object → SQL INSERT
   ├─ Set timestamp de creación automático
   └─ Flush en BD

6. DATABASE (SQLite)
   └─ INSERT INTO punto_recoleccion 
      (nombre, latitud, longitud, capacidad_kg, zona_id, 
       created_at, updated_at)
      VALUES (...);

7. COMMIT TRANSACTION
   └─ db.commit()
   └─ ✅ Datos persistidos en BD

8. RESPONSE BUILDER
   └─ PuntoRecoleccionResponse
   ├─ Convierte modelo BD → JSON
   ├─ Incluye id, timestamps, relaciones
   └─ Status code 201 Created

9. CLIENTE (Navegador)
   └─ Response: 201 Created
   └─ Body:
      {
        "id": 676,
        "nombre": "Calle Principal con Avda Central",
        "latitud": -20.27543,
        "longitud": -70.12891,
        "capacidad_kg": 500,
        "zona_id": 1,
        "created_at": "2025-10-21T15:30:45.123456",
        "updated_at": "2025-10-21T15:30:45.123456"
      }
```

---

## Stack Tecnológico

```
┌─────────────────────────────────────────┐
│  Frontend                               │
├─────────────────────────────────────────┤
│ ✅ Leaflet.js v1.9.4                   │ Mapa interactivo
│ ✅ MarkerCluster plugin                │ Agrupación visual
│ ✅ OpenStreetMap tiles                 │ Cartografía
│ ✅ HTML5 + CSS3                        │ Interfaz
└─────────────────────────────────────────┘
           │
           │ HTTP/REST
           │
┌─────────────────────────────────────────┐
│  Backend                                │
├─────────────────────────────────────────┤
│ ✅ FastAPI 0.104.0                     │ Framework REST
│ ✅ Uvicorn 0.24.0                      │ ASGI server
│ ✅ Pydantic 2.5.0                      │ Validación
│ ✅ SQLAlchemy 2.0.44                   │ ORM
│ ✅ Python 3.13.5                       │ Lenguaje
└─────────────────────────────────────────┘
           │
           │ SQLAlchemy ORM
           │
┌─────────────────────────────────────────┐
│  Database                               │
├─────────────────────────────────────────┤
│ ✅ PostgreSQL 17 (localhost:5432)       │ Producción
│    con 692 registros migrados           │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│  Machine Learning                       │
├─────────────────────────────────────────┤
│ ✅ TensorFlow/Keras                    │ LSTM training
│ ✅ Scikit-learn                        │ Preprocessing
│ ✅ Pandas                              │ Data handling
│ ✅ NumPy                               │ Computations
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│  Optimization                           │
├─────────────────────────────────────────┤
│ ✅ 2-opt Algorithm                     │ VRP solving
│ ✅ NetworkX                            │ Graph analysis
└─────────────────────────────────────────┘
```

---

## Ciclo de Vida de una Solicitud

```
1. REQUEST ENTRY
   └─ Cliente envía HTTP request

2. MIDDLEWARE PROCESSING
   ├─ CORS check
   ├─ Request logging
   ├─ Header parsing
   └─ Continue si válido

3. ROUTING
   ├─ Match endpoint pattern
   ├─ Extract path parameters
   └─ Call router function

4. DEPENDENCY INJECTION
   ├─ Resolver Depends(get_db)
   ├─ Create BD session
   └─ Pass to handler

5. VALIDATION & PARSING
   ├─ JSON → Pydantic model
   ├─ Type checking
   ├─ Constraint validation
   └─ Raise 422 si invalid

6. BUSINESS LOGIC
   ├─ Call service layer
   ├─ Additional validations
   ├─ Calculations
   └─ Database operations

7. DATABASE TRANSACTION
   ├─ Build SQL query
   ├─ Execute via SQLAlchemy
   ├─ Handle results
   └─ Commit o Rollback

8. RESPONSE BUILDING
   ├─ Model → JSON serialization
   ├─ Include metadata
   ├─ Set status code
   └─ Add headers

9. ERROR HANDLING
   ├─ Catch exceptions
   ├─ Format error response
   ├─ Log error
   └─ Return to client

10. RESPONSE DELIVERY
    ├─ Send JSON response
    ├─ Close connection
    └─ Log completion
```

---

## Escalabilidad Futura

```
ACTUAL (Monolítico con PostgreSQL):
┌──────────────────────────────────┐
│ FastAPI + PostgreSQL 17          │
└──────────────────────────────────┘

FUTURO (Microservicios):
┌──────────────────────────────┐  ┌──────────────────────────────┐
│ API Rutas (FastAPI)          │  │ API LSTM (FastAPI)           │
│ ├─ CRUD endpoints            │  │ ├─ Predicción              │
│ ├─ Mapa                      │  │ ├─ Reentrenamiento        │
│ └─ VRP optimization          │  │ └─ Métricas               │
└──────────────────────────────┘  └──────────────────────────────┘
        │                                    │
        └──────────┬───────────────────────┘
                   │
            ┌──────▼────────┐
            │ API Gateway   │
            │ (Rate limit)  │
            └──────┬────────┘
                   │
         ┌─────────┼──────────┐
         │         │          │
    ┌────▼───┐ ┌──▼──┐ ┌─────▼────┐
    │ Cache  │ │Auth │ │ Message  │
    │(Redis) │ │(JWT)│ │ Queue    │
    └────────┘ └─────┘ │(RabbitMQ)│
                        └──────────┘
                           │
         ┌─────────────────┴────────────────┐
         │                                  │
    ┌────▼──────┐                  ┌───────▼────┐
    │ PostgreSQL │                  │  MongoDB   │
    │(Relations) │                  │(NoSQL)     │
    └───────────┘                   └────────────┘
```

