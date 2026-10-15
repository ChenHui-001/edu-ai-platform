@echo off
chcp 65001 >nul 2>&1
title 九年义务教育 AI 学习管理系统 - 服务管理

cd /d "%~dp0"

if "%~1"=="" goto NO_CMD
if /i "%~1"=="help"     goto USAGE
if /i "%~1"=="-h"      goto USAGE
if /i "%~1"=="--help" goto USAGE
if /i "%~1"=="start"   goto DO_START
if /i "%~1"=="up"      goto DO_START
if /i "%~1"=="logs"    goto DO_LOGS
if /i "%~1"=="stop"    goto DO_STOP
if /i "%~1"=="down"    goto DO_STOP
if /i "%~1"=="restart" goto DO_RESTART
if /i "%~1"=="status"  goto DO_STATUS
if /i "%~1"=="reset"   goto DO_RESET
if /i "%~1"=="rebuild" goto DO_REBUILD

echo 未知命令: %~1
echo.
goto USAGE


:DO_START
call "%~dp0start.bat" %~2
exit /b %errorlevel%


:DO_LOGS
echo.
echo 正在查看日志（按 Ctrl+C 退出）...
echo.
docker compose logs -f --tail=100
exit /b 0


:DO_STOP
echo.
echo 正在停止服务...
docker compose down
echo.
echo 已停止。
exit /b 0


:DO_RESTART
echo.
echo 正在重启服务...
docker compose restart
echo.
echo 重启完成，约 15 秒后可用。
echo.
timeout /t 18 /nobreak >nul
docker exec edu-platform curl -sf http://localhost/api/v1/health 2>nul
if not errorlevel 1 (
    echo [OK] 服务已就绪
    start "" "http://localhost:8080"
) else (
    echo [!] 服务仍在启动中，请稍候或运行 start.bat logs 查看日志
)
echo.
pause
exit /b 0


:DO_STATUS
echo.
echo ================ 服务状态 ================
echo.
docker compose ps
echo.
echo ================ 健康检查 ================
echo.
set PORT=8080
if not "%~2"=="" set PORT=%~2
docker exec edu-platform curl -s http://localhost/api/v1/health 2>nul
echo.
echo.
echo ==========================================
echo.
pause
exit /b 0


:DO_RESET
echo.
echo ============================================================
echo   警告：此操作会删除所有数据（用户、题库、试卷、成绩、笔记）
echo.
echo   数据库、错题本、学习记录都将恢复为初始种子状态。
echo ============================================================
echo.
set /p CONFIRM=   确认清空全部数据并重启？输入 yes 继续: 
if /i not "%CONFIRM%"=="yes" (
    echo 已取消。
    pause
    exit /b 0
)

echo.
echo 正在停止并删除数据卷...
docker compose down -v

if exist "data" (
    rmdir /s /q "data" 2>nul
)
if exist "logs" (
    rmdir /s /q "logs" 2>nul
)
echo 数据已清空。
echo.
echo 正在以初始状态重启...
call "%~dp0start.bat"
exit /b %errorlevel%


:DO_REBUILD
echo.
echo 重新构建镜像（不含缓存）...
echo.
docker compose down
docker compose build --no-cache
if errorlevel 1 (
    echo 构建失败。
    pause
    exit /b 1
)
docker compose up -d
echo.
echo 重建完成。
echo.
pause
exit /b 0


:NO_CMD
echo.
echo 请指定命令，例如：
echo.
echo   start.bat start     启动服务
echo   start.bat logs      查看日志
echo   start.bat stop      停止服务
echo.
echo 或直接双击运行（等同于 start）
echo.
pause
exit /b 0


:USAGE
echo.
echo ============================================================
echo   九年义务教育 AI 学习管理系统 - 命令行用法
echo ============================================================
echo.
echo   start.bat [命令] [端口]
echo.
echo   命令：
echo     start      启动服务（默认，推荐首次使用）
echo     stop       停止服务
echo     restart    重启服务
echo     logs       实时查看日志（Ctrl+C 退出）
echo     status     查看服务状态与健康检查
echo     reset      清空全部数据，恢复初始状态
echo     rebuild    清除缓存重新构建镜像
echo.
echo   端口：
echo     默认 8080，可用第二个参数覆盖
echo     例：start.bat start 8081
echo.
echo   快速上手：
echo     1. 双击 start.bat                 启动
echo     2. 浏览器访问 localhost:8080       使用
echo     3. start.bat logs                 看日志
echo     4. start.bat stop                 停服务
echo.
echo ============================================================
echo.
pause
exit /b 0