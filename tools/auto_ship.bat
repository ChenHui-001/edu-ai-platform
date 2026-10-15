@echo off
rem ==============================================================
rem Auto-ship pipeline - Windows entry for tools/auto_ship.sh
rem
rem Runs from Git Bash: bash tools/auto_ship.sh [options]
rem
rem IMPORTANT: keep this file ASCII-only, WITHOUT BOM.
rem   A UTF-8 BOM in a .bat gets glued to the first line, so
rem   '@echo off' fails and the script flash-exits.
rem ==============================================================
setlocal
cd /d "%~dp0\.."

where bash >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] bash not found. Please run tools/auto_ship.sh from Git Bash.
    exit /b 1
)

bash tools/auto_ship.sh %*
set "RC=%errorlevel%"

echo.
if not "%RC%"=="0" (
    echo [SHIP NOT COMPLETED] exit code %RC%
) else (
    echo [SHIP COMPLETED]
)
exit /b %RC%