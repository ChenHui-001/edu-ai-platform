# ==================== 后端依赖层（编译工具装在这里，不进最终镜像）====================
FROM python:3.11-slim AS backend-builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    TZ=Asia/Shanghai

# 国内网络下 deb.debian.org 常不可达，优先使用清华镜像源
RUN sed -i 's|deb.debian.org|mirrors.tuna.tsinghua.edu.cn|g; \
            s|security.debian.org|mirrors.tuna.tsinghua.edu.cn|g' \
        /etc/apt/sources.list /etc/apt/sources.list.d/debian.sources 2>/dev/null || true \
    && apt-get update \
    && apt-get install -y --no-install-recommends --fix-missing \
        gcc g++ \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt


# ==================== 运行层依赖（不含编译器，体积小）====================
FROM python:3.11-slim AS backend-base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    TZ=Asia/Shanghai \
    PATH=/usr/local/bin:$PATH

# libgl1/libglib2.0 为 numpy/PyMuPDF 运行时所需；fonts-noto-cjk 用于中文渲染
RUN sed -i 's|deb.debian.org|mirrors.tuna.tsinghua.edu.cn|g; \
            s|security.debian.org|mirrors.tuna.tsinghua.edu.cn|g' \
        /etc/apt/sources.list /etc/apt/sources.list.d/debian.sources 2>/dev/null || true \
    && apt-get update \
    && apt-get install -y --no-install-recommends --fix-missing \
        curl libgl1 libglib2.0-0 fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

# 从编译层拷贝 site-packages（含 chromadb / langgraph 等纯 wheel 依赖）
COPY --from=backend-builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=backend-builder /usr/local/bin /usr/local/bin


# ==================== 前端构建 ====================
FROM node:20-alpine AS frontend-builder

WORKDIR /app

# 用 package-lock.json + npm ci 保证依赖可复现（npm install 会按 ^ 漂移版本）
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --registry=https://registry.npmmirror.com --no-audit --no-fund

COPY frontend/ ./
RUN npm run build


# ==================== 可选：纯后端镜像（无前端/nginx）====================
# 说明：本阶段必须排在 unified 之前。Docker 默认构建最后一个阶段，
# 若把 backend 放在末尾，`docker build .` 会产出只有 API 的残缺镜像。
# 纯后端镜像需显式指定：docker build --target backend -t <name> .
FROM backend-base AS backend

WORKDIR /app
COPY backend/app ./app
COPY backend/.env.example ./.env.example
# 版本号单一真源：根目录 VERSION 文件。
# 不注入 APP_VERSION 覆盖，让容器内直接读 /app/VERSION；
# 仅当确实要覆盖（如 CI 用 ci-<sha>）时才传 --build-arg APP_VERSION=x.y.z。
# 注意：不要 `ENV APP_VERSION=""` —— buildx 缓存可能让上一轮的值
# （如 latest）残留到新镜像，导致 /health 返回错误版本号。
COPY VERSION ./VERSION
ARG APP_VERSION=""
ENV APP_VERSION=${APP_VERSION}

# ---- 构建溯源信息（发版一致性校验用）----
# 只有版本号是**不够**的：1.0.40 可以构建十次、内容各不相同。
# 必须把「这份镜像到底出自哪个 commit」烧进镜像，才能断言
# 「本地代码 == 镜像代码」。写入 LABEL（可 docker inspect 直读，
# 无需启动容器）与 /app/BUILD_INFO（容器内可自查）两处。
ARG GIT_COMMIT=""
ARG BUILD_TIME=""
LABEL org.opencontainers.image.version=${APP_VERSION} \
      org.opencontainers.image.revision=${GIT_COMMIT} \
      org.opencontainers.image.created=${BUILD_TIME}
RUN printf 'version=%s\ncommit=%s\nbuilt_at=%s\n' \
        "$(cat /app/VERSION 2>/dev/null || echo unknown)" \
        "${GIT_COMMIT:-unknown}" "${BUILD_TIME:-unknown}" \
        > /app/BUILD_INFO

RUN mkdir -p /app/data/uploads /app/data/exports /app/data/logs /app/data/chroma

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]


# ==================== 前后端一体镜像（默认产出，必须是最后一个阶段）====================
# 以 backend-base 为基底（解释器与 site-packages 路径已对齐），
# 再叠加 nginx + supervisord 实现前后端同端口提供服务。
FROM backend-base AS unified

RUN sed -i 's|deb.debian.org|mirrors.tuna.tsinghua.edu.cn|g; \
            s|security.debian.org|mirrors.tuna.tsinghua.edu.cn|g' \
        /etc/apt/sources.list /etc/apt/sources.list.d/debian.sources 2>/dev/null || true \
    && apt-get update \
    && apt-get install -y --no-install-recommends --fix-missing nginx supervisor \
    && rm -f /etc/nginx/sites-available/default /etc/nginx/sites-enabled/default \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ---- 运行用户：固定 UID/GID，避免非 root 运行依赖镜像外账号 ----
# 降权目标只针对 uvicorn：supervisord 与 nginx master 仍需 root ——
# nginx 要绑定特权端口 80 并写 /var/log/nginx，root 降权后无法完成。
# 因此镜像级别**不**写 `USER app`（否则 supervisord 起不来），
# 真正的降权点在 deploy/supervisord.conf 的 [program:backend] user=app。
ARG APP_UID=10001
ARG APP_GID=10001
RUN groupadd -g "${APP_GID}" app \
    && useradd -u "${APP_UID}" -g app -m -d /home/app -s /usr/sbin/nologin app

