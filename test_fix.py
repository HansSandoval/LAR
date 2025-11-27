import requests
import json

try:
    response = requests.get("http://localhost:8000/rutas-planificadas/?limit=20")
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Success! Received {len(data)} routes.")
        if len(data) > 0:
            print("Sample route keys:", data[0].keys())
    else:
        print("Error Response:")
        print(response.text)
except Exception as e:
    print(f"Exception: {e}")
