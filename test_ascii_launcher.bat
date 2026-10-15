@echo off
chcp 65001 >nul 2>&1
title Local Startup
cd /d "%~dp0"
echo Starting PowerShell launcher...
powershell -NoProfile -ExecutionPolicy Bypass -File ".\start.ps1"
pause