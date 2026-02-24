# ============================================================
# SEXTA-FEIRA — Plugin: Máscara MK3 (ESP32)
# ============================================================
# Controla a máscara física do capacete da armadura MK3.
# Comunica-se diretamente com o ESP32 via HTTP local.
#
# Ações disponíveis:
#   - abrir  → Abre a máscara do capacete
#   - fechar → Fecha a máscara do capacete
#
# O ESP32 roda um servidor web local que aceita requisições GET:
#   GET http://{IP_ESP32}/abrir
#   GET http://{IP_ESP32}/fechar
# ============================================================

import os
import time
import logging
import requests
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# Configura logging
logger = logging.getLogger("sexta.plugin.mascara")

# IP do ESP32 da máscara (configurável via .env)
IP_ESP32 = os.getenv("IP_ESP32_MASCARA", "http://192.168.0.117")


def _enviar_comando_mascara(acao: str) -> bool:
    """
    Envia um comando HTTP GET para o ESP32 da máscara.

    Args:
        acao: Ação a ser executada ("abrir" ou "fechar").

    Returns:
        True se o comando foi enviado com sucesso, False caso contrário.
    """
    try:
        url = f"{IP_ESP32}/{acao}"
        requests.get(url, timeout=2)
        logger.info(f"Comando enviado para máscara: {acao}")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Falha ao comunicar com a máscara: {e}")
        return False


def _handler_controlar_mascara(argumentos: dict) -> str:
    """
    Handler do plugin: controla abertura/fechamento da máscara.

    Args:
        argumentos: {"acao": "abrir" | "fechar"}

    Returns:
        Texto para a Sexta-Feira falar.
    """
    acao = argumentos.get("acao", "abrir")
    sucesso = _enviar_comando_mascara(acao)

    if sucesso:
        estado = "aberta" if acao == "abrir" else "fechada"
        return f"Entendido. Máscara {estado}."
    else:
        return "Sem conexão com a máscara. Verifique o ESP32."


def _handler_protocolo_acordar(argumentos: dict) -> str:
    """
    Handler do plugin: protocolo de ativação completa da armadura.
    Liga o reator e abre a máscara em sequência.

    Args:
        argumentos: {} (não recebe argumentos)

    Returns:
        Texto para a Sexta-Feira falar.
    """
    ip_reator = os.getenv("IP_ESP32_REATOR", "http://192.168.0.109")

    # Passo 1: Liga o reator no modo 5 (padrão de ativação)
    try:
        requests.get(f"{ip_reator}/modo?v=5", timeout=2)
        requests.get(f"{ip_reator}/vel?v=30", timeout=2)
        logger.info("Reator ativado no modo 5.")
    except Exception as e:
        logger.error(f"Falha ao ligar reator: {e}")

    time.sleep(2)

    # Passo 2: Abre a máscara
    _enviar_comando_mascara("abrir")

    return "Armadura ativada e pronta, chefe."


def registrar(gerenciador):
    """
    Função de registro automático chamada pelo sistema de plugins.
    Registra as ferramentas de controle da máscara MK3.

    Args:
        gerenciador: Instância do GerenciadorPlugins.
    """
    # Ferramenta: Controlar máscara (abrir/fechar)
    gerenciador.registrar_plugin(
        nome="controlar_mascara",
        descricao=(
            "Abre ou fecha a máscara FÍSICA do capacete. "
            "NÃO use para fechar programas."
        ),
        parametros={
            "type": "object",
            "properties": {
                "acao": {
                    "type": "string",
                    "enum": ["abrir", "fechar"],
                    "description": "Ação: 'abrir' ou 'fechar' a máscara."
                }
            },
            "required": ["acao"],
        },
        handler=_handler_controlar_mascara,
    )

    # Ferramenta: Protocolo de ativação da armadura
    gerenciador.registrar_plugin(
        nome="protocolo_acordar_armadura",
        descricao="Acorda e liga a armadura MK3.",
        handler=_handler_protocolo_acordar,
    )

    logger.info("Plugins da Máscara MK3 registrados.")
