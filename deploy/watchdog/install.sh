#!/usr/bin/env bash
# ================================================================
# 安装 / 卸载服务器侧一致性巡检（systemd timer，每 5 分钟一次）
#
# 用法（在服务器上以 root 执行）：
#   bash install.sh              # 安装并启动
#   bash install.sh --remove     # 停止并删除
#   bash install.sh --status     # 查看状态与最近日志
#
# 从本地一键安装（仓库根目录）：
#   ssh root@186.241.77.194 'bash -s' < deploy/watchdog/install.sh
#
# 注意：本脚本只装**告警**，不自动部署。部署仍走 tools/deploy_release.py
# （备份 + 健康门禁 + 回滚），避免无人值守时把事故放大。
# ================================================================
set -euo pipefail

BASE_DIR="${BASE_DIR:-/opt/edu-ai-platform}"
DEST="$BASE_DIR/watchdog"
UNIT="/etc/systemd/system/edu-watchdog.service"
TIMER="/etc/systemd/system/edu-watchdog.timer"
SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

case "${1:-}" in
  --status)
    systemctl is-active edu-watchdog.timer || true
    systemctl list-timers edu-watchdog.timer --no-pager 2>/dev/null || true
    echo "--- 最近 15 行巡检日志 ---"
    tail -n 15 "$BASE_DIR/logs/watchdog.log" 2>/dev/null || echo "(暂无日志)"
    exit 0
    ;;
  --remove)
    systemctl disable --now edu-watchdog.timer 2>/dev/null || true
    rm -f "$UNIT" "$TIMER"
    systemctl daemon-reload
    echo "已移除 edu-watchdog（$DEST 保留，可手工删除）"
    exit 0
    ;;
esac

mkdir -p "$DEST" "$BASE_DIR/logs"
install -m 0755 "$SRC_DIR/watchdog.sh" "$DEST/watchdog.sh"

cat >"$UNIT" <<'EOF'
[Unit]
Description=新芽学堂 四层一致性巡检（服务器版本 vs 仓库 master）
Documentation=https://github.com/ChenHui-001/edu-ai-platform
After=docker.service

[Service]
Type=oneshot
ExecStart=/opt/edu-ai-platform/watchdog/watchdog.sh
TimeoutStartSec=120
# WATCHDOG_WEBHOOK 留空则不推送；填企业微信/钉钉机器人地址即可收告警
Environment=WATCHDOG_WEBHOOK=
EOF

cat >"$TIMER" <<'EOF'
[Unit]
Description=每 5 分钟检查一次服务器与仓库版本是否一致

[Timer]
OnBootSec=2min
OnUnitActiveSec=5min
AccuracySec=30s
Unit=edu-watchdog.service

[Install]
WantedBy=timers.target
EOF

systemctl daemon-reload
systemctl enable --now edu-watchdog.timer
sleep 1
systemctl start edu-watchdog.service || true

echo "已安装："
systemctl list-timers edu-watchdog.timer --no-pager | head -3
echo "--- 首次巡检输出 ---"
tail -n 5 "$BASE_DIR/logs/watchdog.log" 2>/dev/null || echo "(日志稍后生成)"
echo
echo "改告警地址：编辑 $UNIT 里的 WATCHDOG_WEBHOOK，然后 systemctl daemon-reload && systemctl restart edu-watchdog.timer"
