"""数据库连接与会话管理。SQLite / PostgreSQL 双兼容。"""
import os
from typing import Any, Dict, Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings


class Base(DeclarativeBase):
    """所有 ORM 模型的基类。"""


def _ensure_sqlite_parent_dir(url: str) -> None:
    """确保 SQLite 数据库文件的父目录存在。

    ## 为什么必须在建引擎时做

    **SQLite 不会自动创建父目录**，只会在目录不存在时抛
    `sqlite3.OperationalError: unable to open database file`。而 `create_all`、
    任何一条查询、乃至一个 `SessionLocal()` 的第一次 flush 都可能触发建库 ——
    也就是说建库时机是分散的，靠某一处 `ensure_dirs()` 兜不住。

    这个缺陷曾经真实存在且**被一个无关的副作用掩盖了很久**：
    `core/logger.py` 原来默认启用 loguru FileSink，路径是
    `{LOG_DIR}/app_{time}.log` 即 `./data/logs/...`，loguru 会 `makedirs`
    整个路径 —— 于是 `./data/` 被顺手建出来了，`create_all` 跟着成功。
    把 FileSink 改成默认关闭（那次修复本身是对的）后，`./data` 没人建了，
    CI 的「应用导入与建表检查」立刻报 unable to open database file。
    换句话说：**依赖别人顺手建目录不是"能跑"，是"还没暴露"。**

    PostgreSQL 等非 SQLite URL 直接跳过（服务端已经存在，不是本地路径）。
    """
    if not url.startswith("sqlite"):
        return
    # 只处理文件库：`sqlite:///./data/x.db`、`sqlite:////abs/x.db`、
    # `sqlite:///C:/x.db`(Windows)。`:memory:` 与空路径没有父目录。
    path = url.replace("sqlite:///", "", 1)
    if not path or ":memory:" in path or path.startswith(":"):
        return
    parent = os.path.dirname(os.path.abspath(path))
    if not parent:
        return
    try:
        os.makedirs(parent, exist_ok=True)
    except OSError as exc:
        # 建不出来（只读挂载等）不要在这里炸：让后续真正连库时报出更
        # 具体的错误，而不是把一个 OSError 抛在建引擎这个"看起来无关"的位置。
        from app.core.logger import get_logger

        get_logger("database").warning(
            f"SQLite 数据目录 {parent} 创建失败（连库时可能报错）: {exc}"
        )


def _build_engine():
    """根据 DATABASE_URL 构建引擎，SQLite 走内存优化或文件模式。"""
    url = settings.DATABASE_URL
    _ensure_sqlite_parent_dir(url)
    kwargs: Dict[str, Any] = {"echo": settings.DB_ECHO, "future": True}

    if url.startswith("sqlite"):
        kwargs["connect_args"] = {
            "check_same_thread": settings.SQLITE_CHECK_SAME_THREAD,
            # 连接级兜底超时：PRAGMA busy_timeout 已在 connect 事件里设置，
            # 这里再给 sqlite3 驱动一个默认值，避免某些路径绕过 PRAGMA。
            "timeout": 10,
        }
        # :memory: 测试场景使用 StaticPool 保持单连接
        if ":memory:" in url:
            kwargs["poolclass"] = StaticPool
    else:
        kwargs["pool_pre_ping"] = True
        kwargs["pool_size"] = 10
        kwargs["max_overflow"] = 20

    return create_engine(url, **kwargs)


engine = _build_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    """SQLite 开启外键与 WAL 模式，保证数据完整性并提升并发。

    busy_timeout 必须显式设置：WAL 允许「多读一写」，但**写写仍互斥**。
    默认 busy_timeout=0 表示拿不到写锁立刻报 `database is locked` 而不等待，
    于是任何并发写（审计中间件 + AI 调用日志 + 业务事务）都会随机失败：
    审计日志丢条、AI 调用日志丢条，甚至业务写入直接 500。
    实测回归中 `sys_agent_call_log` 连续 6 次写入全部因锁失败。
    设为 5s 让写操作排队，而不是立即失败。
    """
    if settings.DATABASE_URL.startswith("sqlite"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.close()


def get_db() -> Generator[Session, None, None]:
    """FastAPI 依赖：提供请求级数据库会话。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
