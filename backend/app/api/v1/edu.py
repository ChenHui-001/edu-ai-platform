"""教学基础档案接口：年级、学科、班级（知识点 V2 已迁移到 knowledge.py）。"""
import csv
import io
import re
from typing import Any, Dict, List, Optional
from urllib.parse import quote

from fastapi import APIRouter, Body, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.api.deps import (
    DataScope, get_current_manager, get_current_teacher, get_current_user,
    get_data_scope, require_perm,
)
from app.core.database import get_db
from app.core.exception import BusinessException, NotFoundException, PermissionException
from app.models import (
    Class, ClassRequest, Grade, KnowledgePoint, Notification,
    Subject, User,
)
from app.utils.common import dictify, now_local, ok

router = APIRouter(prefix="/edu", tags=["教学资源"])

GRADE_STAGES = {"primary", "junior"}
SUBJECT_WRITE_PERM = "resource:subject:write"
CN_NUMBERS = {1: "一", 2: "二", 3: "三", 4: "四", 5: "五", 6: "六", 7: "七", 8: "八", 9: "九"}
# 自定义班级名：中文/字母/数字/中英文括号/间隔号/短横线下划线/空格，2-32 字
CLASS_CUSTOM_NAME_RE = re.compile(r"^[\u4e00-\u9fa5A-Za-z0-9()（）·\-_\s]{2,32}$")
CLASS_AUTO_NAME_RE = re.compile(r"^.+\((\d{1,2})\)班$")


def _canonical_grade_name(stage: str, grade_num: int) -> str:
    """按学段+序号生成标准年级名，避免手工输入「七年级」「7年级」混用。"""
    if stage == "primary" and 1 <= grade_num <= 6:
        return f"{CN_NUMBERS[grade_num]}年级"
    if stage == "junior" and 7 <= grade_num <= 9:
        return f"{CN_NUMBERS[grade_num]}年级"
    raise BusinessException("学段与年级序号不匹配：小学为 1-6，初中为 7-9")


def _validate_custom_name(name: str) -> str:
    name = (name or "").strip()
    if not name:
        raise BusinessException("请填写名称")
    if not CLASS_CUSTOM_NAME_RE.match(name):
        raise BusinessException("名称仅支持中文、字母、数字、括号、间隔号、短横线，长度 2-32")
    return name


def _class_no_from_name(name: str) -> Optional[int]:
    m = CLASS_AUTO_NAME_RE.match((name or "").strip())
    return int(m.group(1)) if m else None


def _auto_class_name(db: Session, grade_id: int, class_no: Any) -> str:
    grade = db.get(Grade, grade_id)
    if not grade:
        raise BusinessException("年级不存在")
    try:
        no = int(class_no)
    except (TypeError, ValueError):
        raise BusinessException("请填写班级序号")
    if not 1 <= no <= 99:
        raise BusinessException("班级序号必须为 1-99")
    return f"{grade.name}({no})班"


def _assert_stage(value: str) -> str:
    stage = str(value or "").strip()
    if stage not in GRADE_STAGES:
        raise BusinessException("学段仅支持 primary（小学）/ junior（初中）")
    return stage


def _assert_grade_num(value: Any) -> int:
    try:
        num = int(value)
    except (TypeError, ValueError):
        raise BusinessException("年级序号必须为 1-999 的整数")
    if not 1 <= num <= 999:
        raise BusinessException("年级序号必须为 1-999 的整数")
    return num


def _assert_subject_scope(user: User, grade_id: int) -> None:
    """学科写权限：sys_admin 全量；grade_admin 仅本年级；其他角色拒绝。"""
    codes = set(user.role_codes or [])
    if "sys_admin" in codes:
        return
    if "grade_admin" in codes and grade_id and user.grade_id == grade_id:
        return
    raise PermissionException("只能维护本年级的学科")


def _assert_grade_write_scope(user: User, grade_id: Optional[int]) -> None:
    """班级写操作的年级范围：sys_admin 不限；grade_admin 仅本年级。

    `resource:class:write` 这个权限点年级管理员也持有（前端菜单对年级管理员
    开放班级管理），但接口此前**完全不校验年级**：任何年级管理员都能给任意
    年级建班、改班、删班、批量导学生 —— 可跨年级污染组织结构，甚至向他人
    年级的班级里注入自己可控的学生账号（叠加导入默认口令即为接管链）。
    与同文件 `_assert_subject_scope` 保持同一口径。
    """
    codes = set(user.role_codes or [])
    if "sys_admin" in codes:
        return
    if "grade_admin" in codes:
        scope_grade = user.grade_admin_grade_id or user.grade_id
        if scope_grade and grade_id == scope_grade:
            return
        raise PermissionException("只能维护本年级的班级")
    raise PermissionException("无权维护班级")


