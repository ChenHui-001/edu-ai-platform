"""待办升级动作：转办 / 催办 / 超时（M6）。

**为什么从 flow_engine.py 拆出来**：flow_engine.py 是流程引擎的主文件，
已接近上帝文件阈值。转办、催办、超时是**待办生命周期里的「升级动作」**——
它们不推进流程走向，只改变「这条待办由谁处理、有没有被提醒、
是否已经过期」，是一组内聚的附加能力，单独成模块更清楚。

**与主流程的边界**：
  - 转办不改变流程走向，只变更处理人（并留痕）；
  - 催办不改变待办状态，只发通知；
  - 超时是**计算属性**，逾期不自动关闭待办。

所以这三件事都不属于「流程推进」，放在主文件里反而模糊了边界。
"""
from typing import Any, Dict, List, Optional

from sqlalchemy import select

from app.core.exception import BusinessException, NotFoundException
from app.models.flow import FlowInstance, FlowTask, FlowTransfer
from app.services import notification as notify_cat
from app.services.notification import notify
from app.utils.common import now_local

# 常量与业务标签从主模块导入：单向下（mixin -> engine），
# 主模块不 import mixin 的任何符号，因此不会形成循环导入。
from app.services.flow_constants import (
    BIZ_LABELS, TASK_CLAIMED, TASK_TODO, URGE_COOLDOWN_MINUTES,
)


