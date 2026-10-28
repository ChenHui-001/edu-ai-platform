#!/usr/bin/env bash
# ================================================================
# 统一 e2e 回归入口 —— 手动调试也用这个，不要直接跑 run_all.py
#
# 为什么必须统一入口：本地反复翻车的三个原因都出在"手动起环境"上
#   1) 两个 run_all.py 同时跑，共用同一个 SQLite，互相踩数据 →
#      同一用例名出现两次（一 PASS 一 FAIL）、日志半截中文、莫名 422
#   2) TaskStop / Ctrl+C 只杀包装层，python 子进程存活并长期占写锁 →
#      后续进程写操作被无限阻塞（曾误判为 toggle 接口死锁，卡 15 小时）
#   3) 直接打开发库 → 用例残留污染下一轮（[E2E-RS-] 年级/班级）
#
# 本脚本保证：
#   - 运行前检查残留进程，有则拒绝启动
#   - 每次 mktemp -d 独立数据目录，绝不碰开发库
#   - 自动选空闲端口，跑完清理进程与临时目录
#   - 透传阶段参数给 run_all.py（支持增量）
#
# 用法：
#   bash tools/run_e2e.sh                      # 全量
#   bash tools/run_e2e.sh admin                # 只跑管理员
#   bash tools/run_e2e.sh admin teacher        # 多阶段
#   bash tools/run_e2e.sh --keep               # 保留临时目录便于排查
#
# 本脚本直连 uvicorn（不经 nginx），因此会传 E2E_DIRECT=1 给用例：
# 「X-Real-IP 优先 / 异地登录告警」这类依赖客户端自带头的用例只有直连
# 拓扑下才造得出来；CI 走 nginx 反代，这些头会被覆盖，用例会改判反例。
# 详见 tests/test_unit_ip_login.py 与 test_admin.py 里的拓扑说明。
#
# 退出码：同 run_all.py（0 通过 / 1 失败）
# ================================================================
set -uo pipefail

cd "$(dirname "$0")/.."
ROOT="$(pwd)"

KEEP=0
STAGES=()
for arg in "$@"; do
  case "$arg" in
    --keep) KEEP=1 ;;
    -h|--help) sed -n '2,30p' "$0"; exit 0 ;;
    *) STAGES+=("$arg") ;;
  esac
done

c_reset=$'\033[0m'; c_ok=$'\033[92m'; c_err=$'\033[91m'; c_warn=$'\033[93m'; c_info=$'\033[96m'
step() { echo ""; echo "${c_info}▶ $*${c_reset}"; }
ok()   { echo "  ${c_ok}✔${c_reset} $*"; }
die()  { echo "  ${c_err}✘${c_reset} $*"; exit "$1"; }

# ---------- 解释器 ----------
PY="${PYTHON_BIN:-}"
if [ -z "$PY" ] || ! command -v "$PY" >/dev/null 2>&1; then
  for cand in "python3" "python"; do
    if command -v "$cand" >/dev/null 2>&1; then PY="$cand"; break; fi
  done
fi
[ -n "$PY" ] || die 1 "未找到 python 解释器（可用 PYTHON_BIN 指定）"

# ---------- 1. 残留进程检查（最关键的一步）----------
# 注意：`Get-Process` 只查进程名，必须看 CommandLine 才能分辨是 uvicorn
# 还是 run_all —— 两者都叫 python。
step "1/6  检查残留回归进程"
RESIDUAL=""
if command -v powershell >/dev/null 2>&1; then
  RESIDUAL="$(powershell -NoProfile -Command \
    "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object { \$_.CommandLine -like '*run_all.py*' } | ForEach-Object { \$_.ProcessId }" \
    2>/dev/null | tr -d '\r' | tr '\n' ' ')"
fi
if [ -n "$(echo "$RESIDUAL" | tr -d ' ')" ]; then
  echo "  发现残留 run_all.py 进程: $RESIDUAL"
  echo "  ${c_warn}它们可能持有数据库写锁，继续跑会互相踩数据。${c_reset}"
  if command -v powershell >/dev/null 2>&1; then
    for pid in $RESIDUAL; do
      powershell -NoProfile -Command "Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue" 2>/dev/null || true
    done
    sleep 2
    ok "已清理残留进程"
  else
    die 1 "请手动结束这些进程后重试"
  fi
else
  ok "无残留进程"
fi

# ---------- 2. 独立数据目录 ----------
step "2/6  离线单元回归（真实 IP 取值 / 异地登录判定）"
# 不吃端口、不建正式库、不依赖 nginx：纯函数与纯服务层的精确断言。
# 这类断言放在这里而不是 e2e 里，是因为反代拓扑下头的值会被覆盖，
# e2e 只能断言「伪造值未入库」这个较弱但拓扑无关的性质。
"$PY" tests/test_unit_ip_login.py || die 1 "离线单元回归未通过"

