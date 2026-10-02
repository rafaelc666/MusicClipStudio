#!/usr/bin/env bash
# Derruba o backend e o frontend do MusicClipStudio (equivalente ao PARAR_MusicClipStudio.bat)
pkill -f "uvicorn [b]ackend.app.main:app" 2>/dev/null && echo "[backend] parado" || echo "[backend] não estava rodando"

# Frontend: o RUN_WEB.sh sobe com `next start`, e o Next renomeia o processo
# para "next-server (v…)" — o pkill por "next dev …" nunca casa (bug 01/10).
# Mata quem quer que esteja ESCUTANDO a porta 3100: vale para dev e start.
if command -v fuser >/dev/null 2>&1; then
  fuser -k 3100/tcp 2>/dev/null && echo "[frontend] parado" || echo "[frontend] não estava rodando"
else
  pkill -f "next" 2>/dev/null && echo "[frontend] parado" || echo "[frontend] não estava rodando"
fi
exit 0
