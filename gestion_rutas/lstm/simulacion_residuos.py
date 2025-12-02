import pandas as pd
import numpy as np
import random
import string
from datetime import datetime, timedelta
import requests
import time

# Solo una zona: Sector Sur de Iquique
zonas = {
    1: {'nombre': 'Sector Sur Iquique', 'tipo': 'residencial', 'prioridad': 1},
}

# Función para obtener coordenadas desde Nominatim (OpenStreetMap)
def obtener_coordenadas(calle_nombre):
    """
    Obtiene latitud y longitud de una calle usando la API Nominatim de OpenStreetMap
    """
    try:
        # Construir la búsqueda con ubicación específica (Iquique, Chile)
        query = f"{calle_nombre}, Iquique, Region de Tarapaca, Chile"
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            'q': query,
            'format': 'json',
            'limit': 1
        }
        
        headers = {
            'User-Agent': 'LAR-Waste-Management-System/1.0'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=5)
        time.sleep(1)  # Respetar rate limit de Nominatim (1 segundo entre requests)
        
        if response.status_code == 200 and len(response.json()) > 0:
            resultado = response.json()[0]
            return float(resultado['lat']), float(resultado['lon'])
        else:
            # Si no encuentra la calle exacta, devolver coordenadas aproximadas del Sector Sur
            return None, None
            
    except Exception as e:
        print(f"Error al consultar API para {calle_nombre}: {e}")
        return None, None

