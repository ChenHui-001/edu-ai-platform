"""数据报表接口：学生端、教师端、管理员端。"""
import io
from datetime import timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, Query
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from sqlalchemy import case, desc, func, or_, select
from sqlalchemy.orm import Session

from app.api.deps import (
    DataScope, get_current_admin, get_current_manager, get_current_teacher,
    get_current_user, get_data_scope,
)
from app.core.database import get_db
from app.core.exception import BusinessException, NotFoundException
from app.models import (
    AgentCallLog, Answer, Class, ErrorLog, Grade, KnowledgeMastery, KnowledgePoint,
    Note, Paper, Question, StudyRecord, Submission, Subject, Task, User, WrongQuestion,
)
from app.utils.common import PageParams, dictify, ok, utcnow

router = APIRouter(prefix="/report", tags=["数据报表"])


# ================================================================ 学生端
@router.get("/student/overview", summary="个人学习总览")
def student_overview(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    today = utcnow().strftime("%Y-%m-%d")
    since7 = (utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")
    since30 = (utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")

    def _study(days_field: str = "7"):
        return db.scalar(
            select(func.coalesce(func.sum(StudyRecord.study_seconds), 0)).where(
                StudyRecord.student_id == user.id, StudyRecord.study_date >= days_field
            )
        ) or 0

    total_q = db.scalar(
        select(func.coalesce(func.sum(StudyRecord.question_count), 0)).where(
            StudyRecord.student_id == user.id
        )
    ) or 0
    total_right = db.scalar(
        select(func.coalesce(func.sum(StudyRecord.correct_count), 0)).where(
            StudyRecord.student_id == user.id
        )
    ) or 0

    subs = db.scalars(
        select(Submission).where(
            Submission.student_id == user.id, Submission.score.isnot(None)
        )
    ).all()

    return ok({
        "student": {"id": user.id, "name": user.real_name, "class_id": user.class_id},
        "study_minutes_today": _study(today) // 60,
        "study_minutes_7d": _study(since7) // 60,
        "study_minutes_30d": _study(since30) // 60,
        "question_total": total_q,
        "accuracy": round(total_right / total_q * 100, 2) if total_q else 0,
        "wrong_unmastered": db.scalar(
            select(func.count()).select_from(WrongQuestion).where(
                WrongQuestion.student_id == user.id, WrongQuestion.is_mastered.is_(False)
            )
        ) or 0,
        "wrong_mastered": db.scalar(
            select(func.count()).select_from(WrongQuestion).where(
                WrongQuestion.student_id == user.id, WrongQuestion.is_mastered.is_(True)
            )
        ) or 0,
        "note_count": db.scalar(
            select(func.count()).select_from(Note).where(Note.student_id == user.id)
        ) or 0,
        "exam_count": len(subs),
        "avg_score": round(sum(s.score for s in subs) / len(subs), 2) if subs else 0,
        "pass_count": sum(1 for s in subs if s.is_passed),
    })


@router.get("/student/score-trend", summary="成绩趋势")
def score_trend(
    limit: int = Query(20, le=100), db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    subs = db.scalars(
        select(Submission).where(
            Submission.student_id == user.id, Submission.score.isnot(None)
        ).order_by(Submission.id).limit(limit)
    ).all()
    items = []
    for s in subs:
        task = db.get(Task, s.task_id)
        items.append({
            "id": s.id, "name": task.title if task else "练习",
            "type": task.type if task else "practice",
            "score": s.score, "total_score": task.total_score if task else None,
            "rate": round(s.score / task.total_score * 100, 2) if task and task.total_score else 0,
            "class_rank": s.class_rank, "date": dictify(s.submit_time),
        })
    return ok(items)


@router.get("/student/knowledge-radar", summary="知识点掌握雷达图")
def knowledge_radar(
    subject_id: Optional[int] = None, db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(KnowledgeMastery).where(KnowledgeMastery.student_id == user.id)
    if subject_id:
        stmt = stmt.where(KnowledgeMastery.subject_id == subject_id)
    rows = db.scalars(stmt).all()

    items = []
    for m in rows:
        kp = db.get(KnowledgePoint, m.knowledge_point_id)
        if kp:
            items.append({"id": kp.id, "name": kp.name, "mastery": round(m.mastery, 2)})
    items.sort(key=lambda x: x["mastery"])
    return ok(items[:20])


@router.get("/student/wrong-analysis", summary="错题分析")
def wrong_analysis(
    subject_id: Optional[int] = None, db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    base = select(WrongQuestion).where(WrongQuestion.student_id == user.id)
    if subject_id:
        base = base.where(WrongQuestion.subject_id == subject_id)

    reason_dist = db.execute(
        select(WrongQuestion.error_reason, func.count()).where(
            WrongQuestion.student_id == user.id
        ).group_by(WrongQuestion.error_reason)
    ).all()

    kp_rank = db.execute(
        select(KnowledgePoint.name, func.count())
        .join(WrongQuestion, WrongQuestion.knowledge_point_id == KnowledgePoint.id)
        .where(WrongQuestion.student_id == user.id)
        .group_by(KnowledgePoint.name)
        .order_by(desc(func.count()))
        .limit(10)
    ).all()

    since = (utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")
    trend = db.execute(
        select(WrongQuestion.last_wrong_at, func.count())
        .where(WrongQuestion.student_id == user.id, WrongQuestion.last_wrong_at >= since)
        .group_by(func.date(WrongQuestion.last_wrong_at))
        .order_by(func.date(WrongQuestion.last_wrong_at))
    ).all()

    return ok({
        "reason_distribution": [
            {"reason": r or "未标注", "count": c} for r, c in reason_dist
        ],
        "knowledge_rank": [{"name": n, "count": c} for n, c in kp_rank],
        "trend": [{"date": str(d), "count": c} for d, c in trend],
        "total": db.scalar(select(func.count()).select_from(base.subquery())) or 0,
    })


@router.get("/student/learning-suggestion", summary="个性化学习建议")
def learning_suggestion(
    db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    from app.agents.study_agent import StudyPlannerAgent

    res = StudyPlannerAgent().run(db, user_id=user.id, student_id=user.id, days=7)
    data = res.get("data") or {}
    return ok({
        "summary": data.get("summary"),
        "weak_points": data.get("weak_points", []),
        "advice": data.get("advice", []),
        "daily_plan": data.get("daily_plan", [])[:3],
    })


# ================================================================ 教师端
@router.get("/teacher/class-overview", summary="班级学情概览")
def class_overview(
    class_id: int, task_id: Optional[int] = None, db: Session = Depends(get_db),
    _: User = Depends(get_current_teacher), scope: DataScope = Depends(get_data_scope),
):
    if not scope.is_super:
        allowed = scope.class_ids()
        if allowed is not None and class_id not in allowed:
            raise BusinessException("无权查看该班级数据")

    k = db.get(Class, class_id)
    if not k:
        raise NotFoundException("班级不存在")
    students = db.scalars(select(User).where(User.class_id == class_id)).all()

    stmt = select(Submission).where(
        Submission.student_id.in_([s.id for s in students] or [0]),
        Submission.score.isnot(None),
    )
    if task_id:
        stmt = stmt.where(Submission.task_id == task_id)
    subs = db.scalars(stmt).all()
    scores = [s.score for s in subs]

    # 完成率
    tasks = db.scalars(
        select(Task).where(Task.grade_id == k.grade_id, Task.type != "practice")
    ).all()

    return ok({
        "class": {"id": k.id, "name": k.name, "grade_id": k.grade_id},
        "student_count": len(students),
        "submission_count": len(subs),
        "avg_score": round(sum(scores) / len(scores), 2) if scores else 0,
        "max_score": max(scores) if scores else 0,
        "min_score": min(scores) if scores else 0,
        "pass_rate": round(sum(1 for s in scores if s >= 60) / len(scores) * 100, 2) if scores else 0,
        "score_bands": _score_bands(scores),
        "active_students": len({s.student_id for s in subs}),
    })


def _score_bands(scores: List[float]) -> Dict[str, int]:
    bands = {"90-100": 0, "80-89": 0, "70-79": 0, "60-69": 0, "<60": 0}
    for s in scores:
        if s >= 90: bands["90-100"] += 1
        elif s >= 80: bands["80-89"] += 1
        elif s >= 70: bands["70-79"] += 1
        elif s >= 60: bands["60-69"] += 1
        else: bands["<60"] += 1
    return bands


@router.get("/teacher/student-comparison", summary="学生横向对比")
def student_comparison(
    class_id: int, task_id: Optional[int] = None, db: Session = Depends(get_db),
    _: User = Depends(get_current_teacher),
):
    students = db.scalars(select(User).where(User.class_id == class_id)).all()
    rows = []
    for s in students:
        stmt = select(Submission).where(
            Submission.student_id == s.id, Submission.score.isnot(None)
        )
        if task_id:
            stmt = stmt.where(Submission.task_id == task_id)
        subs = db.scalars(stmt).all()
        scores = [x.score for x in subs]
        wrong = db.scalar(
            select(func.count()).select_from(WrongQuestion).where(
                WrongQuestion.student_id == s.id, WrongQuestion.is_mastered.is_(False)
            )
        ) or 0
        rows.append({
            "student_id": s.id, "name": s.real_name, "username": s.username,
            "submit_count": len(subs),
            "avg_score": round(sum(scores) / len(scores), 2) if scores else 0,
            "max_score": max(scores) if scores else 0,
            "wrong_count": wrong,
            "completion_rate": 100.0 if subs else 0,
        })
    rows.sort(key=lambda x: x["avg_score"], reverse=True)
    for i, r in enumerate(rows, start=1):
        r["rank"] = i
    return ok(rows)


@router.get("/teacher/student-detail", summary="学生个体分析")
def student_detail(
    student_id: int, db: Session = Depends(get_db),
    _: User = Depends(get_current_teacher),
):
    stu = db.get(User, student_id)
    if not stu:
        raise NotFoundException("学生不存在")

    subs = db.scalars(
        select(Submission).where(
            Submission.student_id == student_id, Submission.score.isnot(None)
        ).order_by(Submission.id)
    ).all()

    masteries = db.scalars(
        select(KnowledgeMastery).where(KnowledgeMastery.student_id == student_id)
    ).all()
    kp_items = []
    for m in masteries:
        kp = db.get(KnowledgePoint, m.knowledge_point_id)
        if kp:
            kp_items.append({"name": kp.name, "mastery": round(m.mastery, 2)})
    kp_items.sort(key=lambda x: x["mastery"])

    wrong = db.scalars(
        select(WrongQuestion).where(
            WrongQuestion.student_id == student_id, WrongQuestion.is_mastered.is_(False)
        ).limit(20)
    ).all()

    return ok({
        "student": {
            "id": stu.id, "name": stu.real_name, "username": stu.username,
            "class_id": stu.class_id, "grade_id": stu.grade_id,
        },
        "score_trend": [
            {
                "name": (db.get(Task, s.task_id).title if db.get(Task, s.task_id) else ""),
                "score": s.score, "rank": s.class_rank,
                "date": dictify(s.submit_time),
            }
            for s in subs
        ],
        "knowledge_mastery": kp_items,
        "weak_points": kp_items[:5],
        "wrong_questions": [
            {"id": w.id, "question_id": w.question_id, "error_count": w.error_count,
             "error_reason": w.error_reason}
            for w in wrong
        ],
        "summary": {
            "submit_count": len(subs),
            "avg_score": round(sum(s.score for s in subs) / len(subs), 2) if subs else 0,
        },
    })


@router.get("/teacher/knowledge-effect", summary="知识点教学效果评估")
def knowledge_effect(
    subject_id: Optional[int] = None, db: Session = Depends(get_db),
    _: User = Depends(get_current_teacher),
):
    stmt = (
        select(
            KnowledgePoint.name,
            func.count(Answer.id),
            func.sum(case((Answer.is_correct.is_(True), 1), else_=0)),
        )
        .join(Question, Question.knowledge_point_id == KnowledgePoint.id)
        .join(Answer, Answer.question_id == Question.id)
    )
    if subject_id:
        stmt = stmt.where(Question.subject_id == subject_id)
    rows = db.execute(stmt.group_by(KnowledgePoint.name)).all()

    items = []
    for name, total, right in rows:
        acc = round((right or 0) / total * 100, 2) if total else 0
        items.append({"name": name, "answer_count": total, "accuracy": acc})
    items.sort(key=lambda x: x["accuracy"])
    return ok({
        "items": items,
        "weak": items[:5],
        "good": list(reversed(items[-5:])),
        "avg_accuracy": round(sum(i["accuracy"] for i in items) / len(items), 2) if items else 0,
    })


# ================================================================ 管理员端
@router.get("/admin/overview", summary="系统总览")
def admin_overview(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_manager),
):
    # 参数名必须为 user：export_excel 会以 admin_overview(db, user=...) 复用本函数
    def _count(model, *where):
        stmt = select(func.count()).select_from(model)
        for w in where:
            stmt = stmt.where(w)
        return db.scalar(stmt) or 0

    from app.models import Note

    since7 = utcnow() - timedelta(days=7)
    active_7d = db.scalar(
        select(func.count(func.distinct(User.id))).where(User.last_login_at >= since7)
    ) or 0

    subs = db.scalars(
        select(Submission).where(Submission.score.isnot(None))
    ).all()

    return ok({
        "user": {
            "total": _count(User),
            "student": _count(User, User.identity == "student"),
            "teacher": _count(User, User.identity == "teacher"),
            "active_7d": active_7d,
            "pending": _count(User, User.status == "pending"),
        },
        "content": {
            "question": _count(Question),
            "published_question": _count(Question, Question.status == "published"),
            "paper": _count(Paper),
            "note": _count(Note),
            "knowledge_point": _count(KnowledgePoint),
        },
        "exam": {
            "task": _count(Task),
            "submission": _count(Submission),
            "avg_score": round(sum(s.score for s in subs) / len(subs), 2) if subs else 0,
        },
        "ai": {
            "calls": _count(AgentCallLog),
            "failed": _count(AgentCallLog, AgentCallLog.status == "failed"),
            "fallback": _count(AgentCallLog, AgentCallLog.is_fallback.is_(True)),
        },
        "org": {"grade": _count(Grade), "subject": _count(Subject), "class": _count(Class)},
    })


@router.get("/admin/grade-comparison", summary="各年级教学数据对比")
def grade_comparison(db: Session = Depends(get_db), _: User = Depends(get_current_manager)):
    rows = db.execute(
        select(
            Grade.name,
            func.count(func.distinct(Question.id)),
            func.count(func.distinct(Submission.id)),
        )
        .select_from(Grade)
        .outerjoin(Question, Question.grade_id == Grade.id)
        .outerjoin(Submission, Submission.task_id.in_(select(Task.id).where(Task.grade_id == Grade.id)))
        .group_by(Grade.name)
        .order_by(Grade.grade_num)
    ).all()

    items = []
    for name, q_count, s_count in rows:
        subs = db.scalars(
            select(Submission).join(Task, Task.id == Submission.task_id)
            .where(Task.grade_id == select(Grade.id).where(Grade.name == name).scalar_subquery(),
                   Submission.score.isnot(None))
        ).all()
        scores = [s.score for s in subs]
        users = db.scalar(
            select(func.count()).select_from(User).where(
                User.grade_id == select(Grade.id).where(Grade.name == name).scalar_subquery()
            )
        ) or 0
        items.append({
            "grade_name": name, "question_count": q_count or 0,
            "submission_count": s_count or 0, "user_count": users,
            "avg_score": round(sum(scores) / len(scores), 2) if scores else 0,
        })
    return ok(items)


@router.get("/admin/subject-comparison", summary="各学科教学数据对比")
def subject_comparison(db: Session = Depends(get_db), _: User = Depends(get_current_manager)):
    rows = db.execute(
        select(
            Subject.name,
            func.count(func.distinct(Question.id)),
            func.count(func.distinct(Note.id)),
        )
        .select_from(Subject)
        .outerjoin(Question, Question.subject_id == Subject.id)
        .outerjoin(Note, Note.subject_id == Subject.id)
        .group_by(Subject.name)
    ).all()
    return ok([{"subject": n, "question_count": q or 0, "note_count": c or 0} for n, q, c in rows])


@router.get("/admin/system-runtime", summary="系统运行报表")
def system_runtime(db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    from app.services.scheduler import scheduler_status

    since = utcnow() - timedelta(days=1)
    return ok({
        "scheduler": scheduler_status(),
        "ai_calls_24h": db.scalar(
            select(func.count()).select_from(AgentCallLog).where(AgentCallLog.created_at >= since)
        ) or 0,
        "ai_failed_24h": db.scalar(
            select(func.count()).select_from(AgentCallLog).where(
                AgentCallLog.created_at >= since, AgentCallLog.status == "failed"
            )
        ) or 0,
        "api_error_24h": db.scalar(
            select(func.count()).select_from(ErrorLog).where(
                ErrorLog.created_at >= since
            )
        ) or 0,
    })


# ================================================================ 导出
@router.get("/export/excel", summary="报表导出 Excel")
def export_excel(
    report_type: str = Query(..., description="student_overview / class_overview / admin_overview"),
    class_id: Optional[int] = None,
    student_id: Optional[int] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    wb = Workbook()
    ws = wb.active
    ws.title = "报表"

    if report_type == "student_overview":
        data = student_overview(db, user)["data"]
        ws.append(["个人学习总览"])
        ws.append([])
        for k, v in data.get("student", {}).items():
            ws.append([k, v])
        for k in ("study_minutes_7d", "question_total", "accuracy", "wrong_unmastered",
                  "wrong_mastered", "note_count", "exam_count", "avg_score", "pass_count"):
            ws.append([k, data.get(k)])
    elif report_type == "class_overview" and class_id:
        data = class_overview(class_id, db=db, user=user, scope=_scope_for(user, db))["data"]
        ws.append([f"班级学情报表 - {data['class']['name']}"])
        ws.append([])
        for k, v in data.items():
            if isinstance(v, dict):
                ws.append([k, json_dumps(v)])
            else:
                ws.append([k, v])
    else:
        data = admin_overview(db, user=_as_admin(user))["data"]
        ws.append(["系统总览报表"])
        ws.append([])
        for section, vals in data.items():
            ws.append([f"【{section}】"])
            if isinstance(vals, dict):
                for k, v in vals.items():
                    ws.append([k, v])
            else:
                ws.append([section, vals])
            ws.append([])

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return StreamingResponse(
        buf, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=report_{report_type}.xlsx"},
    )


def json_dumps(v: Any) -> str:
    import json

    return json.dumps(v, ensure_ascii=False)


def _as_admin(user: User) -> User:
    return user


def _scope_for(user: User, db: Session) -> DataScope:
    return DataScope(user, db)
