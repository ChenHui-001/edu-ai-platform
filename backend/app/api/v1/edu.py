"""教学基础档案接口：年级、学科、班级（知识点 V2 已迁移到 knowledge.py）。"""
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, Query
from sqlalchemy import func, select
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


# ---------------------------------------------------------------- 年级
@router.get("/grades", summary="年级列表")
def list_grades(
    stage: Optional[str] = None, db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    stmt = select(Grade)
    if stage:
        stmt = stmt.where(Grade.stage == stage)
    return ok([dictify(g) for g in db.scalars(stmt.order_by(Grade.grade_num)).all()])


@router.post("/grades", summary="新增年级")
def create_grade(
    data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    _: User = Depends(get_current_manager),
):
    if db.scalar(select(Grade).where(Grade.name == data.get("name"))):
        raise BusinessException("年级已存在")
    grade = Grade(
        name=data["name"], stage=data.get("stage", "primary"),
        grade_num=int(data.get("grade_num", 9)),
        sort=data.get("sort", 0),
    )
    db.add(grade)
    db.commit()
    return ok(dictify(grade), message="年级创建成功")


@router.put("/grades/{grade_id}", summary="编辑年级")
def update_grade(
    grade_id: int, data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    _: User = Depends(get_current_manager),
):
    grade = db.get(Grade, grade_id)
    if not grade:
        raise NotFoundException("年级不存在")
    for f in ("name", "stage", "grade_num", "sort", "is_active"):
        if f in data:
            setattr(grade, f, data[f])
    db.commit()
    return ok(dictify(grade), message="年级已更新")


@router.delete("/grades/{grade_id}", summary="删除年级")
def delete_grade(
    grade_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_manager),
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
    _: User = Depends(get_current_manager),
):
    exists = db.scalar(select(Subject).where(
        Subject.grade_id == data.get("grade_id"), Subject.name == data.get("name")
    ))
    if exists:
        raise BusinessException("该年级下学科已存在")
    subject = Subject(
        name=data["name"], grade_id=data["grade_id"],
        textbook_version=data.get("textbook_version"), code=data.get("code"),
        sort=data.get("sort", 0),
    )
    db.add(subject)
    db.commit()
    return ok(dictify(subject), message="学科创建成功")


@router.put("/subjects/{subject_id}", summary="编辑学科")
def update_subject(
    subject_id: int, data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    _: User = Depends(get_current_manager),
):
    subject = db.get(Subject, subject_id)
    if not subject:
        raise NotFoundException("学科不存在")
    for f in ("name", "textbook_version", "code", "sort", "is_active"):
        if f in data:
            setattr(subject, f, data[f])
    db.commit()
    return ok(dictify(subject), message="学科已更新")


@router.delete("/subjects/{subject_id}", summary="删除学科")
def delete_subject(
    subject_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_manager),
):
    subject = db.get(Subject, subject_id)
    if not subject:
        raise NotFoundException("学科不存在")
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
    db: Session = Depends(get_db), _: User = Depends(get_current_manager),
):
    """把指定学科复制到多个目标年级。

    同一 (grade_id, name) 已存在则跳过，不重复创建。常用于把"一年级语文"
    一键铺到 1-9 年级。返回 created / skipped 明细。
    """
    from app.models import Subject as _Sub

    src = db.get(_Sub, subject_id)
    if not src:
        raise NotFoundException("源学科不存在")
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
    mine: bool = False,
    db: Session = Depends(get_db), user: User = Depends(get_current_user),
    scope: DataScope = Depends(get_data_scope),
):
    stmt = select(Class)
    if grade_id:
        stmt = stmt.where(Class.grade_id == grade_id)
    if keyword:
        stmt = stmt.where(Class.name.like(f"%{keyword}%"))
    # mine=true：教师端学情分析等场景只返回任教班级。
    # 不加过滤的话下拉里能看到全部班级，选中非任教班级后接口必然 400，
    # 表现为「下拉可选但一选就报无权查看」（交互矛盾）。
    if mine and "sys_admin" not in user.role_codes:
        allowed = scope.class_ids()
        if allowed is not None:
            stmt = stmt.where(Class.id.in_(allowed or [0]))
    items = []
    for c in db.scalars(stmt.order_by(Class.id)).all():
        d = dictify(c)
        d["grade_name"] = db.get(Grade, c.grade_id).name if db.get(Grade, c.grade_id) else None
        d["student_count"] = db.scalar(
            select(func.count()).select_from(User).where(User.class_id == c.id)
        ) or 0
        head = db.get(User, c.head_teacher_id) if c.head_teacher_id else None
        d["head_teacher_name"] = head.real_name if head else None
        items.append(d)
    return ok(items)


@router.post("/classes", summary="新增班级")
def create_class(
    data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    _: User = Depends(require_perm("resource:class:write")),
):
    # 同年级下同名班级必须拦截：班级下拉按名称展示，出现两个「一年级(1)班」
    # 后学生归属、考勤与统计都会分裂且无法从界面区分。
    # 教师建班申请（create_class_request）一直有这道校验，管理员直接建班漏了。
    name = (data.get("name") or "").strip()
    grade_id = data.get("grade_id")
    if not name:
        raise BusinessException("请填写班级名称")
    if not grade_id or not db.get(Grade, grade_id):
        raise BusinessException("请选择年级")
    if db.scalar(select(Class).where(Class.name == name, Class.grade_id == grade_id)):
        raise BusinessException("该年级下已存在同名班级")
    k = Class(
        name=name, grade_id=grade_id,
        head_teacher_id=data.get("head_teacher_id"), remark=data.get("remark"),
    )
    db.add(k)
    db.commit()
    return ok(dictify(k), message="班级创建成功")


@router.put("/classes/{class_id}", summary="编辑班级")
def update_class(
    class_id: int, data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    _: User = Depends(require_perm("resource:class:write")),
):
    k = db.get(Class, class_id)
    if not k:
        raise NotFoundException("班级不存在")
    if "name" in data:
        new_name = (data.get("name") or "").strip()
        if not new_name:
            raise BusinessException("班级名称不能为空")
        # 改名同样要防重名（同年级内），否则绕过 create 的校验
        target_grade = data.get("grade_id", k.grade_id)
        dup = db.scalar(select(Class).where(
            Class.name == new_name, Class.grade_id == target_grade, Class.id != k.id))
        if dup:
            raise BusinessException("该年级下已存在同名班级")
        data["name"] = new_name
    for f in ("name", "head_teacher_id", "remark", "is_active"):
        if f in data:
            setattr(k, f, data[f])
    db.commit()
    return ok(dictify(k), message="班级已更新")


@router.delete("/classes/{class_id}", summary="删除班级")
def delete_class(
    class_id: int, db: Session = Depends(get_db), _: User = Depends(require_perm("resource:class:write")),
):
    k = db.get(Class, class_id)
    if not k:
        raise NotFoundException("班级不存在")
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
    db: Session = Depends(get_db), _: User = Depends(require_perm("resource:class:write")),
):
    """students: [{username, real_name, password?}]"""
    from app.core.security import hash_password
    from app.models import Role, UserRole

    k = db.get(Class, class_id)
    if not k:
        raise NotFoundException("班级不存在")

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