# ---------------------------------------------------------------- 年级
@router.get("/grades", summary="年级列表")
def list_grades(
    stage: Optional[str] = None, keyword: Optional[str] = None,
    db: Session = Depends(get_db), _: User = Depends(get_current_user),
):
    stmt = select(Grade)
    if stage:
        stmt = stmt.where(Grade.stage == stage)
    if keyword:
        stmt = stmt.where(Grade.name.like(f"%{keyword}%"))
    rows = list(db.scalars(stmt.order_by(Grade.grade_num, Grade.id)).all())
    grade_ids = [g.id for g in rows]
    class_counts = dict(db.execute(
        select(Class.grade_id, func.count()).where(
            Class.grade_id.in_(grade_ids)).group_by(Class.grade_id)
    ).all()) if grade_ids else {}
    subject_counts = dict(db.execute(
        select(Subject.grade_id, func.count()).where(
            Subject.grade_id.in_(grade_ids)).group_by(Subject.grade_id)
    ).all()) if grade_ids else {}
    student_counts = dict(db.execute(
        select(User.grade_id, func.count()).where(
            User.grade_id.in_(grade_ids), User.identity == "student",
        ).group_by(User.grade_id)
    ).all()) if grade_ids else {}
    items = []
    for g in rows:
        d = dictify(g)
        d["class_count"] = int(class_counts.get(g.id) or 0)
        d["subject_count"] = int(subject_counts.get(g.id) or 0)
        d["student_count"] = int(student_counts.get(g.id) or 0)
        d["stage_label"] = "小学" if g.stage == "primary" else "初中"
        items.append(d)
    return ok(items)


@router.post("/grades", summary="新增年级")
def create_grade(
    data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    _: User = Depends(require_perm("resource:grade:write")),
):
    stage = _assert_stage(data.get("stage", "primary"))
    grade_num = _assert_grade_num(data.get("grade_num", 1))
    auto_name = bool(data.get("auto_name"))
    if auto_name:
        # 名称由学段+序号自动生成，前端不再手填，杜绝「7年级/七年级/初一」混用
        name = _canonical_grade_name(stage, grade_num)
    else:
        name = (data.get("name") or "").strip()
    if not name:
        raise BusinessException("请填写年级名称")
    if len(name) > 32:
        raise BusinessException("年级名称不能超过 32 个字符")
    if db.scalar(select(Grade).where(Grade.name == name)):
        raise BusinessException("年级已存在")
    if db.scalar(select(Grade).where(Grade.grade_num == grade_num)):
        raise BusinessException("年级序号已存在")
    grade = Grade(
        name=name, stage=stage, grade_num=grade_num,
        sort=int(data.get("sort", grade_num)), is_active=bool(data.get("is_active", True)),
    )
    db.add(grade)
    db.commit()
    return ok(dictify(grade), message="年级创建成功")


@router.put("/grades/{grade_id}", summary="编辑年级")
def update_grade(
    grade_id: int, data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    _: User = Depends(require_perm("resource:grade:write")),
):
    grade = db.get(Grade, grade_id)
    if not grade:
        raise NotFoundException("年级不存在")
    auto_name = bool(data.get("auto_name"))
    target_stage = _assert_stage(data.get("stage", grade.stage)) if (
        "stage" in data or auto_name) else grade.stage
    target_num = _assert_grade_num(data.get("grade_num", grade.grade_num)) if (
        "grade_num" in data or auto_name) else grade.grade_num
    if "stage" in data:
        grade.stage = target_stage
    if "grade_num" in data:
        grade.grade_num = target_num
    if auto_name or "name" in data:
        name = _canonical_grade_name(target_stage, target_num) if auto_name else (
            data.get("name") or "").strip()
        if not name:
            raise BusinessException("年级名称不能为空")
        if db.scalar(select(Grade).where(Grade.name == name, Grade.id != grade.id)):
            raise BusinessException("年级名称已存在")
        grade.name = name
    if "grade_num" in data and db.scalar(select(Grade).where(
            Grade.grade_num == target_num, Grade.id != grade.id)):
        raise BusinessException("年级序号已存在")
    if "sort" in data:
        grade.sort = int(data["sort"])
    if "is_active" in data:
        grade.is_active = bool(data["is_active"])
    db.commit()
    return ok(dictify(grade), message="年级已更新")


@router.delete("/grades/{grade_id}", summary="删除年级")
def delete_grade(
    grade_id: int, db: Session = Depends(get_db),
    _: User = Depends(require_perm("resource:grade:write")),
):
    grade = db.get(Grade, grade_id)
    if not grade:
        raise NotFoundException("年级不存在")
    # 年级下挂班级/学科/知识点/题目/试卷/任务/教案，外键均为 CASCADE。
    # 直接删除会静默清空整年级教学数据（成绩、答卷、题库不可恢复），
    # 必须逐类检查并给出可操作的阻断原因。
    from app.models import Paper, Question, Task

    refs = []
    for label, model, column in (
        ("班级", Class, Class.grade_id), ("学科", Subject, Subject.grade_id),
        ("知识点", KnowledgePoint, KnowledgePoint.grade_id),
        ("题目", Question, Question.grade_id),
        ("试卷", Paper, Paper.grade_id), ("作业/考试", Task, Task.grade_id),
        ("用户", User, User.grade_id),
    ):
        count = db.scalar(
            select(func.count()).select_from(model).where(column == grade_id)
        ) or 0
        if count:
            refs.append(f"{label} {count} 个")
    if refs:
        raise BusinessException(
            f"该年级仍被以下数据引用：{'、'.join(refs)}；删除会级联清空这些教学数据，"
            "请先清空或迁移后再删除"
        )
    db.delete(grade)
    db.commit()
    return ok(message="年级已删除")


