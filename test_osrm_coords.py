"""
Script para debuggear coordenadas y OSRM
"""

import requests
import sys

print("=" * 60)
print("TESTEAR OSRM CON DIFERENTES COORDENADAS")
print("=" * 60)

# Puntos de Iquique
puntos_iquique = [
    (-20.2399, -70.1254),
    (-20.2844, -70.1746),
    (-20.2512, -70.1401),
]

# Prueba 1: Servidor OSRM público (routing.openstreetmap.de)
print("\n🔍 Prueba 1: OSRM routing.openstreetmap.de")
try:
    coords = ";".join([f"{lon},{lat}" for lat, lon in puntos_iquique])
    url = f"https://routing.openstreetmap.de/osrm/route/v1/driving/{coords}"
    
    params = {
        "steps": "true",
        "geometries": "geojson",
        "overview": "full"
    }
    
    response = requests.get(url, params=params, timeout=10)
    data = response.json()
    print(f"   Status: {data.get('code')}")
    if data.get('code') == 'Ok':
        print(f"   ✅ Funcionó!")
    else:
        print(f"   ❌ Error: {data.get('code')}")
        print(f"   Message: {data.get('message', 'Sin mensaje')}")
except Exception as e:
    print(f"   ❌ Error: {str(e)}")

# Prueba 2: Servidor OSRM público router.project-osrm.org
print("\n🔍 Prueba 2: OSRM router.project-osrm.org")
try:
    coords = ";".join([f"{lon},{lat}" for lat, lon in puntos_iquique])
    url = f"http://router.project-osrm.org/route/v1/driving/{coords}"
    
    params = {
        "steps": "true",
        "geometries": "geojson",
        "overview": "full"
    }
    
    response = requests.get(url, params=params, timeout=10)
    data = response.json()
    print(f"   Status: {data.get('code')}")
    if data.get('code') == 'Ok':
        print(f"   ✅ Funcionó!")
    else:
        print(f"   ❌ Error: {data.get('code')}")
        print(f"   Message: {data.get('message', 'Sin mensaje')}")
except Exception as e:
    print(f"   ❌ Error: {str(e)}")

# Prueba 3: Con coordenadas de prueba (Nueva York)
print("\n🔍 Prueba 3: Coordenadas de prueba (Nueva York)")
try:
    # Nueva York
    coords = "-74.0060,40.7128;-73.9776,40.7614;-74.0089,40.7614"
    url = f"http://router.project-osrm.org/route/v1/driving/{coords}"
    
    params = {
        "steps": "true",
        "geometries": "geojson",
        "overview": "full"
    }
    
    response = requests.get(url, params=params, timeout=10)
    data = response.json()
    print(f"   Status: {data.get('code')}")
    if data.get('code') == 'Ok':
        print(f"   ✅ OSRM funciona con coordenadas válidas!")
    else:
        print(f"   ❌ Error: {data.get('code')}")
except Exception as e:
    print(f"   ❌ Error: {str(e)}")

print("\n" + "=" * 60)
