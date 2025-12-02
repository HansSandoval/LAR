"""
Sistema de Agentes Múltiples (MAS) para Recolección de Residuos
Camiones cooperativos que toman decisiones inteligentes basadas en predicciones LSTM
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
import random
import math
from .dvrptw_env import DVRPTWEnv, Cliente, Camion, OSRMService

try:
    from stable_baselines3 import PPO
except ImportError:
    PPO = None


@dataclass
class DecisionAgente:
    """Representa una decisión tomada por un agente"""
    camion_id: int
    cliente_objetivo_id: int
    razonamiento: str
    prioridad_decision: float
    distancia_estimada: float
    beneficio_estimado: float


class AgenteRecolector:
    """
    Agente autónomo que representa un camión de recolección
    
    Características:
    - Toma decisiones basadas en demanda LSTM
    - Coopera con otros agentes para evitar conflictos
    - Optimiza ruta según proximidad y prioridad
    - Considera capacidad restante
    """
    
    def __init__(self, camion: Camion, env: DVRPTWEnv, modelo_ppo=None, sector_id: int = -1):
        self.camion = camion
        self.env = env
        self.memoria_decisiones: List[DecisionAgente] = []
        self.modelo_ppo = modelo_ppo
        self.sector_id = sector_id
        
        # Parámetros de decisión
        self.peso_distancia = 0.4
        self.peso_demanda = 0.3
        self.peso_prioridad = 0.3

    def seleccionar_accion_ppo(self) -> Optional[int]:
        """
        Usa el modelo PPO para seleccionar el próximo cliente.
        """
        if self.modelo_ppo is None:
            return None

        # 1. Obtener observación
        # Asegurarse de que el entorno tenga el método (por si acaso)
        if hasattr(self.env, 'get_agent_observation'):
            obs = self.env.get_agent_observation(self.camion.id)
        else:
            return None
        
        # 2. Predecir acción
        try:
            action, _ = self.modelo_ppo.predict(obs, deterministic=True)
            
            # Convertir numpy int a python int
            action = int(action)
        except Exception as e:
            print(f"Error predicción PPO: {e}")
            return None
        
        # 3. Interpretar acción (0=Depot, 1..K=Vecino)
        if action == 0:
            return 0 # Depot
            
        # Reconstruir lista de vecinos para saber cuál es el elegido
        clientes_info = []
        for cliente in self.env.clientes:
            if not cliente.servido:
                dist = self.env._calcular_distancia_haversine(
                    self.camion.latitud, self.camion.longitud,
                    cliente.latitud, cliente.longitud
                )
                clientes_info.append({'dist': dist, 'cliente': cliente})
        
        clientes_info.sort(key=lambda x: x['dist'])
        vecinos = clientes_info[:self.env.max_clientes_visibles]
        
        vecino_idx = action - 1
        if vecino_idx < len(vecinos):
            cliente_elegido = vecinos[vecino_idx]['cliente']
            # El sistema MAS usa IDs 1-based para clientes, 0 para depot
            # Cliente.id ya es el ID correcto (1..N)
            return cliente_elegido.id
        else:
            # Acción inválida (ej: eligió vecino 5 pero solo hay 2)
            return 0

    def seleccionar_proximo_cliente(
        self, 
        clientes_disponibles: List[Cliente],
        decisiones_otros_agentes: List[DecisionAgente] = None
    ) -> Optional[int]:
        """
        Selecciona el próximo cliente a visitar.
        Si hay modelo PPO cargado, usa IA. Si no, usa heurística.
        """
        # --- INTENTO CON PPO ---
        if self.modelo_ppo:
            cliente_id_ppo = self.seleccionar_accion_ppo()
            
            # SANITY CHECK MEJORADO: Evitar retornos prematuros al depósito
            if cliente_id_ppo == 0:
                # 1. Si está vacío, prohibido volver
                if self.camion.carga_actual_kg == 0:
                    cliente_id_ppo = None 
                
                # 2. Si tiene carga pero es menos del 90% y hay clientes factibles, prohibido volver
                else:
                    porcentaje_carga = (self.camion.carga_actual_kg / self.camion.capacidad_kg) * 100
                    clientes_factibles_check = [
                        c for c in clientes_disponibles 
                        if not c.servido and c.demanda_kg <= self.camion.capacidad_disponible
                    ]
                    
                    if porcentaje_carga < 90 and len(clientes_factibles_check) > 0:
                        cliente_id_ppo = None
            
            if cliente_id_ppo is not None:
                # Caso 1: PPO decide ir al Depot
                if cliente_id_ppo == 0:
                    dist_depot = self.env._calcular_distancia_haversine(
                        self.camion.latitud, self.camion.longitud,
                        self.env.depot_lat, self.env.depot_lon
                    )
                    decision = DecisionAgente(
                        camion_id=self.camion.id,
                        cliente_objetivo_id=0,
                        razonamiento="IA PPO decidió ir al Depot",
                        prioridad_decision=8.0,
                        distancia_estimada=dist_depot,
                        beneficio_estimado=0.0
                    )
                    self.memoria_decisiones.append(decision)
                    return 0
                
                # Caso 2: PPO decide ir a un cliente
                cliente = next((c for c in clientes_disponibles if c.id == cliente_id_ppo), None)
                
                if cliente and not cliente.servido and cliente.demanda_kg <= self.camion.capacidad_disponible:
                    decision = DecisionAgente(
                        camion_id=self.camion.id,
                        cliente_objetivo_id=cliente_id_ppo,
                        razonamiento=f"IA PPO (Acción {cliente_id_ppo})",
                        prioridad_decision=10.0,
                        distancia_estimada=self._calcular_distancia_a(cliente, usar_osrm=False),
                        beneficio_estimado=cliente.demanda_kg
                    )
                    self.memoria_decisiones.append(decision)
                    return cliente_id_ppo

        # --- FALLBACK HEURÍSTICA ---
        if not clientes_disponibles:
            return None
        
        # Filtrar clientes ya servidos y por capacidad
        clientes_factibles = [
            c for c in clientes_disponibles 
            if not c.servido and c.demanda_kg <= self.camion.capacidad_disponible
        ]
        
        if not clientes_factibles:
            # Regresar al depósito
            dist_depot = self.env._calcular_distancia_haversine(
                self.camion.latitud, self.camion.longitud,
                self.env.depot_lat, self.env.depot_lon
            )
            decision = DecisionAgente(
                camion_id=self.camion.id,
                cliente_objetivo_id=0,
                razonamiento="Heurística: Sin clientes factibles (Retorno)",
                prioridad_decision=5.0,
                distancia_estimada=dist_depot,
                beneficio_estimado=0.0
            )
            self.memoria_decisiones.append(decision)
            return 0
        
        # OPTIMIZACIÓN: Pre-filtrado con Haversine para reducir llamadas a OSRM
        # Calcular distancia Haversine a todos los factibles
        candidatos_preliminares = []
        for cliente in clientes_factibles:
            dist_h = self.env._calcular_distancia_haversine(
                self.camion.latitud, self.camion.longitud,
                cliente.latitud, cliente.longitud
            )
            candidatos_preliminares.append((cliente, dist_h))
        
        # Ordenar por distancia Haversine y tomar los top 15
        candidatos_preliminares.sort(key=lambda x: x[1])
        top_candidatos = [c[0] for c in candidatos_preliminares[:15]]
        
        # Evaluar solo los top candidatos con OSRM completo
        evaluaciones = []
        for cliente in top_candidatos:
            score = self._evaluar_cliente(cliente, decisiones_otros_agentes)
            evaluaciones.append((cliente.id, score, cliente))
        
        # Ordenar por score descendente
        evaluaciones.sort(key=lambda x: x[1], reverse=True)
        
        if not evaluaciones:
            return None

        # Seleccionar el mejor
        mejor_cliente_id, mejor_score, mejor_cliente = evaluaciones[0]
        
        # Registrar decisión
        decision = DecisionAgente(
            camion_id=self.camion.id,
            cliente_objetivo_id=mejor_cliente_id,
            razonamiento=f"Score: {mejor_score:.2f} | Distancia: {self._calcular_distancia_a(mejor_cliente):.2f}km",
            prioridad_decision=mejor_score,
            distancia_estimada=self._calcular_distancia_a(mejor_cliente),
            beneficio_estimado=mejor_cliente.demanda_kg * mejor_cliente.prioridad
        )
        self.memoria_decisiones.append(decision)
        
        return mejor_cliente_id
    
    def _evaluar_cliente(
        self, 
        cliente: Cliente,
        decisiones_otros_agentes: List[DecisionAgente] = None
    ) -> float:
        """
        Evalúa qué tan conveniente es visitar un cliente
        
        Score más alto = mejor opción
        """
        # 1. Factor de distancia (Calculada con OSRM)
        distancia = self._calcular_distancia_a(cliente, usar_osrm=True)
        max_distancia = 5.0
        score_distancia = pow(max(0, 1 - (distancia / max_distancia)), 3)
        
        # 2. Factor de demanda
        score_demanda = cliente.demanda_kg / self.camion.capacidad_kg
        
        # 3. Factor de prioridad
        score_prioridad = cliente.prioridad / 3.0
        
        # 4. Penalización conflicto
        penalizacion_conflicto = 0.0
        if decisiones_otros_agentes:
            for decision in decisiones_otros_agentes:
                if decision.cliente_objetivo_id == cliente.id:
                    if decision.distancia_estimada < distancia:
                        penalizacion_conflicto = 0.8
                    else:
                        penalizacion_conflicto = 0.4
         
        # 5. Bonus retorno
        bonus_retorno = 0.0
        if self.camion.porcentaje_carga > 80:
            # Usar Haversine para estimación rápida al depot
            dist_depot = self.env._calcular_distancia_haversine(
                cliente.latitud, cliente.longitud,
                self.env.depot_lat, self.env.depot_lon
            )
            if dist_depot < 2.0:
                bonus_retorno = 0.15

        # 6. Lógica de Pasajes
        penalizacion_pasaje = 0.0
        es_pasaje = "Pasaje" in cliente.nombre or "Interior" in cliente.nombre
        if es_pasaje:
            if distancia > 0.15:
                penalizacion_pasaje = 0.15
            else:
                penalizacion_pasaje = -0.05 

        # 7. Lógica de Continuidad de Calle
        bonus_misma_calle = 0.0
        penalizacion_cambio_calle = 0.0
        
        if self.camion.nombre_ultimo_punto:
            nombre_origen = self.camion.nombre_ultimo_punto.lower()
            nombre_destino = cliente.nombre.lower()
            calles_origen = [c.strip() for c in nombre_origen.split(" con ")]
            calles_destino = [c.strip() for c in nombre_destino.split(" con ")]
            hay_calle_comun = any(c in calles_destino for c in calles_origen)
            
            if hay_calle_comun:
                if distancia < 0.5:
                    bonus_misma_calle = 0.8  # Aumentado de 0.5
            else:
                if distancia < 0.15: 
                    penalizacion_cambio_calle = 0.8  # Aumentado de 0.6
                elif distancia < 0.3:
                    penalizacion_cambio_calle = 0.4  # Aumentado de 0.3

        # 8. Factor de Cluster (Proximidad inmediata)
        bonus_cluster = 0.0
        if distancia < 0.03: # 30 metros
            bonus_cluster = 0.6

        score = (
            (self.peso_distancia * 2.0) * score_distancia +
            self.peso_demanda * score_demanda +
            self.peso_prioridad * score_prioridad +
            bonus_retorno +
            bonus_misma_calle +
            bonus_cluster -
            penalizacion_conflicto -
            penalizacion_pasaje -
            penalizacion_cambio_calle
        )
        
        return max(0, score)
    
    def _calcular_distancia_a(self, cliente: Cliente, usar_osrm: bool = True) -> float:
        """
        Calcula distancia REAL (OSRM) o Haversine.
        """
        if usar_osrm:
            try:
                ruta = OSRMService.obtener_ruta(
                    self.camion.latitud, self.camion.longitud,
                    cliente.latitud, cliente.longitud
                )
                if ruta and not ruta.get('es_fallback', False):
                    return ruta['distancia_km']
            except Exception:
                pass

        # Fallback: Haversine con factor de tortuosidad
        # Multiplicamos por 1.4 para estimar la distancia real en calle vs línea recta
        dist_haversine = self.env._calcular_distancia_haversine(
            self.camion.latitud, self.camion.longitud,
            cliente.latitud, cliente.longitud
        )
        return dist_haversine * 1.4
    
    def debe_regresar_depot(self) -> bool:
        """Determina si el camión debe regresar al depósito"""
        # Regresar si:
        # 1. Carga > 90% de capacidad
        # 2. No hay clientes factibles con la capacidad restante
        if self.camion.porcentaje_carga > 90:
            return True
        
        # Buscar si hay algún cliente servible con capacidad restante
        clientes_servibles = [
            c for c in self.env.clientes
            if not c.servido and c.demanda_kg <= self.camion.capacidad_disponible
        ]
        
        return len(clientes_servibles) == 0
    
    def get_estado(self) -> Dict:
        """Obtiene estado actual del agente"""
        return {
            'camion_id': self.camion.id,
            'posicion': {'lat': self.camion.latitud, 'lon': self.camion.longitud},
            'carga_actual_kg': self.camion.carga_actual_kg,
            'capacidad_kg': self.camion.capacidad_kg,
            'porcentaje_carga': self.camion.porcentaje_carga,
            'capacidad_disponible': self.camion.capacidad_disponible,
            'distancia_recorrida_km': self.camion.distancia_recorrida_km,
            'activo': self.camion.activo,
            'decisiones_tomadas': len(self.memoria_decisiones)
        }


class CoordinadorMAS:
    """
    Coordinador del Sistema de Agentes Múltiples
    
    Responsabilidades:
    - Crear y gestionar agentes (camiones)
    - Coordinar decisiones para evitar conflictos
    - Optimizar distribución de trabajo
    - Monitorear rendimiento global
    """
    
    def __init__(self, env: DVRPTWEnv, modelo_ppo_path: str = None):
        self.env = env
        self.modelo_ppo = None
        self.mapa_sectores = {} # Mapa id_cliente -> sector_id
        
        if modelo_ppo_path and PPO:
            try:
                self.modelo_ppo = PPO.load(modelo_ppo_path)
                print(f"Modelo PPO cargado en CoordinadorMAS: {modelo_ppo_path}")
            except Exception as e:
                print(f"Error cargando modelo PPO: {e}")
                
        self.agentes: List[AgenteRecolector] = []
        self._inicializar_agentes()
        self._inicializar_sectores() # Sectorización inicial
        
        # Estadísticas
        self.pasos_totales = 0
        self.conflictos_resueltos = 0
        self.decisiones_cooperativas = 0
    
    def _inicializar_agentes(self):
        """Crea un agente por cada camión en el entorno"""
        for i, camion in enumerate(self.env.camiones):
            # Asignar sector_id preliminar (se confirmará en _inicializar_sectores)
            agente = AgenteRecolector(camion, self.env, self.modelo_ppo, sector_id=i)
            self.agentes.append(agente)

    def _inicializar_sectores(self):
        """Asigna sectores a los clientes usando K-Means simple"""
        if not self.env.clientes:
            return

        print("🧩 Iniciando sectorización K-Means...")
        # Puntos de clientes
        puntos = [(c.latitud, c.longitud) for c in self.env.clientes]
        k = len(self.env.camiones)
        
        # Inicializar centroides aleatorios
        centroides = random.sample(puntos, k)
        
        asignaciones = [-1] * len(puntos)
        
        # Iterar (pocas veces es suficiente para esto)
        for _ in range(10):
            # Asignar puntos al centroide más cercano
            nuevas_asignaciones = []
            clusters = [[] for _ in range(k)]
            
            for i, p in enumerate(puntos):
                distancias = [math.sqrt((p[0]-c[0])**2 + (p[1]-c[1])**2) for c in centroides]
                cluster_idx = distancias.index(min(distancias))
                nuevas_asignaciones.append(cluster_idx)
                clusters[cluster_idx].append(p)
            
            if nuevas_asignaciones == asignaciones:
                break
            asignaciones = nuevas_asignaciones
            
            # Recalcular centroides
            for i in range(k):
                if clusters[i]:
                    lat_mean = sum(p[0] for p in clusters[i]) / len(clusters[i])
                    lon_mean = sum(p[1] for p in clusters[i]) / len(clusters[i])
                    centroides[i] = (lat_mean, lon_mean)
        
        # Guardar asignación en mapa
        self.mapa_sectores = {self.env.clientes[i].id: asignaciones[i] for i in range(len(self.env.clientes))}
        
        # Reporte
        for i in range(k):
            count = asignaciones.count(i)
            print(f"🗺️ Sector {i}: {count} clientes asignados")
    
    def ejecutar_paso_cooperativo(self) -> Tuple[List, Dict]:
        """
        Ejecuta un paso de decisión cooperativa entre todos los agentes
        
        Proceso:
        1. Cada agente propone su próximo movimiento
        2. Se detectan y resuelven conflictos (múltiples agentes al mismo cliente)
        3. Se ejecutan las acciones en el entorno
        4. Se actualiza el estado
        
        Returns:
            Tupla (decisiones_propuestas, info_paso)
        """
        self.pasos_totales += 1
        
        # 1. Recopilar decisiones de todos los agentes
        decisiones_propuestas = []
        clientes_disponibles = [c for c in self.env.clientes if not c.servido]
        
        for agente in self.agentes:
            if not agente.camion.activo:
                print(f"⚠️ Agente {agente.camion.id} inactivo")
                continue
            
            # Verificar si debe regresar al depósito
            if agente.debe_regresar_depot():
                print(f"🔙 Agente {agente.camion.id} decide regresar a depot")
                decision = DecisionAgente(
                    camion_id=agente.camion.id,
                    cliente_objetivo_id=0,  # 0 = depot
                    razonamiento="Capacidad casi llena o sin clientes factibles",
                    prioridad_decision=0.0,
                    distancia_estimada=0.0,
                    beneficio_estimado=0.0
                )
                decisiones_propuestas.append(decision)
            else:
                # Cada agente considera las decisiones de otros
                decisiones_otros = [d for d in decisiones_propuestas if d.camion_id != agente.camion.id]
                
                # --- SECTORIZACIÓN ---
                # Filtrar clientes por sector del agente
                clientes_sector = [
                    c for c in clientes_disponibles 
                    if self.mapa_sectores.get(c.id) == agente.sector_id
                ]
                
                # Si quedan clientes en su sector, priorizarlos estrictamente
                # Si no, ayudar a otros sectores (fallback)
                candidates = clientes_sector if clientes_sector else clientes_disponibles
                
                cliente_id = agente.seleccionar_proximo_cliente(
                    candidates,
                    decisiones_otros
                )
                
                if cliente_id is not None:
                    print(f"✅ Agente {agente.camion.id} seleccionó cliente {cliente_id}")
                    # Usar la última decisión del agente
                    if agente.memoria_decisiones:
                        decisiones_propuestas.append(agente.memoria_decisiones[-1])
                else:
                    print(f"❌ Agente {agente.camion.id} NO seleccionó cliente (None)")
        
        # 2. Detectar y resolver conflictos
        conflictos = self._detectar_conflictos(decisiones_propuestas)
        if conflictos:
            decisiones_propuestas = self._resolver_conflictos(decisiones_propuestas, conflictos)
            self.conflictos_resueltos += len(conflictos)
        
        # 3. Ejecutar acciones en el entorno
        rewards = []
        for decision in decisiones_propuestas:
            # Buscar agente correspondiente
            agente = next(a for a in self.agentes if a.camion.id == decision.camion_id)
            
            # Determinar acción (0=depot, 1-N=clientes)
            action = decision.cliente_objetivo_id
            
            # Ejecutar acción
            try:
                # FIX: Usar step_agent para mover el camión correcto
                obs, reward, done, info = self.env.step_agent(action, decision.camion_id)
                rewards.append(reward)
                
                # VERIFICACIÓN DE ESTADO
                if action > 0:
                    cliente_idx = action - 1
                    if 0 <= cliente_idx < len(self.env.clientes):
                        cliente = self.env.clientes[cliente_idx]
                        if not cliente.servido:
                            print(f"⚠️ ALERTA: Cliente {cliente.id} NO fue marcado como servido tras step_agent!")
                            # Forzar servido para evitar bucle infinito
                            cliente.servido = True
                            self.env.clientes_servidos += 1
            except Exception as e:
                print(f"❌ Error crítico ejecutando acción para agente {decision.camion_id}: {e}")
        
        # 4. Recopilar información
        info_paso = {
            'paso': self.pasos_totales,
            'decisiones': len(decisiones_propuestas),
            'conflictos': len(conflictos) if conflictos else 0,
            'reward_promedio': np.mean(rewards) if rewards else 0.0,
            'clientes_servidos': self.env.clientes_servidos,
            'agentes_activos': sum(1 for a in self.agentes if a.camion.activo)
        }
        
        return decisiones_propuestas, info_paso
    
    def _detectar_conflictos(self, decisiones: List[DecisionAgente]) -> List[Tuple[int, int]]:
        """
        Detecta conflictos: múltiples agentes quieren ir al mismo cliente
        
        Returns:
            Lista de tuplas (cliente_id, [agente_ids])
        """
        cliente_a_agentes = {}
        for decision in decisiones:
            cliente_id = decision.cliente_objetivo_id
            if cliente_id == 0:  # Ignorar depot
                continue
            
            if cliente_id not in cliente_a_agentes:
                cliente_a_agentes[cliente_id] = []
            cliente_a_agentes[cliente_id].append(decision.camion_id)
        
        # Filtrar solo clientes con múltiples agentes
        conflictos = [
            (cliente_id, agentes)
            for cliente_id, agentes in cliente_a_agentes.items()
            if len(agentes) > 1
        ]
        
        return conflictos
    
    def _resolver_conflictos(
        self, 
        decisiones: List[DecisionAgente],
        conflictos: List[Tuple[int, List[int]]]
    ) -> List[DecisionAgente]:
        """
        Resuelve conflictos asignando el cliente al agente más cercano/prioritario
        Los otros agentes deben elegir alternativas
        """
        decisiones_resueltas = []
        agentes_reasignar = set()
        
        for cliente_id, agentes_en_conflicto in conflictos:
            # Buscar decisiones en conflicto
            decisiones_conflicto = [
                d for d in decisiones
                if d.cliente_objetivo_id == cliente_id
            ]
            
            # Ordenar por prioridad (distancia + beneficio)
            decisiones_conflicto.sort(
                key=lambda d: d.distancia_estimada / (d.beneficio_estimado + 1),
                reverse=False  # Menor ratio = mejor
            )
            
            # El primero gana el cliente
            ganador = decisiones_conflicto[0]
            decisiones_resueltas.append(ganador)
            
            # Los demás deben reasignar
            for decision in decisiones_conflicto[1:]:
                agentes_reasignar.add(decision.camion_id)
        
        # Agregar decisiones sin conflicto
        for decision in decisiones:
            if decision not in decisiones_resueltas and decision.camion_id not in agentes_reasignar:
                decisiones_resueltas.append(decision)
        
        # Reasignar agentes en conflicto a alternativas
        for agente_id in agentes_reasignar:
            agente = self.agentes[agente_id]
            clientes_disponibles = [
                c for c in self.env.clientes
                if not c.servido and c.id not in [d.cliente_objetivo_id for d in decisiones_resueltas]
            ]
            
            cliente_alternativo = agente.seleccionar_proximo_cliente(
                clientes_disponibles,
                decisiones_resueltas
            )
            
            if cliente_alternativo is not None and agente.memoria_decisiones:
                decisiones_resueltas.append(agente.memoria_decisiones[-1])
        
        self.decisiones_cooperativas += len(agentes_reasignar)
        
        return decisiones_resueltas
    
    def ejecutar_episodio_completo(self, max_pasos: int = 500, verbose: bool = True) -> Dict:
        """
        Ejecuta un episodio completo con todos los agentes cooperando
        
        Returns:
            Estadísticas del episodio
        """
        self.env.reset()
        
        paso = 0
        total_reward = 0.0
        
        if verbose:
            print("\n" + "="*70)
            print("EJECUTANDO EPISODIO CON SISTEMA DE AGENTES MÚLTIPLES")
            print("="*70)
        
        while paso < max_pasos and self.env.clientes_servidos < self.env.num_clientes:
            _, info_paso = self.ejecutar_paso_cooperativo()
            total_reward += info_paso['reward_promedio']
            
            if verbose and paso % 10 == 0:
                print(f"\nPaso {paso}:")
                print(f"  Clientes servidos: {self.env.clientes_servidos}/{self.env.num_clientes}")
                print(f"  Conflictos: {info_paso['conflictos']}")
                print(f"  Reward promedio: {info_paso['reward_promedio']:.2f}")
            
            paso += 1
        
        # Estadísticas finales
        estadisticas = {
            'pasos_totales': paso,
            'clientes_servidos': self.env.clientes_servidos,
            'total_clientes': self.env.num_clientes,
            'porcentaje_completado': (self.env.clientes_servidos / self.env.num_clientes) * 100,
            'reward_total': total_reward,
            'conflictos_totales': self.conflictos_resueltos,
            'decisiones_cooperativas': self.decisiones_cooperativas,
            'distancia_total_km': sum(a.camion.distancia_recorrida_km for a in self.agentes),
            'agentes': [a.get_estado() for a in self.agentes]
        }
        
        if verbose:
            print("\n" + "="*70)
            print("RESUMEN FINAL DEL EPISODIO")
            print("="*70)
            print(f"Clientes servidos: {estadisticas['clientes_servidos']}/{estadisticas['total_clientes']} "
                  f"({estadisticas['porcentaje_completado']:.1f}%)")
            print(f"Pasos totales: {estadisticas['pasos_totales']}")
            print(f"Reward total: {estadisticas['reward_total']:.2f}")
            print(f"Conflictos resueltos: {estadisticas['conflictos_totales']}")
            print(f"Decisiones cooperativas: {estadisticas['decisiones_cooperativas']}")
            print(f"Distancia total: {estadisticas['distancia_total_km']:.2f} km")
            print(f"\nEstado final de agentes:")
            for agente_info in estadisticas['agentes']:
                print(f"  Camión {agente_info['camion_id']}: "
                      f"{agente_info['distancia_recorrida_km']:.2f}km, "
                      f"Carga final: {agente_info['porcentaje_carga']:.1f}%")
        
        return estadisticas
    
    def get_estadisticas(self) -> Dict:
        """Obtiene estadísticas del coordinador"""
        return {
            'pasos_totales': self.pasos_totales,
            'conflictos_resueltos': self.conflictos_resueltos,
            'decisiones_cooperativas': self.decisiones_cooperativas,
            'num_agentes': len(self.agentes),
            'agentes_activos': sum(1 for a in self.agentes if a.camion.activo)
        }


if __name__ == '__main__':
    """
    Ejemplo de uso del Sistema de Agentes Múltiples
    """
    print("="*70)
    print("SISTEMA DE AGENTES MÚLTIPLES - Recolección Cooperativa de Residuos")
    print("="*70)
    
    # Crear entorno
    env = DVRPTWEnv(
        num_camiones=4,
        capacidad_camion_kg=3500.0,
        max_steps=300,
        seed=42
    )
    
    # Crear coordinador MAS
    coordinador = CoordinadorMAS(env)
    
    # Ejecutar episodio completo
    estadisticas = coordinador.ejecutar_episodio_completo(
        max_pasos=300,
        verbose=True
    )
    
    print("\n" + "="*70)
    print("¡Episodio completado exitosamente!")
    print("="*70)
