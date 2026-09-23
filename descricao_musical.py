"""
Interpretacao de uma descricao livre da musica.

O usuario descreve a musica como descreveria para uma pessoa:

    "tribal com tambores e violão clássico, meio melancólico"
    "música para relaxar e dormir"
    "solo de piano clássico, triste e lento"

Dessa frase o modulo extrai tres coisas:

  INSTRUMENTOS -> cenas concretas ("hands drumming on djembe")
  CLIMA        -> emocao (reusa o lexico de `interpretacao.py`)
  RITMO        -> quantas batidas por troca de imagem combina

A descricao NUNCA substitui a letra: ela entra combinada (`combinar`),
como o usuario pediu. Quando os dois apontam para emocoes opostas, o
modulo REGISTRA O CONFLITO em vez de escolher sozinho — quem decide e'
o usuario, na tela.

Nao depende de rede nem de LLM: e' um lexico local, deterministico e
testavel.
"""

from __future__ import annotations

from dataclasses import dataclass, field

try:
    from MusicClipStudio.interpretacao import Emocao, normalizar
except Exception:  # pragma: no cover
    from enum import Enum

    class Emocao(str, Enum):  # type: ignore
        TRISTEZA = "tristeza"
        SAUDADE = "saudade"
        SOLIDAO = "solidao"
        RAIVA = "raiva"
        MEDO = "medo"
        AMOR = "amor"
        PAZ = "paz"
        ALEGRIA = "alegria"
        EUFORIA = "euforia"
        ESPERANCA = "esperanca"
        TENSAO = "tensao"
        MELANCOLIA = "melancolia"

    def normalizar(texto: str) -> str:  # type: ignore
        import unicodedata
        t = unicodedata.normalize("NFD", (texto or "").lower())
        return "".join(c for c in t if unicodedata.category(c) != "Mn")


# ════════════════════════════════════════════════════════════════
# Lexico de instrumentos
# ════════════════════════════════════════════════════════════════

@dataclass
class Instrumento:
    chave: str
    cena: str
    ritmo: str          # sugestao de andamento
    familiar: str = ""  # como aparece no log
    grupo: str = ""     # agrupa variantes de escrita do mesmo instrumento


INSTRUMENTOS: list[Instrumento] = [
    # Percussao / tribal
    Instrumento("tambor", "hands drumming on djembe close up", "tribal", "tambor", "percussao"),
    Instrumento("percussao", "percussion instruments in warm light", "tribal", "percussão", "percussao"),
    Instrumento("percussão", "percussion instruments in warm light", "tribal", "percussão", "percussao"),
    Instrumento("atabaque", "hands striking tall drum", "tribal", "atabaque", "percussao"),
    Instrumento("congas", "conga player hands close up", "tribal", "congas", "percussao"),
    Instrumento("bateria", "drum kit being played energetically", "rock", "bateria", "percussao"),

    # Cordas
    Instrumento("violao", "acoustic guitar strings fingerpicking", "acustico", "violão", "violao"),
    Instrumento("violão", "acoustic guitar strings fingerpicking", "acustico", "violão", "violao"),
    Instrumento("guitarra", "electric guitar player on stage", "rock", "guitarra", "guitarra"),
    Instrumento("baixo", "bass guitar groove close up", "groove", "baixo", "baixo"),
    Instrumento("violino", "violinist performing in concert hall", "classico", "violino", "violino"),
    Instrumento("cello", "cellist playing in dim room", "classico", "cello", "cello"),
    Instrumento("violoncelo", "cellist playing in dim room", "classico", "violoncelo", "cello"),
    Instrumento("harpa", "harp strings in soft light", "lento", "harpa", "harpa"),

    # Teclas
    Instrumento("piano", "piano keys being played softly", "lento", "piano", "piano"),
    Instrumento("teclado", "keyboard player in studio", "eletronico", "teclado", "teclado"),
    Instrumento("orgao", "church organ pipes", "classico", "órgão", "orgao"),
    Instrumento("sintetizador", "synthesizer knobs glowing in dark studio", "eletronico", "sintetizador", "synth"),
    Instrumento("synth", "synthesizer knobs glowing in dark studio", "eletronico", "synth", "synth"),

    # Sopro
    Instrumento("flauta", "flute player in forest light", "suave", "flauta", "flauta"),
    Instrumento("sax", "saxophone player in jazz club", "groove", "sax", "sax"),
    Instrumento("trompete", "trumpet player under stage light", "groove", "trompete", "trompete"),

    # Conjuntos
    Instrumento("orquestra", "orchestra performing wide shot", "classico", "orquestra", "orquestra"),
    Instrumento("coral", "choir singing together", "classico", "coral", "coral"),
    Instrumento("banda", "band performing on stage", "rock", "banda", "banda"),
]


