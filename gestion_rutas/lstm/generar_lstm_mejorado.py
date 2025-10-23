"""
Script mejorado para generar predicciones y visualizaciones
Analiza el desempeño del modelo y genera reportes detallados
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Backend no interactivo
from tensorflow.keras.models import load_model
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import json
from datetime import datetime

print("=" * 80)
print("GENERACIÓN DE PREDICCIONES Y ANÁLISIS")
print("=" * 80)

# CARGAR DATOS Y MODELO
print("\n1. Cargando datos y modelo...")
X = np.load('X.npy', allow_pickle=True).astype(np.float32)
y = np.load('y.npy', allow_pickle=True).astype(np.float32)

# Dividir datos igual que en entrenamiento
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.15, random_state=42, shuffle=True
)
X_train, X_val, y_train, y_val = train_test_split(
    X_train, y_train, test_size=0.176, random_state=42, shuffle=True
)

# Cargar mejor modelo
model = load_model('modelo_lstm_mejor.keras')
print("   ✓ Modelo cargado")

# HACER PREDICCIONES
print("\n2. Haciendo predicciones...")
y_pred_train = model.predict(X_train, verbose=0).flatten()
y_pred_val = model.predict(X_val, verbose=0).flatten()
y_pred_test = model.predict(X_test, verbose=0).flatten()

print("   ✓ Predicciones generadas")

# GUARDAR RESULTADOS EN CSV
print("\n3. Guardando resultados...")

resultados = pd.DataFrame({
    'Real': np.concatenate([y_train, y_val, y_test]),
    'Predicho': np.concatenate([y_pred_train, y_pred_val, y_pred_test]),
    'Conjunto': ['Train']*len(y_train) + ['Validation']*len(y_val) + ['Test']*len(y_test)
})

resultados['Error'] = resultados['Real'] - resultados['Predicho']
resultados['Error_Porcentaje'] = (np.abs(resultados['Error']) / resultados['Real'] * 100)

resultados.to_csv('predicciones_lstm.csv', index=False)
print("   ✓ Resultados guardados en predicciones_lstm.csv")

# CALCULAR MÉTRICAS DETALLADAS
print("\n4. Calculando métricas...")

def calcular_metricas_detalladas(y_true, y_pred, nombre):
    mse = mean_squared_error(y_true, y_pred)
    rmse = np.sqrt(mse)
    mae = mean_absolute_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)
    mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100
    
    print(f"\n   {nombre}:")
    print(f"      MSE:  {mse:.6f}")
    print(f"      RMSE: {rmse:.6f}")
    print(f"      MAE:  {mae:.6f}")
    print(f"      R²:   {r2:.6f}")
    print(f"      MAPE: {mape:.2f}%")
    
    return {
        'mse': float(mse),
        'rmse': float(rmse),
        'mae': float(mae),
        'r2': float(r2),
        'mape': float(mape)
    }

print("\n   Métricas por conjunto:")
metricas_train = calcular_metricas_detalladas(y_train, y_pred_train, "Training")
metricas_val = calcular_metricas_detalladas(y_val, y_pred_val, "Validation")
metricas_test = calcular_metricas_detalladas(y_test, y_pred_test, "Test")

# GENERAR VISUALIZACIONES
print("\n5. Generando gráficos...")

# GRÁFICO ÚNICO: Predicciones vs Demanda Real
fig, ax = plt.subplots(figsize=(14, 6))

# Mostrar primeras 100 muestras del conjunto de test
x_range = np.arange(min(100, len(y_test)))

# Plotear demanda real y predicha
ax.plot(x_range, y_test[:100], 'o-', label='Demanda Real', 
        linewidth=2.5, markersize=5, alpha=0.8, color='#2E86AB', markerfacecolor='#2E86AB')
ax.plot(x_range, y_pred_test[:100], 's-', label='Demanda Predicha', 
        linewidth=2.5, markersize=5, alpha=0.8, color='#A23B72', markerfacecolor='#A23B72')

# Etiquetas y título claros
ax.set_title('Predicción vs Demanda Real de Residuos', 
             fontsize=14, fontweight='bold', pad=20)
ax.set_xlabel('Predicción # (1 a 100)', fontsize=12, fontweight='bold')
ax.set_ylabel('Kilogramos de Residuos', fontsize=12, fontweight='bold')

# Leyenda clara
ax.legend(fontsize=11, loc='best', framealpha=0.95, shadow=True)

# Grid para mejor lectura
ax.grid(True, alpha=0.3, linestyle='--')

# Anotación con R² del modelo en la esquina superior derecha
textstr = f'R² (Test) = {metricas_test["r2"]:.4f}\nRMSE = {metricas_test["rmse"]:.4f}'
ax.text(0.98, 0.97, textstr, transform=ax.transAxes, fontsize=11,
        verticalalignment='top', horizontalalignment='right',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

plt.tight_layout()
plt.savefig('predicciones_visualizacion.png', dpi=300, bbox_inches='tight')
print("   ✓ Gráfico guardado en predicciones_visualizacion.png")
plt.close()

# Calcular errores para el reporte
errores_test = y_test - y_pred_test

# GENERAR REPORTE JSON
print("\n6. Generando reporte...")

reporte = {
    'timestamp': datetime.now().isoformat(),
    'modelo': 'LSTM Avanzado 3 capas',
    'datos': {
        'total_muestras': len(y),
        'train_size': len(y_train),
        'val_size': len(y_val),
        'test_size': len(y_test),
        'sequence_length': int(X.shape[1]),
        'num_features': int(X.shape[2])
    },
    'metricas': {
        'training': metricas_train,
        'validation': metricas_val,
        'test': metricas_test
    },
    'estadisticas_error_test': {
        'media': float(np.mean(errores_test)),
        'std': float(np.std(errores_test)),
        'min': float(np.min(errores_test)),
        'max': float(np.max(errores_test))
    }
}

with open('reporte_predicciones.json', 'w') as f:
    json.dump(reporte, f, indent=2)

print("   ✓ Reporte guardado en reporte_predicciones.json")

# RESUMEN FINAL
print("\n" + "=" * 80)
print("✓ GENERACIÓN DE PREDICCIONES COMPLETADA")
print("=" * 80)
print(f"\nArchivos generados:")
print(f"  • predicciones_lstm.csv - Resultados detallados")
print(f"  • predicciones_visualizacion.png - Gráficos de análisis")
print(f"  • reporte_predicciones.json - Métricas completas")

print(f"\nMejor desempeño en SET DE TEST:")
print(f"  R²: {metricas_test['r2']:.6f}")
print(f"  RMSE: {metricas_test['rmse']:.6f}")
print(f"  MAE: {metricas_test['mae']:.6f}")
print(f"  MAPE: {metricas_test['mape']:.2f}%")

if metricas_test['r2'] > 0.7:
    print(f"\n✓ El modelo tiene buen desempeño predictivo (R² > 0.7)")
elif metricas_test['r2'] > 0.5:
    print(f"\n⚠ El modelo tiene desempeño moderado (R² > 0.5)")
else:
    print(f"\n✗ El modelo necesita mejora (R² < 0.5)")
