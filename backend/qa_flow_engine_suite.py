"""流程引擎（M6）单元与集成套件。

用**内存 SQLite** 真实建表、真实走事务，验证：
  - M6 YAML 定义加载与结构校验；
  - 定义同步到 DB 的幂等性；
  - 流程启动 → 生成待办 → 审批通过 → 实例结束 的完整链路；
  - 驳回 / 退回 / 取消三条分支；
  - 网关条件求值（含规则引用与表达式两种形态）；
  - 并发处理同一待办时的乐观锁；
  - 待办按角色可见、已办按处理人可见；
  - 规则引擎的字段可见性 fail-closed（敏感字段不可读）。

运行：cd backend && python -m pytest qa_flow_engine_suite.py -q
"""
import json
import pathlib

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.exception import BusinessException, NotFoundException
from app.models import FlowDefinition, FlowHistory, FlowInstance, FlowTask
from app.services.flow_engine import (
    FlowDefinitionError,
    FlowEngine,
    build_definition_view,
    load_rule_registry,
)
from app.services.rule_engine import (
    RuleExpressionError,
    RuleViolation,
    evaluate_expression,
)


# ══════════════════════════════════════════════════════════
# 夹具
# ══════════════════════════════════════════════════════════

@pytest.fixture()
def db_session():
    import app.models  # noqa: F401 确保所有表注册到 Base.metadata

    from app.core.database import Base

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, expire_on_commit=False)()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def engine(db_session):
    return FlowEngine(db_session)


class _Actor:
    """轻量用户替身：只需 id 与 role_codes。"""

    def __init__(self, actor_id, role_codes):
        self.id = actor_id
        self.role_codes = role_codes
        self.real_name = f"用户{actor_id}"
        self.username = f"user{actor_id}"


@pytest.fixture()
def teacher():
    return _Actor(101, ["teacher"])


@pytest.fixture()
def grade_admin():
    return _Actor(102, ["grade_admin"])


@pytest.fixture()
def sys_admin():
    return _Actor(103, ["sys_admin"])


def _paper_payload(status="draft", share_scope="private"):
    return {"paper": {"status": status, "share_scope": share_scope}}


def _seed_definition(session, code, raw):
    session.add(FlowDefinition(
        code=code, name=raw.get("name", "t"), flow_type="APPROVAL",
        trigger_type="MANUAL", definition=json.dumps(raw), version=1, status=1))
    session.commit()


# ══════════════════════════════════════════════════════════
# 定义加载与结构校验
# ══════════════════════════════════════════════════════════

def test_yaml_target_flows_load():
    """M6 YAML 的 4 条目标流程必须全部能构建定义视图。"""
    defs = FlowEngine.load_yaml_definitions()
    assert len(defs) == 4
    assert "PAPER_REVIEW_001" in defs


def test_definition_view_has_start_and_end():
    view = FlowEngine.load_yaml_definitions()["PAPER_REVIEW_001"]
    assert view.activities[view.start_activity].type == "START"
    for eid in view.end_activities:
        assert view.activities[eid].type == "END"


def test_definition_requires_single_start():
    """两个 START 活动必须被拒。"""
    raw = {
        "id": "X", "name": "x",
        "activities": [
            {"activityId": "A", "activityType": "START", "nextActivities": ["B"]},
            {"activityId": "B", "activityType": "START", "nextActivities": ["C"]},
            {"activityId": "C", "activityType": "END"},
        ],
    }
    with pytest.raises(FlowDefinitionError, match="START"):
        build_definition_view(raw)


def test_definition_requires_at_least_one_start():
    """没有 START 活动必须被拒。"""
    raw = {
        "id": "X", "name": "x",
        "activities": [
            {"activityId": "A", "activityType": "SYSTEM_TASK", "nextActivities": ["B"]},
            {"activityId": "B", "activityType": "END"},
        ],
    }
    with pytest.raises(FlowDefinitionError, match="START"):
        build_definition_view(raw)


def test_definition_rejects_dangling_next():
    """后继活动不存在必须被拒。"""
    raw = {
        "id": "X", "name": "x",
        "activities": [
            {"activityId": "A", "activityType": "START", "nextActivities": ["ZZZ"]},
            {"activityId": "B", "activityType": "END"},
        ],
    }
    with pytest.raises(FlowDefinitionError, match="后继不存在"):
        build_definition_view(raw)


