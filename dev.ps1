# ==============================================================
#  本地开发模式（不经过 Docker）
#    - 后端：uvicorn app.main:app --reload --port 8000（独立窗口，热重载）
#    - 前端：vite dev server（独立窗口，端口 5173，/api 代理到 8000）
#    - 浏览器自动打开 http://localhost:5173
#
#  说明：
#    - 首次运行自动安装依赖（pip install -r requirements.txt / npm install）
#    - 首次运行自动生成 backend/.env（固定随机 SECRET_KEY、DEBUG=true），
#      避免应用 fail-closed 校验失败；同时保证 --reload 重启后登录令牌不失效
#    - 两个窗口分别承载前后端进程，关窗口或 Ctrl+C 即停止对应服务
#    - 数据库是 backend 目录下的本地 SQLite，与 Docker 容器内数据不互通
#    - 与 Docker 方式（start.bat，打包部署用）可并存，端口互不冲突
# ==============================================================
param(
    [switch]$SkipDeps   # 跳过依赖检查（确认依赖已装好时加速启动）
)

$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

function Write-Step([string]$m) { Write-Host "`n==> $m" -ForegroundColor Cyan }
function Write-Ok([string]$m)   { Write-Host "  [OK] $m" -ForegroundColor Green }
function Write-Err2([string]$m) { Write-Host "  [ERR] $m" -ForegroundColor Red }
function Wait-Enter             { Write-Host ''; Read-Host '按回车键关闭' | Out-Null }

Write-Host ''
Write-Host '======================================================' -ForegroundColor DarkCyan
Write-Host '   学习管理系统 · 本地开发模式（无 Docker）' -ForegroundColor Cyan
Write-Host '======================================================' -ForegroundColor DarkCyan

# ---------- 0. 环境检查 ----------
Write-Step '检查运行环境'

$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) { Write-Err2 '未找到 python（需 3.11+，请先安装并加入 PATH）'; Wait-Enter; exit 1 }
$pyVer = (& python --version) 2>&1
Write-Ok "Python: $pyVer"

$npm = Get-Command npm -ErrorAction SilentlyContinue
if (-not $npm) { Write-Err2 '未找到 npm（需 Node 18+，请先安装并加入 PATH）'; Wait-Enter; exit 1 }
Write-Ok "npm: $(& npm --version)"

# ---------- 1. 依赖安装（幂等：已装的包 pip 自动跳过） ----------
if (-not $SkipDeps) {
    Write-Step '同步后端依赖（backend/requirements.txt，已装的自动跳过）'
    # 不能只抽查单个包：partial 安装（如装过 uvicorn 但缺 pydantic_settings）
    # 会让检查通过而启动 500。requirements.txt 全量跑一遍是幂等的，缺啥补啥。
    #
    # 唯一例外 chromadb：其 0.5.23 钉死 chroma-hnswlib==0.7.6，而该版本
    # 没有 Windows cp312 的预编译 wheel，本机无 C++ 工具链必然编译失败。
    # rag.py 对 chromadb 是函数内懒加载 —— 本地不装只降级 RAG 语义检索
    # （与 LLM 未配置的降级路径一致），主链路完全可用。
    # Docker 镜像（Linux）仍全量安装，生产不受影响。
    $reqLocal = Join-Path $env:TEMP 'requirements-dev.txt'
    Get-Content (Join-Path $PSScriptRoot 'backend/requirements.txt') |
        Where-Object { $_ -notmatch '^\s*chromadb' } |
        Set-Content $reqLocal -Encoding UTF8
    & python -m pip install -q -r $reqLocal
    if ($LASTEXITCODE -ne 0) { Write-Err2 '后端依赖安装失败，请检查网络后重试'; Wait-Enter; exit 1 }
    Write-Ok '后端依赖就绪（chromadb 跳过，RAG 检索本地降级）'

    Write-Step '检查前端依赖（frontend/node_modules）'
    if (-not (Test-Path 'frontend/node_modules')) {
        Write-Host '    首次运行，安装前端依赖（约 1-3 分钟）...'
        Push-Location frontend
        & npm install --no-fund --no-audit
        $npmCode = $LASTEXITCODE
        Pop-Location
        if ($npmCode -ne 0) { Write-Err2 '前端依赖安装失败，请检查网络后重试'; Wait-Enter; exit 1 }
    }
    Write-Ok '前端依赖就绪'
}
else {
    Write-Ok '已按参数跳过依赖检查'
}

