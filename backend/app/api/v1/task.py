"""作业 / 考试发布与学生端答题接口。"""
from datetime import timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends
from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import Session

from app.api.deps import (
    DataScope, get_current_user, get_data_scope, require_perm,
)
from app.core.config import settings
from app.core.database import get_db
from app.core.exception import BusinessException, NotFoundException, PermissionException
from app.models import (
    Answer, Class, Notification, Paper, Submission, Task, TaskAssignment, TaskStatus,
    TaskType, User,
)
from app.services import grading_service
from app.utils.common import PageParams, dictify, now_local, ok

router = APIRouter(prefix="/task", tags=["作业与考试"])

TYPE_LABEL = {"homework": "作业", "exam": "考试", "practice": "随机练习"}

# 教学管理 V2：任务读/写/批改权限点（与 docs/TEACHING_V2.md 一致）
TASK_PERM_LIST = "task:list"
TASK_PERM_WRITE = "task:write"

TASK_SORT_MAP = {
    "created_desc": (Task.created_at.desc(), Task.id.desc()),
    "start_desc": (Task.start_at.desc().nullslast(), Task.id.desc()),
    "end_desc": (Task.end_at.desc().nullslast(), Task.id.desc()),
    "updated_desc": (Task.updated_at.desc(), Task.id.desc()),
}


def _is_sys_admin(user: User) -> bool:
    return "sys_admin" in (user.role_codes or [])


def _is_grade_admin(user: User) -> bool:
    return "grade_admin" in (user.role_codes or [])


def _task_scope_clause(user: User, scope: DataScope):
    """任务读取范围：sys_admin 全量；grade_admin 按 DataScope 本年级；教师仅本人创建。"""
    if _is_sys_admin(user):
        return None
    if _is_grade_admin(user):
        grade_ids = scope.grade_ids() or []
        return Task.grade_id.in_(grade_ids) if grade_ids else (Task.id == -1)
    return Task.creator_id == user.id


def _task_readable(task: Task, user: User, scope: DataScope) -> bool:
    if _is_sys_admin(user) or task.creator_id == user.id:
        return True
    if _is_grade_admin(user):
        return task.grade_id in (scope.grade_ids() or [])
    return False


def _task_editable(task: Task, user: User) -> bool:
    """编辑/删除/批量写：仅创建者或 sys_admin（grade_admin 只读本年级）。"""
    return _is_sys_admin(user) or task.creator_id == user.id


def _task_submission_stats(db: Session, task_ids: List[int]) -> Dict[int, tuple]:
    """批量统计任务提交数/平均分/已批改数/已发布数，避免逐任务查询。"""
    if not task_ids:
        return {}
    rows = db.execute(
        select(
            Submission.task_id,
            func.count(Submission.id),
            func.avg(Submission.score),
            func.sum(case(
                (Submission.status.in_(("fully_graded", "published", "graded")), 1),
                else_=0)),
            func.sum(case((Submission.status == "published", 1), else_=0)),
        ).where(Submission.task_id.in_(task_ids)).group_by(Submission.task_id)
    ).all()
    return {
        int(tid): (int(cnt or 0), round(float(avg or 0), 2), int(g or 0), int(p or 0))
        for tid, cnt, avg, g, p in rows
    }


def _task_assigned_sets(
    db: Session, tasks: List[Task]
) -> Dict[int, tuple]:
    """返回 {task_id: (应交学生 id 集合, 班级名称列表)}（班级成员批量展开）。"""
    class_ids: set = set()
    for t in tasks:
        for a in t.assignments:
            if a.class_id and not a.student_id:
                class_ids.add(a.class_id)
    class_members: Dict[int, set] = {}
    class_names: Dict[int, str] = {}
    if class_ids:
        for cid, uid in db.execute(
            select(User.class_id, User.id).where(User.class_id.in_(class_ids))
        ).all():
            class_members.setdefault(cid, set()).add(uid)
        class_names = {
            c.id: c.name for c in db.scalars(
                select(Class).where(Class.id.in_(class_ids))).all()
        }
    result: Dict[int, tuple] = {}
    for t in tasks:
        ids: set = set()
        names: List[str] = []
        for a in t.assignments:
            if a.student_id:
                ids.add(a.student_id)
            elif a.class_id:
                ids.update(class_members.get(a.class_id, set()))
                if a.class_id in class_names:
                    names.append(class_names[a.class_id])
        result[t.id] = (ids, names)
    return result


def _filtered_tasks_stmt(
    user: User, scope: DataScope, *, task_type: Optional[str] = None,
    status: Optional[str] = None, subject_id: Optional[int] = None,
    class_id: Optional[int] = None, keyword: Optional[str] = None,
):
    """任务列表/统计共用筛选构造（含读取范围）。"""
    stmt = select(Task)
    clause = _task_scope_clause(user, scope)
    if clause is not None:
        stmt = stmt.where(clause)
    if task_type:
        stmt = stmt.where(Task.type == task_type)
    if status:
        stmt = stmt.where(Task.status == status)
    if subject_id:
        stmt = stmt.where(Task.subject_id == subject_id)
    if keyword:
        stmt = stmt.where(Task.title.like(f"%{keyword}%"))
    if class_id:
        class_students = select(User.id).where(User.class_id == class_id)
        assigned = select(TaskAssignment.task_id).where(or_(
            TaskAssignment.class_id == class_id,
            TaskAssignment.student_id.in_(class_students),
        ))
        stmt = stmt.where(Task.id.in_(assigned))
    return stmt


