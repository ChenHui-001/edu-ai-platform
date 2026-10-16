@echo off
rem ==============================================================
rem Local dev launcher for "dev.ps1" (frontend + backend WITHOUT Docker)
rem
rem IMPORTANT: keep this file ASCII-only, WITHOUT BOM.
rem   - Chinese text in a .bat must be UTF-8 with BOM, but the BOM
rem     gets glued to the first line and breaks it:
rem         '<BOM>@echo' is not recognized as a command
rem     -> @echo off never runs -> every line is echoed, and any
rem        Chinese line kills the window (flash-exit).
rem   - So all Chinese output lives in dev.ps1, which handles the
rem     BOM correctly (leading comment block absorbs it).
rem   - Optional args are forwarded, e.g.  dev.bat -SkipDeps
rem ==============================================================
chcp 65001 >nul 2>&1
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File ".\dev.ps1" %*
if errorlevel 1 (
    echo.
    echo [ERROR] dev.ps1 exited with an error. See the messages above.
)
pause
