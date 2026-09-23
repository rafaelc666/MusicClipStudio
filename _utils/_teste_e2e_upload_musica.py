"""
Teste E2E do upload de música — NAVEGADOR REAL.

Reproduz o ambiente do usuário:
  - abre o Chromium apontando para o Studio
  - vai para a Etapa 3, escolhe um arquivo de áudio
  - verifica se a música realmente subiu (player + requisição 200)

⚠️ NÃO usa proxy. O proxy do WorkBuddy (127.0.0.1:51889) existe só no
ambiente da ferramenta; o navegador do usuário não tem proxy nenhum
(ProxyEnable=0 no registro do Windows). Configurar proxy aqui só polui o
teste com erro que o usuário nunca veria.

Uso: py _utils/_teste_e2e_upload_musica.py
"""

import io
import math
import struct
import sys
import wave
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://localhost:3100"
WAV_TMP = Path(r"D:\dev-projetos\MusicClipStudio\output\_teste_musica_e2e.wav")


def gerar_wav(caminho: Path) -> int:
    """Gera um WAV de 3 s e devolve o tamanho em bytes."""
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(caminho), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(44100)
        w.writeframes(
            b"".join(
                struct.pack("<h", int(6000 * math.sin(i / 25))) for i in range(44100 * 3)
            )
        )
    return caminho.stat().st_size


def main() -> int:
    tamanho = gerar_wav(WAV_TMP)
    print(f"WAV de teste: {WAV_TMP.name} ({tamanho} bytes)\n")

    falhas = 0
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        # ⚠️ SEM proxy — igual ao navegador do usuário.
        ctx = browser.new_context(ignore_https_errors=True)
        page = ctx.new_page()

        erros_console = []
        page.on("console", lambda m: erros_console.append(m.text) if m.type == "error" else None)

        requests_api = []
        page.on(
            "request",
            lambda r: requests_api.append(r.url) if "/api/" in r.url else None,
        )

        # guarda o status das respostas de /api para provar o 200
        respostas_api = []
        page.on(
            "response",
            lambda r: respostas_api.append((r.status, r.url))
            if "/api/" in r.url
            else None,
        )

        print("1) abrindo o wizard (/studio/new)...")
        page.goto(f"{BASE}/studio/new", wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(3000)
        print(f"   URL: {page.url}")
        print(f"   title: {page.title()}")

        print("\n2) indo para a Etapa 3 (música) pelo MENU LATERAL...")
        # Clica no item "Áudio" do menu. Antes isso levava a um 404; agora
        # deve apenas trocar a etapa, sem sair da página.
        clicou = False
        for rotulo in ["Áudio", "Audio"]:
            try:
                el = page.get_by_text(rotulo, exact=True).first
                if el.is_visible(timeout=2500):
                    el.click()
                    page.wait_for_timeout(2500)
                    clicou = True
                    break
            except Exception:
                continue

        print(f"   clicou no menu: {clicou}")
        print(f"   URL depois do clique: {page.url}")
        # o clique NÃO deve ter saído do wizard
        if "/studio/new" not in page.url:
            falhas += 1
            print("   >>> FALHA: o menu navegou para fora do wizard!")

        # confirma que a etapa 3 carregou
        tem_upload = page.locator('input[type="file"]').count() > 0
        print(f"   input de arquivo presente: {tem_upload}")

        if tem_upload:
            print("\n3) enviando o arquivo de música...")
            page.locator('input[type="file"]').first.set_input_files(str(WAV_TMP))
            page.wait_for_timeout(7000)

            # procura sinais de sucesso na tela (nome do arquivo / player)
            conteudo = page.content()
            subiu = ("_teste_musica_e2e" in conteudo) or ("musica_e2e" in conteudo)
            print(f"   nome do arquivo aparece na tela: {subiu}")

            # o player de áudio apareceu?
            players = page.locator("audio").count()
            print(f"   elementos <audio> na página: {players}")

            # alguma requisição de upload retornou 200?
            uploads_ok = [
                (st, u) for st, u in respostas_api if "/api/upload/audio" in u and st == 200
            ]
            print(f"   uploads com 200: {len(uploads_ok)}")

            if not (subiu or players or uploads_ok):
                falhas += 1
                print("   >>> FALHA: a música não apareceu como carregada")
            else:
                print("   >>> OK: a música carregou no wizard")
        else:
            falhas += 1
            print("   >>> FALHA: não achei o input de arquivo da Etapa 3")

        print("\n4) requisições /api feitas pelo navegador:")
        for u in dict.fromkeys(requests_api):
            print(f"   - {u}")
        if respostas_api:
            print("   status:")
            for st, u in respostas_api:
                print(f"   - {st} {u}")

        if erros_console:
            print("\n5) erros no console do navegador:")
            for e in erros_console[:6]:
                print(f"   - {e[:160]}")

        ctx.close()
        browser.close()

    # limpa o WAV de teste
    try:
        WAV_TMP.unlink()
    except Exception:
        pass

    print("\n" + "=" * 60)
    print("RESULTADO:", "OK — música sobe no wizard" if falhas == 0 else f"{falhas} falha(s)")
    return 0 if falhas == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
