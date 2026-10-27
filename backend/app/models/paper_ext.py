"""标准组卷扩展模型：命题标准库 / 试卷版本快照 / 试卷收藏。

独立成文件的原因：
- `question.py` 已承载题库 + 试卷核心 CRUD 模型，再塞入命题标准与版本表会让
  那个文件同时承担「业务实体」与「配置元数据」两类职责；
- 命题标准是**管理员可配置**的元数据（题型结构/分值/难度），与试卷实体
  生命周期无关，删卷不应影响标准；
- 版本快照与收藏是纯附属表，只依赖 paper_id，便于单独演进。

外键删除语义（与既有模型保持一致的口径）：
- PaperVersion.paper_id / PaperFavorite.paper_id = CASCADE（纸张没了快照无意义）
- ExamStandard.owner_id = SET NULL（标准是组织资产，创建人被删不该丢标准）
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.utils.common import now_local


class ExamStandard(Base):
    """命题标准（湖北学业水平考试标准）。

    一条记录 = 某学段某学科某考试类型的完整命题规格：
    题型结构（含每题型题量/单题分值）+ 总分 + 时长 + 难度分布。

    `sections` 是 JSON 文本，结构形如：
        [{"code": "single", "name": "一、选择题", "count": 10,
          "score_per": 3, "sort": 1, "difficulty": "easy"}]
    之所以用 JSON 而非子表：题型结构是**整体配置**，无需单独查询某个题型，
    且管理员改结构时是一次性覆盖写，子表只会增加事务复杂度。

    `difficulty_ratio` 同样是 JSON 文本，存**百分制整数**（easy/medium/hard），
    例如 {"easy": 70, "medium": 20, "hard": 10}。整数而非小数是刻意的：
    历史实现里用 0.3/0.5/0.2 小数权重，再被 `int()` 截断成 0，导致组不出题。
    """

    __tablename__ = "edu_exam_standard"
    __table_args__ = (
        # 同一区域 + 学段 + 学科 + 考试类型只能有一套启用标准，
        # 避免组卷时随机命中不同标准导致同科试卷结构不一致。
        UniqueConstraint(
            "region", "stage", "subject_name", "exam_type",
            name="uq_exam_standard_dim",
        ),
        Index("ix_exam_standard_lookup", "stage", "subject_name", "is_active"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), comment="标准名称，如 湖北省初中数学学业水平考试")
    region: Mapped[str] = mapped_column(String(32), default="hubei", index=True, comment="区域")
    stage: Mapped[str] = mapped_column(
        String(16), default="junior", index=True, comment="primary小学 / junior初中")
    subject_name: Mapped[str] = mapped_column(
        String(32), index=True, comment="学科名（与 edu_subject.name 对齐，非 id）")
    exam_type: Mapped[str] = mapped_column(
        String(32), default="final", index=True,
        comment="final期末 / hsee学业水平考试 / unit单元测 / monthly月考")

    total_score: Mapped[float] = mapped_column(Float, default=100.0)
    duration: Mapped[int] = mapped_column(Integer, default=120, comment="考试时长（分钟）")
    sections: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="题型结构 JSON：[{code,name,count,score_per,sort,difficulty}]")
    difficulty_ratio: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="难度分布 JSON（百分制整数）：{easy,medium,hard}")

    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    is_default: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="该学段学科默认选用的标准")
    # seed=内置种子（随版本升级可覆盖） manual=管理员手工配置（升级不覆盖）
    source: Mapped[str] = mapped_column(String(16), default="seed", index=True)
    sort: Mapped[int] = mapped_column(Integer, default=0)

    owner_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("sys_user.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_local, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now_local, onupdate=now_local)


class PaperVersion(Base):
    """试卷版本快照（可回溯）。

    每次试卷题目结构发生变化（组卷/编辑/替换/重排）前，先把**变更后的完整状态**
    写入快照。sections 与 items 一起存，保证回溯时能完整还原版式。

    snapshot 结构：
        {"paper": {...标量字段...},
         "items": [{"question_id", "sort_order", "score", "section_name",
                    "stem", "type", "difficulty", "answer", "analysis"}]}
    存 stem/answer 是刻意的冗余：题库题目可能后续被编辑或删除，
    只存 question_id 会让历史版本还原出「空壳」。
    """

    __tablename__ = "edu_paper_version"
    __table_args__ = (
        UniqueConstraint("paper_id", "version", name="uq_paper_version"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    paper_id: Mapped[int] = mapped_column(
        ForeignKey("edu_paper.id", ondelete="CASCADE"), index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    snapshot: Mapped[str] = mapped_column(Text, comment="整卷快照 JSON")
    change_note: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    item_count: Mapped[int] = mapped_column(Integer, default=0)
    total_score: Mapped[float] = mapped_column(Float, default=0.0)

    created_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("sys_user.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_local, index=True)


class PaperFavorite(Base):
    """试卷收藏（教师个人）。"""

    __tablename__ = "edu_paper_favorite"
    __table_args__ = (
        UniqueConstraint("paper_id", "user_id", name="uq_paper_favorite"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    paper_id: Mapped[int] = mapped_column(
        ForeignKey("edu_paper.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("sys_user.id", ondelete="CASCADE"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_local)
