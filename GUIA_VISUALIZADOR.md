# 🚀 Guía de Uso: Visualizador VRP

## Inicio Rápido

### 1. Ejecutar la aplicación

```bash
cd c:\Users\hanss\Desktop\LAR

# Opción A: Con conda/venv activado
streamlit run app_visualizador_vrp.py

# Opción B: Con Python directo (Windows)
C:\Users\hanss\Desktop\LAR\gestion_rutas\venv\Scripts\python.exe -m streamlit run app_visualizador_vrp.py
```

La aplicación se abrirá automáticamente en http://localhost:8501

### 2. Interfaz Principal

#### Barra Lateral (Izquierda)

**Sección 1: Seleccionar Escenario**
- `Ejemplo Simple (5 puntos)`: Ideal para entender el concepto
- `Ejemplo Medio (9 puntos)`: Caso realista
- `Ejemplo Complejo (15 puntos)`: Desafío mayor
- `Personalizado`: Crear tu propio escenario

**Sección 2: Parámetros**
- **Capacidad por vehículo**: Cantidad máxima de kg que puede llevar cada vehículo
- **Número de vehículos**: Cantidad de camiones disponibles
- **Aplicar 2-opt**: Checkbox para habilitar/deshabilitar optimización local
- **Timeout 2-opt**: Límite de tiempo para la búsqueda local (segundos)

#### Pantalla Principal (Centro/Derecha)

**Sección 1: Métricas**
- Total de nodos/puntos de recolección
- Vehículos disponibles
- Capacidad total del sistema
- Demanda total a recopilar

**Sección 2: Comparativa NN vs 2-opt**
- Distancia obtenida con NN puro
- Distancia después de 2-opt (optimizada)
- Mejora en km y porcentaje

**Sección 3: Mapas Visuales**
- Mapa izquierdo: Solución de Nearest Neighbor
- Mapa derecho: Solución optimizada con 2-opt
  - Cada ruta en color diferente
  - Depósito: Estrella roja
  - Puntos: Círculos azules
  - Líneas: Trayectos de los vehículos

**Sección 4: Tablas Detalladas**
- Tabla NN: Secuencia, distancia y demanda por ruta
- Tabla Optimizada: Lo mismo pero después de 2-opt

**Sección 5: Gráfico de Barras**
- Comparativa visual de distancias por ruta
- Azul: NN | Verde: NN+2-opt

**Sección 6: Indicadores Clave**
- Distancia total NN
- Distancia total optimizada
- Ahorro absoluto y porcentual
- Número de rutas utilizadas

---

## 📊 Ejemplos de Uso

### Caso 1: Entender el concepto (Simple)

1. Selecciona: **"Ejemplo Simple (5 puntos)"**
2. Parámetros: 2 vehículos, capacidad 20 kg
3. Habilita 2-opt
4. Observa:
   - Cómo NN construye una solución inicial rápidamente
   - Cómo 2-opt la mejora intercambiando aristas
   - Típicamente 5-10% de mejora

### Caso 2: Analizar rendimiento (Medio)

1. Selecciona: **"Ejemplo Medio (9 puntos)"**
2. Experimenta con:
   - Diferentes número de vehículos (1, 2, 3)
   - Diferentes capacidades (10, 20, 30 kg)
3. Compara:
   - Cómo más vehículos reduce distancia total
   - Cómo menos capacidad requiere más rutas

### Caso 3: Desafío máximo (Complejo)

1. Selecciona: **"Ejemplo Complejo (15 puntos)"**
2. Habilita 2-opt
3. Observa: Cómo 2-opt mejora una instancia mayor (puede tomar 1-2 segundos)

### Caso 4: Personalizado

1. Selecciona: **"Personalizado"**
2. Ajusta:
   - Número de puntos (3-20)
   - Capacidad por vehículo
   - Número de vehículos
3. Click en **"🔀 Generar aleatorio"**
4. Experimenta múltiples veces para ver diferentes instancias

---

## 🎨 Interpretación de Visualizaciones

### Mapa de Rutas

```
★ = Depósito (punto de salida/retorno)
● = Puntos de recolección (azules)
─ = Trayecto de un vehículo (colores diferentes por ruta)
```

**Lectura:**
- Cada línea de color es una ruta que sigue un vehículo
- Comienza en ★ (depósito), visita ● (puntos), retorna a ★
- Líneas que se cruzan = posible mejora con 2-opt
- Líneas sin cruces = probablemente óptima localmente

### Tabla de Rutas

