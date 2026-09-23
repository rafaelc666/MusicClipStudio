"""E2E: mudar a LETRA muda os prompts e os resultados da busca?

Bug relatado em 21/09/2026:
    "de novo a busca não vem não pegou nada da letra da musica, mesmo
     mudando a letra as opções de busca de imagens e video são as mesmas"

Causa encontrada:
    1) A Etapa 04 era FALSA — um array hardcoded + `setTimeout(1200)` e
       um sufixo "· variação N". Nunca lia a letra, nunca chamava o backend.
    2) A Etapa 05 começava com o termo FIXO "city night cinematic" e não
       tinha ligação nenhuma com os prompts da Etapa 04.

O que este teste exige:
    A) duas letras diferentes geram PROMPTS diferentes;
    B) as imagens da grade mudam junto;
    C) as imagens vêm de domínio externo (pexels...), nunca de /assets/;
    D) nenhum prompt repetido dentro da mesma música.

Uso: python _utils/_teste_e2e_letra_muda_busca.py
     (frontend 3100 + backend 8300 de pé)
"""
from __future__ import annotations

import sys
from pathlib import Path

URL = "http://127.0.0.1:3100/studio/new?step=letra"

CHROMIUM = Path(
    r"C:\Users\User\AppData\Local\ms-playwright\chromium-1234\chrome-win64\chrome.exe"
)

LETRA_SOMBRIA = (
    "Quem foi muito ponderado\n"
    "Nunca fez nada de bom\n"
    "Eu quero ver a chuva cair\n"
    "Sob o letreiro do hotel\n"
    "A noite me engole inteiro\n"
    "Sem ninguem pra me escutar"
)

LETRA_ALEGRE = (
    "Sol na praia festa e alegria\n"
    "Dancando ate o amanhecer\n"
    "Coracao acelerado de amor\n"
    "Gritando de felicidade\n"
    "Todo mundo junto cantando\n"
    "Nunca vou te esquecer"
)


def uma_rodada(page, letra: str, nome: str) -> tuple[list[str], list[str]]:
    """Preenche a letra, gera prompts e volta com (chips, imagens)."""
    print(f"\n── rodada {nome} " + "─" * 40)
    page.goto(URL, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(2500)

    page.locator("textarea").first.fill(letra)
    page.wait_for_timeout(300)

    # Etapa 01 -> 04 (três "Avançar" do navegador do wizard)
    for _ in range(3):
        page.get_by_role("button", name="Avançar").last.click()
        page.wait_for_timeout(700)

    page.get_by_role("button", name="Gerar prompts com IA").click()
    page.wait_for_timeout(4000)

    page.get_by_role("button", name="Ir buscar as mídias destes prompts").click()
    page.wait_for_timeout(6000)

    chips = page.eval_on_selector_all(
        "button.rounded-full",
        "els => els.map(e => e.textContent.trim()).filter(t => t.length > 2)",
    )
    imgs = page.eval_on_selector_all(
        "img",
        "els => els.map(e => e.getAttribute('src') || '').filter(Boolean)",
    )
    print(f"   cenas da letra : {chips}")
    print(f"   imagens ({len(imgs)}): {imgs[:3]}")
    return chips, imgs


def main() -> int:
    from playwright.sync_api import sync_playwright

    print("=" * 70)
    print("  E2E: a letra realmente muda a busca de imagens/vídeo?")
    print("=" * 70)

    with sync_playwright() as p:
        kwargs = {"headless": True, "args": ["--no-proxy-server"]}
        if CHROMIUM.exists():
            kwargs["executable_path"] = str(CHROMIUM)
        browser = p.chromium.launch(**kwargs)
        ctx = browser.new_context(viewport={"width": 1440, "height": 950})
        page = ctx.new_page()

        erros: list[str] = []
        page.on(
            "response",
            lambda r: erros.append(f"{r.status} {r.url}")
            if "/api/" in r.url and r.status >= 400
            else None,
        )

        chips_a, imgs_a = uma_rodada(page, LETRA_SOMBRIA, "A · letra sombria")
        chips_b, imgs_b = uma_rodada(page, LETRA_ALEGRE, "B · letra alegre")

        browser.close()

    print("\n" + "=" * 70)
    ok = True

    def check(cond: bool, msg: str) -> None:
        nonlocal ok
        print(f"  [{'OK ' if cond else 'FALHA'}] {msg}")
        if not cond:
            ok = False

    check(bool(chips_a) and bool(chips_b), "as duas rodadas geraram prompts")
    check(set(chips_a) != set(chips_b), "letras diferentes -> PROMPTS diferentes")
    check(bool(imgs_a) and bool(imgs_b), "as duas rodadas trouxeram imagens")
    check(set(imgs_a) != set(imgs_b), "letras diferentes -> IMAGENS diferentes")

    for nome, imgs in (("A", imgs_a), ("B", imgs_b)):
        locais = [s for s in imgs if s.startswith("/assets")]
        externas = [s for s in imgs if s.startswith("http")]
        check(not locais, f"rodada {nome}: nenhuma imagem local do programa ({len(locais)})")
        check(bool(externas), f"rodada {nome}: imagens externas do banco de stock ({len(externas)})")

    if chips_a:
        check(len(set(chips_a)) == len(chips_a), f"rodada A: sem prompt repetido ({len(chips_a)} cenas)")
    if chips_b:
        check(len(set(chips_b)) == len(chips_b), f"rodada B: sem prompt repetido ({len(chips_b)} cenas)")

    if erros:
        print("\n  chamadas de API com erro:")
        for e in erros:
            print("   ", e)

    print("=" * 70)
    print("  RESULTADO:", "PASSOU" if ok else "FALHOU")
    print("=" * 70)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
