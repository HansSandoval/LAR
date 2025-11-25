"""
Script de prueba para verificar el routing service con OSRM.
Calcula una ruta real por calles entre dos puntos de Iquique.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from gestion_rutas.service.routing_service import RoutingService
from gestion_rutas.models.base import Punto

def test_routing_osrm():
    print("="*60)
    print("TEST: Routing Service con OSRM")
    print("="*60)
    
    # Dos puntos en Sector Sur de Iquique
    punto_a = Punto(
        id=1,
        nombre="Avenida Arturo Prat",
        latitud=-20.2693,
        longitud=-70.1703
    )
    
    punto_b = Punto(
        id=2,
        nombre="Calle Baquedano",
        latitud=-20.2820,
        longitud=-70.1650
    )
    
    print(f"\n📍 Origen: {punto_a.nombre}")
    print(f"   Coordenadas: ({punto_a.latitud}, {punto_a.longitud})")
    
    print(f"\n📍 Destino: {punto_b.nombre}")
    print(f"   Coordenadas: ({punto_b.latitud}, {punto_b.longitud})")
    
    print("\n⏳ Calculando ruta por calles reales con OSRM...")
    
    # Calcular ruta
    ruta = RoutingService.obtener_ruta_entre_puntos(punto_a, punto_b)
    
    if ruta:
        print("\n✅ Ruta calculada exitosamente!")
        print(f"\n📊 Resultados:")
        print(f"   • Distancia real: {ruta['distancia_km']} km")
        print(f"   • Duración estimada: {ruta['duracion_minutos']} minutos")
        print(f"   • Puntos en geometría: {len(ruta['geometry'])} coordenadas")
        
        print(f"\n🗺️  Primeros 5 puntos de la ruta:")
        for i, coord in enumerate(ruta['geometry'][:5]):
            print(f"   {i+1}. [lon={coord[0]:.6f}, lat={coord[1]:.6f}]")
        
        print(f"\n💡 Esta ruta sigue las calles reales de Iquique")
        print(f"   y puede ser visualizada en el mapa con Leaflet")
        
        # Comparar con distancia en línea recta (haversine)
        from math import radians, sin, cos, sqrt, atan2
        
        R = 6371.0
        lat1, lon1 = radians(punto_a.latitud), radians(punto_a.longitud)
        lat2, lon2 = radians(punto_b.latitud), radians(punto_b.longitud)
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        dist_linea_recta = R * c
        
        print(f"\n📏 Comparación:")
        print(f"   • Distancia en línea recta: {dist_linea_recta:.2f} km")
        print(f"   • Distancia por calles: {ruta['distancia_km']} km")
        print(f"   • Diferencia: {(ruta['distancia_km'] - dist_linea_recta):.2f} km")
        print(f"   • Factor de rodeo: {(ruta['distancia_km'] / dist_linea_recta):.2f}x")
        
        return True
    else:
        print("\n❌ Error: No se pudo calcular la ruta")
        print("   Verifica que OSRM esté disponible en:")
        print("   http://router.project-osrm.org")
        return False

if __name__ == "__main__":
    test_routing_osrm()