def test_definition_rejects_end_not_end_type():
    """endActivities 指向非 END 活动必须被拒。"""
    raw = {
        "id": "X", "name": "x",
        "endActivities": ["B"],
        "activities": [
            {"activityId": "A", "activityType": "START", "nextActivities": ["B"]},
            {"activityId": "B", "activityType": "USER_TASK", "roleRef": "R",
             "nextActivities": []},
        ],
    }
    with pytest.raises(FlowDefinitionError, match="END"):
        build_definition_view(raw)


def test_definition_rejects_activity_without_next():
    """非 END 活动没有后继必须被拒。"""
    raw = {
        "id": "X", "name": "x",
        "activities": [
            {"activityId": "A", "activityType": "START", "nextActivities": ["B"]},
            {"activityId": "B", "activityType": "SYSTEM_TASK"},
            {"activityId": "C", "activityType": "END"},
        ],
    }
    with pytest.raises(FlowDefinitionError, match="没有后继"):
        build_definition_view(raw)


# ══════════════════════════════════════════════════════════
# 定义同步
# ══════════════════════════════════════════════════════════

def test_sync_definitions_is_idempotent(db_session, engine):
    """同步两次，第二次不应产生变更。"""
    assert engine.sync_definitions() == 4
    assert engine.sync_definitions() == 0
    rows = db_session.scalars(select(FlowDefinition)).all()
    assert len(rows) == 4
    assert all(r.version == 1 for r in rows)


def test_sync_definitions_persists_yaml_verbatim(db_session, engine):
    """DB 里存的是 M6 YAML 原文（不是拍平的图）。"""
    engine.sync_definitions()
    row = db_session.scalar(
        select(FlowDefinition).where(FlowDefinition.code == "PAPER_REVIEW_001"))
    payload = json.loads(row.definition)
    assert payload["id"] == "FLOW-PAPER-REVIEW-001"
    assert any(a.get("activityId") == "PR03" for a in payload["activities"])


# ══════════════════════════════════════════════════════════
# 完整链路：启动 → 待办 → 审批 → 结束
# ══════════════════════════════════════════════════════════

def test_start_creates_task_at_approval_activity(db_session, engine, teacher):
    """启动流程后应停在审批活动并生成待办。"""
    instance_id = engine.start(
        "PAPER_REVIEW_001", "paper", 42, "PAPER-42",
        variables=_paper_payload(), creator_id=teacher.id)
    instance = db_session.get(FlowInstance, instance_id)
    assert instance.status == "RUNNING"

    tasks = db_session.scalars(
        select(FlowTask).where(FlowTask.instance_id == instance_id)).all()
    assert len(tasks) == 1
    task = tasks[0]
    assert task.activity_id == "PR03"
    assert task.activity_type == "APPROVAL_TASK"
    # role_code 存运行时 code（不是本体 id ROLE-GRADE-ADMIN）
    assert task.role_code == "grade_admin"
    assert task.status == "TODO"


def test_role_id_translated_to_code():
    """本体角色 id 必须翻译成数据库 role code。"""
    from app.services.flow_engine import role_code_of

    assert role_code_of("ROLE-GRADE-ADMIN") == "grade_admin"
    assert role_code_of("ROLE-SYS-ADMIN") == "sys_admin"
    assert role_code_of("ROLE-TEACHER") == "teacher"
    assert role_code_of("ROLE-STUDENT") == "student"
    assert role_code_of("ROLE-GUEST") == "guest"
    # 已经是 code 的原样返回
    assert role_code_of("teacher") == "teacher"
    assert role_code_of(None) == ""


def test_role_mapping_covers_all_m5_roles():
    """映射表必须覆盖 M5 的全部 5 个角色，否则流程定义里的 roleRef 会漏译。"""
    import yaml
    from app.services.flow_engine import ROLE_ID_TO_CODE

    m5_path = (pathlib.Path(__file__).resolve().parents[1]
               / "audit-reports/ontology-inventory/m5-actor-model.yaml")
    if not m5_path.exists():
        pytest.skip("本体 M5 模型不在工作区（容器内不存在）")
    m5 = yaml.safe_load(m5_path.read_text(encoding="utf-8"))
    m5_ids = {r["id"] for r in m5["roles"]}
    assert m5_ids <= set(ROLE_ID_TO_CODE)


