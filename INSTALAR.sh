#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════
# INSTALAR.sh — MusicClipStudio (Linux/macOS)
#
# Instala tudo do zero: venv + dependências Python, Chromium do Playwright,
# dependências do frontend, build de produção e .env base.
#
# Uso:  ./INSTALAR.sh
# ═══════════════════════════════════════════════════════════════════════
set -euo pipefail
cd "$(dirname "$0")"

ok()   { printf "\033[32m✓\033[0m %s\n" "$1"; }
info() { printf "\033[36m→\033[0m %s\n" "$1"; }
falha(){ printf "\033[31m✗ %s\033[0m\n" "$1"; exit 1; }

echo "════════════════════════════════════════════════"
echo "  MusicClipStudio · instalação"
echo "════════════════════════════════════════════════"

# ── 1. Pré-requisitos ──────────────────────────────────────────
info "verificando pré-requisitos…"
command -v python3 >/dev/null || falha "Python 3 não encontrado — instale python.org"
command -v node    >/dev/null || falha "Node.js não encontrado — instale nodejs.org (v18+)"
command -v ffmpeg  >/dev/null || echo "  ⚠ FFmpeg não encontrado — instale (pacman/apt/winget ffmpeg); o render precisa dele"
ok "pré-requisitos presentes"

# ── 2. venv + Python ───────────────────────────────────────────
if [ ! -x venv/bin/python ]; then
  info "criando venv…"
  python3 -m venv venv || falha "não criou o venv"
fi
info "instalando dependências Python (1–2 min)…"
./venv/bin/pip install --quiet --upgrade pip
./venv/bin/pip install --quiet -r requirements.txt || falha "pip falhou"
ok "Python pronto"

# ── 3. Chromium do Playwright ─────────────────────────────────
info "instalando Chromium do Playwright (~150 MB, só na 1ª vez)…"
./venv/bin/playwright install chromium >/dev/null 2>&1 || \
  ./venv/bin/python -m playwright install chromium || falha "playwright install falhou"
ok "Chromium pronto"

# ── 4. .env base ───────────────────────────────────────────────
if [ ! -f .env ]; then
  cp .env.example .env
  ok ".env criado — edite depois com suas chaves (ou use a etapa 01 do app)"
else
  ok ".env já existe (mantido)"
fi

# ── 5. Frontend ────────────────────────────────────────────────
cd musicclipstudio-landing
[ -d node_modules ] || { info "npm install (2–5 min)…"; npm install --no-audit --no-fund || falha "npm install falhou"; }
ok "frontend: dependências prontas"
info "build de produção (1–2 min)…"
./node_modules/.bin/next build >/dev/null || falha "next build falhou"
ok "frontend: build pronto"
cd ..

echo
echo "════════════════════════════════════════════════"
echo "  ✅ Instalação concluída"
echo "════════════════════════════════════════════════"
echo "  Para usar:   ./RUN_WEB.sh"
echo "  Studio:      http://127.0.0.1:3100/studio"
echo "  Parar:       ./PARAR_WEB.sh"
echo "  Chaves:      edite .env OU configure na etapa 01 do app"
echo "════════════════════════════════════════════════"
