"""作业 / 考试 / 答题 / 批改模型。"""
import enum
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.utils.common import now_local

if TYPE_CHECKING:
    # `Mapped["Paper"]` 是 SQLAlchemy 的字符串前向引用，运行时由 registry
    # 解析，不需要真实导入；但静态检查（ruff F821）无法识别这一点。
    # 放在 TYPE_CHECKING 下既满足静态检查，又不引入运行时循环导入
    # （question.py 反向引用 task 模型时会成环）。
    from app.models.question import Paper


class TaskType(str, enum.Enum):
    HOMEWORK = "homework"   # 作业
    EXAM = "exam"           # 考试
    PRACTICE = "practice"   # 随机练习


class TaskStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ONGOING = "ongoing"
    FINISHED = "finished"
    ARCHIVED = "archived"


class GradeStatus(str, enum.Enum):
    NOT_GRADED = "not_graded"
    AUTO_GRADED = "auto_graded"      # 客观题自动判分完成
    FULLY_GRADED = "fully_graded"    # 含主观题，已全部批改
    PUBLISHED = "published"          # 成绩已发布


class Task(Base):
    """作业 / 考试统一定义。"""

    __tablename__ = "edu_task"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(128), index=True)
    type: Mapped[str] = mapped_column(String(16), default=TaskType.HOMEWORK.value, index=True)
    paper_id: Mapped[int] = mapped_column(ForeignKey("edu_paper.id", ondelete="CASCADE"), index=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey("edu_subject.id", ondelete="CASCADE"), index=True)
    grade_id: Mapped[int] = mapped_column(ForeignKey("edu_grade.id", ondelete="CASCADE"), index=True)
    creator_id: Mapped[int] = mapped_column(ForeignKey("sys_user.id", ondelete="CASCADE"), index=True)

    status: Mapped[str] = mapped_column(String(16), default=TaskStatus.DRAFT.value, index=True)
    start_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    end_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)
    duration: Mapped[int] = mapped_column(Integer, default=60, comment="答题时长（分钟）")
    publish_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, comment="定时发布时间")

    # 规则配置
    allow_retake: Mapped[int] = mapped_column(Integer, default=1, comment="允许答题次数")
    show_answer: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否显示答案解析")
    anti_cheat: Mapped[bool] = mapped_column(Boolean, default=False, comment="防切屏")
    total_score: Mapped[float] = mapped_column(Float, default=100.0)
    pass_score: Mapped[float] = mapped_column(Float, default=60.0)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_local, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now_local, onupdate=now_local)

    paper: Mapped["Paper"] = relationship(lazy="selectin")
    assignments: Mapped[List["TaskAssignment"]] = relationship(
        back_populates="task", cascade="all, delete-orphan", lazy="selectin"
    )


class TaskAssignment(Base):
    """任务下发范围：班级 / 学生 / 分组。"""

    __tablename__ = "edu_task_assignment"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("edu_task.id", ondelete="CASCADE"), index=True)
    class_id: Mapped[Optional[int]] = mapped_column(ForeignKey("edu_class.id", ondelete="CASCADE"), nullable=True, index=True)
    student_id: Mapped[Optional[int]] = mapped_column(ForeignKey("sys_user.id", ondelete="CASCADE"), nullable=True, index=True)
    group_name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, comment="分组名称")
    notified: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否已通知")

    task: Mapped[Task] = relationship(back_populates="assignments")


class Submission(Base):
    """一次作答记录（学生 x 任务 x 次数）。"""

    __tablename__ = "edu_submission"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("edu_task.id", ondelete="CASCADE"), index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("sys_user.id", ondelete="CASCADE"), index=True)
    attempt: Mapped[int] = mapped_column(Integer, default=1, comment="第几次作答")

    status: Mapped[str] = mapped_column(String(16), default=GradeStatus.NOT_GRADED.value, index=True)
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    objective_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="客观题得分")
    subjective_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="主观题得分")
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_passed: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    class_rank: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="教师评语")

    # 防作弊与异常记录
    switch_count: Mapped[int] = mapped_column(Integer, default=0, comment="切屏次数")
    submit_count: Mapped[int] = mapped_column(Integer, default=0, comment="提交次数（防重复）")
    submit_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    grade_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_local, index=True)

    answers: Mapped[List["Answer"]] = relationship(
        back_populates="submission", cascade="all, delete-orphan", lazy="selectin"
    )


class Answer(Base):
    """逐题作答与批改结果。"""

    __tablename__ = "edu_answer"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    submission_id: Mapped[int] = mapped_column(ForeignKey("edu_submission.id", ondelete="CASCADE"), index=True)
    paper_item_id: Mapped[int] = mapped_column(ForeignKey("edu_paper_item.id", ondelete="CASCADE"), index=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("edu_question.id", ondelete="CASCADE"), index=True)

    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="学生答案")
    is_correct: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True, index=True)
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    full_score: Mapped[float] = mapped_column(Float, default=0.0)
    grader_type: Mapped[str] = mapped_column(String(16), default="auto", comment="auto/ai/manual")
    ai_comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="AI 建议评语")
    ai_error_points: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="AI 标注错误点 JSON")
    teacher_comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    submission: Mapped[Submission] = relationship(back_populates="answers")


class WrongQuestion(Base):
    """错题本：练习/考试做错自动收录。"""

    __tablename__ = "edu_wrong_question"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("sys_user.id", ondelete="CASCADE"), index=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("edu_question.id", ondelete="CASCADE"), index=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey("edu_subject.id", ondelete="CASCADE"), index=True)
    knowledge_point_id: Mapped[Optional[int]] = mapped_column(ForeignKey("edu_knowledge_point.id", ondelete="SET NULL"), nullable=True, index=True)

    wrong_answer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_count: Mapped[int] = mapped_column(Integer, default=1)
    error_reason: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True, comment="知识点不会/粗心/审题错误")
    ai_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="AI 分析错因")
    source_type: Mapped[str] = mapped_column(String(16), default="practice", comment="practice/exam/homework")
    source_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    source_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)

    is_mastered: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    mastered_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_wrong_at: Mapped[datetime] = mapped_column(DateTime, default=now_local, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_local)
