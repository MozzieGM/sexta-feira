# ============================================================
# SEXTA-FEIRA — Speech-to-Text via Whisper (Groq Cloud)
# ============================================================
# Responsável por converter áudio (WAV) em texto utilizando
# o modelo Whisper Large V3 hospedado na infraestrutura Groq.
#
# O Whisper entende português e inglês misturados, ideal para
# quando o usuário fala nomes de músicas/jogos em inglês.
# ============================================================

import os
import logging
from groq import Groq
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# Configura logging para rastreamento de erros
logger = logging.getLogger("sexta.stt")


class WhisperSTT:
    """
    Classe responsável pela transcrição de áudio usando Whisper via Groq.
    
    Converte bytes de áudio WAV em texto transcrito, suportando
    português brasileiro com termos em inglês misturados.
    """

    def __init__(self):
        """Inicializa o cliente Groq com a API key do ambiente."""
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY não encontrada no .env")
        self.client = Groq(api_key=api_key)
        # Prompt de contexto que ajuda o Whisper a entender o vocabulário
        self.prompt_contexto = (
            "O usuário é brasileiro, mas costuma pedir nomes de músicas, "
            "bandas, jogos e termos técnicos em inglês, como Lose Control, "
            "Steam, Chrome."
        )
        logger.info("WhisperSTT inicializado com sucesso.")

    def transcrever(self, audio_bytes: bytes, formato: str = "wav") -> str:
        """
        Transcreve áudio em texto.

        Args:
            audio_bytes: Bytes brutos do arquivo de áudio.
            formato: Formato do áudio (padrão: "wav").

        Returns:
            Texto transcrito limpo (sem pontuação final desnecessária).

        Raises:
            Exception: Se houver falha na comunicação com a API Groq.
        """
        try:
            # Envia o áudio para o Whisper via API Groq
            transcricao = self.client.audio.transcriptions.create(
                file=(f"audio.{formato}", audio_bytes),
                model="whisper-large-v3",
                prompt=self.prompt_contexto,
            )

            texto = transcricao.text.strip()
            logger.info(f"Transcrição: '{texto}'")
            return texto

        except Exception as e:
            logger.error(f"Erro na transcrição Whisper: {e}")
            raise

    def limpar_texto(self, texto: str) -> str:
        """
        Remove pontuação e normaliza o texto para processamento.

        Args:
            texto: Texto bruto da transcrição.

        Returns:
            Texto em minúsculas sem pontuação.
        """
        return (
            texto.lower()
            .replace(".", "")
            .replace(",", "")
            .replace("!", "")
            .replace("?", "")
        )

    def detectar_wake_word(self, texto: str) -> tuple[bool, str]:
        """
        Verifica se o texto contém a wake word "Sexta-Feira".

        Args:
            texto: Texto transcrito (já limpo).

        Returns:
            Tupla (detectou: bool, comando: str) onde comando é o texto
            após remover a wake word.
        """
        texto_limpo = self.limpar_texto(texto)

        # Verifica variações da wake word
        wake_words = ["sexta-feira", "sexta feira"]
        for wake in wake_words:
            if wake in texto_limpo:
                comando = texto_limpo.replace(wake, "").strip()
                return True, comando

        return False, ""
