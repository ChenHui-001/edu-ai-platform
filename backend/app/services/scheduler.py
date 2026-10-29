"""APScheduler 调度器管理。"""
import os
from typing import Any, Dict, Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select, text

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.logger import get_logger
from app.models import JobExecutionLog, ScheduledJob
from app.services import task_jobs
from app.services.job_lock import (
    acquire_job_lock, clear_expired_locks, current_owner, locked_jobs,
    release_job_lock,
)
from app.utils.common import now_local

logger = get_logger("scheduler")

_scheduler: Optional[BackgroundScheduler] = None


def get_scheduler() -> BackgroundScheduler:
    """获取全局调度器实例。"""
    global _scheduler
    if _scheduler is None:
        _scheduler = BackgroundScheduler(
            timezone="Asia/Shanghai",
            job_defaults={
                "coalesce": True,       # 错过执行窗口只跑一次
                "max_instances": 1,
                "misfire_grace_time": 3600,
            },
        )
    return _scheduler


def _execute(job_id: int, func_path: str, trigger_type: str = "auto") -> None:
    """任务执行包装：抢执行锁 → 记录执行日志 → 跑任务体 → 失败重试通知。

    ## 加锁的位置很关键

    抢锁必须在**建 running 日志之前**：如果先写 log 再抢锁失败，库里会留下
    一条永远停在 `running` 的执行记录（没人会去把它改成 skipped），
    运维看「执行记录」会以为任务卡死了。实测的期望行为是
    「未获锁 → 一条日志都不写」（见 test_a2_job_lock.py 的对照用例 C）。

    也必须在**跑任务体之前就 commit+close 掉抢锁的 session**：SQLite 单写者，
    持着未提交的写事务跑任务体会把全场写操作阻塞到 busy_timeout 上限。
    实测持锁不提交 3s 时，另一进程写 sys_login_log 用了 2221ms（正常 6ms）。
    详见 services/job_lock.py 的模块 docstring ②。

    ## 为什么拆成 `_execute` + `_run_locked` 两个函数

    因为抢锁的 session 必须在跑任务体之前就 commit+close，而任务体自己
    需要一个新的、覆盖整个执行周期的 session（写 running 日志 → 跑 →
    改成 success/failed）。两者的生命周期**不能共用一个 session**，
    拆开是最直白的表达方式：`_execute` 只管锁，`_run_locked` 只管执行。
    """
    if not acquire_job_lock(job_id):
        # 别的进程正在跑。这是正常调度结果，不是错误 —— 不写任何日志。
        return
    try:
        _run_locked(job_id, func_path, trigger_type)
    finally:
        # release 内部自建 session（见 job_lock ②），必须在 _run_locked
        # 的 db.close() 之后调用 —— 这里 _run_locked 已返回，等价满足。
        release_job_lock(job_id)


def _run_locked(job_id: int, func_path: str, trigger_type: str) -> None:
    """持锁执行任务体。只在 `_execute` 抢到锁之后调用。"""
    db = SessionLocal()
    log = None
    started = now_local()
    try:
        job = db.get(ScheduledJob, job_id)
        name = job.name if job else func_path
        log = JobExecutionLog(
            job_id=job_id, job_name=name, status="running",
            started_at=started, trigger_type=trigger_type,
        )
        db.add(log)
        db.commit()

        result = task_jobs.run_job(func_path)
        finished = now_local()
        log.status = "success"
        log.finished_at = finished
        log.duration_ms = int((finished - started).total_seconds() * 1000)
        log.message = str(result)

        if job:
            job.last_run_at = finished
            job.last_status = "success"
            job.last_error = None
            # 不能用 job.run_count += 1：ORM 的读-改-写会丢更新，见 _bump_run_count。
            _bump_run_count(db, job_id)
        db.commit()
        logger.info(f"任务 {name} 执行成功: {result}")

        # 租约超半告警：**不做续租**（要引入后台线程 + 续租失败处理 +
        # 续租与放锁的竞态，复杂度远超收益），改用它兜底。
        #
        # 表达式说明：duration_ms 单位是毫秒，租约是秒，所以「租约的一半」
        # = lease * 1000 / 2 = lease * 500。写成 `* 500` 即使数值正确也
        # 完全不可读 —— 下一个人会以为是"500 倍"而不敢动，或误改成 `* 500`
        # 之外的数。故拆成 `* 1000 // 2` 并在此注明。
        half_lease_ms = settings.JOB_LOCK_LEASE_SECONDS * 1000 // 2
        if log.duration_ms and log.duration_ms > half_lease_ms:
            logger.error(
                f"任务 {name} 耗时 {log.duration_ms}ms 已超过租约的一半"
                f"（{half_lease_ms}ms），存在锁被其他进程提前抢占、"
                f"两个进程同时写的风险，请调大 JOB_LOCK_LEASE_SECONDS"
            )
    except Exception as exc:
        logger.opt(exception=True).error(f"任务 {func_path} 执行失败: {exc}")
        if log:
            finished = now_local()
            log.status = "failed"
            log.finished_at = finished
            log.duration_ms = int((finished - started).total_seconds() * 1000)
            log.message = str(exc)[:2000]
        job = db.get(ScheduledJob, job_id)
        if job:
            job.last_run_at = now_local()
            job.last_status = "failed"
            job.last_error = str(exc)[:2000]
            # 同成功分支：走 SQL 原子自增，不用 job.run_count += 1。
            _bump_run_count(db, job_id)

            # 连续失败通知管理员
            if job.retry_times > 0:
                from app.models import Notification, Role, User, UserRole

                admin_ids = db.scalars(
                    select(User.id).join(UserRole, UserRole.user_id == User.id)
                    .join(Role, Role.id == UserRole.role_id)
                    .where(Role.code == "sys_admin")
                ).all()
                for aid in admin_ids:
                    db.add(
                        Notification(
                            user_id=aid, title="定时任务执行失败",
                            content=f"任务「{job.name}」执行失败：{exc}",
                            type="system", biz_type="job", biz_id=job_id,
                        )
                    )
        db.commit()
    finally:
        db.close()


