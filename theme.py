"""
gui/theme.py
Identidade visual — paleta escura estilo Elton Studio V2.

Direção: "Studio dark" — fundos near-black, contraste elevado,
acento verde para ações primárias, vermelho para navegação ativa,
semânticas distintas: sucesso (verde), aviso (laranja), erro (coral).

Regra de uso:
  - FUNDO/PAINEL/CAMPO/CONTROLE carregam o fundo da interface.
  - CARTAO/CARTAO_HOVER são superfícies de conteúdo (inputs, cards, abas).
  - PRIMARY (verde) é exclusivo do botão que "resolve" a tarefa da tela.
  - NAV_ACTIVE (vermelho) para itens de navegação ativos.
  - DESTRUIVA (vermelho claro) para remoção/parada — nunca PRIMARY.
  - AVISO (laranja) para coisas que pedem atenção.
  - SUCESSO (verde) para estados prontos/OK.
  - ERRO (coral) para texto de erro.
  - INFO (cinza) para neutros.

Toda janela do app deve importar esta classe:
    from MusicClipStudio.theme import Tema
Nunca redefinir cores localmente numa janela nova.
"""

from typing import Final


class Tema:
    # ── Fundos (near-black estilo Elton Studio) ─────────────────────
    FUNDO: Final[str] = "#0B0B10"       # fundo geral da janela/app (near-black)
    PAINEL: Final[str] = "#101018"      # painéis, sidebars, headers
    CAMPO: Final[str] = "#16161F"       # campos/controles em fundo escuro
    CONTROLE: Final[str] = "#16161F"    # alias de CAMPO (compat.)
    HOVER: Final[str] = "#1E1E28"       # hover genérico sobre controle escuro

    # ── Cartões / superfícies (inputs, abas, cards funcionais) ──────
    CARTAO: Final[str] = "#13131B"      # cartões funcionais escuros
    CARTAO_HOVER: Final[str] = "#1A1A24"
    BRANCO: Final[str] = "#E8ECF0"      # texto claro / ícones

    # ── Textbox (fundo escuro, texto claro) ────────────────────────
    TEXTBOX_FUNDO: Final[str] = "#16161F"
    TEXTBOX_TEXTO: Final[str] = "#C8D0D8"

    # ── Bordas ──────────────────────────────────────────────────────
    BORDA: Final[str] = "#252530"           # borda neutra padrão
    BORDA_DESTAQUE: Final[str] = "#4ADE80"  # verde — foco/seleção
    BORDA_SUAVIZADA: Final[str] = "#1E1E28"  # borda muito sutil, fundo=cartão

    # ── Navegação (vermelho — estilo Elton Studio sidebar) ──────────
    NAV_ACTIVE: Final[str] = "#EF4444"      # item de navegação ativo
    NAV_ACTIVE_HOVER: Final[str] = "#DC2626"
    NAV_BG: Final[str] = "#0E0E14"         # fundo da sidebar de navegação

    # ── Ação primária (verde — CTA principal) ───────────────────────
    PRIMARY: Final[str] = "#4ADE80"
    PRIMARY_HOVER: Final[str] = "#22C55E"

    # ── Dourado (acento visual, com moderação) ─────────────────────
    DOURADO: Final[str] = "#FBBF24"
    DOURADO_HOVER: Final[str] = "#F59E0B"

    # ── Destaque / seleção ──────────────────────────────────────────
    DESTAQUE: Final[str] = "#4ADE80"
    DESTAQUE_HOVER: Final[str] = "#22C55E"

    # aliases históricos — compatibilidade com código existente
    ACENTO_QUENTE: Final[str] = PRIMARY
    ACENTO_QUENTE_HOVER: Final[str] = PRIMARY_HOVER
    ACAO: Final[str] = PRIMARY
    ACAO_HOVER: Final[str] = PRIMARY_HOVER

    # ── Semânticas ─────────────────────────────────────────────────
    SECONDARY: Final[str] = "#1E1E28"       # botões secundários
    SECONDARY_HOVER: Final[str] = "#282834"
    DESTRUIVA: Final[str] = "#EF4444"       # remover/parar
    DESTRUIVA_HOVER: Final[str] = "#DC2626"
    AVISO: Final[str] = "#F59E0B"           # atenção / importância
    AVISO_HOVER: Final[str] = "#D97706"
    SUCESSO: Final[str] = "#4ADE80"         # pronto / OK
    SUCESSO_HOVER: Final[str] = "#22C55E"
    ERRO: Final[str] = "#EF4444"            # texto de erro
    INFO: Final[str] = "#6B7280"            # neutro (cinza)

    # ── Texto ──────────────────────────────────────────────────────
    TEXTO: Final[str] = "#C8D0D8"       # texto principal sobre fundo escuro
    TEXTO_CLARO: Final[str] = "#E8ECF0"  # headers, títulos, textos em destaque
    TEXTO_DIM: Final[str] = "#6B7280"    # texto secundário, placeholders
    TEXTO_SUTIL: Final[str] = "#4B5563"  # labels sutis

    # ── Texto sobre cartões/inputs (leitura em fundos #13131B / #16161F) ──
    TEXTO_CARD: Final[str] = "#D1D8E0"     # texto dentro de cartões/inputs

    # ── Passos / Steps (estilo Elton Studio) ───────────────────────
    STEP_ATIVO: Final[str] = "#4ADE80"    # passo concluído/ativo
    STEP_PENDENTE: Final[str] = "#6B7280" # passo pendente
    STEP_BG: Final[str] = "#13131B"      # fundo do indicador de passo

    # ── Forma ──────────────────────────────────────────────────────
    RAIO_CARD: Final[int] = 10
    RAIO_BOTAO: Final[int] = 8
    RAIO_PILULA: Final[int] = 999   # botões/pills totalmente arredondados

    # ══════════════════════════════════════════════════════════════
    #  ESCALA DE ESPAÇAMENTO (grid de 4px — use sempre estes tokens)
    # ══════════════════════════════════════════════════════════════
    ESP_1: Final[int] = 4
    ESP_2: Final[int] = 8
    ESP_3: Final[int] = 12
    ESP_4: Final[int] = 16
    ESP_5: Final[int] = 24
    ESP_6: Final[int] = 32

    # ══════════════════════════════════════════════════════════════
    #  ESCALA TIPOGRÁFICA
    #  Nomes por PAPEL, não por tamanho — assim um ajuste global de
    #  escala não exige caçar tamanhos espalhados pelo código.
    # ══════════════════════════════════════════════════════════════
    FONTE_MICRO: Final[int] = 9     # legendas de passo, meta-info
    FONTE_PEQUENA: Final[int] = 10  # labels secundários, dicas
    FONTE_BASE: Final[int] = 11     # texto padrão de interface
    FONTE_MEDIA: Final[int] = 12    # corpo de leitura
    FONTE_GRANDE: Final[int] = 15   # títulos de seção
    FONTE_TITULO: Final[int] = 20   # título da etapa
    FONTE_DISPLAY: Final[int] = 26  # título de destaque (raro)

    # ══════════════════════════════════════════════════════════════
    #  DIMENSÕES DE LAYOUT (larguras/alturas canônicas)
    # ══════════════════════════════════════════════════════════════
    SIDEBAR_LARGURA: Final[int] = 196   # sidebar legível (antes: 60, apertada)
    TOPBAR_ALTURA: Final[int] = 56
    INDICADOR_ALTURA: Final[int] = 72   # antes 48 -> subtítulo era cortado
    PAINEL_DIREITO_LARGURA: Final[int] = 300
    ALTURA_BOTAO: Final[int] = 34
    ALTURA_BOTAO_GRANDE: Final[int] = 46
    ALTURA_CAMPO: Final[int] = 34

    # ══════════════════════════════════════════════════════════════
    #  SUPERFÍCIES ADICIONAIS (estados de cartão)
    # ══════════════════════════════════════════════════════════════
    CARTAO_ATIVO: Final[str] = "#18222E"   # cartão selecionado (azul sutil)
    BORDA_ATIVA: Final[str] = "#4ADE80"    # borda de cartão selecionado
    FUNDO_VAZIO: Final[str] = "#0E0E15"    # área de "nenhum resultado ainda"
    BLOQUEADO: Final[str] = "#1A1A22"      # controle desabilitado

    # ── Texto sobre superfícies coloridas ─────────────────────────
    TEXTO_SOBRE_PRIMARIA: Final[str] = "#0B0B10"  # escuro sobre verde
    TEXTO_SOBRE_NAV: Final[str] = "#FFFFFF"       # claro sobre vermelho

    # ══════════════════════════════════════════════════════════════
    #  HELPERS
    # ══════════════════════════════════════════════════════════════
    @staticmethod
    def fonte(tamanho: int, negrito: bool = False):
        """Cria uma CTkFont de forma padronizada.

        Evita `font=ctk.CTkFont(size=11, weight="bold")` espalhado pelo
        código. Import tardio para não quebrar quem importa `Tema` em
        contexto sem GUI.

        Requer uma janela Tk já criada (limitação do próprio Tk). Se for
        chamado cedo demais, devolve uma tupla ("nome", tamanho, "bold"?)
        que o Tk aceita igualmente como especificação de fonte — assim o
        chamador nunca quebra.

        Uso:
            font=Tema.fonte(Tema.FONTE_TITULO, negrito=True)
        """
        import customtkinter as ctk
        try:
            return ctk.CTkFont(size=tamanho, weight="bold" if negrito else "normal")
        except RuntimeError:
            # Sem root Tk ainda: devolve spec de fonte que o Tk aceita.
            return ("TkDefaultFont", tamanho, "bold") if negrito else ("TkDefaultFont", tamanho)
