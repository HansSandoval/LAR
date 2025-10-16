from fastapi import FastAPI
from routers import rutas

app = FastAPI()

# Incluir routers
app.include_router(rutas.router)

@app.get("/")
def read_root():
    return {"mensaje": "🚀 API de gestión de rutas funcionando!"}
