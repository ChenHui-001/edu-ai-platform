"""FastAPI 应用入口。"""
import os
from contextlib import asynccontextmanager

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
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Process-Time", "Content-Disposition"],
)
app.add_middleware(AuditMiddleware)

register_exception_handlers(app)
app.include_router(api_router, prefix=settings.API_PREFIX)


@app.get("/api/v1/health", tags=["系统"], summary="健康检查")
def health():
    return {
        "code": 200, "success": True,
        "data": {
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "status": "healthy",
            "database": settings.DATABASE_URL.split("://")[0],
            "llm_enabled": bool(settings.LLM_ENABLED and settings.LLM_API_KEY),
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
