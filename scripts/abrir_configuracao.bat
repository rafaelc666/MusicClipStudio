@echo off
title Configuracao de APIs - Gerador de Clipes Musicais
echo.
echo ========================================
echo   Configuracao de APIs de Midia
echo   Gerador de Clipes Musicais v2
echo ========================================
echo.
echo Abrindo interface grafica...
echo.
python -m gerador_clipes_musicais --config-api
if errorlevel 1 (
    echo.
    echo Erro ao abrir configuracao.
    echo Verifique se o Python esta instalado e configurado.
    echo.
    pause
)