# ---------------------------------------------------------------- 学科
@router.get("/subjects", summary="学科列表")
def list_subjects(
    grade_id: Optional[int] = None, keyword: Optional[str] = None,
    distinct: bool = False,
    db: Session = Depends(get_db), _: User = Depends(get_current_user),
):
    """学科列表。

    学科按年级配置（唯一约束是 (grade_id, name)），所以「语文」在 1-9 年级
    各有一条。不传 grade_id 时会返回 60+ 条同名记录，直接喂给下拉框会出现
    大量重复项。

    `distinct=true` 时按名称去重，每科返回一条代表记录（取 sort 最小、
    即最早年级的 id），并附 `grade_count` 说明它覆盖几个年级。
    需要按年级精确取 subject_id 的场景（建题/组卷）不要传 distinct。
    """
    stmt = select(Subject)
    if grade_id:
        stmt = stmt.where(Subject.grade_id == grade_id)
    if keyword:
        stmt = stmt.where(Subject.name.like(f"%{keyword}%"))
    rows = db.scalars(stmt.order_by(Subject.sort)).all()
    items = []
    for s in rows:
        d = dictify(s)
        g = db.get(Grade, s.grade_id)
        d["grade_name"] = g.name if g else None
        items.append(d)

    if distinct:
        # 同名学科在每个年级各有一条；知识点是挂在具体 subject_id 上的，
        # 因此前端必须能按年级取到精确的那条，否则「数学+七年级」会去查
        # 一年级的知识点。这里一并返回同名各年级的 id 列表。
        by_name = {}
        for d in items:
            by_name.setdefault(d.get("name"), []).append(d)

        order = []
        for name, group in by_name.items():
            rep = group[0]
            rep["grade_count"] = len(group)
            rep["same_name_ids"] = [g["id"] for g in group]
            rep["same_name_grade_ids"] = [g.get("grade_id") for g in group]
            order.append(rep)
        items = order

    return ok(items)


@router.post("/subjects", summary="新增学科")
def create_subject(
    data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    user: User = Depends(require_perm(SUBJECT_WRITE_PERM)),
):
    name = (data.get("name") or "").strip()
    grade_id = data.get("grade_id")
    if not name:
        raise BusinessException("请填写学科名称")
    if not grade_id or not db.get(Grade, grade_id):
        raise BusinessException("请选择年级")
    _assert_subject_scope(user, int(grade_id))
    exists = db.scalar(select(Subject).where(
        Subject.grade_id == grade_id, Subject.name == name
    ))
    if exists:
        raise BusinessException("该年级下学科已存在")
    subject = Subject(
        name=name, grade_id=grade_id,
        textbook_version=data.get("textbook_version"), code=data.get("code"),
        sort=int(data.get("sort", data.get("sort_order", 0)) or 0),
        is_active=bool(data.get("is_active", True)),
    )
    db.add(subject)
    db.commit()
    return ok(dictify(subject), message="学科创建成功")


@router.put("/subjects/{subject_id}", summary="编辑学科")
def update_subject(
    subject_id: int, data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    user: User = Depends(require_perm(SUBJECT_WRITE_PERM)),
):
    subject = db.get(Subject, subject_id)
    if not subject:
        raise NotFoundException("学科不存在")
    _assert_subject_scope(user, subject.grade_id)
    if "name" in data:
        name = (data.get("name") or "").strip()
        if not name:
            raise BusinessException("学科名称不能为空")
        dup = db.scalar(select(Subject).where(
            Subject.grade_id == subject.grade_id, Subject.name == name,
            Subject.id != subject.id))
        if dup:
            raise BusinessException("该年级下学科已存在")
        subject.name = name
    for f in ("textbook_version", "code", "is_active"):
        if f in data:
            setattr(subject, f, data[f])
    if "sort" in data or "sort_order" in data:
        subject.sort = int(data.get("sort", data.get("sort_order", 0)) or 0)
    db.commit()
    return ok(dictify(subject), message="学科已更新")


@router.delete("/subjects/{subject_id}", summary="删除学科")
def delete_subject(
    subject_id: int, db: Session = Depends(get_db),
    user: User = Depends(require_perm(SUBJECT_WRITE_PERM)),
):
    subject = db.get(Subject, subject_id)
    if not subject:
        raise NotFoundException("学科不存在")
    _assert_subject_scope(user, subject.grade_id)
    # 学科被题目/试卷/任务/知识点/教案引用时删学科会级联清空整科数据，
    # 必须先阻断（此前删除学科可直接抹掉该科全部题目与考试记录）。
    from app.models import LessonPlan, Paper, Question, Task

    refs = []
    for label, model, column in (
        ("题目", Question, Question.subject_id),
        ("试卷", Paper, Paper.subject_id),
        ("作业/考试", Task, Task.subject_id),
        ("知识点", KnowledgePoint, KnowledgePoint.subject_id),
        ("教案", LessonPlan, LessonPlan.subject_id),
    ):
        count = db.scalar(
            select(func.count()).select_from(model).where(column == subject_id)
        ) or 0
        if count:
            refs.append(f"{label} {count} 个")
    if refs:
        raise BusinessException(
            f"该学科仍被以下数据引用：{'、'.join(refs)}；删除会级联清空这些教学数据，"
            "请先处理后再删除"
        )
    db.delete(subject)
    db.commit()
    return ok(message="学科已删除")


