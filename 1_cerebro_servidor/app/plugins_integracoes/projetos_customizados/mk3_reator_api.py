# ============================================================
# SEXTA-FEIRA — Plugin: Reator Arc MK3 (ESP32)
# ============================================================
# Controla o reator arc da armadura MK3 via ESP32.
# O reator possui múltiplos modos de iluminação LED.
#
# O ESP32 roda um servidor web local que aceita:
#   GET http://{IP_ESP32}/modo?v={numero_modo}
#   GET http://{IP_ESP32}/vel?v={velocidade}
#
# Modos conhecidos:
#   0  → Desligado
#   1-4 → Modos de cor estáticos
#   5  → Modo padrão da armadura (azul pulsante)
#   6+ → Modos especiais (vermelho, arco-íris, etc.)
#
# NOTA DE SEGURANÇA: A lógica de limite de brilho e proteção
# visual fica hardcoded no firmware C++ do ESP32, garantindo
# segurança independentemente do que a IA enviar.
# ============================================================

import os
import logging
import requests
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# Configura logging
logger = logging.getLogger("sexta.plugin.reator")

# IP do ESP32 do reator (configurável via .env)
IP_ARC = os.getenv("IP_ESP32_REATOR", "http://192.168.0.109").strip()


def _enviar_comando_reator(modo: int, velocidade: int = None) -> bool:
    """
    Envia comandos HTTP GET para o ESP32 do reator arc.

    Args:
        modo: Número do modo de iluminação (0 = desligado).
        velocidade: Velocidade da animação (opcional).

    Returns:
        True se o comando foi enviado com sucesso, False caso contrário.
    """
    try:
        # Envia o modo
        requests.get(f"{IP_ARC}/modo?v={modo}", timeout=2)
        logger.info(f"Reator: modo {modo} ativado.")

        # Envia velocidade se especificada
        if velocidade is not None:
            requests.get(f"{IP_ARC}/vel?v={velocidade}", timeout=2)
            logger.info(f"Reator: velocidade ajustada para {velocidade}.")

        return True

    except requests.exceptions.RequestException as e:
        logger.error(f"Falha ao comunicar com o reator: {e}")
        return False


def _handler_controlar_reator(argumentos: dict) -> str:
    """
    Handler do plugin: controla o modo e velocidade do reator.

    Args:
        argumentos: {"modo": string/int, "velocidade": string/int (opcional)}

    Returns:
        Texto para a Sexta-Feira falar.
    """
    # Pega o valor (seja string ou número) e força para inteiro
    modo_raw = argumentos.get("modo", 0)
    modo = int(modo_raw)
    
    # Faz o mesmo para a velocidade, mas apenas se ela existir
    velocidade_raw = argumentos.get("velocidade", None)
    velocidade = int(velocidade_raw) if velocidade_raw is not None else None

    sucesso = _enviar_comando_reator(modo, velocidade)

    if sucesso:
        if modo == 0:
            return "Reator desligado."
        else:
            return f"Reator no modo {modo}."
    else:
        return "Sem conexão com o reator. Verifique o ESP32."


def registrar(gerenciador):
    """
    Função de registro automático chamada pelo sistema de plugins.
    Registra as ferramentas de controle do reator arc MK3.
    """
    gerenciador.registrar_plugin(
        nome="controlar_reator",
        descricao="Controla o reator arc da armadura. REGRA: Se o usuário pedir para 'ligar' ou 'ativar', assuma AUTOMATICAMENTE o modo '5'. Se pedir para 'desligar' ou 'desativar', assuma o modo '0'.",
        parametros={
            "type": "object",
            "properties": {
                "modo": {
                    "type": "string",
                    "description": "Obrigatório. Número do modo. Use '5' para ligar/ativar e '0' para desligar."
                },
                "velocidade": {
                    "type": "string",
                    "description": "Velocidade da animação em texto (opcional)."
                },
            },
            "required": ["modo"],
        },
        handler=_handler_controlar_reator,
    )

    logger.info("Plugin do Reator Arc MK3 registrado.")
