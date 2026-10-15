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

REM ---------- 1.5 磁盘空间预检 ----------
REM 构建镜像需约 4GB。空间不足时 Docker 会大量重试/超时，
REM 表现为构建极慢甚至假性失败。
REM 查 Docker 数据所在盘（迁到数据盘后系统盘紧张也不影响构建）。
set "FREE_GB="
for /f "usebackq delims=" %%d in (`docker info --format "{{.DockerRootDir}}" 2^>nul`) do (
    echo %%d | findstr /r "^[A-Za-z]:" >nul && (
        for /f "usebackq tokens=1 delims=:" %%l in ("%%d") do set "DISK=%%l"
    )
)
if not defined DISK set "DISK=C"
for /f "usebackq delims=" %%f in (`powershell -NoProfile -Command "$d=Get-PSDrive '!DISK!' -ErrorAction SilentlyContinue; if($d){[math]::Round($d.Free/1GB,0)}"`) do set "FREE_GB=%%f"

if defined FREE_GB (
    if !FREE_GB! lss 4 (
        echo.
        echo   [!] Docker 所在盘(!DISK:)可用仅 !FREE_GB!GB，构建镜像需约 4GB
        echo.
        echo       清理命令：docker image prune -a ^& docker builder prune -a
        echo       或在 Docker Desktop 把 Disk image location 迁到数据盘
        echo.
    ) else (
        echo       [OK] Docker 所在盘(!DISK:)可用 !FREE_GB!GB
    )
) else (
    echo       [OK] 磁盘空间检测跳过
)

REM ---------- 2. 端口检查 ----------
echo.
echo [2/5] 检查端口占用...

set PORT=8080
if not "%~1"=="" set PORT=%~1

call :CheckPort %PORT%
if not errorlevel 1 goto PORT_OK

REM 端口被占用：自动向后顺延，最多试 20 个端口
echo   [!] 端口 %PORT% 已被占用，自动寻找空闲端口...
set /a TRY=0
:PORT_TRY
set /a TRY+=1
set /a NPORT=%PORT%+TRY
call :CheckPort !NPORT!
if errorlevel 1 (
    if !TRY! lss 20 goto PORT_TRY
    echo   [X] 未找到可用端口，请关闭占用程序后重试
    pause
    exit /b 1
)
set PORT=!NPORT!
echo   [OK] 自动改用端口 !PORT!

:PORT_OK
echo       [OK] 端口 !PORT! 可用

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
    for /f "delims=" %%a in ('powershell -NoProfile -Command "[guid]::NewGuid().ToString(''N'') + [guid]::NewGuid().ToString(''N'')"') do set "RKEY=%%a"
    if defined RKEY (
        powershell -NoProfile -Command "(Get-Content '.env' -Encoding UTF8) -replace 'SECRET_KEY=.*', 'SECRET_KEY=!RKEY!' | Set-Content '.env' -Encoding UTF8" >nul 2>&1
        echo       [OK] 已生成随机 SECRET_KEY
    )
)

REM 修正镜像名占位符
findstr /c:"DOCKERHUB_REPO=your-dockerhub-username" ".env" >nul 2>&1
if not errorlevel 1 (
    powershell -NoProfile -Command "(Get-Content '.env' -Encoding UTF8) -replace 'DOCKERHUB_REPO=.*', 'DOCKERHUB_REPO=edu-ai-platform' | Set-Content '.env' -Encoding UTF8" >nul 2>&1
    echo       [OK] 已修正镜像名占位符
)

call :SyncEnvPort !PORT!

REM ---------- 4. 启动服务 ----------
echo.
echo [4/5] 启动服务（首次运行需要构建镜像，约 5-15 分钟）...
echo.
docker compose down --remove-orphans >nul 2>&1

REM 清理「同名但非 compose 管理」的残留容器。
REM 常见场景：之前用 `docker run` 或本脚本旧版本起过 edu-platform，
REM 这些容器没有 com.docker.compose.* 标签，`docker compose down` 清不掉，
REM 会导致 compose up 报 "container name is already in use" 而启动失败。
call :CleanupStaleContainer

docker compose up -d --build
if errorlevel 1 (
    echo.
    echo   [X] 启动失败
    echo.
    echo   请查看上方错误信息。常见原因：
    echo     - 容器名被占用：运行 start.bat reset 或 docker rm -f edu-platform
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

REM 端口可连 != 业务就绪，必须校验健康接口返回 healthy
docker exec edu-platform curl -s --max-time 4 http://localhost/api/v1/health 2>nul | findstr /c:"healthy" >nul 2>&1
if not errorlevel 1 goto READY

if !COUNT! geq 60 (
    echo.
    echo   [!] 等待超时，容器可能仍在初始化
    echo.
    echo       查看日志：start.bat logs
    echo.
    pause
    exit /b 1
)
<nul set /p "=       初始化中... !COUNT! 秒      "
goto WAIT_LOOP

:READY
echo.
<nul set /p "=                                       "

REM ---------- 显示结果 ----------
echo.
echo  ============================================================
echo    启动成功！
echo  ============================================================
echo.
echo    系统首页    http://localhost:!PORT!
echo    接口文档    http://localhost:!PORT!/docs
echo    健康检查    http://localhost:!PORT!/api/v1/health
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
start "" "http://localhost:!PORT!"
echo  浏览器已自动打开，关闭此窗口不会停止服务。
echo.
pause
exit /b 0


REM ================================================================
REM  子程序
REM ================================================================

:CheckPort
REM 用法：call :CheckPort 8080
REM 端口被监听时返回 errorlevel 1，否则返回 0
REM 注意：findstr 不支持星号量词，改用 Get-NetTCPConnection 判断
powershell -NoProfile -Command "if (Get-NetTCPConnection -LocalPort %~1 -State Listen -ErrorAction SilentlyContinue) { exit 1 } else { exit 0 }" >nul 2>&1
exit /b %errorlevel%

:CleanupStaleContainer
REM 移除名为 edu-platform 且不带 compose 标签的残留容器。
REM 判定依据：容器存在，且其 com.docker.compose.project 标签为空。
REM 仅当容器确实存在才执行，避免每次启动都打一行 docker rm 噪音。
set "STALE_ID="
for /f "usebackq delims=" %%i in (`docker ps -aq --filter "name=^edu-platform$"`) do set "STALE_ID=%%i"
if not defined STALE_ID exit /b 0

REM 该容器已被 compose 管理 -> compose down 已经处理过了，不动它
for /f "usebackq delims=" %%l in (`docker inspect -f "{{index .Config.Labels \"com.docker.compose.project\"}}" !STALE_ID! 2^>nul`) do set "STALE_LABEL=%%l"
if defined STALE_LABEL exit /b 0

echo       [i] 清理非 compose 管理的同名容器 !STALE_ID! ...
docker rm -f !STALE_ID! >nul 2>&1
if not errorlevel 1 echo       [OK] 已移除残留容器
exit /b 0

:SyncEnvPort
REM 用法：call :SyncEnvPort 8081
REM 把实际使用的端口写入 .env 的 HOST_PORT，否则 compose 仍监听旧端口
set "SYNC_PORT=%~1"
findstr /c:"HOST_PORT=%SYNC_PORT%" ".env" >nul 2>&1
if not errorlevel 1 exit /b 0
powershell -NoProfile -Command "(Get-Content '.env' -Encoding UTF8) -replace '^HOST_PORT=.*', 'HOST_PORT=%SYNC_PORT%' | Set-Content '.env' -Encoding UTF8" >nul 2>&1
exit /b 0