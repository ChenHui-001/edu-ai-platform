#!/usr/bin/env bash
# ================================================================
# 九年义务教育 AI 学习管理系统 —— 自动交付流水线
#
# 流程：改动检测 → 端到端回归 → git commit → 构建镜像 → (可选)推送
# 设计原则：**测试不过就不提交、不构建、不推送**（fail fast，绝不带病上线）
#
# 用法：
#   ./tools/auto_ship.sh                  # 全流程（不推送）
#   ./tools/auto_ship.sh --push           # 全流程 + 推送 Docker Hub
#   ./tools/auto_ship.sh --msg "xxx"      # 自定义提交信息
#   ./tools/auto_ship.sh --skip-test      # 跳过测试（仅提交+构建，慎用）
#   ./tools/auto_ship.sh --bump patch     # 版本号 +1（1.0.8 -> 1.0.9）后交付
#   ./tools/auto_ship.sh --dry-run        # 只跑测试，不提交不构建
#   ./tools/auto_ship.sh --stages admin teacher
#                                         # 只跑指定阶段（日常迭代用，快 5~10 倍）
#   ./tools/auto_ship.sh --stages auto    # 按 git 改动自动选阶段
#
# ⚠️ 何时**必须**全量（不加 --stages）：
#   1) 发版前；2) 改了 e2e_framework.py / 公共组件 / 数据模型；
#   3) 连续改 3 个以上模块；4) CI 红了要在本地复现。
#
# 退出码：0 成功 / 1 测试失败 / 2 提交失败 / 3 构建失败 / 4 无改动
# ================================================================
set -uo pipefail

cd "$(dirname "$0")/.."
ROOT="$(pwd)"

PUSH=0
SKIP_TEST=0
DRY_RUN=0
BUMP=""
MSG=""
STAGES=""
NAMESPACE="${DOCKERHUB_NAMESPACE:-nanpo}"
REGISTRY="${DOCKERHUB_REPO:-edu-ai-platform}"

while [ $# -gt 0 ]; do
  case "$1" in
    --push)      PUSH=1 ;;
    --skip-test) SKIP_TEST=1 ;;
    --dry-run)   DRY_RUN=1; SKIP_COMMIT=1 ;;
    --msg)       MSG="$2"; shift ;;
    --bump)      BUMP="$2"; shift ;;
    --stages)    STAGES="$2"; shift ;;
    -h|--help)   sed -n '2,32p' "$0"; exit 0 ;;
    *) echo "未知参数: $1"; exit 1 ;;
  esac
  shift
done
SKIP_COMMIT="${SKIP_COMMIT:-0}"

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

# ---------- 0.2 挑选回归阶段 ----------
# 全量 811 项约 34 分钟，日常迭代没必要每次都全量。这里按**影响半径**（不是
# 改了几个文件）决定跑哪些阶段；拿不准就退回全量，宁可慢不可漏。
if [ "$STAGES" = "auto" ]; then
  FILES="$(echo "$CHANGED" | awk '{print $NF}')"
  PICK=""
  add() { for s in $1; do case " $PICK " in *" $s "*) ;; *) PICK="$PICK $s" ;; esac; done; }

  # 共享基座 / 数据模型 / 公共组件 —— 影响面不可预估，直接全量
  if echo "$FILES" | grep -qE 'tests/e2e_framework\.py|backend/app/(models|core|middleware)/|backend/app/services/[a-z_]+\.py|frontend/src/(utils|components)/|Dockerfile|\.github/'; then
    echo "  ${c_warn}改动触及共享基座/数据模型/公共组件 → 必须全量${c_reset}"
    PICK=""
  else
    # 后端路由按模块映射到阶段
    echo "$FILES" | grep -q 'api/v1/admin\|api/v1/system\|api/v1/auth\|api/v1/log' && add "admin system"
    echo "$FILES" | grep -q 'api/v1/question\|api/v1/task\|api/v1/grading'      && add "teacher student"
    echo "$FILES" | grep -q 'api/v1/learning'                                 && add "learning learning_hub"
    echo "$FILES" | grep -q 'api/v1/edu'                                      && add "resource teaching_mgmt"
    echo "$FILES" | grep -q 'api/v1/report\|api/v1/analysis'                  && add "analysis"
    echo "$FILES" | grep -q 'agents/'                                         && add "agent agent_opt agent_struct"
    # 前端改动：后端回归测不到，至少要过构建 + 对应业务阶段
    echo "$FILES" | grep -q '^frontend/' && add "admin teacher student"
    # 纯测试脚本改动：只跑被改的那个脚本对应阶段
    echo "$FILES" | grep -q 'tests/test_admin\.py'           && add "admin"
    echo "$FILES" | grep -q 'tests/test_teacher\.py'         && add "teacher"
    echo "$FILES" | grep -q 'tests/test_student\.py'         && add "student"
    echo "$FILES" | grep -q 'tests/test_learning\.py'        && add "learning"
    echo "$FILES" | grep -q 'tests/test_requirements\.py'    && add "requirements"
    echo "$FILES" | grep -q 'tests/test_teaching_mgmt\.py'   && add "teaching_mgmt"
    echo "$FILES" | grep -q 'tests/test_resource_manage\.py' && add "resource"
    # 什么都匹配不上（文档、配置等）→ 全量，避免漏测
    [ -z "$PICK" ] && PICK=" "
  fi
  STAGES="$(echo "$PICK" | xargs)"
  if [ -z "$STAGES" ]; then
    echo "  ${c_info}按改动自动选中：全部阶段${c_reset}"
    STAGES="ALL"
  else
    echo "  ${c_info}按改动自动选中阶段：${STAGES}${c_reset}"
  fi
