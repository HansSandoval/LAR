"""
Script para inicializar la base de datos sin conflictos con uvicorn
"""

import os
import sys

# Cambiar a directorio del proyecto
os.chdir(r'c:\Users\hanss\Desktop\LAR')
sys.path.insert(0, r'c:\Users\hanss\Desktop\LAR')

print("=" * 60)
print("INICIALIZANDO BASE DE DATOS")
print("=" * 60)

try:
    # Importar después de establecer el path
    from gestion_rutas.database.db import init_db, engine
    from gestion_rutas.models.base import Base
    
    print("\n✅ Importes completados")
    print("\n🔧 Creando todas las tablas...")
    
    # Crear todas las tablas
    Base.metadata.create_all(bind=engine)
    
    print("✅ Base de datos inicializada correctamente!")
    print("\n📋 Tablas creadas:")
    
    # Mostrar tablas creadas
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tablas = inspector.get_table_names()
    
    if tablas:
        for tabla in tablas:
            print(f"   ✓ {tabla}")
        print(f"\n✅ Total de tablas: {len(tablas)}")
    else:
        print("   ⚠️ No se encontraron tablas")
    
except Exception as e:
    print(f"\n❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("INICIALIZACIÓN COMPLETADA")
print("=" * 60)