def test_approve_completes_flow(db_session, engine, teacher, grade_admin):
    """审批通过后实例应结束为 APPROVED。"""
    instance_id = engine.start(
        "PAPER_REVIEW_001", "paper", 42, "PAPER-42",
        variables=_paper_payload(), creator_id=teacher.id)
    task = db_session.scalar(
        select(FlowTask).where(FlowTask.instance_id == instance_id))

    engine.approve(task.id, comment="同意入库", operator=grade_admin)

    instance = db_session.get(FlowInstance, instance_id)
    assert instance.status == "APPROVED"
    assert instance.ended_at is not None

    task_row = db_session.get(FlowTask, task.id)
    assert task_row.status == "DONE"
    assert task_row.action == "APPROVE"
    assert task_row.comment == "同意入库"


def test_reject_ends_flow_with_rejected(db_session, engine, teacher, grade_admin):
    """驳回后实例应结束为 REJECTED。"""
    instance_id = engine.start(
        "PAPER_REVIEW_001", "paper", 43, "PAPER-43",
        variables=_paper_payload(), creator_id=teacher.id)
    task = db_session.scalar(
        select(FlowTask).where(FlowTask.instance_id == instance_id))

    engine.reject(task.id, comment="题目有问题", operator=grade_admin)

    instance = db_session.get(FlowInstance, instance_id)
    assert instance.status == "REJECTED"


def test_return_creates_new_task_at_target(db_session, engine, teacher, grade_admin):
    """退回应回到目标活动并重新生成待办。"""
    instance_id = engine.start(
        "PAPER_REVIEW_001", "paper", 44, "PAPER-44",
        variables=_paper_payload(), creator_id=teacher.id)
    task = db_session.scalar(
        select(FlowTask).where(FlowTask.instance_id == instance_id))

    engine.return_to(task.id, "PR02", comment="补充题目", operator=grade_admin)

    instance = db_session.get(FlowInstance, instance_id)
    assert instance.status == "RUNNING"
    assert instance.ended_at is None

    tasks = db_session.scalars(
        select(FlowTask).where(FlowTask.instance_id == instance_id)).all()
    # 原任务 DONE，新任务在 PR03（PR02 是 BEHAVIOR_CALL，直接推进到 PR03）
    assert len(tasks) == 2
    assert sorted(t.status for t in tasks) == ["DONE", "TODO"]


def test_cancel_ends_flow_and_cancels_tasks(db_session, engine, teacher, grade_admin):
    """取消后实例 CANCELLED，未完成待办一并取消。"""
    instance_id = engine.start(
        "PAPER_REVIEW_001", "paper", 45, "PAPER-45",
        variables=_paper_payload(), creator_id=teacher.id)
    task = db_session.scalar(
        select(FlowTask).where(FlowTask.instance_id == instance_id))

    engine.cancel(task.id, comment="不需要了", operator=grade_admin)

    instance = db_session.get(FlowInstance, instance_id)
    assert instance.status == "CANCELLED"
    task_row = db_session.get(FlowTask, task.id)
    assert task_row.status == "CANCEL"


def test_history_records_each_step(db_session, engine, teacher, grade_admin):
    """留痕应记录 START 与审批动作。"""
    instance_id = engine.start(
        "PAPER_REVIEW_001", "paper", 46, "PAPER-46",
        variables=_paper_payload(), creator_id=teacher.id)
    task = db_session.scalar(
        select(FlowTask).where(FlowTask.instance_id == instance_id))
    engine.approve(task.id, comment="ok", operator=grade_admin)

    rows = db_session.scalars(
        select(FlowHistory).where(FlowHistory.instance_id == instance_id)
        .order_by(FlowHistory.id)).all()
    actions = [r.action for r in rows]
    assert "START" in actions
    assert "APPROVE" in actions


# ══════════════════════════════════════════════════════════
# 网关求值
# ══════════════════════════════════════════════════════════

def test_gateway_selects_approve_branch(db_session, engine, teacher, grade_admin):
    """approval.outcome == 'APPROVE' 时走 PR05 分支。"""
    instance_id = engine.start(
        "PAPER_REVIEW_001", "paper", 47, "PAPER-47",
        variables=_paper_payload(), creator_id=teacher.id)
    task = db_session.scalar(
        select(FlowTask).where(FlowTask.instance_id == instance_id))
    engine.approve(task.id, comment="ok", operator=grade_admin)
    instance = db_session.get(FlowInstance, instance_id)
    assert instance.status == "APPROVED"


