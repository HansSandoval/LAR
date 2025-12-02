import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import logging
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Importar modelos
from models.models import (
    Base, Zona, PuntoRecoleccion, Camion, Turno, Operador,
    PuntoDisposicion, Usuario, Incidencia, PrediccionDemanda,
    RutaPlanificada, RutaEjecutada
)
from database.db import SessionLocal

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ImportadorDatos:
    def __init__(self, csv_path):
        self.df = pd.read_csv(csv_path)
        self.session = SessionLocal()
        logger.info(f"CSV cargado: {csv_path}")
    
    def importar_zonas(self):
        """Importa zonas únicas del CSV"""
        logger.info("Importando ZONAS...")
        
        zonas_unicas = self.df[['id_zona', 'nombre_zona', 'tipo_zona', 'prioridad']].drop_duplicates()
        
        for _, row in zonas_unicas.iterrows():
            # Verificar si existe
            zona_existe = self.session.query(Zona).filter(
                Zona.id_zona == row['id_zona']
            ).first()
            
            if not zona_existe:
                zona = Zona(
                    id_zona=int(row['id_zona']),
                    nombre=row['nombre_zona'],
                    tipo=row['tipo_zona'],
                    prioridad=int(row['prioridad']),
                    coordenadas_limite="[{-20.27, -70.14}]"  # Centro Iquique
                )
                self.session.add(zona)
                logger.info(f"   Zona creada: {row['nombre_zona']}")
        
        self.session.commit()
        logger.info(f"  Total de zonas insertadas")
    
    def importar_puntos_recoleccion(self):
        """Importa puntos de recolección con geocoding"""
        logger.info("Importando PUNTOS DE RECOLECCION...")
        
        # Puntos únicos con sus coordenadas
        puntos_unicos = self.df[[
            'id_zona', 'punto_recoleccion', 'tipo_punto',
            'latitud_punto_recoleccion', 'longitud_punto_recoleccion', 'residuos_kg'
        ]].drop_duplicates(subset=['punto_recoleccion'])
        
        for _, row in puntos_unicos.iterrows():
            punto_existe = self.session.query(PuntoRecoleccion).filter(
                PuntoRecoleccion.nombre == row['punto_recoleccion']
            ).first()
            
            if not punto_existe:
                # Calcular capacidad promedio
                capacidad_promedio = self.df[
                    self.df['punto_recoleccion'] == row['punto_recoleccion']
                ]['residuos_kg'].mean()
                
                punto = PuntoRecoleccion(
                    id_zona=int(row['id_zona']),
                    nombre=row['punto_recoleccion'],
                    tipo=row['tipo_punto'],
                    latitud=float(row['latitud_punto_recoleccion']),
                    longitud=float(row['longitud_punto_recoleccion']),
                    capacidad_kg=float(capacidad_promedio),
                    estado='activo'
                )
                self.session.add(punto)
                logger.info(f"   Punto: {row['punto_recoleccion'][:40]}")
        
        self.session.commit()
        logger.info(f"  Total puntos de recolección insertados")
    
    def importar_camiones(self):
        """Importa camiones únicos del CSV"""
        logger.info("Importando CAMIONES...")
        
        camiones_unicos = self.df[[
            'patente_camion', 'capacidad_kg', 'consumo_km_l',
            'tipo_combustible', 'estado_operativo', 'gps_id'
        ]].drop_duplicates(subset=['patente_camion'])
        
        for _, row in camiones_unicos.iterrows():
            camion_existe = self.session.query(Camion).filter(
                Camion.patente == row['patente_camion']
            ).first()
            
            if not camion_existe:
                camion = Camion(
                    patente=row['patente_camion'],
                    capacidad_kg=float(row['capacidad_kg']),
                    consumo_km_l=float(row['consumo_km_l']),
                    tipo_combustible=row['tipo_combustible'],
                    estado_operativo=row['estado_operativo'],
                    gps_id=row['gps_id']
                )
                self.session.add(camion)
                logger.info(f"   Camión: {row['patente_camion']}")
        
        self.session.commit()
        logger.info(f"  Total camiones insertados")
    
    def importar_puntos_disposicion(self):
        """Importa puntos de disposición únicos"""
        logger.info("Importando PUNTOS DE DISPOSICIÓN...")
        
        disposiciones_unicas = self.df[[
            'nombre_punto_disp', 'tipo_punto_disp',
            'latitud_punto_disp', 'longitud_punto_disp', 'capacidad_diaria_ton'
        ]].drop_duplicates(subset=['nombre_punto_disp'])
        
        for _, row in disposiciones_unicas.iterrows():
            disp_existe = self.session.query(PuntoDisposicion).filter(
                PuntoDisposicion.nombre == row['nombre_punto_disp']
            ).first()
            
            if not disp_existe:
                disposicion = PuntoDisposicion(
                    nombre=row['nombre_punto_disp'],
                    tipo=row['tipo_punto_disp'],
                    latitud=float(row['latitud_punto_disp']),
                    longitud=float(row['longitud_punto_disp']),
                    capacidad_diaria_ton=float(row['capacidad_diaria_ton'])
                )
                self.session.add(disposicion)
                logger.info(f"   Disposición: {row['nombre_punto_disp']}")
        
        self.session.commit()
        logger.info(f"  Total puntos disposición insertados")
    
    def importar_incidencias_desde_contexto(self):
        """Crea incidencias basadas en evento y clima"""
        logger.info("Importando INCIDENCIAS (desde contexto)...")
        
        # Mapeo de eventos a severidad
        severidad_mapa = {
            'festivo': 3,
            'feria_local': 2,
            'evento_especial': 2,
            'ninguno': 0
        }
        
        clima_severidad = {
            'soleado': 0,
            'mayormente soleado': 0,
            'nublado': 1,
            'lluvia': 2
        }
        
        # Filtrar filas con eventos o clima adverso
        incidencias_data = self.df[
            (self.df['evento'] != 'ninguno') | 
            (self.df['clima'] == 'nublado')
        ][['fecha', 'id_zona', 'evento', 'clima', 'residuos_kg', 'patente_camion']].drop_duplicates()
        
        for _, row in incidencias_data.iterrows():
            # Calcular severidad
            severidad = severidad_mapa.get(row['evento'], 0) + clima_severidad.get(row['clima'], 0)
            severidad = min(severidad, 5)  # Max 5
            
            # Obtener IDs
            zona = self.session.query(Zona).filter(Zona.id_zona == row['id_zona']).first()
            camion = self.session.query(Camion).filter(Camion.patente == row['patente_camion']).first()
            
            if zona and camion:
                incidencia = Incidencia(
                    id_zona=zona.id_zona,
                    id_camion=camion.id_camion,
                    tipo=row['evento'] if row['evento'] != 'ninguno' else 'clima_adverso',
                    descripcion=f"{row['evento']} - Clima: {row['clima']} - Residuos: {row['residuos_kg']}kg",
                    fecha_hora=pd.to_datetime(row['fecha']),
                    severidad=severidad
                )
                self.session.add(incidencia)
                logger.info(f"   Incidencia: {row['evento']} (severidad {severidad})")
        
        self.session.commit()
        logger.info(f"  Total incidencias insertadas")
    
    def ejecutar_todo(self):
        """Ejecuta todos los imports en orden"""
        try:
            self.importar_zonas()
            self.importar_puntos_recoleccion()
            self.importar_camiones()
            self.importar_puntos_disposicion()
            self.importar_incidencias_desde_contexto()
            
            print("\n" + "="*80)
            print(" IMPORTACIÓN COMPLETADA EXITOSAMENTE")
            print("="*80)
            print(f"Tablas pobladas:")
            print(f"  - Zonas: {self.session.query(Zona).count()}")
            print(f"  - Puntos de Recolección: {self.session.query(PuntoRecoleccion).count()}")
            print(f"  - Camiones: {self.session.query(Camion).count()}")
            print(f"  - Puntos Disposición: {self.session.query(PuntoDisposicion).count()}")
            print(f"  - Incidencias: {self.session.query(Incidencia).count()}")
            
        except Exception as e:
            logger.error(f"Error durante importación: {str(e)}")
            self.session.rollback()
            raise
        finally:
            self.session.close()

if __name__ == "__main__":
    importador = ImportadorDatos('gestion_rutas/lstm/datos_residuos_iquique_enriquecido.csv')
    importador.ejecutar_todo()
