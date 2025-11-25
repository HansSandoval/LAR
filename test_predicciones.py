import sys
import os

# Agregar path
gestion_path = os.path.join(os.path.dirname(__file__), 'gestion_rutas')
sys.path.insert(0, gestion_path)

# Importar directamente sin pasar por __init__.py
from service.prediccion_mapa_service import PrediccionMapaService
from datetime import datetime, timedelta

# Crear servicio
servicio = PrediccionMapaService()

# Cargar recursos
print("=== CARGANDO RECURSOS ===")
modelo_ok = servicio.cargar_modelo()
datos_ok = servicio.cargar_datos_historicos()

print(f"Modelo cargado: {modelo_ok}")
print(f"Datos cargados: {datos_ok}")

# Obtener puntos
print("\n=== OBTENIENDO PUNTOS ===")
puntos = servicio.obtener_puntos_recoleccion_unicos()
print(f"Total puntos: {len(puntos)}")

if len(puntos) > 0:
    print(f"\nPrimer punto: {puntos[0]}")
    
    # Hacer predicción
    print("\n=== PREDICCIÓN ===")
    fecha = datetime.now() + timedelta(days=1)
    pred = servicio.predecir_residuos(puntos[0]['nombre'], fecha)
    print(f"Predicción: {pred}")
    
    # Generar todas las predicciones
    print("\n=== TODAS LAS PREDICCIONES ===")
    todas = servicio.generar_predicciones_completas(fecha)
    print(f"Total predicciones: {len(todas)}")
    if todas:
        print(f"Primera predicción completa: {todas[0]}")
        print(f"Rango de kg: {min(p['prediccion_kg'] for p in todas)} - {max(p['prediccion_kg'] for p in todas)}")
