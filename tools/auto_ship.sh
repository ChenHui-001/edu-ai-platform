#!/usr/bin/env bash
# ================================================================
# 九年义务教育 AI 学习管理系统 —— 自动交付流水线
#
# 流程：改动检测 → 静态门禁 + 冒烟校验(导库/建表/路由) → git commit
#       → git push → 等待 CI 发布 → 拉取 ghcr 多架构镜像
#       → (可选)复制到 Docker Hub
# 设计原则：**校验不过就不提交、不推送**（fail fast，绝不带病上线）
#
# ⚠️ 2026-10-29 起测试体系（tests/ 与 CI 的 e2e job）已移除。原来的
#    「端到端回归」换成四件事，门槛降低但**不是零**：
#      1) 静态门禁（后端：硬编码地址/弱断言/时间契约/模型外键/迁移列/响应体/
#         裸 SQL/定时任务注册/status 字面量/造数确定性/用例覆盖/N+1 棘轮/ruff；
#         前端：模板引用/重复模板/res.data.data/裸消息框/CSS 变量；
#         文档：现状卡自洽 + 版本基线漂移。道数以 tools/status_snapshot.py 为准）
#      2) 接口级行为回归（tools/verify_p0_fixes.py）+ 高价值场景回归（8 个脚本）
#      3) 导库 + create_all 建表 + 路由数下限（拦住语法错、循环导入、模型断裂）
#      4) CI 的 compileall + 镜像构建仍会独立跑一次
#    代价要说清楚：**页面级行为回归已无自动化覆盖**，改业务逻辑后必须人工点一遍相关页面。
#
# ★ 镜像唯一来源 = CI 构建的 ghcr 多架构镜像（ghcr.io/chenhui-001/edu-ai-platform）
#   本机**不编译任何镜像**：校验用源码直跑，正式镜像等 CI 发布后 pull。
#   好处：本地与服务器跑的是同一份（sha256 逐字节相同），杜绝
#   「同版本号、不同内容」的两份镜像漂移。
#
# 用法：
#   ./tools/auto_ship.sh                  # 全流程（不推 Docker Hub）
#   ./tools/auto_ship.sh --push           # 全流程 + 复制到 Docker Hub（多架构）
#   ./tools/auto_ship.sh --no-push        # 不推 git（离线/临时验证用）
#   ./tools/auto_ship.sh --msg "xxx"      # 自定义提交信息
#   ./tools/auto_ship.sh --skip-test      # 跳过冒烟校验（仅提交，慎用）
#   ./tools/auto_ship.sh --bump patch     # 版本号 +1（1.0.8 -> 1.0.9）后交付
#   ./tools/auto_ship.sh --deploy         # 交付完成后把服务器也切到新版本
#   ./tools/auto_ship.sh --dry-run        # 只跑校验，不提交不拉镜像
#
# ⚠️ 手工验证提示：改动涉及权限、判分、组卷、交卷、迁移时，
#    自动校验完全测不到这些行为，发版前请按 docs/DEVELOPMENT.md 的人工清单过一遍。
#
# 退出码：0 成功 / 1 测试失败 / 2 提交失败 / 3 镜像拉取失败 / 4 无改动
# ================================================================
set -uo pipefail

cd "$(dirname "$0")/.."
ROOT="$(pwd)"

PUSH=0
SKIP_TEST=0
DRY_RUN=0
DEPLOY=0
BUMP=""
MSG=""
STAGES=""
NAMESPACE="${DOCKERHUB_NAMESPACE:-nanpo}"
REGISTRY="${DOCKERHUB_REPO:-edu-ai-platform}"
# ghcr 是**唯一镜像来源**：镜像由 CI 构建（多架构 amd64+arm64），
# 本地与服务器拉同一份，保证 sha256 逐字节一致。本地不再编译镜像。
GHCR_IMAGE="${GHCR_IMAGE:-ghcr.io/chenhui-001/edu-ai-platform}"

