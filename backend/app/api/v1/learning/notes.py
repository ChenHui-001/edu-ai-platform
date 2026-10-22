"""学习中心 - 学习笔记（列表、共享、增删改、AI 整理、导出）。

由原1333 行的 api/v1/grading.py 拆分而来，路由前缀 /learning 保持不变。
"""
import html
from typing import Any, Dict, Optional

from fastapi import APIRouter, BackgroundTasks, Body, Depends, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.api.deps import (
    get_current_student, get_current_student_self,
)
from app.core.database import get_db
from app.core.exception import NotFoundException, PermissionException
from app.models import Note, Subject, User
from app.utils.common import PageParams, dictify, load_json, now_local, ok

router = APIRouter()

def _index_note_bg(note_id: int, title: str, content: str,
                   student_id: int, subject_id: int) -> None:
    """后台向量化：只接收标量，避免在请求会话关闭后访问 ORM 对象。"""
    try:
        from types import SimpleNamespace

        from app.agents.rag import index_note

        index_note(SimpleNamespace(
            id=note_id, title=title or "", content=content or "",
            student_id=student_id, subject_id=subject_id,
        ))
    except Exception:  # noqa: BLE001
        pass


@router.get("/notes", summary="我的笔记列表")
def list_notes(
    params: PageParams = Depends(), subject_id: Optional[int] = None,
    keyword: Optional[str] = None, is_favorite: Optional[bool] = None,
    db: Session = Depends(get_db), user: User = Depends(get_current_student),
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
    # 预加载学科名：原实现每条笔记调用两次 db.get(Subject)（N+1 且重复）
    subject_ids = {n.subject_id for n in rows if n.subject_id}
    subj_names = {
        sid: nm for sid, nm in db.execute(
            select(Subject.id, Subject.name).where(Subject.id.in_(subject_ids))
        ).all()
    } if subject_ids else {}
    items = []
    for n in rows:
        d = dictify(n)
        d["content_preview"] = (n.content or "")[:100]
        d.pop("content", None)
        d["subject_name"] = subj_names.get(n.subject_id)
        items.append(d)
    return ok({"items": items, "total": total, "page": params.page})


@router.get("/notes/shared", summary="同学共享的笔记")
def shared_notes(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    subject_id: Optional[int] = None, db: Session = Depends(get_db),
    user: User = Depends(get_current_student),
):
    """查看同班同学共享的笔记（不含本人，按班级隔离）。

    仅学生可查看他人笔记；教师/管理员即使有 class_id 也不应浏览
    学生私有内容（此前教师能通过自己的班号看到本班学生共享笔记）。
    """
    if user.identity != "student":
        return ok({"items": [], "total": 0})
    from app.models import User as U
    classmates = db.scalars(
        select(U.id).where(U.class_id == user.class_id, U.id != user.id)
    ).all() if user.class_id else []
    if not classmates:
        return ok({"items": [], "total": 0})
    stmt = select(Note).where(
        Note.student_id.in_(classmates), Note.is_shared.is_(True)
    )
    if subject_id:
        stmt = stmt.where(Note.subject_id == subject_id)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(
        stmt.order_by(Note.updated_at.desc()).offset((page - 1) * page_size).limit(page_size)
    ).all()
    items = []
    for n in rows:
        d = dictify(n)
        author = db.get(U, n.student_id)
        d["author_name"] = author.real_name if author else ""
        items.append(d)
    return ok({"items": items, "total": total, "page": page, "page_size": page_size})


@router.get("/notes/{note_id}", summary="笔记详情")
def get_note(
    note_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_student),
):
    note = db.get(Note, note_id)
    if not note:
        raise NotFoundException("笔记不存在")
    if note.student_id != user.id:
        # 仅系统管理员可跨用户查看（数据核查），且必须留审计痕迹
        if "sys_admin" not in user.role_codes:
            raise PermissionException("无权查看该笔记")
        try:
            from app.models import OperationLog

            db.add(OperationLog(
                user_id=user.id, username=user.username,
                module="学习中心", action="查看学生笔记",
                method="GET", path=f"/learning/notes/{note_id}",
                params=f'{{"note_id":{note_id},"owner_id":{note.student_id}}}',
                ip="", status="success",
            ))
        except Exception:  # noqa: BLE001
            pass
    # 浏览数只统计「本人查看」；管理员核查（跨用户）不计入，避免虚增学生笔记热度
    if note.student_id == user.id:
        note.view_count += 1
        db.commit()
    d = dictify(note)
    d["ai_outline"] = load_json(d.get("ai_outline"))
    d["ai_mindmap"] = load_json(d.get("ai_mindmap"))
    d["tags"] = [t for t in (note.tags or "").split(",") if t]
    return ok(d)


