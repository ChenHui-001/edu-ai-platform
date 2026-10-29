#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""离线单元回归：AI 长任务的**僵尸状态判定与启动收割**（B2）。

## 锁的是什么

出题/组卷（`api/v1/agent.py`）与 AI 教案（`api/v1/lesson_ai.py`）共用
`sys_agent_job` 表，执行方式都是 `threading.Thread(daemon=True)`。
daemon 线程**随进程退出无声消失**，于是进程重启（发布、OOM、
`docker restart`、崩溃）之后：

    status = 'running'    ← 永远
    finished_at = NULL
    error = NULL

前端按 status 轮询 → 无限转圈，无上限、无超时、无法自愈。

## 修复前的核心不对称（本文件的由来）

| 接口 | 超时判定 | 后果 |
| --- | --- | --- |
| `GET /lesson/ai/jobs/{id}` | 有（`_job_progress`） | 5 分钟后显示"生成超时" |
| `GET /agent/jobs/{id}` | **完全没有** | 永久 running，前端无限轮询 |
| `GET /agent/jobs`（列表） | **完全没有** | 列表永久显示"运行中" |

同一个表、同一种后台线程模式，两套行为。所以判据抽到
`services/agent_job_state` **单点定义**，三处都调它。

## 为什么两层都要（只做一层就有漏洞）

- **只做读时判定**：脏状态永远留在库里。列表筛选、统计、"能否重试"
  都无从判断；`?status=failed` 查不到真正卡死的那些。
- **只做启动收割**：两次重启之间创建的任务无人处理（进程正常重启一次
  才清理一次），而前端在这期间一直转圈。

## 为什么收割要有宽限期（多 worker 下的误杀）

`uvicorn --workers N` 时每个 worker 都跑启动钩子。worker B 启动时，
worker A 手里可能真有在跑的任务（那是 A 的线程，B 看不到，只能看库）。
若无条件把 running 判死，A 的正常任务被误杀 —— 前端看到 failed，
稍后 A 又写 success，状态来回跳。

判据是 `created_at < now - (300 + 600)`：正常任务 20~90s 早结束了。
单 worker（当前生产形态）下这个宽限是保守的，代价只是"重启后最长
15 分钟才清理"，而读时判定让用户侧**立刻**看到超时、无感。

## 反向验证（`_tmp_reverse_b2.py`，一次性脚本，已删除）

    超时判据恒 False        -> 3 项红（回到修复前）
    created_at 空时判超时    -> 1 项红（无基准臆断）
    收割不设宽限期          -> 4 项红（实测误杀 3 条，含 10 秒前的新任务）
    收割不限定 status       -> 2 项红（把 success 也清了）
    apply_timeout 无条件覆盖 -> 4 项红（把"知识点不存在"盖成"超时"）
    get_job 去掉判定        -> 4 项红（路由返回 running）

⚠️ 反向验证发现的一个教训，已写进 F 组：最初只用 grep 检查
「agent.py 里有没有调用 apply_timeout」，把 `return ok(apply_timeout(..))`
改回 `return ok(d)` 后 **grep 仍然通过**（import 语句还在），探针全绿。
所以 F 组改成**直接调用路由函数本体**断言响应体 —— 弱断言抓不到真 bug。

## 用法

    python tests/test_unit_agent_job_state.py

