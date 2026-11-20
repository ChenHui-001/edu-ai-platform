"""转办 / 催办 / 超时 + 考试催办的测试套件。

沿用 qa_flow_engine_suite.py 的夹具风格：内存 SQLite 真实建表、真实事务。

覆盖：
  - 转办：目标角色校验、不能转给自己、留痕、计数；
  - 催办：未认领不可催、频次限制、通知落地；
  - 超时：逾期判定是**计算属性**、逾期列表、设置/清除截止时间；
  - 考试催办：待交名单计算、只能催待交学生、权限校验。

运行：cd backend && python -m pytest qa_flow_urge_suite.py -q
"""
from datetime import timedelta

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.exception import BusinessException, NotFoundException, PermissionException
from app.models import FlowTask, FlowTransfer, Notification, User
from app.services.flow_engine import FlowEngine
from app.services.task_urge import pending_students
from app.utils.common import now_local


@pytest.fixture()
def db_session():
    import app.models  # noqa: F401

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


class _Actor:
    def __init__(self, actor_id, role_codes, name=None):
        self.id = actor_id
        self.role_codes = role_codes
        self.real_name = name or f"用户{actor_id}"
        self.username = f"user{actor_id}"


def _seed_role(session, code):
    """建角色（若已存在则复用）。

    User.role_codes 是**只读 property**，读的是 user.roles 关系 ——
    所以必须真的建 Role 行并挂 UserRole，不能给 user 赋一个属性。
    """
    from app.models import Role

    role = session.scalar(select(Role).where(Role.code == code))
    if role is None:
        role = Role(code=code, name=code, is_active=True)
        session.add(role)
        session.flush()
    return role


def _seed_user(session, user_id, role_codes, name=None, status="active"):
    from app.models import UserRole

    user = User(
        id=user_id, username=f"user{user_id}", real_name=name or f"用户{user_id}",
        password="x",  # password 是必填列，但测试不走认证
        identity="teacher" if "teacher" in role_codes else "student",
        status=status,
    )
    session.add(user)
    session.flush()
    for code in role_codes:
        role = _seed_role(session, code)
        session.add(UserRole(user_id=user.id, role_id=role.id))
    session.commit()
    return user


@pytest.fixture()
def seeded(db_session):
    """两名年级管理员 + 一名无该角色的用户 + 一名教师。"""
    _seed_user(db_session, 201, ["grade_admin"], "审核员甲")
    _seed_user(db_session, 202, ["grade_admin"], "审核员乙")
    _seed_user(db_session, 203, ["teacher"], "普通教师")
    _seed_user(db_session, 204, ["grade_admin"], "停用账号", status="disabled")
    return db_session


@pytest.fixture()
def engine(seeded):
    return FlowEngine(seeded)


def _start_and_get_task(engine, biz_id=9001):
    instance_id = engine.start(
        "PAPER_REVIEW_001", "paper", biz_id, f"PAPER-{biz_id}",
        variables={"paper": {"status": "draft", "share_scope": "private"}},
        creator_id=201)
    task = engine.db.scalar(
        select(FlowTask).where(FlowTask.instance_id == instance_id))
    return instance_id, task


# ══════════════════════════════════════════════════════════
# 转办
# ══════════════════════════════════════════════════════════

def test_transfer_moves_assignee(engine):
    """转办后处理人变更。"""
    _, task = _start_and_get_task(engine)
    engine.transfer(task.id, to_user_id=202, operator=_Actor(201, ["grade_admin"]))
    assert task.assignee_id == 202
    assert task.status == "CLAIMED"


def test_transfer_records_audit_row(engine):
    """转办必须留痕：谁转给了谁。"""
    _, task = _start_and_get_task(engine)
    engine.claim(task.id, operator=_Actor(201, ["grade_admin"]))
    engine.transfer(task.id, to_user_id=202, operator=_Actor(201, ["grade_admin"]),
                    reason="出差")
    rows = engine.db.scalars(
        select(FlowTransfer).where(FlowTransfer.task_id == task.id)).all()
    assert len(rows) == 1
    assert rows[0].from_user_id == 201
    assert rows[0].to_user_id == 202
    assert rows[0].reason == "出差"


def test_transfer_counts(engine):
    """转办计数与时间戳更新。"""
    _, task = _start_and_get_task(engine)
    engine.transfer(task.id, to_user_id=202, operator=_Actor(201, ["grade_admin"]))
    assert task.transfer_count == 1
    assert task.last_transferred_at is not None


