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
        kwargs["connect_args"] = {"check_same_thread": settings.SQLITE_CHECK_SAME_THREAD}
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
    """SQLite 开启外键与 WAL 模式，保证数据完整性并提升并发。"""
    if settings.DATABASE_URL.startswith("sqlite"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()


def get_db() -> Generator[Session, None, None]:
    """FastAPI 依赖：提供请求级数据库会话。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
