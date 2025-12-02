import requests
import json

try:
    # Fetch route 5 (which we know has geometry)
    response = requests.get("http://localhost:8000/rutas-planificadas/5")
    if response.status_code == 200:
        data = response.json()
        geo = data.get('geometria_json')
        print(f"Type of geometria_json: {type(geo)}")
        if isinstance(geo, list):
            print(f"Length: {len(geo)}")
            if len(geo) > 0:
                print(f"First point: {geo[0]}")
        elif isinstance(geo, str):
            print("It is a STRING!")
            print(f"Content preview: {geo[:50]}")
        else:
            print(f"It is {type(geo)}")
            print(f"Content: {geo}")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"Exception: {e}")
