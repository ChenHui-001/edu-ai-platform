"""题库与试卷接口。"""
import io
import json
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, File, Query, UploadFile
from fastapi.responses import StreamingResponse
from openpyxl import Workbook, load_workbook
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.agents.rag import index_question
from app.api.deps import DataScope, get_current_teacher, get_current_user, get_data_scope
from app.core.database import get_db
from app.core.exception import BusinessException, NotFoundException, PermissionException
from app.models import (
    Grade, KnowledgePoint, Paper, PaperItem, PaperShare, Question, QuestionBankType,
    QuestionStatus, Subject, User,
)
from app.utils.common import PageParams, dictify, ok, utcnow

router = APIRouter(prefix="/question", tags=["题库与试卷"])

QUESTION_TYPE_LABEL = {
    "single": "单选题", "multiple": "多选题", "judge": "判断题", "blank": "填空题",
    "short": "简答题", "calc": "计算题", "material": "材料分析题", "composition": "作文题",
}
DIFFICULTY_LABEL = {"easy": "简单", "medium": "中等", "hard": "困难"}


def _has_access(q: Question, user: User) -> bool:
    """题目可见性：公共题库 + 本人私有题库。"""
    if q.bank_type == QuestionBankType.PUBLIC.value:
        return True
    return q.owner_id == user.id or "sys_admin" in user.role_codes or "grade_admin" in user.role_codes


# ---------------------------------------------------------------- 题目
@router.get("/questions", summary="题目列表")
def list_questions(
    params: PageParams = Depends(),
    keyword: Optional[str] = None,
    grade_id: Optional[int] = None,
    subject_id: Optional[int] = None,
    knowledge_point_id: Optional[int] = None,
    qtype: Optional[str] = None,
    difficulty: Optional[str] = None,
    bank_type: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_teacher),
):
    stmt = select(Question)
    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where(or_(Question.stem.like(like), Question.analysis.like(like)))
    if grade_id:
        stmt = stmt.where(Question.grade_id == grade_id)
    if subject_id:
        stmt = stmt.where(Question.subject_id == subject_id)
    if knowledge_point_id:
        stmt = stmt.where(Question.knowledge_point_id == knowledge_point_id)
    if qtype:
        stmt = stmt.where(Question.type == qtype)
    if difficulty:
        stmt = stmt.where(Question.difficulty == difficulty)
    if bank_type:
        stmt = stmt.where(Question.bank_type == bank_type)
    else:
        stmt = stmt.where(or_(
            Question.bank_type == QuestionBankType.PUBLIC.value,
            Question.owner_id == user.id,
        ))
    if status:
        stmt = stmt.where(Question.status == status)

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(
        stmt.order_by(Question.created_at.desc())
        .offset(params.offset).limit(params.page_size)
    ).all()

    items = []
    for q in rows:
        d = dictify(q)
        kp = db.get(KnowledgePoint, q.knowledge_point_id) if q.knowledge_point_id else None
        d["knowledge_point_name"] = kp.name if kp else None
        d["type_label"] = QUESTION_TYPE_LABEL.get(q.type, q.type)
        d["difficulty_label"] = DIFFICULTY_LABEL.get(q.difficulty, q.difficulty)
        items.append(d)

    # 当前筛选范围内的题型统计
    type_stmt = select(Question.type, func.count()).where(
        Question.subject_id == subject_id
    ).group_by(Question.type) if subject_id else select(Question.type, func.count()).group_by(Question.type)
    type_stats = {t: c for t, c in db.execute(type_stmt).all()}

    return ok({
        "items": items, "total": total, "page": params.page, "page_size": params.page_size,
        "type_stats": type_stats,
    })


@router.post("/questions", summary="新增题目")
def create_question(
    data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    user: User = Depends(get_current_teacher),
):
    if not data.get("stem"):
        raise BusinessException("题干不能为空")
    q = Question(
        type=data.get("type", "single"), stem=data["stem"],
        options=_dump(data.get("options")), answer=_dump(data.get("answer")),
        analysis=data.get("analysis"), score=float(data.get("score", 5)),
        difficulty=data.get("difficulty", "medium"),
        grade_id=data.get("grade_id", 0), subject_id=data["subject_id"],
        knowledge_point_id=data.get("knowledge_point_id"),
        bank_type=data.get("bank_type", QuestionBankType.PRIVATE.value),
        owner_id=user.id, status=data.get("status", QuestionStatus.PUBLISHED.value),
        fingerprint=_fingerprint(data["stem"]), source="manual",
    )
    db.add(q)
    db.commit()
    db.refresh(q)
    index_question(q)
    return ok(dictify(q), message="题目创建成功")


