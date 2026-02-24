# ============================================================
# SEXTA-FEIRA — MQTT Publisher (Transmissor de Comandos)
# ============================================================
# Responsável por publicar mensagens no broker Mosquitto,
# permitindo que o Cérebro envie ordens para:
#   - Satélites PC (casa/{comodo}/pc/comando)
#   - ESP32 da máscara (mk3/mascara)
#   - ESP32 do reator (mk3/reator)
#   - Dispositivos futuros (casa/{comodo}/{dispositivo})
#
# Utiliza o protocolo MQTT que é ultra-leve e rápido,
# ideal para IoT e automação residencial.
# ============================================================

import os
import json
import logging
import threading
import paho.mqtt.client as mqtt
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# Configura logging
logger = logging.getLogger("sexta.mqtt")


class MQTTPublisher:
    """
    Cliente MQTT para publicar comandos do Cérebro no Mosquitto.
    
    Thread-safe e com reconexão automática. Mantém uma conexão
    persistente com o broker para publicações rápidas.
    """

    def __init__(
        self,
        host: str = None,
        porta: int = None,
        client_id: str = "sexta_cerebro",
    ):
        """
        Inicializa o publisher MQTT.

        Args:
            host: Endereço do broker Mosquitto (padrão: variável MQTT_HOST).
            porta: Porta do broker (padrão: variável MQTT_PORT ou 1883).
            client_id: Identificador único deste cliente MQTT.
        """
        self.host = host or os.getenv("MQTT_HOST", "localhost")
        self.porta = porta or int(os.getenv("MQTT_PORT", "1883"))
        self.client_id = client_id

        # Cria o cliente MQTT
        self.client = mqtt.Client(
            client_id=self.client_id,
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        )

        # Configura callbacks
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect

        # Flag de conexão
        self._conectado = False
        self._lock = threading.Lock()

        logger.info(
            f"MQTTPublisher configurado → {self.host}:{self.porta}"
        )

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        """
        Callback chamado quando a conexão com o broker é estabelecida.

        Args:
            rc: Código de resultado (0 = sucesso).
        """
        if rc == 0:
            self._conectado = True
            logger.info("✅ Conectado ao broker MQTT.")
        else:
            logger.error(f"❌ Falha ao conectar ao MQTT. Código: {rc}")

    def _on_disconnect(self, client, userdata, flags, rc, properties=None):
        """Callback chamado quando desconecta do broker."""
        self._conectado = False
        if rc != 0:
            logger.warning(f"⚠️ Desconectado do MQTT inesperadamente. RC: {rc}")

    def conectar(self):
        """
        Estabelece conexão com o broker Mosquitto.
        Inicia o loop de rede em uma thread separada.
        """
        try:
            self.client.connect(self.host, self.porta, keepalive=60)
            self.client.loop_start()  # Thread de background para manter conexão
            logger.info(f"Conectando ao MQTT em {self.host}:{self.porta}...")
        except Exception as e:
            logger.error(f"Erro ao conectar ao MQTT: {e}")

    def desconectar(self):
        """Encerra a conexão com o broker de forma limpa."""
        self.client.loop_stop()
        self.client.disconnect()
        logger.info("Desconectado do MQTT.")

    def publicar(self, topico: str, payload: dict, qos: int = 1) -> bool:
        """
        Publica uma mensagem JSON em um tópico MQTT.

        Args:
            topico: Tópico de destino (ex: "casa/sala/pc/comando").
            payload: Dicionário que será serializado como JSON.
            qos: Quality of Service (0=fire-and-forget, 1=at-least-once).

        Returns:
            True se a mensagem foi publicada com sucesso.
        """
        with self._lock:
            try:
                mensagem = json.dumps(payload, ensure_ascii=False)
                resultado = self.client.publish(topico, mensagem, qos=qos)

                if resultado.rc == mqtt.MQTT_ERR_SUCCESS:
                    logger.info(f"📡 MQTT → {topico}: {mensagem}")
                    return True
                else:
                    logger.error(
                        f"Falha ao publicar no MQTT. RC: {resultado.rc}"
                    )
                    return False

            except Exception as e:
                logger.error(f"Erro ao publicar MQTT: {e}")
                return False

    @property
    def esta_conectado(self) -> bool:
        """Retorna se o cliente está conectado ao broker."""
        return self._conectado
