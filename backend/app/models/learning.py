"""学习中心模型：笔记、知识点掌握度、复习计划。"""
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.utils.common import utcnow


class Note(Base):
    """学习笔记：富文本 + Markdown + 标签。"""

    __tablename__ = "edu_note"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(128), index=True)
    content: Mapped[str] = mapped_column(Text, comment="笔记正文（Markdown / 富文本 HTML）")
    format: Mapped[str] = mapped_column(String(16), default="markdown", comment="markdown/richtext")
    student_id: Mapped[int] = mapped_column(ForeignKey("sys_user.id", ondelete="CASCADE"), index=True)

    subject_id: Mapped[Optional[int]] = mapped_column(ForeignKey("edu_subject.id", ondelete="SET NULL"), nullable=True, index=True)
    knowledge_point_id: Mapped[Optional[int]] = mapped_column(ForeignKey("edu_knowledge_point.id", ondelete="SET NULL"), nullable=True, index=True)
    tags: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment="自定义标签，逗号分隔")

    # AI 增强
    ai_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="AI 提炼核心知识点")
    ai_outline: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="AI 生成大纲 JSON")
    ai_mindmap: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="AI 思维导图 JSON")

    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    is_shared: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class KnowledgeMastery(Base):
    """知识点掌握度：学生 x 知识点（掌握地图数据源）。"""

    __tablename__ = "edu_knowledge_mastery"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("sys_user.id", ondelete="CASCADE"), index=True)
    knowledge_point_id: Mapped[int] = mapped_column(ForeignKey("edu_knowledge_point.id", ondelete="CASCADE"), index=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey("edu_subject.id", ondelete="CASCADE"), index=True)

    total_count: Mapped[int] = mapped_column(Integer, default=0, comment="累计做题数")
    correct_count: Mapped[int] = mapped_column(Integer, default=0, comment="累计正确数")
    mastery: Mapped[float] = mapped_column(Float, default=0.0, comment="掌握度 0-100")
    wrong_count: Mapped[int] = mapped_column(Integer, default=0)
    study_seconds: Mapped[int] = mapped_column(Integer, default=0)
    last_practice_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    @property
    def accuracy(self) -> float:
        return round(self.correct_count / self.total_count * 100, 2) if self.total_count else 0.0


class ReviewPlan(Base):
    """艾宾浩斯复习计划。"""

    __tablename__ = "edu_review_plan"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("sys_user.id", ondelete="CASCADE"), index=True)
    wrong_question_id: Mapped[Optional[int]] = mapped_column(ForeignKey("edu_wrong_question.id", ondelete="CASCADE"), nullable=True, index=True)
    knowledge_point_id: Mapped[int] = mapped_column(ForeignKey("edu_knowledge_point.id", ondelete="CASCADE"), index=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey("edu_subject.id", ondelete="CASCADE"), index=True)

    stage: Mapped[int] = mapped_column(Integer, default=1, comment="第几轮复习")
    scheduled_date: Mapped[str] = mapped_column(String(10), index=True, comment="计划复习日期 YYYY-MM-DD")
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    correct_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class StudyRecord(Base):
    """学习行为记录：时长、做题量（用于报表）。"""

    __tablename__ = "edu_study_record"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("sys_user.id", ondelete="CASCADE"), index=True)
    subject_id: Mapped[Optional[int]] = mapped_column(ForeignKey("edu_subject.id", ondelete="SET NULL"), nullable=True, index=True)

    study_date: Mapped[str] = mapped_column(String(10), index=True, comment="统计日期")
    study_seconds: Mapped[int] = mapped_column(Integer, default=0)
    question_count: Mapped[int] = mapped_column(Integer, default=0)
    correct_count: Mapped[int] = mapped_column(Integer, default=0)
    note_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class QuestionFavorite(Base):
    """题目收藏：学生收藏的题目，可自定义标签和备注，用于考前速刷。"""

    __tablename__ = "edu_question_favorite"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("sys_user.id", ondelete="CASCADE"), index=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("edu_question.id", ondelete="CASCADE"), index=True)
    tag: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, index=True, comment="自定义标签：考前必看/易错/经典")
    note: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment="收藏备注")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
