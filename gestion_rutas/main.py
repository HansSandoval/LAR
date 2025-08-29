from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"mensaje": "🚀 API de gestión de rutas funcionando!"}

@app.get("/ruta/{id}")
def obtener_ruta(id: int):
    return {"ruta_id": id, "detalle": "Aquí irán los datos de la ruta"}
