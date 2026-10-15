"""批改中心接口 + 学习中心（笔记、错题本、复习、随机练习）。"""
import json
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.api.deps import (
    DataScope, get_current_teacher, get_current_user, get_data_scope,
)
from app.core.config import settings
from app.core.database import get_db
from app.core.exception import BusinessException, NotFoundException, PermissionException
from app.models import (
    Answer, Grade, KnowledgeMastery, KnowledgePoint, Note, Paper, Question, ReviewPlan,
    Subject, Submission, Task, User, WrongQuestion,
)
from app.services import grading_service
from app.utils.common import PageParams, dictify, ok, utcnow

grading_router = APIRouter(prefix="/grading", tags=["智能批改"])
learning_router = APIRouter(prefix="/learning", tags=["学习中心"])


# ================================================================ 批改中心
@grading_router.get("/pending", summary="待批改列表")
def pending_submissions(
    params: PageParams = Depends(), task_id: Optional[int] = None,
    class_id: Optional[int] = None, db: Session = Depends(get_db),
    user: User = Depends(get_current_teacher), scope: DataScope = Depends(get_data_scope),
):
    stmt = select(Submission).join(Task, Task.id == Submission.task_id).where(
        Task.status != "archived"
    )
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
            "submission_id": s.id, "task_id": s.task_id,
            "task_title": task.title if task else None,
            "student_id": s.student_id, "student_name": stu.real_name if stu else "",
            "class_id": stu.class_id if stu else None,
            "score": s.score, "objective_score": s.objective_score,
            "subjective_score": s.subjective_score, "status": s.status,
            "class_rank": s.class_rank, "is_passed": s.is_passed,
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
            "stem": q.stem if q else "", "options": _load(q.options) if q else None,
            "standard_answer": _load(q.answer) if q else None,
            "analysis": q.analysis if q else None,
            "knowledge_point_name": kp.name if kp else None,
            "content": a.content, "is_correct": a.is_correct,
            "score": a.score, "full_score": a.full_score, "grader_type": a.grader_type,
            "teacher_comment": a.teacher_comment, "ai_comment": a.ai_comment,
            "ai_error_points": _load(a.ai_error_points),
        })

    stu = db.get(User, sub.student_id)
    return ok({
        "submission_id": sub.id, "task_id": sub.task_id,
        "task_title": task.title if task else None,
        "student": {"id": stu.id, "name": stu.real_name, "class_id": stu.class_id} if stu else None,
        "score": sub.score, "objective_score": sub.objective_score,
        "subjective_score": sub.subjective_score, "status": sub.status,
        "total_score": task.total_score if task else 0,
        "items": items,
    })


@grading_router.post("/submissions/{submission_id}/grade", summary="手动批改 / 采纳 AI 建议")
def grade_submission(
    submission_id: int, data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    user: User = Depends(get_current_teacher),
):
    sub = db.get(Submission, submission_id)
    if not sub:
        raise NotFoundException("作答记录不存在")

    items = data.get("items", [])
    for it in items:
        ans = db.get(Answer, it["answer_id"])
        if not ans or ans.submission_id != submission_id:
            continue
        if "score" in it:
            ans.score = max(0.0, min(float(it["score"]), float(ans.full_score)))
        if "comment" in it:
            ans.teacher_comment = it["comment"]
            ans.grader_type = "manual"
        ans.is_correct = ans.score >= float(ans.full_score) * settings.PASS_SCORE / 100

    db.flush()

    # 重算总分与状态
    answers = db.scalars(select(Answer).where(Answer.submission_id == submission_id)).all()
    objective = sum(a.score or 0 for a in answers if a.grader_type in ("auto", "manual"))
    subjective = sum(a.score or 0 for a in answers if a.grader_type == "ai")
    sub.objective_score = objective
    sub.subjective_score = subjective
    sub.score = round(objective + subjective, 2)
    task = db.get(Task, sub.task_id)
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
    user: User = Depends(get_current_teacher),
):
    sub = db.get(Submission, submission_id)
    if not sub:
        raise NotFoundException("作答记录不存在")
    sub.status = "not_graded"
    sub.score = None
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
    _: User = Depends(get_current_teacher),
):
    from app.models import Notification

    sub = db.get(Submission, submission_id)
    if not sub:
        raise NotFoundException("作答记录不存在")
    sub.status = "published"
    task = db.get(Task, sub.task_id)
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


