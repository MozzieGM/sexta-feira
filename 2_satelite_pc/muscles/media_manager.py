# ============================================================
# SEXTA-FEIRA — Media Manager (Músculos de Mídia)
# ============================================================
# Controla reprodução de mídia no satélite PC:
#   - Buscar e tocar vídeos/músicas no YouTube
#   - Play/Pause, próxima faixa, faixa anterior
#   - Tela cheia e mini-player do YouTube
#
# Utiliza pyautogui para simular teclas de mídia e
# webbrowser para abrir URLs do YouTube.
# ============================================================

import re
import logging
import urllib.parse
import urllib.request
import webbrowser

# Configura logging
logger = logging.getLogger("sexta.media_manager")

# Tenta importar pyautogui para controle de teclas
try:
    import pyautogui
    pyautogui.FAILSAFE = False
except ImportError:
    pyautogui = None
    logger.warning("pyautogui não encontrado. Controles de mídia limitados.")


def tocar_youtube(termo_pesquisa: str) -> bool:
    """
    Busca um vídeo no YouTube e abre o primeiro resultado automaticamente.

    Args:
        termo_pesquisa: Termo de busca (nome da música, vídeo, etc.).

    Returns:
        True se o vídeo foi encontrado e aberto.
    """
    try:
        # Monta a URL de busca do YouTube
        query = urllib.parse.quote(termo_pesquisa)
        url_busca = f"https://www.youtube.com/results?search_query={query}"

        # Faz a requisição e busca IDs de vídeo no HTML
        html = urllib.request.urlopen(url_busca)
        conteudo = html.read().decode()
        video_ids = re.findall(r"watch\?v=(\S{11})", conteudo)

        if video_ids:
            url_video = f"https://www.youtube.com/watch?v={video_ids[0]}"
            webbrowser.open(url_video)
            logger.info(f"YouTube: Tocando '{termo_pesquisa}' → {url_video}")
            return True
        else:
            logger.warning(f"YouTube: Nenhum resultado para '{termo_pesquisa}'")
            return False

    except Exception as e:
        logger.error(f"Erro ao buscar no YouTube: {e}")
        return False


def controle_midia(acao: str) -> bool:
    """
    Controla a reprodução de mídia via teclas de atalho nativas do YouTube.
    """
    if not pyautogui:
        logger.error("pyautogui não disponível para controle de mídia.")
        return False

    try:
        # Pulo do gato: Usamos atalhos NATIVOS do YouTube com if/elif
        # para podermos misturar 'press' (1 tecla) com 'hotkey' (2 teclas juntas)
        
        if acao in ["play_pause", "stop"]:
            pyautogui.press("k")
            logger.info(f"Mídia: {acao} → tecla 'k' (Pause/Play nativo)")
            
        elif acao == "next":
            pyautogui.hotkey("shift", "n")
            logger.info("Mídia: next → 'shift + n' (Próximo vídeo)")
            
        elif acao == "prev":
            pyautogui.hotkey("shift", "p")
            logger.info(f"Mídia: prev → 'shift + p' (Vídeo anterior)")
            
        elif acao == "tela_cheia":
            pyautogui.press("f")
            logger.info("Mídia: tela_cheia → tecla 'f' (Fullscreen)")
            
        elif acao == "mini_player":
            pyautogui.press("i")
            logger.info("Mídia: mini_player → tecla 'i' (Mini-player)")
            
        else:
            logger.warning(f"Ação de mídia desconhecida: {acao}")
            return False

        return True

    except Exception as e:
        logger.error(f"Erro no controle de mídia: {e}")
        return False
