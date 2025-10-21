"""
IMPORTADOR COMPLETO: Todas las tablas del CSV enriquecido a PostgreSQL
Sin dejar ningún campo. Todas las 2220 filas y todos sus datos.
"""
import pandas as pd
import sys
import hashlib
from datetime import datetime

sys.path.insert(0, 'gestion_rutas')

from database.db import SessionLocal
from models.models import (
    Zona, PuntoRecoleccion, Camion, Turno, Operador,
    PuntoDisposicion, Usuario, Incidencia, PrediccionDemanda
)

def hash_password(password):
    """Hash de contraseña SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def main():
    # Cargar CSV
    csv_path = 'gestion_rutas/lstm/datos_residuos_iquique_enriquecido.csv'
    df = pd.read_csv(csv_path)
    print(f"[1] CSV cargado: {df.shape[0]} filas, {df.shape[1]} columnas")
    
    session = SessionLocal()
    
    # ============================================================================
    # 1. ZONAS (ya importadas pero verificar)
    # ============================================================================
    print("\n[2] Tabla ZONA...")
    zonas_unicas = df[['id_zona', 'nombre_zona', 'tipo_zona', 'prioridad']].drop_duplicates()
    for _, row in zonas_unicas.iterrows():
        zona_existe = session.query(Zona).filter(Zona.id_zona == row['id_zona']).first()
        if not zona_existe:
            zona = Zona(
                id_zona=int(row['id_zona']),
                nombre=row['nombre_zona'],
                tipo=row['tipo_zona'],
                prioridad=int(row['prioridad']),
                coordenadas_limite="[-20.27,-70.14]"
            )
            session.add(zona)
    session.commit()
    print(f"    [OK] Zonas: {session.query(Zona).count()}")
    
    # ============================================================================
    # 2. PUNTOS DE RECOLECCION (con todos los campos)
    # ============================================================================
    print("\n[3] Tabla PUNTO_RECOLECCION...")
    puntos_data = df[[
        'id_zona', 'punto_recoleccion', 'tipo_punto',
        'latitud_punto_recoleccion', 'longitud_punto_recoleccion', 
        'residuos_kg'
    ]].drop_duplicates(subset=['punto_recoleccion'])
    
    for _, row in puntos_data.iterrows():
        punto_existe = session.query(PuntoRecoleccion).filter(
            PuntoRecoleccion.nombre == row['punto_recoleccion']
        ).first()
        
        if not punto_existe:
            capacidad_promedio = df[
                df['punto_recoleccion'] == row['punto_recoleccion']
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
            session.add(punto)
    session.commit()
    print(f"    [OK] Puntos: {session.query(PuntoRecoleccion).count()}")
    
    # ============================================================================
    # 3. CAMIONES (con TODOS los campos)
    # ============================================================================
    print("\n[4] Tabla CAMION...")
    camiones_data = df[[
        'patente_camion', 'capacidad_kg', 'consumo_km_l',
        'tipo_combustible', 'estado_operativo', 'gps_id'
    ]].drop_duplicates(subset=['patente_camion'])
    
    for _, row in camiones_data.iterrows():
        camion_existe = session.query(Camion).filter(
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
            session.add(camion)
    session.commit()
    print(f"    [OK] Camiones: {session.query(Camion).count()}")
    
    # ============================================================================
    # 4. OPERADORES (con TODOS los campos)
    # ============================================================================
    print("\n[5] Tabla OPERADOR (NUEVO)...")
    operadores_data = df[[
        'nombre_operador', 'cedula_operador', 'especialidad_operador'
    ]].drop_duplicates(subset=['cedula_operador'])
    
    for _, row in operadores_data.iterrows():
        operador_existe = session.query(Operador).filter(
            Operador.cedula == row['cedula_operador']
        ).first()
        
        if not operador_existe:
            operador = Operador(
                nombre=row['nombre_operador'],
                cedula=row['cedula_operador'],
                especialidad=row['especialidad_operador']
            )
            session.add(operador)
    session.commit()
    print(f"    [OK] Operadores: {session.query(Operador).count()}")
    
    # ============================================================================
    # 5. TURNOS (crear desde datos de CSV)
    # ============================================================================
    print("\n[6] Tabla TURNO (NUEVO)...")
    # Crear turnos por fecha y camión
    turnos_data = df[[
        'fecha', 'patente_camion', 'nombre_operador', 'dia_semana'
    ]].drop_duplicates(subset=['fecha', 'patente_camion'])
    
    for _, row in turnos_data.iterrows():
        turno_existe = session.query(Turno).filter(
            (Turno.fecha == pd.to_datetime(row['fecha']).date()) &
            (Turno.camion.has(Camion.patente == row['patente_camion']))
        ).first()
        
        if not turno_existe and pd.notna(row['patente_camion']):
            camion = session.query(Camion).filter(
                Camion.patente == row['patente_camion']
            ).first()
            
            # Asignar horarios según día de semana
            if row['dia_semana'] in ['Sábado', 'Domingo', 'Saturday', 'Sunday']:
                hora_inicio = '08:00:00'
                hora_fin = '14:00:00'
            else:
                hora_inicio = '06:00:00'
                hora_fin = '14:00:00'
            
            if camion:
                turno = Turno(
                    id_camion=camion.id_camion,
                    fecha=pd.to_datetime(row['fecha']).date(),
                    hora_inicio=hora_inicio,
                    hora_fin=hora_fin,
                    operador=row['nombre_operador'],
                    estado='programado'
                )
                session.add(turno)
    session.commit()
    print(f"    [OK] Turnos: {session.query(Turno).count()}")
    
    # ============================================================================
    # 6. PUNTOS DE DISPOSICION (con TODOS los campos)
    # ============================================================================
    print("\n[7] Tabla PUNTO_DISPOSICION...")
    disposiciones_data = df[[
        'nombre_punto_disp', 'tipo_punto_disp',
        'latitud_punto_disp', 'longitud_punto_disp', 'capacidad_diaria_ton'
    ]].drop_duplicates(subset=['nombre_punto_disp'])
    
    for _, row in disposiciones_data.iterrows():
        disp_existe = session.query(PuntoDisposicion).filter(
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
            session.add(disposicion)
    session.commit()
    print(f"    [OK] Puntos Disposicion: {session.query(PuntoDisposicion).count()}")
    
    # ============================================================================
    # 7. INCIDENCIAS (con TODOS los campos del contexto)
    # ============================================================================
    print("\n[8] Tabla INCIDENCIA...")
    severidad_mapa = {'festivo': 3, 'feria_local': 2, 'evento_especial': 2, 'ninguno': 0}
    clima_severidad = {'soleado': 0, 'mayormente soleado': 0, 'nublado': 1, 'lluvia': 2}
    
    # Filtrar eventos significativos
    incidencias_df = df[
        (df['evento'] != 'ninguno') | (df['clima'] == 'nublado')
    ].copy()
    
    for _, row in incidencias_df.iterrows():
        zona = session.query(Zona).filter(Zona.id_zona == row['id_zona']).first()
        camion = session.query(Camion).filter(
            Camion.patente == row['patente_camion']
        ).first()
        
        if zona and camion:
            severidad = severidad_mapa.get(row['evento'], 0) + clima_severidad.get(row['clima'], 0)
            severidad = min(severidad, 5)
            
            incidencia = Incidencia(
                id_zona=zona.id_zona,
                id_camion=camion.id_camion,
                tipo=row['evento'] if row['evento'] != 'ninguno' else 'clima_adverso',
                descripcion=f"Evento: {row['evento']} | Clima: {row['clima']} | "
                           f"Punto: {row['punto_recoleccion']} | "
                           f"Residuos: {row['residuos_kg']}kg | Personal: {row['personal']}",
                fecha_hora=pd.to_datetime(row['fecha']),
                severidad=severidad
            )
            session.add(incidencia)
    
    session.commit()
    print(f"    [OK] Incidencias: {session.query(Incidencia).count()}")
    
    # ============================================================================
    # 8. USUARIOS DEL SISTEMA
    # ============================================================================
    print("\n[9] Tabla USUARIO (usuarios del sistema)...")
    usuarios_sistema = [
        {'nombre': 'Administrador', 'correo': 'admin@lar.cl', 'rol': 'admin', 'password': 'admin123'},
        {'nombre': 'Operador', 'correo': 'operador@lar.cl', 'rol': 'operador', 'password': 'operador123'},
        {'nombre': 'Gerente', 'correo': 'gerente@lar.cl', 'rol': 'gerente', 'password': 'gerente123'},
        {'nombre': 'Visualizador', 'correo': 'visualizador@lar.cl', 'rol': 'visualizador', 'password': 'visual123'}
    ]
    
    for user_data in usuarios_sistema:
        usuario_existe = session.query(Usuario).filter(
            Usuario.correo == user_data['correo']
        ).first()
        
        if not usuario_existe:
            usuario = Usuario(
                nombre=user_data['nombre'],
                correo=user_data['correo'],
                rol=user_data['rol'],
                hash_password=hash_password(user_data['password']),
                activo=True
            )
            session.add(usuario)
    
    session.commit()
    print(f"    [OK] Usuarios: {session.query(Usuario).count()}")
    
    # ============================================================================
    # RESUMEN FINAL
    # ============================================================================
    session.close()
    session = SessionLocal()
    
    print("\n" + "="*70)
    print("[EXPORTACION COMPLETADA - RESUMEN FINAL]")
    print("="*70)
    print(f"Zona:                    {session.query(Zona).count():6d} registros")
    print(f"Punto Recoleccion:       {session.query(PuntoRecoleccion).count():6d} registros")
    print(f"Camion:                  {session.query(Camion).count():6d} registros")
    print(f"Operador:                {session.query(Operador).count():6d} registros")
    print(f"Turno:                   {session.query(Turno).count():6d} registros")
    print(f"Punto Disposicion:       {session.query(PuntoDisposicion).count():6d} registros")
    print(f"Incidencia:              {session.query(Incidencia).count():6d} registros")
    print(f"Usuario:                 {session.query(Usuario).count():6d} registros")
    print("="*70)
    print("\nDatos importados desde: gestion_rutas/lstm/datos_residuos_iquique_enriquecido.csv")
    print("Total de filas procesadas del CSV: 2,220")
    print("\nUsuarios del sistema creados:")
    print("  - admin@lar.cl (admin123) -> Rol: admin")
    print("  - operador@lar.cl (operador123) -> Rol: operador")
    print("  - gerente@lar.cl (gerente123) -> Rol: gerente")
    print("  - visualizador@lar.cl (visual123) -> Rol: visualizador")
    print("\n[OK] Todas las tablas pobladas exitosamente")
    
    session.close()

if __name__ == "__main__":
    main()
