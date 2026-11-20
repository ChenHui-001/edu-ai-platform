"""流程引擎模型：定义、实例、待办任务、流转留痕。

设计要点（见 audit-reports/ontology-inventory/M6_DESIGN.md）：

- **定义以 M6 YAML 原文入库**，不把图拍平成 node_graph JSON。
  YAML 是唯一语义来源，DB 只是它的运行时投影，可随时重新同步。
- **实例用 (biz_type, biz_id) 软关联**业务对象，不外键到 paper/question 等
  具体业务表，避免流程引擎依赖各业务模型。
- **待办任务以 role_code 为主**：流程定义只声明"谁该审"（M5 角色），
  assignee_id 是运行时派发结果，可为空（无人认领时按角色可见）。
- 流程引擎是**编排层**，不接管业务状态字段。paper.status / question.status
  仍由现有 service 写入，流程只决定"什么时候调"。
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.utils.common import now_local


class FlowDefinition(Base):
    """流程定义（由 M6 YAML 同步而来）。"""

    __tablename__ = "edu_flow_definition"
    __table_args__ = (
        UniqueConstraint("code", name="uq_flow_definition_code"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(64), index=True, comment="流程编码，如 PAPER_REVIEW")
    name: Mapped[str] = mapped_column(String(128), comment="流程名")
    flow_type: Mapped[str] = mapped_column(String(20), comment="COLLABORATION / APPROVAL")
    trigger_type: Mapped[str] = mapped_column(String(20), default="MANUAL", comment="MANUAL/BEHAVIOR/SCHEDULE")
    trigger_behavior: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="BEHAVIOR 触发时引用 M2 行为 id")
    definition: Mapped[str] = mapped_column(Text, comment="M6 YAML 原文（activities + branches）")
    version: Mapped[int] = mapped_column(Integer, default=1, comment="定义版本号，变更递增")
    status: Mapped[int] = mapped_column(Integer, default=1, comment="0=草稿 1=启用 2=停用")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_local)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now_local, onupdate=now_local)


class FlowInstance(Base):
    """流程实例：一次针对具体业务对象的流程运行。"""

    __tablename__ = "edu_flow_instance"
    __table_args__ = (
        Index("ix_flow_instance_biz", "biz_type", "biz_id"),
        Index("ix_flow_instance_status", "status"),
        Index("ix_flow_instance_creator", "creator_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    def_id: Mapped[int] = mapped_column(
        ForeignKey("edu_flow_definition.id", ondelete="RESTRICT"), index=True)
    biz_type: Mapped[str] = mapped_column(String(32), comment="业务对象类型，如 paper / question")
    biz_id: Mapped[int] = mapped_column(Integer, comment="业务对象主键")
    biz_key: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, comment="业务唯一键")
    current_activity_ids: Mapped[str] = mapped_column(
        Text, default="[]", comment="JSON 数组：当前停留的活动")
    variables: Mapped[str] = mapped_column(
        Text, default="{}", comment="JSON：流程变量（网关条件求值用）")
    # 注意：这里**不能**再加 index=True —— 同一列已有显式索引
    # ix_flow_instance_status（见 __table_args__），两套命名会让迁移与模型
    # 差出一个 ix_edu_flow_instance_status，Alembic 一致性门禁直接红。
    status: Mapped[str] = mapped_column(
        String(20), default="RUNNING",
        comment="RUNNING/APPROVED/REJECTED/RETURNED/CANCELLED")
    creator_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("sys_user.id", ondelete="SET NULL"), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=now_local)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now_local, onupdate=now_local)


class FlowTask(Base):
    """待办任务：流程停留点上的待处理事项。"""

    __tablename__ = "edu_flow_task"
    __table_args__ = (
        Index("ix_flow_task_status_role", "status", "role_code"),
        Index("ix_flow_task_assignee_status", "assignee_id", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    instance_id: Mapped[int] = mapped_column(
        ForeignKey("edu_flow_instance.id", ondelete="CASCADE"), index=True)
    activity_id: Mapped[str] = mapped_column(String(64), comment="活动 id")
    activity_type: Mapped[str] = mapped_column(String(20), comment="USER_TASK / APPROVAL_TASK")
    activity_name: Mapped[str] = mapped_column(String(128), default="")
    role_code: Mapped[str] = mapped_column(String(32), index=True, comment="M5 角色 code（主）")
    assignee_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("sys_user.id", ondelete="SET NULL"), nullable=True, index=True,
        comment="实际处理人（派发结果，可空）")
    status: Mapped[str] = mapped_column(String(20), default="TODO", index=True,
        comment="TODO/CLAIMED/DONE/CANCEL")
    action: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, comment="APPROVE/REJECT/RETURN/CANCEL")
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="处理意见")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_local)
    claimed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    done_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    # 截止时间：流程定义可声明，超时后待办仍可处理但会被标记为逾期。
    deadline: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)
    # 催办次数与最近催办时间：用于「催了没人管」的判断与频次限制。
    urge_count: Mapped[int] = mapped_column(Integer, default=0, comment="催办次数")
    last_urged_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="最近催办时间")
    # 转办次数与最近转办时间：转办不是「认领」，是显式指派给别人。
    transfer_count: Mapped[int] = mapped_column(Integer, default=0, comment="转办次数")
    last_transferred_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="最近转办时间")


class FlowTransfer(Base):
    """转办留痕：待办从谁转给谁。

    **为什么单独建表而不是往 FlowHistory 里塞**：FlowHistory 是流程流转的
    不可变轨迹（活动推进、审批结果），转办不改变流程走向 —— 它是**同一活动
    上的处理人变更**。混在一起会让「流转轨迹」这条线被转办记录污染，
    而「这条待办被转手过几次、每次转给了谁」又需要独立查询。
    """

    __tablename__ = "edu_flow_transfer"
    __table_args__ = (
        Index("ix_flow_transfer_task", "task_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_id: Mapped[int] = mapped_column(
        ForeignKey("edu_flow_task.id", ondelete="CASCADE"), index=True)
    from_user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("sys_user.id", ondelete="SET NULL"), nullable=True,
        comment="转出方（可空：待办尚未认领时转办）")
    to_user_id: Mapped[int] = mapped_column(
        ForeignKey("sys_user.id", ondelete="CASCADE"),
        comment="接收方")
    operator_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("sys_user.id", ondelete="SET NULL"), nullable=True,
        comment="发起转办的人")
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="转办理由")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_local, index=True)


class FlowHistory(Base):
    """流转留痕：每一次动作的不可变记录。"""

    __tablename__ = "edu_flow_history"
    __table_args__ = (
        Index("ix_flow_history_instance", "instance_id"),
        Index("ix_flow_history_created", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    instance_id: Mapped[int] = mapped_column(
        ForeignKey("edu_flow_instance.id", ondelete="CASCADE"), index=True)
    activity_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    activity_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    operator_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("sys_user.id", ondelete="SET NULL"), nullable=True)
    operator_name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    action: Mapped[str] = mapped_column(
        String(20), comment="START/APPROVE/REJECT/RETURN/EXECUTE/CANCEL")
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    from_activity: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    to_activity: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_local)
