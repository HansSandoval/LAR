import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error

# Cargar datos preprocesados desde archivo npy
X = np.load('X.npy')
y = np.load('y.npy')

# Dividir en 80% entrenamiento y 20% prueba
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, shuffle=True
)

print('Datos de entrenamiento:', X_train.shape, y_train.shape)
print('Datos de prueba:', X_test.shape, y_test.shape)

# Definir modelo LSTM sencillo
model = Sequential()
model.add(LSTM(units=50, activation='relu', input_shape=(X.shape[1], X.shape[2])))
model.add(Dense(1))

model.compile(optimizer='adam', loss='mse')

# Entrenar el modelo solo con datos de entrenamiento
model.fit(X_train, y_train, epochs=20, batch_size=32)

# Evaluar el modelo con los datos de prueba
y_pred = model.predict(X_test)
mse = mean_squared_error(y_test, y_pred)
print(f'Error cuadrático medio en test: {mse:.4f}')

# Guardar modelo entrenado
model.save('modelo_lstm_residuos.keras')

