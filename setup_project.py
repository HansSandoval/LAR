import os
import sys
import subprocess
import shutil
from pathlib import Path

def print_step(step, message):
    print(f"\n[{step}] {message}")

def check_python_version():
    print_step(1, "Verificando versión de Python...")
    if sys.version_info < (3, 9):
        print(" Error: Se requiere Python 3.9 o superior.")
        sys.exit(1)
    print(f" Python {sys.version_info.major}.{sys.version_info.minor} detectado.")

def create_venv():
    print_step(2, "Creando entorno virtual (.venv)...")
    if os.path.exists(".venv"):
        print(" El entorno virtual ya existe.")
    else:
        subprocess.check_call([sys.executable, "-m", "venv", ".venv"])
        print(" Entorno virtual creado exitosamente.")

def install_dependencies():
    print_step(3, "Instalando dependencias...")
    pip_cmd = os.path.join(".venv", "Scripts", "pip") if os.name == 'nt' else os.path.join(".venv", "bin", "pip")
    
    if not os.path.exists("requirements.txt"):
        print(" Error: No se encontró requirements.txt")
        return

    try:
        subprocess.check_call([pip_cmd, "install", "-r", "requirements.txt"])
        print(" Dependencias instaladas.")
    except subprocess.CalledProcessError:
        print(" Error instalando dependencias.")

def setup_env_file():
    print_step(4, "Configurando archivo .env...")
    if not os.path.exists(".env"):
        print(" Creando archivo .env con configuración por defecto...")
        with open(".env", "w") as f:
            f.write("DB_USER=postgres\n")
            f.write("DB_PASSWORD=admin\n")
            f.write("DB_HOST=localhost\n")
            f.write("DB_PORT=5432\n")
            f.write("DB_NAME=gestion_rutas\n")
        print(" Archivo .env creado. Por favor edítalo con tus credenciales reales.")
    else:
        print(" Archivo .env ya existe.")

def init_database():
    print_step(5, "Inicializando Base de Datos...")
    python_cmd = os.path.join(".venv", "Scripts", "python") if os.name == 'nt' else os.path.join(".venv", "bin", "python")
    
    response = input("¿Deseas inicializar la base de datos ahora? (s/n): ").lower()
    if response == 's':
        try:
            # Ejecutar el script init_db.py dentro del módulo gestion_rutas
            # Necesitamos establecer PYTHONPATH para que encuentre el módulo
            env = os.environ.copy()
            env["PYTHONPATH"] = os.getcwd()
            
            subprocess.check_call([python_cmd, "gestion_rutas/init_db.py"], env=env)
            print(" Base de datos inicializada.")
        except subprocess.CalledProcessError as e:
            print(f" Error inicializando base de datos: {e}")
            print(" Asegúrate de que PostgreSQL esté corriendo y las credenciales en .env sean correctas.")

def main():
    print("="*50)
    print(" ASISTENTE DE INSTALACIÓN - PROYECTO LAR")
    print("="*50)
    
    check_python_version()
    create_venv()
    install_dependencies()
    setup_env_file()
    init_database()
    
    print("\n" + "="*50)
    print(" INSTALACIÓN COMPLETADA")
    print("="*50)
    print("\nPara ejecutar el servidor:")
    print("  1. Activa el entorno: .venv\\Scripts\\activate")
    print("  2. Ejecuta: python run_server.py")
    print("\nPara ejecutar el visualizador:")
    print("  1. Ejecuta: streamlit run app_visualizador_vrp.py")

if __name__ == "__main__":
    main()