@router.post("/notes", summary="创建笔记")
def create_note(
    background: BackgroundTasks, data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_student_self),
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
    # 向量化放后台：Embedding 计算可能耗时数百毫秒，同步执行会拖慢保存响应
    background.add_task(_index_note_bg, note.id, note.title, note.content,
                        note.student_id, note.subject_id or 0)
    return ok(dictify(note), message="笔记创建成功")


@router.put("/notes/{note_id}", summary="更新笔记")
def update_note(
    note_id: int, background: BackgroundTasks, data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_student_self),
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
    background.add_task(_index_note_bg, note.id, note.title, note.content,
                        note.student_id, note.subject_id or 0)
    return ok(message="笔记已更新")


@router.delete("/notes/{note_id}", summary="删除笔记")
def delete_note(
    note_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_student_self),
):
    note = db.get(Note, note_id)
    if not note or note.student_id != user.id:
        raise NotFoundException("笔记不存在")
    db.delete(note)
    db.commit()
    return ok(message="笔记已删除")


@router.put("/notes/{note_id}/share", summary="分享笔记给同学")
def share_note(
    note_id: int, data: Dict[str, Any] = Body(default={}),
    db: Session = Depends(get_db), user: User = Depends(get_current_student_self),
):
    """设置笔记为共享/取消共享，共享后同班同学可在「共享笔记」列表查看。"""
    note = db.get(Note, note_id)
    if not note or note.student_id != user.id:
        raise NotFoundException("笔记不存在")
    note.is_shared = bool(data.get("shared", True))
    db.commit()
    return ok({"is_shared": note.is_shared},
              message="已分享给同班同学" if note.is_shared else "已取消分享")


@router.post("/notes/{note_id}/organize", summary="AI 整理笔记")
def organize_note(
    note_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_student_self),
):
    from app.agents.note_agent import NoteOrganizerAgent

    note = db.get(Note, note_id)
    if not note or note.student_id != user.id:
        raise NotFoundException("笔记不存在")
    agent = NoteOrganizerAgent()
    res = agent.run(db, user_id=user.id, note_id=note_id, save=False)
    return ok(res.get("data"), message="整理完成")


@router.get("/notes/{note_id}/export", summary="导出笔记为 HTML/PDF 预览")
def export_note(
    note_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_student),
):
    note = db.get(Note, note_id)
    if not note or note.student_id != user.id:
        raise NotFoundException("笔记不存在")
    # 内容经 html.escape 转义：笔记由学生自由输入，直接拼接会让
    # <script> 在导出的 HTML 打开时执行（存储型 XSS）。
    safe_title = html.escape(note.title or "")
    safe_content = html.escape(note.content or "")
    # 注意：本地变量名不能叫 html —— 会遮蔽 import 的 html 模块，
    # 同函数内先 html.escape 后赋值将触发 UnboundLocalError。
    html_doc = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>{safe_title}</title><style>
body{{font-family:-apple-system,"Microsoft YaHei",sans-serif;max-width:800px;margin:40px auto;line-height:1.8}}
h1{{border-bottom:2px solid #409eff;padding-bottom:8px}}
pre{{background:#f5f7fa;padding:12px;border-radius:6px;overflow:auto;white-space:pre-wrap}}
</style></head><body>
<h1>{safe_title}</h1><pre>{safe_content}</pre>
<hr><p style="color:#999">导出时间：{now_local():%Y-%m-%d %H:%M:%S}</p>
</body></html>"""
    return ok({"filename": f"{note.title}.html", "html": html_doc})
