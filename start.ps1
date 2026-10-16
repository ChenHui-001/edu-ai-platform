<#
    九年义务教育 AI 学习管理系统 - PowerShell 启动器

    定位：全部中文输出集中在这里。start.bat / stop.bat / manage.bat
    只做转发 —— .bat 必须保持「纯 ASCII 无 BOM」，因为 cmd 会把
    UTF-8 BOM 粘到首行命令上，导致 @echo off 失效、脚本闪退。

    用法（推荐 manage.bat，它会转发到这里）：
      manage.bat                启动（默认 8080，被占用时自动顺延）
      manage.bat stop           停止
      manage.bat logs           查看日志
      manage.bat status         查看状态
      manage.bat restart        重启
      manage.bat reset          清空数据后重启
      manage.bat help           查看全部命令

    直接调用本文件：
      .\start.ps1                启动
      .\start.ps1 8081           换端口启动
      .\start.ps1 -NoBrowser     不自动打开浏览器
      .\start.ps1 -Command stop  也可继续用 -Command 形式
#>

[CmdletBinding(PositionalBinding = $false)]
param(
    # 位置参数：直接 `.\start.ps1 stop` 时接收子命令名。
    # 注意 Port 用 [int] 会被 `stop`/`logs` 这类字符串触发类型转换错误，
    # 所以子命令必须由本参数接收，不能占Port 的位置。
    [Parameter(Position = 0)]
    [string]$Action,

    [Parameter(Position = 1)]
    [string]$ActionPort,

    [int]$Port = 8080,
    [switch]$NoBrowser,
    [ValidateSet('start', 'stop', 'logs', 'status', 'restart', 'reset', 'rebuild', 'help')]
    [string]$Command
)

$ErrorActionPreference = 'Continue'   # docker 的 stderr（如「容器不存在」）不应终止脚本
Set-Location -Path $PSScriptRoot

# 归一化子命令与端口：
#   .\start.ps1                -> start, 8080
#   .\start.ps1 8081           -> start, 8081   （纯数字视为端口）
#   .\start.ps1 stop           -> stop
#   .\start.ps1 start 8081     -> start, 8081
#   .\start.ps1 -Command stop  -> stop（保留旧写法兼容）
$ValidActions = @('start', 'up', 'stop', 'down', 'logs', 'status', 'restart', 'reset', 'rebuild', 'help')
if ($Action) {
    if ($Action -match '^\d+$') {
        # 第一个位置参数是纯数字 -> 当作端口
        $Port = [int]$Action
    } elseif ($ValidActions -contains $Action.ToLower()) {
        $Command = $Action.ToLower()
        if ($Command -eq 'up') { $Command = 'start' }   # `up` 是 `start` 的别名
    } else {
        Write-Host "未知命令: $Action" -ForegroundColor Red
        Write-Host "可用命令: $($ValidActions -join ', ')"
        Write-Host "提示: 直接传数字会被当作端口，例如 .\start.ps1 8081"
        exit 1
    }
}
if ($ActionPort -and $ActionPort -match '^\d+$') {
    $Port = [int]$ActionPort
}
if (-not $Command) { $Command = 'start' }

# 检测是否处于交互式终端：被管道重定向或被其他脚本调起时不阻塞等待
$script:NonInteractive = (
    -not [Environment]::UserInteractive -or
    ($Host.Name -eq 'ServerHost') -or
    [Console]::IsInputRedirected
)

# ---------- 彩色输出 ----------
# PowerShell 5.1 不支持 `e 转义，改用 $Host.UI.RawUI 标准色；非交互环境自动降级为空串
$script:UseColor = $script:NonInteractive -eq $false
if ($script:UseColor) {
    $script:Cyan   = "$([char]27)[96m"
    $script:Green  = "$([char]27)[92m"
    $script:Yellow = "$([char]27)[93m"
    $script:Red    = "$([char]27)[91m"
    $script:Reset  = "$([char]27)[0m"
    $script:Bold   = "$([char]27)[1m"
} else {
    $script:Cyan = $script:Green = $script:Yellow = $script:Red = $script:Reset = $script:Bold = ''
}

