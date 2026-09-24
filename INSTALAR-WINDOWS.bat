@echo off
setlocal EnableDelayedExpansion
title MusicClipStudio - Instalador

REM ═══════════════════════════════════════════════════════════════════
REM  MusicClipStudio — INSTALADOR PARA WINDOWS 10/11
REM
REM  Uso: duplo clique neste arquivo.
REM
REM  O que ele faz:
REM    1. Pergunta ONDE instalar (padrao: %LOCALAPPDATA%\MusicClipStudio)
REM    2. Baixa Python e Node.js PORTATEIS (sem admin, sem instalar no SO)
REM    3. Copia o projeto para a pasta escolhida
REM    4. Instala dependencias (pip, npm), Chromium do Playwright e build
REM    5. Cria atalhos na Area de Trabalho e no Menu Iniciar + DESINSTALAR
REM
REM  Downloads na 1a execucao (~60 MB + dependencias). Internet necessaria.
REM  Requisito unico: winget OU navegador para obter este arquivo.
REM ═══════════════════════════════════════════════════════════════════

echo ════════════════════════════════════════════════════
echo    MusicClipStudio · Instalador para Windows
echo ════════════════════════════════════════════════════
echo.

REM ── 1. Pasta de instalacao ──────────────────────────────────────
set "PADRAO=%LOCALAPPDATA%\MusicClipStudio"
echo Onde instalar?
echo   [Enter] = padrao (%PADRAO%)
echo   ou digite o caminho completo desejado:
set /p "DESTINO=> "
if "%DESTINO%"=="" set "DESTINO=%PADRAO%"
echo.
echo Instalando em: %DESTINO%
echo.

REM ── 2. Copia o projeto (arquivos ao lado deste .bat) ───────────
set "ORIGEM=%~dp0"
if exist "%ORIGEM%backend\app\main.py" (
  echo [1/6] Copiando projeto...
  robocopy "%ORIGEM%" "%DESTINO%" /E /XD .git venv node_modules .next __pycache__ output _backup_* /NFL /NDL /NJH /NJS >nul
  if !ERRORLEVEL! GEQ 8 (echo [X] falhou ao copiar & goto :erro)
) else (
  echo [1/6] Projeto nao esta ao lado do .bat — clonando do GitHub...
  where git >nul 2>nul || (echo [X] Instale o Git de git-scm.com e rode de novo & goto :erro)
  git clone https://github.com/rafaelc666/MusicClipStudio.git "%DESTINO%" || (echo [X] clone falhou & goto :erro)
)
cd /d "%DESTINO%"
echo [OK] projeto em %DESTINO%

REM ── 3. Python portatil ─────────────────────────────────────────
echo [2/6] Python...
where python >nul 2>nul && (
  for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PYV=%%v
  echo   Python do sistema !PYV! encontrado — usando.
  set "PYEXE=python"
) || (
  echo   baixando Python portatil (~25 MB, so na 1a vez)...
  if not exist "runtime\python" (
    mkdir runtime 2>nul
    curl -L -o runtime\python.zip https://www.python.org/ftp/python/3.12.8/python-3.12.8-embed-amd64.zip || (echo [X] download falhou & goto :erro)
    tar -xf runtime\python.zip -C runtime\python 2>nul || (powershell -Command "Expand-Archive -Force runtime\python.zip runtime\python" || (echo [X] extracao falhou & goto :erro))
    del runtime\python.zip
    REM habilita pip no embeddable
    curl -L -o runtime\python\get-pip.py https://bootstrap.pypa.io/get-pip.py
    powershell -Command "(Get-Content runtime\python\python312._pth) -replace '#import site','import site' | Set-Content runtime\python\python312._pth"
  )
  set "PYEXE=%DESTINO%\runtime\python\python.exe"
  "!PYEXE!" runtime\python\get-pip.py --quiet || (echo [X] pip falhou & goto :erro)
  echo   [OK] Python portatil pronto
)
echo [OK] Python: !PYEXE!

REM ── 4. Node portatil ───────────────────────────────────────────
echo [3/6] Node.js...
where node >nul 2>nul && (
  for /f "tokens=1" %%v in ('node --version') do set NODEV=%%v
  echo   Node do sistema !NODEV! encontrado — usando.
  set "NPM=npm"
) || (
  echo   baixando Node.js portatil (~30 MB, so na 1a vez)...
  if not exist "runtime\node" (
    mkdir runtime 2>nul
    curl -L -o runtime\node.zip https://nodejs.org/dist/v22.13.1/node-v22.13.1-win-x64.zip || (echo [X] download falhou & goto :erro)
    powershell -Command "Expand-Archive -Force runtime\node.zip runtime" || (echo [X] extracao falhou & goto :erro)
    move "runtime\node-v22.13.1-win-x64" "runtime\node" >nul
    del runtime\node.zip
  )
  set "NPM=%DESTINO%\runtime\node\npm.cmd"
  echo   [OK] Node portatil pronto
)
echo [OK] npm: !NPM!