@router.post("/subjects/{subject_id}/clone", summary="跨年级复制学科")
def clone_subject(
    subject_id: int, data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_perm(SUBJECT_WRITE_PERM)),
):
    """把指定学科复制到多个目标年级。

    同一 (grade_id, name) 已存在则跳过，不重复创建。常用于把"一年级语文"
    一键铺到 1-9 年级。返回 created / skipped 明细。
    """
    from app.models import Subject as _Sub

    src = db.get(_Sub, subject_id)
    if not src:
        raise NotFoundException("源学科不存在")
    _assert_subject_scope(user, src.grade_id)
    target_grades = data.get("target_grade_ids") or []
    if not isinstance(target_grades, list) or not target_grades:
        raise BusinessException("请选择至少一个目标年级")

    created, skipped = [], []
    for gid in target_grades:
        gid = int(gid)
        if gid == src.grade_id:
            skipped.append({"grade_id": gid, "reason": "源年级，无需复制"})
            continue
        if not db.get(Grade, gid):
            skipped.append({"grade_id": gid, "reason": "年级不存在"})
            continue
        # 年级管理员只能在本年级内操作；跨年级复制仅 sys_admin
        if "sys_admin" not in set(user.role_codes or []) and gid != user.grade_id:
            skipped.append({"grade_id": gid, "reason": "无权复制到其他年级"})
            continue
        if db.scalar(select(_Sub).where(_Sub.grade_id == gid, _Sub.name == src.name)):
            skipped.append({"grade_id": gid, "reason": "该年级已存在同名学科"})
            continue
        new_sub = _Sub(
            name=src.name, grade_id=gid, code=src.code,
            textbook_version=src.textbook_version, sort=src.sort,
        )
        db.add(new_sub)
        db.flush()
        created.append({"id": new_sub.id, "grade_id": gid, "name": src.name})
    db.commit()
    return ok({"created": created, "skipped": skipped,
              "src_subject_id": subject_id},
              message=f"已复制到 {len(created)} 个年级")


# ---------------------------------------------------------------- 知识点
# V2 起知识点相关接口已迁移到 app/api/v1/knowledge.py（新文件，同前缀 /edu）。
# 旧平铺接口 GET /edu/knowledge、/edu/knowledge/list 与
# GET /edu/knowledge/mastery-overview 在新文件中保持路径与返回结构兼容。


# ---------------------------------------------------------------- 班级
def _assert_class_head_teacher(db: Session, teacher_id: Optional[int]) -> None:
    """班主任必须是教师身份；避免把学生/管理员 id 误设为班主任。"""
    if not teacher_id:
        return
    teacher = db.get(User, teacher_id)
    if not teacher or teacher.identity != "teacher" or teacher.status != "active":
        raise BusinessException("班主任必须是启用状态的教师")


def _class_ids_for_scope(scope: DataScope) -> Optional[List[int]]:
    allowed = scope.class_ids()
    return None if allowed is None else list(allowed)


def _assert_class_visible(scope: DataScope, class_id: int) -> None:
    allowed = _class_ids_for_scope(scope)
    if allowed is not None and class_id not in allowed:
        raise PermissionException("无权访问该班级")


def _class_student_count(db: Session, class_id: int) -> int:
    return int(db.scalar(
        select(func.count()).select_from(User).where(
            User.class_id == class_id, User.identity == "student")
    ) or 0)


@router.get("/classes/public", summary="班级列表（注册页匿名可用）")
def list_classes_public(db: Session = Depends(get_db)):
    """注册页在**未登录**状态需要选择班级。

    原先注册页直接调 /edu/classes（需登录）→ 401 被全局拦截器判为
    「登录已过期」→ 跳回 /login，导致注册入口完全打不开。
    此接口只暴露 id / 名称 / 年级，不含学生数、班主任等内部信息。
    """
    items = []
    for c in db.scalars(select(Class).order_by(Class.id)).all():
        g = db.get(Grade, c.grade_id) if c.grade_id else None
        items.append({
            "id": c.id, "name": c.name,
            "grade_id": c.grade_id,
            "grade_name": g.name if g else None,
        })
    return ok(items)


