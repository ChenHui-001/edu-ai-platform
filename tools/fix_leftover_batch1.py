# -*- coding: utf-8 -*-
"""遗留优化项修复（后端 8 项）。

1. [学习中] get_note 管理员核查不计 view_count
2. [学习中] list_notes 预加载 subject（避免 N+1 双查）
3. [全局] PageParams 容错：page/page_size 传 0/负数/超大值时 clamp 而非 422
4. [学习中] create/update_note 的 RAG 索引进后台任务
5. [学情] student-comparison 批量聚合（消除 N+1）
6. [学情] admin/overview 补 avg_score_rate
7. [学情] subject-comparison 支持按年级+学科维度
8. [学情] active_students 增加 participated_students 别名
"""
import io

# ============================================================
# 3) PageParams 容错（全局生效，收益最大先做）
# ============================================================
f = "backend/app/utils/common.py"
s = io.open(f, encoding="utf-8").read()
OLD = '''class PageParams(BaseModel):
    """分页入参。"""

    page: int = Query(1, ge=1, description="页码，从 1 开始")
    page_size: int = Query(
        settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"
    )

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size'''
NEW = '''class PageParams(BaseModel):
    """分页入参。

    容错策略：page/page_size 传入 0、负数或超大值时**自动收敛**到合法区间，
    而不是返回 422。前端分页组件在「清空筛选」「首次渲染」等场景会传 0，
    此前直接 422 导致列表白屏（实测 page=0 / page_size=0 均 422）。
    """

    page: int = Query(1, description="页码，从 1 开始（<1 时按 1 处理）")
    page_size: int = Query(
        settings.DEFAULT_PAGE_SIZE, description="每页数量（越界自动收敛）"
    )

    @field_validator("page", mode="before")
    @classmethod
    def _clamp_page(cls, v):
        try:
            return max(1, int(v))
        except (TypeError, ValueError):
            return 1

    @field_validator("page_size", mode="before")
    @classmethod
    def _clamp_page_size(cls, v):
        try:
            n = int(v)
        except (TypeError, ValueError):
            return settings.DEFAULT_PAGE_SIZE
        return min(max(1, n), settings.MAX_PAGE_SIZE)

    @property
    def offset(self) -> int:
        return (max(1, self.page) - 1) * self.page_size'''
assert OLD in s, "PageParams"
s = s.replace(OLD, NEW)
# 确保导入 field_validator
if "field_validator" not in s.split("\n\n")[0]:
    s = s.replace("from pydantic import BaseModel", "from pydantic import BaseModel, field_validator")
io.open(f, "w", encoding="utf-8", newline="\n").write(s)
print("[3] PageParams 容错完成")

# ============================================================
# 1) + 2) + 4) notes.py
# ============================================================
f2 = "backend/app/api/v1/learning/notes.py"
s2 = io.open(f2, encoding="utf-8").read()

# 2) 预加载 subject：列表里改成一次批量查询
OLD2 = '''    items = []
    for n in rows:
        d = dictify(n)
        d["content_preview"] = (n.content or "")[:100]
        d.pop("content", None)
        d["subject_name"] = db.get(Subject, n.subject_id).name if n.subject_id and db.get(Subject, n.subject_id) else None
        items.append(d)'''
NEW2 = '''    # 预加载学科名：原实现每条笔记调用两次 db.get(Subject)（N+1 且重复）
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
        items.append(d)'''
assert OLD2 in s2, "list_notes subject"
s2 = s2.replace(OLD2, NEW2)

# 1) get_note：仅本人查看才计 view_count
OLD1 = '''    note.view_count += 1
    db.commit()'''
NEW1 = '''    # 浏览数只统计「本人查看」；管理员核查（跨用户）不计入，避免虚增学生笔记热度
    if note.student_id == user.id:
        note.view_count += 1
        db.commit()'''
assert OLD1 in s2, "view_count"
s2 = s2.replace(OLD1, NEW1)

# 4) RAG 索引放后台任务（create + update）
OLD4 = '''    db.add(note)
    db.commit()
    db.refresh(note)
    from app.agents.rag import index_note

    index_note(note)
    return ok(dictify(note), message="笔记创建成功")'''
NEW4 = '''    db.add(note)
    db.commit()
    db.refresh(note)
    # 向量化放后台：Embedding 计算可能耗时数百毫秒，同步执行会拖慢保存响应
    background.add_task(_index_note_bg, note.id, note.title, note.content,
                        note.student_id, note.subject_id or 0)
    return ok(dictify(note), message="笔记创建成功")'''
assert OLD4 in s2, "create note rag"
s2 = s2.replace(OLD4, NEW4)

OLD5 = '''    from app.agents.rag import index_note

    index_note(note)
    return ok(message="笔记已更新")'''
NEW5 = '''    background.add_task(_index_note_bg, note.id, note.title, note.content,
                        note.student_id, note.subject_id or 0)
    return ok(message="笔记已更新")'''
assert OLD5 in s2, "update note rag"
s2 = s2.replace(OLD5, NEW5)

# 函数签名补 background: BackgroundTasks
s2 = s2.replace('''def create_note(
    data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    user: User = Depends(get_current_student_self),
):''',
'''def create_note(
    data: Dict[str, Any] = Body(...), background: BackgroundTasks = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_student_self),
):''')
s2 = s2.replace('''def update_note(
    note_id: int, data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    user: User = Depends(get_current_student_self),
):''',
'''def update_note(
    note_id: int, data: Dict[str, Any] = Body(...), background: BackgroundTasks = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_student_self),
):''')

# 后台索引函数（脱离 ORM 会话，只传标量，避免 session 已关闭）
HELPER = '''

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

'''
anchor = "@router.get(\"/notes\", summary=\"我的笔记列表\")"
assert anchor in s2
s2 = s2.replace(anchor, HELPER.lstrip("\n") + "\n" + anchor, 1)

# 导入 BackgroundTasks
if "BackgroundTasks" not in s2.split("\n\n")[0]:
    s2 = s2.replace("from fastapi import APIRouter, Body, Depends, Query",
                    "from fastapi import APIRouter, BackgroundTasks, Body, Depends, Query")

io.open(f2, "w", encoding="utf-8", newline="\n").write(s2)
print("[1][2][4] notes.py 完成")
