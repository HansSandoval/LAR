"""
Script para probar el endpoint de rutas con calles
Espera a que el servidor esté listo
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

print("=" * 60)
print("ESPERANDO A QUE LA API ESTÉ LISTA...")
print("=" * 60)

# Esperar a que el servidor esté listo
max_intentos = 10
for intento in range(max_intentos):
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=2)
        if response.status_code == 200:
            print("✅ API está lista!\n")
            break
    except:
        print(f"⏳ Intento {intento + 1}/{max_intentos}... esperando...")
        time.sleep(2)
else:
    print("❌ API no respondió después de varios intentos")
    exit(1)

# Probar con ruta_id = 1
ruta_id = 1

print("=" * 60)
print(f"PRUEBA DE ENDPOINT: GET /rutas/{ruta_id}/con-calles")
print("=" * 60)

print(f"\n🔍 Solicitando ruta {ruta_id} con calles...")
try:
    response = requests.get(f"{BASE_URL}/rutas/{ruta_id}/con-calles", timeout=30)
    
    print(f"Status Code: {response.status_code}")
    data = response.json()
    
    print(f"\n📋 Respuesta:")
    print(json.dumps(data, indent=2, ensure_ascii=False))
    
    if response.status_code == 200:
        if "geometry" in data and data["geometry"]:
            print(f"\n✅ ÉXITO - Geometría GeoJSON obtenida:")
            print(f"   - Tipo: {data['geometry']['type']}")
            if 'coordinates' in data['geometry']:
                print(f"   - Coordenadas: {len(data['geometry']['coordinates'])} puntos")
            print(f"   - Distancia: {data.get('distancia_km', 'N/A')} km")
            print(f"   - Duración: {data.get('duracion_minutos', 'N/A')} minutos")
        elif "error" in data:
            print(f"\n⚠️  Error en respuesta: {data['error']}")
        else:
            print(f"\n⚠️  Respuesta sin geometry")
    
except requests.exceptions.ConnectionError:
    print(f"❌ No se pudo conectar a {BASE_URL}")
    print("   Asegúrate de que la API está ejecutándose")
except Exception as e:
    print(f"❌ Error: {str(e)}")