@router.put("/questions/{q_id}", summary="编辑题目")
def update_question(
    q_id: int, data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    user: User = Depends(get_current_teacher),
):
    q = db.get(Question, q_id)
    if not q:
        raise NotFoundException("题目不存在")
    if q.owner_id != user.id and "sys_admin" not in user.role_codes:
        raise PermissionException("只能编辑自己的题目")
    for f, v in (("type", data.get("type")), ("stem", data.get("stem")),
                  ("options", _dump(data.get("options"))), ("answer", _dump(data.get("answer"))),
                  ("analysis", data.get("analysis")), ("score", data.get("score")),
                  ("difficulty", data.get("difficulty")), ("subject_id", data.get("subject_id")),
                  ("grade_id", data.get("grade_id")),
                  ("knowledge_point_id", data.get("knowledge_point_id")),
                  ("status", data.get("status"))):
        if v is not None:
            setattr(q, f, v)
    if data.get("stem"):
        q.fingerprint = _fingerprint(data["stem"])
    db.commit()
    index_question(q)
    return ok(dictify(q), message="题目已更新")


@router.delete("/questions/{q_id}", summary="删除题目")
def delete_question(
    q_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_teacher),
):
    q = db.get(Question, q_id)
    if not q:
        raise NotFoundException("题目不存在")
    if q.owner_id != user.id and "sys_admin" not in user.role_codes:
        raise PermissionException("只能删除自己的题目")
    db.delete(q)
    db.commit()
    return ok(message="题目已删除")


@router.put("/questions/{q_id}/status", summary="上下架 / 审核")
def change_status(
    q_id: int, data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    user: User = Depends(get_current_teacher),
):
    q = db.get(Question, q_id)
    if not q:
        raise NotFoundException("题目不存在")
    status = data.get("status")
    if status == QuestionStatus.PUBLISHED.value and q.bank_type == QuestionBankType.PUBLIC.value:
        # 公共题库上架需管理员审核权限
        if not ({"sys_admin", "grade_admin"} & set(user.role_codes)):
            raise PermissionException("公共题库上架需管理员审核")
    if status not in QuestionStatus.__members__.values() and status not in (
        "draft", "published", "offline"
    ):
        raise BusinessException(f"无效状态：{status}")
    q.status = status
    db.commit()
    return ok(message="状态已更新")


@router.get("/questions/{q_id}/duplicates", summary="题目查重")
def check_duplicate(
    q_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_teacher),
):
    q = db.get(Question, q_id)
    if not q:
        raise NotFoundException("题目不存在")
    dupes = db.scalars(
        select(Question).where(
            Question.fingerprint == q.fingerprint, Question.id != q.id
        ).limit(10)
    ).all()
    return ok([{"id": d.id, "stem": d.stem[:80], "created_at": d.created_at} for d in dupes])


@router.get("/questions/template", summary="下载批量导入模板")
def import_template(db: Session = Depends(get_db), _: User = Depends(get_current_teacher)):
    wb = Workbook()
    ws = wb.active
    ws.title = "题目导入"
    headers = ["题型", "题干", "选项A", "选项B", "选项C", "选项D", "答案", "解析",
               "难度", "分值", "知识点ID", "题库类型"]
    ws.append(headers)
    ws.append(["single", "1 + 1 = ?", "1", "2", "3", "4", "B",
               "加法运算", "easy", "5", "", "private"])
    ws.append(["judge", "地球是圆的", "", "", "", "", "正确", "常识", "easy", "5", "", "private"])
    ws.append(["short", "简述光合作用的意义", "", "", "", "", "", "", "medium", "10", "", "private"])
    for i, w in enumerate(headers, start=1):
        ws.column_dimensions[chr(64 + i)].width = 18

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return StreamingResponse(
        buf, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=questions_template.xlsx"},
    )


