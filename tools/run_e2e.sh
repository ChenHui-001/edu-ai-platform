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
step "2/6  离线单元回归（真实 IP / 异地登录 / 首批性能修复 / 下发性校验 / 任务锁）"
# 不吃端口、不建正式库、不依赖 nginx：纯函数与纯服务层的精确断言。
# 这类断言放在这里而不是 e2e 里，是因为反代拓扑下头的值会被覆盖，
# e2e 只能断言「伪造值未入库」这个较弱但拓扑无关的性质。
"$PY" tests/test_unit_ip_login.py || die 1 "离线单元回归（IP/异地登录）未通过"
# 排名语义（含 NULL 班级兜底）、排名不取回 peers 全量、日报零点边界与
# 索引可用性 —— 这四项在 e2e 的正常数据形态下都碰不到，只能在这一层守。
"$PY" tests/test_unit_perf_batch1.py || die 1 "离线单元回归（性能修复语义）未通过"
# 任务下发的两条路径有两处**刻意的不对称**（指定学生报错 vs 班级静默跳过；
# 停用学生仍有班级 assignment 但不发通知）。e2e 的种子数据里没有停用学生，
# 走不到这些分支，只能在这一层用自建数据精确断言。
"$PY" tests/test_unit_task_assign.py || die 1 "离线单元回归（下发性校验）未通过"
# 强制改密拦截 + 拒绝 old==new。这组只能在离线层：e2e 服务端以
# MUST_CHANGE_PASSWORD_ENFORCED=false 启动（99 处共用硬编码口令的 login
# 需要），拦截在 e2e 里不生效；且 e2e 不能真改密码。
"$PY" tests/test_unit_must_change_pwd.py || die 1 "离线单元回归（强制改密/新旧相同）未通过"
# A2 定时任务执行锁。必须在这一层：e2e 是全新临时库（无遗留锁行）+
# SCHEDULER_ENABLED=false（scheduler.py 的 sync_all_jobs 直接 return 0，
# 没有任何 cron 触发），两个进程永远撞不上 —— 而「锁有没有生效」只能靠
# 双进程同时起跑才看得出来。首组用例是**无锁对照**（通知翻倍），
# 没有它，「有锁时只跑一份」的绿只说明代码能跑。
"$PY" tests/test_a2_job_lock.py || die 1 "离线回归（A2 任务执行锁）未通过"
# S7 图形验证码强制化。必须在这一层：e2e 服务端以 CAPTCHA_ENFORCED=false
# 启动（130+ 处登录/注册调用都不带验证码），`true` 分支在 e2e 里根本不执行；
# 且验证码的正确答案只存在于 PNG 里（`sys_captcha` 存明文，接口只回图和 key），
# e2e 拿不到答案，构造不出"带正确码"的正例。
# 本文件同时守「开关单向收紧」：关掉开关只能放开"不传"，带错码一律拒绝。
"$PY" tests/test_unit_captcha_enforced.py || die 1 "离线回归（S7 验证码强制化）未通过"

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
#
# ---- 强制改密开关：必须同时注入「服务进程」和「测试进程」----
# 服务端为什么设 false：e2e 有 99 处 `.login()` 共用硬编码口令常量，其中
# 42 处是裸登录（直接 post /auth/login 读响应体）。让它们走真实改密流程会让
# "当前密码"在 100+ 个 Client 实例之间漂移。开关默认 true，生产不注入即保持
# 拦截；`change_password` 里拒绝 new==old 是**无条件**的，不受此开关影响，
# 所以关掉它也不会让 S5 的可绕过路径复活。
#
# 测试进程为什么也必须看到它：test_requirements.py 里「未改密访问业务接口」
# 那条断言要按开关取值分支（403 / 200 两种都是被测行为）。测试进程与服务
# 进程是两个独立的进程（CI 里甚至隔着 docker），宿主机 `os.environ` 读不到
# 容器的 `-e`。少注入一处 → 断言按默认 true 期望 403、实际 200 → 必红。
# 故**只此一处定义**，下面用同一个变量喂给两个进程，避免两处字面量漂移。
MUST_CHANGE_PASSWORD_ENFORCED="${MUST_CHANGE_PASSWORD_ENFORCED:-false}"
export MUST_CHANGE_PASSWORD_ENFORCED

# ---- 图形验证码强制化开关（S7）----
# 与上面的强制改密开关是**完全相同的范式**，也需要同时注入两个进程。
#
# 服务端为什么设 false：e2e 有 100 处 `.login()` + 26 处裸
# `post("/auth/login")` + 7 处裸 `post("/auth/register")`，全都不携带验证码。
# 而验证码的正确答案**只存在于 PNG 图片里** —— `GET /auth/captcha` 的响应只有
# base64 图和 key，明文答案存在服务端 `sys_captcha` 表里，这是刻意的。
# 让这一百三十多处调用都去 OCR 识别是不现实的。
#
# 关掉它**不会**让"传一个错的验证码"通过：`_verify_captcha_or_raise` 里
# false 分支只在 `not captcha_key` 时 return，带了 key 一律走
# `verify_captcha`。开关是单向收紧的，最坏情况只降级到「无验证码」。
#
# 测试进程为什么也必须看到它：test_requirements.py 里「不传验证码登录」那条
# 断言按开关取值分支（400 / 200 都是被测行为）。少注入一处 → 按默认 true
# 期望 400、实际 200 → 必红。所以在这里**只定义一次**，下面喂给两个进程。
CAPTCHA_ENFORCED="${CAPTCHA_ENFORCED:-false}"
export CAPTCHA_ENFORCED

# ---- 演示数据 + 运行形态：e2e 必须显式声明，不能靠默认值 ----
# 为什么显式写：`SEED_DEMO_DATA` 默认 true、`APP_ENV` 默认 production。若这里
# 不注入，服务端就是「生产形态 + 演示数据开着」—— A3 启动校验的第 1 项会
# 每次 e2e 都报一条 error 并往测试库写一条 ErrorLog。测试断言的失败原因会
# 变得极难分辨（真的业务断言红了，还是被这条噪音带偏的？）。
#
# APP_ENV=test 的作用就是把这个组合声明为「测试形态」，让那条告警不触发；
# SEED_DEMO_DATA=true 是因为 99 处 `.login()` 都用 teacher1/stu731 这类演示
# 账号，关掉就全线红。**两个必须同时给** —— 只给 SEED_DEMO_DATA 而不给
# APP_ENV，告警照报。
export SEED_DEMO_DATA="${SEED_DEMO_DATA:-true}"
export APP_ENV="${APP_ENV:-test}"
(
  cd backend && \
  DATABASE_URL="$DB_URL" LLM_ENABLED=false SCHEDULER_ENABLED=false \
  MUST_CHANGE_PASSWORD_ENFORCED="$MUST_CHANGE_PASSWORD_ENFORCED" \
  CAPTCHA_ENFORCED="$CAPTCHA_ENFORCED" \
  SEED_DEMO_DATA="$SEED_DEMO_DATA" APP_ENV="$APP_ENV" \
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
