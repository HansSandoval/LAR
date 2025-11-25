"""
Router FastAPI para integración del Sistema Multi-Agente (MAS) con el mapa interactivo.
Proporciona endpoints para:
- Ejecutar simulaciones MAS
- Obtener rutas de camiones en tiempo real
- Estadísticas de recolección
- Streaming de eventos WebSocket
"""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
import sys
import random
import pandas as pd

# Importar el sistema MAS usando importaciones relativas
try:
    from ..vrp.dvrptw_env import DVRPTWEnv, Cliente
    from ..vrp.mas_cooperativo import AgenteRecolector, CoordinadorMAS
except ImportError:
    # Fallback para cuando se ejecuta directamente
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from vrp.dvrptw_env import DVRPTWEnv, Cliente
    from vrp.mas_cooperativo import AgenteRecolector, CoordinadorMAS

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/mas", tags=["Multi-Agent System"])


# ==================== MODELOS PYDANTIC ====================

class ConfiguracionMAS(BaseModel):
    """Configuración para la simulación MAS"""
    num_camiones: int = 3
    capacidad_camion: int = 3500  # kg
    num_clientes: int = 50
    coordenadas_reales: bool = True  # Usar coordenadas de Sector Sur Iquique
    velocidad_simulacion: float = 1.0  # 1.0 = tiempo real, 2.0 = 2x más rápido
    usar_predicciones_lstm: bool = True


class EstadoCamion(BaseModel):
    """Estado actual de un camión"""
    id: int
    nombre: str
    posicion: Dict[str, float]  # {lat, lon}
    ruta: List[Dict[str, float]]  # Lista de posiciones visitadas
    ruta_geometria: Optional[List[List[float]]] = None  # Geometría completa OSRM [[lat,lon],...]
    clientes_servidos: List[int]
    carga_actual: float  # kg
    capacidad_total: float  # kg
    distancia_recorrida: float  # km
    estado: str  # "en_ruta", "retornando", "en_depot"
    color: str  # Color para visualización


class EstadisticasGlobales(BaseModel):
    """Estadísticas globales de la simulación"""
    total_residuos_recolectados: float  # kg
    total_distancia_recorrida: float  # km
    clientes_servidos: int
    clientes_totales: int
    camiones_activos: int
    camiones_totales: int
    tiempo_simulacion: float  # segundos
    eficiencia: float  # porcentaje (0-100)


class EventoMAS(BaseModel):
    """Evento del sistema MAS"""
    tipo: str  # "movimiento", "recogida", "retorno", "estadisticas"
    timestamp: str
    camion_id: Optional[int] = None
    datos: Dict[str, Any]


# ==================== VARIABLES GLOBALES ====================

# Almacenar estado de simulaciones activas
simulaciones_activas: Dict[str, Dict[str, Any]] = {}

# Colores para camiones (paleta distintiva)
COLORES_CAMIONES = [
    "#FF6B6B",  # Rojo
    "#4ECDC4",  # Turquesa
    "#45B7D1",  # Azul
    "#FFA07A",  # Salmón
    "#98D8C8",  # Menta
    "#F7DC6F",  # Amarillo
    "#BB8FCE",  # Púrpura
    "#85C1E2",  # Celeste
]


# ==================== FUNCIONES AUXILIARES ====================

def cargar_predicciones_lstm_csv(num_clientes: int = 50) -> List[float]:
    """
    Carga predicciones LSTM usando el servicio de predicciones.
    Usa el mismo servicio que el endpoint /api/lstm/predicciones-fecha
    """
    try:
        from gestion_rutas.service.prediccion_mapa_service import PrediccionMapaService
        from datetime import datetime, timedelta
        
        logger.info(f"📊 Generando predicciones LSTM para {num_clientes} puntos...")
        servicio = PrediccionMapaService()
        fecha_prediccion = datetime.now() + timedelta(days=1)
        predicciones_completas = servicio.generar_predicciones_completas(fecha_prediccion)
        
        if predicciones_completas and len(predicciones_completas) > 0:
            # Extraer solo los valores de predicción en kg
            predicciones = [pred['prediccion_kg'] for pred in predicciones_completas[:num_clientes]]
            logger.info(f"✅ {len(predicciones)} predicciones LSTM generadas correctamente")
            return predicciones
        else:
            logger.warning("⚠️ No se pudieron generar predicciones LSTM")
    except Exception as e:
        logger.error(f"❌ Error generando predicciones LSTM: {e}")
        import traceback
        logger.error(traceback.format_exc())
    
    # Valores sintéticos si falla
    logger.warning("⚠️ Usando valores sintéticos como fallback")
    return [random.uniform(50, 150) for _ in range(num_clientes)]