# Calles reales del sector sur de Iquique con intersecciones específicas
# Con coordenadas aproximadas (Sector Sur Iquique)
calles = [
    # Avenidas principales con intersecciones
    {'nombre': 'Av. Ramon Perez Opazo con Av. La Tirana', 'id_zona': 1, 'tipo': 'contenedor', 'latitud': -20.252023166927483, 'longitud': -70.1267528568074},
    {'nombre': 'Padre Hurtado con Av. La Tirana', 'id_zona': 1, 'tipo': 'contenedor', 'latitud': -20.25993966543772, 'longitud': -70.12491010809157},
    {'nombre': 'Padre Hurtado con Tamarugal', 'id_zona': 1, 'tipo': 'contenedor', 'latitud': -20.2520, 'longitud': -70.1530},
    {'nombre': 'Padre Hurtado con Los Chunchos', 'id_zona': 1, 'tipo': 'contenedor', 'latitud': -20.2525, 'longitud': -70.1535},
    {'nombre': 'Padre Hurtado con Av. Cinco', 'id_zona': 1, 'tipo': 'contenedor', 'latitud': -20.2530, 'longitud': -70.1540},
    
    {'nombre': 'Av. La Tirana con Tamarugal', 'id_zona': 1, 'tipo': 'contenedor', 'latitud': -20.2535, 'longitud': -70.1545},
    {'nombre': 'Av. La Tirana con Ontario', 'id_zona': 1, 'tipo': 'contenedor', 'latitud': -20.2540, 'longitud': -70.1550},
    {'nombre': 'Av. La Tirana con Toronto', 'id_zona': 1, 'tipo': 'contenedor', 'latitud': -20.2545, 'longitud': -70.1555},
    {'nombre': 'Av. La Tirana con Teresa Wilms Mont', 'id_zona': 1, 'tipo': 'contenedor', 'latitud': -20.2550, 'longitud': -70.1560},
    
    {'nombre': 'Tamarugal con Los Chunchos', 'id_zona': 1, 'tipo': 'contenedor', 'latitud': -20.2555, 'longitud': -70.1565},
    {'nombre': 'Tamarugal con C. Uno', 'id_zona': 1, 'tipo': 'contenedor', 'latitud': -20.2560, 'longitud': -70.1570},
    {'nombre': 'Tamarugal con Ontario', 'id_zona': 1, 'tipo': 'contenedor', 'latitud': -20.2565, 'longitud': -70.1575},
    
    {'nombre': 'Av. Cinco con Pje. Uno', 'id_zona': 1, 'tipo': 'contenedor', 'latitud': -20.2570, 'longitud': -70.1580},
    {'nombre': 'Av. Cinco con Pje. Tres', 'id_zona': 1, 'tipo': 'contenedor', 'latitud': -20.2575, 'longitud': -70.1585},
    {'nombre': 'Av. Cinco con Pje. Cinco', 'id_zona': 1, 'tipo': 'contenedor', 'latitud': -20.2580, 'longitud': -70.1590},
    
    # Calles secundarias
    {'nombre': 'C. Uno', 'id_zona': 1, 'tipo': 'contenedor', 'latitud': -20.2585, 'longitud': -70.1595},
    {'nombre': 'Pje. Dos', 'id_zona': 1, 'tipo': 'contenedor', 'latitud': -20.2590, 'longitud': -70.1600},
    {'nombre': 'Los Chunchos', 'id_zona': 1, 'tipo': 'contenedor', 'latitud': -20.2595, 'longitud': -70.1605},
    {'nombre': 'Ontario', 'id_zona': 1, 'tipo': 'contenedor', 'latitud': -20.2600, 'longitud': -70.1610},
    {'nombre': 'Via Local Dos', 'id_zona': 1, 'tipo': 'contenedor', 'latitud': -20.2605, 'longitud': -70.1615},
    {'nombre': 'Toronto', 'id_zona': 1, 'tipo': 'contenedor', 'latitud': -20.2610, 'longitud': -70.1620},
    {'nombre': 'C. Seis', 'id_zona': 1, 'tipo': 'contenedor', 'latitud': -20.2615, 'longitud': -70.1625},
    {'nombre': 'Teresa Wilms Mont', 'id_zona': 1, 'tipo': 'contenedor', 'latitud': -20.2620, 'longitud': -70.1630},
    
    # Pasajes cortos
    {'nombre': 'Pje. C', 'id_zona': 1, 'tipo': 'contenedor', 'latitud': -20.2625, 'longitud': -70.1635},
    {'nombre': 'Pje. B', 'id_zona': 1, 'tipo': 'contenedor', 'latitud': -20.2630, 'longitud': -70.1640},
    {'nombre': 'Pje. A', 'id_zona': 1, 'tipo': 'contenedor', 'latitud': -20.2635, 'longitud': -70.1645},
    {'nombre': 'Pje. Uno', 'id_zona': 1, 'tipo': 'contenedor', 'latitud': -20.2640, 'longitud': -70.1650},
    {'nombre': 'Pje. Tres', 'id_zona': 1, 'tipo': 'contenedor', 'latitud': -20.2645, 'longitud': -70.1655},
    {'nombre': 'Pje. Siete', 'id_zona': 1, 'tipo': 'contenedor', 'latitud': -20.2650, 'longitud': -70.1660},
    {'nombre': 'Pje. Cinco', 'id_zona': 1, 'tipo': 'contenedor', 'latitud': -20.2655, 'longitud': -70.1665},
    {'nombre': 'Pje. Seis', 'id_zona': 1, 'tipo': 'contenedor', 'latitud': -20.2660, 'longitud': -70.1670},
    {'nombre': 'Pje. Ocho', 'id_zona': 1, 'tipo': 'contenedor', 'latitud': -20.2665, 'longitud': -70.1675},
    
    # Calles de zona residencial
    {'nombre': 'Nueva Cuatro', 'id_zona': 1, 'tipo': 'contenedor', 'latitud': -20.2670, 'longitud': -70.1680},
    {'nombre': 'Ines Solari Magnaso', 'id_zona': 1, 'tipo': 'contenedor', 'latitud': -20.2675, 'longitud': -70.1685},
    {'nombre': 'Los Alagarrobos', 'id_zona': 1, 'tipo': 'contenedor', 'latitud': -20.2680, 'longitud': -70.1690},
    {'nombre': 'La Chamiza', 'id_zona': 1, 'tipo': 'contenedor', 'latitud': -20.2685, 'longitud': -70.1695},
    {'nombre': 'Lebu', 'id_zona': 1, 'tipo': 'contenedor', 'latitud': -20.2690, 'longitud': -70.1700},
    {'nombre': 'Pje. Traiguen', 'id_zona': 1, 'tipo': 'contenedor', 'latitud': -20.2695, 'longitud': -70.1705},
    {'nombre': 'Pje. Temuco', 'id_zona': 1, 'tipo': 'contenedor', 'latitud': -20.2700, 'longitud': -70.1710},
    
    # Zona de cerros con intersecciones principales
    {'nombre': 'Cerro Colorado con C. Int Dos', 'id_zona': 1, 'tipo': 'contenedor', 'latitud': -20.2705, 'longitud': -70.1715},
    {'nombre': 'Cerro Colorado con C. Int Tres', 'id_zona': 1, 'tipo': 'contenedor', 'latitud': -20.2710, 'longitud': -70.1720},
    {'nombre': 'Cerro Colorado con C. Int Cuatro', 'id_zona': 1, 'tipo': 'contenedor', 'latitud': -20.2715, 'longitud': -70.1725},
    
    {'nombre': 'C. Int Dos', 'id_zona': 1, 'tipo': 'contenedor', 'latitud': -20.2720, 'longitud': -70.1730},
    {'nombre': 'C. Int Tres', 'id_zona': 1, 'tipo': 'contenedor', 'latitud': -20.2725, 'longitud': -70.1735},
    {'nombre': 'C. Int Cuatro', 'id_zona': 1, 'tipo': 'contenedor', 'latitud': -20.2730, 'longitud': -70.1740},
    
    {'nombre': 'Cerro Casiri', 'id_zona': 1, 'tipo': 'contenedor', 'latitud': -20.2735, 'longitud': -70.1745},
    {'nombre': 'Coscaya', 'id_zona': 1, 'tipo': 'contenedor', 'latitud': -20.2740, 'longitud': -70.1750},
    {'nombre': 'Sauna', 'id_zona': 1, 'tipo': 'contenedor', 'latitud': -20.2745, 'longitud': -70.1755},
    {'nombre': 'Patara', 'id_zona': 1, 'tipo': 'contenedor', 'latitud': -20.2750, 'longitud': -70.1760},
    {'nombre': 'Cerro Yabricoya', 'id_zona': 1, 'tipo': 'contenedor', 'latitud': -20.2755, 'longitud': -70.1765},
    {'nombre': 'Chiza', 'id_zona': 1, 'tipo': 'contenedor', 'latitud': -20.2760, 'longitud': -70.1770},
    {'nombre': 'Chauca', 'id_zona': 1, 'tipo': 'contenedor', 'latitud': -20.2765, 'longitud': -70.1775},
    {'nombre': 'Calaunsa', 'id_zona': 1, 'tipo': 'contenedor', 'latitud': -20.2770, 'longitud': -70.1780},
    {'nombre': 'Napa', 'id_zona': 1, 'tipo': 'contenedor', 'latitud': -20.2775, 'longitud': -70.1785},
    
    # Zona con nombres de personajes/lugares
    {'nombre': 'Humberto Lizardi Flores', 'id_zona': 1, 'tipo': 'contenedor', 'latitud': -20.2780, 'longitud': -70.1790},
    {'nombre': 'Tres Marias', 'id_zona': 1, 'tipo': 'contenedor', 'latitud': -20.2785, 'longitud': -70.1795},
    {'nombre': 'Avenida Proyectada', 'id_zona': 1, 'tipo': 'contenedor', 'latitud': -20.2790, 'longitud': -70.1800},
    {'nombre': 'Jardines Del Desierto', 'id_zona': 1, 'tipo': 'contenedor', 'latitud': -20.2795, 'longitud': -70.1805},
    
    # Zona de minerales con intersecciones
    {'nombre': 'Los Mineros con Fanerita', 'id_zona': 1, 'tipo': 'contenedor', 'latitud': -20.2800, 'longitud': -70.1810},
    {'nombre': 'Los Mineros con Calcopirita', 'id_zona': 1, 'tipo': 'contenedor', 'latitud': -20.2805, 'longitud': -70.1815},
    {'nombre': 'Los Mineros con Sulfuros', 'id_zona': 1, 'tipo': 'contenedor', 'latitud': -20.2810, 'longitud': -70.1820},
    
    {'nombre': 'Fanerita', 'id_zona': 1, 'tipo': 'contenedor', 'latitud': -20.2815, 'longitud': -70.1825},
    {'nombre': 'Calcopirita', 'id_zona': 1, 'tipo': 'contenedor', 'latitud': -20.2820, 'longitud': -70.1830},
    {'nombre': 'Crisocola', 'id_zona': 1, 'tipo': 'contenedor', 'latitud': -20.2825, 'longitud': -70.1835},
    {'nombre': 'Sulfuros', 'id_zona': 1, 'tipo': 'contenedor', 'latitud': -20.2830, 'longitud': -70.1840},
    {'nombre': 'Cuarzo', 'id_zona': 1, 'tipo': 'contenedor', 'latitud': -20.2835, 'longitud': -70.1845},
    {'nombre': 'Filones', 'id_zona': 1, 'tipo': 'contenedor', 'latitud': -20.2840, 'longitud': -70.1850},
    {'nombre': 'Pje. Granodiorita', 'id_zona': 1, 'tipo': 'contenedor', 'latitud': -20.2845, 'longitud': -70.1855},
    {'nombre': 'Azurita', 'id_zona': 1, 'tipo': 'contenedor', 'latitud': -20.2850, 'longitud': -70.1860},
    {'nombre': 'Pirita', 'id_zona': 1, 'tipo': 'contenedor', 'latitud': -20.2855, 'longitud': -70.1865},
    {'nombre': 'Feldespato', 'id_zona': 1, 'tipo': 'contenedor', 'latitud': -20.2860, 'longitud': -70.1870},
    {'nombre': 'Apilita', 'id_zona': 1, 'tipo': 'contenedor', 'latitud': -20.2865, 'longitud': -70.1875},
    {'nombre': 'Matendisita', 'id_zona': 1, 'tipo': 'contenedor', 'latitud': -20.2870, 'longitud': -70.1880},
    {'nombre': 'Malaquita', 'id_zona': 1, 'tipo': 'contenedor', 'latitud': -20.2875, 'longitud': -70.1885},
]

