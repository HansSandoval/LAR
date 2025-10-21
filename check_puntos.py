"""
Script para verificar las coordenadas exactas en BD
"""

import sys
sys.path.insert(0, r'c:\Users\hanss\Desktop\LAR')

from gestion_rutas.database.db import SessionLocal
from gestion_rutas.models.base import Punto

db = SessionLocal()

try:
    puntos = db.query(Punto).all()
    print("=" * 60)
    print("PUNTOS EN LA BASE DE DATOS")
    print("=" * 60)
    
    for punto in puntos:
        print(f"\nID: {punto.id}")
        print(f"  Nombre: {punto.nombre}")
        print(f"  Latitud: {punto.latitud} (tipo: {type(punto.latitud).__name__})")
        print(f"  Longitud: {punto.longitud} (tipo: {type(punto.longitud).__name__})")
        print(f"  URL OSRM: {punto.longitud},{punto.latitud}")
        
        # Verificar que no sean None o inválidos
        if punto.latitud is None or punto.longitud is None:
            print(f"  ⚠️ ADVERTENCIA: Coordenadas incompletas")
        if not (-90 <= punto.latitud <= 90):
            print(f"  ⚠️ ADVERTENCIA: Latitud fuera de rango")
        if not (-180 <= punto.longitud <= 180):
            print(f"  ⚠️ ADVERTENCIA: Longitud fuera de rango")
            
finally:
    db.close()
