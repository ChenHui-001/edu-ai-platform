"""教案管理接口（/api/v1/lesson/*）。

教师把教学设计沉淀为教案：CRUD + 复制 + 共享 + 引用次数统计。
可关联学科/年级/知识点/课时。
"""
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, File, UploadFile
from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import has_perm, require_perm
from app.core.database import get_db
from app.core.exception import BusinessException, NotFoundException, PermissionException
from app.models import Grade, KnowledgePoint, LessonPlan, LessonStage, Subject, User
from app.utils.common import PageParams, dictify, now_local, ok

router = APIRouter(prefix="/lesson", tags=["教案管理"])

# 教学管理 V2 权限点（docs/TEACHING_V2.md §1）
LESSON_LIST = "lesson:plan:list"
LESSON_WRITE = "lesson:plan:write"
LESSON_COPY = "lesson:plan:copy"
LESSON_SHARE = "lesson:plan:share"

# 列表排序（契约 sort 参数）
PLAN_SORTS = {
    "updated_desc": desc(LessonPlan.updated_at),
    "created_desc": desc(LessonPlan.created_at),
    "created_asc": LessonPlan.created_at.asc(),
    "use_desc": desc(LessonPlan.use_count),
    "title": LessonPlan.title.asc(),
}
MAX_BATCH_PLANS = 200


def _is_sys_admin(user: User) -> bool:
    return "sys_admin" in set(user.role_codes or [])


def _my_subject_ids(db: Session, user: User) -> set:
    """当前教师任教学科 id 集合（共享教案仅同科可见）。"""
    from app.models import TeachingAssignment

    return set(db.scalars(
        select(TeachingAssignment.subject_id).where(
            TeachingAssignment.teacher_id == user.id,
            TeachingAssignment.is_active.is_(True),
        )
    ).all())


def _visible_plan_clause(db: Session, user: User):
    """列表/统计的可见范围：自己创建的 + 同科共享的；sys_admin 全量。"""
    if _is_sys_admin(user):
        return None
    subject_ids = _my_subject_ids(db, user)
    if subject_ids:
        return or_(
            LessonPlan.creator_id == user.id,
            and_(LessonPlan.is_shared == 1, LessonPlan.subject_id.in_(subject_ids)),
        )
    return LessonPlan.creator_id == user.id


def _can_read_plan(plan: LessonPlan, user: User) -> bool:
    """详情/附件读取：创建者、已共享（公开可见）、sys_admin。"""
    return plan.creator_id == user.id or bool(plan.is_shared) or _is_sys_admin(user)


def _assert_plan_readable(plan: LessonPlan, user: User) -> None:
    if not _can_read_plan(plan, user):
        raise PermissionException("该教案未共享，不可查看")


def _plan_order(sort: Optional[str]):
    key = (sort or "updated_desc").strip().lower()
    if key not in PLAN_SORTS:
        raise BusinessException(
            "sort 仅支持 updated_desc / created_desc / created_asc / use_desc / title")
    return PLAN_SORTS[key]


def _parse_plan_ids(raw: Any) -> List[int]:
    """批量 ids 校验：整数数组、去重、非空、≤200。"""
    if not isinstance(raw, list) or not raw:
        raise BusinessException("请选择要操作的教案")
    ids: List[int] = []
    for item in raw:
        try:
            value = int(item)
        except (TypeError, ValueError):
            raise BusinessException("ids 必须为整数列表") from None
        if value not in ids:
            ids.append(value)
    if len(ids) > MAX_BATCH_PLANS:
        raise BusinessException(f"单次最多操作 {MAX_BATCH_PLANS} 份教案")
    return ids


def _unbind_plan_attachments(db: Session, plan_id: int) -> None:
    """删除教案时附件解绑而非删除（文件是教师资产，可能还要用在别处）。"""
    from app.models import Attachment as _Att

    db.query(_Att).filter(
        _Att.biz_type == "lesson_plan", _Att.biz_id == plan_id,
    ).update({"biz_type": None, "biz_id": None, "is_temp": True},
             synchronize_session=False)


