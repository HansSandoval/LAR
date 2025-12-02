import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "gestion_rutas")

SQLALCHEMY_DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
SQLITE_DATABASE_URL = "sqlite:///./gestion_rutas_local.db"

Base = declarative_base()

engine = None
SessionLocal = None

try:
    # Intentar conectar a PostgreSQL
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    # Test connection
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
        logger.info(f"Conectado exitosamente a PostgreSQL: {POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}")
except Exception as e:
    error_msg = str(e)
    try:
        # Intentar decodificar si es bytes
        if isinstance(e, bytes):
            error_msg = e.decode('utf-8', errors='replace')
    except:
        pass
    logger.warning(f"No se pudo conectar a PostgreSQL: {error_msg}")
    logger.warning("Activando modo fallback: SQLite local")
    engine = create_engine(
        SQLITE_DATABASE_URL, connect_args={"check_same_thread": False}
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Inicializar la base de datos (crear tablas)"""
    # Importar modelos aquí para evitar importaciones circulares al inicio
    try:
        from ..models import base
    except ImportError as e:
        logger.error(f"Error importando models.base: {e}")
    
    try:
        from ..models import models
        # Importar la Base de models.models para crear sus tablas también
        from ..models.models import Base as LegacyBase
        logger.info("Creando tablas legacy (models.models)...")
        LegacyBase.metadata.create_all(bind=engine)
    except ImportError as e:
        logger.warning(f"No se pudieron importar/crear tablas legacy: {e}")
    
    logger.info("Creando tablas en la base de datos...")
    Base.metadata.create_all(bind=engine)
    logger.info("Tablas creadas exitosamente.")

# ============================================================================
# Funciones Helper para compatibilidad con código legacy (Raw SQL)
# ============================================================================

def get_connection():
    """Obtener una conexión raw (DBAPI)"""
    return engine.raw_connection()

def execute_query(query, params=None, fetch=True):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        
        # Adaptar placeholders para SQLite
        is_sqlite = "sqlite" in str(engine.url)
        if is_sqlite and params:
            # Fix for OFFSET ... LIMIT syntax which is invalid in SQLite
            # Postgres: OFFSET 10 LIMIT 5 (params: offset, limit)
            # SQLite: LIMIT 5 OFFSET 10 (params: limit, offset)
            
            # Caso 1: OFFSET %s LIMIT %s
            if "OFFSET %s LIMIT %s" in query:
                query = query.replace("OFFSET %s LIMIT %s", "LIMIT %s OFFSET %s")
                # Swap the last two parameters (offset, limit) -> (limit, offset)
                if isinstance(params, (list, tuple)) and len(params) >= 2:
                    params = list(params)
                    # Intercambiar los dos últimos elementos
                    params[-2], params[-1] = params[-1], params[-2]
                    params = tuple(params)
            
            # Caso 2: OFFSET ? LIMIT ? (si ya se reemplazó %s por ?)
            elif "OFFSET ? LIMIT ?" in query:
                query = query.replace("OFFSET ? LIMIT ?", "LIMIT ? OFFSET ?")
                if isinstance(params, (list, tuple)) and len(params) >= 2:
                    params = list(params)
                    params[-2], params[-1] = params[-1], params[-2]
                    params = tuple(params)

            query = query.replace("%s", "?")
            
        cursor.execute(query, params or ())
        
        if fetch:
            if cursor.description:
                columns = [col[0] for col in cursor.description]
                results = [dict(zip(columns, row)) for row in cursor.fetchall()]
                return results
            return []
        return None
    finally:
        conn.close()

def execute_query_one(query, params=None):
    results = execute_query(query, params, fetch=True)
    return results[0] if results else None

def execute_insert_update_delete(query, params=None):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        is_sqlite = "sqlite" in str(engine.url)
        if is_sqlite and params:
            query = query.replace("%s", "?")
            
        cursor.execute(query, params or ())
        conn.commit()
        return cursor.rowcount
    finally:
        conn.close()

def execute_insert_returning(query, params=None):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        is_sqlite = "sqlite" in str(engine.url)
        
        if is_sqlite:
            if params:
                query = query.replace("%s", "?")
            # Strip RETURNING
            if "RETURNING" in query:
                query_clean = query.split("RETURNING")[0]
            else:
                query_clean = query
                
            cursor.execute(query_clean, params or ())
            conn.commit()
            last_id = cursor.lastrowid
            return {"id": last_id} # Basic return
        else:
            cursor.execute(query, params or ())
            conn.commit()
            if cursor.description:
                columns = [col[0] for col in cursor.description]
                row = cursor.fetchone()
                return dict(zip(columns, row)) if row else None
            return None
    finally:
        conn.close()
