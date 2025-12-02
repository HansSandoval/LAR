import os
import numpy as np
from stable_baselines3 import PPO
from stable_baselines3.common.env_checker import check_env
from gestion_rutas.vrp.dvrptw_env import DVRPTWEnv

def entrenar_agente():
    print("🚀 Iniciando entrenamiento de agente PPO para DVRPTW...")
    
    # 1. Configurar entorno en modo MARL (observación fija)
    # Usamos usar_routing_real=False para que el entrenamiento sea rápido (Haversine)
    env = DVRPTWEnv(
        num_camiones=3, # Simulación real con 3 camiones
        capacidad_camion_kg=3500,
        clientes=None, # Generará aleatorios
        depot_lat=-20.2666,
        depot_lon=-70.1300,
        usar_routing_real=False,
        modo_marl=True
    )
    
    # 2. Verificar que el entorno cumple con la API de Gym
    print("🔍 Verificando entorno...")
    check_env(env)
    print("✅ Entorno verificado correctamente.")
    
    # 3. Crear modelo PPO
    # MlpPolicy es adecuado para vectores de características (no imágenes)
    # MEJORA: Red neuronal más profunda [256, 256] y coeficiente de entropía para exploración
    policy_kwargs = dict(net_arch=[256, 256])
    
    model = PPO(
        "MlpPolicy", 
        env, 
        verbose=1,
        learning_rate=0.0003,
        n_steps=2048,
        batch_size=128,
        gamma=0.99,
        ent_coef=0.01, # Fomenta la exploración
        policy_kwargs=policy_kwargs
    )
    
    # 4. Entrenar (Aumentado a 300,000 pasos para convergencia robusta)
    print("🏋️ Entrenando modelo (esto tomará unos minutos)...")
    model.learn(total_timesteps=300000)
    
    # 5. Guardar modelo
    save_path = os.path.join("gestion_rutas", "vrp", "modelo_ppo_vrp")
    model.save(save_path)
    print(f"💾 Modelo guardado en: {save_path}.zip")
    
    # 6. Probar modelo
    print("\n🧪 Probando modelo entrenado...")
    obs, _ = env.reset()
    for i in range(10):
        action, _states = model.predict(obs, deterministic=True)
        obs, reward, done, truncated, info = env.step(action)
        print(f"   Paso {i+1}: Acción {action} -> Reward {reward:.2f}")
        if done:
            break
            
    print("🏁 Entrenamiento finalizado exitosamente.")

if __name__ == "__main__":
    entrenar_agente()
