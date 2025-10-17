# 🎯 VISUALIZADOR VRP - GUÍA RÁPIDA DE INICIO

## ✨ ¿Qué es?

Una aplicación web interactiva (Streamlit) que te permite **visualizar y experimentar** con el planificador de rutas VRP en tiempo real, de forma didáctica y visual.

## 🚀 Cómo ejecutar

### Opción 1: Automática (recomendado)

```bash
cd c:\Users\hanss\Desktop\LAR
C:\Users\hanss\Desktop\LAR\gestion_rutas\venv\Scripts\python.exe -m streamlit run app_visualizador_vrp.py
```

**La app se abrirá automáticamente en: http://localhost:8501**

### Opción 2: Manual

```bash
# Terminal 1: Iniciar Streamlit
cd c:\Users\hanss\Desktop\LAR
streamlit run app_visualizador_vrp.py

# Terminal 2: Abrir en navegador (después de que Streamlit inicie)
# Ir a http://localhost:8501
```

### Opción 3: Si algo falla

```bash
# Verificar que las dependencias están instaladas
C:\Users\hanss\Desktop\LAR\gestion_rutas\venv\Scripts\pip.exe install streamlit plotly pandas

# Ejecutar nuevamente
C:\Users\hanss\Desktop\LAR\gestion_rutas\venv\Scripts\python.exe -m streamlit run C:\Users\hanss\Desktop\LAR\app_visualizador_vrp.py
```

---

## 📋 Lo que verás

### Interfaz Izquierda (Barra Lateral)
- **Selecciona escenario**: Simple, Medio, Complejo o Personalizado
- **Ajusta parámetros**:
  - Capacidad por vehículo
  - Número de vehículos
  - Habilitar/deshabilitar 2-opt
  - Timeout de optimización

### Interfaz Centro/Derecha (Pantalla Principal)

1️⃣ **Métricas** (arriba)
   - Total de nodos, vehículos, capacidad total, demanda total

2️⃣ **Comparativa** 
   - Distancia NN puro vs NN+2-opt
   - Muestra el % de mejora

3️⃣ **Mapas Visuales** (los más importantes!)
   - Mapa izquierdo: Solución inicial (NN)
   - Mapa derecho: Solución optimizada (NN+2-opt)
   - Estrella roja = Depósito
   - Círculos azules = Puntos de recolección
   - Líneas coloreadas = Rutas de cada vehículo

4️⃣ **Tablas Detalladas**
   - Muestra secuencia de cada ruta
   - Distancia recorrida
   - Demanda recolectada

5️⃣ **Gráfico de Barras**
   - Compara visualmente distancias por ruta

6️⃣ **Indicadores Clave**
   - Distancia total, ahorro, eficiencia

---

## 🎨 Escenarios Disponibles

### 1. **Ejemplo Simple (5 puntos)** - Para entender
- 5 zonas de recolección
- Ideal para ver cómo funciona
- Rápido (<100ms)

### 2. **Ejemplo Medio (9 puntos)** - Realista
- 9 zonas de recolección
- Caso más real
- Muestra mejoras típicas (~6%)

### 3. **Ejemplo Complejo (15 puntos)** - Desafiante
- 15 zonas aleatorias
- Ver rendimiento en casos mayores
- Tiempo: 0.5-1.5 segundos

### 4. **Personalizado** - Experimenta
- Crea tu propia instancia
- Genera aleatoriamente con parámetros
- Prueba múltiples escenarios

---

## 🎮 Ejemplos Interactivos

### Experimento 1: Ver el impacto de 2-opt

1. Selecciona: **Ejemplo Medio**
2. Parámetros: Capacidad 20, Vehículos 2
3. **Desactiva 2-opt** (unchecked)
   - Nota la distancia y rutas
4. **Activa 2-opt** (checked)
   - Observa cómo mejora (~6% típicamente)
5. Compara los mapas lado a lado

### Experimento 2: Efecto de la capacidad

1. Selecciona: **Ejemplo Simple**
2. Parámetros: Vehículos 2, **Capacidad 10**
   - Nota: Probablemente necesita más rutas
3. **Capacidad 20**
   - Menos rutas, distancia menor
4. **Capacidad 30**
   - Aún menos rutas
5. Observa la relación entre capacidad y eficiencia

### Experimento 3: Generador aleatorio

1. Selecciona: **Personalizado**
2. Desliza: Número de puntos a 10
3. Click: **🔀 Generar aleatorio**
4. Observa la solución
5. Click nuevamente para nueva instancia aleatoria
6. Nota: Cada instancia es diferente

