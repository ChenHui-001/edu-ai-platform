"""知识图谱先修关系与诊断会话模型。"""
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    CheckConstraint, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.utils.common import now_local


class KnowledgePrerequisite(Base):
    """知识点先修边：学习 topic 之前需要掌握 prerequisite。

    这与 `KnowledgePoint.parent_id` 的教材包含树是两套语义：
    - parent_id：单元 → 章节 → 知识点（展示层级）；
    - 本表：知识点 A → 先修知识点 B（诊断与学习路径）。

    外部项目的 `parent_id` 不能被当作先修关系使用。
    """

    __tablename__ = "edu_knowledge_prerequisite"
    __table_args__ = (
        UniqueConstraint(
            "topic_kp_id", "prerequisite_kp_id", name="uq_kp_prerequisite"),
        CheckConstraint(
            "topic_kp_id <> prerequisite_kp_id", name="ck_kp_prerequisite_not_self"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    topic_kp_id: Mapped[int] = mapped_column(
        ForeignKey("edu_knowledge_point.id", ondelete="CASCADE"),
        index=True, comment="后继知识点（要学的点）")
    prerequisite_kp_id: Mapped[int] = mapped_column(
        ForeignKey("edu_knowledge_point.id", ondelete="CASCADE"),
        index=True, comment="先修知识点（应先掌握的点）")
    strength: Mapped[str] = mapped_column(
        String(8), default="hard", comment="hard 强先修 / soft 弱先修")
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(
        String(32), default="manual", comment="manual/import/cn-math-taxonomy")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_local)


class TaxonomyDiagnosisSession(Base):
    """知识诊断会话。

    `answers_json` 是唯一事实来源；`status_json` 只是最近一次快照，读取时
    会按目标、选项和作答记录重放，避免刷新后状态与作答历史不一致。
    诊断结果不写 `KnowledgeMastery`，正式掌握度仍由作业/练习累计。
    """

    __tablename__ = "edu_taxonomy_diagnosis_session"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("sys_user.id", ondelete="CASCADE"), index=True,
        comment="被诊断学生")
    subject_id: Mapped[int] = mapped_column(
        ForeignKey("edu_subject.id", ondelete="CASCADE"), index=True)
    grade_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("edu_grade.id", ondelete="SET NULL"), nullable=True, index=True)
    targets_json: Mapped[str] = mapped_column(Text, comment="目标知识点 ID JSON")
    mode: Mapped[str] = mapped_column(
        String(16), default="target", comment="target 诊断 / screen 筛查")
    question_limit: Mapped[int] = mapped_column(Integer, default=16)
    confirm_count: Mapped[int] = mapped_column(Integer, default=3)
    answers_json: Mapped[str] = mapped_column(Text, default="[]")
    status_json: Mapped[str] = mapped_column(Text, default="{}")
    seed: Mapped[str] = mapped_column(String(64), default="default")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_local, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=now_local, onupdate=now_local)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
