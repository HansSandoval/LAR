import pandas as pd

df = pd.read_csv('gestion_rutas/lstm/datos_residuos_iquique.csv')
print(f'Registros: {len(df)}')
print(f'Puntos únicos: {df["punto_recoleccion"].nunique()}')

coords = df.groupby('punto_recoleccion')[['latitud_punto_recoleccion', 'longitud_punto_recoleccion']].first()
print(f'\nRango latitud: {coords["latitud_punto_recoleccion"].min():.6f} a {coords["latitud_punto_recoleccion"].max():.6f}')
print(f'Rango longitud: {coords["longitud_punto_recoleccion"].min():.6f} a {coords["longitud_punto_recoleccion"].max():.6f}')

print(f'\nPrimeras 20 calles reales:')
print(coords.head(20))
