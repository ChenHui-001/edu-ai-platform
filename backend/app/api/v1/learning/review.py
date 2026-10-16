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
from app.core.exception import BusinessException, NotFoundException
from app.models import (
    KnowledgeMastery, KnowledgePoint, Paper, Question, ReviewPlan, Submission,
    Task, TaskAssignment, User, WrongQuestion,
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
    # 统计基于全量（不带 limit），否则计划多于 200 条时 pending_count 恒为
    # 截断集内的数量，页面永远提示「还有未完成复习」但不显示是哪些。
    pending_total = db.scalar(
        select(func.count()).select_from(stmt.subquery()).where(
            ReviewPlan.is_completed.is_(False))
    ) or 0
    today = utcnow().strftime("%Y-%m-%d")
    today_total = db.scalar(
        select(func.count()).select_from(stmt.subquery()).where(
            ReviewPlan.is_completed.is_(False),
            ReviewPlan.scheduled_date == today)
    ) or 0

    # 批量预取（此前每条计划 3 次 db.get，200 条 = 600 次查询）
    kp_ids = {p.knowledge_point_id for p in rows if p.knowledge_point_id}
    wq_ids = {p.wrong_question_id for p in rows if p.wrong_question_id}
    kp_map = {k.id: k for k in db.scalars(
        select(KnowledgePoint).where(KnowledgePoint.id.in_(kp_ids))).all()} if kp_ids else {}
    wq_map = {w.id: w for w in db.scalars(
        select(WrongQuestion).where(WrongQuestion.id.in_(wq_ids))).all()} if wq_ids else {}
    q_ids = {w.question_id for w in wq_map.values()}
    q_map = {q.id: q for q in db.scalars(
        select(Question).where(Question.id.in_(q_ids))).all()} if q_ids else {}

    items = []
    for p in rows:
        kp = kp_map.get(p.knowledge_point_id)
        wq = wq_map.get(p.wrong_question_id) if p.wrong_question_id else None
        q = q_map.get(wq.question_id) if wq else None
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
        "today_count": today_total,
        "pending_count": pending_total,
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

    kp_ids = {m.knowledge_point_id for m in rows}
    kp_map = {k.id: k for k in db.scalars(
        select(KnowledgePoint).where(KnowledgePoint.id.in_(kp_ids))).all()} if kp_ids else {}
    data = []
    for m in rows:
        kp = kp_map.get(m.knowledge_point_id)
        if not kp:
            continue
        data.append({
            "knowledge_point_id": kp.id, "name": kp.name,
            "mastery": round(m.mastery, 2), "total_count": m.total_count,
            "correct_count": m.correct_count, "wrong_count": m.wrong_count,
            "level": ("excellent" if m.mastery >= 80 else
                      "good" if m.mastery >= 60 else
                      "pass" if m.mastery >= 40 else "weak"),
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
    # 参数边界：负数/超大值会生成异常计划或拖垮 AI 调用
    try:
        days = max(1, min(int(data.get("days", 7)), 30))
        daily_minutes = max(10, min(int(data.get("daily_minutes", 90)), 600))
    except (TypeError, ValueError):
        raise BusinessException("days / daily_minutes 必须是整数")
    res = agent.run(
        db, user_id=user.id, student_id=user.id,
        days=days, daily_minutes=daily_minutes,
    )
    return ok(res.get("data"), message=res.get("message", "计划生成成功"))


# ================================================================ 随机练习
@router.post("/practice", summary="创建随机练习")
def create_practice(
    data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    subject_id = data.get("subject_id")
    if not subject_id:
        raise BusinessException("请选择学科")
    try:
        count = int(data.get("count", 10))
    except (TypeError, ValueError):
        raise BusinessException("题目数量必须是整数")
    # 边界保护：count 无上限时一次生成上千题的卷子，拖垮交卷与判分
    count = max(1, min(count, 50))
    # grade_id=0 会撞非空外键（IntegrityError 500），缺省回落学生年级
    grade_id = int(data.get("grade_id") or user.grade_id or 0) or None
    if not grade_id:
        raise BusinessException("无法确定年级，请先完善个人信息")
    paper = grading_service.create_practice_paper(
        db, creator_id=user.id,
        grade_id=grade_id, subject_id=int(subject_id),
        count=count,
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
    # 批量取本人提交（此前每条任务一次查询）
    task_ids = [t.id for t in rows]
    sub_map = {}
    if task_ids:
        for sub in db.scalars(
            select(Submission).where(
                Submission.task_id.in_(task_ids), Submission.student_id == user.id,
                Submission.submit_time.isnot(None),
            ).order_by(Submission.submit_time.desc())
        ).all():
            sub_map.setdefault(sub.task_id, sub)

    items = []
    for t in rows:
        sub = sub_map.get(t.id)
        items.append({
            "task_id": t.id, "submission_id": sub.id if sub else None,
            "name": t.title, "created_at": dictify(t.created_at),
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
    # 归属与类型双重校验：
    # 1) 仅 practice 类型可经此入口获取 —— 此前无任何校验，
    #    学生遍历 task_id 可绕过 /task/tasks/{id}/paper 的发布时间
    #    与下发范围管控，提前拿到未发布考试的题目（实测泄露）。
    # 2) 仅创建者本人或被下发者可访问（防 IDOR/枚举）。
    if not task or task.type != "practice":
        raise NotFoundException("练习不存在")
    if task.creator_id != user.id and not db.scalar(
        select(TaskAssignment.id).where(
            TaskAssignment.task_id == task.id,
            TaskAssignment.student_id == user.id,
        )
    ):
        raise NotFoundException("练习不存在")
    paper = db.get(Paper, task.paper_id)
    if not paper:
        raise NotFoundException("练习试卷不存在")
    items = [
        {
            "paper_item_id": it.id, "question_id": it.question_id,
            "sort_order": it.sort_order, "score": it.score, "section_name": it.section_name,
            "type": it.question.type, "stem": it.question.stem,
            "options": load_json(it.question.options),
        }
        for it in sorted(paper.items, key=lambda x: x.sort_order)
        if it.question is not None
    ]
    return ok({
        "task_id": task.id, "name": paper.name, "duration": task.duration,
        "total_score": task.total_score, "items": items,
    })
