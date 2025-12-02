"""
Script de inicio para el servidor FastAPI
Ejecuta desde la raíz del proyecto para resolver importaciones correctamente
"""

import sys
from pathlib import Path

# Agregar el directorio raíz al path
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

# Ahora importar y ejecutar uvicorn
import uvicorn

if __name__ == "__main__":
    print(" Iniciando servidor FastAPI con Sistema Multi-Agente (MAS)")
    print(" URL: http://localhost:8000")
    print(" Docs: http://localhost:8000/docs")
    print(" Mapa MAS: http://localhost:8000/static/mapa_mas_tiempo_real.html")
    print("")
    
    uvicorn.run(
        "gestion_rutas.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=[str(root_dir / "gestion_rutas")],
        log_level="info"
    )
