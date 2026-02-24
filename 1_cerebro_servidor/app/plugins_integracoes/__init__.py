# ============================================================
# SEXTA-FEIRA — Sistema de Plugins (Auto-Discovery)
# ============================================================
# Este módulo implementa o sistema de plugins que permite
# adicionar novas funcionalidades sem modificar o código core.
#
# COMO CRIAR UM NOVO PLUGIN:
#   1. Crie uma pasta dentro de plugins_integracoes/
#   2. Crie um arquivo .py com uma função registrar(gerenciador)
#   3. Na função, chame gerenciador.registrar_plugin() para cada
#      ferramenta que o plugin oferece
#   4. Reinicie o servidor — o plugin será carregado automaticamente
#
# Exemplo mínimo de plugin:
#   def registrar(gerenciador):
#       gerenciador.registrar_plugin(
#           nome="minha_funcao",
#           descricao="Faz algo incrível",
#           parametros={...},  # Formato OpenAI function schema
#           handler=minha_funcao_handler,
#       )
# ============================================================

import os
import importlib
import logging
from pathlib import Path

# Configura logging
logger = logging.getLogger("sexta.plugins")


class GerenciadorPlugins:
    """
    Gerenciador central de plugins da Sexta-Feira.
    
    Responsável por:
    - Descobrir e carregar plugins automaticamente de subpastas
    - Converter plugins em formato de tools para a API Groq
    - Despachar ações para o plugin correto
    """

    def __init__(self):
        """Inicializa o gerenciador com dicionário de plugins vazio."""
        # Dicionário {nome_ferramenta: {descricao, parametros, handler}}
        self.plugins: dict = {}
        logger.info("GerenciadorPlugins inicializado.")

    def registrar_plugin(
        self,
        nome: str,
        descricao: str,
        handler: callable,
        parametros: dict = None,
    ):
        """
        Registra um plugin/ferramenta no gerenciador.

        Args:
            nome: Nome único da ferramenta (ex: "controlar_mascara").
            descricao: Descrição curta para o LLM entender quando usar.
            handler: Função que será chamada quando a ferramenta for acionada.
            parametros: Schema dos parâmetros (formato OpenAI function calling).
                       Se None, a ferramenta não recebe argumentos.
        """
        self.plugins[nome] = {
            "descricao": descricao,
            "parametros": parametros or {"type": "object", "properties": {}},
            "handler": handler,
        }
        logger.info(f"Plugin registrado: '{nome}' — {descricao}")

    def obter_ferramentas_groq(self) -> list[dict]:
        """
        Converte os plugins registrados no formato de tools da API Groq.

        Returns:
            Lista de dicionários no formato esperado pelo Groq (OpenAI-compatible).
        """
        ferramentas = []
        for nome, config in self.plugins.items():
            ferramenta = {
                "type": "function",
                "function": {
                    "name": nome,
                    "description": config["descricao"],
                },
            }
            # Só adiciona parameters se houver propriedades definidas
            if config["parametros"].get("properties"):
                ferramenta["function"]["parameters"] = config["parametros"]

            ferramentas.append(ferramenta)

        return ferramentas

    def executar(self, nome: str, argumentos: dict) -> dict:
        """
        Despacha a execução de uma ação para o plugin correspondente.

        Args:
            nome: Nome da ferramenta a ser executada.
            argumentos: Dicionário de argumentos da ferramenta.

        Returns:
            Dicionário com resultado da execução:
                - "plugin": nome do plugin
                - "sucesso": bool
                - "resposta_fala": texto para a Sexta falar (str)
                - "dados": dados adicionais retornados (dict)
                - "erro": mensagem de erro se houver (str ou None)
        """
        resultado = {
            "plugin": nome,
            "sucesso": False,
            "resposta_fala": "",
            "dados": {},
            "erro": None,
        }

        if nome not in self.plugins:
            resultado["erro"] = f"Plugin '{nome}' não encontrado."
            resultado["resposta_fala"] = f"Plugin {nome} não está instalado."
            logger.warning(f"Plugin não encontrado: '{nome}'")
            return resultado

        try:
            # Chama o handler do plugin com os argumentos
            retorno = self.plugins[nome]["handler"](argumentos)

            # O handler pode retornar uma string (fala) ou um dict completo
            if isinstance(retorno, str):
                resultado["resposta_fala"] = retorno
            elif isinstance(retorno, dict):
                resultado["resposta_fala"] = retorno.get("fala", "")
                resultado["dados"] = retorno.get("dados", {})
            
            resultado["sucesso"] = True
            logger.info(f"Plugin '{nome}' executado com sucesso.")

        except Exception as e:
            resultado["erro"] = str(e)
            resultado["resposta_fala"] = f"Erro ao executar {nome}."
            logger.error(f"Erro no plugin '{nome}': {e}")

        return resultado


def carregar_plugins(gerenciador: GerenciadorPlugins) -> None:
    """
    Escaneia todas as subpastas de plugins_integracoes/ e carrega
    automaticamente módulos Python que possuam a função registrar().

    Cada módulo .py encontrado é importado dinamicamente. Se ele tiver
    uma função chamada 'registrar', ela é chamada passando o gerenciador.

    Args:
        gerenciador: Instância do GerenciadorPlugins para registrar plugins.
    """
    # Diretório base dos plugins (o mesmo diretório deste __init__.py)
    diretorio_plugins = Path(__file__).parent
    logger.info(f"Escaneando plugins em: {diretorio_plugins}")

    # Percorre todas as subpastas
    for pasta in diretorio_plugins.iterdir():
        # Ignora arquivos e pastas especiais (__pycache__ etc)
        if not pasta.is_dir() or pasta.name.startswith("_"):
            continue

        logger.info(f"Verificando pasta de plugins: {pasta.name}")

        # Percorre cada arquivo .py dentro da subpasta
        for arquivo in pasta.glob("*.py"):
            # Ignora __init__.py dos subpacotes
            if arquivo.name.startswith("_"):
                continue

            # Monta o nome do módulo para importação dinâmica
            # Ex: plugins_integracoes.projetos_customizados.mk3_mascara_api
            nome_modulo = f"plugins_integracoes.{pasta.name}.{arquivo.stem}"

            try:
                modulo = importlib.import_module(nome_modulo)

                # Verifica se o módulo tem a função de registro
                if hasattr(modulo, "registrar"):
                    modulo.registrar(gerenciador)
                    logger.info(
                        f"  ✅ Plugin carregado: {arquivo.name}"
                    )
                else:
                    logger.warning(
                        f"  ⚠️ {arquivo.name} não possui função registrar()"
                    )

            except Exception as e:
                logger.error(f"  ❌ Erro ao carregar {arquivo.name}: {e}")

    total = len(gerenciador.plugins)
    logger.info(f"Total de plugins carregados: {total}")