def obtener_coordenadas_sector_sur(num_clientes: int = 50) -> List[Dict[str, float]]:
    """
    Obtiene coordenadas reales del Sector Sur de Iquique.
    Lee desde el CSV de datos reales si existe.
    """
    try:
        csv_path = Path(__file__).parent.parent / "lstm" / "datos_residuos_iquique.csv"
        logger.info(f"🔍 Buscando CSV en: {csv_path}")
        logger.info(f"📁 Archivo existe: {csv_path.exists()}")
        
        if csv_path.exists():
            import pandas as pd
            df = pd.read_csv(csv_path)
            logger.info(f"📊 CSV cargado: {len(df)} registros totales")
            logger.info(f"📋 Columnas: {df.columns.tolist()[:5]}...")
            
            # ✅ COLUMNAS CORRECTAS: latitud_punto_recoleccion, longitud_punto_recoleccion, punto_recoleccion
            if 'latitud_punto_recoleccion' in df.columns and 'longitud_punto_recoleccion' in df.columns:
                # Obtener coordenadas únicas
                coords_unicas = df[['latitud_punto_recoleccion', 'longitud_punto_recoleccion', 'punto_recoleccion']].drop_duplicates()
                logger.info(f"🎯 Coordenadas únicas encontradas: {len(coords_unicas)}")
                
                # Filtrar coordenadas válidas (rango amplio de Iquique)
                coords_validas = coords_unicas[
                    (coords_unicas['latitud_punto_recoleccion'].notna()) &
                    (coords_unicas['longitud_punto_recoleccion'].notna()) &
                    (coords_unicas['latitud_punto_recoleccion'].between(-20.35, -20.15)) &
                    (coords_unicas['longitud_punto_recoleccion'].between(-70.25, -70.05))
                ]
                logger.info(f"✅ Coordenadas válidas después de filtrar: {len(coords_validas)}")
                
                if len(coords_validas) > 0:
                    # Tomar hasta num_clientes coordenadas
                    cant_usar = min(len(coords_validas), num_clientes)
                    coordenadas = []
                    for _, row in coords_validas.head(cant_usar).iterrows():
                        coordenadas.append({
                            'lat': float(row['latitud_punto_recoleccion']),
                            'lon': float(row['longitud_punto_recoleccion']),
                            'nombre': str(row['punto_recoleccion'])
                        })
                    
                    logger.info(f"✅ Cargadas {len(coordenadas)} coordenadas REALES desde CSV")
                    logger.info(f"📍 Ejemplo: {coordenadas[0]}")
                    return coordenadas
                else:
                    logger.warning(f"⚠️ No hay coordenadas válidas después del filtro")
            else:
                logger.warning(f"⚠️ Columnas incorrectas. Disponibles: {df.columns.tolist()}")
        else:
            logger.warning(f"⚠️ Archivo CSV no existe en: {csv_path}")
        
        logger.warning("⚠️ CSV no disponible, usando coordenadas sintéticas")
    except Exception as e:
        logger.error(f"❌ Error cargando coordenadas: {e}")
        import traceback
        logger.error(traceback.format_exc())
    
    # Coordenadas sintéticas del Sector Sur (dentro de Iquique, no en el océano)
    base_lat, base_lon = -20.2666, -70.1300
    return [
        {
            'lat': base_lat + random.uniform(-0.015, 0.015),
            'lon': base_lon + random.uniform(-0.015, 0.015),
            'nombre': f"Punto {i+1}"
        }
        for i in range(num_clientes)
    ]


