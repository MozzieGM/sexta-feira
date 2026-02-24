# ============================================================
# SEXTA-FEIRA — HUD Interativo 60 FPS (Estilo Tony Stark)
# ============================================================
# Interface gráfica flutuante com animações em tempo real.
# Funciona como indicador visual do estado da IA:
#   - idle      → Azul calmo, rotação lenta
#   - escutando → Verde vibrante, respiração rápida
#   - pensando  → Amarelo, contração e giros frenéticos
#   - falando   → Ciano brilhante, ondas sonoras
#
# A janela é transparente, sem bordas, sempre no topo e
# arrastável pelo mouse. Roda a 60 FPS com easing suave.
# ============================================================

import time
import math
import random
import logging
import tkinter as tk

# Configura logging
logger = logging.getLogger("sexta.hud")


class SextaFeiraHUD:
    """
    HUD (Head-Up Display) da Sexta-Feira no estilo Tony Stark.
    
    Exibe um display holográfico flutuante com anéis concêntricos
    que reagem em tempo real ao estado da IA. Cada estado tem
    cores, velocidades e comportamentos visuais distintos.
    """

    def __init__(self, root: tk.Tk, estado_callback: callable = None):
        """
        Inicializa o HUD.

        Args:
            root: Janela principal do Tkinter.
            estado_callback: Função que retorna o estado atual da IA.
                            Se None, usa o estado interno.
        """
        self.root = root
        self._estado_callback = estado_callback
        self._estado_interno = "idle"

        # --- Configuração da janela ---
        self.root.overrideredirect(True)         # Remove bordas
        self.root.wm_attributes("-topmost", True)  # Sempre no topo
        self.root.wm_attributes("-transparentcolor", "black")  # Fundo transparente
        self.root.geometry("250x250+1100+100")   # Posição inicial na tela

        # --- Canvas para desenho ---
        self.canvas = tk.Canvas(
            root, width=250, height=250, bg="black", highlightthickness=0
        )
        self.canvas.pack()

        # --- CAMADAS DO HUD (do fundo para a frente) ---

        # Anel externo tracejado (decorativo, giro super lento)
        self.anel_ext = self.canvas.create_oval(
            15, 15, 235, 235, outline="#003344", width=2, dash=(2, 6)
        )

        # Arcos principais de processamento (dois arcos opostos)
        self.arco_grosso1 = self.canvas.create_arc(
            35, 35, 215, 215, start=0, extent=70,
            outline="#005577", width=4, style=tk.ARC
        )
        self.arco_grosso2 = self.canvas.create_arc(
            35, 35, 215, 215, start=180, extent=70,
            outline="#005577", width=4, style=tk.ARC
        )

        # Arcos finos internos invertidos (tracejados)
        self.arco_fino = self.canvas.create_arc(
            55, 55, 195, 195, start=90, extent=120,
            outline="#0088AA", width=2, style=tk.ARC, dash=(10, 5)
        )

        # Anel reativo (pulsa com a voz)
        self.anel_reativo = self.canvas.create_oval(
            80, 80, 170, 170, outline="#00E5FF", width=1
        )

        # Núcleo denso (centro do reator)
        self.nucleo = self.canvas.create_oval(
            100, 100, 150, 150, fill="#003344", outline="#00E5FF", width=2
        )

        # --- Eventos de arraste ---
        self.root.bind("<ButtonPress-1>", self._iniciar_arraste)
        self.root.bind("<B1-Motion>", self._arrastar)

        # --- Variáveis de física e animação ---
        self.rotacao_principal = 0.0
        self.rotacao_secundaria = 0.0
        self.rotacao_externa = 0.0

        self.raio_nuc = 25.0
        self.raio_nuc_alvo = 25.0
        self.raio_reativo = 45.0
        self.raio_reativo_alvo = 45.0

        # Cores atuais para transição suave (Color Easing)
        self.cor_atual_borda = "#005577"
        self.cor_atual_nucleo = "#003344"

        logger.info("HUD inicializado com sucesso.")

        # Inicia o loop de renderização
        self._atualizar_HUD()

    @property
    def estado(self) -> str:
        """Retorna o estado atual da IA (via callback ou interno)."""
        if self._estado_callback:
            return self._estado_callback()
        return self._estado_interno

    @estado.setter
    def estado(self, valor: str):
        """Define o estado interno da IA."""
        self._estado_interno = valor

    def _iniciar_arraste(self, event):
        """Registra posição inicial do mouse para arrastar a janela."""
        self._drag_x = event.x
        self._drag_y = event.y

    def _arrastar(self, event):
        """Move a janela seguindo o mouse."""
        x = self.root.winfo_x() + (event.x - self._drag_x)
        y = self.root.winfo_y() + (event.y - self._drag_y)
        self.root.geometry(f"+{x}+{y}")

    def _interpolar_cor(
        self, cor_atual: str, cor_alvo: str, velocidade: float = 0.1
    ) -> str:
        """
        Calcula o degradê frame a frame para transição suave de cores.

        Args:
            cor_atual: Cor atual em hexadecimal (#RRGGBB).
            cor_alvo: Cor alvo em hexadecimal.
            velocidade: Fator de interpolação (0.0 a 1.0).

        Returns:
            Nova cor interpolada em hexadecimal.
        """
        try:
            r1 = int(cor_atual[1:3], 16)
            g1 = int(cor_atual[3:5], 16)
            b1 = int(cor_atual[5:7], 16)

            r2 = int(cor_alvo[1:3], 16)
            g2 = int(cor_alvo[3:5], 16)
            b2 = int(cor_alvo[5:7], 16)

            r = int(r1 + (r2 - r1) * velocidade)
            g = int(g1 + (g2 - g1) * velocidade)
            b = int(b1 + (b2 - b1) * velocidade)

            return f"#{r:02x}{g:02x}{b:02x}"
        except (ValueError, IndexError):
            return cor_alvo

    def _atualizar_HUD(self):
        """
        Loop principal de renderização a 60 FPS.
        Atualiza cores, rotações e tamanhos baseado no estado da IA.
        """
        t = time.time()
        estado_atual = self.estado

        # --- LÓGICA DE ESTADOS ---
        if estado_atual == "idle":
            # Azul calmo, respiração suave
            cor_alvo = "#0088AA"
            cor_nuc_alvo = "#002233"
            self.raio_nuc_alvo = 25 + math.sin(t * 2) * 2
            self.raio_reativo_alvo = 45 + math.sin(t * 1.5) * 3
            vel_prin, vel_sec, vel_ext = 40, -30, 5

        elif estado_atual == "escutando":
            # Verde vibrante, respiração rápida (alerta)
            cor_alvo = "#00FF66"
            cor_nuc_alvo = "#005522"
            self.raio_nuc_alvo = 28 + math.sin(t * 8) * 4
            self.raio_reativo_alvo = 55
            vel_prin, vel_sec, vel_ext = 150, -120, 20

        elif estado_atual == "pensando":
            # Amarelo, contração e giros frenéticos
            cor_alvo = "#FFCC00"
            cor_nuc_alvo = "#664400"
            self.raio_nuc_alvo = 15  # Contrai como se processasse
            self.raio_reativo_alvo = 35 + math.sin(t * 15) * 2
            vel_prin, vel_sec, vel_ext = -250, 300, -50

        elif estado_atual == "falando":
            # Ciano brilhante, ondas sonoras
            cor_alvo = "#00E5FF"
            cor_nuc_alvo = "#007799"
            if random.random() > 0.4:
                self.raio_nuc_alvo = random.uniform(20, 40)
                self.raio_reativo_alvo = random.uniform(45, 75)
            vel_prin, vel_sec, vel_ext = 90, -70, 15

        else:
            # Estado desconhecido — fallback para idle
            cor_alvo = "#0088AA"
            cor_nuc_alvo = "#002233"
            self.raio_nuc_alvo = 25
            self.raio_reativo_alvo = 45
            vel_prin, vel_sec, vel_ext = 40, -30, 5

        # --- APLICAÇÃO DA FÍSICA (EASING) ---
        dt = 0.016  # ~60 FPS

        # Suavização dos raios
        self.raio_nuc += (self.raio_nuc_alvo - self.raio_nuc) * 0.15
        self.raio_reativo += (self.raio_reativo_alvo - self.raio_reativo) * 0.2

        # Rotações independentes
        self.rotacao_principal = (self.rotacao_principal + vel_prin * dt) % 360
        self.rotacao_secundaria = (self.rotacao_secundaria + vel_sec * dt) % 360
        self.rotacao_externa = (self.rotacao_externa + vel_ext * dt) % 360

        # Suavização das Cores
        self.cor_atual_borda = self._interpolar_cor(
            self.cor_atual_borda, cor_alvo, 0.08
        )
        self.cor_atual_nucleo = self._interpolar_cor(
            self.cor_atual_nucleo, cor_nuc_alvo, 0.08
        )

        # --- DESENHO NA TELA ---
        cx, cy = 125, 125  # Centro da tela (250/2)

        # Atualiza cores de todos os elementos
        self.canvas.itemconfig(self.arco_grosso1, outline=self.cor_atual_borda)
        self.canvas.itemconfig(self.arco_grosso2, outline=self.cor_atual_borda)
        self.canvas.itemconfig(self.arco_fino, outline=self.cor_atual_borda)
        self.canvas.itemconfig(self.anel_reativo, outline=self.cor_atual_borda)
        self.canvas.itemconfig(
            self.nucleo, fill=self.cor_atual_nucleo, outline=self.cor_atual_borda
        )

        # Atualiza ângulos de rotação
        self.canvas.itemconfig(self.arco_grosso1, start=self.rotacao_principal)
        self.canvas.itemconfig(self.arco_grosso2, start=self.rotacao_principal + 180)
        self.canvas.itemconfig(self.arco_fino, start=self.rotacao_secundaria)

        # Atualiza tamanhos (raios dinâmicos)
        rn = self.raio_nuc
        self.canvas.coords(self.nucleo, cx - rn, cy - rn, cx + rn, cy + rn)

        rr = self.raio_reativo
        self.canvas.coords(
            self.anel_reativo, cx - rr, cy - rr, cx + rr, cy + rr
        )

        # Agenda próximo frame (~60 FPS)
        self.root.after(16, self._atualizar_HUD)
