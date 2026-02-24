# ============================================================
# SEXTA-FEIRA — Servidor Principal (FastAPI)
# ============================================================
# Porta de entrada HTTP do Cérebro Central.
# Recebe áudio dos satélites PC, processa com IA e devolve
# resposta em áudio + dispara ações via MQTT.
#
# Endpoints:
#   POST /processar_audio  → Recebe WAV, retorna MP3 + ações
#   POST /comando_texto    → Recebe texto direto (debug/API)
#   GET  /status           → Health check do servidor
#   GET  /plugins          → Lista plugins carregados
#
# Uso:
#   uvicorn main_server:app --host 0.0.0.0 --port 8000 --reload
# ============================================================

import os
import io
import logging
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Módulos internos do Cérebro
from ai_core.stt_whisper import WhisperSTT
from ai_core.tts_edge import EdgeTTS
from ai_core.groq_brain import GroqBrain
from plugins_integracoes import GerenciadorPlugins, carregar_plugins
from network.mqtt_publisher import MQTTPublisher

# Carrega variáveis de ambiente
load_dotenv()

# Configura logging detalhado
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-20s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("sexta.server")

# ============================================================
# VARIÁVEIS GLOBAIS (inicializadas no lifespan)
# ============================================================
stt: WhisperSTT = None      # Speech-to-Text
tts: EdgeTTS = None          # Text-to-Speech
cerebro: GroqBrain = None    # Motor de IA
mqtt_pub: MQTTPublisher = None  # Publisher MQTT
gerenciador: GerenciadorPlugins = None  # Gerenciador de plugins