COPY backend/app ./app
# 版本号单一真源：根目录 VERSION 文件；缺失时才回退到 APP_VERSION build-arg
COPY VERSION ./VERSION
ARG APP_VERSION=""
ENV APP_VERSION=${APP_VERSION}

# ---- 构建溯源信息（与 backend 阶段保持一致，见该阶段注释）----
ARG GIT_COMMIT=""
ARG BUILD_TIME=""
LABEL org.opencontainers.image.version=${APP_VERSION} \
      org.opencontainers.image.revision=${GIT_COMMIT} \
      org.opencontainers.image.created=${BUILD_TIME}
RUN printf 'version=%s\ncommit=%s\nbuilt_at=%s\n' \
        "$(cat /app/VERSION 2>/dev/null || echo unknown)" \
        "${GIT_COMMIT:-unknown}" "${BUILD_TIME:-unknown}" \
        > /app/BUILD_INFO

# ---- 预热 ChromaDB 的默认 embedding 模型（约 79MB）----
# 不预置的话，**每个全新容器首次做向量检索时都要现场下载**，
# 内网/弱网下必然超时，进而拖垮 /edu/knowledge/reindex 等接口。
# 在构建阶段拉一次，运行时直接命中缓存。
#
# 注意：两个源都可能因网络抖动失败（实测官方 S3 偶发 TLS EOF，
# hf-mirror 返回 308 重定向）。任一成功即可；
# 都失败时只告警不中断构建 —— 运行时 ChromaDB 仍会自行下载，
# 配合 REINDEX_TIMEOUT_SEC 硬超时不会拖死调用方。
#
# 缓存目录必须放在 app 用户可读的位置：降权后 uvicorn 的 HOME=/home/app，
# 若仍预置在 /root/.cache/chroma，app 用户根本读不到（/root 是 0700），
# 预热等于白做、首次向量检索仍要现场下载。同时导出 CHROMA_CACHE_DIR，
# 兼容不同 chromadb 版本「读环境变量 / 用 Path.home() 推导」两种实现。
ARG ONNX_URL="https://chroma-onnx-models.s3.amazonaws.com/all-MiniLM-L6-v2/onnx.tar.gz"
ENV CHROMA_CACHE_DIR=/home/app/.cache/chroma
RUN mkdir -p "$CHROMA_CACHE_DIR/onnx_models/all-MiniLM-L6-v2" \
    && ONNX_DIR="$CHROMA_CACHE_DIR/onnx_models/all-MiniLM-L6-v2" \
    && for u in "$ONNX_URL" \
              "https://hf-mirror.com/chroma/all-MiniLM-L6-v2/resolve/main/onnx.tar.gz"; do \
         echo "尝试下载 embedding 模型: $u"; \
         if curl -fsSL --retry 3 --retry-all-errors --max-time 600 \
                 -o /tmp/onnx.tar.gz "$u" \
            && tar -xzf /tmp/onnx.tar.gz -C "$ONNX_DIR" 2>/dev/null \
            && [ -n "$(ls -A "$ONNX_DIR" 2>/dev/null)" ]; then \
             rm -f /tmp/onnx.tar.gz; \
             echo "embedding 模型预置完成（来源: $u）"; \
             break; \
         fi; \
         echo "  来源不可用，尝试下一个"; \
       done \
    && ls -la "$ONNX_DIR" || true

# 前端静态资源
COPY --from=frontend-builder /app/dist /usr/share/nginx/html
COPY deploy/nginx/default.conf /etc/nginx/conf.d/default.conf
COPY deploy/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# 运行目录属主交给 app：降权后的 uvicorn 要在这里写 SQLite / 附件 / 日志。
# 注意 docker-compose 用 ./data:/app/data 绑定挂载会**盖掉**这里的属主，
# 由下面 CMD 在启动时（仍以 root）对挂载目录再做一次 chown。
RUN mkdir -p /app/data/uploads /app/data/exports /app/data/logs /app/data/chroma \
    && chown -R app:app /app/data /home/app/.cache

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD curl -f http://localhost/api/v1/health || exit 1

# ↑ start-period=60s 是单 worker 的实测值。若 supervisord.conf 的 --workers 调到 N>1，
#   必须同步放大到至少 60*N 秒：每个 worker 各自跑一遍 Chroma embedding 预热
#   （main.py 的 start_chroma_warmup，79MB 模型），2 核机器上 CPU 会被占满，
#   /api/v1/health 可能在窗口内回不来 → retries=3 用尽后容器被判 unhealthy
#   并重启，形成「起来就重启」的循环。调 --workers 时请顺手改这一行。

# 容器以 root 启动（supervisord 需要），启动前先修正 data 目录属主，
# 再 exec 成 supervisord —— 避免 PID1 退化成 shell 导致信号收不到。
# supervisord 内部：nginx 以 root 运行，backend 以 app 运行（见 deploy/supervisord.conf）。
CMD ["/bin/sh", "-c", "mkdir -p /app/data/uploads /app/data/exports /app/data/logs /app/data/chroma && chown -R app:app /app/data 2>/dev/null || true; exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf"]
