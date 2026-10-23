@echo off
rem ==============================================================
rem Local one-click launcher for "start.ps1" (Docker deployment)
rem
rem IMPORTANT: keep this file ASCII-only, WITHOUT BOM.
rem   - Chinese text in a .bat must be UTF-8 with BOM, but the BOM
rem     gets glued to the first line and breaks it:
rem         '<BOM>@echo' is not recognized as a command
rem     -> @echo off never runs -> every line is echoed, and any
rem        Chinese line kills the window (flash-exit).
rem   - So all Chinese output lives in start.ps1, which handles the
rem     BOM correctly (leading comment block absorbs it).
rem
rem What changed in v1.0.42+ (handled by start.ps1 automatically):
rem   - .env is auto-created and a strong random SECRET_KEY is
rem     generated if missing/weak (the backend now refuses to start
rem     in production with the old public placeholder key)
rem   - DEBUG / SEED_DEMO_DATA switches are appended to old .env files
rem   - the local Docker image is rebuilt automatically when its
rem     BUILD_INFO commit differs from the current git HEAD
rem   - start.bat 8081 forwards the port to start.ps1 (same as
rem     manage.bat start 8081)
rem
rem Requirements: Docker Desktop must be installed and running.
rem ==============================================================
chcp 65001 >nul 2>&1
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File ".\start.ps1" %*
if errorlevel 1 (
    echo.
    echo [ERROR] start.ps1 exited with an error. See the messages above.
)
pause
