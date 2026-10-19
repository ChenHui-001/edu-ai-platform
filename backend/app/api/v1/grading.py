"""智能批改中心接口（/api/v1/grading/*）。

原先本文件还混放了学习中心的全部端点（笔记 / 错题本 / 复习 / 练习 /
收藏等），已拆分至 `app/api/v1/learning/` 子包，本文件只保留批改中心。
`learning_router` 作为兼容别名继续从这里导出，`api/router.py` 无需改动。
"""
import json
from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import (
    DataScope, get_current_teacher, get_data_scope,
)
from app.core.config import settings
from app.core.database import get_db
from app.core.exception import BusinessException, NotFoundException, PermissionException
from app.models import Answer, KnowledgePoint, Paper, Submission, Task, User
from app.services import grading_service
from app.utils.common import PageParams, dictify, load_json, ok, utcnow

from .learning import learning_router  # noqa: F401  兼容旧导出路径

grading_router = APIRouter(prefix="/grading", tags=["智能批改"])

@grading_router.get("/pending", summary="待批改列表")
def pending_submissions(
    params: PageParams = Depends(), task_id: Optional[int] = None,
    class_id: Optional[int] = None, include_graded: bool = False,
    db: Session = Depends(get_db), user: User = Depends(get_current_teacher),
    scope: DataScope = Depends(get_data_scope),
):
    stmt = select(Submission).join(Task, Task.id == Submission.task_id).where(
        Task.status != "archived"
    )
    # 默认只返回「待批改」：已完全批改/已发布的不进队列
    # （此前已批改 100/100 的记录也躺在待批列表里，语义矛盾）。
    # include_graded=true 时返回全部（批改中心想看历史记录时用）。
    if not include_graded:
        stmt = stmt.where(Submission.status.notin_(("fully_graded", "published")))
    if not scope.is_super:
        stmt = stmt.where(Task.creator_id == user.id)
    if task_id:
        stmt = stmt.where(Submission.task_id == task_id)
    if class_id:
        stmt = stmt.where(Submission.student_id.in_(
            select(User.id).where(User.class_id == class_id)
        ))

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(
        stmt.order_by(Submission.id.desc()).offset(params.offset).limit(params.page_size)
    ).all()
    items = []
    for s in rows:
        task = db.get(Task, s.task_id)
        stu = db.get(User, s.student_id)
        items.append({
            # submission_id 是权威字段；id 作为别名一并返回。
            # 前端列表用item.id 做key / 拼详情 URL，若只给 submission_id
            # 会取到 undefined，导致详情接口报 422 / 前端提示「未找到该提交记录」。
            "id": s.id, "submission_id": s.id, "task_id": s.task_id,
            "task_title": task.title if task else None,
            "student_id": s.student_id, "student_name": stu.real_name if stu else "",
            "class_id": stu.class_id if stu else None,
            "total_score": task.total_score if task else 0,
            "score": s.score, "objective_score": s.objective_score,
            "subjective_score": s.subjective_score, "status": s.status,
            "class_rank": s.class_rank, "is_passed": s.is_passed,
            "needs_manual": bool(s.subjective_score and s.subjective_score > 0),
            "submit_time": dictify(s.submit_time),
        })
    return ok({"items": items, "total": total, "page": params.page})


