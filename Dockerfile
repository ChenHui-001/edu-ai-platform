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

COPY frontend/package.json ./
RUN npm install --registry=https://registry.npmmirror.com --no-audit --no-fund

COPY frontend/ ./
RUN npm run build


# ==================== 可选：纯后端镜像（无前端/nginx）====================
# 说明：本阶段必须排在 unified 之前。Docker 默认构建最后一个阶段，
# 若把 backend 放在末尾，`docker build .` 会产出只有 API 的残缺镜像。
# 纯后端镜像需显式指定：docker build --target backend -t <name> .
FROM backend-base AS backend

WORKDIR /app
COPY backend/app ./app
# 版本号单一真源：根目录 VERSION 文件；缺失时回退到 APP_VERSION build-arg
COPY VERSION ./VERSION
ARG APP_VERSION=""
ENV APP_VERSION=${APP_VERSION}
COPY backend/.env.example ./.env.example
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

COPY backend/app ./app
# 版本号单一真源：根目录 VERSION 文件；缺失时回退到 APP_VERSION build-arg
COPY VERSION ./VERSION
ARG APP_VERSION=""
ENV APP_VERSION=${APP_VERSION}

# 前端静态资源
COPY --from=frontend-builder /app/dist /usr/share/nginx/html
COPY deploy/nginx/default.conf /etc/nginx/conf.d/default.conf
COPY deploy/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

RUN mkdir -p /app/data/uploads /app/data/exports /app/data/logs /app/data/chroma

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD curl -f http://localhost/api/v1/health || exit 1

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
