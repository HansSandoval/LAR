import os
import json
import psycopg2
from dotenv import load_dotenv

load_dotenv()

POSTGRES_USER = os.getenv("POSTGRES_USER") or os.getenv("DB_USER") or "postgres"
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD") or os.getenv("DB_PASSWORD") or "postgres"
POSTGRES_HOST = os.getenv("POSTGRES_HOST") or os.getenv("DB_HOST") or "localhost"
POSTGRES_PORT = os.getenv("POSTGRES_PORT") or os.getenv("DB_PORT") or "5432"
# Force the DB name that works in the app
POSTGRES_DB = "gestion_rutas"

def reproduce_crash():
    try:
        # Read the payload
        with open("debug_payload_last_attempt.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        
        print(f"Payload loaded. User: {POSTGRES_USER}, DB: {POSTGRES_DB}")
        
        # Pass client_encoding in options to ensure it's set from the start
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            database=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            options="-c client_encoding=LATIN1"
        )
        
        # conn.set_client_encoding('LATIN1') # Already set via options
        cur = conn.cursor()

        print("Attempting INSERT with LATIN1 encoding...")

        query = """
            INSERT INTO ruta_planificada 
            (id_zona, id_turno, fecha, secuencia_puntos, 
             distancia_km, tiempo_estimado_min, version_modelo_vrp, geometria_json)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id_ruta
        """
        
        # Reconstruct arguments from payload
        # Note: secuencia_puntos in payload is just length, we need to fake it or use empty list if we don't have it.
        # Wait, the payload dump only saved the length of secuencia_puntos!
        # "secuencia_puntos_len": 23
        # I need to pass a valid JSON array. I'll pass an empty list or a dummy list of that length.
        # The error might be related to the content of the list if it's a FK check, but usually JSON columns don't enforce FKs inside the JSON unless there are triggers.
        
        # Let's try with a dummy list of integers.
        secuencia_puntos = [1] * data.get("secuencia_puntos_len", 0)
        secuencia_str = json.dumps(secuencia_puntos)
        
        # Geometry
        # The payload has "geometria_sample". I'll use that or a dummy.
        # "geometria_json_len": 13
        geometria_json = [[-20.0, -70.0]] * data.get("geometria_json_len", 0)
        geometria_str = json.dumps(geometria_json)

        args = (
            data["id_zona"],
            data["id_turno"],
            data["fecha"],
            secuencia_str,
            data["distancia_km"],
            data["tiempo_estimado_min"],
            data["version_modelo_vrp"],
            geometria_str
        )

        cur.execute(query, args)
        conn.commit()
        print("✅ INSERT SUCCESSFUL! (This is unexpected if we are reproducing a crash)")
        
        conn.close()

    except psycopg2.Error as e:
        print("\n🔥 CAUGHT POSTGRES ERROR (Decoded with LATIN1):")
        print(f"Message: {e.pgerror}")
        print(f"Code: {e.pgcode}")
    except UnicodeDecodeError as ude:
        print(f"\n💀 CAUGHT UnicodeDecodeError:")
        print(f"Reason: {ude.reason}")
        print(f"Object (bytes): {ude.object}")
        print(f"Start/End: {ude.start}-{ude.end}")
    except Exception as e:
        print(f"\n❌ OTHER ERROR: {type(e).__name__}: {e}")

if __name__ == "__main__":
    reproduce_crash()
