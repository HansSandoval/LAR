# 🎨 VISUALIZADOR VRP - RESUMEN COMPLETO

## 🎯 ¿Qué es?

Una **aplicación web interactiva** (desarrollada con **Streamlit**) que te permite visualizar, experimentar y analizar el comportamiento del planificador de rutas VRP en **localhost** de forma didáctica.

---

## 🚀 Inicio Rápido (2 comandos)

```bash
cd c:\Users\hanss\Desktop\LAR

# Ejecutar la aplicación
C:\Users\hanss\Desktop\LAR\gestion_rutas\venv\Scripts\python.exe -m streamlit run app_visualizador_vrp.py
```

**Resultado**: Se abre automáticamente en http://localhost:8501

---

## 📦 Contenido Entregado

### Archivo Principal
- **`app_visualizador_vrp.py`** (700+ líneas)
  - Aplicación Streamlit completa
  - 4 escenarios predefinidos + personalizado
  - Visualización interactiva con Plotly
  - Cálculos en tiempo real

### Documentación
- **`README_VISUALIZADOR.md`** (esta carpeta)
  - Guía rápida de inicio
  - Ejemplos de uso
  - Solución de problemas

- **`GUIA_VISUALIZADOR.md`** (esta carpeta)
  - Guía completa y detallada
  - Interpretación de gráficos
  - Experimentos sugeridos
  - Tips y trucos

---

## 🎨 Interfaz Gráfica

### Barra Lateral Izquierda (Controles)
```
┌─────────────────────────┐
│ ⚙️ CONFIGURACIÓN        │
├─────────────────────────┤
│ Escenario:              │
│ ○ Simple (5)            │
│ ○ Medio (9)             │
│ ○ Complejo (15)         │
│ ○ Personalizado         │
├─────────────────────────┤
│ Parámetros:             │
│ Capacidad: [20 kg] ◄─►  │
│ Vehículos: [2] ◄─►      │
│ ☑ Aplicar 2-opt         │
│ Timeout: [30s] ◄─►      │
└─────────────────────────┘
```

### Pantalla Principal (Centro/Derecha)
```
┌─────────────────────────────────────────────────────┐
│ 📊 MÉTRICAS                                         │
│ Nodos: 9 │ Vehículos: 2 │ Capacidad: 40kg │ Demanda: 32kg │
├─────────────────────────────────────────────────────┤
│ NN: 249.12 km          │ NN+2opt: 233.70 km         │
│                        │ Mejora: -6.2%              │
├─────────────────────────────────────────────────────┤
│ [Mapa NN]              │ [Mapa 2-opt]               │
│ (lado izquierdo)       │ (lado derecho)             │
├─────────────────────────────────────────────────────┤
│ [Tabla NN]             │ [Tabla 2-opt]              │
├─────────────────────────────────────────────────────┤
│ [Gráfico de Barras Comparativo]                     │
├─────────────────────────────────────────────────────┤
│ Distancia NN: 249.12 km │ Ahorro: 15.42 km (6.2%)  │
│ Distancia Opt: 233.70 km │ Rutas: 2/2              │
└─────────────────────────────────────────────────────┘
```

---

## 🎮 Funcionalidades

### 1. Selección de Escenarios
```
Simple (5 puntos)
├─ Depósito + 4 zonas
├─ Perfecto para entender conceptos
└─ Cálculo: <10ms

Medio (9 puntos)
├─ Depósito + 8 zonas
├─ Caso más realista
└─ Cálculo: ~100ms

Complejo (15 puntos)
├─ Depósito + 14 zonas
├─ Instancia desafiante
└─ Cálculo: 0.5-1.5s

Personalizado
├─ Define tus parámetros
├─ Genera instancias aleatorias
└─ Máxima flexibilidad
```

### 2. Parámetros Ajustables
- **Capacidad**: 10-50 kg por vehículo
- **Vehículos**: 1-5 disponibles
- **2-opt**: Habilitar/Deshabilitar
- **Timeout**: 1-60 segundos

### 3. Visualizaciones
- 📍 **Mapas interactivos**: Rutas sobre coordenadas
- 📊 **Gráficos**: Comparativa de distancias
- 📋 **Tablas**: Detalles de rutas
- 📈 **Métricas**: KPIs en tiempo real

