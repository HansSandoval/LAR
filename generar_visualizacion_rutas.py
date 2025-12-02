"""
Script simple para visualizar rutas VRP
Usa los puntos del mapa de Iquique
"""

import json

# Datos de rutas de ejemplo basadas en Iquique
puntos = [
    {"id": "DEPOSITO", "latitud": -20.2145, "longitud": -70.1545, "nombre": "Centro de Iquique", "tipo": "deposito"},
    {"id": "1", "latitud": -20.262156, "longitud": -70.129893, "nombre": "Avenida Padre Hurtado - Mares del Sur", "tipo": "recoleccion"},
    {"id": "2", "latitud": -20.259861, "longitud": -70.124389, "nombre": "Avenida Padre Hurtado - Jardines del Sur", "tipo": "recoleccion"},
    {"id": "3", "latitud": -20.259960, "longitud": -70.124988, "nombre": "Avenida Padre Hurtado (Sector 3)", "tipo": "recoleccion"},
    {"id": "4", "latitud": -20.255944, "longitud": -70.125653, "nombre": "Avenida La Tirana - Jardines del Sur", "tipo": "recoleccion"},
    {"id": "5", "latitud": -20.241336, "longitud": -70.128191, "nombre": "Avenida La Tirana - Centro Iquique", "tipo": "recoleccion"},
    {"id": "6", "latitud": -20.262094, "longitud": -70.122565, "nombre": "Tamarugal - Jardines del Sur", "tipo": "recoleccion"},
]

# Rutas de ejemplo (generadas con VRP)
rutas = [
    ["DEPOSITO", "1", "3", "6", "DEPOSITO"],  # Ruta 1 (norte/oeste)
    ["DEPOSITO", "2", "4", "5", "DEPOSITO"],  # Ruta 2 (centro/sur)
]

# HTML para visualizar las rutas
html_rutas = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rutas VRP - Iquique</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css" />
    <script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>
    <style>
        body { margin: 0; padding: 0; font-family: Arial, sans-serif; }
        #map { position: absolute; top: 0; bottom: 0; width: 100%; }
        .info-panel {
            position: absolute;
            bottom: 10px;
            left: 10px;
            background: white;
            padding: 15px;
            border-radius: 5px;
            box-shadow: 0 0 15px rgba(0,0,0,0.2);
            max-width: 300px;
            max-height: 300px;
            overflow-y: auto;
            z-index: 1000;
        }
        .info-panel h3 { margin: 0 0 10px 0; font-size: 14px; }
        .ruta-item { padding: 5px; margin: 5px 0; border-left: 4px solid #ccc; padding-left: 10px; }
        .ruta-1 { border-left-color: #FF6B6B; }
        .ruta-2 { border-left-color: #4ECDC4; }
    </style>
</head>
<body>
    <div id="map"></div>
    <div class="info-panel">
        <h3>Rutas VRP Iquique</h3>
        <div id="rutas-info"></div>
    </div>

    <script>
        // Crear mapa
        const map = L.map('map').setView([-20.2400, -70.1300], 14);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors',
            maxZoom: 19
        }).addTo(map);

        // Datos
        const puntos = %PUNTOS_JSON%;
        const rutas = %RUTAS_JSON%;
        
        // Colores para rutas
        const colores = ['#FF6B6B', '#4ECDC4', '#FFE66D', '#95E1D3'];
        
        // Crear mapa de puntos
        const puntosMap = {};
        puntos.forEach(p => puntosMap[p.id] = p);
        
        // Dibujar depósito
        L.circleMarker([-20.2145, -70.1545], {
            radius: 10,
            fillColor: '#000000',
            color: '#FFF',
            weight: 2,
            opacity: 1,
            fillOpacity: 0.8
        }).bindPopup('<b>DEPOSITO</b><br>Centro de Iquique').addTo(map);
        
        // Dibujar rutas
        let info = '';
        rutas.forEach((ruta, idx) => {
            const color = colores[idx % colores.length];
            const coords = [];
            
            // Recopilar coordenadas
            ruta.forEach(idPunto => {
                const punto = puntosMap[idPunto];
                if (punto) {
                    coords.push([punto.latitud, punto.longitud]);
                    
                    // Dibujar punto (excepto depósito)
                    if (idPunto !== 'DEPOSITO') {
                        L.circleMarker([punto.latitud, punto.longitud], {
                            radius: 6,
                            fillColor: color,
                            color: '#000',
                            weight: 1,
                            opacity: 1,
                            fillOpacity: 0.7
                        }).bindPopup(`<b>${punto.nombre}</b><br>ID: ${idPunto}`).addTo(map);
                    }
                }
            });
            
            // Dibujar línea de ruta
            if (coords.length > 0) {
                L.polyline(coords, {
                    color: color,
                    weight: 3,
                    opacity: 0.7,
                    dashArray: idx === 0 ? '' : '5, 5'
                }).addTo(map);
            }
            
            // Info de ruta
            info += `<div class="ruta-item ruta-${idx + 1}">
                <b style="color: ${color}">Ruta ${idx + 1}</b><br>
                ${ruta.slice(1, -1).map((id, i) => `${i + 1}. ${puntosMap[id]?.nombre || id}`).join('<br>')}
            </div>`;
        });
        
        document.getElementById('rutas-info').innerHTML = info;
    </script>
</body>
</html>
"""

# Reemplazar placeholders
html_final = html_rutas.replace('%PUNTOS_JSON%', json.dumps(puntos))
html_final = html_final.replace('%RUTAS_JSON%', json.dumps(rutas))

# Guardar
with open('c:\\Users\\hanss\\Desktop\\LAR\\static\\visualizar_rutas.html', 'w', encoding='utf-8') as f:
    f.write(html_final)

print(" Archivo guardado: static/visualizar_rutas.html")
print("\nAbre en tu navegador:")
print("  http://localhost:8000/static/visualizar_rutas.html")
