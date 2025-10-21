import pandas as pd
import numpy as np
import random
import string
from datetime import datetime, timedelta

# Solo una zona: Sector Sur de Iquique
zonas = {
    1: {'nombre': 'Sector Sur Iquique', 'tipo': 'residencial', 'prioridad': 1},
}

# Calles reales del sector sur de Iquique con intersecciones específicas
calles = [
    # Avenidas principales con intersecciones
    {'nombre': 'Av. Ramon Perez Opazo con Av. La Tirana', 'id_zona': 1, 'tipo': 'contenedor'},
    {'nombre': 'Padre Hurtado con Av. La Tirana', 'id_zona': 1, 'tipo': 'contenedor'},
    {'nombre': 'Padre Hurtado con Tamarugal', 'id_zona': 1, 'tipo': 'contenedor'},
    {'nombre': 'Padre Hurtado con Los Chunchos', 'id_zona': 1, 'tipo': 'contenedor'},
    {'nombre': 'Padre Hurtado con Av. Cinco', 'id_zona': 1, 'tipo': 'contenedor'},
    
    {'nombre': 'Av. La Tirana con Tamarugal', 'id_zona': 1, 'tipo': 'contenedor'},
    {'nombre': 'Av. La Tirana con Ontario', 'id_zona': 1, 'tipo': 'contenedor'},
    {'nombre': 'Av. La Tirana con Toronto', 'id_zona': 1, 'tipo': 'contenedor'},
    {'nombre': 'Av. La Tirana con Teresa Wilms Mont', 'id_zona': 1, 'tipo': 'contenedor'},
    
    {'nombre': 'Tamarugal con Los Chunchos', 'id_zona': 1, 'tipo': 'contenedor'},
    {'nombre': 'Tamarugal con C. Uno', 'id_zona': 1, 'tipo': 'contenedor'},
    {'nombre': 'Tamarugal con Ontario', 'id_zona': 1, 'tipo': 'contenedor'},
    
    {'nombre': 'Av. Cinco con Pje. Uno', 'id_zona': 1, 'tipo': 'contenedor'},
    {'nombre': 'Av. Cinco con Pje. Tres', 'id_zona': 1, 'tipo': 'contenedor'},
    {'nombre': 'Av. Cinco con Pje. Cinco', 'id_zona': 1, 'tipo': 'contenedor'},
    
    # Calles secundarias
    {'nombre': 'C. Uno', 'id_zona': 1, 'tipo': 'contenedor'},
    {'nombre': 'Pje. Dos', 'id_zona': 1, 'tipo': 'contenedor'},
    {'nombre': 'Los Chunchos', 'id_zona': 1, 'tipo': 'contenedor'},
    {'nombre': 'Ontario', 'id_zona': 1, 'tipo': 'contenedor'},
    {'nombre': 'Via Local Dos', 'id_zona': 1, 'tipo': 'contenedor'},
    {'nombre': 'Toronto', 'id_zona': 1, 'tipo': 'contenedor'},
    {'nombre': 'C. Seis', 'id_zona': 1, 'tipo': 'contenedor'},
    {'nombre': 'Teresa Wilms Mont', 'id_zona': 1, 'tipo': 'contenedor'},
    
    # Pasajes cortos
    {'nombre': 'Pje. C', 'id_zona': 1, 'tipo': 'contenedor'},
    {'nombre': 'Pje. B', 'id_zona': 1, 'tipo': 'contenedor'},
    {'nombre': 'Pje. A', 'id_zona': 1, 'tipo': 'contenedor'},
    {'nombre': 'Pje. Uno', 'id_zona': 1, 'tipo': 'contenedor'},
    {'nombre': 'Pje. Tres', 'id_zona': 1, 'tipo': 'contenedor'},
    {'nombre': 'Pje. Siete', 'id_zona': 1, 'tipo': 'contenedor'},
    {'nombre': 'Pje. Cinco', 'id_zona': 1, 'tipo': 'contenedor'},
    {'nombre': 'Pje. Seis', 'id_zona': 1, 'tipo': 'contenedor'},
    {'nombre': 'Pje. Ocho', 'id_zona': 1, 'tipo': 'contenedor'},
    
    # Calles de zona residencial
    {'nombre': 'Nueva Cuatro', 'id_zona': 1, 'tipo': 'contenedor'},
    {'nombre': 'Ines Solari Magnaso', 'id_zona': 1, 'tipo': 'contenedor'},
    {'nombre': 'Los Alagarrobos', 'id_zona': 1, 'tipo': 'contenedor'},
    {'nombre': 'La Chamiza', 'id_zona': 1, 'tipo': 'contenedor'},
    {'nombre': 'Lebu', 'id_zona': 1, 'tipo': 'contenedor'},
    {'nombre': 'Pje. Traiguen', 'id_zona': 1, 'tipo': 'contenedor'},
    {'nombre': 'Pje. Temuco', 'id_zona': 1, 'tipo': 'contenedor'},
    
    # Zona de cerros con intersecciones principales
    {'nombre': 'Cerro Colorado con C. Int Dos', 'id_zona': 1, 'tipo': 'contenedor'},
    {'nombre': 'Cerro Colorado con C. Int Tres', 'id_zona': 1, 'tipo': 'contenedor'},
    {'nombre': 'Cerro Colorado con C. Int Cuatro', 'id_zona': 1, 'tipo': 'contenedor'},
    
    {'nombre': 'C. Int Dos', 'id_zona': 1, 'tipo': 'contenedor'},
    {'nombre': 'C. Int Tres', 'id_zona': 1, 'tipo': 'contenedor'},
    {'nombre': 'C. Int Cuatro', 'id_zona': 1, 'tipo': 'contenedor'},
    
    {'nombre': 'Cerro Casiri', 'id_zona': 1, 'tipo': 'contenedor'},
    {'nombre': 'Coscaya', 'id_zona': 1, 'tipo': 'contenedor'},
    {'nombre': 'Sauna', 'id_zona': 1, 'tipo': 'contenedor'},
    {'nombre': 'Patara', 'id_zona': 1, 'tipo': 'contenedor'},
    {'nombre': 'Cerro Yabricoya', 'id_zona': 1, 'tipo': 'contenedor'},
    {'nombre': 'Chiza', 'id_zona': 1, 'tipo': 'contenedor'},
    {'nombre': 'Chauca', 'id_zona': 1, 'tipo': 'contenedor'},
    {'nombre': 'Calaunsa', 'id_zona': 1, 'tipo': 'contenedor'},
    {'nombre': 'Napa', 'id_zona': 1, 'tipo': 'contenedor'},
    
    # Zona con nombres de personajes/lugares
    {'nombre': 'Humberto Lizardi Flores', 'id_zona': 1, 'tipo': 'contenedor'},
    {'nombre': 'Tres Marias', 'id_zona': 1, 'tipo': 'contenedor'},
    {'nombre': 'Avenida Proyectada', 'id_zona': 1, 'tipo': 'contenedor'},
    {'nombre': 'Jardines Del Desierto', 'id_zona': 1, 'tipo': 'contenedor'},
    
    # Zona de minerales con intersecciones
    {'nombre': 'Los Mineros con Fanerita', 'id_zona': 1, 'tipo': 'contenedor'},
    {'nombre': 'Los Mineros con Calcopirita', 'id_zona': 1, 'tipo': 'contenedor'},
    {'nombre': 'Los Mineros con Sulfuros', 'id_zona': 1, 'tipo': 'contenedor'},
    
    {'nombre': 'Fanerita', 'id_zona': 1, 'tipo': 'contenedor'},
    {'nombre': 'Calcopirita', 'id_zona': 1, 'tipo': 'contenedor'},
    {'nombre': 'Crisocola', 'id_zona': 1, 'tipo': 'contenedor'},
    {'nombre': 'Sulfuros', 'id_zona': 1, 'tipo': 'contenedor'},
    {'nombre': 'Cuarzo', 'id_zona': 1, 'tipo': 'contenedor'},
    {'nombre': 'Filones', 'id_zona': 1, 'tipo': 'contenedor'},
    {'nombre': 'Pje. Granodiorita', 'id_zona': 1, 'tipo': 'contenedor'},
    {'nombre': 'Azurita', 'id_zona': 1, 'tipo': 'contenedor'},
    {'nombre': 'Pirita', 'id_zona': 1, 'tipo': 'contenedor'},
    {'nombre': 'Feldespato', 'id_zona': 1, 'tipo': 'contenedor'},
    {'nombre': 'Apilita', 'id_zona': 1, 'tipo': 'contenedor'},
    {'nombre': 'Matendisita', 'id_zona': 1, 'tipo': 'contenedor'},
    {'nombre': 'Malaquita', 'id_zona': 1, 'tipo': 'contenedor'},
]

