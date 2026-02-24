# ============================================================
# SEXTA-FEIRA — Listener (Ouvido do Satélite PC)
# ============================================================
# Monitora o microfone local continuamente. Quando detecta
# fala, envia o áudio WAV via HTTP POST para o Cérebro Central.
#
# O Cérebro é quem faz toda a IA (Whisper + LLM + TTS).
# Este módulo apenas grava e envia, mantendo o satélite leve.
#
# Fluxo:
#   1. Liga o microfone
#   2. Escuta continuamente com phrase_time_limit
#   3. Captura áudio WAV
#   4. Envia para POST {CEREBRO_URL}/processar_audio
#   5. Recebe resposta (áudio MP3 + ações)
#   6. Repassa áudio ao Speaker e ações ao MQTT Listener
# ============================================================

import os
import json
import base64
import logging
import tempfile
import requests
import speech_recognition as sr
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# Configura logging
logger = logging.getLogger("sexta.listener")


class Listener:
    """
    Ouvido do satélite PC.
    
    Monitora o microfone local e envia áudio para o Cérebro
    Central processar. Recebe de volta a resposta da IA.
    """

    def __init__(
        self,
        cerebro_url: str = None,
        callback_estado: callable = None,
        callback_resposta: callable = None,
    ):
        """
        Inicializa o listener de microfone.

        Args:
            cerebro_url: URL do endpoint de processamento de áudio do Cérebro.
            callback_estado: Função chamada para atualizar o estado visual (HUD).
            callback_resposta: Função chamada quando há resposta do Cérebro
                              (recebe dict com audio_bytes e acoes).
        """
        self.cerebro_url = cerebro_url or os.getenv(
            "CEREBRO_URL", "http://localhost:8000"
        )
        self.callback_estado = callback_estado
        self.callback_resposta = callback_resposta

        # Configura o reconhecedor de voz
        self.recognizer = sr.Recognizer()
        self.recognizer.pause_threshold = 2.0       # Pausa antes de finalizar frase
        self.recognizer.non_speaking_duration = 0.5  # Duração mínima de silêncio
        self.recognizer.dynamic_energy_threshold = False
        self.recognizer.energy_threshold = 300       # Sensibilidade do microfone

        # Microfone (detecta automaticamente o padrão do sistema)
        self.microfone = sr.Microphone()

        # Flag de controle
        self._rodando = True

        logger.info(f"Listener inicializado → Cérebro: {self.cerebro_url}")

    def _atualizar_estado(self, estado: str):
        """Atualiza o estado visual se houver callback configurado."""
        if self.callback_estado:
            self.callback_estado(estado)

    def _enviar_audio_cerebro(self, audio_wav_bytes: bytes) -> dict:
        """
        Envia áudio WAV para o Cérebro Central via HTTP POST.

        Args:
            audio_wav_bytes: Bytes do áudio no formato WAV.

        Returns:
            Dicionário com a resposta do Cérebro ou None em caso de erro.
        """
        try:
            url = f"{self.cerebro_url}/processar_audio"
            files = {"audio": ("audio.wav", audio_wav_bytes, "audio/wav")}

            resposta = requests.post(url, files=files, timeout=30)
            resposta.raise_for_status()

            return resposta.json()

        except requests.exceptions.ConnectionError:
            logger.error("Sem conexão com o Cérebro. Verifique se o Docker está rodando.")
            return None
        except requests.exceptions.Timeout:
            logger.error("Timeout ao comunicar com o Cérebro.")
            return None
        except Exception as e:
            logger.error(f"Erro ao enviar áudio: {e}")
            return None

    def _processar_resposta(self, resposta: dict):
        """
        Processa a resposta recebida do Cérebro.

        Args:
            resposta: Dicionário JSON retornado pelo endpoint /processar_audio.
        """
        if not resposta:
            return

        acao = resposta.get("acao", "ignorar")

        if acao == "ignorar":
            logger.debug(f"Wake word não detectada: {resposta.get('transcricao', '')}")
            return

        if acao == "responder":
            logger.info(f"Resposta: {resposta.get('resposta_texto', '')}")

            # Decodifica áudio MP3 da resposta (base64)
            audio_b64 = resposta.get("audio_base64", "")
            audio_bytes = None
            if audio_b64:
                audio_bytes = base64.b64decode(audio_b64)

            # Chama callback com áudio e ações
            if self.callback_resposta:
                self.callback_resposta({
                    "audio_bytes": audio_bytes,
                    "resposta_texto": resposta.get("resposta_texto", ""),
                    "acoes": resposta.get("acoes", []),
                })

    def iniciar(self):
        """
        Inicia o loop principal de escuta do microfone.
        Deve ser chamado em uma thread separada para não bloquear a UI.
        """
        logger.info("🎙️ Ouvidos ligados. Escutando...")
        self._atualizar_estado("idle")

        while self._rodando:
            with self.microfone as fonte:
                try:
                    # Escuta o microfone (com limite de 20 segundos por frase)
                    audio = self.recognizer.listen(
                        fonte, phrase_time_limit=20
                    )

                    # Obtém bytes WAV do áudio capturado
                    wav_data = audio.get_wav_data()
                    logger.info(f"Áudio capturado: {len(wav_data)} bytes")

                    # Atualiza estado visual
                    self._atualizar_estado("escutando")

                    # Envia para o Cérebro processar
                    self._atualizar_estado("pensando")
                    resposta = self._enviar_audio_cerebro(wav_data)

                    # Processa a resposta
                    self._processar_resposta(resposta)

                    # Volta ao estado idle
                    self._atualizar_estado("idle")

                except sr.WaitTimeoutError:
                    # Timeout normal — ninguém falou
                    pass
                except Exception as e:
                    logger.debug(f"Erro na escuta: {e}")
                    self._atualizar_estado("idle")

    def parar(self):
        """Para o loop de escuta."""
        self._rodando = False
        logger.info("Listener parado.")
