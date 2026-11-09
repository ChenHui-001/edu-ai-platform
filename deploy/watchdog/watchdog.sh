#!/usr/bin/env bash
# ================================================================
# 四层一致性巡检 —— 服务器侧守卫（跑在 186.241.77.194 上）
#
# 为什么要有它：本地/仓库/镜像三层由 CI 与发版脚本守着，但**第四层
# （服务器跑的是哪一版）没有任何东西在看**。真实事故就是镜像发得好好的，
# 服务器停在三天前的版本，而所有 CI 都是绿的。
#
# 判定逻辑（每 5 分钟一次）：
#   1. 容器活着且 healthy            —— 否则 DOWN
#   2. 容器 version == 仓库 master VERSION
#        → 一致：OK（只在状态变化时写日志，避免刷屏）
#        → 不一致且 registry 已有该标签：DRIFT（可部署）
#        → 不一致但 registry 还没有：BUILDING（CI 还在构建，属正常窗口）
#
# 有意**不做自动部署**：无人值守时自动重建会把「迁移失败 + 备份缺失」
# 这种事故放大成「整站打不开」。漂移只告警，实际部署走仓库内
# `tools/deploy_release.py`（带备份/健康门禁/回滚）。
#
# 用法：
#   bash watchdog.sh            # 单次巡检（systemd timer 调用）
#   bash watchdog.sh --verbose  # 无论状态是否变化都打印
# ================================================================
set -uo pipefail

APP="${APP:-edu-platform}"
PORT="${PORT:-8081}"
GHCR_IMAGE="${GHCR_IMAGE:-ghcr.io/chenhui-001/edu-ai-platform}"
RAW_BASE="${RAW_BASE:-https://raw.githubusercontent.com/ChenHui-001/edu-ai-platform/master}"
BASE_DIR="${BASE_DIR:-/opt/edu-ai-platform}"
LOG="${LOG:-$BASE_DIR/logs/watchdog.log}"
STATE="${STATE:-$BASE_DIR/watchdog.state}"
VERBOSE="${1:-}"

mkdir -p "$(dirname "$LOG")"
ts="$(date '+%F %T')"

say() {
  local line="[$ts] $*"
  echo "$line"
  echo "$line" >>"$LOG"
}

# 状态只在变化时落日志：稳定运行时一天 288 次巡检不应产生 288 行噪音
emit() {
  local status="$1" msg="$2"
  local prev=""
  [ -f "$STATE" ] && prev="$(cat "$STATE" 2>/dev/null)"
  if [ "$status" != "$prev" ] || [ "$VERBOSE" = "--verbose" ]; then
    say "[$status] $msg"
    echo "$status" >"$STATE"
    if [ -n "${WATCHDOG_WEBHOOK:-}" ]; then
      curl -fsS -m 8 -X POST -H 'Content-Type: application/json' \
        -d "{\"status\":\"$status\",\"host\":\"$(hostname)\",\"msg\":\"$msg\"}" \
        "$WATCHDOG_WEBHOOK" >/dev/null 2>&1 || say "[WARN] webhook 推送失败"
    fi
  fi
}

# ---- 1. 容器与健康
if ! docker ps --format '{{.Names}}' | grep -qx "$APP"; then
  emit "DOWN" "容器 $APP 不存在或未运行（docker ps 无此名字）"
  exit 1
fi

health="$(curl -s -m 6 "http://127.0.0.1:$PORT/api/v1/health" 2>/dev/null)"
if ! printf '%s' "$health" | grep -q '"healthy"'; then
  emit "DOWN" "健康检查未返回 healthy：${health:0:120}"
  exit 1
fi

# ---- 2. 容器内版本（BUILD_INFO 是唯一硬依据，health 里的 version 同源）
cur="$(docker exec "$APP" sh -c 'cat /app/BUILD_INFO 2>/dev/null' 2>/dev/null \
        | awk -F= '/^version=/{print $2}')"
cur="${cur:-unknown}"

# ---- 3. 仓库 master 的版本（唯一真源）
want="$(curl -fsS -m 10 "$RAW_BASE/VERSION" 2>/dev/null | tr -d '\r\n ')"
if [ -z "$want" ]; then
  emit "UNKNOWN" "取不到仓库 VERSION（网络/仓库不可达），当前容器 $cur"
  exit 0
fi

if [ "$cur" = "$want" ]; then
  emit "OK" "一致：容器 $cur == 仓库 $want"
  exit 0
fi

# ---- 4. 不一致：先确认镜像是否已构建（发版瞬间会有一段构建窗口）
if docker manifest inspect "$GHCR_IMAGE:$want" >/dev/null 2>&1; then
  emit "DRIFT" "服务器 $cur 落后于仓库 $want（镜像已就绪，可执行 tools/deploy_release.py --yes）"
else
  emit "BUILDING" "仓库已到 $want，服务器仍 $cur，镜像尚未发布（CI 构建窗口内属正常）"
fi

exit 0
