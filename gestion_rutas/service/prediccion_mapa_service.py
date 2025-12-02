"""
SERVICIO: Predicciones LSTM para Mapa Interactivo
Genera predicciones de residuos en tiempo real para cada punto de recolección
"""
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json

try:
    from tensorflow import keras
except ImportError:
    keras = None

class PrediccionMapaService:
    """Servicio para generar predicciones LSTM y prepararlas para visualización en mapa"""
    
    def __init__(self):
        self.lstm_dir = Path(__file__).parent.parent / "lstm"
        self.modelo_path = self.lstm_dir / "lstm_temp" / "modelo.keras"
        self.scaler_path = self.lstm_dir / "scalers.pkl"
        
        # USAR CSV CON COORDENADAS REALES DEL SECTOR SUR
        self.datos_path = self.lstm_dir / "datos_residuos_iquique.csv"
        print("Usando CSV con calles reales del Sector Sur de Iquique")
        
        self.modelo = None
        self.scaler = None
        self.df = None
        
    def cargar_modelo(self) -> bool:
        """Cargar modelo LSTM entrenado y scaler"""
        try:
            if keras and self.modelo_path.exists():
                self.modelo = keras.models.load_model(str(self.modelo_path))
                print(f"Modelo LSTM cargado desde {self.modelo_path}")
                
                # Cargar scaler si existe
                if self.scaler_path.exists():
                    import pickle
                    with open(self.scaler_path, 'rb') as f:
                        scalers_dict = pickle.load(f)
                        # Extraer el scaler correcto del diccionario
                        if isinstance(scalers_dict, dict):
                            self.scaler = scalers_dict.get('scaler_y') or scalers_dict.get('scaler')
                            print(f"Scaler cargado desde {self.scaler_path} (tipo: {type(self.scaler).__name__})")
                        else:
                            self.scaler = scalers_dict
                            print(f"Scaler cargado desde {self.scaler_path}")
                else:
                    print(f" Scaler no encontrado en {self.scaler_path}, predicciones sin ajustar")
                    self.scaler = None
                
                return True
            else:
                print(f"No se encontro modelo en {self.modelo_path}")
                return False
        except Exception as e:
            print(f"Error cargando modelo: {e}")
            return False
    
    def cargar_datos_historicos(self) -> bool:
        """Cargar datos históricos del CSV"""
        try:
            if self.datos_path.exists():
                self.df = pd.read_csv(str(self.datos_path))
                self.df['fecha'] = pd.to_datetime(self.df['fecha'])
                print(f" CSV cargado: {len(self.df)} registros")
                print(f" Columnas: {self.df.columns.tolist()}")
                print(f" Puntos únicos: {self.df['punto_recoleccion'].nunique()}")
                print(f" Promedio residuos_kg: {self.df['residuos_kg'].mean():.2f}")
                print(f" Primeros 3 valores residuos_kg: {self.df['residuos_kg'].head(3).tolist()}")
                return True
            else:
                print(f" CSV no encontrado en: {self.datos_path}")
                return False
        except Exception as e:
            print(f" Error cargando CSV: {e}")
            return False
    
    def obtener_puntos_recoleccion_unicos(self) -> List[Dict]:
        """Extraer lista única de puntos con coordenadas reales del Sector Sur"""
        if self.df is None:
            print(" DataFrame es None, no se pueden obtener puntos")
            return []
        
        # Agrupar por punto único
        puntos = self.df.groupby(['punto_recoleccion', 'latitud_punto_recoleccion', 
                                   'longitud_punto_recoleccion']).size().reset_index(name='registros')
        
        puntos_lista = []
        
        for _, row in puntos.iterrows():
            puntos_lista.append({
                'nombre': row['punto_recoleccion'],
                'latitud': row['latitud_punto_recoleccion'],
                'longitud': row['longitud_punto_recoleccion'],
                'registros_historicos': row['registros']
            })
        
        print(f" Puntos únicos extraídos: {len(puntos_lista)}")
        if puntos_lista:
            print(f" Primer punto: {puntos_lista[0]['nombre']}")
        return puntos_lista
    
    def obtener_ultimos_dias(self, punto: str, n_dias: int = 3) -> Optional[np.ndarray]:
        """Obtener últimos N días de residuos para un punto específico"""
        if self.df is None:
            return None
        
        df_punto = self.df[self.df['punto_recoleccion'] == punto].copy()
        
        if len(df_punto) == 0:
            return None
            
        # Usar los datos más recientes disponibles
        df_punto = df_punto.sort_values('fecha', ascending=False)
        
        if len(df_punto) < n_dias:
            # Si no hay suficientes datos, usar el promedio histórico completo
            promedio = df_punto['residuos_kg'].mean() if len(df_punto) > 0 else 80.0
            return np.array([promedio] * n_dias)
        
        # Tomar los últimos n_dias
        ultimos = df_punto.head(n_dias)['residuos_kg'].values[::-1]
        return ultimos
    
    def predecir_residuos(self, punto: str, fecha_prediccion: Optional[datetime] = None) -> Dict:
        """
        Predecir residuos para un punto específico
        
        Args:
            punto: Nombre del punto de recolección
            fecha_prediccion: Fecha para la cual predecir (default: mañana)
        
        Returns:
            Dict con predicción y detalles
        """
        if fecha_prediccion is None:
            fecha_prediccion = datetime.now() + timedelta(days=1)
        
        # Calcular promedio histórico completo para este punto
        if self.df is not None:
            df_punto = self.df[self.df['punto_recoleccion'] == punto]
            if len(df_punto) > 0:
                promedio_historico = df_punto['residuos_kg'].mean()
                # Validar que no sea NaN
                if np.isnan(promedio_historico):
                    promedio_historico = 80.0
            else:
                promedio_historico = 80.0
            
            # Calcular factor del día de la semana basado en datos históricos
            dia_semana = fecha_prediccion.strftime('%A')
            dias_esp = {
                'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miercoles',
                'Thursday': 'Jueves', 'Friday': 'Viernes', 'Saturday': 'Sabado', 'Sunday': 'Domingo'
            }
            dia_esp = dias_esp.get(dia_semana, dia_semana)
            
            # Calcular promedio por día de la semana
            df_dia = df_punto[df_punto['dia_semana'] == dia_esp]
            if len(df_dia) > 0:
                promedio_dia = df_dia['residuos_kg'].mean()
                # Validar que no sea NaN
                if np.isnan(promedio_dia):
                    factor_dia = 1.0
                else:
                    factor_dia = promedio_dia / promedio_historico if promedio_historico > 0 else 1.0
            else:
                factor_dia = 1.0
        else:
            promedio_historico = 80.0
            factor_dia = 1.0
        
        # Obtener últimos 3 días (para mostrar en el popup)
        ultimos_dias = self.obtener_ultimos_dias(punto, n_dias=3)
        if ultimos_dias is None:
            ultimos_dias = np.array([promedio_historico, promedio_historico, promedio_historico])
        
        # Intentar predicción con modelo LSTM si está disponible
        if self.modelo is not None and ultimos_dias is not None:
            try:
                # Preparar entrada para el modelo (shape: [1, 3, 1])
                X = ultimos_dias.reshape(1, 3, 1)
                
                # Hacer predicción
                prediccion = self.modelo.predict(X, verbose=0)[0][0]
                prediccion = max(0, prediccion)
                
                # Ajustar predicción según día de la semana
                prediccion_ajustada = prediccion * factor_dia
                
                # Si la predicción es muy baja (< 10 kg), usar promedio histórico ajustado
                if prediccion_ajustada < 10:
                    return {
                        'punto': punto,
                        'fecha': fecha_prediccion.strftime('%Y-%m-%d'),
                        'prediccion_kg': round(float(promedio_historico * factor_dia), 2),
                        'metodo': 'promedio_historico_ajustado',
                        'confianza': 'media',
                        'ultimos_3_dias': ultimos_dias.tolist()
                    }
                
                return {
                    'punto': punto,
                    'fecha': fecha_prediccion.strftime('%Y-%m-%d'),
                    'prediccion_kg': round(float(prediccion_ajustada), 2),
                    'metodo': 'lstm_ajustado',
                    'confianza': 'alta',
                    'ultimos_3_dias': ultimos_dias.tolist()
                }
            
            except Exception as e:
                print(f"Error en prediccion LSTM para {punto}: {e}")
                # Fallback a promedio
                pass
        
        # Si no hay modelo o falló la predicción, usar promedio histórico ajustado
        resultado = {
            'punto': punto,
            'fecha': fecha_prediccion.strftime('%Y-%m-%d'),
            'prediccion_kg': round(float(promedio_historico * factor_dia), 2),
            'metodo': 'promedio_historico_ajustado',
            'confianza': 'media',
            'ultimos_3_dias': ultimos_dias.tolist()
        }
        print(f"→ Predicción: {punto[:30]:30} = {resultado['prediccion_kg']:6.2f} kg (promedio={promedio_historico:.2f}, factor={factor_dia:.2f})")
        return resultado
    
    def generar_predicciones_completas(self, fecha_prediccion: Optional[datetime] = None) -> List[Dict]:
        """
        Generar predicciones para todos los puntos de recolección
        OPTIMIZADO: Hace predicciones por lotes para mejorar rendimiento
        
        Returns:
            Lista de diccionarios con predicciones y coordenadas para cada punto
        """
        # Cargar recursos
        self.cargar_modelo()
        self.cargar_datos_historicos()
        
        if self.df is None:
            return []
        
        # Obtener puntos únicos
        puntos = self.obtener_puntos_recoleccion_unicos()
        print(f"⏱ Generando predicciones para {len(puntos)} puntos...")
        
        # OPTIMIZACIÓN: Preparar todas las entradas primero
        if self.modelo is not None:
            # Preparar lote de entradas para predicción
            entradas_lote = []
            puntos_validos = []
            
            for punto_info in puntos:
                ultimos_dias = self.obtener_ultimos_dias(punto_info['nombre'], n_dias=3)
                if ultimos_dias is not None:
                    entradas_lote.append(ultimos_dias.reshape(1, 3, 1))
                    puntos_validos.append(punto_info)
            
            if entradas_lote:
                # Hacer predicción por lotes (MUCHO MÁS RÁPIDO)
                import numpy as np
                X_lote = np.vstack(entradas_lote)  # Shape: [n_puntos, 3, 1]
                predicciones_lote = self.modelo.predict(X_lote, verbose=0)  # Una sola llamada
                
                # Aplicar scaler inverso si está disponible
                if self.scaler is not None:
                    try:
                        predicciones_lote = self.scaler.inverse_transform(predicciones_lote)
                        print(f" Scaler inverso aplicado a predicciones")
                    except Exception as e:
                        print(f" Error aplicando scaler inverso: {e}")
                
                # Procesar resultados
                predicciones = []
                for i, punto_info in enumerate(puntos_validos):
                    prediccion_raw = float(predicciones_lote[i][0])
                    
                    # Calcular factores de ajuste
                    if fecha_prediccion is None:
                        fecha_prediccion = datetime.now() + timedelta(days=1)
                    
                    factor_dia = self._calcular_factor_dia(punto_info['nombre'], fecha_prediccion)
                    prediccion_ajustada = max(0, prediccion_raw * factor_dia)
                    
                    # Si la predicción es muy baja (< 5 kg), usar promedio histórico
                    if prediccion_ajustada < 5:
                        # Calcular promedio histórico para este punto
                        df_punto = self.df[self.df['punto_recoleccion'] == punto_info['nombre']]
                        if len(df_punto) > 0:
                            promedio = df_punto['residuos_kg'].mean()
                            if not np.isnan(promedio):
                                prediccion_ajustada = promedio * factor_dia
                                metodo = 'promedio_historico'
                            else:
                                prediccion_ajustada = 80.0 * factor_dia
                                metodo = 'valor_default'
                        else:
                            prediccion_ajustada = 80.0 * factor_dia
                            metodo = 'valor_default'
                    else:
                        metodo = 'lstm_batch'
                    
                    pred_completa = {
                        'punto': punto_info['nombre'],
                        'fecha': fecha_prediccion.strftime('%Y-%m-%d'),
                        'prediccion_kg': round(prediccion_ajustada, 2),
                        'metodo': metodo,
                        'confianza': 'alta' if metodo == 'lstm_batch' else 'media',
                        'latitud': punto_info['latitud'],
                        'longitud': punto_info['longitud'],
                        'registros_historicos': punto_info['registros_historicos']
                    }
                    predicciones.append(pred_completa)
                
                print(f" {len(predicciones)} predicciones generadas por lote en modo optimizado")
                return predicciones
        
        # Fallback: método tradicional si no hay modelo
        predicciones = []
        for punto_info in puntos:
            pred = self.predecir_residuos(punto_info['nombre'], fecha_prediccion)
            
            # Combinar predicción con coordenadas
            pred_completa = {
                **pred,
                'latitud': punto_info['latitud'],
                'longitud': punto_info['longitud'],
                'registros_historicos': punto_info['registros_historicos']
            }
            predicciones.append(pred_completa)
        
        return predicciones
    
    def _calcular_factor_dia(self, punto: str, fecha: datetime) -> float:
        """Calcular factor de ajuste según día de la semana"""
        if self.df is None:
            return 1.0
        
        df_punto = self.df[self.df['punto_recoleccion'] == punto]
        if len(df_punto) == 0:
            return 1.0
        
        promedio_historico = df_punto['residuos_kg'].mean()
        if np.isnan(promedio_historico) or promedio_historico == 0:
            return 1.0
        
        # Obtener día de la semana
        dia_semana = fecha.strftime('%A')
        dias_esp = {
            'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miercoles',
            'Thursday': 'Jueves', 'Friday': 'Viernes', 'Saturday': 'Sabado', 'Sunday': 'Domingo'
        }
        dia_esp = dias_esp.get(dia_semana, dia_semana)
        
        df_dia = df_punto[df_punto['dia_semana'] == dia_esp]
        if len(df_dia) > 0:
            promedio_dia = df_dia['residuos_kg'].mean()
            if not np.isnan(promedio_dia):
                return promedio_dia / promedio_historico
        
        return 1.0
    
    def clasificar_nivel_demanda(self, kg: float) -> Dict:
        """
        Clasificar nivel de demanda según cantidad predicha
        
        Returns:
            Dict con nivel, color y prioridad
        """
        if kg < 50:
            return {'nivel': 'Muy Bajo', 'color': '#00FF00', 'prioridad': 1, 'radio': 3}
        elif kg < 80:
            return {'nivel': 'Bajo', 'color': '#90EE90', 'prioridad': 2, 'radio': 5}
        elif kg < 120:
            return {'nivel': 'Medio', 'color': '#FFD700', 'prioridad': 3, 'radio': 7}
        elif kg < 150:
            return {'nivel': 'Alto', 'color': '#FFA500', 'prioridad': 4, 'radio': 9}
        else:
            return {'nivel': 'Muy Alto', 'color': '#FF0000', 'prioridad': 5, 'radio': 12}
    
    def generar_estadisticas_globales(self, predicciones: List[Dict]) -> Dict:
        """Generar estadísticas agregadas de las predicciones"""
        if not predicciones:
            return {}
        
        total_kg = sum([p['prediccion_kg'] for p in predicciones])
        promedio_kg = total_kg / len(predicciones)
        max_kg = max([p['prediccion_kg'] for p in predicciones])
        min_kg = min([p['prediccion_kg'] for p in predicciones])
        
        # Contar por nivel de demanda
        niveles = {'Muy Bajo': 0, 'Bajo': 0, 'Medio': 0, 'Alto': 0, 'Muy Alto': 0}
        for pred in predicciones:
            nivel = self.clasificar_nivel_demanda(pred['prediccion_kg'])['nivel']
            niveles[nivel] += 1
        
        return {
            'total_puntos': len(predicciones),
            'total_residuos_kg': round(total_kg, 2),
            'promedio_kg': round(promedio_kg, 2),
            'maximo_kg': round(max_kg, 2),
            'minimo_kg': round(min_kg, 2),
            'distribucion_niveles': niveles,
            'fecha_generacion': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
