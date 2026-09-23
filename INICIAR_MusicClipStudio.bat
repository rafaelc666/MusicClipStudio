@echo off
chcp 65001 >nul
title MusicClipStudio WEB - Iniciar
color 0B

REM ================================================================
REM  MusicClipStudio WEB - ATALHO PRINCIPAL
REM
REM  Duplo clique = liga backend + frontend e abre o Studio.
REM
REM  Os servidores sobem em DUAS JANELAS PROPIAS.
REM  DEIXE AS DUAS ABERTAS enquanto usar o programa.
REM  Fechar as janelas = desligar o programa.
REM
REM  ----------------------------------------------------------------
REM   PORTAS DEDICADAS (2026-09-20)
REM
REM   O projeto SAIU de 3000/8000. Essas são as portas padrão que
REM   TODO projeto Next/FastAPI pega, e isso já gerou conflito várias
REM   vezes nesta máquina.
REM
REM       frontend (Next.js)  ->  3100
REM       backend  (FastAPI)  ->  8300
REM
REM   Referência canônica: _utils/_portas.py
REM  ----------------------------------------------------------------
REM
REM  REGRA: se a porta estiver ocupada, este script NAO mata ninguem.
REM  Ele mostra quem esta la e PERGUNTA. Conflito de porta ja derrubou
REM  trabalho do usuario varias vezes - nao repetir isso.
REM ================================================================

set "PROJETO_RAIZ=D:\dev-projetos\MusicClipStudio"
set "FRONT_DIR=%PROJETO_RAIZ%\musicclipstudio-landing"
set "PYEXE=C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe"
set "PORT_FRONT=3100"
set "PORT_BACK=8300"
set "URL_STUDIO=http://127.0.0.1:3100/studio"

REM ----------------------------------------------------------------
REM  IMPORTANTE: limpar variaveis de proxy.
REM
REM  Se existir HTTP_PROXY/HTTPS_PROXY no ambiente, as requisicoes
REM  para 127.0.0.1 sao desviadas para o proxy, que responde
REM  "upstream connect failed" (os error 10061) e NENHUMA PAGINA
REM  CARREGA. Isso ja foi observado nesta maquina.
REM ----------------------------------------------------------------
set "HTTP_PROXY="
set "HTTPS_PROXY="
set "http_proxy="
set "https_proxy="
set "ALL_PROXY="
set "all_proxy="
set "NO_PROXY=127.0.0.1,localhost,::1"
set "no_proxy=127.0.0.1,localhost,::1"

if not exist "%PROJETO_RAIZ%\backend\app\main.py" (
    echo  [ERRO] Projeto nao encontrado: %PROJETO_RAIZ%
    pause & exit /b 1
)
if not exist "%PYEXE%" (
    echo  [ERRO] Python nao encontrado: %PYEXE%
    pause & exit /b 1
)

cd /d "%PROJETO_RAIZ%"

echo.
echo  ============================================================
echo              MusicClipStudio WEB - Iniciando
echo  ============================================================
echo    Backend : http://127.0.0.1:%PORT_BACK%
echo    Studio  : %URL_STUDIO%
echo  ============================================================
echo.

REM ================================================================
REM  BACKEND
REM ================================================================
"%PYEXE%" -c "import urllib.request,sys;urllib.request.urlopen('http://127.0.0.1:%PORT_BACK%/api/health',timeout=2);sys.exit(0)" >nul 2>&1
if not errorlevel 1 (
    echo  [1/3] Backend ja esta rodando na porta %PORT_BACK% - reaproveitando.
    goto :backend_pronto
)

REM --- A porta %PORT_BACK% esta ocupada por OUTRA coisa? ---
call :checar_porta %PORT_BACK% "BACKEND"
if "%PORTA_LIVRE%"=="0" goto :abortar

echo  [1/3] Ligando BACKEND na porta %PORT_BACK%...
start "MusicClipStudio BACKEND (nao feche)" cmd /k ^
    "title MusicClipStudio BACKEND (nao feche) && color 0B && cd /d %PROJETO_RAIZ% && set HTTP_PROXY= && set HTTPS_PROXY= && set http_proxy= && set https_proxy= && set NO_PROXY=127.0.0.1,localhost && echo. && echo  Backend rodando em http://127.0.0.1:%PORT_BACK%. NAO FECHE esta janela. && echo. && \"%PYEXE%\" -m uvicorn backend.app.main:app --host 127.0.0.1 --port %PORT_BACK%"

set "BACKEND_OK="
for /l %%i in (1,1,30) do (
    if not defined BACKEND_OK (
        "%PYEXE%" -c "import urllib.request,sys;urllib.request.urlopen('http://127.0.0.1:%PORT_BACK%/api/health',timeout=2);sys.exit(0)" >nul 2>&1 && set "BACKEND_OK=1"
        if not defined BACKEND_OK timeout /t 1 /nobreak >nul
    )
)
if defined BACKEND_OK (
    echo        Backend OK.
) else (
    echo.
    echo        [ERRO] O BACKEND NAO RESPONDEU na porta %PORT_BACK%.
    echo        Sem o backend, enviar musica NAO funciona.
    echo        Veja a janela azul "MusicClipStudio BACKEND" para o erro.
    echo.
    pause
    goto :abortar
)

:backend_pronto

