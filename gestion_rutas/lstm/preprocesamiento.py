import pandas as pd
from sklearn.preprocessing import LabelEncoder, MinMaxScaler
import numpy as np

# Cargar CSV
df = pd.read_csv('datos_residuos_iquique.csv')

# Convertir columna Fecha a tipo datetime
df['Fecha'] = pd.to_datetime(df['Fecha'])

# Ordenar por Calle y Fecha (importante para secuencias temporales)
df = df.sort_values(by=['Calle', 'Fecha'])

# Codificar variables categóricas con LabelEncoder
le_calle = LabelEncoder()
df['Calle_encoded'] = le_calle.fit_transform(df['Calle'])

le_clima = LabelEncoder()
df['Clima_encoded'] = le_clima.fit_transform(df['Clima'])

le_evento = LabelEncoder()
df['Evento_encoded'] = le_evento.fit_transform(df['Evento'])

# Normalizar variable residuos usando MinMaxScaler entre 0 y 1
scaler = MinMaxScaler()
df['Residuos_scaled'] = scaler.fit_transform(df[['Residuos (kg)']])

# Seleccionamos las columnas para el modelo
data = df[['Calle_encoded', 'Fecha', 'Residuos_scaled', 'Personal', 'Clima_encoded', 'Evento_encoded']]

# Para LSTM la secuencia temporal puede ser semanal, por ejemplo:
# Crear secuencias de 7 días para predecir el siguiente día

sequence_length = 7

def create_sequences(data, seq_length):
    xs = []
    ys = []
    for i in range(len(data) - seq_length):
        x = data.iloc[i:(i + seq_length)].drop(columns=['Fecha']).values
        y = data.iloc[i + seq_length]['Residuos_scaled']
        xs.append(x)
        ys.append(y)
    return np.array(xs), np.array(ys)

X, y = create_sequences(data, sequence_length)

print('Shape de X:', X.shape)  # (ejemplos, días de secuencia, features)
print('Shape de y:', y.shape)  # (ejemplos,)

np.save('X.npy', X)
np.save('y.npy', y)