while [ $# -gt 0 ]; do
  case "$1" in
    --push)      PUSH=1 ;;
    --no-push)   NO_PUSH=1 ;;
    --skip-test) SKIP_TEST=1 ;;
    --dry-run)   DRY_RUN=1; SKIP_COMMIT=1 ;;
    --deploy)    DEPLOY=1 ;;
    --msg)       MSG="$2"; shift ;;
    --bump)      BUMP="$2"; shift ;;
    --stages)    STAGES=""; shift ;;   # 兼容旧命令：阶段已移除，忽略
    -h|--help)   sed -n '2,32p' "$0"; exit 0 ;;
    *) echo "未知参数: $1"; exit 1 ;;
  esac
  shift
done
SKIP_COMMIT="${SKIP_COMMIT:-0}"
NO_PUSH="${NO_PUSH:-0}"

# ---------- 输出helper ----------
c_reset=$'\033[0m'; c_ok=$'\033[92m'; c_err=$'\033[91m'; c_warn=$'\033[93m'; c_info=$'\033[96m'
step() { echo ""; echo "${c_info}▶ $*${c_reset}"; }
ok()   { echo "  ${c_ok}✔${c_reset} $*"; }
die()  { echo "  ${c_err}✘${c_reset} $*"; exit "$1"; }

VERSION="$(cat VERSION 2>/dev/null || echo "0.0.0")"
echo "${c_info}══════════════════════════════════════════════${c_reset}"
echo " 自动交付流水线  ·  版本 ${VERSION}"
echo "${c_info}══════════════════════════════════════════════${c_reset}"

# ---------- 0. 改动检测 ----------
step "0/5  检测工作区改动"
CHANGED="$(git status --porcelain | grep -v '^\s*$' || true)"
if [ -z "$CHANGED" ]; then
  echo "  ${c_warn}工作区干净，无需交付${c_reset}"
  exit 4
fi
echo "$CHANGED" | sed 's/^/  /'
FILE_COUNT="$(echo "$CHANGED" | wc -l | tr -d ' ')"
ok "检测到 $FILE_COUNT 项改动"

# ---------- 0.4 用例静态门禁 ----------
# 把「换环境才炸」的两类缺陷提前到秒级发现，不用等 35 分钟全量：
#   1) 硬编码服务地址 → 换端口就 401/404，伪装成业务 bug
#   2) 恒真断言        → 功能挂了也 PASS，污染整轮结论
step "0c/5  用例静态门禁"
# PYTHON_BIN 由使用者提供（本机是 C:/Program Files/Python312/python.exe）；
# 未提供时退回 PATH 里的 python3 / python。
GATE_PY="${PYTHON_BIN:-}"
if [ -z "$GATE_PY" ] || ! command -v "$GATE_PY" >/dev/null 2>&1; then
  if command -v python3 >/dev/null 2>&1; then GATE_PY=python3
  elif command -v python >/dev/null 2>&1; then GATE_PY=python
  else GATE_PY=""
  fi