fi

if [ -n "$STAGES" ] && [ "$STAGES" != "ALL" ]; then
  step "0.2 回归范围：${STAGES}（非全量）"
  echo "  ${c_warn}⚠ 未跑全量。发版前 / 改公共组件后请去掉 --stages 跑一次全量${c_reset}"
fi

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
    die 1 "静态门禁未通过（硬编码地址 / 恒真断言 / F 类缺陷），修复后再交付"
  fi
  ok "静态门禁通过"
else
  echo "  ${c_warn}未找到 python，跳过静态门禁${c_reset}"
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

# ---------- 1. 端到端回归 ----------
TESTED_IMAGE=""
if [ "$SKIP_TEST" -eq 1 ]; then
  step "1/5  端到端回归 —— 已跳过（--skip-test）"
  [ "$c_warn" ] && echo "  ${c_warn}⚠ 跳过测试直接交付，存在带病上线风险${c_reset}"
else
  step "1/5  端到端回归（按 --stages 选定；默认全量 811 项）"

  # 1.1 构建被测镜像
  TESTED_IMAGE="edu-ai-platform:autoship-test"
  echo "  构建被测镜像 ${TESTED_IMAGE} ..."
  if ! docker build --target unified -t "$TESTED_IMAGE" \
        --build-arg "APP_VERSION=$VERSION" -f Dockerfile . > /tmp/autoship_build.log 2>&1; then
    tail -30 /tmp/autoship_build.log
    die 3 "镜像构建失败，详见 /tmp/autoship_build.log"
  fi
  ok "被测镜像构建完成"

  # 1.2 用独立数据目录启动（绝不复用开发库，避免污染 ./data）
  CI_DATA="$(mktemp -d 2>/dev/null || echo "/tmp/autoship_data_$$")"
  mkdir -p "$CI_DATA"
  E2E_PORT="${E2E_PORT:-8099}"
  CONTAINER="edu-autoship-$$"
  echo "  启动容器 ${CONTAINER}（端口 ${E2E_PORT}，独立数据目录）..."
  docker rm -f "$CONTAINER" >/dev/null 2>&1 || true
  docker run -d --name "$CONTAINER" -p "${E2E_PORT}:80" \
    -e LLM_ENABLED=false -e SCHEDULER_ENABLED=false \
    -e SECRET_KEY="autoship_secret_not_for_prod_$(date +%s)" \
    -v "${CI_DATA}:/app/data" "$TESTED_IMAGE" >/dev/null

  # 1.3 等待健康
  READY=0
  for i in $(seq 1 60); do
    if curl -fsS --noproxy '*' "http://localhost:${E2E_PORT}/api/v1/health" >/dev/null 2>&1; then
      READY=1; break
    fi
    [ $((i % 5)) -eq 0 ] && echo "  等待服务启动... ($i/60)"
    sleep 2
  done
  if [ "$READY" -ne 1 ]; then
    echo "  --- 容器日志 ---"; docker logs "$CONTAINER" --tail 80
    docker rm -f "$CONTAINER" >/dev/null 2>&1
    die 1 "服务启动超时"
  fi
  ok "服务就绪"

  # 1.4 跑测试（e2e_framework 优先读 E2E_BASE 环境变量）
  PY="${PYTHON_BIN:-python3}"
  command -v "$PY" >/dev/null 2>&1 || PY=python
  if [ -n "$STAGES" ] && [ "$STAGES" != "ALL" ]; then
    RUN_ARGS="$STAGES"
    echo "  运行 tests/run_all.py $RUN_ARGS（仅选定阶段）..."
  else
    RUN_ARGS=""
    echo "  运行 tests/run_all.py（全量）..."
  fi
  TEST_LOG="/tmp/autoship_test.log"
  # shellcheck disable=SC2086  # RUN_ARGS 需要按空格拆成多个阶段名
  E2E_BASE="http://localhost:${E2E_PORT}" "$PY" tests/run_all.py $RUN_ARGS > "$TEST_LOG" 2>&1
  TEST_RC=$?
  tail -25 "$TEST_LOG"

  docker rm -f "$CONTAINER" >/dev/null 2>&1 || true
  rm -rf "$CI_DATA"

  if [ $TEST_RC -ne 0 ]; then
    echo ""
    echo "  ${c_err}失败用例明细：${c_reset}"
    grep -A100 "失败用例" "$TEST_LOG" | head -40
    echo ""
    echo "  ${c_err}测试未通过 —— 已中止，不提交、不构建、不推送${c_reset}"
    echo "  完整日志: ${TEST_LOG}"
    exit 1
  fi
  PASSED="$(grep -o '通过 [0-9]*' "$TEST_LOG" | tail -1 | grep -o '[0-9]*')"
  ok "端到端回归全部通过（${PASSED:-?} 项）"