# ════════════════════════════════════════════════════════════════
# Lexico de clima
# ════════════════════════════════════════════════════════════════

# (termo, emocao, ritmo sugerido)
CLIMAS: list[tuple[str, Emocao, str]] = [
    # Calmaria
    ("relaxar", Emocao.PAZ, "muito_lento"),
    ("relaxante", Emocao.PAZ, "muito_lento"),
    ("relax", Emocao.PAZ, "muito_lento"),
    ("dormir", Emocao.PAZ, "muito_lento"),
    ("sono", Emocao.PAZ, "muito_lento"),
    ("meditacao", Emocao.PAZ, "muito_lento"),
    ("meditação", Emocao.PAZ, "muito_lento"),
    ("calmo", Emocao.PAZ, "lento"),
    ("calma", Emocao.PAZ, "lento"),
    ("tranquil", Emocao.PAZ, "lento"),
    ("suave", Emocao.PAZ, "lento"),
    ("ambiente", Emocao.PAZ, "muito_lento"),
    ("chill", Emocao.PAZ, "lento"),

    # Tristeza
    ("melancol", Emocao.MELANCOLIA, "medio"),
    ("triste", Emocao.TRISTEZA, "lento"),
    ("tristeza", Emocao.TRISTEZA, "lento"),
    ("saudade", Emocao.SAUDADE, "lento"),
    ("saudade", Emocao.SAUDADE, "lento"),
    ("sozinho", Emocao.SOLIDAO, "lento"),
    ("solidao", Emocao.SOLIDAO, "lento"),
    ("solitario", Emocao.SOLIDAO, "lento"),
    ("melancolico", Emocao.MELANCOLIA, "medio"),

    # Alegria
    ("alegre", Emocao.ALEGRIA, "rapido"),
    ("feliz", Emocao.ALEGRIA, "rapido"),
    ("animad", Emocao.EUFORIA, "rapido"),
    ("animado", Emocao.EUFORIA, "rapido"),
    ("dancante", Emocao.EUFORIA, "rapido"),
    ("dançante", Emocao.EUFORIA, "rapido"),
    ("dance", Emocao.EUFORIA, "rapido"),
    ("balada", Emocao.EUFORIA, "rapido"),
    ("festa", Emocao.EUFORIA, "rapido"),
    ("euforia", Emocao.EUFORIA, "rapido"),
    ("empolgante", Emocao.EUFORIA, "rapido"),

    # Agressividade
    ("pesado", Emocao.RAIVA, "rapido"),
    ("pesada", Emocao.RAIVA, "rapido"),
    ("agressiv", Emocao.RAIVA, "rapido"),
    ("raiva", Emocao.RAIVA, "rapido"),
    ("metal", Emocao.RAIVA, "rapido"),
    ("punk", Emocao.RAIVA, "rapido"),
    ("intenso", Emocao.RAIVA, "rapido"),

    # Tensao
    ("tenso", Emocao.TENSAO, "medio"),
    ("tensao", Emocao.TENSAO, "medio"),
    ("suspense", Emocao.TENSAO, "medio"),
    ("misterio", Emocao.TENSAO, "medio"),
    ("misterioso", Emocao.TENSAO, "medio"),
    ("sombrio", Emocao.MEDO, "medio"),

    # Epico / esperanca
    ("epico", Emocao.ESPERANCA, "medio"),
    ("épico", Emocao.ESPERANCA, "medio"),
    ("epica", Emocao.ESPERANCA, "medio"),
    ("grandioso", Emocao.ESPERANCA, "medio"),
    ("inspirador", Emocao.ESPERANCA, "medio"),
    ("superacao", Emocao.ESPERANCA, "medio"),
    ("esperanc", Emocao.ESPERANCA, "medio"),

    # Amor
    ("romant", Emocao.AMOR, "lento"),
    ("amor", Emocao.AMOR, "lento"),
    ("apaixonad", Emocao.AMOR, "lento"),
    ("carinho", Emocao.AMOR, "lento"),

    # Ritmo explicito
    ("tribal", Emocao.EUFORIA, "tribal"),
    ("ritmado", Emocao.EUFORIA, "tribal"),
    ("groove", Emocao.EUFORIA, "groove"),
    ("classica", Emocao.MELANCOLIA, "classico"),
    ("clássica", Emocao.MELANCOLIA, "classico"),
]


