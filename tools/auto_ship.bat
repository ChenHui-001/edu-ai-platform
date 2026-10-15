@echo off
REM ================================================================
REM 九年义务教育 AI 学习管理系统 —— 自动交付（Windows 入口）
REM 双击或在 Git Bash / cmd 中运行，等价于 tools/auto_ship.sh
REM ================================================================
setlocal

cd /d "%~dp0\.."

where bash >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到 bash，请使用 Git Bash 运行本脚本
    exit /b 1
)

bash tools/auto_ship.sh %*

echo.
if %errorlevel% neq 0 (
    echo [交付未完成] 退出码 %errorlevel%
) else (
    echo [交付完成]
)
pause