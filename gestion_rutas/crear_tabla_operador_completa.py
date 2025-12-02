import sys
import os

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gestion_rutas.database.db import PostgresDB
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def crear_tabla_operador():
    db = PostgresDB()
    conn = db.get_connection()
    if not conn:
        logger.error("No se pudo conectar a la base de datos")
        return

    try:
        with conn.cursor() as cur:
            # Create table if not exists
            cur.execute("""
                CREATE TABLE IF NOT EXISTS operador (
                    id_operador SERIAL PRIMARY KEY,
                    nombre VARCHAR(100) NOT NULL,
                    cedula VARCHAR(20) UNIQUE NOT NULL,
                    especialidad VARCHAR(50),
                    id_usuario INTEGER REFERENCES usuario(id_usuario)
                );
            """)
            conn.commit()
            logger.info("Tabla 'operador' creada o verificada correctamente.")
            
            # Check if columns exist (in case table existed but with different schema)
            cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'operador'")
            columns = [row[0] for row in cur.fetchall()]
            
            if 'id_usuario' not in columns:
                logger.info("Agregando columna id_usuario...")
                cur.execute("ALTER TABLE operador ADD COLUMN id_usuario INTEGER REFERENCES usuario(id_usuario)")
                conn.commit()
                
            if 'especialidad' not in columns:
                logger.info("Agregando columna especialidad...")
                cur.execute("ALTER TABLE operador ADD COLUMN especialidad VARCHAR(50)")
                conn.commit()

    except Exception as e:
        conn.rollback()
        logger.error(f"Error al crear tabla: {e}")
    finally:
        db.return_connection(conn)

if __name__ == "__main__":
    crear_tabla_operador()
