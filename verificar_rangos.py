import pandas as pd

df = pd.read_csv('c:/Users/Usuario/Desktop/LAR-master/gestion_rutas/lstm/datos_residuos_iquique.csv')

print('='*80)
print('RANGO DE COORDENADAS EN EL CSV:')
print('='*80)
print(f'Latitud:  {df["latitud_punto_recoleccion"].min():.6f} a {df["latitud_punto_recoleccion"].max():.6f}')
print(f'Longitud: {df["longitud_punto_recoleccion"].min():.6f} a {df["longitud_punto_recoleccion"].max():.6f}')

print('\n' + '='*80)
print('COORDENADAS DE REFERENCIA (Centro de Iquique):')
print('='*80)
print('Latitud:  -20.2397')
print('Longitud: -70.1348')

print('\n' + '='*80)
print('SI LAS COORDENADAS DEL CSV ESTAN EN EL OCEANO,')
print('SIGNIFICA QUE EL CSV TIENE DATOS INCORRECTOS DESDE EL ORIGEN')
print('='*80)

# Mostrar algunos puntos de ejemplo
print('\nEJEMPLOS DE PUNTOS:')
puntos = df.groupby('punto_recoleccion')[['latitud_punto_recoleccion', 'longitud_punto_recoleccion']].first()
print(puntos.head(10))
