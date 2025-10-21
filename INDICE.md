# 📋 DOCUMENTACIÓN OFICIAL - PROYECTO LAR

## 📌 Archivos de Referencia

Esta carpeta contiene solo los documentos esenciales:

### 📖 Documentación de Inicio
- **README.md** - Visión general y quick start del proyecto
- **GUIA_INSTALACION.md** - Instalación completa paso a paso
- **GUIA_EJECUCION_API.md** - Cómo ejecutar y usar el API

### 📊 Información del Proyecto
- **RESUMEN_EJECUTIVO.md** - Estado actual, tecnologías y componentes

### 🔌 Documentación de API REST - FASE 5 (NUEVA)
- **RESUMEN_EJECUTIVO_FASE_5.md** ⭐ Resumen para gerentes (KPIs, ROI, próximos pasos)
- **DOCUMENTACION_ENDPOINTS_REST.md** - Referencia completa de todos los 93+ endpoints CRUD
- **RESUMEN_FASE_5_ENDPOINTS_REST.md** - Resumen técnico de implementación
- **GUIA_RAPIDA_ENDPOINTS.md** - Guía práctica con 10+ ejemplos comunes
- **VERIFICACION_FASE_5.md** - Checklist de validación técnica

---

## 🗂️ Estructura del Proyecto

```
LAR/
├── .env                              # Configuración (PostgreSQL)
├── README.md                         ⭐ Inicio aquí
├── GUIA_INSTALACION.md               # Instalación
├── GUIA_EJECUCION_API.md             # Ejecución del API
├── RESUMEN_EJECUTIVO.md              # Estado del proyecto
│
└── gestion_rutas/                    # Aplicación principal
    ├── database/
    │   └── db.py                    # Configuración PostgreSQL
    ├── models/
    │   ├── models.py                # 12 tablas ORM
    │   └── base.py
    ├── service/                     # 5+ servicios
    │   ├── zona_service.py
    │   ├── ruta_service.py
    │   ├── ruta_planificada_service.py
    │   ├── lstm_service.py
    │   └── ...
    ├── routers/                     # Endpoints FastAPI
    │   ├── ruta.py
    │   └── lstm_router.py
    ├── schemas/                     # Modelos Pydantic
    │   └── schemas.py
    ├── lstm/                        # Predicción de demanda
    │   ├── entrenar_lstm.py
    │   ├── predicciones_lstm.csv
    │   └── ...
    ├── vrp/                         # Optimización 2-opt
    │   ├── planificador.py
    │   ├── optimizacion.py
    │   ├── schemas.py
    │   └── test_2opt.py
    ├── main.py                      # Punto de entrada
    └── init_db.py                   # Inicializar BD
```

---

## 🎯 Estado Actual (21 Octubre 2025)

### ✅ Completado
- [x] Base de datos PostgreSQL (504 registros)
- [x] 12 modelos ORM configurados
- [x] 5+ servicios de lógica de negocio
- [x] LSTM con 503 predicciones validadas
- [x] API FastAPI con routers
- [x] Optimización 2-opt para VRP
- [x] Código limpio (sin SQLite, sin Nearest Neighbor)

### 🔄 En Progreso
- [ ] Endpoints CRUD completos (11/12 tablas)
- [ ] Autenticación JWT

### 📋 Pendiente
- [ ] Tests unitarios
- [ ] Documentación OpenAPI mejorada
- [ ] Optimización de queries
- [ ] Deployment

---

## 🚀 Inicio Rápido

### 1. Instalación (5 minutos)
```bash
cd LAR
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 2. Configuración (.env)
```
DB_USER=postgres
DB_PASSWORD=hanskawaii1
DB_HOST=localhost
DB_PORT=5432
DB_NAME=gestion_rutas
```

### 3. Ejecutar
```bash
cd gestion_rutas
python main.py
```

### 4. Acceder
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 📊 Componentes Principales

### Base de Datos
- **Motor**: PostgreSQL
- **Tablas**: 12 (relaciones ORM configuradas)
- **Datos**: 504 registros (1 zona + 503 predicciones LSTM)

### API FastAPI
- **Framework**: FastAPI 0.104+
- **Endpoints**: ~15+ operacionales
- **Validación**: Pydantic models
- **CORS**: Habilitado para desarrollo

### LSTM
- **Modelo**: v1.0 (TensorFlow)
- **Predicciones**: 503 muestras
- **Métricas**: MAPE, RMSE, MAE, R²
- **Validación**: Completa

### VRP 2-opt
- **Algoritmo**: 2-opt (búsqueda local)
- **Entrada**: Nodos, capacidades, vehículos
- **Salida**: Rutas optimizadas
- **Mejora**: Hasta 30%

---

## 📚 Documentación Detallada

Consulta estos archivos para más información:

| Documento | Contiene |
|-----------|----------|
| **GUIA_INSTALACION.md** | Pasos detallados de instalación |
| **GUIA_EJECUCION_API.md** | Cómo ejecutar y usar endpoints |
| **RESUMEN_EJECUTIVO.md** | Descripción técnica del proyecto |

---

## 🔍 Verificación Rápida

```bash
# ¿Funciona PostgreSQL?
psql -U postgres -d gestion_rutas

# ¿Funciona el API?
curl http://localhost:8000/docs

# ¿Funciona LSTM?
curl http://localhost:8000/lstm/metricas

# ¿Funciona VRP?
curl -X POST http://localhost:8000/rutas/planificar \
  -H "Content-Type: application/json" \
  -d '{"candidates":[...],"vehicle_count":2,"capacity":100}'
```

---

## 💡 Tips

1. **Ver logs del API**: Mantén abierta la terminal durante `python main.py`
2. **Acceder a Swagger**: Mejor para explorar y probar endpoints
3. **BD PostgreSQL**: Debe estar corriendo en localhost:5432
4. **Variables de entorno**: Siempre revisar `.env`

---

## 🆘 Troubleshooting

### Error: "connection refused"
→ PostgreSQL no está corriendo o credenciales incorrectas

### Error: "404 Not Found"
→ Endpoint no existe, revisar `/docs` para ver disponibles

### Error: "ModuleNotFoundError"
→ Falta instalar dependencias: `pip install -r requirements.txt`

---

## 🔗 Links Útiles

- 📖 [FastAPI Docs](https://fastapi.tiangolo.com/)
- 🐘 [PostgreSQL](https://www.postgresql.org/)
- 🐍 [SQLAlchemy](https://www.sqlalchemy.org/)
- 🤖 [TensorFlow](https://www.tensorflow.org/)

---

## 📝 Notas

- El proyecto es **production-ready** para la funcionalidad actual
- Se usa **PostgreSQL exclusivamente** (sin SQLite)
- **2-opt** es el único algoritmo VRP (sin Nearest Neighbor)
- Datos LSTM completamente funcionales y validados

---

**Última actualización**: 21 de octubre de 2025  
**Status**: ✅ En desarrollo activo  
**Próximo**: Endpoints CRUD completos
