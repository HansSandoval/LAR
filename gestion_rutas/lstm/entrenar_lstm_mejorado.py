"""
Modelo LSTM Avanzado para predicción de residuos
Arquitectura mejorada con múltiples capas, regularización y callbacks
"""

import numpy as np
import pandas as pd
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout, BatchNormalization
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau, ModelCheckpoint
from tensorflow.keras.optimizers import Adam
from sklearn.model_selection import train_test_split
import json

print("=" * 80)
print("ENTRENAMIENTO DE MODELO LSTM AVANZADO")
print("=" * 80)

# CARGAR DATOS
print("\n1. Cargando datos preprocesados...")
X = np.load('X.npy', allow_pickle=True).astype(np.float32)
y = np.load('y.npy', allow_pickle=True).astype(np.float32)

print(f"   X shape: {X.shape}")
print(f"   y shape: {y.shape}")

# DIVIDIR EN ENTRENAMIENTO, VALIDACIÓN Y PRUEBA
print("\n2. Dividiendo datos (70% train, 15% validation, 15% test)...")
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.15, random_state=42, shuffle=True
)
X_train, X_val, y_train, y_val = train_test_split(
    X_train, y_train, test_size=0.176, random_state=42, shuffle=True
)

print(f"   Training:   X {X_train.shape}, y {y_train.shape}")
print(f"   Validation: X {X_val.shape}, y {y_val.shape}")
print(f"   Test:       X {X_test.shape}, y {y_test.shape}")

# CONSTRUIR MODELO LSTM MEJORADO
print("\n3. Construyendo modelo LSTM avanzado...")
model = Sequential([
    # Primera capa LSTM con 128 unidades
    LSTM(
        units=128,
        activation='relu',
        return_sequences=True,
        input_shape=(X.shape[1], X.shape[2])
    ),
    BatchNormalization(),
    Dropout(0.25),
    
    # Segunda capa LSTM con 64 unidades
    LSTM(
        units=64,
        activation='relu',
        return_sequences=True
    ),
    BatchNormalization(),
    Dropout(0.25),
    
    # Tercera capa LSTM con 32 unidades
    LSTM(
        units=32,
        activation='relu'
    ),
    BatchNormalization(),
    Dropout(0.2),
    
    # Capas Dense para interpretación
    Dense(32, activation='relu'),
    Dropout(0.15),
    
    Dense(16, activation='relu'),
    Dropout(0.1),
    
    # Output layer
    Dense(1, activation='sigmoid')  # sigmoid para salida entre 0-1
])

# Compilar modelo con optimizer personalizado
optimizer = Adam(learning_rate=0.001)
model.compile(
    optimizer=optimizer,
    loss='mse',
    metrics=['mae', 'mse']
)

print("   [OK] Modelo compilado")
print("\n   Resumen del modelo:")
model.summary()

# CALLBACKS
print("\n4. Configurando callbacks...")

# EarlyStopping: detener si no mejora (más paciente ahora)
early_stop = EarlyStopping(
    monitor='val_loss',
    patience=20,
    restore_best_weights=True,
    verbose=1
)

# ReduceLROnPlateau: reducir learning rate si no mejora
reduce_lr = ReduceLROnPlateau(
    monitor='val_loss',
    factor=0.5,
    patience=10,
    min_lr=0.000001,
    verbose=1
)

# ModelCheckpoint: guardar mejor modelo
checkpoint = ModelCheckpoint(
    'modelo_lstm_mejor.keras',
    monitor='val_loss',
    save_best_only=True,
    verbose=1
)

print("   [OK] Callbacks configurados")

# ENTRENAR MODELO
print("\n5. Entrenando modelo (esto puede tardar varios minutos)...")
print("   " + "-" * 76)

history = model.fit(
    X_train, y_train,
    validation_data=(X_val, y_val),
    epochs=150,
    batch_size=32,
    callbacks=[early_stop, reduce_lr, checkpoint],
    verbose=1
)

print("   " + "-" * 76)
print("   [OK] Entrenamiento completado")

# GUARDAR MODELO
print("\n6. Guardando modelo...")
model.save('modelo_lstm_residuos.keras')
print("   [OK] Modelo guardado como modelo_lstm_residuos.keras")

# EVALUAR EN SET DE PRUEBA
print("\n7. Evaluando en set de prueba...")
y_pred_train = model.predict(X_train, verbose=0)
y_pred_val = model.predict(X_val, verbose=0)
y_pred_test = model.predict(X_test, verbose=0)

from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

def calcular_metricas(y_true, y_pred, nombre):
    mse = mean_squared_error(y_true, y_pred)
    rmse = np.sqrt(mse)
    mae = mean_absolute_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)
    
    print(f"\n   {nombre}:")
    print(f"      MSE:  {mse:.6f}")
    print(f"      RMSE: {rmse:.6f}")
    print(f"      MAE:  {mae:.6f}")
    print(f"      R²:   {r2:.6f}")
    
    return {'mse': mse, 'rmse': rmse, 'mae': mae, 'r2': r2}

metricas_train = calcular_metricas(y_train, y_pred_train, "Training")
metricas_val = calcular_metricas(y_val, y_pred_val, "Validation")
metricas_test = calcular_metricas(y_test, y_pred_test, "Test")

# GUARDAR HISTORIAL Y MÉTRICAS
print("\n8. Guardando historial y métricas...")

historial = {
    'epochs': len(history.history['loss']),
    'train_loss': [float(x) for x in history.history['loss']],
    'val_loss': [float(x) for x in history.history['val_loss']],
    'train_mae': [float(x) for x in history.history['mae']],
    'val_mae': [float(x) for x in history.history['val_mae']],
    'metricas': {
        'train': metricas_train,
        'validation': metricas_val,
        'test': metricas_test
    }
}

with open('historial_entrenamiento.json', 'w') as f:
    json.dump(historial, f, indent=2)

print("   [OK] Historial guardado en historial_entrenamiento.json")

print("\n" + "=" * 80)
print("[OK] ENTRENAMIENTO COMPLETADO")
print("=" * 80)
print(f"\nMejor modelo guardado como: modelo_lstm_mejor.keras")
print(f"Próximo paso: ejecutar generar_lstm_mejorado.py")
