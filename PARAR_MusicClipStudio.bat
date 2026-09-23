@echo off
chcp 65001 >nul
title MusicClipStudio WEB - Parar
color 0C

REM ================================================================
REM  MusicClipStudio WEB - Parando os servidores do PROJETO
REM
REM  Portas DEDICADAS (ver _utils/_portas.py):
REM      frontend (Next)     ->  3100
REM      backend  (FastAPI)  ->  8300
REM
REM  ⚠️ So mexe nessas duas portas. Antes de encerrar, CONFERE se o
REM  processo e mesmo do MusicClipStudio (python/node) — se for outra
REM  coisa, avisa e NAO mata.
REM
REM  Isso importa: a versao antiga deste script matava qualquer PID
REM  nas portas 3000/8000 sem verificar de quem era.
REM ================================================================

set "PORT_FRONT=3100"
set "PORT_BACK=8300"

echo.
echo  ============================================================
echo           MusicClipStudio WEB - Parando tudo
echo  ============================================================
echo.

set "ACHOU="
call :parar %PORT_BACK%  "backend"
call :parar %PORT_FRONT% "frontend"

if not defined ACHOU (
    echo  Nada estava rodando nas portas %PORT_FRONT%/%PORT_BACK%.
) else (
    echo.
    echo  Pronto. Servidores do MusicClipStudio encerrados.
)

echo.
timeout /t 4 /nobreak >nul
exit /b 0

REM ----------------------------------------------------------------
REM  :parar <porta> <rotulo>
REM ----------------------------------------------------------------
:parar
set "PID_ALVO="
for /f "tokens=5" %%P in ('netstat -ano ^| findstr LISTENING ^| findstr ":%~1 "') do set "PID_ALVO=%%P"
if not defined PID_ALVO (
    echo  Porta %~1 (%~2): livre.
    exit /b 0
)

REM Confere se o processo e realmente do projeto (python/node).
set "E_DO_PROJETO="
for /f "tokens=1" %%N in ('tasklist /FI "PID eq %PID_ALVO%" /NH 2^>nul') do set "NOME_PROC=%%N"
echo %NOME_PROC% | findstr /i "python node" >nul && set "E_DO_PROJETO=1"

if not defined E_DO_PROJETO (
    echo.
    echo  [ATENCAO] A porta %~1 esta ocupada pelo processo:
    echo            %NOME_PROC%  ^(PID %PID_ALVO%^)
    echo            Isso NAO parece ser do MusicClipStudio.
    echo            Nada foi encerrado. Feche manualmente se quiser.
    echo.
    set "ACHOU=1"
    exit /b 0
)

echo  Encerrando %~2 (PID %PID_ALVO%, %NOME_PROC%) na porta %~1...
taskkill /F /PID %PID_ALVO% >nul 2>&1
set "ACHOU=1"
exit /b 0
