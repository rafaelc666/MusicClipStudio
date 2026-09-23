@echo off
REM ═══════════════════════════════════════════════════════════════════
REM INSTALAR.bat — MusicClipStudio (Windows)
REM Instala tudo do zero: venv, dependências, Chromium, frontend, build.
REM Uso: duplo clique OU  INSTALAR.bat  no terminal.
REM ═══════════════════════════════════════════════════════════════════
setlocal EnableDelayedExpansion
cd /d "%~dp0"

echo ════════════════════════════════════════════════
echo   MusicClipStudio · instalacao (Windows)
echo ════════════════════════════════════════════════

REM ── 1. Pre-requisitos ──────────────────────────────────────────
where python >nul 2>nul || (echo [X] Python nao encontrado - instale em python.org & goto :fim_erro)
where node    >nul 2>nul || (echo [X] Node.js nao encontrado - instale em nodejs.org (v18+) & goto :fim_erro)
where ffmpeg  >nul 2>nul || echo [!] FFmpeg nao encontrado - instale (winget install ffmpeg); o render precisa dele
echo [OK] pre-requisitos presentes

REM ── 2. venv + Python ───────────────────────────────────────────
if not exist venv\Scripts\python.exe (
  echo [..] criando venv...
  python -m venv venv || (echo [X] falhou o venv & goto :fim_erro)
)
echo [..] instalando dependencias Python (1-2 min)...
venv\Scripts\python -m pip install --quiet --upgrade pip
venv\Scripts\pip install --quiet -r requirements.txt || (echo [X] pip falhou & goto :fim_erro)
echo [OK] Python pronto

REM ── 3. Chromium do Playwright ─────────────────────────────────
echo [..] instalando Chromium do Playwright (~150 MB, so na 1a vez)...
venv\Scripts\playwright install chromium >nul 2>nul || venv\Scripts\python -m playwright install chromium
echo [OK] Chromium pronto

REM ── 4. .env base ──────────────────────────────────────────────
if not exist .env (
  copy .env.example .env >nul
  echo [OK] .env criado - edite com suas chaves OU use a etapa 01 do app
) else (
  echo [OK] .env ja existe (mantido)
)

REM ── 5. Frontend ───────────────────────────────────────────────
cd musicclipstudio-landing
if not exist node_modules (
  echo [..] npm install (2-5 min)...
  call npm install --no-audit --no-fund || (echo [X] npm falhou & goto :fim_erro)
)
echo [OK] frontend: dependencias prontas
echo [..] build de producao (1-2 min)...
call node_modules\.bin\next build || (echo [X] next build falhou & goto :fim_erro)
echo [OK] frontend: build pronto
cd ..

echo.
echo ════════════════════════════════════════════════
echo   [OK] Instalacao concluida
echo ════════════════════════════════════════════════
echo   Para usar:  RUN_WEB.bat
echo   Studio:     http://127.0.0.1:3100/studio
echo   Chaves:     edite .env OU configure na etapa 01 do app
echo ════════════════════════════════════════════════
goto :fim

:fim_erro
echo.
echo [X] Instalacao falhou - veja a mensagem acima.

:fim
pause
