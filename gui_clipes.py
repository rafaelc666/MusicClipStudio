"""
gerador_clipes_musicais/gui_clipes.py
Interface gráfica para o Gerador de Clipes Musicais — estilo Elton Studio V2.
"""

import sys
from pathlib import Path
import json
import threading

try:
    import customtkinter as ctk
    from tkinter import filedialog, messagebox
except ImportError:
    print("ERRO: Instale dependências:\n  pip install customtkinter pillow")
    sys.exit(1)

# Adiciona paths
BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

from MusicClipStudio.theme import Tema
from MusicClipStudio.config import ClipConfig, load_config, save_config
from MusicClipStudio.database import StockDatabase, StockMedia
from MusicClipStudio.agent import ClipAgent, AgentMood, AgentStyle


class GuiClipes(ctk.CTk):
    """GUI principal do MusicClipStudio."""

    # Ordem canonica das etapas do fluxo. Fonte unica da verdade:
    # usada pela sidebar, pelo indicator do topo, pela navegacao
    # (Voltar / Avancar) e pela validacao.
    PASSOS_ORDEM = ["letra", "legenda", "audio", "imagens", "midia", "gerar"]

    # Rotulos e numeracao da sidebar (mesma ordem acima)
    NAV_ITEMS = [
        ("letra", "Letra", "01"),
        ("legenda", "Legenda", "02"),
        ("audio", "Áudio", "03"),
        ("imagens", "Imagens", "04"),
        ("midia", "Mídia", "05"),
        ("gerar", "Gerar", "06"),
    ]

    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self.title("MusicClipStudio - Gerador de Clipes Musicais")
        self.geometry("1400x850")
        self.minsize(1000, 600)
        self.configure(fg_color=Tema.FUNDO)

        self._config = load_config()
        self._passo_atual = "letra"
        self._db = StockDatabase(self._config)
        self._agent = ClipAgent(self._config)
        self._midia_selecionada = []
        self._imagens_geradas = []
        self._passo_labels = {}
        self._nav_btns = {}
        self._frames_passos = {}
        self._conteudo_passos = None
        self._linhas_legenda: list[dict] = []
        self._analise_cache = None                # (chave, AnaliseAudio)

        # Ortografia / divergência entre a caixa de letra e a legenda
        self._dic_pt = None                       # DicionarioPT (índice ~4s)
        self._suspeitas: list = []                # PalavraSuspeita na tela
        self._ignoradas: set[str] = set()         # palavras que o usuário cravou
        self._legenda_origem = ""                 # "transcricao" | "letra" | ""
        self._legenda_snapshot = ""               # letra usada p/ montar a legenda
        self.var_mood = ctk.StringVar(value="epic")
        self.var_estilo = ctk.StringVar(value="cinematic")
        # Preferencia de tipo de midia na busca automatica. "Meio a meio"
        # preserva o comportamento antigo (foto + video intercalados).
        self.var_tipo_midia = ctk.StringVar(value="Meio a meio")
        self._bases_fallback: list[str] = []      # bases p/ prompts de IA
        self._trilha_path: str | None = None      # trilha gerada na etapa Áudio
        self._trilha_gerando = False

        self._construir_ui()

    # ════════════════════════════════════════════════════════════
    #  CONSTRUÇÃO DA UI
    # ════════════════════════════════════════════════════════════

    def _construir_ui(self):
        self.grid_columnconfigure(0, weight=0, minsize=Tema.SIDEBAR_LARGURA)
        self.grid_columnconfigure(1, weight=3)
        self.grid_columnconfigure(2, weight=0, minsize=Tema.PAINEL_DIREITO_LARGURA)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)

        self._construir_top_bar()
        self._construir_sidebar_navegacao()
        self._construir_conteudo_principal()
        self._construir_painel_direito()

    def _construir_top_bar(self):
        topbar = ctk.CTkFrame(self, fg_color=Tema.PAINEL, height=Tema.TOPBAR_ALTURA, corner_radius=0)
        topbar.grid(row=0, column=0, columnspan=3, sticky="ew")
        topbar.grid_propagate(False)
        topbar.grid_columnconfigure(2, weight=1)

        # Título do documento atual (o logo já vive na sidebar)
        ctk.CTkLabel(
            topbar, text="Novo clipe musical",
            font=Tema.fonte(Tema.FONTE_MEDIA, negrito=True),
            text_color=Tema.TEXTO_CLARO,
        ).grid(row=0, column=1, padx=Tema.ESP_4, pady=Tema.ESP_3, sticky="w")

        # Botões
        btn_frame = ctk.CTkFrame(topbar, fg_color="transparent")
        btn_frame.grid(row=0, column=2, padx=Tema.ESP_4, pady=Tema.ESP_2, sticky="e")

        ctk.CTkButton(
            btn_frame, text="APIs", width=80, height=Tema.ALTURA_BOTAO,
            command=self._abrir_config_apis,
            fg_color=Tema.CARTAO, hover_color=Tema.CARTAO_HOVER,
            text_color=Tema.TEXTO_CLARO, font=Tema.fonte(Tema.FONTE_BASE),
            border_width=1, border_color=Tema.BORDA_SUAVIZADA,
            corner_radius=Tema.RAIO_BOTAO,
        ).pack(side="left", padx=(0, Tema.ESP_2))

        # Guardamos a referência: o botão da topbar e o da etapa 5 precisam
        # ser habilitados/desabilitados em conjunto durante a geração (B2).
        self._btn_gerar_topbar = ctk.CTkButton(
            btn_frame, text="Gerar", width=90, height=Tema.ALTURA_BOTAO,
            command=self._gerar_clip,
            fg_color=Tema.PRIMARY, hover_color=Tema.PRIMARY_HOVER,
            text_color=Tema.TEXTO_SOBRE_PRIMARIA,
            font=Tema.fonte(Tema.FONTE_BASE, negrito=True),
            corner_radius=Tema.RAIO_BOTAO,
        )
        self._btn_gerar_topbar.pack(side="left")
        self.btn_gerar = self._btn_gerar_topbar

    def _construir_sidebar_navegacao(self):
        sidebar = ctk.CTkFrame(
            self, fg_color=Tema.NAV_BG, corner_radius=0, width=Tema.SIDEBAR_LARGURA,
        )
        sidebar.grid(row=1, column=0, sticky="nsew")
        sidebar.grid_propagate(False)

        # Cabeçalho da sidebar (marca)
        cabecalho = ctk.CTkFrame(sidebar, fg_color="transparent")
        cabecalho.pack(fill="x", padx=Tema.ESP_4, pady=(Tema.ESP_5, Tema.ESP_5))

        ctk.CTkLabel(
            cabecalho, text="MusicClipStudio",
            font=Tema.fonte(Tema.FONTE_GRANDE, negrito=True),
            text_color=Tema.TEXTO_CLARO,
        ).pack(anchor="w")
        ctk.CTkLabel(
            cabecalho, text="Gerador de clipes",
            font=Tema.fonte(Tema.FONTE_MICRO),
            text_color=Tema.TEXTO_SUTIL,
        ).pack(anchor="w")

        # Rótulo da seção
        ctk.CTkLabel(
            sidebar, text="FLUXO",
            font=Tema.fonte(Tema.FONTE_MICRO, negrito=True),
            text_color=Tema.TEXTO_SUTIL,
        ).pack(anchor="w", padx=Tema.ESP_4, pady=(0, Tema.ESP_2))

        nav_items = self.NAV_ITEMS

        for key, label, numero in nav_items:
            btn = ctk.CTkButton(
                sidebar, text=f"  {numero}   {label}",
                width=Tema.SIDEBAR_LARGURA - Tema.ESP_4 * 2,
                height=Tema.ALTURA_BOTAO,
                command=lambda k=key: self._mudar_passo(k),
                fg_color="transparent", hover_color=Tema.HOVER,
                text_color=Tema.TEXTO_DIM, font=Tema.fonte(Tema.FONTE_BASE),
                corner_radius=Tema.RAIO_BOTAO, anchor="w",
            )
            btn.pack(pady=2, padx=Tema.ESP_2)
            self._nav_btns[key] = btn

        # Espaçador
        ctk.CTkLabel(sidebar, text="", fg_color="transparent").pack(expand=True)

        # Config
        ctk.CTkButton(
            sidebar, text="  Configurações",
            width=Tema.SIDEBAR_LARGURA - Tema.ESP_4 * 2,
            height=Tema.ALTURA_BOTAO,
            command=self._abrir_config_apis,
            fg_color="transparent", hover_color=Tema.HOVER,
            text_color=Tema.TEXTO_DIM, font=Tema.fonte(Tema.FONTE_BASE),
            corner_radius=Tema.RAIO_BOTAO, anchor="w",
        ).pack(pady=(0, Tema.ESP_4), padx=Tema.ESP_2)

        self._mudar_passo("letra")

    def _construir_conteudo_principal(self):
        self._conteudo_frame = ctk.CTkFrame(
            self, fg_color=Tema.FUNDO, corner_radius=0,
        )
        self._conteudo_frame.grid(row=1, column=1, sticky="nsew")

        # Passos indicator
        self._construir_passos_indicator()

        # Conteúdo
        self._conteudo_passos = ctk.CTkFrame(self._conteudo_frame, fg_color="transparent")
        self._conteudo_passos.pack(fill="both", expand=True, padx=16, pady=(8, 16))

        self._frames_passos = {}
        self._criar_frame_letra()
        self._criar_frame_legenda()
        self._criar_frame_audio()
        self._criar_frame_imagens()
        self._criar_frame_midia()
        self._criar_frame_gerar()

        self._mostrar_passo("letra")

    def _construir_passos_indicator(self):
        indicator = ctk.CTkFrame(
            self._conteudo_frame, fg_color=Tema.PAINEL,
            height=Tema.INDICADOR_ALTURA, corner_radius=0,
        )
        indicator.pack(fill="x")
        indicator.pack_propagate(False)

        passos = [
            ("letra", "Letra", "Em edição"),
            ("legenda", "Legenda", "Aguardando"),
            ("audio", "Áudio", "Aguardando"),
            ("imagens", "Imagens", "Aguardando"),
            ("midia", "Mídia", "Aguardando"),
            ("gerar", "Gerar", "Aguardando"),
        ]

        for idx, (key, label, status) in enumerate(passos):
            frame = ctk.CTkFrame(indicator, fg_color="transparent")
            frame.pack(side="left", padx=Tema.ESP_4, pady=Tema.ESP_3)

            # Número do passo (estilo Elton Studio)
            icon_label = ctk.CTkLabel(
                frame, text=f"{idx + 1:02d}",
                font=Tema.fonte(Tema.FONTE_BASE, negrito=True),
                text_color=Tema.STEP_PENDENTE,
            )
            icon_label.pack(side="left", padx=(0, Tema.ESP_2))

            text_frame = ctk.CTkFrame(frame, fg_color="transparent")
            text_frame.pack(side="left")

            title = ctk.CTkLabel(
                text_frame, text=label,
                font=Tema.fonte(Tema.FONTE_BASE, negrito=True),
                text_color=Tema.TEXTO_DIM,
            )
            title.pack(anchor="w")

            subtitle = ctk.CTkLabel(
                text_frame, text=status,
                font=Tema.fonte(Tema.FONTE_MICRO),
                text_color=Tema.TEXTO_DIM,
            )
            subtitle.pack(anchor="w")

            self._passo_labels[key] = {
                "icon": icon_label, "title": title, "subtitle": subtitle,
            }

            # Separador entre passos (não depois do último)
            if idx < len(passos) - 1:
                ctk.CTkLabel(
                    indicator, text="›",
                    font=Tema.fonte(Tema.FONTE_GRANDE),
                    text_color=Tema.TEXTO_SUTIL,
                ).pack(side="left")

    def _criar_frame_letra(self):
        frame = ctk.CTkFrame(self._conteudo_passos, fg_color="transparent")
        self._frames_passos["letra"] = frame

        ctk.CTkLabel(
            frame, text="ETAPA 01 · LETRA",
            font=Tema.fonte(Tema.FONTE_PEQUENA, negrito=True),
            text_color=Tema.TEXTO_DIM,
        ).pack(anchor="w", pady=(0, Tema.ESP_1))

        ctk.CTkLabel(
            frame, text="Letra da Música",
            font=Tema.fonte(Tema.FONTE_TITULO, negrito=True),
            text_color=Tema.TEXTO_CLARO,
        ).pack(anchor="w", pady=(0, Tema.ESP_1))

        ctk.CTkLabel(
            frame, text="Cole ou digite a letra da música para gerar o clipe.",
            font=Tema.fonte(Tema.FONTE_MEDIA),
            text_color=Tema.TEXTO_DIM,
        ).pack(anchor="w", pady=(0, Tema.ESP_4))

        # Card
        card = ctk.CTkFrame(frame, fg_color=Tema.CARTAO, corner_radius=Tema.RAIO_CARD)
        card.pack(fill="both", expand=True)

        ctk.CTkLabel(
            card, text="TEXTO DA MÚSICA",
            font=Tema.fonte(Tema.FONTE_PEQUENA, negrito=True),
            text_color=Tema.TEXTO_DIM,
        ).pack(anchor="w", padx=Tema.ESP_4, pady=(Tema.ESP_3, Tema.ESP_2))

        self.txt_letra = ctk.CTkTextbox(
            card, height=300,
            fg_color=Tema.FUNDO, text_color=Tema.TEXTBOX_TEXTO,
            font=Tema.fonte(Tema.FONTE_MEDIA), wrap="word",
            border_width=1, border_color=Tema.BORDA_SUAVIZADA,
        )
        self.txt_letra.pack(fill="both", expand=True, padx=Tema.ESP_4, pady=(0, Tema.ESP_4))
        self._aplicar_placeholder_letra()

        # Botões
        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(fill="x", padx=Tema.ESP_4, pady=(0, Tema.ESP_4))

        ctk.CTkButton(
            btn_frame, text="Carregar arquivo", width=140, height=Tema.ALTURA_BOTAO,
            command=self._carregar_letra_arquivo,
            fg_color=Tema.CARTAO_HOVER, hover_color=Tema.HOVER,
            text_color=Tema.TEXTO_CLARO, font=Tema.fonte(Tema.FONTE_BASE),
            border_width=1, border_color=Tema.BORDA_SUAVIZADA,
            corner_radius=Tema.RAIO_BOTAO,
        ).pack(side="left")

        ctk.CTkButton(
            btn_frame, text="Avançar →", width=120, height=Tema.ALTURA_BOTAO,
            command=lambda: self._mudar_passo("legenda"),
            fg_color=Tema.PRIMARY, hover_color=Tema.PRIMARY_HOVER,
            text_color=Tema.TEXTO_SOBRE_PRIMARIA,
            font=Tema.fonte(Tema.FONTE_BASE, negrito=True),
            corner_radius=Tema.RAIO_BOTAO,
        ).pack(side="right")

    PLACEHOLDER_LETRA = (
        "Cole aqui a letra da música...\n\n"
        "Ex.:\n"
        "  Quando a noite cai sobre a cidade\n"
        "  Eu ainda escuto a tua voz\n"
        "\n"
        "Dica: use \"Carregar arquivo\" para importar um .txt"
    )

    def _aplicar_placeholder_letra(self):
        """Mostra um texto-guia no campo de letra enquanto ele está vazio."""
        caixa = self.txt_letra
        caixa.insert("1.0", self.PLACEHOLDER_LETRA)
        caixa.configure(text_color=Tema.TEXTO_SUTIL)
        self._letra_vazia = True

        def ao_focar(_evt=None):
            if getattr(self, "_letra_vazia", False):
                caixa.delete("1.0", "end")
                caixa.configure(text_color=Tema.TEXTBOX_TEXTO)
                self._letra_vazia = False

        def ao_sair(_evt=None):
            if not caixa.get("1.0", "end").strip():
                caixa.delete("1.0", "end")
                caixa.insert("1.0", self.PLACEHOLDER_LETRA)
                caixa.configure(text_color=Tema.TEXTO_SUTIL)
                self._letra_vazia = True
            self._atualizar_resumo_clipe()
            self._atualizar_divergencia()

        caixa.bind("<FocusIn>", ao_focar)
        caixa.bind("<FocusOut>", ao_sair)

    def _letra_atual(self) -> str:
        """Devolve a letra digitada, ignorando o placeholder."""
        if not hasattr(self, "txt_letra"):
            return ""
        if getattr(self, "_letra_vazia", False):
            return ""
        return self.txt_letra.get("1.0", "end").strip()

    @staticmethod
    def _texto_chave(texto: str) -> str:
        """Normaliza dois textos para comparar (ignora espaços e caixa)."""
        return " ".join((texto or "").split()).strip().lower()

    def _letra_da_legenda(self) -> str:
        """Junta o texto das linhas da etapa 02 ("" se não houver linhas)."""
        textos: list[str] = []
        for linha in getattr(self, "_linhas_legenda", None) or []:
            try:
                texto = linha["texto"].get().strip()
            except Exception:
                continue
            if texto:
                textos.append(texto)
        return "\n".join(textos)

    def _letra_oficial(self) -> str:
        """A letra que alimenta a busca, a interpretação e o resumo.

        Decisão do usuário ("a legenda, e me avisa"): a LEGENDA é a fonte
        da verdade, porque é ela que guarda os tempos reais que o Whisper
        produziu. A caixa da etapa 01 só vale enquanto não existir
        legenda — letra colada na mão e ninguém passou pela etapa 02.

        Era aqui o defeito: a busca lia sempre a etapa 01. Corrigir
        "vois" → "voz" na etapa 02 não mudava nada, e o clipe continuava
        procurando a palavra errada no banco de mídia.
        """
        return self._letra_da_legenda() or self._letra_atual()

    def _letra_diverge(self) -> bool:
        """True quando a caixa da etapa 01 e a legenda não dizem o mesmo."""
        legenda = self._letra_da_legenda()
        if not legenda:
            return False
        return self._texto_chave(legenda) != self._texto_chave(self._letra_atual())

    def _criar_frame_legenda(self):
        """Etapa 02: conferir e editar a legenda antes de gravar.

        Só faz sentido quando a letra veio de transcrição automática. Se
        o usuário digitou a letra, ele já sabe o que está lá e a etapa
        aparece apenas como conferência.
        """
        frame = ctk.CTkFrame(self._conteudo_passos, fg_color="transparent")
        self._frames_passos["legenda"] = frame

        frame.grid_rowconfigure(4, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            frame, text="ETAPA 02 · LEGENDA",
            font=Tema.fonte(Tema.FONTE_PEQUENA, negrito=True),
            text_color=Tema.TEXTO_DIM,
        ).grid(row=0, column=0, sticky="w", pady=(0, Tema.ESP_1))

        ctk.CTkLabel(
            frame, text="Revisar Legenda",
            font=Tema.fonte(Tema.FONTE_TITULO, negrito=True),
            text_color=Tema.TEXTO_CLARO,
        ).grid(row=1, column=0, sticky="w", pady=(0, Tema.ESP_1))

        # Linha de status + botão de transcrever
        barra = ctk.CTkFrame(frame, fg_color=Tema.CARTAO, corner_radius=Tema.RAIO_CARD)
        barra.grid(row=2, column=0, sticky="ew", pady=(0, Tema.ESP_3))
        barra.grid_columnconfigure(1, weight=1)
        self._barra_legenda = barra

        self._btn_transcrever = ctk.CTkButton(
            barra, text="Transcrever do áudio", width=170,
            height=Tema.ALTURA_BOTAO,
            command=self._transcrever_letra,
            fg_color=Tema.PRIMARY, hover_color=Tema.PRIMARY_HOVER,
            text_color=Tema.TEXTO_SOBRE_PRIMARIA,
            font=Tema.fonte(Tema.FONTE_BASE, negrito=True),
            corner_radius=Tema.RAIO_BOTAO,
        )
        self._btn_transcrever.grid(row=0, column=0, padx=Tema.ESP_3, pady=Tema.ESP_3)

        # Ortografia: o Whisper acerta a fonética e erra a grafia
        # ("voz" vira "vois"). Sem revisar, o erro vai para a busca.
        self._btn_ortografia = ctk.CTkButton(
            barra, text="Revisar ortografia", width=150,
            height=Tema.ALTURA_BOTAO,
            command=self._revisar_ortografia,
            fg_color=Tema.CARTAO_HOVER, hover_color=Tema.HOVER,
            text_color=Tema.TEXTO_CLARO,
            font=Tema.fonte(Tema.FONTE_BASE),
            border_width=1, border_color=Tema.BORDA_SUAVIZADA,
            corner_radius=Tema.RAIO_BOTAO,
        )
        self._btn_ortografia.grid(row=0, column=2, padx=(0, Tema.ESP_3),
                                  pady=Tema.ESP_3)

        self.lbl_legenda_status = ctk.CTkLabel(
            barra,
            text="Sem transcrição ainda. Use a letra digitada ou transcreva o áudio.",
            font=Tema.fonte(Tema.FONTE_BASE),
            text_color=Tema.TEXTO_DIM, anchor="w",
        )
        self.lbl_legenda_status.grid(row=0, column=1, sticky="w",
                                     padx=(0, Tema.ESP_3), pady=Tema.ESP_3)

        # Aviso de divergência: etapa 01 x legenda. Começa vazio (sem
        # texto o label não ocupa altura), então não empurra o layout.
        self._lbl_divergencia = ctk.CTkLabel(
            barra, text="", font=Tema.fonte(Tema.FONTE_PEQUENA),
            text_color=Tema.AVISO, anchor="w", justify="left",
            wraplength=680,
        )
        self._lbl_divergencia.grid(row=1, column=0, columnspan=2,
                                   sticky="w", padx=Tema.ESP_3,
                                   pady=(0, Tema.ESP_3))

        self._btn_usar_legenda = ctk.CTkButton(
            barra, text="Usar a legenda na etapa 01", height=26, width=180,
            command=self._espelhar_legenda_na_letra,
            fg_color="transparent", hover_color=Tema.HOVER,
            text_color=Tema.TEXTO_CLARO,
            font=Tema.fonte(Tema.FONTE_PEQUENA),
            border_width=1, border_color=Tema.AVISO,
            corner_radius=Tema.RAIO_BOTAO,
        )

        # ── Ortografia (só aparece depois de clicar em revisar) ──────
        self._card_ortografia = ctk.CTkFrame(
            frame, fg_color=Tema.CARTAO, corner_radius=Tema.RAIO_CARD,
        )
        self._card_ortografia.grid_columnconfigure(0, weight=1)

        topo_orto = ctk.CTkFrame(self._card_ortografia, fg_color="transparent")
        topo_orto.grid(row=0, column=0, sticky="ew",
                       padx=Tema.ESP_3, pady=(Tema.ESP_3, Tema.ESP_1))
        topo_orto.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            topo_orto, text="ORTÓGRAFIA",
            font=Tema.fonte(Tema.FONTE_PEQUENA, negrito=True),
            text_color=Tema.TEXTO_DIM,
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            topo_orto, text="Aplicar as óbvias", height=26, width=130,
            command=self._aplicar_obvias,
            fg_color="transparent", border_width=1,
            border_color=Tema.BORDA, text_color=Tema.TEXTO,
            font=Tema.fonte(Tema.FONTE_PEQUENA),
            corner_radius=Tema.RAIO_BOTAO,
        ).grid(row=0, column=1, sticky="e")

        self._orto_aviso = ctk.CTkLabel(
            self._card_ortografia, text="",
            font=Tema.fonte(Tema.FONTE_PEQUENA),
            text_color=Tema.TEXTO_DIM, anchor="w", justify="left",
            wraplength=740,
        )
        self._orto_aviso.grid(row=1, column=0, sticky="w",
                              padx=Tema.ESP_3, pady=(0, Tema.ESP_2))

        self._orto_lista = ctk.CTkFrame(self._card_ortografia,
                                        fg_color="transparent")
        self._orto_lista.grid(row=2, column=0, sticky="ew",
                              padx=Tema.ESP_2, pady=(0, Tema.ESP_2))
        self._orto_lista.grid_columnconfigure(0, weight=1)

        # Lista de linhas editáveis
        lista_card = ctk.CTkFrame(frame, fg_color=Tema.CARTAO,
                                  corner_radius=Tema.RAIO_CARD)
        lista_card.grid(row=4, column=0, sticky="nsew")
        lista_card.grid_rowconfigure(1, weight=1)
        lista_card.grid_columnconfigure(0, weight=1)

        cabecalho = ctk.CTkFrame(lista_card, fg_color="transparent")
        cabecalho.grid(row=0, column=0, sticky="ew",
                       padx=Tema.ESP_3, pady=(Tema.ESP_3, Tema.ESP_1))

        ctk.CTkLabel(
            cabecalho, text="LINHAS DA LEGENDA",
            font=Tema.fonte(Tema.FONTE_PEQUENA, negrito=True),
            text_color=Tema.TEXTO_DIM,
        ).pack(side="left")

        self.lbl_legenda_total = ctk.CTkLabel(
            cabecalho, text="0 linhas",
            font=Tema.fonte(Tema.FONTE_PEQUENA, negrito=True),
            text_color=Tema.PRIMARY,
        )
        self.lbl_legenda_total.pack(side="right")

        self._legenda_scroll = ctk.CTkScrollableFrame(
            lista_card, fg_color=Tema.FUNDO, corner_radius=Tema.RAIO_BOTAO,
        )
        self._legenda_scroll.grid(row=1, column=0, sticky="nsew",
                                  padx=Tema.ESP_2, pady=(0, Tema.ESP_2))

        self._linhas_legenda: list[dict] = []
        self._mostrar_vazio_legenda()

        # Botões de navegação
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.grid(row=5, column=0, sticky="ew", pady=(Tema.ESP_3, 0))

        ctk.CTkButton(
            btn_frame, text="← Voltar", width=100, height=Tema.ALTURA_BOTAO,
            command=lambda: self._mudar_passo("letra"),
            fg_color=Tema.CARTAO_HOVER, hover_color=Tema.HOVER,
            text_color=Tema.TEXTO_CLARO, font=Tema.fonte(Tema.FONTE_BASE),
            corner_radius=Tema.RAIO_BOTAO,
        ).pack(side="left")

        ctk.CTkButton(
            btn_frame, text="Avançar →", width=120, height=Tema.ALTURA_BOTAO,
            command=lambda: self._mudar_passo("audio"),
            fg_color=Tema.PRIMARY, hover_color=Tema.PRIMARY_HOVER,
            text_color=Tema.TEXTO_SOBRE_PRIMARIA,
            font=Tema.fonte(Tema.FONTE_BASE, negrito=True),
            corner_radius=Tema.RAIO_BOTAO,
        ).pack(side="right")

    def _mostrar_vazio_legenda(self):
        """Estado vazio da lista de legenda."""
        for w in self._legenda_scroll.winfo_children():
            w.destroy()
        vazio = ctk.CTkFrame(self._legenda_scroll, fg_color="transparent")
        vazio.pack(expand=True, pady=Tema.ESP_5)
        self._vazio_legenda_widget = vazio
        ctk.CTkLabel(
            vazio, text="≡",
            font=Tema.fonte(Tema.FONTE_DISPLAY),
            text_color=Tema.TEXTO_SUTIL,
        ).pack()
        ctk.CTkLabel(
            vazio, text="Nenhuma linha ainda",
            font=Tema.fonte(Tema.FONTE_GRANDE, negrito=True),
            text_color=Tema.TEXTO_CLARO,
        ).pack(pady=(Tema.ESP_2, Tema.ESP_1))
        ctk.CTkLabel(
            vazio,
            text="Volte para a etapa 1 e escreva a letra, ou clique em\n"
                 "\"Transcrever do áudio\" para o Whisper ouvir a música.",
            font=Tema.fonte(Tema.FONTE_BASE),
            text_color=Tema.TEXTO_DIM, justify="center",
        ).pack()

    def _limpar_vazio_legenda(self):
        """Remove o placeholder de vazio se ele estiver na tela.

        O estado vazio e' um frame solto dentro do scroll (nao esta em
        `_linhas_legenda`), entao `winfo_children()` seria destrutivo
        demais — precisamos distinguir placeholder de linha real.
        Marcamos o placeholder em `_vazio_legenda_widget`.
        """
        w = getattr(self, "_vazio_legenda_widget", None)
        if w is not None:
            try:
                w.destroy()
            except Exception:
                pass
            self._vazio_legenda_widget = None

    def _criar_frame_audio(self):
        """Etapa Áudio: prompt da trilha, duração e geração via ACE-Step."""
        frame = ctk.CTkFrame(self._conteudo_passos, fg_color="transparent")
        self._frames_passos["audio"] = frame

        ctk.CTkLabel(
            frame, text="ETAPA 03 · ÁUDIO",
            font=Tema.fonte(Tema.FONTE_PEQUENA, negrito=True),
            text_color=Tema.TEXTO_DIM,
        ).pack(anchor="w", pady=(0, Tema.ESP_1))

        ctk.CTkLabel(
            frame, text="Trilha Sonora",
            font=Tema.fonte(Tema.FONTE_TITULO, negrito=True),
            text_color=Tema.TEXTO_CLARO,
        ).pack(anchor="w", pady=(0, Tema.ESP_1))

        ctk.CTkLabel(
            frame, text="Configure e gere a trilha sonora do clipe.",
            font=Tema.fonte(Tema.FONTE_MEDIA),
            text_color=Tema.TEXTO_DIM,
        ).pack(anchor="w", pady=(0, Tema.ESP_4))

        card = ctk.CTkFrame(frame, fg_color=Tema.CARTAO, corner_radius=Tema.RAIO_CARD)
        card.pack(fill="both", expand=True)

        # Prompt da música
        ctk.CTkLabel(
            card, text="PROMPT DA MÚSICA",
            font=Tema.fonte(Tema.FONTE_PEQUENA, negrito=True),
            text_color=Tema.TEXTO_DIM,
        ).pack(anchor="w", padx=16, pady=(12, 4))

        self.txt_music_prompt = ctk.CTkTextbox(
            card, height=80,
            fg_color=Tema.FUNDO, text_color=Tema.TEXTBOX_TEXTO,
            font=Tema.fonte(Tema.FONTE_BASE), wrap="word",
            border_width=1, border_color=Tema.BORDA_SUAVIZADA,
        )
        self.txt_music_prompt.pack(fill="x", padx=16, pady=(0, 8))
        self.txt_music_prompt.insert("1.0", self._config.default_music_prompt)

        # Duração da trilha
        ctk.CTkLabel(
            card, text="Duração da trilha (segundos)",
            font=Tema.fonte(Tema.FONTE_BASE),
            text_color=Tema.TEXTO_DIM,
        ).pack(anchor="w", padx=16, pady=(8, 4))

        self.var_music_duration = ctk.IntVar(value=self._config.default_music_duration)
        ctk.CTkSlider(
            card, from_=10, to=120,
            variable=self.var_music_duration,
            progress_color=Tema.PRIMARY, button_color=Tema.PRIMARY,
        ).pack(fill="x", padx=16, pady=(0, 4))

        ctk.CTkLabel(
            card, textvariable=self.var_music_duration,
            text_color=Tema.TEXTO_DIM, font=Tema.fonte(Tema.FONTE_PEQUENA),
        ).pack(anchor="e", padx=16, pady=(0, 8))

        # Status da trilha
        self.lbl_trilha_status = ctk.CTkLabel(
            card, text="Nenhuma trilha gerada. O clipe será gerado sem áudio.",
            font=Tema.fonte(Tema.FONTE_PEQUENA),
            text_color=Tema.TEXTO_DIM,
        )
        self.lbl_trilha_status.pack(anchor="w", padx=16, pady=(0, 8))

        # Botões da etapa
        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(fill="x", padx=16, pady=(0, 16))

        ctk.CTkButton(
            btn_frame, text="← Voltar", width=100, height=Tema.ALTURA_BOTAO,
            command=lambda: self._mudar_passo("legenda"),
            fg_color=Tema.CARTAO_HOVER, hover_color=Tema.HOVER,
            text_color=Tema.TEXTO_CLARO, font=Tema.fonte(Tema.FONTE_BASE),
            corner_radius=Tema.RAIO_BOTAO,
        ).pack(side="left")

        ctk.CTkButton(
            btn_frame, text="Gerar Áudio", width=120, height=Tema.ALTURA_BOTAO,
            command=self._gerar_trilha_ace,
            fg_color=Tema.PRIMARY, hover_color=Tema.PRIMARY_HOVER,
            text_color=Tema.TEXTO_SOBRE_PRIMARIA,
            font=Tema.fonte(Tema.FONTE_BASE, negrito=True),
            corner_radius=Tema.RAIO_BOTAO,
        ).pack(side="right")

        ctk.CTkButton(
            btn_frame, text="Avançar →", width=120, height=Tema.ALTURA_BOTAO,
            command=lambda: self._mudar_passo("imagens"),
            fg_color=Tema.CARTAO_HOVER, hover_color=Tema.HOVER,
            text_color=Tema.TEXTO, font=Tema.fonte(Tema.FONTE_BASE),
        ).pack(side="right", padx=(0, 8))

    def _gerar_trilha_ace(self):
        """Gera a trilha sonora via ACE-Step (audio.gerar_trilha)."""
        if self._trilha_gerando:
            return

        prompt = self.txt_music_prompt.get("1.0", "end").strip()
        if not prompt:
            messagebox.showwarning("Aviso", "Escreva um prompt para a música.")
            return

        duracao = int(self.var_music_duration.get())
        self._trilha_gerando = True
        self.lbl_trilha_status.configure(text="Gerando trilha (pode levar alguns minutos)...", text_color=Tema.AVISO)
        self._log("[AUDIO] Gerando trilha via ACE-Step...")

        def gerar():
            caminho = None
            erro = None
            try:
                from MusicClipStudio.audio import gerar_trilha
                caminho = gerar_trilha(prompt=prompt, duracao=duracao)
            except Exception as e:
                erro = e

            def finalizar():
                self._trilha_gerando = False
                if caminho:
                    self._trilha_path = caminho
                    self.lbl_trilha_status.configure(
                        text=f"Trilha pronta: {Path(caminho).name}",
                        text_color=Tema.SUCESSO,
                    )
                    self._log(f"[OK] Trilha gerada: {caminho}")
                else:
                    msg = f"[ERROR] Falha na geração da trilha: {erro}" if erro else "[ERROR] ACE-Step não disponível — trilha não gerada."
                    self.lbl_trilha_status.configure(
                        text="Falha na geração da trilha. O clipe será gerado sem áudio.",
                        text_color=Tema.DESTRUIVA,
                    )
                    self._log(msg)

                self._atualizar_resumo_clipe()

            self.after(0, finalizar)

        threading.Thread(target=gerar, daemon=True).start()

    def _criar_frame_imagens(self):
        """Cria o frame de busca/geração de imagens."""
        frame = ctk.CTkFrame(self._conteudo_passos, fg_color="transparent")
        self._frames_passos["imagens"] = frame

        # Layout: topo compacto + galeria grande
        frame.grid_rowconfigure(3, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            frame, text="ETAPA 04 · IMAGENS",
            font=Tema.fonte(Tema.FONTE_PEQUENA, negrito=True),
            text_color=Tema.TEXTO_DIM,
        ).grid(row=0, column=0, sticky="w", padx=Tema.ESP_5, pady=(Tema.ESP_3, 0))

        ctk.CTkLabel(
            frame, text="Buscar ou Gerar Imagens",
            font=Tema.fonte(Tema.FONTE_TITULO, negrito=True),
            text_color=Tema.TEXTO_CLARO,
        ).grid(row=1, column=0, sticky="w", padx=Tema.ESP_5, pady=(0, Tema.ESP_3))

        # === BARRA DE BUSCA COMPACTA ===
        busca_card = ctk.CTkFrame(frame, fg_color=Tema.CARTAO, corner_radius=8)
        busca_card.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 10))

        busca_row = ctk.CTkFrame(busca_card, fg_color="transparent")
        busca_row.pack(fill="x", padx=12, pady=8)

        ctk.CTkButton(
            busca_row, text="Buscar Automaticamente", width=200, height=Tema.ALTURA_BOTAO,
            command=self._busca_automatica,
            fg_color=Tema.SUCESSO, hover_color=Tema.SUCESSO_HOVER,
            text_color=Tema.TEXTO_SOBRE_PRIMARIA, font=Tema.fonte(Tema.FONTE_BASE, negrito=True),
        ).pack(side="left")

        self.lbl_auto_status = ctk.CTkLabel(
            busca_row, text="",
            text_color=Tema.TEXTO_DIM, font=Tema.fonte(Tema.FONTE_PEQUENA),
        )
        self.lbl_auto_status.pack(side="left", padx=(12, 0))

        # Tipo de mídia: controla se a busca puxa vídeo, foto, ou os dois.
        # O texto precisa ser ESCURO: o segmento selecionado fica verde
        # (PRIMARY), e o TEXTO claro padrão desaparecia sobre ele.
        ctk.CTkSegmentedButton(
            busca_row,
            values=["Meio a meio", "Mais vídeos", "Mais fotos"],
            variable=self.var_tipo_midia,
            fg_color=Tema.CARTAO, selected_color=Tema.PRIMARY,
            selected_hover_color=Tema.PRIMARY_HOVER,
            unselected_color=Tema.CARTAO,
            unselected_hover_color=Tema.CARTAO_HOVER,
            text_color=Tema.TEXTO_SOBRE_PRIMARIA, height=26,
            font=Tema.fonte(Tema.FONTE_PEQUENA),
        ).pack(side="left", padx=(12, 0))

        # Separador
        sep = ctk.CTkLabel(
            busca_row, text="│",
            text_color=Tema.BORDA, font=Tema.fonte(Tema.FONTE_GRANDE),
        )
        sep.pack(side="left", padx=(16, 16))

        # IA prompt inline
        ctk.CTkLabel(
            busca_row, text="Prompt IA:",
            font=Tema.fonte(Tema.FONTE_PEQUENA),
            text_color=Tema.TEXTO_DIM,
        ).pack(side="left")

        self.txt_prompt = ctk.CTkEntry(
            busca_row, placeholder_text="Epic concert scene...",
            fg_color=Tema.FUNDO, text_color=Tema.TEXTO,
            width=220,
        )
        self.txt_prompt.pack(side="left", padx=(6, 8))
        self.txt_prompt.insert(0, "Epic concert scene with dramatic lighting")

        # Mood / Estilo para o agente (restaurado)
        ctk.CTkOptionMenu(
            busca_row,
            values=[m.value for m in AgentMood],
            variable=self.var_mood,
            fg_color=Tema.CARTAO, button_color=Tema.PRIMARY,
            text_color=Tema.TEXTO, width=95, height=26,
        ).pack(side="left", padx=(0, 4))

        ctk.CTkOptionMenu(
            busca_row,
            values=[s.value for s in AgentStyle],
            variable=self.var_estilo,
            fg_color=Tema.CARTAO, button_color=Tema.PRIMARY,
            text_color=Tema.TEXTO, width=100, height=26,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            busca_row, text="Gerar IA", width=70, height=28,
            command=self._gerar_imagem_ia,
            fg_color=Tema.PRIMARY, hover_color=Tema.PRIMARY_HOVER,
            text_color=Tema.TEXTO_SOBRE_PRIMARIA, font=Tema.fonte(Tema.FONTE_PEQUENA, negrito=True),
        ).pack(side="left")

        ctk.CTkButton(
            busca_row, text="Auto-prompt", width=85, height=28,
            command=self._auto_gerar_prompt,
            fg_color=Tema.CARTAO_HOVER, hover_color=Tema.HOVER,
            text_color=Tema.TEXTO, font=Tema.fonte(Tema.FONTE_PEQUENA),
        ).pack(side="left", padx=(6, 0))

        # === GALERIA DE RESULTADOS (ocupa todo espaço) ===
        galeria_container = ctk.CTkFrame(frame, fg_color=Tema.CARTAO, corner_radius=8)
        galeria_container.grid(row=3, column=0, sticky="nsew", padx=20, pady=(0, 10))
        galeria_container.grid_rowconfigure(1, weight=1)
        galeria_container.grid_columnconfigure(0, weight=1)

        # Header galeria
        galeria_header = ctk.CTkFrame(galeria_container, fg_color="transparent")
        galeria_header.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 0))

        ctk.CTkLabel(
            galeria_header, text="RESULTADOS",
            font=Tema.fonte(Tema.FONTE_PEQUENA, negrito=True),
            text_color=Tema.TEXTO_DIM,
        ).pack(side="left")

        self.lbl_qtd_selecionadas = ctk.CTkLabel(
            galeria_header, text="0 selecionados",
            text_color=Tema.PRIMARY, font=Tema.fonte(Tema.FONTE_PEQUENA, negrito=True),
        )
        self.lbl_qtd_selecionadas.pack(side="right")

        # Galeria scrollável
        self._galeria_frame = ctk.CTkScrollableFrame(
            galeria_container, fg_color=Tema.FUNDO, corner_radius=6,
        )
        self._galeria_frame.grid(row=1, column=0, sticky="nsew", padx=8, pady=(8, 8))

        vazio = ctk.CTkFrame(self._galeria_frame, fg_color="transparent")
        vazio.pack(expand=True, pady=Tema.ESP_6)

        ctk.CTkLabel(
            vazio, text="◫",
            font=Tema.fonte(Tema.FONTE_DISPLAY),
            text_color=Tema.TEXTO_SUTIL,
        ).pack()
        ctk.CTkLabel(
            vazio, text="Nenhuma mídia carregada ainda",
            font=Tema.fonte(Tema.FONTE_GRANDE, negrito=True),
            text_color=Tema.TEXTO_CLARO,
        ).pack(pady=(Tema.ESP_2, Tema.ESP_1))
        ctk.CTkLabel(
            vazio,
            text="Use \"Buscar Automaticamente\" para puxar imagens e vídeos\n"
                 "a partir da letra, ou gere uma imagem com IA pelo prompt ao lado.",
            font=Tema.fonte(Tema.FONTE_BASE),
            text_color=Tema.TEXTO_DIM, justify="center",
        ).pack()

        # === BOTÕES DE AÇÃO ===
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.grid(row=4, column=0, sticky="ew", padx=20, pady=(0, 10))

        ctk.CTkButton(
            btn_frame, text="← Voltar", width=100, height=Tema.ALTURA_BOTAO,
            command=lambda: self._mudar_passo("audio"),
            fg_color=Tema.CARTAO_HOVER, hover_color=Tema.HOVER,
            text_color=Tema.TEXTO_CLARO, font=Tema.fonte(Tema.FONTE_BASE),
            corner_radius=Tema.RAIO_BOTAO,
        ).pack(side="left")

        ctk.CTkButton(
            btn_frame, text="Avançar →", width=120, height=Tema.ALTURA_BOTAO,
            command=lambda: self._mudar_passo("midia"),
            fg_color=Tema.PRIMARY, hover_color=Tema.PRIMARY_HOVER,
            text_color=Tema.TEXTO_SOBRE_PRIMARIA,
            font=Tema.fonte(Tema.FONTE_BASE, negrito=True),
            corner_radius=Tema.RAIO_BOTAO,
        ).pack(side="right")

    def _criar_frame_midia(self):
        frame = ctk.CTkFrame(self._conteudo_passos, fg_color="transparent")
        self._frames_passos["midia"] = frame

        ctk.CTkLabel(
            frame, text="ETAPA 05 · MÍDIA",
            font=Tema.fonte(Tema.FONTE_PEQUENA, negrito=True),
            text_color=Tema.TEXTO_DIM,
        ).pack(anchor="w", pady=(0, Tema.ESP_1))

        ctk.CTkLabel(
            frame, text="Imagens e Vídeos",
            font=Tema.fonte(Tema.FONTE_TITULO, negrito=True),
            text_color=Tema.TEXTO_CLARO,
        ).pack(anchor="w", pady=(0, Tema.ESP_1))

        ctk.CTkLabel(
            frame, text="Busque imagens e vídeos ou adicione seus próprios arquivos.",
            font=Tema.fonte(Tema.FONTE_MEDIA),
            text_color=Tema.TEXTO_DIM,
        ).pack(anchor="w", pady=(0, Tema.ESP_4))

        # Card
        card = ctk.CTkFrame(frame, fg_color=Tema.CARTAO, corner_radius=Tema.RAIO_CARD)
        card.pack(fill="both", expand=True)

        # Busca
        search_frame = ctk.CTkFrame(card, fg_color="transparent")
        search_frame.pack(fill="x", padx=16, pady=(12, 8))

        ctk.CTkLabel(
            search_frame, text="Buscar mídia:",
            font=Tema.fonte(Tema.FONTE_BASE),
            text_color=Tema.TEXTO_DIM,
        ).pack(side="left", padx=(0, 8))

        self.entry_search = ctk.CTkEntry(
            search_frame, placeholder_text="Ex: concert, music, stage...",
            fg_color=Tema.FUNDO, text_color=Tema.TEXTO,
            width=300,
        )
        self.entry_search.pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            search_frame, text="Buscar", width=100, height=Tema.ALTURA_BOTAO,
            command=self._buscar_midia,
            fg_color=Tema.PRIMARY, hover_color=Tema.PRIMARY_HOVER,
            text_color=Tema.TEXTO_SOBRE_PRIMARIA, font=Tema.fonte(Tema.FONTE_BASE, negrito=True),
        ).pack(side="left")

        # Provider — ⚠️ NOVO (24/09/2026): "todos" consulta os 7 bancos e
        # intercala (pesquisar_multi); default da tela passou a ser "todos"
        # porque buscar num banco só era a causa do "sempre vem coisa do
        # Pexels". Config antigo com provider específico continua valendo.
        _prov_inicial = self._config.stock_provider
        if _prov_inicial in ("", "pexels"):
            _prov_inicial = "todos"
        self.var_provider = ctk.StringVar(value=_prov_inicial)
        ctk.CTkOptionMenu(
            search_frame,
            values=["todos", "pexels", "pixabay", "unsplash", "nasa",
                    "coverr", "giphy", "openverse"],
            variable=self.var_provider,
            fg_color=Tema.CARTAO, button_color=Tema.PRIMARY,
            text_color=Tema.TEXTO, width=120,
        ).pack(side="left", padx=(8, 0))

        # Área de resultados
        self._resultados_frame = ctk.CTkScrollableFrame(
            card, fg_color=Tema.FUNDO, corner_radius=8,
        )
        self._resultados_frame.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        ctk.CTkLabel(
            self._resultados_frame,
            text="Resultados da busca aparecerão aqui.",
            text_color=Tema.TEXTO_DIM, font=Tema.fonte(Tema.FONTE_BASE),
        ).pack(expand=True, pady=40)

        # Botões
        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(fill="x", padx=16, pady=(0, 16))

        ctk.CTkButton(
            btn_frame, text="← Voltar", width=100, height=Tema.ALTURA_BOTAO,
            command=lambda: self._mudar_passo("imagens"),
            fg_color=Tema.CARTAO_HOVER, hover_color=Tema.HOVER,
            text_color=Tema.TEXTO_CLARO, font=Tema.fonte(Tema.FONTE_BASE),
            corner_radius=Tema.RAIO_BOTAO,
        ).pack(side="left")

        ctk.CTkButton(
            btn_frame, text="+ Adicionar arquivo", width=140, height=Tema.ALTURA_BOTAO,
            command=self._adicionar_arquivo_midia,
            fg_color=Tema.CARTAO_HOVER, hover_color=Tema.HOVER,
            text_color=Tema.TEXTO, font=Tema.fonte(Tema.FONTE_BASE),
        ).pack(side="left", padx=(8, 0))

        ctk.CTkButton(
            btn_frame, text="Avançar →", width=120, height=Tema.ALTURA_BOTAO,
            command=lambda: self._mudar_passo("gerar"),
            fg_color=Tema.PRIMARY, hover_color=Tema.PRIMARY_HOVER,
            text_color=Tema.TEXTO_SOBRE_PRIMARIA,
            font=Tema.fonte(Tema.FONTE_BASE, negrito=True),
            corner_radius=Tema.RAIO_BOTAO,
        ).pack(side="right")

    def _criar_frame_gerar(self):
        frame = ctk.CTkFrame(self._conteudo_passos, fg_color="transparent")
        self._frames_passos["gerar"] = frame

        ctk.CTkLabel(
            frame, text="ETAPA 06 · GERAR",
            font=Tema.fonte(Tema.FONTE_PEQUENA, negrito=True),
            text_color=Tema.TEXTO_DIM,
        ).pack(anchor="w", pady=(0, Tema.ESP_1))

        ctk.CTkLabel(
            frame, text="Gerar Clipe",
            font=Tema.fonte(Tema.FONTE_TITULO, negrito=True),
            text_color=Tema.TEXTO_CLARO,
        ).pack(anchor="w", pady=(0, Tema.ESP_1))

        ctk.CTkLabel(
            frame, text="Revise as configurações e gere o clipe musical.",
            font=Tema.fonte(Tema.FONTE_MEDIA),
            text_color=Tema.TEXTO_DIM,
        ).pack(anchor="w", pady=(0, Tema.ESP_4))

        # Card
        card = ctk.CTkFrame(frame, fg_color=Tema.CARTAO, corner_radius=Tema.RAIO_CARD)
        card.pack(fill="both", expand=True)

        # Resumo (conteúdo real — atualizado por _atualizar_resumo_clipe)
        resumo_card = ctk.CTkFrame(card, fg_color=Tema.FUNDO, corner_radius=Tema.RAIO_BOTAO)
        resumo_card.pack(fill="x", padx=Tema.ESP_4, pady=(Tema.ESP_4, Tema.ESP_2))

        ctk.CTkLabel(
            resumo_card, text="RESUMO DO CLIPE",
            font=Tema.fonte(Tema.FONTE_PEQUENA, negrito=True),
            text_color=Tema.TEXTO_DIM,
        ).pack(anchor="w", padx=Tema.ESP_3, pady=(Tema.ESP_2, Tema.ESP_1))

        self.lbl_resumo = ctk.CTkLabel(
            resumo_card, text="",
            font=Tema.fonte(Tema.FONTE_BASE),
            text_color=Tema.TEXTO, justify="left",
        )
        self.lbl_resumo.pack(anchor="w", padx=Tema.ESP_3, pady=(0, Tema.ESP_2))

        # Nota: Formato e FPS vivem no painel direito (fonte única de verdade).
        ctk.CTkLabel(
            card,
            text="Formato, FPS, efeitos e legendas ficam no painel à direita →",
            font=Tema.fonte(Tema.FONTE_MICRO),
            text_color=Tema.TEXTO_SUTIL,
        ).pack(anchor="w", padx=Tema.ESP_4, pady=(0, Tema.ESP_2))

        # Botão gerar
        self.btn_gerar = ctk.CTkButton(
            card, text="GERAR CLIPE MUSICAL",
            width=240, height=Tema.ALTURA_BOTAO_GRANDE,
            command=self._gerar_clip,
            fg_color=Tema.PRIMARY, hover_color=Tema.PRIMARY_HOVER,
            text_color=Tema.TEXTO_SOBRE_PRIMARIA,
            font=Tema.fonte(Tema.FONTE_GRANDE, negrito=True),
            corner_radius=Tema.RAIO_BOTAO,
        )
        self.btn_gerar.pack(anchor="center", pady=(Tema.ESP_4, Tema.ESP_4))
        self._btn_gerar_passo5 = self.btn_gerar

        # Progresso
        self.barra_progresso = ctk.CTkProgressBar(
            card, progress_color=Tema.PRIMARY, fg_color=Tema.BLOQUEADO, height=6,
        )
        self.barra_progresso.set(0)
        self.barra_progresso.pack(fill="x", padx=Tema.ESP_4, pady=(0, Tema.ESP_2))

        self.lbl_status = ctk.CTkLabel(
            card, text="Pronto para gerar",
            text_color=Tema.TEXTO_DIM, font=Tema.fonte(Tema.FONTE_BASE),
        )
        self.lbl_status.pack(pady=(0, Tema.ESP_4))

        self._atualizar_resumo_clipe()

    def _atualizar_resumo_clipe(self):
        """Reflete o estado real do clipe no resumo da etapa 5 (nada fixo)."""
        if not hasattr(self, "lbl_resumo"):
            return

        letra = self._letra_oficial()
        n_linhas = len([ln for ln in letra.splitlines() if ln.strip()])
        if letra:
            letra_txt = f"✓ {n_linhas} linha(s) de letra"
        else:
            letra_txt = "— sem letra"

        if self._trilha_path:
            trilha_txt = f"✓ {Path(self._trilha_path).name}"
        else:
            trilha_txt = "— trilha não gerada"

        n_midia = len(self._midia_selecionada)
        if n_midia:
            midia_txt = f"✓ {n_midia} item(ns) selecionado(s)"
        else:
            midia_txt = "— nenhuma mídia selecionada"

        self.lbl_resumo.configure(
            text=f"• Letra: {letra_txt}\n• Áudio: {trilha_txt}\n• Mídia: {midia_txt}"
        )

    def _construir_painel_direito(self):
        panel = ctk.CTkFrame(self, fg_color=Tema.PAINEL, corner_radius=0)
        panel.grid(row=1, column=2, sticky="nsew", padx=(1, 0))

        scroll = ctk.CTkScrollableFrame(panel, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=8, pady=8)

        # Configurações de Legenda
        ctk.CTkLabel(
            scroll, text="LEGENDAS",
            font=Tema.fonte(Tema.FONTE_PEQUENA, negrito=True),
            text_color=Tema.TEXTO_DIM,
        ).pack(anchor="w", pady=(0, Tema.ESP_2))

        # Ativar legendas
        self.var_lyrics_active = ctk.BooleanVar(value=self._config.lyrics_active)
        ctk.CTkSwitch(
            scroll, text="Mostrar letras",
            variable=self.var_lyrics_active,
            fg_color=Tema.CARTAO, progress_color=Tema.PRIMARY,
            text_color=Tema.TEXTO,
        ).pack(anchor="w", pady=(0, 8))

        # Posição
        ctk.CTkLabel(
            scroll, text="Posição:",
            text_color=Tema.TEXTO_DIM, font=Tema.fonte(Tema.FONTE_PEQUENA),
        ).pack(anchor="w", pady=(0, Tema.ESP_1))

        self.var_lyrics_pos = ctk.StringVar(value=self._config.lyrics_position)
        ctk.CTkOptionMenu(
            scroll, values=["top", "center", "bottom"],
            variable=self.var_lyrics_pos,
            fg_color=Tema.CARTAO, button_color=Tema.PRIMARY,
            text_color=Tema.TEXTO, width=240,
        ).pack(fill="x", pady=(0, 8))

        # Tamanho da fonte
        ctk.CTkLabel(
            scroll, text="Tamanho da fonte:",
            text_color=Tema.TEXTO_DIM, font=Tema.fonte(Tema.FONTE_PEQUENA),
        ).pack(anchor="w", pady=(0, Tema.ESP_1))

        self.var_font_size = ctk.IntVar(value=self._config.lyrics_font_size)
        ctk.CTkSlider(
            scroll, from_=24, to=96,
            variable=self.var_font_size,
            progress_color=Tema.PRIMARY, button_color=Tema.PRIMARY,
        ).pack(fill="x", pady=(0, 4))

        # Separador
        ctk.CTkFrame(scroll, fg_color=Tema.BORDA, height=1).pack(fill="x", pady=8)

        # Agente de Imagens
        ctk.CTkLabel(
            scroll, text="AGENTE DE IMAGENS",
            font=Tema.fonte(Tema.FONTE_PEQUENA, negrito=True),
            text_color=Tema.TEXTO_DIM,
        ).pack(anchor="w", pady=(0, Tema.ESP_2))

        self.var_agent = ctk.BooleanVar(value=self._config.agent_enabled)
        ctk.CTkSwitch(
            scroll, text="Ativar agente IA",
            variable=self.var_agent,
            fg_color=Tema.CARTAO, progress_color=Tema.PRIMARY,
            text_color=Tema.TEXTO,
        ).pack(anchor="w", pady=(0, 8))

        # Estilo
        ctk.CTkLabel(
            scroll, text="Estilo visual:",
            text_color=Tema.TEXTO_DIM, font=Tema.fonte(Tema.FONTE_PEQUENA),
        ).pack(anchor="w", pady=(0, Tema.ESP_1))

        self.var_agent_style = ctk.StringVar(value=self._config.agent_style)
        ctk.CTkOptionMenu(
            scroll, values=["cinematic", "documentary", "music_video", "artistic"],
            variable=self.var_agent_style,
            fg_color=Tema.CARTAO, button_color=Tema.PRIMARY,
            text_color=Tema.TEXTO, width=240,
        ).pack(fill="x", pady=(0, 8))

        # Separador
        ctk.CTkFrame(scroll, fg_color=Tema.BORDA, height=1).pack(fill="x", pady=8)

        # ── CONFIGURAÇÕES DE VÍDEO ──────────────────────────
        ctk.CTkLabel(
            scroll, text="VÍDEO",
            font=Tema.fonte(Tema.FONTE_PEQUENA, negrito=True),
            text_color=Tema.TEXTO_DIM,
        ).pack(anchor="w", pady=(0, Tema.ESP_2))

        # Duração total
        ctk.CTkLabel(
            scroll, text="Duração total (segundos):",
            text_color=Tema.TEXTO_DIM, font=Tema.fonte(Tema.FONTE_PEQUENA),
        ).pack(anchor="w", pady=(0, Tema.ESP_1))

        self.var_video_duration = ctk.IntVar(value=self._config.default_music_duration)
        ctk.CTkSlider(
            scroll, from_=10, to=180,
            variable=self.var_video_duration,
            progress_color=Tema.PRIMARY, button_color=Tema.PRIMARY,
        ).pack(fill="x", pady=(0, 4))

        ctk.CTkLabel(
            scroll, textvariable=self.var_video_duration,
            text_color=Tema.TEXTO_DIM, font=Tema.fonte(Tema.FONTE_PEQUENA),
        ).pack(anchor="e", pady=(0, 8))

        # FPS
        ctk.CTkLabel(
            scroll, text="FPS:",
            text_color=Tema.TEXTO_DIM, font=Tema.fonte(Tema.FONTE_PEQUENA),
        ).pack(anchor="w", pady=(0, Tema.ESP_1))

        self.var_video_fps = ctk.StringVar(value=str(self._config.default_video_fps))
        ctk.CTkOptionMenu(
            scroll, values=["24", "25", "30", "60"],
            variable=self.var_video_fps,
            fg_color=Tema.CARTAO, button_color=Tema.PRIMARY,
            text_color=Tema.TEXTO, width=240,
        ).pack(fill="x", pady=(0, 8))

        # Formato
        ctk.CTkLabel(
            scroll, text="Formato:",
            text_color=Tema.TEXTO_DIM, font=Tema.fonte(Tema.FONTE_PEQUENA),
        ).pack(anchor="w", pady=(0, Tema.ESP_1))

        self.var_video_format = ctk.StringVar(value=self._config.default_video_format)
        ctk.CTkOptionMenu(
            scroll, values=["9/16", "16/9", "1:1", "4:5"],
            variable=self.var_video_format,
            fg_color=Tema.CARTAO, button_color=Tema.PRIMARY,
            text_color=Tema.TEXTO, width=240,
        ).pack(fill="x", pady=(0, 8))

        # Separador
        ctk.CTkFrame(scroll, fg_color=Tema.BORDA, height=1).pack(fill="x", pady=8)

        # ── EFEITOS ─────────────────────────────────────────
        ctk.CTkLabel(
            scroll, text="EFEITOS",
            font=Tema.fonte(Tema.FONTE_PEQUENA, negrito=True),
            text_color=Tema.TEXTO_DIM,
        ).pack(anchor="w", pady=(0, Tema.ESP_2))

        # Efeito de imagem
        ctk.CTkLabel(
            scroll, text="Efeito nas imagens:",
            text_color=Tema.TEXTO_DIM, font=Tema.fonte(Tema.FONTE_PEQUENA),
        ).pack(anchor="w", pady=(0, Tema.ESP_1))

        self.var_effect = ctk.StringVar(value=self._config.default_effect)
        ctk.CTkOptionMenu(
            scroll, values=[
                "zoom_in", "zoom_out", "zoom_in_out", "zoom_diagonal",
                "pan_left", "pan_right", "pan_up", "pan_down",
                "dolly_zoom", "shake", "parallax", "orbital",
                "blur_reveal", "depth_of_field",
                "fade_in", "fade_out",
                "corte",
            ],
            variable=self.var_effect,
            fg_color=Tema.CARTAO, button_color=Tema.PRIMARY,
            text_color=Tema.TEXTO, width=240,
        ).pack(fill="x", pady=(0, 8))

        # Transição
        ctk.CTkLabel(
            scroll, text="Transição entre cenas:",
            text_color=Tema.TEXTO_DIM, font=Tema.fonte(Tema.FONTE_PEQUENA),
        ).pack(anchor="w", pady=(0, Tema.ESP_1))

        self.var_transition = ctk.StringVar(value=self._config.default_transition)
        ctk.CTkOptionMenu(
            scroll, values=[
                "fade", "fade_in", "fade_out", "fade_through_white",
                "slide_left", "slide_right", "slide_up", "slide_down",
                "wipe_linear", "wipe_radial", "iris",
                "split_reveal_horizontal", "split_reveal_vertical",
                "pixelate_reveal", "zoom_reveal",
            ],
            variable=self.var_transition,
            fg_color=Tema.CARTAO, button_color=Tema.PRIMARY,
            text_color=Tema.TEXTO, width=240,
        ).pack(fill="x", pady=(0, 8))

        # Duração do efeito
        ctk.CTkLabel(
            scroll, text="Duração por imagem (segundos):",
            text_color=Tema.TEXTO_DIM, font=Tema.fonte(Tema.FONTE_PEQUENA),
        ).pack(anchor="w", pady=(0, Tema.ESP_1))

        self.var_effect_duration = ctk.DoubleVar(value=5.0)
        ctk.CTkSlider(
            scroll, from_=2.0, to=15.0,
            variable=self.var_effect_duration,
            progress_color=Tema.PRIMARY, button_color=Tema.PRIMARY,
        ).pack(fill="x", pady=(0, 4))

        ctk.CTkLabel(
            scroll, textvariable=self.var_effect_duration,
            text_color=Tema.TEXTO_DIM, font=Tema.fonte(Tema.FONTE_PEQUENA),
        ).pack(anchor="e", pady=(0, 8))

        # Separador
        ctk.CTkFrame(scroll, fg_color=Tema.BORDA, height=1).pack(fill="x", pady=8)

        # ── RITMO (cálculo automático) ──────────────────────
        # A partir daqui os clipes deixam de ser "duração total / n mídias"
        # e passam a ser derivados da música.
        ctk.CTkLabel(
            scroll, text="RITMO DO CORTE",
            font=Tema.fonte(Tema.FONTE_PEQUENA, negrito=True),
            text_color=Tema.TEXTO_DIM,
        ).pack(anchor="w", pady=(0, Tema.ESP_2))

        self.var_ritmo_modo = ctk.StringVar(value="Pela letra (frases)")
        ctk.CTkOptionMenu(
            scroll, values=[
                "Pela letra (frases)",
                "Pela batida da música",
                "Duração fixa",
            ],
            variable=self.var_ritmo_modo,
            command=lambda _v: self._atualizar_previsao_plano(),
            fg_color=Tema.CARTAO, button_color=Tema.PRIMARY,
            text_color=Tema.TEXTO, width=240,
        ).pack(fill="x", pady=(0, 8))

        # Frase maior que isto é fatiada em partes
        ctk.CTkLabel(
            scroll, text="Duração máxima por clipe (s):",
            text_color=Tema.TEXTO_DIM, font=Tema.fonte(Tema.FONTE_PEQUENA),
        ).pack(anchor="w", pady=(0, Tema.ESP_1))

        self.var_max_por_clipe = ctk.DoubleVar(value=6.0)
        ctk.CTkSlider(
            scroll, from_=1.5, to=20.0,
            variable=self.var_max_por_clipe,
            command=lambda _v: self._atualizar_previsao_plano(),
            progress_color=Tema.PRIMARY, button_color=Tema.PRIMARY,
        ).pack(fill="x", pady=(0, 4))

        ctk.CTkLabel(
            scroll, textvariable=self.var_max_por_clipe,
            text_color=Tema.TEXTO_DIM, font=Tema.fonte(Tema.FONTE_PEQUENA),
        ).pack(anchor="e", pady=(0, 8))

        # Tolerância antes de fatiar
        ctk.CTkLabel(
            scroll, text="Tolerância antes de fatiar (%):",
            text_color=Tema.TEXTO_DIM, font=Tema.fonte(Tema.FONTE_PEQUENA),
        ).pack(anchor="w", pady=(0, Tema.ESP_1))

        self.var_tolerancia = ctk.DoubleVar(value=20.0)
        ctk.CTkSlider(
            scroll, from_=0.0, to=60.0,
            variable=self.var_tolerancia,
            command=lambda _v: self._atualizar_previsao_plano(),
            progress_color=Tema.PRIMARY, button_color=Tema.PRIMARY,
        ).pack(fill="x", pady=(0, 4))

        ctk.CTkLabel(
            scroll, textvariable=self.var_tolerancia,
            text_color=Tema.TEXTO_DIM, font=Tema.fonte(Tema.FONTE_PEQUENA),
        ).pack(anchor="e", pady=(0, 8))

        # Batidas por troca (modo "pela batida")
        ctk.CTkLabel(
            scroll, text="Batidas por troca de cena:",
            text_color=Tema.TEXTO_DIM, font=Tema.fonte(Tema.FONTE_PEQUENA),
        ).pack(anchor="w", pady=(0, Tema.ESP_1))

        self.var_batidas_por_troca = ctk.IntVar(value=8)
        ctk.CTkOptionMenu(
            scroll, values=["2", "4", "6", "8", "12", "16", "24", "32"],
            variable=self.var_batidas_por_troca,
            command=lambda _v: self._atualizar_previsao_plano(),
            fg_color=Tema.CARTAO, button_color=Tema.PRIMARY,
            text_color=Tema.TEXTO, width=240,
        ).pack(fill="x", pady=(0, 8))

        # ── DESCRIÇÃO DA MÚSICA ─────────────────────────────
        ctk.CTkLabel(
            scroll, text="MÚSICA (opcional)",
            font=Tema.fonte(Tema.FONTE_PEQUENA, negrito=True),
            text_color=Tema.TEXTO_DIM,
        ).pack(anchor="w", pady=(0, Tema.ESP_2))

        ctk.CTkLabel(
            scroll,
            text="Descreva como você descreveria para uma pessoa:",
            text_color=Tema.TEXTO_DIM, font=Tema.fonte(Tema.FONTE_PEQUENA),
            wraplength=240, justify="left",
        ).pack(anchor="w", pady=(0, Tema.ESP_1))

        self.var_descricao_musica = ctk.StringVar(value="")
        self._ent_descricao = ctk.CTkEntry(
            scroll, textvariable=self.var_descricao_musica,
            placeholder_text="ex: tribal com tambores e violão clássico",
            fg_color=Tema.CARTAO, border_color=Tema.BORDA,
            text_color=Tema.TEXTO, width=240,
        )
        self._ent_descricao.pack(fill="x", pady=(0, 4))
        self._ent_descricao.bind(
            "<FocusOut>", lambda _e: self._ler_descricao_musica()
        )
        self._ent_descricao.bind(
            "<Return>", lambda _e: self._ler_descricao_musica()
        )

        ctk.CTkLabel(
            scroll, text="Exemplos:",
            text_color=Tema.TEXTO_DIM, font=Tema.fonte(Tema.FONTE_PEQUENA),
        ).pack(anchor="w", pady=(4, 2))

        for exemplo in (
            "música para relaxar e dormir",
            "tribal com tambores, pesado",
            "solo de piano clássico, triste",
            "mantra tibetano para meditação",
            "frequência 432Hz para prosperidade",
            "música árabe com oud",
            "lofi beats para estudar",
        ):
            ctk.CTkButton(
                scroll, text=exemplo, anchor="w",
                fg_color="transparent", hover_color=Tema.CARTAO,
                text_color=Tema.TEXTO_DIM,
                font=Tema.fonte(Tema.FONTE_PEQUENA),
                command=lambda t=exemplo: self._usar_exemplo_descricao(t),
            ).pack(fill="x", pady=1)

        self.lbl_leitura_descricao = ctk.CTkLabel(
            scroll, text="", text_color=Tema.TEXTO_DIM,
            font=Tema.fonte(Tema.FONTE_PEQUENA),
            wraplength=240, justify="left",
        )
        self.lbl_leitura_descricao.pack(anchor="w", pady=(4, 8))

        # ── PREVISÃO DO CÁLCULO ─────────────────────────────
        ctk.CTkFrame(scroll, fg_color=Tema.BORDA, height=1).pack(fill="x", pady=8)

        ctk.CTkLabel(
            scroll, text="PREVISÃO",
            font=Tema.fonte(Tema.FONTE_PEQUENA, negrito=True),
            text_color=Tema.TEXTO_DIM,
        ).pack(anchor="w", pady=(0, Tema.ESP_2))

        self.lbl_previsao_plano = ctk.CTkLabel(
            scroll,
            text="Selecione mídias para calcular quantos clipes a música pede.",
            text_color=Tema.TEXTO_DIM, font=Tema.fonte(Tema.FONTE_PEQUENA),
            wraplength=240, justify="left",
        )
        self.lbl_previsao_plano.pack(anchor="w", pady=(0, 4))

        ctk.CTkButton(
            scroll, text="Recalcular previsão", height=28,
            fg_color="transparent", border_width=1,
            border_color=Tema.BORDA, text_color=Tema.TEXTO,
            font=Tema.fonte(Tema.FONTE_PEQUENA),
            command=self._atualizar_previsao_plano,
        ).pack(fill="x", pady=(0, 8))

        # Separador
        ctk.CTkFrame(scroll, fg_color=Tema.BORDA, height=1).pack(fill="x", pady=8)
        ctk.CTkLabel(
            scroll, text="SAÍDA",
            font=Tema.fonte(Tema.FONTE_PEQUENA, negrito=True),
            text_color=Tema.TEXTO_DIM,
        ).pack(anchor="w", pady=(0, Tema.ESP_2))

        self.var_output_dir = ctk.StringVar(value=self._config.output_dir)
        
        output_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        output_frame.pack(fill="x", pady=(0, 8))
        
        self.entry_output = ctk.CTkEntry(
            output_frame, textvariable=self.var_output_dir,
            fg_color=Tema.FUNDO, text_color=Tema.TEXTO,
            font=Tema.fonte(Tema.FONTE_PEQUENA),
        )
        self.entry_output.pack(side="left", fill="x", expand=True, padx=(0, 4))
        
        ctk.CTkButton(
            output_frame, text="...", width=32, height=28,
            command=self._escolher_pasta_saida,
            fg_color=Tema.CARTAO_HOVER, hover_color=Tema.HOVER,
            text_color=Tema.TEXTO, font=Tema.fonte(Tema.FONTE_MEDIA),
        ).pack(side="right")

        # Separador
        ctk.CTkFrame(scroll, fg_color=Tema.BORDA, height=1).pack(fill="x", pady=8)

        # Log
        ctk.CTkLabel(
            scroll, text="LOG",
            font=Tema.fonte(Tema.FONTE_PEQUENA, negrito=True),
            text_color=Tema.TEXTO_DIM,
        ).pack(anchor="w", pady=(0, Tema.ESP_2))

        self.log_box = ctk.CTkTextbox(
            scroll, height=200,
            fg_color=Tema.CARTAO, text_color=Tema.TEXTO_DIM,
            font=Tema.fonte(Tema.FONTE_PEQUENA),
        )
        self.log_box.pack(fill="x")

    # ════════════════════════════════════════════════════════════
    #  NAVEGAÇÃO
    # ════════════════════════════════════════════════════════════

    def _mudar_passo(self, passo: str):
        self._passo_atual = passo

        # O resumo da etapa 6 deve refletir o estado real ao ser exibido.
        if passo == "gerar":
            self._atualizar_resumo_clipe()

        # A etapa de legenda acompanha a letra digitada. Se o usuário
        # escreveu a letra na mão, mostramos as linhas dela com tempo
        # estimado para ele poder ajustar antes de gravar.
        if passo == "legenda":
            self._sincronizar_legenda_com_letra()
            self._atualizar_divergencia()

        for key, btn in self._nav_btns.items():
            if key == passo:
                btn.configure(
                    fg_color=Tema.CARTAO_ATIVO, text_color=Tema.PRIMARY,
                    hover_color=Tema.CARTAO_ATIVO,
                )
            else:
                btn.configure(
                    fg_color="transparent", text_color=Tema.TEXTO_DIM,
                    hover_color=Tema.HOVER,
                )

        passos_ordem = self.PASSOS_ORDEM
        passo_idx = passos_ordem.index(passo) if passo in passos_ordem else 0

        for idx, key in enumerate(passos_ordem):
            labels = self._passo_labels.get(key)
            if not labels:
                continue
            if idx < passo_idx:
                labels["icon"].configure(text_color=Tema.STEP_ATIVO)
                labels["title"].configure(text_color=Tema.STEP_ATIVO)
                labels["subtitle"].configure(text="Concluído")
            elif idx == passo_idx:
                labels["icon"].configure(text_color=Tema.PRIMARY)
                labels["title"].configure(text_color=Tema.TEXTO_CLARO)
                labels["subtitle"].configure(text="Em edição")
            else:
                labels["icon"].configure(text_color=Tema.STEP_PENDENTE)
                labels["title"].configure(text_color=Tema.TEXTO_DIM)
                labels["subtitle"].configure(text="Aguardando")

        self._mostrar_passo(passo)

    def _mostrar_passo(self, passo: str):
        if not self._frames_passos or not self._conteudo_passos:
            return
        for frame in self._frames_passos.values():
            frame.pack_forget()

        frame = self._frames_passos.get(passo)
        if frame:
            frame.pack(in_=self._conteudo_passos, fill="both", expand=True)

    # ════════════════════════════════════════════════════════════
    #  AÇÕES
    # ════════════════════════════════════════════════════════════

    def _carregar_letra_arquivo(self):
        arquivo = filedialog.askopenfilename(
            title="Carregar letra",
            filetypes=[("Texto", "*.txt"), ("Todos", "*.*")],
        )
        if arquivo:
            try:
                texto = Path(arquivo).read_text(encoding="utf-8")
                self.txt_letra.delete("1.0", "end")
                self.txt_letra.insert("1.0", texto)
                self.txt_letra.configure(text_color=Tema.TEXTBOX_TEXTO)
                self._letra_vazia = False
                self._atualizar_resumo_clipe()
                self._log(f"Letra carregada: {Path(arquivo).name}")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao ler arquivo: {e}")

    def _sincronizar_legenda_com_letra(self):
        """Preenche a lista de legenda a partir da letra, se ainda vazia.

        Não sobrescreve uma transcrição já revisada: se o usuário editou
        as linhas, o trabalho dele é preservado — os tempos ali são reais.

        Quando a legenda veio da PRÓPRIA letra, porém, remontar é seguro
        (os tempos eram estimados): se a letra mudou na etapa 01, a
        legenda acompanha em vez de ficar silently desatualizada.
        """
        letra = self._letra_atual()

        if getattr(self, "_linhas_legenda", None):
            if getattr(self, "_legenda_origem", "") == "transcricao":
                self._atualizar_divergencia()
                return
            if self._texto_chave(letra) == getattr(self, "_legenda_snapshot", ""):
                self._atualizar_divergencia()
                return
            self._limpar_legenda()

        if not letra:
            self._mostrar_vazio_legenda()
            self._atualizar_divergencia()
            return

        from MusicClipStudio.transcricao import segmentos_a_partir_de_letra

        # Sem transcrição não há tempo real; distribuímos pela duração
        # da trilha (ou um padrão) para o usuário só refinar.
        duracao = 30.0
        if hasattr(self, "var_music_duration"):
            try:
                duracao = float(self.var_music_duration.get())
            except (ValueError, TypeError):
                duracao = 30.0
        if duracao <= 0:
            duracao = 30.0

        segmentos = segmentos_a_partir_de_letra(letra, duracao)
        if not segmentos:
            self._mostrar_vazio_legenda()
            self._atualizar_divergencia()
            return

        self._legenda_origem = "letra"
        self._legenda_snapshot = self._texto_chave(letra)
        self._definir_linhas_legenda(segmentos)
        self.lbl_legenda_status.configure(
            text="Tempos estimados a partir da letra digitada. "
                 "Ajuste se quiser, ou transcreva o áudio para tempos reais.",
            text_color=Tema.TEXTO_DIM,
        )
        self._atualizar_divergencia()

    def _espelhar_legenda_na_letra(self):
        """Copia a legenda revisada para a caixa da etapa 01.

        A legenda é a fonte da verdade (decisão do usuário), então este é
        o caminho "seguro" quando alguém editou a etapa 01 por conta
        própria e quer que os dois lugares voltem a dizer o mesmo.
        """
        legenda = self._letra_da_legenda()
        if not legenda or not hasattr(self, "txt_letra"):
            return

        self.txt_letra.delete("1.0", "end")
        self.txt_letra.insert("1.0", legenda)
        self.txt_letra.configure(text_color=Tema.TEXTBOX_TEXTO)
        self._letra_vazia = False
        self._legenda_snapshot = self._texto_chave(legenda)

        self._atualizar_divergencia()
        self._atualizar_resumo_clipe()
        self._log("[LETRA] Etapa 01 atualizada com a legenda revisada")

    def _atualizar_divergencia(self):
        """Avisa (sem decidir) quando a etapa 01 e a legenda não batem."""
        lbl = getattr(self, "_lbl_divergencia", None)
        if lbl is None:
            return

        if not self._letra_diverge():
            lbl.configure(text="")
            try:
                self._btn_usar_legenda.grid_forget()
            except Exception:
                pass
            return

        if getattr(self, "_legenda_origem", "") == "transcricao":
            lbl.configure(
                text="A caixa da etapa 01 está diferente da legenda. A "
                     "legenda é que vale — ela tem os tempos reais do "
                     "áudio, e é ela que a busca já está usando.",
            )
        else:
            lbl.configure(
                text="A caixa da etapa 01 mudou depois que a legenda foi "
                     "montada. A busca está usando a legenda.",
            )

        self._btn_usar_legenda.grid(row=1, column=2, padx=(0, Tema.ESP_3),
                                    pady=(0, Tema.ESP_3))

    # ════════════════════════════════════════════════════════════
    #  ETAPA 2 — LEGENDA
    # ════════════════════════════════════════════════════════════

    # ════════════════════════════════════════════════════════════
    #  ETAPA 2 — ORTOGRAFIA
    # ════════════════════════════════════════════════════════════

    def _dicionario_pt(self):
        """O dicionário pt-BR, montado uma vez (o índice custa ~4s)."""
        if getattr(self, "_dic_pt", None) is None:
            from MusicClipStudio.corretor_letra import DicionarioPT

            self._dic_pt = DicionarioPT()
            self._log(f"[ORTO] {self._dic_pt.resumo()}")
        return self._dic_pt

    def _revisar_ortografia(self):
        """Procura, nas linhas da legenda, palavras que não existem em pt-BR."""
        texto = self._letra_da_legenda()
        if not texto:
            messagebox.showinfo(
                "Ortografia", "Nenhuma linha de legenda para revisar."
            )
            return

        if getattr(self, "_dic_pt", None) is None:
            self._orto_aviso.configure(
                text="Carregando o dicionário (primeira vez demora "
                     "alguns segundos)...",
                text_color=Tema.AVISO,
            )
        self._btn_ortografia.configure(state="disabled", text="Verificando...")

        def trabalhar():
            try:
                from MusicClipStudio.corretor_letra import encontrar_suspeitas

                achadas = encontrar_suspeitas(texto, self._dicionario_pt())
                ignoradas = self._ignoradas
                achadas = [s for s in achadas if s.palavra not in ignoradas]
            except Exception as e:
                self.after(0, lambda: self._falhou_ortografia(e))
                return
            self.after(0, lambda: self._mostrar_suspeitas(achadas))

        threading.Thread(target=trabalhar, daemon=True).start()

    def _falhou_ortografia(self, erro):
        self._btn_ortografia.configure(state="normal", text="Revisar ortografia")
        self._orto_aviso.configure(
            text=f"Corretor indisponível: {erro}", text_color=Tema.DESTRUIVA
        )
        self._log(f"[ORTO] Corretor indisponível: {erro}")

    def _mostrar_suspeitas(self, suspeitas):
        """Desenha uma linha por palavra suspeita, com as correções."""
        self._btn_ortografia.configure(state="normal", text="Revisar ortografia")
        self._suspeitas = suspeitas

        for w in self._orto_lista.winfo_children():
            w.destroy()

        if not suspeitas:
            self._orto_aviso.configure(
                text="Nada estranho encontrado — a letra está limpa.",
                text_color=Tema.SUCESSO,
            )
        else:
            obvias = sum(1 for s in suspeitas if s.alta_confianca)
            duvidosas = len(suspeitas) - obvias
            partes = [f"{len(suspeitas)} palavra(s) fora do dicionário"]
            if obvias:
                partes.append(f"{obvias} com correção óbvia")
            if duvidosas:
                partes.append(f"{duvidosas} que só você resolve")
            self._orto_aviso.configure(
                text=" · ".join(partes), text_color=Tema.AVISO
            )

        for suspeita in suspeitas:
            self._desenhar_suspeita(suspeita)

        self._card_ortografia.grid(
            row=3, column=0, sticky="ew", pady=(0, Tema.ESP_3)
        )
        self._log(f"[ORTO] {len(suspeitas)} palavra(s) suspeita(s)")

    def _desenhar_suspeita(self, suspeita):
        """Palavra errada na esquerda, correções possíveis em botões."""
        linha = ctk.CTkFrame(self._orto_lista, fg_color=Tema.FUNDO,
                             corner_radius=Tema.RAIO_BOTAO)
        linha.pack(fill="x", pady=2, padx=2)

        ctk.CTkLabel(
            linha, text=f"L{suspeita.linha}", width=30,
            font=Tema.fonte(Tema.FONTE_MICRO), text_color=Tema.TEXTO_SUTIL,
        ).pack(side="left", padx=(Tema.ESP_2, 0))

        ctk.CTkLabel(
            linha, text=suspeita.palavra,
            font=Tema.fonte(Tema.FONTE_BASE, negrito=True),
            text_color=Tema.AVISO if suspeita.ambigua else Tema.DESTRUIVA,
        ).pack(side="left", padx=(Tema.ESP_1, Tema.ESP_2))

        if not suspeita.sugestoes:
            ctk.CTkLabel(
                linha, text="sem sugestão",
                font=Tema.fonte(Tema.FONTE_PEQUENA),
                text_color=Tema.TEXTO_SUTIL,
            ).pack(side="left")
        else:
            for sugestao in suspeita.sugestoes[:4]:
                ctk.CTkButton(
                    linha, text=sugestao, height=26,
                    fg_color=Tema.CARTAO_HOVER, hover_color=Tema.PRIMARY,
                    text_color=Tema.TEXTO_CLARO,
                    font=Tema.fonte(Tema.FONTE_PEQUENA),
                    corner_radius=Tema.RAIO_BOTAO,
                    command=lambda p=suspeita.palavra, c=sugestao:
                        self._aplicar_correcao(p, c),
                ).pack(side="left", padx=2)

        ctk.CTkButton(
            linha, text="ignorar", width=54, height=26,
            fg_color="transparent", hover_color=Tema.HOVER,
            text_color=Tema.TEXTO_SUTIL,
            font=Tema.fonte(Tema.FONTE_MICRO),
            corner_radius=Tema.RAIO_BOTAO,
            command=lambda w=linha, p=suspeita.palavra:
                self._ignorar_suspeita(w, p),
        ).pack(side="right", padx=(0, Tema.ESP_2))

    def _aplicar_correcao(self, errada: str, certa: str):
        """Troca uma palavra nas linhas da legenda (e no espelho da etapa 01)."""
        from MusicClipStudio.corretor_letra import corrigir_texto

        self._ignoradas.discard(errada)
        self._escrever_correcao(corrigir_texto, {errada: certa})
        self._log(f"[ORTO] {errada} → {certa}")
        self._revisar_ortografia()

    def _aplicar_obvias(self):
        """Aplica só as correções sem empate — as que o sistema tem certeza."""
        from MusicClipStudio.corretor_letra import corrigir_texto

        mapa = {
            s.palavra: s.melhor
            for s in getattr(self, "_suspeitas", [])
            if s.alta_confianca and s.melhor
        }
        if not mapa:
            messagebox.showinfo(
                "Ortografia",
                "Nenhuma correção automática disponível.\n\n"
                "Tudo o que sobrou tem mais de uma palavra possível e só "
                "você sabe qual é a certa — clique na que quiser.",
            )
            return

        self._escrever_correcao(corrigir_texto, mapa)
        self._log(
            "[ORTO] correções automáticas: "
            + ", ".join(f"{k}→{v}" for k, v in mapa.items())
        )
        self._revisar_ortografia()

    def _escrever_correcao(self, corrigir_texto, mapa: dict):
        """Aplica o mapa nas linhas da legenda e no espelho da etapa 01.

        A etapa 01 só é escrita quando os dois lugares ainda dizem o
        mesmo. Se o usuário divergiu de propósito (editou a etapa 01
        sabendo que a legenda é que vale), mexer lá seria passar por
        cima do que ele escreveu.
        """
        espelhar = not self._letra_diverge()

        for linha in getattr(self, "_linhas_legenda", None) or []:
            atual = linha["texto"].get()
            nova = corrigir_texto(atual, mapa)
            if nova != atual:
                linha["texto"].delete(0, "end")
                linha["texto"].insert(0, nova)

        if espelhar and hasattr(self, "txt_letra") \
                and not getattr(self, "_letra_vazia", False):
            atual = self.txt_letra.get("1.0", "end")
            nova = corrigir_texto(atual, mapa)
            if nova != atual:
                self.txt_letra.delete("1.0", "end")
                self.txt_letra.insert("1.0", nova)

        self._atualizar_divergencia()
        self._atualizar_resumo_clipe()

    def _ignorar_suspeita(self, widget, palavra):
        """Marca a palavra como correta — nome próprio, gíria, neologismo."""
        self._ignoradas.add(palavra)
        widget.destroy()
        self._log(f"[ORTO] '{palavra}' mantida do jeito que está")

    def _transcrever_letra(self):
        """Transcreve o áudio em letra, via faster-whisper.

        Só é oferecido quando faz sentido: sem áudio não há o que ouvir,
        e com letra já escrita a transcrição só introduziria divergência.
        """
        letra_existente = self._letra_atual()
        if letra_existente:
            confirmar = messagebox.askyesno(
                "Letra já preenchida",
                "Já existe uma letra na etapa 1.\n\n"
                "Transcrever vai substituir o que está lá. Continuar?",
            )
            if not confirmar:
                return

        if not self._trilha_path or not Path(self._trilha_path).exists():
            messagebox.showwarning(
                "Sem áudio",
                "Nenhum áudio disponível para transcrever.\n\n"
                "Gere a trilha na etapa Áudio primeiro, ou adicione um "
                "arquivo de música.",
            )
            return

        try:
            from MusicClipStudio.transcricao import transcrever
        except ImportError as e:
            messagebox.showerror("Indisponível", f"Transcrição indisponível: {e}")
            return

        self._transcrevendo = True
        self.lbl_legenda_status.configure(
            text="Transcrevendo o áudio... isso pode levar um minuto.",
            text_color=Tema.AVISO,
        )
        self._log("[WHISPER] Iniciando transcrição...")
        audio = self._trilha_path

        def trabalhar():
            resultado = transcrever(
                audio,
                modelo="small",
                idioma="pt",
                callback_log=lambda m: self.after(0, lambda msg=m: self._log(msg)),
                callback_prog=lambda p: self.after(
                    0, lambda v=p: self.lbl_legenda_status.configure(
                        text=f"Transcrevendo... {v}%", text_color=Tema.AVISO
                    )
                ),
            )
            self.after(0, lambda: self._pos_transcricao(resultado))

        threading.Thread(target=trabalhar, daemon=True).start()

    def _pos_transcricao(self, resultado):
        """Trata o retorno da transcrição, na thread da interface."""
        self._transcrevendo = False

        if not resultado.ok:
            self.lbl_legenda_status.configure(
                text=f"Transcrição não concluída: {resultado.erro}",
                text_color=Tema.DESTRUIVA,
            )
            self._log(f"[WHISPER] {resultado.erro}")
            return

        from MusicClipStudio.transcricao import quebrar_em_frases

        # O Whisper agrupa várias frases por segmento. Quebramos para a
        # legenda caber na tela por um tempo legível.
        linhas = quebrar_em_frases(resultado.segmentos, max_segundos=5.0)

        # Origem "transcricao" = tempos REAIS do áudio. Isso protege a
        # lista: a sincronização com a etapa 01 não pode mais sobrescrevê-la.
        self._legenda_origem = "transcricao"
        self._legenda_snapshot = self._texto_chave(
            "\n".join(s.texto for s in linhas if s.texto.strip())
        )
        self._definir_linhas_legenda(linhas)
        self.lbl_legenda_status.configure(
            text=f"Transcrição concluída: {len(linhas)} linha(s) "
                 f"({resultado.idioma}, {resultado.duracao_audio:.0f}s). "
                 f"Revise e ajuste o que quiser.",
            text_color=Tema.SUCESSO,
        )
        self._log(f"[WHISPER] {len(linhas)} linha(s) prontas para revisão")

        # A transcrição também vira a letra oficial do clipe.
        texto = "\n".join(s.texto for s in linhas if s.texto.strip())
        if texto and hasattr(self, "txt_letra"):
            self.txt_letra.delete("1.0", "end")
            self.txt_letra.insert("1.0", texto)
            self.txt_letra.configure(text_color=Tema.TEXTBOX_TEXTO)
            self._letra_vazia = False
            self._atualizar_resumo_clipe()

    def _definir_linhas_legenda(self, segmentos):
        """Redesenha a lista de linhas editáveis a partir dos segmentos."""
        self._linhas_legenda = []
        for w in self._legenda_scroll.winfo_children():
            w.destroy()
        self._vazio_legenda_widget = None

        # As suspeitas eram do texto antigo: saem de cena com ele.
        self._suspeitas = []
        try:
            self._card_ortografia.grid_forget()
        except Exception:
            pass

        for seg in segmentos:
            self._adicionar_linha_legenda(seg.inicio, seg.fim, seg.texto)

        if not segmentos:
            self._mostrar_vazio_legenda()

        self.lbl_legenda_total.configure(
            text=f"{len(self._linhas_legenda)} linha(s)"
        )

    def _adicionar_linha_legenda(self, inicio: float, fim: float, texto: str):
        """Adiciona uma linha editável (tempo + texto) na lista."""
        # O placeholder de vazio nao e' uma linha: sai de cena assim que
        # a primeira linha real entra.
        self._limpar_vazio_legenda()

        linha = ctk.CTkFrame(self._legenda_scroll, fg_color=Tema.CARTAO,
                             corner_radius=Tema.RAIO_BOTAO)
        linha.pack(fill="x", pady=2, padx=2)

        # Tempo
        campo_ini = ctk.CTkEntry(
            linha, width=62, height=Tema.ALTURA_CAMPO,
            fg_color=Tema.FUNDO, text_color=Tema.TEXTO,
            font=Tema.fonte(Tema.FONTE_MICRO), justify="center",
        )
        campo_ini.insert(0, f"{inicio:.2f}")
        campo_ini.pack(side="left", padx=(Tema.ESP_2, 2), pady=Tema.ESP_1)

        ctk.CTkLabel(
            linha, text="→", text_color=Tema.TEXTO_SUTIL,
            font=Tema.fonte(Tema.FONTE_MICRO),
        ).pack(side="left")

        campo_fim = ctk.CTkEntry(
            linha, width=62, height=Tema.ALTURA_CAMPO,
            fg_color=Tema.FUNDO, text_color=Tema.TEXTO,
            font=Tema.fonte(Tema.FONTE_MICRO), justify="center",
        )
        campo_fim.insert(0, f"{fim:.2f}")
        campo_fim.pack(side="left", padx=(2, Tema.ESP_2), pady=Tema.ESP_1)

        # Texto da linha
        campo_texto = ctk.CTkEntry(
            linha, height=Tema.ALTURA_CAMPO,
            fg_color=Tema.FUNDO, text_color=Tema.TEXTBOX_TEXTO,
            font=Tema.fonte(Tema.FONTE_BASE),
        )
        campo_texto.insert(0, texto)
        campo_texto.pack(side="left", fill="x", expand=True,
                         padx=(0, Tema.ESP_2), pady=Tema.ESP_1)

        # Remover linha
        ctk.CTkButton(
            linha, text="×", width=28, height=Tema.ALTURA_CAMPO,
            command=lambda l=linha: self._remover_linha_legenda(l),
            fg_color="transparent", hover_color=Tema.DESTRUIVA,
            text_color=Tema.TEXTO_DIM,
            font=Tema.fonte(Tema.FONTE_MEDIA),
            corner_radius=Tema.RAIO_BOTAO,
        ).pack(side="right", padx=(0, Tema.ESP_1), pady=Tema.ESP_1)

        self._linhas_legenda.append({
            "widget": linha,
            "inicio": campo_ini,
            "fim": campo_fim,
            "texto": campo_texto,
        })
        self.lbl_legenda_total.configure(
            text=f"{len(self._linhas_legenda)} linha(s)"
        )

    def _limpar_legenda(self):
        """Esvazia a lista de linhas e volta ao estado vazio."""
        self._linhas_legenda = []
        self._legenda_origem = ""
        self._legenda_snapshot = ""
        if hasattr(self, "_legenda_scroll"):
            for w in self._legenda_scroll.winfo_children():
                w.destroy()
            self._vazio_legenda_widget = None
            self._mostrar_vazio_legenda()
        if hasattr(self, "lbl_legenda_total"):
            self.lbl_legenda_total.configure(text="0 linhas")

    def _remover_linha_legenda(self, widget):
        """Remove uma linha da lista."""
        self._linhas_legenda = [
            l for l in self._linhas_legenda if l["widget"] is not widget
        ]
        widget.destroy()
        self.lbl_legenda_total.configure(
            text=f"{len(self._linhas_legenda)} linha(s)"
        )
        # Removeu a ultima linha -> volta o estado vazio
        if not self._linhas_legenda:
            self._mostrar_vazio_legenda()

    def ler_legenda_editada(self):
        """Devolve as linhas como estão na tela, com tempos ajustados.

        Usa `getattr` porque a etapa pode nunca ter sido construída em
        contexto de teste.
        """
        from MusicClipStudio.transcricao import SegmentoLegenda

        linhas = getattr(self, "_linhas_legenda", [])
        segmentos: list[SegmentoLegenda] = []
        anterior_fim = 0.0

        for i, l in enumerate(linhas, 1):
            try:
                inicio = max(0.0, float(l["inicio"].get().replace(",", ".")))
            except (ValueError, AttributeError):
                inicio = anterior_fim
            try:
                fim = float(l["fim"].get().replace(",", "."))
            except (ValueError, AttributeError):
                fim = inicio + 2.0

            # Corrige inversão e sobreposição: legenda fora de ordem é
            # erro comum de digitação e quebraria a renderização.
            if fim <= inicio:
                fim = inicio + 1.0
            if inicio < anterior_fim:
                inicio = anterior_fim
                if fim <= inicio:
                    fim = inicio + 1.0

            texto = l["texto"].get().strip()
            anterior_fim = fim

            if not texto:
                continue

            segmentos.append(
                SegmentoLegenda(indice=i, inicio=inicio, fim=fim, texto=texto)
            )

        return segmentos

    def _buscar_midia(self):
        query = self.entry_search.get().strip()
        if not query:
            messagebox.showwarning("Aviso", "Digite um termo para buscar.")
            return
        
        provider = self.var_provider.get()
        self._log(f"Buscando midia: {query} ({provider})")
        
        # Limpa resultados anteriores
        for widget in self._resultados_frame.winfo_children():
            widget.destroy()
        
        # Mostra loading
        loading_label = ctk.CTkLabel(
            self._resultados_frame,
            text="Buscando...",
            text_color=Tema.TEXTO_DIM, font=Tema.fonte(Tema.FONTE_BASE),
        )
        loading_label.pack(expand=True, pady=20)
        
        # Busca em thread separada
        def buscar():
            try:
                if provider == "todos":
                    # Todos os bancos habilitados + termos EN extras da IA
                    # (se houver chave no diálogo de APIs) + selo de status.
                    resultado = self._db.pesquisar_multi(
                        query, max_results=24, usar_ia=True
                    )
                else:
                    resultado = self._db.pesquisar(
                        query, provider=provider, max_results=12
                    )
                # Atualiza GUI na thread principal
                self.after(0, lambda: self._exibir_resultados(resultado))
            except Exception as e:
                self.after(0, lambda: self._log(f"Erro na busca: {e}"))
        
        threading.Thread(target=buscar, daemon=True).start()

    def _gerar_imagem_ia(self):
        """Gera imagem com IA baseado no prompt."""
        prompt = self.txt_prompt.get().strip()
        if not prompt:
            messagebox.showwarning("Aviso", "Digite um prompt para gerar a imagem.")
            return
        
        self._log(f"Gerando imagem com IA: {prompt[:50]}...")
        
        # Mostra na galeria
        card = ctk.CTkFrame(
            self._galeria_frame, fg_color=Tema.CARTAO, corner_radius=8,
        )
        card.pack(fill="x", padx=4, pady=4)
        
        # Placeholder da imagem
        img_frame = ctk.CTkFrame(
            card, fg_color=Tema.FUNDO, corner_radius=6, height=120,
        )
        img_frame.pack(fill="x", padx=8, pady=(8, 4))
        img_frame.pack_propagate(False)
        
        ctk.CTkLabel(
            img_frame, text="Gerando...",
            font=Tema.fonte(Tema.FONTE_MEDIA),
            text_color=Tema.PRIMARY,
            justify="center",
        ).pack(expand=True)
        
        # Info
        ctk.CTkLabel(
            card, text=prompt[:60] + "..." if len(prompt) > 60 else prompt,
            font=Tema.fonte(Tema.FONTE_MICRO),
            text_color=Tema.TEXTO_DIM,
            wraplength=250,
        ).pack(anchor="w", padx=8, pady=(0, 4))
        
        # Botões
        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(fill="x", padx=8, pady=(0, 8))
        
        ctk.CTkButton(
            btn_frame, text="Usar", width=60, height=24,
            command=lambda p=prompt, c=card: self._usar_imagem_gerada(p, c),
            fg_color=Tema.PRIMARY, hover_color=Tema.PRIMARY_HOVER,
            text_color=Tema.FUNDO, font=Tema.fonte(Tema.FONTE_MICRO),
            corner_radius=4,
        ).pack(side="left")
        
        ctk.CTkButton(
            btn_frame, text="Excluir", width=60, height=24,
            command=lambda: card.destroy(),
            fg_color=Tema.DESTRUIVA, hover_color=Tema.DESTRUIVA_HOVER,
            text_color=Tema.FUNDO, font=Tema.fonte(Tema.FONTE_MICRO),
            corner_radius=4,
        ).pack(side="right")
        
        self._imagens_geradas.append({"prompt": prompt, "widget": card})
        self._log(f"Imagem gerada com prompt: {prompt[:30]}...")

    def _usar_imagem_gerada(self, prompt, card_widget=None):
        """Usa a imagem gerada no clipe."""
        # Mesma forma dos itens selecionados na busca (StockMedia), para que
        # selecionar/deselecionar e a geracao tratem tudo de forma uniforme.
        item = StockMedia(
            id=f"ia_{abs(hash(prompt)) % 10**8}",
            url="",
            thumbnail_url="",
            width=0,
            height=0,
            source="ai",
            media_type="photo",
            category="generated",
            tags=[],
            description=prompt,
            download_url="",
        )
        self._midia_selecionada.append(item)

        # Feedback visual
        if card_widget:
            card_widget.configure(fg_color=Tema.SUCESSO)

        self._log(f"Imagem IA adicionada ao clipe (total: {len(self._midia_selecionada)})")
        self._atualizar_contador_selecionadas()
        self._atualizar_resumo_clipe()

    def _auto_gerar_prompt(self):
        """Auto-gera um prompt baseado na letra."""
        letra = self._letra_oficial()
        
        if not letra:
            prompt = "Epic cinematic scene with dramatic lighting and emotional atmosphere"
        else:
            mood = AgentMood(self.var_mood.get())
            style = AgentStyle(self.var_estilo.get())
            queries = self._agent.MOOD_QUERIES.get(mood, ["epic landscape"])
            prompt = f"{queries[0]}, {style.value} style, cinematic"
        
        self.txt_prompt.delete(0, "end")
        self.txt_prompt.insert(0, prompt)
        self._log(f"Prompt auto-gerado: {prompt[:50]}...")

    def _busca_automatica(self):
        """Busca massiva estilo MoneyPrinter: 5 terms × 4 providers = 100+ resultados."""
        self.lbl_auto_status.configure(text="Gerando search terms...", text_color=Tema.AVISO)
        self._log("[SEARCH] Gerando search terms da letra...")

        # Limpa galeria
        for widget in self._galeria_frame.winfo_children():
            widget.destroy()

        # Coleta letra. Le a FONTE OFICIAL (legenda revisada primeiro):
        # corrigir "vois" na etapa 02 e a busca continuar usando a etapa
        # 01 era exatamente o defeito que fazia a busca errar o alvo.
        letra = self._letra_oficial()

        # A descrição da música pode conter um TEMA (mantra, frequencia,
        # classica, arabe...) que MUDA completamente a busca. Detectamos
        # antes de gerar os terms da letra.
        leitura = self._leitura_descricao()
        tema_termos = None
        tema_ignora = False
        tema_nome = ""
        if leitura is not None and leitura.tema_id:
            tema_termos = leitura.tema_termos
            tema_ignora = leitura.tema_ignora_letra
            tema_nome = leitura.tema_nome
            self._log(
                f"[SEARCH] TEMA detectado: {tema_nome} "
                f"(ignora letra: {tema_ignora})"
            )

        # Gerar search terms inteligentes (com tema se houver)
        search_terms = self._db.gerar_search_terms_letra(
            letra, num_terms=5,
            tema_termos=tema_termos,
            tema_ignora_letra=tema_ignora,
        )
        self._log(f"[SEARCH] Terms da letra: {', '.join(search_terms)}")

        # A descrição da música entra COMBINADA com a letra (decisão do
        # usuário: "combinar sempre"), EXCETO quando um tema foi detectado
        # e ele ja' ignorou a letra — nesse caso os termos do tema ja'
        # estao em search_terms e nao precisamos duplicar.
        if leitura is not None and not leitura.vazia and not leitura.tema_id:
            try:
                from MusicClipStudio.descricao_musical import termos_de_busca

                termos_desc = termos_de_busca([], leitura, maximo=3)
                if termos_desc:
                    for t in termos_desc:
                        if t not in search_terms:
                            search_terms.append(t)
                    self._log(
                        f"[SEARCH] + descrição ({leitura.resumo()}): "
                        f"{', '.join(termos_desc)}"
                    )
            except Exception as e:
                self._log(f"[WARN] Descrição não entrou na busca: {e}")

        self._log(f"[SEARCH] {len(search_terms)} termo(s) no total")

        # Guarda as bases para o fallback generativo (se faltar midia).
        self._bases_fallback = list(search_terms)

        pref = self.var_tipo_midia.get() if hasattr(self, "var_tipo_midia") else "Meio a meio"
        apenas_f = pref == "Mais fotos"
        apenas_v = pref == "Mais vídeos"
        self._log(f"[SEARCH] Preferência de mídia: {pref}")

        def buscar():
            self.after(0, lambda: self.lbl_auto_status.configure(
                text=f"Buscando {len(search_terms)} terms...", text_color=Tema.AVISO
            ))

            # Busca massiva: 5 terms x 2 provedores
            resultados = self._db.busca_massiva(
                search_terms,
                apenas_videos=apenas_v,
                apenas_fotos=apenas_f,
                max_por_term=10,
            )

            self.after(0, lambda: self._exibir_resultados_automaticos(resultados))

        threading.Thread(target=buscar, daemon=True).start()

    def _extrair_queries(self, letra):
        """Extrai queries de busca da letra."""
        if not letra:
            return ["concert", "music", "stage"]

        # Palavras irrelevantes para busca
        stopwords = {
            "eu", "tu", "ele", "ela", "nos", "eles", "elas", "meu", "minha",
            "teu", "tua", "seu", "sua", "nosso", "nossa", "dele", "dela",
            "que", "para", "com", "por", "sem", "sob", "entre", "ate",
            "como", "mais", "menos", "muito", "pouco", "todo", "toda",
            "este", "esta", "esse", "essa", "aquele", "aquela",
            "isso", "isto", "aquilo", "aqui", "la", "ai", "onde",
            "quando", "porque", "entao", "mas", "porem", "ou",
            "sim", "nao", "ja", "ainda", "sempre", "nunca",
            "um", "uma", "uns", "umas", "do", "da", "dos", "das",
            "no", "na", "nos", "nas", "ao", "aos", "pela", "pelo",
            "foi", "ser", "estar", "ter", "fazer", "ir", "vir",
            "dizer", "dar", "ver", "saber", "poder", "querer",
            "amor", "vida", "coracao", "alma", "mundo",
        }

        palavras = letra.lower().split()
        # Limpar pontuação e filtrar
        palavras_limpa = []
        for p in palavras:
            p = p.strip(".,;:!?\"'()-")
            if len(p) > 3 and p not in stopwords:
                palavras_limpa.append(p)

        # Pegar palavras mais frequentes/representativas
        from collections import Counter
        contagem = Counter(palavras_limpa)
        mais_comuns = [p for p, _ in contagem.most_common(8)]

        if not mais_comuns:
            return ["concert", "music", "stage"]

        # Criar queries: combinar palavras relevantes
        queries = []

        # Query 1: as 2-3 palavras mais relevantes juntas
        if len(mais_comuns) >= 2:
            queries.append(" ".join(mais_comuns[:3]))
        else:
            queries.append(mais_comuns[0])

        # Query 2: individual se for curta
        if len(mais_comuns) >= 3:
            queries.append(mais_comuns[2])

        # Query 3: combinação diferente
        if len(mais_comuns) >= 4:
            queries.append(f"{mais_comuns[3]} {mais_comuns[0]}")

        # Log das queries
        self._log(f"[SEARCH] Queries da letra: {queries}")

        return queries[:3]

    # Abaixo deste numero de itens, a busca e' considerada insuficiente
    # e o preenchedor generativo entra oferecendo prompts de IA.
    MINIMO_MIDIA_SUFICIENTE = 6

    def _exibir_resultados_automaticos(self, resultados):
        """Exibe resultados da busca automática."""
        for widget in self._galeria_frame.winfo_children():
            widget.destroy()

        if not resultados:
            ctk.CTkLabel(
                self._galeria_frame,
                text="Nenhum resultado encontrado.\n"
                     "Veja abaixo os prompts sugeridos para gerar com IA.",
                text_color=Tema.TEXTO_DIM, font=Tema.fonte(Tema.FONTE_BASE),
                justify="center",
            ).pack(expand=True, pady=(30, 10))
            self.lbl_auto_status.configure(text="0 resultados", text_color=Tema.DESTRUIVA)
            self._oferecer_prompts_preenchimento(0)
            return

        fotos = sum(1 for m in resultados if m.media_type != "video")
        videos = len(resultados) - fotos
        self.lbl_auto_status.configure(
            text=f"{len(resultados)} encontrados ({videos} vídeo, {fotos} foto)",
            text_color=Tema.SUCESSO if len(resultados) >= self.MINIMO_MIDIA_SUFICIENTE
                       else Tema.AVISO,
        )

        grid_frame = ctk.CTkFrame(self._galeria_frame, fg_color="transparent")
        grid_frame.pack(fill="x")

        for idx, item in enumerate(resultados):
            self._criar_card_midia(grid_frame, item, idx)

        # Pouca midia: o video vai repetir (reciclagem). Oferecemos
        # prompts de IA para completar em vez de so' reciclar.
        if len(resultados) < self.MINIMO_MIDIA_SUFICIENTE:
            self._oferecer_prompts_preenchimento(len(resultados))

    def _oferecer_prompts_preenchimento(self, encontrados: int):
        """Mostra prompts de imagem/vídeo para cobrir a falta de mídia.

        Dispara quando a busca devolve pouca coisa. Reaproveita a
        linguagem do tema (se houver) ou das cenas emocionais.
        """
        bases = list(getattr(self, "_bases_fallback", []) or [])
        if not bases:
            return

        faltam = max(self.MINIMO_MIDIA_SUFICIENTE - encontrados, 2)
        quantos = min(max(faltam, 2), 6)

        try:
            from MusicClipStudio.preenchedor_prompts import (
                gerar_prompts, gerar_prompts_para_tema,
            )

            leitura = self._leitura_descricao()
            tema = None
            if leitura is not None and leitura.tema_id:
                from MusicClipStudio.temas_musicais import TEMAS
                tema = next((t for t in TEMAS if t.id == leitura.tema_id), None)

            if tema is not None:
                prompts = gerar_prompts_para_tema(tema, quantos=quantos)
                origem_txt = f"tema {tema.nome}"
            else:
                prompts = gerar_prompts(bases, quantos=quantos, origem="letra")
                origem_txt = "letra"
        except Exception as e:
            self._log(f"[WARN] Não foi possível gerar prompts: {e}")
            return

        if not prompts:
            return

        self._log(
            f"[FALLBACK] Busca rendeu {encontrados} item(ns). "
            f"Gerados {len(prompts)} prompt(ns) de preenchimento ({origem_txt})."
        )

        card = ctk.CTkFrame(self._galeria_frame, fg_color=Tema.CARTAO, corner_radius=8)
        card.pack(fill="x", padx=4, pady=(10, 4))

        ctk.CTkLabel(
            card,
            text=f"Busca rendeu só {encontrados} mídia(s) — "
                 f"o vídeo vai repetir. Use estes prompts com IA:",
            font=Tema.fonte(Tema.FONTE_PEQUENA, negrito=True),
            text_color=Tema.AVISO, justify="left", wraplength=560,
        ).pack(anchor="w", padx=10, pady=(8, 2))

        ctk.CTkLabel(
            card,
            text="Clique em “Usar prompt” para preencher o campo de IA acima e gerar.",
            font=Tema.fonte(Tema.FONTE_MICRO),
            text_color=Tema.TEXTO_DIM,
        ).pack(anchor="w", padx=10, pady=(0, 6))

        for p in prompts:
            linha = ctk.CTkFrame(card, fg_color="transparent")
            linha.pack(fill="x", padx=10, pady=2)

            selo = "VÍDEO" if p.tipo == "video" else "IMAGEM"
            cor_selo = Tema.PRIMARY if p.tipo == "video" else Tema.SUCESSO
            ctk.CTkLabel(
                linha, text=selo, width=54,
                font=Tema.fonte(Tema.FONTE_MICRO, negrito=True),
                text_color=cor_selo,
            ).pack(side="left")

            texto = p.prompt[:78] + "..." if len(p.prompt) > 78 else p.prompt
            ctk.CTkLabel(
                linha, text=texto,
                font=Tema.fonte(Tema.FONTE_MICRO),
                text_color=Tema.TEXTO, justify="left", wraplength=380,
            ).pack(side="left", padx=(2, 6))

            ctk.CTkButton(
                linha, text="Usar prompt", width=88, height=22,
                command=lambda pr=p.prompt: self._usar_prompt_preenchimento(pr),
                fg_color=Tema.CARTAO_HOVER, hover_color=Tema.HOVER,
                text_color=Tema.TEXTO, font=Tema.fonte(Tema.FONTE_MICRO),
                corner_radius=4,
            ).pack(side="right")

    def _usar_prompt_preenchimento(self, prompt: str):
        """Joga o prompt do preenchedor no campo de IA (etapa 04)."""
        self.txt_prompt.delete(0, "end")
        self.txt_prompt.insert(0, prompt)
        self._log(f"[FALLBACK] Prompt carregado no campo de IA: {prompt[:60]}...")
        self.lbl_auto_status.configure(
            text="Prompt carregado — clique em “Gerar IA”", text_color=Tema.AVISO,
        )

    def _exibir_resultados(self, resultado):
        """Exibe os resultados da busca na GUI."""
        for widget in self._resultados_frame.winfo_children():
            widget.destroy()
        
        if not resultado.results:
            ctk.CTkLabel(
                self._resultados_frame,
                text="Nenhum resultado encontrado.",
                text_color=Tema.TEXTO_DIM, font=Tema.fonte(Tema.FONTE_BASE),
            ).pack(expand=True, pady=40)
            return
        
        # Header
        ctk.CTkLabel(
            self._resultados_frame,
            text=f"{len(resultado.results)} resultado(s) encontrado(s)",
            text_color=Tema.TEXTO_CLARO, font=Tema.fonte(Tema.FONTE_BASE, negrito=True),
        ).pack(anchor="w", pady=(8, 2))

        # ⚠️ NOVO (24/09/2026): selo "bancos: pexels ✓12 · giphy ✗403" —
        # falha de banco agora É VISÍVEL (antes era print escondido no console).
        status = getattr(resultado, "status", None) or {}
        if status:
            resumo = " · ".join(f"{p} {s}" for p, s in status.items())
            ctk.CTkLabel(
                self._resultados_frame,
                text=f"bancos: {resumo}",
                text_color=Tema.TEXTO_DIM, font=Tema.fonte(Tema.FONTE_BASE),
            ).pack(anchor="w", pady=(0, 10))
            self._log(f"[SEARCH] status dos bancos: {resumo}")
        
        # Grid de resultados
        grid_frame = ctk.CTkFrame(self._resultados_frame, fg_color="transparent")
        grid_frame.pack(fill="x")
        
        for idx, item in enumerate(resultado.results):
            self._criar_card_midia(grid_frame, item, idx)
        
        self._log(f"{len(resultado.results)} resultado(s) encontrado(s)")

    def _criar_card_midia(self, parent, item, idx):
        """Cria um card para um item de mídia."""
        # 2 colunas para cards maiores
        row = idx // 2
        col = idx % 2
        
        card = ctk.CTkFrame(
            parent, fg_color=Tema.CARTAO, corner_radius=8,
        )
        card.grid(row=row, column=col, padx=6, pady=6, sticky="nsew")
        
        # Thumbnail - maior
        thumb_frame = ctk.CTkFrame(
            card, fg_color=Tema.FUNDO, corner_radius=6, height=140,
        )
        thumb_frame.pack(fill="x", padx=8, pady=(8, 4))
        thumb_frame.pack_propagate(False)
        
        # Tipo de mídia
        tipo = "VIDEO" if item.media_type == "video" else "FOTO"
        
        # Tenta carregar thumbnail real
        thumbnail_url = item.thumbnail_url or item.download_url
        if thumbnail_url and thumbnail_url.startswith("http"):
            self._carregar_thumbnail(thumb_frame, thumbnail_url, tipo)
        else:
            ctk.CTkLabel(
                thumb_frame, text=tipo,
                font=Tema.fonte(Tema.FONTE_MEDIA, negrito=True),
                text_color=Tema.PRIMARY,
            ).pack(expand=True)
        
        # Fonte
        ctk.CTkLabel(
            card, text=item.source.upper(),
            font=Tema.fonte(Tema.FONTE_PEQUENA, negrito=True),
            text_color=Tema.TEXTO_DIM,
        ).pack(anchor="w", padx=8, pady=(4, 0))
        
        # Descrição
        desc = item.description[:60] + "..." if len(item.description) > 60 else item.description
        ctk.CTkLabel(
            card, text=desc or "Sem descrição",
            font=Tema.fonte(Tema.FONTE_BASE),
            text_color=Tema.TEXTO,
            wraplength=280,
        ).pack(anchor="w", padx=8, pady=(2, 4))
        
        # Botão selecionar
        btn = ctk.CTkButton(
            card, text="Selecionar", width=100, height=28,
            command=lambda i=item, b=card: self._selecionar_midia(i, b),
            fg_color=Tema.PRIMARY, hover_color=Tema.PRIMARY_HOVER,
            text_color=Tema.FUNDO, font=Tema.fonte(Tema.FONTE_BASE),
            corner_radius=4,
        )
        btn.pack(anchor="e", padx=8, pady=(0, 8))
        
        # Configura grid
        parent.grid_columnconfigure(col, weight=1)

    def _carregar_thumbnail(self, parent, url, fallback_text="IMG"):
        """Carrega thumbnail de forma assíncrona."""
        from PIL import Image, ImageTk
        import urllib.request
        from io import BytesIO
        
        loading = ctk.CTkLabel(
            parent, text="Carregando...",
            font=Tema.fonte(Tema.FONTE_PEQUENA),
            text_color=Tema.TEXTO_DIM,
        )
        loading.pack(expand=True)
        
        def carregar():
            try:
                # URL limpa
                clean_url = url.split("?")[0] if "?" in url else url
                
                req = urllib.request.Request(clean_url, headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                })
                with urllib.request.urlopen(req, timeout=15) as resp:
                    data = resp.read()
                    
                img = Image.open(BytesIO(data))
                # Redimensionar para card maior
                img.thumbnail((350, 160), Image.Resampling.LANCZOS)
                
                # Converter para PhotoImage do tkinter
                photo = ImageTk.PhotoImage(img)
                
                def mostrar():
                    loading.destroy()
                    label = ctk.CTkLabel(
                        parent, text="",
                        image=photo,
                    )
                    label.image = photo  # Manter referência
                    label.pack(expand=True, fill="both")
                
                self.after(0, mostrar)
            except Exception as e:
                def fallback():
                    loading.configure(text=fallback_text)
                self.after(0, fallback)
        
        threading.Thread(target=carregar, daemon=True).start()

    def _selecionar_midia(self, item, card_widget=None):
        """Seleciona/deseleciona um item de mídia (toggle)."""
        item_id = getattr(item, "id", None)

        # Verificar se já está selecionado
        for i, sel in enumerate(self._midia_selecionada):
            if getattr(sel, "id", None) == item_id:
                # Deselecionar
                self._midia_selecionada.pop(i)
                if card_widget:
                    card_widget.configure(fg_color=Tema.CARTAO)
                desc = getattr(item, "description", "") or ""
                self._log(f"Removido: {getattr(item, 'source', '?')} - {desc[:30]}")
                self._atualizar_contador_selecionadas()
                self._atualizar_resumo_clipe()
                return

        # Selecionar
        self._midia_selecionada.append(item)
        if card_widget:
            card_widget.configure(fg_color=Tema.SUCESSO)
        desc = getattr(item, "description", "") or ""
        self._log(f"Selecionado: {getattr(item, 'source', '?')} - {desc[:30]}")
        self._atualizar_contador_selecionadas()
        self._atualizar_resumo_clipe()

    def _atualizar_contador_selecionadas(self):
        """Atualiza o contador de itens selecionados."""
        if hasattr(self, 'lbl_qtd_selecionadas'):
            self.lbl_qtd_selecionadas.configure(
                text=f"{len(self._midia_selecionada)} itens"
            )
        # Quantidade de mídia muda o cálculo: mantém a previsão honesta.
        self._atualizar_previsao_plano()

    # ══════════════════════════════════════════════════════════
    # Ritmo / descrição / previsão do cálculo
    # ══════════════════════════════════════════════════════════

    def _modo_ritmo(self) -> str:
        """Traduz o rótulo da tela para o modo do planejador."""
        rotulo = self.var_ritmo_modo.get()
        if "letra" in rotulo:
            return "frases"
        if "batida" in rotulo:
            return "batida"
        return "fixo"

    def _config_ritmo(self):
        """Monta o ConfigRitmo a partir dos controles do painel."""
        from MusicClipStudio.planejador import ConfigRitmo

        cfg = ConfigRitmo(
            modo=self._modo_ritmo(),
            max_por_clipe=float(self.var_max_por_clipe.get()),
            tolerancia=float(self.var_tolerancia.get()) / 100.0,
            batidas_por_troca=int(self.var_batidas_por_troca.get()),
            segundos_por_clipe=float(self.var_effect_duration.get()),
        )

        # A descrição pode sugerir um andamento melhor que o padrão,
        # mas só quando o usuário não escolheu batidas na mão.
        leitura = self._leitura_descricao()
        if leitura and leitura.batidas_por_troca:
            cfg.batidas_por_troca = int(leitura.batidas_por_troca)

        return cfg.validar()

    def _leitura_descricao(self):
        """Interpreta a descrição da música. Nunca levanta."""
        texto = self.var_descricao_musica.get()
        if not texto or not texto.strip():
            return None
        try:
            from MusicClipStudio.descricao_musical import interpretar_descricao

            return interpretar_descricao(texto)
        except Exception as e:
            self._log(f"[WARN] Não entendi a descrição: {e}")
            return None

    def _usar_exemplo_descricao(self, texto: str):
        self.var_descricao_musica.set(texto)
        self._ler_descricao_musica()

    def _ler_descricao_musica(self):
        """Mostra o que o código entendeu da descrição digitada."""
        leitura = self._leitura_descricao()
        lbl = getattr(self, "lbl_leitura_descricao", None)

        if leitura is None or leitura.vazia:
            if lbl is not None:
                lbl.configure(
                    text="(não usada — o clipe segue só pela letra)",
                    text_color=Tema.TEXTO_DIM,
                )
            self._atualizar_previsao_plano()
            return

        # Conflito de clima entre letra e descrição: avisa, não decide.
        conflitos = []
        try:
            from MusicClipStudio.descricao_musical import detectar_conflito
            from MusicClipStudio.interpretacao import interpretar_letra

            letra = self._letra_oficial()
            if letra:
                emocao = getattr(interpretar_letra(letra), "emocao", None)
                conflitos = detectar_conflito(emocao, leitura)
        except Exception:
            conflitos = []

        texto = f"Entendi: {leitura.resumo()}"

        # Se um tema foi detectado, avisamos que a busca vai por ele
        if leitura.tema_id:
            texto += (
                f"\n\nTema: {leitura.tema_nome} — a busca usará "
                f"{len(leitura.tema_termos)} termos visuais deste tema"
            )
            if leitura.tema_ignora_letra:
                texto += " (a letra não influencia a busca)"

        if conflitos:
            texto += "\n\n" + "\n".join(conflitos)
            if lbl is not None:
                lbl.configure(text=texto, text_color=Tema.AVISO)
            for c in conflitos:
                self._log(f"[WARN] {c}")
        else:
            if lbl is not None:
                lbl.configure(text=texto, text_color=Tema.TEXTO_DIM)

        self._log(f"[MUSICA] {leitura.resumo()}")
        self._atualizar_previsao_plano()

    def _atualizar_previsao_plano(self):
        """Calcula o plano e mostra quantas mídias faltam ANTES de gerar."""
        lbl = getattr(self, "lbl_previsao_plano", None)
        if lbl is None:
            return

        try:
            from MusicClipStudio.planejador import calcular_plano

            analise = self._analise_audio_cache()
            segmentos = self.ler_legenda_editada()

            plano = calcular_plano(
                duracao=float(self.var_video_duration.get()),
                midias=self._midia_selecionada,
                config=self._config_ritmo(),
                segmentos=segmentos,
                analise=analise,
                callback_log=lambda _m: None,
            )

            if plano.n_slots == 0:
                lbl.configure(
                    text="Sem mídia selecionada — nada a calcular.",
                    text_color=Tema.TEXTO_DIM,
                )
                return

            if not self._midia_selecionada:
                # Sem midia nao existe clipe: mostrar "8 clipes" seria mentira.
                lbl.configure(
                    text=f"A música pede {plano.n_slots} clipe(s) "
                         f"(~{plano.duracao_media:.1f}s cada).\n"
                         f"Selecione mídias na etapa anterior.",
                    text_color=Tema.AVISO,
                )
                return

            linhas = [
                f"{plano.n_slots} clipe(s) · {plano.modo_usado}",
                f"~{plano.duracao_media:.1f}s por clipe",
                f"cobre {plano.duracao_coberta:.0f}s de "
                f"{plano.duracao_musica:.0f}s",
            ]
            if plano.bpm:
                linhas.append(f"{plano.bpm:.0f} BPM")

            cor = Tema.TEXTO_DIM
            if plano.midias_faltando:
                linhas.append(
                    f"faltam {plano.midias_faltando} mídia(s) — "
                    f"{plano.reciclagens} reciclagem(ns)"
                )
                cor = Tema.AVISO
            elif self._midia_selecionada:
                sobra = len(self._midia_selecionada) - plano.n_slots
                if sobra > 0:
                    linhas.append(f"sobram {sobra} mídia(s) sem uso")

            for aviso in plano.avisos[:2]:
                linhas.append(f"! {aviso}")

            lbl.configure(text="\n".join(linhas), text_color=cor)

        except Exception as e:
            lbl.configure(
                text=f"Cálculo indisponível: {e}", text_color=Tema.DESTRUIVA
            )

    def _analise_audio_cache(self):
        """Analisa o áudio uma vez e reaproveita (caro: BPM + energia).

        Chave = caminho + mtime, para uma trilha trocada invalidar o cache.
        """
        if not self._trilha_path:
            return None

        try:
            caminho = Path(self._trilha_path)
            if not caminho.exists():
                return None
            chave = (str(caminho), caminho.stat().st_mtime)

            if getattr(self, "_analise_cache", None) is not None:
                if self._analise_cache[0] == chave:
                    return self._analise_cache[1]

            from MusicClipStudio.analise_audio import analisar

            resultado = analisar(self._trilha_path, callback_log=lambda _m: None)
            self._analise_cache = (chave, resultado)
            return resultado
        except Exception as e:
            self._log(f"[WARN] Análise de áudio indisponível: {e}")
            return None

    def _adicionar_arquivo_midia(self):
        arquivos = filedialog.askopenfilenames(
            title="Adicionar mídia",
            filetypes=[
                ("Todos", "*.*"),
                ("Mídia", "*.jpg *.jpeg *.png *.mp4 *.webp *.gif *.bmp"),
                ("Áudio", "*.mp3 *.wav *.ogg *.m4a"),
            ],
        )
        if arquivos:
            for arquivo in arquivos:
                ext = Path(arquivo).suffix.lower()
                tipo = "video" if ext in [".mp4", ".webm", ".avi"] else "photo"
                if ext in [".mp3", ".wav", ".ogg", ".m4a"]:
                    tipo = "audio"
                
                item = StockMedia(
                    id=f"local_{abs(hash(arquivo)) % 10**8}",
                    url=arquivo,
                    thumbnail_url="",
                    width=0,
                    height=0,
                    source="local",
                    media_type=tipo,
                    category="local",
                    tags=[],
                    description=Path(arquivo).name,
                    download_url=arquivo,
                )
                self._midia_selecionada.append(item)
            
            self._log(f"{len(arquivos)} arquivo(s) adicionado(s)")
            self._atualizar_contador_selecionadas()
            self._atualizar_resumo_clipe()

    def _gerar_clip(self):
        """Gera o clipe musical."""
        if not self._midia_selecionada:
            messagebox.showwarning("Aviso", "Selecione pelo menos uma mídia primeiro.")
            return

        letra = self._letra_oficial()
        if not letra:
            messagebox.showwarning(
                "Aviso",
                "Digite ou carregue a letra da música na etapa 1 antes de gerar.",
            )
            return
        
        output_dir = self.var_output_dir.get()
        if not output_dir:
            messagebox.showwarning("Aviso", "Escolha a pasta de saída.")
            return
        
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = str(Path(output_dir) / f"clipe_{timestamp}.mp4")
        
        self._log("[CLIP] Iniciando geração do clipe...")
        self.lbl_status.configure(text="Gerando clipe...", text_color=Tema.AVISO)
        self._definir_estado_gerar(True)

        # Legendas revisadas na etapa 2. Se o usuario nao passou pela
        # etapa, `_linhas_legenda` esta vazio e o video sai sem legenda.
        legendas = self.ler_legenda_editada()
        if legendas:
            self._log(f"[LEGENDA] {len(legendas)} linha(s) serao gravadas no vídeo")
        else:
            self._log("[LEGENDA] Nenhuma linha — vídeo será gerado sem legenda")

        # Ritmo calculado a partir da musica. Montado na thread principal
        # (le widgets de Tk) e passado pronto para a thread de geracao.
        config_ritmo = self._config_ritmo()
        descricao_musica = self.var_descricao_musica.get().strip()
        self._log(
            f"[RITMO] {config_ritmo.modo} · max {config_ritmo.max_por_clipe:.1f}s "
            f"· tolerância {config_ritmo.tolerancia:.0%} "
            f"· {config_ritmo.batidas_por_troca} batidas/troca"
        )

        def gerar():
            try:
                from MusicClipStudio.gerador import gerar_clipe
                
                resultado = gerar_clipe(
                    midia_selecionada=self._midia_selecionada,
                    output_path=output_path,
                    duracao_total=self.var_video_duration.get(),
                    fps=int(self.var_video_fps.get()),
                    formato=self.var_video_format.get(),
                    efeito=self.var_effect.get(),
                    transicao=self.var_transition.get(),
                    duracao_por_imagem=self.var_effect_duration.get(),
                    audio_path=self._trilha_path,
                    legendas=legendas,
                    config_ritmo=config_ritmo,
                    descricao=descricao_musica,
                    callback_log=lambda msg: self.after(0, lambda m=msg: self._log(m)),
                    callback_prog=lambda p: self.after(0, lambda v=p: self.barra_progresso.set(v/100)),
                )
                
                def reativar():
                    self._definir_estado_gerar(False)
                    if resultado:
                        self.lbl_status.configure(
                            text=f"Pronto: {Path(resultado).name}",
                            text_color=Tema.SUCESSO
                        )
                        self._log(f"[OK] Clipe salvo em: {resultado}")
                    else:
                        self.lbl_status.configure(
                            text="Erro na geração",
                            text_color=Tema.DESTRUIVA
                        )
                self.after(0, reativar)
            except Exception as e:
                def erro():
                    self._definir_estado_gerar(False)
                    self._log(f"[ERROR] Erro: {e}")
                    self.lbl_status.configure(
                        text="Erro na geração",
                        text_color=Tema.DESTRUIVA
                    )
                self.after(0, erro)
        
        threading.Thread(target=gerar, daemon=True).start()

    def _escolher_pasta_saida(self):
        """Abre diálogo para escolher pasta de saída."""
        pasta = filedialog.askdirectory(title="Escolher pasta de saída")
        if pasta:
            self.var_output_dir.set(pasta)
            self._config.output_dir = pasta
            self._log(f"Pasta de saída: {pasta}")

    def _definir_estado_gerar(self, ocupado: bool):
        """Mantém os botões 'Gerar' (topbar + etapa 5) em sincronia.

        Existem dois botões que disparam a geração, em pontos diferentes da
        tela. Sem isto, um deles ficava clicável durante a geração (B2).
        """
        for attr in ("_btn_gerar_topbar", "btn_gerar"):
            btn = getattr(self, attr, None)
            if btn is None:
                continue
            try:
                if ocupado:
                    btn.configure(state="disabled", text="Gerando...",
                                   fg_color=Tema.BLOQUEADO)
                else:
                    btn.configure(state="normal", fg_color=Tema.PRIMARY)
                    # O botão da etapa 5 tem rótulo longo e próprio.
                    btn.configure(
                        text="GERAR CLIPE MUSICAL"
                        if btn is getattr(self, "_btn_gerar_passo5", None)
                        else "Gerar"
                    )
            except Exception:
                pass

    def _abrir_config_apis(self):
        try:
            from MusicClipStudio.ui_config import APIConfigUI
            APIConfigUI(self).show()
        except Exception as e:
            messagebox.showinfo("Config", f"Configuração de APIs: {e}")

    def _log(self, msg: str):
        self.log_box.insert("end", f"• {msg}\n")
        self.log_box.see("end")


def main():
    app = GuiClipes()
    app.mainloop()


if __name__ == "__main__":
    main()