def crear_clientes_con_datos_reales(config: ConfiguracionMAS) -> List[Cliente]:
    """
    Crea clientes usando coordenadas reales y predicciones LSTM.
    """
    # Obtener coordenadas reales
    coordenadas = obtener_coordenadas_sector_sur(config.num_clientes)
    
    # Obtener predicciones LSTM
    if config.usar_predicciones_lstm:
        predicciones = cargar_predicciones_lstm_csv(config.num_clientes)
    else:
        predicciones = [random.uniform(50, 150) for _ in range(config.num_clientes)]
    
    # Crear clientes
    clientes = []
    for i, (coord, demanda) in enumerate(zip(coordenadas, predicciones)):
        lat = coord['lat']
        lon = coord['lon']
        
        # VALIDACIÓN: Filtrar coordenadas fuera de Iquique
        if not (-20.35 <= lat <= -20.15) or not (-70.25 <= lon <= -70.05):
            logger.warning(f"⚠️ Coordenada fuera de rango: {coord.get('nombre', f'Punto {i+1}')} ({lat}, {lon})")
            # Ajustar a coordenadas válidas del Sector Sur
            lat = max(-20.35, min(-20.15, lat))
            lon = max(-70.25, min(-70.05, lon))
            logger.info(f"   ✓ Ajustada a: ({lat}, {lon})")
        
        cliente = Cliente(
            id=i+1,  # IDs empiezan en 1 (0 reservado para depot)
            nombre=coord.get('nombre', f"Punto {i+1}"),
            latitud=lat,
            longitud=lon,
            demanda_kg=demanda,
            prioridad=1,  # Prioridad normal por defecto
            ventana_inicio=0.0,  # Sin restricción de tiempo
            ventana_fin=float('inf')  # Sin restricción de tiempo
        )
        clientes.append(cliente)
    
    logger.info(f"✅ Creados {len(clientes)} clientes con coordenadas validadas")
    return clientes


# ==================== ENDPOINTS ====================

@router.post("/simular", response_model=Dict[str, Any])
async def iniciar_simulacion(config: ConfiguracionMAS):
    """
    Inicia una nueva simulación MAS con los parámetros especificados.
    Retorna un ID de simulación para tracking.
    """
    try:
        sim_id = f"sim_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        logger.info(f"🚀 Iniciando simulación {sim_id}")
        logger.info(f"   - Camiones: {config.num_camiones}")
        logger.info(f"   - Clientes: {config.num_clientes}")
        logger.info(f"   - Capacidad: {config.capacidad_camion}kg")
        logger.info(f"   - LSTM: {'✓' if config.usar_predicciones_lstm else '✗'}")
        
        # Crear clientes con datos reales
        clientes_objetos = crear_clientes_con_datos_reales(config)
        
        # Convertir objetos Cliente a diccionarios para el entorno
        clientes_dict = []
        for cliente in clientes_objetos:
            clientes_dict.append({
                'id': cliente.id,
                'nombre': cliente.nombre,
                'latitud': cliente.latitud,
                'longitud': cliente.longitud,
                'demanda_kg': cliente.demanda_kg,
                'prioridad': cliente.prioridad,
                'tiempo_servicio': cliente.tiempo_servicio
            })
        
        # Crear entorno DVRPTW
        # Depot en el centro del Sector Sur de Iquique (coordenadas VÁLIDAS)
        # Iquique está en: Latitud -20.2° (sur), Longitud -70.1° (oeste)
        depot_lat = -20.2666  # Centro Sector Sur (TIERRA, no océano)
        depot_lon = -70.1300  # Dentro de la ciudad
        
        logger.info(f"🏠 Depot configurado en: ({depot_lat}, {depot_lon})")
        
        env = DVRPTWEnv(
            num_camiones=config.num_camiones,
            capacidad_camion_kg=config.capacidad_camion,
            clientes=clientes_dict,
            depot_lat=depot_lat,
            depot_lon=depot_lon,
            usar_routing_real=True,  # ✅ ACTIVADO - rutas por calles reales OSRM
            penalizacion_distancia=0.1,
            recompensa_servicio=10.0,
            max_steps=500,
            seed=42
        )
        
        # Crear coordinador MAS
        coordinador = CoordinadorMAS(env)
        
        # Guardar estado de simulación
        simulaciones_activas[sim_id] = {
            'config': config,
            'env': env,
            'coordinador': coordinador,
            'clientes': clientes_dict,
            'inicio': datetime.now(),
            'activa': True,
            'paso_actual': 0,
            'eventos': []
        }
        
        logger.info(f"✅ Simulación {sim_id} creada exitosamente")
        
        return {
            'simulacion_id': sim_id,
            'mensaje': 'Simulación iniciada correctamente',
            'config': config.dict(),
            'num_clientes_reales': len(clientes_dict),
            'coordenadas_depot': {'lat': -20.2666, 'lon': -70.1300}
        }
        
    except Exception as e:
        logger.error(f"❌ Error iniciando simulación: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/simulacion/{sim_id}/estado", response_model=Dict[str, Any])
