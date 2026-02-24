// ============================================================
// SEXTA-FEIRA — Firmware: Máscara MK3 (ESP32)
// ============================================================
// Controle sincronizado de servos para abertura da faceplate.
// Utiliza a biblioteca ServoEasing para movimentos suaves e
// naturais (Cubic In/Out), evitando trancos no mecanismo.
//
// Endpoints API:
//   GET /abrir   → Executa sequência de abertura sincronizada.
//   GET /fechar  → Executa sequência de fechamento.
//   GET /status  → Retorna 1 (aberto) ou 0 (fechado).
//
// HARDWARE:
//   - ESP32 DevKit.
//   - Servo Topo (GPIO 18) | Servo Base (GPIO 19).
//   - Botão Físico (GPIO 13) com resistor interno PULLUP.
//
// LÓGICA DE ENERGIA:
//   ⚠️ O sistema desliga (detach) os servos ao fechar para
//   evitar ruído e aquecimento. Quando aberta, os servos
//   permanecem ativos para sustentar o peso da faceplate.
// ============================================================

#include <Arduino.h>
#define USE_ESP32_SERVO_LIB
#include <ESP32Servo.h>
#include <ServoEasing.hpp>
#include <WebServer.h>
#include <WiFi.h>

// ============================================================
// CONFIGURAÇÕES (ajustei conforme meu hardware)
// ============================================================

const char *wifi_ssid = "SEU_WIFI_AQUI";
const char *wifi_password = "SUA_SENHA_AQUI";
WebServer server(80);

ServoEasing servoTop;    // Pino 18
ServoEasing servoBottom; // Pino 19

const int buttonPin = 13;
int location = 0;

// ÂNGULOS CALIBRADOS
int top_closed = 180;
int top_open = 80;
int bottom_closed = 60;
int bottom_open = 0;

void moverSincronizado(int t_angle, int b_angle, int novaLoc) {
  if (!servoTop.attached())
    servoTop.attach(18);
  if (!servoBottom.attached())
    servoBottom.attach(19);

  servoTop.setEasingType(EASE_CUBIC_IN_OUT);
  servoBottom.setEasingType(EASE_CUBIC_IN_OUT);

  servoTop.setEaseTo(t_angle);
  servoBottom.setEaseTo(b_angle);

  setSpeedForAllServos(190);
  updateAllServos();
  synchronizeAllServosStartAndWaitForAllServosToStop();

  location = novaLoc;

  if (location == 0) {
    delay(200);
    servoTop.detach();
    servoBottom.detach();
  }
  // Aberto (location 1) mantém os servos ligados para segurar o peso
}

void abrir() { moverSincronizado(top_open, bottom_open, 1); }
void fechar() { moverSincronizado(top_closed, bottom_closed, 0); }

// --- ENDPOINTS DA API ---

void handleRoot() {
  server.send(200, "text/plain",
              "Sistema Mozzie Online. Use /abrir, /fechar ou /status");
}

void setup() {
  Serial.begin(115200);

  ESP32PWM::allocateTimer(0);
  ESP32PWM::allocateTimer(1);
  ESP32PWM::allocateTimer(2);
  ESP32PWM::allocateTimer(3);

  pinMode(buttonPin, INPUT_PULLUP);

  moverSincronizado(top_closed, bottom_closed, 0);

  WiFi.begin(wifi_ssid, wifi_password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  // Rotas para em Python
  server.on("/", handleRoot);
  server.on("/abrir", []() {
    abrir();
    server.send(200, "text/plain", "1"); // Retorna 1 (Aberto)
  });
  server.on("/fechar", []() {
    fechar();
    server.send(200, "text/plain", "0"); // Retorna 0 (Fechado)
  });
  server.on("/status",
            []() { server.send(200, "text/plain", String(location)); });

  server.begin();
  Serial.println("\nAPI Mozzie Pronta!");
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());
}

void loop() {
  server.handleClient();

  if (digitalRead(buttonPin) == LOW) {
    if (location == 0)
      abrir();
    else
      fechar();
    while (digitalRead(buttonPin) == LOW)
      delay(10);
  }
}