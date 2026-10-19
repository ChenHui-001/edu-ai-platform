"""轻量 SQLite 结构迁移：启动时幂等补列。

背景：项目依赖 `Base.metadata.create_all` 建表，但它**只创建缺失的表，
不会给已存在的表添加新列**。模型加了字段、老库没有该列时，一切涉及
该列的读写都会 500（案例：v1.0.19 给 sys_attachment 加 biz_type，
老库长期未暴露，直到教案附件按 biz_type 查询才炸）。

在引入 Alembic 之前，用这张清单兜底：启动时逐项检查，缺列则
ALTER TABLE ADD COLUMN（SQLite 支持，且重复执行幂等——先 PRAGMA 探测）。
"""
import logging
from typing import List, Tuple

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# (表名, 列名, 列类型 DDL)。新加模型字段若老库可能缺列，登记到这里。
MIGRATION_COLUMNS: List[Tuple[str, str, str]] = [
    # v1.0.19: Attachment 业务绑定（教案/作业等按 biz_type+biz_id 挂附件）
    ("sys_attachment", "biz_type", "VARCHAR(32)"),
]


def run_column_migrations(db: Session) -> List[str]:
    """幂等补列，返回本次实际新增的列（用于日志）。"""
    applied: List[str] = []
    for table, column, ddl in MIGRATION_COLUMNS:
        try:
            rows = db.execute(
                text(f"PRAGMA table_info({table})")).fetchall()
            if not rows:
                continue  # 表尚不存在：create_all 会建出全列结构
            existing = {r[1] for r in rows}
            if column in existing:
                continue
            db.execute(text(
                f"ALTER TABLE {table} ADD COLUMN {column} {ddl}"))
            db.commit()
            applied.append(f"{table}.{column}")
            logger.warning("结构迁移：已为 %s 补充列 %s", table, column)
        except Exception as exc:  # noqa: BLE001
            db.rollback()
            logger.error("结构迁移失败 %s.%s: %s", table, column, exc)
    return applied