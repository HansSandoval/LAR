# 🧠 LSTM - Predicción de Demanda de Residuos

## 📋 Descripción Rápida

Modelo LSTM para predicción de demanda de residuos en Sector Sur Iquique.

**Desempeño:** R² = 0.6458 (64.58% de precisión)

---

## 📁 Archivos

### Scripts Ejecutables (en orden)
1. **`generar_csv_final.py`** - Genera `datos_residuos_iquique.csv`
2. **`preprocesamiento_mejorado.py`** - Crea `X.npy` y `y.npy`
3. **`entrenar_lstm_mejorado.py`** - Entrena modelo → `modelo_lstm_mejor.keras`
4. **`generar_lstm_mejorado.py`** - Genera predicciones

### Datos
- `datos_residuos_iquique.csv` - 20,250 registros de residuos
- `X.npy` - Features (14 timesteps × 11 features)
- `y.npy` - Targets (demanda real)
- `scalers.pkl` - Normalizadores

### Modelo
- `modelo_lstm_mejor.keras` - Modelo entrenado (1.67 GB)

### Resultados
- `predicciones_lstm.csv` - Predicciones vs reales
- `predicciones_visualizacion.png` - Gráfico de desempeño
- `reporte_predicciones.json` - Métricas detalladas

---

## 🚀 Uso Rápido

```bash
# 1. Generar datos
python generar_csv_final.py

# 2. Preprocesar
python preprocesamiento_mejorado.py

# 3. Entrenar modelo
python entrenar_lstm_mejorado.py

# 4. Generar predicciones
python generar_lstm_mejorado.py
```

---

## 📊 Métricas Finales

| Métrica | Valor |
|---------|-------|
| R² (Test) | 0.6458 |
| RMSE | 0.1001 |
| MAE | 0.0627 |
| Muestras | 20,086 |

---

## 💾 Requisitos Python

```
tensorflow>=2.13
keras>=2.13
numpy
pandas
scikit-learn
matplotlib
```

---

## 📌 Notas

- Datos realistas para Iquique (pasajes bajos, clima árido)
- 675 intersecciones × 30 días = base de datos
- Lookback: 14 días para predicciones
- Modelo completo: 136K parámetros

---

**Última actualización:** 22 de Octubre 2025
