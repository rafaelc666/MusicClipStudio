@echo off
chcp 65001 >nul
title MusicClipStudio - Diagnostico
color 0E

REM ================================================================
REM  MusicClipStudio WEB - DIAGNOSTICO
REM
REM  Se o programa nao abrir, rode este arquivo.
REM  Ele verifica tudo e mostra exatamente onde esta o problema.
REM ================================================================

set "PROJETO_RAIZ=D:\dev-projetos\MusicClipStudio"
set "PYEXE=C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe"

cd /d "%PROJETO_RAIZ%"

echo.
echo  ============================================================
echo           MusicClipStudio WEB - DIAGNOSTICO
echo  ============================================================
echo.

if not exist "%PYEXE%" (
    echo  [ERRO FATAL] Python nao encontrado em:
    echo      %PYEXE%
    echo.
    pause & exit /b 1
)

"%PYEXE%" _utils\_diagnostico_frontend.py

echo.
echo  ============================================================
echo   Para LIGAR o programa: MusicClipStudio WEB (na Desktop)
echo   Para DESLIGAR:         Parar MusicClipStudio (na Desktop)
echo  ============================================================
echo.
pause
exit /b 0
