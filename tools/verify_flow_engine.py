"""End-to-end verification of the flow engine (M6) against an isolated database.

Covers the HTTP surface (todo / done / instances / claim / approve / reject / return /
cancel) plus the definition-sync endpoint, using the real FastAPI app and a real
SQLite database. No business table state is touched: the engine is an orchestration
layer and the paper status stays where it is.

Run: python tools/verify_flow_engine.py
"""
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
TEMP = tempfile.TemporaryDirectory(prefix="flow-engine-", ignore_cleanup_errors=True)
os.environ.update({
    "DATABASE_URL": f"sqlite:///{Path(TEMP.name) / 'test.db'}",
    "SECRET_KEY": "isolated-flow-engine-test-key-0123456789abcdef",
    "SEED_BASE_DATA": "false", "SEED_DEMO_DATA": "false",
    "SCHEDULER_ENABLED": "false", "LLM_ENABLED": "false",
    "RAG_WARMUP_ENABLED": "false", "DEBUG": "false",
    "UPLOAD_DIR": str(Path(TEMP.name) / "uploads"),
    "EXPORT_DIR": str(Path(TEMP.name) / "exports"),
    "LOG_DIR": str(Path(TEMP.name) / "logs"),
})

from fastapi import Depends
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.api.deps import get_current_admin, get_current_user
from app.core.config import settings
from app.core.database import Base, SessionLocal, engine, get_db
from app.main import app
from app.models import Grade, Role, User, UserRole
from app.services.flow_engine import FlowEngine
from app.utils.common import now_local

CHECKS = 0


def check(name, condition):
    global CHECKS
    if not condition:
        raise AssertionError(name)
    CHECKS += 1
    print(f"[OK] {name}")


def seed(db):
    grade = db.scalar(select(Grade).where(Grade.grade_num == 1))
    if grade is None:
        grade = Grade(name="流程测试年级", stage="primary", grade_num=1)
        db.add(grade)
        db.flush()

    roles = {}
    for code in ("sys_admin", "grade_admin", "teacher"):
        role = db.scalar(select(Role).where(Role.code == code))
        if role is None:
            role = Role(code=code, name=code, data_scope="all", sort=1)
            db.add(role)
            db.flush()
        roles[code] = role

    users = {}
    for code in ("sys_admin", "grade_admin", "teacher"):
        user = db.scalar(select(User).where(User.username == f"flow_{code}"))
        if user is None:
            user = User(username=f"flow_{code}", password="x", real_name=code,
                        identity=code, status="active")
            db.add(user)
            db.flush()
            db.add(UserRole(user_id=user.id, role_id=roles[code].id))
        users[code] = user

    # 第二个年级管理员：转办必须有接收方，且转办后处理人要变更。
    user2 = db.scalar(select(User).where(User.username == "flow_grade_admin_2"))
    if user2 is None:
        user2 = User(username="flow_grade_admin_2", password="x",
                     real_name="审核员乙", identity="grade_admin",
                     status="active")
        db.add(user2)
        db.flush()
        db.add(UserRole(user_id=user2.id, role_id=roles["grade_admin"].id))
    db.commit()
    return {"grade": grade.id,
            "sys_admin": users["sys_admin"].id,
            "grade_admin": users["grade_admin"].id,
            "grade_admin_2": user2.id,
            "teacher": users["teacher"].id}


