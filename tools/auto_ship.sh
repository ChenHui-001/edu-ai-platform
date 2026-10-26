#!/usr/bin/env bash
# ================================================================
# 九年义务教育 AI 学习管理系统 —— 自动交付流水线
#
# 流程：改动检测 → 端到端回归(源码直跑) → git commit → git push
#       → 等待 CI 发布 → 拉取 ghcr 多架构镜像 → (可选)复制到 Docker Hub
# 设计原则：**测试不过就不提交、不推送**（fail fast，绝不带病上线）
#
# ★ 镜像唯一来源 = CI 构建的 ghcr 多架构镜像（ghcr.io/chenhui-001/edu-ai-platform）
#   本机**不编译任何镜像**：回归用源码直跑，正式镜像等 CI 发布后 pull。
#   好处：本地与服务器跑的是同一份（sha256 逐字节相同），杜绝
#   「同版本号、不同内容」的两份镜像漂移。
#
# 用法：
#   ./tools/auto_ship.sh                  # 全流程（不推 Docker Hub）
#   ./tools/auto_ship.sh --push           # 全流程 + 复制到 Docker Hub（多架构）
#   ./tools/auto_ship.sh --no-push        # 不推 git（离线/临时验证用）
#   ./tools/auto_ship.sh --msg "xxx"      # 自定义提交信息
#   ./tools/auto_ship.sh --skip-test      # 跳过测试（仅提交，慎用）
#   ./tools/auto_ship.sh --bump patch     # 版本号 +1（1.0.8 -> 1.0.9）后交付
#   ./tools/auto_ship.sh --dry-run        # 只跑测试，不提交不拉镜像
#   ./tools/auto_ship.sh --stages admin teacher
#                                         # 只跑指定阶段（日常迭代用，快 5~10 倍）
#   ./tools/auto_ship.sh --stages auto    # 按 git 改动自动选阶段
#
# ⚠️ 何时**必须**全量（不加 --stages）：
#   1) 发版前；2) 改了 e2e_framework.py / 公共组件 / 数据模型；
#   3) 连续改 3 个以上模块；4) CI 红了要在本地复现。
#
# 退出码：0 成功 / 1 测试失败 / 2 提交失败 / 3 镜像拉取失败 / 4 无改动
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
# ghcr 是**唯一镜像来源**：镜像由 CI 构建（多架构 amd64+arm64），
# 本地与服务器拉同一份，保证 sha256 逐字节一致。本地不再编译镜像。
GHCR_IMAGE="${GHCR_IMAGE:-ghcr.io/chenhui-001/edu-ai-platform}"

while [ $# -gt 0 ]; do
  case "$1" in
    --push)      PUSH=1 ;;
    --no-push)   NO_PUSH=1 ;;
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
  "$GATE_PY" tools/check_model_fk.py || GATE_RC=1
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
    die 1 "静态门禁未通过（硬编码地址 / 恒真断言 / 时间契约 / 模型输出写外键 / F 类缺陷），修复后再交付"
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
# 回归**直接跑工作区源码**（uvicorn + 独立临时库），不构建任何本地镜像。
# 理由：镜像的唯一来源是 CI 构建的 ghcr 多架构镜像 —— 本地与服务器必须跑
# 同一份（sha256 逐字节相同），本地再编一份只会产生「两个同名不同内容的
# 镜像」这种最危险的漂移。回归要验的是「即将提交的代码」，源码直跑更准确。
if [ "$SKIP_TEST" -eq 1 ]; then
  step "1/5  端到端回归 —— 已跳过（--skip-test）"
  [ "$c_warn" ] && echo "  ${c_warn}⚠ 跳过测试直接交付，存在带病上线风险${c_reset}"
else
  step "1/5  端到端回归（源码直跑，不构建镜像）"

  # 1.1 跑回归：复用 run_e2e.sh（内部已处理残留进程检查 → mktemp 独立数据目录
  #      → 自动选空闲端口 → 校验 /health 的 server_time 契约 → 跑 run_all.py → 清理）
  PY="${PYTHON_BIN:-python3}"
  command -v "$PY" >/dev/null 2>&1 || PY=python
  TEST_LOG="/tmp/autoship_test.log"
  if [ -n "$STAGES" ] && [ "$STAGES" != "ALL" ]; then
    echo "  运行 tests/run_all.py ${STAGES}（仅选定阶段）..."
    PYTHON_BIN="$PY" bash tools/run_e2e.sh $STAGES > "$TEST_LOG" 2>&1
  else
    echo "  运行 tests/run_all.py（全量）..."
    PYTHON_BIN="$PY" bash tools/run_e2e.sh > "$TEST_LOG" 2>&1
  fi
  TEST_RC=$?
  tail -25 "$TEST_LOG"

  if [ $TEST_RC -ne 0 ]; then
    echo ""
    echo "  ${c_err}失败用例明细：${c_reset}"
    grep -A100 "失败用例" "$TEST_LOG" | head -40
    echo ""
    echo "  ${c_err}测试未通过 —— 已中止，不提交、不推送${c_reset}"
    echo "  完整日志: ${TEST_LOG}"
    exit 1
  fi
  PASSED="$(grep -o '通过 [0-9]*' "$TEST_LOG" | tail -1 | grep -o '[0-9]*')"
  ok "端到端回归全部通过（${PASSED:-?} 项）"
fi

if [ "$DRY_RUN" -eq 1 ]; then
  step "dry-run 模式 —— 测试已跑完，跳过提交与镜像拉取"
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

echo ""
echo "${c_ok}══════════════════════════════════════════════${c_reset}"
echo " ${c_ok}✓ 自动交付完成${c_reset}  版本 ${VERSION}"
echo " ${c_ok}══════════════════════════════════════════════${c_reset}"
echo "  提交：$(git log -1 --format='%h %s' | cut -c1-60)"
echo "  镜像：$FINAL_LOCAL（ghcr 多架构，本地与服务器同源）"
echo "  启动：docker run -d -p 8080:80 -v ./data:/app/data $FINAL_LOCAL"
echo ""