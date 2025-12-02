import os
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

# Dummy Base class for backward compatibility with old ORM models
# (not used anymore - we use PostgreSQL direct queries now)
class Base:
    pass

# PostgreSQL 17 - Configuración para Iquique
# Intentar leer variables con prefijo POSTGRES_ y si no, DB_ (compatibilidad con .env)
POSTGRES_USER = os.getenv("POSTGRES_USER") or os.getenv("DB_USER") or "postgres"
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD") or os.getenv("DB_PASSWORD") or "postgres"
POSTGRES_HOST = os.getenv("POSTGRES_HOST") or os.getenv("DB_HOST") or "localhost"
POSTGRES_PORT = os.getenv("POSTGRES_PORT") or os.getenv("DB_PORT") or "5432"
POSTGRES_DB = os.getenv("POSTGRES_DB") or os.getenv("DB_NAME") or "gestion_rutas"

print(f"[DB] Usando PostgreSQL directo: {POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}")


class PostgresDB:
    
    def __init__(self):
        self.host = POSTGRES_HOST
        self.port = POSTGRES_PORT
        self.database = POSTGRES_DB
        self.user = POSTGRES_USER
        self.password = POSTGRES_PASSWORD
    
    def get_connection(self):
        """Obtiene conexión a PostgreSQL"""
        try:
            # Conectar usando configuración estándar
            # Usamos options='-c client_encoding=LATIN1' para asegurar que incluso los mensajes
            # de error de conexión (FATAL) se puedan decodificar si vienen en español/win1252.
            conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
                options="-c client_encoding=LATIN1"
            )
            # Ya no es necesario set_client_encoding explícito si se pasa en options,
            # pero lo dejamos por seguridad o lo quitamos.
            # conn.set_client_encoding('UTF8') <--- NO USAR UTF8 si el servidor manda basura
            return conn
        except psycopg2.Error as e:
            logger.error(f"Error conectando a PostgreSQL: {e}")
            raise
    
    @contextmanager
    def get_cursor(self, commit=True):
        """Context manager para cursor con auto-commit/rollback"""
        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            yield cursor
            if commit:
                conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Error en transacción: {e}")
            raise
        finally:
            cursor.close()
            conn.close()


# Instancia global
db = PostgresDB()


def execute_query(query, params=None, fetch=True):
    """Ejecutar query SELECT - retorna lista de dicts"""
    with db.get_cursor(commit=False) as cursor:
        cursor.execute(query, params or ())
        if fetch:
            resultados = cursor.fetchall()
            return [dict(row) for row in resultados]
        return None


def execute_query_one(query, params=None):
    """Ejecutar query SELECT - retorna un dict o None"""
    with db.get_cursor(commit=False) as cursor:
        cursor.execute(query, params or ())
        resultado = cursor.fetchone()
        return dict(resultado) if resultado else None


def execute_insert_update_delete(query, params=None):
    """Ejecutar INSERT/UPDATE/DELETE - retorna filas afectadas"""
    with db.get_cursor() as cursor:
        cursor.execute(query, params or ())
        return cursor.rowcount


def execute_insert_returning(query, params=None):
    """Ejecutar INSERT con RETURNING - retorna el registro insertado"""
    with db.get_cursor() as cursor:
        cursor.execute(query, params or ())
        resultado = cursor.fetchone()
        return dict(resultado) if resultado else None
