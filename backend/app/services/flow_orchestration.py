"""业务流程编排适配层（M6）。

把「业务事件 → 流程引擎动作」的映射从各个 API 文件里抽出来。

**为什么单独成文件**：编排代码是纯胶水逻辑，塞进 API 文件会让那些
本来就超长的文件继续变胖（`check_file_size.py` 的预算只许降不许升），
而且胶水逻辑混在业务逻辑里，出问题时很难判断是业务错了还是编排错了。

**设计边界（务必保持）**：
  - 流程引擎是**编排层**，不接管业务状态字段。`paper.status` /
    `registration.status` 仍由既有 service 写入；
  - 流程实例启动/推进失败**不得**让业务接口失败——业务已受理时，
    业务状态必须如实反映，编排失败只记 warning。

第二条是硬约束：审批流是增强项，不是主链路的强依赖。否则引擎一个 bug
就能让整个业务不可用，而用户看到的只是"提交审核报 500"。
"""
from typing import Optional

from app.core.logger import get_logger
from app.services.flow_engine import FlowEngine

logger = get_logger("flow_orchestration")


def start_paper_review_flow(db, paper, user) -> None:
    """提交审核时启动试卷审核流程实例（产生年级管理员待办）。"""
    try:
        engine = FlowEngine(db)
        existing = engine.find_instance("paper", paper.id)
        if existing is not None:
            return  # 已有运行中的实例，不重复发起
        engine.start(
            "PAPER_REVIEW_001", "paper", paper.id, f"PAPER-{paper.id}",
            variables={
                "paper": {
                    "status": paper.status,
                    "share_scope": paper.share_scope,
                },
            },
            creator_id=user.id,
        )
    except Exception as exc:  # 编排失败不影响业务结果
        logger.warning(f"试卷审核流程启动失败 paper={paper.id}: {exc}")


def complete_paper_review_flow(db, paper, user, action: str,
                               comment: Optional[str] = None) -> None:
    """审核通过/驳回时推进试卷审核流程实例。"""
    try:
        engine = FlowEngine(db)
        instance = engine.find_instance("paper", paper.id)
        if instance is None:
            return
        tasks = engine.pending_tasks(instance.id)
        if not tasks:
            return
        task_id = tasks[0]["id"]
        if action == "APPROVE":
            engine.approve(task_id, comment=comment, operator=user)
        else:
            engine.reject(task_id, comment=comment, operator=user)
    except Exception as exc:  # 编排失败不影响业务结果
        logger.warning(f"试卷审核流程推进失败 paper={paper.id}: {exc}")


def sync_paper_review_flow(db, paper, user, action: str,
                          comment: Optional[str] = None) -> None:
    """试卷审核的**统一编排入口**。

    action 取值 submit / approve / reject——与 `review_paper` 的 action 同名，
    由本函数分派到启动或推进。API 层因此只需要一次调用，不必在三个分支里
    各写一遍编排语句（`paper_compose.py` 已在文件预算边缘，多一行就破）。
    """
    if action == "submit":
        start_paper_review_flow(db, paper, user)
    else:
        complete_paper_review_flow(
            db, paper, user, "APPROVE" if action == "approve" else "REJECT",
            comment=comment)


def start_registration_flow(db, user, biz_key: Optional[str] = None) -> None:
    """提交注册申请时启动注册审批流程实例（产生系统管理员待办）。"""
    try:
        engine = FlowEngine(db)
        existing = engine.find_instance("registration", user.id)
        if existing is not None:
            return
        engine.start(
            # code 由 M6 YAML 的 flow id 归一化而来：
            # FLOW-REGISTRATION-001-T -> REGISTRATION_001_T
            "REGISTRATION_001_T", "registration", user.id, biz_key,
            variables={"user": {"username": getattr(user, "username", "")}},
            creator_id=user.id,
        )
    except Exception as exc:  # 编排失败不影响业务结果
        logger.warning(f"注册审批流程启动失败 user={user.id}: {exc}")


def complete_registration_flow(db, user, action: str,
                               comment: Optional[str] = None) -> None:
    """注册审批通过/驳回时推进流程实例。"""
    try:
        engine = FlowEngine(db)
        instance = engine.find_instance("registration", user.id)
        if instance is None:
            return
        tasks = engine.pending_tasks(instance.id)
        if not tasks:
            return
        task_id = tasks[0]["id"]
        if action == "APPROVE":
            engine.approve(task_id, comment=comment, operator=user)
        else:
            engine.reject(task_id, comment=comment, operator=user)
    except Exception as exc:  # 编排失败不影响业务结果
        logger.warning(f"注册审批流程推进失败 user={user.id}: {exc}")
