# 🚛 Sistema Integral: LSTM + MAS + VRP

## ¿Qué es esto?

Este es el **sistema completo e integrado** que combina:
1. **Predicciones LSTM**: Muestra todos los puntos de basura con sus cantidades estimadas
2. **Optimización VRP**: Calcula la ruta más eficiente
3. **Multi-Agentes (MAS)**: Camiones inteligentes que cooperan entre sí
4. **Visualización en Tiempo Real**: Mapa interactivo con actualización automática

## 📍 Acceso al Sistema

**URL Principal:**
```
http://localhost:8000/static/mapa_integral_lstm_mas.html
```

## 🎯 Cómo Funciona (Paso a Paso)

### PASO 1: Cargar Puntos de Basura
1. Selecciona una **fecha de recolección** en el calendario
2. Click en **"Cargar Puntos de Basura"**
3. Verás aparecer **74 puntos** en el mapa con colores:
   - 🟢 **Verde**: Baja cantidad (< 80 kg)
   - 🟠 **Naranja**: Media cantidad (80-120 kg)
   - 🔴 **Rojo**: Alta cantidad (> 120 kg)

### PASO 2: Configurar Camiones
- **Número de Camiones**: Cuántos camiones usar (1-10)
- **Capacidad por Camión**: Cuántos kg puede cargar cada uno (default: 3500 kg)

### PASO 3: Iniciar Simulación
1. Click en **"Iniciar Simulación"**
2. Los camiones aparecen en el mapa (círculos rojos numerados)
3. Se mueven automáticamente cada 2 segundos
4. Las rutas se dibujan dinámicamente (líneas rojas punteadas)

### PASO 4: Observar en Tiempo Real
El sistema actualiza automáticamente:
- **KG Recolectados**: Total de basura recogida
- **Puntos Servidos**: Cuántos puntos ya fueron visitados
- **Eficiencia**: Porcentaje de completitud
- **Estado de Camiones**: Carga actual y distancia recorrida

## 🔧 Conceptos Clave

### ¿Qué es un "Cliente"?
En el contexto de VRP (Vehicle Routing Problem):
- **Cliente = Punto de Recolección de Basura**
- **Número de Clientes = Cantidad de puntos a visitar**

Por ejemplo:
- 50 clientes = 50 contenedores de basura en diferentes calles
- Cada cliente tiene su ubicación GPS y cantidad de kg predicha

### ¿De dónde salen los puntos?
Los puntos vienen de tu archivo CSV:
```
gestion_rutas/lstm/datos_residuos_iquique.csv
```

Este CSV contiene:
- 74 puntos reales del Sector Sur de Iquique
- Coordenadas GPS reales de calles
- Historial de residuos por fecha
- Predicciones LSTM por punto

### ¿Qué hace el sistema MAS?
El sistema Multi-Agente hace que los camiones:
1. **Cooperen**: No compiten por el mismo punto
2. **Decidan inteligentemente**: Van al punto más cercano con más basura
3. **Evitan conflictos**: Si dos camiones quieren ir al mismo sitio, uno cede
4. **Optimizan rutas**: Minimizan distancia y maximizan recolección

## 📊 Paneles del Mapa

### Panel Derecho (Configuración)
- Selección de fecha
- Configuración de camiones
- Botones de control
- Leyenda de colores

### Panel Inferior Izquierdo (Estadísticas)
- KG recolectados en tiempo real
- Puntos servidos vs totales
- Eficiencia de la operación
- Lista de camiones con su estado

## 🎨 Elementos Visuales

| Elemento | Descripción |
|----------|-------------|
| 🔵 Círculo azul grande | Zona de cobertura (5 km de radio) |
| 🔵 Punto azul | Depot (base de operaciones) |
| 🟢🟠🔴 Círculos colores | Puntos de basura (tamaño = cantidad) |
| 🔴 Círculo numerado | Camión activo |
| ➖ Línea roja punteada | Ruta del camión |

## ❓ Preguntas Frecuentes

