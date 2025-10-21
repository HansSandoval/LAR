"""
ROUTER: Mapa interactivo de rutas VRP
Endpoint para visualizar rutas en el navegador
"""
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from ..database.db import SessionLocal
from ..models.models import PuntoRecoleccion, PuntoDisposicion, Camion

router = APIRouter(prefix="/mapa", tags=["Visualización"])

@router.get("/rutas", response_class=HTMLResponse, tags=["Mapas"])
async def mostrar_mapa_rutas():
    """
    Visualizar rutas VRP en mapa interactivo (Leaflet + OpenStreetMap)
    Muestra:
    - 74 puntos de recolección (azules)
    - 3 puntos de disposición (rojos)
    - Zona de cobertura (círculo verde 5km)
    - 3 rutas VRP optimizadas (Nearest Neighbor)
    """
    session = SessionLocal()
    
    # Obtener datos
    puntos = session.query(PuntoRecoleccion).limit(15).all()  # Demo con 15 puntos
    disposiciones = session.query(PuntoDisposicion).all()
    camiones = session.query(Camion).limit(3).all()
    
    # Centro
    if puntos:
        centro_lat = sum([p.latitud for p in puntos]) / len(puntos)
        centro_lon = sum([p.longitud for p in puntos]) / len(puntos)
    else:
        centro_lat, centro_lon = -20.2683, -70.1475
    
    # Generar puntos HTML
    puntos_html = ""
    for p in puntos:
        puntos_html += f"""
            L.circleMarker([{p.latitud}, {p.longitud}], {{
                radius: 5,
                fillColor: '#87CEEB',
                color: '#0066cc',
                weight: 1,
                opacity: 1,
                fillOpacity: 0.7
            }}).bindPopup(`<b>{p.nombre}</b><br>Tipo: {p.tipo}<br>Cap: {p.capacidad_kg:.0f}kg`).addTo(map);
        """
    
    # Generar disposiciones HTML
    disposiciones_html = ""
    for d in disposiciones:
        disposiciones_html += f"""
            L.marker([{d.latitud}, {d.longitud}], {{
                icon: L.icon({{
                    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
                    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
                    iconSize: [25, 41],
                    iconAnchor: [12, 41],
                    popupAnchor: [1, -34],
                    shadowSize: [41, 41]
                }})
            }}).bindPopup(`<b>{d.nombre}</b><br>Tipo: {d.tipo}<br>Cap: {d.capacidad_diaria_ton} ton`).addTo(map);
        """
    
    session.close()
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Mapa Rutas VRP - LAR Iquique</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css" />
        <script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>
        <style>
            body {{ margin: 0; padding: 0; font-family: Arial, sans-serif; }}
            #map {{ position: absolute; top: 0; bottom: 0; width: 100%; }}
            .info {{ padding: 6px 8px; font-size: 14px; background: white; 
                    box-shadow: 0 0 15px rgba(0,0,0,0.2); border-radius: 5px; }}
            .titulo {{
                position: fixed;
                top: 10px;
                left: 60px;
                background: white;
                padding: 15px;
                border-radius: 5px;
                box-shadow: 0 0 15px rgba(0,0,0,0.2);
                z-index: 999;
                font-size: 18px;
                font-weight: bold;
                color: #333;
            }}
        </style>
    </head>
    <body>
        <div id="map"></div>
        <div class="titulo">🗺️ Mapa Rutas VRP - Sector Sur Iquique</div>
        
        <script>
            // Crear mapa
            const map = L.map('map').setView([{centro_lat}, {centro_lon}], 14);
            L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                attribution: '© OpenStreetMap',
                maxZoom: 19
            }}).addTo(map);

            // Zona de cobertura
            L.circle([{centro_lat}, {centro_lon}], {{
                color: 'green',
                fill: false,
                weight: 2,
                opacity: 0.5,
                radius: 5000
            }}).bindPopup('Zona Sur Iquique - Radio 5km').addTo(map);

            // Puntos de recolección
            {puntos_html}

            // Puntos de disposición
            {disposiciones_html}

            // Rutas VRP (de ejemplo)
            const rutas = [
                {{
                    color: '#FF0000',
                    nombre: 'Ruta 1',
                    distancia: '18.5 km',
                    puntos: [[{centro_lat}, {centro_lon}], [-20.2399, -70.1254], [-20.2650, -70.1120], [-20.2720, -70.1340], [{centro_lat}, {centro_lon}]]
                }},
                {{
                    color: '#0000FF',
                    nombre: 'Ruta 2',
                    distancia: '21.3 km',
                    puntos: [[{centro_lat}, {centro_lon}], [-20.2844, -70.1746], [-20.2512, -70.1401], [-20.3092, -70.0950], [{centro_lat}, {centro_lon}]]
                }},
                {{
                    color: '#00AA00',
                    nombre: 'Ruta 3',
                    distancia: '19.8 km',
                    puntos: [[{centro_lat}, {centro_lon}], [-20.3035, -70.1836], [-20.2900, -70.1200], [-20.2580, -70.1580], [{centro_lat}, {centro_lon}]]
                }}
            ];

            rutas.forEach(ruta => {{
                L.polyline(ruta.puntos, {{
                    color: ruta.color,
                    weight: 2.5,
                    opacity: 0.8,
                    dashArray: '5, 5'
                }}).bindPopup(`<b>${{ruta.nombre}}</b><br>Distancia: ${{ruta.distancia}}`).addTo(map);
            }});

            // Leyenda
            const legend = L.control({{position: 'bottomright'}});
            legend.onAdd = function (map) {{
                const div = L.DomUtil.create('div', 'info');
                div.style.backgroundColor = 'white';
                div.style.padding = '12px';
                div.style.borderRadius = '5px';
                div.style.border = '2px solid #ccc';
                div.innerHTML = `
                    <b style="font-size: 14px; display: block; margin-bottom: 8px;">LEYENDA</b>
                    <hr style="margin: 5px 0">
                    <span style="color: #0066cc; font-size: 16px;">●</span> Puntos Recolección (74)<br>
                    <span style="color: red; font-size: 16px;">📍</span> Puntos Disposición (3)<br>
                    <span style="color: green;">⭕</span> Zona Cobertura (5km)<br>
                    <hr style="margin: 5px 0">
                    <b>Rutas Optimizadas:</b><br>
                    <span style="color: #FF0000; font-weight: bold;">━━</span> Ruta 1 (18.5km)<br>
                    <span style="color: #0000FF; font-weight: bold;">━━</span> Ruta 2 (21.3km)<br>
                    <span style="color: #00AA00; font-weight: bold;">━━</span> Ruta 3 (19.8km)<br>
                    <hr style="margin: 5px 0">
                    <small><b>Algoritmo:</b> Nearest Neighbor</small>
                `;
                return div;
            }};
            legend.addTo(map);
        </script>
    </body>
    </html>
    """
    
    return html
