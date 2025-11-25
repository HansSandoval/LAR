import pandas as pd

df = pd.read_csv('c:/Users/Usuario/Desktop/LAR-master/gestion_rutas/lstm/datos_residuos_iquique.csv')

puntos = df.groupby('punto_recoleccion')[['latitud_punto_recoleccion', 'longitud_punto_recoleccion']].first()

print(f"Total puntos unicos: {len(puntos)}")
print("\nAnalizando coordenadas:")
print("="*80)

# Centro aproximado de Iquique ciudad
centro_lat = -20.2397
centro_lon = -70.1348

# Calcular distancias
import math

def distancia(lat1, lon1, lat2, lon2):
    """Distancia aproximada en km"""
    return math.sqrt((lat2-lat1)**2 + (lon2-lon1)**2) * 111  # 1 grado ≈ 111 km

puntos_tierra = 0
puntos_oceano = 0

print("\nPuntos que parecen estar EN TIERRA (distancia < 5km del centro):")
for nombre, row in puntos.iterrows():
    dist = distancia(centro_lat, centro_lon, row['latitud_punto_recoleccion'], row['longitud_punto_recoleccion'])
    if dist < 5:
        puntos_tierra += 1
        if puntos_tierra <= 5:  # Mostrar solo primeros 5
            print(f"  - {nombre}: [{row['latitud_punto_recoleccion']}, {row['longitud_punto_recoleccion']}] - {dist:.2f}km")

print(f"\n...y {puntos_tierra - 5} puntos más en tierra" if puntos_tierra > 5 else "")

print("\n" + "="*80)
print("\nPuntos que parecen estar EN OCEANO (distancia > 5km del centro):")
for nombre, row in puntos.iterrows():
    dist = distancia(centro_lat, centro_lon, row['latitud_punto_recoleccion'], row['longitud_punto_recoleccion'])
    if dist >= 5:
        puntos_oceano += 1
        if puntos_oceano <= 10:  # Mostrar primeros 10
            print(f"  - {nombre}: [{row['latitud_punto_recoleccion']}, {row['longitud_punto_recoleccion']}] - {dist:.2f}km")

print(f"\n...y {puntos_oceano - 10} puntos más en océano" if puntos_oceano > 10 else "")

print("\n" + "="*80)
print(f"\nRESUMEN:")
print(f"  Puntos en tierra: {puntos_tierra}")
print(f"  Puntos en océano: {puntos_oceano}")
print(f"  Porcentaje en océano: {puntos_oceano/len(puntos)*100:.1f}%")
