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


class PaperStatus(str, enum.Enum):
    """试卷状态（V3 标准组卷审核流）。

    draft→pending→published 的审核链只对**进入公共库**的试卷生效；
    私有卷 / 仅共享卷直接 published，保持既有行为不变。
    """

    DRAFT = "draft"
    PENDING = "pending"        # 待审核（申请进入公共库）
    PUBLISHED = "published"
    REJECTED = "rejected"      # 审核驳回
    ARCHIVED = "archived"      # 停用（被任务引用时不可删，只能停用）


class ShareScope(str, enum.Enum):
    """共享范围三级 + 私有 + 公共库。"""

    PRIVATE = "private"        # 仅自己
    GRADE = "grade"            # 同年级同学科教师
    SCHOOL = "school"          # 全校同学科教师
    PUBLIC = "public"          # 公共库（需审核）


class SharePermission(str, enum.Enum):
    """共享权限三级。"""

    VIEW = "view"              # 仅查看
    REUSE = "reuse"            # 可引用另存（复制为新卷）
    EDIT = "edit"              # 可编辑


class Paper(Base):
    """试卷。

    V3 扩展字段全部可空 / 带默认值，老数据升级后行为不变：
    - `status` 默认 published，存量试卷不会因为新增审核态而"消失"
    - `share_scope` 默认 private，但可见性判定仍以 `is_shared` 为主，两者取或
    """

    __tablename__ = "edu_paper"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), index=True)
    grade_id: Mapped[int] = mapped_column(ForeignKey("edu_grade.id", ondelete="CASCADE"), index=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey("edu_subject.id", ondelete="CASCADE"), index=True)
    total_score: Mapped[float] = mapped_column(Float, default=100.0)
    duration: Mapped[int] = mapped_column(Integer, default=60, comment="建议时长（分钟）")
    # 原为 String(64)：{"easy":70,"medium":20,"hard":10} 已占 33 字符，
    # 带小数或额外维度必然超 64 被截断成非法 JSON（实测组卷后前端解析失败）。
    # 改 Text 后既兼容存量 varchar 数据，也不再依赖长度猜测。
    difficulty_ratio: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="难度分布 JSON（百分制整数）")
    knowledge_coverage: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="知识点覆盖报告 JSON")
    difficulty_report: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="难度分析 JSON")

    creator_id: Mapped[int] = mapped_column(ForeignKey("sys_user.id", ondelete="CASCADE"), index=True)
    source: Mapped[str] = mapped_column(String(16), default="manual", comment="manual/ai")
    is_shared: Mapped[bool] = mapped_column(Boolean, default=False, comment="共享给同科教师")
    use_count: Mapped[int] = mapped_column(Integer, default=0)

    # ---- V3 标准组卷扩展 ----
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="试卷说明/命题双向细目表")
    exam_type: Mapped[Optional[str]] = mapped_column(
        String(32), nullable=True, index=True, comment="final/hsee/unit/monthly/custom")
    stage: Mapped[Optional[str]] = mapped_column(
        String(16), nullable=True, index=True, comment="primary/junior（冗余便于筛选）")
    textbook_version: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(
        String(16), default=PaperStatus.PUBLISHED.value, index=True,
        comment="draft/pending/published/rejected/archived")
    standard_id: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, index=True, comment="依据的命题标准 id（不设 FK：标准可重建）")
    share_scope: Mapped[str] = mapped_column(
        String(16), default=ShareScope.PRIVATE.value, index=True, comment="private/grade/school/public")
    review_comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="审核意见")
    review_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("sys_user.id", ondelete="SET NULL"), nullable=True)
    review_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    current_version: Mapped[int] = mapped_column(Integer, default=1, comment="当前版本号")
    # 组卷参数留档：便于"按上次参数再组一套"与结果复现
    generation_params: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="组卷参数 JSON（模式/题型结构/难度/来源策略）")
    type_report: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="题型分布报告 JSON（第三份报告）")

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
    # 大题分组以 code 为准（题型标识）。用名称分组会在「一、选择题」被改成
    # 「一、单项选择」后失配；code 不变，改名不影响分组归属。
    section_code: Mapped[Optional[str]] = mapped_column(
        String(32), nullable=True, index=True, comment="大题题型标识 single/blank/short…")
    section_sort: Mapped[int] = mapped_column(Integer, default=0, comment="大题顺序")
    # 单题分值可覆盖题库默认分（卷面分与题库分解耦），此处仅记录来源便于审计
    score_override: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="分值是否由教师手工指定（非题库默认）")

    paper: Mapped[Paper] = relationship(back_populates="items")
    question: Mapped[Question] = relationship(lazy="selectin")


class PaperShare(Base):
    """试卷分享记录。

    V3 增加 `permission`（三级权限）与 `scope`（分享时的范围快照）。
    去重仍以 (paper_id, to_user_id) 为准；`UniqueConstraint` 只对新建库生效
    （SQLite 不能给已存在的表 ALTER ADD CONSTRAINT），老库靠写入口的
    exists 检查保证幂等——两处逻辑都在 `_share_paper_to` 收口。
    """

    __tablename__ = "edu_paper_share"
    __table_args__ = (
        UniqueConstraint("paper_id", "to_user_id", name="uq_paper_share_target"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    paper_id: Mapped[int] = mapped_column(ForeignKey("edu_paper.id", ondelete="CASCADE"), index=True)
    from_user_id: Mapped[int] = mapped_column(ForeignKey("sys_user.id", ondelete="CASCADE"))
    to_user_id: Mapped[int] = mapped_column(ForeignKey("sys_user.id", ondelete="CASCADE"), index=True)
    permission: Mapped[str] = mapped_column(
        String(16), default="view", comment="view仅查看 / reuse可另存 / edit可编辑")
    scope: Mapped[Optional[str]] = mapped_column(
        String(16), nullable=True, comment="分享时的范围：grade/school/user")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_local)