# ============================================================
# LIFESPAN — Inicialização e encerramento do servidor
# ============================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gerencia o ciclo de vida do servidor.
    Inicializa todos os componentes na startup e limpa no shutdown.
    """
    global stt, tts, cerebro, mqtt_pub, gerenciador

    logger.info("=" * 60)
    logger.info("🧠 SEXTA-FEIRA — Cérebro Central inicializando...")
    logger.info("=" * 60)

    # 1. Inicializa STT (Whisper)
    stt = WhisperSTT()
    logger.info("✅ STT (Whisper) pronto.")

    # 2. Inicializa TTS (Edge-TTS)
    tts = EdgeTTS()
    logger.info("✅ TTS (Edge-TTS) pronto.")

    # 3. Inicializa MQTT Publisher
    mqtt_pub = MQTTPublisher()
    mqtt_pub.conectar()
    logger.info("✅ MQTT Publisher conectado.")

    # 4. Inicializa e carrega plugins
    gerenciador = GerenciadorPlugins()
    
    # Injeta MQTT no plugin de PC commands
    try:
        from plugins_integracoes.pc_commands.windows_api import set_mqtt_publisher
        set_mqtt_publisher(mqtt_pub)
    except ImportError:
        logger.warning("Plugin PC Commands não encontrado para injeção MQTT.")

    carregar_plugins(gerenciador)
    logger.info(f"✅ {len(gerenciador.plugins)} plugins carregados.")

    # 5. Inicializa o Cérebro (LLM) com os plugins
    cerebro = GroqBrain(gerenciador_plugins=gerenciador)
    logger.info("✅ Cérebro (Groq LLM) pronto.")

    logger.info("=" * 60)
    logger.info("🚀 SEXTA-FEIRA ONLINE — Aguardando comandos...")
    logger.info("=" * 60)

    # Executa a aplicação
    yield

    # Shutdown: limpa recursos
    logger.info("Encerrando Sexta-Feira...")
    if mqtt_pub:
        mqtt_pub.desconectar()
    logger.info("Sexta-Feira desligada. Até a próxima, chefe.")


# ============================================================
# APP FASTAPI
# ============================================================
app = FastAPI(
    title="Sexta-Feira — Cérebro Central",
    description=(
        "API de Inteligência Artificial da armadura MK3. "
        "Processa áudio, gera respostas e controla hardware."
    ),
    version="2.0.0",
    lifespan=lifespan,
)

# CORS — permite requisições de qualquer origem (rede local)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# MODELOS DE REQUEST/RESPONSE
# ============================================================
class ComandoTexto(BaseModel):
    """Modelo para receber comandos de texto direto."""
    texto: str


class RespostaIA(BaseModel):
    """Modelo de resposta padrão da IA."""
    resposta: str
    acoes: list
    erro: str = None


# ============================================================
# ENDPOINTS
# ============================================================

@app.get("/status")
async def status():
    """
    Health check do servidor.
    Retorna o estado de todos os componentes.
    """
    return {
        "status": "online",
        "nome": "Sexta-Feira",
        "versao": "2.0.0",
        "componentes": {
            "stt": stt is not None,
            "tts": tts is not None,
            "cerebro": cerebro is not None,
            "mqtt": mqtt_pub.esta_conectado if mqtt_pub else False,
            "plugins": len(gerenciador.plugins) if gerenciador else 0,
        },
    }


@app.get("/plugins")
async def listar_plugins():
    """
    Lista todos os plugins carregados e suas ferramentas.
    Útil para debug e verificação.
    """
    if not gerenciador:
        raise HTTPException(status_code=503, detail="Gerenciador não inicializado.")

    plugins_info = {}
    for nome, config in gerenciador.plugins.items():
        plugins_info[nome] = {
            "descricao": config["descricao"],
            "parametros": config["parametros"],
        }

    return {"total": len(plugins_info), "plugins": plugins_info}


@app.post("/processar_audio")
async def processar_audio(audio: UploadFile = File(...)):
    """
    Endpoint principal — Processa áudio enviado por um satélite PC.

    Fluxo:
    1. Recebe arquivo WAV do satélite
    2. Transcreve com Whisper (STT)
    3. Detecta wake word "Sexta-Feira"
    4. Processa com LLM (Groq) + tool calling
    5. Gera áudio de resposta (TTS)
    6. Retorna MP3 + ações executadas

    Args:
        audio: Arquivo de áudio WAV enviado via multipart/form-data.

    Returns:
        JSON com resposta de texto, áudio base64, e ações executadas.
    """
    try:
        # 1. Lê os bytes do áudio enviado
        audio_bytes = await audio.read()
        logger.info(f"Áudio recebido: {len(audio_bytes)} bytes")

        # 2. Transcreve o áudio para texto
        texto_transcrito = stt.transcrever(audio_bytes)
        logger.info(f"Transcrição: '{texto_transcrito}'")

        # 3. Detecta wake word
        detectou, comando = stt.detectar_wake_word(texto_transcrito)

        if not detectou:
            return JSONResponse(content={
                "acao": "ignorar",
                "motivo": "Wake word não detectada.",
                "transcricao": texto_transcrito,
            })

        # Se só chamou "Sexta-Feira" sem comando
        if not comando:
            audio_resposta = await tts.gerar_audio_bytes("Sim, chefe?")
            import base64
            return JSONResponse(content={
                "acao": "responder",
                "resposta_texto": "Sim, chefe?",
                "audio_base64": base64.b64encode(audio_resposta).decode(),
                "acoes": [],
            })

        # 4. Processa o comando com o Cérebro
        resultado = cerebro.pensar(comando)
        logger.info(f"Resposta: '{resultado['resposta']}'")

        # 5. Gera áudio da resposta
        resposta_texto = resultado["resposta"]

        # Junta frases de resposta dos plugins com a resposta do LLM
        falas_plugins = [
            a["resposta_fala"]
            for a in resultado["acoes"]
            if a.get("resposta_fala")
        ]
        if falas_plugins and not resposta_texto:
            resposta_texto = " ".join(falas_plugins)
        elif falas_plugins and resposta_texto:
            resposta_texto = resposta_texto + " " + " ".join(falas_plugins)

        # Gera o MP3 se houver texto para falar
        audio_base64 = ""
        if resposta_texto:
            audio_resposta = await tts.gerar_audio_bytes(resposta_texto)
            import base64
            audio_base64 = base64.b64encode(audio_resposta).decode()

        return JSONResponse(content={
            "acao": "responder",
            "transcricao": texto_transcrito,
            "comando": comando,
            "resposta_texto": resposta_texto,
            "audio_base64": audio_base64,
            "acoes": resultado["acoes"],
            "erro": resultado.get("erro"),
        })

    except Exception as e:
        logger.error(f"Erro ao processar áudio: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/comando_texto", response_model=RespostaIA)
async def comando_texto(comando: ComandoTexto):
    """
    Endpoint de debug — Envia comando de texto direto (sem áudio).
    Útil para testar o cérebro sem precisar de microfone.

    Args:
        comando: Objeto JSON com campo "texto".

    Returns:
        Resposta da IA com texto e ações executadas.
    """
    try:
        resultado = cerebro.pensar(comando.texto)
        return RespostaIA(
            resposta=resultado["resposta"],
            acoes=resultado["acoes"],
            erro=resultado.get("erro"),
        )
    except Exception as e:
        logger.error(f"Erro no comando de texto: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# EXECUÇÃO DIRETA (sem Docker)
# ============================================================
if __name__ == "__main__":
    import uvicorn

    porta = int(os.getenv("SERVER_PORT", "8000"))
    logger.info(f"Iniciando servidor na porta {porta}...")
    uvicorn.run(
        "main_server:app",
        host="0.0.0.0",
        port=porta,
        reload=True,
    )
