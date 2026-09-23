"""
Calculo de quantas midias o clipe precisa.

Este modulo responde a pergunta que o gerador antigo nao fazia: em vez de
dividir a duracao total pelo numero de midias que o usuario escolheu, ele
DERIVA os clipes da propria musica.

Dois modos de derivar os clipes:

  FRASES  — usa as frases da letra (com os tempos do Whisper). Cada clipe
            cobre uma frase, entao o corte cai no silencio depois da
            palavra, nunca no meio dela.

  BATIDA  — usa a grade de batidas do audio (librosa). Para quando nao ha
            letra, ou quando o usuario escolheu cortar no ritmo.

O modulo so CALCULA: ele devolve um plano. Quem baixa midia e renderiza
video e' o gerador. Isso deixa o calculo testavel sem tocar em rede nem
em ffmpeg.

Decisoes do usuario embutidas aqui:
  - frases longas: so fatia se passar do maximo com folga (tolerancia)
  - reciclagem: embaralha cada volta, com semente fixa (reproduzivel)
  - efeito: pela natureza da midia (imagem = movimento, video = direto)
  - alternancia: video nos trechos de energia alta, imagem nos calmos
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from MusicClipStudio.analise_audio import AnaliseAudio, grid_de_batidas


# ════════════════════════════════════════════════════════════════
# Configuracao
# ════════════════════════════════════════════════════════════════

@dataclass
class ConfigRitmo:
    """Como o clipe deve ser ritmado."""

    modo: str = "frases"          # "frases" | "batida" | "fixo"
    max_por_clipe: float = 6.0    # frase maior que isso e' fatiada
    tolerancia: float = 0.20      # folga antes de fatiar (20%)
    batidas_por_troca: int = 8    # no modo "batida"
    segundos_por_clipe: float = 5.0  # no modo "fixo"
    minimo_por_clipe: float = 1.2    # evita clipe que pisca
    semente: int = 42             # reprodutibilidade do embaralhamento

    def validar(self) -> "ConfigRitmo":
        """Corrige valores impossiveis em vez de deixar quebrar depois."""
        self.max_por_clipe = max(1.0, float(self.max_por_clipe))
        self.tolerancia = min(max(0.0, float(self.tolerancia)), 1.0)
        self.batidas_por_troca = max(1, int(self.batidas_por_troca))
        self.segundos_por_clipe = max(1.0, float(self.segundos_por_clipe))
        self.minimo_por_clipe = max(0.3, float(self.minimo_por_clipe))
        if self.modo not in ("frases", "batida", "fixo"):
            self.modo = "frases"
        return self


# ════════════════════════════════════════════════════════════════
# Estruturas do plano
# ════════════════════════════════════════════════════════════════

@dataclass
class Slot:
    """Um clipe na linha do tempo: quando entra, quando sai, o que mostra."""

    indice: int
    inicio: float
    fim: float
    texto: str = ""
    parte: int = 1
    partes: int = 1
    origem: str = ""            # "frase" | "batida" | "fixo"
    energia: float = 0.5

    @property
    def duracao(self) -> float:
        return max(0.0, self.fim - self.inicio)

    def __repr__(self) -> str:
        texto = f" {self.texto[:28]!r}" if self.texto else ""
        return (f"Slot({self.indice}, {self.inicio:.2f}-{self.fim:.2f}, "
                f"{self.duracao:.2f}s{texto})")


@dataclass
class PlanoClipe:
    """O resultado: slots prontos e o diagnostico do calculo."""

    slots: list[Slot] = field(default_factory=list)
    modo_usado: str = ""
    duracao_musica: float = 0.0
    bpm: float = 0.0
    midias_disponiveis: int = 0
    midias_faltando: int = 0
    reciclagens: int = 0
    avisos: list[str] = field(default_factory=list)

    @property
    def n_slots(self) -> int:
        return len(self.slots)

    @property
    def duracao_coberta(self) -> float:
        return sum(s.duracao for s in self.slots)

    @property
    def duracao_media(self) -> float:
        return self.duracao_coberta / self.n_slots if self.slots else 0.0

    @property
    def precisa_reciclar(self) -> bool:
        return self.midias_faltando > 0

    def resumo(self) -> str:
        """Linha curta para exibir na interface."""
        if not self.slots:
            return "nenhum clipe calculado"

        partes = [
            f"{self.n_slots} clipe(s)",
            f"~{self.duracao_media:.1f}s cada",
            f"cobre {self.duracao_coberta:.0f}s",
        ]
        if self.bpm > 0:
            partes.insert(0, f"{self.bpm:.0f} BPM")
        if self.midias_faltando:
            partes.append(
                f"faltam {self.midias_faltando} mídia(s) — "
                f"{self.reciclagens} reciclagem(ns)"
            )
        return " · ".join(partes)

    def explicar(self) -> list[str]:
        """Linhas para o log, explicando como o plano foi montado."""
        linhas = [
            f"[PLANO] Modo: {self.modo_usado}",
            f"[PLANO] Música: {self.duracao_musica:.1f}s"
            + (f" · {self.bpm:.0f} BPM" if self.bpm > 0 else ""),
            f"[PLANO] Clipes: {self.n_slots} "
            f"(média {self.duracao_media:.1f}s)",
            f"[PLANO] Mídias disponíveis: {self.midias_disponiveis}",
        ]
        if self.midias_faltando:
            linhas.append(
                f"[PLANO] Faltam {self.midias_faltando} mídia(s); "
                f"serão recicladas em {self.reciclagens} volta(s)"
            )
        for aviso in self.avisos:
            linhas.append(f"[PLANO] AVISO: {aviso}")
        return linhas


# ════════════════════════════════════════════════════════════════
# Derivacao dos slots
# ════════════════════════════════════════════════════════════════

def _fatiar_segmento(inicio: float, fim: float, texto: str, cfg: ConfigRitmo,
                     origem: str, energia: float,
                     contador: list) -> list[Slot]:
    """Converte um trecho de tempo em 1+ slots, respeitando o maximo.

    A tolerancia evita fatiar por pouco: uma frase de 6.3s com maximo
    6.0s fica inteira, porque cortar por 0.3s so faria a imagem piscar.
    """
    duracao = fim - inicio
    if duracao <= 0:
        return []

    limite = cfg.max_por_clipe * (1.0 + cfg.tolerancia)

    if duracao <= limite:
        n_partes = 1
    else:
        n_partes = int(math.ceil(duracao / cfg.max_por_clipe))

    # Nao criar partes menores que o minimo: prefere menos partes
    while n_partes > 1 and (duracao / n_partes) < cfg.minimo_por_clipe:
        n_partes -= 1

    passo = duracao / n_partes
    slots = []
    for i in range(n_partes):
        ini = inicio + i * passo
        f = inicio + (i + 1) * passo if i < n_partes - 1 else fim
        contador[0] += 1
        slots.append(Slot(
            indice=contador[0],
            inicio=ini,
            fim=f,
            texto=texto,
            parte=i + 1,
            partes=n_partes,
            origem=origem,
            energia=energia,
        ))
    return slots


def slots_de_frases(segmentos, cfg: ConfigRitmo,
                    analise: Optional[AnaliseAudio] = None) -> list[Slot]:
    """Uma frase da letra -> um ou mais clipes.

    `segmentos` e' a lista de SegmentoLegenda vinda da transcricao (que
    ja traz inicio/fim). Sem analise de audio, a energia fica neutra.
    """
    contador = [0]
    slots: list[Slot] = []

    for seg in segmentos or []:
        texto = (getattr(seg, "texto", "") or "").strip()
        inicio = float(getattr(seg, "inicio", 0.0) or 0.0)
        fim = float(getattr(seg, "fim", 0.0) or 0.0)

        energia = 0.5
        if analise is not None:
            energia = analise.energia_em((inicio + fim) / 2.0)

        slots.extend(_fatiar_segmento(
            inicio, fim, texto, cfg, "frase", energia, contador
        ))

    return slots


def slots_de_batida(analise: AnaliseAudio, cfg: ConfigRitmo,
                    duracao: float) -> list[Slot]:
    """Corta no ritmo da musica, usando a grade de batidas.

    Cada trecho entre batidas vira um clipe, com a energia medida no
    meio dele — e' o que permite depois decidir imagem vs video.
    """
    grade = grid_de_batidas(analise, duracao, cfg.batidas_por_troca)
    contador = [0]
    slots: list[Slot] = []

    for a, b in zip(grade, grade[1:]):
        if (b - a) < cfg.minimo_por_clipe:
            continue
        meio = (a + b) / 2.0
        contador[0] += 1
        slots.append(Slot(
            indice=contador[0],
            inicio=a,
            fim=b,
            texto="",
            origem="batida",
            energia=analise.energia_em(meio) if analise else 0.5,
        ))

    return slots


def slots_uniformes(duracao: float, cfg: ConfigRitmo,
                    analise: Optional[AnaliseAudio] = None) -> list[Slot]:
    """Fallback: divide a duracao em partes iguais.

    Usado quando nao ha nem letra nem batida detectavel. E' o
    comportamento antigo, mas agora explicito e avisado.
    """
    return _grade_uniforme(0.0, duracao, cfg, analise, origem="fixo")


def _grade_uniforme(inicio: float, duracao: float, cfg: ConfigRitmo,
                    analise: Optional[AnaliseAudio] = None,
                    origem: str = "fixo") -> list[Slot]:
    """Grade uniforme de `inicio` ate `duracao`, sem buraco no comeco.

    `slots_uniformes` comeca sempre em 0 (fallback puro). Esta versao
    aceita um inicio arbitrario, e' o que permite preencher a sobra
    COLADA no ultimo clipe de letra — se a grade comecasse em 0, o
    primeiro slot aproveitavel cairia depois do fim da letra e abriria
    um buraco (ex: letra ate 19s, grade em passos de 5 -> pulava de
    19.0 para 20.0 e 1s da musica ficava sem imagem).
    """
    if duracao <= 0 or inicio >= duracao:
        return []

    passo = cfg.segundos_por_clipe
    slots: list[Slot] = []

    t = float(inicio)
    while t < duracao:
        fim = min(t + passo, duracao)
        if (fim - t) < cfg.minimo_por_clipe and slots:
            slots[-1].fim = duracao
            break
        slots.append(Slot(
            indice=len(slots) + 1,
            inicio=t,
            fim=fim,
            texto="",
            origem=origem,
            energia=analise.energia_em((t + fim) / 2.0) if analise else 0.5,
        ))
        t = fim

    return slots


# ════════════════════════════════════════════════════════════════
# Casamento midia <-> slot
# ════════════════════════════════════════════════════════════════

def _tipo_da_midia(midia: Any) -> str:
    """'video' ou 'imagem', aceitando objetos e dicts."""
    if isinstance(midia, dict):
        tipo = midia.get("media_type") or midia.get("type") or "image"
    else:
        tipo = getattr(midia, "media_type", None) or "image"
    tipo = str(tipo).lower()
    return "video" if "video" in tipo else "imagem"


def dividir_midias(midias: list) -> tuple[list, list]:
    """Separa a lista em (videos, imagens), preservando a ordem."""
    videos, imagens = [], []
    for m in midias or []:
        if _tipo_da_midia(m) == "video":
            videos.append(m)
        else:
            imagens.append(m)
    return videos, imagens


def ordenar_por_energia(slots: list[Slot], videos: list, imagens: list,
                        semente: int = 42) -> list:
    """Distribui as midias pelos slots conforme a energia de cada um.

    Regra (decisao do usuario: "intensidade emocional"):
      - energia alta  -> prefere video (movimento combina com o clímax)
      - energia baixa -> prefere imagem (estatica combina com calmaria)

    Quando um dos lados acaba, o outro cobre — sem deixar slot vazio.
    """
    if not slots:
        return []

    rng = random.Random(semente)

    # Ordena cada pool de forma reproduzivel, intercalando variedade
    vids = list(videos)
    imgs = list(imagens)
    rng.shuffle(vids)
    rng.shuffle(imgs)

    iv = ii = 0
    escolhidas = []

    for slot in slots:
        quer_video = slot.energia >= 0.5

        if quer_video:
            if iv < len(vids):
                escolhidas.append(vids[iv]); iv += 1
                continue
            if ii < len(imgs):
                escolhidas.append(imgs[ii]); ii += 1
                continue
        else:
            if ii < len(imgs):
                escolhidas.append(imgs[ii]); ii += 1
                continue
            if iv < len(vids):
                escolhidas.append(vids[iv]); iv += 1
                continue

        # Ambos esgotaram: paramos; a reciclagem cuida do resto
        break

    return escolhidas


def reciclar_midias(midias_usadas: list, slots_restantes: int,
                    todas_videos: list, todas_imagens: list,
                    cfg: ConfigRitmo) -> tuple[list, int]:
    """Completa os slots que faltam, embaralhando cada volta.

    Devolve (midias_extras, n_voltas). A mesma semente garante que gerar
    o clipe duas vezes com os mesmos dados produza o mesmo resultado.
    """
    if slots_restantes <= 0:
        return [], 0

    pool = list(todas_videos) + list(todas_imagens)
    if not pool:
        return [], 0

    rng = random.Random(cfg.semente + 977)
    extras: list = []
    voltas = 0

    while len(extras) < slots_restantes:
        volta = list(pool)
        rng.shuffle(volta)
        extras.extend(volta)
        voltas += 1
        # Trava de seguranca: pool vazio ou slots absurdos nao podem
        # virar loop infinito.
        if voltas > 200:
            break

    return extras[:slots_restantes], voltas


# ════════════════════════════════════════════════════════════════
# Efeito por natureza da midia
# ════════════════════════════════════════════════════════════════

# Efeitos que funcionam bem em imagem parada (dão vida sem inventar movimento)
EFEITOS_IMAGEM = (
    "zoom_in", "zoom_out", "zoom_in_out", "pan_left", "pan_right",
    "zoom_diagonal", "dolly_zoom", "parallax",
)

# Efeitos para imagem em trecho calmo (movimento suave, sem agredir)
EFEITOS_IMAGEM_CALMO = (
    "zoom_in", "zoom_out", "pan_left", "pan_right", "fade_in", "fade_out",
)

# Efeito para imagem em trecho intenso (movimento perceptivel)
EFEITOS_IMAGEM_INTENSO = (
    "zoom_in", "dolly_zoom", "shake", "zoom_diagonal", "parallax",
)

# Video ja tem movimento proprio: aplicar zoom/pan nele costuma dar
# enjoo e some com o enquadramento original. "corte" = toca direto.
EFEITOS_VIDEO = ("corte",)


def escolher_efeito(slot: Slot, midia: Any, indice: int) -> str:
    """Efeito conforme a natureza da midia e a energia do trecho.

    Decisao do usuario: "pela natureza da mídia". Video toca direto;
    imagem recebe movimento escolhido pela energia do trecho, variando
    entre clipes para nao repetir o mesmo movimento.
    """
    tipo = _tipo_da_midia(midia)

    if tipo == "video":
        return EFEITOS_VIDEO[0]

    if slot.energia >= 0.65:
        lista = EFEITOS_IMAGEM_INTENSO
    elif slot.energia <= 0.35:
        lista = EFEITOS_IMAGEM_CALMO
    else:
        lista = EFEITOS_IMAGEM

    return lista[indice % len(lista)]


# ════════════════════════════════════════════════════════════════
# Ponto de entrada
# ════════════════════════════════════════════════════════════════

def calcular_plano(
    duracao: float,
    midias: list,
    config: Optional[ConfigRitmo] = None,
    segmentos=None,
    analise: Optional[AnaliseAudio] = None,
    callback_log: Optional[Callable] = None,
) -> PlanoClipe:
    """Calcula quantos clipes a musica precisa e como distribuir a midia.

    Ordem de preferencia para derivar os clipes:
      1. frases da letra (se houver segmentos e o modo permitir)
      2. grade de batidas (se o audio foi analisado)
      3. divisao uniforme (fallback, com aviso)

    Nunca levanta excecao por dados ruins: devolve um plano valido e
    registra o problema em `avisos`.
    """
    if callback_log is None:
        callback_log = lambda _m: None

    cfg = (config or ConfigRitmo()).validar()
    plano = PlanoClipe(
        duracao_musica=float(duracao or 0.0),
        bpm=float(getattr(analise, "bpm", 0.0) or 0.0),
        midias_disponiveis=len(midias or []),
    )

    if plano.duracao_musica <= 0:
        plano.avisos.append("duração da música desconhecida")
        callback_log("[PLANO] Sem duração: não há como calcular clipes")
        return plano

    # ── 1. Derivar os slots ────────────────────────────────────
    segmentos_validos = [
        s for s in (segmentos or [])
        if float(getattr(s, "fim", 0) or 0) > float(getattr(s, "inicio", 0) or 0)
    ]

    if cfg.modo == "frases" and segmentos_validos:
        plano.slots = slots_de_frases(segmentos_validos, cfg, analise)
        plano.modo_usado = "frases"

        # Segmentos podem nao cobrir a musica inteira (intro instrumental,
        # ou Whisper que perdeu o final). Nao deixar buraco preto.
        if plano.slots:
            fim_letra = plano.slots[-1].fim
            faltando = plano.duracao_musica - fim_letra
            if faltando > cfg.minimo_por_clipe:
                plano.avisos.append(
                    f"{faltando:.1f}s da música ficaram sem frase; "
                    f"cobrindo com clipes extras"
                )
                # Grade COLADA no fim da letra: comecar em 0 abriria um
                # buraco entre o ultimo clipe de letra e o primeiro extra.
                extra = _grade_uniforme(
                    fim_letra, plano.duracao_musica, cfg, analise,
                    origem="sobra",
                )
                base = len(plano.slots)
                for i, s in enumerate(extra, 1):
                    s.indice = base + i
                plano.slots.extend(extra)

    elif cfg.modo in ("batida", "frases") and analise is not None \
            and analise.tem_batidas:
        if cfg.modo == "frases":
            plano.avisos.append(
                "sem frases de letra; usando a batida como referência"
            )
        plano.slots = slots_de_batida(analise, cfg, plano.duracao_musica)
        plano.modo_usado = "batida"

    else:
        if cfg.modo == "batida" and (analise is None or not analise.tem_batidas):
            plano.avisos.append(
                "não foi possível detectar batidas; usando duração fixa"
            )
        elif cfg.modo == "frases" and not segmentos_validos:
            plano.avisos.append(
                "sem letra transcrita; usando duração fixa"
            )
        plano.slots = slots_uniformes(plano.duracao_musica, cfg, analise)
        plano.modo_usado = "fixo"

    if not plano.slots:
        plano.avisos.append("nenhum clipe pôde ser derivado")
        callback_log("[PLANO] Não foi possível derivar clipes")
        return plano

    # ── 2. Casamento com a midia ───────────────────────────────
    n = plano.n_slots
    videos, imagens = dividir_midias(midias)

    if not videos and not imagens:
        plano.avisos.append("nenhuma mídia disponível")
        return plano

    diretas = ordenar_por_energia(plano.slots, videos, imagens, cfg.semente)

    if len(diretas) < n:
        faltam = n - len(diretas)
        extras, voltas = reciclar_midias(
            diretas, faltam, videos, imagens, cfg
        )
        plano.midias_faltando = faltam
        plano.reciclagens = voltas
        plano.midias = list(diretas) + list(extras)  # type: ignore[attr-defined]
    else:
        plano.midias_faltando = 0
        plano.reciclagens = 0
        plano.midias = list(diretas)  # type: ignore[attr-defined]

    # Efeito por slot, coerente com a midia escolhida
    plano.efeitos = [  # type: ignore[attr-defined]
        escolher_efeito(s, m, i)
        for i, (s, m) in enumerate(zip(plano.slots, plano.midias))
    ]

    for linha in plano.explicar():
        callback_log(linha)

    return plano


def _auto_teste() -> None:
    """Checagens internas. Rodar direto para validar o calculo."""
    from MusicClipStudio.transcricao import SegmentoLegenda

    cfg = ConfigRitmo()

    print("== tolerancia antes de fatiar ==")
    # limite efetivo = max * (1 + tol) = 6.0 * 1.2 = 7.2s
    for dur, esperado in ((5.0, 1), (6.0, 1), (6.3, 1),
                          (7.0, 1), (7.3, 2), (20.0, 4)):
        seg = SegmentoLegenda(1, 0.0, dur, "teste")
        slots = slots_de_frases([seg], cfg)
        ok = "OK" if len(slots) == esperado else "FALHOU"
        print(f"  {dur:5.1f}s max={cfg.max_por_clipe} tol={cfg.tolerancia}"
              f" -> {len(slots)} clipe(s) (esperado {esperado}) {ok}")

    print("\n== reciclagem embaralha cada volta ==")
    mídias = [f"m{i}" for i in range(12)]
    plano = calcular_plano(180.0, mídias, cfg, callback_log=lambda _m: None)
    print(f"  {plano.n_slots} clipes, {len(mídias)} mídias "
          f"-> faltam {plano.midias_faltando}, {plano.reciclagens} volta(s)")
    print(f"  {plano.resumo()}")

    print("\n== efeito pela natureza ==")
    slot = Slot(1, 0.0, 3.0, energia=0.9)
    print("  video  ->", escolher_efeito(slot, {"type": "video"}, 0))
    print("  imagem ->", escolher_efeito(slot, {"type": "image"}, 0))

    print("\n== fallback sem nada ==")
    p2 = calcular_plano(30.0, mídias, cfg,
                        analise=AnaliseAudio(), callback_log=lambda _m: None)
    print(f"  modo: {p2.modo_usado} | {p2.n_slots} clipes")
    print(f"  avisos: {p2.avisos}")

    print("\n== duracao invalida ==")
    p3 = calcular_plano(0.0, mídias, cfg, callback_log=lambda _m: None)
    print(f"  slots: {p3.n_slots} | avisos: {p3.avisos}")

    print("\nauto-teste: OK")


if __name__ == "__main__":
    _auto_teste()