function Write-Step  { param($msg) Write-Host "$script:Cyan[*]$script:Reset $msg" }
function Write-Ok    { param($msg) Write-Host "$script:Green[OK]$script:Reset $msg" }
function Write-Warn  { param($msg) Write-Host "$script:Yellow[!]$script:Reset $msg" }
function Write-Err   { param($msg) Write-Host "$script:Red[X]$script:Reset $msg" }

function Write-Banner {
    Write-Host ""
    Write-Host "$script:Cyan$( '═' * 60)$script:Reset"
    Write-Host "$script:Cyan  九年义务教育 AI 学习管理系统   本地一键启动$script:Reset"
    Write-Host "$script:Cyan$( '═' * 60)$script:Reset"
    Write-Host ""
}

function Wait-Enter {
    param([string]$Text = '按 Enter 键退出...')
    # 非交互环境（管道 / CI / 被其他脚本调起）直接返回，不阻塞
    if ($script:NonInteractive) { return }
    Write-Host ''
    Write-Host $Text -ForegroundColor DarkGray
    try { [void](Read-Host) } catch { }
}

# ---------- Docker 检查 ----------
function Test-DockerReady {
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        Write-Err '未检测到 Docker'
        Write-Host ''
        Write-Host '    请先安装 Docker Desktop：https://www.docker.com/products/docker-desktop/'
        Write-Host '    安装后需重启电脑，并确保 Docker 已启动。'
        return $false
    }
    try {
        $null = docker info 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Err 'Docker 已安装但未运行'
            Write-Host ''
            Write-Host '    请双击打开 Docker Desktop，等待 whale 图标停止转动后重试。'
            return $false
        }
    } catch {
        Write-Err "Docker 状态检查失败：$_"
        return $false
    }
    return $true
}

# ---------- 端口检查 ----------
function Test-PortFree {
    param([int]$CheckPort)
    $inUse = Get-NetTCPConnection -LocalPort $CheckPort -State Listen -ErrorAction SilentlyContinue
    return (-not $inUse)
}

function Resolve-Port {
    param([int]$WantPort)
    if (Test-PortFree -CheckPort $WantPort) { return $WantPort }

    Write-Warn "端口 $WantPort 已被占用"
    Write-Host ''
    Write-Host '    可换个端口重新运行，例如：'
    Write-Host "      .\start.ps1 -Port $($WantPort + 1)"
    Write-Host ''

    for ($i = 0; $i -lt 10; $i++) {
        $alt = $WantPort + 1 + $i
        if (Test-PortFree -CheckPort $alt) {
            Write-Ok "自动改用端口 $alt"
            return $alt
        }
    }
    Write-Err '未找到可用端口'
    return 0
}

# ---------- 准备 .env ----------
function Initialize-Env {
    if (-not (Test-Path '.env')) {
        Copy-Item '.env.example' '.env' -Force
        Write-Ok '已生成 .env（默认关闭大模型，AI 走规则引擎）'
    } else {
        Write-Ok '.env 已存在'
    }

    # 修正镜像名占位符，避免构建出 your-dockerhub-username/... 这种无意义标签
    $content = Get-Content '.env' -Raw -Encoding UTF8
    $patched = $false

    if ($content -match 'DOCKERHUB_REPO=your-dockerhub-username/edu-ai-platform') {
        $content = $content -replace 'DOCKERHUB_REPO=.*', 'DOCKERHUB_REPO=edu-ai-platform'
        $patched = $true
    }

    # 端口：compose 读的是 .env 里的 HOST_PORT，必须与实际使用端口保持一致
    if ($content -match 'HOST_PORT=(\d+)') {
        if ([int]$Matches[1] -ne $script:UsePort) {
            $content = $content -replace 'HOST_PORT=\d+', "HOST_PORT=$script:UsePort"
            $patched = $true
        }
    } else {
        $content += "`nHOST_PORT=$script:UsePort"
        $patched = $true
    }

    # SECRET_KEY 仍是占位符或明显退化（如全 a）时重新生成
    $needsKey = $false
    if ($content -match 'SECRET_KEY=CHANGE_ME_IN_PRODUCTION') { $needsKey = $true }
    elseif ($content -match 'SECRET_KEY=([a-zA-Z0-9]{16,})') {
        $k = $Matches[1]
        # 单一字符重复（如 aaaa...）视为退化
        if (($k.ToCharArray() | Select-Object -Unique).Count -lt 8) { $needsKey = $true }
    }

    if ($needsKey) {
        # 用 Guid 拼接保证随机性（PS 5.1 无 RandomNumberGenerator.Fill）
        $key = ([guid]::NewGuid().ToString('N')) + ([guid]::NewGuid().ToString('N'))
        $content = $content -replace 'SECRET_KEY=.*', "SECRET_KEY=$key"
        $patched = $true
        Write-Ok '已生成随机 SECRET_KEY'
    }

    if ($patched) {
        [System.IO.File]::WriteAllText(
            (Resolve-Path '.env'), $content, (New-Object System.Text.UTF8Encoding $false))
    }
}

