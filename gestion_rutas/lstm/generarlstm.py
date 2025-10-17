import numpy as np
import pandas as pd
from tensorflow.keras.models import load_model
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import matplotlib.pyplot as plt

# Cargar datos
X = np.load('X.npy')
y = np.load('y.npy')

# Dividir en entrenamiento y prueba (igual que antes)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, shuffle=True
)

# Cargar modelo entrenado
model = load_model('modelo_lstm_residuos.keras')

# Hacer predicciones en el set de prueba
y_pred = model.predict(X_test)

# Guardar resultados en un CSV
resultados = pd.DataFrame({
    'Real': y_test.flatten(),
    'Predicho': y_pred.flatten()
})
resultados.to_csv('predicciones_lstm.csv', index=False)

# Graficar los primeros 100 resultados
plt.figure(figsize=(10,5))
plt.plot(resultados['Real'][:100], label='Real')
plt.plot(resultados['Predicho'][:100], label='Predicho')
plt.legend()
plt.title('Comparación de residuos reales vs. predichos (primeros 100)')
plt.xlabel('Ejemplo')
plt.ylabel('Residuos (normalizado)')
plt.show()
