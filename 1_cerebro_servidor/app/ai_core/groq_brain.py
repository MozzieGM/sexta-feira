# ============================================================
# SEXTA-FEIRA — Cérebro IA (Groq LLM + Tool Calling)
# ============================================================
# Motor de inteligência principal. Recebe texto do usuário,
# processa com o LLM da Groq (Llama 3.3 70B), identifica
# intenções e retorna respostas + ações de ferramentas.
#
# Recursos:
#   - System prompt com personalidade da Sexta-Feira
#   - Histórico de conversa por sessão
#   - Tool calling para hardware, mídia e sistema operacional
#   - Integração com sistema de plugins auto-discovery
# ============================================================

import os
import json
import logging
from groq import Groq
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# Configura logging
logger = logging.getLogger("sexta.brain")

# Modelo de IA padrão
MODELO_PADRAO = "llama-3.3-70b-versatile"

# System prompt que define a personalidade da Sexta-Feira
SYSTEM_PROMPT = (
    "Você é a Sexta-Feira, inteligência artificial da armadura MK3. "
    "Seu criador é o Mozzie. "
    "DIRETRIZ PRIMÁRIA (O MAIS IMPORTANTE): Você é uma assistente "
    "conversacional. Se o usuário perguntar 'tá me ouvindo?', 'tudo bem?', "
    "der bom dia, contar uma piada ou apenas conversar, VOCÊ É ESTRITAMENTE "
    "PROIBIDA DE USAR FERRAMENTAS. Responda APENAS com texto, conversando "
    "naturalmente. "
    "REGRA 2: Só acione ferramentas de hardware, janelas, mídia ou volume se "
    "houver uma ORDEM EXPLÍCITA E CLARA para isso (ex: 'aumenta o volume', "
    "'abre a máscara', 'toca youtube'). "
    "Personalidade: Prestativa, direta e com um leve tom sarcástico e "
    "inteligente."
)


class GroqBrain:
    """
    Cérebro principal da Sexta-Feira.
    
    Processa texto do usuário usando o LLM Groq com tool calling,
    retorna resposta textual e lista de ações para execução.
    """

    def __init__(self, gerenciador_plugins=None):
        """
        Inicializa o cérebro com o cliente Groq e plugins opcionais.

        Args:
            gerenciador_plugins: Instância do GerenciadorPlugins para
                                 obter ferramentas e executar ações.
        """
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY não encontrada no .env")

        self.client = Groq(api_key=api_key)
        self.modelo = MODELO_PADRAO
        self.gerenciador_plugins = gerenciador_plugins

        # Histórico de conversa (limitado para não estourar tokens)
        self.historico: list[dict] = []
        self.max_historico = 20  # Máximo de mensagens no contexto

        logger.info(f"GroqBrain inicializado — Modelo: {self.modelo}")

    def _obter_ferramentas(self) -> list[dict]:
        """
        Obtém a lista de ferramentas disponíveis dos plugins carregados.

        Returns:
            Lista de tool definitions no formato esperado pela API Groq.
        """
        if self.gerenciador_plugins:
            return self.gerenciador_plugins.obter_ferramentas_groq()
        return []

    def _construir_mensagens(self, texto_usuario: str) -> list[dict]:
        """
        Monta o array de mensagens com system prompt + histórico + nova msg.

        Args:
            texto_usuario: Texto transcrito do usuário.

        Returns:
            Lista de mensagens formatada para a API Groq.
        """
        mensagens = [{"role": "system", "content": SYSTEM_PROMPT}]

        # Adiciona histórico recente (Window Sliding)
        mensagens.extend(self.historico[-self.max_historico:])

        # Adiciona a mensagem atual do usuário
        mensagens.append({"role": "user", "content": texto_usuario})

        return mensagens

    def pensar(self, texto_usuario: str) -> dict:
        """
        Processa a entrada do usuário e retorna resposta + ações.

        Este é o método principal. Ele:
        1. Envia o texto para o LLM com tool calling habilitado
        2. Identifica se o LLM quer usar ferramentas
        3. Executa as ações via plugins
        4. Retorna resposta textual e lista de resultados

        Args:
            texto_usuario: Texto do comando do usuário.

        Returns:
            Dicionário com:
                - "resposta": texto para falar (str)
                - "acoes": lista de ações executadas (list[dict])
                - "erro": mensagem de erro se houver (str ou None)
        """
        resultado = {
            "resposta": "",
            "acoes": [],
            "erro": None,
        }

        try:
            ferramentas = self._obter_ferramentas()
            mensagens = self._construir_mensagens(texto_usuario)

            # Parâmetros da chamada ao LLM
            params = {
                "messages": mensagens,
                "model": self.modelo,
                "temperature": 0.3,
                "max_tokens": 250,
            }

            # Só adiciona tools se houver plugins carregados
            if ferramentas:
                params["tools"] = ferramentas
                params["tool_choice"] = "auto"

            # Chamada ao LLM Groq
            chat_completion = self.client.chat.completions.create(**params)
            resposta = chat_completion.choices[0].message

            # Processa tool calls (se houver)
            if getattr(resposta, "tool_calls", None) and self.gerenciador_plugins:
                for tool in resposta.tool_calls:
                    nome = tool.function.name
                    argumentos = json.loads(tool.function.arguments)

                    logger.info(f"Tool call: {nome}({argumentos})")

                    # Executa a ação via plugin correspondente
                    acao_resultado = self.gerenciador_plugins.executar(
                        nome, argumentos
                    )
                    resultado["acoes"].append(acao_resultado)

            # Captura resposta textual
            if resposta.content:
                resultado["resposta"] = resposta.content

            # Se não houve tool calls nem texto, resposta genérica
            if not resultado["acoes"] and not resultado["resposta"]:
                resultado["resposta"] = "Desculpe, não entendi o que disse."

            # Atualiza histórico da conversa
            self.historico.append({"role": "user", "content": texto_usuario})
            
            # Precisamos GARANTIR que a IA saiba que já respondeu ao comando.
            # Se ela falou algo, usamos a fala. Se ela apenas executou ferramentas, usamos o retorno dos plugins.
            texto_historico = resultado["resposta"]
            
            if not texto_historico and resultado["acoes"]:
                # Junta o retorno dos plugins (ex: "Reator no modo 5") para salvar na memória
                texto_historico = " ".join(str(acao) for acao in resultado["acoes"])
            
            if not texto_historico:
                texto_historico = "Comando executado com sucesso."

            # Salva a resposta da assistente para ela não achar que está devendo tarefas
            self.historico.append({
                "role": "assistant",
                "content": texto_historico,
            })

        except Exception as e:
            logger.error(f"Erro no Groq: {e}")
            resultado["erro"] = str(e)
            resultado["resposta"] = "Falha de conexão neural."

        return resultado

    def limpar_historico(self):
        """Reseta o histórico de conversa."""
        self.historico.clear()
        logger.info("Histórico de conversa limpo.")
