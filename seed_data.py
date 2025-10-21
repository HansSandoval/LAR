"""
Script para insertar datos de prueba en la base de datos
"""

import os
import sys
from datetime import date, datetime

os.chdir(r'c:\Users\hanss\Desktop\LAR')
sys.path.insert(0, r'c:\Users\hanss\Desktop\LAR')

from gestion_rutas.database.db import SessionLocal
from gestion_rutas.models.base import (
    Cliente, Ruta, Punto, Entrega, Vehiculo,
    EstadoRuta, EstadoEntrega
)

print("=" * 60)
print("INSERTANDO DATOS DE PRUEBA")
print("=" * 60)

db = SessionLocal()

try:
    # 1. Verificar si ya existen datos
    ruta_existente = db.query(Ruta).first()
    if ruta_existente:
        print("✅ Ya existen rutas en la BD, usando datos existentes")
        db.close()
        sys.exit(0)
    
    print("\n🔧 Creando cliente de prueba...")
    cliente = Cliente(
        nombre="Cliente Test",
        direccion="Iquique",
        telefono="123456789",
        email="test@example.com"
    )
    db.add(cliente)
    db.flush()
    
    print("🔧 Creando vehículo de prueba...")
    vehiculo = Vehiculo(
        placa="TEST-001",
        marca="Toyota",
        modelo="Hilux",
        anio=2020,
        capacidad_kg=5000,
        combustible_km_litro=12,
        estado="disponible"
    )
    db.add(vehiculo)
    db.flush()
    
    print("🔧 Creando puntos de recolección...")
    puntos = [
        Punto(
            nombre="Punto 1",
            descripcion="Av. Ramon Perez Opazo con Av. La Tirana",
            latitud=-20.2399,
            longitud=-70.1254,
            tipo_punto="recoleccion"
        ),
        Punto(
            nombre="Punto 2",
            descripcion="Padre Hurtado con Av. La Tirana",
            latitud=-20.2844,
            longitud=-70.1746,
            tipo_punto="recoleccion"
        ),
        Punto(
            nombre="Punto 3",
            descripcion="Padre Hurtado con Tamarugal",
            latitud=-20.2512,
            longitud=-70.1401,
            tipo_punto="recoleccion"
        ),
        Punto(
            nombre="Punto 4",
            descripcion="Padre Hurtado con Los Chunchos",
            latitud=-20.3092,
            longitud=-70.0950,
            tipo_punto="recoleccion"
        ),
        Punto(
            nombre="Punto 5",
            descripcion="Padre Hurtado con Av. Cinco",
            latitud=-20.3035,
            longitud=-70.1836,
            tipo_punto="recoleccion"
        ),
        Punto(
            nombre="Punto 6",
            descripcion="Punto Sur 6",
            latitud=-20.2650,
            longitud=-70.1120,
            tipo_punto="recoleccion"
        ),
    ]
    
    for punto in puntos:
        db.add(punto)
    db.flush()
    
    print("🔧 Creando ruta de prueba...")
    ruta = Ruta(
        id_cliente=cliente.id,
        id_vehiculo=vehiculo.id,
        nombre="Ruta Sur Iquique - Test",
        descripcion="Ruta de prueba para demostración con calles",
        fecha_planificacion=date.today(),
        secuencia_puntos=[p.id for p in puntos],
        algoritmo_vrp="nearest_neighbor",
        estado=EstadoRuta.PLANIFICADA,
        distancia_planificada_km=25.5,
        duracion_planificada_minutos=90
    )
    db.add(ruta)
    db.flush()
    
    print("🔧 Creando entregas para cada punto...")
    for idx, punto in enumerate(puntos):
        entrega = Entrega(
            id_cliente=cliente.id,
            id_punto=punto.id,
            id_ruta=ruta.id,
            peso_kg=50 + (idx * 10),
            volumen_m3=0.5,
            estado=EstadoEntrega.PENDIENTE,
            fecha_programada=date.today(),
            fecha_creacion=datetime.now()
        )
        db.add(entrega)
    
    # Commit de todas las transacciones
    db.commit()
    
    print("\n✅ Datos de prueba insertados correctamente!")
    print(f"\n📋 Datos creados:")
    print(f"   ✓ Cliente: {cliente.nombre}")
    print(f"   ✓ Vehículo: {vehiculo.placa}")
    print(f"   ✓ Puntos: {len(puntos)}")
    print(f"   ✓ Ruta: {ruta.nombre} (ID: {ruta.id})")
    print(f"\n🚀 Usa ruta ID: {ruta.id} para probar en el mapa")
    
except Exception as e:
    db.rollback()
    print(f"\n❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    db.close()

print("\n" + "=" * 60)
