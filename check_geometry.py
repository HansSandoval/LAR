import sys
import os
import json
from datetime import date, datetime

# Add project root to path
sys.path.insert(0, os.getcwd())

from gestion_rutas.database.db import execute_query

def json_serial(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError (f"Type {type(obj)} not serializable")

try:
    # Check the last 5 routes, casting to text to see content
    query = """
        SELECT id_ruta, fecha, 
               CASE WHEN geometria_json IS NULL THEN 'NULL' ELSE 'NOT NULL' END as geo_status,
               substring(cast(geometria_json as text) from 1 for 50) as geo_preview
        FROM ruta_planificada 
        ORDER BY id_ruta DESC 
        LIMIT 5
    """
    results = execute_query(query)
    print(json.dumps(results, indent=2, default=json_serial))
except Exception as e:
    print(f"Error: {e}")
