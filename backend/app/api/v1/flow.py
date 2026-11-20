"""流程引擎接口（/api/v1/flow/*）。

提供待办中心的三件事：
  - 我的待办（按角色可见）
  - 我的已办（按处理人可见）
  - 我发起的流程

以及流程实例详情（含完整留痕）。

权限模型（与 M5 一致）：待办按 `role_code` 过滤——流程定义声明"谁该审"，
任何持有该角色的登录用户都能看到并处理同一份待办（认领后 assignee_id 记录实际处理人）。
这与「提交作答」这类归属校验型接口不同：审批是**角色职责**，不是个人数据。
"""
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin, get_current_user
from app.core.database import get_db
from app.schemas.flow import (
    FlowActionIn, FlowDeadlineIn, FlowReturnIn, FlowTransferIn, FlowUrgeIn,
)
from app.services.flow_engine import FlowEngine
from app.utils.common import PageParams, ok

router = APIRouter(prefix="/flow", tags=["流程待办"])


@router.get("/todo", summary="我的待办")
def todo_list(params: PageParams = Depends(),
               db: Session = Depends(get_db), user=Depends(get_current_user)):
    """当前用户角色可见的待办任务。"""
    engine = FlowEngine(db)
    return ok(engine.todo_list(user, page=params.page, page_size=params.page_size))


@router.get("/done", summary="我的已办")
def done_list(params: PageParams = Depends(),
              db: Session = Depends(get_db), user=Depends(get_current_user)):
    """当前用户处理过的任务。"""
    engine = FlowEngine(db)
    return ok(engine.done_list(user, page=params.page, page_size=params.page_size))


@router.get("/instances", summary="我发起的流程")
def my_instances(params: PageParams = Depends(),
                 db: Session = Depends(get_db), user=Depends(get_current_user)):
    """当前用户发起的流程实例。"""
    engine = FlowEngine(db)
    return ok(engine.my_instances(user, page=params.page, page_size=params.page_size))


@router.get("/instances/{instance_id}", summary="流程实例详情")
def instance_detail(instance_id: int,
                    db: Session = Depends(get_db), user=Depends(get_current_user)):
    """流程实例详情：当前活动、待办列表与完整流转留痕。"""
    engine = FlowEngine(db)
    return ok(engine.instance_detail(instance_id))


@router.post("/tasks/{task_id}/claim", summary="认领待办")
def claim_task(task_id: int, db: Session = Depends(get_db),
               user=Depends(get_current_user)):
    """认领待办：绑定实际处理人（角色仍可由其他人接手）。"""
    engine = FlowEngine(db)
    task = engine.claim(task_id, operator=user)
    return ok(engine.task_out(task), message="已认领")


@router.post("/tasks/{task_id}/approve", summary="审批通过")
def approve_task(task_id: int, data: Optional[FlowActionIn] = None,
                 db: Session = Depends(get_db), user=Depends(get_current_user)):
    """审批通过。"""
    comment = data.comment if data else None
    engine = FlowEngine(db)
    instance = engine.approve(task_id, comment=comment, operator=user)
    return ok(engine.instance_out(instance), message="已通过")


@router.post("/tasks/{task_id}/reject", summary="审批驳回")
def reject_task(task_id: int, data: Optional[FlowActionIn] = None,
                db: Session = Depends(get_db), user=Depends(get_current_user)):
    """审批驳回（意见是否必填由流程规则强制）。"""
    comment = data.comment if data else None
    engine = FlowEngine(db)
    instance = engine.reject(task_id, comment=comment, operator=user)
    return ok(engine.instance_out(instance), message="已驳回")


@router.post("/tasks/{task_id}/return", summary="退回重填")
def return_task(task_id: int, data: FlowReturnIn,
                db: Session = Depends(get_db), user=Depends(get_current_user)):
    """退回到指定活动重新提交。"""
    engine = FlowEngine(db)
    instance = engine.return_to(
        task_id, data.target_activity_id, comment=data.comment, operator=user)
    return ok(engine.instance_out(instance), message="已退回")


@router.post("/tasks/{task_id}/cancel", summary="取消流程")
def cancel_task(task_id: int, data: Optional[FlowActionIn] = None,
                db: Session = Depends(get_db), user=Depends(get_current_user)):
    """取消流程（引擎级动作，不要求流程定义声明 CANCEL）。"""
    comment = data.comment if data else None
    engine = FlowEngine(db)
    instance = engine.cancel(task_id, comment=comment, operator=user)
    return ok(engine.instance_out(instance), message="已取消")


@router.post("/definitions/sync", summary="同步流程定义")
def sync_definitions(db: Session = Depends(get_db), user=Depends(get_current_admin)):
    """把 M6 YAML 的目标流程同步进数据库（幂等）。

    仅系统管理员可用——定义同步会改变待办的产生方式。
    """
    engine = FlowEngine(db)
    count = engine.sync_definitions()
    return ok({"synced": count}, message=f"已同步 {count} 条流程定义")


@router.get("/overdue", summary="逾期待办")
def overdue_list(params: PageParams = Depends(),
                 db: Session = Depends(get_db), user=Depends(get_current_user)):
    """已过截止时间但仍未处理的待办。

    逾期**不自动关闭**待办——流程卡在谁手上由人决定怎么办
    （催办 / 转办 / 直接处理），引擎无权替人把事情结掉。
    """
    engine = FlowEngine(db)
    return ok(engine.overdue_tasks(user, page=params.page, page_size=params.page_size))


@router.get("/tasks/{task_id}/transfer-candidates", summary="可转办人员")
def transfer_candidates(task_id: int, db: Session = Depends(get_db),
                        user=Depends(get_current_user)):
    """持有该待办角色的其他用户（不含当前处理人）。"""
    engine = FlowEngine(db)
    return ok(engine.transfer_candidates(task_id))


@router.post("/tasks/{task_id}/transfer", summary="转办待办")
def transfer_task(task_id: int, data: FlowTransferIn,
                  db: Session = Depends(get_db), user=Depends(get_current_user)):
    """把待办转给另一个人（同一角色内）。

    与「认领」的区别：认领是自己接手，转办是指定别人。
    转办会留下「谁转给了谁」的留痕。
    """
    engine = FlowEngine(db)
    task = engine.transfer(task_id, data.to_user_id, operator=user, reason=data.reason)
    return ok(engine.task_out(task), message="已转办")


@router.post("/tasks/{task_id}/urge", summary="催办")
def urge_task(task_id: int, data: Optional[FlowUrgeIn] = None,
              db: Session = Depends(get_db), user=Depends(get_current_user)):
    """给待办处理人发提醒通知。

    有频次限制（同一待办 30 分钟内只能催一次）—— 否则管理员能连点几十次，
    把对方的通知列表刷爆。
    """
    engine = FlowEngine(db)
    result = engine.urge(task_id, operator=user,
                          comment=data.comment if data else None)
    return ok(result, message=f"已催办 {result['to_user_name']}")


@router.put("/tasks/{task_id}/deadline", summary="设置待办截止时间")
def set_deadline_task(task_id: int, data: FlowDeadlineIn,
                      db: Session = Depends(get_db),
                      user=Depends(get_current_user)):
    """设置 / 清除待办的截止时间。

    活动声明的 timeout 给出**默认**截止时间，但现实里审核有时需要更宽限
    （出差、跨节假日），有时要提前收口（快放暑假了）。这个端点让管理端
    能按条调整，清除（传 null）则该待办不再计入逾期待办。
    """
    engine = FlowEngine(db)
    task = engine.set_deadline(task_id, data.deadline, operator=user)
    return ok(engine.task_out(task), message="已设置截止时间")
