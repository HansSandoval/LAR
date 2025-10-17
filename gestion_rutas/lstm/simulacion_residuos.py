import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

# Calles reales de Iquique
calles = [
    'Padre Hurtado',
    'Av. Arturo Prat Chacón',
    'Av. La Tirana',
    'Tamarugal',
    'C. Uno',
    'Pje. Dos',
    'Manuel Balmaceda',
    'Los Chunchos',
    'Francisco Bilbao',
    'Ontario',
    'Via Local Dos',
    'Toronto',
    'C. Seis',
    'Teresa Wilms Mont',
    'Pje. C',
    'Pje. B',
    'Pje. A',
    'Av. Cinco',
    'C. Seis',
    'Costanera',
    'Playa Ancha',
    'Pje. Uno',
    'Pje. Tres',
    'Pje. Siete',
    'Dr. Amador Negme',
    'Dr. Juan Noe',
    'Pje. Cinco',
    'Pje. Seis',
    'Pje. Siete',
    'Pje. Ocho',
    'Nueva Cuatro',
    'Playa El Saladero',
    'Ines Solari Magnaso',
    'Playa Quintero',
    'Pje. Playa Chauca',
    'Playa Las Pizarras',
    'Los Alagarrobos',
    'La Chamiza',
    'Nueva Cuatro',
    'Lebu',
    'Pje. Traiguen',
    'Pje. Temuco',
    'Cerro Colorado',
    'C. Int Dos',
    'C. Int Tres',
    'C. Int Cuatro',
    'Cerro Casiri',
    'Coscaya',
    'Sauna',
    'Ontario',
    'Patara',
    'Cerro Yabricoya',
    'Chiza',
    'Chauca',
    'Calaunsa',
    'Napa',
    'Humberto Lizardi Flores',
    'Los Mineros',
    'Fanerita',
    'Calcopirita',
    'Crisocola',
    'Fanerita',
    'Sulfuros',
    'Cuarzo',
    'Filones',
    'Pje. Granodiorita',
    'Azurita',
    'Pirita',
    'Feldespato',
    'Apilita',
    'Matendisita',
    'Malaquita',
    'Cinco Sur',
    'Tres Marias',
    'Avenida Proyectada',
    'Avenida Dos Oriente',
    'Mar Tirreno',
    'Mar Mediterráneo',
    'Mar Caspio',
    'Mar Adriático',
    'Mar Egeo',
    'Mar Del Nte.',
    'Av. Reina Mar',
    'Jardines Del Desierto',
]

# Fechas: 30 días desde el 1 de septiembre de 2025
fecha_inicio = datetime(2025, 9, 1)
fechas = [fecha_inicio + timedelta(days=i) for i in range(30)]

# Opciones para clima y eventos
climas = ['soleado', 'nublado']
eventos = ['ninguno', 'feria', 'festivo']

# Simulación de datos
registros = []
for calle in calles:
    for fecha in fechas:
        residuos = np.random.randint(80, 200)  # kg
        personal = np.random.randint(2, 5)     # personas
        clima = random.choice(climas)
        evento = random.choices(eventos, weights=[0.7, 0.2, 0.1])[0]
        registros.append({
            'Calle': calle,
            'Fecha': fecha.strftime('%Y-%m-%d'),
            'Residuos (kg)': residuos,
            'Personal': personal,
            'Clima': clima,
            'Evento': evento
        })

# Crear DataFrame
df = pd.DataFrame(registros)

# Mostrar las primeras filas
print(df.head())

# Guardar a CSV si lo necesitas
df.to_csv('datos_residuos_iquique.csv', index=False)