async def obtener_estado_simulacion(sim_id: str):
    """
    Obtiene el estado actual completo de una simulación:
    - Estado de cada camión
    - Estadísticas globales
    - Clientes servidos/pendientes
    """
    try:
        if sim_id not in simulaciones_activas:
            raise HTTPException(status_code=404, detail="Simulación no encontrada")
        
        sim = simulaciones_activas[sim_id]
        env = sim['env']
        coordinador = sim['coordinador']
        
        logger.info(f"📊 Obteniendo estado de simulación {sim_id}")
        logger.info(f"   - Camiones: {len(coordinador.agentes)}")
        logger.info(f"   - Clientes: {len(env.clientes)}")
        
        # Construir estado de camiones
        estados_camiones = []
        for i, agente in enumerate(coordinador.agentes):
            camion = agente.camion
            
            logger.debug(f"   Camión {i}: pos=({camion.latitud}, {camion.longitud}), carga={camion.carga_actual_kg}")
            
            # Construir ruta con coordenadas REALES por calles (si están disponibles)
            ruta_coords = []
            ruta_geometria = []  # Geometría completa por calles OSRM
            
            # Si el camión tiene geometría de ruta calculada por OSRM, usarla
            if hasattr(camion, 'ruta_geometria') and camion.ruta_geometria:
                # Convertir de [lon, lat] a [lat, lon] para Leaflet
                ruta_geometria = [[coord[1], coord[0]] for coord in camion.ruta_geometria]
                logger.info(f"Camión {i}: Enviando geometría OSRM con {len(ruta_geometria)} puntos")
            
            # Waypoints (puntos de destino planificados)
            for cliente_id in camion.ruta_actual:
                if cliente_id < len(env.clientes):
                    cliente = env.clientes[cliente_id]
                    ruta_coords.append({'lat': cliente.latitud, 'lon': cliente.longitud})
            
            # Agregar posición actual
            posicion_actual = {'lat': camion.latitud, 'lon': camion.longitud}
            
            # Determinar estado
            if camion.latitud == env.depot_lat and camion.longitud == env.depot_lon:
                if camion.carga_actual_kg > 0:
                    estado = "en_depot"
                else:
                    estado = "en_depot"
            else:
                estado = "en_ruta"
            
            estado_camion = EstadoCamion(
                id=i,
                nombre=f"Camión {i+1}",
                posicion=posicion_actual,
                ruta=ruta_coords,  # Waypoints (destinos)
                ruta_geometria=ruta_geometria if ruta_geometria else None,  # Geometría OSRM
                clientes_servidos=camion.ruta_actual.copy(),
                carga_actual=camion.carga_actual_kg,
                capacidad_total=camion.capacidad_kg,
                distancia_recorrida=camion.distancia_recorrida_km,
                estado=estado,
                color=COLORES_CAMIONES[i % len(COLORES_CAMIONES)]
            )
            
            # Agregar geometría de ruta real si está disponible
            dict_camion = estado_camion.dict()
            if ruta_geometria:
                dict_camion['ruta_geometria'] = ruta_geometria  # Ruta completa por calles
            
            estados_camiones.append(dict_camion)
        
        # Estadísticas globales
        clientes_servidos = sum(cliente.servido for cliente in env.clientes)
        total_residuos = sum(
            cliente.demanda_kg for cliente in env.clientes if cliente.servido
        )
        distancia_total = sum(agente.camion.distancia_recorrida_km for agente in coordinador.agentes)
        camiones_activos = sum(
            1 for agente in coordinador.agentes 
            if agente.camion.latitud != env.depot_lat or agente.camion.longitud != env.depot_lon
        )
        
        eficiencia = (clientes_servidos / len(env.clientes) * 100) if env.clientes else 0
        
        tiempo_sim = (datetime.now() - sim['inicio']).total_seconds()
        
        estadisticas = EstadisticasGlobales(
            total_residuos_recolectados=total_residuos,
            total_distancia_recorrida=distancia_total,
            clientes_servidos=clientes_servidos,
            clientes_totales=len(env.clientes),
            camiones_activos=camiones_activos,
            camiones_totales=len(coordinador.agentes),
            tiempo_simulacion=tiempo_sim,
            eficiencia=eficiencia
        )
        
        # Agregar lista de IDs de clientes servidos para actualizar visualización
        clientes_servidos_ids = [
            i for i, cliente in enumerate(env.clientes) if cliente.servido
        ]
        
        return {
            'simulacion_id': sim_id,
            'paso': sim['paso_actual'],
            'camiones': estados_camiones,
            'estadisticas': estadisticas.dict(),
            'clientes_servidos_ids': clientes_servidos_ids,  # IDs de puntos servidos
            'activa': sim['activa']
        }
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo estado de simulación {sim_id}: {e}")
        logger.exception(e)
        raise HTTPException(status_code=500, detail=f"Error obteniendo estado: {str(e)}")