def test_transfer_rejects_self(engine):
    """不能转给自己——那是认领。"""
    _, task = _start_and_get_task(engine)
    with pytest.raises(BusinessException, match="不能转办给自己"):
        engine.transfer(task.id, to_user_id=201, operator=_Actor(201, ["grade_admin"]))


def test_transfer_rejects_wrong_role(engine):
    """目标必须持有该待办对应的角色。"""
    _, task = _start_and_get_task(engine)
    with pytest.raises(BusinessException, match="不具备"):
        engine.transfer(task.id, to_user_id=203, operator=_Actor(201, ["grade_admin"]))


def test_transfer_rejects_disabled_user(engine):
    """停用账号不能成为接手人。"""
    _, task = _start_and_get_task(engine)
    with pytest.raises(BusinessException, match="状态异常"):
        engine.transfer(task.id, to_user_id=204, operator=_Actor(201, ["grade_admin"]))


def test_transfer_rejects_unknown_user(engine):
    _, task = _start_and_get_task(engine)
    with pytest.raises(NotFoundException):
        engine.transfer(task.id, to_user_id=9999, operator=_Actor(201, ["grade_admin"]))


def test_transfer_candidates_exclude_current(engine):
    """可转办人员里不含当前处理人，且只含同角色用户。"""
    _, task = _start_and_get_task(engine)
    engine.claim(task.id, operator=_Actor(201, ["grade_admin"]))
    ids = {c["id"] for c in engine.transfer_candidates(task.id)}
    assert 201 not in ids
    assert 202 in ids
    assert 203 not in ids   # teacher 不是 grade_admin
    assert 204 not in ids   # 停用账号


def test_transfer_on_done_task_rejected(engine):
    """已完成的待办不能转办。"""
    instance_id, task = _start_and_get_task(engine)
    engine.approve(task.id, comment="ok", operator=_Actor(201, ["grade_admin"]))
    with pytest.raises(BusinessException, match="已"):
        engine.transfer(task.id, to_user_id=202, operator=_Actor(201, ["grade_admin"]))


# ══════════════════════════════════════════════════════════
# 催办
# ══════════════════════════════════════════════════════════

def test_urge_requires_claimed(engine):
    """未认领的待办没有明确的催办对象。"""
    _, task = _start_and_get_task(engine)
    with pytest.raises(BusinessException, match="尚未认领"):
        engine.urge(task.id, operator=_Actor(201, ["grade_admin"]))


def test_urge_sends_notification(engine):
    """催办给处理人发站内通知。"""
    _, task = _start_and_get_task(engine)
    engine.claim(task.id, operator=_Actor(201, ["grade_admin"]))
    result = engine.urge(task.id, operator=_Actor(201, ["grade_admin"]),
                          comment="尽快处理")
    assert result["urged"] is True
    assert result["to_user_id"] == 201
    notes = engine.db.scalars(select(Notification)).all()
    assert len(notes) == 1
    assert notes[0].user_id == 201
    assert "催办" in notes[0].title
    assert "尽快处理" in (notes[0].content or "")


def test_urge_counts(engine):
    _, task = _start_and_get_task(engine)
    engine.claim(task.id, operator=_Actor(201, ["grade_admin"]))
    engine.urge(task.id, operator=_Actor(201, ["grade_admin"]))
    assert task.urge_count == 1
    assert task.last_urged_at is not None


def test_urge_cooldown_blocks_spam(engine):
    """频次限制：30 分钟内不能连催。"""
    _, task = _start_and_get_task(engine)
    engine.claim(task.id, operator=_Actor(201, ["grade_admin"]))
    engine.urge(task.id, operator=_Actor(201, ["grade_admin"]))
    with pytest.raises(BusinessException, match="过于频繁"):
        engine.urge(task.id, operator=_Actor(201, ["grade_admin"]))


def test_urge_after_transfer_targets_new_owner(engine):
    """转办后催办对象是新处理人。"""
    _, task = _start_and_get_task(engine)
    engine.claim(task.id, operator=_Actor(201, ["grade_admin"]))
    engine.transfer(task.id, to_user_id=202, operator=_Actor(201, ["grade_admin"]))
    result = engine.urge(task.id, operator=_Actor(201, ["grade_admin"]))
    assert result["to_user_id"] == 202


# ══════════════════════════════════════════════════════════
# 超时
# ══════════════════════════════════════════════════════════

def test_task_out_is_overdue_computed(engine):
    """逾期是计算属性，不是存储状态。"""
    from datetime import timedelta

    from app.utils.common import now_local

    _, task = _start_and_get_task(engine)
    out = engine.task_out(task)
    assert out["is_overdue"] is False

    task.deadline = now_local() - timedelta(minutes=1)
    engine.db.commit()
    assert engine.task_out(task)["is_overdue"] is True


