"""教案管理（Lesson Plan）。

教师把一节课的教学设计沉淀为教案：学科/年级/教材版本/课题/课时数/
教学目标/重难点/教学过程（多阶段）/板书设计/作业布置/教学反思。

可复制、可共享给同科教师、统计使用次数。
"""
from datetime import datetime
from typing import List, Optional

from sqlalchemy import ForeignKey, Index, Integer, String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.edu import KnowledgePoint, Subject, Grade
from app.utils.common import now_local


class LessonPlan(Base):
    """教案主表。"""

    __tablename__ = "edu_lesson_plan"
    __table_args__ = (
        Index("ix_lesson_plan_subject_grade", "subject_id", "grade_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(128), index=True,
                                       comment="教案标题（如：解一元一次方程——移项）")
    topic: Mapped[str] = mapped_column(String(128), comment="课题")
    # 学科是按年级配置的（unique (grade_id, name)），所以这里存精确的 subject_id
    subject_id: Mapped[int] = mapped_column(ForeignKey("edu_subject.id", ondelete="CASCADE"), index=True)
    grade_id: Mapped[int] = mapped_column(ForeignKey("edu_grade.id", ondelete="CASCADE"), index=True)
    textbook_version: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    knowledge_point_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("edu_knowledge_point.id", ondelete="SET NULL"),
        nullable=True, index=True)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=45, comment="课时长度（分钟）")
    period: Mapped[Optional[str]] = mapped_column(String(32), nullable=True,
                                                 comment="第几课时，如「第 1 课时」")

    # 教学设计主体（Markdown 风格，前端用 textarea 显示）
    objectives: Mapped[str] = mapped_column(Text, default="", comment="教学目标（三维目标）")
    key_points: Mapped[str] = mapped_column(Text, default="", comment="教学重点")
    difficulties: Mapped[str] = mapped_column(Text, default="", comment="教学难点")
    # AI 教案要求「教学准备 / 课堂练习」为独立章节，原模型只能用教学过程
    # 或作业字段勉强承载，导致生成结果无处落库。
    teaching_preparation: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="教学准备（教具/课件/学具/课前任务）")
    class_exercise: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="课堂练习（随堂检测题，含答案）")
    board_design: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="板书设计")
    homework: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="作业布置")
    reflection: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="教学反思")

    # 元信息
    creator_id: Mapped[int] = mapped_column(ForeignKey("sys_user.id", ondelete="CASCADE"), index=True)
    use_count: Mapped[int] = mapped_column(Integer, default=0, comment="被引用次数")
    is_shared: Mapped[bool] = mapped_column(Integer, default=0,
                                            comment="是否共享给同科教师（0/1 兼容 SQLite）")
    # AI 生成溯源：便于在教案库里区分「人工撰写」与「AI 生成后人工修订」
    ai_generated: Mapped[bool] = mapped_column(Integer, default=0,
                                               comment="是否由 AI 生成（0/1 兼容 SQLite）")
    ai_job_id: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="来源生成任务 sys_agent_job.id")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_local, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now_local, onupdate=now_local)

    # 关系
    subject: Mapped["Subject"] = relationship()
    grade: Mapped["Grade"] = relationship()
    knowledge_point: Mapped[Optional["KnowledgePoint"]] = relationship()
    stages: Mapped[List["LessonStage"]] = relationship(
        back_populates="lesson", cascade="all, delete-orphan",
        order_by="LessonStage.sort_order", lazy="selectin")


class LessonStage(Base):
    """教学过程阶段（导入/新授/练习/小结/作业等）。"""

    __tablename__ = "edu_lesson_stage"
    __table_args__ = (
        Index("ix_lesson_stage_lesson", "lesson_id", "sort_order"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lesson_id: Mapped[int] = mapped_column(ForeignKey("edu_lesson_plan.id", ondelete="CASCADE"),
                                            index=True)
    name: Mapped[str] = mapped_column(String(32), comment="阶段名（如：导入 / 新课讲授）")
    duration_minutes: Mapped[int] = mapped_column(Integer, default=5, comment="该阶段时长")
    content: Mapped[str] = mapped_column(Text, default="", comment="阶段概述 / 设计意图")
    # AI 教案要求「师生活动」分列展示；原来只有一段 content，无法体现
    # 「教师说什么、学生做什么」。保留 content 作整体说明，两个新列放明细。
    teacher_activity: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="教师活动")
    student_activity: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="学生活动")
    sort_order: Mapped[int] = mapped_column(Integer, default=0, comment="排序")

    lesson: Mapped["LessonPlan"] = relationship(back_populates="stages")