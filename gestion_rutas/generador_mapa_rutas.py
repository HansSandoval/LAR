"""
VISUALIZADOR DE RUTAS - Sector Sur Iquique
Genera mapa interactivo con:
- Puntos de recolección (azul)
- Puntos de disposición (rojo)
- Rutas VRP simuladas (líneas)
"""
import folium
from folium import plugins
import sys
sys.path.insert(0, 'gestion_rutas')

from database.db import SessionLocal
from models.models import (
    PuntoRecoleccion, PuntoDisposicion, Zona, Camion, Turno
)
import math
import random

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calcula distancia en km entre dos puntos"""
    R = 6371
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = math.sin(dLat/2) * math.sin(dLat/2) + \
        math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * \
        math.sin(dLon/2) * math.sin(dLon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def nearest_neighbor_route(punto_inicio, puntos_disponibles, punto_fin):
    """Algoritmo Nearest Neighbor para generar ruta"""
    ruta = [punto_inicio]
    puntos_restantes = set(puntos_disponibles)
    distancia_total = 0
    
    actual = punto_inicio
    
    while puntos_restantes:
        # Encontrar punto más cercano
        proximo = min(
            puntos_restantes,
            key=lambda p: haversine_distance(
                actual['lat'], actual['lon'], 
                p['lat'], p['lon']
            )
        )
        
        distancia_total += haversine_distance(
            actual['lat'], actual['lon'],
            proximo['lat'], proximo['lon']
        )
        
        ruta.append(proximo)
        puntos_restantes.remove(proximo)
        actual = proximo
    
    # Volver al punto final
    distancia_total += haversine_distance(
        actual['lat'], actual['lon'],
        punto_fin['lat'], punto_fin['lon']
    )
    ruta.append(punto_fin)
    
    return ruta, distancia_total

def main():
    session = SessionLocal()
    
    print("[1] Cargando datos...")
    
    # Datos base
    zona = session.query(Zona).first()
    puntos = session.query(PuntoRecoleccion).all()
    disposiciones = session.query(PuntoDisposicion).all()
    camiones = session.query(Camion).all()
    
    # Centro del mapa
    centro_lat = sum([p.latitud for p in puntos]) / len(puntos)
    centro_lon = sum([p.longitud for p in puntos]) / len(puntos)
    
    print(f"[2] Creando mapa centrado en ({centro_lat:.4f}, {centro_lon:.4f})...")
    
    # Crear mapa base
    mapa = folium.Map(
        location=[centro_lat, centro_lon],
        zoom_start=14,
        tiles='OpenStreetMap'
    )
    
    # Crear capa de círculo para delimitar la zona
    folium.Circle(
        location=[centro_lat, centro_lon],
        radius=5000,  # 5 km
        color='green',
        fill=False,
        weight=2,
        opacity=0.5,
        popup='Zona Sur Iquique (delimitación 5km)',
        tooltip='Área de cobertura'
    ).add_to(mapa)
    
    # Agregar puntos de recolección
    print(f"[3] Agregando {len(puntos)} puntos de recolección...")
    for punto in puntos:
        folium.CircleMarker(
            location=[punto.latitud, punto.longitud],
            radius=6,
            popup=f"<b>{punto.nombre}</b><br>Tipo: {punto.tipo}<br>Capacidad: {punto.capacidad_kg:.0f}kg",
            tooltip=punto.nombre,
            color='blue',
            fill=True,
            fillColor='lightblue',
            fillOpacity=0.7,
            weight=2
        ).add_to(mapa)
    
    # Agregar puntos de disposición
    print(f"[4] Agregando {len(disposiciones)} puntos de disposición...")
    for disp in disposiciones:
        folium.Marker(
            location=[disp.latitud, disp.longitud],
            popup=f"<b>{disp.nombre}</b><br>Tipo: {disp.tipo}<br>Capacidad: {disp.capacidad_diaria_ton} ton/día",
            tooltip=disp.nombre,
            icon=folium.Icon(color='red', icon='trash', prefix='fa')
        ).add_to(mapa)
    
    # Generar rutas simuladas (una por camión disponible)
    print(f"[5] Generando {len(camiones)} rutas VRP simuladas...")
    
    colores_rutas = ['red', 'blue', 'green', 'purple', 'orange']
    
    # Convertir puntos a formato de ruta
    puntos_data = [
        {'lat': p.latitud, 'lon': p.longitud, 'nombre': p.nombre, 'id': p.id_punto}
        for p in puntos
    ]
    
    disposicion_principal = {
        'lat': disposiciones[0].latitud,
        'lon': disposiciones[0].longitud,
        'nombre': disposiciones[0].nombre
    }
    
    for idx, camion in enumerate(camiones[:3]):  # Mostrar 3 rutas
        print(f"  Ruta {idx+1}: {camion.patente} (Capacidad: {camion.capacidad_kg}kg)")
        
        # Seleccionar puntos para esta ruta (aleatorio o por capacidad)
        cantidad_puntos = random.randint(8, 15)
        puntos_ruta = random.sample(puntos_data, min(cantidad_puntos, len(puntos_data)))
        
        # Generar ruta con Nearest Neighbor
        ruta, distancia = nearest_neighbor_route(
            disposicion_principal,
            puntos_ruta,
            disposicion_principal
        )
        
        # Dibujar ruta en el mapa
        color = colores_rutas[idx % len(colores_rutas)]
        
        # Coordenadas para la línea
        coordenadas = [[p['lat'], p['lon']] for p in ruta]
        
        folium.PolyLine(
            coordenadas,
            color=color,
            weight=2,
            opacity=0.7,
            popup=f"Ruta {camion.patente}: {distancia:.1f}km",
            tooltip=f"Ruta {camion.patente}"
        ).add_to(mapa)
        
        # Agregar inicio/fin de ruta con marcadores
        folium.CircleMarker(
            location=[ruta[0]['lat'], ruta[0]['lon']],
            radius=4,
            color=color,
            fill=True,
            fillColor=color,
            opacity=1,
            tooltip=f"Inicio Ruta {camion.patente}"
        ).add_to(mapa)
    
    # Agregar leyenda
    legend_html = '''
    <div style="position: fixed; 
            bottom: 50px; right: 50px; width: 220px; height: 180px; 
            background-color: white; border:2px solid grey; z-index:9999; 
            font-size:14px; padding: 10px">
    <b>Leyenda</b><br>
    <span style="color:blue">●</span> Puntos de Recolección (74)<br>
    <span style="color:red">🗑</span> Puntos de Disposición (3)<br>
    <span style="color:green">⭕</span> Zona de Cobertura (5km)<br>
    <br>
    <b>Rutas VRP:</b><br>
    <span style="color:red">—</span> Ruta 1<br>
    <span style="color:blue">—</span> Ruta 2<br>
    <span style="color:green">—</span> Ruta 3<br>
    </div>
    '''
    mapa.get_root().html.add_child(folium.Element(legend_html))
    
    # Guardar mapa
    output_path = 'static/mapa_rutas_iquique.html'
    mapa.save(output_path)
    print(f"\n[OK] Mapa guardado en: {output_path}")
    print(f"     Abre en navegador: file://{output_path}")
    
    # Estadísticas
    print("\n" + "="*60)
    print("ESTADISTICAS DEL MAPA")
    print("="*60)
    print(f"Zona: {zona.nombre}")
    print(f"Puntos de recolección: {len(puntos)}")
    print(f"Puntos de disposición: {len(disposiciones)}")
    print(f"Camiones disponibles: {len(camiones)}")
    print(f"Centro zona: ({centro_lat:.4f}, {centro_lon:.4f})")
    print(f"Radio de cobertura: 5 km")
    print(f"Rutas visualizadas: 3")
    print("="*60)
    
    session.close()

if __name__ == "__main__":
    main()
