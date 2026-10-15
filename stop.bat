@echo off
rem ==============================================================
rem Stop the service - thin launcher for "start.ps1 stop"
rem
rem IMPORTANT: keep this file ASCII-only, WITHOUT BOM.
rem   A UTF-8 BOM in a .bat gets glued to the first line, so
rem   '@echo off' fails and the script flash-exits.
rem   All Chinese output lives in start.ps1.
rem ==============================================================
chcp 65001 >nul 2>&1
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File ".\start.ps1" stop
echo.
timeout /t 5 /nobreak >nul
exit /b 0