"""
Script FINAL: Simulación de residuos con intersecciones REALES y coordenadas precisas
Sector Sur de Iquique - Ruta 13
Datos extraídos de OpenStreetMap y Nominatim
"""

import pandas as pd
import numpy as np
import random
import json
from datetime import datetime, timedelta

# Cargar intersecciones con coordenadas precisas de OpenStreetMap
with open('intersecciones_con_coordenadas.json', 'r', encoding='utf-8') as f:
    datos_intersecciones = json.load(f)

intersecciones_dict = {}
for inter in datos_intersecciones['intersecciones']:
    intersecciones_dict[inter['nombre']] = (inter['latitud'], inter['longitud'])

print('=' * 100)
print('GENERACIÓN DE CSV - SIMULACIÓN DE RESIDUOS SECTOR SUR IQUIQUE')
print('=' * 100)
print(f'\n✓ Intersecciones cargadas: {len(intersecciones_dict)}')
print(f'✓ Período: 30 días (2024-10-01 a 2024-10-30)')
print(f'✓ Coordenadas: Precisas de OpenStreetMap\n')

# Zona única
zona = {
    'id': 1,
    'nombre': 'Sector Sur Iquique',
    'tipo': 'residencial',
    'prioridad': 1
}

# Datos fijos para camiones, operadores y puntos de disposición
def generar_patente():
    """Genera patente con formato XX-XX-NUMERO"""
    letras1 = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=2))
    letras2 = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=2))
    numero = random.randint(10, 99)
    return f"{letras1}-{letras2}-{numero}"

camiones = [
    {'patente': generar_patente(), 'capacidad': 5000, 'consumo': 3.5, 'tipo': 'gasolina'}
    for _ in range(5)
]

operadores = [
    {'nombre': f'Nombre{i}', 'cedula': f'cedula{i}', 'especialidad': f'especialidad{(i%3)+1}'}
    for i in range(1, 9)
]

puntos_disp = [
    {'nombre': 'Punto Disposición 1', 'tipo': 'vertedero', 'lat': -20.25, 'lon': -70.16, 'capacidad': 100},
    {'nombre': 'Punto Disposición 2', 'tipo': 'reciclaje', 'lat': -20.27, 'lon': -70.17, 'capacidad': 50},
    {'nombre': 'Punto Disposición 3', 'tipo': 'compostaje', 'lat': -20.26, 'lon': -70.15, 'capacidad': 30},
]

# Función para clasificar tipo de calle
def clasificar_tipo_calle(nombre):
    """Avenidas grandes > calles medianas > pasajes pequeños"""
    nombre_lower = nombre.lower()
    if any(x in nombre_lower for x in ['avenida', 'av.', 'av', 'ruta', 'circunvalación']):
        return 'avenida'
    elif any(x in nombre_lower for x in ['calle', 'paseo', 'alameda']):
        return 'calle'
    else:
        return 'pasaje'

# Función para generar residuos con variabilidad realista
def generar_residuos(nombre_calle, dia_num, clima, evento):
    """
    Variabilidad según: tipo calle, día de semana, clima, evento
    - Avenidas: 400-700 kg (mucho tráfico)
    - Calles: 250-400 kg (tráfico medio)
    - Pasajes: 50-150 kg (muy poco tráfico)
    """
    tipo_calle = clasificar_tipo_calle(nombre_calle)
    dia_semana_num = dia_num % 7
    
    # Base por tipo de calle (PASAJES SIGNIFICATIVAMENTE MENOR)
    if tipo_calle == 'avenida':
        base = np.random.uniform(400, 700)
    elif tipo_calle == 'calle':
        base = np.random.uniform(250, 400)
    else:  # pasaje - MUCHO MENOR
        base = np.random.uniform(50, 150)
    
    # Factor por día (fines de semana +20%)
    factor_dia = 1.2 if dia_semana_num in [5, 6] else 1.0
    
    # Factor por clima de Iquique (árido, mayormente soleado)
    if clima == 'nublado':
        factor_clima = 0.98  # Muy raro, casi sin efecto
    elif clima == 'parcialmente soleado':
        factor_clima = 1.0  # Normal
    else:  # soleado (más frecuente)
        factor_clima = 1.0
    
    # Factor por evento (REALISTA: pocos eventos en un mes)
    if evento == 'feriado':
        factor_evento = 0.6  # Menos actividad en feriados
    elif evento == 'feria local':
        factor_evento = 1.4  # Un poco más residuos en ferias
    else:  # normal (mayoría de días)
        factor_evento = 1.0
    
    residuos = int(base * factor_dia * factor_clima * factor_evento * np.random.uniform(0.9, 1.1))
    return max(30, residuos)

# Generar datos
datos = []
fecha_inicio = datetime(2024, 10, 1)
calles_nombres = list(intersecciones_dict.keys())

print(f'Generando datos para {len(calles_nombres)} intersecciones x 30 días...\n')

