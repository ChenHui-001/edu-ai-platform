"""数据库连接与会话管理。SQLite / PostgreSQL 双兼容。"""
from typing import Any, Dict, Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings


class Base(DeclarativeBase):
    """所有 ORM 模型的基类。"""


def _build_engine():
    """根据 DATABASE_URL 构建引擎，SQLite 走内存优化或文件模式。"""
    url = settings.DATABASE_URL
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