# Quantas batidas por troca cada padrao de ritmo sugere
BATIDAS_POR_RITMO: dict[str, int] = {
    "muito_lento": 16,
    "lento": 12,
    "medio": 8,
    "acustico": 8,
    "suave": 12,
    "classico": 10,
    "groove": 6,
    "tribal": 4,
    "rock": 4,
    "rapido": 4,
    "eletronico": 4,
}


# Emocoes que nao combinam entre si: se a letra diz uma e a descricao
# diz a oposta, avisamos em vez de escolher.
_OPOSTAS = {
    Emocao.TRISTEZA: {Emocao.ALEGRIA, Emocao.EUFORIA},
    Emocao.MELANCOLIA: {Emocao.ALEGRIA, Emocao.EUFORIA},
    Emocao.SOLIDAO: {Emocao.EUFORIA, Emocao.ALEGRIA},
    Emocao.SAUDADE: {Emocao.EUFORIA},
    Emocao.RAIVA: {Emocao.PAZ, Emocao.AMOR},
    Emocao.EUFORIA: {Emocao.TRISTEZA, Emocao.MELANCOLIA, Emocao.SOLIDAO},
    Emocao.ALEGRIA: {Emocao.TRISTEZA, Emocao.MELANCOLIA, Emocao.SOLIDAO},
    Emocao.PAZ: {Emocao.RAIVA, Emocao.TENSAO},
    Emocao.AMOR: {Emocao.RAIVA},
}


@dataclass
class LeituraDescricao:
    """O que o modulo entendeu da descricao do usuario."""

    texto_original: str = ""
    instrumentos: list[Instrumento] = field(default_factory=list)
    climas: list[Emocao] = field(default_factory=list)
    ritmo: str = ""
    batidas_por_troca: int = 0
    cenas: list[str] = field(default_factory=list)
    conflitos: list[str] = field(default_factory=list)

    # Tema musical detectado (classica, mantra, frequencia, arabe, etc.)
    tema_id: str = ""
    tema_nome: str = ""
    tema_termos: list[str] = field(default_factory=list)
    tema_ignora_letra: bool = False
    tema_prioridade_videos: float = 0.5

    @property
    def vazia(self) -> bool:
        return (
            not self.instrumentos
            and not self.climas
            and not self.tema_id
        )

    @property
    def emocao_principal(self) -> Emocao | None:
        return self.climas[0] if self.climas else None

    def resumo(self) -> str:
        if self.vazia:
            return "descrição não informada"

        partes = []
        if self.tema_nome:
            partes.append(self.tema_nome)
        if self.instrumentos:
            nomes = ", ".join(i.familiar or i.chave for i in self.instrumentos[:4])
            partes.append(nomes)
        if self.climas:
            partes.append("/".join(c.value for c in self.climas[:3]))
        if self.ritmo:
            partes.append(f"ritmo {self.ritmo}")
        return " · ".join(partes)

    def peso(self) -> float:
        """Quanto a descricao deve pesar na busca (0..0.6).

        Descricao mais especifica (instrumentos + clima) pesa mais.
        Teto de 0.6 para a letra nunca ser ignorada — o usuario pediu
        para combinar, nao para a descricao mandar sozinha.
        """
        peso = len(self.instrumentos) * 0.15 + len(self.climas) * 0.20
        return min(peso, 0.6)


