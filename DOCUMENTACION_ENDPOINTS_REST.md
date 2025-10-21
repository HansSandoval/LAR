# 📋 Documentación de Endpoints REST - Sistema de Gestión de Rutas

**Versión:** 1.0.0  
**Fecha:** Enero 2024  
**Base URL:** `http://localhost:8000`  
**Documentación Interactiva:** `http://localhost:8000/docs`

---

## 📊 Resumen de Endpoints Creados

Total de endpoints CRUD implementados: **75+**  
Total de routers: **12** (6 existentes + 6 nuevos en esta fase)

### Distribución de Endpoints por Router

| Router | Endpoints | Tipo |
|--------|-----------|------|
| **zona_router** | 7 | GET list, GET by-id, POST, PUT, DELETE, PATCH estado, GET estadísticas |
| **punto_router** | 7 | GET list, GET by-id, POST, PUT, DELETE, GET proximidad |
| **camion_router** | 7 | GET list, GET by-id, POST, PUT, DELETE, PATCH estado, GET estadísticas |
| **ruta_planificada_router** | 7 | GET list, GET by-id, POST, PUT, DELETE, PATCH estado, GET detalles |
| **turno_router** | 7 | GET list, GET by-id, POST, PUT, DELETE, PATCH estado, GET camion |
| **ruta_ejecutada_router** | 8 | GET list, GET by-id, POST, PUT, DELETE, GET detalles, GET desviacion |
| **incidencia_router** | 9 | GET list, GET by-id, POST, PUT, DELETE, GET por-tipo, GET por-severidad, GET criticas |
| **prediccion_demanda_router** | 8 | GET list, GET by-id, POST, PUT, DELETE, GET ultimas, GET estadísticas |
| **usuario_router** | 9 | GET list, GET by-id, POST, PUT, DELETE, PATCH estado, PATCH cambiar-password, GET rol |
| **punto_disposicion_router** | 8 | GET list, GET by-id, POST, PUT, DELETE, GET proximidad, GET estadísticas |
| **periodo_temporal_router** | 8 | GET list, GET by-id, POST, PUT, DELETE, GET activos, GET por-estacionalidad |
| **ruta + lstm_router** | 10 | Endpoints existentes (entrenamiento LSTM, optimización VRP, etc.) |

---

## 🔄 Nuevos Routers Creados en Esta Fase

### 1. **Turno Router** (`/turnos`)

**Base Model:** `Turno`  
**Descripción:** Gestión de turnos de trabajo asignados a camiones

#### Endpoints Disponibles

| Método | Ruta | Descripción |
|--------|------|-------------|
| **GET** | `/turnos/` | Listar turnos con paginación y filtros |
| **GET** | `/turnos/{turno_id}` | Obtener turno por ID |
| **POST** | `/turnos/` | Crear nuevo turno |
| **PUT** | `/turnos/{turno_id}` | Actualizar turno |
| **DELETE** | `/turnos/{turno_id}` | Eliminar turno |
| **PATCH** | `/turnos/{turno_id}/estado` | Cambiar estado del turno |
| **GET** | `/turnos/{turno_id}/camion` | Obtener información del camión del turno |

**Filtros disponibles en GET /turnos/:**
- `estado` - Filtrar por estado (activo, inactivo, completado)
- `id_camion` - Filtrar por camión
- `fecha_desde` - Filtrar desde fecha
- `fecha_hasta` - Filtrar hasta fecha

**Estados válidos:** `activo`, `inactivo`, `completada`

**Ejemplo de payload POST:**
```json
{
    "id_camion": 1,
    "fecha": "2024-01-15",
    "hora_inicio": "08:00:00",
    "hora_fin": "16:00:00",
    "operador": "Juan Pérez",
    "estado": "activo"
}
```

---

### 2. **Ruta Ejecutada Router** (`/rutas-ejecutadas`)

**Base Model:** `RutaEjecutada`  
**Descripción:** Registro y seguimiento de rutas ejecutadas en tiempo real

#### Endpoints Disponibles

