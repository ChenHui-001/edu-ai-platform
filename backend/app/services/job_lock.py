"""定时任务执行锁：多 worker 下保证同一任务同一时刻只有一个进程在跑。

## 问题的形状

`uvicorn --workers 2` 时每个 worker 都跑 `main.lifespan` → 各自
`sync_all_jobs()` → 各自一个 `BackgroundScheduler`。cron 是墙钟触发，
N 个进程会在**同一分钟同时**叫醒同一个任务。

`max_instances=1` 只在**单个 scheduler 内部**生效，管不到跨进程。
而 `JOB_HANDLERS` 里的任务都是「扫描 + 批量写」：

    任务                          实测耗时      规模
    publish_scheduled_tasks 空跑   0.7–1.1 ms   —
    同上 3 个任务                  140–172 ms   450 条通知
    同上 5 个任务                  553–652 ms   2400 条通知
    同上 20 个任务                 1351 ms      6000 条通知
    同上 60 个任务（压力上限）       8281 ms      28800 条通知
    clean_old_logs                 2592 ms      3×30 万过期行

并发执行不是「多跑一遍」而是**写放大 N 倍**。实测 2 进程同一瞬间起跑
`publish_scheduled_tasks`：

    无锁：[A] {'activated': 3, 'notified': 450}
          [B] {'activated': 3, 'notified': 450}
          -> notification=900  job_execution_log=2   ← 每个学生收到两条通知

## 方案：DB 行锁（条件 UPSERT）

不用 `fcntl.flock`（A1 启动锁刚用过）：A1 守的是**启动期一次性**的
建表/迁移/播种，进程活多久锁就持多久是合理的；而任务锁必须是**短租约 +
可抢占**的 —— 进程崩溃后不能让整个调度停摆 30 分钟，必须能自动接管。
文件锁做不到「崩溃后按时间自动失效」，要额外的心跳文件与清理逻辑，
而 DB 行锁一条 `WHERE expire_at < now` 就够。

抢占是一条语句，在 SQLite 单写者模型下天然原子：

    INSERT INTO sys_job_lock (...) VALUES (...)
    ON CONFLICT (job_id) DO UPDATE SET owner=..., expire_at=...
    WHERE sys_job_lock.expire_at < :now

`WHERE` 挂在 `DO UPDATE` 上 —— 冲突且**旧租约未过期**时整句不生效，
`rowcount` 为 0，即「没抢到」。实测 8 进程 `multiprocessing.Barrier`
同一瞬间发同一条语句：

    空表     5/5 轮：抢到 1/8，错误 0
    未过期  10/10 轮：抢到 0/8，错误 0
    已过期   5/5 轮：抢到 1/8，错误 0

**默认 deferred 事务就够，不需要 `BEGIN IMMEDIATE`。** 这与
「SELECT 在 pysqlite legacy 模式下不开事务 → 不会 SQLITE_BUSY_SNAPSHOT」
是同一个结论的两面：这条语句本身是单条写，天然串行。

## 三个「写错了不报错、只是静默失效」的点

### ① 时间列不能用 `CURRENT_TIMESTAMP`

见 `models.JobLock` 的 docstring，有实测数字。一句话：SQLite 的 DATETIME
是字符串按字典序比较，`CURRENT_TIMESTAMP`（UTC、无微秒、19 字符）与
`now_local()`（本地、带微秒、26 字符）混用时，租约**写入瞬间即过期**，
锁永远抢得到、永不互斥、日志里毫无异常。本文件所有时间一律 `now_local()`。

### ② 抢锁的 session 必须 commit + close **之后**才跑任务体

SQLite 是单写者。如果持着「已抢占但未提交」的事务去跑任务体，任务体
（以及同时段所有别的请求）的写操作全被这把写锁挡住。实测持有 3s 不提交、
另一进程写 `sys_login_log`：

    commit+close 后再跑        -> 用户写 6ms     成功
    不提交、跑完才 commit      -> 用户写 2221ms  （已逼近 busy_timeout=5000）

所以 `acquire_job_lock` 内部自建 session、`finally` 里 commit+close，
**返回值是 bool 而不是 session** —— 任务体拿不到那个 session，
想犯错也没有入口。`release_job_lock` 同样自建 session。

### ③ 释放必须按 owner 限定

`DELETE ... WHERE job_id = :id AND owner = :me`。无条件 DELETE 的问题：
进程 A 崩溃留下未过期锁 → 进程 B 抢占失败、跳过 → B 觉得「反正我也没跑，
顺手清一下」→ 把 A 的锁删了 → 下一分钟 A（或 C）和 B 又同时跑。
互斥退化成靠运气。

`owner` 带 uuid 是为了绕开 pid 复用：容器里 pid 高度重复（都是 7、8 这样的
小数字），只靠 `hostname:pid` 会把重启后的新进程误认成崩溃前的旧进程，
于是它能删掉「别人」的锁。

## 租约期为什么是 1800s

实测最慢的 handler 是 `clean_old_logs`（3×30 万行）2592ms，
1800s 有 694 倍余量。更关键的理由不是余量，而是
**所有 handler 都是「补齐式扫描」**：

    publish_scheduled_tasks  WHERE publish_at <= now
    clean_old_logs           WHERE created_at < cutoff
    clean_expired_exams      WHERE end_at < deadline

漏掉一个窗口不丢数据、只是延后到下一个窗口。**这才是能容忍「崩溃后最长
停 30 分钟」的前提。** 如果将来有人加一个「只在精确时刻做一次、错过就
永久丢失」的 handler，必须同步下调 `JOB_LOCK_LEASE_SECONDS`，
否则那个窗口会被静默跳过。
"""
import os
import socket
import uuid
from typing import Optional

