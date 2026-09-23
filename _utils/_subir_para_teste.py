"""Sobe backend + frontend do MusicClipStudio para teste imediato.

Uso:
    python _utils/_subir_para_teste.py

NOTA: por rodar dentro do ambiente isolado do assistente, os processos
podem ser encerrados ao fim do turno. Para uso normal, o usuario deve
dar duplo clique em MusicClipStudio WEB.lnk na Desktop.
"""
import subprocess
import sys
import time
import urllib.request

RAIZ = r"D:\dev-projetos\MusicClipStudio"
PYEXE = r"C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe"

CMD_BACKEND = (
    f'cd /d {RAIZ} && "{PYEXE}" -m uvicorn backend.app.main:app '
    f"--host 127.0.0.1 --port 8300 > _backend.log 2>&1"
)
CMD_FRONTEND = (
    f"cd /d {RAIZ}\\musicclipstudio-landing && npx next dev "
    f"--hostname 127.0.0.1 --port 3100 > ..\\_frontend.log 2>&1"
)


def vivo(url: str, timeout: int = 2) -> bool:
    try:
        urllib.request.urlopen(url, timeout=timeout)
        return True
    except Exception:
        return False


def main() -> int:
    print("subindo backend...")
    subprocess.Popen(["cmd", "/c", "start", "/MIN", "cmd", "/c", CMD_BACKEND])
    print("subindo frontend...")
    subprocess.Popen(["cmd", "/c", "start", "/MIN", "cmd", "/c", CMD_FRONTEND])

    inicio = time.time()
    ok_b = ok_f = False
    while time.time() - inicio < 120:
        if not ok_b and vivo("http://127.0.0.1:8300/api/health"):
            ok_b = True
            print(f"  backend  OK  ({round(time.time()-inicio)}s)")
        if not ok_f and vivo("http://127.0.0.1:3100/studio"):
            ok_f = True
            print(f"  frontend OK  ({round(time.time()-inicio)}s)")
        if ok_b and ok_f:
            break
        time.sleep(2)

    print()
    print(f"backend = {ok_b} | frontend = {ok_f}")
    if ok_b and ok_f:
        print("Studio: http://127.0.0.1:3100/studio")
    return 0 if (ok_b and ok_f) else 1


if __name__ == "__main__":
    sys.exit(main())