function Remove-StaleContainer {
    # 移除名为 edu-platform 且不带 compose 标签的残留容器。
    # compose 只管理带 com.docker.compose.* 标签的容器；
    # 之前用 `docker run` 起的同名容器会让 compose up 报
    # "container name is already in use" 而启动失败。
    $ids = @(docker ps -aq --filter 'name=^edu-platform$' 2>$null)
    if ($ids.Count -eq 0) { return }

    foreach ($cid in $ids) {
        if (-not $cid) { continue }
        $label = docker inspect -f '{{index .Config.Labels "com.docker.compose.project"}}' $cid 2>$null
        # 标签非空 = 由 compose 管理，compose down 已处理，不动它
        if ($label) { continue }
        Write-Warn "清理非 compose 管理的同名容器 $($cid.Substring(0,12))..."
        docker rm -f $cid 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) { Write-Ok '已移除残留容器' }
    }
}

# ---------- 各命令实现 ----------
function Invoke-Start {
    Write-Banner

    Write-Step '检查运行环境...'
    if (-not (Test-DockerReady)) { Wait-Enter; return }
    Write-Ok 'Docker 引擎就绪'

    Write-Step '检查端口占用...'
    $script:UsePort = Resolve-Port -WantPort $Port
    if ($script:UsePort -eq 0) { Wait-Enter; return }

    Write-Step '准备配置...'
    Initialize-Env

    docker compose down --remove-orphans 2>&1 | Out-Null
    Remove-StaleContainer

    # 镜像已存在则直接启动，不再 --build。
    # compose 的 --build 会重走整个 Dockerfile —— 其中 embedding 模型
    # 预置步骤要访问 S3/HF 镜像，国内网络下双源各等满 600s 超时
    # （一键启动卡在 #22 十几分钟就是它）。本地镜像本就是 CI/上次构建
    # 产物，版本跟随 .env 的 IMAGE_TAG；强制重建请用 manage.bat rebuild。
    # 镜像名/标签从 .env 解析（compose 的 image: 行用的就是这两个变量）
    $imgRepo = 'edu-ai-platform'
    $imgTag = 'latest'
    if (Test-Path '.env') {
        $envText = Get-Content '.env' -Raw -Encoding UTF8
        if ($envText -match '(?m)^\s*DOCKERHUB_REPO=(.+?)\s*$') { $imgRepo = $Matches[1].Trim() }
        if ($envText -match '(?m)^\s*IMAGE_TAG=(.+?)\s*$') { $imgTag = $Matches[1].Trim() }
    }
    $fullImage = "{0}:{1}" -f $imgRepo, $imgTag
    $haveImage = $false
    docker image inspect $fullImage *> $null
    if ($LASTEXITCODE -eq 0) { $haveImage = $true }

    if ($haveImage) {
        Write-Ok "本地已有镜像 $fullImage，跳过构建直接启动"
        Write-Host '    如需强制重建：manage.bat rebuild（或 .\start.ps1 -Action rebuild）'
        Write-Host ''
        docker compose up -d
    } else {
        Write-Step '首次运行，开始构建镜像（约 5-15 分钟）...'
        Write-Host '    构建完成后会自动打开浏览器。'
        Write-Host ''
        docker compose up -d --build
    }
    if ($LASTEXITCODE -ne 0) {
        Write-Err '启动失败'
        Write-Host ''
        Write-Host '    常见原因：'
        Write-Host '      - 容器名被占用：运行 .\start.ps1 -Action reset 或 docker rm -f edu-platform'
        Write-Host '      - 镜像源拉取失败：检查 Docker Desktop 的 Registry Mirrors 设置'
        Write-Host '      - 端口冲突：换端口重试 .\start.ps1 -Port 8081'
        Write-Host '      - 磁盘不足：镜像约需 3GB 空间'
        Wait-Enter
        return
    }

    Write-Step '等待服务就绪...'
    $ready = $false
    for ($i = 1; $i -le 90; $i++) {
        Start-Sleep -Seconds 2
        $elapsed = $i * 2
        Write-Host "`r    初始化中... $elapsed 秒     " -NoNewline -ForegroundColor DarkGray

        # 校验健康接口确实返回 healthy，而非仅端口可连
        $h = docker exec edu-platform curl -s --max-time 4 http://localhost/api/v1/health 2>$null
        if ($h -match '"status"\s*:\s*"healthy"') { $ready = $true; break }
    }
    Write-Host ''

    if (-not $ready) {
        Write-Warn '等待超时，容器可能仍在初始化'
        Write-Host ''
        Write-Host '    查看日志：manage.bat logs'
        Wait-Enter
        return
    }

    Write-Host ''
    Write-Host "$script:Green$( '═' * 60)$script:Reset"
    Write-Host "$script:Green  启动成功！$script:Reset"
    Write-Host "$script:Green$( '═' * 60)$script:Reset"
    Write-Host ''
    # 注意用 ${} 界定变量边界：$script:Cyanhttp 会被解析成变量名
    # Cyanhttp 而丢失 "http:" 前缀，导致输出成 //localhost:8080
    Write-Host "    系统首页    ${script:Bold}${script:Cyan}http://localhost:${script:UsePort}${script:Reset}"
    Write-Host "    接口文档    http://localhost:${script:UsePort}/docs"
    Write-Host "    健康检查    http://localhost:${script:UsePort}/api/v1/health"
    Write-Host ''
    Write-Host "  $( '─' * 52)"
    Write-Host '    默认账号'
    Write-Host ''
    Write-Host '      系统管理员   admin        / Admin@123456'
    Write-Host '      教师         teacher1     / Teacher@123'
    Write-Host '      学生         stu731       / Student@123'
    Write-Host ''
    Write-Host '    注：首次登录会强制修改密码'
    Write-Host "$script:Green$( '═' * 60)$script:Reset"
    Write-Host ''
    Write-Host '  常用命令：'
    Write-Host ''
    Write-Host '    双击 start.bat / stop.bat / manage.bat'
    Write-Host ''
    Write-Host '    manage.bat status      查看服务状态'
    Write-Host '    manage.bat logs        查看运行日志'
    Write-Host '    manage.bat stop        停止服务'
    Write-Host '    manage.bat restart     重启服务'
    Write-Host '    manage.bat help        查看全部命令'
    Write-Host ''
    Write-Host ''

    if (-not $NoBrowser) {
        Start-Process "http://localhost:$script:UsePort"
        Write-Host '    浏览器已自动打开，关闭此窗口不会停止服务。' -ForegroundColor DarkGray
    }

    Wait-Enter
}