def _plan_reference_reason(db: Session, plan_id: int) -> Optional[str]:
    """检查教案是否被其它业务表引用（批量删除时进 skipped）。

    当前数据模型没有 Task/Course 直连教案的外键；这里按 ORM metadata 动态
    扫描所有 `lesson_plan_id` 列（未来新增引用表自动生效），
    `edu_lesson_stage` 属于教案自身内容（级联删除）不计入引用。
    """
    from app.core.database import Base

    for table in Base.metadata.tables.values():
        if table.name == "edu_lesson_stage":
            continue
        columns = [c for c in table.columns if c.name == "lesson_plan_id"]
        if not columns:
            continue
        try:
            ref = db.scalar(
                select(func.count()).select_from(table).where(columns[0] == plan_id))
        except Exception:  # noqa: BLE001  表结构异常不应阻断删除
            continue
        if ref:
            return f"被 {table.name} 引用 {ref} 条，无法删除"
    return None


def _hydrate(db: Session, plan: LessonPlan) -> Dict[str, Any]:
    """把 ORM 对象转成完整字典（含关联展示字段）。"""
    d = dictify(plan)
    if plan.subject:
        d["subject_name"] = plan.subject.name
    if plan.grade:
        d["grade_name"] = plan.grade.name
    if plan.knowledge_point:
        d["knowledge_point_name"] = plan.knowledge_point.name
    if plan.stages:
        d["stages"] = [dictify(s) for s in sorted(plan.stages, key=lambda x: x.sort_order)]
    d["attachments"] = _plan_attachments(db, plan.id)
    # 列表筛选/前端展示用的来源字段（manual/ai），旧字段全部保留
    d["source"] = "ai" if plan.ai_generated else "manual"
    return d


