# ============================================================
# SEXTA-FEIRA — System Manager (Músculos do Sistema Operacional)
# ============================================================
# Executa ações no sistema operacional local do satélite PC.
# Suporte cross-platform: Windows (principal) e Linux (futuro).
#
# Ações suportadas:
#   - Abrir programas (Chrome, Steam, Notepad, etc.)
#   - Gerenciar janelas (minimizar, fechar)
#   - Controlar volume do sistema
#   - Escrever/Ler/Listar arquivos de texto
# ============================================================

import os
import sys
import logging
import subprocess
import platform

# Configura logging
logger = logging.getLogger("sexta.sys_manager")

# Detecta o sistema operacional
SO_ATUAL = platform.system().lower()  # "windows" ou "linux"

# Se estiver no Windows, importa pyautogui para controle de teclado
try:
    import pyautogui
    pyautogui.FAILSAFE = False  # Desabilita failsafe para automação
except ImportError:
    pyautogui = None
    logger.warning("pyautogui não encontrado. Controles de teclado desabilitados.")

# Diretório para arquivos de texto da Sexta-Feira
PASTA_ARQUIVOS = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "arquivos_sexta_feira"
)
os.makedirs(PASTA_ARQUIVOS, exist_ok=True)

# ============================================================
# MAPA DE PROGRAMAS — Traduz nomes falados para comandos do SO
# ============================================================
MAPA_PROGRAMAS_WINDOWS = {
    "google chrome": "chrome",
    "chrome": "chrome",
    "youtube": "chrome",
    "steam": "steam://open/main",
    "notepad mais mais": "notepad++",
    "notepad++": "notepad++",
    "bloco de notas": "notepad",
    "calculadora": "calc",
    "spotify": "spotify",
}

MAPA_PROGRAMAS_LINUX = {
    "google chrome": "google-chrome",
    "chrome": "google-chrome",
    "youtube": "google-chrome",
    "steam": "steam",
    "bloco de notas": "gedit",
    "calculadora": "gnome-calculator",
    "spotify": "spotify",
}

# Mapa de processos para fechar programas
MAPA_PROCESSOS_WINDOWS = {
    "google chrome": "chrome.exe",
    "chrome": "chrome.exe",
    "youtube": "chrome.exe",
    "steam": "steam.exe",
    "notepad mais mais": "notepad++.exe",
    "notepad++": "notepad++.exe",
    "bloco de notas": "notepad.exe",
    "calculadora": "calculator.exe",
    "spotify": "spotify.exe",
}


# ============================================================
# FUNÇÕES DE CONTROLE DO SISTEMA
# ============================================================

