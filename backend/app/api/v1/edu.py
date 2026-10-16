"""教学基础档案接口：年级、学科、知识点、班级。"""
import time
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.agents.rag import index_knowledge, reindex_all
from app.api.deps import DataScope, get_current_teacher, get_current_user, get_data_scope
from app.core.config import settings
from app.core.database import get_db
from app.core.exception import BusinessException, NotFoundException
from app.models import Class, Grade, KnowledgePoint, Subject, User
from app.utils.common import dictify, ok

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
    _: User = Depends(get_current_teacher),
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
    _: User = Depends(get_current_teacher),
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
    grade_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_teacher),
):
    grade = db.get(Grade, grade_id)
    if not grade:
        raise NotFoundException("年级不存在")
    db.delete(grade)
    db.commit()
    return ok(message="年级已删除")


# ---------------------------------------------------------------- 学科
@router.get("/subjects", summary="学科列表")
def list_subjects(
    grade_id: Optional[int] = None, keyword: Optional[str] = None,
    db: Session = Depends(get_db), _: User = Depends(get_current_user),
):
    stmt = select(Subject)
    if grade_id:
        stmt = stmt.where(Subject.grade_id == grade_id)
    if keyword:
        stmt = stmt.where(Subject.name.like(f"%{keyword}%"))
    rows = db.scalars(stmt.order_by(Subject.sort)).all()
    items = []
    for s in rows:
        d = dictify(s)
        d["grade_name"] = db.get(Grade, s.grade_id).name if db.get(Grade, s.grade_id) else None
        items.append(d)
    return ok(items)


@router.post("/subjects", summary="新增学科")
def create_subject(
    data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    _: User = Depends(get_current_teacher),
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
    _: User = Depends(get_current_teacher),
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
    subject_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_teacher),
):
    subject = db.get(Subject, subject_id)
    if not subject:
        raise NotFoundException("学科不存在")
    db.delete(subject)
    db.commit()
    return ok(message="学科已删除")


# ---------------------------------------------------------------- 知识点
@router.get("/knowledge", summary="知识点树")
def knowledge_tree(
    grade_id: Optional[int] = None, subject_id: Optional[int] = None,
    term: Optional[int] = None,
    keyword: Optional[str] = None, db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """知识点树。grade_id/subject_id 不传时返回全部（供前端初始化加载）。"""
    stmt = select(KnowledgePoint).where(KnowledgePoint.is_active.is_(True))
    if grade_id:
        stmt = stmt.where(KnowledgePoint.grade_id == grade_id)
    if subject_id:
        stmt = stmt.where(KnowledgePoint.subject_id == subject_id)
    if term:
        stmt = stmt.where(KnowledgePoint.term == term)
    if keyword:
        stmt = stmt.where(or_(KnowledgePoint.name.like(f"%{keyword}%"),
                              KnowledgePoint.keywords.like(f"%{keyword}%")))
    rows = list(db.scalars(stmt.order_by(KnowledgePoint.sort, KnowledgePoint.id)).all())
    return ok([dictify(r) for r in rows])


@router.get("/knowledge/list", summary="知识点平铺列表")
def knowledge_list(
    grade_id: Optional[int] = None, subject_id: Optional[int] = None,
    level: Optional[int] = None, keyword: Optional[str] = None,
    params_limit: int = Query(200, le=1000),
    db: Session = Depends(get_db), _: User = Depends(get_current_user),
):
    stmt = select(KnowledgePoint).where(KnowledgePoint.is_active.is_(True))
    if grade_id:
        stmt = stmt.where(KnowledgePoint.grade_id == grade_id)
    if subject_id:
        stmt = stmt.where(KnowledgePoint.subject_id == subject_id)
    if level:
        stmt = stmt.where(KnowledgePoint.level == level)
    if keyword:
        stmt = stmt.where(KnowledgePoint.name.like(f"%{keyword}%"))
    return ok([dictify(r) for r in db.scalars(stmt.limit(params_limit)).all()])


@router.post("/knowledge", summary="新增知识点")
def create_knowledge(
    data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    _: User = Depends(get_current_teacher),
):
    kp = KnowledgePoint(
        name=data["name"], grade_id=data["grade_id"], subject_id=data["subject_id"],
        level=int(data.get("level", 3)), parent_id=data.get("parent_id"),
        path=data.get("path"), term=int(data.get("term", 1)),
        code=data.get("code"), description=data.get("description"),
        difficulty=data.get("difficulty", "medium"),
        keywords=data.get("keywords"), sort=data.get("sort", 0),
    )
    db.add(kp)
    db.commit()
    db.refresh(kp)
    index_knowledge(kp)
    return ok(dictify(kp), message="知识点创建成功")


@router.put("/knowledge/{kp_id}", summary="编辑知识点")
def update_knowledge(
    kp_id: int, data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    _: User = Depends(get_current_teacher),
):
    kp = db.get(KnowledgePoint, kp_id)
    if not kp:
        raise NotFoundException("知识点不存在")
    for f in ("name", "level", "parent_id", "path", "term", "code", "description",
              "difficulty", "keywords", "sort", "is_active"):
        if f in data:
            setattr(kp, f, data[f])
    db.commit()
    index_knowledge(kp)
    return ok(dictify(kp), message="知识点已更新")


@router.delete("/knowledge/{kp_id}", summary="删除知识点")
def delete_knowledge(
    kp_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_teacher),
):
    kp = db.get(KnowledgePoint, kp_id)
    if not kp:
        raise NotFoundException("知识点不存在")
    db.delete(kp)
    db.commit()
    return ok(message="知识点已删除")


