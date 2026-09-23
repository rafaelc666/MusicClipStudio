"""E2E real: a busca de mídia (Etapa 5) MOSTRA os resultados na grade?

Bug corrigido em 21/09/2026: o botão "Buscar" chamava a API, mostrava um toast
com o total, e JOGAVA OS RESULTADOS FORA — a grade continuava desenhando um
array fixo de imagens locais do programa. O usuário via "Encontradas 15 mídias"
e nada mudava na tela.

Este teste prova o comportamento correto:
    1. abre o wizard na Etapa 5 (Mídia);
    2. registra quais imagens estão na grade ANTES;
    3. clica em "Buscar";
    4. espera a rede e confere que as imagens da grade MUDARAM;
    5. confirma que as novas imagens vêm de domínio externo (pexels etc.),
       não de /assets/ (que são as locais do programa).

Uso: python _utils/_teste_e2e_busca_midia.py
     (com frontend na 3100 e backend na 8300 rodando)
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

URL_FRONT = "http://127.0.0.1:3100"
URL_ETAPA = f"{URL_FRONT}/studio/new?step=midia"

CHROMIUM = Path(
    r"C:\Users\User\AppData\Local\ms-playwright\chromium-1234\chrome-win64\chrome.exe"
)


def main() -> int:
    from playwright.sync_api import sync_playwright

    print("=" * 66)
    print("  E2E: a busca de mídia mostra os resultados na grade?")
    print("=" * 66)

    with sync_playwright() as p:
        kwargs = {"headless": True, "args": ["--no-proxy-server"]}
        if CHROMIUM.exists():
            kwargs["executable_path"] = str(CHROMIUM)
        browser = p.chromium.launch(**kwargs)
        ctx = browser.new_context(no_viewport=False, viewport={"width": 1440, "height": 900})
        page = ctx.new_page()

        reqs: list[str] = []
        respostas: list[tuple[int, str]] = []
        page.on("request", lambda r: reqs.append(r.url) if "/api/" in r.url else None)
        page.on(
            "response",
            lambda r: respostas.append((r.status, r.url)) if "/api/" in r.url else None,
        )

        print(f"\n1) abrindo {URL_ETAPA}")
        page.goto(URL_ETAPA, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(2500)

        # ── imagens ANTES ──
        antes = page.eval_on_selector_all(
            "img", "els => els.map(e => e.getAttribute('src')).filter(Boolean)"
        )
        antes_locais = [s for s in antes if s.startswith("/assets/")]
        print(f"   imagens na grade antes: {len(antes)}  (locais: {len(antes_locais)})")

        # ── clica em Buscar ──
        print("\n2) clicando em 'Buscar'...")
        btn = page.get_by_role("button", name="Buscar")
        if btn.count() == 0:
            btn = page.locator("button:has-text('Buscar')")
        btn.first.click()

        # espera a resposta da API de busca
        for _ in range(60):
            if any("/api/midia/buscar" in u for _, u in respostas):
                break
            page.wait_for_timeout(500)
        page.wait_for_timeout(3000)

        # ── imagens DEPOIS ──
        depois = page.eval_on_selector_all(
            "img", "els => els.map(e => e.getAttribute('src')).filter(Boolean)"
        )
        depois_externos = [s for s in depois if s.startswith("http")]
        print(f"   imagens na grade depois: {len(depois)}  (externas: {len(depois_externos)})")

        # ── requisições ──
        print("\n3) requisições /api:")
        for r in dict.fromkeys(reqs):
            print("   -", r)
        print("   respostas:")
        for st, u in respostas:
            print(f"   - {st} {u}")

        # ── veredito ──
        mudou = set(antes) != set(depois)
        tem_externa = len(depois_externos) >= 4
        ok_http = any(
            st == 200 and "/api/midia/buscar" in u for st, u in respostas
        )

        print("\n" + "=" * 66)
        print(f"  grade mudou apos buscar .......: {mudou}")
        print(f"  imagens externas na grade .....: {tem_externa} ({len(depois_externos)})")
        print(f"  /api/midia/buscar respondeu 200: {ok_http}")
        veredito = mudou and tem_externa and ok_http
        print("  RESULTADO:", "PASSOU" if veredito else "FALHOU")
        print("=" * 66)

        browser.close()
        return 0 if veredito else 2


if __name__ == "__main__":
    raise SystemExit(main())