@router.get("/classes", summary="班级列表")
def list_classes(
    grade_id: Optional[int] = None, keyword: Optional[str] = None,
    mine: bool = False, status: Optional[str] = None,
    page: Optional[int] = None, page_size: Optional[int] = None,
    db: Session = Depends(get_db), user: User = Depends(get_current_user),
    scope: DataScope = Depends(get_data_scope),
):
    """班级列表。

    兼容旧调用：不传 page/page_size 时返回数组（注册/下拉/既有 E2E 依赖）；
    传分页参数时返回 `{items,total,page,page_size}`，管理页用分页版。
    """
    stmt = select(Class)
    if grade_id:
        stmt = stmt.where(Class.grade_id == grade_id)
    if keyword:
        stmt = stmt.where(Class.name.like(f"%{keyword}%"))
    if status == "active":
        stmt = stmt.where(Class.is_active.is_(True))
    elif status == "inactive":
        stmt = stmt.where(Class.is_active.is_(False))
    # mine=true：教师端学情分析等场景只返回任教班级。
    if mine and "sys_admin" not in user.role_codes:
        allowed = scope.class_ids()
        if allowed is not None:
            stmt = stmt.where(Class.id.in_(allowed or [0]))
    if "sys_admin" not in user.role_codes and not mine:
        # 非管理员在班级管理页只看到本 scope 内班级（教师任教/年级管理员本年级），
        # 避免下拉里出现无权访问的班级。
        allowed = scope.class_ids()
        if allowed is not None:
            stmt = stmt.where(Class.id.in_(allowed or [0]))

    total = int(db.scalar(select(func.count()).select_from(stmt.subquery())) or 0)
    if page is not None and page_size is not None:
        page = max(1, int(page))
        page_size = min(200, max(1, int(page_size)))
        rows = list(db.scalars(
            stmt.order_by(Class.id).offset((page - 1) * page_size).limit(page_size)
        ).all())
    else:
        rows = list(db.scalars(stmt.order_by(Class.id)).all())

    # 批量取年级/班主任/学生数，避免逐个 get 的 N+1
    grade_ids = {c.grade_id for c in rows if c.grade_id}
    head_ids = {c.head_teacher_id for c in rows if c.head_teacher_id}
    grades = {g.id: g.name for g in db.scalars(
        select(Grade).where(Grade.id.in_(grade_ids))).all()} if grade_ids else {}
    heads = {u.id: u.real_name for u in db.scalars(
        select(User).where(User.id.in_(head_ids))).all()} if head_ids else {}
    counts = dict(db.execute(
        select(User.class_id, func.count()).where(
            User.class_id.in_([c.id for c in rows]),
            User.identity == "student",
        ).group_by(User.class_id)
    ).all()) if rows else {}

    items = []
    for c in rows:
        d = dictify(c)
        d["grade_name"] = grades.get(c.grade_id)
        d["student_count"] = int(counts.get(c.id) or 0)
        d["head_teacher_name"] = heads.get(c.head_teacher_id)
        d["class_no"] = _class_no_from_name(c.name)
        items.append(d)
    if page is not None and page_size is not None:
        return ok({"items": items, "total": total, "page": page, "page_size": page_size})
    return ok(items)


@router.get("/classes/stats", summary="班级统计（管理页顶部卡片）")
def class_stats(
    grade_id: Optional[int] = None, db: Session = Depends(get_db),
    _: User = Depends(get_current_user), scope: DataScope = Depends(get_data_scope),
):
    stmt = select(Class)
    if grade_id:
        stmt = stmt.where(Class.grade_id == grade_id)
    allowed = _class_ids_for_scope(scope)
    if allowed is not None:
        stmt = stmt.where(Class.id.in_(allowed or [0]))
    rows = list(db.scalars(stmt).all())
    ids = [c.id for c in rows]
    students = int(db.scalar(
        select(func.count()).select_from(User).where(
            User.class_id.in_(ids), User.identity == "student")
    ) or 0) if ids else 0
    active = sum(1 for c in rows if c.is_active)
    with_head = sum(1 for c in rows if c.head_teacher_id)
    by_grade = []
    for g in db.scalars(select(Grade).order_by(Grade.sort)).all():
        n = sum(1 for c in rows if c.grade_id == g.id)
        if n:
            by_grade.append({"grade_id": g.id, "grade_name": g.name, "count": n})
    return ok({
        "total": len(rows), "students": students,
        "active": active, "inactive": len(rows) - active,
        "with_head_teacher": with_head,
        "head_teacher_coverage": round(with_head / len(rows) * 100, 1) if rows else 0,
        "by_grade": by_grade,
    })


@router.post("/classes", summary="新增班级")
def create_class(
    data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    user: User = Depends(require_perm("resource:class:write")),
):
    grade_id = data.get("grade_id")
    if not grade_id or not db.get(Grade, grade_id):
        raise BusinessException("请选择年级")
    _assert_grade_write_scope(user, int(grade_id))
    auto_name = bool(data.get("auto_name"))
    strict_name = bool(data.get("strict_name"))
    if auto_name:
        name = _auto_class_name(db, int(grade_id), data.get("class_no"))
    else:
        name = (data.get("name") or "").strip()
        if strict_name:
            name = _validate_custom_name(name)
    if not name:
        raise BusinessException("请填写班级名称")
    if db.scalar(select(Class).where(Class.name == name, Class.grade_id == grade_id)):
        raise BusinessException("该年级下已存在同名班级")
    _assert_class_head_teacher(db, data.get("head_teacher_id"))
    k = Class(
        name=name, grade_id=grade_id,
        head_teacher_id=data.get("head_teacher_id"),
        remark=data.get("remark") if data.get("remark") is not None else data.get("description"),
        is_active=bool(data.get("is_active", True)),
    )
    db.add(k)
    db.commit()
    d = dictify(k)
    d["class_no"] = _class_no_from_name(k.name)
    return ok(d, message="班级创建成功")