### 4. Interactividad Real-Time
- Cambia parámetros
- Gráficos actualizan instantáneamente
- Resultados se recalculan automáticamente

---

## 📊 Ejemplo de Uso

### Paso 1: Iniciar

```bash
C:\Users\hanss\Desktop\LAR\gestion_rutas\venv\Scripts\python.exe -m streamlit run app_visualizador_vrp.py
```

### Paso 2: Se abre http://localhost:8501

### Paso 3: Seleccionar "Ejemplo Medio"

Ver:
- 9 puntos de recolección
- Depósito central

### Paso 4: Observar Mapas

**Mapa Izquierdo (NN)**:
- Solución inicial rápida
- Posibles cruces de rutas

**Mapa Derecho (NN+2opt)**:
- Solución mejorada
- Mejor ordenamiento

### Paso 5: Analizar Métricas

```
NN:        249.12 km
NN+2opt:   233.70 km
────────────────────
Mejora:    6.2% ✅
```

### Paso 6: Experimentar

- Baja capacidad → Más rutas
- Aumenta vehículos → Menos distancia
- Desactiva 2-opt → Ve diferencia

---

## 🎓 Lo que Verás (Ejemplo)

### Visualización en Mapa

```
         P7
      D (Depósito)
       * ★ *
      / | \
     /  |  \
   P1   P4  P2
   ●    ●   ●
    \   |  /
     \ /\ /
      P3 P8
      ●  ●
      
★ = Depósito (estrella roja)
● = Puntos de recolección (círculos azules)
— = Trayectos (líneas coloreadas)

Colores diferentes = Vehículos diferentes
Líneas que cruzan = Posible mejora con 2-opt
```

### Gráfico Comparativo

```
Distancia (km)
    ▲
150 │        ┌─────┐
    │        │NN  │
100 │ ┌─────┐│    │
    │ │NN  │└────┬┴──┐
 50 │ │2opt│     │NN+│
    │ │    │     │2op│
    └─┼────┼─────┼───┼──→ Rutas
      │    │     │   │
    Ruta 1 Ruta 2 Ruta 3

NN (azul) > NN+2opt (verde)
→ 2-opt mejoró la solución
```

### Tabla de Detalles

```
NN Puro:
┌─────────────────────────────────────┐
│ Ruta      │ Secuencia      │ Distancia │
├─────────────────────────────────────┤
│ Veh 1     │ D→P1→P3→P2→D   │ 113.45 km │
│ Veh 2     │ D→P4→P5→D      │ 135.67 km │
└─────────────────────────────────────┘

NN+2opt:
┌─────────────────────────────────────┐
│ Ruta      │ Secuencia      │ Distancia │
├─────────────────────────────────────┤
│ Veh 1     │ D→P1→P2→P3→D   │ 98.03 km  │
│ Veh 2     │ D→P4→P5→D      │ 135.67 km │
└─────────────────────────────────────┘
```

---

## 🔬 Experimentos Sugeridos

### Experimento 1: Impacto de 2-opt
1. Selecciona: **Ejemplo Medio**
2. **Desactiva 2-opt**
   - Nota: 249.12 km
3. **Activa 2-opt**
   - Nota: 233.70 km
4. **Diferencia: -6.2% ✅**

### Experimento 2: Efecto de Capacidad
1. Selecciona: **Ejemplo Simple**
2. Capacidad **10 kg**
   - Más rutas necesarias
3. Capacidad **20 kg**
   - Balance óptimo
4. Capacidad **30 kg**
   - Menos rutas

### Experimento 3: Escalabilidad
1. Personalizado: **5 nodos**
   - Tiempo: <50ms
2. Personalizado: **10 nodos**
   - Tiempo: ~100ms
3. Personalizado: **15 nodos**
   - Tiempo: ~500ms
4. Ver: O(n²) crecimiento

### Experimento 4: Aleatoriedad
1. Personalizado: **Genera 10 nodos**
2. **🔀 Generar aleatorio** (5 veces)
3. Compara: Variabilidad de mejoras
4. Nota: Diferentes instancias = diferentes mejoras

---

## 📈 Métricas Mostradas

