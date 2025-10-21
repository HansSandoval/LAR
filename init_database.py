"""
Script para inicializar la base de datos
Crea todas las tablas necesarias
"""

import sys
sys.path.insert(0, '/c/Users/hanss/Desktop/LAR')

from gestion_rutas.database.db import init_db, engine
from gestion_rutas.models.base import Base

print("=" * 60)
print("INICIALIZANDO BASE DE DATOS")
print("=" * 60)

try:
    print("\n🔧 Creando todas las tablas...")
    init_db()
    print("✅ Base de datos inicializada correctamente!")
    print("\n📋 Tablas creadas:")
    
    # Mostrar tablas creadas
    inspector = __import__('sqlalchemy').inspect(engine)
    tablas = inspector.get_table_names()
    for tabla in tablas:
        print(f"   - {tabla}")
    
    print(f"\n✅ Total de tablas: {len(tablas)}")
    
except Exception as e:
    print(f"\n❌ Error al inicializar: {str(e)}")
    sys.exit(1)
