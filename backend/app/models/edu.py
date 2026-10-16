"""教学基础档案模型：年级 / 学科 / 教材 / 知识点 / 班级。"""
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.utils.common import utcnow


class Grade(Base):
    """年级：小学 1-6 年级，初中 7-9 年级。"""

    __tablename__ = "edu_grade"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(32), unique=True, index=True, comment="如 一年级 / 七年级")
    stage: Mapped[str] = mapped_column(String(16), default="primary", comment="primary小学 / junior初中")
    grade_num: Mapped[int] = mapped_column(Integer, default=1, comment="年级序号 1-9")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort: Mapped[int] = mapped_column(Integer, default=0)

    subjects: Mapped[List["Subject"]] = relationship(back_populates="grade", lazy="selectin")
    classes: Mapped[List["Class"]] = relationship(back_populates="grade", lazy="selectin")


class Subject(Base):
    """学科：按年级配置，关联教材版本。"""

    __tablename__ = "edu_subject"
    __table_args__ = (UniqueConstraint("grade_id", "name", name="uq_grade_subject"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(32), index=True, comment="语文/数学/英语等")
    code: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    textbook_version: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, comment="教材版本：人教版/苏教版")
    grade_id: Mapped[int] = mapped_column(ForeignKey("edu_grade.id", ondelete="CASCADE"), index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort: Mapped[int] = mapped_column(Integer, default=0)

    grade: Mapped[Grade] = relationship(back_populates="subjects")


class Class(Base):
    """班级。"""

    __tablename__ = "edu_class"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), index=True)
    grade_id: Mapped[int] = mapped_column(ForeignKey("edu_grade.id", ondelete="CASCADE"), index=True)
    head_teacher_id: Mapped[Optional[int]] = mapped_column(ForeignKey("sys_user.id", ondelete="SET NULL"), nullable=True, comment="班主任")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    remark: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    grade: Mapped[Grade] = relationship(back_populates="classes")


class KnowledgePoint(Base):
    """多级知识点树：年级 - 学期 - 单元 - 章节 - 知识点。"""

    __tablename__ = "edu_knowledge_point"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), index=True)
    level: Mapped[int] = mapped_column(Integer, default=4, comment="层级 1单元 2章节 3知识点")
    parent_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True, comment="树形父级")
    path: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment="物化路径 如 1-3-12")
    grade_id: Mapped[int] = mapped_column(ForeignKey("edu_grade.id", ondelete="CASCADE"), index=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey("edu_subject.id", ondelete="CASCADE"), index=True)
    term: Mapped[int] = mapped_column(Integer, default=1, comment="学期 1上 2下")
    code: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    difficulty: Mapped[str] = mapped_column(String(16), default="medium", comment="简单/中等/困难")
    keywords: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment="检索关键词，逗号分隔")
    sort: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class TeachingAssignment(Base):
    """教师授课关系：教师 - 班级 - 学科（用于数据权限）。"""

    __tablename__ = "edu_teaching_assignment"
    __table_args__ = (UniqueConstraint("teacher_id", "class_id", "subject_id", name="uq_teach"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("sys_user.id", ondelete="CASCADE"), index=True)
    class_id: Mapped[int] = mapped_column(ForeignKey("edu_class.id", ondelete="CASCADE"), index=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey("edu_subject.id", ondelete="CASCADE"), index=True)
    grade_id: Mapped[int] = mapped_column(ForeignKey("edu_grade.id", ondelete="CASCADE"), index=True)
    school_year: Mapped[str] = mapped_column(String(16), default="2026-2027")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class ClassRequest(Base):
    """教师自建班级申请（管理员审核制）。

    流程：教师提交（pending）→ 管理员 approve（真实建班并回填 class_id、
    申请教师自动设为班主任）/ reject（附理由）→ 结果站内通知教师。
    (teacher_id, name, status) 唯一：同教师同名 pending 不可重复提交。
    """
    __tablename__ = "edu_class_request"
    __table_args__ = (
        UniqueConstraint("teacher_id", "name", "status", name="uq_class_req_tns"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("sys_user.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(64))
    grade_id: Mapped[int] = mapped_column(ForeignKey("edu_grade.id", ondelete="CASCADE"), index=True)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="pending", index=True,
                                        comment="pending/approved/rejected")
    review_by: Mapped[Optional[int]] = mapped_column(ForeignKey("sys_user.id", ondelete="SET NULL"), nullable=True)
    review_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    review_note: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    class_id: Mapped[Optional[int]] = mapped_column(ForeignKey("edu_class.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