def verify_integration(ids, call, as_user):
    """注册审批 + 试卷审核接入流程引擎后的端到端行为。"""
    from app.models import FlowInstance, FlowTask, Registration
    from app.services.flow_engine import FlowEngine
    from app.core.database import SessionLocal

    # ---- 试卷审核：submit 产生待办，approve 推进实例 ----
    as_teacher = ids["teacher"]
    with SessionLocal() as db:
        from app.models import Paper, Subject
        subject = db.scalar(select(Subject).where(Subject.grade_id == ids["grade"]))
        if subject is None:
            subject = Subject(name="数学", grade_id=ids["grade"])
            db.add(subject)
            db.flush()
        paper = Paper(name="流程接入测试卷", status="draft",
                      share_scope="private", creator_id=as_teacher,
                      grade_id=ids["grade"], subject_id=subject.id,
                      total_score=100, duration=60, created_at=now_local())
        db.add(paper)
        db.commit()
        paper_id = paper.id

    as_user(ids["teacher"])
    call("POST", f"/question/papers/{paper_id}/review", {"action": "submit"})

    with SessionLocal() as db:
        inst = db.scalar(select(FlowInstance).where(
            FlowInstance.biz_type == "paper",
            FlowInstance.biz_id == paper_id))
        check("提交审核启动了流程实例", inst is not None)
        task = db.scalar(select(FlowTask).where(
            FlowTask.instance_id == inst.id))
        check("流程实例产生 1 条待办", task is not None)
        check("待办角色为 grade_admin", task.role_code == "grade_admin")

    # 年级管理员通过流程待办接口审批（而非直接调 review）
    as_user(ids["grade_admin"])
    todo = call("GET", "/flow/todo")
    check("年级管理员可见待办", todo["total"] >= 1)

    # 通过既有接口 approve，流程实例应被推进
    as_user(ids["grade_admin"])
    call("POST", f"/question/papers/{paper_id}/review",
         {"action": "approve", "comment": "同意"})

    with SessionLocal() as db:
        inst = db.get(FlowInstance, inst.id)
        check("审核通过后流程实例为 APPROVED", inst.status == "APPROVED")

    # ---- 注册审批 ----
    from app.models import User
    as_user(ids["sys_admin"])
    with SessionLocal() as db:
        reg_user = User(username="flow_reg_student", password="x",
                        real_name="流程注册用户", identity="student",
                        status="pending", created_at=now_local())
        db.add(reg_user)
        db.flush()
        reg = Registration(user_id=reg_user.id, identity="student",
                           status="pending", created_at=now_local())
        db.add(reg)
        db.commit()
        reg_user_id = reg_user.id

    # 直接走 service 层启动流程（避免注册接口需要验证码）
    with SessionLocal() as db:
        engine = FlowEngine(db)
        engine.start("REGISTRATION_001_T", "registration", reg_user_id,
                     f"USER-{reg_user_id}",
                     variables={"user": {"status": "pending"}},
                     creator_id=None)

    with SessionLocal() as db:
        inst2 = db.scalar(select(FlowInstance).where(
            FlowInstance.biz_type == "registration",
            FlowInstance.biz_id == reg_user_id))
        check("注册流程实例已创建", inst2 is not None)
        t2 = db.scalar(select(FlowTask).where(FlowTask.instance_id == inst2.id))
        check("注册待办角色为 sys_admin", t2.role_code == "sys_admin")


def verify_escalation(ids, call, as_user):
    """转办 / 催办 / 逾期的 HTTP 链路。"""
    from datetime import timedelta

    from app.models import FlowTask, FlowTransfer, Notification
    from app.services.flow_engine import FlowEngine
    from app.core.database import SessionLocal

    # ---- 造一条 grade_admin 的待办 ----
    with SessionLocal() as db:
        engine = FlowEngine(db)
        inst_id = engine.start(
            "PAPER_REVIEW_001", "paper", 9101, "PAPER-9101",
            variables={"paper": {"status": "draft", "share_scope": "private"}},
            creator_id=ids["teacher"])
        task = db.scalar(select(FlowTask).where(FlowTask.instance_id == inst_id))
        task_id = task.id
        check("活动声明 timeout 后待办带 deadline", task.deadline is not None)

    # ---- 逾期待办列表 ----
    as_user(ids["grade_admin"])
    overdue = call("GET", "/flow/overdue")
    check("逾期待办初始为空（deadline 还没到）", overdue["total"] == 0)

    # ---- 转办候选人 ----
    candidates = call("GET", f"/flow/tasks/{task_id}/transfer-candidates")
    cand_ids = {c["id"] for c in candidates}
    check("候选人含第二个年级管理员", ids["grade_admin_2"] in cand_ids)
    check("候选人不含教师（角色不符）", ids["teacher"] not in cand_ids)

    # ---- 越权：教师不能转办别人的待办 ----
    as_user(ids["teacher"])
    call("POST", f"/flow/tasks/{task_id}/transfer",
         {"to_user_id": ids["grade_admin_2"]}, expected=403)

    # ---- 正常转办 ----
    as_user(ids["grade_admin"])
    transferred = call("POST", f"/flow/tasks/{task_id}/transfer",
                       {"to_user_id": ids["grade_admin_2"], "reason": "出差"})
    check("转办后处理人是接收方", transferred["assignee_id"] == ids["grade_admin_2"])
    check("转办计数为 1", transferred["transfer_count"] == 1)

    with SessionLocal() as db:
        rows = db.scalars(select(FlowTransfer).where(
            FlowTransfer.task_id == task_id)).all()
        check("转办留下 1 条留痕", len(rows) == 1)
        check("留痕记录了理由", rows[0].reason == "出差")
        check("留痕记录了接收方", rows[0].to_user_id == ids["grade_admin_2"])

    # ---- 不能转给自己 ----
    as_user(ids["grade_admin_2"])
    call("POST", f"/flow/tasks/{task_id}/transfer",
         {"to_user_id": ids["grade_admin_2"]}, expected=400)

    # ---- 催办 ----
    as_user(ids["grade_admin"])
    urged = call("POST", f"/flow/tasks/{task_id}/urge", {"comment": "尽快处理"})
    check("催办返回接收方姓名", urged["urged"] is True)
    check("催办计数为 1", urged["urge_count"] == 1)

    with SessionLocal() as db:
        notes = db.scalars(select(Notification).where(
            Notification.user_id == ids["grade_admin_2"])).all()
        check("催办发出了通知", len(notes) >= 1)

    # ---- 催办频次限制 ----
    as_user(ids["grade_admin"])
    call("POST", f"/flow/tasks/{task_id}/urge", {"comment": "再催一次"}, expected=400)

    # ---- 设置 / 清除截止时间 ----
    from app.utils.common import now_local
    as_user(ids["grade_admin"])
    future = now_local() + timedelta(days=2)
    updated = call("PUT", f"/flow/tasks/{task_id}/deadline",
                   {"deadline": future.strftime("%Y-%m-%d %H:%M:%S")})
    check("截止时间已设置", updated["deadline"] is not None)
    check("未到期的待办不算逾期", updated["is_overdue"] is False)

    # 推到过去 -> 进入逾期待办
    as_user(ids["grade_admin"])
    past = now_local() - timedelta(hours=1)
    updated2 = call("PUT", f"/flow/tasks/{task_id}/deadline",
                    {"deadline": past.strftime("%Y-%m-%d %H:%M:%S")})
    check("过期后 is_overdue 为真", updated2["is_overdue"] is True)

    overdue = call("GET", "/flow/overdue")
    check("逾期待办列表含该待办", overdue["total"] >= 1)
    check("逾期不自动关闭待办（仍在列表中）",
          any(i["id"] == task_id for i in overdue["items"]))

    # 清除截止时间 -> 不再是逾期待办
    as_user(ids["grade_admin"])
    cleared = call("PUT", f"/flow/tasks/{task_id}/deadline", {"deadline": None})
    check("清除后 deadline 为空", cleared["deadline"] is None)
    check("清除后不再是逾期待办", cleared["is_overdue"] is False)


