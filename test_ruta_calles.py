"""
Script para probar el endpoint de rutas con calles
"""

import requests
import json

# URL base de la API
BASE_URL = "http://localhost:8000"

# Primero, obtener una ruta existente
print("=" * 60)
print("PRUEBA DE ENDPOINT: GET /rutas/{ruta_id}/con-calles")
print("=" * 60)

# Probar con ruta_id = 1
ruta_id = 1

print(f"\n🔍 Solicitando ruta {ruta_id} con calles...")
response = requests.get(f"{BASE_URL}/rutas/{ruta_id}/con-calles")

print(f"Status Code: {response.status_code}")
print(f"\n📋 Respuesta:")
print(json.dumps(response.json(), indent=2, ensure_ascii=False))

# Si la respuesta es exitosa, mostrar información adicional
if response.status_code == 200:
    data = response.json()
    if "geometry" in data:
        print(f"\n✅ Geometría GeoJSON obtenida:")
        print(f"   - Tipo: {data['geometry']['type']}")
        print(f"   - Coordenadas: {len(data['geometry']['coordinates'])} puntos")
        print(f"   - Distancia: {data['distancia_km']} km")
        print(f"   - Duración: {data['duracion_minutos']} minutos")
    elif "error" in data:
        print(f"\n⚠️  Error: {data['error']}")
