#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
#  MusicClipStudio · abrir o Studio a partir do atalho da Desktop
#  - Se a stack (backend 8300 + frontend 3100) já estiver de pé,
#    só abre o navegador.
#  - Se não estiver, sobe tudo primeiro (via RUN_WEB.sh).
# ─────────────────────────────────────────────────────────────
cd "$(dirname "$0")/.." || exit 1

if curl -s --noproxy '*' -m 3 http://127.0.0.1:8300/api/health >/dev/null 2>&1 \
   && curl -s --noproxy '*' -m 3 -o /dev/null http://127.0.0.1:3100/ 2>&1; then
  echo "[atalho] stack já está no ar — abrindo o Studio…"
else
  echo "[atalho] stack não está no ar — subindo…"
  ./RUN_WEB.sh
fi

xdg-open "http://127.0.0.1:3100/studio" >/dev/null 2>&1