# ================================================================ 学习笔记
@learning_router.get("/notes", summary="我的笔记列表")
def list_notes(
    params: PageParams = Depends(), subject_id: Optional[int] = None,
    keyword: Optional[str] = None, is_favorite: Optional[bool] = None,
    db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    stmt = select(Note).where(Note.student_id == user.id)
    if subject_id:
        stmt = stmt.where(Note.subject_id == subject_id)
    if keyword:
        stmt = stmt.where(or_(Note.title.like(f"%{keyword}%"), Note.content.like(f"%{keyword}%")))
    if is_favorite is not None:
        stmt = stmt.where(Note.is_favorite.is_(is_favorite))

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(
        stmt.order_by(Note.updated_at.desc()).offset(params.offset).limit(params.page_size)
    ).all()
    items = []
    for n in rows:
        d = dictify(n)
        d["content_preview"] = (n.content or "")[:100]
        d.pop("content", None)
        d["subject_name"] = db.get(Subject, n.subject_id).name if n.subject_id and db.get(Subject, n.subject_id) else None
        items.append(d)
    return ok({"items": items, "total": total, "page": params.page})


@learning_router.get("/notes/{note_id}", summary="笔记详情")
def get_note(
    note_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    note = db.get(Note, note_id)
    if not note:
        raise NotFoundException("笔记不存在")
    if note.student_id != user.id and "sys_admin" not in user.role_codes:
        raise PermissionException("无权查看该笔记")
    note.view_count += 1
    db.commit()
    d = dictify(note)
    d["ai_outline"] = _load(d.get("ai_outline"))
    d["ai_mindmap"] = _load(d.get("ai_mindmap"))
    d["tags"] = [t for t in (note.tags or "").split(",") if t]
    return ok(d)


@learning_router.post("/notes", summary="创建笔记")
def create_note(
    data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    note = Note(
        title=data.get("title") or "未命名笔记", content=data.get("content", ""),
        format=data.get("format", "markdown"), student_id=user.id,
        subject_id=data.get("subject_id"), knowledge_point_id=data.get("knowledge_point_id"),
        tags=",".join(data["tags"]) if isinstance(data.get("tags"), list) else data.get("tags"),
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    from app.agents.rag import index_note

    index_note(note)
    return ok(dictify(note), message="笔记创建成功")


@learning_router.put("/notes/{note_id}", summary="更新笔记")
def update_note(
    note_id: int, data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    note = db.get(Note, note_id)
    if not note or note.student_id != user.id:
        raise NotFoundException("笔记不存在")
    for f in ("title", "content", "format", "subject_id", "knowledge_point_id"):
        if f in data:
            setattr(note, f, data[f])
    if "tags" in data:
        note.tags = ",".join(data["tags"]) if isinstance(data["tags"], list) else data["tags"]
    if "is_favorite" in data:
        note.is_favorite = bool(data["is_favorite"])
    db.commit()
    from app.agents.rag import index_note

    index_note(note)
    return ok(message="笔记已更新")


@learning_router.delete("/notes/{note_id}", summary="删除笔记")
def delete_note(
    note_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    note = db.get(Note, note_id)
    if not note or note.student_id != user.id:
        raise NotFoundException("笔记不存在")
    db.delete(note)
    db.commit()
    return ok(message="笔记已删除")


@learning_router.post("/notes/{note_id}/organize", summary="AI 整理笔记")
def organize_note(
    note_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    from app.agents.note_agent import NoteOrganizerAgent

    note = db.get(Note, note_id)
    if not note or note.student_id != user.id:
        raise NotFoundException("笔记不存在")
    agent = NoteOrganizerAgent()
    res = agent.run(db, user_id=user.id, note_id=note_id, save=False)
    return ok(res.get("data"), message="整理完成")


@learning_router.get("/notes/{note_id}/export", summary="导出笔记为 HTML/PDF 预览")
def export_note(
    note_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    note = db.get(Note, note_id)
    if not note or note.student_id != user.id:
        raise NotFoundException("笔记不存在")
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>{note.title}</title><style>
body{{font-family:-apple-system,"Microsoft YaHei",sans-serif;max-width:800px;margin:40px auto;line-height:1.8}}
h1{{border-bottom:2px solid #409eff;padding-bottom:8px}}
pre{{background:#f5f7fa;padding:12px;border-radius:6px;overflow:auto}}
</style></head><body>
<h1>{note.title}</h1><pre>{note.content}</pre>
<hr><p style="color:#999">导出时间：{utcnow():%Y-%m-%d %H:%M:%S}</p>
</body></html>"""
    return ok({"filename": f"{note.title}.html", "html": html})


# ================================================================ 错题本
@learning_router.get("/wrong-questions", summary="错题本列表")
def list_wrong(
    params: PageParams = Depends(), subject_id: Optional[int] = None,
    knowledge_point_id: Optional[int] = None, error_reason: Optional[str] = None,
    is_mastered: Optional[bool] = None, keyword: Optional[str] = None,
    db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    stmt = select(WrongQuestion).where(WrongQuestion.student_id == user.id)
    if subject_id:
        stmt = stmt.where(WrongQuestion.subject_id == subject_id)
    if knowledge_point_id:
        stmt = stmt.where(WrongQuestion.knowledge_point_id == knowledge_point_id)
    if error_reason:
        stmt = stmt.where(WrongQuestion.error_reason == error_reason)
    if is_mastered is not None:
        stmt = stmt.where(WrongQuestion.is_mastered.is_(is_mastered))
    if keyword:
        stmt = stmt.where(WrongQuestion.question_id.in_(
            select(Question.id).where(Question.stem.like(f"%{keyword}%"))
        ))

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(
        stmt.order_by(WrongQuestion.last_wrong_at.desc())
        .offset(params.offset).limit(params.page_size)
    ).all()

    items = []
    for w in rows:
        q = db.get(Question, w.question_id)
        kp = db.get(KnowledgePoint, w.knowledge_point_id) if w.knowledge_point_id else None
        items.append({
            "id": w.id, "question_id": w.question_id,
            "stem": q.stem if q else "", "options": _load(q.options) if q else None,
            "answer": _load(q.answer) if q else None, "analysis": q.analysis if q else None,
            "type": q.type if q else None, "difficulty": q.difficulty if q else None,
            "wrong_answer": w.wrong_answer, "error_count": w.error_count,
            "error_reason": w.error_reason, "ai_reason": w.ai_reason,
            "source_name": w.source_name, "source_type": w.source_type,
            "knowledge_point_name": kp.name if kp else None,
            "is_mastered": w.is_mastered,
            "last_wrong_at": dictify(w.last_wrong_at),
        })
    return ok({"items": items, "total": total, "page": params.page})


@learning_router.put("/wrong-questions/{wid}", summary="标注错因 / 标记掌握")
def update_wrong(
    wid: int, data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    w = db.get(WrongQuestion, wid)
    if not w or w.student_id != user.id:
        raise NotFoundException("错题记录不存在")
    if "error_reason" in data:
        w.error_reason = data["error_reason"]
    if "is_mastered" in data:
        w.is_mastered = bool(data["is_mastered"])
        w.mastered_at = utcnow() if data["is_mastered"] else None
    db.commit()
    return ok(message="已更新")


@learning_router.post("/wrong-questions/{wid}/analyze", summary="AI 分析错因")
def analyze_wrong(
    wid: int, db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    from app.agents.grading_agent import GradingAgent

    w = db.get(WrongQuestion, wid)
    if not w or w.student_id != user.id:
        raise NotFoundException("错题记录不存在")
    q = db.get(Question, w.question_id)
    if not q:
        raise NotFoundException("题目不存在")

    grading = GradingAgent()
    res = grading.run(db, user_id=user.id, items=[{
        "question_id": q.id, "student_answer": w.wrong_answer or "", "full_score": q.score,
    }])
    r = (res.get("data") or {}).get("results", [{}])
    first = r[0] if r else {}
    w.ai_reason = first.get("comment")
    db.commit()
    return ok({"analysis": first.get("comment"), "error_points": first.get("error_points", [])})


@learning_router.post("/wrong-questions/{wid}/redo", summary="错题重做（生成专项练习）")
def redo_wrong(
    wid: int, db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    w = db.get(WrongQuestion, wid)
    if not w or w.student_id != user.id:
        raise NotFoundException("错题记录不存在")
    q = db.get(Question, w.question_id)
    if not q:
        raise NotFoundException("题目不存在")
    # 同知识点同类题
    stmt = select(Question).where(
        Question.subject_id == w.subject_id, Question.type == q.type,
        Question.id != q.id, Question.status == "published",
    )
    if w.knowledge_point_id:
        stmt = stmt.where(Question.knowledge_point_id == w.knowledge_point_id)
    similar = list(db.scalars(stmt.limit(5)).all())
    return ok({
        "origin": {"id": q.id, "stem": q.stem, "answer": _load(q.answer), "analysis": q.analysis},
        "similar": [{"id": s.id, "stem": s.stem, "difficulty": s.difficulty, "score": s.score}
                    for s in similar],
    })


@learning_router.get("/wrong-questions/export", summary="导出错题")
def export_wrong(
    subject_id: Optional[int] = None, with_answer: bool = True,
    db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    stmt = select(WrongQuestion).where(
        WrongQuestion.student_id == user.id, WrongQuestion.is_mastered.is_(False)
    )
    if subject_id:
        stmt = stmt.where(WrongQuestion.subject_id == subject_id)

    lines = ["# 我的错题本", ""]
    for i, w in enumerate(db.scalars(stmt.limit(200)).all(), start=1):
        q = db.get(Question, w.question_id)
        if not q:
            continue
        opts = _load(q.options) or []
        lines.append(f"## {i}. {q.stem}")
        for o in opts:
            lines.append(f"- {o.get('key')}. {o.get('text')}")
        if with_answer:
            lines.append(f"\n**答案**：{q.answer}")
            lines.append(f"**解析**：{q.analysis or '暂无'}\n")
    return ok({"content": "\n".join(lines), "format": "markdown"})


# ================================================================ 智能复习
@learning_router.get("/review/plans", summary="我的复习计划")
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


@learning_router.put("/review/plans/{plan_id}/complete", summary="完成复习")
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


@learning_router.get("/review/mastery", summary="知识点掌握地图")
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


@learning_router.post("/review/plan", summary="AI 生成复习计划")
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
@learning_router.post("/practice", summary="创建随机练习")
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


@learning_router.get("/practice/history", summary="练习历史")
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
@learning_router.get("/practice/{task_id}", summary="获取练习题目")
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
            "options": _load(it.question.options),
        }
        for it in sorted(paper.items, key=lambda x: x.sort_order)
    ]
    return ok({
        "task_id": task.id, "name": paper.name, "duration": task.duration,
        "total_score": task.total_score, "items": items,
    })


def _load(v: Optional[str]) -> Any:
    if not v:
        return None
    try:
        return json.loads(v)
    except json.JSONDecodeError:
        return v