fi
if [ -n "$GATE_PY" ]; then
  GATE_RC=0
  "$GATE_PY" tools/check_hardcoded_host.py || GATE_RC=1
  "$GATE_PY" tools/check_weak_assertion.py || GATE_RC=1
  "$GATE_PY" tools/check_time_contract.py || GATE_RC=1
  "$GATE_PY" tools/check_model_fk.py || GATE_RC=1
  "$GATE_PY" tools/check_migration_columns.py || GATE_RC=1
  # Q-06：迁移链能建库 + 与模型/create_all 结构一致。3s，纯临时库，不碰真实库。
  # 少了这一条，Alembic 会退化成"文件建了但没人跑过"的摆设。
  "$GATE_PY" tools/check_alembic_sync.py || GATE_RC=1
  "$GATE_PY" tools/check_schema_bodies.py || GATE_RC=1
  "$GATE_PY" tools/check_api_sql.py || GATE_RC=1
  "$GATE_PY" tools/check_job_handlers.py || GATE_RC=1
  # Q-07：sys_agent_job.status 只许用 agent_job_state 常量（success/succeeded 两套拼写曾致终态误判）
  "$GATE_PY" tools/check_job_status_literals.py || GATE_RC=1
  # 演示造数确定性（两次生成指纹一致）与「关键模块必须有测试 import」：
  # 两者都只在 CI 跑过，本地漏跑就会「提交后等 2 分钟才知道红」。
  # 实测耗时 10s / 0.3s，放进本地门禁不痛。
  "$GATE_PY" tools/check_gen_data_determinism.py || GATE_RC=1
  "$GATE_PY" tools/check_new_code_tests.py || GATE_RC=1
  # N+1 棘轮：A 类（循环内逐条查库）只许降不许升。
  # 脚本早就写好了，但此前只在 CI 定时任务里跑，本地改完 API 直接提交，
  # 到 CI 才发现（或根本没人看）。默认非严格模式只出报告，--ratchet 卡基线。
  "$GATE_PY" tools/check_n_plus_one.py --ratchet || GATE_RC=1
  # ruff 未安装时 lint_gate 返回 2 —— 那是「环境缺工具」而不是「代码有缺陷」，
  # 与 CI 不同（CI 里会先 pip install ruff，缺了就是流程错）。
  # 本地缺失只告警不阻断，避免为了跑一次交付先折腾环境。
  "$GATE_PY" tools/lint_gate.py || {
    rc=$?
    if [ "$rc" -eq 2 ]; then
      echo "  ${c_warn}未安装 ruff，跳过 F 类静态检查（CI 仍会强制校验）${c_reset}"
    else
      GATE_RC=1
    fi
  }
  if [ "$GATE_RC" -ne 0 ]; then
    die 1 "静态门禁未通过（硬编码地址 / 恒真断言 / 时间契约 / 模型输出写外键 / F 类缺陷 / 造数确定性 / 用例覆盖），修复后再交付"
  fi
  ok "静态门禁通过"

  # 前端四道普查同样只在 CI 跑过：改 .vue 时最容易踩「模板引用未定义标识符」
  # 「整块模板被复制成两份」「res.data.data 恒 undefined」「裸 ElMessageBox」，
  # 四者 build 与 eslint 全绿、浏览器里才炸。四道合计 <2s，一并前置。
  FE_RC=0
  # check_css_tokens：CSS 变量自引用 / 未定义引用。此前只在 CI 跑，
  # 历史上曾因 `--el-color-primary` 被写成自引用导致 primary 按钮全透明，
  # 本地全绿、上线才发现。与其余四道合并进同一轮（<1s）。
  for _g in scan_vue_refs scan_vue_dup check_data_data check_bare_messagebox check_css_tokens; do
    "$GATE_PY" "tools/${_g}.py" || FE_RC=1
  done
  if [ "$FE_RC" -ne 0 ]; then
    die 1 "前端静态普查未通过（白屏引用 / 重复模板块 / res.data.data / 裸消息框 / CSS 变量），修复后再交付"
  fi
  ok "前端静态普查通过"
else
  echo "  ${c_warn}未找到 python，跳过静态门禁${c_reset}"
fi

# ---------- 0.4 行为回归（接口级） ----------
# 项目自 2026-10-29 移除 tests/ 后，后端行为回归是真空的：静态门禁只看
# 「代码长什么样」，看不出「端点串起来还对不对」。这个脚本用临时库 +
# TestClient 走真实 HTTP，覆盖导出(P0-1)、异步组卷解析(P0-3)、Agent 组卷(P0-4)、
# 覆盖写保留大题结构(P1-1)、删题重算(P1-4)、版本乐观锁(P1-9)、自测卷题型(P1-10)、
# 版本对比(F-02)、班级薄弱点(F-03)、任务取消(F-04)、请求体默认值(BUG-026)、
# 报表缓存(P-07：命中/refresh 绕过后写回/跨用户不串键/深拷贝/容量上限)。
if [ -n "$GATE_PY" ] && [ -f tools/verify_p0_fixes.py ]; then
  # 断言条数从输出里数，不在脚本里写死 —— 写死过一次 80，加到 92 时没人改，
  # 那句 ✔ 就变成假的了。
  _vlog="/tmp/auto_ship_verify_p0.log"
  if ! "$GATE_PY" tools/verify_p0_fixes.py > "$_vlog" 2>&1; then
    tail -30 "$_vlog" 2>/dev/null
    die 1 "接口级行为回归未通过（导出 / 组卷 / 大题结构 / 成绩重算 / 版本 / 自测卷 / 取消 / 报表缓存 / 写接口契约）"
  fi
  _vn="$(grep -cE '^[[:space:]]+(PASS|FAIL)' "$_vlog" || true)"
  ok "接口级行为回归通过（${_vn} 条断言）"
