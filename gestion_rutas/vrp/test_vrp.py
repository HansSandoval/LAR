"""test_vrp.py - Prueba rápida del planificador VRP"""

import sys
import json
from pathlib import Path

# Agregar gestion_rutas al path para importar módulos
sys.path.insert(0, str(Path(__file__).parent.parent))

from vrp.schemas import VRPInput, NodeCoordinate, VRPOutput
from vrp.planificador import planificar_vrp_api


def test_simple():
    """Test con un ejemplo simple: 1 depósito + 4 puntos, 2 vehículos."""
    
    nodos = [
        NodeCoordinate(id='D', x=50, y=50, demand=0),  # Depósito
        NodeCoordinate(id=1, x=45, y=68, demand=10),
        NodeCoordinate(id=2, x=42, y=70, demand=7),
        NodeCoordinate(id=3, x=60, y=60, demand=12),
        NodeCoordinate(id=4, x=30, y=40, demand=5),
    ]
    
    entrada = VRPInput(
        candidates=nodos,
        vehicle_count=2,
        capacity=20
    )
    
    print("=" * 60)
    print("TEST SIMPLE: Planificador VRP")
    print("=" * 60)
    print(f"\n✓ Entrada creada:")
    print(f"  - Nodos: {len(entrada.candidates)}")
    print(f"  - Vehículos: {entrada.vehicle_count}")
    print(f"  - Capacidad por vehículo: {entrada.capacity}")
    
    # Ejecutar planificador
    salida: VRPOutput = planificar_vrp_api(entrada)
    
    print(f"\n✓ Salida obtenida:")
    print(f"  - Rutas: {salida.routes}")
    print(f"  - No asignados: {salida.unassigned}")
    print(f"  - Distancia total: {salida.total_distance:.2f}")
    
    # Imprimir en JSON
    print(f"\n✓ JSON Output:")
    print(json.dumps(json.loads(salida.model_dump_json()), indent=2, ensure_ascii=False))
    
    return salida


def test_con_matriz_personalizada():
    """Test con matriz de distancias precomputada."""
    
    nodos = [
        NodeCoordinate(id='D', x=0, y=0, demand=0),
        NodeCoordinate(id='A', x=1, y=1, demand=5),
        NodeCoordinate(id='B', x=2, y=0, demand=5),
    ]
    
    # Matriz de distancias 3x3 (pequeña)
    matriz = [
        [0.0, 1.414, 2.0],
        [1.414, 0.0, 1.414],
        [2.0, 1.414, 0.0],
    ]
    
    entrada = VRPInput(
        candidates=nodos,
        distance_matrix=matriz,
        vehicle_count=1,
        capacity=15
    )
    
    print("\n" + "=" * 60)
    print("TEST CON MATRIZ PERSONALIZADA")
    print("=" * 60)
    
    salida = planificar_vrp_api(entrada)
    
    print(f"\n✓ Ruta obtenida: {salida.routes}")
    print(f"  Distancia: {salida.total_distance:.2f}")
    
    return salida


if __name__ == '__main__':
    try:
        print("\n🚀 Iniciando pruebas del planificador VRP...\n")
        
        # Test 1
        test_simple()
        
        # Test 2
        test_con_matriz_personalizada()
        
        print("\n" + "=" * 60)
        print("✅ TODAS LAS PRUEBAS COMPLETADAS EXITOSAMENTE")
        print("=" * 60 + "\n")
        
    except Exception as e:
        print(f"\n❌ ERROR durante la prueba:")
        print(f"   {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
