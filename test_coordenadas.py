"""Script para diagnosticar problema de coordenadas"""
import sys
sys.path.insert(0, 'c:/Users/Usuario/Desktop/LAR-master')

from gestion_rutas.service.prediccion_mapa_service import PrediccionMapaService
from datetime import datetime, timedelta

# Crear servicio
servicio = PrediccionMapaService()

# Generar predicciones
fecha = datetime.now() + timedelta(days=5)
predicciones = servicio.generar_predicciones_completas(fecha)

print(f"\nTotal predicciones: {len(predicciones)}")
print(f"\nPrimeras 5 predicciones:")
print("="*80)

for i, pred in enumerate(predicciones[:5]):
    print(f"\n{i+1}. {pred['punto']}")
    print(f"   Latitud:  {pred['latitud']}")
    print(f"   Longitud: {pred['longitud']}")
    print(f"   Tipo latitud:  {type(pred['latitud'])}")
    print(f"   Tipo longitud: {type(pred['longitud'])}")
    print(f"   Prediccion: {pred['prediccion_kg']} kg")

print("\n" + "="*80)
print("\nRangos:")
lats = [p['latitud'] for p in predicciones]
lons = [p['longitud'] for p in predicciones]
print(f"Latitud:  {min(lats):.6f} a {max(lats):.6f}")
print(f"Longitud: {min(lons):.6f} a {max(lons):.6f}")

# Verificar si hay valores nulos o extraños
print("\n" + "="*80)
print("\nVerificacion de valores:")
for i, pred in enumerate(predicciones):
    if pred['latitud'] == 0 or pred['longitud'] == 0:
        print(f"WARNING: Punto {i} tiene coordenada en 0")
    if abs(pred['latitud']) > 90 or abs(pred['longitud']) > 180:
        print(f"WARNING: Punto {i} tiene coordenada fuera de rango")
    if isinstance(pred['latitud'], str) or isinstance(pred['longitud'], str):
        print(f"WARNING: Punto {i} tiene coordenada como string")

print("\nDiagnostico completado!")