@router.post("/simulacion/{sim_id}/paso")
async def ejecutar_paso_simulacion(sim_id: str):
    """
    Ejecuta un paso de la simulación (todos los agentes toman una decisión).
    Retorna los eventos generados y el nuevo estado.
    """
    if sim_id not in simulaciones_activas:
        raise HTTPException(status_code=404, detail="Simulación no encontrada")
    
    sim = simulaciones_activas[sim_id]
    
    if not sim['activa']:
        return {'mensaje': 'Simulación finalizada', 'eventos': []}
    
    try:
        env = sim['env']
        coordinador = sim['coordinador']
        
        # Ejecutar paso cooperativo
        decisiones, info = coordinador.ejecutar_paso_cooperativo()
        
        # Generar eventos para visualización
        eventos = []
        timestamp = datetime.now().isoformat()
        
        for decision in decisiones:
            if decision and decision.cliente_objetivo_id > 0:  # Cliente real (no depot)
                # Buscar cliente por ID (lista es 0-indexed pero IDs empiezan en 1)
                cliente = next((c for c in env.clientes if c.id == decision.cliente_objetivo_id), None)
                if cliente:
                    evento = EventoMAS(
                        tipo="recogida",
                        timestamp=timestamp,
                        camion_id=decision.camion_id,
                        datos={
                            'cliente_id': decision.cliente_objetivo_id,
                            'posicion': {'lat': cliente.latitud, 'lon': cliente.longitud},
                            'residuos_kg': cliente.demanda_kg,
                            'razonamiento': decision.razonamiento
                        }
                    )
                    eventos.append(evento.dict())
            
            elif decision and decision.cliente_objetivo_id == 0:  # Retorno al depot
                agente = next(a for a in coordinador.agentes if a.camion.id == decision.camion_id)
                evento = EventoMAS(
                    tipo="retorno",
                    timestamp=timestamp,
                    camion_id=decision.camion_id,
                    datos={
                        'posicion': {'lat': env.depot_lat, 'lon': env.depot_lon},
                        'carga_descargada': agente.camion.carga_actual
                    }
                )
                eventos.append(evento.dict())
        
        sim['eventos'].extend(eventos)
        sim['paso_actual'] += 1
        
        # Verificar si terminó
        if all(cliente.servido for cliente in env.clientes):
            sim['activa'] = False
            logger.info(f"✅ Simulación {sim_id} completada: 100% clientes servidos")
        
        return {
            'mensaje': 'Paso ejecutado',
            'paso': sim['paso_actual'],
            'eventos': eventos,
            'conflictos_resueltos': info.get('conflictos_resueltos', 0)
        }
        
    except Exception as e:
        logger.error(f"❌ Error ejecutando paso: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/simulacion/{sim_id}/auto")
