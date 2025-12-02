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
        num_camiones=1,
        capacidad_camion_kg=3500,
        clientes=None, # Generará aleatorios
        depot_lat=-20.2666,
        depot_lon=-70.1300,
        usar_routing_real=False,
        modo_marl=True
    )
    
    # 2. Verificar que el entorno cumple con la API de Gym
    print(" Verificando entorno...")
    check_env(env)
    print("Entorno verificado correctamente.")
    
    # 3. Crear modelo PPO
    # MlpPolicy es adecuado para vectores de características (no imágenes)
    model = PPO(
        "MlpPolicy", 
        env, 
        verbose=1,
        learning_rate=0.0003,
        n_steps=2048,
        batch_size=64,
        gamma=0.99
    )
    
    # 4. Entrenar (Pocos pasos solo para demostración/inicialización)
    # En un caso real, esto serían 100,000+ pasos
    print("Entrenando modelo (esto puede tardar unos segundos)...")
    model.learn(total_timesteps=5000)
    
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
