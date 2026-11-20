"""流程引擎（M6 落地实现）。

流程引擎是**编排层**，不接管业务状态字段：
  - `paper.status` / `question.status` 等业务状态**保留不动**，
    仍由现有 service（M2 行为）写入；
  - 流程只决定"什么时候调"以及"由谁审"。

设计要点（见 audit-reports/ontology-inventory/M6_DESIGN.md）：
  1. 定义以 M6 YAML 原文入库，DB 只是运行时投影，可用 `sync_definitions` 重放；
  2. 实例用 (biz_type, biz_id) 软关联业务对象，引擎不依赖具体业务模型；
  3. 待办任务以 role_code 为主（对齐 M5「角色任务」语义），
     assignee_id 是派发结果，可为空；
  4. 网关分支用规则引擎求值，规则来自 M3，字段可见性 fail-closed。

并发安全：SQLite 单写者模型下，同一实例的并发处理可能撞车。
本实现用「任务状态条件更新」做乐观校验（见 `_close_task`），
让并发的第二次审批拿到 0 行更新并被拒绝，而不是静默覆盖。
"""
from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Dict, Iterable, List, Optional, Tuple

import yaml
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.exception import BusinessException, NotFoundException, PermissionException
from app.models.flow import (
    FlowDefinition, FlowHistory, FlowInstance, FlowTask,
)
from app.services.flow_constants import (
    ACT_APPROVAL_TASK, ACT_END, ACT_GATEWAY, ACT_START,
    BIZ_LABELS,
    HUMAN_ACTIVITY_TYPES, INSTANCE_APPROVED, INSTANCE_CANCELLED,
    INSTANCE_REJECTED, INSTANCE_RETURNED, INSTANCE_RUNNING,
    ROLE_ID_TO_CODE, TASK_CANCEL, TASK_CLAIMED, TASK_DONE,
    TASK_TODO, TERMINAL_INSTANCE_STATUS,
)
from app.services.flow_escalation import FlowEscalationMixin
from app.services.rule_engine import RuleRegistry, RuleViolation
from app.utils.common import now_local


# ══════════════════════════════════════════════════════════
# 常量
# ══════════════════════════════════════════════════════════

def role_code_of(role_ref: Optional[str]) -> str:
    """把本体角色 id 翻译成数据库 role code。

 已经是 code 的（'teacher'）原样返回——这样流程定义可以直接写
    运行时 code，不必强制走本体 id。
    """
    if not role_ref:
        return ""
    if role_ref in ROLE_ID_TO_CODE:
        return ROLE_ID_TO_CODE[role_ref]
    return role_ref

# M6 YAML 的候选路径：
#   1) backend/app/ontology/ —— **随代码分发**的副本（容器镜像里只有 backend/app，
#      没有 audit-reports/，所以生产必须靠这一份）；
#   2) 仓库根下的 audit-reports/ontology-inventory/ —— 盘点的权威副本（开发态优先读它，
#      这样改本体立刻生效，不用同步两份）。
_APP_ONTOLOGY_DIR = pathlib.Path(__file__).resolve().parents[1] / "ontology"
_FLOW_MODEL_CANDIDATES = (
    pathlib.Path(__file__).resolve().parents[3]
    / "audit-reports" / "ontology-inventory" / "m6-flow-model.yaml",
    _APP_ONTOLOGY_DIR / "m6-flow-model.yaml",
)


def _find_flow_model_path() -> Optional[pathlib.Path]:
    for path in _FLOW_MODEL_CANDIDATES:
        if path.exists():
            return path
    return None


class FlowDefinitionError(BusinessException):
    """流程定义本身不合法（缺活动、悬空后继、循环等）。"""


@dataclass(frozen=True)
class Activity:
    """流程定义中的一个活动（归一化视图）。"""

    id: str
    name: str
    type: str
    next_activities: Tuple[str, ...]
    branches: Tuple[Dict[str, Any], ...]
    role_ref: Optional[str]
    behavior_ref: Optional[str]
    rule_ref: Optional[str]
    approval_outcomes: Tuple[str, ...]
    # 活动级超时约束（框架 v9 6.3.3 的 timeout 字段，单位小时）。
    # 为 None 表示该活动不设截止时间 —— 不设就不该出现在逾期列表里。
    timeout_hours: Optional[int]
    raw: Dict[str, Any]


@dataclass(frozen=True)
class FlowDefinitionView:
    """一份流程定义的运行时视图。"""

    id: str
    code: str
    name: str
    flow_type: str
    trigger_type: str
    trigger_behavior: Optional[str]
    role_refs: Tuple[str, ...]
    business_object_refs: Tuple[str, ...]
    activities: Dict[str, Activity]
    start_activity: str
    end_activities: Tuple[str, ...]
    raw: Dict[str, Any]

    def activity(self, activity_id: str) -> Activity:
        act = self.activities.get(activity_id)
        if act is None:
            raise FlowDefinitionError(f"流程活动不存在：{activity_id}")
        return act


