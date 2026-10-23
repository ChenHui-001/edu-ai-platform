@echo off
rem ==============================================================
rem Local dev launcher for "dev.ps1" (frontend + backend, NO Docker)
rem
rem IMPORTANT: keep this file ASCII-only, WITHOUT BOM.
rem   - Chinese text in a .bat must be UTF-8 with BOM, but the BOM
rem     gets glued to the first line and breaks it:
rem         '<BOM>@echo' is not recognized as a command
rem     -> @echo off never runs -> every line is echoed, and any
rem        Chinese line kills the window (flash-exit).
rem   - So all Chinese output lives in dev.ps1, which handles the
rem     BOM correctly (leading comment block absorbs it).
rem
rem What it does:
rem   - checks python / npm
rem   - installs missing dependencies (skip with -SkipDeps)
rem   - creates backend/.env on first run (fixed random SECRET_KEY,
rem     DEBUG=true) so the fail-closed config check passes and tokens
rem     survive uvicorn --reload restarts
rem   - starts backend on :8000 and frontend on :5173
rem
rem Optional args are forwarded, e.g.  dev.bat -SkipDeps
rem ==============================================================
chcp 65001 >nul 2>&1
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File ".\dev.ps1" %*
if errorlevel 1 (
    echo.
    echo [ERROR] dev.ps1 exited with an error. See the messages above.
)
pause
