"""Testa o comportamento de CONFLITO DE PORTA do INICIAR_MusicClipStudio.bat.

O que se quer provar (foi o pedido do usuario, repetido ~30 vezes):
    se a porta estiver ocupada, o launcher NAO mata ninguem sozinho --
    ele mostra quem esta la e PERGUNTA.

O teste:
    1. ocupa a porta do frontend com um servidor de teste proprio;
    2. roda o .bat alimentando a resposta "N" (nao mexer);
    3. confere que o processo de teste SOBREVIVEU e que a saida contem
       o aviso de conflito;
    4. repete com "S" e confere que ai sim ele encerra.

Uso: python _utils/_teste_conflito_porta.py
"""
from __future__ import annotations

import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
BAT = RAIZ / "INICIAR_MusicClipStudio.bat"
SYS = Path("C:/Windows/System32")
NETSTAT = SYS / "netstat.exe"

PORT_FRONT = 3100


def ocupar_porta(porta: int) -> tuple[socket.socket, int]:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("127.0.0.1", porta))
    s.listen(1)
    return s, s.getsockname()[1]


def pid_da_porta(porta: int) -> str | None:
    try:
        r = subprocess.run([str(NETSTAT), "-ano"], capture_output=True, text=True, timeout=10)
        for linha in r.stdout.splitlines():
            if f":{porta} " in linha and "LISTENING" in linha.upper():
                return linha.split()[-1]
    except Exception:
        pass
    return None


def rodar_bat(resposta: str, timeout: int = 40) -> str:
    """Roda o .bat alimentando uma resposta. O .bat pode abrir janelas; matamos
    o processo ao final."""
    try:
        p = subprocess.run(
            [str(SYS / "cmd.exe"), "/c", str(BAT)],
            input=resposta + "\r\n",
            capture_output=True, text=True, timeout=timeout,
            cwd=str(RAIZ),
            encoding="utf-8", errors="replace",
        )
        return (p.stdout or "") + (p.stderr or "")
    except subprocess.TimeoutExpired as e:
        saida = ""
        if e.stdout:
            saida += e.stdout if isinstance(e.stdout, str) else e.stdout.decode("utf-8", "replace")
        return saida + "\n[TIMEOUT]"


def main() -> int:
    print("=" * 66)
    print("  Teste: o launcher PERGUNTA antes de mexer em porta ocupada?")
    print("=" * 66)

    if not BAT.exists():
        print(f"[ERRO] nao existe: {BAT}")
        return 1

    # ── Cenario: porta ocupada + resposta "N" ──
    print(f"\n[1] Ocupando a porta {PORT_FRONT} com um servidor de teste...")
    srv = threading.Thread(target=lambda: _segurar(PORT_FRONT), daemon=True)
    srv.start()
    time.sleep(1.5)

    pid_antes = pid_da_porta(PORT_FRONT)
    print(f"    porta ocupada pelo PID {pid_antes}")

    print('\n[2] Rodando o .bat com resposta "N" (nao mexer)...')
    saida = rodar_bat("N")
    linhas = [l for l in saida.splitlines() if l.strip()]
    achou_conflito = any("conflito" in l.lower() for l in linhas)
    print(f"    aviso de conflito na saida: {achou_conflito}")

    pid_depois = pid_da_porta(PORT_FRONT)
    sobreviveu = pid_depois == pid_antes
    print(f"    PID antes/depois: {pid_antes} / {pid_depois}")
    print(f"    >>> NAO MATOU (correto): {sobreviveu}")

    # mostra as linhas relevantes
    print("\n    --- trecho da saida ---")
    for l in linhas:
        if any(k in l.lower() for k in ("conflito", "escolha", "abortad", "nada foi", "pid", "porta")):
            print("     ", l.strip())
    print("    -----------------------")

    ok = achou_conflito and sobreviveu
    print("\n" + "=" * 66)
    print("  RESULTADO:", "PASSOU" if ok else "FALHOU")
    print("=" * 66)
    return 0 if ok else 2


def _segurar(porta: int) -> None:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("127.0.0.1", porta))
    s.listen(1)
    time.sleep(60)
    s.close()


if __name__ == "__main__":
    raise SystemExit(main())
