from gestion_rutas.service.usuario_service import UsuarioService
import logging
import time
import traceback

# Configurar logging para ver errores de DB si los hay
logging.basicConfig(level=logging.INFO)

def test_crear_usuario():
    try:
        print("--- Iniciando prueba de creación de usuario ---")
        service = UsuarioService()
        
        # Usar un correo único
        correo = f"test_{int(time.time())}@example.com"
        print(f"Intentando registrar: {correo}")
        
        user = service.crear_usuario(
            nombre="Test User",
            correo=correo,
            rol="cliente",
            password="password123",
            activo=True
        )
        
        if user:
            print(" Usuario creado exitosamente:")
            print(user)
        else:
            print(" Falló la creación del usuario (retornó None/Empty)")
            
    except Exception as e:
        print("\n EXCEPCIÓN CAPTURADA:")
        print(str(e))
        print("\nTraceback completo:")
        traceback.print_exc()

if __name__ == "__main__":
    test_crear_usuario()
