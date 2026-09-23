@echo off
chcp 65001 >nul
title Instalar Atalho MusicClipStudio WEB na Desktop
color 0B

REM ================================================================
REM  Instalador de atalho — copia o lançador principal para a
REM  Área de Trabalho (Desktop) do usuário logado no Windows.
REM
REM  USO: duplo clique. Roda 1 vez só.
REM ================================================================

set "FONTE=%~dp0MusicClipStudio_WEB.bat"
set "DESKTOP=%USERPROFILE%\Desktop"
set "DESTINO=%DESKTOP%\MusicClipStudio WEB.bat"

echo.
echo  ╔══════════════════════════════════════════════════════════╗
echo  ║   MusicClipStudio WEB · Instalar atalho na Desktop       ║
echo  ╚══════════════════════════════════════════════════════════╝
echo.
echo   Fonte do atalho : %FONTE%
echo   Desktop do user : %DESKTOP%
echo   Destino final   : %DESTINO%
echo.

if not exist "%FONTE%" (
    echo   [ERRO] Arquivo fonte NAO encontrado: %FONTE%
    echo          Execute este script de DENTRO da pasta _Atalhos\.
    pause
    exit /b 1
)

if exist "%DESTINO%" (
    choice /C SN /M "   Ja existe um atalho na Desktop. Deseja SOBRESCREVER"
    if errorlevel 2 (
        echo   Ok, cancelado.
        pause
        exit /b 0
    )
)

copy /Y "%FONTE%" "%DESTINO%" >nul
if errorlevel 1 (
    echo.
    echo   [FALHA] Nao foi possivel copiar para a Desktop.
    echo   Tente executar este arquivo como ADMINISTRADOR.
    pause
    exit /b 1
)

REM Extra: criar tambem um .url (atalho Internet) somente para abrir a pagina
REM caso a stack ja esteja rodando em background
set "URL_ATALHO=%DESKTOP%\MusicClipStudio Studio (Web).url"
(
    echo [{000214A0-0000-0000-C000-000000000046}]
    echo Prop3=19,2
    echo [InternetShortcut]
    echo URL=http://127.0.0.1:3100/studio
    echo HotKey=0
    echo IconIndex=0
    echo IconFile=%SystemRoot%\system32\msedge.dll
) > "%URL_ATALHO%"

echo.
echo  ───────────────────────────────────────────────────────────
echo   ✔ Atalho COPIADO com sucesso para sua Desktop!
echo     • %DESTINO%
echo     • %URL_ATALHO%
echo  ───────────────────────────────────────────────────────────
echo.
echo   Modo de uso:
echo     1) Duplo clique em "MusicClipStudio WEB.bat"
echo        → liga backend + frontend e abre o navegador automatico
echo.
echo     2) Se a stack JA estiver rodando em background,
echo        use "MusicClipStudio Studio (Web).url" para abrir rapido.
echo.
pause
exit /b 0