# Mapeo de días de la semana al español
dias_semana_espanol = {
    0: 'Lunes',
    1: 'Martes',
    2: 'Miércoles',
    3: 'Jueves',
    4: 'Viernes',
    5: 'Sábado',
    6: 'Domingo'
}

# Generar patentes aleatorias formato XX-XX-NUMERO
def generar_patente():
    letras = ''.join(random.choices(string.ascii_uppercase, k=2))
    letras2 = ''.join(random.choices(string.ascii_uppercase, k=2))
    numero = str(random.randint(10, 99))
    return f"{letras}-{letras2}-{numero}"

# Generar camiones aleatorios
camiones = []
for i in range(5):
    camiones.append({
        'patente': generar_patente(),
        'capacidad_kg': random.choice([3500, 5000]),
        'consumo_km_l': round(random.uniform(4.0, 6.0), 1),
        'tipo_combustible': 'diesel',
        'estado_operativo': random.choice(['activo', 'mantenimiento']),
        'gps_id': f"GPS{str(i+1).zfill(3)}"
    })

# Operadores genéricos
operadores = []
for i in range(1, 9):
    operadores.append({
        'nombre': f'Nombre{i}',
        'cedula': f'cedula{i}',
        'especialidad': f'especialidad{random.randint(1,3)}'
    })