# Mapear días a español
dias_es = {
    'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miercoles',
    'Thursday': 'Jueves', 'Friday': 'Viernes', 'Saturday': 'Sabado',
    'Sunday': 'Domingo'
}

# Definir días de feriado en octubre 2024 (máximo 1-2 por mes)
feriados = [12]  # Octubre 12: Aniversario de Iquique (o similar)
ferias = [5, 19]  # Ferias locales en dos fechas

for dia in range(30):
    if dia % 5 == 0:
        print(f'  Procesando día {dia+1}/30...')
    
    fecha = fecha_inicio + timedelta(days=dia)
    dia_semana = dias_es.get(fecha.strftime('%A'), '')
    es_fin_semana = 1 if dia % 7 in [5, 6] else 0
    
    # Determinar tipo de evento
    if dia in feriados:
        evento = 'feriado'
    elif dia in ferias:
        evento = 'feria local'
    else:
        evento = 'normal'
    
    for calle_nombre in calles_nombres:
        lat, lon = intersecciones_dict[calle_nombre]
        
        camion = random.choice(camiones)
        operador = random.choice(operadores)
        punto_disp = random.choice(puntos_disp)
        
        # Clima de Iquique: mayormente soleado (70%), parcialmente soleado (25%), nublado (5%)
        clima_random = random.random()
        if clima_random < 0.05:
            clima = 'nublado'
        elif clima_random < 0.30:
            clima = 'parcialmente soleado'
        else:
            clima = 'soleado'
        
        # GENERAR RESIDUOS CON VARIABILIDAD REALISTA
        residuos_kg = generar_residuos(calle_nombre, dia, clima, evento)
        
        registro = {
            'id_zona': zona['id'],
            'nombre_zona': zona['nombre'],
            'tipo_zona': zona['tipo'],
            'prioridad': zona['prioridad'],
            'punto_recoleccion': calle_nombre,
            'tipo_punto': 'intersección',
            'latitud_punto_recoleccion': lat,
            'longitud_punto_recoleccion': lon,
            'fecha': fecha.strftime('%Y-%m-%d'),
            'residuos_kg': residuos_kg,
            'clima': clima,
            'evento': evento,
            'dia_semana': dia_semana,
            'es_fin_semana': es_fin_semana,
            'patente_camion': camion['patente'],
            'capacidad_kg': camion['capacidad'],
            'consumo_km_l': camion['consumo'],
            'tipo_combustible': camion['tipo'],
            'estado_operativo': 'activo',
            'gps_id': f"GPS-{random.randint(1000, 9999)}",
            'nombre_operador': operador['nombre'],
            'cedula_operador': operador['cedula'],
            'especialidad_operador': operador['especialidad'],
            'personal': 1,
            'nombre_punto_disp': punto_disp['nombre'],
            'tipo_punto_disp': punto_disp['tipo'],
            'latitud_punto_disp': punto_disp['lat'],
            'longitud_punto_disp': punto_disp['lon'],
            'capacidad_diaria_ton': punto_disp['capacidad'],
        }
        
        datos.append(registro)

# Crear DataFrame
df = pd.DataFrame(datos)

# Ordenar columnas
columnas_orden = [
    'id_zona', 'nombre_zona', 'tipo_zona', 'prioridad',
    'punto_recoleccion', 'tipo_punto', 'latitud_punto_recoleccion', 'longitud_punto_recoleccion',
    'fecha', 'residuos_kg', 'clima', 'evento', 'dia_semana', 'es_fin_semana',
    'patente_camion', 'capacidad_kg', 'consumo_km_l', 'tipo_combustible', 'estado_operativo', 'gps_id',
    'nombre_operador', 'cedula_operador', 'especialidad_operador', 'personal',
    'nombre_punto_disp', 'tipo_punto_disp', 'latitud_punto_disp', 'longitud_punto_disp', 'capacidad_diaria_ton',
]

df = df[columnas_orden]

# Guardar CSV
output_file = 'datos_residuos_iquique_final.csv'
df.to_csv(output_file, index=False, encoding='utf-8')

print(f'\n✓ CSV generado exitosamente: {output_file}')
print(f'  - Total de registros: {len(df):,}')
print(f'  - Intersecciones únicas: {df["punto_recoleccion"].nunique()}')
print(f'  - Período: {fecha_inicio.strftime("%Y-%m-%d")} a {(fecha_inicio + timedelta(days=29)).strftime("%Y-%m-%d")}')
print(f'  - Columnas: {len(df.columns)}')
print(f'  - Coordenadas: PRECISAS DE OPENSTREETMAP (Nominatim)')
print(f'\n✓ Primeros registros del CSV:\n')
print(df.head(10))

print(f'\n✓ Estadísticas de coordenadas:')
print(f'  Latitudes: min={df["latitud_punto_recoleccion"].min():.4f}, max={df["latitud_punto_recoleccion"].max():.4f}')
print(f'  Longitudes: min={df["longitud_punto_recoleccion"].min():.4f}, max={df["longitud_punto_recoleccion"].max():.4f}')

print('\n' + '=' * 100)
