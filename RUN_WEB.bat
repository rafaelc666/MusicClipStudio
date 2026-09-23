@echo off
REM Garante que caminhos relativos funcionem mesmo ao abrir este arquivo de outra pasta.
cd /d "%~dp0"
chcp 65001 >nul
REM =================================================================
REM  MusicClipStudio WEB — Launcher
REM  Inicia Backend FastAPI (porta 8300) + Frontend Next.js (porta 3100)
REM =================================================================

title MusicClipStudio · Web Stack
color 0B

echo.
echo  ╔══════════════════════════════════════════════════════════╗
echo  ║           MusicClipStudio · Web Stack Launcher           ║
echo  ╠══════════════════════════════════════════════════════════╣
echo  ║  Backend:  FastAPI · http://127.0.0.1:8300/api/health    ║
echo  ║  Frontend: Next.js · http://127.0.0.1:3100/studio        ║
echo  ╚══════════════════════════════════════════════════════════╝
echo.

REM ── 0. Descobrir o Python CERTO ────────────────────────────────
REM  Nem sempre o "python" do PATH serve: pode ser um runtime
REM  isolado sem as dependencias. Testamos os candidatos comuns e
REM  usamos o primeiro que conseguir importar fastapi+uvicorn.
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
REM Fallback: tenta o python generico do PATH
if not defined PYEXE (
    python -c "import fastapi, uvicorn" >nul 2>&1 && set "PYEXE=python"
)

if not defined PYEXE (
    echo  [ERRO] Nenhum Python com FastAPI/Uvicorn encontrado.
    echo.
    echo         Instale as dependencias com:
    echo             python -m pip install -r requirements-web.txt
    echo.
    pause
    exit /b 1
)
echo  [0/4] Python encontrado: %PYEXE%

REM ── 1. Instalar dependências Python (backend) se necessário ──
REM IMPORTANTE: dentro de blocos IF, parênteses em comandos ECHO encerram o
REM bloco no cmd.exe. Por isso as mensagens abaixo evitam esse caractere.
if not exist "requirements-web-installed.ok" (
    echo [1/4] Instalando dependências Python: FastAPI, Uvicorn e demais pacotes...
    %PYEXE% -m pip install -r requirements-web.txt --quiet
    if errorlevel 1 (
        echo ERRO ao instalar requirements-web.txt. Verifique seu Python ou pip.
        pause
        exit /b 1
    )
    echo. > requirements-web-installed.ok
    echo       OK.
) else (
    echo [1/4] Dependências Python: marcador de instalação encontrado
)

REM ── 2. Instalar dependências NPM (frontend) se necessário ──
pushd musicclipstudio-landing
if not exist "node_modules" (
    echo.
    echo [2/4] Instalando dependências NPM: Next.js, Tailwind, shadcn e lucide...
    call npm install
    if errorlevel 1 (
        echo ERRO ao instalar node_modules. Verifique se Node.js 20 ou superior está instalado.
        popd
        pause
        exit /b 1
    )
    echo       OK.
) else (
    echo [2/4] Dependências NPM: já existentes
)
popd

REM ── 3. Iniciar Backend FastAPI em terminal separado ──
echo.
echo [3/4] Iniciando Backend FastAPI (porta 8300)...
REM Usa o executável completo do cmd para evitar uma camada extra de cmd.exe.
start "MusicClipStudio · Backend FastAPI" /d "%~dp0" "%ComSpec%" /k ^
    title MusicClipStudio · Backend FastAPI ^& ^
    color 0B ^& ^
    echo Backend em: http://127.0.0.1:8300/api/health ^& ^
    echo. ^& ^
    "%PYEXE%" -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8300

REM Espera rápida para o backend começar (opcional, só para ordem de logs).
REM O caminho completo evita que o timeout do Git Bash seja chamado por engano.
%SystemRoot%\System32\timeout.exe /t 2 /nobreak >nul

REM ── 4. Iniciar Frontend Next.js (em primeiro plano neste terminal) ──
echo.
echo [4/4] Iniciando Frontend Next.js (porta 3100)...
echo.
cd /d musicclipstudio-landing
title MusicClipStudio · Frontend Next.js
call npm run dev

pause