@router.post("/questions/import", summary="Excel 批量导入题目")
async def import_questions(
    file: UploadFile = File(...), grade_id: Optional[int] = Query(None),
    subject_id: Optional[int] = Query(None),
    db: Session = Depends(get_db), user: User = Depends(get_current_teacher),
):
    content = await file.read()
    try:
        wb = load_workbook(io.BytesIO(content), data_only=True)
    except Exception as exc:
        raise BusinessException(f"Excel 解析失败：{exc}")

    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        raise BusinessException("文件为空")

    headers = [str(h).strip() if h else "" for h in rows[0]]
    idx = {h: i for i, h in enumerate(headers)}
    required = {"题型", "题干", "答案"}
    if not required.issubset(set(headers)):
        raise BusinessException(f"模板缺少必需列：{'、'.join(required - set(headers))}")

    created, skipped = 0, []
    for line_no, row in enumerate(rows[1:], start=2):
        def get(key: str, default=None):
            i = idx.get(key)
            return row[i] if i is not None and i < len(row) else default

        stem = get("题干")
        if not stem or not str(stem).strip():
            continue
        qtype = str(get("题型", "single")).strip()
        if qtype not in QUESTION_TYPE_LABEL:
            qtype = "single"
        options = None
        opts = {k: get(f"选项{k}") for k in "ABCD"}
        if any(opts.values()):
            options = [{"key": k, "text": str(v)} for k, v in opts.items() if v]
            options = json.dumps(options, ensure_ascii=False)
        fp = _fingerprint(str(stem))
        if db.scalar(select(Question).where(Question.fingerprint == fp)):
            skipped.append({"line": line_no, "reason": "题目重复", "stem": str(stem)[:40]})
            continue
        kp_id = get("知识点ID")
        db.add(Question(
            type=qtype, stem=str(stem), options=options,
            answer=_dump(get("答案")), analysis=get("解析"),
            difficulty=str(get("难度", "medium")),
            score=float(get("分值", 5) or 5),
            grade_id=grade_id or 0, subject_id=subject_id or 0,
            knowledge_point_id=int(kp_id) if kp_id else None,
            bank_type=str(get("题库类型", "private")),
            owner_id=user.id, status=QuestionStatus.PUBLISHED.value,
            fingerprint=fp, source="import",
        ))
        created += 1
    db.commit()
    return ok({"created": created, "skipped": skipped, "skipped_count": len(skipped)},
              message=f"成功导入 {created} 道题目，跳过 {len(skipped)} 道")


@router.get("/questions/export", summary="导出题目为 Excel")
def export_questions(
    subject_id: Optional[int] = None, grade_id: Optional[int] = None,
    db: Session = Depends(get_db), user: User = Depends(get_current_teacher),
):
    stmt = select(Question).where(or_(
        Question.bank_type == QuestionBankType.PUBLIC.value, Question.owner_id == user.id
    ))
    if subject_id:
        stmt = stmt.where(Question.subject_id == subject_id)
    if grade_id:
        stmt = stmt.where(Question.grade_id == grade_id)
    rows = db.scalars(stmt.limit(5000)).all()

    wb = Workbook()
    ws = wb.active
    ws.title = "题库导出"
    ws.append(["题型", "题干", "答案", "解析", "难度", "分值", "知识点ID", "状态", "创建时间"])
    for q in rows:
        kp = db.get(KnowledgePoint, q.knowledge_point_id) if q.knowledge_point_id else None
        ws.append([
            QUESTION_TYPE_LABEL.get(q.type, q.type), q.stem, q.answer, q.analysis,
            DIFFICULTY_LABEL.get(q.difficulty, q.difficulty), q.score,
            kp.name if kp else "", q.status,
            q.created_at.strftime("%Y-%m-%d %H:%M") if q.created_at else "",
        ])
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return StreamingResponse(
        buf, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=questions_export.xlsx"},
    )


# ---------------------------------------------------------------- 试卷
@router.get("/papers", summary="试卷列表")
def list_papers(
    params: PageParams = Depends(), subject_id: Optional[int] = None,
    grade_id: Optional[int] = None, keyword: Optional[str] = None,
    db: Session = Depends(get_db), user: User = Depends(get_current_teacher),
):
    stmt = select(Paper).where(
        or_(Paper.creator_id == user.id, Paper.is_shared.is_(True))
    )
    if subject_id:
        stmt = stmt.where(Paper.subject_id == subject_id)
    if grade_id:
        stmt = stmt.where(Paper.grade_id == grade_id)
    if keyword:
        stmt = stmt.where(Paper.name.like(f"%{keyword}%"))
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(
        stmt.order_by(Paper.created_at.desc()).offset(params.offset).limit(params.page_size)
    ).all()
    items = []
    for p in rows:
        d = dictify(p)
        d["item_count"] = len(p.items)
        d["creator_name"] = db.get(User, p.creator_id).real_name if db.get(User, p.creator_id) else None
        sub = db.get(Subject, p.subject_id)
        d["subject_name"] = sub.name if sub else None
        gr = db.get(Grade, p.grade_id)
        d["grade_name"] = gr.name if gr else None
        items.append(d)
    return ok({"items": items, "total": total, "page": params.page})