def interpretar_descricao(texto: str) -> LeituraDescricao:
    """Le a descricao livre do usuario.

    Devolve sempre um objeto; descricao vazia ou irreconhecivel da um
    resultado `vazia=True` (o resto do pipeline segue so com a letra).
    """
    leitura = LeituraDescricao(texto_original=texto or "")

    if not texto or not texto.strip():
        return leitura

    norm = normalizar(texto)

    # ── Instrumentos ───────────────────────────────────────────
    # Deduplica por GRUPO, nao por chave: "violão" e "violao" sao o
    # mesmo instrumento escrito de duas formas e nao devem contar 2x.
    grupos_vistos = set()
    for instr in INSTRUMENTOS:
        chave = normalizar(instr.chave)
        grupo = instr.grupo or instr.chave
        if chave and chave in norm and grupo not in grupos_vistos:
            grupos_vistos.add(grupo)
            leitura.instrumentos.append(instr)

    # ── Clima ──────────────────────────────────────────────────
    for termo, emocao, ritmo in CLIMAS:
        if normalizar(termo) in norm:
            if emocao not in leitura.climas:
                leitura.climas.append(emocao)
            if not leitura.ritmo:
                leitura.ritmo = ritmo

    # O ritmo do INSTRUMENTO tem prioridade sobre o do clima.
    # "tribal com tambores, meio melancólico" e' tribal: o tambor
    # define o andamento; "melancólico" tinge a emoção, não o ritmo.
    if leitura.instrumentos:
        ritmo_instr = leitura.instrumentos[0].ritmo
        if ritmo_instr:
            leitura.ritmo = ritmo_instr

    leitura.batidas_por_troca = BATIDAS_POR_RITMO.get(leitura.ritmo, 8)

    # ── Tema musical ───────────────────────────────────────────
    # Quando o usuario diz "mantra tibetano" ou "432hz", nao estamos
    # falando de instrumento/clima — e' um TEMA que muda completamente
    # os termos de busca. Detectamos aqui e guardamos.
    try:
        from MusicClipStudio.temas_musicais import detectar_tema, termos_do_tema

        tema = detectar_tema(texto)
        if tema is not None:
            leitura.tema_id = tema.id
            leitura.tema_nome = tema.nome
            leitura.tema_termos = termos_do_tema(tema, maximo=10)
            leitura.tema_ignora_letra = tema.ignora_letra
            leitura.tema_prioridade_videos = tema.prioridade_videos
    except Exception:
        pass  # tema indisponivel = segue sem tema

    # ── Cenas ──────────────────────────────────────────────────
    for instr in leitura.instrumentos[:3]:
        if instr.cena not in leitura.cenas:
            leitura.cenas.append(instr.cena)

    for emocao in leitura.climas[:2]:
        for cena in _cenas_da_emocao(emocao):
            if cena not in leitura.cenas:
                leitura.cenas.append(cena)
            if len(leitura.cenas) >= 6:
                break

    return leitura


def _cenas_da_emocao(emocao: Emocao) -> list[str]:
    """Busca as cenas da emocao no dicionario de `interpretacao`."""
    try:
        from MusicClipStudio.interpretacao import CENAS
        return list(CENAS.get(emocao, []))
    except Exception:
        return []


def detectar_conflito(emocao_letra: Emocao | None,
                      leitura: LeituraDescricao) -> list[str]:
    """Avisa quando letra e descricao apontam para lados opostos.

    Nao resolve o conflito: devolve as mensagens para a tela, porque
    a decisao e' do usuario.
    """
    conflitos: list[str] = []

    if emocao_letra is None or leitura is None or leitura.vazia:
        return conflitos

    desc = leitura.emocao_principal
    if desc is None:
        return conflitos

    incompativel = _OPOSTAS.get(desc, set())
    if emocao_letra in incompativel:
        conflitos.append(
            f"Conflito de clima: a letra está em {emocao_letra.value} "
            f"mas a descrição pede {desc.value}. "
            f"As duas serão combinadas — ajuste se o resultado não servir."
        )

    return conflitos


def combinar_cenas(
    cenas_letra: list[str],
    leitura: LeituraDescricao,
    maximo: int = 8,
) -> list[str]:
    """Mistura as cenas da letra com as da descricao.

    A letra vem primeiro (ela e' o que esta sendo cantado). As cenas da
    descricao entram intercaladas, na proporcao do peso — assim o clipe
    nao fica nem literal demais nem generico demais.
    """
    if not leitura or leitura.vazia or not leitura.cenas:
        return list(cenas_letra or [])[:maximo]

    if not cenas_letra:
        return list(leitura.cenas)[:maximo]

    # Quantas cenas da descricao entram (proporcional ao peso)
    n_desc = max(1, int(round(maximo * leitura.peso())))
    n_desc = min(n_desc, len(leitura.cenas), maximo - 1)

    resultado: list[str] = []
    i_letra = i_desc = 0

    # Intercala: 2 da letra, 1 da descricao — mantem a letra como eixo
    while len(resultado) < maximo:
        for _ in range(2):
            if i_letra < len(cenas_letra) and len(resultado) < maximo:
                if cenas_letra[i_letra] not in resultado:
                    resultado.append(cenas_letra[i_letra])
                i_letra += 1
        if i_desc < n_desc and len(resultado) < maximo:
            if leitura.cenas[i_desc] not in resultado:
                resultado.append(leitura.cenas[i_desc])
            i_desc += 1
        elif i_letra >= len(cenas_letra) and i_desc >= n_desc:
            break

    return resultado[:maximo]


# ════════════════════════════════════════════════════════════════
# Ponte com a busca de estoque
# ════════════════════════════════════════════════════════════════

