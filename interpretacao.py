"""
MusicClipStudio/interpretacao.py
Camada de interpretação emocional da letra.

PROBLEMA QUE ESTE MÓDULO RESOLVE
--------------------------------
Buscar mídia a partir da letra crua produz resultados literais e errados.
Se a letra diz "estou de coração partido", uma busca direta devolve:

    - corações despedaçados (clipart 3D)
    - ilustrações de emoji de coração quebrado

O que o clipe precisa é:

    - uma pessoa triste, chorando, sozinha na janela
    - sombra na parede, olhar baixo, desabafo no telefone

O salto é de METÁFORA → SENSAÇÃO FÍSICA FILMÁVEL. Nunca de metáfora → objeto
da metáfora. Este módulo faz esse salto.

COMO FUNCIONA
-------------
1. A linha da letra é normalizada (acentos, caixa, pontuação).
2. Procuramos expressões emocionais conhecidas (PT e EN), do mais específico
   para o mais genérico — "coração partido" antes de "coração".
3. Cada expressão aponta para uma EMOÇÃO e para a INTENSIDADE dela.
4. A emoção vira um conjunto de CENAS VISUAIS concretas, já em inglês, que é
   o idioma com melhor acervo nos bancos de imagem.
5. Negação ("não estou mais triste") e contraste ("chorei mas agora sorrio")
   ajustam o resultado.

O módulo é determinístico e offline: não chama API nenhuma. Isso é de
propósito — a escolha da cena não pode depender de rede nem ter latência,
já que roda uma vez por beat do clipe.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from enum import Enum
from typing import Final


# ════════════════════════════════════════════════════════════════════
#  EMOÇÕES
# ════════════════════════════════════════════════════════════════════

class Emocao(str, Enum):
    """Emoções que o clipe sabe representar visualmente."""

    TRISTEZA = "tristeza"          # perda, luto, choro, vazio
    SAUDADE = "saudade"            # ausência, lembrança, distância
    SOLIDAO = "solidao"            # isolamento, abandono
    RAIVA = "raiva"                # revolta, grito, ruptura
    MEDO = "medo"                  # apreensão, pesadelo, fuga
    AMOR = "amor"                  # afeto presente, carinho, entrega
    PAZ = "paz"                    # calma, aceitação, natureza
    ALEGRIA = "alegria"            # festa, dança, riso
    EUFORIA = "euforia"            # auge, explosão, catarse
    ESPERANCA = "esperanca"        # recomeço, luz, superação
    TENSAO = "tensao"              # expectativa, suspense, iminência
    MELANCOLIA = "melancolia"      # nostalgia doce, fim de tarde


# ════════════════════════════════════════════════════════════════════
#  CENAS VISUAIS POR EMOÇÃO
#  Regra de ouro: nada de objeto da metáfora. Só o que uma câmera filma.
# ════════════════════════════════════════════════════════════════════

CENAS: Final[dict[Emocao, list[str]]] = {
    Emocao.TRISTEZA: [
        "person crying alone in dark room",
        "tears streaming down face close up",
        "silhouette sitting by rainy window",
        "sad woman looking down at floor",
        "hands covering face grief",
        "lonely figure walking in rain at night",
    ],
    Emocao.SAUDADE: [
        "woman looking at old photographs",
        "empty chair by window soft light",
        "person staring at distant horizon",
        "hand touching old letters memory",
        "silhouette waiting at empty train station",
        "faded wall with old picture frames",
    ],
    Emocao.SOLIDAO: [
        "single person alone in crowded street",
        "empty apartment at night one lamp",
        "lone figure on empty beach winter",
        "person sitting alone in diner window",
        "empty bed unmade morning light",
        "solitary walk through fog",
    ],
    Emocao.RAIVA: [
        "fists clenched close up tension",
        "person shouting screaming frustration",
        "shattered glass on floor",
        "stormy sky dark clouds brewing",
        "sharp shadows on angry face",
        "slammed door motion blur",
    ],
    Emocao.MEDO: [
        "person hiding in shadows looking back",
        "dark corridor with single light",
        "running figure motion blur night",
        "hands trembling close up",
        "empty room with unsettling light",
        "silhouette before closed door",
    ],
    Emocao.AMOR: [
        "couple holding hands close up",
        "tender embrace soft window light",
        "two people laughing together warm",
        "gentle touch on face",
        "slow dance in living room",
        "sunrise walk together holding hands",
    ],
    Emocao.PAZ: [
        "calm lake mirror reflection dawn",
        "person breathing deeply in nature",
        "soft light through forest leaves",
        "still water with gentle ripples",
        "quiet field of tall grass wind",
        "meditation silhouette at sunrise",
    ],
    Emocao.ALEGRIA: [
        "friends laughing together outdoors",
        "person dancing freely in street",
        "children running through sprinkler",
        "celebration confetti in the air",
        "barefoot running on grass",
        "smiling face lit by warm sun",
    ],
    Emocao.EUFORIA: [
        "concert crowd hands raised lights",
        "person jumping arms open sky",
        "confetti explosion celebration",
        "dancing wildly in neon lights",
        "standing on mountain peak victorious",
        "surfing huge wave motion",
    ],
    Emocao.ESPERANCA: [
        "sunrise breaking over horizon",
        "person walking toward open door light",
        "seedling growing through cracked concrete",
        "first light through curtains morning",
        "person looking up at bright sky",
        "open road stretching toward sunrise",
    ],
    Emocao.TENSAO: [
        "clock ticking close up",
        "person pacing room shadows",
        "hand hovering over phone",
        "car headlights in rearview mirror",
        "two people in standoff silent",
        "footstep in empty hallway",
    ],
    Emocao.MELANCOLIA: [
        "golden hour empty street autumn",
        "person watching sunset alone rooftop",
        "old record player spinning",
        "rain on window late afternoon",
        "empty swing moving in breeze",
        "dust particles in beam of light",
    ],
}


# ════════════════════════════════════════════════════════════════════
#  LÉXICO EMOCIONAL
#  Ordem importa: o dicionário é percorrido do mais específico ao mais
#  genérico. Expressões longas vêm primeiro para não serem capturadas
#  por palavras soltas (ex.: "coração partido" antes de "coração").
# ════════════════════════════════════════════════════════════════════

LEXICO: Final[list[tuple[str, Emocao, float]]] = [
    # ── TRISTEZA — perda, choro, vazio ──────────────────────────────
    ("coracao partido", Emocao.TRISTEZA, 1.0),
    ("coracao quebrado", Emocao.TRISTEZA, 1.0),
    ("coracao em pedacos", Emocao.TRISTEZA, 1.0),
    ("em pedacos", Emocao.TRISTEZA, 0.9),
    ("despedacado", Emocao.TRISTEZA, 0.9),
    ("broken heart", Emocao.TRISTEZA, 1.0),
    ("heart in pieces", Emocao.TRISTEZA, 1.0),
    ("brokenhearted", Emocao.TRISTEZA, 1.0),
    ("broken hearted", Emocao.TRISTEZA, 1.0),
    ("heartbreak", Emocao.TRISTEZA, 0.95),
    ("chorei", Emocao.TRISTEZA, 0.9),
    ("chorando", Emocao.TRISTEZA, 0.9),
    ("choro", Emocao.TRISTEZA, 0.85),
    ("lagrimas", Emocao.TRISTEZA, 0.9),
    ("tears", Emocao.TRISTEZA, 0.85),
    ("crying", Emocao.TRISTEZA, 0.9),
    ("sofrendo", Emocao.TRISTEZA, 0.85),
    ("dor", Emocao.TRISTEZA, 0.7),
    ("magoa", Emocao.TRISTEZA, 0.8),
    ("ferida", Emocao.TRISTEZA, 0.7),
    ("vazio", Emocao.TRISTEZA, 0.7),
    ("emptiness", Emocao.TRISTEZA, 0.7),
    ("triste", Emocao.TRISTEZA, 0.8),
    ("tristeza", Emocao.TRISTEZA, 0.85),
    ("sad", Emocao.TRISTEZA, 0.8),
    ("sadness", Emocao.TRISTEZA, 0.85),
    ("acabou", Emocao.TRISTEZA, 0.7),
    ("adeus", Emocao.TRISTEZA, 0.8),
    ("goodbye", Emocao.TRISTEZA, 0.75),
    ("perdi", Emocao.TRISTEZA, 0.75),
    ("lost you", Emocao.TRISTEZA, 0.85),

    # ── SAUDADE — ausência, memória ─────────────────────────────────
    ("saudade", Emocao.SAUDADE, 1.0),
    ("saudades", Emocao.SAUDADE, 1.0),
    ("tenho saudade", Emocao.SAUDADE, 1.0),
    ("lembranca", Emocao.SAUDADE, 0.85),
    ("lembrancas", Emocao.SAUDADE, 0.85),
    ("memoria", Emocao.SAUDADE, 0.8),
    ("memories", Emocao.SAUDADE, 0.8),
    ("memory", Emocao.SAUDADE, 0.75),
    ("longing", Emocao.SAUDADE, 0.9),
    ("missing you", Emocao.SAUDADE, 0.95),
    ("miss you", Emocao.SAUDADE, 0.9),
    ("ainda lembro", Emocao.SAUDADE, 0.9),
    ("te espero", Emocao.SAUDADE, 0.8),
    ("distante", Emocao.SAUDADE, 0.7),
    ("longe de voce", Emocao.SAUDADE, 0.85),
    ("passado", Emocao.SAUDADE, 0.6),

    # ── SOLIDÃO ─────────────────────────────────────────────────────
    ("sozinho", Emocao.SOLIDAO, 0.9),
    ("sozinha", Emocao.SOLIDAO, 0.9),
    ("só eu", Emocao.SOLIDAO, 0.85),
    ("solidao", Emocao.SOLIDAO, 0.95),
    ("lonely", Emocao.SOLIDAO, 0.9),
    ("alone", Emocao.SOLIDAO, 0.85),
    ("abandonado", Emocao.SOLIDAO, 0.85),
    ("abandonada", Emocao.SOLIDAO, 0.85),
    ("ninguem", Emocao.SOLIDAO, 0.7),
    ("ninguem me", Emocao.SOLIDAO, 0.85),

    # ── RAIVA ───────────────────────────────────────────────────────
    ("raiva", Emocao.RAIVA, 0.95),
    ("odio", Emocao.RAIVA, 0.95),
    ("odeio", Emocao.RAIVA, 0.9),
    ("anger", Emocao.RAIVA, 0.9),
    ("hate", Emocao.RAIVA, 0.9),
    ("furioso", Emocao.RAIVA, 0.9),
    ("furious", Emocao.RAIVA, 0.9),
    ("grito", Emocao.RAIVA, 0.8),
    ("gritar", Emocao.RAIVA, 0.8),
    ("scream", Emocao.RAIVA, 0.85),
    ("revolta", Emocao.RAIVA, 0.85),
    ("chega", Emocao.RAIVA, 0.6),
    ("basta", Emocao.RAIVA, 0.6),

    # ── MEDO ────────────────────────────────────────────────────────
    ("medo", Emocao.MEDO, 0.9),
    ("assustado", Emocao.MEDO, 0.85),
    ("assustada", Emocao.MEDO, 0.85),
    ("fear", Emocao.MEDO, 0.9),
    ("afraid", Emocao.MEDO, 0.9),
    ("scared", Emocao.MEDO, 0.9),
    ("terror", Emocao.MEDO, 0.9),
    ("pesadelo", Emocao.MEDO, 0.85),
    ("nightmare", Emocao.MEDO, 0.85),
    ("fugir", Emocao.MEDO, 0.8),
    ("escapar", Emocao.MEDO, 0.75),
    ("perigo", Emocao.MEDO, 0.8),
    ("danger", Emocao.MEDO, 0.8),

    # ── AMOR ────────────────────────────────────────────────────────
    ("te amo", Emocao.AMOR, 1.0),
    ("amo voce", Emocao.AMOR, 1.0),
    ("amor", Emocao.AMOR, 0.9),
    ("apaixonado", Emocao.AMOR, 0.95),
    ("apaixonada", Emocao.AMOR, 0.95),
    ("love you", Emocao.AMOR, 1.0),
    ("i love", Emocao.AMOR, 0.95),
    ("beijo", Emocao.AMOR, 0.85),
    ("abraco", Emocao.AMOR, 0.85),
    ("kiss", Emocao.AMOR, 0.85),
    ("hug", Emocao.AMOR, 0.8),
    ("meu bem", Emocao.AMOR, 0.8),
    ("querida", Emocao.AMOR, 0.75),
    ("carinho", Emocao.AMOR, 0.8),
    ("junto de voce", Emocao.AMOR, 0.8),

    # ── PAZ ─────────────────────────────────────────────────────────
    ("paz", Emocao.PAZ, 0.9),
    ("peace", Emocao.PAZ, 0.9),
    ("calmo", Emocao.PAZ, 0.85),
    ("calma", Emocao.PAZ, 0.85),
    ("calm", Emocao.PAZ, 0.85),
    ("tranquilo", Emocao.PAZ, 0.8),
    ("sereno", Emocao.PAZ, 0.8),
    ("respirar", Emocao.PAZ, 0.7),
    ("silencio", Emocao.PAZ, 0.7),
    ("silence", Emocao.PAZ, 0.7),
    ("serenity", Emocao.PAZ, 0.85),

    # ── ALEGRIA ─────────────────────────────────────────────────────
    ("feliz", Emocao.ALEGRIA, 0.9),
    ("felicidade", Emocao.ALEGRIA, 0.95),
    ("alegria", Emocao.ALEGRIA, 0.95),
    ("happy", Emocao.ALEGRIA, 0.9),
    ("happiness", Emocao.ALEGRIA, 0.95),
    ("sorrindo", Emocao.ALEGRIA, 0.85),
    ("sorriso", Emocao.ALEGRIA, 0.85),
    ("sorrio", Emocao.ALEGRIA, 0.85),
    ("sorri", Emocao.ALEGRIA, 0.8),
    ("sorrir", Emocao.ALEGRIA, 0.85),
    ("sorridente", Emocao.ALEGRIA, 0.85),
    ("smile", Emocao.ALEGRIA, 0.85),
    ("smiling", Emocao.ALEGRIA, 0.85),
    ("rindo", Emocao.ALEGRIA, 0.85),
    ("ri", Emocao.ALEGRIA, 0.7),
    ("laughing", Emocao.ALEGRIA, 0.85),
    ("dancando", Emocao.ALEGRIA, 0.85),
    ("dancei", Emocao.ALEGRIA, 0.8),
    ("dancing", Emocao.ALEGRIA, 0.85),
    ("festa", Emocao.ALEGRIA, 0.8),
    ("party", Emocao.ALEGRIA, 0.8),

    # ── EUFORIA ─────────────────────────────────────────────────────
    ("explodir", Emocao.EUFORIA, 0.8),
    ("no auge", Emocao.EUFORIA, 0.85),
    ("vitoria", Emocao.EUFORIA, 0.85),
    ("victory", Emocao.EUFORIA, 0.85),
    ("liberdade", Emocao.EUFORIA, 0.8),
    ("freedom", Emocao.EUFORIA, 0.8),
    ("voar", Emocao.EUFORIA, 0.75),
    ("flying", Emocao.EUFORIA, 0.75),
    ("invencivel", Emocao.EUFORIA, 0.85),
    ("unstopable", Emocao.EUFORIA, 0.8),

    # ── ESPERANÇA ───────────────────────────────────────────────────
    ("esperanca", Emocao.ESPERANCA, 0.95),
    ("hope", Emocao.ESPERANCA, 0.95),
    ("recomeco", Emocao.ESPERANCA, 0.9),
    ("recomecar", Emocao.ESPERANCA, 0.9),
    ("start again", Emocao.ESPERANCA, 0.9),
    ("novo dia", Emocao.ESPERANCA, 0.85),
    ("amanhecer", Emocao.ESPERANCA, 0.85),
    ("sunrise", Emocao.ESPERANCA, 0.8),
    ("luz", Emocao.ESPERANCA, 0.7),
    ("light", Emocao.ESPERANCA, 0.65),
    ("vai passar", Emocao.ESPERANCA, 0.9),
    ("melhorar", Emocao.ESPERANCA, 0.75),
    ("futuro", Emocao.ESPERANCA, 0.7),
    # Expressões de renascimento — a letra raramente diz "esperança"
    # literal; ela diz que o sol nasce de novo.
    ("sol vai nascer", Emocao.ESPERANCA, 0.85),
    ("sol nascer", Emocao.ESPERANCA, 0.8),
    ("sol nasceu", Emocao.ESPERANCA, 0.8),
    ("nascer de novo", Emocao.ESPERANCA, 0.85),
    ("sun will rise", Emocao.ESPERANCA, 0.8),
    ("new day", Emocao.ESPERANCA, 0.75),
    ("dia novo", Emocao.ESPERANCA, 0.8),
    ("vai melhorar", Emocao.ESPERANCA, 0.85),
    ("dias melhores", Emocao.ESPERANCA, 0.85),
    ("segue em frente", Emocao.ESPERANCA, 0.75),
    ("sigo em frente", Emocao.ESPERANCA, 0.75),
    ("levantar", Emocao.ESPERANCA, 0.7),
    ("vencer", Emocao.ESPERANCA, 0.7),
    ("superar", Emocao.ESPERANCA, 0.8),

    # ── TENSÃO ──────────────────────────────────────────────────────
    ("tensao", Emocao.TENSAO, 0.9),
    ("tension", Emocao.TENSAO, 0.9),
    ("ansioso", Emocao.TENSAO, 0.85),
    ("ansiedade", Emocao.TENSAO, 0.85),
    ("anxious", Emocao.TENSAO, 0.85),
    ("nervoso", Emocao.TENSAO, 0.8),
    ("esperando", Emocao.TENSAO, 0.7),
    ("waiting", Emocao.TENSAO, 0.7),
    ("suspense", Emocao.TENSAO, 0.85),
    ("silence", Emocao.TENSAO, 0.6),
    ("segredo", Emocao.TENSAO, 0.75),
    ("secret", Emocao.TENSAO, 0.75),

    # ── MELANCOLIA ──────────────────────────────────────────────────
    ("melancolia", Emocao.MELANCOLIA, 0.95),
    ("melancholy", Emocao.MELANCOLIA, 0.95),
    ("nostalgia", Emocao.MELANCOLIA, 0.9),
    ("nostalgic", Emocao.MELANCOLIA, 0.9),
    ("outono", Emocao.MELANCOLIA, 0.75),
    ("autumn", Emocao.MELANCOLIA, 0.75),
    ("fim de tarde", Emocao.MELANCOLIA, 0.8),
    ("sunset", Emocao.MELANCOLIA, 0.7),
    ("por do sol", Emocao.MELANCOLIA, 0.75),
    ("passando", Emocao.MELANCOLIA, 0.6),
]


# ════════════════════════════════════════════════════════════════════
#  MARCADORES DE CONTRASTE E NEGAÇÃO
# ════════════════════════════════════════════════════════════════════

NEGACOES: Final[tuple[str, ...]] = (
    "nao", "nem", "nunca", "jamais", "no", "not", "never", "dont", "don't",
)

CONTRASTE: Final[tuple[str, ...]] = (
    "mas", "porem", "contudo", "entretanto", "todavia",
    "but", "however", "though", "yet", "although",
)

# Emoções positivas, para o ajuste de contraste saber o que é "virada".
POSITIVAS: Final[frozenset[Emocao]] = frozenset({
    Emocao.ALEGRIA, Emocao.EUFORIA, Emocao.ESPERANCA,
    Emocao.AMOR, Emocao.PAZ,
})


# ════════════════════════════════════════════════════════════════════
#  RESULTADO
# ════════════════════════════════════════════════════════════════════

@dataclass
class LeituraEmocional:
    """Resultado da interpretação de uma linha da letra."""

    linha_original: str
    emocao: Emocao
    intensidade: float                      # 0.0 a 1.0
    confianca: float                        # 0.0 a 1.0
    cenas: list[str] = field(default_factory=list)
    gatilhos: list[str] = field(default_factory=list)
    tem_negacao: bool = False
    tem_contraste: bool = False
    virada: bool = False                    # contraste que troca a emoção

    @property
    def query_visual(self) -> str:
        """Query principal, pronta para os bancos de imagem."""
        return self.cenas[0] if self.cenas else ""

    def queries(self, n: int = 3) -> list[str]:
        """As n melhores queries para esta leitura."""
        return self.cenas[:n]


# ════════════════════════════════════════════════════════════════════
#  NORMALIZAÇÃO
# ════════════════════════════════════════════════════════════════════

def normalizar(texto: str) -> str:
    """Minúsculas, sem acento, pontuação vira espaço.

    Reduzir a acento facilita casar "coração" e "coracao" na mesma regra,
    que é como as pessoas escrevem letra na prática.
    """
    if not texto:
        return ""
    # Decompõe e remove os acentos
    sem_acento = "".join(
        c for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )
    sem_acento = sem_acento.lower()
    # Pontuação e símbolos viram espaço, preservando espaços existentes
    limpo = re.sub(r"[^\w\s]", " ", sem_acento)
    return re.sub(r"\s+", " ", limpo).strip()


def _tem_marcador(texto_normalizado: str, marcadores: tuple[str, ...]) -> bool:
    """Verifica se algum marcador aparece como palavra inteira."""
    palavras = set(texto_normalizado.split())
    for m in marcadores:
        if " " in m:
            if m in texto_normalizado:
                return True
        elif m in palavras:
            return True
    return False


# Palavras que podem aparecer ENTRE as partes de uma expressão sem
# mudar o sentido. "meu coração ESTÁ EM pedaços" precisa casar com
# "coracao em pedacos" mesmo com o verbo no meio.
_VAZIAS_INTERCALADAS: Final[frozenset[str]] = frozenset({
    "esta", "estao", "estou", "ta", "tava", "foi", "era", "sera",
    "ficou", "ficando", "ja", "muito", "todo", "toda", "todos", "todas",
    "meu", "minha", "seu", "sua", "o", "a", "os", "as", "de", "do", "da",
    "em", "num", "numa", "e", "is", "was", "my", "your", "the", "in",
    "so", "very", "been", "being", "got", "get", "am", "are",
})


def _casa_expressao(expressao: str, texto: str, palavras: list[str]) -> bool:
    """Casa uma expressão multipalavra tolerando palavras vazias no meio.

    Casamento direto de substring é rígido demais: a letra real escreve
    "meu coração está em pedaços" e não "coração em pedaços". Aqui as
    palavras-chave da expressão precisam aparecer na ORDEM certa, mas
    palavras vazias podem se intercalar entre elas.
    """
    if " " not in expressao:
        return expressao in palavras

    if expressao in texto:
        return True

    alvo = expressao.split()
    i_alvo = 0
    for palavra in palavras:
        if i_alvo >= len(alvo):
            return True
        if palavra == alvo[i_alvo]:
            i_alvo += 1
        elif palavra in _VAZIAS_INTERCALADAS:
            continue
        else:
            # Palavra de conteúdo fora de ordem: não casa.
            return False
    return i_alvo >= len(alvo)


# ════════════════════════════════════════════════════════════════════
#  NÚCLEO
# ════════════════════════════════════════════════════════════════════

def interpretar(linha: str) -> LeituraEmocional:
    """Traduz uma linha de letra em emoção e cenas visuais filmáveis.

    Este é o ponto de entrada principal.

    >>> r = interpretar("estou de coração partido")
    >>> r.emocao
    <Emocao.TRISTEZA: 'tristeza'>
    >>> r.query_visual
    'person crying alone in dark room'
    """
    original = linha or ""
    texto = normalizar(original)

    if not texto:
        return LeituraEmocional(
            linha_original=original,
            emocao=Emocao.MELANCOLIA,
            intensidade=0.3,
            confianca=0.0,
            cenas=list(CENAS[Emocao.MELANCOLIA]),
        )

    tem_neg = _tem_marcador(texto, NEGACOES)
    tem_con = _tem_marcador(texto, CONTRASTE)

    # ── Casamento do léxico ─────────────────────────────────────────
    # Percorremos na ordem declarada (específico -> genérico) e guardamos
    # todos os acertos, não só o primeiro: a linha mais longa costuma
    # trazer mais de uma emoção e queremos resolver isso depois.
    acertos: list[tuple[str, Emocao, float]] = []
    palavras = texto.split()
    for expressao, emocao, forca in LEXICO:
        if _casa_expressao(expressao, texto, palavras):
            acertos.append((expressao, emocao, forca))

    if acertos:
        # A expressão mais longa é a mais específica, portanto a mais
        # confiável. Empate resolve pela força declarada.
        acertos.sort(key=lambda a: (len(a[0]), a[2]), reverse=True)
        gatilho, emocao, forca = acertos[0]
        confianca = 0.75 if len(gatilho) > 8 else 0.6
        if len(acertos) > 1:
            # Mais evidência convergindo aumenta a confiança.
            confianca = min(0.95, confianca + 0.15)
    else:
        # Sem acerto: a linha não tem carga emocional explícita.
        # Devolvemos melancolia neutra com confiança baixa, para o
        # chamador poder preferir o mood global do clipe.
        return LeituraEmocional(
            linha_original=original,
            emocao=Emocao.MELANCOLIA,
            intensidade=0.35,
            confianca=0.1,
            cenas=list(CENAS[Emocao.MELANCOLIA]),
            tem_negacao=tem_neg,
            tem_contraste=tem_con,
        )

    intensidade = forca

    # ── Contraste: "chorei, mas agora sorrio" ───────────────────────
    # Havendo contraste, a emoção que aparece DEPOIS do conectivo é a
    # que fecha a linha, então ela vence. Isso é o que dá o arco do
    # clipe: a cena final combina com o último estado da frase.
    virada = False
    if tem_con and len(acertos) > 1:
        pos_marcador = len(texto)
        for c in CONTRASTE:
            pos = texto.find(c)
            if pos != -1:
                pos_marcador = min(pos_marcador, pos)

        # Comparamos pela posição de cada expressão no texto, não pela
        # ordem em que apareceram na varredura do léxico.
        def _posicao(expr: str) -> int:
            p = texto.find(expr)
            if p != -1:
                return p
            # Expressão flexível: usamos a posição da primeira palavra.
            primeira = expr.split()[0]
            return texto.find(primeira)

        depois = [a for a in acertos if _posicao(a[0]) > pos_marcador]
        if depois:
            # Entre as que vêm depois, a mais específica manda.
            depois.sort(key=lambda a: (len(a[0]), a[2]), reverse=True)
            gatilho, emocao, forca = depois[0]
            intensidade = forca
            virada = True
            confianca = min(0.95, confianca + 0.1)

    # ── Negação ─────────────────────────────────────────────────────
    # "não estou mais triste": a emoção declarada é justamente a que
    # NÃO vale. Trocamos pela oposta e derrubamos a intensidade, porque
    # negação costuma indicar um estado mais brando.
    if tem_neg and emocao not in POSITIVAS:
        oposta = _oposta(emocao)
        if oposta is not None:
            emocao = oposta
            intensidade = max(0.3, intensidade - 0.35)
            confianca = max(0.4, confianca - 0.15)
    elif tem_neg and emocao in POSITIVAS:
        emocao = Emocao.MELANCOLIA
        intensidade = max(0.3, intensidade - 0.3)

    return LeituraEmocional(
        linha_original=original,
        emocao=emocao,
        intensidade=round(intensidade, 2),
        confianca=round(confianca, 2),
        cenas=list(CENAS.get(emocao, CENAS[Emocao.MELANCOLIA])),
        gatilhos=[a[0] for a in acertos[:3]],
        tem_negacao=tem_neg,
        tem_contraste=tem_con,
        virada=virada,
    )


# Mapa de oposição, usado pela negação.
_OPOSTAS: Final[dict[Emocao, Emocao]] = {
    Emocao.TRISTEZA: Emocao.ESPERANCA,
    Emocao.SOLIDAO: Emocao.AMOR,
    Emocao.RAIVA: Emocao.PAZ,
    Emocao.MEDO: Emocao.PAZ,
    Emocao.TENSAO: Emocao.PAZ,
    Emocao.MELANCOLIA: Emocao.ESPERANCA,
    Emocao.SAUDADE: Emocao.PAZ,
    Emocao.AMOR: Emocao.SOLIDAO,
    Emocao.ALEGRIA: Emocao.MELANCOLIA,
    Emocao.EUFORIA: Emocao.MELANCOLIA,
    Emocao.ESPERANCA: Emocao.MELANCOLIA,
    Emocao.PAZ: Emocao.TENSAO,
}


def _oposta(e: Emocao) -> Emocao | None:
    return _OPOSTAS.get(e)


# ════════════════════════════════════════════════════════════════════
#  AGREGADO — leitura de várias linhas
# ════════════════════════════════════════════════════════════════════

def emocao_dominante(linhas: list[str], confianca_minima: float = 0.2) -> Emocao | None:
    """Emoção que mais aparece num conjunto de linhas.

    Serve para decidir o mood global do clipe a partir da letra inteira,
    em vez da primeira palavra-chave que aparecer.

    Devolve None quando NENHUMA linha tem carga emocional confiável. Isso
    importa: uma letra como "epic music" descreve ESTILO, não emoção, e
    forçar um mood ali atropelaria a decisão do usuário. Quem chama deve
    tratar o None caindo no seu próprio critério.

    >>> emocao_dominante(["epic music"]) is None
    True
    >>> emocao_dominante(["chorei a noite inteira"]).value
    'tristeza'
    """
    if not linhas:
        return None

    contagem: dict[Emocao, float] = {}
    for linha in linhas:
        leitura = interpretar(linha)
        if leitura.confianca < confianca_minima:
            continue
        # Ponderamos por intensidade e confiança: uma linha muito
        # emocional deve pesar mais que uma linha neutra.
        peso = leitura.intensidade * leitura.confianca
        contagem[leitura.emocao] = contagem.get(leitura.emocao, 0.0) + peso

    if not contagem:
        return None
    return max(contagem.items(), key=lambda kv: kv[1])[0]


def intensidade_media(linhas: list[str]) -> float:
    """Intensidade emocional média, de 0.0 a 1.0.

    Serve para decidir ritmo de corte: letra intensa pede corte mais rápido.
    """
    if not linhas:
        return 0.0
    valores = [interpretar(l).intensidade for l in linhas if l.strip()]
    return round(sum(valores) / len(valores), 2) if valores else 0.0
