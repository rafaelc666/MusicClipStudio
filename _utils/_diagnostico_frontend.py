"""Diagnostico completo: testa se o programa funciona quando os servidores
estao no ar, e documenta por que eles caem no ambiente do assistente.

Uso:
    python _utils/_diagnostico_frontend.py
"""
import json
import subprocess
import sys
import time
import urllib.request

RAIZ = r"D:\dev-projetos\MusicClipStudio"
PYEXE = r"C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe"
FRONT = RAIZ + r"\musicclipstudio-landing"

ROTAS_FRONT = ["/", "/studio", "/studio/new"]
APIS_BACK = ["/api/health", "/api/config", "/api/projetos", "/api/projetos-stats"]


def resp(url: str, timeout: int = 5):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, b""
    except Exception as e:
        return None, str(e).encode()


def checar_proxy():
    """Detecta proxy de ambiente - causa raiz conhecida deste projeto.

    Se HTTP_PROXY/HTTPS_PROXY estiverem definidos e no_proxy NAO cobrir o
    localhost, as requisicoes para 127.0.0.1:3100 sao desviadas para o proxy
    e voltam como "upstream connect failed" (os error 10061). O sintoma e
    pagina com ~124 bytes em vez do HTML real.
    """
    import os
    print("\n[0] PROXY DE AMBIENTE")
    encontrados = {k: os.environ.get(k) for k in
                   ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy",
                    "ALL_PROXY", "all_proxy")
                   if os.environ.get(k)}
    no_proxy = os.environ.get("no_proxy") or os.environ.get("NO_PROXY") or ""
    cobre_local = ("127.0.0.1" in no_proxy) or ("localhost" in no_proxy)
    if encontrados:
        for k, v in encontrados.items():
            print(f"    {k} = {v}")
        if cobre_local:
            print("    no_proxy cobre o localhost - OK")
        else:
            print("    [PERIGO] no_proxy NAO cobre o localhost!")
            print("             O proxy pode interceptar 127.0.0.1:3100 e")
            print("             devolver 'upstream connect failed'.")
    else:
        print("    nenhum proxy definido - OK")
    return not encontrados or cobre_local


def main() -> int:
    print("=" * 68)
    print("DIAGNOSTICO - MusicClipStudio WEB")
    print("=" * 68)

    # 0. Proxy de ambiente (causa raiz conhecida)
    checar_proxy()

    # 1. Backend ja no ar?
    print("\n[1] BACKEND (porta 8300)")
    for ep in APIS_BACK:
        st, _ = resp(f"http://127.0.0.1:8300{ep}")
        marca = "OK " if st == 200 else "---"
        print(f"    [{marca}] {st}  {ep}")

    # 2. Frontend no ar? (verifica TAMANHO, nao so status)
    print("\n[2] FRONTEND (porta 3100)")
    front_ok = False
    for rota in ROTAS_FRONT:
        st, corpo = resp(f"http://127.0.0.1:3100{rota}", timeout=15)
        n = len(corpo)
        # HTML de verdade tem milhares de bytes; erro de proxy tem ~124
        parece_proxy = n < 400 and b"upstream connect failed" in corpo
        if parece_proxy:
            marca = "PROXY"
        elif st == 200 and n > 1000:
            marca = "OK "
            front_ok = True
        else:
            marca = "---"
        print(f"    [{marca}] {st}  {rota}  ({n} bytes)")
        if parece_proxy:
            print("            ^ mensagem de erro de proxy, nao a pagina!")

    # 3. Midia real (a etapa que o usuario citou)
    print("\n[3] BUSCA DE MIDIA REAL (etapa de imagens/video)")
    try:
        req = urllib.request.Request(
            "http://127.0.0.1:8300/api/midia/buscar",
            data=json.dumps({"query": "sunset ocean", "max_results": 3}).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=40) as r:
            d = json.loads(r.read())
        itens = d.get("resultados", [])
        print(f"    OK  {len(itens)} itens encontrados")
        for it in itens[:3]:
            print(f"        - {it.get('tipo'):<5} {it.get('provider'):<8} "
                  f"{str(it.get('url_full', ''))[:46]}")
    except Exception as e:
        print(f"    ERRO: {type(e).__name__}: {e}")

    # 4. Veredito
    print("\n" + "=" * 68)
    if front_ok:
        print("VEREDITO: o programa ESTA funcionando - as paginas carregam.")
        print("          Abra: http://127.0.0.1:3100/studio")
    else:
        print("VEREDITO: o FRONTEND nao esta servindo as paginas.")
        print()
        print("  Causas possiveis, em ordem:")
        print("   1) Servidor nao esta no ar (rode MusicClipStudio WEB.lnk)")
        print("   2) PROXY interceptando o localhost - veja a secao [0] acima.")
        print("      Se houver HTTP_PROXY definido, ele desvia 127.0.0.1:3100")
        print("      e devolve 'upstream connect failed' em vez da pagina.")
        print("      O INICIAR_MusicClipStudio.bat ja limpa esses proxies.")
        print("   3) Servidor iniciado pelo assistente - ele morre ao fim do")
        print("      turno. Use o atalho da Desktop.")
    print("=" * 68)
    return 0 if front_ok else 1


if __name__ == "__main__":
    sys.exit(main())