# Cena em portugues -> termo que o banco de imagens entende.
# O banco tem lexico proprio (em portugues); a descricao livre do
# usuario precisa virar termo de busca. Sem isto a descricao entra
# so como ruido no meio das queries da letra.
ALIAS_BUSCA: dict[str, str] = {
    # percussao / tribal
    "hands drumming on djembe close up": "tribal drums",
    "percussion instruments in warm light": "percussion instruments",
    "hands striking tall drum": "african drums",
    "conga player hands close up": "congas percussion",
    "drum kit being played energetically": "drum kit",
    # cordas
    "acoustic guitar strings fingerpicking": "acoustic guitar",
    "electric guitar player on stage": "electric guitar",
    "bass guitar groove close up": "bass guitar",
    "classical guitar warm tone": "classical guitar",
    "violin bow close up emotional": "violin",
    "cello strings deep resonant": "cello",
    "harp strings glissando": "harp",
    # teclas
    "piano keys close up slow motion": "piano keys",
    "grand piano in empty hall": "grand piano",
    "hands playing synthesizer": "synthesizer",
    "church organ pipes": "organ pipes",
    # sopro
    "flute player soft light": "flute",
    "saxophone player moody light": "saxophone",
    "trumpet player jazz club": "trumpet",
    # conjuntos
    "full orchestra playing": "orchestra concert",
    "choir singing in warm light": "choir singing",
    "band playing on stage": "live band stage",
}


def cena_para_busca(cena: str) -> str:
    """Traduz uma cena interna para um termo de busca utilizavel."""
    if not cena:
        return ""
    return ALIAS_BUSCA.get(cena, cena)


def termos_de_busca(
    cenas_letra: list[str],
    leitura: LeituraDescricao | None,
    maximo: int = 8,
) -> list[str]:
    """Junta cenas da letra + descricao num unico conjunto de termos.

    REGRA DO TEMA: se a descricao detectou um tema musical (mantra,
    frequencia, classica, arabe...), os termos do tema SAO a busca.
    A letra NAO entra (porque e' em sanscrito, arabe, ou nao existe).

    Sem tema: a letra vem primeiro (e' o que esta sendo cantado). As
    cenas da descricao entram intercaladas na proporcao do peso.
    """
    if not leitura or leitura.vazia:
        return [c for c in (cenas_letra or []) if c][:maximo]

    # ── TEMA detectado: a descricao manda sozinha ─────────────
    if leitura.tema_id and leitura.tema_termos:
        return leitura.tema_termos[:maximo]

    # ── Sem tema: combinacao letra + descricao (como antes) ────
    combinadas = combinar_cenas(cenas_letra or [], leitura, maximo=maximo)

    termos: list[str] = []
    for cena in combinadas:
        termo = cena_para_busca(cena)
        if termo and termo not in termos:
            termos.append(termo)

    return termos[:maximo]


def _auto_teste() -> None:
    print("== descricao tribal ==")
    d = interpretar_descricao(
        "tribal com tambores e violão clássico, meio melancólico"
    )
    print(" ", d.resumo())
    print("  instrumentos:", [i.chave for i in d.instrumentos])
    print("  climas:", [c.value for c in d.climas])
    print("  ritmo:", d.ritmo, "| batidas/troca:", d.batidas_por_troca)
    print("  peso:", round(d.peso(), 2))
    print("  cenas:", d.cenas[:4])

    print("\n== descricao para relaxar ==")
    r = interpretar_descricao("música para relaxar e dormir")
    print(" ", r.resumo())
    print("  batidas/troca:", r.batidas_por_troca)

    print("\n== descricao vazia ==")
    v = interpretar_descricao("")
    print("  vazia?", v.vazia, "| resumo:", v.resumo())

    print("\n== descricao irreconhecivel ==")
    x = interpretar_descricao("xyz abc 123")
    print("  vazia?", x.vazia)

    print("\n== conflito letra vs descricao ==")
    conf = detectar_conflito(Emocao.TRISTEZA, interpretar_descricao("festa animada"))
    print(" ", conf or "nenhum")

    print("\n== combinacao de cenas ==")
    letra = ["person crying alone in dark room",
             "tears streaming down face close up"]
    cenas = combinar_cenas(letra, d, maximo=6)
    print(" ", cenas)

    print("\n== termos de busca combinados ==")
    letra_cenas = ["person crying alone in dark room",
                   "tears streaming down face close up"]
    termos = termos_de_busca(letra_cenas, d, maximo=6)
    for t in termos:
        print("  -", t)
    so_letra = termos_de_busca(letra_cenas, interpretar_descricao(""), maximo=6)
    print("  sem descricao:", so_letra)
    so_desc = termos_de_busca([], d, maximo=4)
    print("  sem letra:   ", so_desc)

    print("\nauto-teste: OK")


if __name__ == "__main__":
    _auto_teste()
