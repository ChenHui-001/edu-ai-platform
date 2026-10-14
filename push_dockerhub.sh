#!/usr/bin/env bash
# ================================================================
# 九年义务教育 AI 学习管理系统 - Docker Hub 一键推送脚本
#
# 用法：
#   ./push_dockerhub.sh <DockerHub用户名>
#   例：./push_dockerhub.sh chenhuichen
#
# 前置条件：
#   1. 已执行 docker login（Docker Hub 现已强制要求 PAT，密码登录会报 insufficient_scope）
#      docker login --username <用户名> --password-stdin <<< '<你的PAT>'
#   2. 本地已有镜像 edu-ai-platform:1.0.0
#      docker build --target unified -t edu-ai-platform:1.0.0 .
# ================================================================

set -euo pipefail

NAMESPACE="${1:-}"
TAG="${2:-1.0.0}"
IMAGE="edu-ai-platform:${TAG}"

if [ -z "$NAMESPACE" ]; then
  echo "用法: $0 <DockerHub用户名> [标签，默认 1.0.0]"
  exit 1
fi

cd "$(dirname "$0")"

echo ">>> 检查本地镜像 ${IMAGE}"
if ! docker image inspect "$IMAGE" >/dev/null 2>&1; then
  echo "镜像不存在，开始构建..."
  docker build --target unified -t "$IMAGE" .
fi

REMOTE="${NAMESPACE}/edu-ai-platform:${TAG}"

echo ">>> 推送前验证 Docker Hub 登录状态"
if ! docker info 2>/dev/null | grep -q "Username:"; then
  echo "未登录 Docker Hub，请先执行："
  echo "  docker login --username ${NAMESPACE} --password-stdin <<< '<你的PAT>'"
  exit 1
fi

echo ">>> 打标签：${IMAGE} -> ${REMOTE}"
docker tag "$IMAGE" "$REMOTE"

echo ">>> 同时打 latest 标签"
docker tag "$IMAGE" "${NAMESPACE}/edu-ai-platform:latest"

echo ">>> 推送到 Docker Hub"
docker push "$REMOTE"
docker push "${NAMESPACE}/edu-ai-platform:latest"

echo ""
echo ">>> 推送完成"
echo "  docker pull ${REMOTE}"
echo "  docker pull ${NAMESPACE}/edu-ai-platform:latest"
echo ""
echo "  启动：docker run -d -p 8080:80 -v ./data:/app/data ${REMOTE}"
echo "  或：  docker compose up -d"