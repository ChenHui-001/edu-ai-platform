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
# 索引可覆盖：CI（GitHub Actions）走默认 PyPI，国内本机构建走镜像源，
# 避免 files.pythonhosted.org 读超时把构建卡死。重试次数与超时同时放宽。
ARG PIP_INDEX_URL="https://pypi.org/simple"
ARG PIP_EXTRA_INDEX_URL=""
RUN pip install --no-cache-dir --retries 10 --timeout 120 \
        --index-url "$PIP_INDEX_URL" \
        ${PIP_EXTRA_INDEX_URL:+--extra-index-url "$PIP_EXTRA_INDEX_URL"} \
        -r /tmp/requirements.txt \
    && pip uninstall -y \
        kubernetes aiohttp aiohappyeyeballs aiosignal durationpy frozenlist \
        multidict oauthlib propcache python-dateutil requests-oauthlib six \
        websocket-client yarl \
        zstandard hf_xet mmh3 \
    && pip check 2>&1 | grep -v "No broken requirements found" || true

# ---- 阶段 0 镜像瘦身：剔除无用传递依赖（已实测验证）----
# 上面的 pip uninstall 是**卸载真包**，不是装假包。依据与实测见
# backend/requirements.txt 末尾「体积裁剪约束」注释。
#
# 摘出来的包与其体积（实测 2.5.47 镜像）：
#   kubernetes 84MB + aiohttp 9MB + websocket-client/durationpy/
#   requests-oauthlib/oauthlib/six/urllib3*/multidict/yarl/propcache/
#   aiosignal/frozenlist/aiohappyeyeballs/python-dateutil  ≈ 96MB
#   zstandard 24MB（仅 httpx/langsmith 的 try/except 可选路径）
#   hf_xet 11MB（仅 huggingface_hub 的 xet 加速上传）
#   mmh3 1MB
#
# ★ 不能删的（实测依赖图）：
#   requests / urllib3 / certifi / idna / charset-normalizer —— langsmith、
#     tiktoken、httpx 仍在用；attrs —— jsonschema/referencing 仍在用；
#     pyyaml —— chromadb/huggingface_hub/langchain-core 仍在用；
#     typing-extensions / tzdata —— 大半个依赖树共用。
#
# 实测（2.5.47 镜像内真实卸载后）：chromadb create/add/query、langchain +
# langgraph 导入、langsmith 导入、httpx 真实网络请求、uvicorn 真实起服务并
# 响应 HTTP、PyMuPDF/Pillow 中文字体渲染、FastAPI 全栈 —— 全部通过。


# ==================== 运行层依赖（不含编译器，体积小）====================
FROM python:3.11-slim AS backend-base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    TZ=Asia/Shanghai \
    PATH=/usr/local/bin:$PATH \
    HOME=/home/app

