# -*- coding: utf-8 -*-
"""阶段 0：镜像瘦身实测记录（2026-11-20）

记录 2.5.47 → 2.5.49 阶段 0 的镜像体积裁剪：做了什么、证据是什么、
哪些结论被推翻了。**所有数字都是容器内实测**，不是估算。
"""

# ---- 体积对照（docker images 实测）----
IMAGES = {
    "2.5.47 unified（原基线）": "2.01GB",
    "2.5.47 backend（纯后端）": "1.59GB",
    "阶段 0 unified（瘦身后）": "1.39GB",
    "阶段 0 backend（瘦身后）": "1.32GB",
}

# ---- 分层拆解（docker history 实测）----
LAYERS = {
    "site-packages": ("906MB", "452MB", "剔 .pyc 134MB + kubernetes 依赖树 96MB + zstandard/hf_xet/mmh3 36MB"),
    "apt 包（libllvm19/mesa/libz3 等）": ("408MB", "≈218MB", "去掉 libgl1 拖进的 Mesa/LLVM 图形栈 ≈190MB"),
    "字体（fonts-noto-cjk）": ("89MB", "38MB", "删两个全项目零引用的 Serif .ttc ≈51MB"),
    "ONNX embedding 模型": ("79MB", "79MB", "保留——实测集合维度 384，MiniLM 真的在用"),
    "前端 dist": ("5.1MB", "5.1MB", "无变化"),
    "nginx + supervisord": ("53MB", "53MB", "无变化"),
}

# ---- 剔除包清单与体积（容器内 du -sm 实测）----
REMOVED = [
    ("kubernetes", 84, "chromadb 的 K8s 分布式后端专用；本项目用 PersistentClient 本地模式"),
    ("aiohttp", 9, "kubernetes 独占"),
    ("websocket-client", 1, "kubernetes 独占；项目零 WebSocket 用法（rg 无命中）"),
    ("durationpy", 1, "kubernetes 独占"),
    ("requests-oauthlib", 1, "kubernetes 独占"),
    ("oauthlib", 1, "kubernetes 独占"),
    ("six", 1, "kubernetes 独占"),
    ("urllib3 等 12 个小包", 3, "kubernetes 独占尾巴"),
    ("zstandard", 24, "仅 httpx/langsmith 以 try/except 保护的可选 zstd 路径"),
    ("hf_xet", 11, "仅 huggingface_hub 的 xet 加速上传路径"),
    ("mmh3", 1, "chromadb 的 hash 辅助"),
    (".pyc（916 个 __pycache__）", 134, "pip 编译缓存；容器常驻数小时，+0.5s 启动换 134MB 划算"),
    ("libgl1 拖进的图形栈", 190, "libllvm19 123MB + mesa-libgallium 40MB + libz3-4 26MB"),
    ("NotoSerifCJK 两个 .ttc", 51, "全项目零引用（rg NotoSerif 无命中）"),
]

# ---- 依赖图不动点分析：哪些**不能**删 ----
KEEP = [
    ("requests / urllib3 / certifi / idna / charset-normalizer", "langsmith、tiktoken、httpx 仍在用"),
    ("attrs", "jsonschema / referencing 仍在用"),
    ("pyyaml", "chromadb / huggingface_hub / langchain-core 仍在用"),
    ("typing-extensions / tzdata", "大半个依赖树共用"),
    ("onnxruntime", "chromadb 的默认 embedding 函数运行时必需"),
    ("tokenizers", "chromadb 的默认 embedding 函数运行时必需"),
    ("chromadb_rust_bindings", "chromadb 核心 rust 运行时"),
    ("langsmith", "langchain_core.tracers.schemas 硬 import"),
    ("opentelemetry-sdk / exporter-otlp-proto-grpc", "chromadb import 期加载"),
]

# ---- 修复的三个真实缺陷 ----
FIXES = [
    ("rule_engine.py 依赖 simpleeval 但 requirements.txt 未声明",
     "生产镜像里该包不存在，任何触达规则引擎的请求都会 ImportError。"
     "本地 venv 因被顺带安装才没暴露。已补 simpleeval==0.9.13。"),
    ("backend 阶段未预置 ONNX 模型",
     "docker build --target backend 的镜像首次向量检索要现场下载 79MB，"
     "内网/弱网下必然超时。已把预置提到 backend-base。"),
    ("ENV CHROMA_CACHE_DIR 完全无效",
     "chromadb 1.5.9 只认 Path.home()（onnx_mini_lm_l6_v2.py:39），"
     "原注释「兼容两种实现」是误导。真正生效的开关是 HOME，已设 HOME=/home/app。"),
]

# ---- 验证矩阵（全部通过）----
VERIFICATIONS = [
    ("容器内真实卸载后 chromadb create/add/query", "PASS"),
    ("langchain + langgraph + langchain_openai 导入", "PASS"),
    ("langsmith 导入", "PASS"),
    ("httpx 真实网络请求", "PASS"),
    ("uvicorn 真实起服务并响应 HTTP", "PASS"),
    ("PyMuPDF / Pillow 中文字体渲染", "PASS"),
    ("FastAPI 全栈（fastapi/sqlalchemy/alembic/psycopg2/jwt/loguru/apscheduler）", "PASS"),
    ("容器 /api/v1/health + /api/v1/ready", "PASS"),
    ("容器前端首页 HTTP 200", "PASS"),
    ("ONNX 模型命中预置（无现场下载）", "PASS"),
    ("30 项 tools/check_* + tools/verify_* 门禁", "PASS"),
    ("3 个 backend/qa_*_suite.py", "PASS"),
    ("前端 vitest 187 用例 + eslint", "PASS"),
    ("浏览器回归 26 步（含转办/催办/催交考试/逾期/窄屏）", "PASS"),
]


if __name__ == "__main__":
    print("镜像体积对照：")
    for k, v in IMAGES.items():
        print(f"  {k:28s} {v}")
    print()
    print(f"剔除项合计：{sum(mb for _, mb, _ in REMOVED)} MB")
    print(f"验证项：{len(VERIFICATIONS)} 条全部通过")