fi

# ---------- 0.4b 高价值场景回归（P-06） ----------
# 这些脚本此前只在 CI 的「功能回归测试」定时任务里跑，本地发版时是盲区：
# 组卷引擎、作答丢失、卷面结构、PDF 安全这些改坏了，静态门禁一个都看不出来。
# 只挑「快且稳」的（合计约 98s）；重脚本留给 CI：
#   verify_student_retake(103s)、verify_paper_module(起独立服务,106 项)、
#   verify_paper_manage(>150s) —— 放进发版链路会把 3 分钟拖成 8 分钟。
# `verify_llm_routing` 约 3s 且不碰库/不碰网络：它覆盖场景路由与按 biz_type
# 预算（F-06），而这类「配置存了但读不到」的缺口静态门禁完全看不出来。
# `verify_ai_fill_parallel` 约 2s：唯一直接驱动 `_ai_fill_gaps` 的脚本（补题并行、
# 批次分档、空正文减半重试、熔断早退、缺口原因回传）。组卷补题出问题最贵的
# 就是"静默补不上"，靠人工点页面根本发现不了。
# 每个脚本单独 180s 上限：卡死要能报出是哪一个，而不是整条流水线挂住。
if [ -n "$GATE_PY" ]; then
  REGRESS_SCRIPTS="verify_paper_rescore verify_compose_engine verify_pdf_export_safety \
verify_bugfix_256 verify_compose_regenerate verify_paper_v3 verify_llm_routing \
verify_ai_fill_parallel"
  # macOS 自带 coreutils 的路径与 Linux 不同；两条都没有就直接跑（不设上限），
  # 不能因为缺一个可选命令就让发版脚本直接报错。
  TIMEOUT_CMD=""
  if command -v timeout >/dev/null 2>&1; then
    TIMEOUT_CMD="timeout 180"
  elif command -v gtimeout >/dev/null 2>&1; then
    TIMEOUT_CMD="gtimeout 180"
  fi
  for _s in $REGRESS_SCRIPTS; do
    if [ ! -f "tools/$_s.py" ]; then
      echo "  ${c_warn}跳过（不存在）：$_s${c_reset}"
      continue
    fi
    _log="/tmp/auto_ship_regress_${_s}.log"
    # shellcheck disable=SC2086  # TIMEOUT_CMD 需要按空格拆成命令+参数
    if ! $TIMEOUT_CMD "$GATE_PY" "tools/$_s.py" > "$_log" 2>&1; then
      # 失败时把日志尾部打出来：否则只有一句「未通过」，还得自己去翻
      tail -30 "$_log" 2>/dev/null
      die 1 "场景回归未通过：$_s（完整输出见 $_log）"
    fi
    ok "场景回归：$_s"
  done
fi

# ---------- 0.5 磁盘预检 ----------
# 每次构建 2 份 ~1.5GB 镜像。磁盘不足会让 IO 骤降，表现为大量接口超时
# （reindex 120s、创建题目 timed out），看起来像代码 bug 实为 IO 不够。
#
# 查的是 **Docker 数据盘**（默认系统盘；若已把Docker Desktop 的
# Disk image location 迁到数据盘，则数据盘才是真正的瓶颈）。
# 注意：Git Bash 里 `docker info` 返回的DockerRootDir 是 /var/lib/docker
# 这个 WSL 内部路径，df 对它无效，要用 Windows 侧查询。
step "0b/5  磁盘空间预检"

_docker_disk_free_gb() {
    # 优先查 Docker 实际所在盘；取不到再回退系统盘
    local root
    root="$(docker info --format '{{.DockerRootDir}}' 2>/dev/null || true)"
    if command -v powershell >/dev/null 2>&1 && [ -n "$root" ]; then
        # Docker Desktop（WSL2）：数据在 vhdx，按挂载点所在盘算
        local drive
        drive="$(printf '%s' "$root" | sed -n 's#^\([A-Za-z]\):.*#\1#p')"
        if [ -n "$drive" ]; then
            powershell -NoProfile -Command \
                "\$d=(Get-PSDrive '$drive' -ErrorAction SilentlyContinue); if(\$d){[math]::Round(\$d.Free/1GB,0)}" 2>/dev/null && return
        fi
    fi
    command -v powershell >/dev/null 2>&1 && \
        powershell -NoProfile -Command "[math]::Round((Get-PSDrive C).Free/1GB,0)" 2>/dev/null
}
FREE_GB="$(_docker_disk_free_gb)"
[ -z "$FREE_GB" ] && FREE_GB=0