# fonts-noto-cjk 用于中文渲染（验证码 + PDF 导出）
#
# ★ 阶段 0 瘦身：原先这里还装了 libgl1 + libglib2.0-0，注释说
#   「为 numpy/PyMuPDF 运行时所需」——**这个说法是错的**。实测：
#   对镜像内**全部** .so 做 ldd 扫描，无任何一个链接 libGL/libglib/
#   libEGL/libgbm；且项目不装 opencv，PyMuPDF 用的是 MuPDF 自带渲染器，
#   不走 OpenGL。装它们的唯一后果是拖进整套 Mesa/LLVM 图形栈：
#     libllvm19 123MB + mesa-libgallium 40MB + libz3-4 26MB ≈ 190MB
#   （libgl1 → libglx0/libglvnd0 → libglx-mesa0 → mesa-libgallium →
#     libllvm19 → libz3-4）
# 去掉后 numpy / PyMuPDF / Pillow / reportlab 全部照常工作（已实测）。
RUN sed -i 's|deb.debian.org|mirrors.tuna.tsinghua.edu.cn|g; \
            s|security.debian.org|mirrors.tuna.tsinghua.edu.cn|g' \
        /etc/apt/sources.list /etc/apt/sources.list.d/debian.sources 2>/dev/null || true \
    && apt-get update \
    && apt-get install -y --no-install-recommends --fix-missing \
        curl fonts-noto-cjk \
    && apt-get purge -y --auto-remove \
        libgl1 libglib2.0-0 libgl1-mesa-glx libgl1-mesa-dri \
        libglx0 libglvnd0 libglx-mesa0 mesa-libgallium libllvm19 \
        libz3-4 libgbm1 libdrm2 libdrm-common libx11-6 libx11-data \
        libxcb1 libxcb-dri3-0 libxcb-glx0 libxcb-present0 libxcb-randr0 \
        libxcb-shm0 libxcb-sync1 libxcb-xfixes0 libxdmcp6 libxext6 \
        libxshmfence1 libxxf86vm1 libsensors-config libsensors5 \
        libvulkan1 libdrm-amdgpu1 libdrm-intel1 libpciaccess0 libedit2 \
    && rm -rf /var/lib/apt/lists/*

# ---- 阶段 0 瘦身：字体只留 Sans，砍掉从未被引用的 Serif ----
# fonts-noto-cjk 带 4 个 .ttc（合计 89MB）：
#   NotoSansCJK-Bold.ttc    19MB  ← app/core/security.py 验证码字体
#   NotoSansCJK-Regular.ttc 18MB  ← app/services/paper_export_service.py PDF 导出
#   NotoSerifCJK-Bold.ttc    26MB  ← 全项目零引用（rg 无命中）
#   NotoSerifCJK-Regular.ttc 25MB  ← 全项目零引用
# 砍掉两个 Serif 文件后，验证码与 PDF 导出的中文渲染照常（已实测）。
RUN rm -f /usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc \
        /usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc \
    && ls -la /usr/share/fonts/opentype/noto/

# 从编译层拷贝 site-packages（含 chromadb / langgraph 等纯 wheel 依赖）
COPY --from=backend-builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=backend-builder /usr/local/bin /usr/local/bin

# ---- 阶段 0 瘦身：剔掉 site-packages 里的 .pyc（实测 134MB）----
# pip 安装时会把 .py 编译成 .pyc 缓存。容器里这些 .pyc 占了 134MB
# （site-packages 共 906MB，其中 916 个 __pycache__ 目录）。
# 代价：进程首次 import 需重新编译，实测启动 1.65s → 2.13s（+0.5s）。
# 容器常驻数小时、只启动一次，这个代价换 134MB 是算盘的。
# 注意 PYTHONDONTWRITEBYTECODE=1 已设，运行时不会再生成新的 .pyc。
RUN find /usr/local/lib/python3.11/site-packages -name "__pycache__" -type d \
        -prune -exec rm -rf {} + \
    && find /usr/local/lib/python3.11/site-packages -name "*.pyc" -delete \
    && echo "pyc cleaned"

# ---- 预置 ChromaDB 的默认 embedding 模型（约 79MB）----
# ★ 阶段 0 修复：原先**只有 unified 阶段**预置 ONNX 模型，backend 阶段
#   没有。结果 `docker build --target backend` 出来的镜像，首次做向量检索
#   会现场下载 79MB（实测 slim-test 容器启动日志里确实在下载），
#   内网/弱网下必然超时，拖垮 /edu/knowledge/reindex 等接口。
#   现在把预置提到 backend-base，两者共用同一份缓存。
#
# ★ chromadb 1.5.9 只认 Path.home()，不读任何环境变量（实测）：
#   chromadb/utils/embedding_functions/onnx_mini_lm_l6_v2.py:39
#     DOWNLOAD_PATH = Path.home() / ".cache" / "chroma" / "onnx_models" / MODEL_NAME
#   因此原来的 `ENV CHROMA_CACHE_DIR=...` **完全无效**（原注释作“兼容两种实现”
#   是误导）。真正生效的开关是 HOME 环境变量 → Path.home()。
#   上面已给 backend-base 设 HOME=/home/app，预置目录也必须是 /home/app/.cache；
#   若预置在 /root/.cache/chroma，app 用户根本读不到（/root 是 0700），
#   预置等于白做、首次向量检索仍要现场下载。
#
# 因此 backend-base 必须先创建 app 用户（统一在 unified 阶段也要用）。
ARG ONNX_URL="https://chroma-onnx-models.s3.amazonaws.com/all-MiniLM-L6-v2/onnx.tar.gz"
RUN groupadd -g 10001 app \
    && useradd -u 10001 -g app -m -d /home/app -s /usr/sbin/nologin app \
    && mkdir -p /home/app/.cache/chroma/onnx_models/all-MiniLM-L6-v2 \
    && ONNX_DIR=/home/app/.cache/chroma/onnx_models/all-MiniLM-L6-v2 \
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
    && chown -R app:app /home/app/.cache \
    && ls -la "$ONNX_DIR" || true


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
# Q-06：迁移体系要能在容器内直接跑（alembic upgrade/stamp），
# 只 COPY app 而不带 alembic.ini + migrations 的话，镜像里没有任何迁移文件，
# 生产上想演进结构就只能回退到手工改库。
COPY backend/alembic.ini ./alembic.ini
COPY backend/migrations ./migrations
COPY backend/.env.example ./.env.example
# 版本号单一真源：根目录 VERSION 文件。
# 不注入 APP_VERSION 覆盖，让容器内直接读 /app/VERSION；
# 仅当确实要覆盖（如 CI 用 ci-<sha>）时才传 --build-arg APP_VERSION=x.y.z。
# 注意：不要 `ENV APP_VERSION=""` —— buildx 缓存可能让上一轮的值
# （如 latest）残留到新镜像，导致 /health 返回错误版本号。
COPY VERSION ./VERSION
# 镜像体积声明（unified 镜像实测）。随代码走，容器内可自查，
# 也供 tools/status_snapshot.py 读取（现状卡「镜像体积」一行的事实源）。
COPY IMAGE_SIZE ./IMAGE_SIZE
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
# app 用户已在 backend-base 阶段创建（ONNX 模型预置需要它），
# 此处不再重复创建（重复 groupadd 会报 "already exists" 并中断构建）。
ARG APP_UID=10001
ARG APP_GID=10001

COPY backend/app ./app
COPY backend/alembic.ini ./alembic.ini
COPY backend/migrations ./migrations
# 版本号单一真源：根目录 VERSION 文件；缺失时才回退到 APP_VERSION build-arg
COPY VERSION ./VERSION
# 镜像体积声明（unified 镜像实测）。随代码走，容器内可自查，
# 也供 tools/status_snapshot.py 读取（现状卡「镜像体积」一行的事实源）。
COPY IMAGE_SIZE ./IMAGE_SIZE
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

# embedding 模型的预置已上移到 backend-base 阶段（见上方）。
# unified 继承 backend-base，因此自动包含预置好的 ONNX 缓存，
# 无需在此复制一份（重复下载会多花 ~15s 构建时间）。

# 前端静态资源
COPY --from=frontend-builder /app/dist /usr/share/nginx/html
COPY deploy/nginx/default.conf /etc/nginx/conf.d/default.conf
COPY deploy/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
# 容器守卫：backend/nginx 重试耗尽被置 FATAL 时主动让容器退出，
# 使 restart 策略生效，避免「容器 Up、全站 502」这种隐蔽故障。
COPY deploy/fatal_guard.py /usr/local/bin/fatal_guard.py
RUN chmod +x /usr/local/bin/fatal_guard.py

# 运行目录属主交给 app：降权后的 uvicorn 要在这里写 SQLite / 附件 / 日志。
# 注意 docker-compose 用 ./data:/app/data 绑定挂载会**盖掉**这里的属主，
# 由下面 CMD 在启动时（仍以 root）对挂载目录再做一次 chown。
RUN mkdir -p /app/data/uploads /app/data/exports /app/data/logs /app/data/chroma \
    && chown -R app:app /app/data /home/app/.cache

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD curl -f http://localhost/api/v1/ready || exit 1

# ↑ start-period=60s 是单 worker 的实测值。若 supervisord.conf 的 --workers 调到 N>1，
#   必须同步放大到至少 60*N 秒：每个 worker 各自跑一遍 Chroma embedding 预热
#   （main.py 的 start_chroma_warmup，79MB 模型），2 核机器上 CPU 会被占满，
#   /api/v1/health 可能在窗口内回不来 → retries=3 用尽后容器被判 unhealthy
#   并重启，形成「起来就重启」的循环。调 --workers 时请顺手改这一行。

# 容器以 root 启动（supervisord 需要），启动前先修正 data 目录属主，
# 再 exec 成 supervisord —— 避免 PID1 退化成 shell 导致信号收不到。
# supervisord 内部：nginx 以 root 运行，backend 以 app 运行（见 deploy/supervisord.conf）。
CMD ["/bin/sh", "-c", "mkdir -p /app/data/uploads /app/data/exports /app/data/logs /app/data/chroma && chown -R app:app /app/data 2>/dev/null || true; exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf"]