# ---------- 3. 独立数据目录 ----------
step "3/6  准备独立数据目录"
DATA_DIR="$(mktemp -d 2>/dev/null || echo "/tmp/e2e_data_$$")"
# Windows 路径给 SQLite 与 uvicorn 用，需要反斜杠格式
case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*)
    DATA_WIN="$(cygpath -w "$DATA_DIR")"
    DB_URL="sqlite:///${DATA_WIN//\\//}/e2e.db"
    ;;
  *)
    DB_URL="sqlite:///${DATA_DIR}/e2e.db"
    ;;
esac
ok "数据目录: $DATA_DIR"

# ---------- 3. 选空闲端口并启动后端 ----------
step "4/6  启动被测服务"
PORT="${E2E_PORT:-}"
if [ -z "$PORT" ]; then
  for p in 8001 8002 8003 8004 8005 8006 8007 8008 8009 8010; do
    if ! (echo > "/dev/tcp/127.0.0.1/$p") >/dev/null 2>&1; then PORT="$p"; break; fi
  done
fi
[ -n "$PORT" ] || die 1 "8001-8010 均被占用，请用 E2E_PORT 指定"
ok "端口: $PORT"

SERVER_LOG="/tmp/e2e_server_$$.log"
# SCHEDULER_ENABLED=false 与 CI 保持一致：回归不应依赖定时触发，
# 否则「本地开、CI 关」会造成两边行为不一致（另一类"本地绿 CI 红"）。
(
  cd backend && \
  DATABASE_URL="$DB_URL" LLM_ENABLED=false SCHEDULER_ENABLED=false \
  SECRET_KEY="e2e_local_only_not_for_prod_$$" \
  "$PY" -m uvicorn app.main:app --host 127.0.0.1 --port "$PORT" \
  > "$SERVER_LOG" 2>&1
) &
SERVER_PID=$!

cleanup() {
  [ -n "${SERVER_PID:-}" ] && kill "$SERVER_PID" 2>/dev/null
  # uvicorn 会 fork 子进程，按命令行兜底再杀一次
  if command -v powershell >/dev/null 2>&1; then
    powershell -NoProfile -Command \
      "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object { \$_.CommandLine -like '*uvicorn*$PORT*' } | ForEach-Object { Stop-Process -Id \$_.ProcessId -Force -ErrorAction SilentlyContinue }" \
      2>/dev/null || true
  fi
  if [ "$KEEP" -eq 0 ]; then rm -rf "$DATA_DIR" 2>/dev/null || true; fi
}
trap cleanup EXIT INT TERM

READY=0
for i in $(seq 1 60); do
  if curl -fsS --noproxy '*' "http://127.0.0.1:${PORT}/api/v1/health" >/dev/null 2>&1; then
    READY=1; break
  fi
  sleep 1
done
if [ "$READY" -ne 1 ]; then
  echo "  --- 服务日志 ---"; tail -40 "$SERVER_LOG"
  die 1 "服务启动超时"
fi

# 契约自检：server_time 是 e2e 时间窗的唯一基准，缺失会让时间用例在 CI 上假失败
HEALTH="$(curl -fsS --noproxy '*' "http://127.0.0.1:${PORT}/api/v1/health" 2>/dev/null || echo '{}')"
case "$HEALTH" in
  *server_time*) ok "server_time 契约正常" ;;
  *) die 1 "/health 未返回 server_time —— 时间窗用例将失去基准" ;;
esac

# ---------- 4. 跑回归 ----------
step "5/6  运行回归"
if [ ${#STAGES[@]} -gt 0 ]; then
  echo "  阶段: ${STAGES[*]}（增量）"
  E2E_BASE="http://127.0.0.1:${PORT}" E2E_DIRECT=1 "$PY" -u tests/run_all.py "${STAGES[@]}"
else
  echo "  阶段: 全部（全量）"
  # ⚠️ 必须走独立分支，不能写 `"${STAGES[@]:-}"`：空数组时该写法会展开成
  # **一个空字符串参数**，run_all.py 拿到 sys.argv[1:] == [""] → only=[""]
  # → 没有任何阶段名匹配 → 跑 0 项用例并以「全部通过」退出。
  # 这是典型的「参数展开看似无害、实际静默改变语义」。
  E2E_BASE="http://127.0.0.1:${PORT}" E2E_DIRECT=1 "$PY" -u tests/run_all.py
fi
RC=$?

# ---------- 5. 结果 ----------
step "6/6  结果"
if [ "$RC" -eq 0 ]; then
  ok "回归通过"
else
  echo "  ${c_err}回归未通过（退出码 $RC）${c_reset}"
  echo "  服务日志: $SERVER_LOG"
  [ "$KEEP" -eq 1 ] && echo "  数据目录: $DATA_DIR"
fi
exit "$RC"
