@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
title 九年义务教育 AI 学习管理系统 - 本地一键启动

cd /d "%~dp0"

echo.
echo  ============================================================
echo    九年义务教育 AI 学习管理系统   本地一键启动
echo  ============================================================
echo.

REM ---------- 1. 环境检查 ----------
echo [1/5] 检查运行环境...

where docker >nul 2>&1
if errorlevel 1 (
    echo.
    echo   [X] 未检测到 Docker
    echo.
    echo       请先安装 Docker Desktop: https://www.docker.com/products/docker-desktop/
    echo       安装后需重启电脑，并确保 Docker 已启动。
    echo.
    pause
    exit /b 1
)

docker info >nul 2>&1
if errorlevel 1 (
    echo.
    echo   [X] Docker 未运行
    echo.
    echo       请双击打开 Docker Desktop，等待 whale 图标停止转动后重试。
    echo.
    pause
    exit /b 1
)

echo       [OK] Docker 引擎就绪

REM ---------- 2. 端口检查 ----------
echo.
echo [2/5] 检查端口占用...

set PORT=8080
if not "%~1"=="" set PORT=%~1

netstat -ano | findstr /r /c:":%PORT% .*LISTENING" >nul 2>&1
if not errorlevel 1 (
    echo.
    echo   [!] 端口 %PORT% 已被占用
    echo.
    echo       方案一：换端口启动   start.bat 8081
    echo       方案二：关闭占用进程
    echo.
    set /p CHOICE=       请输入端口号（直接回车用 %PORT%，输入 c 取消）: 
    if /i "%CHOICE%"=="c" exit /b 0
    if not "%CHOICE%"=="" set PORT=%CHOICE%
    netstat -ano | findstr /r /c:":%PORT% .*LISTENING" >nul 2>&1
    if not errorlevel 1 (
        echo       [X] 端口 %PORT% 仍被占用，请换个端口。
        pause
        exit /b 1
    )
)
echo       [OK] 端口 %PORT% 可用

REM ---------- 3. 准备环境变量 ----------
echo.
echo [3/5] 准备配置...

if not exist ".env" (
    copy /y ".env.example" ".env" >nul 2>&1
    echo       [OK] 已生成 .env（默认关闭大模型，AI 走规则引擎）
) else (
    echo       [OK] .env 已存在
)

REM 生成随机 SECRET_KEY（仅当还是默认值）
findstr /c:"CHANGE_ME_IN_PRODUCTION" ".env" >nul 2>&1
if not errorlevel 1 (
    set "RKEY="
    for /f "delims=" %%a in ('powershell -NoProfile -Command "-join ([char[]](Get-Random -Maximum 62 -Count 48))"') do set "RKEY=%%a"
    if defined RKEY (
        powershell -NoProfile -Command "(Get-Content '.env' -Encoding UTF8) -replace 'CHANGE_ME_IN_PRODUCTION.*', '!RKEY!' | Set-Content '.env' -Encoding UTF8" >nul 2>&1
        echo       [OK] 已生成随机 SECRET_KEY
    )
)

REM ---------- 4. 启动服务 ----------
echo.
echo [4/5] 启动服务（首次运行需要构建镜像，约 5-15 分钟）...
echo.
docker compose down --remove-orphans >nul 2>&1
docker compose up -d --build
if errorlevel 1 (
    echo.
    echo   [X] 启动失败
    echo.
    echo   请查看上方错误信息。常见原因：
    echo     - 镜像源拉取失败：检查 Docker Desktop 的 Registry Mirrors 设置
    echo     - 端口冲突：运行 start.bat 8081 换端口
    echo     - 磁盘不足：镜像约需 3GB 空间
    echo.
    pause
    exit /b 1
)

REM ---------- 5. 等待就绪 ----------
echo.
echo [5/5] 等待服务就绪...

set /a COUNT=0
:WAIT_LOOP
set /a COUNT+=1
timeout /t 3 /nobreak >nul 2>&1

docker exec edu-platform curl -sf http://localhost/api/v1/health >nul 2>&1
if not errorlevel 1 goto READY

if %COUNT% geq 40 (
    echo.
    echo   [!] 等待超时，容器可能仍在初始化
    echo.
    echo       查看日志：start.bat logs
    echo.
    pause
    exit /b 1
)
<nul set /p "=       初始化中... %COUNT%0%%"
goto WAIT_LOOP

:READY
echo.

REM ---------- 显示结果 ----------
echo.
echo  ============================================================
echo    启动成功！
echo  ============================================================
echo.
echo    系统首页    http://localhost:%PORT%
echo    接口文档    http://localhost:%PORT%/docs
echo    健康检查    http://localhost:%PORT%/api/v1/health
echo.
echo  ------------------------------------------------------------
echo    默认账号
echo.
echo      系统管理员   admin        / Admin@123456
echo      教师         teacher1     / Teacher@123
echo      学生         stu731       / Student@123
echo.
echo    注：首次登录会强制修改密码
echo  ============================================================
echo.
echo  常用命令：
echo.
echo    start.bat logs      查看运行日志
echo    start.bat stop      停止服务
echo    start.bat restart   重启服务
echo    start.bat reset     清空数据后重启（重置为初始状态）
echo.
echo.

REM 自动打开浏览器
start "" "http://localhost:%PORT%"
echo  浏览器已自动打开，关闭此窗口不会停止服务。
echo.
pause