| Método | Ruta | Descripción |
|--------|------|-------------|
| **GET** | `/rutas-ejecutadas/` | Listar rutas ejecutadas con paginación |
| **GET** | `/rutas-ejecutadas/{ruta_exec_id}` | Obtener ruta ejecutada por ID |
| **POST** | `/rutas-ejecutadas/` | Crear registro de ruta ejecutada |
| **PUT** | `/rutas-ejecutadas/{ruta_exec_id}` | Actualizar ruta ejecutada |
| **DELETE** | `/rutas-ejecutadas/{ruta_exec_id}` | Eliminar ruta ejecutada |
| **GET** | `/rutas-ejecutadas/{ruta_exec_id}/detalles-completos` | Obtener detalles completos con relaciones |
| **GET** | `/rutas-ejecutadas/{ruta_exec_id}/desviacion` | Calcular desviación vs planificado |

**Filtros disponibles en GET /rutas-ejecutadas/:**
- `id_ruta` - Filtrar por ruta planificada
- `id_camion` - Filtrar por camión
- `fecha_desde` - Filtrar desde fecha
- `fecha_hasta` - Filtrar hasta fecha

**Validaciones:**
- Cumplimiento horario: 0-100%
- Duración real > 0
- Referencias válidas a Ruta y Camión

**Ejemplo de payload POST:**
```json
{
    "id_ruta": 1,
    "id_camion": 1,
    "fecha": "2024-01-15",
    "distancia_real_km": 45.5,
    "duracion_real_min": 120,
    "cumplimiento_horario_pct": 95.5,
    "desviacion_km": 2.3,
    "telemetria_json": {}
}
```

---

### 3. **Incidencia Router** (`/incidencias`)

**Base Model:** `Incidencia`  
**Descripción:** Registro de incidentes y problemas ocurridos durante rutas

#### Endpoints Disponibles

| Método | Ruta | Descripción |
|--------|------|-------------|
| **GET** | `/incidencias/` | Listar incidencias con filtros |
| **GET** | `/incidencias/{incidencia_id}` | Obtener incidencia por ID |
| **POST** | `/incidencias/` | Crear nueva incidencia |
| **PUT** | `/incidencias/{incidencia_id}` | Actualizar incidencia |
| **DELETE** | `/incidencias/{incidencia_id}` | Eliminar incidencia |
| **GET** | `/incidencias/estadisticas/por-tipo` | Estadísticas agrupadas por tipo |
| **GET** | `/incidencias/estadisticas/por-severidad` | Estadísticas agrupadas por severidad |
| **GET** | `/incidencias/criticas` | Listar solo incidencias críticas |

**Filtros disponibles en GET /incidencias/:**
- `tipo` - Tipo de incidencia
- `severidad_min` - Severidad mínima (1-5)
- `severidad_max` - Severidad máxima (1-5)
- `id_zona` - Filtrar por zona
- `id_camion` - Filtrar por camión
- `fecha_desde` - Filtrar desde fecha
- `fecha_hasta` - Filtrar hasta fecha

**Niveles de severidad:**
- 1 = Baja
- 2 = Media
- 3 = Normal
- 4 = Alta
- 5 = Crítica

**Ejemplo de payload POST:**
```json
{
    "id_ruta_exec": 1,
    "id_zona": 1,
    "id_camion": 1,
    "tipo": "accidente",
    "descripcion": "Colisión menor en calle Principal",
    "fecha_hora": "2024-01-15T14:30:00",
    "severidad": 3
}
```

---

### 4. **Predicción Demanda Router** (`/predicciones-demanda`)

**Base Model:** `PrediccionDemanda`  
**Descripción:** Gestión de predicciones LSTM de demanda de residuos por zona

#### Endpoints Disponibles

