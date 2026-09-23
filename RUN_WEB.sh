#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
#  MusicClipStudio · lançador Linux (equivalente ao RUN_WEB.bat)
#  Sobe backend (8300) + frontend (3100) desanexados do terminal.
#  Uso:  ./RUN_WEB.sh        → sobe a stack
#        ./PARAR_WEB.sh      → derruba a stack
# ─────────────────────────────────────────────────────────────
set -u
cd "$(dirname "$0")"

PYTHON="./venv/bin/python"
LOG_B="/tmp/mcs_backend.log"
LOG_F="/tmp/mcs_frontend.log"

if [ ! -x "$PYTHON" ]; then
  echo "[ERRO] venv não encontrado. Rode antes:"
  echo "  python -m venv venv && ./venv/bin/pip install -r requirements-web.txt"
  exit 1
fi

# spawn desanexado (duplo-fork) — sobrevive ao fechamento do terminal
spawn() {  # spawn <log> <cmd> <args...>
  local log="$1"; shift
  python3 - "$log" "$@" <<'PYEOF' >/dev/null 2>&1 || return 1
import os, sys
log, cmd = sys.argv[1], sys.argv[2:]
pid = os.fork()
if pid == 0:
    os.setsid()
    if os.fork() == 0:
        with open(log, 'w') as f:
            os.dup2(f.fileno(), 1); os.dup2(f.fileno(), 2)
        devnull = os.open(os.devnull, os.O_RDONLY)
        os.dup2(devnull, 0)
        os.execvp(cmd[0], cmd)
    os._exit(0)
os.waitpid(pid, 0)
PYEOF
}

echo "[1/2] backend  → http://127.0.0.1:8300  (log: $LOG_B)"
spawn "$LOG_B" "$PYTHON" -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8300 || { echo "falhou"; exit 1; }

echo "[2/2] frontend → http://127.0.0.1:3100  (log: $LOG_F)"
cd musicclipstudio-landing
if [ ! -d .next ]; then
  # ⚠️ 23/09/2026: primeira execução faz o BUILD de produção uma vez
  # (`next dev` em modo desenvolvimento é lento, expõe erros internos e
  # não é adequado para uso contínuo).
  echo "   (primeira execução: compilando produção — leva 1–2 min)"
  ./node_modules/.bin/next build >/dev/null 2>&1 || { echo "falhou o build (veja npm run build)"; exit 1; }
fi
spawn "$LOG_F" ./node_modules/.bin/next start --hostname 127.0.0.1 --port 3100 || { echo "falhou"; exit 1; }
cd ..

sleep 4
curl -s --noproxy '*' -m 5 http://127.0.0.1:8300/api/health >/dev/null \
  && echo "✓ backend respondendo" || echo "⚠ backend ainda não respondeu (veja $LOG_B)"
curl -s --noproxy '*' -m 5 -o /dev/null http://127.0.0.1:3100/ \
  && echo "✓ frontend respondendo" || echo "⚠ frontend ainda compilando (aguarde ~10s; veja $LOG_F)"

echo ""
echo "Studio: http://127.0.0.1:3100/studio"
echo "Parar:  ./PARAR_WEB.sh"
