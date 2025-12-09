package com.lar;

import jade.core.Profile;
import jade.core.ProfileImpl;
import jade.core.Runtime;
import jade.wrapper.AgentController;
import jade.wrapper.ContainerController;

public class JadeLauncher {
    public static void main(String[] args) {
        System.out.println("Iniciando JADE...");

        // 1. Obtener la instancia del Runtime de JADE
        Runtime rt = Runtime.instance();

        // 2. Configurar el perfil
        Profile p = new ProfileImpl();
        p.setParameter(Profile.MAIN_HOST, "localhost");
        p.setParameter(Profile.GUI, "true");

        // 3. Crear el contenedor principal
        ContainerController cc = rt.createMainContainer(p);

        try {
            // Iniciar Agente de Prueba (HelloAgent)
            AgentController hello = cc.createNewAgent("test_agent", "com.lar.agents.HelloAgent", null);
            hello.start();

            // Iniciar 3 Agentes Camión (Digital Twins)
            for (int i = 1; i <= 3; i++) {
                String agentName = "camion_" + i;
                AgentController camion = cc.createNewAgent(agentName, "com.lar.agents.CamionAgent", null);
                camion.start();
                System.out.println("🚛 Agente lanzado: " + agentName);
            }
            
            System.out.println("✅ Todos los agentes lanzados exitosamente.");
            
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
