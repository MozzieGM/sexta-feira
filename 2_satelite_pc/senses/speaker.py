# ============================================================
# SEXTA-FEIRA — Speaker (Boca do Satélite PC)
# ============================================================
# Reproduz áudio MP3 na caixa de som local do computador.
# Recebe os bytes MP3 gerados pelo Cérebro Central e toca
# usando pygame.mixer para reprodução de alta qualidade.
#
# Também gerencia o estado da IA ("falando" / "idle") para
# que o HUD reaja visualmente durante a fala.
# ============================================================

import os
import tempfile
import logging
import pygame

# Configura logging
logger = logging.getLogger("sexta.speaker")


class Speaker:
    """
    Boca do satélite PC — reproduz áudio da Sexta-Feira.
    
    Toca arquivos MP3 usando pygame.mixer e gerencia
    o ciclo de vida do áudio temporário.
    """

    def __init__(self, callback_estado: callable = None):
        """
        Inicializa o speaker com pygame.mixer.

        Args:
            callback_estado: Função chamada para atualizar o estado
                            visual ("falando" / "idle").
        """
        self.callback_estado = callback_estado

        # Inicializa o mixer de áudio do pygame
        if not pygame.mixer.get_init():
            pygame.mixer.init()

        logger.info("Speaker inicializado.")

    def _atualizar_estado(self, estado: str):
        """Atualiza o estado visual se houver callback."""
        if self.callback_estado:
            self.callback_estado(estado)

    def falar_bytes(self, audio_bytes: bytes):
        """
        Reproduz áudio a partir de bytes MP3.

        Args:
            audio_bytes: Bytes do arquivo MP3 a ser reproduzido.
        """
        if not audio_bytes:
            logger.warning("Nenhum áudio recebido para reproduzir.")
            return

        arquivo_temp = None
        try:
            # Salva bytes em arquivo temporário
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=".mp3"
            ) as fp:
                fp.write(audio_bytes)
                arquivo_temp = fp.name

            # Reproduz o áudio
            self._atualizar_estado("falando")
            pygame.mixer.music.load(arquivo_temp)
            pygame.mixer.music.play()

            # Aguarda o fim da reprodução
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)

            logger.info("Áudio reproduzido com sucesso.")

        except Exception as e:
            logger.error(f"Erro ao reproduzir áudio: {e}")

        finally:
            # Limpa recursos
            self._atualizar_estado("idle")
            pygame.mixer.music.unload()

            # Remove arquivo temporário
            if arquivo_temp:
                try:
                    os.remove(arquivo_temp)
                except OSError:
                    pass

    def falar_arquivo(self, caminho_mp3: str):
        """
        Reproduz áudio a partir de um arquivo MP3 no disco.

        Args:
            caminho_mp3: Caminho completo do arquivo MP3.
        """
        if not os.path.exists(caminho_mp3):
            logger.error(f"Arquivo não encontrado: {caminho_mp3}")
            return

        try:
            self._atualizar_estado("falando")
            pygame.mixer.music.load(caminho_mp3)
            pygame.mixer.music.play()

            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)

            logger.info(f"Áudio reproduzido: {caminho_mp3}")

        except Exception as e:
            logger.error(f"Erro ao reproduzir {caminho_mp3}: {e}")

        finally:
            self._atualizar_estado("idle")
            pygame.mixer.music.unload()

    def parar(self):
        """Para a reprodução atual imediatamente."""
        try:
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()
            self._atualizar_estado("idle")
        except Exception:
            pass
