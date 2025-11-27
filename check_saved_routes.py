import requests
import json

try:
    # Listar rutas
    response = requests.get("http://localhost:8000/rutas-planificadas/")
    if response.status_code == 200:
        rutas = response.json()
        print(f"✅ Se encontraron {len(rutas)} rutas guardadas.")
        if rutas:
            print("Ejemplo de ruta (ID, Fecha, Zona):")
            r = rutas[0]
            print(f"ID: {r.get('id_ruta') or r.get('id_ruta_planificada')}")
            print(f"Fecha: {r.get('fecha') or r.get('fecha_planificacion')}")
            print(f"Geometria presente: {'geometria_json' in r and r['geometria_json'] is not None}")
            
            # Si hay geometria, mostrar primer punto
            if r.get('geometria_json'):
                print(f"Primer punto geometria: {r['geometria_json'][0]}")
    else:
        print(f"❌ Error al listar rutas: {response.status_code} - {response.text}")

except Exception as e:
    print(f"❌ Error de conexión: {e}")