@router.put("/classes/{class_id}", summary="编辑班级")
def update_class(
    class_id: int, data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    user: User = Depends(require_perm("resource:class:write")),
):
    k = db.get(Class, class_id)
    if not k:
        raise NotFoundException("班级不存在")
    # 先校验「这个班级本来归不归我管」，再校验「要搬去的年级归不归我管」——
    # 只校验前者会留下「把本年级班级改挂到别的年级」的越权口子。
    _assert_grade_write_scope(user, k.grade_id)
    target_grade = data.get("grade_id", k.grade_id)
    if target_grade != k.grade_id:
        _assert_grade_write_scope(user, int(target_grade))
    if target_grade != k.grade_id and not db.get(Grade, target_grade):
        raise BusinessException("目标年级不存在")
    auto_name = bool(data.get("auto_name"))
    strict_name = bool(data.get("strict_name"))
    if auto_name:
        class_no = data.get("class_no") or _class_no_from_name(k.name) or 1
        new_name = _auto_class_name(db, int(target_grade), class_no)
    elif "name" in data:
        new_name = (data.get("name") or "").strip()
        if strict_name:
            new_name = _validate_custom_name(new_name)
    else:
        new_name = k.name
    if new_name != k.name:
        dup = db.scalar(select(Class).where(
            Class.name == new_name, Class.grade_id == target_grade, Class.id != k.id))
        if dup:
            raise BusinessException("该年级下已存在同名班级")
        data["name"] = new_name
    if "head_teacher_id" in data:
        _assert_class_head_teacher(db, data.get("head_teacher_id"))

    grade_changed = target_grade != k.grade_id
    for f in ("name", "head_teacher_id", "remark", "is_active", "grade_id"):
        if f in data:
            setattr(k, f, data[f])
    # 兼容前端字段名 description（旧页面的 form 用 description，实际落 remark）
    if "description" in data and "remark" not in data:
        k.remark = data["description"]
    if grade_changed:
        # 班级换年级时，班内学生的 grade_id 必须一起迁移，否则学情/筛选错位
        db.execute(update(User).where(
            User.class_id == k.id, User.identity == "student"
        ).values(grade_id=target_grade))
    db.commit()
    d = dictify(k)
    d["class_no"] = _class_no_from_name(k.name)
    return ok(d, message="班级已更新")


@router.post("/classes/batch", summary="批量启用/停用/删除班级")
def batch_classes(
    data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    user: User = Depends(require_perm("resource:class:write")),
):
    action = str(data.get("action") or "").lower()
    if action not in {"enable", "disable", "delete"}:
        raise BusinessException("action 仅支持 enable / disable / delete")
    ids = [int(x) for x in (data.get("ids") or []) if str(x).isdigit()]
    if not ids:
        raise BusinessException("请选择班级")
    done, skipped = [], []
    for cid in ids:
        c = db.get(Class, cid)
        if not c:
            skipped.append({"id": cid, "reason": "班级不存在"})
            continue
        # 越权直接抛 403，不能静默 skip —— 否则调用方会把"被拒绝"
        # 误解为"班级有问题"，也会掩盖越权尝试。
        _assert_grade_write_scope(user, c.grade_id)
        if action == "delete":
            cnt = _class_student_count(db, cid)
            if cnt:
                skipped.append({"id": cid, "name": c.name,
                                "reason": f"仍有 {cnt} 名学生"})
                continue
            db.delete(c)
        else:
            c.is_active = action == "enable"
        done.append(cid)
    db.commit()
    return ok({"done": done, "skipped": skipped},
              message=f"完成 {len(done)} 个，跳过 {len(skipped)} 个")


@router.delete("/classes/{class_id}", summary="删除班级")
def delete_class(
    class_id: int, db: Session = Depends(get_db),
    user: User = Depends(require_perm("resource:class:write")),
):
    k = db.get(Class, class_id)
    if not k:
        raise NotFoundException("班级不存在")
    _assert_grade_write_scope(user, k.grade_id)
    student_cnt = db.scalar(select(func.count()).select_from(User).where(
        User.class_id == class_id, User.identity == "student")) or 0
    if student_cnt:
        raise BusinessException(
            f"该班级仍有 {student_cnt} 名学生，请先转移学生后再删除")
    db.delete(k)
    db.commit()
    return ok(message="班级已删除")


@router.post("/classes/{class_id}/students", summary="批量导入学生")
def import_students(
    class_id: int, students: List[Dict[str, Any]] = Body(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_perm("resource:class:write")),
):
    """students: [{username, real_name, password?}]"""
    from app.core.security import hash_password
    from app.models import Role, UserRole

    k = db.get(Class, class_id)
    if not k:
        raise NotFoundException("班级不存在")
    _assert_grade_write_scope(user, k.grade_id)

    role = db.scalar(select(Role).where(Role.code == "student"))
    created, skipped = 0, []
    for s in students:
        username = s.get("username")
        if not username or not s.get("real_name"):
            skipped.append({"username": username, "reason": "账号或姓名为空"})
            continue
        if db.scalar(select(User).where(User.username == username)):
            skipped.append({"username": username, "reason": "账号已存在"})
            continue
        u = User(
            username=username, password=hash_password(s.get("password", "Student@123")),
            real_name=s["real_name"], identity="student", status="active",
            grade_id=k.grade_id, class_id=class_id,
            email=s.get("email"), phone=s.get("phone"), must_change_password=True,
        )
        db.add(u)
        db.flush()
        if role:
            db.add(UserRole(user_id=u.id, role_id=role.id))
        created += 1
    db.commit()
    return ok({"created": created, "skipped": skipped},
              message=f"成功导入 {created} 名学生")