if [ "$FREE_GB" -lt 4 ]; then
  echo "  ${c_warn}Docker 所在盘可用仅 ${FREE_GB}GB（构建需约 4GB），正在清理...${c_reset}"
  docker image prune -af --filter "until=24h" >/dev/null 2>&1
  docker builder prune -af >/dev/null 2>&1
  FREE_GB="$(_docker_disk_free_gb)"
  [ -z "$FREE_GB" ] && FREE_GB=0
  if [ "$FREE_GB" -lt 2 ]; then
    die 3 "Docker 所在盘空间不足（${FREE_GB}GB）。\n     Docker 数据默认在系统盘，建议在 Docker Desktop\n     Settings → Resources → Advanced 里把 Disk image location\n     迁到数据盘，或手动清理历史镜像与构建缓存"
  fi
  ok "清理完成，可用 ${FREE_GB}GB"
else
  ok "Docker 所在盘可用 ${FREE_GB}GB"
fi

# ---------- 版本号 bump（可选，须在测试前完成） ----------
if [ -n "$BUMP" ]; then
  step "版本号 bump ($BUMP)"
  IFS='.' read -r MAJ MIN PAT <<< "$VERSION"
  case "$BUMP" in
    major) NEW="$((MAJ+1)).0.0" ;;
    minor) NEW="$MAJ.$((MIN+1)).0" ;;
    patch) NEW="$MAJ.$MIN.$((PAT+1))" ;;
    *) die 1 "非法 --bump 值: $BUMP（可选 major/minor/patch）" ;;
  esac
  echo "$NEW" > VERSION
  ok "VERSION: $VERSION -> $NEW"
  VERSION="$NEW"
fi

# ---------- 0d. 文档基线（Q-02） ----------
# 必须在 bump **之后**跑：bump 改了 VERSION，现状卡上的数字（版本/用例数/
# 端点断言数）当场过期。放在 bump 之前校验，等于校验一个即将被改掉的版本。
#
# 两件事：
#   1) --write 重算 docs/STATUS.md 里的 auto 区块（幂等，无变化就不产生 diff）
#   2) check_doc_versions 拦住"文档自己写死当前版本号"——这是「文档基线漂移」
#      的唯一机械防线，README 曾经写死过 2.0.0，RELEASE_CONSISTENCY 曾有一张
#      停在 2.1.12 的现状表，两次都是 CI 全绿而读者被误导。
if [ -n "$GATE_PY" ]; then
  step "0d/5  文档基线一致性"
  # --write 是幂等的：数字没变就不产生 diff。dry-run 下也会重算这张卡
  # （与 bump 会改 VERSION 同理：卡片是 VERSION 的派生品，不是独立状态）。
  if ! "$GATE_PY" tools/status_snapshot.py --write; then
    die 1 "现状卡重算失败（docs/STATUS.md 或 tools/status_snapshot.py 有问题）"
  fi
  ok "现状卡已重算"
  if ! "$GATE_PY" tools/check_doc_versions.py; then
    die 1 "文档版本基线漂移：非归档文档写死了当前版本号，改成指向 docs/STATUS.md"
  fi
fi

# ---------- 1. 冒烟校验（取代原端到端回归） ----------
# 测试体系移除后这里换成「源码级冒烟」：证明即将提交的代码**能被导入、
# 能建出全部表、路由没少**。它抓不到业务行为错误，但能抓住这几类
# 提交了就会炸线上/炸 CI 的问题：
#   - 语法错、循环导入、模块级异常（import 即失败）
#   - 模型定义断裂 / create_all 抛错（起服务即 500）
#   - 路由被误删或装饰器写错（接口 404，但编译期完全看不出来）
# 与 CI 的 compileall + 镜像构建互补：那是「能打包」，这是「能起来」。
if [ "$SKIP_TEST" -eq 1 ]; then
  step "1/5  冒烟校验 —— 已跳过（--skip-test）"
  echo "  ${c_warn}⚠ 跳过校验直接交付，存在带病上线风险${c_reset}"
