# Guía de Instalación - API Gestión de Rutas VRP + LSTM

## 📋 Requisitos Previos

- **Python 3.9+**
- **PostgreSQL 12+** (corriendo en localhost:5432)
- **pip** (gestor de paquetes Python)

## 🚀 Instalación Paso a Paso

### 1. Clonar el Repositorio

```bash
git clone <tu-repo-url>
cd LAR
```

### 2. Crear Entorno Virtual

```bash
# En Windows
python -m venv venv
venv\Scripts\activate

# En Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar Variables de Entorno

Crear o actualizar el archivo `.env` en la raíz del proyecto:

```env
# Configuración de Ambiente
ENVIRONMENT=production

# PostgreSQL Configuration
DB_USER=postgres
DB_PASSWORD=hanskawaii1
DB_HOST=localhost
DB_PORT=5432
DB_NAME=gestion_rutas

# Configuración de FastAPI
API_TITLE=API Gestión de Rutas VRP
API_VERSION=1.0.0
API_DESCRIPTION=Backend para gestión de rutas, LSTM y VRP

# CORS
CORS_ORIGINS=["http://localhost", "http://localhost:8000", "http://localhost:3000"]
```

### 5. Crear Base de Datos en PostgreSQL

```sql
-- Conectar a PostgreSQL como administrador
psql -U postgres

-- Crear la base de datos
CREATE DATABASE gestion_rutas;

-- (Opcional) Crear usuario específico
CREATE USER gestion_user WITH PASSWORD 'tu_password';
ALTER ROLE gestion_user SET client_encoding TO 'utf8';
ALTER ROLE gestion_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE gestion_user SET default_transaction_deferrable TO on;
GRANT ALL PRIVILEGES ON DATABASE gestion_rutas TO gestion_user;
```

### 6. Ejecutar el Servidor API

```bash
cd gestion_rutas
python main.py
```

El API estará disponible en: `http://localhost:8000`

### 7. Acceder a la Documentación

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 📦 Estructura del Proyecto

```
gestion_rutas/
├── database/
│   └── db.py                 # Configuración de PostgreSQL
├── models/
│   ├── models.py             # ORM Models
│   └── ruta.py               # Modelos de Ruta
├── service/
│   ├── ruta_service.py       # Lógica de Rutas
│   ├── lstm_service.py       # Lógica de LSTM
│   └── zona_service.py       # Lógica de Zonas
├── routers/
│   ├── ruta.py               # Endpoints de Rutas
│   └── lstm_router.py        # Endpoints de LSTM
├── lstm/
│   ├── entrenar_lstm.py      # Entrenamiento del modelo
│   ├── preprocesamiento.py   # Preprocesamiento de datos
│   └── predicciones_lstm.csv # Predicciones del modelo
├── static/
│   └── css/
│       └── styles.css        # Estilos
├── templates/
│   ├── index.html
│   ├── app.html
│   └── about.html
├── main.py                   # Punto de entrada de FastAPI
└── init_db.py                # Script para inicializar BD
```

## 🔧 Operaciones Comunes

### Inicializar Base de Datos

```bash
python init_db.py
```

### Crear Tablas

```python
from database.db import init_db
init_db()
```

### Verificar Conexión a PostgreSQL

```bash
python -c "
from database.db import engine
print('Conexión a PostgreSQL:', engine)
"
```

## ⚠️ Troubleshooting

### Error: "connection refused"
- Verificar que PostgreSQL esté corriendo: `psql -U postgres`
- Verificar credenciales en `.env`

### Error: "database does not exist"
- Crear la base de datos: `CREATE DATABASE gestion_rutas;`

### Error: "No module named 'gestion_rutas'"
- Estar en el directorio correcto: `cd gestion_rutas`
- Reinstalar dependencias: `pip install -r requirements.txt`

## 📝 Notas

- Este proyecto usa **solo PostgreSQL** para todas las operaciones
- Todos los datos se almacenan en PostgreSQL (localhost:5432)
- La configuración está basada en variables de entorno
- El API incluye CORS habilitado para desarrollo

## 📚 Documentación Adicional

- Ver `README.md` para descripción general del proyecto
- Ver `GUIA_EJECUCION_API.md` para más detalles del API
