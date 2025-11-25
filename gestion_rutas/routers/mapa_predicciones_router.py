"""
ROUTER: Mapa Interactivo con Predicciones LSTM
Endpoint dinámico para visualizar predicciones de residuos en tiempo real
"""
from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse, JSONResponse
from datetime import datetime, timedelta
from typing import Optional

from ..service.prediccion_mapa_service import PrediccionMapaService

router = APIRouter(prefix="/mapa", tags=["Visualización LSTM"])

@router.get("/predicciones", response_class=HTMLResponse, tags=["Mapas"])
async def mapa_predicciones_lstm(
    fecha: Optional[str] = Query(None, description="Fecha predicción (YYYY-MM-DD). Default: mañana")
):
    """
    MAPA INTERACTIVO CON PREDICCIONES LSTM
    
    Visualiza:
    - 74 puntos de recolección con predicciones LSTM
    - Marcadores coloreados según nivel de demanda
    - Actualización dinámica de predicciones
    - Estadísticas globales
    - Leyenda interactiva
    
    Características:
    - Actualización en tiempo real
    - Colores dinámicos (verde, amarillo, rojo)
    - Tamaño de marcador proporcional a demanda
    - Popups con detalles de predicción
    - Compatible con sistema de optimización de rutas
    """
    
    # Parsear fecha
    fecha_prediccion = None
    if fecha:
        try:
            fecha_prediccion = datetime.strptime(fecha, '%Y-%m-%d')
        except ValueError:
            fecha_prediccion = datetime.now() + timedelta(days=1)
    else:
        fecha_prediccion = datetime.now() + timedelta(days=1)
    
    # Generar predicciones
    servicio = PrediccionMapaService()
    predicciones = servicio.generar_predicciones_completas(fecha_prediccion)
    
    if not predicciones:
        return """
        <html>
            <body>
                <h1>Error</h1>
                <p>No se pudieron cargar las predicciones. Verifica que:</p>
                <ul>
                    <li>El archivo <code>datos_residuos_iquique.csv</code> existe</li>
                    <li>El modelo LSTM esta entrenado (<code>modelo.keras</code>)</li>
                </ul>
                <a href="/mapa/rutas">Volver al mapa basico</a>
            </body>
        </html>
        """
    
    # Calcular centro del mapa
    centro_lat = sum([p['latitud'] for p in predicciones]) / len(predicciones)
    centro_lon = sum([p['longitud'] for p in predicciones]) / len(predicciones)
    
    # Generar estadísticas
    estadisticas = servicio.generar_estadisticas_globales(predicciones)
    
    # Generar marcadores JavaScript dinámicos
    marcadores_js = ""
    for idx, pred in enumerate(predicciones):
        nivel = servicio.clasificar_nivel_demanda(pred['prediccion_kg'])
        
        marcadores_js += f"""
            const marker{idx} = L.circleMarker([{pred['latitud']}, {pred['longitud']}], {{
                radius: {nivel['radio']},
                fillColor: '{nivel['color']}',
                color: '#000000',
                weight: 1,
                opacity: 1,
                fillOpacity: 0.7
            }}).bindPopup(`
                <div style="min-width: 250px;">
                    <h3 style="margin: 0 0 10px 0; color: {nivel['color']};">
                        {pred['punto']}
                    </h3>
                    <hr style="margin: 5px 0;">
                    <p style="margin: 5px 0;">
                        <b>Fecha:</b> {pred['fecha']}<br>
                        <b>Prediccion:</b> <span style="color: {nivel['color']}; font-size: 18px; font-weight: bold;">
                            {pred['prediccion_kg']:.0f} kg
                        </span><br>
                        <b>Nivel:</b> {nivel['nivel']}<br>
                        <b>Metodo:</b> {pred['metodo']}<br>
                        <b>Confianza:</b> {pred['confianza'].upper()}
                    </p>
                    <hr style="margin: 5px 0;">
                    <small style="color: #666;">
                        Lat: {pred['latitud']:.4f}, Lon: {pred['longitud']:.4f}<br>
                        Ultimos 3 dias: {', '.join([str(int(x)) for x in pred['ultimos_3_dias']])} kg<br>
                        Registros historicos: {pred['registros_historicos']}
                    </small>
                </div>
            `).addTo(map);
            allMarkers.push(marker{idx});
        """
    
    # HTML completo
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Mapa Predicciones LSTM - LAR Iquique</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css" />
        <script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>
        <style>
            body {{ 
                margin: 0; 
                padding: 0; 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            }}
            #map {{ 
                position: absolute; 
                top: 0; 
                bottom: 0; 
                width: 100%; 
            }}
            .titulo {{
                position: fixed;
                top: 10px;
                left: 60px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 15px 20px;
                border-radius: 8px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.3);
                z-index: 999;
                font-size: 18px;
                font-weight: bold;
            }}
            .controles {{
                position: fixed;
                top: 10px;
                right: 10px;
                background: white;
                padding: 15px;
                border-radius: 8px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.2);
                z-index: 999;
                max-width: 300px;
            }}
            .estadisticas {{
                position: fixed;
                bottom: 10px;
                left: 10px;
                background: white;
                padding: 15px;
                border-radius: 8px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.2);
                z-index: 999;
                max-width: 350px;
            }}
            .btn {{
                background: #667eea;
                color: white;
                border: none;
                padding: 10px 15px;
                border-radius: 5px;
                cursor: pointer;
                font-weight: bold;
                margin: 5px;
                transition: all 0.3s;
            }}
            .btn:hover {{
                background: #764ba2;
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            }}
            .nivel-item {{
                display: flex;
                align-items: center;
                margin: 5px 0;
                font-size: 13px;
            }}
            .nivel-color {{
                width: 20px;
                height: 20px;
                border-radius: 50%;
                margin-right: 8px;
                border: 1px solid #000;
            }}
            .stat-value {{
                font-size: 24px;
                font-weight: bold;
                color: #667eea;
            }}
            input[type="date"] {{
                padding: 8px;
                border: 2px solid #667eea;
                border-radius: 5px;
                margin: 5px 0;
                width: 100%;
            }}
        </style>
    </head>
    <body>
        <div id="map"></div>
        
        <div class="titulo">
            Predicciones LSTM - Residuos Iquique
        </div>
        
        <div class="controles">
            <h3 style="margin: 0 0 10px 0;">Controles</h3>
            <label><b>Fecha Prediccion:</b></label>
            <input type="date" id="fecha-input" value="{fecha_prediccion.strftime('%Y-%m-%d')}">
            <button class="btn" onclick="actualizarPredicciones()">Actualizar</button>
            <button class="btn" onclick="exportarDatos()">Exportar JSON</button>
            <hr style="margin: 10px 0;">
            <div style="font-size: 12px; color: #666;">
                <b>Informacion:</b><br>
                - Predicciones LSTM en tiempo real<br>
                - Actualizacion dinamica<br>
                - Click en marcadores para detalles<br>
                - Colores segun nivel de demanda
            </div>
        </div>
        
        <div class="estadisticas">
            <h3 style="margin: 0 0 10px 0;">Estadisticas Globales</h3>
            <div style="background: #f0f0f0; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                <div style="text-align: center;">
                    <div class="stat-value">{estadisticas['total_residuos_kg']:,.0f} kg</div>
                    <div style="font-size: 12px; color: #666;">Total Predicho</div>
                </div>
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 10px;">
                <div style="background: #f0f0f0; padding: 8px; border-radius: 5px; text-align: center;">
                    <div style="font-weight: bold; color: #667eea;">{estadisticas['promedio_kg']:.0f} kg</div>
                    <div style="font-size: 11px; color: #666;">Promedio</div>
                </div>
                <div style="background: #f0f0f0; padding: 8px; border-radius: 5px; text-align: center;">
                    <div style="font-weight: bold; color: #667eea;">{estadisticas['total_puntos']}</div>
                    <div style="font-size: 11px; color: #666;">Puntos</div>
                </div>
            </div>
            <hr style="margin: 10px 0;">
            <b style="font-size: 13px;">Distribucion por Nivel:</b>
            <div class="nivel-item">
                <div class="nivel-color" style="background: #00FF00;"></div>
                <span>Muy Bajo: <b>{estadisticas['distribucion_niveles']['Muy Bajo']}</b></span>
            </div>
            <div class="nivel-item">
                <div class="nivel-color" style="background: #90EE90;"></div>
                <span>Bajo: <b>{estadisticas['distribucion_niveles']['Bajo']}</b></span>
            </div>
            <div class="nivel-item">
                <div class="nivel-color" style="background: #FFD700;"></div>
                <span>Medio: <b>{estadisticas['distribucion_niveles']['Medio']}</b></span>
            </div>
            <div class="nivel-item">
                <div class="nivel-color" style="background: #FFA500;"></div>
                <span>Alto: <b>{estadisticas['distribucion_niveles']['Alto']}</b></span>
            </div>
            <div class="nivel-item">
                <div class="nivel-color" style="background: #FF0000;"></div>
                <span>Muy Alto: <b>{estadisticas['distribucion_niveles']['Muy Alto']}</b></span>
            </div>
            <hr style="margin: 10px 0;">
            <small style="color: #666;">
                Generado: {estadisticas['fecha_generacion']}<br>
                Rango: {estadisticas['minimo_kg']:.0f} - {estadisticas['maximo_kg']:.0f} kg
            </small>
        </div>
        
        <script>
            // Crear mapa con coordenadas centradas en los datos reales
            const map = L.map('map').setView([-20.2693, -70.1703], 15);
            L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                attribution: '© OpenStreetMap',
                maxZoom: 19
            }}).addTo(map);

            // Array para almacenar todos los marcadores
            const allMarkers = [];

            // Agregar marcadores con predicciones
            {marcadores_js}

            // Ajustar vista para mostrar todos los marcadores
            if (allMarkers.length > 0) {{
                const group = L.featureGroup(allMarkers);
                map.fitBounds(group.getBounds().pad(0.1));
            }}

            // Función para actualizar predicciones
            function actualizarPredicciones() {{
                const fecha = document.getElementById('fecha-input').value;
                window.location.href = `/mapa/predicciones?fecha=${{fecha}}`;
            }}

            // Función para exportar datos
            function exportarDatos() {{
                const fecha = document.getElementById('fecha-input').value;
                window.open(`/mapa/predicciones/json?fecha=${{fecha}}`, '_blank');
            }}
        </script>
    </body>
    </html>
    """
    
    return html


@router.get("/predicciones/json", response_class=JSONResponse, tags=["Datos"])
async def predicciones_json(
    fecha: Optional[str] = Query(None, description="Fecha prediccion (YYYY-MM-DD)")
):
    """
    API JSON: Obtener predicciones LSTM en formato JSON
    
    Util para:
    - Integracion con otros sistemas
    - Exportacion de datos
    - Conexion con optimizador de rutas
    - Analisis externo
    """
    # Parsear fecha
    fecha_prediccion = None
    if fecha:
        try:
            fecha_prediccion = datetime.strptime(fecha, '%Y-%m-%d')
        except ValueError:
            fecha_prediccion = datetime.now() + timedelta(days=1)
    else:
        fecha_prediccion = datetime.now() + timedelta(days=1)
    
    # Generar predicciones
    servicio = PrediccionMapaService()
    predicciones = servicio.generar_predicciones_completas(fecha_prediccion)
    estadisticas = servicio.generar_estadisticas_globales(predicciones)
    
    # Agregar clasificación de nivel
    for pred in predicciones:
        nivel_info = servicio.clasificar_nivel_demanda(pred['prediccion_kg'])
        pred['nivel_demanda'] = nivel_info['nivel']
        pred['color'] = nivel_info['color']
        pred['prioridad'] = nivel_info['prioridad']
    
    return {
        'success': True,
        'fecha_prediccion': fecha_prediccion.strftime('%Y-%m-%d'),
        'predicciones': predicciones,
        'estadisticas': estadisticas,
        'mensaje': f'Predicciones generadas para {len(predicciones)} puntos de recolección'
    }
