"""
Script de preprocesamiento mejorado para LSTM
Convierte datos del CSV en secuencias preparadas para el modelo
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler, LabelEncoder
import json
from datetime import datetime
import pickle

print("=" * 80)
print("PREPROCESAMIENTO MEJORADO PARA LSTM - SECTOR SUR IQUIQUE")
print("=" * 80)

# Cargar CSV con datos reales
print("\n1. Cargando datos...")
df = pd.read_csv('datos_residuos_iquique.csv')
print(f"   ✓ Cargados {len(df)} registros")
print(f"   Columnas: {list(df.columns)[:10]}...")

# Convertir fecha a datetime
df['fecha'] = pd.to_datetime(df['fecha'])

# Ordenar por punto de recolección y fecha (IMPORTANTE para secuencias)
df = df.sort_values(by=['punto_recoleccion', 'fecha']).reset_index(drop=True)
print(f"   ✓ Datos ordenados por ubicación y fecha")

# FEATURE ENGINEERING
print("\n2. Ingeniería de características...")

# Extraer características temporales
df['dia_mes'] = df['fecha'].dt.day
df['mes'] = df['fecha'].dt.month
df['semana_año'] = df['fecha'].dt.isocalendar().week
df['dia_semana_num'] = df['fecha'].dt.dayofweek

# Codificar variables categóricas
print("   Codificando variables categóricas...")
le_punto = LabelEncoder()
df['punto_encoded'] = le_punto.fit_transform(df['punto_recoleccion'])

le_clima = LabelEncoder()
df['clima_encoded'] = le_clima.fit_transform(df['clima'])

le_evento = LabelEncoder()
df['evento_encoded'] = le_evento.fit_transform(df['evento'])

le_combustible = LabelEncoder()
df['combustible_encoded'] = le_combustible.fit_transform(df['tipo_combustible'])

# Guardar los encoders para usar después
encoders = {
    'punto': le_punto,
    'clima': le_clima,
    'evento': le_evento,
    'combustible': le_combustible
}

with open('encoders.pkl', 'wb') as f:
    pickle.dump(encoders, f)

print("   ✓ Encoders guardados en encoders.pkl")

# Normalizar características numéricas
print("   Normalizando características...")
scaler_residuos = MinMaxScaler(feature_range=(0, 1))
df['residuos_scaled'] = scaler_residuos.fit_transform(df[['residuos_kg']])

scaler_capacidad = MinMaxScaler(feature_range=(0, 1))
df['capacidad_scaled'] = scaler_capacidad.fit_transform(df[['capacidad_kg']])

scaler_consumo = MinMaxScaler(feature_range=(0, 1))
df['consumo_scaled'] = scaler_consumo.fit_transform(df[['consumo_km_l']])

# Guardar scalers
scalers = {
    'residuos': scaler_residuos,
    'capacidad': scaler_capacidad,
    'consumo': scaler_consumo
}

with open('scalers.pkl', 'wb') as f:
    pickle.dump(scalers, f)

print("   ✓ Scalers guardados en scalers.pkl")

# CREAR SECUENCIAS TEMPORALES
print("\n3. Creando secuencias temporales...")

# Seleccionar features para el modelo
features_cols = [
    'punto_encoded',
    'residuos_scaled',
    'clima_encoded',
    'evento_encoded',
    'combustible_encoded',
    'dia_mes',
    'mes',
    'semana_año',
    'dia_semana_num',
    'capacidad_scaled',
    'consumo_scaled',
    'es_fin_semana'
]

data = df[features_cols + ['residuos_kg']].copy()

# Longitud de secuencia (usar 14 días anteriores para predecir siguiente día)
sequence_length = 14

def create_sequences(data, seq_length):
    """
    Crea secuencias de X y etiquetas y
    X: secuencias de 'sequence_length' días
    y: residuos del siguiente día
    """
    xs = []
    ys = []
    
    for i in range(len(data) - seq_length):
        # Secuencia de features (excluyendo residuos_kg que es el target)
        x = data.iloc[i:i + seq_length, :-1].values
        # Target: residuos del siguiente día (normalizado)
        y = data.iloc[i + seq_length, 1]  # residuos_scaled está en posición 1
        
        xs.append(x)
        ys.append(y)
    
    return np.array(xs), np.array(ys)

X, y = create_sequences(data, sequence_length)

print(f"   ✓ Secuencias creadas")
print(f"   X shape: {X.shape}  (muestras, timesteps, features)")
print(f"   y shape: {y.shape}  (muestras,)")
print(f"   Número de features: {X.shape[2]}")

# ELIMINAR OUTLIERS (opcional pero recomendado)
print("\n4. Limpiando outliers...")

# Usar IQR para detectar outliers
Q1 = np.percentile(y, 25)
Q3 = np.percentile(y, 75)
IQR = Q3 - Q1
lower_bound = Q1 - 1.5 * IQR
upper_bound = Q3 + 1.5 * IQR

mask = (y >= lower_bound) & (y <= upper_bound)
X_clean = X[mask]
y_clean = y[mask]

outliers_removed = len(y) - len(y_clean)
print(f"   ✓ {outliers_removed} outliers removidos")
print(f"   Datos después de limpieza: {len(y_clean)} muestras")

# GUARDAR DATOS
print("\n5. Guardando datos preprocesados...")
np.save('X.npy', X_clean)
np.save('y.npy', y_clean)

# Guardar información para referencia
info = {
    'timestamp': datetime.now().isoformat(),
    'total_registros': len(df),
    'total_secuencias': len(X_clean),
    'sequence_length': sequence_length,
    'num_features': X.shape[2],
    'features': features_cols,
    'X_shape': X_clean.shape,
    'y_shape': y_clean.shape,
    'y_min': float(y_clean.min()),
    'y_max': float(y_clean.max()),
    'y_mean': float(y_clean.mean()),
    'y_std': float(y_clean.std()),
}

with open('preprocessing_info.json', 'w') as f:
    json.dump(info, f, indent=2)

print(f"   ✓ X.npy guardado - shape: {X_clean.shape}")
print(f"   ✓ y.npy guardado - shape: {y_clean.shape}")
print(f"   ✓ preprocessing_info.json guardado")

print("\n" + "=" * 80)
print("✓ PREPROCESAMIENTO COMPLETADO EXITOSAMENTE")
print("=" * 80)
print(f"\nEstadísticas del target (y):")
print(f"  Min: {y_clean.min():.4f}")
print(f"  Max: {y_clean.max():.4f}")
print(f"  Mean: {y_clean.mean():.4f}")
print(f"  Std: {y_clean.std():.4f}")
print(f"\nPróximo paso: ejecutar entrenar_lstm_mejorado.py")