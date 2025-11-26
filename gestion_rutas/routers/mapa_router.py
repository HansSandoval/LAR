# -*- coding: utf-8 -*-
from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from ..database.db import execute_query
import json

router = APIRouter(prefix="/mapa", tags=["Visualización"])

@router.get("/data")
async def obtener_datos_mapa():
    """Obtener datos del mapa en formato JSON"""
    try:
        puntos = execute_query("SELECT * FROM punto_recoleccion WHERE latitud IS NOT NULL AND longitud IS NOT NULL", ())
        disposiciones = execute_query("SELECT * FROM punto_disposicion WHERE latitud IS NOT NULL AND longitud IS NOT NULL", ())
        
        puntos_data = []
        for p in puntos:
            puntos_data.append({
                "id_punto": p.get('id'),
                "lat": p.get('latitud'),
                "lng": p.get('longitud'),
                "nombre": p.get('nombre') or "Sin nombre",
                "tipo": p.get('tipo_punto'),
                "estado": p.get('estado_activo')
            })
        
        disposiciones_data = []
        for d in disposiciones:
            disposiciones_data.append({
                "id_punto_disp": d.get('id'),
                "lat": d.get('latitud'),
                "lng": d.get('longitud'),
                "nombre": d.get('nombre') or "Sin nombre",
                "tipo": d.get('tipo')
            })
        
        return {
            "puntos_recoleccion": puntos_data,
            "puntos_disposicion": disposiciones_data,
            "rutas": [],
            "resumen": {
                "total_puntos": len(puntos_data),
                "total_disposiciones": len(disposiciones_data)
            }
        }
    except Exception as e:
        return {"error": str(e), "puntos_recoleccion": [], "puntos_disposicion": [], "rutas": [], "resumen": {"total_puntos": 0, "total_disposiciones": 0}}

@router.get("/rutas", response_class=HTMLResponse)
async def mostrar_mapa_rutas():
    try:
        puntos = execute_query("SELECT * FROM punto_recoleccion WHERE latitud IS NOT NULL AND longitud IS NOT NULL", ())
        disposiciones = execute_query("SELECT * FROM punto_disposicion WHERE latitud IS NOT NULL AND longitud IS NOT NULL", ())
        
        if puntos:
            lats = [p.get('latitud') for p in puntos]
            lons = [p.get('longitud') for p in puntos]
            centro_lat = sum(lats) / len(lats)
            centro_lon = sum(lons) / len(lons)
        else:
            centro_lat = -20.2683
            centro_lon = -70.1475
        
        # Construir JSON de puntos con JSON estándar
        puntos_data = []
        for p in puntos:
            puntos_data.append({
                "lat": p.get('latitud'),
                "lng": p.get('longitud'),
                "nombre": p.get('nombre') or "Sin nombre"
            })
        puntos_json = json.dumps(puntos_data, ensure_ascii=False)
        
        # Construir JSON de disposiciones
        disposiciones_data = []
        for d in disposiciones:
            disposiciones_data.append({
                "lat": d.get('latitud'),
                "lng": d.get('longitud'),
                "nombre": d.get('nombre') or "Sin nombre"
            })
        disposiciones_json = json.dumps(disposiciones_data, ensure_ascii=False)
        
        html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mapa VRP - Iquique</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css"/>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet.markercluster/1.5.1/MarkerCluster.css"/>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet.markercluster/1.5.1/MarkerCluster.Default.css"/>
    <style>
        body {{ margin: 0; padding: 0; font-family: Arial, sans-serif; }}
        #map {{ height: 100vh; width: 100%; }}
        .info {{ background: white; padding: 12px; border-radius: 5px; box-shadow: 0 0 15px rgba(0,0,0,0.2); max-width: 280px; }}
        .info h4 {{ margin: 0 0 8px 0; color: #08519c; font-size: 16px; }}
        .info p {{ margin: 5px 0; font-size: 13px; }}
        .legend {{ background: white; padding: 12px; border-radius: 5px; box-shadow: 0 0 15px rgba(0,0,0,0.2); font-size: 12px; }}
        .legend-item {{ margin: 6px 0; display: flex; align-items: center; }}
        .legend-color {{ width: 14px; height: 14px; margin-right: 8px; border-radius: 2px; }}
    </style>
</head>
<body>
    <div id="map"></div>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet.markercluster/1.5.1/leaflet.markercluster.js"></script>
    <script>
        const puntos = {puntos_json};
        const disposiciones = {disposiciones_json};
        const map = L.map('map').setView([{centro_lat}, {centro_lon}], 13);
        
        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
            attribution: '© OpenStreetMap',
            maxZoom: 19
        }}).addTo(map);
        
        const markerGroup = L.markerClusterGroup({{
            maxClusterRadius: 50,
            showCoverageOnHover: true,
            zoomToBoundsOnClick: true
        }});
        
        puntos.forEach((punto, idx) => {{
            const marker = L.circleMarker([punto.lat, punto.lng], {{
                radius: 5,
                fillColor: '#3388ff',
                color: '#0066cc',
                weight: 1,
                opacity: 1,
                fillOpacity: 0.7
            }});
            marker.bindPopup('<b>Punto ' + (idx + 1) + '</b><br>' + punto.nombre);
            markerGroup.addLayer(marker);
        }});
        
        map.addLayer(markerGroup);
        
        disposiciones.forEach((disp, idx) => {{
            const marker = L.marker([disp.lat, disp.lng], {{
                icon: L.icon({{
                    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
                    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
                    iconSize: [25, 41],
                    iconAnchor: [12, 41],
                    popupAnchor: [1, -34],
                    shadowSize: [41, 41]
                }})
            }});
            marker.bindPopup('<b>Disposición ' + (idx + 1) + '</b><br>' + disp.nombre);
            marker.addTo(map);
        }});
        
        L.circle([{centro_lat}, {centro_lon}], {{
            color: '#2ecc71',
            fillColor: '#27ae60',
            fillOpacity: 0.1,
            radius: 7000,
            weight: 2,
            dashArray: '5, 5'
        }}).bindPopup('Zona de cobertura (7km)').addTo(map);
        
        const info = L.control({{position: 'topleft'}});
        info.onAdd = function(map) {{
            const div = L.DomUtil.create('div', 'info');
            div.innerHTML = '<h4>Mapa VRP Iquique</h4><p><b>Puntos:</b> ' + puntos.length + '</p><p><b>Disposición:</b> ' + disposiciones.length + '</p>';
            return div;
        }};
        info.addTo(map);
        
        const legend = L.control({{position: 'bottomright'}});
        legend.onAdd = function(map) {{
            const div = L.DomUtil.create('div', 'legend');
            div.innerHTML = '<div class="legend-item"><span class="legend-color" style="background:#3388ff;border:1px solid #0066cc;"></span><span>Recolección</span></div><div class="legend-item"><span class="legend-color" style="background:#ff6b6b;"></span><span>Disposición</span></div>';
            return div;
        }};
        legend.addTo(map);
        
        map.invalidateSize();
    </script>
</body>
</html>"""
        
        return html_content
    except Exception as e:
        return f"<h1>Error cargando mapa</h1><p>{str(e)}</p>"
