#  Sistema de Gestión de Rutas Logísticas

Sistema de optimización de rutas para recolección de residuos con predicción de demanda LSTM e integración VRP con 2-opt.

---

##  Características

-  **API FastAPI** - Endpoints REST completos
-  **PostgreSQL** - Base de datos centralizada
-  **LSTM** - Predicción de demanda (503 predicciones validadas)
-  **2-opt** - Optimización de rutas VRP
-  **12 Modelos ORM** - Relaciones configuradas
-  **5+ Servicios** - Lógica de negocio desacoplada

---

##  Tech Stack

| Componente | Tecnología |
|-----------|-----------|
| Backend | FastAPI 0.104+ |
| Base de Datos | PostgreSQL 12+ |
| ORM | SQLAlchemy 2.0 |
| ML/Predicción | TensorFlow/LSTM |
| Optimización VRP | 2-opt (búsqueda local) |

---

##  Documentación Rápida

| Documento | Propósito |
|-----------|----------|
| [GUIA_INSTALACION.md](GUIA_INSTALACION.md) | Instalación paso a paso |
| [GUIA_EJECUCION_API.md](GUIA_EJECUCION_API.md) | Cómo ejecutar el API |
| [RESUMEN_EJECUTIVO.md](RESUMEN_EJECUTIVO.md) | Estado del proyecto |

---

##  Quick Start

### 1. Instalación

```bash
git clone <repo>
cd LAR
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configurar Base de Datos

Crear archivo `.env`:
```
DB_USER=postgres
DB_PASSWORD=hanskawaii1
DB_HOST=localhost
DB_PORT=5432
DB_NAME=gestion_rutas
```

### 3. Ejecutar API

```bash
cd gestion_rutas
python main.py
```

API disponible en: `http://localhost:8000`

---

##  Endpoints Principales

### Rutas VRP
- `GET /rutas/health` - Estado
- `POST /rutas/planificar` - Calcular ruta optimizada
- `GET /rutas/{id}` - Obtener ruta

### LSTM Predicciones
- `GET /lstm/metricas` - Métricas del modelo
- `GET /lstm/estadisticas` - Estadísticas de predicciones
- `POST /lstm/predecir` - Nueva predicción

---

##  Estructura

```
gestion_rutas/
├── database/         # Configuración PostgreSQL
├── models/           # 12 tablas ORM
├── service/          # 5+ servicios de lógica
├── routers/          # Endpoints FastAPI
├── schemas/          # Modelos Pydantic
├── lstm/             # Modelo y predicciones
├── vrp/              # Optimización 2-opt
└── main.py           # Punto de entrada
```

---

##  Estado del Proyecto

 **Completado:**
- Base de datos (PostgreSQL)
- Modelos ORM (12 tablas)
- Servicios (5+)
- LSTM (503 predicciones)
- 2-opt VRP

 **En Progreso:**
- Endpoints CRUD completos
- Autenticación JWT

---

##  Links Rápidos

-  [Documentación API](http://localhost:8000/docs) - Swagger interactivo
-  [Guía de Instalación](GUIA_INSTALACION.md)
-  [Guía de Ejecución](GUIA_EJECUCION_API.md)
-  [Resumen Ejecutivo](RESUMEN_EJECUTIVO.md)

---

##  Licencia

Proyecto desarrollado para gestión de residuos en Iquique, Chile.

---

##  Desarrollo

**Status**: En desarrollo activo  
**Próximo**: Endpoints CRUD completos  
**Último Update**: Octubre 2025
