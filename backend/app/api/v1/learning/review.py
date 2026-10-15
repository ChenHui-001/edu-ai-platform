"""学习中心 - 智能复习（艾宾浩斯计划、掌握地图）与随机练习。

由原 1333 行的 api/v1/grading.py 拆分而来，路由前缀 /learning 保持不变。

注意：`/practice/history` 必须注册在 `/practice/{task_id}` 之前，
否则静态路径会被参数路由抢先匹配返回 422。
"""
from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.exception import NotFoundException
from app.models import (
    KnowledgeMastery, KnowledgePoint, Paper, Question, ReviewPlan, Submission,
    Task, User, WrongQuestion,
)
from app.services import grading_service
from app.utils.common import PageParams, dictify, load_json, ok, utcnow

router = APIRouter()

@router.get("/review/plans", summary="我的复习计划")
def review_plans(
    scheduled_date: Optional[str] = None, is_completed: Optional[bool] = None,
    db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    stmt = select(ReviewPlan).where(ReviewPlan.student_id == user.id)
    if scheduled_date:
        stmt = stmt.where(ReviewPlan.scheduled_date == scheduled_date)
    if is_completed is not None:
        stmt = stmt.where(ReviewPlan.is_completed.is_(is_completed))
    rows = db.scalars(stmt.order_by(ReviewPlan.scheduled_date).limit(200)).all()

    items = []
    for p in rows:
        kp = db.get(KnowledgePoint, p.knowledge_point_id)
        wq = db.get(WrongQuestion, p.wrong_question_id) if p.wrong_question_id else None
        q = db.get(Question, wq.question_id) if wq else None
        items.append({
            "id": p.id, "scheduled_date": p.scheduled_date, "stage": p.stage,
            "knowledge_point_id": p.knowledge_point_id,
            "knowledge_point_name": kp.name if kp else None,
            "subject_id": p.subject_id,
            "is_completed": p.is_completed,
            "question_id": wq.question_id if wq else None,
            "stem": q.stem if q else None,
        })

    today = utcnow().strftime("%Y-%m-%d")
    return ok({
        "items": items,
        "today_count": sum(1 for i in items if i["scheduled_date"] == today and not i["is_completed"]),
        "pending_count": sum(1 for i in items if not i["is_completed"]),
        "today": today,
    })


@router.put("/review/plans/{plan_id}/complete", summary="完成复习")
def complete_review(
    plan_id: int, data: Dict[str, Any] = Body(default={}), db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    p = db.get(ReviewPlan, plan_id)
    if not p or p.student_id != user.id:
        raise NotFoundException("复习计划不存在")
    p.is_completed = True
    p.completed_at = utcnow()
    p.correct_rate = data.get("correct_rate")

    # 艾宾浩斯闭环：同一错题累计完成 2 轮即视为掌握。
    # 原实现判断单条计划的 stage >= 2，但计划生成时 stage 恒为 1，
    # 该条件永不成立，错题永远无法被标记为已掌握。
    if p.wrong_question_id:
        finished = db.scalar(
            select(func.count()).select_from(ReviewPlan).where(
                ReviewPlan.student_id == user.id,
                ReviewPlan.wrong_question_id == p.wrong_question_id,
                ReviewPlan.is_completed.is_(True),
            )
        ) or 0
        if finished >= 2:
            w = db.get(WrongQuestion, p.wrong_question_id)
            if w:
                w.is_mastered = True
                w.mastered_at = utcnow()
    db.commit()
    return ok(message="复习完成")


@router.get("/review/mastery", summary="知识点掌握地图")
def mastery_map(
    subject_id: Optional[int] = None, db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(KnowledgeMastery).where(KnowledgeMastery.student_id == user.id)
    if subject_id:
        stmt = stmt.where(KnowledgeMastery.subject_id == subject_id)
    rows = db.scalars(stmt).all()

    data = []
    for m in rows:
        kp = db.get(KnowledgePoint, m.knowledge_point_id)
        if not kp:
            continue
        data.append({
            "knowledge_point_id": kp.id, "name": kp.name,
            "mastery": round(m.mastery, 2), "total_count": m.total_count,
            "correct_count": m.correct_count, "wrong_count": m.wrong_count,
            "level": m.level if hasattr(m, "level") else None,
            "subject_id": m.subject_id,
        })
    data.sort(key=lambda x: x["mastery"])
    weak = [d for d in data if d["mastery"] < 60]
    strong = [d for d in data if d["mastery"] >= 80]
    return ok({
        "items": data,
        "weak_points": weak[:10],
        "strong_points": strong[:10],
        "avg_mastery": round(sum(d["mastery"] for d in data) / len(data), 2) if data else 0,
    })


@router.post("/review/plan", summary="AI 生成复习计划")
def generate_plan(
    data: Dict[str, Any] = Body(default={}), db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    from app.agents.study_agent import StudyPlannerAgent

    agent = StudyPlannerAgent()
    res = agent.run(
        db, user_id=user.id, student_id=user.id,
        days=int(data.get("days", 7)), daily_minutes=int(data.get("daily_minutes", 90)),
    )
    return ok(res.get("data"), message=res.get("message", "计划生成成功"))


# ================================================================ 随机练习
@router.post("/practice", summary="创建随机练习")
def create_practice(
    data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    paper = grading_service.create_practice_paper(
        db, creator_id=user.id,
        grade_id=int(data.get("grade_id", 0)), subject_id=int(data["subject_id"]),
        count=int(data.get("count", 10)),
        question_types=data.get("question_types"),
        difficulty=data.get("difficulty"),
        knowledge_point_ids=data.get("knowledge_point_ids"),
    )
    task = grading_service.create_practice_task(db, user.id, paper)
    return ok({"task_id": task.id, "paper_id": paper.id, "total": len(paper.items)},
              message="练习已生成")


@router.get("/practice/history", summary="练习历史")
def practice_history(
    params: PageParams = Depends(), db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(Task).where(
        Task.type == "practice", Task.creator_id == user.id
    )
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(
        stmt.order_by(Task.created_at.desc()).offset(params.offset).limit(params.page_size)
    ).all()
    items = []
    for t in rows:
        sub = db.scalar(
            select(Submission).where(
                Submission.task_id == t.id, Submission.student_id == user.id
            ).limit(1)
        )
        items.append({
            "task_id": t.id, "name": t.title, "created_at": dictify(t.created_at),
            "score": sub.score if sub else None,
            "total_score": t.total_score,
            "accuracy": round((sub.score / t.total_score) * 100, 2) if sub and t.total_score else 0,
        })
    return ok({"items": items, "total": total, "page": params.page})


# 注意：/practice/history 必须注册在 /practice/{task_id} 之前，
# 否则 FastAPI 会把 "history" 当作 task_id 解析并返回 422。
@router.get("/practice/{task_id}", summary="获取练习题目")
def get_practice(
    task_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    task = db.get(Task, task_id)
    if not task:
        raise NotFoundException("练习不存在")
    paper = db.get(Paper, task.paper_id)
    items = [
        {
            "paper_item_id": it.id, "question_id": it.question_id,
            "sort_order": it.sort_order, "score": it.score, "section_name": it.section_name,
            "type": it.question.type, "stem": it.question.stem,
            "options": load_json(it.question.options),
        }
        for it in sorted(paper.items, key=lambda x: x.sort_order)
    ]
    return ok({
        "task_id": task.id, "name": paper.name, "duration": task.duration,
        "total_score": task.total_score, "items": items,
    })