### ¿Por qué sale solo un punto verde?
**Antes:** Solo se veía el depot (base)
**Ahora:** Debes hacer click en "Cargar Puntos de Basura" primero

### ¿Qué pasa al hacer click en "Ejecutar Paso"?
Ese botón es del **sistema anterior** (individual).
**Ahora:** La simulación se actualiza **automáticamente cada 2 segundos**

### ¿Cuántos clientes debo poner?
El sistema **usa automáticamente** todos los puntos del CSV (74 puntos).
Si el CSV no está disponible, usa 50 puntos sintéticos como respaldo.

### ¿Los camiones siguen rutas reales?
Sí, los camiones:
1. Parten del depot real en Iquique
2. Visitan puntos con coordenadas GPS reales
3. Siguen la ruta óptima calculada por el algoritmo VRP

## 🐛 Solución de Problemas

### Problema: "No hay predicciones disponibles"
**Causa:** Falta el archivo CSV o modelo LSTM
**Solución:**
1. Verifica que exista: `gestion_rutas/lstm/datos_residuos_iquique.csv`
2. Si no existe, el sistema usará datos sintéticos

### Problema: Camiones no se mueven
**Causa:** Simulación no iniciada o ya terminó
**Solución:**
1. Verifica que hiciste click en "Iniciar Simulación"
2. Si ya terminó (100% eficiencia), click en "Detener" y luego "Iniciar" de nuevo

### Problema: No aparecen puntos en el mapa
**Causa:** No se ejecutó "Cargar Puntos de Basura"
**Solución:**
1. Selecciona una fecha
2. Click en "Cargar Puntos de Basura"
3. Espera a ver el mensaje de confirmación

## 🔄 Comparación: Antes vs Ahora

### Sistema Anterior (mas_tiempo_real.html)
- ❌ Solo mostraba depot
- ❌ "Número de clientes" abstracto
- ❌ No mostraba puntos LSTM
- ❌ Sin calendario
- ❌ "Ejecutar Paso" manual

### Sistema Nuevo (mapa_integral_lstm_mas.html)
- ✅ Muestra 74 puntos reales de basura
- ✅ Calendario para seleccionar fecha
- ✅ Predicciones LSTM visuales
- ✅ Camiones que se mueven automáticamente
- ✅ Rutas dibujadas en tiempo real
- ✅ Estadísticas actualizadas cada 2 segundos

## 🚀 Flujo Completo Recomendado

```mermaid
1. Abrir: http://localhost:8000/static/mapa_integral_lstm_mas.html
2. Seleccionar fecha del calendario
3. Click "Cargar Puntos de Basura" → Ver 74 puntos en colores
4. Configurar número de camiones (recomendado: 3)
5. Click "Iniciar Simulación" → Ver camiones moverse
6. Observar estadísticas actualizarse en tiempo real
7. Cuando llegue a 100%, click "Detener Simulación"
8. Para nueva simulación, cambiar fecha y repetir
```

## 📁 Archivos Importantes

| Archivo | Descripción |
|---------|-------------|
| `static/mapa_integral_lstm_mas.html` | **NUEVA** interfaz completa |
| `static/mapa_mas_tiempo_real.html` | Interfaz anterior (básica) |
| `routers/lstm_router.py` | API para predicciones LSTM |
| `routers/mas_router.py` | API para simulación MAS |
| `lstm/datos_residuos_iquique.csv` | Datos reales de Iquique |

## 💡 Consejos de Uso

1. **Primera vez**: Usa solo 3 camiones y 50 puntos para ver cómo funciona
2. **Velocidad**: La simulación es rápida (2 segundos por paso)
3. **Datos reales**: Selecciona fechas recientes para mejores predicciones
4. **Zoom**: Haz zoom en el mapa para ver detalles de cada punto
5. **Popups**: Click en cualquier punto/camión para ver información detallada

---

**Creado:** 2025-11-11
**Versión:** 2.0 - Sistema Integral
**Estado:** ✅ Operativo
