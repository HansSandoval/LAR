package com.lar.agents;

import jade.core.Agent;
import jade.core.behaviours.TickerBehaviour;
import jade.core.behaviours.CyclicBehaviour;
import jade.lang.acl.ACLMessage;
import jade.domain.DFService;
import jade.domain.FIPAException;
import jade.domain.FIPAAgentManagement.DFAgentDescription;
import jade.domain.FIPAAgentManagement.ServiceDescription;
import okhttp3.MediaType;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.util.concurrent.TimeUnit;

public class CamionAgent extends Agent {

    private final OkHttpClient client = new OkHttpClient.Builder()
        .connectTimeout(30, TimeUnit.SECONDS)
        .writeTimeout(30, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .build();
    private final ObjectMapper mapper = new ObjectMapper();
    public static final MediaType JSON = MediaType.get("application/json; charset=utf-8");
    private String myId;
    private boolean avisadoLleno = false; // Flag para evitar spam de mensajes

    @Override
    protected void setup() {
        // El nombre local del agente será su ID (ej: "camion_1")
        this.myId = getLocalName();
        
        System.out.println("🚛 Camión Digital Twin INICIADO: " + myId);

        // 1. Registrar servicio en las Páginas Amarillas (DF) para que otros me encuentren
        DFAgentDescription dfd = new DFAgentDescription();
        dfd.setName(getAID());
        ServiceDescription sd = new ServiceDescription();
        sd.setType("transporte-residuos");
        sd.setName("camion-recolector");
        dfd.addServices(sd);
        try {
            DFService.register(this, dfd);
        } catch (FIPAException fe) {
            fe.printStackTrace();
        }

        // 2. Comportamiento para recibir mensajes de otros agentes (Comunicación JADE Pura)
        addBehaviour(new CyclicBehaviour(this) {
            public void action() {
                ACLMessage msg = myAgent.receive();
                if (msg != null) {
                    System.out.println("💬 " + myId + " recibió de " 
                        + msg.getSender().getLocalName() + ": " + msg.getContent());
                } else {
                    block();
                }
            }
        });

        // 3. Comportamiento cíclico: Consultar estado cada 2 segundos (más rápido para reaccionar)
        addBehaviour(new TickerBehaviour(this, 2000) {
            @Override
            protected void onTick() {
                consultarEstadoMundo();
            }
        });
    }

    @Override
    protected void takeDown() {
        try {
            DFService.deregister(this);
        } catch (FIPAException fe) {
            fe.printStackTrace();
        }
    }

    private void consultarEstadoMundo() {
        Request request = new Request.Builder()
            .url("http://localhost:8000/bridge/world/state")
            .build();

        try (Response response = client.newCall(request).execute()) {
            if (response.isSuccessful() && response.body() != null) {
                String jsonResponse = response.body().string();
                procesarEstado(jsonResponse);
            } else {
                // System.out.println("❌ " + myId + ": Error HTTP " + response.code());
            }
        } catch (IOException e) {
            // System.out.println("⚠️ " + myId + ": Error de conexión: " + e.getMessage());
        }
    }

    private void procesarEstado(String json) {
        try {
            JsonNode root = mapper.readTree(json);
            JsonNode camiones = root.path("camiones");
            
            if (camiones.has(myId)) {
                JsonNode miEstado = camiones.get(myId);
                double lat = miEstado.path("lat").asDouble();
                double lon = miEstado.path("lon").asDouble();
                int carga = miEstado.path("carga").asInt();
                int capacidad = miEstado.path("capacidad").asInt(1000); // Default 1000 si no viene
                JsonNode ruta = miEstado.path("ruta");
                
                // System.out.println("📍 " + myId + " Pos: [" + lat + ", " + lon + "] | Carga: " + carga);
                
                // LÓGICA DE DECISIÓN DEL AGENTE (CEREBRO)
                // Si no tengo ruta asignada (estoy libre)
                if (ruta.isEmpty()) {
                    // Si estoy lleno (o casi, > 90%), voy a descargar
                    if (carga >= capacidad * 0.9) {
                        // COMUNICACIÓN ENTRE AGENTES: Avisar que me retiro
                        if (!avisadoLleno) {
                            avisarOtrosAgentes("ESTOY_LLENO_VOY_A_VERTEDERO");
                            avisadoLleno = true;
                        }
                        
                        System.out.println("⚠️ " + myId + ": Lleno (" + carga + "/" + capacidad + "). Yendo a vertedero...");
                        enviarAccion("DESCARGAR", "vertedero");
                    } 
                    // Si tengo espacio, pido más trabajo
                    else {
                        avisadoLleno = false; // Reset flag
                        System.out.println("💡 " + myId + ": Libre y con espacio. Solicitando asignación...");
                        enviarAccion("SOLICITAR_RUTA", "zona_asignada");
                    }
                }
                
            }
            
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    // Método auxiliar para enviar mensajes JADE a otros camiones
    private void avisarOtrosAgentes(String contenido) {
        DFAgentDescription template = new DFAgentDescription();
        ServiceDescription sd = new ServiceDescription();
        sd.setType("transporte-residuos");
        template.addServices(sd);
        try {
            DFAgentDescription[] result = DFService.search(this, template);
            ACLMessage msg = new ACLMessage(ACLMessage.INFORM);
            for (int i = 0; i < result.length; ++i) {
                // No enviarme a mí mismo
                if (!result[i].getName().equals(getAID())) {
                    msg.addReceiver(result[i].getName());
                }
            }
            msg.setContent(contenido);
            send(msg);
        } catch (FIPAException fe) {
            fe.printStackTrace();
        }
    }

    private void enviarAccion(String tipoAccion, String destino) {
        try {
            // Construir JSON: { "agent_id": "...", "action_type": "...", "parameters": { "destino": "..." } }
            ObjectNode jsonBody = mapper.createObjectNode();
            jsonBody.put("agent_id", myId);
            jsonBody.put("action_type", tipoAccion);
            
            ObjectNode params = mapper.createObjectNode();
            params.put("destino", destino);
            jsonBody.set("parameters", params);

            RequestBody body = RequestBody.create(jsonBody.toString(), JSON);
            Request request = new Request.Builder()
                .url("http://localhost:8000/bridge/agent/action")
                .post(body)
                .build();

            try (Response response = client.newCall(request).execute()) {
                if (response.isSuccessful()) {
                    System.out.println("✅ " + myId + ": Acción enviada correctamente.");
                } else {
                    System.out.println("❌ " + myId + ": Error enviando acción: " + response.code());
                }
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