# Mapeo de días de la semana al español
dias_semana_espanol = {
    0: 'Lunes',
    1: 'Martes',
    2: 'Miercoles',
    3: 'Jueves',
    4: 'Viernes',
    5: 'Sabado',
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

# Fechas: 365 días (1 año) para datos más realistas
fecha_inicio = datetime(2024, 1, 1)
fechas = [fecha_inicio + timedelta(days=i) for i in range(365)]

# Opciones para clima y eventos
climas = ['soleado', 'nublado', 'mayormente soleado']
eventos = ['ninguno', 'feria_local', 'festivo']

# BALANCE ÓPTIMO: Patrón claro con variación moderada
registros = []

# Tendencia mensual SUAVE (no tan pronunciada)
ruido_mensual = [0.92, 0.94, 0.96, 0.98, 1.00, 1.02, 1.04, 1.06, 1.04, 1.02, 1.00, 0.96]

# Solo 3-4 semanas atípicas al año (no 8)
semanas_atipicas = set(np.random.choice(range(52), size=4, replace=False))

# Cada calle tiene comportamiento único pero NO tan extremo
perfiles_calles = {}
for calle in calles:
    perfiles_calles[calle['nombre']] = {
        'base_multiplicador': np.random.uniform(0.88, 1.12),  # Más cercano a 1
        'tiene_patron_semanal': np.random.random() > 0.15,  # 85% tienen patrón (antes era 70%)
        'intensidad_patron': np.random.uniform(0.75, 1.25),  # Menos extremo
    }

for calle in calles:
    perfil = perfiles_calles[calle['nombre']]
    
    for fecha in fechas:
        mes = fecha.month - 1
        semana_del_año = fecha.isocalendar()[1]
        es_semana_atipica = semana_del_año in semanas_atipicas
        
        # Base de residuos más consistente
        if 'con' in calle['nombre']:  # Intersección
            residuos_kg = np.random.uniform(45, 95)
        elif 'Pje.' in calle['nombre']:  # Pasaje
            residuos_kg = np.random.uniform(35, 80)
        else:  # Calle completa
            residuos_kg = np.random.uniform(65, 155)
        
        # Aplicar multiplicador único de la calle
        residuos_kg *= perfil['base_multiplicador']
        
        # Tendencia mensual suave
        residuos_kg *= ruido_mensual[mes]
        
        dia_semana = fecha.weekday()
        
        # Si la calle tiene patrón semanal Y no es semana atípica
        if perfil['tiene_patron_semanal'] and not es_semana_atipica:
            # Patrón semanal con MÁS variabilidad en los extremos
            if dia_semana == 0:  # Lunes
                factor_dia = np.random.uniform(1.05, 1.40)
            elif dia_semana == 1:  # Martes  
                factor_dia = np.random.uniform(0.90, 1.25)
            elif dia_semana == 2:  # Miércoles
                factor_dia = np.random.uniform(1.15, 1.50)
            elif dia_semana == 3:  # Jueves
                factor_dia = np.random.uniform(1.15, 1.50)
            elif dia_semana == 4:  # Viernes
                factor_dia = np.random.uniform(1.00, 1.35)
            elif dia_semana == 5:  # Sábado
                # Sábado con MUCHA más variabilidad - a veces bajo, a veces no tanto
                factor_dia = np.random.uniform(0.65, 1.10)
            else:  # Domingo
                # Domingo con RANGO MÁS AMPLIO - romper el valle consistente
                factor_dia = np.random.uniform(0.55, 1.05)
            
            # Aplicar intensidad del patrón
            factor_dia = 1.0 + (factor_dia - 1.0) * perfil['intensidad_patron']
        else:
            # Sin patrón pero no tan aleatorio
            factor_dia = np.random.uniform(0.85, 1.30)
        
        residuos_kg *= factor_dia
        
        # Ruido diario MODERADO
        ruido_diario = np.random.uniform(0.88, 1.18)
        residuos_kg *= ruido_diario
        
        # Semanas atípicas tienen ruido adicional pero no extremo
        if es_semana_atipica:
            residuos_kg *= np.random.uniform(0.85, 1.25)
            
        personal = np.random.randint(2, 4)
        clima = random.choice(climas)
        evento = random.choices(eventos, weights=[0.76, 0.12, 0.08, 0.04])[0]
        
        # Variación por eventos MODERADA
        if evento == 'feria_local':
            residuos_kg *= np.random.uniform(1.20, 1.45)
        elif evento == 'festivo':
            residuos_kg *= np.random.uniform(0.85, 1.20)
        elif evento == 'evento_deportivo':
            residuos_kg *= np.random.uniform(1.10, 1.35)
        
        # Convertir a entero
        residuos_kg = max(20, int(residuos_kg))  # Mínimo 20kg
        
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
            'latitud_punto_recoleccion': calle['latitud'],
            'longitud_punto_recoleccion': calle['longitud'],
            
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
print(f"Periodo: {fechas[0].strftime('%Y-%m-%d')} al {fechas[-1].strftime('%Y-%m-%d')}")
print(f"Puntos de recoleccion: {len(calles)}")
print(f"Camiones disponibles: {len(camiones)}")
print(f"Operadores disponibles: {len(operadores)}")
print(f"Puntos de disposicion: {len(puntos_disposicion)}")
print(f"Zona: {zonas[1]['nombre']} ({zonas[1]['tipo']})")

print(f"\n{'='*100}")
print("TIPOS DE PUNTOS DE RECOLECCION:")
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
print("PUNTOS DE DISPOSICION:")
print(f"{'='*100}")
for i, p in enumerate(puntos_disposicion, 1):
    print(f"  {i}. {p['nombre']:<30} | Tipo: {p['tipo']:<15} | Cap: {p['capacidad_diaria_ton']} ton/dia")

print(f"\n{'='*100}")
print("PRIMERAS 10 FILAS:")
print(f"{'='*100}")
print(df.head(10).to_string())

print(f"\n{'='*100}")
print("ESTADISTICAS DE RESIDUOS (KG):")
print(f"{'='*100}")
print(df['residuos_kg'].describe())

print(f"\n{'='*100}")
print("DISTRIBUCION POR DIA DE LA SEMANA:")
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

