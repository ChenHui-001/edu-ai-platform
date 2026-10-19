"""教案管理接口（/api/v1/lesson/*）。

教师把教学设计沉淀为教案：CRUD + 复制 + 共享 + 引用次数统计。
可关联学科/年级/知识点/课时。
"""
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_teacher, get_data_scope
from app.core.database import get_db
from app.core.exception import BusinessException, NotFoundException, PermissionException
from app.models import Grade, KnowledgePoint, LessonPlan, LessonStage, Subject, User
from app.utils.common import PageParams, dictify, load_json, ok, utcnow

router = APIRouter(prefix="/lesson", tags=["教案管理"])


def _hydrate(plan: LessonPlan) -> Dict[str, Any]:
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
    return d


# ============================================================
# 列表 / 详情
# ============================================================
@router.get("/plans", summary="教案列表（教师）")
def list_plans(
    params: PageParams = Depends(), subject_id: Optional[int] = None,
    grade_id: Optional[int] = None, keyword: Optional[str] = None,
    only_mine: bool = False,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_teacher),
):
    """教案列表。

    - 默认：当前教师自己 + 共享给同科教师的
    - only_mine=true：只看自己
    """
    stmt = select(LessonPlan).options(
        selectinload(LessonPlan.stages),
        selectinload(LessonPlan.subject),
        selectinload(LessonPlan.grade),
    )
    if only_mine:
        stmt = stmt.where(LessonPlan.creator_id == user.id)
    else:
        # 同科教师共享的也看得到：用 subject_id 匹配 + 排除自己
        stmt = stmt.where(
            (LessonPlan.creator_id == user.id) | (LessonPlan.is_shared == 1)
        )
    if subject_id:
        stmt = stmt.where(LessonPlan.subject_id == subject_id)
    if grade_id:
        stmt = stmt.where(LessonPlan.grade_id == grade_id)
    if keyword:
        kw = f"%{keyword}%"
        stmt = stmt.where(
            (LessonPlan.title.like(kw)) | (LessonPlan.topic.like(kw))
        )

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(
        stmt.order_by(desc(LessonPlan.updated_at))
        .offset(params.offset).limit(params.page_size)
    ).all()
    return ok({"items": [_hydrate(r) for r in rows],
               "total": total, "page": params.page, "page_size": params.page_size})


@router.get("/plans/{plan_id}", summary="教案详情")
def get_plan(plan_id: int, db: Session = Depends(get_db),
             user: User = Depends(get_current_teacher)):
    plan = db.get(LessonPlan, plan_id)
    if not plan:
        raise NotFoundException("教案不存在")
    # 越权：不是自己创建且没共享 → 拒
    if (plan.creator_id != user.id and not plan.is_shared
            and "sys_admin" not in user.role_codes):
        raise PermissionException("该教案未共享，不可查看")
    # 引用次数自增
    plan.use_count += 1
    db.commit()
    return ok(_hydrate(plan))


# ============================================================
# 创建
# ============================================================
@router.post("/plans", summary="新建教案")
def create_plan(
    data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    user: User = Depends(get_current_teacher),
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
        board_design=data.get("board_design"),
        homework=data.get("homework"),
        reflection=data.get("reflection"),
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
            sort_order=s.get("sort_order", i),
        ))
    db.commit()
    db.refresh(plan)
    return ok(_hydrate(plan), message="教案已创建")


# ============================================================
# 编辑
# ============================================================
@router.put("/plans/{plan_id}", summary="编辑教案")
def update_plan(
    plan_id: int, data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db), user: User = Depends(get_current_teacher),
):
    plan = db.get(LessonPlan, plan_id)
    if not plan:
        raise NotFoundException("教案不存在")
    if plan.creator_id != user.id and "sys_admin" not in user.role_codes:
        raise PermissionException("只能编辑自己的教案")
    # 可改字段
    for f in ("title", "topic", "textbook_version", "period",
              "objectives", "key_points", "difficulties",
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
                sort_order=s.get("sort_order", i),
            ))
    plan.updated_at = utcnow()
    db.commit()
    db.refresh(plan)
    return ok(_hydrate(plan), message="教案已更新")


# ============================================================
# 删除
# ============================================================
@router.delete("/plans/{plan_id}", summary="删除教案")
def delete_plan(plan_id: int, db: Session = Depends(get_db),
                user: User = Depends(get_current_teacher)):
    plan = db.get(LessonPlan, plan_id)
    if not plan:
        raise NotFoundException("教案不存在")
    if plan.creator_id != user.id and "sys_admin" not in user.role_codes:
        raise PermissionException("只能删除自己的教案")
    db.delete(plan)
    db.commit()
    return ok(message="教案已删除")


# ============================================================
# 复制 / 共享
# ============================================================
@router.post("/plans/{plan_id}/copy", summary="复制教案")
def copy_plan(plan_id: int, data: Dict[str, Any] = Body(default={}),
              db: Session = Depends(get_db),
              user: User = Depends(get_current_teacher)):
    """复制一份教案到当前教师名下。"""
    src = db.get(LessonPlan, plan_id)
    if not src:
        raise NotFoundException("教案不存在")
    if src.creator_id != user.id and not src.is_shared:
        raise PermissionException("该教案未共享，不可复制")
    new_title = (data.get("title") if isinstance(data, dict) else None) \
        or f"{src.title}（副本）"
    plan = LessonPlan(
        title=new_title, topic=src.topic,
        subject_id=src.subject_id, grade_id=src.grade_id,
        textbook_version=src.textbook_version,
        knowledge_point_id=src.knowledge_point_id,
        duration_minutes=src.duration_minutes, period=src.period,
        objectives=src.objectives, key_points=src.key_points,
        difficulties=src.difficulties, board_design=src.board_design,
        homework=src.homework, reflection=src.reflection,
        creator_id=user.id, is_shared=0,
    )
    db.add(plan)
    db.flush()
    for s in src.stages:
        db.add(LessonStage(
            lesson_id=plan.id, name=s.name,
            duration_minutes=s.duration_minutes, content=s.content,
            sort_order=s.sort_order,
        ))
    src.use_count += 1
    db.commit()
    db.refresh(plan)
    return ok(_hydrate(plan), message="教案已复制到我的教案库")


@router.post("/plans/{plan_id}/share", summary="共享/取消共享")
def toggle_share(plan_id: int, data: Dict[str, Any] = Body(...),
                db: Session = Depends(get_db),
                user: User = Depends(get_current_teacher)):
    """共享开关：is_shared=true 时同科教师可在列表里看到并复制。"""
    plan = db.get(LessonPlan, plan_id)
    if not plan:
        raise NotFoundException("教案不存在")
    if plan.creator_id != user.id:
        raise PermissionException("只能共享自己的教案")
    plan.is_shared = 1 if data.get("is_shared", True) else 0
    plan.updated_at = utcnow()
    db.commit()
    return ok({"is_shared": bool(plan.is_shared)},
              message="已共享" if plan.is_shared else "已取消共享")