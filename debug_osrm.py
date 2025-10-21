"""
Script para debuggear el problema con OSRM
"""

import sys
sys.path.insert(0, r'c:\Users\hanss\Desktop\LAR')

from gestion_rutas.database.db import SessionLocal
from gestion_rutas.models.base import Ruta, Entrega, Punto
from gestion_rutas.service.routing_service import RoutingService

db = SessionLocal()

try:
    print("=" * 60)
    print("DEBUGGEAR ENDPOINT RUTA CON CALLES")
    print("=" * 60)
    
    # Obtener ruta 2
    ruta = db.query(Ruta).filter(Ruta.id == 2).first()
    print(f"\n✓ Ruta encontrada: {ruta}")
    print(f"  - ID: {ruta.id}")
    print(f"  - Nombre: {ruta.nombre}")
    
    # Obtener entregas
    entregas = db.query(Entrega).filter(Entrega.id_ruta == 2).all()
    print(f"\n✓ Entregas encontradas: {len(entregas)}")
    
    # Obtener puntos
    puntos = []
    for entrega in entregas:
        punto = db.query(Punto).filter(Punto.id == entrega.id_punto).first()
        if punto:
            puntos.append(punto)
            print(f"  - Punto {punto.id}: ({punto.latitud}, {punto.longitud}) - {punto.nombre}")
    
    print(f"\n✓ Total de puntos: {len(puntos)}")
    
    if len(puntos) >= 2:
        print(f"\n🔍 Llamando a OSRM...")
        resultado = RoutingService.obtener_ruta_optimizada(puntos)
        
        if resultado:
            print(f"\n✅ ÉXITO!")
            print(f"  - Distancia: {resultado['distancia_km']} km")
            print(f"  - Duración: {resultado['duracion_minutos']} min")
            print(f"  - Geometry type: {resultado['geometry']['type']}")
            print(f"  - Coordenadas: {len(resultado['geometry']['coordinates'])} puntos")
        else:
            print(f"\n❌ OSRM no retornó datos")
    else:
        print(f"\n❌ No hay suficientes puntos")
        
except Exception as e:
    print(f"\n❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