def test_gateway_reject_branch_ends_rejected(db_session, engine, teacher, grade_admin):
    """approval.outcome == 'REJECT' 时走 PR06 分支并以 REJECTED 结束。"""
    instance_id = engine.start(
        "PAPER_REVIEW_001", "paper", 48, "PAPER-48",
        variables=_paper_payload(), creator_id=teacher.id)
    task = db_session.scalar(
        select(FlowTask).where(FlowTask.instance_id == instance_id))
    engine.reject(task.id, comment="不行", operator=grade_admin)
    instance = db_session.get(FlowInstance, instance_id)
    assert instance.status == "REJECTED"


def test_gateway_without_match_and_no_default_raises(db_session):
    """网关无分支命中且无默认分支时必须抛错，不能静默走错分支。"""
    raw = {
        "id": "X", "name": "x", "endActivities": ["C"],
        "activities": [
            {"activityId": "A", "activityType": "START", "nextActivities": ["B"]},
            {"activityId": "B", "activityType": "GATEWAY", "branches": [
                {"branchName": "永假", "conditionExpression": "1 == 2",
                 "targetActivity": "C"},
            ]},
            {"activityId": "C", "activityType": "END"},
        ],
    }
    _seed_definition(db_session, "TEST_GW", raw)
    eng = FlowEngine(db_session)
    with pytest.raises(FlowDefinitionError, match="没有分支命中"):
        eng.start("TEST_GW", "paper", 1, "K1", variables={})


def test_gateway_uses_default_branch_when_no_match(db_session):
    """无分支命中但有默认分支时走默认分支。"""
    raw = {
        "id": "X", "name": "x", "endActivities": ["C"],
        "activities": [
            {"activityId": "A", "activityType": "START", "nextActivities": ["B"]},
            {"activityId": "B", "activityType": "GATEWAY", "branches": [
                {"branchName": "永假", "conditionExpression": "1 == 2",
                 "targetActivity": "C"},
                {"branchName": "兜底", "targetActivity": "C", "isDefault": True},
            ]},
            {"activityId": "C", "activityType": "END"},
        ],
    }
    _seed_definition(db_session, "TEST_GW_DEFAULT", raw)
    eng = FlowEngine(db_session)
    instance_id = eng.start("TEST_GW_DEFAULT", "paper", 1, "K1", variables={})
    instance = db_session.get(FlowInstance, instance_id)
    assert instance.status == "APPROVED"


# ══════════════════════════════════════════════════════════
# 并发与幂等
# ══════════════════════════════════════════════════════════

def test_double_approve_second_is_rejected(db_session, engine, teacher, grade_admin):
    """同一待办被审批两次时，第二次必须报错而不是静默覆盖。"""
    instance_id = engine.start(
        "PAPER_REVIEW_001", "paper", 49, "PAPER-49",
        variables=_paper_payload(), creator_id=teacher.id)
    task = db_session.scalar(
        select(FlowTask).where(FlowTask.instance_id == instance_id))
    engine.approve(task.id, comment="第一次", operator=grade_admin)

    with pytest.raises(BusinessException):
        engine.approve(task.id, comment="第二次", operator=grade_admin)


def test_approve_on_done_task_raises(db_session, engine, teacher, grade_admin):
    """已完成的任务不能再处理。"""
    instance_id = engine.start(
        "PAPER_REVIEW_001", "paper", 50, "PAPER-50",
        variables=_paper_payload(), creator_id=teacher.id)
    task = db_session.scalar(
        select(FlowTask).where(FlowTask.instance_id == instance_id))
    engine.approve(task.id, comment="ok", operator=grade_admin)
    with pytest.raises(BusinessException):
        engine.reject(task.id, comment="反悔", operator=grade_admin)


def test_approve_unsupported_action_rejected(db_session):
    """审批活动未声明该动作时必须拒绝。"""
    raw = {
        "id": "X", "name": "x", "endActivities": ["C"],
        "activities": [
            {"activityId": "A", "activityType": "START", "nextActivities": ["B"]},
            {"activityId": "B", "activityType": "APPROVAL_TASK", "roleRef": "R",
             "approvalOutcomes": ["APPROVE"], "nextActivities": ["C"]},
            {"activityId": "C", "activityType": "END"},
        ],
    }
    _seed_definition(db_session, "TEST_ONLY_APPROVE", raw)
    eng = FlowEngine(db_session)
    instance_id = eng.start("TEST_ONLY_APPROVE", "paper", 2, "K2", variables={})
    task = db_session.scalar(
        select(FlowTask).where(FlowTask.instance_id == instance_id))
    with pytest.raises(BusinessException, match="不支持"):
        eng.reject(task.id, comment="不行", operator=grade_admin)


# ══════════════════════════════════════════════════════════
# 查询
# ══════════════════════════════════════════════════════════

