"""optimizacion.py

Módulo de optimización VRP con búsqueda local.

Contiene:
- Heurística 2-opt para mejora de rutas
- Or-opt (desplazamiento de secuencias)
- Validación de capacidad después de modificaciones
"""

from typing import List, Tuple, Dict
import time


def calcula_distancia_ruta(ruta: List[int], dist_matrix: List[List[float]]) -> float:
    """Calcula la distancia total de una ruta."""
    if len(ruta) < 2:
        return 0.0
    dist = 0.0
    for i in range(len(ruta) - 1):
        dist += dist_matrix[ruta[i]][ruta[i + 1]]
    return dist


def delta_2opt(ruta: List[int], i: int, j: int, dist_matrix: List[List[float]]) -> float:
    """
    Calcula el cambio de distancia al intercambiar aristas en 2-opt.
    
    En 2-opt, se eliminan aristas (i, i+1) y (j, j+1) y se reemplazan por
    (i, j) y (i+1, j+1), invirtiendo el segmento [i+1...j].
    
    Retorna: delta_distancia (negativo = mejora)
    """
    if i >= j or j - i < 1:
        return 0.0
    
    n = len(ruta)
    if j + 1 >= n:
        return 0.0
    
    # Distancia actual
    dist_actual = dist_matrix[ruta[i]][ruta[i + 1]] + dist_matrix[ruta[j]][ruta[j + 1]]
    
    # Distancia nueva
    dist_nueva = dist_matrix[ruta[i]][ruta[j]] + dist_matrix[ruta[i + 1]][ruta[j + 1]]
    
    return dist_nueva - dist_actual


def aplica_2opt(ruta: List[int], dist_matrix: List[List[float]]) -> List[int]:
    """
    Aplica un movimiento 2-opt: intercambia dos aristas invirtiendo un segmento.
    
    Retorna la ruta mejorada o la misma si no hay mejora.
    """
    mejor_ruta = ruta[:]
    mejor_distancia = calcula_distancia_ruta(mejor_ruta, dist_matrix)
    
    n = len(ruta)
    mejorado = True
    
    while mejorado:
        mejorado = False
        for i in range(n - 2):
            for j in range(i + 2, n - 1):
                delta = delta_2opt(mejor_ruta, i, j, dist_matrix)
                
                if delta < -1e-6:  # Si hay mejora (con tolerancia numérica)
                    # Aplicar 2-opt: invertir segmento [i+1...j]
                    nueva_ruta = mejor_ruta[:i + 1] + mejor_ruta[i + 1:j + 1][::-1] + mejor_ruta[j + 1:]
                    nueva_distancia = calcula_distancia_ruta(nueva_ruta, dist_matrix)
                    
                    if nueva_distancia < mejor_distancia - 1e-6:
                        mejor_ruta = nueva_ruta
                        mejor_distancia = nueva_distancia
                        mejorado = True
                        break
            if mejorado:
                break
    
    return mejor_ruta


def optimiza_rutas_2opt(routes: List[List[int]], dist_matrix: List[List[float]], max_iteraciones: int = 1000, timeout: float = 60.0) -> Dict:
    """
    Optimiza múltiples rutas usando 2-opt.
    
    Entrada:
    - routes: lista de rutas (cada ruta es lista de índices incluyendo depósito)
    - dist_matrix: matriz de distancias
    - max_iteraciones: máximo de iteraciones por ruta
    - timeout: tiempo máximo en segundos
    
    Retorna dict con:
    - 'routes': rutas optimizadas
    - 'distancia_inicial': distancia antes de optimización
    - 'distancia_final': distancia después de optimización
    - 'mejora_pct': mejora en porcentaje
    - 'tiempo_s': tiempo de ejecución
    - 'iteraciones': iteraciones realizadas
    """
    tiempo_inicio = time.time()
    
    # Calcular distancia inicial
    distancia_inicial = sum(calcula_distancia_ruta(r, dist_matrix) for r in routes)
    
    rutas_optimizadas = []
    iteraciones_total = 0
    
    for idx_ruta, ruta in enumerate(routes):
        if time.time() - tiempo_inicio > timeout:
            print(f"⚠️  Timeout alcanzado. Deteniendo optimización en ruta {idx_ruta}.")
            rutas_optimizadas.append(ruta)
            continue
        
        # 2-opt iterativo para esta ruta
        ruta_opt = ruta[:]
        for it in range(max_iteraciones):
            if time.time() - tiempo_inicio > timeout:
                break
            
            ruta_nueva = aplica_2opt(ruta_opt, dist_matrix)
            
            if ruta_nueva == ruta_opt:
                # Convergencia: no hay más mejoras
                break
            
            ruta_opt = ruta_nueva
            iteraciones_total += 1
        
        rutas_optimizadas.append(ruta_opt)
    
    # Calcular distancia final
    distancia_final = sum(calcula_distancia_ruta(r, dist_matrix) for r in rutas_optimizadas)
    print(f"DEBUG: optimiza_rutas_2opt calc final: {distancia_final}. Rutas: {len(rutas_optimizadas)}")
    
    tiempo_total = time.time() - tiempo_inicio
    
    mejora_pct = ((distancia_inicial - distancia_final) / distancia_inicial * 100) if distancia_inicial > 0 else 0
    
    return {
        'routes': rutas_optimizadas,
        'distancia_inicial': distancia_inicial,
        'distancia_final': distancia_final,
        'mejora_pct': mejora_pct,
        'tiempo_s': tiempo_total,
        'iteraciones': iteraciones_total,
    }


def or_opt_single(ruta: List[int], dist_matrix: List[List[float]]) -> List[int]:
    """
    Or-opt: desplaza una secuencia de 1, 2 o 3 nodos a otra posición.
    
    Más rápido que 2-opt para instancias grandes.
    """
    mejor_ruta = ruta[:]
    mejor_distancia = calcula_distancia_ruta(mejor_ruta, dist_matrix)
    
    n = len(ruta)
    
    for tamaño_seg in [1, 2, 3]:
        for i in range(1, n - tamaño_seg - 1):
            # Extraer segmento [i...i+tamaño_seg-1]
            segmento = mejor_ruta[i:i + tamaño_seg]
            resto = mejor_ruta[:i] + mejor_ruta[i + tamaño_seg:]
            
            # Probar insertar en todas las posiciones del resto
            for j in range(len(resto)):
                nueva_ruta = resto[:j] + segmento + resto[j:]
                nueva_distancia = calcula_distancia_ruta(nueva_ruta, dist_matrix)
                
                if nueva_distancia < mejor_distancia - 1e-6:
                    mejor_ruta = nueva_ruta
                    mejor_distancia = nueva_distancia
    
    return mejor_ruta


def valida_capacidad_ruta(ruta: List[int], demands: List[float], capacity: float) -> bool:
    """
    Verifica que una ruta respeta la restricción de capacidad.
    
    El primer y último nodo (depósito) tienen demanda 0.
    """
    carga = 0.0
    for idx in ruta[1:-1]:  # Excluir depósito (inicio y fin)
        carga += demands[idx]
        if carga > capacity + 1e-6:  # Tolerancia numérica
            return False
    return True
