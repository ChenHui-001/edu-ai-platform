@echo off
rem ==============================================================
rem Service manager - thin launcher for "start.ps1"
rem
rem Usage:  manage.bat <start|stop|logs|status|restart|reset|rebuild> [port]
rem         manage.bat help
rem
rem IMPORTANT: keep this file ASCII-only, WITHOUT BOM.
rem   A UTF-8 BOM in a .bat gets glued to the first line, so
rem   '@echo off' fails ("not recognized as an internal or external
rem   command"). That leaves @echo off unexecuted, every line gets
rem   echoed, and the first Chinese line kills the window (flash-exit).
rem   All Chinese output therefore lives in start.ps1.
rem ==============================================================
chcp 65001 >nul 2>&1
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File ".\start.ps1" %*
if errorlevel 1 (
    echo.
    echo [ERROR] start.ps1 exited with an error. See the messages above.
)
pause