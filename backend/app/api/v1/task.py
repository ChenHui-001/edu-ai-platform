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
        d["completion_rate"] = (
            round(subs / len(t.assignments) * 100, 2) if t.assignments else 0
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

    task_type = data.get("type", TaskType.HOMEWORK.value)
    start_at = _parse_dt(data.get("start_at")) or utcnow()
    end_at = _parse_dt(data.get("end_at")) or (start_at + timedelta(days=7))
    publish_at = _parse_dt(data.get("publish_at"))
    # 定时发布：publish_at 在未来 → 草稿状态落库、暂不通知学生，
    # 由内置任务 publish_scheduled_tasks 到期激活并补发通知。
    scheduled = bool(publish_at and publish_at > utcnow())

    task = Task(
        title=data.get("title") or paper.name, type=task_type, paper_id=paper.id,
        subject_id=paper.subject_id, grade_id=paper.grade_id, creator_id=user.id,
        status=TaskStatus.DRAFT.value if scheduled else TaskStatus.PUBLISHED.value,
        start_at=start_at, end_at=end_at,
        duration=int(data.get("duration") or paper.duration),
        publish_at=publish_at,
        allow_retake=int(data.get("allow_retake", 1)),
        show_answer=bool(data.get("show_answer", True)),
        anti_cheat=bool(data.get("anti_cheat", False)),
        total_score=paper.total_score,
        pass_score=float(data.get("pass_score", settings.PASS_SCORE)),
        description=data.get("description"),
    )
    db.add(task)
    db.flush()

    # 下发范围
    student_ids: List[int] = []
    class_ids: List[int] = data.get("class_ids", [])
    student_ids.extend(data.get("student_ids", []))

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
    if task.status == TaskStatus.DRAFT.value or (
        task.publish_at and task.publish_at > utcnow()
    ):
        raise BusinessException("任务尚未发布，无法提交")
    if task.end_at and task.end_at < utcnow():
        raise BusinessException("任务已截止，无法提交")
    if task.start_at and task.start_at > utcnow():
        raise BusinessException("任务尚未开始")

    attempt = int(data.get("attempt", 1))
    exists = db.scalar(
        select(Submission).where(
            Submission.task_id == task_id, Submission.student_id == user.id,
            Submission.attempt == attempt,
        )
    )
    if exists and exists.submit_time:
        if attempt >= task.allow_retake:
            raise BusinessException(f"最多允许作答 {task.allow_retake} 次")
        attempt += 1

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
    if data.get("switch"):
        sub.switch_count += 1
    sub.duration_seconds = int(data.get("duration_seconds") or sub.duration_seconds or 0)
    db.commit()
    return ok({"switch_count": sub.switch_count})


@router.get("/submissions/{submission_id}", summary="作答详情（含解析）")
def submission_detail(
    submission_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    sub = db.get(Submission, submission_id)
    if not sub:
        raise NotFoundException("作答记录不存在")
    if sub.student_id != user.id and "sys_admin" not in user.role_codes and "teacher" not in user.role_codes:
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