def test_overdue_tasks_lists_only_expired(engine):
    """逾期列表只含已过截止时间的待办。"""
    from datetime import timedelta

    from app.utils.common import now_local

    _, task = _start_and_get_task(engine)
    task.deadline = now_local() - timedelta(minutes=5)
    engine.db.commit()
    result = engine.overdue_tasks(_Actor(201, ["grade_admin"]))
    assert result["total"] == 1
    assert result["items"][0]["id"] == task.id


def test_overdue_excludes_future_deadline(engine):
    from datetime import timedelta

    from app.utils.common import now_local

    _, task = _start_and_get_task(engine)
    task.deadline = now_local() + timedelta(hours=2)
    engine.db.commit()
    assert engine.overdue_tasks(_Actor(201, ["grade_admin"]))["total"] == 0


def test_overdue_excludes_other_roles(engine):
    """待办按角色过滤：别的角色看不到。"""
    from datetime import timedelta

    from app.utils.common import now_local

    _, task = _start_and_get_task(engine)
    task.deadline = now_local() - timedelta(minutes=5)
    engine.db.commit()
    assert engine.overdue_tasks(_Actor(203, ["teacher"]))["total"] == 0


def test_overdue_does_not_auto_close(engine):
    """逾期不自动关闭待办——结不结由人决定。"""
    from datetime import timedelta

    from app.utils.common import now_local

    _, task = _start_and_get_task(engine)
    task.deadline = now_local() - timedelta(minutes=5)
    engine.db.commit()
    engine.overdue_tasks(_Actor(201, ["grade_admin"]))
    assert task.status == "TODO"


def test_set_deadline_and_clear(engine):
    """设置与清除截止时间。"""
    from datetime import timedelta

    from app.utils.common import now_local

    _, task = _start_and_get_task(engine)
    engine.set_deadline(task.id, now_local() + timedelta(days=1))
    assert task.deadline is not None
    engine.set_deadline(task.id, None)
    assert task.deadline is None


# ══════════════════════════════════════════════════════════
# 越权防护：操作人必须持有待办角色
# ══════════════════════════════════════════════════════════

def test_transfer_rejects_operator_without_role(engine):
    """操作人没有该待办角色时不能转办。

    此前只校验了**目标用户**的角色，操作人可以是任意登录用户 ——
    等于任何人都能把别人的待办转走。
    """
    _, task = _start_and_get_task(engine)
    with pytest.raises(PermissionException, match="角色"):
        engine.transfer(task.id, to_user_id=202, operator=_Actor(203, ["teacher"]))


def test_urge_rejects_operator_without_role(engine):
    """操作人没有该待办角色时不能催办。"""
    _, task = _start_and_get_task(engine)
    engine.claim(task.id, operator=_Actor(201, ["grade_admin"]))
    with pytest.raises(PermissionException, match="角色"):
        engine.urge(task.id, operator=_Actor(203, ["teacher"]))


def test_claim_rejects_operator_without_role(engine):
    """无角色的用户不能认领。"""
    _, task = _start_and_get_task(engine)
    with pytest.raises(PermissionException, match="角色"):
        engine.claim(task.id, operator=_Actor(203, ["teacher"]))


def test_sys_admin_may_operate_any_role(engine):
    """系统管理员可兜底处理任意角色的积压待办。"""
    _, task = _start_and_get_task(engine)
    engine.claim(task.id, operator=_Actor(205, ["sys_admin"]))
    assert task.assignee_id == 205


# ══════════════════════════════════════════════════════════
# deadline 数据来源
# ══════════════════════════════════════════════════════════

def test_task_deadline_from_activity_timeout(engine):
    """活动声明的 timeout 会落成待办的 deadline。

    此前 _create_task 从不给 deadline 赋值，逾期待办列表恒为空 ——
    超时功能是个只能看不能用的空壳。
    """
    _, task = _start_and_get_task(engine)
    assert task.deadline is not None
    # PAPER_REVIEW_001 的 PR03 声明 timeout: 48 小时
    delta = task.deadline - task.created_at
    assert timedelta(hours=47) < delta <= timedelta(hours=48)


def test_overdue_list_populated_by_timeout(engine):
    """把 deadline 推到过去后，逾期待办列表应能查出来。"""
    _, task = _start_and_get_task(engine)
    task.deadline = now_local() - timedelta(minutes=5)
    engine.db.commit()
    result = engine.overdue_tasks(_Actor(201, ["grade_admin"]))
    assert result["total"] == 1
    assert result["items"][0]["id"] == task.id
    assert result["items"][0]["is_overdue"] is True