def _plan_attachments(db: Session, plan_id: int) -> List[Dict[str, Any]]:
    """教案附件（复用 Attachment 体系：biz_type="lesson_plan" + biz_id=plan_id）。

    教案附件需对「教案可见者」可见（含共享教案的阅读者），
    故这里主动聚合而非依赖 /attachments 列表接口（后者按 uploader 过滤，
    会让共享教案的阅读者看不到他人上传的课件）。
    """
    import os as _os
    from app.models import Attachment

    rows = db.scalars(
        select(Attachment).where(
            Attachment.biz_type == "lesson_plan",
            Attachment.biz_id == plan_id,
        ).order_by(desc(Attachment.created_at))
    ).all()
    items = []
    for a in rows:
        d = dictify(a)
        d.pop("file_path", None)
        ext = _os.path.splitext(a.filename or "")[1].lower()
        d["ext"] = ext
        d["previewable"] = ext in {".jpg", ".jpeg", ".png", ".gif", ".webp", ".pdf",
                                    ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx"}
        d["preview_url"] = f"/api/v1/attachments/{a.id}/preview"
        d["download_url"] = f"/api/v1/attachments/{a.id}/download"
        items.append(d)
    return items


# 列表 / 详情
@router.get("/plans", summary="教案列表（教师）")
def list_plans(
    params: PageParams = Depends(), subject_id: Optional[int] = None,
    grade_id: Optional[int] = None, keyword: Optional[str] = None,
    source: Optional[str] = None, shared: Optional[bool] = None,
    sort: Optional[str] = None, only_mine: bool = False,
    db: Session = Depends(get_db),
    user: User = Depends(require_perm(LESSON_LIST)),
):
    """教案列表。

    - 默认：自己创建的 + 同科共享的（sys_admin 全量）
    - only_mine=true：只看自己
    - 新增筛选：grade_id/subject_id/source(manual/ai)/shared/sort
    """
    stmt = select(LessonPlan).options(
        selectinload(LessonPlan.stages),
        selectinload(LessonPlan.subject),
        selectinload(LessonPlan.grade),
    )
    if only_mine:
        stmt = stmt.where(LessonPlan.creator_id == user.id)
    else:
        visible = _visible_plan_clause(db, user)
        if visible is not None:
            stmt = stmt.where(visible)
    if subject_id:
        stmt = stmt.where(LessonPlan.subject_id == subject_id)
    if grade_id:
        stmt = stmt.where(LessonPlan.grade_id == grade_id)
    if shared is not None:
        stmt = stmt.where(LessonPlan.is_shared == (1 if shared else 0))
    if source not in (None, ""):
        source_value = str(source).strip().lower()
        if source_value not in ("manual", "ai"):
            raise BusinessException("source 仅支持 manual / ai")
        stmt = stmt.where(LessonPlan.ai_generated == (1 if source_value == "ai" else 0))
    if keyword:
        kw = f"%{keyword}%"
        stmt = stmt.where(
            (LessonPlan.title.like(kw)) | (LessonPlan.topic.like(kw))
        )

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(
        stmt.order_by(_plan_order(sort))
        .offset(params.offset).limit(params.page_size)
    ).all()
    return ok({"items": [_hydrate(db, r) for r in rows],
               "total": total, "page": params.page, "page_size": params.page_size})


@router.get("/plans/stats", summary="教案统计")
def plan_stats(
    db: Session = Depends(get_db),
    user: User = Depends(require_perm(LESSON_LIST)),
):
    """按当前用户可见范围统计：总数/我的/共享/AI/我的共享。"""
    visible = _visible_plan_clause(db, user)

    def _count(*conditions) -> int:
        stmt = select(func.count()).select_from(LessonPlan)
        if visible is not None:
            stmt = stmt.where(visible)
        for condition in conditions:
            stmt = stmt.where(condition)
        return int(db.scalar(stmt) or 0)

    return ok({
        "total": _count(),
        "mine": _count(LessonPlan.creator_id == user.id),
        "shared": _count(LessonPlan.is_shared == 1),
        "ai": _count(LessonPlan.ai_generated == 1),
        "mine_shared": _count(
            LessonPlan.creator_id == user.id, LessonPlan.is_shared == 1),
    })


@router.get("/plans/{plan_id}", summary="教案详情")
def get_plan(plan_id: int, db: Session = Depends(get_db),
             user: User = Depends(require_perm(LESSON_LIST))):
    plan = db.get(LessonPlan, plan_id)
    if not plan:
        raise NotFoundException("教案不存在")
    # 越权：不是自己创建且没共享 → 拒（sys_admin 审计可读）
    _assert_plan_readable(plan, user)
    # 引用次数自增
    plan.use_count += 1
    db.commit()
    return ok(_hydrate(db, plan))


# 创建
@router.post("/plans", summary="新建教案")
def create_plan(
    data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    user: User = Depends(require_perm(LESSON_WRITE)),
):
    title = (data.get("title") or "").strip()
    topic = (data.get("topic") or "").strip()
    subject_id = data.get("subject_id")
    grade_id = data.get("grade_id")
    if not (title and topic and subject_id and grade_id):
        raise BusinessException("标题/课题/学科/年级为必填")
    # 关联对象存在性
    if not db.get(Subject, subject_id):
        raise BusinessException("学科不存在")
    if not db.get(Grade, grade_id):
        raise BusinessException("年级不存在")
    kp_id = data.get("knowledge_point_id")
    if kp_id and not db.get(KnowledgePoint, kp_id):
        raise BusinessException("知识点不存在")

    plan = LessonPlan(
        title=title, topic=topic,
        subject_id=int(subject_id), grade_id=int(grade_id),
        textbook_version=data.get("textbook_version"),
        knowledge_point_id=kp_id,
        duration_minutes=int(data.get("duration_minutes") or 45),
        period=data.get("period"),
        objectives=data.get("objectives") or "",
        key_points=data.get("key_points") or "",
        difficulties=data.get("difficulties") or "",
        teaching_preparation=data.get("teaching_preparation"),
        class_exercise=data.get("class_exercise"),
        board_design=data.get("board_design"),
        homework=data.get("homework"),
        reflection=data.get("reflection"),
        ai_generated=1 if data.get("ai_generated") else 0,
        ai_job_id=data.get("ai_job_id"),
        creator_id=user.id, is_shared=0,
    )
    db.add(plan)
    db.flush()

    # 教学过程阶段
    for i, s in enumerate(data.get("stages") or []):
        if not s.get("name"):
            continue
        db.add(LessonStage(
            lesson_id=plan.id, name=s["name"],
            duration_minutes=int(s.get("duration_minutes") or 5),
            content=s.get("content") or "",
            teacher_activity=s.get("teacher_activity"),
            student_activity=s.get("student_activity"),
            sort_order=s.get("sort_order", i),
        ))
    db.commit()
    db.refresh(plan)
    return ok(_hydrate(db, plan), message="教案已创建")


# 编辑
@router.put("/plans/{plan_id}", summary="编辑教案")
def update_plan(
    plan_id: int, data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_perm(LESSON_WRITE)),
):
    plan = db.get(LessonPlan, plan_id)
    if not plan:
        raise NotFoundException("教案不存在")
    _plan_editable(plan, user)
    # 可改字段
    for f in ("title", "topic", "textbook_version", "period",
              "objectives", "key_points", "difficulties",
              "teaching_preparation", "class_exercise",
              "board_design", "homework", "reflection", "is_shared"):
        if f in data:
            setattr(plan, f, data[f])
    for f in ("subject_id", "grade_id", "knowledge_point_id", "duration_minutes"):
        if f in data and data[f] is not None:
            setattr(plan, f, data[f])
    # 阶段：传了 stages 就整体替换
    if "stages" in data:
        # 先删旧的（cascade 会处理，但显式删更安全）
        for s in list(plan.stages):
            db.delete(s)
        db.flush()
        for i, s in enumerate(data.get("stages") or []):
            if not s.get("name"):
                continue
            db.add(LessonStage(
                lesson_id=plan.id, name=s["name"],
                duration_minutes=int(s.get("duration_minutes") or 5),
                content=s.get("content") or "",
                teacher_activity=s.get("teacher_activity"),
                student_activity=s.get("student_activity"),
                sort_order=s.get("sort_order", i),
            ))
    plan.updated_at = now_local()
    db.commit()
    db.refresh(plan)
    return ok(_hydrate(db, plan), message="教案已更新")


