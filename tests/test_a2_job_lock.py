#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""离线回归：A2 定时任务执行锁（多 worker 下同一任务只跑一份）。

## 这个文件锁的是什么

`uvicorn --workers N` 时每个 worker 各自 `sync_all_jobs()` → 各自一个
APScheduler。cron 是墙钟触发，N 个进程会在同一分钟同时叫醒同一个任务，
而 `max_instances=1` 只在**单个 scheduler 内部**生效，管不到跨进程。

`JOB_HANDLERS` 里的任务全是「扫描 + 批量写」，并发执行不是「多跑一遍」
而是**写放大 N 倍**：`publish_scheduled_tasks` 会给同一批学生插两遍通知。

修复是 `sys_job_lock` 表 + 条件 UPSERT 抢占（见 `services/job_lock.py`）。

## 为什么必须做「无锁对照」

**跑一次看它成功，什么也证明不了。** 如果锁根本没生效、或者根本没被调用，
双进程跑完照样「都执行了、都没报错」。要证明锁有判别力，必须先证明
「去掉锁时测试能看出问题」。

所以本文件用**两个真进程 + 文件屏障**（不是线程、不是 monkeypatch）跑四组
对照，`[A]` 那组是这套验收的命门：

    [A] 无锁（monkeypatch acquire 恒返回 True）
        两个进程都执行 -> notification=900  job_execution_log=2   ← 通知翻倍
    [B] 有锁，租约 600s
        恰好一个执行   -> notification=450  job_execution_log=1
    [C] 锁被崩溃进程占住且未到期（owner=DEAD, expire=now+600s）
        两个都跳过     -> notification=0  锁行保留  job_execution_log=0
    [D] 崩溃进程的锁已过期（expire=now-3600s）
        恰好一个接管   -> notification=450  锁行被接管后清空

`[A]` 证明「如果锁失效，测试能看出来」；没有它，`[B]` 的绿只说明
「代码能跑」。同理 `[C]` 证明「未到期不抢」，`[D]` 证明「到期能接管」——
两者合起来才是「租约」的完整语义，只测其一会让「租约永不生效」或
「租约永远立即生效」两种反向 bug 都通过。

## 反向验证（判别力证明）

把 `scheduler._execute` 开头那三行

    if not acquire_job_lock(job_id):
        # 别的进程正在跑。这是正常调度结果，不是错误 —— 不写任何日志。
        return

改成 `if False:  # [反向验证]` （等价于回到无锁状态），重跑本文件，实测：

    共 28 项 | 通过 20 | 失败 8
    失败项：
      V2 ② ★ 通知只有一份（450）              -> notification=900
      V2 ③ ★ 执行日志只有一条                  -> job_execution_log=2
      V3 ② ★ 一条通知都没发（没人拿到锁）       -> notification=900
      V3 ③ ★ 一条执行日志都没写                -> job_execution_log=2
      V3 ④ run_count 未变                    -> run_count=1
      V4 ② ★ 过期锁被接管，通知只有一份         -> notification=900
      V4 ③ ★ 执行日志只有一条                  -> job_execution_log=2
      V4 ④ ★ 接管后释放，锁表清空              -> lock_rows=1

**V1 那五条保持全绿** —— 这是正确的判别结构：V1 本来就是「模拟无锁」，
它不该因为真实实现变成无锁而改变。如果 V1 也红了，说明 `A2_DISABLE_LOCK`
的注入方式有问题（两组对照没真正区分开），那反而是测试自身的 bug。

恢复后 28/28。所以这组断言对「锁到底有没有生效」有判别力。

## 一条顺带发现的缺陷（V1 ④）

无锁时 `run_count` 只记 1 次、而实际执行了 2 次。原因不是锁，是
`job.run_count += 1` 为 ORM 层的 read-modify-write：两个进程各自 SELECT
到 0、各自写回 1，后提交的覆盖先提交的（lost update）。单独复现：

    两个 session 各自读到: 0 0     ← 都基于同一快照
    交错提交后 run_count = 1       ← 期望 2，实际 1