def main():
    for directory in (settings.UPLOAD_DIR, settings.EXPORT_DIR, settings.LOG_DIR):
        Path(directory).mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(engine)

    with TestClient(app) as client:
        with SessionLocal() as db:
            ids = seed(db)

        def as_user(user_id):
            def override(db=Depends(get_db)):
                return db.get(User, user_id)
            app.dependency_overrides[get_current_user] = override
            app.dependency_overrides[get_current_admin] = override

        def call(method, path, data=None, expected=200):
            response = client.request(method, "/api/v1" + path, json=data)
            if response.status_code != expected:
                raise AssertionError(
                    f"{method} {path}: {response.status_code} {response.text[:800]}")
            check(f"{method} {path} -> {expected}", response.status_code == expected)
            return response.json().get("data")

        # ---- 定义同步（仅管理员）----
        as_user(ids["sys_admin"])
        synced = call("POST", "/flow/definitions/sync")
        check("同步 4 条目标流程", synced["synced"] == 4)
        again = call("POST", "/flow/definitions/sync")
        check("同步幂等（第二次 0 条变更）", again["synced"] == 0)

        # ---- 启动流程并产生待办 ----
        with SessionLocal() as db:
            engine_obj = FlowEngine(db)
            instance_id = engine_obj.start(
                "PAPER_REVIEW_001", "paper", 9001, "PAPER-9001",
                variables={"paper": {"status": "draft", "share_scope": "private"}},
                creator_id=ids["teacher"])
            task = db.scalar(
                select(__import__("app.models", fromlist=["FlowTask"]).FlowTask)
                .where(__import__("app.models", fromlist=["FlowTask"]).FlowTask
                       .instance_id == instance_id))
            task_id = task.id
            check("待办落在 grade_admin 角色", task.role_code == "grade_admin")

        # ---- 教师看不到待办 ----
        as_user(ids["teacher"])
        todo = call("GET", "/flow/todo")
        check("教师待办为空", todo["total"] == 0)

        # ---- 年级管理员看得到待办 ----
        as_user(ids["grade_admin"])
        todo = call("GET", "/flow/todo")
        check("年级管理员可见 1 条待办", todo["total"] == 1)
        check("待办活动为 PR03", todo["items"][0]["activity_id"] == "PR03")
        # 前端依赖的字段：退回目标按流程编码白名单选择，
        # 流程名称/业务标签用于列表展示。缺一个前端就会显示空白。
        check("待办带流程编码", todo["items"][0]["flow_code"] == "PAPER_REVIEW_001")
        check("待办带角色编码", todo["items"][0]["role_code"] == "grade_admin")
        check("待办带活动名称", bool(todo["items"][0]["activity_name"]))

        # ---- 认领 ----
        claimed = call("POST", f"/flow/tasks/{task_id}/claim")
        check("认领后状态为 CLAIMED", claimed["status"] == "CLAIMED")
        check("认领后绑定处理人", claimed["assignee_id"] == ids["grade_admin"])

        # ---- 审批通过 ----
        approved = call("POST", f"/flow/tasks/{task_id}/approve",
                        {"comment": "同意入库"})
        check("实例状态为 APPROVED", approved["status"] == "APPROVED")

        # ---- 已办 ----
        done = call("GET", "/flow/done")
        check("已办 1 条", done["total"] == 1)
        check("已办动作是 APPROVE", done["items"][0]["action"] == "APPROVE")

        # ---- 实例详情含留痕 ----
        detail = call("GET", f"/flow/instances/{instance_id}")
        check("详情含待办", len(detail["tasks"]) == 1)
        check("详情含留痕", len(detail["history"]) >= 2)
        check("详情带流程名称", bool(detail["flow_name"]))
        check("详情带流程编码", detail["flow_code"] == "PAPER_REVIEW_001")
        check("详情带业务标签", detail["biz_label"] == "试卷")
        check("详情带业务键", detail["biz_key"] == "PAPER-9001")
        check("留痕含动作与操作人", bool(detail["history"][0]["action"]))

        # ---- 驳回链路 ----
        with SessionLocal() as db:
            engine_obj = FlowEngine(db)
            inst2 = engine_obj.start(
                "PAPER_REVIEW_001", "paper", 9002, "PAPER-9002",
                variables={"paper": {"status": "draft", "share_scope": "private"}},
                creator_id=ids["teacher"])
            t2 = db.scalar(
                select(__import__("app.models", fromlist=["FlowTask"]).FlowTask)
                .where(__import__("app.models", fromlist=["FlowTask"]).FlowTask
                       .instance_id == inst2))
            task2 = t2.id
        rejected = call("POST", f"/flow/tasks/{task2}/reject", {"comment": "题目有问题"})
        check("驳回后实例为 REJECTED", rejected["status"] == "REJECTED")

        # ---- 退回链路 ----
        with SessionLocal() as db:
            engine_obj = FlowEngine(db)
            inst3 = engine_obj.start(
                "PAPER_REVIEW_001", "paper", 9003, "PAPER-9003",
                variables={"paper": {"status": "draft", "share_scope": "private"}},
                creator_id=ids["teacher"])
            t3 = db.scalar(
                select(__import__("app.models", fromlist=["FlowTask"]).FlowTask)
                .where(__import__("app.models", fromlist=["FlowTask"]).FlowTask
                       .instance_id == inst3))
            task3 = t3.id
        returned = call("POST", f"/flow/tasks/{task3}/return",
                        {"target_activity_id": "PR02", "comment": "补充题目"})
        check("退回后实例回到 RUNNING", returned["status"] == "RUNNING")

        # ---- 取消链路 ----
        with SessionLocal() as db:
            engine_obj = FlowEngine(db)
            inst4 = engine_obj.start(
                "PAPER_REVIEW_001", "paper", 9004, "PAPER-9004",
                variables={"paper": {"status": "draft", "share_scope": "private"}},
                creator_id=ids["teacher"])
            t4 = db.scalar(
                select(__import__("app.models", fromlist=["FlowTask"]).FlowTask)
                .where(__import__("app.models", fromlist=["FlowTask"]).FlowTask
                       .instance_id == inst4))
            task4 = t4.id
        cancelled = call("POST", f"/flow/tasks/{task4}/cancel", {"comment": "不需要了"})
        check("取消后实例为 CANCELLED", cancelled["status"] == "CANCELLED")

        # ---- 我发起的 ----
        as_user(ids["teacher"])
        mine = call("GET", "/flow/instances")
        check("教师发起 4 条流程", mine["total"] == 4)

        # ---- 重复处理同一待办必须被拒 ----
        as_user(ids["grade_admin"])
        call("POST", f"/flow/tasks/{task_id}/approve", {"comment": "再来一次"}, expected=400)

        verify_integration(ids, call, as_user)
        verify_escalation(ids, call, as_user)

        # ---- 未登录必须 401 ----
        app.dependency_overrides.clear()
        call("GET", "/flow/todo", expected=401)

    print()
    print(f"全部通过：流程引擎 HTTP 链路 {CHECKS} 项校验")


if __name__ == "__main__":
    main()