@grading_router.get("/submissions/{submission_id}", summary="批改详情")
def grading_detail(
    submission_id: int, db: Session = Depends(get_db),
    _: User = Depends(get_current_teacher),
):
    from app.models import Question

    sub = db.get(Submission, submission_id)
    if not sub:
        raise NotFoundException("作答记录不存在")
    task = db.get(Task, sub.task_id)
    paper = db.get(Paper, task.paper_id) if task else None

    items = []
    for a in sub.answers:
        q = db.get(Question, a.question_id)
        kp = db.get(KnowledgePoint, q.knowledge_point_id) if q and q.knowledge_point_id else None
        items.append({
            "answer_id": a.id, "paper_item_id": a.paper_item_id,
            "question_id": a.question_id, "type": q.type if q else None,
            "stem": q.stem if q else "", "options": load_json(q.options) if q else None,
            "standard_answer": load_json(q.answer) if q else None,
            "analysis": q.analysis if q else None,
            "knowledge_point_name": kp.name if kp else None,
            "content": a.content, "is_correct": a.is_correct,
            "score": a.score, "full_score": a.full_score, "grader_type": a.grader_type,
            "teacher_comment": a.teacher_comment, "ai_comment": a.ai_comment,
            "ai_error_points": load_json(a.ai_error_points),
        })

    stu = db.get(User, sub.student_id)
    # 未批改态（打回后）不展示残留分数：历史脏数据（reject 未清分时代）
    # 会在批改面板显示「主观 83 分 / 未批改」的矛盾信息。
    pending_state = sub.status in ("not_graded", None)
    if pending_state:
        for it in items:
            it["score"] = None
            it["is_correct"] = None
            it["teacher_comment"] = None
    return ok({
        "submission_id": sub.id, "task_id": sub.task_id,
        "task_title": task.title if task else None,
        "student": {"id": stu.id, "name": stu.real_name, "class_id": stu.class_id} if stu else None,
        "score": None if pending_state else sub.score,
        "objective_score": 0 if pending_state else sub.objective_score,
        "subjective_score": 0 if pending_state else sub.subjective_score,
        "status": sub.status,
        "total_score": task.total_score if task else 0,
        "items": items,
    })


@grading_router.post("/submissions/{submission_id}/grade", summary="手动批改 / 采纳 AI 建议")
def grade_submission(
    submission_id: int, data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    user: User = Depends(get_current_teacher), scope: DataScope = Depends(get_data_scope),
):
    sub = db.get(Submission, submission_id)
    if not sub:
        raise NotFoundException("作答记录不存在")
    task = db.get(Task, sub.task_id)
    # 数据范围校验：只有任务创建者（或管理员）可批改
    if task and not scope.is_super and task.creator_id != user.id:
        raise PermissionException("只能批改自己发布的任务")

    # 前后端契约：前端 GradingCenter 发 {answers: [{answer_id, score,
    # teacher_comment}]}，后端原读 items+comment——键名全不匹配导致
    # 循环空转、分数从未保存（页面却提示「已保存」）。双键名兼容。
    items = data.get("items") or data.get("answers") or []
    for it in items:
        ans = db.get(Answer, it["answer_id"])
        if not ans or ans.submission_id != submission_id:
            continue
        if "score" in it:
            ans.score = max(0.0, min(float(it["score"]), float(ans.full_score)))
        comment = it.get("teacher_comment", it.get("comment"))
        if comment is not None:
            ans.teacher_comment = comment
            ans.grader_type = "manual"
        if ans.score is not None:
            ans.is_correct = ans.score >= float(ans.full_score) * settings.PASS_SCORE / 100

    db.flush()

    # 重算总分与状态。口径：auto=客观题机器判分 → objective_score；
    # manual（教师手批）与 ai（AI 辅助）均属主观题判分 → subjective_score。
    # 此前把 manual 计入 objective、ai 计入 subjective，口径相反。
    answers = db.scalars(select(Answer).where(Answer.submission_id == submission_id)).all()
    objective = sum(a.score or 0 for a in answers if a.grader_type == "auto")
    subjective = sum(a.score or 0 for a in answers if a.grader_type in ("ai", "manual"))
    sub.objective_score = objective
    sub.subjective_score = subjective
    sub.score = round(objective + subjective, 2)
    sub.is_passed = sub.score >= (task.pass_score if task else settings.PASS_SCORE)
    sub.status = "fully_graded"
    sub.grade_time = utcnow()

    if data.get("reject"):
        sub.status = "not_graded"

    db.commit()
    return ok({"score": sub.score, "status": sub.status}, message="批改已保存")


