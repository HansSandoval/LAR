from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from .routers import (
    ruta, mapa_router,
    zona_router, punto_router, camion_router, ruta_planificada_router,
    turno_router, usuario_router, punto_disposicion_router,
    lstm_router, mas_router, operador_router, bridge_router
)
import logging
import os
from pathlib import Path

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="API Gestión de Rutas VRP",
    description="API completa para optimización de rutas de entrega con VRP y predicción LSTM",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(zona_router.router)
app.include_router(punto_router.router)
app.include_router(camion_router.router)
app.include_router(ruta_planificada_router.router)
app.include_router(turno_router.router)
# app.include_router(ruta_ejecutada_router.router)  # Pendiente: Conversión a PostgreSQL
# app.include_router(incidencia_router.router)  # Pendiente: Conversión a PostgreSQL
app.include_router(usuario_router.router)
app.include_router(operador_router.router)
app.include_router(punto_disposicion_router.router)
app.include_router(ruta.router)
app.include_router(mapa_router.router)
app.include_router(lstm_router.router)
app.include_router(mas_router.router)
app.include_router(bridge_router.router)

# Nota: Los siguientes routers están pendientes de conversión a PostgreSQL directo:
# app.include_router(lstm_router.router)
# app.include_router(mapa_predicciones_router.router)
# app.include_router(mas_router.router)
# app.include_router(ruta_ejecutada_router.router)
# app.include_router(incidencia_router.router)
# app.include_router(prediccion_demanda_router.router)
# app.include_router(periodo_temporal_router.router)

# Montar archivos estáticos
static_dir = Path(__file__).parent.parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    logger.info(f"Archivos estáticos montados desde: {static_dir}")
else:
    logger.warning(f"Directorio estático no encontrado: {static_dir}")

# Montar directorio temporal de LSTM para gráficos
lstm_temp_dir = Path(__file__).parent / "lstm" / "lstm_temp"
lstm_temp_dir.mkdir(parents=True, exist_ok=True)
app.mount("/lstm-temp", StaticFiles(directory=str(lstm_temp_dir)), name="lstm-temp")
logger.info(f"Directorio temporal LSTM montado: {lstm_temp_dir}")

@app.get("/")
def read_root():
    """Página de inicio"""
    return FileResponse('static/inicio.html')

@app.get("/api-info")
def read_api_info():
    return {
        "mensaje": " API de gestión de rutas funcionando!",
        "endpoints": {
            "zonas": "/zonas",
            "puntos": "/puntos",
            "camiones": "/camiones",
            "rutas_planificadas": "/rutas-planificadas",
            "turnos": "/turnos",
            "rutas_ejecutadas": "/rutas-ejecutadas",
            "incidencias": "/incidencias",
            "predicciones_demanda": "/predicciones-demanda",
            "usuarios": "/usuarios",
            "puntos_disposicion": "/puntos-disposicion",
            "periodos_temporales": "/periodos-temporales",
            "rutas": "/rutas",
            "lstm": "/lstm",
            "mapa_rutas": "/mapa/rutas",
            "mapa_predicciones_lstm": "/mapa/predicciones",
            "predicciones_json": "/mapa/predicciones/json",
            "documentación": "/docs"
        }
    }

@app.get("/health")
def health_check():
    """Verificar salud general de la API"""
    return {"status": "healthy", "service": "gestion-rutas-api"}