def is_task_assigned_to(db: Session, task: Task, user: User) -> bool:
    """判断任务是否下发给该用户（按 student_id / class_id 两条下发路径）。

    TaskAssignment 支持三种范围：指定学生、指定班级、分组。
    分组目前无成员表，故按「有班级或指定本人」判定。
    任务创建者与系统管理员不受此限制（教师需预览自己的卷子）。
    """
    if task.creator_id == user.id:
        return True
    if "sys_admin" in user.role_codes:
        return True
    q = select(TaskAssignment.id).where(TaskAssignment.task_id == task.id)
    if db.scalar(q.where(TaskAssignment.student_id == user.id)):
        return True
    if user.class_id and db.scalar(
        q.where(TaskAssignment.class_id == user.class_id)
    ):
        return True
    return False


def assert_task_accessible(db: Session, task: Task, user: User) -> None:
    """作答类接口的统一归属校验。

    此前 `/tasks/{id}/paper` 只校验发布时间，**未校验任务是否下发给当前用户**，
    导致任意登录用户遍历 task_id 即可拿到他人考试的题目并作答（越权）。
    这里补上归属判断；创建者与超管豁免。
    """
    if not is_task_assigned_to(db, task, user):
        raise PermissionException("该任务未下发给当前用户")


# ---------------------------------------------------------------- 教师端
@router.get("/tasks", summary="作业考试列表（教师）")
def list_tasks(
    params: PageParams = Depends(), task_type: Optional[str] = None,
    status: Optional[str] = None, subject_id: Optional[int] = None,
    class_id: Optional[int] = None, keyword: Optional[str] = None,
    sort: str = "created_desc", db: Session = Depends(get_db),
    user: User = Depends(require_perm(TASK_PERM_LIST)),
    scope: DataScope = Depends(get_data_scope),
):
    stmt = _filtered_tasks_stmt(
        user, scope, task_type=task_type, status=status,
        subject_id=subject_id, class_id=class_id, keyword=keyword,
    )
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(
        stmt.order_by(*TASK_SORT_MAP.get(sort, TASK_SORT_MAP["created_desc"]))
        .offset(params.offset).limit(params.page_size)
    ).all()

    task_ids = [t.id for t in rows]
    sub_stats = _task_submission_stats(db, task_ids)
    assigned_map = _task_assigned_sets(db, rows)

    items = []
    for t in rows:
        d = dictify(t)
        d["type_label"] = TYPE_LABEL.get(t.type, t.type)
        subs, avg_score, graded_count, published_count = sub_stats.get(
            t.id, (0, 0.0, 0, 0))
        assigned_ids, class_names = assigned_map.get(t.id, (set(), []))
        d["assignment_count"] = len(t.assignments)
        d["submission_count"] = subs
        d["assigned_count"] = len(assigned_ids)
        d["completion_rate"] = (
            round(min(subs, len(assigned_ids)) / len(assigned_ids) * 100, 2)
            if assigned_ids else 0
        )
        # V2 新增字段（旧字段全部保留）
        d["class_names"] = class_names
        d["avg_score"] = avg_score
        d["graded_count"] = graded_count
        d["published_count"] = published_count
        items.append(d)
    return ok({"items": items, "total": total, "page": params.page})


@router.get("/tasks/stats", summary="作业考试统计")
def task_stats(
    task_type: Optional[str] = None, status: Optional[str] = None,
    subject_id: Optional[int] = None, class_id: Optional[int] = None,
    keyword: Optional[str] = None, db: Session = Depends(get_db),
    user: User = Depends(require_perm(TASK_PERM_LIST)),
    scope: DataScope = Depends(get_data_scope),
):
    """同列表筛选范围（不分页）的任务统计。"""
    stmt = _filtered_tasks_stmt(
        user, scope, task_type=task_type, status=status,
        subject_id=subject_id, class_id=class_id, keyword=keyword,
    )
    rows = list(db.scalars(stmt).all())
    total = len(rows)
    draft = sum(1 for t in rows if t.status == TaskStatus.DRAFT.value)
    finished = sum(1 for t in rows if t.status in (
        TaskStatus.FINISHED.value, TaskStatus.ARCHIVED.value))
    ongoing = max(0, total - draft - finished)

    task_ids = [t.id for t in rows]
    sub_stats = _task_submission_stats(db, task_ids)
    assigned_map = _task_assigned_sets(db, rows)

    submission_count = sum(v[0] for v in sub_stats.values())
    assigned_count = sum(len(v[0]) for v in assigned_map.values())
    rates = []
    for t in rows:
        subs = sub_stats.get(t.id, (0, 0.0, 0, 0))[0]
        assigned = len(assigned_map.get(t.id, (set(), []))[0])
        if assigned:
            rates.append(min(subs, assigned) / assigned * 100)
    return ok({
        "total": total,
        "ongoing": ongoing,
        "finished": finished,
        "draft": draft,
        "assigned_count": assigned_count,
        "submission_count": submission_count,
        "avg_completion": round(sum(rates) / len(rates), 2) if rates else 0,
    })


