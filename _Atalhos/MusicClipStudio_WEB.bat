@echo off
chcp 65001 >nul
title MusicClipStudio WEB · Iniciar Tudo
color 0B

REM ================================================================
REM  MusicClipStudio WEB · Atalho principal
REM  Copie este arquivo para sua Área de Trabalho (Desktop)
REM  Duplo clique = inicia backend + frontend + abre o Studio no navegador
REM ================================================================

REM Garantir que rodamos a partir da RAIZ do projeto MusicClipStudio,
REM não importa de onde este .bat foi chamado.
REM
REM Se o atalho estiver na Área de Trabalho (Desktop), usamos o caminho
REM fixo do projeto. Para mudar de máquina, basta editar abaixo:

set "PROJETO_RAIZ=D:\dev-projetos\MusicClipStudio"

REM ── Fallback: se arrastamos esse .bat de dentro do projeto
if not exist "%PROJETO_RAIZ%\RUN_WEB.bat" (
    REM Tenta usar a pasta deste .bat como raiz
    set "PROJETO_RAIZ=%~dp0"
)
if not exist "%PROJETO_RAIZ%\RUN_WEB.bat" (
    echo.
    echo  [ERRO] Pasta do projeto MusicClipStudio NAO encontrada.
    echo         Caminho tentado: %PROJETO_RAIZ%
    echo.
    echo         Edite este arquivo .bat e ajuste PROJETO_RAIZ para
    echo         apontar para a pasta raiz do MusicClipStudio.
    echo.
    pause
    exit /b 1
)

cd /d "%PROJETO_RAIZ%"

echo.
echo  ╔══════════════════════════════════════════════════════════╗
echo  ║         MusicClipStudio WEB · Ligando a stack            ║
echo  ╠══════════════════════════════════════════════════════════╣
echo  ║  Backend : FastAPI + engine.py + scene_engine            ║
echo  ║  Frontend: Next.js 16 (Turbopack) · Design Neon          ║
echo  ╚══════════════════════════════════════════════════════════╝
echo.

REM ── 0. Descobrir o Python CERTO ────────────────────────────────
REM  O "python" do PATH pode ser um runtime isolado sem as deps.
REM  Testamos os candidatos e usamos o primeiro que importar fastapi.
set "PYEXE="
for %%P in (
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
    "C:\Python312\python.exe"
) do (
    if not defined PYEXE if exist %%P (
        %%P -c "import fastapi, uvicorn" >nul 2>&1 && set "PYEXE=%%~P"
    )
)
if not defined PYEXE (
    python -c "import fastapi, uvicorn" >nul 2>&1 && set "PYEXE=python"
)
if not defined PYEXE (
    echo  [ERRO] Nenhum Python com FastAPI/Uvicorn encontrado.
    echo         Rode: python -m pip install -r requirements-web.txt
    echo.
    pause
    exit /b 1
)

REM ── 1. Abrir backend FastAPI em nova janela ──
start "🎵 MusicClipStudio · Backend API" /MIN cmd /k ^
    "cd /d %PROJETO_RAIZ% && title MusicClipStudio · Backend (FastAPI :8300) && color 0B && echo. && echo Backend on-line em:  http://127.0.0.1:8300/docs && echo. && %PYEXE% -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8300"

REM Esperar uns 4s para o backend subir (evita 404 no primeiro carregamento)
echo   [1/3] Ligando backend FastAPI (:8300)...
timeout /t 4 /nobreak >nul

REM ── 2. Abrir frontend Next.js em nova janela ──
echo   [2/3] Ligando frontend Next.js (:3100)...
start "🎵 MusicClipStudio · Frontend Web" cmd /k ^
    "cd /d %PROJETO_RAIZ%\musicclipstudio-landing && title MusicClipStudio · Frontend (Next :3100) && color 0A && echo. && echo Frontend on-line em: http://127.0.0.1:3100/studio && echo. && npx next dev --hostname 127.0.0.1 --port 3100"

REM Esperar um pouco mais (Turbopack demora ~5s no cold start)
timeout /t 8 /nobreak >nul

REM ── 3. Abrir navegador padrão no Studio ──
echo   [3/3] Abrindo Studio no navegador padrao...
start "" "http://127.0.0.1:3100/studio"

echo.
echo  ✔ Pronto! Se o navegador nao abriu, clique manualmente:
echo    http://127.0.0.1:3100/studio
echo.
echo  Duas janelas CMD ficaram abertas em segundo plano (minimizadas).
echo  Para FECHAR tudo, feche ambas as janelas.
echo.
timeout /t 5 /nobreak >nul
exit /b 0