```
┌─────────────────────────────────────────────────┐
│ Vehículo 1: D → P1 → P3 → P2 → D               │
│ Distancia: 45.2 km                              │
│ Demanda: 12 kg (respeta límite de 20 kg)        │
└─────────────────────────────────────────────────┘
```

### Gráfico de Barras

```
     Distancia (km)
     ▲
  45 │ ┌─────┐
  40 │ │ NN  │ ┌────────┐
  35 │ │     │ │NN+2opt │
  30 │ └─────┘ └────────┘
     └──────────────────────→ Rutas
     
Compara visualmente:
- Barras azules más altas = más oportunidad de mejora con 2-opt
- Barras verdes más bajas = mejora aplicada
```

---

## 🔧 Parámetros Avanzados

### ¿Cuándo aumentar el timeout?

- **Instancias pequeñas (<20 nodos)**: 1-5 segundos es suficiente
- **Instancias medianas (20-100 nodos)**: 5-15 segundos
- **Instancias grandes (>100 nodos)**: 15-60 segundos

### ¿Cuándo deshabilitar 2-opt?

- Para ver la velocidad de NN puro
- Para comparar tiempos
- Para entender línea base
- **Recomendación**: Siempre mantener habilitado en producción

### Efectos de Capacidad

| Capacidad | Efecto | Ejemplo |
|-----------|--------|---------|
| Baja (5 kg) | Más rutas necesarias | 4-5 vehículos para 20 kg total |
| Media (20 kg) | Balance óptimo | 2-3 vehículos típicamente |
| Alta (50 kg) | Pocas rutas | 1-2 vehículos pueden hacerlo |

---

## 📈 Qué Esperar

### Métrica de Mejora (2-opt)

| Tipo de Instancia | Mejora Típica |
|-------------------|---------------|
| Muy pequeña (3-5) | 0-5% |
| Pequeña (5-10) | 5-15% |
| Mediana (10-50) | 3-10% |
| Grande (50+) | 1-5% |

**Nota**: Mejora depende de qué tan buena sea la solución inicial de NN.

---

## 🐛 Solución de Problemas

### App no abre

```bash
# Reinstalar Streamlit
pip install streamlit --upgrade

# Ejecutar con logs
streamlit run app_visualizador_vrp.py --logger.level=debug
```

### Los mapas no se ven

- Asegúrate de tener Plotly instalado: `pip install plotly`
- Recarga la página: F5 o Cmd+R

### Timeout de 2-opt muy largo

- Baja el slider a 5-10 segundos
- Desactiva 2-opt momentáneamente
- Reduce número de nodos

---

## 💡 Experimentos Sugeridos

### Experimento 1: Impacto de la capacidad
1. Fija: Simple, 2-opt ON, 2 vehículos
2. Varía: Capacidad de 10 → 20 → 30 kg
3. Observa: Cómo la distancia cambia

### Experimento 2: Impacto del 2-opt
1. Fija: Medio, 2 vehículos, 20 kg
2. Ejecuta con 2-opt ON
3. Ejecuta con 2-opt OFF
4. Compara: Tiempos y distancias

### Experimento 3: Escalabilidad
1. Personalizado: Genera 5, 10, 15 nodos
2. Observa: Cómo crece el tiempo de cálculo
3. Nota: O(n²) para NN, O(n² × iter) para 2-opt

### Experimento 4: Aleatoriedad
1. Personalizado: 10 nodos
2. Genera 5 instancias aleatorias distintas
3. Compara: Variabilidad de mejoras

---

## 🔗 Integración con API

Puedes usar el visualizador **simultáneamente** con la API:

```bash
# Terminal 1: Visualizador
streamlit run app_visualizador_vrp.py

# Terminal 2: API FastAPI
python -m uvicorn main:app --reload --port 8000
```

Ambos usan los mismos módulos VRP, así que verás resultados idénticos.

---

## 📞 Documentación Relacionada

- `vrp/README.md`: Arquitectura completa
- `vrp/OPTIMIZACION_2OPT.md`: Teoría de 2-opt
- `vrp/API_INTEGRATION.md`: Uso vía API
- `test_2opt.py`: Tests programáticos

---

## ✨ Tips y Trucos

- **Realtime feedback**: Los cambios en la barra lateral se reflejan instantáneamente
- **Exportar datos**: Puedes copiar/pegar tablas en Excel
- **Pantalla completa**: F11 en el navegador para mejor visualización
- **Zoom en mapas**: Usa rueda del ratón en los gráficos Plotly
- **Descargar gráficos**: Click en el icono de cámara en Plotly

---

¡Disfruta explorando el planificador VRP de forma interactiva! 🚀
