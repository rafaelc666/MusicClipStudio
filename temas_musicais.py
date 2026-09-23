"""
Temas musicais → termos de busca para mídia de stock.

Quando a música NÃO TEM LETRA em português (ou não tem letra nenhuma),
a busca por palavras-chave da letra falha completamente. Este módulo
mapeia TEMAS reconhecíveis na descrição do usuário para termos de busca
em inglês que realmente encontram vídeos/imagens relevantes.

Cobertura:
  - Música clássica / orquestral / solo instrumental
  - Mantras / cantos sagrados (sânscrito, tibetano, gregoriano)
  - Frequências / healing (432Hz, 528Hz, 741Hz, etc.)
  - Música árabe / turca / persa
  - Ambiente / natureza / meditação / sono
  - Eletrônica / synthwave / lo-fi
  - Jazz / blues / bossa nova

Cada tema define:
  - palavras-chave em português que disparam o tema
  - termos de busca em inglês (priorizados: os primeiros são os melhores)
  - proporção sugerida de vídeos vs fotos
  - se a letra é irrelevante (True = ignora a letra completamente)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TemaMusical:
    """Um tema reconhecível e seus termos de busca."""

    id: str                          # identificador interno
    nome: str                        # nome amigável
    palavras_chave: list[str]        # em português — disparam o tema
    termos_busca: list[str]          # em inglês — vão para o stock API
    descricao: str = ""              # explicação para o log
    ignora_letra: bool = False       # True = não usa a letra para busca
    prioridade_videos: float = 0.5   # 0.0 = só fotos, 1.0 = só vídeos
    # ⚠️ NOVO (23/09/2026): qualificador curto que puxa a ESTÉTICA do gênero
    # nas cenas vindas da emoção da letra (ex.: gospel → "golden light").
    # Vazio = o tema não qualifica cenas da letra.
    estetica: str = ""


# ════════════════════════════════════════════════════════════════
# Catálogo de temas
# ════════════════════════════════════════════════════════════════

TEMAS: list[TemaMusical] = [
    # ── Clássica / Orquestral ─────────────────────────────────
    TemaMusical(
        id="classica",
        nome="Música Clássica",
        palavras_chave=[
            "classica", "clássica", "classico", "clássico",
            "orquestra", "orquestral", "sinfonia", "sinfonica",
            "mozart", "beethoven", "bach", "vivaldi", "chopin",
            "concerto", "opera", "ópera", "aria",
            "violino", "piano", "cello", "violoncelo",
            "quarteto", "quinteto", "filarmonica",
        ],
        termos_busca=[
            "orchestra performing",
            "classical music concert",
            "violinist close up",
            "piano keys hands",
            "concert hall audience",
            "cello player emotional",
            "conductor orchestra",
            "string quartet",
            "symphony orchestra stage",
            "grand piano hall",
        ],
        descricao="Instrumentos, concert halls, maestros",
        prioridade_videos=0.6,
    ),

    # ── Mantras / Sagrado ─────────────────────────────────────
    TemaMusical(
        id="mantra",
        nome="Mantras e Música Sagrada",
        palavras_chave=[
            "mantra", "mantras", "sagrado", "sacred",
            "sánscrito", "sanscrito", "sanskrit",
            "tibetano", "tibetan", "monge", "monk chanting",
            "gregoriano", "gregorian", "canto gregoriano",
            "igreja", "church choir", "cantico",
            "om", "aum", "hare krishna", "buddhist",
            "budista", "meditacao guiada", "meditação guiada",
            "reiki", "chakra", "kundalini",
        ],
        termos_busca=[
            "tibetan monk meditation",
            "buddhist temple golden",
            "prayer wheels spinning",
            "sacred geometry animation",
            "monk chanting monastery",
            "hindu temple ceremony",
            "prayer candles glow",
            "lotus flower bloom",
            "zen garden raking",
            "stained glass church light",
            "tibetan singing bowl",
            "prayer flags wind",
        ],
        descricao="Templos, monges, geometria sagrada, velas",
        ignora_letra=True,
        prioridade_videos=0.7,
    ),

    # ── Gospel / Worship / Louvor ─────────────────────────────
    # ⚠️ NOVO (23/09/2026): faltava tema para letras cristãs — uma
    # música como "Coração Igual ao Teu" (perdão, cruz, quebrantamento)
    # caía no mood DARK genérico e recebia "dark city"/"rainy street",
    # que não têm NADA a ver. Termos visuais típicos do gênero: luz,
    # cruz, céu, mãos, batismo, comunidade, natureza grandiosa.
    TemaMusical(
        id="gospel",
        nome="Gospel / Worship / Louvor",
        palavras_chave=[
            "gospel", "worship", "louvor", "adoracao", "adoração",
            "jesus", "cristo", "christ", "deus", "god", "senhor", "lord",
            "igreja", "church", "fe", "fé", "faith", "oracao", "oração", "prayer",
            "biblia", "bíblia", "bible", "salmo", "psalm", "espirito santo", "espírito santo",
            "cruz", "cross", "calvario", "calvário", "perdao", "perdão", "forgive", "forgiveness",
            "graca", "graça", "grace", "misericordia", "misericórdia", "mercy",
            "salvacao", "salvação", "salvation", "redenção", "redencao", "redemption",
            "batismo", "baptism", "batizar", "consagracao", "consagração",
            "aleluia", "hallelujah", "halleluya", "amem", "amen", "amém",
            "pastor", "congregacao", "congregação", "culto", "missa",
            "coracao igual", "coração igual", "quebrantado", "oleiro", "vaso", "rebanho",
        ],
        termos_busca=[
            "sun rays through clouds sky",
            "cross silhouette sunset",
            "hands raised worship concert",
            "light shining through window church",
            "open bible candle light",
            "person kneeling prayer sunrise",
            "ocean waves sunrise hope",
            "mountain top clouds aerial",
            "dove flying slow motion sky",
            "golden field wind sunset",
            "candle glow dark church",
            "crowd hands united concert light",
            "baptism river water",
            "stained glass light interior",
            "seedling growing sunlight",
            "storm clouds breaking sunlight",
        ],
        descricao="Luz, cruz, céu, mãos em adoração, esperança, natureza grandiosa",
        prioridade_videos=0.55,
        estetica="golden light",
    ),

    # ── Frequências / Healing ─────────────────────────────────
    TemaMusical(
        id="frequencia",
        nome="Frequências e Som Curativo",
        palavras_chave=[
            "432hz", "432 hz", "528hz", "528 hz",
            "741hz", "741 hz", "639hz", "639 hz",
            "frequencia", "frequência", "frequency",
            "solfeggio", "solfégio", "tom curativo",
            "healing sound", "sound healing", "binaural",
            "binural", "theta waves", "delta waves",
            "alpha waves", "gamma waves",
            "prosperidade", "abundancia", "abundância",
            "dinheiro", "riqueza", "manifestacao", "manifestação",
            "dormir", "sono", "sleep", "insônia", "insonia",
            "ansiedade", "calma", "relaxamento profundo",
            "limpeza energética", "aura cleansing",
        ],
        termos_busca=[
            "cosmic energy abstract",
            "fractal animation loop",
            "water ripples slow motion",
            "aurora borealis timelapse",
            "galaxy stars nebula",
            "crystal singing bowl",
            "sacred geometry flower of life",
            "chakra colors glow",
            "ocean waves sunset",
            "forest stream peaceful",
            "abstract particles flow",
            "mandala spinning",
            "moon phases timelapse",
            "sunlight through trees",
        ],
        descricao="Abstrato, cósmico, natureza, geometria sagrada, cristais",
        ignora_letra=True,
        prioridade_videos=0.8,
    ),

    # ─- Árabe / Turca / Persa ─────────────────────────────────
    TemaMusical(
        id="arabe",
        nome="Música Árabe / Turca / Persa",
        palavras_chave=[
            "arabe", "árabe", "arabic", "arabo",
            "turca", "turkish", "turco",
            "persa", "persian", "iraniano",
            "oud", "qanun", "ney", "darbuka", "darbouka",
            "belly dance", "danca do ventre", "dança do ventre",
            "sufi", "sufismo", "whirling dervish",
            "medio oriente", "médio oriente", "middle east",
            "marrocos", "morocco", "marrakesh",
            "bazaar", "bazar", "souk", "souq",
        ],
        termos_busca=[
            "middle eastern architecture",
            "moroccan lantern glow",
            "desert sunset camel",
            "arabic calligraphy ink",
            "oud player close up",
            "spice market bazaar",
            "mosque dome golden",
            "belly dancer silhouette",
            "whirling dervish spin",
            "medina alley morocco",
            "tea ceremony middle east",
            "henna hands intricate",
        ],
        descricao="Arquitetura árabe, deserto, lanternas, mercados, dervixes",
        ignora_letra=True,
        prioridade_videos=0.6,
    ),

    # ── Meditação / Natureza ──────────────────────────────────
    TemaMusical(
        id="meditacao",
        nome="Meditação e Natureza",
        palavras_chave=[
            "meditacao", "meditação", "meditation",
            "yoga", "yogi", "asana", "pranayama",
            "mindfulness", "atenção plena", "atencao plena",
            "natureza", "nature", "natural",
            "floresta", "forest", "mata", "jungle",
            "montanha", "mountain", "montanhas",
            "oceano", "ocean", "mar", "sea",
            "rio", "river", "cachoeira", "waterfall",
            "aurora", "aurora boreal", "northern lights",
            "amanhecer", "sunrise", "por do sol", "sunset",
            "chuva", "rain", "neve", "snow",
        ],
        termos_busca=[
            "person meditating sunrise",
            "yoga pose nature",
            "forest mist morning",
            "waterfall tropical",
            "ocean waves aerial",
            "mountain peak clouds",
            "northern lights iceland",
            "bamboo forest path",
            "lotus pond reflection",
            "desert sand dunes",
            "rain window cozy",
            "snow falling forest",
        ],
        descricao="Pessoas meditando, paisagens naturais, elementos",
        prioridade_videos=0.7,
    ),

    # ─- Eletrônica / Synth / Lo-fi ────────────────────────────
    TemaMusical(
        id="eletronica",
        nome="Eletrônica / Synthwave / Lo-fi",
        palavras_chave=[
            "eletronica", "eletrônica", "electronic",
            "edm", "techno", "house", "trance",
            "synth", "synthwave", "retrowave",
            "lofi", "lo-fi", "low fi", "lo fi beats", "beats",
            "chillwave", "vaporwave",
            "dj", "rave", "festival", "party",
            "neon", "cyberpunk", "futuristic",
            "dubstep", "drum and bass", "dnb",
        ],
        termos_busca=[
            "neon city night",
            "synthwave sunset car",
            "dj controller hands",
            "festival crowd lights",
            "cyberpunk city rain",
            "retro computer screen",
            "lofi room anime",
            "laser show concert",
            "equalizer bars glow",
            "turntable vinyl spin",
            "nightclub lights smoke",
            "futuristic corridor",
        ],
        descricao="Neon, cidade noturna, festivais, retro-futurismo",
        prioridade_videos=0.8,
    ),

    # ─- Jazz / Blues / Bossa ──────────────────────────────────
    TemaMusical(
        id="jazz",
        nome="Jazz / Blues / Bossa Nova",
        palavras_chave=[
            "jazz", "blues", "bossa", "bossa nova",
            "samba", "mpb", "musica popular brasileira",
            "saxofone", "saxophone", "sax",
            "piano jazz", "jazz piano",
            "contrabaixo", "double bass",
            "trompete", "trumpet",
            "new orleans", "nova orleans",
            "club", "jazz club", "speakeasy",
            "improvisacao", "improvisação", "jam session",
        ],
        termos_busca=[
            "jazz club saxophone",
            "saxophone player moody",
            "piano jazz hands",
            "double bass player",
            "trumpet player stage",
            "new orleans street band",
            "vinyl record spinning",
            "smoky jazz bar",
            "drum brushes close up",
            "brass section stage",
            "acoustic guitar bossa",
            "rio de janeiro beach",
        ],
        descricao="Clubes de jazz, instrumentos de sopro, vinil, Bossa",
        prioridade_videos=0.6,
    ),

    # ─- Rock / Metal / Punk ───────────────────────────────────
    TemaMusical(
        id="rock",
        nome="Rock / Metal / Punk",
        palavras_chave=[
            "rock", "metal", "punk", "hard rock",
            "heavy metal", "death metal", "black metal",
            "grunge", "indie rock", "alternative",
            "guitarra eletrica", "electric guitar",
            "bateria", "drums", "drum solo",
            "palco", "stage", "show", "concert",
            "headbanging", "moshpit", "crowd surfing",
            "rock pesado", "rock and roll",
        ],
        termos_busca=[
            "rock concert crowd",
            "electric guitar solo",
            "drummer stage lights",
            "moshpit crowd energy",
            "stage lights concert",
            "band performing live",
            "guitar strings close",
            "crowd hands raised",
            "smoke stage lights",
            "microphone singer",
            "drum kit close up",
            "concert pyrotechnics",
        ],
        descricao="Shows ao vivo, guitarras, bateria, energia da multidão",
        prioridade_videos=0.8,
    ),

    # ─- Hip-hop / Rap / Trap ──────────────────────────────────
    TemaMusical(
        id="hiphop",
        nome="Hip-hop / Rap / Trap",
        palavras_chave=[
            "hip hop", "hiphop", "rap", "trap",
            "mc", "rapper", "freestyle", "battle",
            "graffiti", "street", "urban",
            "beat", "beats", "producer",
            "skate", "basketball", "street basketball",
        ],
        termos_busca=[
            "rapper microphone studio",
            "graffiti wall urban",
            "street basketball sunset",
            "skateboard trick slow",
            "producer studio equipment",
            "city night skyline",
            "breakdance spin freeze",
            "turntable dj hands",
            "urban alley graffiti",
            "car lowrider night",
            "studio recording booth",
            "street fashion walk",
        ],
        descricao="Rapper, graffiti, rua, skate, estúdio, carros",
        prioridade_videos=0.7,
    ),

    # ─- Country / Folk / Acústico ─────────────────────────────
    TemaMusical(
        id="country",
        nome="Country / Folk / Acústico",
        palavras_chave=[
            "country", "folk", "acustico", "acústico", "acoustic",
            "violao", "violão", "fingerstyle",
            "campfire", "fogueira", "bonfire",
            "estrada", "road", "highway", "estrada deserta",
            "interior", "rural", "fazenda", "farm",
            "cowboy", "western", "sertanejo", "sertaneja",
        ],
        termos_busca=[
            "acoustic guitar sunset",
            "campfire night friends",
            "country road sunset",
            "farm landscape golden",
            "pickup truck road",
            "barn wooden interior",
            "western desert cowboy",
            "river bank guitar",
            "wheat field wind",
            "porch swing sunset",
            "horse running field",
            "dirt road horizon",
        ],
        descricao="Violão ao pôr do sol, estradas, fazendas, fogueiras",
        prioridade_videos=0.6,
    ),

    # ─- Infantil / Lullaby ────────────────────────────────────
    TemaMusical(
        id="infantil",
        nome="Música Infantil / Ninar",
        palavras_chave=[
            "infantil", "crianca", "criança", "kids", "children",
            "ninar", "berco", "berço", "lullaby", "nursery",
            "brinquedo", "toy", "teddy bear",
            "estrelas", "stars", "moon", "lua",
            "nuvem", "cloud", "balao", "balão", "balloon",
        ],
        termos_busca=[
            "baby sleeping peaceful",
            "teddy bear soft light",
            "mobile spinning crib",
            "stars night sky",
            "clouds fluffy animation",
            "hot air balloon sky",
            "mother baby cradle",
            "moon stars nursery",
            "paper boat water",
            "bubbles floating slow",
            "rainbow sky children",
            "toy blocks colorful",
        ],
        descricao="Bebês dormindo, ursinhos, móbiles, estrelas, balões",
        prioridade_videos=0.5,
    ),
]


# ════════════════════════════════════════════════════════════════
# API pública
# ════════════════════════════════════════════════════════════════

def detectar_tema(texto: str) -> Optional[TemaMusical]:
    """Detecta qual tema melhor casa com a descrição do usuário.

    Retorna o tema com mais palavras-chave encontradas, ou None se
    nenhuma palavra bater. Palavras muito curtas (< 4 letras) e
    stopwords comuns são ignoradas para evitar falsos positivos.

    IMPORTANTE: instrumentos isolados ("violão", "piano", "guitarra")
    NÃO disparam tema — eles já são tratados pelo módulo de instrumentos
    em `descricao_musical.py`. O tema só dispara quando há palavras
    FORTEMENTE associadas ao gênero ("mantra", "432hz", "árabe",
    "clássica", "lofi", etc.).
    """
    if not texto:
        return None

    norm = _normalizar(texto)
    palavras_texto = set(norm.split())

    # Stopwords que causam falsos positivos
    stopwords = {
        "para", "com", "sem", "por", "que", "como", "mais", "muito",
        "todo", "toda", "este", "esta", "esse", "essa", "aqui", "la",
        "ja", "ainda", "sempre", "nunca", "sim", "nao", "ou", "mas",
        "num", "numa", "pro", "pra", "pros", "pras", "e", "de", "da",
        "do", "dos", "das", "em", "no", "na", "nos", "nas", "um", "uma",
    }
    palavras_texto -= stopwords

    melhor: Optional[TemaMusical] = None
    melhor_score = 0

    for tema in TEMAS:
        score = 0
        for chave in tema.palavras_chave:
            chave_norm = _normalizar(chave)
            if len(chave_norm) < 3:
                continue
            # Palavra inteira no texto (mais confiável)
            if chave_norm in palavras_texto:
                # Palavras curtas (3-4 letras) são mais genéricas e
                # podem ser instrumentos — pontuam menos
                if len(chave_norm) <= 4:
                    score += 1
                else:
                    score += 2
            # Substring só conta para palavras longas (>= 6)
            elif len(chave_norm) >= 6 and chave_norm in norm:
                score += 1

        if score > melhor_score:
            melhor_score = score
            melhor = tema

    # Threshold: score >= 3 para temas que ignoram letra (mantra,
    # frequencia, arabe) — precisam de evidencia forte. Score >= 2
    # para temas que combinam com letra (classica, jazz, rock, etc.)
    # — uma palavra longa (2 pts) ou duas curtas (1+1) bastam.
    if melhor is None:
        return None
    minimo = 3 if melhor.ignora_letra else 2
    return melhor if melhor_score >= minimo else None


def termos_do_tema(tema: TemaMusical, maximo: int = 8) -> list[str]:
    """Devolve os termos de busca do tema, limitados."""
    return tema.termos_busca[:maximo]


def info_tema(tema: TemaMusical) -> str:
    """Resumo legível para o log."""
    return f"{tema.nome}: {tema.descricao} ({len(tema.termos_busca)} termos)"


def _normalizar(texto: str) -> str:
    import unicodedata
    import re
    t = unicodedata.normalize("NFD", (texto or "").lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    # Remove pontuação para matching limpo
    t = re.sub(r"[^\w\s]", " ", t)
    return t


def _auto_teste() -> None:  # pragma: no cover
    casos = [
        ("solo de piano clássico, triste", "classica"),
        ("mantra tibetano para meditação", "mantra"),
        ("frequência 432hz para prosperidade", "frequencia"),
        ("música árabe com oud e darbuka", "arabe"),
        ("lofi beats para estudar", "eletronica"),
        ("jazz club saxofone", "jazz"),
        ("rock pesado com guitarra", "rock"),
        ("ninar bebê com estrelas", "infantil"),
        ("musica completamente aleatoria xyz", None),
    ]

    for descricao, esperado_id in casos:
        tema = detectar_tema(descricao)
        achado = tema.id if tema else None
        status = "OK" if achado == esperado_id else "FALHA"
        print(f"  [{status}] '{descricao[:40]}' -> {achado}")
        if tema:
            print(f"       termos: {tema.termos_busca[:3]}")

    print("\nauto-teste: OK")


if __name__ == "__main__":
    _auto_teste()
