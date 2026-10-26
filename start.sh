#!/usr/bin/env bash
# ================================================================
# 新芽学堂 · 九年义务教育 AI 学习平台 - 本地一键启动（macOS / Linux）
#
# 用法：
#   ./start.sh              启动服务
#   ./start.sh 8081         换端口启动
#   ./start.sh logs|status|stop|restart|reset|rebuild
# ================================================================

set -euo pipefail

cd "$(dirname "$0")"

C_RESET="\033[0m"; C_CYAN="\033[96m"; C_GREEN="\033[92m"
C_YELLOW="\033[93m"; C_RED="\033[91m"; C_BOLD="\033[1m"

COMMAND="${1:-start}"
WANT_PORT="${2:-8080}"
CONTAINER="edu-platform"
# 兼容 ./start.sh 8081 写法（原实现把 8081 当未知命令）
if [[ "$COMMAND" =~ ^[0-9]+$ ]]; then
  WANT_PORT="$COMMAND"
  COMMAND="start"
fi

info()  { echo -e "${C_CYAN}[*]${C_RESET} $1"; }
ok()    { echo -e "${C_GREEN}[OK]${C_RESET} $1"; }
warn()  { echo -e "${C_YELLOW}[!]${C_RESET} $1"; }
fail()  { echo -e "${C_RED}[X]${C_RESET} $1"; }

# ---------- 环境检查 ----------
check_docker() {
  if ! command -v docker >/dev/null 2>&1; then
    fail "未检测到 Docker"
    echo "    请先安装：https://docs.docker.com/get-docker/"
    exit 1
  fi
  if ! docker info >/dev/null 2>&1; then
    fail "Docker 未运行"
    echo "    请启动 Docker Desktop 或 dockerd 后重试"
    exit 1
  fi
  ok "Docker 引擎就绪"
}

# ---------- 端口检查 ----------
port_free() {
  ! (command -v lsof >/dev/null 2>&1 && lsof -iTCP:"$1" -sTCP:LISTEN -t >/dev/null 2>&1) \
    && ! (command -v ss >/dev/null 2>&1 && ss -ltn 2>/dev/null | grep -q ":$1 ")
}

resolve_port() {
  local p=$1
  if port_free "$p"; then echo "$p"; return; fi
  warn "端口 $p 已被占用，自动寻找下一个空闲端口..."
  for i in $(seq 1 20); do
    local alt=$((p + i))
    if port_free "$alt"; then ok "改用端口 $alt"; echo "$alt"; return; fi
  done
  fail "未找到可用端口"
  exit 1
}

# ---------- 准备 .env ----------
gen_secret() {
  if command -v openssl >/dev/null 2>&1; then
    openssl rand -hex 32
  else
    head -c 64 /dev/urandom | od -An -tx1 | tr -d ' \n'
  fi
}

set_env_value() {
  local key=$1 value=$2
  if grep -qE "^\s*${key}=" .env; then
    sed -i.bak "s|^\s*${key}=.*|${key}=${value}|" .env && rm -f .env.bak
  else
    printf '\n%s=%s\n' "$key" "$value" >> .env
  fi
}

is_weak_secret() {
  local key=${1:-}
  [ -z "$key" ] && return 0
  [[ "$key" == CHANGE_ME* ]] && return 0
  [ "${#key}" -lt 32 ] && return 0
  local uniq
  uniq=$(printf '%s' "$key" | fold -w1 | sort -u | wc -l | tr -d ' ')
  [ "$uniq" -lt 8 ] && return 0
  return 1
}

# 所有会调用 docker compose 的子命令都必须先跑本函数：
# compose 的 ${SECRET_KEY:?...} 在变量为空时会让 down/logs/status 也直接失败。
ensure_env() {
  if [ ! -f .env ]; then
    cp .env.example .env
    ok "已从 .env.example 生成 .env"
  fi

  # 修正镜像名占位符
  if grep -q "DOCKERHUB_REPO=your-dockerhub-username" .env; then
    sed -i.bak 's|^DOCKERHUB_REPO=.*|DOCKERHUB_REPO=edu-ai-platform|' .env && rm -f .env.bak
  fi

  # SECRET_KEY：空 / 占位符 / 过短 / 单字符重复 → 重新生成（应用已 fail-closed）
  local key
  key=$(grep -E '^SECRET_KEY=' .env | head -n1 | cut -d= -f2- || true)
  if is_weak_secret "$key"; then
    set_env_value SECRET_KEY "$(gen_secret)"
    ok "已生成随机 SECRET_KEY（至少 32 位）"
  fi

  # 新版本开关：旧 .env 缺失时补默认值
  grep -qE '^DEBUG=' .env || echo "DEBUG=false" >> .env
  grep -qE '^SEED_DEMO_DATA=' .env || echo "SEED_DEMO_DATA=true" >> .env
}

