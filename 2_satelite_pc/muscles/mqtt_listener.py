# ============================================================
# SEXTA-FEIRA — MQTT Listener (Orelha de Rede do Satélite)
# ============================================================
# Fica inscrito no broker MQTT aguardando comandos do Cérebro.
# Quando recebe uma mensagem, despacha para o módulo correto.
#
# Tópicos inscritos:
#   casa/{NOME_COMODO}/pc/comando → Comandos de OS/mídia/volume
#
# Payload esperado (JSON):
#   {"acao": "abrir_programa", "dados": {"nome_programa": "chrome"}}
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
logger = logging.getLogger("sexta.mqtt_listener")


class MQTTListener:
    """
    Listener MQTT do satélite PC.
    
    Inscreve-se nos tópicos relevantes e despacha comandos
    recebidos para os managers de sistema e mídia.
    """

    def __init__(
        self,
        host: str = None,
        porta: int = None,
        nome_comodo: str = None,
        callback_comando: callable = None,
    ):
        """
        Inicializa o listener MQTT.

        Args:
            host: Endereço do broker Mosquitto.
            porta: Porta do broker (padrão: 1883).
            nome_comodo: Nome do cômodo deste PC (ex: "escritorio").
            callback_comando: Função chamada quando um comando é recebido.
                             Recebe (acao: str, dados: dict).
        """
        self.host = host or os.getenv("MQTT_HOST", "localhost")
        self.porta = porta or int(os.getenv("MQTT_PORT", "1883"))
        self.nome_comodo = nome_comodo or os.getenv("NOME_COMODO", "escritorio")
        self.callback_comando = callback_comando

        # Tópico no qual este satélite escuta
        self.topico = f"casa/{self.nome_comodo}/pc/comando"

        # Client ID único baseado no cômodo
        nome_dispositivo = os.getenv("NOME_DISPOSITIVO", "pc")
        client_id = f"satelite_{self.nome_comodo}_{nome_dispositivo}"

        # Cria o cliente MQTT
        self.client = mqtt.Client(
            client_id=client_id,
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        )

        # Configura callbacks
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect

        logger.info(
            f"MQTTListener configurado → {self.host}:{self.porta} "
            f"| Tópico: {self.topico}"
        )

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        """Callback de conexão: inscreve-se no tópico do cômodo."""
        if rc == 0:
            logger.info(f"✅ Conectado ao MQTT. Inscrito em: {self.topico}")
            # Inscreve-se no tópico deste cômodo
            self.client.subscribe(self.topico)
            # Inscreve-se também no tópico broadcast (para todos os PCs)
            self.client.subscribe("casa/todos/pc/comando")
        else:
            logger.error(f"❌ Falha na conexão MQTT. RC: {rc}")

    def _on_disconnect(self, client, userdata, flags, rc, properties=None):
        """Callback de desconexão."""
        if rc != 0:
            logger.warning(f"⚠️ Desconectado do MQTT: RC={rc}")

    def _on_message(self, client, userdata, msg):
        """
        Callback quando uma mensagem MQTT é recebida.
        Parseia o JSON e despacha para o callback de comando.

        Args:
            msg: Mensagem MQTT recebida.
        """
        try:
            # Decodifica o payload JSON
            payload = json.loads(msg.payload.decode("utf-8"))
            acao = payload.get("acao", "")
            dados = payload.get("dados", {})

            logger.info(f"📡 Comando MQTT recebido: {acao} | Dados: {dados}")

            # Despacha para o callback
            if self.callback_comando:
                self.callback_comando(acao, dados)
            else:
                logger.warning("Nenhum callback de comando configurado.")

        except json.JSONDecodeError as e:
            logger.error(f"Payload MQTT inválido: {e}")
        except Exception as e:
            logger.error(f"Erro ao processar mensagem MQTT: {e}")

    def conectar(self):
        """
        Conecta ao broker MQTT e inicia o loop de escuta.
        Thread-safe — o loop roda em background.
        """
        try:
            self.client.connect(self.host, self.porta, keepalive=60)
            self.client.loop_start()
            logger.info(f"Conectando ao MQTT em {self.host}:{self.porta}...")
        except Exception as e:
            logger.error(f"Erro ao conectar ao MQTT: {e}")

    def desconectar(self):
        """Encerra a conexão MQTT de forma limpa."""
        self.client.loop_stop()
        self.client.disconnect()
        logger.info("MQTTListener desconectado.")