else
  step "1/5  冒烟校验（导库 / 建表 / 路由数）"

  PY="${PYTHON_BIN:-python3}"
  command -v "$PY" >/dev/null 2>&1 || PY=python
  SMOKE_LOG="/tmp/autoship_smoke.log"
  SMOKE_DIR="$(mktemp -d)"
  # 用一次性临时库，绝不碰 ./data 里的真实数据
  (
    cd backend && \
    DATABASE_URL="sqlite:///${SMOKE_DIR}/smoke.db" \
    LLM_ENABLED=false SCHEDULER_ENABLED=false SEED_DEMO_DATA=false DEBUG=false \
    APP_ENV=test SECRET_KEY=autoship_smoke_secret_key_0123456789ab \
    "$PY" -c "
from app.main import app
from app.core.database import Base, engine
Base.metadata.create_all(bind=engine)
routes = len(app.routes)
tables = len(Base.metadata.tables)
print(f'路由={routes} 表={tables}')
assert routes >= 250, f'路由数异常偏少：{routes} < 250，可能有路由被误删'
assert tables >= 45,  f'表数异常偏少：{tables} < 45，可能有模型未注册'
print('SMOKE_OK')
"
  ) > "$SMOKE_LOG" 2>&1
  SMOKE_RC=$?
  rm -rf "$SMOKE_DIR"
  tail -6 "$SMOKE_LOG"

  if [ $SMOKE_RC -ne 0 ] || ! grep -q "SMOKE_OK" "$SMOKE_LOG"; then
    echo ""
    echo "  ${c_err}冒烟校验失败 —— 已中止，不提交、不推送${c_reset}"
    echo "  完整日志: ${SMOKE_LOG}"
    exit 1
  fi
  ok "冒烟校验通过（$(grep -o '路由=[0-9]* 表=[0-9]*' "$SMOKE_LOG" | tail -1)）"
fi

if [ "$DRY_RUN" -eq 1 ]; then
  step "dry-run 模式 —— 校验已跑完，跳过提交与镜像拉取"
  echo ""
  echo "${c_ok}✓ dry-run 完成：校验通过，未做任何提交或构建${c_reset}"
  exit 0
fi

# ---------- 2. git commit ----------
step "2/5  提交代码"
if [ -z "$MSG" ]; then
  MSG="chore: 自动交付 $(date '+%Y-%m-%d %H:%M')"
  if [ -n "$CHANGED" ]; then
    SUBJ="$(echo "$CHANGED" | head -3 | awk '{print $2}' | tr '\n' ' ')"
    MSG="chore: 自动交付 ${SUBJ}"
  fi
fi

git add -A || die 2 "git add 失败"
if git diff --cached --quiet; then
  echo "  ${c_warn}暂存区为空，跳过提交${c_reset}"
else
  # 提交信息末尾附带验证结论，便于回溯
  FULL_MSG="$MSG"
  if [ "$SKIP_TEST" -eq 0 ]; then
    FULL_MSG="${MSG}"$'\n\n'"校验: 静态门禁 + 接口级行为回归 + 场景回归 + 冒烟通过"
  fi
  if ! git commit -m "$FULL_MSG"; then
    die 2 "git commit 失败"
  fi
  ok "已提交 $(git rev-parse --short HEAD)"
fi

# ---------- 2b. git push ----------
# 代码必须离开本机，否则镜像里烧的 commit 在远端不存在 —— 镜像无法溯源，
# 也无法在 CI 复现。这一步以前是缺失的：本地一直领先远程若干提交，
# 而构建照常进行，「本地比远程新」这个漂移从未被发现。
step "2b/5  推送到远程仓库"
if [ "$NO_PUSH" -eq 1 ]; then
  echo "  ${c_warn}已跳过（--no-push）${c_reset}"
else
  BRANCH="$(git rev-parse --abbrev-ref HEAD)"
  if git push origin "$BRANCH"; then
    ok "已推送 origin/${BRANCH}"
  else
    die 2 "git push 失败 —— 代码未进入远程，构建出的镜像将无法溯源"
  fi
fi

