# 🤖 SEXTA-FEIRA — Assistente de IA Distribuída

> **"Sistemas online. Pronta, chefe."**

Assistente de inteligência artificial inspirada na F.R.I.D.A.Y. do MCU. Controla a armadura MK3, gerencia dispositivos IoT e executa comandos de voz de forma distribuída via rede local.

---

## 📋 Índice

- [Visão Geral](#-visão-geral)
- [Arquitetura](#-arquitetura)
- [Pré-requisitos](#-pré-requisitos)
- [Instalação Rápida](#-instalação-rápida)
- [Como Usar](#-como-usar)
- [Sistema de Plugins](#-sistema-de-plugins)
- [Adicionar Novo Satélite](#-adicionar-novo-satélite)
- [Firmwares ESP32](#-firmwares-esp32)
- [Estrutura de Pastas](#-estrutura-de-pastas)
- [Solução de Problemas](#-solução-de-problemas)

---

## 🌐 Visão Geral

O projeto é dividido em **3 camadas** que se comunicam pela rede local:

| Camada | Nome | Onde Roda | Função |
|--------|------|-----------|--------|
| 🧠 | **Cérebro Central** | Docker (qualquer PC/Raspberry Pi) | IA, processamento de voz, decisões |
| 💻 | **Satélite PC** | Nativo no Windows/Linux | Microfone, áudio, ações no SO |
| ⚡ | **Firmwares** | ESP32 (Arduino) | Servo da máscara, LEDs do reator |

### Fluxo de um Comando

```
Você fala: "Sexta-Feira, ative o protocolo de combate"
    │
    ▼
💻 Satélite PC: Grava áudio WAV → POST /processar_audio
    │
    ▼
🧠 Cérebro: Whisper (STT) → Groq LLM → Edge-TTS → MQTT
    │
    ├──► 💻 PC toca MP3: "Protocolo de combate ativado, chefe."
    ├──► ⚡ MQTT → mk3/mascara → ESP32 fecha máscara
    └──► ⚡ MQTT → mk3/reator → ESP32 modo vermelho
```

---

## 🏗️ Arquitetura

> 💡 **Nota:** O detalhamento técnico de cada nó da rede e as instruções de deploy via Docker Compose estarão disponíveis em breve.

---

## 📦 Pré-requisitos

### Para o Cérebro (Docker)
- **Docker Desktop** instalado ([download](https://www.docker.com/products/docker-desktop/))
- **Conta Groq** com API Key ([console.groq.com](https://console.groq.com))

### Para o Satélite PC
- **Python 3.10+** ([python.org](https://www.python.org))
- **Microfone** conectado ao PC
- **Caixas de som** para ouvir as respostas

### Para os ESP32 (Opcional)
- **Arduino IDE** com suporte a ESP32
- **Bibliotecas**: ESP32Servo, Adafruit NeoPixel

---

## 🚀 Instalação Rápida

### 1. Clone o repositório

```bash
git clone https://github.com/MozzieGM/sexta-feira.git
cd sexta_feira
```

### 2. Configure o Cérebro

```bash
# Edite o .env com sua API key
cd 1_cerebro_servidor
# No .env, coloque sua GROQ_API_KEY
# Ajuste os IPs dos ESP32 se necessário

# Suba os containers
docker-compose up -d

# Containers rebuild
docker-compose up --build -d

# Verifique se está online
curl http://localhost:8000/status
```

Resposta esperada:
```json
{
  "status": "online",
  "nome": "Sexta-Feira",
  "versao": "2.0.0",
  "componentes": {
    "stt": true,
    "tts": true,
    "cerebro": true,
    "mqtt": true,
    "plugins": 11
  }
}
```

### 3. Configure o Satélite PC

```bash
cd ../2_satelite_pc

# Instale as dependências
pip install -r requirements.txt

# Edite o .env
# CEREBRO_URL=http://localhost:8000  (mesmo PC)
# CEREBRO_URL=http://192.168.0.X:8000  (outro PC)

# Execute
python main_satelite.py
```

O HUD holográfico aparecerá na tela e o microfone começará a escutar. Diga **"Sexta-Feira"** seguido do seu comando.

### 4. (Opcional) Gere o .exe

```bash
# Gera executável standalone
build.bat

# O .exe estará em dist/SextaFeira_Satelite.exe
```

---

## 🎤 Como Usar

### Comandos de Voz
Sempre comece com **"Sexta-Feira"** seguido do comando:

| Comando | O que faz |
|---------|-----------|
| "Sexta-Feira, tudo bem?" | Conversa natural |
| "Sexta-Feira, abre o Chrome" | Abre programa no PC |
| "Sexta-Feira, toca Thunderstruck" | Busca e toca no YouTube |
| "Sexta-Feira, aumenta o volume" | Volume do sistema +50% |
| "Sexta-Feira, minimiza tudo" | Win+D no satélite |
| "Sexta-Feira, abre a máscara" | Servo da máscara MK3 |
| "Sexta-Feira, reator modo 5" | LEDs do reator arc |
| "Sexta-Feira, ativa protocolo de combate" | Liga reator + fecha máscara |
| "Sexta-Feira, anota isso: ..." | Salva em arquivo .txt |

### API de Debug (sem microfone)
Teste o cérebro enviando texto direto:

```bash
curl -X POST http://localhost:8000/comando_texto \
  -H "Content-Type: application/json" \
  -d '{"texto": "que horas são?"}'
```

---

## 🔌 Sistema de Plugins

O cérebro usa **auto-discovery de plugins**. Para adicionar uma nova funcionalidade:

### 1. Crie uma pasta para seu plugin

```
1_cerebro_servidor/app/plugins_integracoes/
└── meu_plugin/
    ├── __init__.py       # Vazio
    └── meu_modulo.py     # Seu código
```

### 2. Implemente a função `registrar()`

```python
# meu_modulo.py
import logging
logger = logging.getLogger("sexta.plugin.meu_plugin")

def _handler_minha_funcao(argumentos: dict) -> str:
    """Executa a ação do plugin."""
    valor = argumentos.get("parametro", "")
    # ... sua lógica aqui ...
    return f"Ação executada com {valor}."

def registrar(gerenciador):
    """Registra o plugin no sistema (chamado automaticamente)."""
    gerenciador.registrar_plugin(
        nome="minha_funcao",
        descricao="Descrição curta para o LLM saber quando usar.",
        parametros={
            "type": "object",
            "properties": {
                "parametro": {
                    "type": "string",
                    "description": "O que este parâmetro faz."
                }
            },
            "required": ["parametro"],
        },
        handler=_handler_minha_funcao,
    )
    logger.info("Meu plugin registrado!")
```

### 3. Reinicie o Cérebro

```bash
docker-compose restart cerebro
```

O plugin será detectado automaticamente. Verifique em `GET /plugins`.

---

## 🖥️ Adicionar Novo Satélite

Para instalar a Sexta-Feira em outro PC da casa:

1. **Copie a pasta `2_satelite_pc/`** para o novo PC
2. **Edite o `.env`** do novo satélite:
   ```
   CEREBRO_URL=http://IP_DO_CEREBRO:8000
   MQTT_HOST=IP_DO_CEREBRO
   NOME_COMODO=sala        # Nome único para este cômodo
   NOME_DISPOSITIVO=pc_sala
   ```
3. **Instale dependências**: `pip install -r requirements.txt`
4. **Execute**: `python main_satelite.py`

Cada satélite escuta seu próprio tópico MQTT (`casa/sala/pc/comando`), então comandos podem ser direcionados para PCs específicos.

---

## ⚡ Firmwares ESP32

Os firmwares ficam em `3_firmwares_hardware/`. São templates documentados:

### Máscara (armadura_mk3/mascara_servo.ino)
- Servo motor controlado via HTTP
- Endpoints: `/abrir`, `/fechar`, `/status`
- Ajuste `PINO_SERVO`, `ANGULO_ABERTA`, `ANGULO_FECHADA`

### Reator Arc (reator_arc/reator_leds.ino)
- 11 LEDs WS2812B com 10 modos de animação
- Endpoints: `/modo?v=N`, `/vel?v=N`, `/status`
- **Brilho máximo hardcoded** para proteção visual

### Upload para ESP32
1. Abra o `.ino` no Arduino IDE
2. Configure Wi-Fi (SSID e senha)
3. Selecione a placa "ESP32 Dev Module"
4. Faça upload
5. Anote o IP no Serial Monitor
6. Configure o IP no `.env` do Cérebro

---

## 📁 Estrutura de Pastas

```
sexta_feira/
│
├── 🧠 1_cerebro_servidor/          # Docker — Cérebro Central
│   ├── docker-compose.yml          # Orquestração dos containers
│   ├── Dockerfile                  # Build do container Python
│   ├── .env                        # Chaves e configurações
│   │
│   ├── mosquitto/
│   │   └── mosquitto.conf          # Config do broker MQTT
│   │
│   └── app/
│       ├── main_server.py          # FastAPI — porta de entrada
│       ├── requirements.txt        # Dependências Python
│       │
│       ├── ai_core/
│       │   ├── groq_brain.py       # LLM + tool calling
│       │   ├── stt_whisper.py      # Transcrição de áudio
│       │   └── tts_edge.py         # Síntese de voz
│       │
│       ├── plugins_integracoes/
│       │   ├── __init__.py         # Auto-discovery de plugins
│       │   ├── projetos_customizados/
│       │   │   ├── mk3_mascara_api.py   # Controle da máscara
│       │   │   └── mk3_reator_api.py    # Controle do reator
│       │   └── pc_commands/
│       │       └── windows_api.py  # Comandos via MQTT
│       │
│       └── network/
│           └── mqtt_publisher.py   # Publicador MQTT
│
├── 💻 2_satelite_pc/               # Nativo — Satélite PC
│   ├── main_satelite.py            # Ponto de entrada
│   ├── requirements.txt
│   ├── build.bat                   # Gera .exe
│   ├── .env                       # Config local
│   │
│   ├── ui/
│   │   └── hud_60fps.py           # HUD Tony Stark (Tkinter)
│   ├── senses/
│   │   ├── listener.py            # Microfone → HTTP
│   │   └── speaker.py             # Reproduz MP3
│   └── muscles/
│       ├── mqtt_listener.py       # Recebe comandos MQTT
│       ├── sys_manager.py         # Controle do SO
│       └── media_manager.py       # YouTube e mídia
│
└── ⚡ 3_firmwares_hardware/        # Arduino — ESP32
    ├── armadura_mk3/
    │   └── mascara_servo.ino      # Firmware da máscara
    └── reator_arc/
        └── reator_leds.ino        # Firmware do reator
```

---

## 🔧 Solução de Problemas

### Cérebro não inicia
```bash
# Verifique logs do Docker
docker-compose logs cerebro

# Verifique se a porta 8000 está livre
netstat -an | findstr 8000
```

### Satélite não conecta ao Cérebro
```bash
# Teste a conectividade
curl http://IP_DO_CEREBRO:8000/status

# Verifique o firewall do Windows
# Libere as portas 8000 (HTTP) e 1883 (MQTT)
```

### Microfone não detecta fala
- Verifique se o microfone está configurado como padrão no Windows
- Ajuste `energy_threshold` no `listener.py` (padrão: 300)
- Teste: `python -c "import speech_recognition as sr; print(sr.Microphone.list_microphone_names())"`

### ESP32 não responde
- Verifique IP no Serial Monitor do Arduino IDE
- `ping IP_DO_ESP32` para testar conectividade
- Configure IP fixo no roteador (DHCP Reservation)

### MQTT não funciona
```bash
# Teste publicando manualmente
mosquitto_pub -h localhost -t "casa/escritorio/pc/comando" \
  -m '{"acao":"abrir_programa","dados":{"nome_programa":"chrome"}}'
```

---

## 🛠️ Tecnologias

| Tecnologia | Uso |
|-----------|-----|
| **Python 3.11** | Linguagem principal |
| **FastAPI** | API HTTP do Cérebro |
| **Docker** | Containerização do Cérebro |
| **Mosquitto** | Broker MQTT |
| **Groq** | LLM (Llama 3.3 70B) + Whisper STT |
| **Edge-TTS** | Síntese de voz neural Microsoft |
| **Tkinter** | HUD (interface gráfica) |
| **pygame** | Reprodução de áudio |
| **pyautogui** | Controle de teclado/mouse |
| **ESP32** | Microcontrolador para hardware |

---

## 📄 Licença

Projeto pessoal desenvolvido por **Mozzie**.

---

> **"Até a próxima, chefe."** — Sexta-Feira