@grading_router.post("/submissions/{submission_id}/reject", summary="打回重做")
def reject_submission(
    submission_id: int, data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    user: User = Depends(get_current_teacher), scope: DataScope = Depends(get_data_scope),
):
    sub = db.get(Submission, submission_id)
    if not sub:
        raise NotFoundException("作答记录不存在")
    task = db.get(Task, sub.task_id)
    if task and not scope.is_super and task.creator_id != user.id:
        raise PermissionException("只能打回自己发布任务的提交")
    sub.status = "not_graded"
    sub.score = None
    # 打回后各题得分/评语一并清空，否则「客观/主观分」残留旧值，
    # 批改面板显示与实际状态矛盾（实测打回后仍显示客观 0/主观 83）。
    for a in db.scalars(select(Answer).where(Answer.submission_id == submission_id)).all():
        a.score = None
        a.is_correct = None
        a.teacher_comment = None
        # grader_type 是非空列（Mapped[str]），置 None 会触发约束错误
        # 导致整个 reject 事务回滚（打回后分数清不掉的真实原因）
        a.grader_type = "auto"
    sub.objective_score = 0
    sub.subjective_score = 0
    sub.is_passed = None
    sub.grade_time = None
    sub.comment = data.get("reason", "答案不合格，请重新提交")
    db.add(__import__("app.models", fromlist=["Notification"]).Notification(
        user_id=sub.student_id, title="作业被退回",
        content=f"《{db.get(Task, sub.task_id).title}》被退回：{sub.comment}",
        type="system", biz_type="task", biz_id=sub.task_id,
    ))
    db.commit()
    return ok(message="已打回，学生可重新提交")


@grading_router.post("/submissions/{submission_id}/publish", summary="发布成绩")
def publish_score(
    submission_id: int, db: Session = Depends(get_db),
    user: User = Depends(get_current_teacher), scope: DataScope = Depends(get_data_scope),
):
    from app.models import Notification

    sub = db.get(Submission, submission_id)
    if not sub:
        raise NotFoundException("作答记录不存在")
    task = db.get(Task, sub.task_id)
    if task and not scope.is_super and task.creator_id != user.id:
        raise PermissionException("只能发布自己发布任务的成绩")
    # 未批改的提交没有有效分数，发布出去学生会看到 None/0 分
    if sub.score is None:
        raise BusinessException("该提交尚未完成批改，无法发布成绩")
    sub.status = "published"
    db.add(Notification(
        user_id=sub.student_id, title="成绩已发布",
        content=f"《{task.title}》成绩：{sub.score} 分，班级排名第 {sub.class_rank or '-'} 名",
        type="system", biz_type="task", biz_id=sub.task_id,
    ))
    db.commit()
    return ok(message="成绩已发布")


@grading_router.post("/tasks/{task_id}/report", summary="生成班级学情报告")
def class_report(
    task_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_teacher),
):
    task = db.get(Task, task_id)
    if not task:
        raise NotFoundException("任务不存在")
    sub = db.scalar(
        select(Submission).where(
            Submission.task_id == task_id, Submission.score.isnot(None)
        ).limit(1)
    )
    if not sub:
        raise BusinessException("暂无可用于分析的已批改记录")
    report = grading_service.grade_summary(db, sub)
    report["task_title"] = task.title
    return ok(report)


@grading_router.post("/tasks/{task_id}/ai-comment", summary="AI 生成学情教学建议")
def ai_teaching_advice(
    task_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_teacher),
):
    from app.agents.base import get_orchestrator

    task = db.get(Task, task_id)
    if not task:
        raise NotFoundException("任务不存在")
    sub = db.scalar(
        select(Submission).where(
            Submission.task_id == task_id, Submission.score.isnot(None)
        ).limit(1)
    )
    if not sub:
        raise BusinessException("暂无已批改记录")
    report = grading_service.grade_summary(db, sub)

    orch = get_orchestrator()
    from app.agents.tutor_agent import TutorAgent

    tutor = TutorAgent()
    prompt_data = json.dumps(report, ensure_ascii=False, default=str)[:3000]
    res = tutor.call_llm(
        f"以下是《{task.title}》的班级学情数据，请生成教学重点与改进建议：\n{prompt_data}",
        db=db, user_id=user.id, biz_type="analysis",
    )
    if res["success"] and res.get("raw"):
        return ok({"advice": res["raw"], "report": report})
    return ok({
        "advice": (
            f"班级平均分 {report.get('avg_score', 0)} 分，及格率 {report.get('pass_rate', 0)}%。\n"
            f"薄弱知识点：{'、'.join(k['name'] for k in report.get('weak_knowledge', [])) or '暂无'}。\n"
            "建议在下次课前针对薄弱知识点安排专项讲解，并布置同类练习巩固。"
        ),
        "report": report,
        "is_fallback": True,
    })