function Invoke-Stop {
    Write-Host ''
    Write-Host '正在停止服务...' -ForegroundColor Cyan
    docker compose down
    Remove-StaleContainer
    Write-Host ''
    Write-Ok '已停止'
    Wait-Enter
}

function Invoke-Logs {
    Write-Host ''
    Write-Host '正在查看日志（按 Ctrl+C 退出）...' -ForegroundColor Cyan
    Write-Host ''
    docker compose logs -f --tail=100
}

function Invoke-Status {
    Write-Host ''
    Write-Host '════════════════ 服务状态 ════════════════' -ForegroundColor Cyan
    Write-Host ''
    docker ps --filter "name=edu-platform" --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"
    Write-Host ''
    Write-Host '════════════════ 健康检查 ════════════════' -ForegroundColor Cyan
    Write-Host ''

    # 用 docker ps 直接判断，避免 compose ps --format json 在含中文路径下解析失败
    $names = docker ps --format '{{.Names}}' 2>$null
    if (-not ($names -contains 'edu-platform')) {
        Write-Warn '服务未运行'
        Write-Host ''
        Write-Host '    启动服务：.\start.ps1'
        Write-Host ''
        Wait-Enter
        return
    }

    $health = docker exec edu-platform curl -s --max-time 5 http://localhost/api/v1/health 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host $health -ForegroundColor Green
    } else {
        Write-Warn '健康检查未通过，可能仍在启动中'
        Write-Host "    查看日志：manage.bat logs"
    }
    Write-Host ''
    Write-Host ''
    Wait-Enter
}

