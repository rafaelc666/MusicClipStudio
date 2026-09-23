"""
Renderizacao das legendas sobre o video.

Responsabilidade deste modulo: transformar uma lista de `SegmentoLegenda`
em legendas VISIVEIS, queimadas nos frames do video.

Por que Pillow e nao TextClip/ImageMagick:
  - TextClip do moviepy 2.x depende de ImageMagick, que costuma faltar no
    Windows e quebra o render inteiro no meio da geracao.
  - Desenhar com Pillow garante acentuacao correta (a letra vem em pt-BR),
    controle de quebra de linha e uma faixa de fundo para legibilidade,
    sem dependencia externa.

O modulo nao decide QUAIS legendas existem: ele recebe a lista ja revisada
pelo usuario (etapa 2 da GUI) e so desenha.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

try:
    from MusicClipStudio.transcricao import SegmentoLegenda
except Exception:  # pragma: no cover - import defensivo
    SegmentoLegenda = None


# ════════════════════════════════════════════════════════════════
# Estilo
# ════════════════════════════════════════════════════════════════

@dataclass
class EstiloLegenda:
    """Parametros visuais da legenda queimada no video."""

    tamanho_fonte: int = 54
    fonte: str = ""                  # vazio = escolhe automaticamente
    cor_texto: tuple = (255, 255, 255)
    cor_borda: tuple = (0, 0, 0)
    cor_fundo: tuple = (0, 0, 0, 140)  # RGBA: preto translucido
    margem_inferior: float = 0.12    # fracao da altura
    largura_max: float = 0.86        # fracao da largura
    espacamento_linhas: int = 10
    padding_x: int = 28
    padding_y: int = 16
    raio_fundo: int = 12
    contorno: int = 3

    # Aliases em portugues para o uso na GUI
    @property
    def altura_relativa(self) -> float:
        return self.margem_inferior


# Fontes candidatas por ordem de preferencia. Todas existem no Windows
# ou sao faceis de achar; se nenhuma servir, caimos na fonte padrao do PIL.
_FONTES_CANDIDATAS = (
    "segoeuib.ttf",   # Segoe UI Bold
    "segoeui.ttf",    # Segoe UI
    "arialbd.ttf",    # Arial Bold
    "arial.ttf",
    "calibrib.ttf",
    "DejaVuSans-Bold.ttf",
    "DejaVuSans.ttf",
)


def _carregar_fonte(tamanho: int, preferida: str = ""):
    """Carrega uma fonte que suporte acentos.

    Tenta, em ordem: a fonte pedida, uma lista de fontes conhecidas do
    Windows, e por fim a fonte embutida do Pillow (que e' minima mas
    nao quebra o render).
    """
    tentativas: list[str] = []
    if preferida:
        tentativas.append(preferida)
    tentativas.extend(_FONTES_CANDIDATAS)

    for nome in tentativas:
        try:
            return ImageFont.truetype(nome, tamanho)
        except (OSError, IOError):
            continue

    # Ultimo recurso: fonte escalavel embutida
    try:
        return ImageFont.load_default(size=tamanho)
    except TypeError:  # Pillow antigo nao aceita `size`
        return ImageFont.load_default()


def _quebrar_texto(draw: ImageDraw.ImageDraw, texto: str, fonte,
                   largura_max: int) -> list[str]:
    """Quebra o texto em linhas que cabem em `largura_max` pixels.

    Quebra por palavra. Se uma unica palavra for maior que a largura
    (caso raro, mas acontece com palavras coladas), ela fica sozinha
    na linha em vez de ser cortada — cortar texto em legenda e' pior
    que deixar uma linha longa.
    """
    if not texto.strip():
        return []

    def largura_de(t: str) -> float:
        try:
            return draw.textlength(t, font=fonte)
        except AttributeError:
            return draw.textsize(t, font=fonte)[0]

    palavras = texto.split()
    linhas: list[str] = []
    atual = ""

    for palavra in palavras:
        candidata = f"{atual} {palavra}".strip()
        if largura_de(candidata) <= largura_max or not atual:
            atual = candidata
        else:
            linhas.append(atual)
            atual = palavra

    if atual:
        linhas.append(atual)

    return linhas


def desenhar_legenda(
    frame: Image.Image,
    texto: str,
    estilo: EstiloLegenda | None = None,
) -> Image.Image:
    """Desenha uma linha de legenda sobre um frame.

    Recebe e devolve um `PIL.Image`. Nao modifica o frame original.
    """
    estilo = estilo or EstiloLegenda()
    if not texto.strip():
        return frame

    base = frame.convert("RGBA")
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    largura, altura = base.size
    fonte = _carregar_fonte(estilo.tamanho_fonte, estilo.fonte)

    largura_max_px = int(largura * estilo.largura_max)
    linhas = _quebrar_texto(draw, texto, fonte, largura_max_px)
    if not linhas:
        return frame

    # Medir o bloco inteiro
    larguras = []
    for linha in linhas:
        try:
            larguras.append(draw.textlength(linha, font=fonte))
        except AttributeError:
            larguras.append(draw.textsize(linha, font=fonte)[0])

    try:
        altura_linha = draw.textbbox((0, 0), "Ag", font=fonte)[3]
    except AttributeError:
        altura_linha = estilo.tamanho_fonte

    largura_texto = max(larguras) if larguras else 0
    altura_texto = (altura_linha * len(linhas)
                    + estilo.espacamento_linhas * (len(linhas) - 1))

    # Caixa de fundo (fundo escuro translucido melhora a leitura sobre
    # qualquer imagem, sem precisar de contorno grosso)
    caixa_w = largura_texto + estilo.padding_x * 2
    caixa_h = altura_texto + estilo.padding_y * 2
    caixa_x = (largura - caixa_w) / 2
    caixa_y = altura - caixa_h - altura * estilo.margem_inferior

    # Nao deixar a caixa sair pela parte de cima em videos muito baixos
    caixa_y = max(caixa_y, altura * 0.02)

    draw.rounded_rectangle(
        [caixa_x, caixa_y, caixa_x + caixa_w, caixa_y + caixa_h],
        radius=estilo.raio_fundo,
        fill=estilo.cor_fundo,
    )

    # Texto, linha a linha, centralizado dentro da caixa
    cursor_y = caixa_y + estilo.padding_y
    for linha, largura_linha in zip(linhas, larguras):
        x = (largura - largura_linha) / 2
        # Contorno: desenha o texto levemente deslocado antes do texto
        # principal. Isso mantem a legenda legivel sobre fundos claros
        # sem depender de stroke_color (que nem toda versao suporta).
        if estilo.contorno > 0:
            for dx in (-estilo.contorno, 0, estilo.contorno):
                for dy in (-estilo.contorno, 0, estilo.contorno):
                    if dx == 0 and dy == 0:
                        continue
                    draw.text((x + dx, cursor_y + dy), linha,
                              font=fonte, fill=estilo.cor_borda)
        draw.text((x, cursor_y), linha, font=fonte, fill=estilo.cor_texto)
        cursor_y += altura_linha + estilo.espacamento_linhas

    resultado = Image.alpha_composite(base, overlay)

    # Se o frame original era RGB, devolver RGB (moviepy espera 3 canais
    # para o codec libx264 com yuv420p)
    if frame.mode == "RGB":
        return resultado.convert("RGB")
    return resultado


def legenda_ativa(segmentos, t: float):
    """Devolve o segmento que cobre o instante `t`, ou None.

    Aceita qualquer objeto com `.inicio`, `.fim` e `.texto`, o que
    inclui `SegmentoLegenda`.
    """
    for seg in segmentos:
        if seg.inicio <= t < seg.fim:
            return seg
    return None


# ════════════════════════════════════════════════════════════════
# Integracao com o video
# ════════════════════════════════════════════════════════════════

def aplicar_legendas(video_clip, segmentos, estilo: EstiloLegenda | None = None,
                     callback_log=None):
    """Devolve um novo clip com as legendas queimadas nos frames.

    Envolve o `make_frame` do clip original: para cada instante, desenha
    a legenda correspondente. Nao reencoda nada aqui — a codificacao
    continua acontecendo no `write_videofile` de quem chamou.

    Se `segmentos` estiver vazio, devolve o clip original inalterado
    (importante: nao força um render extra de graca).
    """
    if callback_log is None:
        callback_log = lambda _m: None

    segmentos = [s for s in (segmentos or []) if getattr(s, "texto", "").strip()]
    if not segmentos:
        callback_log("[LEGENDA] Nenhuma legenda para queimar")
        return video_clip

    estilo = estilo or EstiloLegenda()

    def aplicar(get_frame, t: float):
        """Assinatura exigida pelo moviepy 2.x: (get_frame, t)."""
        frame = get_frame(t)
        seg = legenda_ativa(segmentos, t)
        if seg is None:
            return frame

        imagem = Image.fromarray(np.asarray(frame).astype("uint8"))
        imagem = desenhar_legenda(imagem, seg.texto, estilo)
        return np.asarray(imagem)

    novo = video_clip.transform(aplicar)
    callback_log(f"[LEGENDA] {len(segmentos)} legenda(s) serao queimadas")
    return novo


# ════════════════════════════════════════════════════════════════
# Fallback via ffmpeg (SRT externo)
# ════════════════════════════════════════════════════════════════

def _achar_ffmpeg() -> str | None:
    caminho = shutil.which("ffmpeg")
    return caminho


def queimar_srt_ffmpeg(video_entrada: str, srt_path: str, video_saida: str,
                       callback_log=None) -> str:
    """Queima um SRT no video usando ffmpeg (subtitles filter).

    Caminho alternativo: mais rapido que redesenhar frame a frame, mas
    depende do filtro `subtitles` estar compilado no ffmpeg e do
    escapamento correto do caminho no Windows (que e' a fonte classica
    de falha silenciosa).
    """
    if callback_log is None:
        callback_log = print

    ffmpeg = _achar_ffmpeg()
    if not ffmpeg:
        callback_log("[LEGENDA] ffmpeg nao encontrado — fallback indisponivel")
        return ""

    # O filtro subtitles interpreta ':' e '\' como separadores; no Windows
    # precisamos escapar o caminho ou ele corta a string no meio.
    srt_escapado = (str(Path(srt_path).resolve())
                    .replace("\\", "/")
                    .replace(":", r"\:"))
    filtro = f"subtitles='{srt_escapado}'"

    cmd = [
        ffmpeg, "-y", "-i", str(video_entrada),
        "-vf", filtro,
        "-c:a", "copy",
        "-c:v", "libx264", "-crf", "18", "-preset", "fast",
        str(video_saida),
    ]

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              encoding="utf-8", errors="replace")
    except Exception as e:
        callback_log(f"[LEGENDA] Erro chamando ffmpeg: {e}")
        return ""

    if proc.returncode != 0:
        cauda = (proc.stderr or "")[-400:]
        callback_log(f"[LEGENDA] ffmpeg falhou (rc={proc.returncode}): {cauda}")
        return ""

    callback_log(f"[LEGENDA] SRT queimado via ffmpeg: {video_saida}")
    return str(video_saida)


# ════════════════════════════════════════════════════════════════
# Conversao de / para SRT (para usar com o fallback do ffmpeg)
# ════════════════════════════════════════════════════════════════

def _formato_srt(segundos: float) -> str:
    """Segundos → HH:MM:SS,mmm (com rollover correto de milissegundos)."""
    if segundos < 0:
        segundos = 0.0
    total_ms = int(round(segundos * 1000))
    h, resto = divmod(total_ms, 3_600_000)
    m, resto = divmod(resto, 60_000)
    s, ms = divmod(resto, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def segmentos_para_srt(segmentos, saida: str) -> str:
    """Escreve os segmentos revisados como SRT.

    Serve tanto para o fallback do ffmpeg quanto para entregar o arquivo
    de legenda junto com o video (o usuario costuma querer os dois).
    """
    caminho = Path(saida)
    caminho.parent.mkdir(parents=True, exist_ok=True)

    with open(caminho, "w", encoding="utf-8") as f:
        for i, seg in enumerate(segmentos, 1):
            texto = str(seg.texto).strip()
            if not texto:
                continue
            f.write(f"{i}\n")
            f.write(f"{_formato_srt(seg.inicio)} --> {_formato_srt(seg.fim)}\n")
            f.write(f"{texto}\n\n")

    return str(caminho)


def segmentos_de_srt(caminho: str) -> list:
    """Le um SRT de volta para segmentos (usado em testes e reimportacao)."""
    if SegmentoLegenda is None:  # pragma: no cover
        raise RuntimeError("SegmentoLegenda indisponivel")

    texto = Path(caminho).read_text(encoding="utf-8")
    blocos = [b for b in texto.strip().split("\n\n") if b.strip()]
    segmentos = []

    for i, bloco in enumerate(blocos, 1):
        linhas = [l for l in bloco.split("\n") if l.strip()]
        if len(linhas) < 2:
            continue
        try:
            faixa = linhas[1]
            ini_str, fim_str = [p.strip() for p in faixa.split("-->")]
        except ValueError:
            continue
        corpo = " ".join(linhas[2:]).strip()
        segmentos.append(SegmentoLegenda(
            indice=i,
            inicio=_segundos_de_srt(ini_str),
            fim=_segundos_de_srt(fim_str),
            texto=corpo,
        ))

    return segmentos


def _segundos_de_srt(tempo: str) -> float:
    """'HH:MM:SS,mmm' → segundos."""
    tempo = tempo.strip().replace(",", ".")
    partes = tempo.split(":")
    if len(partes) != 3:
        return 0.0
    h, m, s = partes
    try:
        return int(h) * 3600 + int(m) * 60 + float(s)
    except ValueError:
        return 0.0