| Método | Ruta | Descripción |
|--------|------|-------------|
| **GET** | `/predicciones-demanda/` | Listar predicciones con filtros |
| **GET** | `/predicciones-demanda/{prediccion_id}` | Obtener predicción por ID |
| **POST** | `/predicciones-demanda/` | Crear nueva predicción |
| **PUT** | `/predicciones-demanda/{prediccion_id}` | Actualizar predicción |
| **DELETE** | `/predicciones-demanda/{prediccion_id}` | Eliminar predicción |
| **GET** | `/predicciones-demanda/zona/{id_zona}/ultimas` | Últimas predicciones de una zona |
| **GET** | `/predicciones-demanda/estadisticas/precision-modelo` | Precisión por versión LSTM |

**Filtros disponibles en GET /predicciones-demanda/:**
- `id_zona` - Filtrar por zona
- `horizonte_horas` - Horizonte de predicción
- `fecha_desde` - Desde fecha
- `fecha_hasta` - Hasta fecha
- `modelo_version` - Versión del modelo LSTM

**Ejemplo de payload POST:**
```json
{
    "id_zona": 1,
    "horizonte_horas": 24,
    "fecha_prediccion": "2024-01-15T10:30:00",
    "valor_predicho_kg": 2500.5,
    "valor_real_kg": 2450.0,
    "modelo_lstm_version": "v2.0",
    "error_rmse": 125.3,
    "error_mape": 5.2
}
```

---

### 5. **Usuario Router** (`/usuarios`)

**Base Model:** `Usuario`  
**Descripción:** Gestión de usuarios con control de roles

#### Endpoints Disponibles

| Método | Ruta | Descripción |
|--------|------|-------------|
| **GET** | `/usuarios/` | Listar usuarios con filtros |
| **GET** | `/usuarios/{usuario_id}` | Obtener usuario por ID |
| **POST** | `/usuarios/` | Crear nuevo usuario |
| **PUT** | `/usuarios/{usuario_id}` | Actualizar usuario |
| **DELETE** | `/usuarios/{usuario_id}` | Eliminar usuario |
| **PATCH** | `/usuarios/{usuario_id}/estado` | Cambiar estado (activo/inactivo) |
| **PATCH** | `/usuarios/{usuario_id}/cambiar-password` | Cambiar contraseña |
| **GET** | `/usuarios/rol/{rol_id}` | Listar usuarios por rol |

**Filtros disponibles en GET /usuarios/:**
- `rol` - Filtrar por rol
- `activo` - Filtrar por estado
- `nombre` - Buscar por nombre

**Roles válidos:** `admin`, `operador`, `gerente`, `visualizador`

**Validaciones:**
- Email único y formato válido
- Contraseña mínimo 8 caracteres
- Rol debe ser válido

**Ejemplo de payload POST:**
```json
{
    "nombre": "Juan Pérez",
    "correo": "juan.perez@example.com",
    "rol": "operador",
    "password": "MiPassword123"
}
```

---

### 6. **Punto Disposición Router** (`/puntos-disposicion`)

**Base Model:** `PuntoDisposicion`  
**Descripción:** Gestión de puntos de disposición final de residuos

#### Endpoints Disponibles

| Método | Ruta | Descripción |
|--------|------|-------------|
| **GET** | `/puntos-disposicion/` | Listar puntos con filtros |
| **GET** | `/puntos-disposicion/{punto_id}` | Obtener punto por ID |
| **POST** | `/puntos-disposicion/` | Crear nuevo punto |
| **PUT** | `/puntos-disposicion/{punto_id}` | Actualizar punto |
| **DELETE** | `/puntos-disposicion/{punto_id}` | Eliminar punto |
| **GET** | `/puntos-disposicion/proximidad/por-coordenadas` | Buscar por proximidad |
| **GET** | `/puntos-disposicion/estadisticas/por-tipo` | Estadísticas por tipo |

**Filtros disponibles en GET /puntos-disposicion/:**
- `tipo` - Tipo de disposición (relleno, reciclaje, compostaje)
- `nombre` - Buscar por nombre

**Validaciones:**
- Latitud: -90 a 90
- Longitud: -180 a 180
- Capacidad > 0

**Ejemplo de payload POST:**
```json
{
    "nombre": "Relleno Sanitario Norte",
    "tipo": "relleno",
    "latitud": -20.2558,
    "longitud": -70.1402,
    "capacidad_diaria_ton": 500.0
}
```