REM ================================================================
REM  FRONTEND
REM ================================================================
"%PYEXE%" -c "import urllib.request,sys;urllib.request.urlopen('http://127.0.0.1:%PORT_FRONT%/studio',timeout=2);sys.exit(0)" >nul 2>&1
if not errorlevel 1 (
    echo  [2/3] Frontend ja esta rodando na porta %PORT_FRONT% - reaproveitando.
    goto :frontend_pronto
)

REM --- A porta %PORT_FRONT% esta ocupada por OUTRA coisa? ---
call :checar_porta %PORT_FRONT% "FRONTEND"
if "%PORTA_LIVRE%"=="0" goto :abortar

REM ----------------------------------------------------------------
REM  LIMPEZA DE SEGURANCA DO CACHE (.next)
REM
REM  O cache do Turbopack usa arquivos .sst (dados) + .meta (indice).
REM  Se ficar corrompido (ex.: .meta apontando para .sst que sumiu),
REM  o dev server PANICA e nao sobe ("FATAL: Turbopack error").
REM
REM  Aqui apagamos o .next INTEIRO, de uma vez, via Python
REM  (shutil.rmtree) - nunca em pedacos. E' barato: o cache se
REM  reconstroi sozinho no proximo start.
REM ----------------------------------------------------------------
echo  [2/3] Limpando cache do frontend (.next)...
"%PYEXE%" -c "import shutil,os; p=r'%FRONT_DIR%\.next'; shutil.rmtree(p,ignore_errors=True); print('  cache limpo.' if not os.path.isdir(p) else '  aviso: cache parcial')"

echo  [2/3] Ligando FRONTEND na porta %PORT_FRONT%...
start "MusicClipStudio FRONTEND (nao feche)" cmd /k ^
    "title MusicClipStudio FRONTEND (nao feche) && color 0A && cd /d %FRONT_DIR% && set HTTP_PROXY= && set HTTPS_PROXY= && set http_proxy= && set https_proxy= && set NO_PROXY=127.0.0.1,localhost && echo. && echo  Studio rodando em %URL_STUDIO%. NAO FECHE esta janela. && echo. && npx next dev --hostname 127.0.0.1 --port %PORT_FRONT%"

echo        aguardando o Studio responder (pode levar ~1 min)...
set "FRONTEND_OK="
for /l %%i in (1,1,90) do (
    if not defined FRONTEND_OK (
        "%PYEXE%" -c "import urllib.request,sys;urllib.request.urlopen('http://127.0.0.1:%PORT_FRONT%/studio',timeout=2);sys.exit(0)" >nul 2>&1 && set "FRONTEND_OK=1"
        if not defined FRONTEND_OK timeout /t 1 /nobreak >nul
    )
)
if defined FRONTEND_OK (echo        Frontend OK.) else (echo        [AVISO] Frontend nao respondeu - veja a janela verde do frontend)

:frontend_pronto

REM ================================================================
REM  NAVEGADOR
REM ================================================================
echo  [3/3] Abrindo o Studio no navegador...
start "" "%URL_STUDIO%"

echo.
echo  ============================================================
echo    PRONTO!  Studio: %URL_STUDIO%
echo.
echo    DEIXE AS DUAS JANELAS ABERTAS:
echo      - MusicClipStudio BACKEND  (azul)
echo      - MusicClipStudio FRONTEND (verde)
echo.
echo    Para desligar: feche as duas janelas.
echo    (ou use PARAR_MusicClipStudio.bat)
echo  ============================================================
echo.
timeout /t 10 /nobreak >nul
exit /b 0

REM ================================================================
REM  :checar_porta  <porta>  <rotulo>
REM
REM  Se a porta estiver OCUPADA, mostra quem esta la e PERGUNTA.
REM  Nunca mata nada sozinho. Define PORTA_LIVRE=1 ou 0.
REM ================================================================
:checar_porta
set "PORTA_LIVRE=1"
set "PID_CONFLITO="
for /f "tokens=5" %%P in ('netstat -ano ^| findstr LISTENING ^| findstr ":%~1 "') do set "PID_CONFLITO=%%P"
if not defined PID_CONFLITO exit /b 0

echo.
echo  ############################################################
echo   CONFLITO DE PORTA - %~2
echo  ############################################################
echo    A porta %~1 JA ESTA EM USO (PID %PID_CONFLITO%).
echo    Este script NAO vai encerrar nada sozinho.
echo.
echo    Escolha como continuar:
echo.
echo      [S] Parar o processo %PID_CONFLITO% e continuar
echo      [N] Nao mexer - abortar o inicio
echo      [C] Continuar mesmo assim (vai dar erro, geralmente)
echo.
set "ESCOLHA="
set /p "ESCOLHA=    Sua escolha [S/N/C]: "
echo  ############################################################
echo.

if /i "%ESCOLHA%"=="S" goto :matar_e_seguir
if /i "%ESCOLHA%"=="C" exit /b 0
echo    Nada foi alterado. Abortando.
set "PORTA_LIVRE=0"
exit /b 0

:matar_e_seguir
echo    Encerrando PID %PID_CONFLITO% (porta %~1)...
taskkill /F /PID %PID_CONFLITO% >nul 2>&1
timeout /t 2 /nobreak >nul
exit /b 0

:abortar
echo.
echo  ============================================================
echo    Inicio ABORTADO - nada foi alterado na sua maquina.
echo.
echo    Para ver quem esta ocupando as portas:
echo        "%PYEXE%" "%PROJETO_RAIZ%\\_utils\\_portas.py"
echo  ============================================================
echo.
pause
exit /b 1