class FlowEscalationMixin:
    """转办 / 催办 / 超时的实现。"""

    def transfer(self, task_id: int, to_user_id: int, operator: Any = None,
                 reason: Optional[str] = None) -> FlowTask:
        """转办：把待办指派给另一个人。

        与「认领」的区别：认领是**自己接手**（角色不变），转办是**指定别人**
        （处理人变更）。两者的区别在留痕上体现 —— 转办必须留下
        「谁转给了谁」的记录，否则事后无法解释「这条待办为什么一直没人处理」。

        权限：发起人必须持有该待办对应的角色 —— 否则任何登录用户都能把
        别人的待办转走。
        """
        task = self._load_task(task_id)
        self._assert_operable(task)
        # 操作人必须是该待办角色的持有者。此前只校验了**目标用户**，
        # 任何登录用户都能把别人的待办转走 —— 越权。
        self._assert_role_holder(task, operator)
        operator_id = self._operator_id(operator)

        target = self._load_transfer_target(task, to_user_id)
        # 不能转给自己：那是「认领」，语义不同，留痕也不该混。
        if target.id == operator_id:
            raise BusinessException("不能转办给自己，请使用「认领」")

        self.db.add(FlowTransfer(
            task_id=task.id,
            from_user_id=task.assignee_id,
            to_user_id=target.id,
            operator_id=operator_id,
            reason=reason,
            created_at=now_local(),
        ))
        task.assignee_id = target.id
        task.status = TASK_CLAIMED
        task.claimed_at = task.claimed_at or now_local()
        task.transfer_count = (task.transfer_count or 0) + 1
        task.last_transferred_at = now_local()
        self.db.commit()
        return task

    def _load_transfer_target(self, task: FlowTask, to_user_id: int) -> Any:
        """取转办目标用户，并校验其持有该待办对应的角色。"""
        from app.models import User

        target_id = int(to_user_id)
        target = self.db.get(User, target_id)
        if target is None:
            raise NotFoundException("转办目标用户不存在")
        if not getattr(target, "is_active", False):
            raise BusinessException("转办目标用户账号状态异常")
        # 目标必须持有该待办对应的角色，否则转过去也处理不了。
        role_codes = self._user_role_codes(target)
        if task.role_code not in role_codes:
            raise BusinessException(
                f"该用户不具备「{task.role_code}」角色，无法接手这条待办")
        return target

    def transfer_candidates(self, task_id: int) -> List[Dict[str, Any]]:
        """可转办人员：持有该待办角色的其他用户（不含当前处理人）。"""
        from app.models import User

        task = self._load_task(task_id)
        rows = self.db.scalars(
            select(User).where(User.status == "active").order_by(User.id)
        ).all()
        out = []
        for u in rows:
            if u.id == task.assignee_id:
                continue
            if task.role_code not in self._user_role_codes(u):
                continue
            out.append({
                "id": u.id,
                "username": u.username,
                "real_name": u.real_name or u.username,
                "current_assignee": u.id == task.assignee_id,
            })
        return out

    # ------------------------------------------------------------------
    # 催办
    # ------------------------------------------------------------------

    def urge(self, task_id: int, operator: Any = None,
             comment: Optional[str] = None) -> Dict[str, Any]:
        """催办：给待办处理人发提醒通知。

        催办对象是**已认领的**处理人；尚未认领的待办是「角色级待办池」，
        催办没有明确对象 —— 此时按同角色的其他处理人处理不了
        （他们还没接手），所以直接报错并提示先认领。

        频次限制：同一待办两次催办间隔至少 `URGE_COOLDOWN_MINUTES` 分钟。
        """
        task = self._load_task(task_id)
        self._assert_operable(task)
        self._assert_role_holder(task, operator)
        if not task.assignee_id:
            raise BusinessException(
                "该待办尚未认领，无人可催。请先认领或等待角色内其他人接手。")

        last = task.last_urged_at
        if last is not None:
            elapsed = (now_local() - last).total_seconds() / 60
            if elapsed < URGE_COOLDOWN_MINUTES:
                wait = int(URGE_COOLDOWN_MINUTES - elapsed)
                raise BusinessException(f"催办过于频繁，请 {wait} 分钟后再试")

        from app.models import User

        target = self.db.get(User, task.assignee_id)
        if target is None:
            raise BusinessException("待办处理人不存在，无法催办")

        # 通知正文带上待办信息，接收方不用点进详情才知道被催的是哪件事。
        instance = self.db.get(FlowInstance, task.instance_id)
        biz_label = ""
        if instance is not None:
            biz_label = BIZ_LABELS.get(instance.biz_type, instance.biz_type)

        notify(
            self.db, target.id,
            title=f"待办催办：{task.activity_name}",
            content=(f"「{biz_label}」有一条待办「{task.activity_name}」等待处理。"
                     + (f"催办留言：{comment}" if comment else "")),
            type="system", biz_type="flow", biz_id=task.id,
            category=notify_cat.CATEGORY_SYSTEM,
        )
        task.urge_count = (task.urge_count or 0) + 1
        task.last_urged_at = now_local()
        self.db.commit()
        return {
            "urged": True,
            "to_user_id": target.id,
            "to_user_name": target.real_name or target.username,
            "urge_count": task.urge_count,
        }

    # ------------------------------------------------------------------
    # 超时
    # ------------------------------------------------------------------

    def overdue_tasks(self, user: Any, page: int = 1,
                      page_size: int = 20) -> Dict[str, Any]:
        """逾期待办：已过截止时间但仍未处理。

        逾期**不自动关闭**待办 —— 流程卡在谁手上，应该由人决定怎么办
        （催办、转办或直接处理），引擎无权替人把事情结掉。
        """
        role_codes = self._user_role_codes(user)
        if not role_codes:
            return {"items": [], "total": 0, "page": page, "page_size": page_size}
        now = now_local()
        query = (
            select(FlowTask)
            .where(FlowTask.status.in_([TASK_TODO, TASK_CLAIMED]),
                   FlowTask.role_code.in_(role_codes),
                   FlowTask.deadline.isnot(None),
                   FlowTask.deadline < now)
            .order_by(FlowTask.deadline.asc())
        )
        total = len(self.db.scalars(query).all())
        rows = self.db.scalars(query.offset((page - 1) * page_size)
                               .limit(page_size)).all()
        return {
            "items": [self.task_out(row) for row in rows],
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    def set_deadline(self, task_id: int, deadline: Optional[Any] = None,
                     operator: Any = None) -> FlowTask:
        """设置待办截止时间。

        deadline 为 None 表示清除截止时间（不再是逾期待办）。
        """
        task = self._load_task(task_id)
        self._assert_operable(task)
        task.deadline = deadline
        self.db.commit()
        return task
