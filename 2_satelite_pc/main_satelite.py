# ============================================================
# SEXTA-FEIRA — Satélite PC (Ponto de Entrada Principal)
# ============================================================
# Este é o executável que roda em cada PC da casa.
# Ele conecta todos os módulos do satélite:
#   - HUD (interface visual estilo Tony Stark)
#   - Listener (microfone → envia áudio ao Cérebro)
#   - Speaker (reproduz áudio MP3 da resposta)
#   - MQTT Listener (recebe comandos do Cérebro)
#   - System Manager (executa ações no SO)
#   - Media Manager (controla YouTube e mídia)
#
# Uso:
#   python main_satelite.py          (roda com terminal)
#   pythonw main_satelite.py         (roda sem terminal)
#   SextaFeira_Satelite.exe          (versão compilada)
#
# O satélite é leve — toda a inteligência fica no Cérebro.
# Ele apenas escuta → envia → recebe → executa.
# ============================================================

import os
import sys
import logging
import threading
import tkinter as tk
from dotenv import load_dotenv

# Carrega variáveis de ambiente locais do satélite
load_dotenv()

# Configura logging detalhado
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-20s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("sexta.satelite")

# Importa módulos internos do satélite
from ui.hud_60fps import SextaFeiraHUD
from senses.listener import Listener
from senses.speaker import Speaker
from muscles.mqtt_listener import MQTTListener
from muscles.sys_manager import (
    abrir_programa,
    gerenciar_janelas,
    controle_volume,
    escrever_txt,
    ler_txt,
    listar_arquivos,
)
from muscles.media_manager import tocar_youtube, controle_midia


# ============================================================
# ESTADO GLOBAL DA IA (compartilhado entre threads)
# ============================================================
estado_ia = "idle"
_estado_lock = threading.Lock()


def obter_estado() -> str:
    """Retorna o estado atual da IA (thread-safe)."""
    with _estado_lock:
        return estado_ia


def definir_estado(novo_estado: str):
    """Define o estado da IA (thread-safe)."""
    global estado_ia
    with _estado_lock:
        estado_ia = novo_estado


# ============================================================
# DESPACHADOR DE COMANDOS MQTT
# ============================================================
# Instância global do speaker (inicializada no main)
speaker: Speaker = None


def despachar_comando_mqtt(acao: str, dados: dict):
    """
    Recebe comandos do MQTT e despacha para o módulo correto.
    Esta função é chamada pelo MQTTListener quando chega uma mensagem.

    Args:
        acao: Nome da ação a executar.
        dados: Dicionário com dados adicionais.
    """
    logger.info(f"Despachando comando: {acao} → {dados}")

    try:
        if acao == "abrir_programa":
            abrir_programa(dados.get("nome_programa", ""))

        elif acao == "gerenciar_janelas":
            gerenciar_janelas(
                dados.get("acao", "minimizar_tudo"),
                dados.get("nome_programa", ""),
            )

        elif acao == "tocar_youtube":
            tocar_youtube(dados.get("termo_pesquisa", ""))

        elif acao == "controle_midia":
            controle_midia(dados.get("acao", "play_pause"))

        elif acao == "controle_volume":
            controle_volume(
                dados.get("alvo", "pc"),
                dados.get("acao", "aumentar"),
            )

        elif acao == "escrever_txt":
            escrever_txt(
                dados.get("nome_arquivo", "anotacoes.txt"),
                dados.get("conteudo", ""),
            )

        elif acao == "ler_txt":
            conteudo = ler_txt(dados.get("nome_arquivo", ""))
            logger.info(f"Conteúdo do arquivo: {conteudo}")

        elif acao == "listar_arquivos":
            arquivos = listar_arquivos()
            logger.info(f"Arquivos encontrados: {arquivos}")

        else:
            logger.warning(f"Ação desconhecida: {acao}")

    except Exception as e:
        logger.error(f"Erro ao despachar comando '{acao}': {e}")


# ============================================================
# CALLBACK DE RESPOSTA DO CÉREBRO
# ============================================================

def processar_resposta_cerebro(resposta: dict):
    """
    Processa a resposta recebida do Cérebro Central.
    Toca o áudio e atualiza o estado da IA.

    Args:
        resposta: Dicionário com "audio_bytes", "resposta_texto" e "acoes".
    """
    global speaker

    audio_bytes = resposta.get("audio_bytes")
    texto = resposta.get("resposta_texto", "")

    if texto:
        logger.info(f"Sexta-Feira: {texto}")

    # Reproduz o áudio de resposta
    if audio_bytes and speaker:
        definir_estado("falando")
        speaker.falar_bytes(audio_bytes)
        definir_estado("idle")


# ============================================================
# PONTO DE ENTRADA PRINCIPAL
# ============================================================

def main():
    """
    Inicializa todos os componentes do satélite e inicia o loop principal.
    """
    global speaker

    logger.info("=" * 60)
    logger.info("💻 SEXTA-FEIRA — Satélite PC inicializando...")
    logger.info("=" * 60)

    nome_comodo = os.getenv("NOME_COMODO", "escritorio")
    cerebro_url = os.getenv("CEREBRO_URL", "http://localhost:8000")
    logger.info(f"Cômodo: {nome_comodo} | Cérebro: {cerebro_url}")

    # 1. Inicializa o Speaker (reprodução de áudio)
    speaker = Speaker(callback_estado=definir_estado)
    logger.info("✅ Speaker pronto.")

    # 2. Inicializa o Listener (microfone)
    listener = Listener(
        cerebro_url=cerebro_url,
        callback_estado=definir_estado,
        callback_resposta=processar_resposta_cerebro,
    )
    logger.info("✅ Listener pronto.")

    # 3. Inicializa o MQTT Listener (recebe comandos da rede)
    mqtt = MQTTListener(
        nome_comodo=nome_comodo,
        callback_comando=despachar_comando_mqtt,
    )
    mqtt.conectar()
    logger.info("✅ MQTT Listener conectado.")

    # 4. Inicia o Listener de microfone em thread separada
    thread_listener = threading.Thread(
        target=listener.iniciar,
        daemon=True,
        name="Thread-Listener",
    )
    thread_listener.start()
    logger.info("✅ Thread de escuta iniciada.")

    logger.info("=" * 60)
    logger.info("🚀 SATÉLITE ONLINE — Aguardando comandos...")
    logger.info("=" * 60)

    # 5. Inicia o HUD (Tkinter — precisa rodar na thread principal)
    root = tk.Tk()
    hud = SextaFeiraHUD(root, estado_callback=obter_estado)
    logger.info("✅ HUD inicializado.")

    # Callback de fechamento
    def ao_fechar():
        """Limpa recursos ao fechar a janela."""
        logger.info("Encerrando satélite...")
        listener.parar()
        mqtt.desconectar()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", ao_fechar)

    # Inicia o loop do Tkinter (bloqueante)
    root.mainloop()


if __name__ == "__main__":
    main()