def _parse_timeout_hours(value):
    """解析流程活动声明的 timeout，成小时数。

    框架 v9 6.3.3 把 timeout 定义为 Duration，本实现统一按**小时**解释：
    YAML 里写 `timeout: 48` 或 `timeout: "48h"` 都表示 48 小时。

    解析失败一律返回 None（该活动不设截止时间）—— 与其让一条写错的
    timeout 把整条流程的定义校验拖挂，不如让它退化成「无超时约束」。
    """
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        hours = int(value)
        return hours if hours > 0 else None
    text_value = str(value).strip().lower()
    if text_value.endswith("h"):
        text_value = text_value[:-1]
    elif text_value.endswith("d"):
        try:
            days = int(text_value[:-1])
        except ValueError:
            return None
        return days * 24 if days > 0 else None
    try:
        hours = int(text_value)
    except ValueError:
        return None
    return hours if hours > 0 else None


def _normalize_activities(raw: Dict[str, Any]) -> Dict[str, Activity]:
    """把 M6 YAML 的 activities[] 归一化成 Activity 字典。"""
    out: Dict[str, Activity] = {}
    for item in raw.get("activities") or []:
        activity_id = item.get("activityId") or item.get("id")
        if not activity_id:
            raise FlowDefinitionError(f"流程活动缺少 activityId：{item}")
        branches = tuple(item.get("branches") or ())
        next_activities = tuple(item.get("nextActivities") or ())
        out[activity_id] = Activity(
            id=activity_id,
            name=item.get("name") or activity_id,
            type=(item.get("activityType") or "").upper(),
            next_activities=next_activities,
            branches=branches,
            role_ref=item.get("roleRef"),
            behavior_ref=item.get("behaviorRef"),
            rule_ref=item.get("ruleRef"),
            approval_outcomes=tuple(item.get("approvalOutcomes") or ()),
            timeout_hours=_parse_timeout_hours(item.get("timeout")),
            raw=item,
        )
    return out


def build_definition_view(raw: Dict[str, Any]) -> FlowDefinitionView:
    """从 M6 YAML 的一条流程构建运行时视图，并做结构校验。"""
    activities = _normalize_activities(raw)
    if not activities:
        raise FlowDefinitionError(f"流程定义没有活动：{raw.get('id')}")

    start_candidates = [a.id for a in activities.values() if a.type == ACT_START]
    if len(start_candidates) != 1:
        raise FlowDefinitionError(
            f"流程 {raw.get('id')} 必须有且仅有一个 START 活动，实得 {start_candidates}")
    start_activity = raw.get("startActivity") or start_candidates[0]
    if start_activity not in activities:
        raise FlowDefinitionError(f"startActivity 不存在：{start_activity}")

    end_activities = tuple(raw.get("endActivities") or ())
    if not end_activities:
        end_activities = tuple(a.id for a in activities.values() if a.type == ACT_END)
    if not end_activities:
        raise FlowDefinitionError(f"流程 {raw.get('id')} 没有 END 活动")
    for eid in end_activities:
        if eid not in activities:
            raise FlowDefinitionError(f"endActivities 指向不存在的活动：{eid}")
        if activities[eid].type != ACT_END:
            raise FlowDefinitionError(f"endActivities 必须指向 END 活动：{eid}")

    # 后继可达性：非 END 活动必须有后继，且后继必须存在
    for act in activities.values():
        if act.type == ACT_END:
            continue
        if act.type == ACT_GATEWAY:
            for branch in act.branches:
                target = branch.get("targetActivity")
                if target not in activities:
                    raise FlowDefinitionError(
                        f"网关 {act.id} 分支指向不存在的活动：{target}")
            continue
        if not act.next_activities:
            raise FlowDefinitionError(f"活动 {act.id} 没有后继")
        for target in act.next_activities:
            if target not in activities:
                raise FlowDefinitionError(
                    f"活动 {act.id} 的后继不存在：{target}")

    return FlowDefinitionView(
        id=raw.get("id") or "",
        code=(raw.get("id") or "").replace("FLOW-", "").replace("-", "_").upper(),
        name=raw.get("name") or "",
        flow_type=raw.get("flowType") or "APPROVAL",
        trigger_type=(raw.get("trigger") or {}).get("triggerType") or "MANUAL",
        trigger_behavior=(raw.get("trigger") or {}).get("behaviorRef"),
        role_refs=tuple(raw.get("roleRefs") or ()),
        business_object_refs=tuple(raw.get("businessObjectRefs") or ()),
        activities=activities,
        start_activity=start_activity,
        end_activities=end_activities,
        raw=raw,
    )


# ══════════════════════════════════════════════════════════
# 引擎
# ══════════════════════════════════════════════════════════

