"""作业 / 考试发布与学生端答题接口。"""
from datetime import timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.api.deps import (
    DataScope, get_current_teacher, get_current_user, get_data_scope,
)
from app.core.config import settings
from app.core.database import get_db
from app.core.exception import BusinessException, NotFoundException, PermissionException
from app.models import (
    Answer, Class, Notification, Paper, Submission, Task, TaskAssignment, TaskStatus,
    TaskType, User,
)
from app.services import grading_service
from app.utils.common import PageParams, dictify, ok, utcnow

router = APIRouter(prefix="/task", tags=["作业与考试"])

TYPE_LABEL = {"homework": "作业", "exam": "考试", "practice": "随机练习"}


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
    keyword: Optional[str] = None, db: Session = Depends(get_db),
    user: User = Depends(get_current_teacher), scope: DataScope = Depends(get_data_scope),
):
    stmt = select(Task)
    if not scope.is_super:
        stmt = stmt.where(Task.creator_id == user.id)
    if task_type:
        stmt = stmt.where(Task.type == task_type)
    if status:
        stmt = stmt.where(Task.status == status)
    if subject_id:
        stmt = stmt.where(Task.subject_id == subject_id)
    if keyword:
        stmt = stmt.where(Task.title.like(f"%{keyword}%"))

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(
        stmt.order_by(Task.created_at.desc()).offset(params.offset).limit(params.page_size)
    ).all()
    items = []
    for t in rows:
        d = dictify(t)
        d["type_label"] = TYPE_LABEL.get(t.type, t.type)
        d["assignment_count"] = len(t.assignments)
        subs = db.scalar(
            select(func.count()).select_from(Submission).where(Submission.task_id == t.id)
        ) or 0
        d["submission_count"] = subs
        # 完成率分母必须展开班级成员（assignments 里一个班只算 1 条，
        # 会导致与详情页口径不一致、甚至出现 200% 这种值）
        assigned_ids = set()
        for a in t.assignments:
            if a.student_id:
                assigned_ids.add(a.student_id)
            elif a.class_id:
                assigned_ids.update(db.scalars(
                    select(User.id).where(User.class_id == a.class_id)).all())
        d["assigned_count"] = len(assigned_ids)
        d["completion_rate"] = (
            round(min(subs, len(assigned_ids)) / len(assigned_ids) * 100, 2)
            if assigned_ids else 0
        )
        items.append(d)
    return ok({"items": items, "total": total, "page": params.page})


@router.post("/tasks", summary="发布作业 / 考试")
def create_task(
    data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    user: User = Depends(get_current_teacher),
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
    start_at = _parse_dt(data.get("start_at")) or utcnow()
    end_at = _parse_dt(data.get("end_at")) or (start_at + timedelta(days=7))
    publish_at = _parse_dt(data.get("publish_at"))
    # 定时发布：publish_at 在未来 → 草稿状态落库、暂不通知学生，
    # 由内置任务 publish_scheduled_tasks 到期激活并补发通知。
    scheduled = bool(publish_at and publish_at > utcnow())

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
    user: User = Depends(get_current_teacher),
):
    """任务详情：教师仅看自己创建的；管理员看全量。
    之前缺这个接口，前端编辑回查只能 405。
    """
    task = db.get(Task, task_id)
    if not task:
        raise NotFoundException("任务不存在")
    if task.creator_id != user.id and "sys_admin" not in user.role_codes:
        raise PermissionException("无权限查看该任务")
    return ok(dictify(task))


@router.put("/tasks/{task_id}", summary="编辑任务")
def update_task(
    task_id: int, data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    user: User = Depends(get_current_teacher),
):
    task = db.get(Task, task_id)
    if not task:
        raise NotFoundException("任务不存在")
    if task.creator_id != user.id and "sys_admin" not in user.role_codes:
        raise PermissionException("无权限编辑该任务")
    for f in ("title", "description", "duration", "allow_retake", "show_answer",
              "anti_cheat", "pass_score"):
        if f in data:
            setattr(task, f, data[f])
    for f in ("start_at", "end_at"):
        if data.get(f):
            setattr(task, f, _parse_dt(data[f]))
    db.commit()
    return ok(message="任务已更新")


