import requests
import time

def test_osrm():
    # Coordinates for Iquique (approximate)
    lat1, lon1 = -20.2693, -70.1703
    lat2, lon2 = -20.2700, -70.1600
    
    coords = f"{lon1},{lat1};{lon2},{lat2}"
    url = f"http://router.project-osrm.org/route/v1/driving/{coords}"
    params = {
        "geometries": "geojson",
        "overview": "full"
    }
    
    print(f"Testing URL: {url}")
    
    try:
        start = time.time()
        response = requests.get(url, params=params, timeout=10)
        end = time.time()
        
        print(f"Status Code: {response.status_code}")
        print(f"Time taken: {end - start:.2f} seconds")
        
        if response.status_code == 200:
            data = response.json()
            print("Response JSON keys:", data.keys())
            if "routes" in data:
                print(f"Found {len(data['routes'])} routes")
                print("First route distance:", data["routes"][0]["distance"])
            else:
                print("No routes found in response")
        else:
            print("Error response:", response.text)
            
    except Exception as e:
        print(f"Exception occurred: {e}")

if __name__ == "__main__":
    test_osrm()
