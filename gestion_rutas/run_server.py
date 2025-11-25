"""
Script simple para arrancar el servidor FastAPI
"""
import sys
import os

# Agregar la carpeta actual al path de Python
sys.path.insert(0, os.path.dirname(__file__))

# Ahora importar uvicorn y arrancar
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