# 删除
@router.delete("/plans/{plan_id}", summary="删除教案")
def delete_plan(plan_id: int, db: Session = Depends(get_db),
                user: User = Depends(require_perm(LESSON_WRITE))):
    plan = db.get(LessonPlan, plan_id)
    if not plan:
        raise NotFoundException("教案不存在")
    _plan_editable(plan, user)
    # 附件解绑而非删除：文件是教师资产，教案删了课件可能还要用在别的教案里。
    # biz 置空 + is_temp=1，交由临时附件定时清理任务按既定策略处理。
    _unbind_plan_attachments(db, plan_id)
    db.delete(plan)
    db.commit()
    return ok(message="教案已删除")


# 复制 / 共享
@router.post("/plans/{plan_id}/copy", summary="复制教案")
def copy_plan(plan_id: int, data: Dict[str, Any] = Body(default={}),
              db: Session = Depends(get_db),
              user: User = Depends(require_perm(LESSON_COPY))):
    """复制一份教案到当前教师名下（需 lesson:plan:copy）。"""
    src = db.get(LessonPlan, plan_id)
    if not src:
        raise NotFoundException("教案不存在")
    _assert_plan_readable(src, user)
    new_title = (data.get("title") if isinstance(data, dict) else None) \
        or f"{src.title}（副本）"
    plan = LessonPlan(
        title=new_title, topic=src.topic,
        subject_id=src.subject_id, grade_id=src.grade_id,
        textbook_version=src.textbook_version,
        knowledge_point_id=src.knowledge_point_id,
        duration_minutes=src.duration_minutes, period=src.period,
        objectives=src.objectives, key_points=src.key_points,
        difficulties=src.difficulties,
        teaching_preparation=src.teaching_preparation,
        class_exercise=src.class_exercise,
        board_design=src.board_design,
        homework=src.homework, reflection=src.reflection,
        # 副本不继承 ai_job_id（那条任务记录属于原作者，与副本无溯源关系），
        # 但保留 ai_generated 标记，便于教案库区分内容来源
        ai_generated=src.ai_generated, ai_job_id=None,
        creator_id=user.id, is_shared=0,
    )
    db.add(plan)
    db.flush()
    for s in src.stages:
        db.add(LessonStage(
            lesson_id=plan.id, name=s.name,
            duration_minutes=s.duration_minutes, content=s.content,
            teacher_activity=s.teacher_activity,
            student_activity=s.student_activity,
            sort_order=s.sort_order,
        ))
    src.use_count += 1
    db.commit()
    db.refresh(plan)
    return ok(_hydrate(db, plan), message="教案已复制到我的教案库")


