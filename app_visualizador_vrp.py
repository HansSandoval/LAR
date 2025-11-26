"""
app_visualizador_vrp.py

Aplicación Streamlit para visualizar y analizar soluciones VRP.
Interfaz didáctica para ver el funcionamiento del planificador de rutas.

Ejecución:
    streamlit run app_visualizador_vrp.py
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Agregar ruta del proyecto
sys.path.insert(0, str(Path(__file__).parent / "gestion_rutas"))

from vrp import VRPInput, NodeCoordinate, planificar_vrp_api
from vrp.optimizacion import calcula_distancia_ruta
from vrp.planificador import validate_and_prepare, nearest_neighbor_vrp
from vrp.inference_ppo import planificar_con_ppo


# Configuración de página
st.set_page_config(
    page_title="Visualizador VRP - Planificador de Rutas",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
    .improvement {
        background: linear-gradient(135deg, #00d084 0%, #00d2fc 100%);
        color: white;
        padding: 15px;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# Título
st.title("🚚 Visualizador de Planificador VRP")
st.markdown("**Sistema interactivo para optimización de rutas de recolección**")

# ============================================================================
# BARRA LATERAL - CONFIGURACIÓN
# ============================================================================

st.sidebar.header("⚙️ Configuración")

# Selector de escenario predefinido
escenario = st.sidebar.radio(
    "Selecciona un escenario:",
    ["Ejemplo Simple (5 puntos)", "Ejemplo Medio (9 puntos)", "Ejemplo Complejo (15 puntos)", "Personalizado"]
)

# ============================================================================
# DEFINIR ESCENARIOS PREDEFINIDOS
# ============================================================================

def crear_escenario_simple():
    """Escenario con 5 puntos - iquique"""
    return [
        NodeCoordinate(id='D', x=0, y=0, demand=0),
        NodeCoordinate(id='P1', x=10, y=15, demand=5),
        NodeCoordinate(id='P2', x=25, y=10, demand=3),
        NodeCoordinate(id='P3', x=20, y=25, demand=4),
        NodeCoordinate(id='P4', x=5, y=20, demand=2),
    ]

def crear_escenario_medio():
    """Escenario con 9 puntos - más realista"""
    return [
        NodeCoordinate(id='D', x=0, y=0, demand=0),
        NodeCoordinate(id='P1', x=10, y=20, demand=5),
        NodeCoordinate(id='P2', x=30, y=15, demand=3),
        NodeCoordinate(id='P3', x=25, y=35, demand=4),
        NodeCoordinate(id='P4', x=15, y=10, demand=2),
        NodeCoordinate(id='P5', x=40, y=30, demand=6),
        NodeCoordinate(id='P6', x=50, y=10, demand=4),
        NodeCoordinate(id='P7', x=35, y=50, demand=3),
        NodeCoordinate(id='P8', x=20, y=45, demand=5),
    ]

def crear_escenario_complejo():
    """Escenario con 15 puntos - más desafiante"""
    np.random.seed(42)
    nodos = [NodeCoordinate(id='D', x=50, y=50, demand=0)]
    ids = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N']
    for idx, id_node in enumerate(ids):
        x = np.random.uniform(0, 100)
        y = np.random.uniform(0, 100)
        demand = np.random.randint(2, 10)
        nodos.append(NodeCoordinate(id=id_node, x=x, y=y, demand=demand))
    return nodos

# Cargar escenario
if escenario == "Ejemplo Simple (5 puntos)":
    nodos = crear_escenario_simple()
elif escenario == "Ejemplo Medio (9 puntos)":
    nodos = crear_escenario_medio()
elif escenario == "Ejemplo Complejo (15 puntos)":
    nodos = crear_escenario_complejo()
else:  # Personalizado
    st.sidebar.write("**Crear escenario personalizado**")
    num_puntos = st.sidebar.slider("Número de puntos:", 3, 20, 5)
    capacidad = st.sidebar.slider("Capacidad por vehículo (kg):", 10, 50, 20)
    vehículos = st.sidebar.slider("Número de vehículos:", 1, 5, 2)
    
    # Generar aleatorio (default o al presionar botón)
    np.random.seed(np.random.randint(0, 10000))
    nodos = [NodeCoordinate(id='D', x=50, y=50, demand=0)]
    for i in range(num_puntos - 1):
        nodos.append(NodeCoordinate(
            id=f'P{i+1}',
            x=np.random.uniform(0, 100),
            y=np.random.uniform(0, 100),
            demand=np.random.randint(2, 8)
        ))
    
    if st.sidebar.button("🔀 Generar aleatorio"):
        np.random.seed(np.random.randint(0, 10000))
        nodos = [NodeCoordinate(id='D', x=50, y=50, demand=0)]
        for i in range(num_puntos - 1):
            nodos.append(NodeCoordinate(
                id=f'P{i+1}',
                x=np.random.uniform(0, 100),
                y=np.random.uniform(0, 100),
                demand=np.random.randint(2, 8)
            ))
        st.rerun()

# Parámetros de optimización
st.sidebar.markdown("---")
st.sidebar.header("🔧 Parámetros")

# Obtener del escenario o permitir personalización
if escenario != "Personalizado":
    capacidad = st.sidebar.slider("Capacidad por vehículo (kg):", 10, 50, 20)
    vehículos = st.sidebar.slider("Número de vehículos:", 1, 5, 2)

aplicar_2opt = st.sidebar.checkbox("Aplicar 2-opt (búsqueda local)", value=True)
timeout_2opt = st.sidebar.slider("Timeout 2-opt (segundos):", 1, 60, 30) if aplicar_2opt else 30

# ============================================================================
# PROCESAR ENTRADA Y GENERAR SOLUCIONES
# ============================================================================

entrada = VRPInput(candidates=nodos, vehicle_count=vehículos, capacity=capacidad)

# Obtener matriz de distancias
prep = validate_and_prepare(entrada)
dist_matrix = prep['dist_matrix']
demands = [float(n.demand or 0.0) for n in nodos]

# Solución NN (sin 2-opt)
result_nn = nearest_neighbor_vrp(dist_matrix, demands, vehículos, capacidad)
routes_nn = result_nn['routes']
distancia_nn = result_nn['total_distance']

# Convertir IDs de salida a índices para gráficas
def ids_a_indices(routes_ids):
    """Convierte rutas con IDs a índices."""
    # Crear mapa robusto para IDs (str y int)
    id_to_idx = {}
    for i, n in enumerate(nodos):
        id_val = n.id if n.id is not None else i
        id_to_idx[id_val] = i
        id_to_idx[str(id_val)] = i # Asegurar versión string
        
    rutas_indices = []
    for ruta in routes_ids:
        ruta_idx = []
        for id_ in ruta:
            if id_ in id_to_idx:
                ruta_idx.append(id_to_idx[id_])
            elif str(id_) in id_to_idx:
                ruta_idx.append(id_to_idx[str(id_)])
        rutas_indices.append(ruta_idx)
    return rutas_indices

# Selección de algoritmo
st.sidebar.markdown("---")
algoritmo = st.sidebar.radio("🧠 Algoritmo de Planificación:", ["Heurística (NN + 2-opt)", "Agente IA (PPO - RL)"])

if algoritmo == "Agente IA (PPO - RL)":
    with st.spinner("🤖 El Agente IA está explorando el entorno..."):
        rutas_ppo_ids = planificar_con_ppo(nodos, vehículos, capacidad)
    
    if rutas_ppo_ids:
        print(f"DEBUG: Rutas IA (IDs): {rutas_ppo_ids}")
        routes_final = ids_a_indices(rutas_ppo_ids)
        print(f"DEBUG: Rutas IA (Indices): {routes_final}")
        # Calcular distancia usando la matriz de distancias existente
        distancia_final = sum(calcula_distancia_ruta(r, dist_matrix) for r in routes_final)
        st.sidebar.success("✅ Ruta generada por IA")
    else:
        st.error("⚠️ No se pudo cargar el modelo PPO o falló la inferencia.")
        routes_final = []
        distancia_final = 0.0
else:
    # Solución NN+2opt
    salida = planificar_vrp_api(entrada, aplicar_2opt=aplicar_2opt, timeout_2opt=timeout_2opt)
    routes_final = ids_a_indices(salida.routes)
    distancia_final = salida.total_distance

# ============================================================================
# MÉTRICAS PRINCIPALES
# ============================================================================

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("📍 Nodos", len(nodos) - 1)

with col2:
    st.metric("🚚 Vehículos", vehículos)

with col3:
    st.metric("📦 Capacidad Total", f"{vehículos * capacidad} kg")

with col4:
    demanda_total = sum(n.demand or 0 for n in nodos)
    st.metric("📊 Demanda Total", f"{demanda_total} kg")

# ============================================================================
# COMPARATIVA
# ============================================================================

st.markdown("---")
col_comparison_l, col_comparison_r = st.columns(2)

with col_comparison_l:
    st.subheader("📈 Nearest Neighbor (Inicial)")
    st.metric("Distancia", f"{distancia_nn:.2f} km", delta=f"(Inicial)")

with col_comparison_r:
    if algoritmo == "Agente IA (PPO - RL)":
        st.subheader("🤖 Agente IA (PPO)")
        mejora = distancia_nn - distancia_final
        mejora_pct = (mejora / distancia_nn * 100) if distancia_nn > 0 else 0
        st.metric(
            "Distancia", 
            f"{distancia_final:.2f} km",
            delta=f"-{mejora:.2f} km ({mejora_pct:.1f}%)",
            delta_color="inverse"
        )
    elif aplicar_2opt:
        mejora = distancia_nn - distancia_final
        mejora_pct = (mejora / distancia_nn * 100) if distancia_nn > 0 else 0
        st.subheader("✨ NN + 2-opt (Optimizado)")
        st.metric(
            "Distancia", 
            f"{distancia_final:.2f} km",
            delta=f"-{mejora:.2f} km ({mejora_pct:.1f}%)",
            delta_color="inverse"
        )
    else:
        st.subheader("NN + 2-opt (Desactivado)")
        st.metric("Distancia", f"{distancia_final:.2f} km", delta="(Sin 2-opt)")

# ============================================================================
# VISUALIZACIÓN 1: MAPA CON RUTAS (NN)
# ============================================================================

st.markdown("---")
col_map_nn, col_map_opt = st.columns(2)

def crear_mapa_rutas(routes, dist_matrix, titulo):
    """Crea visualización de rutas."""
    fig = go.Figure()
    
    colores_ruta = px.colors.qualitative.Plotly
    
    # Graficar cada ruta
    for idx_ruta, ruta in enumerate(routes):
        color = colores_ruta[idx_ruta % len(colores_ruta)]
        dist_ruta = calcula_distancia_ruta(ruta, dist_matrix)
        
        # Coordenadas de la ruta
        xs = [nodos[i].x for i in ruta]
        ys = [nodos[i].y for i in ruta]
        
        # Línea de ruta
        fig.add_trace(go.Scatter(
            x=xs, y=ys,
            mode='lines+markers',
            name=f'Ruta {idx_ruta + 1} ({dist_ruta:.1f} km)',
            line=dict(color=color, width=2),
            marker=dict(size=8),
            hovertemplate='<b>%{text}</b><extra></extra>',
            text=[nodos[i].id for i in ruta],
        ))
    
    # Graficar depósito destacado
    fig.add_trace(go.Scatter(
        x=[nodos[0].x],
        y=[nodos[0].y],
        mode='markers',
        name='Depósito',
        marker=dict(size=20, color='red', symbol='star'),
        hovertemplate='<b>Depósito</b><extra></extra>'
    ))
    
    # Graficar puntos de recolección
    xs_puntos = [nodos[i].x for i in range(1, len(nodos))]
    ys_puntos = [nodos[i].y for i in range(1, len(nodos))]
    demandas = [nodos[i].demand for i in range(1, len(nodos))]
    ids_puntos = [nodos[i].id for i in range(1, len(nodos))]
    
    fig.add_trace(go.Scatter(
        x=xs_puntos, y=ys_puntos,
        mode='markers',
        name='Puntos',
        marker=dict(size=10, color='lightblue', line=dict(width=1, color='blue')),
        text=[f"{id_}: {dem} kg" for id_, dem in zip(ids_puntos, demandas)],
        hovertemplate='<b>%{text}</b><extra></extra>',
        showlegend=False
    ))
    
    fig.update_layout(
        title=titulo,
        xaxis_title="X (km)",
        yaxis_title="Y (km)",
        hovermode='closest',
        height=500,
        showlegend=True,
        template='plotly_white',
    )
    
    return fig

with col_map_nn:
    fig_nn = crear_mapa_rutas(routes_nn, dist_matrix, "🗺️ Nearest Neighbor (Inicial)")
    st.plotly_chart(fig_nn, use_container_width=True)

with col_map_opt:
    fig_opt = crear_mapa_rutas(routes_final, dist_matrix, "🗺️ Después de 2-opt (Optimizado)")
    st.plotly_chart(fig_opt, use_container_width=True)

# ============================================================================
# TABLA DETALLADA DE RUTAS
# ============================================================================

st.markdown("---")
st.subheader("📋 Detalle de Rutas")

col_detail_nn, col_detail_opt = st.columns(2)

def crear_tabla_rutas(routes, dist_matrix, titulo):
    """Crea tabla con detalles de rutas."""
    data = []
    for idx_ruta, ruta in enumerate(routes):
        dist = calcula_distancia_ruta(ruta, dist_matrix)
        demanda_ruta = sum(nodos[i].demand or 0 for i in ruta[1:-1])
        secuencia = ' → '.join(nodos[i].id for i in ruta)
        data.append({
            'Ruta': f'Vehículo {idx_ruta + 1}',
            'Secuencia': secuencia,
            'Distancia (km)': f"{dist:.2f}",
            'Demanda (kg)': f"{demanda_ruta:.0f}",
        })
    
    return pd.DataFrame(data)

with col_detail_nn:
    st.markdown("**Nearest Neighbor**")
    df_nn = crear_tabla_rutas(routes_nn, dist_matrix, "NN")
    st.dataframe(df_nn, use_container_width=True, hide_index=True)

with col_detail_opt:
    st.markdown("**NN + 2-opt (Optimizado)**")
    df_opt = crear_tabla_rutas(routes_final, dist_matrix, "Optimizado")
    st.dataframe(df_opt, use_container_width=True, hide_index=True)

# ============================================================================
# ANÁLISIS DE DISTANCIAS POR RUTA
# ============================================================================

st.markdown("---")
st.subheader("📊 Comparativa de Distancias por Ruta")

col_chart_dist = st.columns(1)[0]

datos_comparativa = []
for idx in range(max(len(routes_nn), len(routes_final))):
    dist_nn = calcula_distancia_ruta(routes_nn[idx], dist_matrix) if idx < len(routes_nn) else 0
    dist_opt = calcula_distancia_ruta(routes_final[idx], dist_matrix) if idx < len(routes_final) else 0
    datos_comparativa.append({
        'Ruta': f'Vehículo {idx + 1}',
        'NN (km)': dist_nn,
        'NN+2opt (km)': dist_opt,
    })

df_comparativa = pd.DataFrame(datos_comparativa)

fig_dist = go.Figure(data=[
    go.Bar(name='Nearest Neighbor', x=df_comparativa['Ruta'], y=df_comparativa['NN (km)'], marker_color='lightblue'),
    go.Bar(name='NN + 2-opt', x=df_comparativa['Ruta'], y=df_comparativa['NN+2opt (km)'], marker_color='lightgreen'),
])

fig_dist.update_layout(
    barmode='group',
    title='Distancia por Ruta: NN vs NN+2-opt',
    xaxis_title='Ruta',
    yaxis_title='Distancia (km)',
    height=400,
    template='plotly_white',
)

st.plotly_chart(fig_dist, use_container_width=True)

# ============================================================================
# INDICADORES CLAVE
# ============================================================================

st.markdown("---")
st.subheader("🎯 Indicadores Clave")

col_ind1, col_ind2, col_ind3, col_ind4 = st.columns(4)

with col_ind1:
    dist_total_nn = distancia_nn
    st.metric("Distancia NN", f"{dist_total_nn:.2f} km")

with col_ind2:
    dist_total_opt = distancia_final
    st.metric("Distancia Opt", f"{dist_total_opt:.2f} km")

with col_ind3:
    if dist_total_nn > 0:
        ahorro = dist_total_nn - dist_total_opt
        ahorro_pct = (ahorro / dist_total_nn * 100)
        st.metric("Ahorro", f"{ahorro:.2f} km ({ahorro_pct:.1f}%)")
    else:
        st.metric("Ahorro", "0 km")

with col_ind4:
    num_rutas = len(routes_final)
    st.metric("Rutas Utilizadas", f"{num_rutas}/{vehículos}")

# ============================================================================
# INFORMACIÓN Y FOOTER
# ============================================================================

st.markdown("---")
st.info(
    """
    **ℹ️ Información:**
    - **Nearest Neighbor**: Heurística constructiva rápida (O(n²))
    - **2-opt**: Búsqueda local que intercambia aristas para mejorar la solución
    - **Mejora típica**: 5-20% de reducción de distancia
    - Todas las restricciones de capacidad se respetan
    """
)

st.markdown(
    """
    <footer style='text-align: center; margin-top: 50px; color: gray;'>
        <small>🚚 Visualizador VRP - Planificador de Rutas de Recolección</small><br>
        <small>Desarrollado con Streamlit + Plotly</small>
    </footer>
    """,
    unsafe_allow_html=True
)
