import logging
from gestion_rutas.database.db import PostgresDB

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def actualizar_tabla_operador():
    """
    Agrega la columna id_usuario a la tabla operador y establece la llave foránea.
    """
    db = PostgresDB()
    conn = db.get_connection()
    
    if not conn:
        logger.error("No se pudo conectar a la base de datos.")
        return

    try:
        cursor = conn.cursor()
        
        # 1. Agregar columna id_usuario si no existe
        logger.info("Agregando columna id_usuario a tabla operador...")
        cursor.execute("""
            ALTER TABLE operador 
            ADD COLUMN IF NOT EXISTS id_usuario INTEGER;
        """)
        
        # 2. Agregar constraint de llave foránea
        # Primero verificamos si ya existe para evitar errores
        cursor.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_operador_usuario') THEN
                    ALTER TABLE operador 
                    ADD CONSTRAINT fk_operador_usuario 
                    FOREIGN KEY (id_usuario) 
                    REFERENCES usuario(id_usuario);
                END IF;
            END
            $$;
        """)
        
        conn.commit()
        logger.info(" Tabla operador actualizada exitosamente.")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error al actualizar tabla: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    actualizar_tabla_operador()
