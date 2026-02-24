// ============================================================
// SEXTA-FEIRA — Firmware: Reator Arc MK3 (ESP32)
// ============================================================
// Firmware de controle dos 11 LEDs individuais do Reator Arc.
// Cria um servidor web local no ESP32 para receber comandos
// via Python (Sexta-Feira) ou navegador.
//
// Endpoints:
//   GET /modo?v={n}  → Altera a animação (0-7)
//   GET /vel?v={n}   → Altera a velocidade (ms)
//   GET /status      → Retorna o modo ativo
//
// HARDWARE:
//   - ESP32 DevKit
//   - 11 LEDs (Comuns/Alto brilho) ligados individualmente
//   - Pinos: 13, 14, 18, 19, 21, 22, 23, 25, 26, 32, 33
//
// MODOS DE ILUMINAÇÃO (Conforme lógica do Loop):
//   0 → DESLIGADO: Apaga todos os LEDs.
//   1 → FIXO: Todos os LEDs em brilho máximo.
//   2 → PULSAR: Efeito "respiração" (Fade In/Out) em todos os LEDs.
//   3 → GIRAR: Um LED aceso por vez circulando o reator.
//   4 → CONTAR: Preenchimento sequencial dos LEDs com delay.
//   5 → IGNIÇÃO (BOOT): Pisca o centro e ativa o modo FIXO.
//   6 → IGNIÇÃO (LOOP): Ciclo de flash de inicialização.
//   7 → INVERSÃO: LEDs externos girando com o centro pulsando.
//
// SEGURANÇA:
//   ⚠️ O brilho máximo é limitado pela variável 'brilhoMax'.
//   Assegure que os resistores dos LEDs estão adequados para 3.3V.
// ============================================================

#include <WebServer.h>
#include <WiFi.h>

// ============================================================
// CONFIGURAÇÕES (ajuste conforme seu hardware)
// ============================================================

// Credenciais Wi-Fi
const char *ssid = "SEU_WIFI_AQUI";
const char *password = "SUA_SENHA_AQUI";

WebServer server(80);

// --- PINOS ---
int leds[] = {13, 14, 18, 19, 21, 22, 23, 25, 26, 32, 33};
const int numLeds = 11;

int modoAtual = 0;
int velocidade = 50;
int brilhoMax = 255;

// --- FUNÇÕES DE LÓGICA ---
void desligarTudo() {
  for (int i = 0; i < numLeds; i++) {
    analogWrite(leds[i], 0);
    digitalWrite(leds[i], LOW);
  }
}

// --- ENDPOINTS API ---
void handleModoAPI() {
  modoAtual = server.arg("v").toInt();
  if (modoAtual == 0)
    desligarTudo();
  server.send(200, "text/plain", String(modoAtual));
}

void handleVelAPI() {
  velocidade = server.arg("v").toInt();
  server.send(200, "text/plain", String(velocidade));
}

void setup() {
  Serial.begin(115200);
  for (int i = 0; i < numLeds; i++) {
    pinMode(leds[i], OUTPUT);
    digitalWrite(leds[i], LOW);
  }

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  // Rotas para Python
  server.on("/", []() {
    server.send(200, "text/plain", "ARC API Online. Use /modo?v=X ou /vel?v=X");
  });
  server.on("/modo", handleModoAPI);
  server.on("/vel", handleVelAPI);
  server.on("/status",
            []() { server.send(200, "text/plain", String(modoAtual)); });

  server.begin();
  Serial.println("\nARC REACTOR API READY!");
  Serial.println(WiFi.localIP());
}

void loop() {
  server.handleClient();

  if (modoAtual == 0) {
    desligarTudo();
    delay(100);
  } else if (modoAtual == 1) { // FIXO
    for (int i = 0; i < numLeds; i++)
      analogWrite(leds[i], brilhoMax);
  } else if (modoAtual == 2) { // PULSAR
    static float angulo = 0;
    int b = (sin(angulo) * 110) + 140;
    for (int i = 0; i < numLeds; i++)
      analogWrite(leds[i], b);
    angulo += 0.05;
    delay(velocidade / 5);
  } else if (modoAtual == 3) { // GIRAR
    static int p = numLeds - 1;
    for (int i = 1; i < numLeds; i++)
      analogWrite(leds[i], (i == p) ? brilhoMax : 0);
    analogWrite(leds[0], 100);
    p--;
    if (p < 1)
      p = numLeds - 1;
    delay(velocidade);
  } else if (modoAtual == 4) { // CONTAR
    desligarTudo();
    for (int i = numLeds - 1; i >= 1; i--) {
      server.handleClient();
      if (modoAtual != 4)
        break;
      analogWrite(leds[i], brilhoMax);
      delay(velocidade * 2);
    }
    if (modoAtual == 4) {
      analogWrite(leds[0], brilhoMax);
      delay(500);
      desligarTudo();
      delay(200);
    }
  } else if (modoAtual == 5 || modoAtual == 6) { // IGNICAO
    for (int k = 0; k < 3; k++) {
      server.handleClient();
      if (modoAtual == 0)
        break;
      analogWrite(leds[0], brilhoMax);
      delay(100);
      analogWrite(leds[0], 0);
      delay(100);
    }
    for (int i = 0; i < numLeds; i++)
      analogWrite(leds[i], brilhoMax);
    delay(800);
    desligarTudo();
    delay(400);
    if (modoAtual == 5)
      modoAtual = 1;
  } else if (modoAtual == 7) { // INVERSAO
    static int lastModo = 0;
    if (lastModo != 7) {
      for (int k = 0; k < 3; k++) {
        analogWrite(leds[0], brilhoMax);
        delay(80);
        analogWrite(leds[0], 0);
        delay(80);
      }
      lastModo = 7;
    }
    static int p1 = 1;
    static float pulsarCentral = 0;
    int p2 = numLeds - p1;
    for (int i = 1; i < numLeds; i++) {
      if (i == p1 || i == p2)
        analogWrite(leds[i], brilhoMax);
      else
        analogWrite(leds[i], 20);
    }
    int bCentro = (sin(pulsarCentral) * 50) + 150;
    analogWrite(leds[0], bCentro);
    pulsarCentral += 0.2;
    p1++;
    if (p1 >= numLeds)
      p1 = 1;
    delay(velocidade);
  }
}