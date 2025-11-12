"""
Sistema de Agentes Múltiples (MAS) para Recolección de Residuos
Camiones cooperativos que toman decisiones inteligentes basadas en predicciones LSTM
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
from .dvrptw_env import DVRPTWEnv, Cliente, Camion


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
    
    def __init__(self, camion: Camion, env: DVRPTWEnv):
        self.camion = camion
        self.env = env
        self.memoria_decisiones: List[DecisionAgente] = []
        
        # Parámetros de decisión
        self.peso_distancia = 0.4
        self.peso_demanda = 0.3
        self.peso_prioridad = 0.3
        
    def seleccionar_proximo_cliente(
        self, 
        clientes_disponibles: List[Cliente],
        decisiones_otros_agentes: List[DecisionAgente] = None
    ) -> Optional[int]:
        """
        Selecciona el próximo cliente a visitar de forma inteligente
        
        Criterios:
        1. Proximidad geográfica (minimizar distancia)
        2. Demanda de residuos (priorizar alta demanda)
        3. Prioridad del cliente (urgencia)
        4. Capacidad disponible del camión
        5. Evitar conflictos con otros agentes
        
        Returns:
            ID del cliente seleccionado o None si debe regresar al depósito
        """
        if not clientes_disponibles:
            return None
        
        # Filtrar clientes ya servidos
        clientes_no_servidos = [c for c in clientes_disponibles if not c.servido]
        
        if not clientes_no_servidos:
            return None
        
        # Filtrar clientes que exceden capacidad
        clientes_factibles = [
            c for c in clientes_no_servidos 
            if c.demanda_kg <= self.camion.capacidad_disponible
        ]
        
        if not clientes_factibles:
            # Si no hay clientes factibles, regresar al depósito
            return 0
        
        # Evaluar cada cliente
        evaluaciones = []
        for cliente in clientes_factibles:
            score = self._evaluar_cliente(cliente, decisiones_otros_agentes)
            evaluaciones.append((cliente.id, score, cliente))
        
        # Ordenar por score descendente
        evaluaciones.sort(key=lambda x: x[1], reverse=True)
        
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
        
        return mejor_cliente_id + 1  # +1 porque acción 0 es depot
    
    def _evaluar_cliente(
        self, 
        cliente: Cliente,
        decisiones_otros_agentes: List[DecisionAgente] = None
    ) -> float:
        """
        Evalúa qué tan conveniente es visitar un cliente
        
        Score más alto = mejor opción
        """
        # 1. Factor de distancia (invertido: menor distancia = mejor)
        distancia = self._calcular_distancia_a(cliente)
        max_distancia = 10.0  # km (normalización)
        score_distancia = max(0, 1 - (distancia / max_distancia))
        
        # 2. Factor de demanda (normalizado)
        score_demanda = cliente.demanda_kg / self.camion.capacidad_kg
        
        # 3. Factor de prioridad (normalizado)
        score_prioridad = cliente.prioridad / 3.0
        
        # 4. Penalización si otro agente ya lo tiene como objetivo
        penalizacion_conflicto = 0.0
        if decisiones_otros_agentes:
            for decision in decisiones_otros_agentes:
                if decision.cliente_objetivo_id == cliente.id:
                    # Comparar prioridades: si el otro agente está más cerca, penalizar más
                    if decision.distancia_estimada < distancia:
                        penalizacion_conflicto = 0.5
                    else:
                        penalizacion_conflicto = 0.2
        
        # 5. Bonus si el camión está casi lleno y el cliente está cerca del depósito
        bonus_retorno = 0.0
        if self.camion.porcentaje_carga > 80:
            distancia_cliente_depot = self.env._calcular_distancia(
                cliente.latitud, cliente.longitud,
                self.env.depot_lat, self.env.depot_lon
            )
            if distancia_cliente_depot < 2.0:  # Muy cerca del depósito
                bonus_retorno = 0.15
        
        # Calcular score ponderado
        score = (
            self.peso_distancia * score_distancia +
            self.peso_demanda * score_demanda +
            self.peso_prioridad * score_prioridad +
            bonus_retorno -
            penalizacion_conflicto
        )
        
        return max(0, score)  # Score no puede ser negativo
    
    def _calcular_distancia_a(self, cliente: Cliente) -> float:
        """Calcula distancia desde posición actual del camión al cliente"""
        return self.env._calcular_distancia(
            self.camion.latitud, self.camion.longitud,
            cliente.latitud, cliente.longitud
        )
    
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
    
    def __init__(self, env: DVRPTWEnv):
        self.env = env
        self.agentes: List[AgenteRecolector] = []
        self._inicializar_agentes()
        
        # Estadísticas
        self.pasos_totales = 0
        self.conflictos_resueltos = 0
        self.decisiones_cooperativas = 0
    
    def _inicializar_agentes(self):
        """Crea un agente por cada camión en el entorno"""
        for camion in self.env.camiones:
            agente = AgenteRecolector(camion, self.env)
            self.agentes.append(agente)
    
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
                continue
            
            # Verificar si debe regresar al depósito
            if agente.debe_regresar_depot():
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
                
                cliente_id = agente.seleccionar_proximo_cliente(
                    clientes_disponibles,
                    decisiones_otros
                )
                
                if cliente_id is not None:
                    # Usar la última decisión del agente
                    if agente.memoria_decisiones:
                        decisiones_propuestas.append(agente.memoria_decisiones[-1])
        
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
            if decision.cliente_objetivo_id == 0:
                action = 0
            else:
                action = decision.cliente_objetivo_id + 1
            
            # Ejecutar acción
            obs, reward, done, info = self.env.step(action)
            rewards.append(reward)
        
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
