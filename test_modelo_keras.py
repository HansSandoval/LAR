import tensorflow as tf
from pathlib import Path

print("TensorFlow version:", tf.__version__)

# Probar cargar modelo
modelo_path = Path("gestion_rutas/lstm/lstm_temp/modelo.keras")
print(f"\nIntentando cargar: {modelo_path}")
print(f"Archivo existe: {modelo_path.exists()}")

if modelo_path.exists():
    try:
        modelo = tf.keras.models.load_model(str(modelo_path))
        print(f"✅ Modelo cargado exitosamente!")
        print(f"\nArquitectura:")
        modelo.summary()
        
        # Probar predicción
        import numpy as np
        test_input = np.random.random((1, 3, 1))
        pred = modelo.predict(test_input, verbose=0)
        print(f"\n✅ Predicción de prueba: {pred[0][0]:.2f}")
        
    except Exception as e:
        print(f"❌ Error al cargar modelo: {e}")
        print(f"\nTipo de error: {type(e).__name__}")
else:
    print("❌ Archivo no encontrado")