function Invoke-Restart {
    Write-Host ''
    Write-Step '正在重启服务...'
    docker compose restart
    Write-Step '等待后端就绪...'
    for ($i = 1; $i -le 30; $i++) {
        Start-Sleep -Seconds 2
        $h = docker exec edu-platform curl -s --max-time 4 http://localhost/api/v1/health 2>$null
        if ($h -match '"status"\s*:\s*"healthy"') {
            Write-Ok "服务已就绪（$($i * 2) 秒）"
            if (-not $NoBrowser) { Start-Process "http://localhost:$Port" }
            Wait-Enter
            return
        }
    }
    Write-Warn '服务仍未就绪'
    Write-Host '    查看日志：manage.bat logs'
    Wait-Enter
}

function Invoke-Reset {
    Write-Host ''
    Write-Host '════════════════════════════════════════════════' -ForegroundColor Red
    Write-Host '  警告：此操作会删除所有数据' -ForegroundColor Red
    Write-Host ''
    Write-Host '  用户、题库、试卷、成绩、笔记、错题本' -ForegroundColor Red
    Write-Host '  将全部恢复为初始种子状态。' -ForegroundColor Red
    Write-Host '════════════════════════════════════════════════' -ForegroundColor Red
    Write-Host ''

    $answer = Read-Host '  确认清空全部数据并重启？输入 yes 继续'
    if ($answer -ne 'yes') {
        Write-Host ''
        Write-Host '已取消。' -ForegroundColor DarkGray
        Wait-Enter
        return
    }

    Write-Host ''
    Write-Step '停止服务并删除数据卷...'
    docker compose down -v 2>&1 | Out-Null
    Remove-StaleContainer
    foreach ($dir in @('data', 'logs')) {
        if (Test-Path $dir) {
            Remove-Item $dir -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
    Write-Ok '数据已清空'
    Write-Host ''
    Invoke-Start
}

function Invoke-Help {
    Write-Host ''
    Write-Host '════════════════ 用法 ════════════════' -ForegroundColor Cyan
    Write-Host ''
    Write-Host '  manage.bat [命令] [端口]'
    Write-Host ''
    Write-Host '    (无参数)      启动服务（默认 8080，被占用时自动顺延）'
    Write-Host '    start        启动服务'
    Write-Host '    stop         停止服务'
    Write-Host '    restart      重启服务'
    Write-Host '    status       查看状态与健康检查'
    Write-Host '    logs         跟随查看日志（Ctrl+C 退出）'
    Write-Host '    reset        清空数据后以初始状态重启（不可逆）'
    Write-Host '    rebuild      无缓存重新构建镜像（耗时较长）'
    Write-Host '    help         显示本帮助'
    Write-Host ''
    Write-Host '  示例：'
    Write-Host '    manage.bat start 8081'
    Write-Host ''
    Write-Host '  常见账号：admin / Admin@123456（首次登录须改密）'
    Write-Host ''
    Wait-Enter
}

function Invoke-Rebuild {
    Write-Host ''
    Write-Step '清除缓存重新构建镜像（耗时较长）...'
    docker compose down
    Remove-StaleContainer
    docker compose build --no-cache
    if ($LASTEXITCODE -ne 0) {
        Write-Err '构建失败'
        Wait-Enter
        return
    }
    docker compose up -d
    Write-Ok '重建完成'
    Wait-Enter
}

# ---------- 主入口 ----------
switch ($Command) {
    'start'   { Invoke-Start }
    'stop'    { Invoke-Stop }
    'logs'    { Invoke-Logs }
    'status'  { Invoke-Status }
    'restart' { Invoke-Restart }
    'reset'   { Invoke-Reset }
    'rebuild' { Invoke-Rebuild }
    'help'    { Invoke-Help }
}