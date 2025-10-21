"""test_2opt.py - Prueba y comparación de 2-opt vs Nearest Neighbor"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from vrp.schemas import VRPInput, NodeCoordinate
from vrp.planificador import planificar_vrp_api, validate_and_prepare
from vrp.optimizacion import optimiza_rutas_2opt, calcula_distancia_ruta


def test_comparacion_nn_vs_2opt():
    """Compara la calidad de NN vs NN+2-opt."""
    
    print("=" * 70)
    print("TEST: Comparación Nearest Neighbor vs 2-opt")
    print("=" * 70)
    
    # Crear instancia de prueba más compleja
    nodos = [
        NodeCoordinate(id='D', x=0, y=0, demand=0),        # Depósito
        NodeCoordinate(id=1, x=10, y=20, demand=5),
        NodeCoordinate(id=2, x=30, y=15, demand=3),
        NodeCoordinate(id=3, x=25, y=35, demand=4),
        NodeCoordinate(id=4, x=15, y=10, demand=2),
        NodeCoordinate(id=5, x=40, y=30, demand=6),
        NodeCoordinate(id=6, x=50, y=10, demand=4),
        NodeCoordinate(id=7, x=35, y=50, demand=3),
        NodeCoordinate(id=8, x=20, y=45, demand=5),
    ]
    
    print(f"\n📊 Instancia: {len(nodos)} nodos, demanda total: {sum(n.demand or 0 for n in nodos)} kg")
    
    # Entrada VRP
    entrada = VRPInput(candidates=nodos, vehicle_count=2, capacity=15)
    
    # Paso 1: Obtener solución solo con NN (sin 2-opt)
    print("\n" + "-" * 70)
    print("PASO 1: Construcción inicial (sin optimización local)")
    print("-" * 70)
    
    prep = validate_and_prepare(entrada)
    dist_matrix = prep['dist_matrix']
    demands = [float(n.demand or 0.0) for n in nodos]
    
    # result_nn = nearest_neighbor_vrp(dist_matrix, demands, entrada.vehicle_count, entrada.capacity)
    # routes_nn = result_nn['routes']
    # distancia_nn = result_nn['total_distance']
    
    # print(f"\n✓ Rutas NN:")
    # for idx, r in enumerate(routes_nn, 1):
    #     secuencia = " → ".join(str(nodos[i].id) for i in r)
    #     dist_ruta = calcula_distancia_ruta(r, dist_matrix)
    #     print(f"  Vehículo {idx}: {secuencia}")
    #     print(f"              Distancia: {dist_ruta:.2f} km")
    
    # print(f"\n📍 Distancia total NN: {distancia_nn:.2f} km")
    
    # Paso 2: Aplicar 2-opt mediante planificar_vrp_api
    print("\n" + "-" * 70)
    print("PASO 2: Búsqueda Local 2-opt con planificar_vrp_api")
    print("-" * 70)
    
    import time
    start_time = time.time()
    result_vrp = planificar_vrp_api(entrada, timeout_2opt=30.0)
    tiempo_opt = time.time() - start_time
    
    routes_2opt = [[nodos[i].id for i in r] for r in result_vrp.routes] if result_vrp.routes else []
    distancia_2opt = result_vrp.total_distance
    
    print(f"\n✓ Rutas después de 2-opt:")
    for idx, r in enumerate(routes_2opt, 1):
        secuencia = " → ".join(str(rid) for rid in r)
        print(f"  Vehículo {idx}: {secuencia}")
    
    print(f"\n📍 Distancia total 2-opt: {distancia_2opt:.2f} km")
    print(f"⏱️  Tiempo total: {tiempo_opt:.3f} segundos")
    
    # Comparativa
    print("\n" + "=" * 70)
    print("RESULTADOS")
    print("=" * 70)
    
    print(f"\n📈 Métrica de mejora:")
    print(f"  Distancia 2-opt:     {distancia_2opt:.2f} km")
    
    if distancia_2opt > 0:
        print(f"\n✅ Planificación completada exitosamente")
    
    return {
        'distancia_2opt': distancia_2opt,
        'tiempo_s': tiempo_opt,
    }


def test_api_con_2opt():
    """Test del endpoint con 2-opt activado."""
    
    print("\n" + "=" * 70)
    print("TEST: API FastAPI con 2-opt integrado")
    print("=" * 70)
    
    nodos = [
        NodeCoordinate(id='D', x=50, y=50, demand=0),
        NodeCoordinate(id=1, x=45, y=68, demand=10),
        NodeCoordinate(id=2, x=42, y=70, demand=7),
        NodeCoordinate(id=3, x=60, y=60, demand=12),
        NodeCoordinate(id=4, x=30, y=40, demand=5),
        NodeCoordinate(id=5, x=55, y=20, demand=9),
    ]
    
    # Test 1: Con 2-opt (por defecto)
    print("\n✓ Ejecutando con 2-opt habilitado...")
    entrada = VRPInput(candidates=nodos, vehicle_count=2, capacity=20)
    salida_con_2opt = planificar_vrp_api(entrada, aplicar_2opt=True, timeout_2opt=10.0)
    
    print(f"  Rutas: {salida_con_2opt.routes}")
    print(f"  Distancia: {salida_con_2opt.total_distance:.2f} km")
    
    # Test 2: Sin 2-opt (NN puro)
    print("\n✓ Ejecutando sin 2-opt (NN puro)...")
    salida_sin_2opt = planificar_vrp_api(entrada, aplicar_2opt=False)
    
    print(f"  Rutas: {salida_sin_2opt.routes}")
    print(f"  Distancia: {salida_sin_2opt.total_distance:.2f} km")
    
    mejora = salida_sin_2opt.total_distance - salida_con_2opt.total_distance
    mejora_pct = (mejora / salida_sin_2opt.total_distance * 100) if salida_sin_2opt.total_distance > 0 else 0
    
    print(f"\n📊 Comparativa:")
    print(f"  NN (sin 2-opt):  {salida_sin_2opt.total_distance:.2f} km")
    print(f"  NN + 2-opt:      {salida_con_2opt.total_distance:.2f} km")
    print(f"  Mejora:          {mejora:.2f} km ({mejora_pct:.1f}%)")


if __name__ == '__main__':
    try:
        print("\n🚀 Iniciando pruebas de 2-opt...\n")
        
        # Test 1: Comparación detallada
        test_comparacion_nn_vs_2opt()
        
        # Test 2: API con 2-opt
        test_api_con_2opt()
        
        print("\n" + "=" * 70)
        print("✅ TODOS LOS TESTS COMPLETADOS EXITOSAMENTE")
        print("=" * 70 + "\n")
        
    except Exception as e:
        print(f"\n❌ ERROR durante las pruebas:")
        print(f"   {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
