from fastapi import FastAPI
from routers import ruta

app = FastAPI()

# Incluir routers
app.include_router(ruta.router)

@app.get("/")
def read_root():
    return {"mensaje": "🚀 API de gestión de rutas funcionando!"}

