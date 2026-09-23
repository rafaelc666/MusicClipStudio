"""
Encurtador de termos de busca para stock API.

PROBLEMA (diagnosticado em 2026-09-17)
═══════════════════════════════════════════════════════════════════════
A camada emocional (interpretacao.CENAS) descreve cenas como frases
cinematograficas de 5+ palavras:

    "empty apartment at night one lamp"
    "single person alone in crowded street"
    "person sitting alone in diner window"

Isso e' um PROMPT perfeito para IA generativa, mas um PESSIMO termo
de busca. Pexels e Pixabay indexam CONCEITOS CURTOS (2-3 palavras) e
fazem match por palavra isolada. Mandar 5 palavras faz a API cair num
match parcial em palavras genericas ("person", "empty", "night"), e o
resultado e' foto aleatoria fora de contexto.

  MANUAL (humano digita):   "rain"        -> 7.612 videos relevantes
  API (frase da cena):      "empty apartment at night one lamp"
                                          -> match difuso e irrelevante

Solucao: para a API, reduzir a cena ao seu NUCLEO visual (sujeito +
contexto), mantendo ate ~3 palavras. A frase completa continua sendo
usada como prompt de IA generativa (onde ela e' valiosa).
"""

from __future__ import annotations

import re

# ════════════════════════════════════════════════════════════════
# Palavras que NAO ajudam a API (enchimento narrativo)
# ════════════════════════════════════════════════════════════════

# Ruido gramatical: nunca devem virar termo de busca.
STOPWORDS_EN = {
    "a", "an", "the", "of", "in", "on", "at", "to", "for", "with",
    "by", "from", "into", "onto", "over", "under", "and", "or",
    "is", "are", "was", "were", "be", "being", "very", "just",
    "his", "her", "its", "their", "one", "some", "any",
}

# Palavras que descrevem MODIFICADOR, nao o sujeito. Uteis como
# segundo termo, ruins como nucleo (a API devolve tudo e nada).
MODIFICADORES_FRACOS = {
    "close", "closeup", "up", "slow", "motion", "soft", "warm",
    "cold", "dark", "light", "bright", "deep", "high", "low",
    "long", "short", "big", "small", "old", "new", "young",
    "empty", "full", "single", "lone", "lonely", "solitary",
    "alone", "distant", "far", "near", "beautiful", "sad",
}


def _palavras(texto: str) -> list[str]:
    """Normaliza para lista de palavras minusculas sem pontuacao."""
    t = (texto or "").lower()
    t = re.sub(r"[^\w\s]", " ", t)
    return [p for p in t.split() if p]


def _nucleo_forte(palavras: list[str], max_palavras: int) -> str:
    """Escolhe o nucleo visual de uma cena.

    Regra central: um MODIFICADOR sozinho nao e' termo de busca. A API
    responde a substantivos. Entao:
      1. o PRIMEIRO substantivo (nao-modificador) ancora o termo;
      2. os ultimos termos de conteudo entram como contexto, desde que
         nao sejam modificadores fracos (a menos que nao haja escolha);
      3. se nada sobrar, cai de volta para o primeiro termo de conteudo.
    """
    # 1. ancora: primeiro substantivo de conteudo
    ancora = ""
    for p in palavras:
        if p not in STOPWORDS_EN and p not in MODIFICADORES_FRACOS:
            ancora = p
            break
    if not ancora:
        for p in palavras:
            if p not in STOPWORDS_EN:
                ancora = p
                break
    if not ancora and palavras:
        ancora = palavras[0]

    nucleo = [ancora] if ancora else []

    # 2. contexto: ultimos termos de conteudo, preferindo nao-fracos
    candidatos = [
        p for p in palavras
        if p not in STOPWORDS_EN and p not in nucleo
    ]
    fortes = [p for p in candidatos if p not in MODIFICADORES_FRACOS]
    fracos = [p for p in candidatos if p in MODIFICADORES_FRACOS]

    espaco = max_palavras - len(nucleo)
    if espaco > 0:
        nucleo.extend(fortes[-espaco:])
        espaco = max_palavras - len(nucleo)
    if espaco > 0:
        # Sem substantivos suficientes: usa modificador como ultimo recurso.
        nucleo.extend(fracos[-espaco:])

    # Deduplica preservando ordem.
    vistos: set[str] = set()
    limpo: list[str] = []
    for p in nucleo:
        if p and p not in vistos:
            vistos.add(p)
            limpo.append(p)
    return " ".join(limpo[:max_palavras])


def termo_curto(cena: str, max_palavras: int = 3) -> str:
    """Reduz uma cena longa ao nucleo visual pesquisavel.

    Exemplos:
      "empty apartment at night one lamp"     -> "apartment night lamp"
      "single person alone in crowded street" -> "person crowded street"
      "lone figure on empty beach winter"     -> "figure beach winter"
      "person sitting alone in diner window"  -> "person diner window"
      "silhouette sitting by rainy window"    -> "silhouette rainy window"
    """
    palavras = _palavras(cena)
    if not palavras:
        return ""

    if len(palavras) <= max_palavras:
        return " ".join(palavras)

    return _nucleo_forte(palavras, max_palavras)


def termos_curtos(cenas: list[str], max_palavras: int = 3) -> list[str]:
    """Aplica termo_curto a uma lista, removendo duplicatas e vazios."""
    saida: list[str] = []
    vistos: set[str] = set()
    for cena in cenas or []:
        termo = termo_curto(cena, max_palavras=max_palavras)
        if termo and termo not in vistos:
            vistos.add(termo)
            saida.append(termo)
    return saida


def _auto_teste() -> None:
    casos = [
        ("empty apartment at night one lamp", "apartment lamp"),
        ("single person alone in crowded street", "person street"),
        ("lone figure on empty beach winter", "figure winter"),
        ("person sitting alone in diner window", "person window"),
        ("empty bed unmade morning light", "bed light"),
        ("silhouette sitting by rainy window", "silhouette window"),
        ("hands covering face grief", "hands grief"),
        ("woman looking at old photographs", "woman photographs"),
        ("solitary walk through fog", "walk fog"),
    ]
    print("== cena longa -> termo de busca ==")
    ok = 0
    for cena, esperado_contem in casos:
        curto = termo_curto(cena)
        marca = "OK " if curto and len(curto.split()) <= 3 else "!! "
        if curto and len(curto.split()) <= 3:
            ok += 1
        print(f"  {marca}{cena:42} -> {curto!r}")
    print(f"\n{ok}/{len(casos)} dentro do limite de 3 palavras")


if __name__ == "__main__":
    _auto_teste()