---

### 7. **Período Temporal Router** (`/periodos-temporales`)

**Base Model:** `PeriodoTemporal`  
**Descripción:** Gestión de períodos temporales para análisis estacional

#### Endpoints Disponibles

| Método | Ruta | Descripción |
|--------|------|-------------|
| **GET** | `/periodos-temporales/` | Listar períodos con filtros |
| **GET** | `/periodos-temporales/{periodo_id}` | Obtener período por ID |
| **POST** | `/periodos-temporales/` | Crear nuevo período |
| **PUT** | `/periodos-temporales/{periodo_id}` | Actualizar período |
| **DELETE** | `/periodos-temporales/{periodo_id}` | Eliminar período |
| **GET** | `/periodos-temporales/activos/en-rango` | Períodos activos en rango |
| **GET** | `/periodos-temporales/por-estacionalidad/{estacionalidad}` | Períodos por estación |

**Filtros disponibles en GET /periodos-temporales/:**
- `tipo_granularidad` - diario, semanal, mensual, anual
- `estacionalidad` - verano, invierno, primavera, otoño, general

**Ejemplo de payload POST:**
```json
{
    "fecha_inicio": "2024-01-01T00:00:00",
    "fecha_fin": "2024-01-31T23:59:59",
    "tipo_granularidad": "diario",
    "estacionalidad": "verano"
}
```

---

## 📚 Endpoints Existentes (Fases Anteriores)

### Zona Router (`/zonas`) - 6 endpoints
- Gestión completa de zonas de recolección
- Incluye estadísticas de puntos, rutas, incidencias

### Punto Router (`/puntos`) - 7 endpoints
- Gestión completa de puntos de recolección
- Búsqueda por proximidad geográfica

### Camión Router (`/camiones`) - 7 endpoints
- Gestión de flota vehicular
- Control de estado operativo
- Estadísticas de rutas ejecutadas

### Ruta Planificada Router (`/rutas-planificadas`) - 7 endpoints
- Gestión de rutas optimizadas con VRP
- Vista detallada con información relacionada

### Ruta Router (`/rutas`) - 5+ endpoints
- Optimización de rutas (algoritmo 2-opt)
- Generación de secuencias optimizadas

### LSTM Router (`/lstm`) - 5+ endpoints
- Entrenamiento de modelo LSTM
- Generación de predicciones
- Estadísticas de precisión

---

## 🔐 Validaciones Implementadas

### Validaciones Comunes

✅ **Campos obligatorios**: Validados mediante Pydantic  
✅ **Tipos de datos**: Conversión automática y validación  
✅ **Rangos**: Minutos, máximos, valores positivos  
✅ **Relaciones**: Verificación de referencias FK  
✅ **Unicidad**: Email de usuarios, etc.  
✅ **Enumeraciones**: Estados, roles, tipos  

### Por Router

**Turno:**
- Hora inicio < Hora fin
- Camión existe
- Estados válidos

**RutaEjecutada:**
- Cumplimiento 0-100%
- Duración > 0
- Referencias válidas

**Incidencia:**
- Severidad 1-5
- Zona y Camión existen
- Ruta ejecutada existe (opcional)

**PrediccionDemanda:**
- Horizonte > 0
- Valores ≥ 0
- Zona existe
- Errores ≥ 0

**Usuario:**
- Email válido y único
- Contraseña ≥ 8 caracteres
- Rol válido

**PuntoDisposicion:**
- Coordenadas válidas
- Capacidad > 0

**PeriodoTemporal:**
- Fecha inicio < Fecha fin
- Granularidad válida

---

## 📊 Estructura de Respuestas

### Respuesta Exitosa (200/201)

```json
{
    "id_xxx": 1,
    "campo1": "valor",
    "campo2": 123,
    ...
}
```

### Lista Paginada (GET list)

```json
{
    "data": [
        {"id": 1, "campo": "valor"},
        {"id": 2, "campo": "valor"}
    ],
    "total": 250,
    "skip": 0,
    "limit": 10
}
```