init_env() {
  local port=$1
  ensure_env

  # 写入实际端口
  if grep -q "^HOST_PORT=" .env; then
    sed -i.bak "s|^HOST_PORT=.*|HOST_PORT=$port|" .env && rm -f .env.bak
  else
    echo "HOST_PORT=$port" >> .env
  fi
  ok ".env 已就绪（端口 $port）"
}

# ---------- 各命令 ----------
do_start() {
  echo ""
  echo -e "${C_CYAN}$(printf '═%.0s' {1..60})${C_RESET}"
  echo -e "${C_CYAN}  新芽学堂 · 九年义务教育 AI 学习平台   本地一键启动${C_RESET}"
  echo -e "${C_CYAN}$(printf '═%.0s' {1..60})${C_RESET}"
  echo ""

  info "检查运行环境..."
  check_docker

  info "检查端口占用..."
  local port
  port=$(resolve_port "$WANT_PORT")

  info "准备配置..."
  init_env "$port"

  info "启动服务（首次运行需构建镜像，约 5-15 分钟）..."
  # 构建指纹：compose 的 build.args 读取这两个变量，写入镜像 /app/BUILD_INFO。
  # 本地「改了代码但仍在跑旧镜像」的问题可通过该 commit 对比排查。
  export GIT_COMMIT="$(git rev-parse HEAD 2>/dev/null || echo unknown)"
  export BUILD_TIME="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  docker compose down --remove-orphans >/dev/null 2>&1 || true
  if ! docker compose up -d --build; then
    echo ""
    fail "启动失败"
    echo "    常见原因：镜像源拉取失败 / 端口冲突 / 磁盘不足"
    exit 1
  fi

  info "等待服务就绪..."
  local ready=0
  for i in $(seq 1 90); do
    sleep 2
    printf "\r    初始化中... %d 秒     " $((i * 2))
    if docker exec "$CONTAINER" curl -s --max-time 4 \
        http://localhost/api/v1/health 2>/dev/null | grep -q '"status":"healthy"'; then
      ready=1
      break
    fi
  done
  echo ""

  if [ "$ready" -ne 1 ]; then
    echo ""
    warn "等待超时，容器可能仍在初始化"
    echo "    查看日志：./start.sh logs"
    exit 1
  fi

  echo ""
  echo -e "${C_GREEN}$(printf '═%.0s' {1..60})${C_RESET}"
  echo -e "${C_GREEN}  启动成功！${C_RESET}"
  echo -e "${C_GREEN}$(printf '═%.0s' {1..60})${C_RESET}"
  echo ""
  echo "    系统首页    ${C_BOLD}${C_CYAN}http://localhost:$port${C_RESET}"
  echo "    接口文档    http://localhost:$port/docs"
  echo "    健康检查    http://localhost:$port/api/v1/health"
  echo ""
  echo "  $(printf '─%.0s' {1..52})"
  if [ "$(grep -E '^SEED_DEMO_DATA=' .env | head -n1 | cut -d= -f2- || true)" = "false" ]; then
    echo "    演示账号已关闭（SEED_DEMO_DATA=false）"
    echo "    请使用初始化时的 admin 账号登录，或走注册审批流程"
  else
    echo "    默认账号"
    echo ""
    echo "      系统管理员   admin        / Admin@123456"
    echo "      教师         teacher1     / Teacher@123"
    echo "      学生         stu731       / Student@123"
  fi
  echo ""
  echo "    注：默认口令仅用于首次初始化，请登录后立即修改；"
  echo "        生产环境请设置 SEED_DEMO_DATA=false 关闭演示账号。"
  echo "        SECRET_KEY 已自动生成并写入 .env（请勿泄露/提交）。"
  echo -e "${C_GREEN}$(printf '═%.0s' {1..60})${C_RESET}"
  echo ""
  echo "  常用命令："
  echo ""
  echo "    ./start.sh logs      查看运行日志"
  echo "    ./start.sh stop      停止服务"
  echo "    ./start.sh restart   重启服务"
  echo "    ./start.sh reset     清空数据后重启"
  echo ""

  if command -v xdg-open >/dev/null 2>&1; then
    xdg-open "http://localhost:$port" >/dev/null 2>&1 || true
  elif command -v open >/dev/null 2>&1; then
    open "http://localhost:$port"
  fi
  echo "  浏览器已自动打开。"
  echo ""
}