# ---------- 3. 拉取 CI 构建的多架构镜像（唯一镜像来源） ----------
# **本地不再编译任何镜像。** 镜像唯一来源 = CI 构建的 ghcr 多架构镜像，
# 本地与服务器跑同一份（sha256 逐字节相同），从根本上消除
# 「本地自建一份、远程一份，同版本号不同内容」这种最危险的漂移。
step "3/5  拉取多架构镜像 ${GHCR_IMAGE}:${VERSION}"

# 一致性校验：确认 VERSION 已提交、已推送、tag 自洽。
# **必须在 git commit 之后**跑 —— 此时工作区应干净，commit 已是最终的。
GATE_PRE_RC=0
"$GATE_PY" tools/check_release_consistency.py --pre --no-image || GATE_PRE_RC=$?
if [ "$GATE_PRE_RC" -ne 0 ]; then
  die 3 "发布前一致性校验未通过（见上方明细），已中止"
fi

GIT_COMMIT="$(git rev-parse HEAD)"

# 3.1 等待 CI 把该版本发布到 ghcr。
# 代码刚 push，CI 的 docker-publish 工作流此刻才开始构建（多架构 + QEMU，
# 实测需 20~45 分钟）。这里轮询到 manifest 出现为止，超时即中止。
WAIT_MAX="${CI_WAIT_MAX:-2700}"   # 默认 45 分钟
WAITED=0
while true; do
  if docker manifest inspect "${GHCR_IMAGE}:${VERSION}" >/dev/null 2>&1; then
    ok "CI 已发布 ${VERSION}（等待 ${WAITED}s）"
    break
  fi
  if [ "$WAITED" -ge "$WAIT_MAX" ]; then
    echo ""
    echo "  ${c_err}等待 CI 发布镜像超时（${WAIT_MAX}s）${c_reset}"
    echo "  ${GHCR_IMAGE}:${VERSION} 尚未出现在 registry"
    echo "  请检查 GitHub Actions 的「Docker 镜像发布」工作流是否成功"
    die 3 "CI 未发布镜像"
  fi
  [ $((WAITED % 60)) -eq 0 ] && echo "  等待 CI 发布镜像... (${WAITED}s/${WAIT_MAX}s)"
  sleep 15
  WAITED=$((WAITED + 15))
done

# 3.2 拉取（多架构 index，含 amd64/arm64）
if ! docker pull "${GHCR_IMAGE}:${VERSION}"; then
  die 3 "拉取镜像失败：${GHCR_IMAGE}:${VERSION}"
fi
ok "已拉取 ${GHCR_IMAGE}:${VERSION}"

# 3.3 核对镜像内指纹：版本与 commit 必须等于本地 HEAD。
# 不能只信拉取成功——拉到的可能是缓存的旧层。
IMG_VER="$(docker run --rm --entrypoint sh "${GHCR_IMAGE}:${VERSION}" -c 'cat /app/VERSION' 2>/dev/null | tr -d '\r\n ')"
IMG_COMMIT="$(docker run --rm --entrypoint sh "${GHCR_IMAGE}:${VERSION}" -c 'grep ^commit /app/BUILD_INFO | cut -d= -f2' 2>/dev/null | tr -d '\r\n ')"
if [ "$IMG_VER" != "$VERSION" ] || [ "$IMG_COMMIT" != "$GIT_COMMIT" ]; then
  die 3 "镜像指纹不匹配：镜像内 version=${IMG_VER:-?} commit=${IMG_COMMIT:-?}，期望 version=${VERSION} commit=${GIT_COMMIT}"
fi
ok "镜像指纹一致：version=${IMG_VER} commit=${IMG_COMMIT:0:7}"

FINAL_LOCAL="${GHCR_IMAGE}:${VERSION}"

# 3.4 清理历史遗留的本地自建镜像（只保留 ghcr 多架构镜像这一份来源）
CLEANED="$(docker images --format '{{.Repository}}:{{.Tag}}' \
  | grep -v '^ghcr\.io/chenhui-001/edu-ai-platform:' \
  | grep -E '^(edu-ai-platform|nanpo/edu-ai-platform):' \
  | wc -l | tr -d ' ')"
