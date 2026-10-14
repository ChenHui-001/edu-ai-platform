@echo off
chcp 65001 >nul 2>&1
title 停止服务 - 九年义务教育 AI 学习管理系统

cd /d "%~dp0"

echo.
echo  正在停止服务...
echo.

docker compose down

echo.
echo  [OK] 服务已停止
echo.
echo  如需重新启动，双击 start.bat
echo.
timeout /t 5 /nobreak >nul
exit /b 0