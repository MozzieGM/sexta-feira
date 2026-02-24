# ============================================================
# SEXTA-FEIRA — Plugin: Comandos de PC (via MQTT)
# ============================================================
# Em vez de executar comandos diretamente (como no monolito),
# este plugin publica comandos via MQTT para que os satélites
# PC espalhados pela casa os executem localmente.
#
# Fluxo:
#   1. Cérebro recebe comando de voz ("abre o chrome")
#   2. LLM identifica tool call "abrir_programa"
#   3. Este plugin publica no MQTT: casa/{comodo}/pc/comando
#   4. O satélite PC inscrito no tópico executa a ação
#
# Comandos suportados:
#   - abrir_programa      → Abre apps (Chrome, Steam, etc.)
#   - gerenciar_janelas   → Minimiza/fecha janelas
#   - controle_midia      → Play/Pause, tela cheia, mini player
#   - controle_volume     → Volume do PC e do YouTube
#   - tocar_youtube       → Busca e toca vídeos
#   - escrever_txt        → Cria arquivo de texto
#   - ler_txt             → Lê arquivo de texto
#   - listar_arquivos     → Lista arquivos da pasta
# ============================================================

import json
import logging

# Configura logging
logger = logging.getLogger("sexta.plugin.pc_commands")

# Referência global ao publisher MQTT (injetada na inicialização)
_mqtt_publisher = None

# Tópico MQTT padrão para comandos de PC
# O satélite se inscreve em "casa/+/pc/comando" para ouvir
TOPICO_PADRAO = "casa/escritorio/pc/comando"


def set_mqtt_publisher(publisher):
    """
    Injeta a referência do publisher MQTT no módulo.
    Chamado pelo main_server.py durante a inicialização.

    Args:
        publisher: Instância do MQTTPublisher.
    """
    global _mqtt_publisher
    _mqtt_publisher = publisher
    logger.info("MQTT Publisher injetado no plugin PC Commands.")


def _publicar_comando(acao: str, dados: dict = None) -> bool:
    """
    Publica um comando no tópico MQTT para os satélites PC.

    Args:
        acao: Nome da ação (ex: "abrir_programa").
        dados: Dicionário com dados adicionais da ação.

    Returns:
        True se publicado com sucesso.
    """
    if _mqtt_publisher is None:
        logger.warning("MQTT Publisher não configurado. Comando local.")
        return False

    payload = {"acao": acao, "dados": dados or {}}

    try:
        _mqtt_publisher.publicar(TOPICO_PADRAO, payload)
        logger.info(f"Comando MQTT publicado: {acao} → {TOPICO_PADRAO}")
        return True
    except Exception as e:
        logger.error(f"Erro ao publicar MQTT: {e}")
        return False


# ============================================================
# HANDLERS DAS FERRAMENTAS
# ============================================================

def _handler_abrir_programa(argumentos: dict) -> str:
    """Publica comando para abrir um programa no satélite PC."""
    programa = argumentos.get("nome_programa", "")
    _publicar_comando("abrir_programa", {"nome_programa": programa})
    return f"Iniciando {programa}, chefe."


def _handler_gerenciar_janelas(argumentos: dict) -> str:
    """Publica comando para gerenciar janelas no satélite PC."""
    acao = argumentos.get("acao", "minimizar_tudo")
    nome = argumentos.get("nome_programa", "")
    _publicar_comando("gerenciar_janelas", {"acao": acao, "nome_programa": nome})

    respostas = {
        "minimizar_tudo": "Área de trabalho limpa.",
        "minimizar_atual": "Janela minimizada.",
        "fechar_programa": f"Encerrando as atividades de {nome}.",
    }
    return respostas.get(acao, "Comando de janela executado.")