# Puntos de disposición
puntos_disposicion = [
    {'nombre': 'Centro de Acopio Sur Iquique', 'tipo': 'acopio_central', 'latitud': -20.2500, 'longitud': -70.1500, 'capacidad_diaria_ton': 50.0},
    {'nombre': 'Punto Reciclaje Av. Cinco', 'tipo': 'reciclaje', 'latitud': -20.2520, 'longitud': -70.1480, 'capacidad_diaria_ton': 15.0},
    {'nombre': 'Vertedero Municipal', 'tipo': 'vertedero', 'latitud': -20.2800, 'longitud': -70.1200, 'capacidad_diaria_ton': 100.0},
]

# Fechas: 30 días desde el 1 de septiembre de 2025
fecha_inicio = datetime(2025, 9, 1)
fechas = [fecha_inicio + timedelta(days=i) for i in range(30)]

# Opciones para clima y eventos
climas = ['soleado', 'nublado', 'mayormente soleado']
eventos = ['ninguno', 'feria_local', 'festivo']

# Simulación de datos históricos de residuos
registros = []
for calle in calles:
    for fecha in fechas:
        # Residuos base más bajos para intersecciones/puntos específicos
        if 'con' in calle['nombre']:  # Es una intersección
            residuos_kg = np.random.randint(30, 100)  # Menos residuos en intersecciones
        elif 'Pje.' in calle['nombre']:  # Es un pasaje
            residuos_kg = np.random.randint(20, 80)   # Pasajes generan menos residuos
        else:  # Calle completa
            residuos_kg = np.random.randint(50, 150)  # Calles completas más residuos
            
        personal = np.random.randint(2, 4)     # personas
        clima = random.choice(climas)
        evento = random.choices(eventos, weights=[0.75, 0.15, 0.1])[0]
        
        # Variación por eventos
        if evento == 'feria_local':
            residuos_kg = int(residuos_kg * 1.4)
        elif evento == 'festivo':
            residuos_kg = int(residuos_kg * 1.2)
            
        # Variación por día de la semana (más residuos en lunes post fin de semana)
        if fecha.weekday() == 0:  # Lunes
            residuos_kg = int(residuos_kg * 1.15)
        
        # Seleccionar aleatoriamente un camión, operador y punto de disposición
        camion = random.choice(camiones)
        operador = random.choice(operadores)
        punto_disp = random.choice(puntos_disposicion)
            
        registros.append({
            # Zona
            'id_zona': calle['id_zona'],
            'nombre_zona': zonas[1]['nombre'],
            'tipo_zona': zonas[1]['tipo'],
            'prioridad': zonas[1]['prioridad'],
            
            # Punto de recolección
            'punto_recoleccion': calle['nombre'],
            'tipo_punto': calle['tipo'],
            
            # Datos del residuo
            'fecha': fecha.strftime('%Y-%m-%d'),
            'residuos_kg': residuos_kg,
            'clima': clima,
            'evento': evento,
            'dia_semana': dias_semana_espanol[fecha.weekday()],
            'es_fin_semana': 1 if fecha.weekday() >= 5 else 0,
            
            # Camión
            'patente_camion': camion['patente'],
            'capacidad_kg': camion['capacidad_kg'],
            'consumo_km_l': camion['consumo_km_l'],
            'tipo_combustible': camion['tipo_combustible'],
            'estado_operativo': camion['estado_operativo'],
            'gps_id': camion['gps_id'],
            
            # Operador
            'nombre_operador': operador['nombre'],
            'cedula_operador': operador['cedula'],
            'especialidad_operador': operador['especialidad'],
            'personal': personal,
            
            # Punto de disposición
            'nombre_punto_disp': punto_disp['nombre'],
            'tipo_punto_disp': punto_disp['tipo'],
            'latitud_punto_disp': punto_disp['latitud'],
            'longitud_punto_disp': punto_disp['longitud'],
            'capacidad_diaria_ton': punto_disp['capacidad_diaria_ton'],
        })

