"""FastAPI 应用入口。"""
import os
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.core.database import Base, SessionLocal, engine
from app.core.exception import register_exception_handlers
from app.core.logger import get_logger
from app.middleware.audit import AuditMiddleware

logger = get_logger("main")


def ensure_dirs() -> None:
    """确保运行所需目录存在。"""
    for d in (settings.UPLOAD_DIR, settings.EXPORT_DIR, settings.LOG_DIR,
              settings.CHROMA_PERSIST_DIR, os.path.dirname(settings.DATABASE_URL.replace("sqlite:///", "")) or "."):
        os.makedirs(d, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：初始化数据库、种子数据、调度器。"""
    ensure_dirs()

    # 建表（轻量化场景用 create_all，生产可切换 Alembic）
    Base.metadata.create_all(bind=engine)

    # 老库补列（create_all 不会给已存在的表加新列，模型加字段后必须跑这步）
    from app.core.db_migrations import (
        run_column_migrations, run_knowledge_v2_migration, run_question_v2_migration,
    )

    _mig_db = SessionLocal()
    try:
        applied = run_column_migrations(_mig_db)
        if applied:
            logger.warning(f"已执行结构补列迁移: {applied}")
        run_knowledge_v2_migration(_mig_db)
        # 题库 V2：首次启动清空历史题库（用户已确认可删；放在知识库迁移之后）
        run_question_v2_migration(_mig_db)
    finally:
        _mig_db.close()
    logger.info("数据库表结构已就绪")

    # 种子数据
    try:
        db = SessionLocal()
        try:
            from app.services.init_db import init_all

            init_all(db)
        finally:
            db.close()
    except Exception as exc:
        logger.opt(exception=True).error(f"种子数据初始化失败: {exc}")

    # 预热 AI Agent
    try:
        from app.agents.base import get_orchestrator

        orch = get_orchestrator()
        logger.info(f"Agent 编排引擎就绪（模式：{orch.mode}）")
    except Exception as exc:
        logger.warning(f"Agent 引擎初始化异常: {exc}")

    # 后台预热 Chroma embedding 模型：避免首次 AI 请求触发 79MB 下载而卡住
    try:
        from app.agents.rag import start_chroma_warmup

        start_chroma_warmup()
    except Exception as exc:
        logger.warning(f"Chroma 预热启动失败: {exc}")

    # 定时任务
    if settings.SCHEDULER_ENABLED:
        try:
            from app.services.scheduler import sync_all_jobs

            n = sync_all_jobs()
            logger.info(f"定时任务同步完成：{n} 个")
        except Exception as exc:
            logger.warning(f"定时任务启动失败: {exc}")

    logger.info(f"{settings.APP_NAME} v{settings.APP_VERSION} 启动完成")
    yield

    from app.services.scheduler import get_scheduler

    if get_scheduler().running:
        get_scheduler().shutdown(wait=False)
    logger.info("应用已关闭")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="九年义务教育学习管理系统（AI Agent 版）后端 API",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# 中间件
# CORS：allow_credentials=True 与 allow_origins=["*"] 组合会被浏览器拒绝生效，
# 本项目鉴权走 Authorization 头（无 Cookie），故通配来源时关闭 credentials。
_allow_cors_credentials = "*" not in settings.CORS_ORIGINS
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=_allow_cors_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Process-Time", "Content-Disposition"],
)
app.add_middleware(AuditMiddleware)

register_exception_handlers(app)
app.include_router(api_router, prefix=settings.API_PREFIX)


@app.get("/api/v1/health", tags=["系统"], summary="健康检查")
def health():
    # llm_enabled 必须走 is_available()（sys_config 优先于 .env）。
    # 原来只看 settings.LLM_ENABLED/LLM_API_KEY，管理员在「AI 配置」页填好密钥后，
    # 健康检查与系统配置页仍显示 llm_enabled=false，看起来像配置没生效。
    try:
        from app.agents.llm import is_available as _llm_available
        llm_on = _llm_available()
    except Exception:  # noqa: BLE001  健康检查不能被 AI 模块拖垮
        llm_on = bool(settings.LLM_ENABLED and settings.LLM_API_KEY)
    return {
        "code": 200, "success": True,
        "data": {
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "status": "healthy",
            "database": settings.DATABASE_URL.split("://")[0],
            "llm_enabled": llm_on,
            # 服务端当前时间（服务端本地时区，naive）。供 e2e 构造时间窗参数用：
            # CI runner 是 UTC、容器是 Asia/Shanghai，测试进程用 datetime.now()
            # 拼 publish_at/deadline 会差 8 小时，导致「定时发布」被立即执行、
            # 「未开考」被当成已开始。取服务端时间可彻底消除该时区耦合。
            "server_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        },
    }


@app.get("/", include_in_schema=False)
def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/api/v1/health",
    }
