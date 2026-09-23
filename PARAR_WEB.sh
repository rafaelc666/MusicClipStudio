#!/usr/bin/env bash
# Derruba o backend e o frontend do MusicClipStudio (equivalente ao PARAR_MusicClipStudio.bat)
pkill -f "uvicorn [b]ackend.app.main:app" 2>/dev/null && echo "[backend] parado" || echo "[backend] não estava rodando"
pkill -f "[n]ext dev --hostname 127.0.0.1 --port 3100" 2>/dev/null && echo "[frontend] parado" || echo "[frontend] não estava rodando"
exit 0
