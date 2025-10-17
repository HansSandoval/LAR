"""test_api.py - Prueba del endpoint FastAPI de planificación VRP"""

import json
import sys
from pathlib import Path

# Agregar gestion_rutas al path
sys.path.insert(0, str(Path(__file__).parent))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_endpoint_root():
    """Test del endpoint raíz."""
    print("\n" + "=" * 60)
    print("TEST: GET /")
    print("=" * 60)
    
    response = client.get("/")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    assert response.status_code == 200
    print("✅ PASS")


def test_endpoint_obtener_ruta():
    """Test del endpoint GET /rutas/{id}."""
    print("\n" + "=" * 60)
    print("TEST: GET /rutas/123")
    print("=" * 60)
    
    response = client.get("/rutas/123")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    assert response.status_code == 200
    print("✅ PASS")


def test_endpoint_planificar():
    """Test del endpoint POST /rutas/planificar."""
    print("\n" + "=" * 60)
    print("TEST: POST /rutas/planificar")
    print("=" * 60)
    
    # Datos de entrada
    payload = {
        "candidates": [
            {"id": "D", "x": 50, "y": 50, "demand": 0},
            {"id": 1, "x": 45, "y": 68, "demand": 10},
            {"id": 2, "x": 42, "y": 70, "demand": 7},
            {"id": 3, "x": 60, "y": 60, "demand": 12},
            {"id": 4, "x": 30, "y": 40, "demand": 5},
        ],
        "vehicle_count": 2,
        "capacity": 20
    }
    
    print(f"\nPayload:")
    print(json.dumps(payload, indent=2))
    
    response = client.post("/rutas/planificar", json=payload)
    print(f"\nStatus: {response.status_code}")
    print(f"\nResponse:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    
    assert response.status_code == 200
    result = response.json()
    assert "routes" in result
    assert "unassigned" in result
    assert "total_distance" in result
    
    print("\n✅ PASS - Endpoint funcionando correctamente")


def test_endpoint_planificar_con_matriz():
    """Test del endpoint POST /rutas/planificar con matriz personalizada."""
    print("\n" + "=" * 60)
    print("TEST: POST /rutas/planificar (con matriz)")
    print("=" * 60)
    
    payload = {
        "candidates": [
            {"id": "D", "x": 0, "y": 0, "demand": 0},
            {"id": "A", "x": 1, "y": 1, "demand": 5},
            {"id": "B", "x": 2, "y": 0, "demand": 5},
        ],
        "distance_matrix": [
            [0.0, 1.414, 2.0],
            [1.414, 0.0, 1.414],
            [2.0, 1.414, 0.0],
        ],
        "vehicle_count": 1,
        "capacity": 15
    }
    
    response = client.post("/rutas/planificar", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    assert response.status_code == 200
    print("✅ PASS")


if __name__ == '__main__':
    try:
        print("\n🚀 Iniciando pruebas del endpoint FastAPI...\n")
        
        test_endpoint_root()
        test_endpoint_obtener_ruta()
        test_endpoint_planificar()
        test_endpoint_planificar_con_matriz()
        
        print("\n" + "=" * 60)
        print("✅ TODOS LOS TESTS PASARON EXITOSAMENTE")
        print("=" * 60 + "\n")
        
    except Exception as e:
        print(f"\n❌ ERROR durante los tests:")
        print(f"   {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