@router.post("/plans/{plan_id}/share", summary="共享/取消共享")
def toggle_share(plan_id: int, data: Dict[str, Any] = Body(...),
                db: Session = Depends(get_db),
                user: User = Depends(require_perm(LESSON_SHARE))):
    """共享开关：is_shared=true 时同科教师可在列表里看到并复制。

    权限：lesson:plan:share；且只有创建者可切换（sys_admin 也不能改他人共享状态，
    契约「共享/取消共享仅创建者」）。
    """
    plan = db.get(LessonPlan, plan_id)
    if not plan:
        raise NotFoundException("教案不存在")
    if plan.creator_id != user.id:
        raise PermissionException("只能共享自己的教案")
    plan.is_shared = 1 if data.get("is_shared", True) else 0
    plan.updated_at = now_local()
    db.commit()
    return ok({"is_shared": bool(plan.is_shared)},
              message="已共享" if plan.is_shared else "已取消共享")


@router.post("/plans/batch", summary="批量操作教案")
def batch_plans(
    data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    user: User = Depends(require_perm(LESSON_WRITE, LESSON_SHARE)),
):
    """批量删除/共享/取消共享。

    - 仅创建者或 sys_admin 可操作；同批存在越权节点 → 整体 403（不部分写入）；
    - delete 有引用（课程/任务/未来新增 lesson_plan_id 引用表）时进 skipped；
    - share/unshare 需要 lesson:plan:share，delete 需要 lesson:plan:write；
    - 返回 {done:[ids], skipped:[{id,reason}]}。
    """
    action = str(data.get("action") or "").strip().lower()
    if action not in {"delete", "share", "unshare"}:
        raise BusinessException("action 仅支持 delete / share / unshare")
    required_perm = LESSON_SHARE if action in {"share", "unshare"} else LESSON_WRITE
    if not has_perm(user, required_perm):
        raise PermissionException(f"缺少权限：{required_perm}")

    ids = _parse_plan_ids(data.get("ids"))
    found = {
        plan.id: plan for plan in db.scalars(
            select(LessonPlan).where(LessonPlan.id.in_(ids))
        ).all()
    }
    skipped: List[Dict[str, Any]] = [
        {"id": plan_id, "reason": "不存在"} for plan_id in ids if plan_id not in found
    ]
    targets = [found[plan_id] for plan_id in ids if plan_id in found]
    if not targets:
        return ok({"done": [], "skipped": skipped})

    # 契约：同批只要有一个越权节点，整体 403（防部分写入歧义）
    if not _is_sys_admin(user):
        for plan in targets:
            if plan.creator_id != user.id:
                raise PermissionException(
                    "所选教案中存在无权操作的教案，已拒绝整批操作")

    done: List[int] = []
    for plan in targets:
        if action == "delete":
            reason = _plan_reference_reason(db, plan.id)
            if reason:
                skipped.append({"id": plan.id, "reason": reason})
                continue
            _unbind_plan_attachments(db, plan.id)
            db.delete(plan)
            done.append(plan.id)
        else:
            plan.is_shared = 1 if action == "share" else 0
            plan.updated_at = now_local()
            done.append(plan.id)

    db.commit()
    action_label = {"delete": "删除", "share": "共享", "unshare": "取消共享"}[action]
    return ok({"done": done, "skipped": skipped},
              message=f"批量{action_label}完成 {len(done)} 份")


