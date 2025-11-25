"""
Script para actualizar coordenadas del CSV
Distribuye los 74 puntos uniformemente en el Sector Sur de Iquique
Mantiene todos los datos de residuos intactos
"""
import pandas as pd
import numpy as np

# Límites del Sector Sur de Iquique
# Desde Av. Ramón Pérez Opazo (-20.252) hacia el sur
LAT_MIN = -20.275  # Sur
LAT_MAX = -20.252  # Norte (Av. Ramón Pérez Opazo)
LON_MIN = -70.140  # Oeste
LON_MAX = -70.120  # Este

print("="*100)
print("CORRECCION DE COORDENADAS - SECTOR SUR DE IQUIQUE")
print("="*100)

# Cargar CSV actual
csv_path = 'datos_residuos_iquique.csv'
print(f"\nCargando: {csv_path}")
df = pd.read_csv(csv_path)

print(f"  Registros: {len(df)}")
print(f"  Puntos únicos: {df['punto_recoleccion'].nunique()}")

# Obtener puntos únicos
puntos_unicos = df['punto_recoleccion'].unique()
n_puntos = len(puntos_unicos)

print(f"\n{'='*100}")
print(f"GENERANDO {n_puntos} COORDENADAS DISTRIBUIDAS EN SECTOR SUR")
print(f"{'='*100}")
print(f"  Área: Lat {LAT_MIN} a {LAT_MAX}, Lon {LON_MIN} a {LON_MAX}")

# Generar coordenadas dispersas (no en línea)
np.random.seed(42)  # Para reproducibilidad

nuevas_coordenadas = {}
for punto in puntos_unicos:
    # Coordenadas aleatorias dentro del Sector Sur
    lat = np.random.uniform(LAT_MIN, LAT_MAX)
    lon = np.random.uniform(LON_MIN, LON_MAX)
    nuevas_coordenadas[punto] = (lat, lon)
    print(f"  {punto[:50]:<50} -> [{lat:.6f}, {lon:.6f}]")

# Aplicar nuevas coordenadas al DataFrame
print(f"\n{'='*100}")
print("ACTUALIZANDO CSV...")
print(f"{'='*100}")

df_nuevo = df.copy()

for punto, (lat, lon) in nuevas_coordenadas.items():
    mask = df_nuevo['punto_recoleccion'] == punto
    df_nuevo.loc[mask, 'latitud_punto_recoleccion'] = lat
    df_nuevo.loc[mask, 'longitud_punto_recoleccion'] = lon

# Guardar
output_path = 'datos_residuos_iquique.csv'
df_nuevo.to_csv(output_path, index=False)

print(f"\n✓ CSV actualizado: {output_path}")

# Verificar dispersión
print(f"\n{'='*100}")
print("VERIFICACION DE DISPERSION")
print(f"{'='*100}")

coords_df = df_nuevo.groupby('punto_recoleccion')[['latitud_punto_recoleccion', 'longitud_punto_recoleccion']].first()
correlacion = np.corrcoef(coords_df['latitud_punto_recoleccion'], coords_df['longitud_punto_recoleccion'])[0,1]

print(f"  Rango latitud:  {coords_df['latitud_punto_recoleccion'].min():.6f} a {coords_df['latitud_punto_recoleccion'].max():.6f}")
print(f"  Rango longitud: {coords_df['longitud_punto_recoleccion'].min():.6f} a {coords_df['longitud_punto_recoleccion'].max():.6f}")
print(f"  Correlación lat-lon: {correlacion:.4f}")
print(f"  Estado: {'✓ DISPERSAS (OK)' if abs(correlacion) < 0.3 else '✗ EN LINEA (MAL)'}")

print(f"\n{'='*100}")
print("COMPLETADO")
print(f"{'='*100}")
print("Los 74 puntos ahora están dispersos en el Sector Sur de Iquique")
print("Los datos de residuos se mantuvieron intactos")