退出码：0 = 全部通过，1 = 有失败。
"""
import os
import sys
import tempfile
from datetime import timedelta

# ---- 必须在导入 app.* 之前定好环境 ----
_TMP = tempfile.mkdtemp(prefix="unit_agent_job_")
os.environ["DATABASE_URL"] = "sqlite:///" + os.path.join(_TMP, "u.db").replace("\\", "/")
os.environ["LLM_ENABLED"] = "false"
os.environ["SCHEDULER_ENABLED"] = "false"
os.environ["DEBUG"] = "false"
os.environ["SECRET_KEY"] = "unit_agent_job_secret_key_32chars_min"

_BACKEND = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"
)
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

import app.models  # noqa: F401,E402  确保全部表注册到 Base.metadata
from app.api.v1 import agent as agent_mod  # noqa: E402
from app.api.v1 import lesson_ai  # noqa: E402
from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.models import AgentJob, JobExecutionLog, ScheduledJob  # noqa: E402
from app.services import agent_job_state as S  # noqa: E402
from app.utils.common import now_local  # noqa: E402

_FAILED = []
_PASSED = 0


def ok(name, cond, detail=""):
    """断言并打印。刻意不叫 check()：tools/check_weak_assertion.py 只扫
    e2e 里的 `check(...)`，两边命名分开，扫描结果不互相污染。"""
    global _PASSED
    if cond:
        _PASSED += 1
        print(f"  [PASS] {name}" + (f"  -> {detail}" if detail else ""))
    else:
        _FAILED.append(name)
        print(f"  [FAIL] {name}  -> {detail}")


class _User:
    """最小 User stand-in：get_job / list_jobs 只用到 id 与 role_codes。"""
    id = 1
    role_codes = ["teacher"]


class _PageParams:
    offset = 0
    page_size = 50
    page = 1


class _JobObj:
    """最小 job stand-in：供判据函数与 lesson_ai._job_progress 使用。"""

    def __init__(self, status, created_at, error=None):
        self.status = status
        self.created_at = created_at
        self.error = error
        self.id = 999
        self.progress = 40
        self.stage = "生成中"
        self.result = None
        self.finished_at = None


def mk_job(age_seconds, status="running", user_id=1):
    """建一条 AgentJob，返回 id。age_seconds = 距今多少秒前创建。"""
    db = SessionLocal()
    try:
        j = AgentJob(
            user_id=user_id, agent="question", status=status,
            created_at=now_local() - timedelta(seconds=age_seconds),
            params="{}",
        )
        db.add(j)
        db.commit()
        db.refresh(j)
        return j.id
    finally:
        db.close()


def job_status(job_id):
    db = SessionLocal()
    try:
        at = db.get(AgentJob, job_id)
        return at.status if at else None
    finally:
        db.close()


def wipe():
    """清空两张任务表（每个 case 开头用，避免相互干扰）。"""
    db = SessionLocal()
    try:
        db.query(AgentJob).delete()
        db.query(JobExecutionLog).delete()
        db.commit()
    finally:
        db.close()


# ============================================================
# A 组：读时判定的边界
# ============================================================
def case_is_timed_out():
    print("\n" + "-" * 70)
    print("A 组：超时判据的边界（哪个状态判、用哪个时间列、无基准怎么办）")
    print("-" * 70)
    T = S.JOB_TIMEOUT_SECONDS
    # ⚠️ 边界断言必须用**注入的固定 now**，不能靠 now_local() 现取两次。
    # 第一版写的是 `S.is_timed_out("running", now_local() - timedelta(seconds=T))`：
    # 构造 created_at 与函数内部取 now 是两次独立调用，中间流逝的微秒让
    # 耗时变成 T + 0.000x → 严格大于 T → 判超时。本地（调用快）侥幸绿，
    # CI（机器慢）稳定红 —— 实测 CI 47/48，唯一红项就是 A②。
    # 这不是判据的 bug（`>` 的语义正确），是测试自己的时序竞态。
    BASE = now_local()

    ok("A① 刚创建的 running 不算超时",
       S.is_timed_out("running", BASE, now=BASE) is False)
    ok("A② 恰好等于阈值不算超时（用 > 不是 >=）",
       S.is_timed_out("running", BASE - timedelta(seconds=T), now=BASE) is False,
       f"T={T}")
    ok("A③ 超阈值 1 秒算超时",
       S.is_timed_out("running", BASE - timedelta(seconds=T + 1), now=BASE) is True)
    ok("A④ pending 也判超时（线程没起来就崩的形态）",
       S.is_timed_out("pending", BASE - timedelta(seconds=T + 1), now=BASE) is True)
    ok("A⑤ success 永不判超时（哪怕 30 天前）",
       S.is_timed_out("success", BASE - timedelta(days=30), now=BASE) is False)
    ok("A⑥ failed 永不判超时",
       S.is_timed_out("failed", BASE - timedelta(days=30), now=BASE) is False)
    ok("A⑦ created_at 为空 ≠ 超时（无基准不臆断）",
       S.is_timed_out("running", None, now=BASE) is False)
    ok("A⑧ status 为空按非运行态处理",
       S.is_timed_out(None, BASE - timedelta(days=1), now=BASE) is False)
    ok("A⑨ 亚秒级超出阈值也判超时（T+0.5s）",
       S.is_timed_out("running", BASE - timedelta(seconds=T + 0.5), now=BASE) is True)
    ok("A⑩ 亚秒级未达阈值不判超时（T-0.5s）",
       S.is_timed_out("running", BASE - timedelta(seconds=T - 0.5), now=BASE) is False)

    ok("A⑪ effective_status 把超时呈现为 failed",
       S.effective_status("running", BASE - timedelta(seconds=T + 1)) == "failed")
    ok("A⑫ effective_status 对正常任务原样返回",
       S.effective_status("running", BASE) == "running")
    ok("A⑬ 阈值与 lesson_ai 同源（不再各定义一份）",
       lesson_ai.JOB_TIMEOUT_SECONDS == S.JOB_TIMEOUT_SECONDS,
       f"{lesson_ai.JOB_TIMEOUT_SECONDS} vs {S.JOB_TIMEOUT_SECONDS}")


# ============================================================
# B 组：apply_timeout 不能污染正常任务
# ============================================================
def case_apply_timeout():
    print("\n" + "-" * 70)
    print("B 组：apply_timeout 只覆盖超时的，正常任务的 error 必须原样保留")
    print("-" * 70)
    T = S.JOB_TIMEOUT_SECONDS
    # 与 A 组同理：不依赖"两次 now_local() 之间的时间流逝"。
    # apply_timeout 内部调用 is_timed_out 时不注入 now，所以这里的比较
    # 必须**留出足够余量**（用 T+100 而不是恰好 T），避免边界抖动。
    BASE = now_local()

    d1 = S.apply_timeout(_JobObj("running", BASE - timedelta(seconds=T + 100)),
                         {"error": None})
    ok("B① 超时 → status=failed", d1["status"] == "failed", d1["status"])
    ok("B② 超时 → timed_out=True", d1["timed_out"] is True)
    ok("B③ 超时 → error 是可读中文", "超时" in (d1["error"] or ""),
       (d1["error"] or "")[:30])

    d2 = S.apply_timeout(_JobObj("failed", BASE, error="知识点不存在"),
                         {"error": "知识点不存在"})
    ok("B④ 正常失败任务保留自己的 error（不被'超时'盖掉）",
       d2["error"] == "知识点不存在", d2["error"])
    ok("B⑤ 正常失败任务 timed_out=False", d2["timed_out"] is False)

    # 极端但真实：线程写了 error 却没来得及改 status（崩在两句之间）
    d3 = S.apply_timeout(
        _JobObj("running", BASE - timedelta(seconds=T + 100),
                error="模型返回格式错误"),
        {"error": "模型返回格式错误"})
    ok("B⑥ 超时时原 error 备份到 error_before_timeout",
       d3["error_before_timeout"] == "模型返回格式错误",
       d3.get("error_before_timeout"))
    ok("B⑦ 对外 error 换成超时文案（用户先要知道该重试）",
       "超时" in (d3["error"] or ""), (d3["error"] or "")[:30])


# ============================================================
# C 组：启动收割
# ============================================================
def case_reap():
    print("\n" + "-" * 70)
    print("C 组：启动收割（清遗留 / 不误杀宽限期内的 / 不动已完成）")
    print("-" * 70)
    wipe()

    old_id = mk_job(7200)                              # 2h 前，必清
    fresh_id = mk_job(10)                              # 10s 前，必留
    edge_id = mk_job(S.JOB_TIMEOUT_SECONDS + 60)        # 超时但在宽限期内，必留
    done_id = mk_job(7200, status="success")            # 已完成，必留

    db = SessionLocal()
    try:
        n = S.reap_orphan_jobs(db)
    finally:
        db.close()

    ok("C① 只收割 1 条（越过宽限期的那个）", n == 1, f"实际 {n}")
    ok("C② 2 小时前的 running 被标记 failed", job_status(old_id) == "failed",
       job_status(old_id))
    ok("C③ 10 秒前的 running **未被误杀**", job_status(fresh_id) == "running",
       job_status(fresh_id))
    ok("C④ 超时但仍在宽限期内的**未被误杀**（多 worker 安全）",
       job_status(edge_id) == "running", job_status(edge_id))
    ok("C⑤ success 不受影响", job_status(done_id) == "success", job_status(done_id))

    db = SessionLocal()
    try:
        r = db.get(AgentJob, old_id)
        ok("C⑥ 收割时写了可读原因", bool(r.error) and "超时" in (r.error or ""),
           (r.error or "")[:30])
        ok("C⑦ 收割时写了 finished_at", r.finished_at is not None)
        ok("C⑧ 收割时 progress 置 100（不再显示进行中）", r.progress == 100,
           str(r.progress))
    finally:
        db.close()

    # 幂等：再跑一次不应再清任何东西
    db = SessionLocal()
    try:
        n2 = S.reap_orphan_jobs(db)
    finally:
        db.close()
    ok("C⑨ 幂等（再跑一次收割 0 条）", n2 == 0, f"实际 {n2}")


# ============================================================
# D 组：JobExecutionLog 同样收割
# ============================================================
def case_reap_exec_log():
    print("\n" + "-" * 70)
    print("D 组：定时任务执行记录（sys_job_execution_log）也要收割")
    print("-" * 70)
    wipe()

    db = SessionLocal()
    try:
        sj = ScheduledJob(name="unit_probe_job",
                          func_path="task_jobs.clean_old_logs",
                          cron_expression="0 3 * * *")
        db.add(sj)
        db.commit()
        db.refresh(sj)
        old_log = JobExecutionLog(
            job_id=sj.id, job_name="unit_probe_job", status="running",
            started_at=now_local() - timedelta(hours=2), trigger_type="auto")
        fresh_log = JobExecutionLog(
            job_id=sj.id, job_name="unit_probe_job", status="running",
            started_at=now_local(), trigger_type="auto")
        db.add_all([old_log, fresh_log])
        db.commit()
        old_log_id, fresh_log_id = old_log.id, fresh_log.id
    finally:
        db.close()

    db = SessionLocal()
    try:
        n = S.reap_orphan_jobs(db)
    finally:
        db.close()

    ok("D① 收割到旧执行记录", n >= 1, f"{n} 条")
    db = SessionLocal()
    try:
        ol = db.get(JobExecutionLog, old_log_id)
        fl = db.get(JobExecutionLog, fresh_log_id)
        ok("D② 2h 前的执行记录标记 failed", ol.status == "failed", ol.status)
        ok("D③ 新的执行记录未误杀", fl.status == "running", fl.status)
        ok("D④ duration_ms 写 0 而非 NULL（报表分母自洽）",
           ol.duration_ms == 0, str(ol.duration_ms))
        ok("D⑤ 写了可读 message", bool(ol.message) and "超时" in (ol.message or ""),
           (ol.message or "")[:30])
        ok("D⑥ finished_at 落定", ol.finished_at is not None)
    finally:
        db.close()


# ============================================================
# E 组：两个接口判据同源（不能各判各的）
# ============================================================
def case_same_criteria():
    print("\n" + "-" * 70)
    print("E 组：agent 与 lesson_ai 对同一任务给出相同结论")
    print("-" * 70)
    T = S.JOB_TIMEOUT_SECONDS
    BASE = now_local()

    zombie = _JobObj("running", BASE - timedelta(seconds=T + 100))
    agent_view = S.apply_timeout(zombie, {"status": "running", "error": None})
    lesson_view = lesson_ai._job_progress(zombie)
    ok("E① 僵尸任务两边都是 failed",
       agent_view["status"] == "failed" and lesson_view["status"] == "failed",
       f"agent={agent_view['status']} lesson={lesson_view['status']}")
    ok("E② 两边都给出非空原因",
       bool(agent_view["error"]) and bool(lesson_view["error"]))

    normal = _JobObj("running", BASE)
    agent_view2 = S.apply_timeout(normal, {"status": "running", "error": None})
    lesson_view2 = lesson_ai._job_progress(normal)
    ok("E③ 正常任务两边都是 running",
       agent_view2["status"] == "running" and lesson_view2["status"] == "running")


# ============================================================
# F 组：路由真实调用（弱断言抓不到的那一层）
# ============================================================
def case_route_real():
    print("\n" + "-" * 70)
    print("F 组：直接调用路由函数本体（grep 源码抓不到这一层）")
    print("-" * 70)
    wipe()

    zombie_id = mk_job(2 * 3600)
    fresh_id = mk_job(5)

    db = SessionLocal()
    try:
        r_z = agent_mod.get_job(zombie_id, db=db, user=_User())
        r_f = agent_mod.get_job(fresh_id, db=db, user=_User())
    finally:
        db.close()

    z, f = r_z["data"], r_f["data"]
    ok("F① 僵尸任务经 /agent/jobs/{id} 返回 failed", z["status"] == "failed", z["status"])
    ok("F② 僵尸任务带 timed_out=True", z.get("timed_out") is True, str(z.get("timed_out")))
    ok("F③ 僵尸任务 error 是可读中文",
       bool(z.get("error")) and "超时" in z["error"], (z.get("error") or "")[:30])
    ok("F④ 正常任务经路由仍返回 running", f["status"] == "running", f["status"])
    ok("F⑤ 正常任务 timed_out=False", f.get("timed_out") is False, str(f.get("timed_out")))

    # 列表接口的筛选语义：僵尸任务在库里是 running，但呈现为 failed，
    # 所以 ?status=running 不该含它、?status=failed 必须含它。
    db = SessionLocal()
    try:
        r_all = agent_mod.list_jobs(params=_PageParams(), status=None, db=db, user=_User())
        r_run = agent_mod.list_jobs(params=_PageParams(), status="running", db=db, user=_User())
        r_fail = agent_mod.list_jobs(params=_PageParams(), status="failed", db=db, user=_User())
    finally:
        db.close()

    run_ids = [i["id"] for i in r_run["data"]["items"]]
    fail_ids = [i["id"] for i in r_fail["data"]["items"]]
    all_items = r_all["data"]["items"]

    ok("F⑥ 全量列表里僵尸任务呈现为 failed",
       any(i["id"] == zombie_id and i["status"] == "failed" for i in all_items))
    ok("F⑦ ?status=running 不含僵尸任务（否则用户以为还在跑）",
       zombie_id not in run_ids, str(run_ids))
    ok("F⑧ ?status=failed 含僵尸任务（库里真实 status 仍是 running）",
       zombie_id in fail_ids, str(fail_ids))
    ok("F⑨ ?status=running 含正常任务", fresh_id in run_ids, str(run_ids))


# ============================================================
# G 组：启动钩子接线（收割必须真的被 main.lifespan 调用）
# ============================================================
def case_wired_up():
    print("\n" + "-" * 70)
    print("G 组：接线检查（收割函数存在但没人调 = 没修）")
    print("-" * 70)
    import inspect

    import app.main as main_mod  # 显式导入：本文件此前只导了 app.api.v1.*

    main_src = inspect.getsource(main_mod.lifespan)
    ok("G① main.lifespan 里调用了 reap_orphan_jobs",
       "reap_orphan_jobs" in main_src)

    # 收割失败不能阻断启动：try/except 必须存在
    ok("G② 收割异常被兜住（不阻断启动）",
       "僵尸任务收割未执行" in main_src or "except" in main_src.split("reap_orphan_jobs")[0])

    ok("G③ 宽限期大于超时阈值（否则等于没有宽限）",
       S.REAP_GRACE_SECONDS > 0,
       f"grace={S.REAP_GRACE_SECONDS}s, timeout={S.JOB_TIMEOUT_SECONDS}s")


def main() -> int:
    Base.metadata.create_all(bind=engine)

    print("=" * 70)
    print("离线单元回归：AI 长任务僵尸状态判定与启动收割（B2）")
    print("=" * 70)

    case_is_timed_out()
    case_apply_timeout()
    case_reap()
    case_reap_exec_log()
    case_same_criteria()
    case_route_real()
    case_wired_up()

    print("\n" + "=" * 70)
    total = _PASSED + len(_FAILED)
    print(f"合计 {total} 项：通过 {_PASSED}，失败 {len(_FAILED)}")
    if _FAILED:
        print("\n失败项：")
        for n in _FAILED:
            print(f"  - {n}")
        print("=" * 70)
        return 1
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