def test_todo_list_filters_by_role(db_session, engine, teacher, grade_admin):
    """待办按当前用户角色过滤——年级管理员看得到，教师看不到。"""
    engine.start("PAPER_REVIEW_001", "paper", 51, "PAPER-51",
                 variables=_paper_payload(), creator_id=teacher.id)
    assert engine.todo_list(grade_admin)["total"] == 1
    assert engine.todo_list(teacher)["total"] == 0


def test_todo_list_empty_for_no_roles(db_session, engine):
    """无角色用户看不到任何待办。"""
    assert engine.todo_list(_Actor(999, []))["total"] == 0


def test_done_list_filters_by_assignee(db_session, engine, teacher, grade_admin):
    """已办按处理人过滤。"""
    instance_id = engine.start(
        "PAPER_REVIEW_001", "paper", 52, "PAPER-52",
        variables=_paper_payload(), creator_id=teacher.id)
    task = db_session.scalar(
        select(FlowTask).where(FlowTask.instance_id == instance_id))
    engine.approve(task.id, comment="ok", operator=grade_admin)

    assert engine.done_list(grade_admin)["total"] == 1
    assert engine.done_list(teacher)["total"] == 0


def test_my_instances_filters_by_creator(db_session, engine, teacher, grade_admin):
    """我发起的按 creator_id 过滤。"""
    engine.start("PAPER_REVIEW_001", "paper", 53, "PAPER-53",
                 variables=_paper_payload(), creator_id=teacher.id)
    assert engine.my_instances(teacher)["total"] == 1
    assert engine.my_instances(grade_admin)["total"] == 0


def test_instance_detail_includes_history(db_session, engine, teacher, grade_admin):
    """实例详情含留痕与待办。"""
    instance_id = engine.start(
        "PAPER_REVIEW_001", "paper", 54, "PAPER-54",
        variables=_paper_payload(), creator_id=teacher.id)
    detail = engine.instance_detail(instance_id)
    assert detail["biz_type"] == "paper"
    assert len(detail["tasks"]) == 1
    assert len(detail["history"]) >= 1


def test_instance_detail_missing_raises(db_session, engine):
    """不存在的实例抛 404。"""
    with pytest.raises(NotFoundException):
        engine.instance_detail(999999)


def test_find_instance_prevents_duplicate(db_session, engine, teacher):
    """运行中的实例可被查到（用于防重复发起）。"""
    engine.start("PAPER_REVIEW_001", "paper", 55, "PAPER-55",
                 variables=_paper_payload(), creator_id=teacher.id)
    assert engine.find_instance("paper", 55) is not None
    assert engine.find_instance("paper", 999) is None


# ══════════════════════════════════════════════════════════
# 认领
# ══════════════════════════════════════════════════════════

def test_claim_binds_assignee(db_session, engine, teacher, grade_admin):
    """认领后任务绑定处理人并变为 CLAIMED。"""
    instance_id = engine.start(
        "PAPER_REVIEW_001", "paper", 56, "PAPER-56",
        variables=_paper_payload(), creator_id=teacher.id)
    task = db_session.scalar(
        select(FlowTask).where(FlowTask.instance_id == instance_id))
    engine.claim(task.id, operator=grade_admin)
    row = db_session.get(FlowTask, task.id)
    assert row.status == "CLAIMED"
    assert row.assignee_id == grade_admin.id
    assert row.claimed_at is not None


def test_claim_done_task_raises(db_session, engine, teacher, grade_admin):
    """已完成的待办不能认领。"""
    instance_id = engine.start(
        "PAPER_REVIEW_001", "paper", 57, "PAPER-57",
        variables=_paper_payload(), creator_id=teacher.id)
    task = db_session.scalar(
        select(FlowTask).where(FlowTask.instance_id == instance_id))
    engine.approve(task.id, comment="ok", operator=grade_admin)
    with pytest.raises(BusinessException):
        engine.claim(task.id, operator=grade_admin)


# ══════════════════════════════════════════════════════════
# 规则引擎安全边界
# ══════════════════════════════════════════════════════════

def test_rule_registry_loads_all_rules():
    """M3 的 37 条规则必须全部能注册（表达式静态校验通过）。"""
    registry = load_rule_registry()
    assert len(registry.all()) == 37