### Error (400/404/500)

```json
{
    "detail": "Descripción del error"
}
```

### Eliminación (204)

```
Sin contenido
```

---

## 🚀 Ejemplos de Uso

### Crear un turno

```bash
curl -X POST "http://localhost:8000/turnos/" \
  -H "Content-Type: application/json" \
  -d '{
    "id_camion": 1,
    "fecha": "2024-01-15",
    "hora_inicio": "08:00:00",
    "hora_fin": "16:00:00",
    "operador": "Juan Pérez",
    "estado": "activo"
  }'
```

### Listar incidencias críticas

```bash
curl "http://localhost:8000/incidencias/criticas?skip=0&limit=10"
```

### Obtener predicciones recientes de una zona

```bash
curl "http://localhost:8000/predicciones-demanda/zona/1/ultimas?horizonte_horas=24&limite=5"
```

### Buscar puntos de disposición cercanos

```bash
curl "http://localhost:8000/puntos-disposicion/proximidad/por-coordenadas?latitud=-20.25&longitud=-70.14&radio_km=50"
```

### Cambiar contraseña de usuario

```bash
curl -X PATCH "http://localhost:8000/usuarios/1/cambiar-password?password_actual=OldPass123&password_nueva=NewPass456"
```

---

## 📋 Checklist de Cobertura CRUD

| Modelo | GET List | GET ID | POST | PUT | DELETE | Especial | Estado |
|--------|----------|--------|------|-----|--------|----------|--------|
| Zona | ✅ | ✅ | ✅ | ✅ | ✅ | Estadísticas | ✅ |
| PuntoRecoleccion | ✅ | ✅ | ✅ | ✅ | ✅ | Proximidad | ✅ |
| Camion | ✅ | ✅ | ✅ | ✅ | ✅ | Estado, Estadísticas | ✅ |
| RutaPlanificada | ✅ | ✅ | ✅ | ✅ | ✅ | Detalles | ✅ |
| Turno | ✅ | ✅ | ✅ | ✅ | ✅ | Estado, Camión | ✅ |
| RutaEjecutada | ✅ | ✅ | ✅ | ✅ | ✅ | Detalles, Desviación | ✅ |
| Incidencia | ✅ | ✅ | ✅ | ✅ | ✅ | Estadísticas, Críticas | ✅ |
| PrediccionDemanda | ✅ | ✅ | ✅ | ✅ | ✅ | Últimas, Precisión | ✅ |
| Usuario | ✅ | ✅ | ✅ | ✅ | ✅ | Estado, Password, Rol | ✅ |
| PuntoDisposicion | ✅ | ✅ | ✅ | ✅ | ✅ | Proximidad, Estadísticas | ✅ |
| PeriodoTemporal | ✅ | ✅ | ✅ | ✅ | ✅ | Activos, Estacionalidad | ✅ |
| Ruta/LSTM | ✅ | ✅ | ✅ | ✅ | ✅ | Entrenamiento, Predicción | ✅ |

---

## 🔄 Status Code Reference

| Código | Significado | Casos de Uso |
|--------|------------|---------------|
| **200** | OK | GET exitoso, PUT exitoso |
| **201** | Created | POST exitoso |
| **204** | No Content | DELETE exitoso |
| **400** | Bad Request | Validación fallida, datos inválidos |
| **401** | Unauthorized | Contraseña incorrecta |
| **404** | Not Found | Recurso no existe |
| **500** | Server Error | Error interno del servidor |

---

## 🔄 Próximos Pasos

1. ✅ Crear 8 CRUD routers (COMPLETADO)
2. ✅ Extender schemas Pydantic (COMPLETADO)
3. ✅ Integrar routers en main.py (COMPLETADO)
4. ⏳ Testing e integración
5. ⏳ Implementar autenticación JWT
6. ⏳ Agregar autorización por roles
7. ⏳ Documentación de bases de datos
8. ⏳ Tests unitarios e integración

---

**Versión de Documentación:** 1.0  
**Última Actualización:** Enero 2024  
**Autor:** Sistema de Gestión de Rutas
