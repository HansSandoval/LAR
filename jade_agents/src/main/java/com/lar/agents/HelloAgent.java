package com.lar.agents;

import jade.core.Agent;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.Response;
import java.io.IOException;

public class HelloAgent extends Agent {
    
    private final OkHttpClient client = new OkHttpClient();

    @Override
    protected void setup() {
        System.out.println("------------------------------------------------");
        System.out.println("🤖 Agente " + getLocalName() + " INICIADO");
        
        // Intentar conectar con Python
        conectarConPython();
        
        System.out.println("------------------------------------------------");
        // No matamos al agente todavía para ver el resultado
        // doDelete(); 
    }

    private void conectarConPython() {
        System.out.println("📡 Intentando contactar a FastAPI (Python)...");
        
        Request request = new Request.Builder()
            .url("http://localhost:8000/bridge/ping")
            .build();

        try (Response response = client.newCall(request).execute()) {
            if (response.isSuccessful() && response.body() != null) {
                String respuesta = response.body().string();
                System.out.println("✅ RESPUESTA DE PYTHON: " + respuesta);
            } else {
                System.out.println("❌ Error: Python respondió con código " + response.code());
            }
        } catch (IOException e) {
            System.out.println("❌ FALLO DE CONEXIÓN: ¿Está corriendo run_server.py?");
            System.out.println("   Error: " + e.getMessage());
        }
    }
}
