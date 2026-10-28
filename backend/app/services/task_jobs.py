"""定时任务执行逻辑（APScheduler 调度）。"""
from datetime import timedelta
from typing import Any, Dict

from sqlalchemy import func, select

from app.core.database import SessionLocal
from app.core.logger import get_logger
from app.models import (
    Attachment, ReviewPlan, StudyRecord, Submission, Task, TaskAssignment,
    TaskStatus, User,
)
from app.utils.common import now_local

logger = get_logger("jobs")

_TYPE_LABEL = {"homework": "作业", "exam": "考试", "practice": "随机练习"}


def clean_expired_exams() -> Dict[str, Any]:
    """清理过期考试：超过结束时间 30 天未批改的考试归档。"""
    db = SessionLocal()
    try:
        deadline = now_local() - timedelta(days=30)
        rows = db.scalars(
            select(Task).where(
                Task.type.in_(["exam", "homework"]),
                Task.end_at.isnot(None),
                Task.end_at < deadline,
                Task.status.in_([TaskStatus.PUBLISHED.value, TaskStatus.ONGOING.value]),
            )
        ).all()
        for t in rows:
            t.status = TaskStatus.ARCHIVED.value
        db.commit()
        return {"archived": len(rows)}
    finally:
        db.close()


def generate_daily_report() -> Dict[str, Any]:
    """生成学习日报：统计前一日学习数据。"""
    db = SessionLocal()
    try:
        # 只取一次当前时间：日报的「日期标签」与「统计窗口」必须来自同一个
        # 时间点，否则跨零点执行时标签与统计可能落在不同的一天。
        now = now_local()
        yesterday = (now - timedelta(days=1)).strftime("%Y-%m-%d")
        rows = db.scalars(select(StudyRecord).where(StudyRecord.study_date == yesterday)).all()
        active_students = len(rows)
        total_questions = sum(r.question_count for r in rows)
        total_correct = sum(r.correct_count for r in rows)

        # 原实现用 `func.date(Submission.submit_time) == yesterday`：函数包裹列，
        # SQLite 无法用 submit_time 上的索引，等于日报每次全表扫描 + 逐行求值。
        # 改为半开区间 [昨日 00:00, 今日 00:00) —— 与「日期部分等于昨日」等价，
        # 但变成纯粹的列比较，索引可用。
        # 时间基准必须与写库一致：全库 submit_time 都由 now_local() 写入的
        # **naive 本地时间**，因此这里也用 naive 本地零点，不引入 UTC/tzinfo
        # （否则会整体偏移一个时区，把边界附近的交卷统计错位）。
        day_start = (now - timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        day_end = day_start + timedelta(days=1)
        subs = db.scalars(
            select(Submission).where(
                Submission.submit_time >= day_start,
                Submission.submit_time < day_end,
                Submission.score.isnot(None),
            )
        ).all()

        logger.info(
            f"日报 {yesterday}: 活跃学生 {active_students}, 做题 {total_questions}, "
            f"交卷 {len(subs)}"
        )
        return {
            "date": yesterday,
            "active_students": active_students,
            "questions": total_questions,
            "accuracy": round(total_correct / total_questions * 100, 2) if total_questions else 0,
            "submissions": len(subs),
            "avg_score": round(sum(s.score for s in subs) / len(subs), 2) if subs else 0,
        }
    finally:
        db.close()


def generate_weekly_report() -> Dict[str, Any]:
    """生成学情周报。"""
    db = SessionLocal()
    try:
        since = (now_local() - timedelta(days=7)).strftime("%Y-%m-%d")
        rows = db.scalars(select(StudyRecord).where(StudyRecord.study_date >= since)).all()
        subs = db.scalars(
            select(Submission).where(
                func.date(Submission.submit_time) >= since,
                Submission.score.isnot(None),
            )
        ).all()
        stats = {
            "period": since,
            "active_students": len(rows),
            "study_hours": round(sum(r.study_seconds for r in rows) / 3600, 1),
            "questions": sum(r.question_count for r in rows),
            "submissions": len(subs),
            "avg_score": round(sum(s.score for s in subs) / len(subs), 2) if subs else 0,
        }
        logger.info(f"周报统计: {stats}")
        return stats
    finally:
        db.close()


def clean_temp_attachments() -> Dict[str, Any]:
    """清理临时附件：超过 7 天且未绑定业务。"""
    import os

    db = SessionLocal()
    try:
        deadline = now_local() - timedelta(days=7)
        rows = db.scalars(
            select(Attachment).where(
                Attachment.is_temp.is_(True),
                Attachment.created_at < deadline,
                Attachment.biz_id.is_(None),
            )
        ).all()
        removed = 0
        for a in rows:
            try:
                if a.file_path and os.path.exists(a.file_path):
                    os.remove(a.file_path)
                db.delete(a)
                removed += 1
            except OSError as exc:
                logger.warning(f"附件 {a.id} 删除失败: {exc}")
        db.commit()
        return {"removed": removed}
    finally:
        db.close()


def push_review_reminders() -> Dict[str, Any]:
    """按艾宾浩斯计划推送今日复习清单。"""
    from app.models import Notification

    db = SessionLocal()
    try:
        today = now_local().strftime("%Y-%m-%d")
        plans = db.scalars(
            select(ReviewPlan).where(
                ReviewPlan.scheduled_date == today,
                ReviewPlan.is_completed.is_(False),
            )
        ).all()
        # 按学生聚合
        by_student: Dict[int, list] = {}
        for p in plans:
            by_student.setdefault(p.student_id, []).append(p)

        sent = 0
        for student_id, items in by_student.items():
            db.add(
                Notification(
                    user_id=student_id,
                    title=f"今日复习提醒（{len(items)} 个知识点）",
                    content="、".join(str(i.knowledge_point_id) for i in items[:5]),
                    type="review",
                    biz_type="review",
                )
            )
            sent += 1
        db.commit()
        logger.info(f"复习提醒推送 {sent} 名学生")
        return {"students": sent, "plans": len(plans)}
    finally:
        db.close()


def clean_old_logs() -> Dict[str, Any]:
    """清理过期运维数据：日志表/通知/任务执行记录无界增长会拖慢 SQLite。

    - 操作日志/登录日志：保留 90 天
    - 错误日志/AI 调用日志：保留 90 天
    - 任务执行日志：保留 30 天
    - 已读站内通知：保留 30 天（未读通知不清理）
    """
    from app.models import (
        AgentCallLog, ErrorLog, JobExecutionLog, LoginLog, Notification,
        OperationLog,
    )

    db = SessionLocal()
    try:
        now = now_local()
        cut90 = now - timedelta(days=90)
        cut30 = now - timedelta(days=30)
        removed: Dict[str, int] = {}
        for name, model, column, cutoff in (
            ("operation_log", OperationLog, OperationLog.created_at, cut90),
            ("login_log", LoginLog, LoginLog.login_at, cut90),
            ("error_log", ErrorLog, ErrorLog.created_at, cut90),
            ("agent_call_log", AgentCallLog, AgentCallLog.created_at, cut90),
            ("job_execution_log", JobExecutionLog, JobExecutionLog.started_at, cut30),
        ):
            count = db.query(model).filter(column < cutoff).delete(
                synchronize_session=False
            )
            if count:
                removed[name] = count
        notifications = db.query(Notification).filter(
            Notification.is_read.is_(True),
            Notification.created_at < cut30,
        ).delete(synchronize_session=False)
        if notifications:
            removed["notifications"] = notifications
        db.commit()
        if removed:
            logger.info(f"运维数据清理完成: {removed}")
        return removed
    finally:
        db.close()


def publish_scheduled_tasks() -> Dict[str, Any]:
    """定时发布：把 publish_at 已到期的草稿任务激活并补发学生通知。

    create_task 中 publish_at 在未来的任务以 draft 状态落库且不通知学生；
    本任务每分钟扫描一次，到期后置为 published 并补发通知。
    """
    from app.models import Notification

    db = SessionLocal()
    try:
        now = now_local()
        due = db.scalars(
            select(Task).where(
                Task.status == TaskStatus.DRAFT.value,
                Task.publish_at.isnot(None),
                Task.publish_at <= now,
            )
        ).all()
        activated = 0
        notified_total = 0
        for task in due:
            task.status = TaskStatus.PUBLISHED.value
            # 补发学生通知（与 create_task 的通知逻辑一致）
            notify_ids = set(
                db.scalars(
                    select(TaskAssignment.student_id).where(
                        TaskAssignment.task_id == task.id,
                        TaskAssignment.student_id.isnot(None),
                    )
                ).all()
            )
            class_ids = db.scalars(
                select(TaskAssignment.class_id).where(
                    TaskAssignment.task_id == task.id,
                    TaskAssignment.class_id.isnot(None),
                )
            ).all()
            for cid in class_ids:
                notify_ids.update(
                    db.scalars(
                        select(User.id).where(
                            User.class_id == cid, User.status == "active"
                        )
                    ).all()
                )
            end_txt = task.end_at.strftime("%Y-%m-%d %H:%M") if task.end_at else "-"
            for sid in notify_ids:
                db.add(
                    Notification(
                        user_id=sid,
                        title=f"新的{_TYPE_LABEL.get(task.type, '任务')}发布",
                        content=f"{task.title}，截止时间：{end_txt}",
                        type="exam", biz_type="task", biz_id=task.id,
                    )
                )
            db.execute(
                TaskAssignment.__table__.update()
                .where(TaskAssignment.task_id == task.id)
                .values(notified=True)
            )
            activated += 1
            notified_total += len(notify_ids)
        if activated:
            db.commit()
        logger.info(f"定时发布激活 {activated} 个任务，补发通知 {notified_total} 人次")
        return {"activated": activated, "notified": notified_total}
    finally:
        db.close()


# 任务注册表：func_path -> 执行函数
JOB_HANDLERS = {
    "app.services.task_jobs.clean_expired_exams": clean_expired_exams,
    "app.services.task_jobs.generate_daily_report": generate_daily_report,
    "app.services.task_jobs.clean_temp_attachments": clean_temp_attachments,
    "app.services.task_jobs.push_review_reminders": push_review_reminders,
    "app.services.task_jobs.generate_weekly_report": generate_weekly_report,
    "app.services.task_jobs.publish_scheduled_tasks": publish_scheduled_tasks,
    "app.services.task_jobs.clean_old_logs": clean_old_logs,
}


def run_job(func_path: str) -> Dict[str, Any]:
    """按 func_path 执行任务。"""
    handler = JOB_HANDLERS.get(func_path)
    if not handler:
        raise ValueError(f"未找到任务处理函数：{func_path}")
    return handler()