def _handler_tocar_youtube(argumentos: dict) -> str:
    """Publica comando para buscar e tocar vídeo no YouTube."""
    pesquisa = argumentos.get("termo_pesquisa", "")
    _publicar_comando("tocar_youtube", {"termo_pesquisa": pesquisa})
    return f"Acessando os servidores. Buscando por {pesquisa}."


def _handler_controle_midia(argumentos: dict) -> str:
    """Publica comando de controle de mídia (play/pause, tela cheia, etc.)."""
    acao = argumentos.get("acao", "play_pause")
    
    # O Pulo do Gato: O Windows/Chrome ignora a tecla 'stop'. 
    # Então se a IA mandar parar, nós forçamos o envio de 'play_pause'.
    acao_mqtt = "play_pause" if acao == "stop" else acao
    
    _publicar_comando("controle_midia", {"acao": acao_mqtt})

    respostas = {
        "play_pause": "Mídia alterada.",
        "stop": "Reprodução interrompida.",
        "next": "Próxima faixa.",
        "prev": "Faixa anterior.",
        "tela_cheia": "Alterando o modo de tela do vídeo.",
        "mini_player": "Ativando o mini-player.",
    }
    return respostas.get(acao, "Comando de mídia executado.")


def _handler_controle_volume(argumentos: dict) -> str:
    """Publica comando de controle de volume (PC ou YouTube)."""
    alvo = argumentos.get("alvo", "pc")
    acao = argumentos.get("acao", "aumentar")
    _publicar_comando("controle_volume", {"alvo": alvo, "acao": acao})

    if alvo == "pc":
        respostas = {
            "aumentar": "Aumentando o volume do sistema.",
            "diminuir": "Abaixando o volume do sistema.",
            "mutar": "Áudio do computador silenciado.",
            "maximo": "Volume do sistema no máximo.",
        }
    else:
        respostas = {
            "aumentar": "Volume da música aumentado.",
            "diminuir": "Volume da música reduzido.",
            "mutar": "YouTube mutado.",
            "maximo": "Volume do YouTube no máximo.",
        }
    return respostas.get(acao, "Volume ajustado.")


def _handler_escrever_txt(argumentos: dict) -> str:
    """Publica comando para criar arquivo de texto no satélite."""
    nome = argumentos.get("nome_arquivo", "anotacoes.txt")
    conteudo = argumentos.get("conteudo", "")
    _publicar_comando("escrever_txt", {
        "nome_arquivo": nome,
        "conteudo": conteudo,
    })
    return f"Anotado, chefe. Guardei as informações no arquivo {nome}."


def _handler_ler_txt(argumentos: dict) -> str:
    """Publica comando para ler arquivo de texto no satélite."""
    nome = argumentos.get("nome_arquivo", "")
    _publicar_comando("ler_txt", {"nome_arquivo": nome})
    return f"Solicitando leitura do arquivo {nome}."


def _handler_listar_arquivos(argumentos: dict) -> str:
    """Publica comando para listar arquivos de texto no satélite."""
    _publicar_comando("listar_arquivos", {})
    return "Listando os arquivos disponíveis."


# ============================================================
# REGISTRO AUTOMÁTICO DOS PLUGINS
# ============================================================

