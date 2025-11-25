import pandas as pd

df = pd.read_csv('c:/Users/Usuario/Desktop/LAR-master/gestion_rutas/lstm/datos_residuos_iquique_corregido.csv')
puntos = df.groupby('punto_recoleccion')[['latitud_punto_recoleccion', 'longitud_punto_recoleccion']].first()

print('='*80)
print('COORDENADAS DEL CSV CORREGIDO (GEOCODIFICADO)')
print('='*80)
print('\nPRIMERAS 10 COORDENADAS:')
print(puntos.head(10))

print(f'\n{"="*80}')
print('ESTADÍSTICAS:')
print(f'{"="*80}')
print(f'Total puntos únicos: {len(puntos)}')
print(f'Rango latitud:  {puntos["latitud_punto_recoleccion"].min():.6f} a {puntos["latitud_punto_recoleccion"].max():.6f}')
print(f'Rango longitud: {puntos["longitud_punto_recoleccion"].min():.6f} a {puntos["longitud_punto_recoleccion"].max():.6f}')

# Verificar si las coordenadas están dispersas (no en línea)
import numpy as np
correlacion = np.corrcoef(puntos["latitud_punto_recoleccion"], puntos["longitud_punto_recoleccion"])[0,1]
print(f'\nCorrelación lat-lon: {correlacion:.4f}')
print('(Si está cerca de 1.0 o -1.0, están en línea recta)')
print('(Si está cerca de 0.0, están dispersas)')
