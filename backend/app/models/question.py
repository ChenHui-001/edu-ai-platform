"""题库与试卷模型。"""
import enum
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.utils.common import now_local


class QuestionType(str, enum.Enum):
    SINGLE = "single"          # 单选题
    MULTIPLE = "multiple"      # 多选题
    JUDGE = "judge"            # 判断题
    BLANK = "blank"            # 填空题
    SHORT_ANSWER = "short"     # 简答题
    CALCULATION = "calc"       # 计算题
    MATERIAL = "material"      # 材料分析题
    COMPOSITION = "composition"  # 作文题


OBJECTIVE_TYPES = {
    QuestionType.SINGLE.value,
    QuestionType.MULTIPLE.value,
    QuestionType.JUDGE.value,
    QuestionType.BLANK.value,
}


class Difficulty(str, enum.Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class QuestionBankType(str, enum.Enum):
    PRIVATE = "private"  # 我的题库
    PUBLIC = "public"    # 公共题库


class QuestionStatus(str, enum.Enum):
    DRAFT = "draft"        # 待审核（AI 生成题目先入待审核库）
    PUBLISHED = "published"
    OFFLINE = "offline"


class Question(Base):
    __tablename__ = "edu_question"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # 题目属性
    type: Mapped[str] = mapped_column(String(16), default=QuestionType.SINGLE.value, index=True)
    stem: Mapped[str] = mapped_column(Text, comment="题干，支持富文本/图片/公式")
    options: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="选项 JSON：[{key,text}]")
    answer: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="标准答案 JSON")
    analysis: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="解析")
    score: Mapped[float] = mapped_column(Float, default=5.0)
    difficulty: Mapped[str] = mapped_column(String(16), default=Difficulty.MEDIUM.value, index=True)

    # 关联维度
    grade_id: Mapped[int] = mapped_column(ForeignKey("edu_grade.id", ondelete="CASCADE"), index=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey("edu_subject.id", ondelete="CASCADE"), index=True)
    knowledge_point_id: Mapped[Optional[int]] = mapped_column(ForeignKey("edu_knowledge_point.id", ondelete="SET NULL"), nullable=True, index=True)

    # 归属与状态
    bank_type: Mapped[str] = mapped_column(String(16), default=QuestionBankType.PRIVATE.value, index=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("sys_user.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String(16), default=QuestionStatus.PUBLISHED.value, index=True)
    fingerprint: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True, comment="题干哈希，用于查重")
    source: Mapped[str] = mapped_column(String(32), default="manual", comment="manual/ai_import")
    usage_count: Mapped[int] = mapped_column(Integer, default=0, comment="被使用次数")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_local, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now_local, onupdate=now_local)


class QuestionKnowledge(Base):
    """题目与知识点多对多（支持一题多知识点）。"""

    __tablename__ = "edu_question_knowledge"
    __table_args__ = (UniqueConstraint("question_id", "knowledge_point_id", name="uq_q_kp"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("edu_question.id", ondelete="CASCADE"), index=True)
    knowledge_point_id: Mapped[int] = mapped_column(ForeignKey("edu_knowledge_point.id", ondelete="CASCADE"), index=True)


class Paper(Base):
    """试卷。"""

    __tablename__ = "edu_paper"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), index=True)
    grade_id: Mapped[int] = mapped_column(ForeignKey("edu_grade.id", ondelete="CASCADE"), index=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey("edu_subject.id", ondelete="CASCADE"), index=True)
    total_score: Mapped[float] = mapped_column(Float, default=100.0)
    duration: Mapped[int] = mapped_column(Integer, default=60, comment="建议时长（分钟）")
    difficulty_ratio: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, comment="难度分布")
    knowledge_coverage: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="知识点覆盖报告 JSON")
    difficulty_report: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="难度分析 JSON")

    creator_id: Mapped[int] = mapped_column(ForeignKey("sys_user.id", ondelete="CASCADE"), index=True)
    source: Mapped[str] = mapped_column(String(16), default="manual", comment="manual/ai")
    is_shared: Mapped[bool] = mapped_column(Boolean, default=False, comment="共享给同科教师")
    use_count: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_local, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now_local, onupdate=now_local)

    items: Mapped[List["PaperItem"]] = relationship(
        back_populates="paper", cascade="all, delete-orphan", order_by="PaperItem.sort_order", lazy="selectin"
    )


class PaperItem(Base):
    """试卷题目项。"""

    __tablename__ = "edu_paper_item"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    paper_id: Mapped[int] = mapped_column(ForeignKey("edu_paper.id", ondelete="CASCADE"), index=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("edu_question.id", ondelete="CASCADE"), index=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    score: Mapped[float] = mapped_column(Float, default=5.0)
    section_name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, comment="大题标题，如 一、选择题")

    paper: Mapped[Paper] = relationship(back_populates="items")
    question: Mapped[Question] = relationship(lazy="selectin")


class PaperShare(Base):
    """试卷分享记录。"""

    __tablename__ = "edu_paper_share"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    paper_id: Mapped[int] = mapped_column(ForeignKey("edu_paper.id", ondelete="CASCADE"), index=True)
    from_user_id: Mapped[int] = mapped_column(ForeignKey("sys_user.id", ondelete="CASCADE"))
    to_user_id: Mapped[int] = mapped_column(ForeignKey("sys_user.id", ondelete="CASCADE"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_local)
