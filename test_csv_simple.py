import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta

# Cargar CSV directamente
csv_path = Path("gestion_rutas/lstm/datos_residuos_iquique.csv")
df = pd.read_csv(csv_path)
df['fecha'] = pd.to_datetime(df['fecha'])

print(f"Total registros: {len(df)}")
print(f"Puntos únicos: {df['punto_recoleccion'].nunique()}")
print(f"Promedio general residuos_kg: {df['residuos_kg'].mean():.2f}")
print()

# Obtener puntos únicos
puntos = df.groupby(['punto_recoleccion', 'latitud_punto_recoleccion', 
                      'longitud_punto_recoleccion']).size().reset_index(name='registros')

print(f"Puntos únicos agrupados: {len(puntos)}")
print()

# Tomar primer punto
primer_punto = puntos.iloc[0]
nombre_punto = primer_punto['punto_recoleccion']
print(f"Primer punto: {nombre_punto}")
print(f"  Latitud: {primer_punto['latitud_punto_recoleccion']}")
print(f"  Longitud: {primer_punto['longitud_punto_recoleccion']}")
print(f"  Registros: {primer_punto['registros']}")
print()

# Calcular promedio para ese punto
df_punto = df[df['punto_recoleccion'] == nombre_punto]
promedio = df_punto['residuos_kg'].mean()
print(f"Promedio residuos_kg para {nombre_punto}: {promedio:.2f} kg")
print(f"Valores ejemplo: {df_punto['residuos_kg'].head(10).tolist()}")
