"""
Prueba simple de OSRM sin problemas de query string
"""

import requests
import json

print("=" * 60)
print("PRUEBA OSRM SIN OPTIMIZE")
print("=" * 60)

# Coordenadas de Iquique
coords = "-70.1254,-20.2399;-70.1746,-20.2844;-70.1401,-20.2512"

url = "http://router.project-osrm.org/route/v1/driving/" + coords

print(f"\n🔗 URL: {url}")

# Parámetros separados
params = {
    "steps": "true",
    "geometries": "geojson",
    "overview": "full"
}

print(f"📦 Parámetros: {params}")

try:
    response = requests.get(url, params=params, timeout=30)
    print(f"\n📊 Status Code: {response.status_code}")
    print(f"📋 URL Real: {response.url}")
    
    data = response.json()
    print(f"\n📝 Respuesta JSON:")
    print(json.dumps(data, indent=2)[:500])
    
    if data.get("code") == "Ok":
        print(f"\n✅ ¡Éxito!")
        print(f"   Rutas: {len(data.get('routes', []))}")
        if data.get('routes'):
            ruta = data['routes'][0]
            print(f"   Distancia: {ruta['distance'] / 1000:.2f} km")
            print(f"   Duración: {ruta['duration'] / 60:.2f} min")
    else:
        print(f"\n❌ Error: {data.get('code')}")
        print(f"   Mensaje: {data.get('message')}")
        
except Exception as e:
    print(f"\n❌ Excepción: {str(e)}")
    import traceback
    traceback.print_exc()
