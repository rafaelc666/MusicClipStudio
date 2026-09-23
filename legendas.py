"""
Geração de legendas SRT a partir de letras.

Converte letra de música em blocos de legenda sincronizados
com a duração total do clipe.
"""

import re
from pathlib import Path
from typing import Optional


def _formato_srt(segundos: float) -> str:
    """Converte segundos → formato SRT (HH:MM:SS,mmm)."""
    h = int(segundos // 3600)
    m = int((segundos % 3600) // 60)
    s = int(segundos % 60)
    ms = int(round((segundos - int(segundos)) * 1000))
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def gerar_srt_letras(
    lyrics: str,
    saida: str,
    duracao_total: float,
    n_blocos: int = 5,
) -> str:
    """
    Gera arquivo SRT a partir de letras de música.

    Divide a letra em blocos sincronizados com a duração total.

    Args:
        lyrics: Letra completa
        saida: Caminho do arquivo SRT de saída
        duracao_total: Duração total do clipe em segundos
        n_blocos: Número aproximado de blocos de legenda

    Returns:
        Caminho do arquivo SRT gerado
    """
    linhas = [l.strip() for l in lyrics.split("\n") if l.strip()]
    if not linhas:
        linhas = [""]

    # Dividir linhas em blocos
    blocos = _dividir_em_blocos(linhas, n_blocos)

    # Calcular tempo por bloco
    tempo_bloco = duracao_total / len(blocos) if blocos else duracao_total

    srt_path = Path(saida)
    srt_path.parent.mkdir(parents=True, exist_ok=True)

    with open(srt_path, "w", encoding="utf-8") as f:
        for i, bloco in enumerate(blocos, 1):
            inicio = (i - 1) * tempo_bloco
            fim = min(i * tempo_bloco, duracao_total)
            texto = " ".join(bloco)
            texto = re.sub(r'\s+', ' ', texto).strip()
            if texto and texto[-1] not in ".!?":
                texto += "."

            f.write(f"{i}\n")
            f.write(f"{_formato_srt(inicio)} --> {_formato_srt(fim)}\n")
            f.write(f"{texto}\n\n")

    return str(srt_path)


def _dividir_em_blocos(linhas: list[str], n_blocos: int) -> list[list[str]]:
    """Divide linhas em n_blocos grupos balanceados."""
    if not linhas:
        return []

    if len(linhas) <= n_blocos:
        return [[l] for l in linhas]

    # Distribuir linhas de forma balanceada
    blocos = []
    tamanho = max(1, len(linhas) // n_blocos)

    for i in range(0, len(linhas), tamanho):
        bloco = linhas[i:i + tamanho]
        if bloco:
            blocos.append(bloco)

    return blocos if blocos else [linhas]


def gerar_srt_por_frase(
    lyrics: str,
    saida: str,
    duracao_total: float,
    frase_sep: str = "\n",
) -> str:
    """
    Gera SRT onde cada frase/linha da letra é um bloco.

    Útil quando a letra já está formatada frase por frase.
    """
    frases = [f.strip() for f in lyrics.split(frase_sep) if f.strip()]

    if not frases:
        return ""

    tempo_frase = duracao_total / len(frases)

    srt_path = Path(saida)
    srt_path.parent.mkdir(parents=True, exist_ok=True)

    with open(srt_path, "w", encoding="utf-8") as f:
        for i, frase in enumerate(frases, 1):
            inicio = (i - 1) * tempo_frase
            fim = min(i * tempo_frase, duracao_total)
            texto = re.sub(r'\s+', ' ', frase).strip()
            if texto[-1] not in ".!?":
                texto += "."

            f.write(f"{i}\n")
            f.write(f"{_formato_srt(inicio)} --> {_formato_srt(fim)}\n")
            f.write(f"{texto}\n\n")

    return str(srt_path)