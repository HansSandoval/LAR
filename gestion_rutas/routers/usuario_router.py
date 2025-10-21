"""
Router para gestionar operaciones CRUD en la tabla Usuario.
Endpoints para crear, listar, actualizar y eliminar usuarios con roles.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..database.db import get_db
from ..models.models import Usuario
from ..schemas.schemas import (
    UsuarioCreate,
    UsuarioUpdate,
    UsuarioResponse
)
import re

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])


def validar_email(email: str) -> bool:
    """Valida que el email tenga formato correcto."""
    patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(patron, email) is not None


def validar_password(password: str) -> bool:
    """Valida que la contraseña sea fuerte (mínimo 8 caracteres)."""
    return len(password) >= 8


@router.get(
    "/",
    response_model=dict,
    summary="Listar todos los usuarios con paginación y filtros",
    description="Retorna una lista paginada de usuarios con opciones de filtrado por rol y estado"
)
async def get_usuarios(
    skip: int = Query(0, ge=0, description="Número de registros a saltar"),
    limit: int = Query(10, ge=1, le=100, description="Número máximo de registros a retornar"),
    rol: str = Query(None, description="Filtrar por rol (admin, operador, gerente, visualizador)"),
    activo: bool = Query(None, description="Filtrar por estado activo/inactivo"),
    nombre: str = Query(None, description="Filtrar por nombre (búsqueda parcial)"),
    db: Session = Depends(get_db)
):
    """
    Obtiene una lista paginada de usuarios con filtros opcionales.
    
    **Parámetros de filtrado:**
    - `rol`: Filtra por rol del usuario (admin, operador, gerente, visualizador)
    - `activo`: Filtra usuarios activos (true) o inactivos (false)
    - `nombre`: Busca usuarios cuyo nombre contenga el texto especificado
    
    **Ejemplo de uso:**
    ```
    GET /usuarios/?skip=0&limit=10&rol=operador&activo=true
    ```
    """
    try:
        query = db.query(Usuario)
        
        # Aplicar filtros
        if rol:
            query = query.filter(Usuario.rol == rol)
        if activo is not None:
            query = query.filter(Usuario.activo == activo)
        if nombre:
            query = query.filter(Usuario.nombre.ilike(f"%{nombre}%"))
        
        # Obtener total
        total = query.count()
        
        # Aplicar paginación
        usuarios = query.offset(skip).limit(limit).all()
        
        return {
            "data": [UsuarioResponse.from_orm(u) for u in usuarios],
            "total": total,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar usuarios: {str(e)}")


@router.get(
    "/{usuario_id}",
    response_model=UsuarioResponse,
    summary="Obtener un usuario por ID",
    description="Retorna los detalles de un usuario específico"
)
async def get_usuario(usuario_id: int, db: Session = Depends(get_db)):
    """
    Obtiene los detalles de un usuario específico por su ID.
    
    **Ejemplo de uso:**
    ```
    GET /usuarios/1
    ```
    """
    try:
        usuario = db.query(Usuario).filter(Usuario.id_usuario == usuario_id).first()
        if not usuario:
            raise HTTPException(status_code=404, detail=f"Usuario con ID {usuario_id} no encontrado")
        return UsuarioResponse.from_orm(usuario)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener usuario: {str(e)}")


@router.post(
    "/",
    response_model=UsuarioResponse,
    status_code=201,
    summary="Crear un nuevo usuario",
    description="Crea un nuevo registro de usuario con contraseña encriptada"
)
async def create_usuario(usuario: UsuarioCreate, db: Session = Depends(get_db)):
    """
    Crea un nuevo usuario.
    
    **Validaciones:**
    - El email debe tener formato válido
    - El email debe ser único
    - La contraseña debe tener mínimo 8 caracteres
    - El rol debe ser válido
    
    **Roles válidos:** admin, operador, gerente, visualizador
    
    **Ejemplo de payload:**
    ```json
    {
        "nombre": "Juan Pérez",
        "correo": "juan.perez@example.com",
        "rol": "operador",
        "password": "MiPassword123"
    }
    ```
    """
    try:
        # Validar email
        if not validar_email(usuario.correo):
            raise HTTPException(status_code=400, detail="Email no tiene formato válido")
        
        # Validar que el email es único
        usuario_existente = db.query(Usuario).filter(Usuario.correo == usuario.correo).first()
        if usuario_existente:
            raise HTTPException(status_code=400, detail="El email ya está registrado")
        
        # Validar password
        if not validar_password(usuario.password):
            raise HTTPException(status_code=400, detail="La contraseña debe tener mínimo 8 caracteres")
        
        # Validar rol
        roles_validos = ["admin", "operador", "gerente", "visualizador"]
        if usuario.rol not in roles_validos:
            raise HTTPException(status_code=400, detail=f"Rol inválido. Debe ser uno de: {', '.join(roles_validos)}")
        
        # Encriptar contraseña (en producción usar bcrypt o similar)
        from hashlib import sha256
        hash_password = sha256(usuario.password.encode()).hexdigest()
        
        nuevo_usuario = Usuario(
            nombre=usuario.nombre,
            correo=usuario.correo,
            rol=usuario.rol,
            hash_password=hash_password,
            activo=True
        )
        db.add(nuevo_usuario)
        db.commit()
        db.refresh(nuevo_usuario)
        return UsuarioResponse.from_orm(nuevo_usuario)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al crear usuario: {str(e)}")


@router.put(
    "/{usuario_id}",
    response_model=UsuarioResponse,
    summary="Actualizar un usuario",
    description="Actualiza los datos de un usuario existente"
)
async def update_usuario(
    usuario_id: int,
    usuario_data: UsuarioUpdate,
    db: Session = Depends(get_db)
):
    """
    Actualiza un usuario existente.
    
    **Ejemplo de uso:**
    ```
    PUT /usuarios/1
    ```
    
    **Ejemplo de payload:**
    ```json
    {
        "nombre": "Juan Pérez García",
        "rol": "gerente"
    }
    ```
    """
    try:
        usuario = db.query(Usuario).filter(Usuario.id_usuario == usuario_id).first()
        if not usuario:
            raise HTTPException(status_code=404, detail=f"Usuario con ID {usuario_id} no encontrado")
        
        # Validar email si se cambia
        if usuario_data.correo and usuario_data.correo != usuario.correo:
            if not validar_email(usuario_data.correo):
                raise HTTPException(status_code=400, detail="Email no tiene formato válido")
            
            usuario_existente = db.query(Usuario).filter(Usuario.correo == usuario_data.correo).first()
            if usuario_existente:
                raise HTTPException(status_code=400, detail="El email ya está registrado por otro usuario")
        
        # Validar rol si se cambia
        if usuario_data.rol:
            roles_validos = ["admin", "operador", "gerente", "visualizador"]
            if usuario_data.rol not in roles_validos:
                raise HTTPException(status_code=400, detail=f"Rol inválido. Debe ser uno de: {', '.join(roles_validos)}")
        
        # Validar password si se proporciona
        if usuario_data.password:
            if not validar_password(usuario_data.password):
                raise HTTPException(status_code=400, detail="La contraseña debe tener mínimo 8 caracteres")
            
            from hashlib import sha256
            usuario.hash_password = sha256(usuario_data.password.encode()).hexdigest()
        
        # Actualizar campos
        if usuario_data.nombre:
            usuario.nombre = usuario_data.nombre
        if usuario_data.correo:
            usuario.correo = usuario_data.correo
        if usuario_data.rol:
            usuario.rol = usuario_data.rol
        if usuario_data.activo is not None:
            usuario.activo = usuario_data.activo
        
        db.commit()
        db.refresh(usuario)
        return UsuarioResponse.from_orm(usuario)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al actualizar usuario: {str(e)}")


@router.delete(
    "/{usuario_id}",
    status_code=204,
    summary="Eliminar un usuario",
    description="Elimina un usuario de la base de datos (desactivación lógica recomendada)"
)
async def delete_usuario(usuario_id: int, db: Session = Depends(get_db)):
    """
    Elimina un usuario de la base de datos.
    
    **Advertencia:** Esta operación no se puede deshacer.
    **Recomendación:** Considerar usar PATCH para desactivar el usuario en lugar de eliminarlo.
    
    **Ejemplo de uso:**
    ```
    DELETE /usuarios/1
    ```
    """
    try:
        usuario = db.query(Usuario).filter(Usuario.id_usuario == usuario_id).first()
        if not usuario:
            raise HTTPException(status_code=404, detail=f"Usuario con ID {usuario_id} no encontrado")
        
        db.delete(usuario)
        db.commit()
        return None
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al eliminar usuario: {str(e)}")


@router.patch(
    "/{usuario_id}/estado",
    response_model=UsuarioResponse,
    summary="Cambiar estado del usuario",
    description="Activa o desactiva un usuario (alternativa a eliminación)"
)
async def update_usuario_estado(
    usuario_id: int,
    activo: bool = Query(..., description="Estado del usuario (true=activo, false=inactivo)"),
    db: Session = Depends(get_db)
):
    """
    Cambia el estado de un usuario entre activo e inactivo.
    
    **Ejemplo de uso:**
    ```
    PATCH /usuarios/1/estado?activo=false
    ```
    """
    try:
        usuario = db.query(Usuario).filter(Usuario.id_usuario == usuario_id).first()
        if not usuario:
            raise HTTPException(status_code=404, detail=f"Usuario con ID {usuario_id} no encontrado")
        
        usuario.activo = activo
        db.commit()
        db.refresh(usuario)
        return UsuarioResponse.from_orm(usuario)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al actualizar estado: {str(e)}")


@router.patch(
    "/{usuario_id}/cambiar-password",
    summary="Cambiar contraseña del usuario",
    description="Actualiza la contraseña de un usuario"
)
async def cambiar_password(
    usuario_id: int,
    password_actual: str = Query(..., description="Contraseña actual del usuario"),
    password_nueva: str = Query(..., description="Nueva contraseña"),
    db: Session = Depends(get_db)
):
    """
    Cambia la contraseña de un usuario verificando la contraseña actual.
    
    **Validaciones:**
    - La contraseña actual debe ser correcta
    - La nueva contraseña debe tener mínimo 8 caracteres
    
    **Ejemplo de uso:**
    ```
    PATCH /usuarios/1/cambiar-password?password_actual=OldPass123&password_nueva=NewPass456
    ```
    """
    try:
        usuario = db.query(Usuario).filter(Usuario.id_usuario == usuario_id).first()
        if not usuario:
            raise HTTPException(status_code=404, detail=f"Usuario con ID {usuario_id} no encontrado")
        
        # Validar contraseña actual
        from hashlib import sha256
        hash_actual = sha256(password_actual.encode()).hexdigest()
        if hash_actual != usuario.hash_password:
            raise HTTPException(status_code=401, detail="Contraseña actual incorrecta")
        
        # Validar nueva contraseña
        if not validar_password(password_nueva):
            raise HTTPException(status_code=400, detail="La nueva contraseña debe tener mínimo 8 caracteres")
        
        # Actualizar contraseña
        usuario.hash_password = sha256(password_nueva.encode()).hexdigest()
        db.commit()
        
        return {"mensaje": "Contraseña actualizada exitosamente"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al cambiar contraseña: {str(e)}")


@router.get(
    "/rol/{rol_id}",
    response_model=dict,
    summary="Listar usuarios por rol",
    description="Retorna todos los usuarios que tienen un rol específico"
)
async def get_usuarios_por_rol(
    rol_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Obtiene todos los usuarios que tienen un rol específico.
    
    **Roles válidos:** admin, operador, gerente, visualizador
    
    **Ejemplo de uso:**
    ```
    GET /usuarios/rol/operador?skip=0&limit=10
    ```
    """
    try:
        roles_validos = ["admin", "operador", "gerente", "visualizador"]
        if rol_id not in roles_validos:
            raise HTTPException(status_code=400, detail=f"Rol inválido. Debe ser uno de: {', '.join(roles_validos)}")
        
        query = db.query(Usuario).filter(Usuario.rol == rol_id)
        total = query.count()
        usuarios = query.offset(skip).limit(limit).all()
        
        return {
            "rol": rol_id,
            "data": [UsuarioResponse.from_orm(u) for u in usuarios],
            "total": total,
            "skip": skip,
            "limit": limit
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar usuarios por rol: {str(e)}")
