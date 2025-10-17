import sys
print("Python path:", sys.path[:3])

try:
    print("Importando vrp...")
    from vrp import VRPInput, VRPOutput, planificar_vrp_api
    print("✅ VRP importado")
except ImportError as e:
    print(f"❌ Error importando VRP: {e}")
    sys.exit(1)

try:
    print("Importando FastAPI...")
    from fastapi import FastAPI
    print("✅ FastAPI importado")
except ImportError as e:
    print(f"❌ Error importando FastAPI: {e}")
    sys.exit(1)

try:
    print("Importando main...")
    from main import app
    print("✅ main importado")
except Exception as e:
    print(f"❌ Error importando main: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n✅ Todas las importaciones funcionan!")