def abrir_programa(nome_programa: str) -> bool:
    """
    Abre um programa pelo nome (cross-platform).

    Args:
        nome_programa: Nome do programa como falado pelo usuário.

    Returns:
        True se o programa foi aberto com sucesso.
    """
    nome_lower = nome_programa.lower()

    if SO_ATUAL == "windows":
        mapa = MAPA_PROGRAMAS_WINDOWS
        comando = mapa.get(nome_lower, nome_lower)
        try:
            os.startfile(comando)
            logger.info(f"Programa aberto (Windows): {comando}")
            return True
        except Exception as e:
            logger.error(f"Falha ao abrir {comando}: {e}")
            return False

    elif SO_ATUAL == "linux":
        mapa = MAPA_PROGRAMAS_LINUX
        comando = mapa.get(nome_lower, nome_lower)
        try:
            subprocess.Popen(
                [comando],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            logger.info(f"Programa aberto (Linux): {comando}")
            return True
        except Exception as e:
            logger.error(f"Falha ao abrir {comando}: {e}")
            return False

    else:
        logger.error(f"Sistema operacional não suportado: {SO_ATUAL}")
        return False


def gerenciar_janelas(acao: str, nome_programa: str = "") -> bool:
    """
    Gerencia janelas do sistema operacional.

    Args:
        acao: "minimizar_tudo", "minimizar_atual" ou "fechar_programa".
        nome_programa: Nome do programa (apenas para fechar_programa).

    Returns:
        True se a ação foi executada com sucesso.
    """
    try:
        if SO_ATUAL == "windows":
            if acao == "minimizar_tudo":
                if pyautogui:
                    pyautogui.hotkey("win", "d")
                logger.info("Todas as janelas minimizadas.")
                return True

            elif acao == "minimizar_atual":
                if pyautogui:
                    pyautogui.hotkey("win", "down")
                    import time
                    time.sleep(0.1)
                    pyautogui.hotkey("win", "down")
                logger.info("Janela atual minimizada.")
                return True

            elif acao == "fechar_programa":
                nome_lower = nome_programa.lower()
                exe = MAPA_PROCESSOS_WINDOWS.get(nome_lower, nome_lower)
                if not exe.endswith(".exe"):
                    exe += ".exe"
                os.system(f"taskkill /im {exe} /f")
                logger.info(f"Programa fechado: {exe}")
                return True

        elif SO_ATUAL == "linux":
            if acao == "minimizar_tudo":
                subprocess.run(["wmctrl", "-k", "on"], check=False)
                return True
            elif acao == "fechar_programa":
                subprocess.run(["pkill", "-f", nome_programa], check=False)
                return True

    except Exception as e:
        logger.error(f"Erro ao gerenciar janelas: {e}")

    return False


def controle_volume(alvo: str, acao: str) -> bool:
    """
    Controla o volume do sistema ou do YouTube.

    Args:
        alvo: "pc" para volume do sistema, "youtube" para controle do player.
        acao: "aumentar", "diminuir", "mutar" ou "maximo".

    Returns:
        True se o comando foi executado.
    """
    if not pyautogui:
        logger.error("pyautogui não disponível para controle de volume.")
        return False

    try:
        if alvo == "pc":
            acoes = {
                "aumentar": lambda: pyautogui.press("volumeup", presses=10),
                "diminuir": lambda: pyautogui.press("volumedown", presses=10),
                "mutar": lambda: pyautogui.press("volumemute"),
                "maximo": lambda: pyautogui.press("volumeup", presses=50),
            }
        elif alvo == "youtube":
            acoes = {
                "aumentar": lambda: pyautogui.press("up", presses=5),
                "diminuir": lambda: pyautogui.press("down", presses=5),
                "mutar": lambda: pyautogui.press("m"),
                "maximo": lambda: pyautogui.press("up", presses=20),
            }
        else:
            logger.warning(f"Alvo de volume desconhecido: {alvo}")
            return False

        executor = acoes.get(acao)
        if executor:
            executor()
            logger.info(f"Volume: {alvo} → {acao}")
            return True

    except Exception as e:
        logger.error(f"Erro no controle de volume: {e}")

    return False


# ============================================================
# FUNÇÕES DE ARQUIVO DE TEXTO
# ============================================================

def escrever_txt(nome_arquivo: str, conteudo: str) -> bool:
    """
    Cria ou sobrescreve um arquivo .txt.

    Args:
        nome_arquivo: Nome do arquivo (com ou sem extensão).
        conteudo: Conteúdo a ser salvo.

    Returns:
        True se salvo com sucesso.
    """
    try:
        if not nome_arquivo.endswith(".txt"):
            nome_arquivo += ".txt"
        caminho = os.path.join(PASTA_ARQUIVOS, nome_arquivo)
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(conteudo)
        logger.info(f"Arquivo salvo: {caminho}")
        return True
    except Exception as e:
        logger.error(f"Erro ao salvar arquivo: {e}")
        return False


def ler_txt(nome_arquivo: str) -> str:
    """
    Lê o conteúdo de um arquivo .txt.

    Args:
        nome_arquivo: Nome do arquivo.

    Returns:
        Conteúdo do arquivo ou mensagem de erro.
    """
    try:
        if not nome_arquivo.endswith(".txt"):
            nome_arquivo += ".txt"
        caminho = os.path.join(PASTA_ARQUIVOS, nome_arquivo)
        if os.path.exists(caminho):
            with open(caminho, "r", encoding="utf-8") as f:
                return f.read()
        else:
            return f"Arquivo {nome_arquivo} não encontrado."
    except Exception as e:
        logger.error(f"Erro ao ler arquivo: {e}")
        return f"Erro ao ler {nome_arquivo}."


def listar_arquivos() -> list:
    """
    Lista todos os arquivos .txt na pasta da Sexta-Feira.

    Returns:
        Lista de nomes de arquivos.
    """
    try:
        return [f for f in os.listdir(PASTA_ARQUIVOS) if f.endswith(".txt")]
    except Exception as e:
        logger.error(f"Erro ao listar arquivos: {e}")
        return []