def _bump_run_count(db, job_id: int) -> None:
    """`run_count` 加 1。**必须走 SQL 原子自增，不能用 ORM 的 `+= 1`。**

    ## 为什么 `job.run_count += 1` 是错的

    ORM 的 `+= 1` 编译出来是三步：`SELECT run_count` → Python 层 `+1` →
    `UPDATE ... SET run_count = <字面值>`。两个执行者若基于同一快照读到同一个
    旧值，就都写回同一个新值，后提交的覆盖先提交的 —— **lost update**。
    实测（两个 session 各读到 0、各自 +1、交错提交）：

        两者各自读到 (0, 0)
        交错提交后 run_count = 1      ← 期望 2，实际 1

    而 `SET run_count = run_count + 1` 的读与写是同一条语句，被 SQLite 的
    写锁整体串行化，**不存在读-改-写窗口**。

    注意：有 A2 执行锁之后这个失真在「同一任务并发触发」的场景里已经看不到
    （V2④ 恒为 1），但根因一直在 `+= 1` 这个写法上 —— 一旦将来引入「同一任务
    允许并发执行不同分片」，它会立刻重新出现。所以按写法修，不按场景修。

    ## 为什么抽成函数，而不是在调用处各写一遍

    这条 SQL 的要点是「读与写在同一条语句里」，写两遍迟早有人只改一处、
    或者加个 WHERE / 先读后写把它悄悄退回成两步。抽出来之后
    `test_a2_job_lock.py` 的 V1⑦ 也能直接拿它做确定性反证：**同一形状下
    ORM 写法丢一次（V1⑥）、这里不丢（V1⑦）**。

    Args:
        db: 调用方的事务 session。本函数**不提交** —— 由调用方 commit，
            以保证 `run_count` 与 `last_run_at`/`last_status` 落在同一事务里。
        job_id: `sys_scheduled_job.id`。
    """
    db.execute(
        text("UPDATE sys_scheduled_job SET run_count = run_count + 1 WHERE id = :jid"),
        {"jid": job_id},
    )


def add_job(job: ScheduledJob) -> bool:
    """注册单个任务到调度器。"""
    sched = get_scheduler()
    try:
        parts = job.cron_expression.split()
        if len(parts) != 5:
            raise ValueError(f"Cron 表达式需 5 段：{job.cron_expression}")
        trigger = CronTrigger(
            minute=parts[0], hour=parts[1], day=parts[2],
            month=parts[3], day_of_week=parts[4],
        )
        sched.add_job(
            _execute,
            trigger=trigger,
            args=[job.id, job.func_path],
            id=f"job_{job.id}",
            name=job.name,
            replace_existing=True,
        )
        return True
    except Exception as exc:
        logger.error(f"任务 {job.name} 注册失败: {exc}")
        return False


def remove_job(job_id: int) -> None:
    """移除任务。"""
    try:
        get_scheduler().remove_job(f"job_{job_id}")
    except Exception:
        pass