@router.get("/papers/{paper_id}", summary="试卷详情（含题目）")
def get_paper(
    paper_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_teacher),
):
    paper = db.get(Paper, paper_id)
    if not paper:
        raise NotFoundException("试卷不存在")
    _assert_paper_readable(db, paper, user)

    d = dictify(paper)
    items = []
    for it in sorted(paper.items, key=lambda x: x.sort_order):
        q = it.question
        kp = db.get(KnowledgePoint, q.knowledge_point_id) if q and q.knowledge_point_id else None
        items.append({
            "paper_item_id": it.id, "question_id": q.id, "sort_order": it.sort_order,
            "score": it.score, "section_name": it.section_name,
            "type": q.type, "type_label": QUESTION_TYPE_LABEL.get(q.type, q.type),
            "stem": q.stem, "options": _load(q.options), "answer": _load(q.answer),
            "analysis": q.analysis, "difficulty": q.difficulty,
            "knowledge_point_name": kp.name if kp else None,
        })
    d["items"] = items
    return ok(d)


@router.post("/papers", summary="手动组卷")
def create_paper(
    data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    user: User = Depends(get_current_teacher),
):
    name = data.get("name")
    if not name:
        raise BusinessException("试卷名称不能为空")
    paper = Paper(
        name=name, grade_id=data.get("grade_id", 0), subject_id=data["subject_id"],
        total_score=float(data.get("total_score", 100)),
        duration=int(data.get("duration", 60)), creator_id=user.id,
        source="manual", difficulty_ratio=data.get("difficulty_ratio"),
    )
    db.add(paper)
    db.flush()
    total = 0.0
    for i, item in enumerate(data.get("items", []), start=1):
        score = float(item.get("score", 5))
        total += score
        db.add(
            PaperItem(
                paper_id=paper.id, question_id=item["question_id"],
                sort_order=i, score=score, section_name=item.get("section_name"),
            )
        )
    paper.total_score = total or paper.total_score
    db.commit()
    db.refresh(paper)
    return ok({"id": paper.id, "name": paper.name, "total_score": paper.total_score},
              message="组卷成功")


@router.put("/papers/{paper_id}", summary="编辑试卷")
def update_paper(
    paper_id: int, data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    user: User = Depends(get_current_teacher),
):
    paper = db.get(Paper, paper_id)
    if not paper:
        raise NotFoundException("试卷不存在")
    if paper.creator_id != user.id and "sys_admin" not in user.role_codes:
        raise PermissionException("只能编辑自己创建的试卷")

    if "name" in data:
        paper.name = data["name"]
    if "duration" in data:
        paper.duration = int(data["duration"])
    if "items" in data:
        db.execute(PaperItem.__table__.delete().where(PaperItem.paper_id == paper_id))
        total = 0.0
        for i, item in enumerate(data["items"], start=1):
            score = float(item.get("score", 5))
            total += score
            db.add(
                PaperItem(
                    paper_id=paper_id, question_id=item["question_id"],
                    sort_order=i, score=score, section_name=item.get("section_name"),
                )
            )
        paper.total_score = total
    db.commit()
    return ok(message="试卷已更新")


@router.delete("/papers/{paper_id}", summary="删除试卷")
def delete_paper(
    paper_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_teacher),
):
    paper = db.get(Paper, paper_id)
    if not paper:
        raise NotFoundException("试卷不存在")
    if paper.creator_id != user.id and "sys_admin" not in user.role_codes:
        raise PermissionException("只能删除自己创建的试卷")
    db.delete(paper)
    db.commit()
    return ok(message="试卷已删除")