@router.get("/classes/{class_id}/students", summary="班级学生列表（分页/搜索）")
def list_class_students(
    class_id: int, keyword: Optional[str] = None,
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db), _: User = Depends(get_current_user),
    scope: DataScope = Depends(get_data_scope),
):
    klass = db.get(Class, class_id)
    if not klass:
        raise NotFoundException("班级不存在")
    _assert_class_visible(scope, class_id)
    stmt = select(User).where(
        User.class_id == class_id, User.identity == "student")
    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where((User.username.like(like)) | (User.real_name.like(like)))
    total = int(db.scalar(select(func.count()).select_from(stmt.subquery())) or 0)
    rows = list(db.scalars(
        stmt.order_by(User.username).offset((page - 1) * page_size).limit(page_size)
    ).all())
    items = [{
        "id": u.id, "username": u.username, "real_name": u.real_name,
        "phone": u.phone, "email": u.email, "status": u.status,
        "grade_id": u.grade_id, "class_id": u.class_id,
    } for u in rows]
    return ok({"items": items, "total": total, "page": page, "page_size": page_size,
               "class_name": klass.name})


@router.get("/classes/{class_id}/students/export", summary="导出班级学生 CSV")
def export_class_students(
    class_id: int, db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
    scope: DataScope = Depends(get_data_scope),
):
    klass = db.get(Class, class_id)
    if not klass:
        raise NotFoundException("班级不存在")
    _assert_class_visible(scope, class_id)
    rows = db.scalars(select(User).where(
        User.class_id == class_id, User.identity == "student"
    ).order_by(User.username)).all()
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["学号", "姓名", "手机号", "邮箱", "状态"])
    for u in rows:
        writer.writerow([u.username, u.real_name, u.phone or "", u.email or "", u.status])
    data = ("\ufeff" + buf.getvalue()).encode("utf-8")
    filename = quote(f"{klass.name}-学生名单.csv")
    return StreamingResponse(
        io.BytesIO(data), media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"},
    )


@router.post("/classes/{class_id}/students/batch-remove", summary="批量移出班级")
def batch_remove_students(
    class_id: int, data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    _: User = Depends(require_perm("resource:class:write")),
    scope: DataScope = Depends(get_data_scope),
):
    klass = db.get(Class, class_id)
    if not klass:
        raise NotFoundException("班级不存在")
    _assert_class_visible(scope, class_id)
    ids = [int(x) for x in (data.get("ids") or []) if str(x).isdigit()]
    if not ids:
        raise BusinessException("请选择学生")
    rows = db.scalars(select(User).where(
        User.id.in_(ids), User.class_id == class_id, User.identity == "student")).all()
    for u in rows:
        u.class_id = None
    db.commit()
    return ok({"removed": len(rows)}, message=f"已移出 {len(rows)} 名学生")


@router.delete("/classes/{class_id}/students/{student_id}", summary="移出班级")
def remove_student(
    class_id: int, student_id: int, db: Session = Depends(get_db),
    user: User = Depends(get_current_teacher),
    scope: DataScope = Depends(get_data_scope),
):
    klass = db.get(Class, class_id)
    if not klass:
        raise NotFoundException("班级不存在")
    # 此前 class_id 参数完全未使用：任意教师可把任意班级的学生置空（水平越权）。
    allowed = scope.class_ids()
    if allowed is not None and class_id not in allowed:
        raise PermissionException("无权管理该班级")
    u = db.get(User, student_id)
    if not u:
        raise NotFoundException("学生不存在")
    if u.class_id != class_id:
        raise BusinessException("该学生不属于该班级")
    u.class_id = None
    db.commit()
    return ok(message="学生已移出班级")


# ---------------------------------------------------------------- 人员简表
@router.get("/people/brief", summary="人员简表（仅 id/姓名/账号，教师端下拉用）")
def people_brief(
    identity: str = Query(..., regex="^(student|teacher)$"),
    class_id: Optional[int] = None,
    db: Session = Depends(get_db), user: User = Depends(get_current_teacher),
    scope: DataScope = Depends(get_data_scope),
):
    """教师端下拉的人员简表，替代此前误用的 /system/users（admin 专属，
    教师调用必 403 —— PaperManage 筛出题人、StudentAnalysis 选学生
    两处都踩过）。

    - identity=teacher：全校在职教师（出题人筛选；仅 id/姓名/账号，
      不含手机邮箱等敏感字段，教师互见合理）
    - identity=student：指定班级的学生；教师只能拉**任教班级**，
      越界班级按 DataScope 拒绝（防拉全校学生名单）
    """
    if identity == "teacher":
        stmt = select(User.id, User.real_name, User.username).where(
            User.identity == "teacher", User.status == "active")
        rows = db.execute(stmt.order_by(User.id)).all()
    else:
        if not class_id:
            raise BusinessException("请指定 class_id")
        if not scope.is_super:
            allowed = scope.class_ids()
            # grade_admin 的 class_ids() 返回 None（本年级全量），
            # 与超管同语义；教师必须命中任教班级
            if allowed is not None and class_id not in allowed:
                if "grade_admin" not in user.role_codes:
                    raise BusinessException("无权查看该班级学生")
        rows = db.execute(
            select(User.id, User.real_name, User.username).where(
                User.identity == "student", User.class_id == class_id,
                User.status == "active").order_by(User.username)
        ).all()
    return ok({"items": [{"id": r[0], "real_name": r[1], "username": r[2]} for r in rows]})


# ---------------------------------------------------------------- 班级掌握概览
# 已迁移到 app/api/v1/knowledge.py 的 GET /edu/knowledge/mastery-overview，
# 路径与返回结构保持不变（本文件不再注册该路由，避免重复）。


