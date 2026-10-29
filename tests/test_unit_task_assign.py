#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""离线单元回归：任务下发对象的状态校验（指定学生路径 vs 班级路径）。

## 这个文件锁的是什么

`task.py` 的 `create_task` 里有**两条下发路径**，历史上是两套标准：

- 班级路径：`select(User.id).where(User.class_id == cid, User.status == "active")`
- 指定学生路径：只判 `db.get(User, sid)` 存不存在，**完全不过滤 status**

后果是「停用」只拦住了登录，没拦住任务下发：教师勾中一个已停用/待审批的
学生，该学生仍会收到站内通知、`TaskAssignment` 照常写入。修复（`fb634bc`）
给指定学生路径补了 active 校验，且**报错而非静默剔除**。

## 反控：回退修复后本文件应有 23 项失败

这组断言在 `fb634bc` **之前**的代码上不是全红，而是**部分红** —— 这是它
的判别力所在。实测（`git show 0adf94d:backend/app/api/v1/task.py` 覆盖后
复跑）：`checked=40 passed=17 failed=23`，退出码 1。

| 场景 | 修复前 | 修复后 |
| --- | --- | --- |
| 指定 disabled 学生 → 被拒 | ✘ 200 成功 | ✅ 400 报错 |
| 该学生双表（通知 + assignment）零记录 | ✘ 各 +1 | ✅ 零新增 |
| 多个不合规学生一次列全 | ✘ 200 成功 | ✅ 一条消息列全 |
| 2 班 + 停用指定学生 → 整体回滚 | ✘ 提交了 4 类记录 | ✅ 全回滚 |
| 定时发布路径拦截 | ✘ 建出草稿 | ✅ 400 报错 |
| 正常学生单发 | ✅ | ✅ |
| 2 班 + 1 指定学生 | ✅ | ✅ |
| 不存在的学生 ID | ✅ | ✅ |

**最后三行在修复前后都通过。** 它们不是判据，是**防回归的护栏**：如果哪天
有人为了通过上面几行而把下发逻辑改坏（把班级路径也改成报错、或把
`notify_ids` 与 `TaskAssignment` 拆成两个数据源），这三行会先红。审阅时
不要因为「修复前也是绿的」就把它们当冗余删掉。

### 一条差点漏掉的假绿

场景八原写法只断言「错误消息里不含 a1/b1」，结果它在**修复前的版本上也
通过** —— 因为修复前根本不报错，消息是一条「作业发布成功，已通知 3 名
学生」，当然不含这两个名字。是反控把这个假绿暴露出来的，现补了一条
「消息必须是拒绝文案」的前置断言。**这就是为什么这组断言必须做反控。**

## 三处刻意的不对称，必须锁住（否则会被后人"顺手统一"改坏）

1. **指定学生不合规 → 报错；班级里有人不合规 → 静默跳过。**
   教师显式点名了一个人，悄悄丢参数比报错更糟；班级是批量对象，一个停用
   学生不该让整单失败。
2. **班级里的停用学生仍拥有 assignment（按班级粒度），但不发通知。**
   刻意留的：恢复账号后能看到历史作业。所以断言写的是「班级 assignment
   存在 + 该学生无通知」，不是「该学生无 assignment」—— 后者是错的表述。
3. **`notify_ids` 不对 `student_ids` 二次过滤。**
   上面已校验过 active，这里再滤一次会与 `TaskAssignment`（不过滤）产生
   偏差，变成「通知发了但作业列表里没有」。

## 为什么走 HTTP 而不是直接调函数

失败的请求必须验证**真实事务边界**：`create_task` 在参数校验之前就
`db.add(task)` + `db.flush()`，校验失败时若 `get_db` 的收尾没把未提交事务
丢掉，脏 Task 行会留在库里。直接调函数时我自己写了 `db.rollback()`，反而
把这道保障"替"代码实现了 —— 那样测不出真实行为。走 TestClient 才是在测
产品代码本身。

## 用法

    python tests/test_unit_task_assign.py