def sync_all_jobs() -> int:
    """从数据库同步全部启用的任务。"""
    if not settings.SCHEDULER_ENABLED:
        return 0
    sched = get_scheduler()
    db = SessionLocal()
    count = 0
    try:
        jobs = db.scalars(
            select(ScheduledJob).where(ScheduledJob.is_active.is_(True))
        ).all()
        for j in jobs:
            if add_job(j):
                count += 1
        if not sched.running:
            sched.start()
            logger.info(f"调度器已启动，注册 {count} 个任务")
    finally:
        db.close()

    # 顺手清掉上一轮崩溃遗留的过期锁。放在这里（而不是定时任务里）的理由：
    # 启动是唯一一个「必然发生、且不需要抢锁」的时点 —— 用任务去清理锁
    # 会绕回同一个问题（清理任务本身要不要锁）。清理失败不影响启动。
    try:
        cleared = clear_expired_locks()
        if cleared:
            logger.info(f"启动时清理了 {cleared} 条过期任务锁")
    except Exception as exc:
        logger.warning(f"启动时清理过期任务锁失败: {exc}")

    return count


def run_job_now(job_id: int) -> Dict[str, Any]:
    """手动执行任务。

    ## 与 `_execute` 的加锁差异

    自动触发撞锁时**静默跳过**（下个 cron 窗口再来），手动触发撞锁时
    **明确报错** —— 管理员点了按钮，什么都没发生还不能告诉他原因，
    会让人反复点、怀疑按钮坏了。所以这里抛 `BusinessException`，
    由 `api/v1/logs.py` 转成 400「该任务正在执行中，请稍后再试」。

    ## 为什么不排队等锁

    等锁会让 HTTP 请求挂最多 1800s（租约时长），代理层早就超时了，
    而且排队期间用户看不到任何反馈。直接报错让用户重试更诚实。

    ## 加锁位置

    也在写 running 日志**之前** —— 撞锁时不留下停在 running 的记录
    （与 `_execute` 同理，见其 docstring）。
    """
    from app.core.exception import BusinessException

    db = SessionLocal()
    try:
        job = db.get(ScheduledJob, job_id)
        if not job:
            raise ValueError("任务不存在")
        func_path, job_name = job.func_path, job.name
    finally:
        # 先关掉这个 session 再去抢锁：抢锁内部要 commit，
        # 这个 session 上还有未完成的事务会互相等（SQLite 单写者）。
        db.close()

    if not acquire_job_lock(job_id):
        raise BusinessException("该任务正在执行中，请稍后再试")

    started = now_local()
    db = SessionLocal()
    try:
        log = JobExecutionLog(
            job_id=job_id, job_name=job_name, status="running",
            started_at=started, trigger_type="manual",
        )
        db.add(log)
        db.commit()
        try:
            result = task_jobs.run_job(func_path)
            log.status = "success"
            log.message = str(result)
        except Exception as exc:
            log.status = "failed"
            log.message = str(exc)[:2000]
            raise
        finally:
            log.finished_at = now_local()
            log.duration_ms = int((now_local() - started).total_seconds() * 1000)
            db.commit()
        return result
    finally:
        db.close()
        release_job_lock(job_id)


def scheduler_status() -> Dict[str, Any]:
    """调度器运行状态。

    ## 为什么多了 worker 相关的 3 个字段

    `uvicorn --workers N` 之后，「调度器在跑」不再是一个进程级事实：
    N 个 worker 各有一个 scheduler、各有一份 job 列表。只报
    `running` / `job_count` 会让运维以为只有一份。新增字段是**纯增量**，
    既有调用方（`api/v1/logs.py`、`api/v1/report.py`）都是原样透传，
    零改动。

    `locked_jobs` 直接查表而不是查本进程内存 —— 锁是跨进程的，
    本进程只知道自己的（也未必有）。
    """
    sched = get_scheduler()
    jobs = []
    if sched.running:
        for j in sched.get_jobs():
            jobs.append({
                "id": j.id, "name": j.name,
                "next_run": j.next_run_time.strftime("%Y-%m-%d %H:%M:%S")
                if j.next_run_time else None,
            })
    return {
        "running": sched.running,
        "job_count": len(jobs),
        "jobs": jobs,
        # ---- 多 worker 观测（纯增量字段）----
        "worker_pid": os.getpid(),
        "worker_id": current_owner(),
        "locked_jobs": locked_jobs(),
    }
