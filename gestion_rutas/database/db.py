import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from ..models.models import Base

# Cargar variables de entorno
load_dotenv()

# PostgreSQL 17 - Configuración para Iquique
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "gestion_rutas")

# URL de conexión PostgreSQL
DATABASE_URL = f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}?client_encoding=utf8"

print(f"[DB] Usando PostgreSQL: {POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}")

# Crear engine de PostgreSQL con manejo de encoding UTF-8
engine = create_engine(
    DATABASE_URL, 
    echo=False, 
    pool_pre_ping=True, 
    pool_size=10,
    connect_args={'application_name': 'gestion_rutas', 'options': '-c client_encoding=utf8'}
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependencia para inyectar sesiones en FastAPI
def get_db():
    """Obtener sesión de base de datos para usar en endpoints"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Crear todas las tablas en la base de datos"""
    Base.metadata.create_all(bind=engine)

def drop_db():
    """Eliminar todas las tablas de la base de datos"""
    Base.metadata.drop_all(bind=engine)