退出码：0 = 全部通过，1 = 有失败。
"""
import os
import sys
import tempfile
from datetime import timedelta

# ---- 必须在导入 app.* 之前定好环境：避免在仓库里建出脏库、避免拉外网 ----
_TMP = tempfile.mkdtemp(prefix="unit_task_assign_")
os.environ["DATABASE_URL"] = "sqlite:///" + os.path.join(_TMP, "unit.db").replace("\\", "/")
os.environ["LLM_ENABLED"] = "false"
os.environ["SCHEDULER_ENABLED"] = "false"
os.environ["DEBUG"] = "false"
os.environ.setdefault("SECRET_KEY", "unit_test_secret_key_not_for_prod")

_BACKEND = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"
)
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

import app.models  # noqa: F401,E402  确保全部表注册到 Base.metadata
from app.core.database import Base, engine  # noqa: E402
from app.core.security import create_access_token  # noqa: E402
from app.main import app  # noqa: E402
from app.utils.common import now_local  # noqa: E402

_FAILED = []
_PASSED = 0
_FIXED = "fb634bc"  # 本文件所锁定的修复 commit（用于报错文案）


def ok(name, cond, detail=""):
    """断言并打印。刻意不叫 check()：tools/check_weak_assertion.py 只扫
    e2e 的 check(...) 恒真写法，两边命名分开，扫描结果不会互相污染。"""
    global _PASSED
    if cond:
        _PASSED += 1
        print(f"  [PASS] {name}" + (f"  -> {detail}" if detail else ""))
    else:
        _FAILED.append(name)
        print(f"  [FAIL] {name}  -> {detail}")


# ============================================================
# 造数据：年级 / 学科 / 两个班 / 教师（含任教关系与 task:write）/ 若干学生
# ============================================================
def seed():
    """建一套最小可下发环境，返回一个 id 字典（全部是纯 int/str，不带 ORM 对象）。

    只返回标量是关键：session 关闭后 ORM 实例变 detached，再读 `.id` 会抛
    `DetachedInstanceError`，把「造数据」的问题伪装成「代码缺陷」。
    """
    from sqlalchemy.orm import sessionmaker

    from app.models import (
        Class, Grade, IdentityType, Paper, Permission, PermissionType,
        Role, RolePermission, Subject, TeachingAssignment, User, UserRole,
        UserStatus,
    )

    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        g = Grade(name="单元测试一年级")
        db.add(g)
        db.flush()
        sub = Subject(name="数学", grade_id=g.id)
        db.add(sub)
        db.flush()

        ca = Class(name="单元A班", grade_id=g.id)
        cb = Class(name="单元B班", grade_id=g.id)
        db.add_all([ca, cb])
        db.flush()

        # 教师角色带 task:write —— 让它走真实的 require_perm，
        # 而不是靠 sys_admin 短路（sys_admin 会跳过任教范围校验，
        # 那样就测不到「修复没破坏 scope 检查」）。
        role = Role(code="teacher", name="教师", data_scope="taught_class")
        db.add(role)
        db.flush()
        perm = Permission(code="task:write", name="任务发布",
                          type=PermissionType.BUTTON.value)
        db.add(perm)
        db.flush()
        db.add(RolePermission(role_id=role.id, permission_id=perm.id))

        def mk_user(name, *, klass=None, status=UserStatus.ACTIVE.value,
                    identity=IdentityType.STUDENT.value, is_teacher=False):
            u = User(
                username=name, password="x" * 20, real_name=name,
                identity=identity, status=status, grade_id=g.id,
                class_id=klass.id if klass else None,
                must_change_password=False,
            )
            db.add(u)
            db.flush()
            if is_teacher:
                db.add(UserRole(user_id=u.id, role_id=role.id))
                db.flush()
            return u

        teacher = mk_user("unit_teacher_t", identity=IdentityType.TEACHER.value,
                          is_teacher=True)
        # 任教两个班：走真实 DataScope.class_ids()，两类下发都在范围内
        for c in (ca, cb):
            db.add(TeachingAssignment(teacher_id=teacher.id, class_id=c.id,
                                      subject_id=sub.id, grade_id=g.id))
        db.flush()

        a1 = mk_user("unit_a1_active", klass=ca)
        a2 = mk_user("unit_a2_disabled", klass=ca, status=UserStatus.DISABLED.value)
        b1 = mk_user("unit_b1_active", klass=cb)
        s1 = mk_user("unit_s1_active")                                  # 无班级，单发对象
        s2 = mk_user("unit_s2_disabled", status=UserStatus.DISABLED.value)
        s3 = mk_user("unit_s3_pending", status=UserStatus.PENDING.value)

        paper = Paper(name="单元测试试卷", grade_id=g.id, subject_id=sub.id,
                      creator_id=teacher.id, total_score=100, duration=60)
        db.add(paper)
        db.commit()

        return {
            "grade_id": g.id, "subject_id": sub.id,
            "class_a": ca.id, "class_b": cb.id,
            "teacher_id": teacher.id, "paper_id": paper.id,
            "a1": a1.id, "a2": a2.id, "b1": b1.id,
            "s1": s1.id, "s2": s2.id, "s3": s3.id,
            "n_a1": a1.username, "n_a2": a2.username, "n_b1": b1.username,
            "n_s1": s1.username, "n_s2": s2.username, "n_s3": s3.username,
        }
    finally:
        db.close()


# ============================================================
# 请求与查询辅助
# ============================================================
def make_client(token):
    """TestClient + Bearer 头。

    刻意**不用** `with TestClient(app)`：进入上下文会触发 lifespan，
    进而跑 `init_all`（整套种子数据 + 迁移 + Agent 预热）。那既慢又会把
    测试数据搅乱，而本文件只需要「表结构 + 我自己的数据」。
    """
    from fastapi.testclient import TestClient

    c = TestClient(app, raise_server_exceptions=False)
    c.headers.update({"Authorization": f"Bearer {token}"})
    return c


def new_paper(ids, name="单元测试试卷"):
    """每次下发都建一份新卷，避免 use_count / 可见性互相干扰。"""
    from sqlalchemy.orm import sessionmaker

    from app.models import Paper

    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        p = Paper(name=name, grade_id=ids["grade_id"], subject_id=ids["subject_id"],
                  creator_id=ids["teacher_id"], total_score=100, duration=60)
        db.add(p)
        db.commit()
        return p.id
    finally:
        db.close()


def post_task(client, ids, *, class_ids=None, student_ids=None, scheduled=False,
              label="case"):
    """发一次下发请求，返回 (status_code, body)。"""
    data = {
        "title": f"单元-{label}",
        "type": "homework",
        "paper_id": new_paper(ids),
        "class_ids": class_ids or [],
        "student_ids": student_ids or [],
    }
    if scheduled:
        data["publish_at"] = (now_local() + timedelta(hours=3)).strftime(
            "%Y-%m-%d %H:%M:%S")
    r = client.post("/api/v1/task/tasks", json=data)
    try:
        body = r.json()
    except ValueError:  # 非 JSON 响应
        body = {"_raw": r.text[:300]}
    return r.status_code, body


def snapshot():
    """全库计数快照。用于断言「失败的下发没有在库里留下任何东西」。"""
    from sqlalchemy import func, select
    from sqlalchemy.orm import sessionmaker

    from app.models import Notification, Task, TaskAssignment

    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        return {
            "task": db.scalar(select(func.count()).select_from(Task)),
            "asg_student": db.scalar(
                select(func.count()).select_from(TaskAssignment).where(
                    TaskAssignment.student_id.isnot(None))),
            "asg_class": db.scalar(
                select(func.count()).select_from(TaskAssignment).where(
                    TaskAssignment.class_id.isnot(None))),
            "noti": db.scalar(select(func.count()).select_from(Notification)),
        }
    finally:
        db.close()


def task_detail(task_id):
    """取某个任务的下发结果明细（只取标量，不返回 ORM 对象）。"""
    from sqlalchemy import func, select
    from sqlalchemy.orm import sessionmaker

    from app.models import Notification, TaskAssignment

    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        return {
            "asg_students": sorted(db.scalars(
                select(TaskAssignment.student_id).where(
                    TaskAssignment.task_id == task_id,
                    TaskAssignment.student_id.isnot(None))).all()),
            "asg_classes": sorted(db.scalars(
                select(TaskAssignment.class_id).where(
                    TaskAssignment.task_id == task_id,
                    TaskAssignment.class_id.isnot(None))).all()),
            "noti_users": sorted(db.scalars(
                select(Notification.user_id).where(
                    Notification.biz_type == "task",
                    Notification.biz_id == task_id)).all()),
            "noti_total": db.scalar(
                select(func.count()).select_from(Notification).where(
                    Notification.biz_type == "task",
                    Notification.biz_id == task_id)),
        }
    finally:
        db.close()


def noti_count_of(user_id):
    """某用户名下的通知总数（跨任务），用于证明「一处都没产生」。"""
    from sqlalchemy import func, select
    from sqlalchemy.orm import sessionmaker

    from app.models import Notification

    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        return db.scalar(select(func.count()).select_from(Notification).where(
            Notification.user_id == user_id))
    finally:
        db.close()


# ============================================================
# 一、指定学生为停用状态 → 报错，且双表零记录
# ============================================================
def case_disabled_student(ids, client):
    print("\n一、指定停用学生 → 报错，且 Notification / TaskAssignment 双表零记录")

    before = snapshot()
    sc, body = post_task(client, ids, student_ids=[ids["s2"]], label="disabled-only")
    after = snapshot()

    msg = str(body.get("message") or "")
    ok("① 请求被拒（HTTP 400，非 500/200）", sc == 400, f"status={sc} body={body}")
    ok("② 错误信息含学生账号名", ids["n_s2"] in msg, f"message={msg[:120]}")
    ok("③ 错误信息含学生 ID", f"ID={ids['s2']}" in msg, f"message={msg[:120]}")
    ok("④ 错误信息带状态中文标签「已停用」", "已停用" in msg, f"message={msg[:120]}")

    # 双表断言：只拦一处是最容易出现的半吊子修复，必须两张表都查。
    ok("⑤ Task 表零新增（校验失败不留脏任务）",
       after["task"] == before["task"], f"{before['task']} -> {after['task']}")
    ok("⑥ TaskAssignment 表零新增",
       after["asg_student"] == before["asg_student"],
       f"{before['asg_student']} -> {after['asg_student']}")
    ok("⑦ Notification 表零新增",
       after["noti"] == before["noti"], f"{before['noti']} -> {after['noti']}")
    ok("⑧ 该学生名下通知数仍为 0", noti_count_of(ids["s2"]) == 0,
       f"n={noti_count_of(ids['s2'])}")


# ============================================================
# 二、待审批（pending）同样按「不可用」拒绝，且标签正确
# ============================================================
def case_pending_student(ids, client):
    print("\n二、指定待审批学生 → 同样拒绝，标签区分「待审批」与「已停用」")

    sc, body = post_task(client, ids, student_ids=[ids["s3"]], label="pending-only")
    msg = str(body.get("message") or "")
    ok("① 被拒", sc == 400, f"status={sc}")
    ok("② 标签为「待审批」（不能一律写成「已停用」）",
       "待审批" in msg, f"message={msg[:120]}")
    # 注意：报错文案前缀本身就是「以下学生已停用或不可用」（涵盖两种状态），
    # 所以不能断言整条消息里没有「已停用」——那条断言会恒假。要判的是**括号里
    # 这个学生自己的标签**。
    ok("③ 括号内该生标签是「待审批」而非「已停用」",
       f"ID={ids['s3']}，待审批" in msg, f"message={msg[:120]}")


# ============================================================
# 三、多个不合规学生 → 一次列全（不是逐个报）
# ============================================================
def case_multiple_inactive(ids, client):
    print("\n三、多个不合规学生 → 一次报错列全，避免教师逐个重试")

    sc, body = post_task(client, ids, student_ids=[ids["s2"], ids["s3"]],
                         label="two-inactive")
    msg = str(body.get("message") or "")
    ok("① 被拒", sc == 400, f"status={sc}")
    ok("② 两个学生账号名都在同一条消息里",
       ids["n_s2"] in msg and ids["n_s3"] in msg, f"message={msg[:160]}")
    ok("③ 各自带各自的标签",
       "已停用" in msg and "待审批" in msg, f"message={msg[:160]}")
    ok("④ 是一个请求就列全（不是只报第一个）",
       msg.count("ID=") >= 2, f"ID 出现次数={msg.count('ID=')}")


# ============================================================
# 四、正常学生单发 → 通知与 assignment 都正常且同源
# ============================================================
def case_active_only(ids, client):
    print("\n四、正常学生单发 → 通知与 assignment 各 1 条且指向同一人")

    sc, body = post_task(client, ids, student_ids=[ids["s1"]], label="active-only")
    ok("① 下发成功（HTTP 200 + success）",
       sc == 200 and body.get("success") is True, f"status={sc} body={body}")

    tid = (body.get("data") or {}).get("id")
    ok("② 返回了 task_id", isinstance(tid, int) and tid > 0, f"task_id={tid}")
    if not isinstance(tid, int):
        return
    d = task_detail(tid)
    ok("③ 指定学生 assignment 恰好 1 条",
       d["asg_students"] == [ids["s1"]], f"asg_students={d['asg_students']}")
    ok("④ 通知恰好 1 条", d["noti_total"] == 1, f"noti_total={d['noti_total']}")
    ok("⑤ 通知与 assignment 同源（同一个学生）",
       d["asg_students"] == d["noti_users"], 
       f"asg={d['asg_students']} noti={d['noti_users']}")
    ok("⑥ 未传 class_ids 时无班级维度记录",
       d["asg_classes"] == [], f"asg_classes={d['asg_classes']}")


# ============================================================
# 五、2 班 + 1 指定学生 → 三类对象各归各位（跨班级混合下发）
# ============================================================
def case_two_classes_plus_one(ids, client):
    print("\n五、2 班 + 1 指定学生 → 班级 2 条 + 学生 1 条 + 通知 3 人")

    sc, body = post_task(client, ids, class_ids=[ids["class_a"], ids["class_b"]],
                         student_ids=[ids["s1"]], label="2class+1student")
    ok("① 下发成功（修复未波及这条路径）",
       sc == 200 and body.get("success") is True, f"status={sc} body={body}")

    tid = (body.get("data") or {}).get("id")
    if not isinstance(tid, int):
        ok("② 返回了 task_id", False, f"task_id={tid}")
        return
    d = task_detail(tid)

    ok("② 班级 assignment 恰好 2 条",
       d["asg_classes"] == sorted([ids["class_a"], ids["class_b"]]),
       f"asg_classes={d['asg_classes']}")
    ok("③ 指定学生 assignment 恰好 1 条",
       d["asg_students"] == [ids["s1"]], f"asg_students={d['asg_students']}")

    # 通知集合 = A班 active + B班 active + 指定学生
    expect = sorted([ids["a1"], ids["b1"], ids["s1"]])
    ok("④ 通知对象 = A班active + B班active + 指定学生",
       d["noti_users"] == expect, f"got={d['noti_users']} expected={expect}")

    # 刻意的不对称：班级里的停用学生不收到通知，但班级 assignment 照样存在
    # （按班级粒度覆盖他，恢复账号后能看到历史作业）。这是设计，不是缺陷。
    ok("⑤ 班级内的停用学生未收到通知（原有正确行为）",
       ids["a2"] not in d["noti_users"], f"a2={ids['a2']} noti={d['noti_users']}")
    ok("⑥ 但班级 assignment 仍覆盖该班（恢复账号后可见历史作业）",
       ids["class_a"] in d["asg_classes"],
       f"asg_classes={d['asg_classes']}（本行锁的是「班级粒度下发」这一事实，"
       f"不要改成断言 asg_students 含 a2）")
    ok("⑦ 班级路径未改成报错（停用学生不该让整单失败）",
       sc == 200, f"status={sc}")
    ok("⑧ 停用学生名下通知数仍为 0", noti_count_of(ids["a2"]) == 0,
       f"n={noti_count_of(ids['a2'])}")


# ============================================================
# 六、定时发布（草稿）路径同样被拦
# ============================================================
def case_scheduled(ids, client):
    print("\n六、定时发布路径同样被拦（校验点在 scheduled 分支 return 之前）")

    before = snapshot()
    sc, body = post_task(client, ids, student_ids=[ids["s2"]], scheduled=True,
                         label="disabled-scheduled")
    after = snapshot()
    msg = str(body.get("message") or "")

    ok("① 定时发布同样被拒（不留「建时放行、到期才发现」的延迟失败）",
       sc == 400, f"status={sc} body={body}")
    ok("② 错误信息含学生账号名", ids["n_s2"] in msg, f"message={msg[:120]}")
    ok("③ 未落草稿 Task 行",
       after["task"] == before["task"], f"{before['task']} -> {after['task']}")
    ok("④ 未落任何 assignment/通知",
       after["asg_student"] == before["asg_student"]
       and after["asg_class"] == before["asg_class"]
       and after["noti"] == before["noti"],
       f"asg_stu {before['asg_student']}->{after['asg_student']}, "
       f"asg_cls {before['asg_class']}->{after['asg_class']}, "
       f"noti {before['noti']}->{after['noti']}")


# ============================================================
# 七、既有语义不得改变：不存在的学生仍报「不存在」
# ============================================================
def case_ghost_student(ids, client):
    print("\n七、不存在的学生 ID → 原提示「不存在」未被改成「已停用」")

    sc, body = post_task(client, ids, student_ids=[9_999_999], label="ghost")
    msg = str(body.get("message") or "")
    ok("① 被拒", sc == 400, f"status={sc}")
    ok("② 提示仍是「不存在」，没有滑到状态分支",
       "不存在" in msg and "已停用" not in msg, f"message={msg[:120]}")


# ============================================================
# 八、混合场景：班级 + 停用指定学生 → 整体回滚，且错误不牵连班级
# ============================================================
def case_mixed_reject(ids, client):
    print("\n八、2 班 + 停用指定学生 → 整体拒绝并回滚，错误只指向该指定学生")

    before = snapshot()
    sc, body = post_task(client, ids, class_ids=[ids["class_a"], ids["class_b"]],
                         student_ids=[ids["s2"]], label="2class+disabled")
    after = snapshot()
    msg = str(body.get("message") or "")

    ok("① 整体被拒", sc == 400, f"status={sc}")
    ok("② 错误指向停用的指定学生", ids["n_s2"] in msg, f"message={msg[:140]}")
    # 先断言消息确实是「拒绝」而不是「成功」——否则「不含 a1/b1」会因为在
    # 一条成功消息里当然不出现而恒真（反控实测：不加这行，本条在修复前的
    # 版本上照样通过，属于假绿）。
    ok("③ 消息是拒绝文案，不是成功回执", "无法下发" in msg, f"message={msg[:140]}")
    ok("④ 未把班级里的正常学生一起列进错误（两类对象不混报）",
       ids["n_a1"] not in msg and ids["n_b1"] not in msg, f"message={msg[:140]}")
    ok("⑤ 全部回滚：四张表计数均未变",
       after == before, f"{before} -> {after}")


def main():
    print("=" * 72)
    print("离线单元回归：任务下发对象状态校验（指定学生 vs 班级）")
    print(f"锁定的修复：{_FIXED}")
    print("=" * 72)

    ids = seed()
    token = create_access_token(ids["teacher_id"], role="teacher")
    client = make_client(token)

    # 冒烟：先确认鉴权链路本身通了，否则后面所有 400 都可能是「没权限」
    # 而不是「学生状态不合规」，会把断言全部伪装成假绿。
    sc, body = post_task(client, ids, student_ids=[ids["s1"]], label="smoke")
    if sc != 200:
        print(f"\n[中止] 冒烟下发失败，鉴权/环境异常，后续断言无意义："
              f"status={sc} body={body}")
        return 1
    print("\n[冒烟] 正常下发返回 200，鉴权链路就绪")

    case_disabled_student(ids, client)
    case_pending_student(ids, client)
    case_multiple_inactive(ids, client)
    case_active_only(ids, client)
    case_two_classes_plus_one(ids, client)
    case_scheduled(ids, client)
    case_ghost_student(ids, client)
    case_mixed_reject(ids, client)

    print("\n" + "-" * 72)
    total = _PASSED + len(_FAILED)
    print(f"checked={total} passed={_PASSED} failed={len(_FAILED)}")
    if _FAILED:
        print("失败项：")
        for n in _FAILED:
            print(f"  ✘ {n}")
        print(f"\n提示：这些断言锁定的是 {_FIXED}。若刚回退了该 commit，"
              f"请确认是有意为之。")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