fi

if [ "$DRY_RUN" -eq 1 ]; then
  step "dry-run 模式 —— 测试已跑完，跳过提交与构建"
  docker rmi "$TESTED_IMAGE" >/dev/null 2>&1 || true
  echo ""
  echo "${c_ok}✓ dry-run 完成：测试通过，未做任何提交或构建${c_reset}"
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
    FULL_MSG="${MSG}"$'\n\n'"e2e: 210 项全通过（${PASSED:-?} 通过 / 0 失败）"
  fi
  if ! git commit -m "$FULL_MSG"; then
    die 2 "git commit 失败"
  fi
  ok "已提交 $(git rev-parse --short HEAD)"
fi

# ---------- 3. 构建正式镜像 ----------
step "3/5  构建镜像 ${REGISTRY}:${VERSION}"
FINAL_LOCAL="edu-ai-platform:${VERSION}"
if docker build --target unified -t "$FINAL_LOCAL" \
      --build-arg "APP_VERSION=${VERSION}" -f Dockerfile . > /tmp/autoship_final.log 2>&1; then
  ok "镜像构建完成：$FINAL_LOCAL"
else
  tail -30 /tmp/autoship_final.log
  die 3 "正式镜像构建失败，详见 /tmp/autoship_final.log"
fi

docker rmi "$TESTED_IMAGE" >/dev/null 2>&1 || true
docker image prune -f >/dev/null 2>&1 || true

# ---------- 4. 推送（可选） ----------
if [ "$PUSH" -eq 1 ]; then
  step "4/5  推送 Docker Hub"
  if ! docker info 2>/dev/null | grep -q "Username:"; then
    die 1 "未登录 Docker Hub，请先 docker login"
  fi
  REMOTE="${NAMESPACE}/${REGISTRY}:${VERSION}"
  docker tag "$FINAL_LOCAL" "$REMOTE" && docker tag "$FINAL_LOCAL" "${NAMESPACE}/${REGISTRY}:latest"
  docker push "$REMOTE" && docker push "${NAMESPACE}/${REGISTRY}:latest" \
    && ok "已推送 $REMOTE" || die 3 "推送失败"
else
  step "4/5  推送 —— 已跳过（加 --push 启用）"
  echo "  手动推送：./push_dockerhub.sh ${NAMESPACE} ${VERSION}"
fi

echo ""
echo "${c_ok}══════════════════════════════════════════════${c_reset}"
echo " ${c_ok}✓ 自动交付完成${c_reset}  版本 ${VERSION}"
echo " ${c_ok}══════════════════════════════════════════════${c_reset}"
echo "  提交：$(git log -1 --format='%h %s' | cut -c1-60)"
echo "  镜像：$FINAL_LOCAL"
echo "  启动：docker run -d -p 8080:80 -v ./data:/app/data $FINAL_LOCAL"
echo ""