@router.post("/tasks/batch", summary="批量操作作业考试")
def batch_tasks(
    data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    user: User = Depends(require_perm(TASK_PERM_WRITE)),
):
    """批量结束/发布/删除任务。同批含有权任务 → 整体 403；业务失败进 skipped。"""
    action = str(data.get("action") or "").strip().lower()
    if action not in {"close", "publish", "delete"}:
        raise BusinessException("action 仅支持 close / publish / delete")
    raw_ids = data.get("ids") or []
    if not isinstance(raw_ids, list) or not raw_ids:
        raise BusinessException("请选择要操作的任务")
    ids: List[int] = []
    for item in raw_ids:
        try:
            value = int(item)
        except (TypeError, ValueError):
            raise BusinessException("ids 必须为整数列表")
        if value not in ids:
            ids.append(value)

    found = {
        t.id: t for t in db.scalars(select(Task).where(Task.id.in_(ids))).all()
    }
    tasks = [found[i] for i in ids if i in found]
    skipped: List[Dict[str, Any]] = [
        {"id": i, "reason": "不存在"} for i in ids if i not in found]
    if not tasks:
        return ok({"done": [], "skipped": skipped})
    # 同批只要有一个任务无权操作，整体 403（防部分写入歧义）
    if any(not _task_editable(t, user) for t in tasks):
        raise PermissionException("所选任务中存在无权操作的任务，已拒绝整批操作")

    done: List[int] = []
    if action == "delete":
        sub_counts = dict(db.execute(
            select(Submission.task_id, func.count()).where(
                Submission.task_id.in_([t.id for t in tasks])
            ).group_by(Submission.task_id)
        ).all())
        for t in tasks:
            count = int(sub_counts.get(t.id, 0) or 0)
            if count:
                skipped.append({
                    "id": t.id,
                    "reason": f"该任务已有 {count} 份提交，删除会连带丢失成绩",
                })
                continue
            db.delete(t)
            done.append(t.id)
    elif action == "close":
        for t in tasks:
            t.status = TaskStatus.FINISHED.value
            done.append(t.id)
    else:  # publish
        for t in tasks:
            if t.status != TaskStatus.DRAFT.value:
                skipped.append({"id": t.id, "reason": "仅草稿任务可发布"})
                continue
            t.status = TaskStatus.PUBLISHED.value
            t.publish_at = now_local()
            done.append(t.id)

    db.commit()
    return ok({"done": done, "skipped": skipped},
              message=f"批量操作完成 {len(done)} 个，跳过 {len(skipped)} 个")


