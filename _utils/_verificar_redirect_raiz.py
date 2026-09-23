"""
Verifica em NAVEGADOR REAL (Playwright/Chromium) para onde cada rota vai.

Motivo: as páginas do App Router renderizam no cliente. Inspecionar o HTML cru
NÃO diz qual componente ganhou — o texto vem vazio. Só um browser de verdade
mostra a URL final após o redirecionamento client-side (router.replace).

Testa:
  /                        -> deve terminar em /studio  (o PROGRAMA)
  /studio                  -> deve ficar em /studio     (o PROGRAMA)
  /landing                 -> deve ficar em /landing    (marketing)

Uso: py _utils/_verificar_redirect_raiz.py
"""

import sys
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:3100"

# (rota pedida, trecho esperado na URL final, título esperado aproximado)
CASOS = [
    ("/", "manda para /studio", "/studio"),
    ("/studio", "e' o programa", "/studio"),
    ("/studio/new", "e' o wizard", "/studio/new"),
    ("/landing", "e' a landing", "/landing"),
]


def main() -> int:
    falhas = 0
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(ignore_https_errors=True)

        # Navegador nao deve usar o proxy do sistema (que intercepta localhost).
        ctx.set_extra_http_headers({})

        for rota, descricao, esperado in CASOS:
            page = ctx.new_page()
            erros = []
            page.on("pageerror", lambda e: erros.append(str(e)))
            try:
                page.goto(BASE + rota, wait_until="networkidle", timeout=45000)
                # da' tempo do useEffect/router.replace rodar
                page.wait_for_timeout(2500)
                url_final = page.url
                titulo = page.title()
                # texto visivel, para provar que renderizou algo real
                corpo = page.inner_text("body")[:160].replace("\n", " ")

                ok = esperado in url_final
                marca = "OK " if ok else "FALHA"
                if not ok:
                    falhas += 1

                print(f"{marca} {rota:14s} -> {url_final}")
                print(f"      ({descricao}) esperado conter: {esperado}")
                print(f"      title : {titulo[:70]}")
                print(f"      texto : {corpo[:120]}")
                if erros:
                    print(f"      ERROS JS: {erros[:2]}")
                print()
            except Exception as e:
                falhas += 1
                print(f"FALHA {rota:14s} -> excecao: {type(e).__name__}: {str(e)[:150]}\n")
            finally:
                page.close()

        browser.close()

    print("=" * 60)
    if falhas == 0:
        print("RESULTADO: TODOS OS REDIRECIONAMENTOS OK")
    else:
        print(f"RESULTADO: {falhas} rota(s) com problema")
    return 0 if falhas == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
