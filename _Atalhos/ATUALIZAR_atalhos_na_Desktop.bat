@echo off
chcp 65001 >nul
title Atualizar Atalhos MusicClipStudio WEB na Desktop
color 0B

REM ================================================================
REM  ATUALIZADOR de atalhos — copia o lancador + o .url para a
REM  Area de Trabalho, SOBRESCREVENDO sempre (sem perguntar).
REM
REM  Diferente do INSTALAR_atalho_na_Desktop.bat:
REM    - nao pergunta nada (roda em silencio)
REM    - sempre atualiza, mesmo se ja existir
REM    - pode rodar quantas vezes quiser
REM
REM  USO: duplo clique. Serve para "sincronizar" os atalhos
REM       depois de qualquer mudanca no lancador.
REM ================================================================

set "PASTA=%~dp0"
set "FONTE=%PASTA%MusicClipStudio_WEB.bat"
set "DESKTOP=%USERPROFILE%\Desktop"
set "DESTINO=%DESKTOP%\MusicClipStudio WEB.bat"
set "URL_ATALHO=%DESKTOP%\MusicClipStudio Studio (Web).url"

echo.
echo  ╔══════════════════════════════════════════════════════════╗
echo  ║  MusicClipStudio WEB · Atualizar atalhos da Desktop      ║
echo  ╚══════════════════════════════════════════════════════════╝
echo.

if not exist "%FONTE%" (
    echo   [ERRO] Lancador nao encontrado: %FONTE%
    echo          Rode este script de DENTRO da pasta _Atalhos\.
    pause
    exit /b 1
)

if not exist "%DESKTOP%" (
    echo   [ERRO] Desktop nao encontrado: %DESKTOP%
    pause
    exit /b 1
)

REM ── 1. Lancador principal ──
if exist "%DESTINO%" (
    echo   [1/2] Atualizando atalho existente...
) else (
    echo   [1/2] Criando atalho novo...
)
copy /Y "%FONTE%" "%DESTINO%" >nul
if errorlevel 1 (
    echo.
    echo   [FALHA] Nao foi possivel escrever na Desktop.
    echo          Feche o arquivo se estiver aberto e tente de novo.
    echo          Se persistir, execute como ADMINISTRADOR.
    pause
    exit /b 1
)
echo         OK  -^>  %DESTINO%

REM ── 2. Atalho de URL (abre o Studio se a stack ja estiver ligada) ──
echo   [2/2] Atualizando atalho de URL...
(
    echo [{000214A0-0000-0000-C000-000000000046}]
    echo Prop3=19,2
    echo [InternetShortcut]
    echo URL=http://127.0.0.1:3100/studio
    echo HotKey=0
    echo IconIndex=0
    echo IconFile=%SystemRoot%\system32\msedge.dll
) > "%URL_ATALHO%"
echo         OK  -^>  %URL_ATALHO%

echo.
echo  ───────────────────────────────────────────────────────────
echo   ✔ Atalhos sincronizados com a Desktop.
echo  ───────────────────────────────────────────────────────────
echo.
echo   Como usar:
echo     • "MusicClipStudio WEB.bat"           -^> liga tudo e abre o Studio
echo     • "MusicClipStudio Studio (Web).url"  -^> abre o Studio direto
echo.
timeout /t 5 /nobreak >nul
exit /b 0
