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

from app.core.config import settings

logger = logging.getLogger(__name__)

# (表名, 列名, 列类型 DDL)。新加模型字段若老库可能缺列，登记到这里。
MIGRATION_COLUMNS: List[Tuple[str, str, str]] = [
    # v1.0.19: Attachment 业务绑定（教案/作业等按 biz_type+biz_id 挂附件）
    ("sys_attachment", "biz_type", "VARCHAR(32)"),
    # v1.0.42: AI 教案 —— 教案主体补齐「教学准备 / 课堂练习」与生成溯源，
    # 教学过程补「师生活动」分列。AI 教案要求这些是独立章节，
    # 老库没有该列时 create_all 不会补，读写即 500。
    ("edu_lesson_plan", "teaching_preparation", "TEXT"),
    ("edu_lesson_plan", "class_exercise", "TEXT"),
    ("edu_lesson_plan", "ai_generated", "INTEGER DEFAULT 0"),
    ("edu_lesson_plan", "ai_job_id", "INTEGER"),
    ("edu_lesson_stage", "teacher_activity", "TEXT"),
    ("edu_lesson_stage", "student_activity", "TEXT"),
    # v1.0.42: AI 任务进度提示（前后端轮询要给出「正在做什么」）
    ("sys_agent_job", "progress", "INTEGER DEFAULT 0"),
    ("sys_agent_job", "stage", "VARCHAR(64)"),
]


def run_column_migrations(db: Session) -> List[str]:
    """幂等补列，返回本次实际新增的列（用于日志）。"""
    applied: List[str] = []
    # 本迁移基于 SQLite 的 PRAGMA table_info；切 PostgreSQL 时 PRAGMA 不存在，
    # 逐个失败并静默跳过会让「模型加列、老库缺列」问题在切库后重新出现。
    # 明确跳过并提示使用 Alembic，避免给出"已迁移"的假象。
    if not settings.DATABASE_URL.startswith("sqlite"):
        logger.warning(
            "当前数据库非 SQLite，已跳过轻量补列迁移；"
            "请使用 Alembic（requirements 已内置）管理结构变更"
        )
        return applied
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