@router.delete("/tasks/{task_id}", summary="删除任务")
def delete_task(
    task_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_teacher),
):
    task = db.get(Task, task_id)
    if not task:
        raise NotFoundException("任务不存在")
    if task.creator_id != user.id and "sys_admin" not in user.role_codes:
        raise PermissionException("无权限删除该任务")
    db.delete(task)
    db.commit()
    return ok(message="任务已删除")


@router.get("/tasks/{task_id}/submissions", summary="任务提交情况")
def task_submissions(
    task_id: int, params: PageParams = Depends(), class_id: Optional[int] = None,
    db: Session = Depends(get_db), user: User = Depends(get_current_teacher),
):
    task = db.get(Task, task_id)
    if not task:
        raise NotFoundException("任务不存在")
    # 数据范围：只有任务创建者（或管理员）能看提交名单、分数与切屏记录。
    # 此前缺此校验，任意教师遍历 task_id 即可获取他人任务的学生成绩。
    if task.creator_id != user.id and "sys_admin" not in user.role_codes:
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

    items = []
    for s in rows:
        stu = db.get(User, s.student_id)
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

    # 应交名单与完成率
    assigned_ids: set = set()
    for a in task.assignments:
        if a.student_id:
            assigned_ids.add(a.student_id)
        elif a.class_id:
            assigned_ids.update(
                db.scalars(select(User.id).where(User.class_id == a.class_id)).all()
            )
    submitted_ids = {s.student_id for s in rows} | set(
        db.scalars(select(Submission.student_id).where(Submission.task_id == task_id)).all()
    )
    pending = list(assigned_ids - submitted_ids)

    return ok({
        "items": items, "total": total, "assigned": len(assigned_ids),
        "submitted": len(submitted_ids & assigned_ids) if assigned_ids else len(submitted_ids),
        "completion_rate": round(len(submitted_ids & assigned_ids) / len(assigned_ids) * 100, 2)
        if assigned_ids else 0,
        "pending_students": [
            {"id": pid, "name": (db.get(User, pid).real_name if db.get(User, pid) else "")}
            for pid in pending[:50]
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
        (Task.publish_at.is_(None)) | (Task.publish_at <= utcnow()),
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
            delta = (t.end_at - utcnow()).total_seconds()
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
    now = utcnow()
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
    task_finished = bool(task.end_at and task.end_at < utcnow())
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
        task.publish_at and task.publish_at > utcnow()
    ):
        raise BusinessException("任务尚未发布，无法提交")
    if task.end_at and task.end_at < utcnow():
        raise BusinessException("任务已截止，无法提交")
    if task.start_at and task.start_at > utcnow():
        raise BusinessException("任务尚未开始")

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
            raise BusinessException(f"最多允许作答 {max_attempt} 次，已用完次数")
        attempt = last.attempt + 1
    else:
        # 未交卷的草稿沿用其 attempt，保证覆盖同一份而不是新建
        attempt = last.attempt if last else 1

    sub = grading_service.get_student_submission(db, task_id, user.id, attempt)
    answers = data.get("answers", [])
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
    if data.get("switch"):
        sub.switch_count += 1
    sub.duration_seconds = int(data.get("duration_seconds") or sub.duration_seconds or 0)
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

    scored = list(rows)
    return ok({
        "items": items, "total": total, "page": params.page,
        "summary": {
            "count": len(scored),
            "avg_score": round(sum(s.score for s in scored) / len(scored), 2) if scored else 0,
            "max_score": max((s.score for s in scored), default=0),
            "min_score": min((s.score for s in scored), default=0),
            "pass_rate": round(sum(1 for s in scored if s.is_passed) / len(scored) * 100, 2)
            if scored else 0,
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
