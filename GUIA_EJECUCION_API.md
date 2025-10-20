# 🚀 Guía de Ejecución - API Gestión de Rutas VRP

## Requisitos Previos

- Python 3.10+
- Virtual Environment activado
- Dependencias instaladas: `pip install -r requirements.txt`

## 📋 Estructura del Proyecto

```
gestion_rutas/
├── main.py                      # FastAPI app principal
├── database/db.py               # Configuración SQLAlchemy
├── models/models.py             # Modelos ORM
├── service/                     # Lógica de negocio
├── routers/                     # Endpoints FastAPI
├── lstm/                        # Módulo LSTM
└── venv/                        # Virtual environment
```

## 🔧 Configuración Inicial

### 1. Activar Virtual Environment

**Windows (PowerShell):**
```powershell
cd c:\Users\hanss\Desktop\LAR\gestion_rutas
.\venv\Scripts\Activate.ps1
```

**Windows (CMD):**
```cmd
cd c:\Users\hanss\Desktop\LAR\gestion_rutas
venv\Scripts\activate.bat
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 2. Verificar Dependencias

```bash
pip list
```

**Paquetes Requeridos:**
- fastapi
- sqlalchemy
- pandas
- numpy
- matplotlib
- seaborn

### 3. Configuración de Base de Datos

**Crear archivo `.env` en `gestion_rutas/`:**
```
ENVIRONMENT=development
# DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/gestion_rutas

# O dejar vacío para usar SQLite por defecto (recomendado desarrollo)
```

### 4. Inicializar Base de Datos

```bash
python init_db.py
```

Esto creará:
- Todas las tablas en `gestion_rutas.db` (SQLite)
- Datos de prueba iniciales

## ▶️ Ejecutar la API

### Opción 1: Ejecución Estándar

```bash
python main.py
```

**Salida esperada:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
```

### Opción 2: Ejecución con Uvicorn Directo

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Parámetros:**
- `--reload`: Reinicia al detectar cambios (desarrollo)
- `--host`: Dirección de escucha (0.0.0.0 = localhost)
- `--port`: Puerto (por defecto 8000)

### Opción 3: Ejecución con Logs Detallados

```bash
uvicorn main:app --reload --log-level debug
```

## 📊 Acceder a la API

### 1. Documentación Interactiva

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

### 2. Endpoints Principales

#### Health Check
```bash
curl http://localhost:8000/health
```

#### LSTM - Obtener Métricas
```bash
curl http://localhost:8000/lstm/metricas
```

#### LSTM - Realizar Predicción
```bash
curl "http://localhost:8000/lstm/predecir?tipo_zona=industrial&hora_del_dia=10&dia_semana=1"
```

#### VRP - Planificar Rutas
```bash
curl -X POST http://localhost:8000/rutas/planificar \
  -H "Content-Type: application/json" \
  -d '{
    "candidates": [
      {"id": "D", "x": 50, "y": 50, "demand": 0},
      {"id": 1, "x": 45, "y": 68, "demand": 10}
    ],
    "vehicle_count": 2,
    "capacity": 20
  }'
```

## 🧪 Ejecutar Pruebas

### Validación LSTM

```bash
python lstm/test_lstm_validation.py
```

**Genera:**
- Gráficos de validación
- Reportes JSON
- Métricas de desempeño

## 📝 Archivos de Configuración

### `.env` (Ejemplo)
```
ENVIRONMENT=development
API_TITLE=API Gestión de Rutas VRP
API_VERSION=1.0.0
DEBUG=True
ALLOWED_ORIGINS=["http://localhost", "http://localhost:3000", "http://localhost:8000"]
```

### `requirements.txt`
```
fastapi==0.104.0
sqlalchemy==2.0.44
psycopg2-binary==2.9.11
pandas==2.3.3
numpy==2.3.4
matplotlib==3.8.0
seaborn==0.13.0
uvicorn==0.24.0
pydantic==2.5.0
python-dotenv==1.1.1
```

## 🐛 Troubleshooting

### Error: ModuleNotFoundError
```bash
# Solución: Instalar paquete faltante
pip install nombre_paquete
```

### Error: Database connection failed
```bash
# Solución: Verificar .env y credenciales PostgreSQL
# O usar SQLite por defecto (dejar DATABASE_URL vacío)
```

### Error: Port already in use
```bash
# Solución: Cambiar puerto
uvicorn main:app --port 8001
```

### Error: Permission denied (Linux/Mac)
```bash
# Solución: Dar permisos
chmod +x main.py
```

## 📊 Monitoreo

### Ver Logs Detallados
```bash
# En otra terminal
tail -f app.log
```

### Verificar Salud de Servicios
```bash
curl http://localhost:8000/health
curl http://localhost:8000/lstm/health
```

## 🔄 Actualizar Dependencias

```bash
pip install --upgrade -r requirements.txt
```

## 📦 Generar archivo requirements.txt

```bash
pip freeze > requirements.txt
```

## 🌐 Ejecutar en Red Local

```bash
# Todos en red local pueden acceder a: http://<tu_ip>:8000
uvicorn main:app --host 0.0.0.0 --port 8000
```

**Para encontrar tu IP:**
- **Windows**: `ipconfig` (buscar IPv4)
- **Linux/Mac**: `ifconfig` (buscar inet)

## 📱 Ejecutar en Background (Linux/Mac)

```bash
nohup uvicorn main:app --port 8000 > app.log 2>&1 &
```

Para detener:
```bash
pkill -f "uvicorn main:app"
```

## 🔐 Ejecutar en Background (Windows)

Usar batch file: `EJECUTAR_API.bat`
```batch
@echo off
cd c:\Users\hanss\Desktop\LAR\gestion_rutas
python -m uvicorn main:app --reload --port 8000
pause
```

---

**Documentación completa:** http://localhost:8000/docs
**Estado API:** http://localhost:8000/health
**Modelo LSTM:** http://localhost:8000/lstm/health
