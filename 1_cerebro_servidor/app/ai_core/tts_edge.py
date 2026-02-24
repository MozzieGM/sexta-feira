# ============================================================
# SEXTA-FEIRA — Text-to-Speech via Edge-TTS (Microsoft Neural)
# ============================================================
# Gera áudio MP3 com a voz neural da Sexta-Feira usando o
# serviço Edge-TTS da Microsoft (gratuito e de alta qualidade).
#
# Voz padrão: pt-BR-ThalitaNeural (feminina brasileira)
# Taxa: +20% (fala ligeiramente mais rápido para soar natural)
# ============================================================

import asyncio
import tempfile
import logging
import edge_tts

# Configura logging
logger = logging.getLogger("sexta.tts")

# Constantes de configuração de voz
VOZ_PADRAO = "pt-BR-ThalitaNeural"
TAXA_FALA = "+20%"


class EdgeTTS:
    """
    Classe responsável pela síntese de voz da Sexta-Feira.
    
    Utiliza Edge-TTS (Microsoft Neural Voices) para gerar áudio
    MP3 de alta qualidade a partir de texto.
    """

    def __init__(self, voz: str = VOZ_PADRAO, taxa: str = TAXA_FALA):
        """
        Inicializa o sintetizador de voz.

        Args:
            voz: Identificador da voz neural (padrão: ThalitaNeural).
            taxa: Velocidade da fala (padrão: +20%).
        """
        self.voz = voz
        self.taxa = taxa
        logger.info(f"EdgeTTS inicializado — Voz: {self.voz}, Taxa: {self.taxa}")

    async def _gerar_audio_async(self, texto: str, caminho_arquivo: str) -> None:
        """
        Gera o áudio de forma assíncrona e salva no caminho especificado.

        Args:
            texto: Texto a ser convertido em fala.
            caminho_arquivo: Caminho completo do arquivo MP3 de saída.
        """
        communicate = edge_tts.Communicate(texto, self.voz, rate=self.taxa)
        await communicate.save(caminho_arquivo)

    def gerar_audio_arquivo(self, texto: str) -> str:
        """
        Gera um arquivo MP3 temporário com a fala sintetizada.

        Args:
            texto: Texto a ser convertido em fala.

        Returns:
            Caminho do arquivo MP3 temporário gerado.
        """
        try:
            # Cria arquivo temporário que não será deletado automaticamente
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=".mp3"
            ) as fp:
                caminho_audio = fp.name

            # Executa a geração assíncrona
            asyncio.run(self._gerar_audio_async(texto, caminho_audio))
            logger.info(f"Áudio gerado: {caminho_audio}")
            return caminho_audio

        except Exception as e:
            logger.error(f"Erro ao gerar áudio: {e}")
            raise

    async def gerar_audio_bytes(self, texto: str) -> bytes:
        """
        Gera áudio MP3 e retorna como bytes (ideal para enviar via HTTP).

        Args:
            texto: Texto a ser convertido em fala.

        Returns:
            Bytes do arquivo MP3 gerado.
        """
        try:
            # Gera em arquivo temporário e lê os bytes
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=".mp3"
            ) as fp:
                caminho = fp.name

            await self._gerar_audio_async(texto, caminho)

            with open(caminho, "rb") as f:
                audio_bytes = f.read()

            # Limpa o arquivo temporário
            import os
            os.remove(caminho)

            logger.info(f"Áudio gerado em memória: {len(audio_bytes)} bytes")
            return audio_bytes

        except Exception as e:
            logger.error(f"Erro ao gerar áudio em bytes: {e}")
            raise
