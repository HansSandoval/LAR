import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from models.models import Base

# Cargar variables de entorno
load_dotenv()

# Configuración de base de datos
ENV = os.getenv("ENVIRONMENT", "development")
DATABASE_URL = os.getenv("DATABASE_URL")

# Si no hay URL configurada, usar conexión por defecto
if not DATABASE_URL:
    if ENV == "production":
        # PostgreSQL para producción
        DB_USER = os.getenv("DB_USER", "postgres")
        DB_PASSWORD = os.getenv("DB_PASSWORD", "hanskawaii1")
        DB_HOST = os.getenv("DB_HOST", "localhost")
        DB_PORT = os.getenv("DB_PORT", "5432")
        DB_NAME = os.getenv("DB_NAME", "gestion_rutas")
        DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    else:
        # SQLite para desarrollo
        DATABASE_URL = "sqlite:///./gestion_rutas.db"

# Crear engine
if "sqlite" in DATABASE_URL:
    engine = create_engine(
        DATABASE_URL, 
        connect_args={"check_same_thread": False},
        echo=ENV == "development"
    )
else:
    engine = create_engine(DATABASE_URL, echo=ENV == "development")

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
    """Eliminar todas las tablas (solo desarrollo)"""
    if ENV == "development":
        Base.metadata.drop_all(bind=engine)
