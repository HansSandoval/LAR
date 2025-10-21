#!/usr/bin/env python3
"""Script para arreglar todas las importaciones absolutas a relativas"""

import os
import re
from pathlib import Path

def fix_imports_in_file(filepath):
    """Arregla importaciones en un archivo"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    
    # Arreglar importaciones absolutas a relativas
    replacements = [
        (r'from database\.db', 'from ..database.db'),
        (r'from models\.models', 'from ..models.models'),
        (r'from models\.base', 'from ..models.base'),
        (r'from schemas\.schemas', 'from ..schemas.schemas'),
        (r'from schemas\.', 'from ..schemas.'),
        (r'from service\..+import', lambda m: m.group(0).replace('from service.', 'from ..service.')),
        (r'from service import', 'from ..service import'),
        (r'from vrp\..+import', lambda m: m.group(0).replace('from vrp.', 'from ..vrp.')),
        (r'from vrp import', 'from ..vrp import'),
        (r'from lstm\..+import', lambda m: m.group(0).replace('from lstm.', 'from ..lstm.')),
        (r'from lstm import', 'from ..lstm import'),
        (r'from gestion_rutas\.models', 'from ..models'),
        (r'from gestion_rutas\.database', 'from ..database'),
        (r'from gestion_rutas\.schemas', 'from ..schemas'),
        (r'from gestion_rutas\.service', 'from ..service'),
        (r'from gestion_rutas\.vrp', 'from ..vrp'),
        (r'from gestion_rutas\.lstm', 'from ..lstm'),
    ]
    
    for pattern, replacement in replacements:
        if callable(replacement):
            content = re.sub(pattern, replacement, content)
        else:
            content = re.sub(pattern, replacement, content)
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def main():
    """Procesar todos los archivos Python"""
    project_root = Path('c:/Users/hanss/Desktop/LAR/gestion_rutas')
    
    # Directorios a procesar
    dirs_to_process = ['routers', 'service', 'database', 'models', 'schemas', 'vrp', 'lstm']
    
    total_fixed = 0
    for directory in dirs_to_process:
        dir_path = project_root / directory
        if not dir_path.exists():
            print(f"⚠️  {directory} no existe")
            continue
        
        for py_file in dir_path.glob('*.py'):
            if py_file.name.startswith('test_') or py_file.name == '__init__.py':
                continue
            
            if fix_imports_in_file(str(py_file)):
                print(f"✅ {py_file.name}")
                total_fixed += 1
            else:
                print(f"⏭️  {py_file.name} (sin cambios)")
    
    print(f"\n✨ Total de archivos arreglados: {total_fixed}")

if __name__ == '__main__':
    main()
