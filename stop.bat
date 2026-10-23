@echo off
rem ==============================================================
rem Stop the Docker service - thin launcher for "start.ps1 stop"
rem
rem IMPORTANT: keep this file ASCII-only, WITHOUT BOM.
rem   A UTF-8 BOM in a .bat gets glued to the first line, so
rem   '@echo off' fails and the script flash-exits.
rem   All Chinese output lives in start.ps1.
rem
rem start.ps1 stop first ensures .env exists and contains a strong
rem SECRET_KEY: docker compose would otherwise fail on the
rem ${SECRET_KEY:?...} interpolation even for "down".
rem ==============================================================
chcp 65001 >nul 2>&1
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File ".\start.ps1" stop
if errorlevel 1 (
    echo.
    echo [ERROR] stop failed. See the messages above.
)
echo.
timeout /t 3 /nobreak >nul
exit /b 0
