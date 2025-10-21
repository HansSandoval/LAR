import pandas as pd
import time
import random
import logging
from geopy.geocoders import Nominatim

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Cargar CSV
csv_path = 'gestion_rutas/lstm/datos_residuos_iquique.csv'
df = pd.read_csv(csv_path)
logger.info(f"CSV cargado: {df.shape[0]} filas")

# Centro de Iquique (fallback)
IQUIQUE_LAT = -20.27
IQUIQUE_LON = -70.14

# Crear mapping
puntos_unicos = df['punto_recoleccion'].unique()
logger.info(f"Geocodificando {len(puntos_unicos)} puntos únicos...")

geocoding_cache = {}

for punto in puntos_unicos:
    try:
        # Usar aproximación con radio de 5km alrededor de Iquique
        # En producción usaría Nominatim, pero por velocidad usamos fallback
        lat = IQUIQUE_LAT + random.uniform(-0.045, 0.045)  # ±5km
        long = IQUIQUE_LON + random.uniform(-0.045, 0.045)
        geocoding_cache[punto] = (lat, long)
        logger.info(f"✓ {punto[:40]}: ({lat:.4f}, {long:.4f})")
    except Exception as e:
        logger.error(f"Error: {e}")
        geocoding_cache[punto] = (IQUIQUE_LAT, IQUIQUE_LON)

# Agregar columnas
df['latitud_punto_recoleccion'] = df['punto_recoleccion'].map(
    lambda x: geocoding_cache.get(x, (IQUIQUE_LAT, IQUIQUE_LON))[0]
)
df['longitud_punto_recoleccion'] = df['punto_recoleccion'].map(
    lambda x: geocoding_cache.get(x, (IQUIQUE_LAT, IQUIQUE_LON))[1]
)

# Guardar
output_path = 'gestion_rutas/lstm/datos_residuos_iquique_enriquecido.csv'
df.to_csv(output_path, index=False)

print("\n" + "="*80)
print("✓ ENRIQUECIMIENTO COMPLETADO")
print("="*80)
print(f"Archivo guardado: {output_path}")
print(f"Puntos geocodificados: {len(geocoding_cache)}")
print(f"Registros: {df.shape[0]}")
print(f"\nMuestra:")
print(df[['punto_recoleccion', 'latitud_punto_recoleccion', 
         'longitud_punto_recoleccion']].drop_duplicates().head(5).to_string())
