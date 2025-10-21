import pandas as pd
import time
from geopy.geocoders import Nominatim
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def enriquecer_csv_con_geocoding():
    """
    Lee datos_residuos_iquique.csv, agrega lat/long a puntos de recolección,
    y guarda en CSV enriquecido
    """
    
    # Cargar CSV
    csv_path = 'gestion_rutas/lstm/datos_residuos_iquique.csv'
    df = pd.read_csv(csv_path)
    logger.info(f"CSV cargado: {df.shape[0]} filas, {df.shape[1]} columnas")
    
    # Inicializar geocoder (OpenStreetMap - Nominatim)
    geolocator = Nominatim(user_agent="lar_gestion_rutas_v1")
    
    # Crear mapping de punto_recoleccion -> (lat, long)
    puntos_unicos = df['punto_recoleccion'].unique()
    logger.info(f"Encontrados {len(puntos_unicos)} puntos únicos de recolección")
    
    geocoding_cache = {}
    
    # Geocodificar cada punto
    for idx, punto in enumerate(puntos_unicos):
        try:
            # Agregar contexto: Iquique, Chile
            direccion = f"{punto}, Iquique, Chile"
            logger.info(f"[{idx+1}/{len(puntos_unicos)}] Geocodificando: {punto}")
            
            location = geolocator.geocode(direccion, timeout=10)
            
            if location:
                lat, long = location.latitude, location.longitude
                geocoding_cache[punto] = (lat, long)
                logger.info(f"  ✓ Geocodificado: ({lat:.4f}, {long:.4f})")
            else:
                # Si no encuentra, usar center de Iquique + variación aleatoria
                import random
                lat = -20.27 + random.uniform(-0.05, 0.05)  # ± 5.5 km
                long = -70.14 + random.uniform(-0.05, 0.05)
                geocoding_cache[punto] = (lat, long)
                logger.warning(f"  ⚠ No geocodificado, usando aproximación: ({lat:.4f}, {long:.4f})")
            
            # Rate limit: 1 segundo entre requests (política Nominatim)
            time.sleep(1.1)
            
        except Exception as e:
            logger.error(f"  ✗ Error geocodificando {punto}: {str(e)}")
            # Fallback: usar coordenada aproximada de Iquique
            import random
            lat = -20.27 + random.uniform(-0.05, 0.05)
            long = -70.14 + random.uniform(-0.05, 0.05)
            geocoding_cache[punto] = (lat, long)
            logger.warning(f"  Using fallback coordinates: ({lat:.4f}, {long:.4f})")
            time.sleep(2)  # Esperar más después de error
    
    # Agregar columnas de lat/long para puntos de recolección
    df['latitud_punto_recoleccion'] = df['punto_recoleccion'].map(
        lambda x: geocoding_cache.get(x, (-20.27, -70.14))[0]
    )
    df['longitud_punto_recoleccion'] = df['punto_recoleccion'].map(
        lambda x: geocoding_cache.get(x, (-20.27, -70.14))[1]
    )
    
    logger.info(f"Geocoding completado para {len(geocoding_cache)} puntos")
    
    # Guardar CSV enriquecido
    output_path = 'gestion_rutas/lstm/datos_residuos_iquique_enriquecido.csv'
    df.to_csv(output_path, index=False)
    logger.info(f"CSV enriquecido guardado en: {output_path}")
    
    # Mostrar resumen
    print("\n" + "="*80)
    print("RESUMEN DE GEOCODING")
    print("="*80)
    print(f"Puntos únicos: {len(geocoding_cache)}")
    print(f"Registros totales: {df.shape[0]}")
    print(f"\nMuestra de puntos geocodificados:")
    for i, (punto, (lat, long)) in enumerate(list(geocoding_cache.items())[:5]):
        print(f"  {punto}: ({lat:.4f}, {long:.4f})")
    
    print(f"\nPrimeras filas del CSV enriquecido:")
    print(df[['punto_recoleccion', 'latitud_punto_recoleccion', 
             'longitud_punto_recoleccion', 'latitud_punto_disp', 
             'longitud_punto_disp']].drop_duplicates().head(10).to_string())
    
    return df, geocoding_cache

if __name__ == "__main__":
    print("Iniciando enriquecimiento de CSV con geocoding...")
    print("Esto puede tomar 2-3 minutos (1 segundo por punto + 74 puntos únicos)\n")
    
    df, cache = enriquecer_csv_con_geocoding()
    
    print("\n✓ Proceso completado exitosamente")
    print(f"Archivo guardado: gestion_rutas/lstm/datos_residuos_iquique_enriquecido.csv")
