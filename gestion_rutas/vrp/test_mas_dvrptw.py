"""
Script de prueba para el Sistema de Agentes Múltiples (MAS)
con entorno DVRPTW sin time windows
"""

import sys
from pathlib import Path

# Agregar path del proyecto
sys.path.append(str(Path(__file__).parent.parent))

from vrp.dvrptw_env import DVRPTWEnv, cargar_predicciones_lstm
from vrp.mas_cooperativo import CoordinadorMAS, AgenteRecolector


def test_entorno_basico():
    """Prueba básica del entorno DVRPTW"""
    print("\n" + "="*70)
    print("TEST 1: Entorno DVRPTW Básico")
    print("="*70)
    
    env = DVRPTWEnv(
        num_camiones=2,
        capacidad_camion_kg=3500.0,
        max_steps=50,
        seed=42
    )
    
    print(f" Entorno creado exitosamente")
    print(f"  - Camiones: {env.num_camiones}")
    print(f"  - Clientes: {env.num_clientes}")
    print(f"  - Capacidad por camión: {env.capacidad_camion_kg} kg")
    
    # Reset
    obs = env.reset()
    print(f" Reset exitoso")
    print(f"  - Observación shape: {obs.shape}")
    
    # Ejecutar algunos pasos
    for i in range(5):
        action = env.action_space.sample()
        obs, reward, done, info = env.step(action)
        print(f"  Paso {i+1}: Acción={action}, Reward={reward:.2f}, Evento={info.get('evento')}")
        
        if done:
            break
    
    env.close()
    print(" Test básico completado\n")


def test_agente_individual():
    """Prueba de un agente individual"""
    print("="*70)
    print("TEST 2: Agente Individual")
    print("="*70)
    
    env = DVRPTWEnv(
        num_camiones=1,
        capacidad_camion_kg=3500.0,
        seed=42
    )
    
    camion = env.camiones[0]
    agente = AgenteRecolector(camion, env)
    
    print(f" Agente creado exitosamente")
    print(f"  - Camión ID: {agente.camion.id}")
    print(f"  - Capacidad: {agente.camion.capacidad_kg} kg")
    
    # Seleccionar próximo cliente
    clientes_disponibles = [c for c in env.clientes if not c.servido]
    cliente_id = agente.seleccionar_proximo_cliente(clientes_disponibles)
    
    print(f" Selección de cliente exitosa")
    print(f"  - Cliente seleccionado: {cliente_id}")
    
    if agente.memoria_decisiones:
        ultima_decision = agente.memoria_decisiones[-1]
        print(f"  - Razonamiento: {ultima_decision.razonamiento}")
        print(f"  - Prioridad: {ultima_decision.prioridad_decision:.2f}")
        print(f"  - Distancia: {ultima_decision.distancia_estimada:.2f} km")
    
    print(" Test agente individual completado\n")


def test_mas_cooperativo():
    """Prueba del Sistema de Agentes Múltiples"""
    print("="*70)
    print("TEST 3: Sistema de Agentes Múltiples Cooperativo")
    print("="*70)
    
    env = DVRPTWEnv(
        num_camiones=3,
        capacidad_camion_kg=3500.0,
        max_steps=100,
        seed=42
    )
    
    coordinador = CoordinadorMAS(env)
    
    print(f" Coordinador MAS creado")
    print(f"  - Número de agentes: {len(coordinador.agentes)}")
    
    # Ejecutar algunos pasos
    print("\n Ejecutando 10 pasos cooperativos...")
    for i in range(10):
        info_paso = coordinador.ejecutar_paso_cooperativo()
        if i % 3 == 0:
            print(f"  Paso {info_paso['paso']}: "
                  f"Servidos={info_paso['clientes_servidos']}, "
                  f"Conflictos={info_paso['conflictos']}, "
                  f"Reward={info_paso['reward_promedio']:.2f}")
    
    estadisticas = coordinador.get_estadisticas()
    print(f"\n Estadísticas del coordinador:")
    print(f"  - Pasos totales: {estadisticas['pasos_totales']}")
    print(f"  - Conflictos resueltos: {estadisticas['conflictos_resueltos']}")
    print(f"  - Decisiones cooperativas: {estadisticas['decisiones_cooperativas']}")
    
    print(" Test MAS cooperativo completado\n")


def test_episodio_completo():
    """Prueba de un episodio completo"""
    print("="*70)
    print("TEST 4: Episodio Completo con MAS")
    print("="*70)
    
    env = DVRPTWEnv(
        num_camiones=4,
        capacidad_camion_kg=3500.0,
        max_steps=200,
        seed=42
    )
    
    coordinador = CoordinadorMAS(env)
    
    print(" Iniciando episodio completo...\n")
    
    estadisticas = coordinador.ejecutar_episodio_completo(
        max_pasos=200,
        verbose=True
    )
    
    # Validar resultados
    print("\n" + "="*70)
    print("VALIDACIÓN DE RESULTADOS")
    print("="*70)
    
    assert estadisticas['clientes_servidos'] > 0, " No se sirvió ningún cliente"
    print(f" Clientes servidos: {estadisticas['clientes_servidos']}")
    
    assert estadisticas['reward_total'] != 0, " Reward total es 0"
    print(f" Reward total: {estadisticas['reward_total']:.2f}")
    
    assert estadisticas['distancia_total_km'] > 0, " No se recorrió distancia"
    print(f" Distancia total: {estadisticas['distancia_total_km']:.2f} km")
    
    eficiencia = (estadisticas['clientes_servidos'] / estadisticas['pasos_totales']) * 100
    print(f" Eficiencia: {eficiencia:.1f}% clientes/paso")
    
    print("\n Todos los tests pasaron exitosamente!")


def test_sin_time_windows():
    """Verifica que NO hay restricciones de time windows"""
    print("\n" + "="*70)
    print("TEST 5: Verificación SIN Time Windows")
    print("="*70)
    
    env = DVRPTWEnv(num_camiones=1, seed=42)
    
    print("Verificando que NO existen restricciones de ventanas de tiempo...\n")
    
    for i, cliente in enumerate(env.clientes[:5]):
        print(f"Cliente {i}:")
        print(f"  - Ventana inicio: {cliente.ventana_inicio}")
        print(f"  - Ventana fin: {cliente.ventana_fin}")
        
        # Validar
        assert cliente.ventana_inicio == 0.0, f" Cliente {i} tiene límite inferior != 0"
        assert cliente.ventana_fin == float('inf'), f" Cliente {i} tiene límite superior != infinito"
        print(f"   Sin restricciones de tiempo")
    
    print(f"\n Confirmado: Todos los clientes tienen ventanas [0, ∞) (SIN RESTRICCIONES)")


def ejecutar_todos_los_tests():
    """Ejecuta todos los tests"""
    print("\n" + "="*90)
    print(" "*20 + "SUITE DE TESTS - DVRPTW + MAS")
    print("="*90)
    
    try:
        test_entorno_basico()
        test_agente_individual()
        test_sin_time_windows()
        test_mas_cooperativo()
        test_episodio_completo()
        
        print("\n" + "="*90)
        print(" "*30 + " TODOS LOS TESTS PASARON ")
        print("="*90)
        
    except Exception as e:
        print(f"\n ERROR EN LOS TESTS:")
        print(f"   {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    ejecutar_todos_los_tests()