case "$COMMAND" in
  start|"")
    do_start
    ;;
  logs)
    echo ""
    info "查看日志（Ctrl+C 退出）..."
    ensure_env
    docker compose logs -f --tail=100
    ;;
  stop|down)
    echo ""
    info "正在停止服务..."
    ensure_env
    docker compose down
    ok "已停止"
    ;;
  restart)
    echo ""
    info "正在重启服务..."
    ensure_env
    docker compose restart
    for i in $(seq 1 30); do
      sleep 2
      if docker exec "$CONTAINER" curl -s --max-time 4 \
          http://localhost/api/v1/health 2>/dev/null | grep -q '"status":"healthy"'; then
        ok "服务已就绪（$((i * 2)) 秒）"
        exit 0
      fi
    done
    warn "服务仍未就绪，查看日志：./start.sh logs"
    exit 1
    ;;
  status)
    echo ""
    echo -e "${C_CYAN}════════════════ 服务状态 ════════════════${C_RESET}"
    ensure_env
    docker compose ps
    echo ""
    echo -e "${C_CYAN}════════════════ 健康检查 ════════════════${C_RESET}"
    if docker ps --format '{{.Names}}' | grep -q "^$CONTAINER$"; then
      docker exec "$CONTAINER" curl -s --max-time 5 http://localhost/api/v1/health
      echo ""
    else
      warn "服务未运行（启动：./start.sh）"
    fi
    echo ""
    ;;
  reset)
    echo ""
    echo -e "${C_RED}════════════════════════════════════════════════${C_RESET}"
    echo -e "${C_RED}  警告：此操作会删除所有数据${C_RESET}"
    echo -e "${C_RED}  用户、题库、试卷、成绩、笔记、错题本将恢复初始状态${C_RESET}"
    echo -e "${C_RED}════════════════════════════════════════════════${C_RESET}"
    echo ""
    read -r -p "  确认清空全部数据并重启？输入 yes 继续: " ans
    if [ "$ans" != "yes" ]; then
      echo "已取消。"
      exit 0
    fi
    docker compose down -v >/dev/null 2>&1 || true
    rm -rf data logs
    ok "数据已清空"
    do_start
    ;;
  rebuild)
    echo ""
    info "清除缓存重新构建镜像（耗时较长）..."
    ensure_env
    export GIT_COMMIT="$(git rev-parse HEAD 2>/dev/null || echo unknown)"
    export BUILD_TIME="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    docker compose down
    docker compose build --no-cache
    docker compose up -d
    ok "重建完成"
    ;;
  help|-h|--help)
    echo ""
    echo "  用法：./start.sh [命令] [端口]"
    echo ""
    echo "  命令："
    echo "    start      启动服务（默认）"
    echo "    logs       实时查看日志"
    echo "    status     查看服务状态"
    echo "    stop       停止服务"
    echo "    restart    重启服务"
    echo "    reset      清空全部数据，恢复初始状态"
    echo "    rebuild    清除缓存重新构建镜像"
    echo ""
    echo "  例：./start.sh start 8081 或 ./start.sh 8081"
    echo ""
    echo "  注意：首次启动会自动生成 .env 与随机 SECRET_KEY；"
    echo "        生产部署请设置 SEED_DEMO_DATA=false 关闭演示账号。"
    echo ""
    ;;
  *)
    fail "未知命令: $COMMAND"
    echo "    可用命令：start / logs / status / stop / restart / reset / rebuild"
    exit 1
    ;;
esac