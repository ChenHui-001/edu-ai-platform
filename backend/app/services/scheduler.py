"""APScheduler 调度器管理。"""
from typing import Any, Dict, Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.logger import get_logger
from app.models import JobExecutionLog, ScheduledJob
from app.services import task_jobs
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
    """任务执行包装：记录执行日志、失败重试通知。"""
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
            job.run_count += 1
        db.commit()
        logger.info(f"任务 {name} 执行成功: {result}")
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
            job.run_count += 1

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
    return count


def run_job_now(job_id: int) -> Dict[str, Any]:
    """手动执行任务。"""
    db = SessionLocal()
    try:
        job = db.get(ScheduledJob, job_id)
        if not job:
            raise ValueError("任务不存在")
        started = now_local()
        log = JobExecutionLog(
            job_id=job_id, job_name=job.name, status="running",
            started_at=started, trigger_type="manual",
        )
        db.add(log)
        db.commit()
        try:
            result = task_jobs.run_job(job.func_path)
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


def scheduler_status() -> Dict[str, Any]:
    """调度器运行状态。"""
    sched = get_scheduler()
    jobs = []
    if sched.running:
        for j in sched.get_jobs():
            jobs.append({
                "id": j.id, "name": j.name,
                "next_run": j.next_run_time.strftime("%Y-%m-%d %H:%M:%S")
                if j.next_run_time else None,
            })
    return {"running": sched.running, "job_count": len(jobs), "jobs": jobs}