class FlowEngine(FlowEscalationMixin):
    """流程引擎。

 典型用法：

        engine = FlowEngine(db)
        instance_id = engine.start(
            "PAPER_REVIEW_001", "paper", paper.id, f"PAPER-{paper.id}",
            variables={"paper": paper}, creator_id=user.id,
        )
        engine.approve(task_id, comment="同意", operator=user)
    """

    def __init__(self, db: Session, rules: Optional[RuleRegistry] = None):
        self.db = db
        self._rules = rules

    # ------------------------------------------------------------------
    # 规则
    # ------------------------------------------------------------------
    @property
    def rules(self) -> RuleRegistry:
        """惰性加载 M3 规则注册表（进程内缓存）。"""
        if self._rules is None:
            self._rules = load_rule_registry()
        return self._rules

    # ------------------------------------------------------------------
    # 定义
    # ------------------------------------------------------------------
    def load_definition(self, code: str) -> FlowDefinitionView:
        """按 code 取流程定义（DB 优先，回落到 YAML 源）。"""
        row = self.db.scalar(
            select(FlowDefinition).where(FlowDefinition.code == code))
        if row is None:
            row = self.db.scalar(
                select(FlowDefinition).where(FlowDefinition.code == code.upper()))
        if row is None:
            # DB 未同步时直接读 YAML 源，保证「YAML 是唯一语义来源」
            for view in self.load_yaml_definitions().values():
                if view.code == code or view.id == code:
                    return view
            raise NotFoundException(f"流程定义不存在：{code}")
        return build_definition_view(json.loads(row.definition))

    @staticmethod
    def load_yaml_definitions() -> Dict[str, FlowDefinitionView]:
        """读取 M6 YAML，返回 {code: 定义视图}。"""
        path = _find_flow_model_path()
        if path is None:
            return {}
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        out: Dict[str, FlowDefinitionView] = {}
        for raw in (data.get("target_flows") or []):
            view = build_definition_view(raw)
            out[view.code] = view
        return out

    def sync_definitions(self) -> int:
        """把 M6 YAML 的目标流程同步进 DB。返回同步条数。

 幂等：内容未变则不动 version；内容变了 version+1（便于审计「定义改过几次」）。
        """
        count = 0
        for code, view in self.load_yaml_definitions().items():
            payload = json.dumps(view.raw, ensure_ascii=False, sort_keys=True)
            row = self.db.scalar(
                select(FlowDefinition).where(FlowDefinition.code == code))
            if row is None:
                self.db.add(FlowDefinition(
                    code=code,
                    name=view.name,
                    flow_type=view.flow_type,
                    trigger_type=view.trigger_type,
                    trigger_behavior=view.trigger_behavior,
                    definition=payload,
                    version=1,
                    status=1,
                ))
                count += 1
                continue
            current = json.dumps(json.loads(row.definition), ensure_ascii=False,
                                 sort_keys=True)
            if current != payload:
                row.definition = payload
                row.version = (row.version or 1) + 1
                row.name = view.name
                row.flow_type = view.flow_type
                row.trigger_type = view.trigger_type
                row.trigger_behavior = view.trigger_behavior
                row.updated_at = now_local()
                count += 1
        self.db.commit()
        return count

    # ------------------------------------------------------------------
    # 实例生命周期
    # ------------------------------------------------------------------
    def start(self, def_code: str, biz_type: str, biz_id: int,
              biz_key: Optional[str] = None,
              variables: Optional[Dict[str, Any]] = None,
              creator_id: Optional[int] = None) -> int:
        """启动流程实例，返回 instance_id。"""
        view = self.load_definition(def_code)
        instance = FlowInstance(
            def_id=self._definition_row_id(view),
            biz_type=biz_type,
            biz_id=biz_id,
            biz_key=biz_key,
            current_activity_ids=json.dumps([view.start_activity]),
            variables=json.dumps(variables or {}, ensure_ascii=False),
            status=INSTANCE_RUNNING,
            creator_id=creator_id,
            started_at=now_local(),
        )
        self.db.add(instance)
        self.db.flush()

        self._write_history(
            instance.id, activity_id=view.start_activity,
            activity_name=view.activity(view.start_activity).name,
            operator_id=creator_id, action="START",
            to_activity=view.start_activity,
        )
        # 从 START 推进到第一个后继
        start_act = view.activity(view.start_activity)
        self._advance(instance, view, start_act.next_activities, creator_id)
        self.db.commit()
        return instance.id

    def _definition_row_id(self, view: FlowDefinitionView) -> int:
        row = self.db.scalar(
            select(FlowDefinition).where(FlowDefinition.code == view.code))
        if row is None:
            # YAML 有但 DB 未同步：自动落库，保证外键有效
            row = FlowDefinition(
                code=view.code,
                name=view.name,
                flow_type=view.flow_type,
                trigger_type=view.trigger_type,
                trigger_behavior=view.trigger_behavior,
                definition=json.dumps(view.raw, ensure_ascii=False, sort_keys=True),
                version=1,
                status=1,
            )
            self.db.add(row)
            self.db.flush()
        return row.id

    def _advance(self, instance: FlowInstance, view: FlowDefinitionView,
                 next_activities: Iterable[str], operator_id: Optional[int]) -> None:
        """推进到指定活动：逐个消解 SYSTEM/BEHAVIOR 活动，遇人工活动生成待办。"""
        pending = list(next_activities)
        guard = 0
        while pending:
            guard += 1
            if guard > 50:
                raise FlowDefinitionError(
                    f"流程 {view.code} 活动推进超过 50 步，疑似死循环")
            activity_id = pending.pop(0)
            act = view.activity(activity_id)

            if act.type == ACT_END:
                self._finish_instance(instance, view, act, operator_id)
                return

            if act.type in HUMAN_ACTIVITY_TYPES:
                self._create_task(instance, act)
                instance.current_activity_ids = json.dumps([activity_id])
                return

            # SYSTEM_TASK / BEHAVIOR_CALL：记录留痕后继续推进
            self._write_history(
                instance.id, activity_id=act.id, activity_name=act.name,
                operator_id=operator_id, action="EXECUTE", to_activity=act.id,
            )
            if act.type == ACT_GATEWAY:
                target = self._evaluate_gateway(instance, view, act)
                if target:
                    pending.insert(0, target)
                continue
            pending = list(act.next_activities) + pending

    def _create_task(self, instance: FlowInstance, act: Activity) -> FlowTask:
        """在人工活动上生成待办任务。"""
        task = FlowTask(
            instance_id=instance.id,
            activity_id=act.id,
            activity_type=act.type,
            activity_name=act.name,
            # role_code 存运行时 code（grade_admin），不是本体 id（ROLE-GRADE-ADMIN），
            # 待办查询要拿 sys_role.code 过滤。
            role_code=role_code_of(act.role_ref),
            status=TASK_TODO,
            created_at=now_local(),
            # deadline 由活动声明的 timeout 推导（框架 v9 6.3.3）。
            # 此前这里从不赋值，于是「逾期待办」列表恒为空 —— 超时功能
            # 是个只能看不能用的空壳。现在活动没声明 timeout 就是 None，
            # 也就是「这条待办不参与超时统计」。
            deadline=now_local() + timedelta(hours=act.timeout_hours)
            if act.timeout_hours else None,
        )
        self.db.add(task)
        self.db.flush()
        return task

    def _evaluate_gateway(self, instance: FlowInstance, view: FlowDefinitionView,
                          gateway: Activity) -> Optional[str]:
        """求值网关分支，返回目标活动 id。

 条件求值顺序：先试 `isDefault` 之外的分支（按声明顺序），
        都不命中则走默认分支。分支条件用规则引擎求值，
        规则/表达式不可用时**不静默兜底**——抛错让流程停在网关，
        避免「条件写错 → 走错分支 → 静默改数据」。
        """
        variables = self._instance_variables(instance)
        default_target: Optional[str] = None
        for branch in gateway.branches:
            target = branch.get("targetActivity")
            if branch.get("isDefault"):
                default_target = target
                continue
            if self._branch_matches(branch, variables):
                return target
        if default_target:
            return default_target
        raise FlowDefinitionError(
            f"网关 {gateway.id} 没有分支命中且无默认分支，流程已停在网关")

    def _branch_matches(self, branch: Dict[str, Any],
                        variables: Dict[str, Any]) -> bool:
        """判断网关分支条件是否成立。"""
        rule_ref = branch.get("ruleRef")
        if rule_ref:
            rule = self.rules.get(rule_ref)
            if rule is None:
                raise FlowDefinitionError(f"网关引用的规则不存在：{rule_ref}")
            try:
                rule.check(variables)
                return True
            except RuleViolation:
                return False

        expression = branch.get("conditionExpression")
        if not expression:
            return False
        # 条件表达式里的 `approval.outcome` 属于流程自身状态，
        # 由调用方注入到 variables['approval']，这里直接求值。
        from app.services.rule_engine import evaluate_expression
        try:
            result = evaluate_expression(
                expression, variables, declared=_declared_fields(variables))
        except Exception as exc:
            raise FlowDefinitionError(
                f"网关条件求值失败（{expression}）：{exc}") from exc
        return bool(result)

    def _instance_variables(self, instance: FlowInstance) -> Dict[str, Any]:
        """实例的流程变量。"""
        try:
            return json.loads(instance.variables or "{}")
        except (TypeError, ValueError):
            return {}

    def _finish_instance(self, instance: FlowInstance, view: FlowDefinitionView,
                         end_act: Activity, operator_id: Optional[int]) -> None:
        """流程到达 END：按 END 上的 outcome 决定实例终态。"""
        outcome = (end_act.raw.get("outcome") or "").upper()
        variables = self._instance_variables(instance)
        approval = variables.get("approval") or {}
        approval_outcome = (approval.get("outcome") or "").upper()

        # 审批结果优先：它才是本次流转的真实结论。
        #
        # 注意这里必须用**精确比对**，不能用子串包含：
        # END 上的 outcome 形如 "APPROVED_OR_REJECTED"（两条路径共用一个 END），
        # `"REJECTED" in "APPROVED_OR_REJECTED"` 为 True，
        # 会把「审批通过」误判成「审批驳回」——实例状态与实际审批结论相反。
        if approval_outcome == "REJECT":
            status = INSTANCE_REJECTED
        elif approval_outcome == "RETURN":
            status = INSTANCE_RETURNED
        elif approval_outcome == "APPROVE":
            status = INSTANCE_APPROVED
        elif outcome == "REJECTED":
            status = INSTANCE_REJECTED
        elif outcome == "RETURNED":
            status = INSTANCE_RETURNED
        elif outcome == "CANCELLED":
            status = INSTANCE_CANCELLED
        else:
            status = INSTANCE_APPROVED

        instance.status = status
        instance.current_activity_ids = json.dumps([end_act.id])
        instance.ended_at = now_local()
        self._write_history(
            instance.id, activity_id=end_act.id, activity_name=end_act.name,
            operator_id=operator_id, action="EXECUTE", to_activity=end_act.id,
        )

    def _write_history(self, instance_id: int, *, activity_id: Optional[str],
                       activity_name: Optional[str], operator_id: Optional[int],
                       action: str, comment: Optional[str] = None,
                       from_activity: Optional[str] = None,
                       to_activity: Optional[str] = None) -> None:
        operator_name = None
        if operator_id is not None:
            from app.models.system import User
            user = self.db.get(User, operator_id)
            operator_name = (user.real_name or user.username) if user else None
        self.db.add(FlowHistory(
            instance_id=instance_id,
            activity_id=activity_id,
            activity_name=activity_name,
            operator_id=operator_id,
            operator_name=operator_name,
            action=action,
            comment=comment,
            from_activity=from_activity,
            to_activity=to_activity,
            created_at=now_local(),
        ))

    # ------------------------------------------------------------------
    # 审批动作
    # ------------------------------------------------------------------
    def approve(self, task_id: int, comment: Optional[str] = None,
                operator: Any = None) -> FlowInstance:
        """审批通过。"""
        return self._complete_task(task_id, "APPROVE", comment, operator)

    def reject(self, task_id: int, comment: Optional[str] = None,
               operator: Any = None) -> FlowInstance:
        """审批驳回。"""
        return self._complete_task(task_id, "REJECT", comment, operator)

    def return_to(self, task_id: int, target_activity_id: str,
                  comment: Optional[str] = None, operator: Any = None) -> FlowInstance:
        """退回到指定活动（重新提交）。"""
        return self._complete_task(
            task_id, "RETURN", comment, operator, target_activity_id=target_activity_id)

    def cancel(self, task_id: int, comment: Optional[str] = None,
               operator: Any = None) -> FlowInstance:
        """取消流程。"""
        return self._complete_task(task_id, "CANCEL", comment, operator)

    def claim(self, task_id: int, operator: Any = None) -> FlowTask:
        """认领待办（把任务从 TODO 变为 CLAIMED 并绑定处理人）。"""
        task = self._load_task(task_id)
        self._assert_operable(task)
        self._assert_role_holder(task, operator)
        operator_id = self._operator_id(operator)
        task.status = TASK_CLAIMED
        task.assignee_id = operator_id
        task.claimed_at = now_local()
        self.db.commit()
        return task

    def _complete_task(self, task_id: int, action: str, comment: Optional[str],
                       operator: Any, target_activity_id: Optional[str] = None
                       ) -> FlowInstance:
        """完成任务并推进流程。"""
        task = self._load_task(task_id)
        self._assert_operable(task)

        instance = self.db.get(FlowInstance, task.instance_id)
        if instance is None:
            raise NotFoundException("流程实例不存在")
        if instance.status in TERMINAL_INSTANCE_STATUS:
            raise BusinessException(f"流程已结束（{instance.status}），不能再处理")

        view = self._instance_view(instance)
        act = view.activity(task.activity_id)

        # 审批活动必须覆盖该动作
        if act.type == ACT_APPROVAL_TASK and act.approval_outcomes:
            # CANCEL 是**引擎级**动作（撤回/作废），不属于业务审批结果，
            # 因此不要求流程定义把它列进 approvalOutcomes。
            if action != "CANCEL" and action not in act.approval_outcomes:
                raise BusinessException(
                    f"活动 {act.id} 不支持 {action} 操作，"
                    f"仅允许 {'/'.join(act.approval_outcomes)}")

        operator_id = self._operator_id(operator)

        # 乐观锁：条件更新保证并发下只有一个执行者成功
        closed = self.db.execute(
            update(FlowTask)
            .where(FlowTask.id == task.id,
                   FlowTask.status.in_([TASK_TODO, TASK_CLAIMED]))
            .values(status=TASK_DONE, action=action, comment=comment,
                    done_at=now_local(), assignee_id=operator_id)
        ).rowcount
        if not closed:
            self.db.rollback()
            raise BusinessException("该待办已被处理，请刷新后重试")

        # 把审批结果注入流程变量，供网关条件求值
        variables = self._instance_variables(instance)
        variables["approval"] = {
            "outcome": action,
            "comment": comment or "",
            "operator_id": operator_id,
            "activity_id": act.id,
        }
        instance.variables = json.dumps(variables, ensure_ascii=False, default=str)

        self._write_history(
            instance.id, activity_id=act.id, activity_name=act.name,
            operator_id=operator_id, action=action, comment=comment,
            from_activity=act.id,
        )

        if action == "CANCEL":
            # 当前任务本身就是被取消的那一个 → 标记为 CANCEL 而不是 DONE。
            # （乐观锁那一步已经把它置成 DONE，这里改回来。）
            task_row = self.db.get(FlowTask, task.id)
            if task_row is not None:
                task_row.status = TASK_CANCEL
                task_row.action = "CANCEL"
                task_row.done_at = now_local()
            instance.status = INSTANCE_CANCELLED
            instance.ended_at = now_local()
            instance.current_activity_ids = json.dumps([act.id])
            self._cancel_open_tasks(instance.id)
            self.db.commit()
            return instance

        if action == "RETURN":
            if not target_activity_id:
                raise BusinessException("退回必须指定目标活动")
            if target_activity_id not in view.activities:
                raise BusinessException(f"退回目标活动不存在：{target_activity_id}")
            # 退回：实例回到目标活动重新开始
            instance.status = INSTANCE_RUNNING
            instance.current_activity_ids = json.dumps([target_activity_id])
            instance.ended_at = None
            target_act = view.activity(target_activity_id)
            self._advance(instance, view, target_act.next_activities or [target_activity_id],
                          operator_id)
            self.db.commit()
            return instance

        # APPROVE / REJECT：沿活动声明的后继推进
        self._advance(instance, view, act.next_activities, operator_id)
        self.db.commit()
        return instance

    def _load_task(self, task_id: int) -> FlowTask:
        task = self.db.get(FlowTask, task_id)
        if task is None:
            raise NotFoundException("待办任务不存在")
        return task

    def _assert_operable(self, task: FlowTask) -> None:
        if task.status in (TASK_DONE, TASK_CANCEL):
            raise BusinessException(f"待办任务已{('完成' if task.status == TASK_DONE else '取消')}")

    def _assert_role_holder(self, task: FlowTask, operator: Any) -> None:
        """校验操作人持有该待办对应的角色。

        待办是**角色职责**（审批是岗位职责，不是个人数据），所以能操作它
        的人必须是该角色的持有者。少了这道校验，任何登录用户都能认领、
        转走、催办别人的待办 —— 越权且会让待办的处理人分配完全失序。

        系统管理员是例外：运维角色需要能兜底处理积压待办。
        """
        if operator is None:
            return
        codes = set(self._user_role_codes(operator))
        if "sys_admin" in codes:
            return
        if task.role_code not in codes:
            raise PermissionException(
                f"需要「{task.role_code}」角色才能处理该待办")

    def _user_name(self, user_id: Optional[int]) -> str:
        """取用户显示名。查不到返回空串，不抛异常 —— 列表里一个人名
        缺失不该让整个接口 500。"""
        if not user_id:
            return ""
        from app.models import User

        try:
            user = self.db.get(User, user_id)
        except Exception:  # noqa: BLE001
            return ""
        if user is None:
            return ""
        return user.real_name or user.username or ""

    @staticmethod
    def _operator_id(operator: Any) -> Optional[int]:
        if operator is None:
            return None
        if isinstance(operator, int):
            return operator
        return getattr(operator, "id", None)

    def _instance_view(self, instance: FlowInstance) -> FlowDefinitionView:
        """取实例对应的流程定义视图。"""
        row = self.db.get(FlowDefinition, instance.def_id)
        if row is None:
            raise NotFoundException("流程定义不存在")
        return build_definition_view(json.loads(row.definition))

    def _cancel_open_tasks(self, instance_id: int) -> None:
        """取消实例下所有未完成的待办。"""
        for task in self.db.scalars(
            select(FlowTask).where(
                FlowTask.instance_id == instance_id,
                FlowTask.status.in_([TASK_TODO, TASK_CLAIMED]),
            )
        ).all():
            task.status = TASK_CANCEL
            task.action = "CANCEL"
            task.done_at = now_local()

    # ------------------------------------------------------------------
    # 查询
    # ------------------------------------------------------------------
    def todo_list(self, user: Any, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """我的待办：按当前用户角色过滤 role_code。"""
        role_codes = self._user_role_codes(user)
        if not role_codes:
            return {"items": [], "total": 0, "page": page, "page_size": page_size}
        query = (
            select(FlowTask)
            .where(FlowTask.status.in_([TASK_TODO, TASK_CLAIMED]),
                   FlowTask.role_code.in_(role_codes))
            .order_by(FlowTask.created_at.desc())
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

    def done_list(self, user: Any, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """我的已办：处理人是我且已完成的任务。"""
        operator_id = self._operator_id(user)
        if operator_id is None:
            return {"items": [], "total": 0, "page": page, "page_size": page_size}
        query = (
            select(FlowTask)
            .where(FlowTask.assignee_id == operator_id, FlowTask.status == TASK_DONE)
            .order_by(FlowTask.done_at.desc())
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

    def my_instances(self, user: Any, page: int = 1,
                     page_size: int = 20) -> Dict[str, Any]:
        """我发起的流程实例。"""
        operator_id = self._operator_id(user)
        if operator_id is None:
            return {"items": [], "total": 0, "page": page, "page_size": page_size}
        query = (
            select(FlowInstance)
            .where(FlowInstance.creator_id == operator_id)
            .order_by(FlowInstance.started_at.desc())
        )
        total = len(self.db.scalars(query).all())
        rows = self.db.scalars(query.offset((page - 1) * page_size)
                               .limit(page_size)).all()
        return {
            "items": [self.instance_out(row) for row in rows],
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    def instance_detail(self, instance_id: int) -> Dict[str, Any]:
        """实例详情：含当前活动、待办与全部留痕。"""
        instance = self.db.get(FlowInstance, instance_id)
        if instance is None:
            raise NotFoundException("流程实例不存在")
        tasks = self.db.scalars(
            select(FlowTask).where(FlowTask.instance_id == instance_id)
            .order_by(FlowTask.created_at.asc())
        ).all()
        histories = self.db.scalars(
            select(FlowHistory).where(FlowHistory.instance_id == instance_id)
            .order_by(FlowHistory.created_at.asc(), FlowHistory.id.asc())
        ).all()
        out = self.instance_out(instance)
        out["tasks"] = [self.task_out(t) for t in tasks]
        out["history"] = [
            {
                "id": h.id,
                "activity_id": h.activity_id,
                "activity_name": h.activity_name,
                "operator_id": h.operator_id,
                "operator_name": h.operator_name,
                "action": h.action,
                "comment": h.comment,
                "from_activity": h.from_activity,
                "to_activity": h.to_activity,
                "created_at": h.created_at.strftime("%Y-%m-%d %H:%M:%S")
                if h.created_at else None,
            }
            for h in histories
        ]
        return out

    def find_instance(self, biz_type: str, biz_id: int) -> Optional[FlowInstance]:
        """按业务对象查运行中的实例（防重复发起）。"""
        return self.db.scalar(
            select(FlowInstance)
            .where(FlowInstance.biz_type == biz_type,
                   FlowInstance.biz_id == biz_id,
                   FlowInstance.status == INSTANCE_RUNNING)
            .order_by(FlowInstance.id.desc())
        )

    def pending_tasks(self, instance_id: int) -> List[Dict[str, Any]]:
        """实例下尚未处理的待办（TODO / CLAIMED）。"""
        rows = self.db.scalars(
            select(FlowTask)
            .where(FlowTask.instance_id == instance_id,
                   FlowTask.status.in_([TASK_TODO, TASK_CLAIMED]))
            .order_by(FlowTask.created_at.asc())
        ).all()
        return [self.task_out(row) for row in rows]

    @staticmethod
    def _user_role_codes(user: Any) -> List[str]:
        """取用户的角色 code 列表（与 M5 的 code 对齐）。"""
        codes = getattr(user, "role_codes", None)
        if codes:
            return list(codes)
        roles = getattr(user, "roles", None) or []
        out = []
        for role in roles:
            code = getattr(role, "code", None)
            if code:
                out.append(code)
        return out

    def task_out(self, task: FlowTask) -> Dict[str, Any]:
        # 流程编码：前端要按流程类型决定「退回」的目标节点。
        # 没有它，前端只能把所有历史节点都列出来让用户瞎选。
        flow_code = ""
        try:
            instance = self.db.get(FlowInstance, task.instance_id)
            if instance is not None:
                definition = self.db.get(FlowDefinition, instance.def_id)
                if definition is not None:
                    flow_code = definition.code or ""
        except Exception:  # noqa: BLE001 定义缺失不应让整个列表接口失败
            flow_code = ""
        return {
            "id": task.id,
            "instance_id": task.instance_id,
            "activity_id": task.activity_id,
            "activity_type": task.activity_type,
            "activity_name": task.activity_name,
            "role_code": task.role_code,
            "assignee_id": task.assignee_id,
            "flow_code": flow_code,
            "status": task.status,
            "action": task.action,
            "comment": task.comment,
            "created_at": task.created_at.strftime("%Y-%m-%d %H:%M:%S")
            if task.created_at else None,
            "claimed_at": task.claimed_at.strftime("%Y-%m-%d %H:%M:%S")
            if task.claimed_at else None,
            "done_at": task.done_at.strftime("%Y-%m-%d %H:%M:%S")
            if task.done_at else None,
            "deadline": task.deadline.strftime("%Y-%m-%d %H:%M:%S")
            if task.deadline else None,
            # 逾期是**计算属性**而非存储状态：同一个 deadline 随时间推移
            # 就会变成逾期，存一个布尔值就要靠定时任务刷新，不刷新就永远是错的。
            "is_overdue": bool(
                task.deadline is not None
                and task.deadline < now_local()
                and task.status in (TASK_TODO, TASK_CLAIMED)),
            "urge_count": task.urge_count or 0,
            "last_urged_at": task.last_urged_at.strftime("%Y-%m-%d %H:%M:%S")
            if task.last_urged_at else None,
            "transfer_count": task.transfer_count or 0,
            "last_transferred_at": task.last_transferred_at.strftime("%Y-%m-%d %H:%M:%S")
            if task.last_transferred_at else None,
            "assignee_name": self._user_name(task.assignee_id),
        }

    def instance_out(self, instance: FlowInstance) -> Dict[str, Any]:
        try:
            current = json.loads(instance.current_activity_ids or "[]")
        except (TypeError, ValueError):
            current = []
        # 流程名称：前端要显示「试卷公共库审核」而不是 `PAPER_REVIEW_001`。
        # def_id → FlowDefinition 是 1:1，查询失败不能影响实例输出。
        flow_name = ""
        flow_code = ""
        try:
            definition = self.db.get(FlowDefinition, instance.def_id)
            if definition is not None:
                flow_name = definition.name or ""
                flow_code = definition.code or ""
        except Exception:  # noqa: BLE001 定义缺失不应让整个列表接口失败
            flow_name = ""
        return {
            "id": instance.id,
            "def_id": instance.def_id,
            "flow_code": flow_code,
            "flow_name": flow_name,
            "biz_type": instance.biz_type,
            "biz_id": instance.biz_id,
            "biz_key": instance.biz_key,
            "biz_label": BIZ_LABELS.get(instance.biz_type, instance.biz_type),
            "current_activity_ids": current,
            "status": instance.status,
            "creator_id": instance.creator_id,
            "started_at": instance.started_at.strftime("%Y-%m-%d %H:%M:%S")
            if instance.started_at else None,
            "ended_at": instance.ended_at.strftime("%Y-%m-%d %H:%M:%S")
            if instance.ended_at else None,
        }


# ══════════════════════════════════════════════════════════
# 规则注册表加载
# ══════════════════════════════════════════════════════════

_RULE_MODEL_CANDIDATES = (
    pathlib.Path(__file__).resolve().parents[3]
    / "audit-reports" / "ontology-inventory" / "m3-rule-model.yaml",
    _APP_ONTOLOGY_DIR / "m3-rule-model.yaml",
)

_rule_registry_cache: Optional[RuleRegistry] = None


def load_rule_registry() -> RuleRegistry:
    """加载 M3 规则注册表（进程内缓存）。

 规则定义不在代码里，而在本体 M3 YAML —— 这是「规则外置」的核心：
    改规则不改代码；DB 与 YAML 的规则 id 由 check_references.py 保证一致。
    """
    global _rule_registry_cache
    if _rule_registry_cache is not None:
        return _rule_registry_cache

    path = None
    for candidate in _RULE_MODEL_CANDIDATES:
        if candidate.exists():
            path = candidate
            break
    if path is None:
        _rule_registry_cache = RuleRegistry()
        return _rule_registry_cache

    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    rules = []
    for raw in data.get("rules") or []:
        from app.services.rule_engine import Rule
        rules.append(Rule(
            id=raw["id"],
            name=raw.get("name") or raw["id"],
            expression=raw.get("expression") or "",
            violation_message=raw.get("violationMessage") or "规则校验未通过",
            enforced_at=raw.get("enforcedAt") or "ALWAYS",
            category=raw.get("category") or "FIELD",
            description=raw.get("description") or "",
            params=tuple(raw.get("params") or ()),
            reads=tuple(raw.get("reads") or ()),
        ))
    _rule_registry_cache = RuleRegistry(rules)
    return _rule_registry_cache


def _declared_fields(variables: Dict[str, Any]) -> List[str]:
    """从流程变量里推导网关条件可见的字段名。

 条件表达式里的 `approval.outcome` 需要能看到 `outcome`。
 变量里已有的 dict 走 dict 自身的键，其余对象走其公开标量属性。
    """
    declared: set = set()
    for value in variables.values():
        if isinstance(value, dict):
            declared.update(k for k in value.keys() if isinstance(k, str))
    return sorted(declared)
