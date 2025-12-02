from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from ..schemas.schemas import OperadorCreate, OperadorUpdate, OperadorResponse
from ..service.operador_service import OperadorService

router = APIRouter(prefix="/operadores", tags=["Operadores"])
operador_service = OperadorService()

@router.post("/", response_model=OperadorResponse, summary="Crear nuevo operador")
async def crear_operador(operador: OperadorCreate):
    """Crear un nuevo operador"""
    if operador.email:
        existing = operador_service.obtener_operador_por_email(operador.email)
        if existing:
            raise HTTPException(status_code=400, detail="Ya existe un operador con ese email")
    
    nuevo_operador = operador_service.crear_operador(
        nombre=operador.nombre,
        email=operador.email,
        telefono=operador.telefono,
        estado=operador.estado,
        id_usuario=operador.id_usuario
    )
    return nuevo_operador

@router.get("/", response_model=List[OperadorResponse], summary="Listar operadores")
async def listar_operadores(skip: int = 0, limit: int = 100):
    """Listar todos los operadores"""
    return operador_service.listar_operadores(skip, limit)

@router.get("/{operador_id}", response_model=OperadorResponse, summary="Obtener operador por ID")
async def obtener_operador(operador_id: int):
    """Obtener un operador específico"""
    operador = operador_service.obtener_operador(operador_id)
    if not operador:
        raise HTTPException(status_code=404, detail="Operador no encontrado")
    return operador

@router.put("/{operador_id}", response_model=OperadorResponse, summary="Actualizar operador")
async def actualizar_operador(operador_id: int, operador: OperadorUpdate):
    """Actualizar un operador existente"""
    existing = operador_service.obtener_operador(operador_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Operador no encontrado")
    
    datos_actualizar = {k: v for k, v in operador.dict(exclude_unset=True).items()}
    updated_operador = operador_service.actualizar_operador(operador_id, datos_actualizar)
    return updated_operador

@router.delete("/{operador_id}", summary="Eliminar operador")
async def eliminar_operador(operador_id: int):
    """Eliminar un operador"""
    existing = operador_service.obtener_operador(operador_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Operador no encontrado")
    
    try:
        operador_service.eliminar_operador(operador_id)
    except Exception as e:
        error_msg = str(e).lower()
        if "foreign key" in error_msg or "constraint" in error_msg:
            raise HTTPException(
                status_code=400, 
                detail="No se puede eliminar el operador porque tiene registros asociados (rutas, vehículos, etc.)."
            )
        raise HTTPException(status_code=500, detail="Error interno al eliminar operador")
    return {"mensaje": "Operador eliminado exitosamente"}