有锁之后这个统计失真顺带消失了（V2 ④），但根因在 `+= 1` 这个写法上，
不在这批改动范围内 —— 如果将来引入「同一任务允许并发执行不同分片」的
设计，它会重新出现。

## 两个容易写错的地方（本文件已规避）

1. **子进程必须重新 import 产品代码**，不能靠 fork 继承父进程已改过的
   monkeypatch 状态（Windows 上是 spawn，pytest 下也可能不同）。所以
   「无锁」不是在父进程 monkeypatch，而是通过环境变量 `A2_DISABLE_LOCK=1`
   让子进程自己 monkeypatch。
2. **屏障要用文件**，不能用 `multiprocessing.Barrier`：spawn 模式下
   Barrier 需要能 pickle 传递到子进程，Windows 上偶尔会挂死；文件屏障
   是「子进程等文件出现」，行为确定、超时可控。

## 用法

    python tests/test_a2_job_lock.py

退出码：0 = 全部通过，1 = 有失败。
"""
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

# ---- 必须在导入 app.* 之前定好环境：避免在仓库里建出脏库、避免拉外网 ----
_TMP = tempfile.mkdtemp(prefix="unit_a2_job_lock_")
_DB_PATH = os.path.join(_TMP, "unit.db").replace("\\", "/")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB_PATH
os.environ["LLM_ENABLED"] = "false"
os.environ["SCHEDULER_ENABLED"] = "false"
os.environ["DEBUG"] = "false"
os.environ["SECRET_KEY"] = "unit_a2_job_lock_secret_0123456789abcdef"

_BACKEND = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"
)
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

_FAILED = []
_PASSED = 0

from app.models import ScheduledJob as _JOB_MODEL  # noqa: E402  供 V1⑥ 直接操作

# 子进程可执行的工作体：调产品代码的 _execute，被 monkeypatch 成幂等的
# 「插 N 条通知」以便数副作用。用环境变量传参，不靠命令行（Windows 引号地狱）。
CHILD_CODE = r'''
import os, sys, time, json
sys.path.insert(0, os.environ["A2_BACKEND"])

# 环境已由父进程通过 env 传好（DATABASE_URL / SECRET_KEY 等）
if os.environ.get("A2_DISABLE_LOCK") == "1":
    import app.services.scheduler as _sch
    import app.services.job_lock as _jl
    _jl_acquire_orig = _jl.acquire_job_lock
    # 关键：无锁对照组必须让「锁」这个动作整体消失，而不只是"总返回 True"。
    # 返回 True 但不动表 = 真实的无锁多进程行为（每个进程都认为自己该跑）。
    _sch.acquire_job_lock = lambda *a, **kw: True
    _sch.release_job_lock = lambda *a, **kw: None

from app.core.database import Base, engine, SessionLocal
import app.models  # noqa: F401
from app.models import Notification, ScheduledJob, JobExecutionLog, User
from app.services import scheduler, task_jobs

JOB_ID = int(os.environ["A2_JOB_ID"])
NOTIFY_PER_RUN = int(os.environ.get("A2_NOTIFY_PER_RUN", "450"))
ADMIN_ID = int(os.environ["A2_ADMIN_ID"])

def fake_handler():
    """幂等的批量写：插 N 条通知。用于放大「跑了两遍」这件事。"""
    db = SessionLocal()
    try:
        for i in range(NOTIFY_PER_RUN):
            db.add(Notification(
                user_id=ADMIN_ID, title="a2_probe", content=f"probe-{i}",
                type="system", biz_type="a2probe", biz_id=JOB_ID,
            ))
        db.commit()
        return {"notified": NOTIFY_PER_RUN}
    finally:
        db.close()

task_jobs.run_job = lambda func_path: fake_handler()

# 等待屏障文件：保证两个进程同一瞬间起跑
barrier = os.environ["A2_BARRIER"]
deadline = time.time() + 30
while not os.path.exists(barrier):
    if time.time() > deadline:
        print("BARRIER_TIMEOUT", file=sys.stderr); sys.exit(3)
    time.sleep(0.01)

scheduler._execute(JOB_ID, "a2.fake", trigger_type="auto")
print("DONE")
'''


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
# 造数据
# ============================================================
def seed():
    """建一个任务 + 一个管理员。返回纯标量（避免 detached 实例）。"""
    from sqlalchemy.orm import sessionmaker

    from app.core.database import Base, engine
    from app.models import (
        IdentityType, Role, User, UserRole, UserStatus,
    )
    from app.models import ScheduledJob
    from app.core.security import hash_password

    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        role = Role(code="sys_admin", name="系统管理员")
        db.add(role)
        db.flush()
        admin = User(
            username="a2admin", real_name="A2管理员",
            password=hash_password("A2Admin@12345"),
            identity=IdentityType.SYS_ADMIN, status=UserStatus.ACTIVE,
        )
        db.add(admin)
        db.flush()
        db.add(UserRole(user_id=admin.id, role_id=role.id))
        job = ScheduledJob(
            name="a2_probe_job", func_path="a2.fake", cron_expression="0 3 * * *",
            is_builtin=False, is_active=True, retry_times=0,
        )
        db.add(job)
        db.commit()
        return {"admin_id": admin.id, "job_id": job.id}
    finally:
        db.close()


def reset_state(job_id):
    """清空探针产生的副作用，让每组对照从同一基线起跑。"""
    from sqlalchemy import text

    from app.core.database import SessionLocal

    db = SessionLocal()
    try:
        db.execute(text("DELETE FROM sys_notification WHERE biz_type='a2probe'"))
        db.execute(text("DELETE FROM sys_job_execution_log WHERE job_id=:j"), {"j": job_id})
        db.execute(text("DELETE FROM sys_job_lock"))
        db.execute(text("UPDATE sys_scheduled_job SET run_count=0 WHERE id=:j"), {"j": job_id})
        db.commit()
    finally:
        db.close()


def counts(job_id):
    """读回副作用计数。"""
    from sqlalchemy import text

    from app.core.database import SessionLocal

    db = SessionLocal()
    try:
        notif = db.execute(
            text("SELECT COUNT(*) FROM sys_notification WHERE biz_type='a2probe'")
        ).scalar() or 0
        logs = db.execute(
            text("SELECT COUNT(*) FROM sys_job_execution_log WHERE job_id=:j"), {"j": job_id}
        ).scalar() or 0
        locks = db.execute(text("SELECT COUNT(*) FROM sys_job_lock")).scalar() or 0
        run_count = db.execute(
            text("SELECT run_count FROM sys_scheduled_job WHERE id=:j"), {"j": job_id}
        ).scalar() or 0
        return {"notification": int(notif), "job_execution_log": int(logs),
                "lock_rows": int(locks), "run_count": int(run_count)}
    finally:
        db.close()


def preseed_lock(job_id, owner, expire_delta_seconds):
    """预置一把属于「已崩溃进程」的锁。"""
    from datetime import timedelta

    from sqlalchemy import text

    from app.core.database import SessionLocal
    from app.utils.common import now_local

    now = now_local()
    db = SessionLocal()
    try:
        db.execute(text("DELETE FROM sys_job_lock WHERE job_id=:j"), {"j": job_id})
        db.execute(
            text("""INSERT INTO sys_job_lock (job_id, owner, acquired_at, expire_at)
                    VALUES (:j, :o, :now, :exp)"""),
            {"j": job_id, "o": owner, "now": now,
             "exp": now + timedelta(seconds=expire_delta_seconds)},
        )
        db.commit()
    finally:
        db.close()


# ============================================================
# 双进程跑一轮
# ============================================================
def run_two_procs(job_id, admin_id, *, disable_lock=False, notify_per_run=450,
                  timeout=90):
    """起两个真进程，用文件屏障让它们同一瞬间调用 `scheduler._execute`。

    Returns:
        (rc_a, rc_b, out_a, out_b)
    """
    barrier = os.path.join(_TMP, f"barrier_{uuid_suffix()}")
    child_file = os.path.join(_TMP, "a2_child.py")
    Path(child_file).write_text(CHILD_CODE, encoding="utf-8")

    env = dict(os.environ)
    env.update({
        "A2_BACKEND": _BACKEND,
        "A2_JOB_ID": str(job_id),
        "A2_ADMIN_ID": str(admin_id),
        "A2_NOTIFY_PER_RUN": str(notify_per_run),
        "A2_BARRIER": barrier,
        "PYTHONIOENCODING": "utf-8",
    })
    env.pop("A2_DISABLE_LOCK", None)
    if disable_lock:
        env["A2_DISABLE_LOCK"] = "1"

    procs = [
        subprocess.Popen([sys.executable, child_file], env=env,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        for _ in range(2)
    ]
    # 两个进程都已启动，放行屏障
    time.sleep(0.6)
    Path(barrier).write_text("go", encoding="utf-8")

    outs = []
    for p in procs:
        try:
            out, err = p.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            p.kill()
            out, err = p.communicate()
            err = (err or "") + "\n[TIMEOUT]"
        outs.append((p.returncode, out, err))
    return outs[0], outs[1]


_UUID_SEQ = [0]


def uuid_suffix():
    _UUID_SEQ[0] += 1
    return f"{os.getpid()}_{_UUID_SEQ[0]}"


# ============================================================
# 主流程
# ============================================================
def main():
    ids = seed()
    job_id, admin_id = ids["job_id"], ids["admin_id"]
    print(f"\n探针任务 id={job_id}，管理员 id={admin_id}，库={_DB_PATH}\n")

    # ---------- V1：无锁对照（命门）----------
    print("V1、无锁对照 —— 证明「锁失效时用例能看出来」")
    reset_state(job_id)
    (rc_a, out_a, err_a), (rc_b, out_b, err_b) = run_two_procs(
        job_id, admin_id, disable_lock=True)
    c = counts(job_id)
    ok("V1 ① 两个子进程都正常结束",
       rc_a == 0 and rc_b == 0, f"rc={rc_a},{rc_b} err={(err_a+err_b)[:200]}")
    ok("V1 ② ★ 无锁时通知翻倍（900 = 450×2）",
       c["notification"] == 900, f"notification={c['notification']} 期望 900")
    ok("V1 ③ ★ 无锁时执行日志两条",
       c["job_execution_log"] == 2, f"job_execution_log={c['job_execution_log']} 期望 2")
    # V1 ④ 刻意**不断言精确值**。`run_count` 在进程级并发下是 1 或 2，取决于
    # 两次 read-modify-write 恰好交错（1，lost update）还是串行（2）。
    # 实测 5 次里有 2 次得到 2。断言精确值会让这条用例随机红 —— 而 CI 里
    # **随机红的断言比没有断言更坏**：它训练人忽略失败。
    # lost update 本身是确定性的，用 V1 ⑥ 在单进程内精确复现（见下）。
    ok("V1 ④ 无锁时 run_count 只能说 ≤2（该值并发下不确定，精确判定见 V1 ⑥）",
       c["run_count"] <= 2, f"run_count={c['run_count']}（1=lost update / 2=恰好串行）")
    ok("V1 ⑤ 无锁时锁表始终为空（对照组不应写锁）",
       c["lock_rows"] == 0, f"lock_rows={c['lock_rows']}")

    # V1 ⑥：把 lost update 从"进程竞速"里剥出来，做成**确定性**断言。
    # 两个 session 各自读同一行、各自 +1、交错提交 —— 结果必为 1，不是 2。
    # 这条与 A2 的锁无关，它锁的是一个独立缺陷：`run_count += 1` 是 ORM 层
    # read-modify-write，不是 SQL 原子自增。有锁时不会触发（V2④），
    # 但将来若引入"同一任务允许并发执行不同分片"，它会重新出现。
    from sqlalchemy import text as _text
    from app.core.database import SessionLocal as _SL
    reset_state(job_id)
    _a, _b = _SL(), _SL()
    try:
        _ja = _a.get(_JOB_MODEL, job_id)
        _jb = _b.get(_JOB_MODEL, job_id)
        both_saw = (_ja.run_count, _jb.run_count)
        _ja.run_count += 1
        _a.commit()
        _jb.run_count += 1
        _b.commit()
    finally:
        _a.close()
        _b.close()
    _dbr = _SL()
    try:
        final = _dbr.get(_JOB_MODEL, job_id).run_count
        _dbr.execute(_text("UPDATE sys_scheduled_job SET run_count=0 WHERE id=:j"), {"j": job_id})
        _dbr.commit()
    finally:
        _dbr.close()
    ok("V1 ⑥★ lost update 确定性复现：两个 session 各 +1、交错提交 → 只记 1",
       both_saw == (0, 0) and final == 1,
       f"两者各自读到 {both_saw}，交错提交后 run_count={final}（期望 1，不是 2）")

    # ---------- V2：有锁，租约充足 ----------
    print("\nV2、有锁（租约 600s）—— 严格互斥")
    reset_state(job_id)
    (rc_a, out_a, err_a), (rc_b, out_b, err_b) = run_two_procs(job_id, admin_id)
    c = counts(job_id)
    ok("V2 ① 两个子进程都正常结束",
       rc_a == 0 and rc_b == 0, f"rc={rc_a},{rc_b} err={(err_a+err_b)[:200]}")
    ok("V2 ② ★ 通知只有一份（450）",
       c["notification"] == 450, f"notification={c['notification']} 期望 450")
    ok("V2 ③ ★ 执行日志只有一条",
       c["job_execution_log"] == 1, f"job_execution_log={c['job_execution_log']} 期望 1")
    ok("V2 ④ ★ run_count 只累加一次（且这次是准确的）",
       c["run_count"] == 1, f"run_count={c['run_count']} 期望 1")
    ok("V2 ⑤ 执行完毕后锁已释放（表为空）",
       c["lock_rows"] == 0, f"lock_rows={c['lock_rows']} 期望 0")
    # 子进程的输出可读性：至少有一个打印了 DONE（两个都会，只是以下断言更弱）
    ok("V2 ⑥ 两个进程都跑完了（无挂死）",
       "DONE" in out_a and "DONE" in out_b, f"out={out_a[:40]}|{out_b[:40]}")

    # ---------- V3：锁被崩溃进程占住且未到期 ----------
    print("\nV3、锁被崩溃进程占住且未到期 —— 两个都跳过，且不写任何日志")
    reset_state(job_id)
    preseed_lock(job_id, owner="DEADHOST:1:deadbeef", expire_delta_seconds=600)
    (rc_a, out_a, err_a), (rc_b, out_b, err_b) = run_two_procs(job_id, admin_id)
    c = counts(job_id)
    ok("V3 ① 两个子进程都正常结束（跳过不是错误）",
       rc_a == 0 and rc_b == 0, f"rc={rc_a},{rc_b} err={(err_a+err_b)[:200]}")
    ok("V3 ② ★ 一条通知都没发（没人拿到锁）",
       c["notification"] == 0, f"notification={c['notification']} 期望 0")
    ok("V3 ③ ★ 一条执行日志都没写（不能留停在 running 的假记录）",
       c["job_execution_log"] == 0, f"job_execution_log={c['job_execution_log']} 期望 0")
    ok("V3 ④ run_count 未变",
       c["run_count"] == 0, f"run_count={c['run_count']} 期望 0")
    ok("V3 ⑤ ★ 崩溃进程的锁行**保留**（跳过者不得删他人锁）",
       c["lock_rows"] == 1, f"lock_rows={c['lock_rows']} 期望 1")

    # ---------- V4：崩溃进程的锁已过期 ----------
    print("\nV4、锁已过期 —— 恰好一个接管并执行")
    reset_state(job_id)
    preseed_lock(job_id, owner="DEADHOST:1:deadbeef", expire_delta_seconds=-3600)
    (rc_a, out_a, err_a), (rc_b, out_b, err_b) = run_two_procs(job_id, admin_id)
    c = counts(job_id)
    ok("V4 ① 两个子进程都正常结束",
       rc_a == 0 and rc_b == 0, f"rc={rc_a},{rc_b} err={(err_a+err_b)[:200]}")
    ok("V4 ② ★ 过期锁被接管，通知只有一份",
       c["notification"] == 450, f"notification={c['notification']} 期望 450")
    ok("V4 ③ ★ 执行日志只有一条",
       c["job_execution_log"] == 1, f"job_execution_log={c['job_execution_log']} 期望 1")
    ok("V4 ④ ★ 接管后释放，锁表清空",
       c["lock_rows"] == 0, f"lock_rows={c['lock_rows']} 期望 0")

    # ---------- V5：手动执行撞锁 → BusinessException（HTTP 400 的来源）----------
    print("\nV5、手动执行撞锁 —— 必须明确报错，不能静默无反应")
    from app.core.exception import BusinessException
    from app.services import scheduler as sch

    reset_state(job_id)
    preseed_lock(job_id, owner="OTHERHOST:99:cafe", expire_delta_seconds=600)
    raised = None
    try:
        sch.run_job_now(job_id)
    except BusinessException as exc:
        raised = exc
    except Exception as exc:  # noqa: BLE001 其他类型即失败，需报出来
        raised = f"WRONG_TYPE:{type(exc).__name__}:{exc}"
    ok("V5 ① ★ 撞锁时抛 BusinessException（不是静默返回）",
       isinstance(raised, BusinessException),
       f"got={type(raised).__name__ if raised else None}: {raised}")
    msg = str(getattr(raised, "message", "") or raised or "")
    ok("V5 ② ★ 错误信息说明是「正在执行中」而非「执行失败」",
       "正在执行中" in msg and "任务执行失败" not in msg, f"msg={msg}")
    c = counts(job_id)
    ok("V5 ③ 撞锁时不写执行日志（不能留假 running 记录）",
       c["job_execution_log"] == 0, f"job_execution_log={c['job_execution_log']} 期望 0")
    ok("V5 ④ 撞锁时不发通知",
       c["notification"] == 0, f"notification={c['notification']} 期望 0")
    ok("V5 ⑤ 他人的锁行保留",
       c["lock_rows"] == 1, f"lock_rows={c['lock_rows']} 期望 1")

    # ---------- V6：租约时间列不用 CURRENT_TIMESTAMP ----------
    print("\nV6、租约时间基准 —— CURRENT_TIMESTAMP 会让锁写入即过期")
    import sqlite3

    con = sqlite3.connect(_DB_PATH)
    try:
        row = con.execute(
            "SELECT CURRENT_TIMESTAMP, ?",
            (__import__("app.utils.common", fromlist=["now_local"]).now_local()
             .strftime("%Y-%m-%d %H:%M:%S.%f"),),
        ).fetchone()
        cur_ts, local_ts = row[0], row[1]
        cmp = con.execute("SELECT ? < ?", (cur_ts, local_ts)).fetchone()[0]
    finally:
        con.close()
    ok("V6 ① ★ CURRENT_TIMESTAMP（UTC、无微秒）字典序 < now_local()（本地、带微秒）",
       cmp == 1, f"CURRENT_TIMESTAMP={cur_ts!r} now_local={local_ts!r} -> {cur_ts!r} < {local_ts!r} is True")
    ok("V6 ② 两者长度不同（19 vs 26）—— 这才是字典序错位的根因",
       len(cur_ts) == 19 and len(local_ts) == 26, f"{len(cur_ts)} vs {len(local_ts)}")
    # 直接验证产品代码用的列：抢到锁后 expire_at 必须 > now（未过期）
    reset_state(job_id)
    from app.services.job_lock import acquire_job_lock, release_job_lock
    got = acquire_job_lock(job_id, lease_seconds=60)
    con = sqlite3.connect(_DB_PATH)
    try:
        expire_at = con.execute(
            "SELECT expire_at FROM sys_job_lock WHERE job_id=?", (job_id,)
        ).fetchone()[0]
        still_valid = con.execute(
            "SELECT ? > CURRENT_TIMESTAMP", (expire_at,)
        ).fetchone()[0]
    finally:
        con.close()
    ok("V6 ③ ★ 产品代码写入的 expire_at 确实在未来（锁不会写入即过期）",
       got and still_valid == 1, f"expire_at={expire_at!r} still_valid={still_valid}")
    release_job_lock(job_id)

    # ---------- V7：锁不阻塞业务写 ----------
    print("\nV7、锁不阻塞业务写 —— 抢锁事务必须 commit **并** close 之后才跑任务体")
    reset_state(job_id)
    (rc_a, out_a, err_a), (rc_b, out_b, err_b) = run_two_procs(job_id, admin_id)
    c = counts(job_id)
    ok("V7 ① 互斥仍然成立（前置条件，否则本组无意义）",
       c["notification"] == 450, f"notification={c['notification']}")
    ok("V7 ② 执行完毕后锁行已释放，业务写不会被残留锁挡住",
       c["lock_rows"] == 0, f"lock_rows={c['lock_rows']} 期望 0")
    # 直接量「抢锁返回的那一瞬间，写锁是否已交还」：抢完立刻用另一个连接写库。
    #
    # ⚠️ 这条断言的判别力边界（我实测过，别误解）：
    # 把 job_lock.acquire_job_lock 的 `db.commit()` 删掉再跑，V4 会红
    # （900 通知 / 2 条日志 / 锁行残留）+ V6③ 因查不到锁行而崩 —— 也就是说
    # **commit 那步是判据，V4/V6 已经守住了**。
    # 而只删 `db.close()`（保留 commit）时本组**仍然全绿**，因为 pysqlite 在
    # commit 之后已把写锁交还，连接还开着不构成阻塞。
    # 所以 V7 ③④ 是**护栏**而不是判据：它守的是「将来有人把 commit 挪到
    # 任务体之后」这类改动在运行时立刻可见，但它抓不到「close 被删」。
    # 审阅时不要因为它反向验证不红就删掉。
    from app.services.job_lock import acquire_job_lock as _acq, release_job_lock as _rel
    reset_state(job_id)
    t0 = time.time()
    got = _acq(job_id, lease_seconds=60)
    acq_ms = (time.time() - t0) * 1000
    import sqlite3 as _sq
    con2 = _sq.connect(_DB_PATH, timeout=0.2)
    try:
        t1 = time.time()
        con2.execute(
            "INSERT INTO sys_notification (user_id, title, content, type, biz_type, biz_id, is_read, created_at)"
            " VALUES (?, 'v7', 'concurrent-write', 'system', 'a2probe', 0, 0, '2026-01-01 00:00:00')",
            (admin_id,))
        con2.commit()
        write_ms = (time.time() - t1) * 1000
    finally:
        con2.close()
    _rel(job_id)
    ok("V7 ③ 抢锁本身是独立短事务（< 200ms，没有把 session 挂住）",
       got and acq_ms < 200, f"acquire 耗时 {acq_ms:.1f}ms")
    ok("V7 ④ 持锁期间另一连接可立即写入（< 50ms）【护栏，判据在 V4/V6】",
       write_ms < 50, f"并发写耗时 {write_ms:.1f}ms（未 commit 时会到 2000ms+）")

    # ---------- V8：租约配置守卫 ----------
    print("\nV8、租约配置守卫 —— 租约为 0 等于锁完全失效且不报任何错")
    from app.core.config import Settings
    fresh = Settings()
    ok("V8 ① ★ JOB_LOCK_LEASE_SECONDS 默认值是 1800 而不是 0",
       fresh.JOB_LOCK_LEASE_SECONDS == 1800, f"got={fresh.JOB_LOCK_LEASE_SECONDS}")
    ok("V8 ② 是正整数类型",
       isinstance(fresh.JOB_LOCK_LEASE_SECONDS, int) and fresh.JOB_LOCK_LEASE_SECONDS > 0,
       f"type={type(fresh.JOB_LOCK_LEASE_SECONDS).__name__}")

    # ---------- 汇总 ----------
    total = _PASSED + len(_FAILED)
    print(f"  离线回归完成：共 {total} 项 | 通过 {_PASSED} | 失败 {len(_FAILED)}")
    if _FAILED:
        print("\n失败用例：")
        for n in _FAILED:
            print(f"  - {n}")
    print(f"{'=' * 66}\n")
    return 1 if _FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