if [ "${CLEANED:-0}" -gt 0 ]; then
  docker images --format '{{.Repository}}:{{.Tag}}' \
    | grep -v '^ghcr\.io/chenhui-001/edu-ai-platform:' \
    | grep -E '^(edu-ai-platform|nanpo/edu-ai-platform):' \
    | xargs -r docker rmi -f >/dev/null 2>&1 || true
  ok "已清理 ${CLEANED} 个历史本地镜像（只保留 ghcr 多架构镜像）"
fi

# ---------- 4. 推送（可选） ----------
if [ "$PUSH" -eq 1 ]; then
  step "4/5  推送 Docker Hub（复制 ghcr 的多架构 index，不重新编译）"
  if ! docker info 2>/dev/null | grep -q "Username:"; then
    die 1 "未登录 Docker Hub，请先 docker login"
  fi
  REMOTE="${NAMESPACE}/${REGISTRY}:${VERSION}"
  # 用 imagetools **复制整个 manifest index**（含 amd64/arm64 两个子 manifest）。
  # 若改用 docker tag + docker push，只会推当前平台的单架构镜像，
  # 造成「Docker Hub 是单架构、ghcr 是多架构」的隐性降级。
  if ! docker buildx imagetools create -t "$REMOTE" "$FINAL_LOCAL"; then
    die 3 "复制 manifest index 失败：$REMOTE"
  fi
  docker buildx imagetools create -t "${NAMESPACE}/${REGISTRY}:latest" "$FINAL_LOCAL" || true
  if ! docker buildx imagetools push "$REMOTE"; then
    die 3 "推送失败：$REMOTE"
  fi
  docker buildx imagetools push "${NAMESPACE}/${REGISTRY}:latest" || true
  ok "已推送 $REMOTE（多架构）"

  # 推送后回查：不能只信 docker push 的退出码——它只说明字节传上去了，
  # 不说明传上去的是不是这次的代码。这里比对远端镜像内的版本与 commit 指纹。
  step "4b/5  发布后一致性核对"
  if ! "$GATE_PY" tools/check_release_consistency.py --post --repo "${NAMESPACE}/${REGISTRY}"; then
    die 4 "发布后核对未通过：远端镜像与本地代码不一致，请检查 tag/latest 指向"
  fi
else
  step "4/5  推送 —— 已跳过（加 --push 启用）"
  echo "  手动推送：./push_dockerhub.sh ${NAMESPACE} ${VERSION}"
fi

# ---------- 4c. 部署到生产（可选） ----------
# 为什么默认不部署：这台机器的网络到服务器 22 端口不稳定（/32 直连路由会随
# 换网失效），把"发版"和"上线"绑死会让一次网络抖动卡住整条交付流水线。
# 显式加 --deploy 才做，且部署器自带备份/健康门禁/回滚。
if [ "$DEPLOY" -eq 1 ]; then
  step "4c/5  部署到生产（备份 → 拉取 → 重建 → 健康门禁 → 失败回滚）"
  if ! "$GATE_PY" tools/deploy_release.py --yes; then
    die 5 "部署失败（脚本已尝试回滚到上一版本），详见上方输出"
  fi
  ok "服务器已切换到 ${VERSION}"
fi

# ---------- 4d. 四层一致性巡检 ----------
# 每发一次版都看一眼「服务器跟上没有」：三层绿而服务器停在旧版，
# 正是第三轮复审里最难发现的一类漂移（CI 全绿、线上没修）。
step "一致性巡检：本地 / 仓库 / 镜像 / 服务器"
if ! "$GATE_PY" tools/check_four_layer.py --no-fetch; then
  echo "  ${c_warn}存在漂移${c_reset}：服务器可能仍跑旧版。对齐命令："
  echo "    ${GATE_PY} tools/deploy_release.py --yes"
  echo "  或下次发版直接加 ${c_info}--deploy${c_reset}"
fi

echo ""
echo "${c_ok}══════════════════════════════════════════════${c_reset}"
echo " ${c_ok}✓ 自动交付完成${c_reset}  版本 ${VERSION}"
echo " ${c_ok}══════════════════════════════════════════════${c_reset}"
echo "  提交：$(git log -1 --format='%h %s' | cut -c1-60)"
echo "  镜像：$FINAL_LOCAL（ghcr 多架构，本地与服务器同源）"
echo "  启动：docker run -d -p 8080:80 -v ./data:/app/data $FINAL_LOCAL"
echo ""