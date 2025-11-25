import pandas as pd

df = pd.read_csv('c:/Users/Usuario/Desktop/LAR-master/gestion_rutas/lstm/datos_residuos_iquique.csv')
punto = df.iloc[0]

print('Primer punto del CSV:')
print(f"Punto: {punto['punto_recoleccion']}")
print(f"Latitud (CSV): {punto['latitud_punto_recoleccion']}")
print(f"Longitud (CSV): {punto['longitud_punto_recoleccion']}")
print('')
print('VERIFICACION:')
print('Si esta coordenada esta en Iquique (Chile), deberia estar cerca de:')
print('Latitud: -20.2 (sur)')
print('Longitud: -70.1 (oeste)')
print('')
print('Si los numeros estan INTERCAMBIADOS, estarian en el oceano!')
print('')

# Verificar si estan intercambiados
lat = punto['latitud_punto_recoleccion']
lon = punto['longitud_punto_recoleccion']

print(f"Coordenada actual: [{lat}, {lon}]")
print(f"Coordenada invertida: [{lon}, {lat}]")
print('')
print('Prueba en Google Maps:')
print(f"Normal: https://www.google.com/maps?q={lat},{lon}")
print(f"Invertida: https://www.google.com/maps?q={lon},{lat}")
