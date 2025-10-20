from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import ruta, lstm_router
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="API Gestión de Rutas VRP",
    description="API para optimización de rutas de entrega con VRP y predicción LSTM",
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
app.include_router(ruta.router)
app.include_router(lstm_router.router)

@app.get("/")
def read_root():
    return {
        "mensaje": "🚀 API de gestión de rutas funcionando!",
        "endpoints": {
            "rutas": "/rutas",
            "lstm": "/lstm",
            "documentación": "/docs"
        }
    }

@app.get("/health")
def health_check():
    """Verificar salud general de la API"""
    return {"status": "healthy", "service": "gestion-rutas-api"}

