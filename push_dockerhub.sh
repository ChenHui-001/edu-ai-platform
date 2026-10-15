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
#   2. 本地已有镜像（标签默认读根目录 VERSION 文件，为版本号唯一真源）
#      docker build --target unified -t edu-ai-platform:$(cat VERSION) .
# ================================================================

set -euo pipefail

cd "$(dirname "$0")"

NAMESPACE="${1:-}"
# 标签默认取根目录 VERSION（唯一真源），其次取环境变量 IMAGE_TAG
TAG="${2:-$(cat VERSION 2>/dev/null || echo "${IMAGE_TAG:-latest}")}"
IMAGE="edu-ai-platform:${TAG}"

if [ -z "$NAMESPACE" ]; then
  echo "用法: $0 <DockerHub用户名> [标签，默认读 VERSION 文件]"
  exit 1
fi

echo ">>> 版本号真源 VERSION = ${TAG}"

echo ">>> 检查本地镜像 ${IMAGE}"
if ! docker image inspect "$IMAGE" >/dev/null 2>&1; then
  echo "镜像不存在，开始构建..."
  docker build --target unified -t "$IMAGE" .
fi

REMOTE="${NAMESPACE}/edu-ai-platform:${TAG}"

# Docker Hub 在国内网络下经常出现瞬时 EOF（auth.docker.io/token 或
# registry-1.docker.io 的 Head 请求），单个 blob 失败即中断整次推送。
# 这里对每个标签做最多 3 次重试，已上传的分层会被复用，重试成本很低。
push_with_retry() {
  local remote="$1"
  for i in 1 2 3; do
    echo "    推送 ${remote}（第 ${i}/3 次）..."
    if docker push "$remote" 2>&1 | tail -3; then
      if docker manifest inspect "$remote" >/dev/null 2>&1; then
        echo "    ✔ ${remote} 推送成功"
        return 0
      fi
    fi
    [ "$i" -lt 3 ] && echo "    网络异常，${i} 秒后重试..." && sleep 8
  done
  return 1
}

echo ">>> 推送前验证 Docker Hub 登录状态"
if ! docker info 2>/dev/null | grep -q "Username:"; then
  echo "未登录 Docker Hub，请先执行："
  echo "  docker login --username ${NAMESPACE} --password-stdin <<< '<你的PAT>'"
  exit 1
fi

echo ">>> 打标签：${IMAGE} -> ${REMOTE}"
docker tag "$IMAGE" "$REMOTE"
docker tag "$IMAGE" "${NAMESPACE}/edu-ai-platform:latest"

echo ">>> 推送到 Docker Hub"
FAILED=""
push_with_retry "$REMOTE" || FAILED="${FAILED} ${REMOTE}"

# latest 失败不影响版本标签可用性，只告警不中断
push_with_retry "${NAMESPACE}/edu-ai-platform:latest" \
  || FAILED="${FAILED} ${NAMESPACE}/edu-ai-platform:latest"

if [ -n "$FAILED" ]; then
  echo ""
  echo ">>> 部分标签推送失败：${FAILED}"
  echo "    网络恢复后可单独重推：docker push <标签>"
  echo "    已成功的标签不受影响，可正常拉取使用。"
  exit 1
fi

echo ""
echo ">>> 推送完成"
echo "  docker pull ${REMOTE}"
echo "  docker pull ${NAMESPACE}/edu-ai-platform:latest"
echo ""
echo "  启动：docker run -d -p 8080:80 -v ./data:/app/data ${REMOTE}"
echo "  或：  docker compose up -d"