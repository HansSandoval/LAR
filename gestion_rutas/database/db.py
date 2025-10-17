from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from gestion_rutas.models.models import Base  

DB_USER = "postgres"           
DB_PASSWORD = "hanskawaii1"  
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "gestion_rutas"

DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL, echo=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)