# Crear DataFrame
df = pd.DataFrame(registros)

# Mostrar resumen
print("=" * 100)
print("DATOS GENERADOS - SECTOR SUR DE IQUIQUE")
print("=" * 100)
print(f"\nTotal de registros: {len(df)}")
print(f"Período: {fechas[0].strftime('%Y-%m-%d')} al {fechas[-1].strftime('%Y-%m-%d')}")
print(f"Puntos de recolección: {len(calles)}")
print(f"Camiones disponibles: {len(camiones)}")
print(f"Operadores disponibles: {len(operadores)}")
print(f"Puntos de disposición: {len(puntos_disposicion)}")
print(f"Zona: {zonas[1]['nombre']} ({zonas[1]['tipo']})")

print(f"\n{'='*100}")
print("TIPOS DE PUNTOS DE RECOLECCIÓN:")
print(f"{'='*100}")
intersecciones = len([c for c in calles if 'con' in c['nombre']])
pasajes = len([c for c in calles if 'Pje.' in c['nombre']])
calles_completas = len(calles) - intersecciones - pasajes
print(f"  Intersecciones: {intersecciones}")
print(f"  Pasajes: {pasajes}")
print(f"  Calles completas: {calles_completas}")

print(f"\n{'='*100}")
print("CAMIONES:")
print(f"{'='*100}")
for i, c in enumerate(camiones, 1):
    print(f"  {i}. {c['patente']:<12} | Cap: {c['capacidad_kg']} kg | Consumo: {c['consumo_km_l']} km/l | Estado: {c['estado_operativo']}")

print(f"\n{'='*100}")
print("OPERADORES:")
print(f"{'='*100}")
for i, o in enumerate(operadores, 1):
    print(f"  {i}. {o['nombre']:<25} | Cédula: {o['cedula']:<15} | Especialidad: {o['especialidad']}")

print(f"\n{'='*100}")
print("PUNTOS DE DISPOSICIÓN:")
print(f"{'='*100}")
for i, p in enumerate(puntos_disposicion, 1):
    print(f"  {i}. {p['nombre']:<30} | Tipo: {p['tipo']:<15} | Cap: {p['capacidad_diaria_ton']} ton/día")

print(f"\n{'='*100}")
print("PRIMERAS 10 FILAS:")
print(f"{'='*100}")
print(df.head(10).to_string())

print(f"\n{'='*100}")
print("ESTADÍSTICAS DE RESIDUOS (KG):")
print(f"{'='*100}")
print(df['residuos_kg'].describe())

print(f"\n{'='*100}")
print("DISTRIBUCIÓN POR DÍA DE LA SEMANA:")
print(f"{'='*100}")
print(df.groupby('dia_semana')['residuos_kg'].agg(['count', 'mean', 'sum']).round(2))

# Guardar a CSV
df.to_csv('datos_residuos_iquique.csv', index=False)

print("\n" + "=" * 100)
print("✓ ARCHIVO CSV GENERADO: datos_residuos_iquique.csv")
print("=" * 100)
print(f"Total de registros guardados: {len(df)}")
print(f"Total de columnas: {len(df.columns)}")
print(f"\nColumnas:\n{', '.join(df.columns)}")
print("=" * 100)