def registrar(gerenciador):
    """
    Registra todas as ferramentas de controle de PC no gerenciador.

    Args:
        gerenciador: Instância do GerenciadorPlugins.
    """
    # Abrir programas
    gerenciador.registrar_plugin(
        nome="abrir_programa",
        descricao="Abre programas no computador (ex: chrome, steam, bloco de notas).",
        parametros={
            "type": "object",
            "properties": {
                "nome_programa": {
                    "type": "string",
                    "description": "Nome do programa a abrir."
                }
            },
            "required": ["nome_programa"],
        },
        handler=_handler_abrir_programa,
    )

    # Gerenciar janelas
    gerenciador.registrar_plugin(
        nome="gerenciar_janelas",
        descricao=(
            "Minimiza janelas do Windows ou FECHA programas específicos."
        ),
        parametros={
            "type": "object",
            "properties": {
                "acao": {
                    "type": "string",
                    "enum": ["minimizar_tudo", "minimizar_atual", "fechar_programa"],
                },
                "nome_programa": {
                    "type": "string",
                    "description": "Nome do programa (apenas para fechar_programa)."
                },
            },
            "required": ["acao"],
        },
        handler=_handler_gerenciar_janelas,
    )

    # Tocar YouTube
    gerenciador.registrar_plugin(
        nome="tocar_youtube",
        descricao="Busca e TOCA AUTOMATICAMENTE uma música ou vídeo no YouTube.",
        parametros={
            "type": "object",
            "properties": {
                "termo_pesquisa": {
                    "type": "string",
                    "description": "Termo de busca para o YouTube."
                }
            },
            "required": ["termo_pesquisa"],
        },
        handler=_handler_tocar_youtube,
    )

    # Controle de mídia
    gerenciador.registrar_plugin(
        nome="controle_midia",
        descricao=(
            "Controla a reprodução e a EXIBIÇÃO do vídeo "
            "(tela cheia ou mini-player)."
        ),
        parametros={
            "type": "object",
            "properties": {
                "acao": {
                    "type": "string",
                    "enum": [
                        "play_pause", "stop", "next", "prev",
                        "tela_cheia", "mini_player",
                    ],
                }
            },
            "required": ["acao"],
        },
        handler=_handler_controle_midia,
    )

    # Controle de volume
    gerenciador.registrar_plugin(
        nome="controle_volume",
        descricao=(
            "Aumenta, diminui ou muta o volume, separando o som do "
            "'PC' (sistema) do som do 'YouTube'. "
            "REGRA ABSOLUTA: Chame esta ferramenta APENAS UMA VEZ por comando. "
            "Você não consegue definir porcentagens exatas (como 3% ou 50%). "
            "Se o usuário pedir uma porcentagem específica, execute a ação 'diminuir' ou 'aumentar' UMA ÚNICA VEZ e avise que ajustou o volume em um bloco fixo."
        ),
        parametros={
            "type": "object",
            "properties": {
                "alvo": {
                    "type": "string",
                    "enum": ["pc", "youtube"],
                    "description": "Alvo: 'pc' para sistema ou 'youtube'."
                },
                "acao": {
                    "type": "string",
                    "enum": ["aumentar", "diminuir", "mutar", "maximo"],
                    "description": "Ação de volume a executar."
                },
            },
            "required": ["alvo", "acao"],
        },
        handler=_handler_controle_volume,
    )

    # Escrever arquivo de texto
    gerenciador.registrar_plugin(
        nome="escrever_txt",
        descricao="Cria um arquivo .txt e anota informações nele.",
        parametros={
            "type": "object",
            "properties": {
                "nome_arquivo": {
                    "type": "string",
                    "description": "Nome do arquivo (ex: anotacoes.txt)."
                },
                "conteudo": {
                    "type": "string",
                    "description": "Conteúdo a ser salvo no arquivo."
                },
            },
            "required": ["nome_arquivo", "conteudo"],
        },
        handler=_handler_escrever_txt,
    )

    # Ler arquivo de texto
    gerenciador.registrar_plugin(
        nome="ler_txt",
        descricao="Lê em voz alta o conteúdo de um arquivo .txt.",
        parametros={
            "type": "object",
            "properties": {
                "nome_arquivo": {
                    "type": "string",
                    "description": "Nome do arquivo a ser lido."
                }
            },
            "required": ["nome_arquivo"],
        },
        handler=_handler_ler_txt,
    )

    # Listar arquivos
    gerenciador.registrar_plugin(
        nome="listar_arquivos",
        descricao="Informa quais arquivos .txt existem na pasta.",
        handler=_handler_listar_arquivos,
    )

    logger.info("Plugins de Comandos de PC registrados (8 ferramentas).")
