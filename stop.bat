@echo off
chcp 65001 >nul 2>&1
title 停止服务 - 九年义务教育 AI 学习管理系统

cd /d "%~dp0"

echo.
echo  正在停止服务...
echo.

docker compose down

REM compose 只管理带 com.docker.compose.* 标签的容器。
REM 若存在用 docker run 或旧版本脚本起的同名容器，需额外清理，
REM 否则下次 start.bat 会报 "container name is already in use"。
for /f "usebackq delims=" %%i in (`docker ps -aq --filter "name=^edu-platform$"`) do (
    set "STALE_ID=%%i"
    set "STALE_LABEL="
    for /f "usebackq delims=" %%l in (`docker inspect -f "{{index .Config.Labels \"com.docker.compose.project\"}}" !STALE_ID! 2^>nul`) do set "STALE_LABEL=%%l"
    if not defined STALE_LABEL (
        echo  清理残留容器 !STALE_ID! ...
        docker rm -f !STALE_ID! >nul 2>&1
    )
)

echo.
echo  [OK] 服务已停止
echo.
echo  如需重新启动，双击 start.bat
echo.
timeout /t 5 /nobreak >nul
exit /b 0