from sqlalchemy import text

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.logger import get_logger
from app.utils.common import now_local

logger = get_logger("job_lock")

# 本进程身份。**必须在模块级算一次**，不能每次调用重新生成：
# - pid 用于日志可读性
# - uuid 用于区分「同一 pid 的不同世代」（容器里 pid 高度重复）
# 每次调用重新生成 uuid 会让 release 找不到自己抢的那行，
# 锁永远释放不掉（只能等 1800s 租约到期）—— 而且不报错。
_OWNER = (
    f"{socket.gethostname()}:{os.getpid()}:{uuid.uuid4().hex[:8]}"
)[:80]  # 截断到列宽，hostname 在 CI 里可能很长


def current_owner() -> str:
    """本进程的锁持有者标识（`hostname:pid:uuid[:8]`）。"""
    return _OWNER


def acquire_job_lock(job_id: int, lease_seconds: Optional[int] = None) -> bool:
    """尝试抢占任务执行锁。

    Args:
        job_id: 任务 ID（`sys_scheduled_job.id`）。
        lease_seconds: 租约时长，默认取 `settings.JOB_LOCK_LEASE_SECONDS`。

    Returns:
        True = 抢到了，调用方**必须**在同一路径上 `release_job_lock`；
        False = 别的进程正在执行，调用方应跳过本次触发（不是错误）。

    ## 为什么返回值不是 session

    见模块 docstring 的 ②。session 在 `finally` 里已 commit+close，
    调用方拿不到它就不会误用。SQLite 单写者模型下，持着未提交的写事务
    去跑任务体会把全场写操作阻塞到 `busy_timeout` 上限。
    """
    lease = int(lease_seconds or settings.JOB_LOCK_LEASE_SECONDS)
    now = now_local()
    # 租约到期时刻用 Python 算好再传参，**不用** SQL 的 datetime('now', ...)。
    # SQLite 的 datetime() 返回 UTC 且无微秒，同样踩 ① 的坑。
    from datetime import timedelta

    expire = now + timedelta(seconds=lease)

    db = SessionLocal()
    try:
        # 条件 UPSERT：`WHERE` 挂在 DO UPDATE 上，冲突且旧租约未过期时整句不生效。
        # 这是「抢占」的全部实现 —— 一条语句，无读-改-写窗口。
        result = db.execute(
            text("""
                INSERT INTO sys_job_lock (job_id, owner, acquired_at, expire_at)
                VALUES (:jid, :owner, :now, :expire)
                ON CONFLICT (job_id) DO UPDATE
                SET owner = :owner, acquired_at = :now, expire_at = :expire
                WHERE sys_job_lock.expire_at < :now
            """),
            {"jid": job_id, "owner": _OWNER, "now": now, "expire": expire},
        )
        got = result.rowcount > 0
        db.commit()
    except Exception as exc:
        # 抢锁本身失败（如表不存在）不应该让任务「静默不跑」——
        # 但也不能放行（那就退化成无锁）。这里 rollback 后抛出，
        # 由 _execute 的 except 记成 failed，运维能在执行记录里看到。
        db.rollback()
        logger.opt(exception=True).error(f"任务 {job_id} 抢占执行锁异常: {exc}")
        raise
    finally:
        # 必须在任务体之前关掉：见模块 docstring ②。
        db.close()

    if got:
        logger.debug(f"任务 {job_id} 获得执行锁（owner={_OWNER}, 租约 {lease}s）")
    else:
        logger.info(f"任务 {job_id} 正由其他进程执行，本次跳过")
    return got


