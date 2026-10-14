"""定时任务执行逻辑（APScheduler 调度）。"""
from datetime import timedelta
from typing import Any, Dict

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.logger import get_logger
from app.models import (
    Answer, Attachment, ReviewPlan, StudyRecord, Submission, Task, TaskStatus,
)
from app.utils.common import utcnow

logger = get_logger("jobs")


def clean_expired_exams() -> Dict[str, Any]:
    """清理过期考试：超过结束时间 30 天未批改的考试归档。"""
    db = SessionLocal()
    try:
        deadline = utcnow() - timedelta(days=30)
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
        yesterday = (utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
        rows = db.scalars(select(StudyRecord).where(StudyRecord.study_date == yesterday)).all()
        active_students = len(rows)
        total_questions = sum(r.question_count for r in rows)
        total_correct = sum(r.correct_count for r in rows)

        subs = db.scalars(
            select(Submission).where(
                func.date(Submission.submit_time) == yesterday,
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
        since = (utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")
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
        deadline = utcnow() - timedelta(days=7)
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
        today = utcnow().strftime("%Y-%m-%d")
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


# 任务注册表：func_path -> 执行函数
JOB_HANDLERS = {
    "app.services.task_jobs.clean_expired_exams": clean_expired_exams,
    "app.services.task_jobs.generate_daily_report": generate_daily_report,
    "app.services.task_jobs.clean_temp_attachments": clean_temp_attachments,
    "app.services.task_jobs.push_review_reminders": push_review_reminders,
    "app.services.task_jobs.generate_weekly_report": generate_weekly_report,
}


def run_job(func_path: str) -> Dict[str, Any]:
    """按 func_path 执行任务。"""
    handler = JOB_HANDLERS.get(func_path)
    if not handler:
        raise ValueError(f"未找到任务处理函数：{func_path}")
    return handler()