@router.post("/papers/{paper_id}/copy", summary="试卷复制复用")
def copy_paper(
    paper_id: int, data: Dict[str, Any] = Body(default={}),
    db: Session = Depends(get_db), user: User = Depends(get_current_teacher),
):
    src = db.get(Paper, paper_id)
    if not src:
        raise NotFoundException("试卷不存在")
    _assert_paper_readable(db, src, user)
    new = Paper(
        name=data.get("name", f"{src.name}副本"), grade_id=src.grade_id,
        subject_id=src.subject_id, total_score=src.total_score,
        duration=src.duration, difficulty_ratio=src.difficulty_ratio,
        knowledge_coverage=src.knowledge_coverage, difficulty_report=src.difficulty_report,
        creator_id=user.id, source=src.source,
    )
    db.add(new)
    db.flush()
    for it in src.items:
        db.add(PaperItem(
            paper_id=new.id, question_id=it.question_id, sort_order=it.sort_order,
            score=it.score, section_name=it.section_name,
        ))
    db.commit()
    return ok({"id": new.id, "name": new.name}, message="试卷复制成功")


@router.post("/papers/{paper_id}/share", summary="共享试卷给同科教师")
def share_paper(
    paper_id: int, data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    user: User = Depends(get_current_teacher),
):
    paper = db.get(Paper, paper_id)
    if not paper:
        raise NotFoundException("试卷不存在")
    if paper.creator_id != user.id and "sys_admin" not in user.role_codes:
        raise PermissionException("只能共享自己的试卷")
    to_ids = data.get("user_ids", [])
    if not to_ids:
        raise BusinessException("请选择接收人")

    for uid in to_ids:
        exists = db.scalar(
            select(PaperShare).where(
                PaperShare.paper_id == paper_id, PaperShare.to_user_id == uid
            )
        )
        if not exists:
            db.add(PaperShare(paper_id=paper_id, from_user_id=user.id, to_user_id=uid))
        from app.models import Notification

        db.add(Notification(
            user_id=uid, title="收到共享试卷",
            content=f"{user.real_name} 共享了试卷《{paper.name}》",
            type="system", biz_type="paper", biz_id=paper_id,
        ))
    paper.is_shared = True
    db.commit()
    return ok(message=f"已共享给 {len(to_ids)} 名教师")


@router.get("/papers/{paper_id}/export", summary="导出试卷（Excel）")
def export_paper(
    paper_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_teacher),
):
    paper = db.get(Paper, paper_id)
    if not paper:
        raise NotFoundException("试卷不存在")
    _assert_paper_readable(db, paper, user)

    wb = Workbook()
    ws = wb.active
    ws.title = "试卷"
    sub = db.get(Subject, paper.subject_id)
    gr = db.get(Grade, paper.grade_id)
    ws.append([paper.name])
    ws.append([f"{gr.name if gr else ''} {sub.name if sub else ''}",
               f"总分：{paper.total_score}", f"时间：{paper.duration} 分钟"])
    ws.append([])
    current_section = None
    idx = 1
    for it in sorted(paper.items, key=lambda x: x.sort_order):
        if it.section_name and it.section_name != current_section:
            current_section = it.section_name
            ws.append([current_section])
        q = it.question
        opts = _load(q.options) or []
        opt_text = "  ".join(f"{o['key']}. {o['text']}" for o in opts)
        ws.append([f"{idx}. （{it.score}分）{q.stem}"])
        if opt_text:
            ws.append([f"    {opt_text}"])
        ws.append([f"    答案：{q.answer or ''}"])
        if q.analysis:
            ws.append([f"    解析：{q.analysis}"])
        ws.append([])
        idx += 1

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return StreamingResponse(
        buf, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=paper_{paper_id}.xlsx"},
    )


# ---------------------------------------------------------------- 工具
def _assert_paper_readable(db: Session, paper: Paper, user: User) -> None:
    """试卷读取归属校验：仅创建者、被共享者、公开卷或管理员可读。

    试卷详情含标准答案，缺少校验会导致任意教师遍历 paper_id
    读取他人试卷答案。复制与导出同样受此保护。
    """
    if paper.creator_id == user.id or "sys_admin" in user.role_codes:
        return
    if paper.is_shared:
        return
    shared = db.scalar(
        select(PaperShare.id).where(
            PaperShare.paper_id == paper.id,
            PaperShare.to_user_id == user.id,
        )
    )
    if not shared:
        raise PermissionException("无权查看该试卷")


def _dump(v: Any) -> Optional[str]:
    if v is None:
        return None
    return v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)


def _load(v: Optional[str]) -> Any:
    if not v:
        return None
    try:
        return json.loads(v)
    except json.JSONDecodeError:
        return v


def _fingerprint(stem: str) -> str:
    import hashlib
    import re

    norm = re.sub(r"\s+", "", re.sub(r"[（(].*?[)）]", "", stem))
    return hashlib.md5(norm.encode()).hexdigest()
