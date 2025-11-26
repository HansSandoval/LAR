"""
Script para probar la generación de rutas VRP con OSRM
y visualizar las rutas en el mapa de Iquique
"""

from gestion_rutas.vrp.schemas import VRPInput, NodeCoordinate
from gestion_rutas.vrp.planificador import planificar_vrp_api
import json

# Puntos de recolección de Iquique (del mapa)
puntos_iquique = [
    # Depósito (Centro de Iquique)
    NodeCoordinate(id="DEPOSITO", x=-20.2145, y=-70.1545, demand=0),
    
    # Puntos de recolección reales en Iquique
    NodeCoordinate(id="1", x=-20.262156, y=-70.129893, demand=500),  # Avenida Padre Hurtado - Mares del Sur
    NodeCoordinate(id="2", x=-20.259861, y=-70.124389, demand=480),  # Avenida Padre Hurtado - Jardines del Sur
    NodeCoordinate(id="3", x=-20.259960, y=-70.124988, demand=520),  # Avenida Padre Hurtado (Sector 3)
    NodeCoordinate(id="4", x=-20.255944, y=-70.125653, demand=450),  # Avenida La Tirana - Jardines del Sur
    NodeCoordinate(id="5", x=-20.241336, y=-70.128191, demand=490),  # Avenida La Tirana - Centro Iquique
    NodeCoordinate(id="6", x=-20.262094, y=-70.122565, demand=510),  # Tamarugal - Jardines del Sur
    NodeCoordinate(id="7", x=-20.2180, y=-70.1500, demand=400),      # Calle Zentenario - Iquique Centro
    NodeCoordinate(id="8", x=-20.2160, y=-70.1480, demand=470),      # Calle Baquedano - Iquique Centro
]

print("=" * 80)
print("PRUEBA DE GENERACIÓN DE RUTAS VRP CON OSRM")
print("=" * 80)
print(f"\nPuntos a procesar: {len(puntos_iquique)}")
print(f"Depósito: {puntos_iquique[0].id}")
print(f"Puntos de recolección: {len(puntos_iquique) - 1}")
print("\nPuntos:")
for p in puntos_iquique:
    print(f"  {p.id:12} -> Lat: {p.x:.6f}, Lon: {p.y:.6f}, Demanda: {p.demand} kg")

# Crear entrada VRP
print("\n" + "-" * 80)
print("CREANDO ENTRADA VRP...")
print("-" * 80)

input_vrp = VRPInput(
    candidates=puntos_iquique,
    vehicle_count=2,  # 2 camiones
    capacity=5000,    # 5 toneladas por camión
    distance_matrix=None  # OSRM calculará la matriz
)

print(f"\nVehículos: {input_vrp.vehicle_count}")
print(f"Capacidad por vehículo: {input_vrp.capacity} kg")

# Planificar rutas CON OSRM (distancias reales)
print("\n" + "-" * 80)
print("PLANIFICANDO RUTAS CON OSRM (Distancias Reales)...")
print("-" * 80)

try:
    result_vrp = planificar_vrp_api(input_vrp, timeout_2opt=30.0, use_osrm=True)
    
    print("\n✓ Rutas generadas exitosamente\n")
    print(f"Número de rutas: {len(result_vrp.routes)}")
    print(f"Distancia total: {result_vrp.total_distance:.2f} km")
    print(f"Nodos no asignados: {len(result_vrp.unassigned)}")
    
    if result_vrp.unassigned:
        print(f"  No asignados: {result_vrp.unassigned}")
    
    print("\n" + "=" * 80)
    print("DETALLE DE RUTAS")
    print("=" * 80)
    
    for i, ruta in enumerate(result_vrp.routes, 1):
        print(f"\nRUTA {i}:")
        print(f"  Secuencia: {' → '.join(ruta)}")
        
        # Calcular distancia y demanda de la ruta
        distancia_ruta = 0
        demanda_ruta = 0
        for j in range(len(ruta) - 1):
            id_actual = ruta[j]
            id_siguiente = ruta[j + 1]
            
            # Encontrar puntos
            punto_actual = next((p for p in puntos_iquique if p.id == id_actual), None)
            punto_siguiente = next((p for p in puntos_iquique if p.id == id_siguiente), None)
            
            if punto_actual and punto_siguiente:
                demanda_ruta += punto_actual.demand
        
        print(f"  Demanda total: {demanda_ruta} kg")
        print(f"  Puntos en ruta: {len(ruta) - 2} (sin contar depósito inicio/fin)")
    
    # Guardar output para visualización
    print("\n" + "=" * 80)
    print("GUARDANDO RESULTADOS...")
    print("=" * 80)
    
    output_data = {
        "rutas": result_vrp.routes,
        "distancia_total_km": result_vrp.total_distance,
        "no_asignados": result_vrp.unassigned,
        "puntos": [
            {
                "id": p.id,
                "latitud": p.x,
                "longitud": p.y,
                "demanda": p.demand
            }
            for p in puntos_iquique
        ],
        "metodo": "VRP con OSRM (distancias reales)"
    }
    
    with open('c:\\Users\\hanss\\Desktop\\LAR\\rutas_generadas.json', 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print("\n✓ Archivo guardado: rutas_generadas.json")
    print("\nPuedes visualizar las rutas en:")
    print("  http://localhost:8000/static/mapa_rutas_iquique.html")
    
except Exception as e:
    print(f"\n❌ Error al generar rutas: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