| Métrica | Significado |
|---------|------------|
| **Nodos** | Total de zonas de recolección |
| **Vehículos** | Camiones disponibles |
| **Capacidad** | Máximo kg por vehículo |
| **Distancia NN** | Con Nearest Neighbor puro |
| **Distancia Opt** | Después de 2-opt |
| **Mejora %** | (NN - Opt) / NN × 100 |
| **Rutas Utilizadas** | Cuántos vehículos usados / disponibles |

---

## 🛠️ Requisitos Técnicos

### Instalado Automáticamente
```
streamlit >= 1.0
plotly >= 5.0
pandas >= 1.0
numpy >= 1.0
```

### Instalación Manual
```bash
C:\Users\hanss\Desktop\LAR\gestion_rutas\venv\Scripts\pip.exe install streamlit plotly pandas numpy
```

---

## 📱 Acceso

### Local Solamente ✅
- URL: **http://localhost:8501**
- Rango: Tu computadora
- Seguridad: Total (sin internet)

### Para Permitir Red (opcional)
```bash
streamlit run app_visualizador_vrp.py --server.address 0.0.0.0
```
Luego acceder desde otra máquina con: http://[IP_TU_PC]:8501

---

## 🎯 Características Didácticas

✅ **Visualización clara**: Mapas interactivos  
✅ **Parámetros ajustables**: Experimenta en tiempo real  
✅ **Comparativa lado a lado**: NN vs NN+2opt  
✅ **Múltiples escenarios**: Simple → Complejo  
✅ **Generador aleatorio**: Prueba infinitas instancias  
✅ **Métricas en vivo**: KPIs actualizados  
✅ **Tablas detalladas**: Detalles de cada ruta  
✅ **Gráficos comparativos**: Barras, líneas, mapas  

---

## 🐛 Solución de Problemas

### "No se abre"
```bash
pip install streamlit plotly pandas
python -m streamlit run app_visualizador_vrp.py
```

### "No se ve nada"
- Recarga la página (F5)
- Verifica que Plotly está instalado

### "Está lento"
- Baja timeout de 2-opt
- Reduce número de nodos
- Desactiva 2-opt

### "Error de importación"
- Usa la ruta completa del venv
- Verifica sys.path en app_visualizador_vrp.py

---

## 📚 Documentación Relacionada

Dentro de este proyecto:
- `README_VISUALIZADOR.md` - Esta carpeta
- `GUIA_VISUALIZADOR.md` - Guía detallada
- `gestion_rutas/vrp/README.md` - Arquitectura VRP
- `gestion_rutas/vrp/OPTIMIZACION_2OPT.md` - Teoría 2-opt
- `gestion_rutas/vrp/test_2opt.py` - Tests

---

## 🌟 Ventajas de Esta Visualización

| Aspecto | Streamlit vs API |
|--------|-----------------|
| **Visualización** | ✅ Nativa | ❌ Manual |
| **Interactividad** | ✅ Real-time | ❌ Request/Response |
| **Didáctica** | ✅ Muy clara | ⚠️ Requiere análisis |
| **Experimentación** | ✅ Inmediata | ⚠️ Requiere requests |
| **Mapas** | ✅ Plotly interactivo | ❌ No |
| **Comparativas** | ✅ Lado a lado | ❌ Manual |

---

## 🎓 Flujo de Aprendizaje

```
1. Ejecuta Streamlit
        ↓
2. Selecciona "Simple"
        ↓
3. Observa mapas NN y 2-opt
        ↓
4. Lee tablas detalladas
        ↓
5. Nota diferencias (mejora ~6%)
        ↓
6. Experimenta con parámetros
        ↓
7. Intenta "Medio" y "Complejo"
        ↓
8. Genera instancias aleatorias
        ↓
9. Entiende completamente VRP + 2-opt ✅
```

---

## ✨ Conclusión

Con esta visualización:
- 👁️ **VES** cómo funciona el planificador
- 🧠 **ENTIENDES** NN vs 2-opt
- 🎮 **EXPERIMENTAS** con parámetros
- 📊 **ANALIZAS** resultados visualmente
- 🚀 **APRENDES** de forma didáctica

**Ahora el planificador VRP es completamente transparente y educativo.**

---

## 🚀 Comando Final

```bash
cd c:\Users\hanss\Desktop\LAR
C:\Users\hanss\Desktop\LAR\gestion_rutas\venv\Scripts\python.exe -m streamlit run app_visualizador_vrp.py
```

¡A disfrutar! 🎉
