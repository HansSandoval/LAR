import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "gestion_rutas")

def check_integrity():
    try:
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            database=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD
        )
        # Force LATIN1 just to be able to read names if they have accents
        conn.set_client_encoding('LATIN1')
        cur = conn.cursor()

        print("--- Checking Foreign Keys ---")
        
        # Check Zona 1
        cur.execute("SELECT id_zona, nombre_zona FROM zona WHERE id_zona = 1")
        zona = cur.fetchone()
        if zona:
            print(f"✅ Zona 1 exists: {zona}")
        else:
            print(f"❌ Zona 1 DOES NOT EXIST")

        # Check Turno 1
        cur.execute("SELECT id_turno, nombre_turno FROM turno WHERE id_turno = 1")
        turno = cur.fetchone()
        if turno:
            print(f"✅ Turno 1 exists: {turno}")
        else:
            print(f"❌ Turno 1 DOES NOT EXIST")

        conn.close()

    except Exception as e:
        print(f"Error checking integrity: {e}")

if __name__ == "__main__":
    check_integrity()
