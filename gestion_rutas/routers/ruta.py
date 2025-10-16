from fastapi import APIRouter

router = APIRouter(
    prefix="/rutas",      
    tags=["Rutas"]        
)

@router.get("/{id}")
def obtener_ruta(id: int):
    return {"ruta_id": id, "detalle": "Aquí irán los datos de la ruta"}