REM ── 5. Dependencias ────────────────────────────────────────────
echo [4/6] Dependencias Python (2-4 min)...
"!PYEXE!" -m pip install --quiet -r requirements.txt || (echo [X] pip falhou & goto :erro)
echo [OK] dependencias Python

echo [5/6] Frontend + Chromium (3-6 min)...
cd musicclipstudio-landing
call "!NPM!" install --no-audit --no-fund || (echo [X] npm falhou & goto :erro)
call "!NPM!" run build || (echo [X] build falhou & goto :erro)
cd ..
"!PYEXE!" -m playwright install chromium || (echo [X] chromium falhou & goto :erro)
if not exist .env copy .env.example .env >nul
echo [OK] tudo instalado

REM ── 6. Atalhos + launcher + desinstalador ──────────────────────
echo [6/6] Atalhos e launcher...

> "INICIAR-MUSICCLIP.bat" (
  @echo off
  cd /d "%%~dp0"
  start "" /min cmd /c ""!PYEXE!" -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8300"
  cd musicclipstudio-landing
  start "" /min cmd /c "call "!NPM!" run start -- --hostname 127.0.0.1 --port 3100"
  timeout /t 8 /nobreak >nul
  start http://127.0.0.1:3100/studio
)

> "PARAR-MUSICCLIP.bat" (
  @echo off
  taskkill /f /im node.exe >nul 2>nul
  for /f "tokens=5" %%p in ('netstat -aon ^| findstr :8300 ^| findstr LISTENING') do taskkill /f /pid %%p >nul 2>nul
  echo MusicClipStudio parado.
  timeout /t 2 /nobreak >nul
)

REM atalhos (Area de Trabalho + Menu Iniciar) via PowerShell
set "PS=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
set "WORK=%DESTINO%\INICIAR-MUSICCLIP.bat"
"!PS!" -NoProfile -Command ^
 "$w = New-Object -ComObject WScript.Shell; $d=[Environment]::GetFolderPath('Desktop'); $s=$w.CreateShortcut(\"$d\MusicClipStudio.lnk\"); $s.TargetPath='%WORK%'; $s.WorkingDirectory='%DESTINO%'; $s.IconLocation='%SystemRoot%\System32\ddores.dll,201'; $s.Save()" || goto :atalho_erro
set "MENU=%APPDATA%\Microsoft\Windows\Start Menu\Programs"
"!PS!" -NoProfile -Command ^
 "$w = New-Object -ComObject WScript.Shell; $s=$w.CreateShortcut('%MENU%\MusicClipStudio.lnk'); $s.TargetPath='%WORK%'; $s.WorkingDirectory='%DESTINO%'; $s.Save()" >nul 2>nul
"!PS!" -NoProfile -Command ^
 "$w = New-Object -ComObject WScript.Shell; $s=$w.CreateShortcut('%MENU%\Desinstalar MusicClipStudio.lnk'); $s.TargetPath='%DESTINO%\DESINSTALAR.bat'; $s.WorkingDirectory='%DESTINO%'; $s.Save()" >nul 2>nul
goto :atalho_ok
:atalho_erro
echo   [!] atalhos falharam (o app funciona mesmo assim — INICIAR-MUSICCLIP.bat)
:atalho_ok

> "DESINSTALAR.bat" (
  @echo off
  echo Isto vai APAGAR o MusicClipStudio desta pasta:
  echo   %DESTINO%
  echo (inclui contas e chaves salvas — backupe output\ se precisar)
  choice /c SN /m "Confirmar desinstalacao"
  if errorlevel 2 exit
  cd /d "%DESTINO%\.."
  del "%APPDATA%\Microsoft\Windows\Start Menu\Programs\MusicClipStudio.lnk" 2>nul
  del "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Desinstalar MusicClipStudio.lnk" 2>nul
  del "%USERPROFILE%\Desktop\MusicClipStudio.lnk" 2>nul
  rmdir /s /q "%DESTINO%"
  echo Desinstalado.
  pause
)

echo.
echo ════════════════════════════════════════════════════
echo   [OK] INSTALACAO CONCLUIDA
echo ════════════════════════════════════════════════════
echo   Usar:      atalho "MusicClipStudio" na Area de Trabalho
echo              (ou %DESTINO%\INICIAR-MUSICCLIP.bat)
echo   Parar:     PARAR-MUSICCLIP.bat
echo   Desinstalar: DESINSTALAR.bat (no Menu Iniciar tambem)
echo   Chaves:    etapa 01 do app OU edite %DESTINO%\.env
echo ════════════════════════════════════════════════════
choice /c SN /m "Abrir o MusicClipStudio agora"
if not errorlevel 2 start "" "%DESTINO%\INICIAR-MUSICCLIP.bat"
goto :fim

:erro
echo.
echo [X] Instalacao falhou — veja a mensagem acima e rode de novo.

:fim
pause
