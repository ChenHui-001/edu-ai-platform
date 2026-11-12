"""Alembic 运行环境（Q-06）。

三条不可省的约定：

1. **URL 只有一个真源**：默认取 `settings.DATABASE_URL`，与业务代码连同一个库。
   `ALEMBIC_DB_URL` 仅用于校验脚本指向临时库 —— 这条口子让"在临时库上演练
   迁移"成为可能，而不必改 `.env`。
2. **必须 import app.models**：`Base.metadata` 是空的壳，模型没被导入时
   autogenerate 会愉快地生成一个"删掉所有表"的迁移。这是最经典的事故。
3. **batch 模式**：SQLite 不支持 `ALTER COLUMN`，改列/删列必须走
   `render_as_batch=True` —— 否则生成的迁移在 SQLite 上直接报错，
   而 CI 与生产都是 SQLite。
"""
import os
import sys

from alembic import context
from sqlalchemy import create_engine, pool

# 让 alembic 在任意工作目录下都能 import 到 app 包
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings  # noqa: E402
from app.core.database import Base  # noqa: E402
import app.models  # noqa: E402,F401  —— 注册全部 ORM 模型，别删

config = context.config
target_metadata = Base.metadata


def _database_url() -> str:
    return os.environ.get("ALEMBIC_DB_URL") or settings.DATABASE_URL


def run_migrations_offline() -> None:
    """离线模式：只把 SQL 打到 stdout，不连库（`alembic upgrade head --sql`）。"""
    context.configure(
        url=_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """在线模式：连库执行。用 NullPool —— 迁移是一次性短连接，
    连接池只会在进程退出时留下未关闭的句柄（Windows 上表现为文件占用）。"""
    connectable = create_engine(_database_url(), poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()
    connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