# ---------------------------------------------------------------- 教师建班申请（审核制）
CLASS_REQUEST_STATUS = {"pending", "approved", "rejected"}


@router.post("/class-requests", summary="教师提交建班申请")
def create_class_request(
    data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    user: User = Depends(get_current_teacher),
):
    """教师自建班级申请：提交后进入 pending，由年级管理员/超管审核。"""
    name = (data.get("name") or "").strip()
    grade_id = data.get("grade_id")
    if not name:
        raise BusinessException("请填写班级名称")
    if not grade_id or not db.get(Grade, grade_id):
        raise BusinessException("请选择年级")
    if db.scalar(select(Class).where(Class.name == name, Class.grade_id == grade_id)):
        raise BusinessException("该年级下已存在同名班级")
    # 同教师同名 pending 幂等拦截（DB 还有唯一约束兜底）
    dup = db.scalar(select(ClassRequest).where(
        ClassRequest.teacher_id == user.id, ClassRequest.name == name,
        ClassRequest.status == "pending"))
    if dup:
        raise BusinessException("您已提交过同名申请，等待审核中")

    req = ClassRequest(teacher_id=user.id, name=name, grade_id=grade_id,
                       description=(data.get("description") or "").strip()[:255])
    db.add(req)
    db.commit()
    db.refresh(req)
    return ok(dictify(req), message="申请已提交，等待管理员审核")


@router.get("/class-requests/mine", summary="我的建班申请")
def my_class_requests(
    db: Session = Depends(get_db), user: User = Depends(get_current_teacher),
):
    rows = db.scalars(select(ClassRequest).where(
        ClassRequest.teacher_id == user.id
    ).order_by(ClassRequest.created_at.desc())).all()
    items = []
    for r in rows:
        d = dictify(r)
        g = db.get(Grade, r.grade_id)
        d["grade_name"] = g.name if g else None
        if r.class_id:
            c = db.get(Class, r.class_id)
            d["class_name"] = c.name if c else None
        items.append(d)
    return ok({"items": items})


@router.get("/class-requests", summary="建班申请列表（管理员审核用）")
def list_class_requests(
    status: Optional[str] = Query(None), db: Session = Depends(get_db),
    _: User = Depends(get_current_manager),
):
    if status and status not in CLASS_REQUEST_STATUS:
        raise BusinessException("非法的状态筛选")
    stmt = select(ClassRequest)
    if status:
        stmt = stmt.where(ClassRequest.status == status)
    rows = db.scalars(stmt.order_by(ClassRequest.created_at.desc())).all()
    items = []
    for r in rows:
        d = dictify(r)
        t = db.get(User, r.teacher_id)
        d["teacher_name"] = t.real_name if t else ""
        d["username"] = t.username if t else ""
        g = db.get(Grade, r.grade_id)
        d["grade_name"] = g.name if g else None
        items.append(d)
    return ok({"items": items})


@router.post("/class-requests/{req_id}/review", summary="审核建班申请")
def review_class_request(
    req_id: int, data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    user: User = Depends(get_current_manager),
):
    """approve：真实创建班级并回填，申请教师自动成为班主任；
    reject：需附理由。审核结果均站内通知申请教师。"""
    req = db.get(ClassRequest, req_id)
    if not req:
        raise NotFoundException("申请不存在")
    if req.status != "pending":
        raise BusinessException("该申请已处理过")
    action = data.get("action")
    if action not in ("approve", "reject"):
        raise BusinessException("action 必须是 approve / reject")
    note = (data.get("note") or "").strip()[:255]
    if action == "reject" and not note:
        raise BusinessException("拒绝时请填写理由")

    req.review_by = user.id
    req.review_at = now_local()
    req.review_note = note

    if action == "approve":
        if db.scalar(select(Class).where(Class.name == req.name, Class.grade_id == req.grade_id)):
            raise BusinessException("该年级下已存在同名班级，无法通过（请拒绝并说明）")
        new_class = Class(name=req.name, grade_id=req.grade_id,
                          head_teacher_id=req.teacher_id, remark=req.description)
        db.add(new_class)
        db.flush()
        req.class_id = new_class.id
        req.status = "approved"
        db.add(Notification(user_id=req.teacher_id,
                     title="建班申请已通过",
                     content=f"您申请的班级「{req.name}」已创建，您已被设为班主任。"
                             + (f"备注：{note}" if note else ""),
                     type="system", biz_type="class_request", biz_id=req.id))
        msg = "已通过并创建班级"
    else:
        req.status = "rejected"
        db.add(Notification(user_id=req.teacher_id,
                     title="建班申请被拒绝",
                     content=f"您申请的班级「{req.name}」未通过审核。理由：{note}",
                     type="system", biz_type="class_request", biz_id=req.id))
        msg = "已拒绝"

    db.commit()
    return ok(dictify(req), message=msg)


@router.delete("/class-requests/{req_id}", summary="撤回我的建班申请")
def withdraw_class_request(
    req_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_teacher),
):
    req = db.get(ClassRequest, req_id)
    if not req or req.teacher_id != user.id:
        raise NotFoundException("申请不存在")
    if req.status != "pending":
        raise BusinessException("已处理的申请不可撤回")
    db.delete(req)
    db.commit()
    return ok(message="申请已撤回")