@router.post("/tasks", summary="发布作业 / 考试")
def create_task(
    data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    user: User = Depends(require_perm(TASK_PERM_WRITE)),
):
    paper = db.get(Paper, data.get("paper_id"))
    if not paper:
        raise BusinessException("请选择试卷")

    # 校验任务类型：仅允许 homework / exam，非法值直接拒绝，
    # 否则 db 会写脏数据进入 task.type（SQLite String 列不强制枚举）
    raw_type = data.get("type", TaskType.HOMEWORK.value)
    valid_types = {t.value for t in TaskType}
    if raw_type not in valid_types:
        raise BusinessException(
            f"无效的任务类型 {raw_type!r}，允许：{','.join(sorted(valid_types))}")
    task_type = raw_type
    start_at = _parse_dt(data.get("start_at")) or now_local()
    end_at = _parse_dt(data.get("end_at")) or (start_at + timedelta(days=7))
    publish_at = _parse_dt(data.get("publish_at"))
    # 定时发布：publish_at 在未来 → 草稿状态落库、暂不通知学生，
    # 由内置任务 publish_scheduled_tasks 到期激活并补发通知。
    scheduled = bool(publish_at and publish_at > now_local())

    # 参数范围校验（此前完全不校验，可写出 pass_score=9999、
    # duration=0、end_at 早于 start_at 的脏任务）
    # 注意：不能用 or 兜底取默认值——duration=0 是非法输入而非"未传"，
    # `0 or paper.duration` 会静默采用试卷时长，校验形同虚设。
    raw_duration = data.get("duration")
    duration_val = int(raw_duration) if raw_duration is not None else int(paper.duration or 0)
    if duration_val <= 0:
        raise BusinessException("考试时长必须大于 0 分钟")
    # 及格分默认值必须与试卷总分匹配：settings.PASS_SCORE=60 是百分制假设，
    # 遇到总分 5 分的随堂练习会导致「默认参数永远无法发布」，故超出时按 60% 折算。
    total = float(paper.total_score or 100)
    if data.get("pass_score") is None:
        pass_score = settings.PASS_SCORE if settings.PASS_SCORE <= total else round(total * 0.6, 2)
    else:
        pass_score = float(data["pass_score"])
    if not (0 < pass_score <= total):
        raise BusinessException(f"及格分应在 0~{total} 之间，当前 {pass_score}")
    if end_at <= start_at:
        raise BusinessException("截止时间必须晚于开始时间")

    task = Task(
        title=data.get("title") or paper.name, type=task_type, paper_id=paper.id,
        subject_id=paper.subject_id, grade_id=paper.grade_id, creator_id=user.id,
        status=TaskStatus.DRAFT.value if scheduled else TaskStatus.PUBLISHED.value,
        start_at=start_at, end_at=end_at,
        duration=duration_val,
        publish_at=publish_at,
        allow_retake=int(data.get("allow_retake", 1)),
        show_answer=bool(data.get("show_answer", True)),
        anti_cheat=bool(data.get("anti_cheat", False)),
        total_score=paper.total_score,
        pass_score=pass_score,
        description=data.get("description"),
    )
    db.add(task)
    db.flush()

    # 下发范围
    student_ids: List[int] = []
    class_ids: List[int] = data.get("class_ids", [])
    student_ids.extend(data.get("student_ids", []))
    # 没有任何下发对象的任务学生永远看不到（孤儿任务），直接拒绝。
    # 定时发布同样需要下发对象。
    if not class_ids and not student_ids:
        raise BusinessException("请选择下发班级或学生")

    # 下发对象存在性 + 教师任教范围校验（管理员不限）
    role_codes = user.role_codes
    is_admin = "sys_admin" in role_codes
    for cid in class_ids:
        if not db.get(Class, cid):
            raise BusinessException(f"班级 {cid} 不存在")
        if not is_admin:
            scope = DataScope(user=user, db=db)
            allowed = scope.class_ids()
            if allowed is not None and cid not in allowed:
                raise BusinessException(f"只能给自己任教的班级下发（班级 {cid} 不在任教范围）")
    for sid in student_ids:
        if not db.get(User, sid):
            raise BusinessException(f"学生 {sid} 不存在")

    for cid in class_ids:
        db.add(TaskAssignment(task_id=task.id, class_id=cid))
    for sid in student_ids:
        db.add(TaskAssignment(task_id=task.id, student_id=sid))

    if scheduled:
        paper.use_count += 1
        db.commit()
        db.refresh(task)
        return ok(
            dictify(task),
            message=f"{TYPE_LABEL.get(task_type)}已保存，将于 "
                    f"{publish_at.strftime('%Y-%m-%d %H:%M')} 自动发布",
        )

    # 通知学生
    notify_ids = set(student_ids)
    for cid in class_ids:
        notify_ids.update(
            db.scalars(select(User.id).where(User.class_id == cid, User.status == "active")).all()
        )
    for sid in notify_ids:
        db.add(Notification(
            user_id=sid,
            title=f"新的{TYPE_LABEL.get(task_type, '任务')}发布",
            content=f"{task.title}，截止时间：{end_at.strftime('%Y-%m-%d %H:%M')}",
            type="exam", biz_type="task", biz_id=task.id,
        ))
    db.execute(
        TaskAssignment.__table__.update()
        .where(TaskAssignment.task_id == task.id)
        .values(notified=True)
    )
    paper.use_count += 1
    db.commit()
    db.refresh(task)
    return ok(dictify(task), message=f"{TYPE_LABEL.get(task_type)}发布成功，已通知 {len(notify_ids)} 名学生")


@router.get("/tasks/{task_id}", summary="任务详情")
def get_task(
    task_id: int, db: Session = Depends(get_db),
    user: User = Depends(require_perm(TASK_PERM_LIST)),
    scope: DataScope = Depends(get_data_scope),
):
    """任务详情：教师仅看自己创建的；grade_admin 可看本年级；sys_admin 全量。"""
    task = db.get(Task, task_id)
    if not task:
        raise NotFoundException("任务不存在")
    if not _task_readable(task, user, scope):
        raise PermissionException("无权限查看该任务")
    return ok(dictify(task))


@router.put("/tasks/{task_id}", summary="编辑任务")
def update_task(
    task_id: int, data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    user: User = Depends(require_perm(TASK_PERM_WRITE)),
):
    task = db.get(Task, task_id)
    if not task:
        raise NotFoundException("任务不存在")
    if not _task_editable(task, user):
        raise PermissionException("无权限编辑该任务")

    # 编辑接口此前直接 setattr：null/字符串可写进非空列、duration=0、
    # pass_score 超过总分、end_at 早于 start_at 都能落库（create 校验形同虚设）。
    # 这里与 create_task 使用同一套范围校验，非法输入返回 400 而不是 500。
    updates: Dict[str, Any] = {}
    if "title" in data:
        title = str(data.get("title") or "").strip()
        if not title:
            raise BusinessException("标题不能为空")
        if len(title) > 128:
            raise BusinessException("标题不能超过 128 个字符")
        updates["title"] = title
    if "description" in data:
        description = str(data.get("description") or "")
        if len(description) > 20000:
            raise BusinessException("任务说明不能超过 20000 个字符")
        updates["description"] = description
    if "duration" in data:
        try:
            duration = int(data["duration"])
        except (TypeError, ValueError):
            raise BusinessException("考试时长必须是整数分钟") from None
        if duration <= 0:
            raise BusinessException("考试时长必须大于 0 分钟")
        updates["duration"] = duration
    if "allow_retake" in data:
        try:
            allow_retake = int(data["allow_retake"])
        except (TypeError, ValueError):
            raise BusinessException("允许作答次数必须是整数") from None
        if allow_retake < 1:
            raise BusinessException("允许作答次数至少为 1")
        updates["allow_retake"] = allow_retake
    for flag in ("show_answer", "anti_cheat"):
        if flag in data:
            if not isinstance(data[flag], bool):
                raise BusinessException(f"{flag} 必须是布尔值")
            updates[flag] = data[flag]
    if "pass_score" in data:
        try:
            pass_score = float(data["pass_score"])
        except (TypeError, ValueError):
            raise BusinessException("及格分必须是数字") from None
        total = float(task.total_score or 100)
        if not (0 < pass_score <= total):
            raise BusinessException(f"及格分应在 0~{total} 之间，当前 {pass_score}")
        updates["pass_score"] = pass_score

    start_at = task.start_at
    end_at = task.end_at
    if data.get("start_at"):
        start_at = _parse_dt(data["start_at"])
        if start_at is None:
            raise BusinessException("开始时间格式不正确")
    if data.get("end_at"):
        end_at = _parse_dt(data["end_at"])
        if end_at is None:
            raise BusinessException("截止时间格式不正确")
    if start_at and end_at and end_at <= start_at:
        raise BusinessException("截止时间必须晚于开始时间")

    for key, value in updates.items():
        setattr(task, key, value)
    task.start_at = start_at
    task.end_at = end_at
    db.commit()
    return ok(message="任务已更新")