# ---------- 1.5 本地后端 .env ----------
# 后端配置从「工作目录 backend/ 下的 .env」读取（config.py env_file=".env"）。
# SECRET_KEY 已改为 fail-closed：DEBUG=false 且密钥弱时应用拒绝启动；
# DEBUG=true 时每次进程重启会生成临时密钥，--reload 一改代码所有登录令牌失效。
# 因此本地开发固定写入 backend/.env：随机强密钥 + DEBUG=true。
function New-DevSecret { return ([guid]::NewGuid().ToString('N')) + ([guid]::NewGuid().ToString('N')) }
function Test-DevWeakSecret {
    param([string]$Key)
    if ([string]::IsNullOrWhiteSpace($Key)) { return $true }
    $v = $Key.Trim()
    if ($v -match '^CHANGE_ME') { return $true }
    if ($v.Length -lt 32) { return $true }
    if (($v.ToCharArray() | Select-Object -Unique).Count -lt 8) { return $true }
    return $false
}
function Initialize-BackendEnv {
    $envPath = Join-Path $PSScriptRoot 'backend/.env'
    if (-not (Test-Path $envPath)) {
        $content = @(
            '# 本地开发配置（dev.ps1 自动生成；已在 .gitignore 中忽略）',
            "SECRET_KEY=$(New-DevSecret)",
            'DEBUG=true',
            'SEED_DEMO_DATA=true',
            'LOG_LEVEL=INFO'
        ) -join "`n"
        [System.IO.File]::WriteAllText(
            $envPath, $content + "`n", (New-Object System.Text.UTF8Encoding $false))
        Write-Ok '已生成 backend/.env（DEBUG=true，固定随机 SECRET_KEY）'
        return
    }
    $text = Get-Content $envPath -Raw -Encoding UTF8
    if ($null -eq $text) { $text = '' }
    $patched = $false
    $m = [regex]::Match($text, '(?m)^\s*SECRET_KEY=(.*)$')
    $key = if ($m.Success) { $m.Groups[1].Value.Trim() } else { '' }
    if (Test-DevWeakSecret $key) {
        $newKey = New-DevSecret
        if ($m.Success) {
            $text = [regex]::Replace($text, '(?m)^\s*SECRET_KEY=.*$', "SECRET_KEY=$newKey")
        } else {
            $text = $text.TrimEnd() + "`nSECRET_KEY=$newKey`n"
        }
        $patched = $true
        Write-Ok 'backend/.env：已补全随机 SECRET_KEY'
    }
    if ($text -notmatch '(?m)^\s*DEBUG=') {
        $text = $text.TrimEnd() + "`nDEBUG=true`n"; $patched = $true
    }
    if ($text -notmatch '(?m)^\s*SEED_DEMO_DATA=') {
        $text = $text.TrimEnd() + "`nSEED_DEMO_DATA=true`n"; $patched = $true
    }
    if ($patched) {
        [System.IO.File]::WriteAllText(
            $envPath, $text, (New-Object System.Text.UTF8Encoding $false))
    }
    Write-Ok 'backend/.env 已就绪（本地开发模式）'
}

# ---------- 2. 启动后端（独立窗口，热重载） ----------
Initialize-BackendEnv
Write-Step '启动后端 uvicorn（端口 8000，独立窗口，--reload 热重载）'
$backendCmd = 'chcp 65001 >nul & title backend(8000) & cd /d "' +
              (Join-Path $PSScriptRoot 'backend') +
              '" & python -m uvicorn app.main:app --reload --port 8000'
Start-Process cmd -ArgumentList "/k $backendCmd" -WindowStyle Normal

# ---------- 3. 等后端就绪再启动前端（消除启动竞态） ----------
Write-Host '    等待后端就绪（浏览器恢复的旧标签页连接时后端必须已监听，'
Write-Host '    否则 vite 代理会报启动瞬间的 ECONNREFUSED）'
$ready = $false
for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Seconds 2
    try {
        $null = Invoke-WebRequest 'http://localhost:8000/api/v1/health' -TimeoutSec 3 -UseBasicParsing
        $ready = $true; break
    } catch { Write-Host -NoNewline '.' }
}
if ($ready) { Write-Ok '后端已就绪' } else { Write-Err2 '后端 60s 内未就绪（详情看 backend 窗口日志）' }

# ---------- 4. 启动前端 vite（独立窗口） ----------
Write-Step '启动前端 vite（端口 5173，独立窗口）'
$frontendCmd = 'chcp 65001 >nul & title frontend(5173) & cd /d "' +
               (Join-Path $PSScriptRoot 'frontend') +
               '" & npm run dev'
Start-Process cmd -ArgumentList "/k $frontendCmd" -WindowStyle Normal

Start-Process 'http://localhost:5173'

Write-Host ''
Write-Ok '本地开发环境已启动：'
Write-Host '    前端  http://localhost:5173   （vite 窗口）'
Write-Host '    后端  http://localhost:8000   （uvicorn 窗口，/docs 可看接口文档）'
Write-Host ''
Write-Host '    停止：关闭对应窗口，或在窗口内 Ctrl+C'
Write-Host '    提示：改代码即时生效（后端 --reload / 前端 vite HMR）'
Write-Host '    注意：此模式数据存 backend 目录下 SQLite，与 Docker 容器数据不互通'
Write-Host ''
