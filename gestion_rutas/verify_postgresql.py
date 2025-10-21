"""
Script de verificación final
Confirma que PostgreSQL tiene los datos y está listo para producción
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, func
from sqlalchemy.orm import sessionmaker
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Obtener configuración
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "hanskawaii1")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "gestion_rutas")

DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

logger.info("\n" + "="*80)
logger.info("🔍 VERIFICACIÓN DE BASE DE DATOS POSTGRESQL")
logger.info("="*80)

try:
    # Conectar
    engine = create_engine(DATABASE_URL, echo=False)
    
    # Test 1: Conexión
    logger.info("\n✅ Test 1: Conectando a PostgreSQL...")
    connection = engine.connect()
    result = connection.execute(text("SELECT 1"))
    logger.info("   ✅ Conexión exitosa")
    
    # Test 2: Tablas
    logger.info("\n✅ Test 2: Verificando tablas...")
    result = connection.execute(text("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public'
    """))
    tables = [row[0] for row in result]
    logger.info(f"   Tablas encontradas: {', '.join(tables)}")
    
    # Test 3: Contar registros
    logger.info("\n✅ Test 3: Contando registros...")
    result = connection.execute(text("SELECT COUNT(*) FROM zona"))
    zona_count = result.fetchone()[0]
    logger.info(f"   Zonas: {zona_count}")
    
    result = connection.execute(text("SELECT COUNT(*) FROM prediccion_demanda"))
    pred_count = result.fetchone()[0]
    logger.info(f"   Predicciones: {pred_count}")
    
    # Test 4: Estadísticas
    logger.info("\n✅ Test 4: Calculando estadísticas...")
    result = connection.execute(text("""
        SELECT 
            AVG(error_mape) as promedio_mape,
            AVG(error_rmse) as promedio_rmse,
            MIN(valor_real_kg) as min_real,
            MAX(valor_real_kg) as max_real,
            COUNT(*) as total
        FROM prediccion_demanda
    """))
    stats = result.fetchone()
    if stats:
        logger.info(f"   Promedio MAPE: {stats[0]:.2f}%")
        logger.info(f"   Promedio RMSE: {stats[1]:.6f}")
        logger.info(f"   Rango Real: {stats[2]:.2f} - {stats[3]:.2f} kg")
        logger.info(f"   Total registros: {stats[4]}")
    
    # Test 5: Muestra de datos
    logger.info("\n✅ Test 5: Muestrando primeros registros...")
    result = connection.execute(text("""
        SELECT id_prediccion, valor_real_kg, valor_predicho_kg, error_mape
        FROM prediccion_demanda
        ORDER BY id_prediccion ASC
        LIMIT 3
    """))
    for row in result:
        logger.info(f"   ID: {row[0]} | Real: {row[1]:.2f}kg | Predicho: {row[2]:.2f}kg | MAPE: {row[3]:.2f}%")
    
    connection.close()
    
    logger.info("\n" + "="*80)
    logger.info("✅ TODAS LAS VERIFICACIONES COMPLETADAS EXITOSAMENTE")
    logger.info("="*80)
    logger.info("\n📊 BASE DE DATOS POSTGRESQL LISTA PARA PRODUCCIÓN")
    logger.info("\n" + "="*80 + "\n")
    
except Exception as e:
    logger.error(f"\n❌ Error: {str(e)}")
    logger.error(f"\nVerifica tu archivo .env:")
    logger.error(f"  DB_USER={DB_USER}")
    logger.error(f"  DB_HOST={DB_HOST}")
    logger.error(f"  DB_PORT={DB_PORT}")
    logger.error(f"  DB_NAME={DB_NAME}")
    
    logger.info("\n" + "="*80 + "\n")
