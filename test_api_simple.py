import requests
import json

# Probar endpoint de predicciones
url = "http://localhost:8000/api/lstm/predicciones-fecha?fecha=2025-11-26"
print(f"Probando: {url}")

try:
    response = requests.get(url, timeout=30)
    print(f"\nStatus Code: {response.status_code}")
    print(f"\nResponse Headers: {dict(response.headers)}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\nKeys en respuesta: {list(data.keys())}")
        if 'predicciones' in data:
            print(f"Número de predicciones: {len(data['predicciones'])}")
            if data['predicciones']:
                print(f"\nPrimera predicción: {json.dumps(data['predicciones'][0], indent=2)}")
    else:
        print(f"\nError: {response.text}")
        
except requests.exceptions.Timeout:
    print("\n❌ TIMEOUT - El servidor tardó más de 30 segundos en responder")
    print("Esto significa que el endpoint está colgado o procesando indefinidamente")
except Exception as e:
    print(f"\n❌ Error: {e}")