@router.delete("/tasks/{task_id}", summary="删除任务")
def delete_task(
    task_id: int, db: Session = Depends(get_db),
    user: User = Depends(require_perm(TASK_PERM_WRITE)),
):
    task = db.get(Task, task_id)
    if not task:
        raise NotFoundException("任务不存在")
    if not _task_editable(task, user):
        raise PermissionException("无权限删除该任务")
    db.delete(task)
    db.commit()
    return ok(message="任务已删除")


@router.get("/tasks/{task_id}/submissions", summary="任务提交情况")
def task_submissions(
    task_id: int, params: PageParams = Depends(), class_id: Optional[int] = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_perm(TASK_PERM_LIST)),
    scope: DataScope = Depends(get_data_scope),
):
    task = db.get(Task, task_id)
    if not task:
        raise NotFoundException("任务不存在")
    # 数据范围：任务创建者 / 本年级管理员（DataScope）/ sys_admin 可看提交名单，
    # 其余教师遍历 task_id 不能获取他人任务的学生成绩。
    if not _task_readable(task, user, scope):
        raise PermissionException("无权限查看该任务的提交情况")

    stmt = select(Submission).where(Submission.task_id == task_id)
    if class_id:
        stmt = stmt.where(Submission.student_id.in_(
            select(User.id).where(User.class_id == class_id)
        ))
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(
        stmt.order_by(Submission.score.desc().nullslast())
        .offset(params.offset).limit(params.page_size)
    ).all()

    # 批量预取本页学生，避免循环内逐条 db.get(User)
    stu_ids = {s.student_id for s in rows if s.student_id}
    stu_map: Dict[int, User] = {
        u.id: u for u in db.scalars(select(User).where(User.id.in_(stu_ids))).all()
    } if stu_ids else {}

    items = []
    for s in rows:
        stu = stu_map.get(s.student_id)
        items.append({
            "submission_id": s.id, "student_id": s.student_id,
            "student_name": stu.real_name if stu else "",
            "class_id": stu.class_id if stu else None,
            "attempt": s.attempt, "score": s.score, "is_passed": s.is_passed,
            "class_rank": s.class_rank, "status": s.status,
            "switch_count": s.switch_count,
            "total_score": task.total_score,
            "duration_seconds": s.duration_seconds,
            "submit_time": s.submit_time.strftime("%Y-%m-%d %H:%M:%S") if s.submit_time else None,
        })

    # 应交名单与完成率：先收集学生 id 与班级 id，再一次 IN 查询，
    # 避免每遇到一条班级下发就查一次用户表（N+1）。
    assigned_ids: set = set()
    class_ids: set = set()
    for a in task.assignments:
        if a.student_id:
            assigned_ids.add(a.student_id)
        elif a.class_id:
            class_ids.add(a.class_id)
    if class_ids:
        assigned_ids.update(
            db.scalars(select(User.id).where(User.class_id.in_(class_ids))).all()
        )
    submitted_ids = {s.student_id for s in rows} | set(
        db.scalars(select(Submission.student_id).where(Submission.task_id == task_id)).all()
    )
    pending = list(assigned_ids - submitted_ids)

    # 待交名单只展示前 50 人：一次批量取名，替代逐人两次 db.get(User)
    pending_page = pending[:50]
    pending_user_ids = {pid for pid in pending_page if pid}
    pending_names = {
        u.id: u.real_name for u in db.scalars(
            select(User).where(User.id.in_(pending_user_ids))
        ).all()
    } if pending_user_ids else {}

    return ok({
        "items": items, "total": total, "assigned": len(assigned_ids),
        "submitted": len(submitted_ids & assigned_ids) if assigned_ids else len(submitted_ids),
        "completion_rate": round(len(submitted_ids & assigned_ids) / len(assigned_ids) * 100, 2)
        if assigned_ids else 0,
        "pending_students": [
            {"id": pid, "name": pending_names.get(pid, "")}
            for pid in pending_page
        ],
    })


