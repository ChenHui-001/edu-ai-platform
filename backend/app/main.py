"""FastAPI 应用入口。"""
import os
import time
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


# ---------------------------------------------------------------- 启动互斥
# 启动期前 5 步（建表 / 补列迁移 / 两个 V2 数据迁移 / 种子）**必须单点执行**。
#
# 为什么不能靠"反正幂等"糊过去：
# - `run_knowledge_v2_migration`（db_migrations.py:145）与
#   `run_question_v2_migration`（:105-107）里是**破坏性 DELETE**，守卫只是
#   `sys_config` 里的一个标记位。两个 worker 同时读到"未执行"就会**都执行删除**。
#   全新库上无害（表本就空），但「从 <V2 升级到 V2」的那一次重启恰好是部署时
#   起多个 worker 的同一时刻 —— 知识树被清空且无法从日志里看出原因。
# - `init_all` 的「空表才播」守卫同理：`edu_class.name` 无唯一约束，
#   两个进程会各插一份（实测 4 条变 8 条）；随后 `User.username` 的唯一约束
#   触发 IntegrityError，`init_all` 中途抛异常 → 后续 `init_exam_standards` /
#   `init_demo_data` / `enforce_default_admin_password` **全部跳过**。
#   最后一项就是 S5，于是"强制改密"在多 worker 下变成概率行为。
#
# 方案：文件锁（`fcntl.flock`）包住这 5 步。
# - 为什么不用 supervisord 前置 bootstrap 进程：那要新增 `bootstrap.py` +
#   `RUN_STARTUP_HOOKS` 开关 + 改部署拓扑；flock 约 20 行、
#   不动部署拓扑，且 worker 数无关。
# - 为什么不用 DB 锁表：建表之前还没有表可锁 —— 锁必须比被保护的操作更早存在。
# - Windows 无 `fcntl`：本地直连 uvicorn 跑单进程 + 临时库时不存在并发，
#   降级为不加锁直接执行（ImportError 分支）。
# - 锁文件放在 DB 同目录：同一个 DB 天然对应同一把锁；换库（测试用临时库）
#   自动换锁，不会跨库互斥。
def _startup_lock_path() -> str:
    db_path = settings.DATABASE_URL.replace("sqlite:///", "")
    db_dir = os.path.dirname(os.path.abspath(db_path)) or "."
    return os.path.join(db_dir, ".startup.lock")


@asynccontextmanager
async def _startup_lock():
    """启动钩子互斥锁。拿不到锁就等待（而非跳过）。

    为什么是"等待"不是"跳过"：跳过会让后到的 worker 在种子/迁移**未完成**时
    就开始服务请求，学生可能查到半套数据。等待的代价只是第二个 worker 晚
    几秒就绪（`HEALTHCHECK --start-period` 已为此留出余量）。
    """
    try:
        import fcntl
    except ImportError:
        # Windows / 非 POSIX：e2e 单进程场景，无并发，直接放行。
        logger.debug("当前平台无 fcntl，跳过启动互斥（仅限单进程场景）")
        yield 0.0
        return

    path = _startup_lock_path()
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    started = time.monotonic()
    fh = open(path, "a+")  # noqa: SIM115 需要跨 yield 持有句柄
    try:
        try:
            fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            logger.info("另一个进程正在执行启动钩子，本进程等待其完成…")
            fcntl.flock(fh.fileno(), fcntl.LOCK_EX)  # 阻塞等待
        waited = time.monotonic() - started
        if waited > 1:
            logger.info(f"启动钩子等待 {waited:.1f}s 后获得锁")
        yield waited
    finally:
        try:
            fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
        finally:
            fh.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：初始化数据库、种子数据、调度器。"""
    ensure_dirs()

    # 这 5 步必须单点执行，理由见文件头「启动互斥」注释。
    # create_all 也放进锁内：它是 `IF NOT EXISTS` 语义、并发安全，但放在锁内
    # 可以让「后到的进程」在建表完成后再开始迁移，语义更线性（无额外代价）。
    async with _startup_lock() as waited:
        if waited > 0.5:
            logger.info(f"启动钩子已等待 {waited:.1f}s，继续执行")

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

    # 启动收割僵尸任务（B2）。**必须在启动锁之外**：它与另外 5 步无关，
    # 只是修正上一进程留下的状态；占着锁会让另一个 worker 白白多等。
    #
    # 为什么需要它：AgentJob/JobExecutionLog 都是「写 status=running 后跑
    # daemon 线程」，进程退出时线程无线程收尾 → 状态永久停在 running，
    # 前端按 status 轮询就无限转圈（出题/组卷页实测如此）。
    # 读时判定（services/agent_job_state.apply_timeout）负责让前端**立刻**
    # 看到超时，这里负责把库里的脏状态落定。两者都要，缺一个就有漏洞：
    # 只有读时判定 → 脏数据永远留在库里，列表筛选/统计无从判断；
    # 只有启动收割 → 上一次重启之后、下一次重启之前创建的任务无人处理。
    try:
        _reap_db = SessionLocal()
        try:
            from app.services.agent_job_state import reap_orphan_jobs

            n_reaped = reap_orphan_jobs(_reap_db)
            if n_reaped:
                logger.warning(f"启动收割：共清理 {n_reaped} 条遗留的僵尸任务记录")
        finally:
            _reap_db.close()
    except Exception as exc:  # noqa: BLE001 收割失败绝不能阻断启动
        logger.warning(f"僵尸任务收割未执行: {exc}")

    # 启动后置校验：只喊话，不修复、不阻断（见 services/startup_checks.py 文件头）。
    # **必须在 A1 启动锁之外**：它不写任何业务数据（只可能写一条幂等 ErrorLog），
    # 没必要占着锁；而占着锁会让另一个 worker 在本进程做日志落库时多等一次。
    # 这里重新开一个 SessionLocal —— 上面 init_all 用的那个 db 已在 finally 里
    # close 了，不要复用那个变量。
    try:
        _chk_db = SessionLocal()
        try:
            from app.services.startup_checks import run_startup_checks

            run_startup_checks(_chk_db)
        finally:
            _chk_db.close()
    except Exception as exc:  # noqa: BLE001 校验失败绝不能阻断启动
        logger.warning(f"启动校验未执行: {exc}")

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
    description="新芽学堂 · 九年义务教育 AI 学习平台（AI Agent 版）后端 API",
    # 生产（DEBUG=false）关闭交互式文档：/docs、/redoc、/openapi.json 会把
    # 全部端点连同参数结构完整暴露给**匿名**访问者，攻击者可直接拿到
    # 「198 个接口的全图」再逐个试探归属校验缺失的接口（本系统历史漏洞
    # 多为此类）。本地开发保留，便于联调与按需导出 openapi.json。
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
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
