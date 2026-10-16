"""学习中心 - 错题本（列表、标注错因、AI 分析、错题重做、导出）。

由原 1333 行的 api/v1/grading.py 拆分而来，路由前缀 /learning 保持不变。
"""
import html
import io
from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.exception import NotFoundException
from app.models import KnowledgePoint, Question, User, WrongQuestion
from app.utils.common import PageParams, dictify, load_json, ok, utcnow

router = APIRouter()

@router.get("/wrong-questions", summary="错题本列表")
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
            "stem": q.stem if q else "", "options": load_json(q.options) if q else None,
            "answer": load_json(q.answer) if q else None, "analysis": q.analysis if q else None,
            "type": q.type if q else None, "difficulty": q.difficulty if q else None,
            "wrong_answer": w.wrong_answer, "error_count": w.error_count,
            "error_reason": w.error_reason, "ai_reason": w.ai_reason,
            "source_name": w.source_name, "source_type": w.source_type,
            "knowledge_point_name": kp.name if kp else None,
            "is_mastered": w.is_mastered,
            "last_wrong_at": dictify(w.last_wrong_at),
        })
    return ok({"items": items, "total": total, "page": params.page})


@router.put("/wrong-questions/{wid}", summary="标注错因 / 标记掌握")
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


@router.post("/wrong-questions/{wid}/analyze", summary="AI 分析错因")
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


@router.post("/wrong-questions/{wid}/redo", summary="错题重做（生成专项练习）")
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
        "origin": {"id": q.id, "stem": q.stem, "answer": load_json(q.answer), "analysis": q.analysis},
        "similar": [{"id": s.id, "stem": s.stem, "difficulty": s.difficulty, "score": s.score}
                    for s in similar],
    })


@router.get("/wrong-questions/export", summary="导出错题")
def export_wrong(
    subject_id: Optional[int] = None, with_answer: bool = True,
    fmt: str = Query("markdown", regex="^(markdown|html|pdf)$"),
    db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    """导出错题本：
    - markdown：返回 markdown 文本（默认）
    - html/pdf：返回 HTML 文档（浏览器打印为 PDF）
    """
    stmt = select(WrongQuestion).where(
        WrongQuestion.student_id == user.id, WrongQuestion.is_mastered.is_(False)
    )
    if subject_id:
        stmt = stmt.where(WrongQuestion.subject_id == subject_id)

    wrongs = db.scalars(stmt.limit(200)).all()
    if fmt == "markdown":
        lines = ["# 我的错题本", ""]
        for i, w in enumerate(wrongs, start=1):
            q = db.get(Question, w.question_id)
            if not q:
                continue
            opts = load_json(q.options) or []
            lines.append(f"## {i}. {q.stem}")
            for o in opts:
                lines.append(f"- {o.get('key')}. {o.get('text')}")
            if with_answer:
                lines.append(f"\n**答案**：{q.answer}")
                lines.append(f"**解析**：{q.analysis or '暂无'}\n")
        return ok({"content": "\n".join(lines), "format": "markdown"})

    # html / pdf → HTML 文档
    rows = ["<!DOCTYPE html><html><head><meta charset='utf-8'>"
            "<title>我的错题本</title></head><body>"]
    rows.append("<h1 style='text-align:center'>我的错题本</h1><hr/>")
    for i, w in enumerate(wrongs, start=1):
        q = db.get(Question, w.question_id)
        if not q:
            continue
        opts = load_json(q.options) or []
        rows.append(f"<p><b>{i}.</b> {html.escape(q.stem or '')}</p>")
        if opts:
            rows.append("<ol type='A'>" + "".join(
                f"<li>{html.escape(str(o.get('text') or ''))}</li>" for o in opts) + "</ol>")
        if with_answer:
            rows.append(f"<p><i>答案：{html.escape(q.answer or '')}</i></p>")
            rows.append(f"<p><i>解析：{html.escape(q.analysis or '暂无')}</i></p>")
        rows.append("<hr/>")
    rows.append("</body></html>")
    # 本地名不能用 html —— 会遮蔽 html 模块，同函数前面 html.escape 直接 UnboundLocalError
    html_doc = "\n".join(rows)
    ext = "pdf" if fmt == "pdf" else "html"
    mt = "text/html"
    return StreamingResponse(
        io.BytesIO(html_doc.encode("utf-8")), media_type=mt,
        headers={"Content-Disposition": f"attachment; filename=wrong_questions.{ext}"},
    )
