from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from gestion_rutas.models.models import Base  # Ajusta el import si el nombre de la carpeta/archivo es diferente

DB_USER = "postgres"           # Cambia si usas otro usuario
DB_PASSWORD = "hanskawaii1"  # Tu clave de PostgreSQL
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "gestion_rutas"

DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL, echo=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)