# ---------------------------------------------------------------- 学生端
@router.get("/my/tasks", summary="我的作业考试")
def my_tasks(
    params: PageParams = Depends(), task_type: Optional[str] = None,
    status: Optional[str] = None, db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    my_ids = set()
    stmt = select(TaskAssignment).where(TaskAssignment.student_id == user.id)
    for a in db.scalars(stmt).all():
        my_ids.add(a.task_id)
    # 班级下发的任务
    if user.class_id:
        for a in db.scalars(
            select(TaskAssignment).where(TaskAssignment.class_id == user.class_id)
        ).all():
            my_ids.add(a.task_id)
    if not my_ids:
        return ok({"items": [], "total": 0})

    q = select(Task).where(
        Task.id.in_(my_ids),
        Task.type != TaskType.PRACTICE.value,
        # 定时发布的任务到期前对学生不可见
        Task.status != TaskStatus.DRAFT.value,
        (Task.publish_at.is_(None)) | (Task.publish_at <= now_local()),
    )
    if task_type:
        q = q.where(Task.type == task_type)
    if status:
        q = q.where(Task.status == status)

    total = db.scalar(select(func.count()).select_from(q.subquery())) or 0
    rows = db.scalars(
        q.order_by(Task.end_at.desc().nullslast())
        .offset(params.offset).limit(params.page_size)
    ).all()

    items = []
    for t in rows:
        d = dictify(t)
        d["type_label"] = TYPE_LABEL.get(t.type, t.type)
        sub = db.scalar(
            select(Submission).where(
                Submission.task_id == t.id, Submission.student_id == user.id
            ).order_by(Submission.attempt.desc()).limit(1)
        )
        d["my_submission"] = dictify(sub) if sub else None
        d["attempt_count"] = db.scalar(
            select(func.count()).select_from(Submission).where(
                Submission.task_id == t.id, Submission.student_id == user.id
            )
        ) or 0
        # 距截止
        if t.end_at:
            delta = (t.end_at - now_local()).total_seconds()
            d["remaining_seconds"] = int(delta) if delta > 0 else 0
        items.append(d)
    return ok({"items": items, "total": total, "page": params.page})


@router.get("/tasks/{task_id}/paper", summary="获取试卷（作答用，不含答案）")
def get_task_paper(
    task_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    task = db.get(Task, task_id)
    if not task:
        raise NotFoundException("任务不存在")
    paper = db.get(Paper, task.paper_id)
    if not paper:
        raise NotFoundException("试卷不存在")

    # 发布/开考时间管控（任务创建者豁免，便于教师预览）：
    # 未发布或未到开考时间，禁止提前获取题目，防止泄题。
    is_creator = task.creator_id == user.id
    # 归属校验：任务必须下发给当前用户，否则遍历 task_id 即可越权作答他人考试
    assert_task_accessible(db, task, user)
    now = now_local()
    if not is_creator:
        if task.status == TaskStatus.DRAFT.value or (
            task.publish_at and task.publish_at > now
        ):
            raise PermissionException("任务尚未发布")
        if task.start_at and task.start_at > now:
            raise PermissionException("考试尚未开始，请按时进入")

    # 答案可见性判定：仅任务创建者，或（允许显示答案 且 学生已交卷/任务已截止）可见
    has_submitted = db.scalar(
        select(Submission.id).where(
            Submission.task_id == task_id,
            Submission.student_id == user.id,
            Submission.submit_time.isnot(None),
        )
    ) is not None
    # 已交卷状态回传给答题页：否则学生重新打开 /student/exam/{id} 会看到
    # 一张全新的可作答试卷，做完一场才在交卷时被 400「次数已用完」打回。
    my_sub = db.scalar(
        select(Submission).where(
            Submission.task_id == task_id, Submission.student_id == user.id,
        ).order_by(Submission.attempt.desc()).limit(1)
    )
    task_finished = bool(task.end_at and task.end_at < now_local())
    reveal_answer = is_creator or (task.show_answer and (has_submitted or task_finished))

    items = []
    for it in sorted(paper.items, key=lambda x: x.sort_order):
        q = it.question
        d = {
            "paper_item_id": it.id, "question_id": q.id, "sort_order": it.sort_order,
            "score": it.score, "section_name": it.section_name, "type": q.type,
            "stem": q.stem, "options": _load(q.options),
        }
        if reveal_answer:
            d["answer"] = _load(q.answer)
            d["analysis"] = q.analysis
        items.append(d)

    return ok({
        "task": {
            "id": task.id, "title": task.title, "type": task.type, "duration": task.duration,
            "total_score": task.total_score, "start_at": dictify(task.start_at),
            "end_at": dictify(task.end_at), "anti_cheat": task.anti_cheat,
            "allow_retake": task.allow_retake, "show_answer": task.show_answer,
            "my_submission": None if my_sub is None else {
                "id": my_sub.id,
                "score": my_sub.score,
                "total_score": task.total_score,
                "status": my_sub.status,
                "submit_time": dictify(my_sub.submit_time),
                "attempt": my_sub.attempt,
            },
            "max_attempt": max(int(task.allow_retake or 1), 1),
        },
        "paper": {"id": paper.id, "name": paper.name, "total_score": paper.total_score},
        "items": items,
    })


@router.post("/tasks/{task_id}/submit", summary="提交作答")
def submit_answers(
    task_id: int, data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    task = db.get(Task, task_id)
    if not task:
        raise NotFoundException("任务不存在")
    # 归属校验：未下发给当前用户的任务不允许提交（防越权交卷）
    assert_task_accessible(db, task, user)
    if task.status == TaskStatus.DRAFT.value or (
        task.publish_at and task.publish_at > now_local()
    ):
        raise BusinessException("任务尚未发布，无法提交")
    if task.status in (TaskStatus.FINISHED.value, TaskStatus.ARCHIVED.value):
        raise BusinessException("任务已结束，无法提交")
    if task.end_at and task.end_at < now_local():
        raise BusinessException("任务已截止，无法提交")
    if task.start_at and task.start_at > now_local():
        raise BusinessException("任务尚未开始")

    # 服务端兜底校验单次作答时长：前端倒计时可被绕过（改系统时钟 / 直接调
    # 接口），这里按 task.duration（分钟）换算并留 300 秒容差，拦截明显超时
    # 的提交。duration_seconds 缺省或非法时不限制，保持对老客户端宽容。
    raw_duration = data.get("duration_seconds")
    try:
        submitted_duration = float(raw_duration) if raw_duration is not None else None
    except (TypeError, ValueError):
        submitted_duration = None
    if (
        submitted_duration is not None and submitted_duration > 0
        and task.duration and task.duration > 0
        and submitted_duration > task.duration * 60 + 300
    ):
        raise BusinessException("作答时长超出考试时长限制，无法提交")

    # attempt 一律由服务端判定：此前直接信任客户端传入值，
    # 学生传 attempt=99 即可绕过 allow_retake=1 无限重考。
    last = db.scalar(
        select(Submission).where(
            Submission.task_id == task_id, Submission.student_id == user.id,
        ).order_by(Submission.attempt.desc()).limit(1)
    )
    max_attempt = max(int(task.allow_retake or 1), 1)
    if last and last.submit_time:
        if last.attempt >= max_attempt:
            # 被教师打回（reject_submission 置 status=not_graded 且清空 score）：
            # 允许复用同一 attempt 覆盖重做，而不是报「次数已用完」，否则学生
            # 永远无法重新提交。交卷时仅因主观题待批而 not_graded 的卷子 score
            # 非空，不在放行范围，避免借此绕过 allow_retake 次数限制。
            if last.status == "not_graded" and last.score is None:
                attempt = last.attempt
            else:
                raise BusinessException(f"最多允许作答 {max_attempt} 次，已用完次数")
        else:
            attempt = last.attempt + 1
    else:
        # 未交卷的草稿沿用其 attempt，保证覆盖同一份而不是新建
        attempt = last.attempt if last else 1

    answers = data.get("answers", [])
    if not isinstance(answers, list):
        raise BusinessException("答题数据格式错误")

    # 单次交卷会按主观题数量放大 LLM 调用（每题一次往返）。限流必须放在
    # 任何业务写库之前（get_student_submission 会 flush 草稿、save_answers
    # 会 flush 作答记录，事务已开始后无法回滚这次调用成本）。
    # 仅在 LLM 真实可用时计数：纯客观题交卷不需要 AI，LLM 关闭时不应额外限流，
    # 否则「AI 未配置」的正常交卷会被学员的其它 AI 调用挤占额度。
    from app.agents.llm import is_available as _llm_available

    if _llm_available():
        from app.core.rate_limit import check_agent_rate

        check_agent_rate(db, user.id, cost=max(1, min(len(answers) // 3 + 1, 20)))

    sub = grading_service.get_student_submission(db, task_id, user.id, attempt)
    summary = grading_service.save_answers(db, sub, answers, auto_grade=True)
    result = grading_service.finalize_submission(
        db, sub, duration_seconds=data.get("duration_seconds")
    )
    db.refresh(sub)

    response = {
        "submission_id": sub.id,
        **result,
        "grading": summary,
    }
    if task.show_answer:
        from app.models import Question

        ans = db.scalars(select(Answer).where(Answer.submission_id == sub.id)).all()
        details = []
        for a in ans:
            q = db.get(Question, a.question_id)
            details.append({
                "paper_item_id": a.paper_item_id, "is_correct": a.is_correct,
                "score": a.score, "full_score": a.full_score, "comment": a.teacher_comment,
                "answer": _load(q.answer) if q else None,
                "analysis": q.analysis if q else None,
            })
        response["answers"] = details
    return ok(response, message="交卷成功")


@router.post("/tasks/{task_id}/heartbeat", summary="作答心跳（防切屏计时）")
def heartbeat(
    task_id: int, data: Dict[str, Any] = Body(default={}), db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """记录切屏次数与答题时长。"""
    sub = db.scalar(
        select(Submission).where(
            Submission.task_id == task_id, Submission.student_id == user.id
        ).order_by(Submission.attempt.desc()).limit(1)
    )
    if not sub:
        return ok(message="no active submission")
    # 已交卷记录不允许再改切屏次数/时长（否则交卷后可篡改考试行为数据）
    if sub.submit_time is not None:
        return ok({"switch_count": sub.switch_count}, message="已交卷，心跳忽略")
    # 心跳由前端每几十秒打一次，其中绝大多数请求既没切屏、时长也没变化。
    # 原实现无条件 commit：即使零变更也要抢一次 SQLite 写锁并提交空事务，
    # 全班同时答题时这条空写会被几十个客户端同时触发。现只在真有变更时提交，
    # 无变更直接返回当前值（返回结构与文案不变）。
    changed = False
    if data.get("switch"):
        sub.switch_count += 1
        changed = True
    duration = int(data.get("duration_seconds") or sub.duration_seconds or 0)
    if duration != sub.duration_seconds:
        sub.duration_seconds = duration
        changed = True
    if changed:
        db.commit()
    return ok({"switch_count": sub.switch_count})


@router.get("/submissions/{submission_id}", summary="作答详情（含解析）")
def submission_detail(
    submission_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user),
    scope: DataScope = Depends(get_data_scope),
):
    sub = db.get(Submission, submission_id)
    if not sub:
        raise NotFoundException("作答记录不存在")
    # 归属校验：本人 / 按角色分派。
    # 原判断只要角色是 teacher 就放行，导致**任何教师可遍历
    # submission_id 查看他人作答详情与答案解析**（含未教的班）。
    # 现按角色分派，并统一走 DataScope：
    # - 本人：始终可看
    # - sys_admin / grade_admin：DataScope 返回 None（不受限）
    # - teacher：仅授课班级内的学生（class_ids()）
    # - student：**只能看自己**，绝不因同班而看到同班同学的作答
    if sub.student_id != user.id:
        if "sys_admin" not in user.role_codes:
            if "teacher" not in user.role_codes and "grade_admin" not in user.role_codes:
                # 学生（含访客等无教学角色的账号）：仅本人
                raise PermissionException("无权查看该作答记录")
            allowed = scope.class_ids()
            stu_class = db.scalar(select(User.class_id).where(User.id == sub.student_id))
            if allowed is None:
                # grade_admin：本年级所有数据，DataScope 视其为不限
                if "grade_admin" not in user.role_codes:
                    raise PermissionException("无权查看该作答记录")
            elif stu_class is None or stu_class not in allowed:
                raise PermissionException("无权查看该作答记录")

    task = db.get(Task, sub.task_id)
    answers = []
    from app.models import Question

    for a in sub.answers:
        q = db.get(Question, a.question_id)
        answers.append({
            "question_id": a.question_id, "content": a.content,
            "is_correct": a.is_correct, "score": a.score, "full_score": a.full_score,
            "grader_type": a.grader_type, "comment": a.teacher_comment,
            "stem": q.stem if q else "", "options": _load(q.options) if q else None,
            "answer": _load(q.answer) if q else None, "analysis": q.analysis if q else None,
        })

    return ok({
        "id": sub.id, "task_id": sub.task_id, "task_title": task.title if task else None,
        "student_id": sub.student_id, "score": sub.score,
        "objective_score": sub.objective_score, "subjective_score": sub.subjective_score,
        "is_passed": sub.is_passed, "class_rank": sub.class_rank, "status": sub.status,
        "submit_time": dictify(sub.submit_time), "duration_seconds": sub.duration_seconds,
        "answers": answers,
    })


@router.get("/my/scores", summary="我的成绩中心")
def my_scores(
    params: PageParams = Depends(), db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(Submission).where(
        Submission.student_id == user.id, Submission.score.isnot(None)
    )
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(
        stmt.order_by(Submission.id.desc()).offset(params.offset).limit(params.page_size)
    ).all()
    items = []
    for s in rows:
        task = db.get(Task, s.task_id)
        d = dictify(s)
        d["task_title"] = task.title if task else None
        d["type"] = task.type if task else None
        d["type_label"] = TYPE_LABEL.get(task.type, "") if task else ""
        d["total_score"] = task.total_score if task else None
        items.append(d)

    # 汇总必须对「全量已评分记录」做 SQL 聚合：此前直接统计当前页 rows，
    # 翻到第 2 页后平均分/最高分/及格率会变成当页的统计（与 total 矛盾）。
    count, avg_score, max_score, min_score, passed = db.execute(
        select(
            func.count(Submission.id),
            func.avg(Submission.score),
            func.max(Submission.score),
            func.min(Submission.score),
            func.sum(case((Submission.is_passed.is_(True), 1), else_=0)),
        ).where(
            Submission.student_id == user.id,
            Submission.score.isnot(None),
        )
    ).one()
    count = int(count or 0)
    return ok({
        "items": items, "total": total, "page": params.page,
        "summary": {
            "count": count,
            "avg_score": round(float(avg_score or 0), 2),
            "max_score": float(max_score or 0),
            "min_score": float(min_score or 0),
            "pass_rate": round(float(passed or 0) / count * 100, 2) if count else 0,
        },
    })


# ---------------------------------------------------------------- 工具
def _parse_dt(v: Any):
    if not v:
        return None
    if isinstance(v, str):
        from datetime import datetime

        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
            try:
                return datetime.strptime(v, fmt)
            except ValueError:
                continue
        return None
    return v


def _load(v: Optional[str]) -> Any:
    import json

    if not v:
        return None
    try:
        return json.loads(v)
    except json.JSONDecodeError:
        return v
