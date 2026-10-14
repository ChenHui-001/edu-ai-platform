# ==================== 后端依赖层（单独缓存）====================
FROM python:3.11-slim AS backend-base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    TZ=Asia/Shanghai

# PyMuPDF / numpy 等需要系统库；中文字体用于附件与验证码渲染
# 国内网络下 deb.debian.org 常不可达，优先使用清华镜像源
RUN sed -i 's|deb.debian.org|mirrors.tuna.tsinghua.edu.cn|g; \
            s|security.debian.org|mirrors.tuna.tsinghua.edu.cn|g' \
        /etc/apt/sources.list /etc/apt/sources.list.d/debian.sources 2>/dev/null || true \
    && apt-get update \
    && apt-get install -y --no-install-recommends --fix-missing \
        gcc g++ curl libgl1 libglib2.0-0 fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt


# ==================== 前端构建 ====================
FROM node:20-alpine AS frontend-builder

WORKDIR /app

COPY frontend/package.json ./
RUN npm install --registry=https://registry.npmmirror.com --no-audit --no-fund

COPY frontend/ ./
RUN npm run build


# ==================== 前后端一体镜像（默认产出）=================
# 以 python:3.11-slim 为基底（与 backend-base 同源，site-packages 可直接复用），
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

# 前端静态资源
COPY --from=frontend-builder /app/dist /usr/share/nginx/html
COPY deploy/nginx/default.conf /etc/nginx/conf.d/default.conf
COPY deploy/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

RUN mkdir -p /app/data/uploads /app/data/exports /app/data/logs /app/data/chroma \
    && nginx -t 2>/dev/null || true

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD curl -f http://localhost/api/v1/health || exit 1

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]


# ==================== 可选：纯后端镜像 ====================
FROM backend-base AS backend

WORKDIR /app
COPY backend/app ./app
COPY backend/.env.example ./.env.example
RUN mkdir -p /app/data/uploads /app/data/exports /app/data/logs /app/data/chroma

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