# 附件（图片 / PPT / 文档等教学资料）
def _plan_editable(plan: LessonPlan, user: User) -> None:
    """教案附件写入权限：创建者，或 sys_admin。共享只赋予读/复制权，不赋予写权。"""
    if plan.creator_id != user.id and "sys_admin" not in user.role_codes:
        raise PermissionException("只能管理自己教案的附件")


@router.post("/plans/{plan_id}/attachments", summary="上传教案附件（图片/PPT/文档）")
def upload_plan_attachment(
    plan_id: int, file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_perm(LESSON_WRITE)),
):
    """教案专用附件上传。

    不走通用 /attachments/upload：那边接受任意 biz_type/biz_id 且无归属校验，
    任何登录用户可以把附件挂到他人教案上（越权）。业务归属校验放在业务端点。
    """
    import hashlib
    import os
    import uuid

    from app.core.config import settings
    from app.models import Attachment

    plan = db.get(LessonPlan, plan_id)
    if not plan:
        raise NotFoundException("教案不存在")
    _plan_editable(plan, user)

    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in settings.ALLOWED_UPLOAD_TYPES:
        raise BusinessException(
            f"不支持的文件类型 {ext}，允许：{'、'.join(settings.ALLOWED_UPLOAD_TYPES)}")
    content = file.file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE * 1024 * 1024:
        raise BusinessException(f"文件大小超过限制（{settings.MAX_UPLOAD_SIZE}MB）")

    stored_name = f"{uuid.uuid4().hex}_{hashlib.md5(content).hexdigest()[:12]}{ext}"
    day_dir = os.path.join(settings.UPLOAD_DIR, now_local().strftime("%Y%m%d"))
    os.makedirs(day_dir, exist_ok=True)
    full_path = os.path.abspath(os.path.join(day_dir, stored_name))
    if not full_path.startswith(os.path.abspath(settings.UPLOAD_DIR)):
        raise BusinessException("非法文件路径")
    with open(full_path, "wb") as fp:
        fp.write(content)

    att = Attachment(
        filename=file.filename, stored_name=stored_name, file_path=full_path,
        file_size=len(content), file_type=file.content_type,
        category="lesson_plan", biz_type="lesson_plan", biz_id=plan.id,
        uploader_id=user.id, is_temp=False,
    )
    db.add(att)
    plan.updated_at = now_local()
    db.commit()
    db.refresh(att)
    return ok({
        "id": att.id, "filename": att.filename, "size": att.file_size, "ext": ext,
        "preview_url": f"/api/v1/attachments/{att.id}/preview",
        "download_url": f"/api/v1/attachments/{att.id}/download",
    }, message="附件上传成功")


@router.get("/plans/{plan_id}/attachments", summary="教案附件列表")
def list_plan_attachments(
    plan_id: int, db: Session = Depends(get_db),
    user: User = Depends(require_perm(LESSON_LIST)),
):
    plan = db.get(LessonPlan, plan_id)
    if not plan:
        raise NotFoundException("教案不存在")
    _assert_plan_readable(plan, user)
    return ok(_plan_attachments(db, plan_id))


@router.delete("/plans/{plan_id}/attachments/{att_id}", summary="删除教案附件")
def delete_plan_attachment(
    plan_id: int, att_id: int, db: Session = Depends(get_db),
    user: User = Depends(require_perm(LESSON_WRITE)),
):
    import os

    from app.models import Attachment

    plan = db.get(LessonPlan, plan_id)
    if not plan:
        raise NotFoundException("教案不存在")
    _plan_editable(plan, user)
    att = db.get(Attachment, att_id)
    if not att or att.biz_type != "lesson_plan" or att.biz_id != plan_id:
        raise NotFoundException("附件不存在或不属于该教案")
    # 删除磁盘文件（忽略失败——DB 记录为准，孤儿文件由定时清理兜底）
    try:
        if att.file_path and os.path.exists(att.file_path):
            os.remove(att.file_path)
    except OSError:
        pass
    db.delete(att)
    db.commit()
    return ok(message="附件已删除")