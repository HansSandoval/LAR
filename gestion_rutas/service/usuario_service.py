"""
Service Layer para Usuarios - PostgreSQL Directo
"""

from typing import List, Optional, Dict, Any
from ..database.db import execute_query, execute_query_one, execute_insert_returning, execute_insert_update_delete
import logging
from hashlib import sha256

logger = logging.getLogger(__name__)


class UsuarioService:
    """Servicio para operaciones con Usuarios"""

    @staticmethod
    def crear_usuario(
        nombre: str,
        correo: str,
        rol: str,
        password: str,
        activo: bool = True
    ) -> Optional[Dict]:
        """Crear nuevo usuario"""
        try:
            hash_password = sha256(password.encode()).hexdigest()
            query = """
                INSERT INTO usuario (nombre, correo, rol, hash_password, activo)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id_usuario, nombre, correo, rol, activo
            """
            resultado = execute_insert_returning(query, (nombre, correo, rol, hash_password, activo))
            if resultado:
                logger.info(f"Usuario {resultado.get('id_usuario')} creado: {correo}")
            return resultado
        except Exception as e:
            logger.error(f"Error al crear usuario: {str(e)}")
            raise

    @staticmethod
    def obtener_usuario(usuario_id: int) -> Optional[Dict]:
        """Obtener usuario por ID"""
        query = "SELECT id_usuario, nombre, correo, rol, activo FROM usuario WHERE id_usuario = %s"
        return execute_query_one(query, (usuario_id,))

    @staticmethod
    def obtener_usuario_por_correo(correo: str) -> Optional[Dict]:
        """Obtener usuario por correo"""
        query = "SELECT id_usuario, nombre, correo, rol, activo FROM usuario WHERE correo = %s"
        return execute_query_one(query, (correo,))

    @staticmethod
    def obtener_usuarios(
        rol: Optional[str] = None,
        activo: Optional[bool] = None,
        nombre: Optional[str] = None,
        skip: int = 0,
        limit: int = 10
    ) -> tuple[List[Dict], int]:
        """Obtener usuarios con filtros"""
        conditions = []
        params = []
        
        if rol:
            conditions.append("rol = %s")
            params.append(rol)
        if activo is not None:
            conditions.append("activo = %s")
            params.append(activo)
        if nombre:
            conditions.append("nombre ILIKE %s")
            params.append(f"%{nombre}%")
        
        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
        
        params.extend([skip, limit])
        query = f"SELECT id_usuario, nombre, correo, rol, activo FROM usuario{where_clause} ORDER BY id_usuario OFFSET %s LIMIT %s"
        usuarios = execute_query(query, tuple(params))
        
        count_query = f"SELECT COUNT(*) as total FROM usuario{where_clause}"
        count_result = execute_query_one(count_query, tuple(params[:-2]) if conditions else ())
        total = count_result['total'] if count_result else 0
        
        return usuarios, total

    @staticmethod
    def actualizar_usuario(usuario_id: int, datos: Dict[str, Any]) -> Optional[Dict]:
        """Actualizar datos de un usuario"""
        campos = []
        valores = []
        
        for key, value in datos.items():
            if value is not None:
                if key == 'password':
                    campos.append("hash_password = %s")
                    valores.append(sha256(value.encode()).hexdigest())
                else:
                    campos.append(f"{key} = %s")
                    valores.append(value)
        
        if not campos:
            return UsuarioService.obtener_usuario(usuario_id)
        
        valores.append(usuario_id)
        query = f"UPDATE usuario SET {', '.join(campos)} WHERE id_usuario = %s RETURNING id_usuario, nombre, correo, rol, activo"
        return execute_insert_returning(query, tuple(valores))

    @staticmethod
    def cambiar_estado_usuario(usuario_id: int, activo: bool) -> Optional[Dict]:
        """Cambiar estado del usuario (activar/desactivar)"""
        query = "UPDATE usuario SET activo = %s WHERE id_usuario = %s RETURNING id_usuario, nombre, correo, rol, activo"
        return execute_insert_returning(query, (activo, usuario_id))

    @staticmethod
    def eliminar_usuario(usuario_id: int) -> bool:
        """Eliminar un usuario"""
        query = "DELETE FROM usuario WHERE id_usuario = %s"
        resultado = execute_insert_update_delete(query, (usuario_id,))
        return resultado > 0

    @staticmethod
    def validar_credenciales(correo: str, password: str) -> Optional[Dict]:
        """Validar credenciales de usuario"""
        usuario = UsuarioService.obtener_usuario_por_correo(correo)
        if not usuario:
            return None
        
        hash_password = sha256(password.encode()).hexdigest()
        query = "SELECT id_usuario, nombre, correo, rol, activo FROM usuario WHERE correo = %s AND hash_password = %s AND activo = true"
        return execute_query_one(query, (correo, hash_password))
