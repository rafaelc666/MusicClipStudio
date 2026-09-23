"""
Gerador de prompts de preenchimento (fallback generativo).

CONTEXTO
═══════════════════════════════════════════════════════════════════════
Quando a busca por stock nao encontra midia suficiente para cobrir o
video, o clipe fica com "reciclagem" (a mesma midia repetindo). Em vez
disso, este modulo produz PROMPTS de imagem e de video a partir do
tema/emocao da musica, para o usuario gerar com IA e completar o video.

Os prompts saem em dois formatos:
  - imagem: prompt de still cinematografico (fotograma)
  - video : prompt de tomada em movimento (com camera/acao)

A fonte de vocabulario e' o tema musical (temas_musicais.py) quando
existe; sem tema, cai nas cenas emocionais (interpretacao.CENAS).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

# ════════════════════════════════════════════════════════════════
# Vocabulario de movimento/qualidade para os prompts
# ════════════════════════════════════════════════════════════════

MOVIMENTOS_VIDEO: list[str] = [
    "slow cinematic camera push in",
    "gentle handheld drift",
    "aerial drone shot slowly descending",
    "slow pan left revealing the scene",
    "static shot with subtle movement in frame",
    "slow motion details",
]

QUALIDADES_IMAGEM: list[str] = [
    "cinematic still, shallow depth of field",
    "moody film photography, 35mm",
    "wide establishing shot, golden hour",
    "intimate close up, soft natural light",
    "atmospheric wide shot, volumetric light",
]

SUFIXO_COMUM = "no text, no watermark, no letters, highly detailed, 4k"


@dataclass
class PromptPreenchimento:
    """Um prompt sugerido para preencher uma lacuna de midia."""
    prompt: str
    tipo: str = "image"          # "image" | "video"
    origem: str = ""             # de onde veio (tema, emocao, letra)
    indice: int = 0

    def __str__(self) -> str:
        return f"[{self.tipo}] {self.prompt}"


def _limpar(base: str) -> str:
    """Remove sujeira de um termo de busca para virar base de prompt."""
    return " ".join((base or "").split()).strip(" ,.;:")


def gerar_prompts(
    bases: list[str],
    quantos: int = 4,
    tipos: Optional[list[str]] = None,
    origem: str = "",
) -> list[PromptPreenchimento]:
    """Gera prompts de imagem e/ou video a partir de bases de cena.

    Args:
        bases: cenas/termos base (ex: termos do tema ou cenas da emocao)
        quantos: quantos prompts ao todo
        tipos: quais tipos gerar ("image", "video", ou ambos)
        origem: rotulo de rastreio (tema/emocao/letra)

    Returns:
        Lista de PromptPreenchimento alternando imagem e video.
    """
    tipos = tipos or ["image", "video"]
    limpos = [b for b in (_limpar(b) for b in (bases or [])) if b]
    if not limpos or quantos <= 0:
        return []

    saida: list[PromptPreenchimento] = []
    i = 0
    while len(saida) < quantos:
        base = limpos[i % len(limpos)]
        tipo = tipos[len(saida) % len(tipos)]

        if tipo == "video":
            movimento = MOVIMENTOS_VIDEO[len(saida) % len(MOVIMENTOS_VIDEO)]
            prompt = f"{base}, {movimento}, {SUFIXO_COMUM}"
        else:
            qualidade = QUALIDADES_IMAGEM[len(saida) % len(QUALIDADES_IMAGEM)]
            prompt = f"{base}, {qualidade}, {SUFIXO_COMUM}"

        saida.append(PromptPreenchimento(
            prompt=prompt, tipo=tipo, origem=origem, indice=len(saida),
        ))
        i += 1

        # Evita laco infinito quando ha menos bases que prompts pedidos
        # e todas as combinacoes ja' foram usadas.
        if i > len(limpos) * max(len(tipos), 1) * 2:
            break

    return saida


def gerar_prompts_para_tema(
    tema, quantos: int = 4, tipos: Optional[list[str]] = None,
) -> list[PromptPreenchimento]:
    """Prompts a partir de um TemaMusical (termos_busca em ingles)."""
    if tema is None:
        return []
    bases = list(getattr(tema, "termos_busca", []) or [])
    return gerar_prompts(bases, quantos=quantos, tipos=tipos,
                         origem=getattr(tema, "nome", "") or "tema")


def gerar_prompts_para_emocao(
    emocao, quantos: int = 4, tipos: Optional[list[str]] = None,
) -> list[PromptPreenchimento]:
    """Prompts a partir de uma emocao (interpretacao.CENAS)."""
    try:
        from MusicClipStudio.interpretacao import CENAS
    except Exception:
        return []

    bases = list(CENAS.get(emocao, [])) if emocao is not None else []
    if not bases:
        # Sem emocao definida, usa o conjunto mais generico disponivel.
        for cenas in CENAS.values():
            bases.extend(cenas)
    return gerar_prompts(bases, quantos=quantos, tipos=tipos, origem="emocao")


def _auto_teste() -> None:
    print("== prompts a partir de cenas emocionais ==")
    for p in gerar_prompts(
        ["empty apartment at night", "rainy window close up"],
        quantos=4,
    ):
        print(f"  {p}")

    print("\n== prompts de tema (mantra) ==")
    try:
        from MusicClipStudio.temas_musicais import TEMAS
        mantra = next((t for t in TEMAS if t.id == "mantra"), None)
        for p in gerar_prompts_para_tema(mantra, quantos=4):
            print(f"  {p}")
    except Exception as e:
        print(f"  (temas indisponiveis: {e})")


if __name__ == "__main__":
    _auto_teste()