def test_ontology_assets_shipped_with_app():
    """本体副本必须随 backend/app 分发。

    容器镜像只 COPY backend/app（没有 audit-reports/），所以流程定义与规则
    的运行时副本必须放在 app/ontology/ 下。缺了它，生产环境启动后
    流程引擎会找不到任何定义——而本地开发态因为有 audit-reports/ 而一切正常，
    这种「本地过、线上炸」的差异最难查。
    """
    from app.services.flow_engine import _APP_ONTOLOGY_DIR

    assert (_APP_ONTOLOGY_DIR / "m6-flow-model.yaml").exists(), (
        "backend/app/ontology/m6-flow-model.yaml 缺失：容器镜像里没有 "
        "audit-reports/，流程引擎将找不到任何流程定义")
    assert (_APP_ONTOLOGY_DIR / "m3-rule-model.yaml").exists(), (
        "backend/app/ontology/m3-rule-model.yaml 缺失：容器镜像里规则注册表为空")


def test_ontology_copy_matches_source():
    """随代码分发的副本必须与本体源文件一致（防止只改了一份）。"""
    from app.services.flow_engine import _APP_ONTOLOGY_DIR

    source_dir = pathlib.Path(__file__).resolve().parents[1] / "audit-reports/ontology-inventory"
    if not source_dir.exists():
        pytest.skip("本体源文件不在工作区（容器内不存在）")
    for name in ("m6-flow-model.yaml", "m3-rule-model.yaml"):
        source = (source_dir / name).read_text(encoding="utf-8")
        shipped = (_APP_ONTOLOGY_DIR / name).read_text(encoding="utf-8")
        assert source == shipped, (
            f"{name} 的随代码副本与本体源文件不一致——"
            "改本体后必须同步 backend/app/ontology/ 下的副本")


def test_expression_rejects_dunder():
    """属性穿透必须被拒。"""
    with pytest.raises(RuleExpressionError):
        evaluate_expression("x.__class__", {"x": 1})


def test_expression_rejects_forbidden_identifier():
    """禁用标识符必须被拒（按独立单词比对，ongoing 不误伤）。"""
    with pytest.raises(RuleExpressionError):
        evaluate_expression("import os", {})
    assert evaluate_expression("status == 'ongoing'", {"status": "ongoing"}) is True


def test_undeclared_object_field_not_readable():
    """未声明 reads 时，对象的**非敏感**字段不可读（fail-closed）。

    敏感字段另有硬黑名单保护（见 test_sensitive_field_never_readable），
    那条路径与 reads 声明无关。
    """

    class Obj:
        def __init__(self):
            self.status = "draft"
            self.password_hash = "secret"
            self.share_scope = "private"

    with pytest.raises(Exception):
        evaluate_expression("paper.share_scope == 'private'", {"paper": Obj()})


def test_declared_field_becomes_readable():
    """字段一旦被声明即可读——证明上一条拒绝确实来自未声明，而非类型限制。"""

    class Obj:
        def __init__(self):
            self.status = "draft"
            self.password_hash = "secret"
            self.share_scope = "private"

    result = evaluate_expression(
        "paper.share_scope == 'private'", {"paper": Obj()},
        declared=("status", "share_scope"))
    assert result is True


def test_declared_fields_readable():
    """声明了 reads 的字段可读。"""

    class Obj:
        def __init__(self):
            self.status = "draft"
            self.share_scope = "private"

    result = evaluate_expression(
        "paper.status == 'draft' AND paper.share_scope == 'private'",
        {"paper": Obj()}, declared=("status", "share_scope"))
    assert result is True


def test_sensitive_field_never_readable():
    """敏感字段即使被声明也不放行。"""

    class Obj:
        def __init__(self):
            self.password_hash = "secret"
            self.status = "draft"

    with pytest.raises(Exception):
        evaluate_expression(
            "paper.password_hash == 'secret'", {"paper": Obj()},
            declared=("password_hash", "status"))


def test_rule_violation_raised_when_condition_false():
    """规则不满足时抛 RuleViolation。"""
    registry = load_rule_registry()
    rule = registry.require("RULE-PAPER-REVIEW-STATE-GUARD")
    with pytest.raises(RuleViolation):
        rule.check({"paper": {"status": "pending", "share_scope": "private"}})


def test_sql_dialect_keywords_converted():
    """框架的大写 AND/OR/NOT 必须能求值。"""
    assert evaluate_expression("a == 1 AND NOT (b == 2)", {"a": 1, "b": 3}) is True


def test_literal_string_with_and_not_converted():
    """字符串字面量里的 AND 不能被改写。"""
    assert evaluate_expression("name == 'A AND B'", {"name": "A AND B"}) is True
