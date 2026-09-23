"""
MusicClipStudio/transcricao.py
Transcrição de áudio em letra sincronizada, via faster-whisper.

QUANDO ISTO É USADO
-------------------
Só quando o usuário NÃO fornece a letra. Se a letra existe, ela é a
verdade — transcrever por cima só introduziria erro.

POR QUE faster-whisper E NÃO openai-whisper
--------------------------------------------
O modelo é o mesmo (Whisper), mas a implementação CTranslate2 é bem mais
rápida e usa menos memória, o que importa porque aqui a transcrição
disputa a GPU com a geração de áudio e vídeo. A API também já devolve
os tempos por segmento, que é justamente o que a legenda precisa.

O QUE ESTE MÓDULO DEVOLVE
-------------------------
Uma lista de `SegmentoLegenda`, cada um com texto, início e fim em
segundos. É exatamente o que a tela de edição de legenda consome e o
que dá para virar SRT sem mais nenhuma conta.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Callable, Optional


# ════════════════════════════════════════════════════════════════════
#  MODELOS DISPONÍVEIS
#  Ordem crescente de qualidade e custo. "small" é o ponto de
#  equilíbrio para letra de música: entende português bem e ainda roda
#  em máquina modesta.
# ════════════════════════════════════════════════════════════════════

MODELOS: tuple[str, ...] = ("tiny", "base", "small", "medium", "large-v3")

MODELO_PADRAO: str = "small"


# ════════════════════════════════════════════════════════════════════
#  RESULTADO
# ════════════════════════════════════════════════════════════════════

@dataclass
class SegmentoLegenda:
    """Uma linha de legenda com seu tempo."""

    indice: int
    inicio: float          # segundos
    fim: float             # segundos
    texto: str

    @property
    def duracao(self) -> float:
        return max(0.0, self.fim - self.inicio)

    def para_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def de_dict(cls, d: dict) -> "SegmentoLegenda":
        return cls(
            indice=int(d.get("indice", 0)),
            inicio=float(d.get("inicio", 0.0)),
            fim=float(d.get("fim", 0.0)),
            texto=str(d.get("texto", "")),
        )


@dataclass
class ResultadoTranscricao:
    """Tudo que a transcrição produziu."""

    segmentos: list[SegmentoLegenda] = field(default_factory=list)
    idioma: str = ""
    duracao_audio: float = 0.0
    modelo: str = ""
    erro: str = ""

    @property
    def ok(self) -> bool:
        return bool(self.segmentos) and not self.erro

    @property
    def texto_completo(self) -> str:
        """Letra inteira, uma linha por segmento."""
        return "\n".join(s.texto for s in self.segmentos if s.texto.strip())

    def tempo_estimado_por_linha(self) -> float:
        """Duração média de uma linha, útil para distribuir sem sincronia."""
        if not self.segmentos:
            return 0.0
        return sum(s.duracao for s in self.segmentos) / len(self.segmentos)


# ════════════════════════════════════════════════════════════════════
#  DISPONIBILIDADE
# ════════════════════════════════════════════════════════════════════

def faster_whisper_disponivel() -> bool:
    """Verifica se a biblioteca está instalada."""
    try:
        import faster_whisper  # noqa: F401
        return True
    except ImportError:
        return False


def _achar_ffmpeg() -> Optional[str]:
    """Localiza o ffmpeg, que o Whisper usa para decodificar o áudio.

    O faster-whisper precisa abrir o arquivo antes de transcrever. Se o
    ffmpeg não estiver no PATH, procuramos nos lugares onde ele costuma
    ficar em instalações Windows de uso comum.
    """
    import shutil

    encontrado = shutil.which("ffmpeg")
    if encontrado:
        return encontrado

    candidatos = [
        Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Links" / "ffmpeg.exe",
        Path("C:/ffmpeg/bin/ffmpeg.exe"),
        Path("C:/Program Files/ffmpeg/bin/ffmpeg.exe"),
        Path(os.environ.get("USERPROFILE", "")) / "scoop" / "shims" / "ffmpeg.exe",
    ]
    for c in candidatos:
        try:
            if c.exists():
                return str(c)
        except OSError:
            continue
    return None


# ════════════════════════════════════════════════════════════════════
#  TRANSCRIÇÃO
# ════════════════════════════════════════════════════════════════════

def transcrever(
    audio_path: str,
    modelo: str = MODELO_PADRAO,
    idioma: Optional[str] = None,
    callback_log: Optional[Callable[[str], None]] = None,
    callback_prog: Optional[Callable[[int], None]] = None,
    device: str = "auto",
) -> ResultadoTranscricao:
    """Transcreve um arquivo de áudio em segmentos com tempo.

    Args:
        audio_path: Caminho do áudio (mp3, wav, m4a, ...).
        modelo: tiny | base | small | medium | large-v3.
        idioma: Força um idioma ("pt", "en"). None deixa o Whisper detectar.
        callback_log: Recebe mensagens de progresso em texto.
        callback_prog: Recebe um percentual de 0 a 100.
        device: "auto", "cuda" ou "cpu".

    Returns:
        ResultadoTranscricao. Mesmo em falha devolve o objeto com o campo
        `erro` preenchido, em vez de estourar exceção — assim quem chama
        não precisa de try/except em volta para tratar o caso normal de
        "não deu, seguimos sem legenda".

    >>> r = transcrever("musica.mp3")          # doctest: +SKIP
    >>> r.ok                                    # doctest: +SKIP
    True
    """
    log = callback_log or (lambda m: None)
    prog = callback_prog or (lambda p: None)

    caminho = Path(audio_path)
    if not caminho.exists():
        msg = f"Arquivo de áudio não encontrado: {audio_path}"
        log(f"[WHISPER] {msg}")
        return ResultadoTranscricao(segmentos=[], modelo=modelo, erro=msg)

    if not faster_whisper_disponivel():
        msg = (
            "faster-whisper não instalado. "
            "Instale com: pip install faster-whisper"
        )
        log(f"[WHISPER] {msg}")
        return ResultadoTranscricao(segmentos=[], modelo=modelo, erro=msg)

    if modelo not in MODELOS:
        log(f"[WHISPER] Modelo '{modelo}' desconhecido; usando '{MODELO_PADRAO}'.")
        modelo = MODELO_PADRAO

    try:
        from faster_whisper import WhisperModel
    except ImportError as e:
        msg = f"Falha ao importar faster_whisper: {e}"
        log(f"[WHISPER] {msg}")
        return ResultadoTranscricao(segmentos=[], modelo=modelo, erro=msg)

    # ── Escolha do dispositivo ──────────────────────────────────────
    # Em "auto" tentamos a GPU e caímos para CPU se não houver CUDA.
    # CPU com int8 é surpreendentemente usável para um áudio só.
    if device == "auto":
        try:
            import torch
            usar_cuda = torch.cuda.is_available()
        except ImportError:
            usar_cuda = False
        device = "cuda" if usar_cuda else "cpu"

    compute_type = "float16" if device == "cuda" else "int8"

    log(f"[WHISPER] Carregando modelo '{modelo}' em {device} ({compute_type})...")
    prog(5)

    try:
        wmodel = WhisperModel(modelo, device=device, compute_type=compute_type)
    except Exception as e:
        # Caso clássico: pediram cuda mas falta a lib CUDA. Tentamos CPU
        # antes de desistir, porque a transcrição ainda é possível.
        log(f"[WHISPER] Falha ao carregar em {device}: {e}")
        if device == "cuda":
            log("[WHISPER] Tentando novamente em CPU...")
            try:
                wmodel = WhisperModel(modelo, device="cpu", compute_type="int8")
                device = "cpu"
            except Exception as e2:
                msg = f"Não foi possível carregar o modelo: {e2}"
                log(f"[WHISPER] {msg}")
                return ResultadoTranscricao(segmentos=[], modelo=modelo, erro=msg)
        else:
            msg = f"Não foi possível carregar o modelo: {e}"
            log(f"[WHISPER] {msg}")
            return ResultadoTranscricao(segmentos=[], modelo=modelo, erro=msg)

    log(f"[WHISPER] Transcrevendo: {caminho.name}")
    prog(15)

    try:
        # vad_filter remove trechos sem fala. Em música isso é arriscado
        # (intro instrumental não tem voz), mas ajuda a não inventar
        # texto em cima de trecho só instrumental.
        segmentos_brutos, info = wmodel.transcribe(
            str(caminho),
            language=idioma,
            vad_filter=True,
            beam_size=5,
            word_timestamps=False,
        )

        duracao = float(getattr(info, "duration", 0.0) or 0.0)
        idioma_detectado = getattr(info, "language", "") or (idioma or "")

        segmentos: list[SegmentoLegenda] = []
        for i, seg in enumerate(segmentos_brutos, 1):
            texto = (seg.text or "").strip()
            if not texto:
                continue
            segmentos.append(
                SegmentoLegenda(
                    indice=i,
                    inicio=float(seg.start),
                    fim=float(seg.end),
                    texto=texto,
                )
            )
            # Progresso de 15% a 95% conforme o áudio avança.
            if duracao > 0:
                pct = 15 + int((float(seg.end) / duracao) * 80)
                prog(min(pct, 95))

    except Exception as e:
        msg = f"Erro durante a transcrição: {e}"
        log(f"[WHISPER] {msg}")
        return ResultadoTranscricao(segmentos=[], modelo=modelo, erro=msg)

    prog(100)

    if not segmentos:
        msg = (
            "Nenhuma fala detectada. O áudio pode ser instrumental — "
            "nesse caso o clipe segue sem legenda."
        )
        log(f"[WHISPER] {msg}")
        return ResultadoTranscricao(
            segmentos=[], idioma=idioma_detectado,
            duracao_audio=duracao, modelo=modelo, erro=msg,
        )

    log(
        f"[WHISPER] Pronto: {len(segmentos)} linha(s), "
        f"idioma '{idioma_detectado}', {duracao:.1f}s de áudio."
    )

    return ResultadoTranscricao(
        segmentos=segmentos,
        idioma=idioma_detectado,
        duracao_audio=duracao,
        modelo=modelo,
    )


# ════════════════════════════════════════════════════════════════════
#  SRT
# ════════════════════════════════════════════════════════════════════

def _formato_srt(segundos: float) -> str:
    """Segundos -> HH:MM:SS,mmm (formato do SRT)."""
    if segundos < 0:
        segundos = 0.0
    h = int(segundos // 3600)
    m = int((segundos % 3600) // 60)
    s = int(segundos % 60)
    ms = int(round((segundos - int(segundos)) * 1000))
    # O arredondamento pode empurrar para 1000ms.
    if ms >= 1000:
        ms = 0
        s += 1
        if s >= 60:
            s = 0
            m += 1
            if m >= 60:
                m = 0
                h += 1
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def segmentos_para_srt(segmentos: list[SegmentoLegenda]) -> str:
    """Converte os segmentos no texto de um arquivo SRT."""
    linhas: list[str] = []
    for i, seg in enumerate(segmentos, 1):
        linhas.append(str(i))
        linhas.append(f"{_formato_srt(seg.inicio)} --> {_formato_srt(seg.fim)}")
        linhas.append(seg.texto)
        linhas.append("")
    return "\n".join(linhas)


def salvar_srt(segmentos: list[SegmentoLegenda], saida: str) -> str:
    """Grava os segmentos como arquivo .srt e devolve o caminho."""
    caminho = Path(saida)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(segmentos_para_srt(segmentos), encoding="utf-8")
    return str(caminho)


def ajustar_segmentos(
    segmentos: list[SegmentoLegenda],
    deslocamento: float = 0.0,
    duracao_total: Optional[float] = None,
) -> list[SegmentoLegenda]:
    """Desloca todos os tempos e, opcionalmente, limita à duração.

    O deslocamento serve quando o áudio transcrito tem um trecho de
    silêncio no começo e a legenda precisa começar mais cedo ou mais
    tarde do que o Whisper achou.
    """
    ajustados: list[SegmentoLegenda] = []
    for seg in segmentos:
        inicio = max(0.0, seg.inicio + deslocamento)
        fim = max(inicio, seg.fim + deslocamento)
        if duracao_total is not None:
            inicio = min(inicio, duracao_total)
            fim = min(fim, duracao_total)
        ajustados.append(
            SegmentoLegenda(
                indice=seg.indice, inicio=inicio, fim=fim, texto=seg.texto,
            )
        )
    return ajustados


# ════════════════════════════════════════════════════════════════════
#  QUEBRA EM LINHAS DE LEGENDA
# ════════════════════════════════════════════════════════════════════

def quebrar_em_frases(
    segmentos: list[SegmentoLegenda],
    max_segundos: float = 5.0,
    max_palavras: int = 12,
) -> list[SegmentoLegenda]:
    """Divide segmentos longos em linhas de legenda utilizáveis.

    O Whisper tende a agrupar várias frases num segmento só — no teste
    com áudio real ele juntou três linhas em 7 segundos. Numa legenda de
    clipe isso fica ruim: a pessoa lê tudo de uma vez e a linha seguinte
    demora a chegar.

    Aqui dividimos por pontuação e, quando ainda ficar longo, por
    quantidade de palavras. O tempo é distribuído proporcionalmente ao
    número de palavras de cada pedaço, que é uma aproximação boa porque
    a fala mantém ritmo mais ou menos constante.

    >>> segs = [SegmentoLegenda(1, 0.0, 9.0, "Uma frase. Outra frase. Terceira.")]
    >>> [s.texto for s in quebrar_em_frases(segs)]
    ['Uma frase.', 'Outra frase.', 'Terceira.']
    """
    resultado: list[SegmentoLegenda] = []
    indice = 1

    for seg in segmentos:
        pedacos = _dividir_texto(seg.texto, max_palavras)

        if len(pedacos) <= 1:
            resultado.append(
                SegmentoLegenda(indice=indice, inicio=seg.inicio,
                                fim=seg.fim, texto=seg.texto.strip())
            )
            indice += 1
            continue

        # Tempo distribuído conforme o peso de cada pedaço, para a
        # legenda acompanhar a fala em vez de cortar no meio.
        pesos = [max(1, len(p.split())) for p in pedacos]
        total_peso = sum(pesos)
        duracao = max(0.0, seg.fim - seg.inicio)
        cursor = seg.inicio

        for pedaco, peso in zip(pedacos, pesos):
            fatia = duracao * (peso / total_peso)
            fim = min(cursor + fatia, seg.fim)
            if fim <= cursor:
                fim = cursor + 0.1
            resultado.append(
                SegmentoLegenda(
                    indice=indice,
                    inicio=round(cursor, 3),
                    fim=round(fim, 3),
                    texto=pedaco,
                )
            )
            cursor = fim
            indice += 1

    return resultado


def _dividir_texto(texto: str, max_palavras: int) -> list[str]:
    """Divide um texto em pedaços, primeiro por frase e depois por tamanho."""
    import re

    texto = texto.strip()
    if not texto:
        return []

    # Quebra mantendo o sinal de pontuação junto da frase.
    frases = re.findall(r"[^.!?…]+[.!?…]*", texto)
    frases = [f.strip() for f in frases if f.strip()]

    if not frases:
        frases = [texto]

    # Frases ainda muito longas são cortadas por contagem de palavras.
    pedacos: list[str] = []
    for frase in frases:
        palavras = frase.split()
        if len(palavras) <= max_palavras:
            pedacos.append(frase)
            continue
        for i in range(0, len(palavras), max_palavras):
            pedacos.append(" ".join(palavras[i:i + max_palavras]))

    # Se um único pedaço durar demais mas for curto em palavras
    # (letra com palavras longas), ainda vale devolver como está.
    return pedacos


def segmentos_a_partir_de_letra(
    letra: str,
    duracao_total: float,
) -> list[SegmentoLegenda]:
    """Distribui linhas de letra já conhecida ao longo da duração.

    Usado quando o usuário FORNECEU a letra: não há transcrição, mas a
    tela de edição ainda precisa de tempos para mostrar. A distribuição
    é uniforme, ponderada pelo tamanho de cada linha — o usuário ajusta
    o que quiser depois.
    """
    linhas = [l.strip() for l in letra.splitlines() if l.strip()]
    if not linhas or duracao_total <= 0:
        return []

    pesos = [max(1, len(l.split())) for l in linhas]
    total_peso = sum(pesos)
    cursor = 0.0
    segmentos: list[SegmentoLegenda] = []

    for i, (linha, peso) in enumerate(zip(linhas, pesos), 1):
        fatia = duracao_total * (peso / total_peso)
        fim = min(cursor + fatia, duracao_total)
        segmentos.append(
            SegmentoLegenda(
                indice=i, inicio=round(cursor, 3), fim=round(fim, 3), texto=linha,
            )
        )
        cursor = fim

    return segmentos
