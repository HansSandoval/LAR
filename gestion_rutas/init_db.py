"""
Script de inicialización de base de datos
Crea todas las tablas y datos de prueba
"""

import logging
from datetime import date, datetime, time
# DEPRECATED: Este archivo usa el patrón antiguo de SQLAlchemy
# Usar scripts específicos de PostgreSQL para migraciones
from .database.db import SessionLocal, init_db
from .models.models import (
    Zona, PuntoRecoleccion, Camion, Turno, 
    RutaPlanificada, RutaEjecutada, Incidencia, 
    PrediccionDemanda, Usuario, PeriodoTemporal
)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Deprecated: Este módulo ya no se utiliza con PostgreSQL directo


def crear_datos_prueba():
    """Crear datos de prueba en la base de datos"""
    db = SessionLocal()
    
    try:
        # Crear zonas
        zona1 = Zona(
            nombre="Zona Centro",
            tipo="urbana",
            area_km2=25.5,
            poblacion=150000,
            prioridad=1
        )
        zona2 = Zona(
            nombre="Zona Norte",
            tipo="urbana",
            area_km2=35.8,
            poblacion=200000,
            prioridad=2
        )
        
        db.add(zona1)
        db.add(zona2)
        db.flush()
        
        logger.info(f"✓ Zonas creadas: {zona1.nombre}, {zona2.nombre}")
        
        # Crear puntos de recolección
        puntos = [
            PuntoRecoleccion(
                id_zona=zona1.id_zona,
                nombre="Depósito Central",
                tipo="deposito",
                latitud=-20.2167,
                longitud=-70.1500,
                capacidad_kg=5000.0,
                estado="activo"
            ),
            PuntoRecoleccion(
                id_zona=zona1.id_zona,
                nombre="Centro Comercial",
                tipo="recoleccion",
                latitud=-20.2100,
                longitud=-70.1400,
                capacidad_kg=500.0,
                estado="activo"
            ),
            PuntoRecoleccion(
                id_zona=zona1.id_zona,
                nombre="Sector Industrial",
                tipo="recoleccion",
                latitud=-20.2250,
                longitud=-70.1600,
                capacidad_kg=800.0,
                estado="activo"
            ),
            PuntoRecoleccion(
                id_zona=zona2.id_zona,
                nombre="Zona Norte - Centro",
                tipo="recoleccion",
                latitud=-20.1900,
                longitud=-70.1300,
                capacidad_kg=600.0,
                estado="activo"
            ),
        ]
        
        for punto in puntos:
            db.add(punto)
        db.flush()
        
        logger.info(f"✓ Puntos de recolección creados: {len(puntos)}")
        
        # Crear camiones
        camion1 = Camion(
            patente="VRPX001",
            capacidad_kg=2500.0,
            consumo_km_l=8.5,
            tipo_combustible="diesel",
            estado_operativo="disponible",
            gps_id="GPS001"
        )
        camion2 = Camion(
            patente="VRPX002",
            capacidad_kg=3000.0,
            consumo_km_l=7.5,
            tipo_combustible="diesel",
            estado_operativo="disponible",
            gps_id="GPS002"
        )
        
        db.add(camion1)
        db.add(camion2)
        db.flush()
        
        logger.info(f"✓ Camiones creados: {camion1.patente}, {camion2.patente}")
        
        # Crear turnos
        turno1 = Turno(
            id_camion=camion1.id_camion,
            fecha=date.today(),
            hora_inicio=time(6, 0),
            hora_fin=time(14, 0),
            operador="Juan Pérez",
            estado="activo"
        )
        turno2 = Turno(
            id_camion=camion2.id_camion,
            fecha=date.today(),
            hora_inicio=time(14, 0),
            hora_fin=time(22, 0),
            operador="Carlos López",
            estado="activo"
        )
        
        db.add(turno1)
        db.add(turno2)
        db.flush()
        
        logger.info(f"✓ Turnos creados: {turno1.operador}, {turno2.operador}")
        
        # Crear rutas planificadas
        # Geometría dummy (línea recta entre puntos)
        geo1 = [
            [puntos[0].latitud, puntos[0].longitud],
            [puntos[1].latitud, puntos[1].longitud],
            [puntos[2].latitud, puntos[2].longitud]
        ]
        geo2 = [
            [puntos[0].latitud, puntos[0].longitud],
            [puntos[3].latitud, puntos[3].longitud]
        ]

        ruta1 = RutaPlanificada(
            id_zona=zona1.id_zona,
            id_turno=turno1.id_turno,
            fecha=date.today(),
            secuencia_puntos=[puntos[0].id_punto, puntos[1].id_punto, puntos[2].id_punto],
            distancia_planificada_km=35.5,
            duracion_planificada_min=180,
            version_modelo_vrp="v1.0",
            geometria_json=geo1
        )
        ruta2 = RutaPlanificada(
            id_zona=zona2.id_zona,
            id_turno=turno2.id_turno,
            fecha=date.today(),
            secuencia_puntos=[puntos[0].id_punto, puntos[3].id_punto],
            distancia_planificada_km=28.2,
            duracion_planificada_min=150,
            version_modelo_vrp="v1.0",
            geometria_json=geo2
        )
        
        db.add(ruta1)
        db.add(ruta2)
        db.flush()
        
        logger.info(f"✓ Rutas planificadas creadas: {len([ruta1, ruta2])}")
        
        # Crear usuario
        usuario = Usuario(
            nombre="Admin",
            correo="admin@gestion-rutas.com",
            rol="administrador",
            hash_password="hashed_password_here",
            activo=True
        )
        
        db.add(usuario)
        db.commit()
        
        logger.info(f"✓ Usuario creado: {usuario.nombre}")
        logger.info("✓ Datos de prueba insertados exitosamente")
        
    except Exception as e:
        db.rollback()
        logger.error(f"✗ Error al crear datos de prueba: {str(e)}")
        raise
    finally:
        db.close()


def main():
    """Función principal"""
    logger.info("=" * 60)
    logger.info("Inicializando Base de Datos - Gestión de Rutas VRP")
    logger.info("=" * 60)
    
    try:
        # Crear tablas
        logger.info("\n1. Creando estructura de tablas...")
        init_db()
        logger.info("✓ Tablas creadas exitosamente")
        
        # Crear datos de prueba
        logger.info("\n2. Insertando datos de prueba...")
        crear_datos_prueba()
        
        logger.info("\n" + "=" * 60)
        logger.info("✓ Base de datos inicializada correctamente")
        logger.info("✓ Conectada a PostgreSQL en: localhost:5432/gestion_rutas")
        logger.info("=" * 60 + "\n")
        
    except Exception as e:
        logger.error(f"\n✗ Error en inicialización: {str(e)}")
        raise


if __name__ == "__main__":
    main()