def release_job_lock(job_id: int) -> None:
    """释放任务执行锁。只删自己持有的那行。

    在任何情况下都不应该抛异常打断调用方 —— 释放失败最坏的结果是
    「锁多留到租约到期（1800s）」，而抛异常会让已经成功的任务被记成 failed，
    或让 `finally` 掩盖掉真正的业务异常。故这里吞掉异常并记日志。
    """
    db = SessionLocal()
    try:
        result = db.execute(
            text("DELETE FROM sys_job_lock WHERE job_id = :jid AND owner = :owner"),
            {"jid": job_id, "owner": _OWNER},
        )
        db.commit()
        if result.rowcount == 0:
            # 正常情况下不该发生（抢到了就该有自己那行）。发生说明：
            # 租约在任务执行期间过期并被别的进程接管了 —— 那是租约太短，
            # 值得一条 warning（任务可能已经在两个进程里都跑过了）。
            logger.warning(
                f"任务 {job_id} 释放锁时未找到自己的锁行（owner={_OWNER}）—— "
                f"租约可能已在执行期间过期，检查 JOB_LOCK_LEASE_SECONDS"
            )
    except Exception as exc:
        logger.opt(exception=True).error(f"任务 {job_id} 释放执行锁异常: {exc}")
    finally:
        db.close()


def locked_jobs() -> list:
    """当前未过期的锁（供 `/jobs/status` 观测用）。

    Returns:
        `[{"job_id": int, "owner": str, "acquired_at": str, "expire_at": str}, ...]`
    """
    db = SessionLocal()
    try:
        rows = db.execute(
            text("""
                SELECT job_id, owner, acquired_at, expire_at
                FROM sys_job_lock WHERE expire_at >= :now ORDER BY job_id
            """),
            {"now": now_local()},
        ).fetchall()
        return [
            {
                "job_id": int(r[0]),
                "owner": str(r[1]),
                "acquired_at": str(r[2]),
                "expire_at": str(r[3]),
            }
            for r in rows
        ]
    except Exception as exc:
        # 观测接口不该因为锁表异常而 500。
        logger.warning(f"读取任务锁状态失败: {exc}")
        return []
    finally:
        db.close()


def clear_expired_locks() -> int:
    """清理已过期的锁行，返回删除行数。

    不是正确性所必需（抢占语句自己会覆盖过期行），只是让
    `/jobs/status` 的观测结果更干净、并顺手回收空间。
    """
    db = SessionLocal()
    try:
        result = db.execute(
            text("DELETE FROM sys_job_lock WHERE expire_at < :now"),
            {"now": now_local()},
        )
        db.commit()
        return int(result.rowcount or 0)
    except Exception as exc:
        logger.warning(f"清理过期任务锁失败: {exc}")
        db.rollback()
        return 0
    finally:
        db.close()
