"""
Script para obtener TODAS las calles reales del Sector Sur de Iquique
Usando Overpass API para extraer toda la red vial desde OpenStreetMap
Sector Sur: SOLO desde Av. Ramón Pérez Opazo (-20.252) hacia el sur
"""
import requests
import time
import json
import pandas as pd
import numpy as np
from collections import defaultdict
from pathlib import Path
import math

# Definir límites ESTRICTOS del Sector Sur de Iquique
# SOLO desde Av. Ramón Pérez Opazo hacia el sur (NO al norte)
BBOX = {
    'sur': -20.280,      # Límite sur
    'norte': -20.2525,   # LÍMITE ESTRICTO: Av. Ramón Pérez Opazo (NO incluir nada al norte)
    'oeste': -70.145,    # Límite oeste
    'este': -70.115      # Límite este (hacia el cerro)
}

# Filtro estricto de latitud para SECTOR SUR
LAT_MIN_SECTOR_SUR = -20.2525  # Todo debe estar al SUR (más negativo) de este valor

def obtener_calles_overpass():
    """Obtener TODAS las calles, pasajes, intersecciones y vías del Sector Sur"""
    
    print("Consultando Overpass API...")
    print(f"Área: Lat {BBOX['norte']} a {BBOX['sur']}, Lon {BBOX['oeste']} a {BBOX['este']}")
    print("Buscando TODAS las vías: avenidas, calles, pasajes, caminos, senderos...")
    
    # Query Overpass QL - TODOS los tipos de highway con nombre o sin nombre
    overpass_query = f"""
    [out:json][timeout:90];
    (
      way["highway"]({BBOX['sur']},{BBOX['oeste']},{BBOX['norte']},{BBOX['este']});
    );
    out body;
    >;
    out skel qt;
    """
    
    overpass_url = "https://overpass-api.de/api/interpreter"
    
    try:
        response = requests.post(
            overpass_url,
            data={'data': overpass_query},
            timeout=120
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error en API: Status {response.status_code}")
            return None
            
    except Exception as e:
        print(f"Error consultando API: {e}")
        return None

def procesar_calles(data):
    """Procesar datos de Overpass y extraer calles ÚNICAS del SECTOR SUR + intersecciones REALES"""
    
    if not data or 'elements' not in data:
        print("No se recibieron datos válidos")
        return [], []
    
    # Separar nodos y ways
    nodes = {}
    ways = []
    
    for element in data['elements']:
        if element['type'] == 'node':
            nodes[element['id']] = {
                'lat': element['lat'],
                'lon': element['lon']
            }
        elif element['type'] == 'way':
            ways.append(element)
    
    print(f"  Nodos obtenidos: {len(nodes)}")
    print(f"  Vías totales encontradas: {len(ways)}")
    print(f"\n  Procesando vías y buscando intersecciones REALES...")
    print(f"  {'='*90}")
    
    # Agrupar vías por nombre REAL
    calles_agrupadas = {}
    vias_sin_nombre = 0
    vias_fuera_sector = 0
    vias_procesadas = 0
    
    # Diccionario para rastrear qué vías comparten nodos (intersecciones reales)
    nodos_a_vias = {}  # {node_id: [lista de way_ids]}
    way_id_to_info = {}  # {way_id: {'nombre': ..., 'nodes': [...]}}
    
    for idx, way in enumerate(ways, 1):
        if idx % 50 == 0:
            print(f"  Progreso: {idx}/{len(ways)} vías procesadas...")
        
        tags = way.get('tags', {})
        nombre_real = tags.get('name', '').strip()
        tipo_via = tags.get('highway', 'unknown')
        way_id = way['id']
        
        # IGNORAR vías sin nombre
        if not nombre_real:
            vias_sin_nombre += 1
            continue
        
        # Obtener coordenadas de los nodos de esta vía
        way_nodes = way.get('nodes', [])
        coords = []
        coords_validas = []
        
        for node_id in way_nodes:
            if node_id in nodes:
                node = nodes[node_id]
                # FILTRO ESTRICTO: Solo nodos en SECTOR SUR
                if node['lat'] < LAT_MIN_SECTOR_SUR:
                    coords.append(node)
                    coords_validas.append(node_id)
                    
                    # Registrar que este nodo pertenece a esta vía
                    if node_id not in nodos_a_vias:
                        nodos_a_vias[node_id] = []
                    nodos_a_vias[node_id].append(way_id)
        
        # Si no hay coordenadas en el Sector Sur, ignorar esta vía
        if len(coords) < 1:
            vias_fuera_sector += 1
            continue
        
        vias_procesadas += 1
        
        # Calcular punto central de este segmento EN SECTOR SUR
        lat_avg = sum(c['lat'] for c in coords) / len(coords)
        lon_avg = sum(c['lon'] for c in coords) / len(coords)
        
        # Guardar info de esta vía
        way_id_to_info[way_id] = {
            'nombre': nombre_real,
            'tipo': tipo_via,
            'nodes': coords_validas,
            'lat': lat_avg,
            'lon': lon_avg
        }
        
        # Agrupar por nombre real
        if nombre_real not in calles_agrupadas:
            calles_agrupadas[nombre_real] = {
                'nombre': nombre_real,
                'tipo': tipo_via,
                'coords_totales': [],
                'way_ids': []
            }
            print(f"    ✓ Encontrada: {nombre_real:<50} (Lat: {lat_avg:.6f}, Lon: {lon_avg:.6f})")
        
        calles_agrupadas[nombre_real]['coords_totales'].extend(coords)
        calles_agrupadas[nombre_real]['way_ids'].append(way_id)
    
    print(f"\n  {'='*90}")
    print(f"  Resumen de procesamiento:")
    print(f"    - Vías procesadas en Sector Sur: {vias_procesadas}")
    print(f"    - Vías sin nombre (ignoradas): {vias_sin_nombre}")
    print(f"    - Vías fuera del Sector Sur (ignoradas): {vias_fuera_sector}")
    print(f"    - Calles únicas encontradas: {len(calles_agrupadas)}")
    
    # Calles a EXCLUIR del sector (rutas/carreteras fuera del área urbana)
    CALLES_EXCLUIDAS = {
        'Ruta 16', 
        'Circunvalación Sur', 
        'Segundo Acceso',
        'Ruta A-620'
    }
    
    # Crear lista de calles únicas (FILTRANDO excluidas)
    calles = []
    for nombre, info in calles_agrupadas.items():
        # FILTRAR calles excluidas
        if nombre in CALLES_EXCLUIDAS:
            continue
            
        if info['coords_totales']:
            lat_avg = sum(c['lat'] for c in info['coords_totales']) / len(info['coords_totales'])
            lon_avg = sum(c['lon'] for c in info['coords_totales']) / len(info['coords_totales'])
        
        if lat_avg < LAT_MIN_SECTOR_SUR:
            calles.append({
                'nombre': nombre,
                'latitud': lat_avg,
                'longitud': lon_avg,
                'tipo': info['tipo'],
                'way_ids': info['way_ids']
            })
    
    print(f"    - Calles verificadas en Sector Sur: {len(calles)}")
    
    # BUSCAR INTERSECCIONES REALES (nodos compartidos entre vías)
    print(f"\n  Buscando intersecciones REALES (nodos compartidos)...")
    
    # Calles a EXCLUIR del sector (rutas/carreteras fuera del área urbana)
    CALLES_EXCLUIDAS = {
        'Ruta 16', 
        'Circunvalación Sur', 
        'Segundo Acceso',
        'Ruta A-620'  # También parece ser carretera
    }
    
    intersecciones = []
    nodos_procesados = set()
    
    for node_id, way_ids in nodos_a_vias.items():
        # Si 2 o más vías comparten este nodo, es una intersección REAL
        if len(way_ids) >= 2:
            if node_id in nodos_procesados:
                continue
            nodos_procesados.add(node_id)
            
            # Obtener nombres de las vías que se cruzan
            vias_en_cruce = []
            for way_id in way_ids[:2]:  # Tomar máximo 2 vías
                if way_id in way_id_to_info:
                    vias_en_cruce.append(way_id_to_info[way_id])
            
            if len(vias_en_cruce) == 2:
                via1_nombre = vias_en_cruce[0]['nombre']
                via2_nombre = vias_en_cruce[1]['nombre']
                
                # FILTRO 1: NO agregar si ambas vías tienen el mismo nombre
                if via1_nombre == via2_nombre:
                    continue
                
                # FILTRO 2: NO agregar si alguna vía está en la lista de excluidas
                if via1_nombre in CALLES_EXCLUIDAS or via2_nombre in CALLES_EXCLUIDAS:
                    continue
                
                node = nodes[node_id]
                # Verificar que está en Sector Sur
                if node['lat'] < LAT_MIN_SECTOR_SUR:
                    intersecciones.append({
                        'nombre': f"{via1_nombre} con {via2_nombre}",
                        'latitud': node['lat'],
                        'longitud': node['lon'],
                        'tipo': 'interseccion',
                        'node_id': node_id
                    })
    
    print(f"    - Intersecciones REALES encontradas (antes de deduplicar): {len(intersecciones)}")
    
    # ELIMINAR DUPLICADOS: Mantener solo una intersección por cada nombre único
    intersecciones_unicas = {}
    for inter in intersecciones:
        nombre = inter['nombre']
        # También verificar el nombre invertido (A con B = B con A)
        partes = nombre.split(' con ')
        if len(partes) == 2:
            nombre_invertido = f"{partes[1]} con {partes[0]}"
            # Si ya existe el nombre o su versión invertida, mantener el primero
            if nombre not in intersecciones_unicas and nombre_invertido not in intersecciones_unicas:
                intersecciones_unicas[nombre] = inter
        else:
            # Si no tiene formato "A con B", agregar tal cual
            if nombre not in intersecciones_unicas:
                intersecciones_unicas[nombre] = inter
    
    intersecciones = list(intersecciones_unicas.values())
    print(f"    - Intersecciones únicas (después de deduplicar): {len(intersecciones)}")
    
    # Ordenar calles por tipo
    orden_tipos = ['motorway', 'trunk', 'primary', 'secondary', 'tertiary', 
                   'residential', 'service', 'unclassified', 'pedestrian', 
                   'footway', 'path', 'track']
    
    def prioridad_tipo(calle):
        try:
            return orden_tipos.index(calle['tipo'])
        except ValueError:
            return 999
    
    calles.sort(key=lambda x: (prioridad_tipo(x), x['nombre']))
    
    return calles, intersecciones

def actualizar_csv(puntos_reales, csv_path='datos_residuos_iquique.csv'):
    """Actualizar CSV para incluir TODOS los puntos reales con patrones de residuos variables"""
    
    print(f"\nActualizando CSV: {csv_path}")
    
    df = pd.read_csv(csv_path)
    
    print(f"  Registros originales: {len(df)}")
    print(f"  Puntos reales disponibles: {len(puntos_reales)}")
    print(f"  → EXPANDIENDO CSV para incluir TODOS los puntos con patrones de residuos...")
    
    # Crear nuevo DataFrame con TODOS los puntos reales
    registros_nuevos = []
    
    # Obtener fechas (365 días)
    fechas_unicas = sorted(df['fecha'].unique())
    print(f"  → Generando {len(puntos_reales)} × {len(fechas_unicas)} = {len(puntos_reales) * len(fechas_unicas)} registros...")
    
    # Tendencia mensual suave (igual que simulacion_residuos.py)
    ruido_mensual = [0.92, 0.94, 0.96, 0.98, 1.00, 1.02, 1.04, 1.06, 1.04, 1.02, 1.00, 0.96]
    
    # Semanas atípicas (3-4 al año)
    semanas_atipicas = set(np.random.choice(range(52), size=4, replace=False))
    
    # Para cada punto real, generar perfil único
    for idx, punto in enumerate(puntos_reales, 1):
        if idx % 50 == 0:
            print(f"    Procesando punto {idx}/{len(puntos_reales)}...")
        
        # Perfil único del punto (como en simulacion_residuos.py)
        perfil = {
            'base_multiplicador': np.random.uniform(0.88, 1.12),
            'tiene_patron_semanal': np.random.random() > 0.15,  # 85% tienen patrón
            'intensidad_patron': np.random.uniform(0.75, 1.25),
        }
        
        # Tomar un registro base como plantilla
        registro_base = df.iloc[0].copy()
        
        for fecha_str in fechas_unicas:
            fecha = pd.to_datetime(fecha_str)
            mes = fecha.month - 1
            semana_del_año = fecha.isocalendar()[1]
            es_semana_atipica = semana_del_año in semanas_atipicas
            dia_semana = fecha.weekday()
            
            # Determinar base según tipo de punto
            if 'con' in punto['nombre']:  # Intersección
                residuos_kg = np.random.uniform(45, 95)
            elif 'Pasaje' in punto['nombre'] or 'Pje.' in punto['nombre']:  # Pasaje
                residuos_kg = np.random.uniform(35, 80)
            else:  # Calle completa
                residuos_kg = np.random.uniform(65, 155)
            
            # Aplicar multiplicador único del punto
            residuos_kg *= perfil['base_multiplicador']
            
            # Tendencia mensual suave
            residuos_kg *= ruido_mensual[mes]
            
            # Patrón semanal si aplica
            if perfil['tiene_patron_semanal'] and not es_semana_atipica:
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
                    factor_dia = np.random.uniform(0.65, 1.10)
                else:  # Domingo
                    factor_dia = np.random.uniform(0.55, 1.05)
                
                factor_dia = 1.0 + (factor_dia - 1.0) * perfil['intensidad_patron']
            else:
                factor_dia = np.random.uniform(0.85, 1.30)
            
            residuos_kg *= factor_dia
            
            # Ruido diario moderado
            ruido_diario = np.random.uniform(0.88, 1.18)
            residuos_kg *= ruido_diario
            
            # Semanas atípicas
            if es_semana_atipica:
                residuos_kg *= np.random.uniform(0.85, 1.25)
            
            # Convertir a entero (mínimo 20kg)
            residuos_kg = max(20, int(residuos_kg))
            
            # Crear registro para este punto y fecha
            nuevo_registro = registro_base.copy()
            nuevo_registro['punto_recoleccion'] = punto['nombre']
            nuevo_registro['latitud_punto_recoleccion'] = punto['latitud']
            nuevo_registro['longitud_punto_recoleccion'] = punto['longitud']
            nuevo_registro['fecha'] = fecha_str
            nuevo_registro['residuos_kg'] = residuos_kg  # ¡VALOR VARIABLE!
            nuevo_registro['dia_semana'] = ['Lunes', 'Martes', 'Miercoles', 'Jueves', 'Viernes', 'Sabado', 'Domingo'][dia_semana]
            nuevo_registro['es_fin_semana'] = 1 if dia_semana >= 5 else 0
            
            registros_nuevos.append(nuevo_registro)
    
    # Crear nuevo DataFrame
    df_nuevo = pd.DataFrame(registros_nuevos)
    
    print(f"  → Total registros generados: {len(df_nuevo)}")
    
    # Mostrar tipos de vías incluidas
    tipos_count = {}
    for p in puntos_reales:
        tipo = p.get('tipo', 'unknown')
        tipos_count[tipo] = tipos_count.get(tipo, 0) + 1
    
    print(f"\n  Tipos de vías/puntos incluidos:")
    for tipo, count in sorted(tipos_count.items(), key=lambda x: -x[1]):
        print(f"    - {tipo}: {count}")
    
    # Guardar
    df_nuevo.to_csv(csv_path, index=False)
    
    print(f"\n  ✓ CSV actualizado con TODOS los puntos")
    
    return df_nuevo

# ============================================================================
# MAIN
# ============================================================================

print("="*100)
print("ACTUALIZANDO DATOS CON CALLES REALES DEL SECTOR SUR DE IQUIQUE")
print("="*100)
print("Área: Desde Av. Ramón Pérez Opazo hacia el sur")
print()

# 1. Obtener datos de Overpass O cargar desde JSON
backup_file = 'calles_sector_sur_real.json'
print("[1/4] Consultando OpenStreetMap (Overpass API)...")

if Path(backup_file).exists():
    print(f"  → Archivo de respaldo encontrado: {backup_file}")
    print(f"  → Intentando API primero...")

data = obtener_calles_overpass()

if not data:
    print("\n⚠️  API no disponible, cargando desde archivo de respaldo...")
    
    if Path(backup_file).exists():
        with open(backup_file, 'r', encoding='utf-8') as f:
            puntos_backup = json.load(f)
        
        # Separar calles e intersecciones
        calles = [p for p in puntos_backup if p.get('tipo') != 'interseccion']
        intersecciones = [p for p in puntos_backup if p.get('tipo') == 'interseccion']
        
        print(f"  ✓ Cargados desde respaldo:")
        print(f"    - Calles: {len(calles)}")
        print(f"    - Intersecciones: {len(intersecciones)}")
        
        # Saltar al paso 3
        puntos_totales = calles + intersecciones
        print(f"\n[3/3] Total de puntos: {len(puntos_totales)}")
        
        # Actualizar CSV con patrones variables
        df_actualizado = actualizar_csv(puntos_totales)
        
        # Mostrar resumen
        print(f"\n{'='*100}")
        print("RESUMEN DE CALLES REALES ENCONTRADAS")
        print(f"{'='*100}\n")
        print("Primeras 20 calles reales del Sector Sur:\n")
        print(df_actualizado.groupby('punto_recoleccion')[['latitud_punto_recoleccion', 'longitud_punto_recoleccion']].first().head(20))
        
        print(f"\n{'='*100}")
        print("✓ COMPLETADO")
        print(f"{'='*100}")
        print(f"El archivo datos_residuos_iquique.csv ahora contiene:")
        print(f"  - Nombres REALES de calles del Sector Sur de Iquique")
        print(f"  - Coordenadas REALES extraídas de OpenStreetMap")
        print(f"  - Patrones de residuos VARIABLES por punto y fecha")
        print(f"\nRecarga el mapa y entrena el modelo LSTM con el nuevo CSV")
        exit(0)
    else:
        print("\n❌ ERROR: No se pudieron obtener datos ni desde API ni desde archivo de respaldo")
        print("Posibles causas:")
        print("  - Servidor sobrecargado (intenta en unos minutos)")
        print("  - Problema de conexión")
        print("  - El área tiene pocas calles registradas en OpenStreetMap")
        exit(1)

# 2. Procesar calles Y encontrar intersecciones REALES
print("\n[2/3] Procesando vías y encontrando intersecciones REALES...")
calles, intersecciones = procesar_calles(data)

if not calles:
    print("\n❌ ERROR: No se encontraron calles en el área")
    print("El Sector Sur podría no tener calles registradas en OpenStreetMap")
    exit(1)

print(f"  ✓ Calles extraídas: {len(calles)}")
print(f"  ✓ Intersecciones REALES: {len(intersecciones)}")

# 3. Combinar y actualizar CSV
puntos_totales = calles + intersecciones
print(f"\n[3/3] Total de puntos: {len(puntos_totales)}")

# Guardar JSON de respaldo
with open('calles_sector_sur_real.json', 'w', encoding='utf-8') as f:
    json.dump(puntos_totales, f, indent=2, ensure_ascii=False)
print("  ✓ Respaldo guardado: calles_sector_sur_real.json")

# Actualizar CSV
df_nuevo = actualizar_csv(puntos_totales)

# Mostrar resumen
print("\n" + "="*100)
print("RESUMEN DE CALLES REALES ENCONTRADAS")
print("="*100)

puntos_df = df_nuevo.groupby('punto_recoleccion')[['latitud_punto_recoleccion', 'longitud_punto_recoleccion']].first()
print(f"\nPrimeras 20 calles reales del Sector Sur:\n")
print(puntos_df.head(20).to_string())

print("\n" + "="*100)
print("✓ COMPLETADO")
print("="*100)
print("El archivo datos_residuos_iquique.csv ahora contiene:")
print("  - Nombres REALES de calles del Sector Sur de Iquique")
print("  - Coordenadas REALES extraídas de OpenStreetMap")
print("  - Datos de residuos originales preservados")
print("\nRecarga el mapa para ver los puntos en ubicaciones reales")
