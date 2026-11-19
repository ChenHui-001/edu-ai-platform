"""Persistent remediation, tutor feedback and upstream synchronization records."""
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.utils.common import now_local


class RemediationPlan(Base):
    __tablename__ = "edu_remediation_plan"
    __table_args__ = (UniqueConstraint("student_id", "diagnosis_id", name="uq_remediation_diagnosis"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("sys_user.id"), index=True)
    diagnosis_id: Mapped[int] = mapped_column(ForeignKey("edu_taxonomy_diagnosis_session.id"))
    title: Mapped[str] = mapped_column(String(128))
    payload: Mapped[str] = mapped_column(Text)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_local)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now_local, onupdate=now_local)


class TutorFeedback(Base):
    __tablename__ = "edu_tutor_feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("sys_user.id"), index=True)
    class_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("edu_class.id", ondelete="SET NULL"), nullable=True, index=True,
        comment="核对结果适用的班级；教师纠错必须有班级范围")
    question_id: Mapped[int] = mapped_column(ForeignKey("edu_question.id"))
    stage: Mapped[str] = mapped_column(String(16))
    content: Mapped[str] = mapped_column(Text)
    correction: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reviewer_id: Mapped[Optional[int]] = mapped_column(ForeignKey("sys_user.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_local)


class TaxonomySyncRun(Base):
    __tablename__ = "edu_taxonomy_sync_run"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("sys_user.id"), index=True)
    action: Mapped[str] = mapped_column(String(16))
    source_commit: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(16), default="preview")
    report: Mapped[str] = mapped_column(Text)
    bundle_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    backup_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_local)