---

## 📊 Qué significan los gráficos

### Mapa de Rutas
```
★ Estrella roja   = Depósito (salida/retorno)
● Círculos azules = Puntos de recolección
─ Líneas colores  = Ruta de cada vehículo

Verde    = Ruta 1
Azul     = Ruta 2
Naranja  = Ruta 3
etc.
```

**Lectura:**
- Cada línea es un vehículo
- Comienza en ★, visita ●, retorna a ★
- Líneas que se cruzan = puede haber mejora
- Líneas sin cruces = probablemente óptimas

### Gráfico de Barras Comparativo
```
Azul  (Nearest Neighbor puro)
Verde (Después de 2-opt)

Barra verde más corta = 2-opt mejoró la ruta
Barra de mismo tamaño  = Ruta ya era óptima
```

### Tabla de Rutas
```
Vehículo 1: D → P1 → P3 → D
├─ Distancia: 45.2 km
└─ Demanda: 12 kg (respeta límite 20 kg)

Vehículo 2: D → P2 → P4 → D
├─ Distancia: 38.5 km
└─ Demanda: 8 kg
```

---

## 🔧 Parámetros Clave

### Capacidad por Vehículo
- **Baja (5 kg)**: Muchas rutas pequeñas
- **Media (20 kg)**: Balance (típico)
- **Alta (50 kg)**: Pocas rutas grandes

### Número de Vehículos
- **1**: Un único camión (puede no caber todo)
- **2-3**: Típico para ciudades pequeñas
- **5+**: Para ciudades grandes

### 2-opt
- **ON**: Busca mejorar iterativamente (recomendado)
- **OFF**: Solo Nearest Neighbor (más rápido pero peor calidad)

### Timeout 2-opt
- **1-5s**: Instancias pequeñas
- **10-15s**: Instancias medianas
- **30s+**: Instancias grandes

---

## ✅ Checklist de Exploración

- [ ] Ejecuta "Ejemplo Simple" - entiende los conceptos
- [ ] Activa/desactiva 2-opt - ve la mejora
- [ ] Prueba "Ejemplo Medio" con diferentes capacidades
- [ ] Genera 3 escenarios aleatorios - nota variabilidad
- [ ] Compara tiempos con/sin 2-opt
- [ ] Ajusta vehículos y observa impacto
- [ ] Exporta un gráfico (click cámara en Plotly)

---

## 🐛 Si algo no funciona

### "No se abre la aplicación"
```bash
# Instalar dependencias nuevamente
C:\Users\hanss\Desktop\LAR\gestion_rutas\venv\Scripts\pip.exe install streamlit plotly pandas

# Ejecutar
C:\Users\hanss\Desktop\LAR\gestion_rutas\venv\Scripts\python.exe -m streamlit run C:\Users\hanss\Desktop\LAR\app_visualizador_vrp.py
```

### "Dice 'No module named streamlit'"
- Asegúrate de usar el Python del venv
- Verifica que instalaste con `pip install streamlit`
- Usa la ruta completa: `C:\Users\hanss\Desktop\LAR\gestion_rutas\venv\Scripts\`

### "Los mapas no se ven"
- Recarga la página (F5)
- Verifica que Plotly está instalado: `pip install plotly`
- Cierra y reabre el navegador

### "Está muy lento"
- Baja el timeout de 2-opt
- Reduce el número de nodos
- Desactiva 2-opt temporalmente

---

## 📞 URLs Útiles

- **Streamlit app**: http://localhost:8501
- **API FastAPI** (separado): http://localhost:8000
- **Docs API**: http://localhost:8000/docs

---

## 📚 Documentación Relacionada

Para más detalles:
- `GUIA_VISUALIZADOR.md`: Guía completa y detallada
- `gestion_rutas/vrp/README.md`: Arquitectura técnica
- `gestion_rutas/vrp/OPTIMIZACION_2OPT.md`: Teoría de 2-opt
- `gestion_rutas/vrp/test_2opt.py`: Tests programáticos

---

## 🎯 Objetivo Didáctico

Esta visualización te permite:
1. ✅ **Ver** cómo funciona Nearest Neighbor
2. ✅ **Entender** cómo 2-opt mejora las rutas
3. ✅ **Experimentar** con diferentes parámetros
4. ✅ **Visualizar** en mapas interactivos
5. ✅ **Analizar** métricas en tiempo real

¡Ahora sí puedes explorar el planificador VRP de forma visual e interactiva! 🚀

---

**Tip**: Abre esta aplicación en una pantalla y la API en otra para comparar resultados en tiempo real.