async def ejecutar_simulacion_completa(sim_id: str, max_pasos: int = 500):
    """
    Ejecuta la simulación completa hasta terminar o alcanzar max_pasos.
    """
    if sim_id not in simulaciones_activas:
        raise HTTPException(status_code=404, detail="Simulación no encontrada")
    
    sim = simulaciones_activas[sim_id]
    coordinador = sim['coordinador']
    
    try:
        logger.info(f"🏁 Ejecutando simulación completa {sim_id}")
        
        resultado = coordinador.ejecutar_episodio_completo(max_pasos=max_pasos)
        
        sim['activa'] = False
        sim['resultado_final'] = resultado
        
        logger.info(f"✅ Simulación {sim_id} completada:")
        logger.info(f"   - Clientes servidos: {resultado['clientes_servidos']}/{resultado['clientes_totales']}")
        logger.info(f"   - Recompensa total: {resultado['recompensa_total']:.2f}")
        logger.info(f"   - Pasos ejecutados: {resultado['pasos_ejecutados']}")
        
        return {
            'mensaje': 'Simulación completada',
            'resultado': resultado
        }
        
    except Exception as e:
        logger.error(f"❌ Error en simulación completa: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/simulacion/{sim_id}")
async def detener_simulacion(sim_id: str):
    """
    Detiene y elimina una simulación activa.
    """
    if sim_id not in simulaciones_activas:
        raise HTTPException(status_code=404, detail="Simulación no encontrada")
    
    del simulaciones_activas[sim_id]
    logger.info(f"🛑 Simulación {sim_id} detenida y eliminada")
    
    return {'mensaje': 'Simulación detenida', 'simulacion_id': sim_id}


@router.get("/simulaciones")
async def listar_simulaciones():
    """
    Lista todas las simulaciones activas.
    """
    lista = []
    for sim_id, sim in simulaciones_activas.items():
        lista.append({
            'id': sim_id,
            'activa': sim['activa'],
            'paso': sim['paso_actual'],
            'inicio': sim['inicio'].isoformat(),
            'num_camiones': sim['config'].num_camiones,
            'num_clientes': sim['config'].num_clientes
        })
    
    return {'simulaciones': lista, 'total': len(lista)}


# ==================== WEBSOCKET ====================

# Mantener conexiones activas
websocket_connections: List[WebSocket] = []

@router.websocket("/ws/{sim_id}")
async def websocket_endpoint(websocket: WebSocket, sim_id: str):
    """
    WebSocket para streaming de eventos en tiempo real.
    Envía actualizaciones cada vez que ocurre un evento en la simulación.
    """
    await websocket.accept()
    websocket_connections.append(websocket)
    
    logger.info(f"🔌 WebSocket conectado para simulación {sim_id}")
    
    try:
        if sim_id not in simulaciones_activas:
            await websocket.send_json({
                'error': 'Simulación no encontrada',
                'simulacion_id': sim_id
            })
            await websocket.close()
            return
        
        sim = simulaciones_activas[sim_id]
        ultimo_paso_enviado = -1
        
        # Loop de envío de actualizaciones
        while sim['activa']:
            # Verificar si hay nuevos eventos
            if sim['paso_actual'] > ultimo_paso_enviado:
                # Obtener estado actual
                estado = await obtener_estado_simulacion(sim_id)
                
                # Enviar actualización
                await websocket.send_json({
                    'tipo': 'actualizacion',
                    'simulacion_id': sim_id,
                    'estado': estado
                })
                
                ultimo_paso_enviado = sim['paso_actual']
            
            # Pequeña pausa para no saturar
            await asyncio.sleep(0.1)
        
        # Simulación terminada
        await websocket.send_json({
            'tipo': 'fin',
            'simulacion_id': sim_id,
            'mensaje': 'Simulación completada'
        })
        
    except WebSocketDisconnect:
        logger.info(f"🔌 WebSocket desconectado para {sim_id}")
    except Exception as e:
        logger.error(f"❌ Error en WebSocket: {e}")
    finally:
        if websocket in websocket_connections:
            websocket_connections.remove(websocket)


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        'status': 'ok',
        'servicio': 'MAS Router',
        'simulaciones_activas': len(simulaciones_activas),
        'websockets_activos': len(websocket_connections)
    }