@router.post("/knowledge/reindex", summary="重建向量索引")
def reindex(db: Session = Depends(get_db), _: User = Depends(get_current_teacher)):
    """全量重建向量索引。

    `reindex_all` 已改为批量 upsert（耗时下降一个数量级），
    但仍可能因首次下载 embedding 模型（~79MB）或数据量过大而很慢。
    这里传入 **wall-clock deadline**：到点后 reindex_all 在批间自行收尾，
    保留已完成部分并返回 timed_out 标记，避免长时间挂起拖死调用方。
    """
    t0 = time.time()
    budget = settings.REINDEX_TIMEOUT_SEC
    stats = reindex_all(db, deadline=time.monotonic() + budget)
    elapsed = int((time.time() - t0) * 1000)
    stats["elapsed_ms"] = elapsed

    if stats.get("timed_out"):
        return ok(stats, message=(
            f"向量索引重建超时（>{budget}s），已中断并保留已完成部分。"
            "若为首次运行，多因需要下载 embedding 模型，请检查网络后重试"
        ))
    slow = elapsed > settings.REINDEX_WARN_MS
    return ok(
        stats,
        message=("向量索引重建完成" if not slow
                 else f"向量索引重建耗时偏长({elapsed}ms)，建议分批执行"),
    )


# ---------------------------------------------------------------- 班级
@router.get("/classes", summary="班级列表")
def list_classes(
    grade_id: Optional[int] = None, keyword: Optional[str] = None,
    db: Session = Depends(get_db), _: User = Depends(get_current_user),
):
    stmt = select(Class)
    if grade_id:
        stmt = stmt.where(Class.grade_id == grade_id)
    if keyword:
        stmt = stmt.where(Class.name.like(f"%{keyword}%"))
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
    _: User = Depends(get_current_teacher),
):
    k = Class(
        name=data["name"], grade_id=data["grade_id"],
        head_teacher_id=data.get("head_teacher_id"), remark=data.get("remark"),
    )
    db.add(k)
    db.commit()
    return ok(dictify(k), message="班级创建成功")


@router.put("/classes/{class_id}", summary="编辑班级")
def update_class(
    class_id: int, data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    _: User = Depends(get_current_teacher),
):
    k = db.get(Class, class_id)
    if not k:
        raise NotFoundException("班级不存在")
    for f in ("name", "head_teacher_id", "remark", "is_active"):
        if f in data:
            setattr(k, f, data[f])
    db.commit()
    return ok(dictify(k), message="班级已更新")


@router.delete("/classes/{class_id}", summary="删除班级")
def delete_class(
    class_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_teacher),
):
    k = db.get(Class, class_id)
    if not k:
        raise NotFoundException("班级不存在")
    db.delete(k)
    db.commit()
    return ok(message="班级已删除")


@router.post("/classes/{class_id}/students", summary="批量导入学生")
def import_students(
    class_id: int, students: List[Dict[str, Any]] = Body(...),
    db: Session = Depends(get_db), _: User = Depends(get_current_teacher),
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
    _: User = Depends(get_current_teacher),
):
    u = db.get(User, student_id)
    if not u:
        raise NotFoundException("学生不存在")
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
