import requests
import time

def test_server(name, url):
    print(f"\nProbando {name}...")
    # Coordenadas de Iquique (Sector Sur)
    lat1, lon1 = -20.2693, -70.1703
    lat2, lon2 = -20.2600, -70.1500
    
    coords = f"{lon1},{lat1};{lon2},{lat2}"
    full_url = f"{url}/{coords}"
    params = {"geometries": "geojson", "overview": "full"}
    
    try:
        start = time.time()
        response = requests.get(full_url, params=params, timeout=5)
        end = time.time()
        
        if response.status_code == 200:
            data = response.json()
            if "routes" in data:
                print(f"✅ ÉXITO: {end - start:.2f}s")
                print(f"   Distancia: {data['routes'][0]['distance']}m")
                return True
            else:
                print("⚠️ Respuesta válida pero sin rutas")
        else:
            print(f"❌ Error HTTP: {response.status_code}")
            
    except Exception as e:
        print(f"❌ FALLÓ: {e}")
    return False

if __name__ == "__main__":
    servers = [
        ("OSRM Demo (Actual)", "http://router.project-osrm.org/route/v1/driving"),
        ("OSRM Alemania (Alternativa)", "https://routing.openstreetmap.de/routed-car/route/v1/driving")
    ]
    
    for name, url in servers:
        test_server(name, url)
