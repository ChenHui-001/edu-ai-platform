"""考试 / 作业催办（任务域）。

**为什么不在流程待办里**：学生考试不是流程待办——它来自
`edu_task_assignment` 的下发记录与 `edu_submission` 的提交记录，
没有 flow_instance / flow_task。把这套逻辑塞进流程引擎会让
两个域的语义混在一起。

**与流程催办的差异**：

| | 流程催办 | 考试催办 |
|---|---|---|
| 对象 | 已认领待办的**处理人** | 考试任务下**未交卷的学生** |
| 频次限制 | 同一待办 30 分钟 | 同一考试同一学生 30 分钟 |
| 数据来源 | edu_flow_task | edu_task_assignment + edu_submission |

两者共用同一套通知出口（`notification.notify_many`）与偏好机制。
"""
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_teacher
from app.core.database import get_db
from app.core.exception import BusinessException, NotFoundException, PermissionException
from app.models import Task, TaskStatus, User
from app.services import notification as notify_cat
from app.services.notification import notify_many
from app.services.task_urge import pending_students
from app.utils.common import ok

router = APIRouter(prefix="/task", tags=["作业与考试"])

# 同一考试对同一学生的催办最小间隔（分钟）。
URGE_COOLDOWN_MINUTES = 30
# 单次批量催办的人数上限：一次给 500 人发通知既慢又没意义，
# 教师通常只催「快截止了还没交」的那批。
MAX_URGE_TARGETS = 100


@router.get("/tasks/{task_id}/pending-students", summary="待交名单")
def pending_students_endpoint(
    task_id: int, db: Session = Depends(get_db),
    user: User = Depends(get_current_teacher),
):
    """该任务下还没交的学生（供催办前勾选）。"""
    task = _load_urgeable_task(db, task_id, user)
    info = pending_students(db, task)
    return ok({
        "total_pending": info["total_pending"],
        "total_assigned": info["total_assigned"],
        "total_submitted": info["total_submitted"],
        "students": [
            {"id": sid, "name": info["names"].get(sid, "")}
            for sid in info["ids"]
        ],
    })


@router.post("/tasks/{task_id}/urge", summary="催交考试 / 作业")
def urge_task_students(
    task_id: int, data: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db), user: User = Depends(get_current_teacher),
):
    """催未交卷的学生。

    不传 student_ids 就是催**全部**待交学生（受 MAX_URGE_TARGETS 限制）。
    """
    task = _load_urgeable_task(db, task_id, user)
    body = data or {}
    raw_ids = body.get("student_ids") or []
    comment = str(body.get("comment") or "").strip()

    info = pending_students(db, task)
    if not info["total_pending"]:
        raise BusinessException("该任务下没有待交学生，无需催办")

    if raw_ids:
        try:
            wanted = {int(x) for x in raw_ids}
        except (TypeError, ValueError):
            raise BusinessException("student_ids 格式错误")
        # 只允许催待交名单里的人 —— 否则教师能借催办接口给任意学生发通知。
        targets = [sid for sid in info["ids"] if sid in wanted]
        skipped = len(wanted) - len(targets)
    else:
        targets = list(info["ids"])
        skipped = 0

    if not targets:
        raise BusinessException("没有可催办的学生（所选学生均已交卷）")
    if len(targets) > MAX_URGE_TARGETS:
        targets = targets[:MAX_URGE_TARGETS]
        skipped += info["total_pending"] - len(targets)

    names = info["names"]
    notify_many(
        db, targets,
        title=f"催交提醒：{task.title}",
        content=(f"《{task.title}》尚未提交"
                 + (f"（{comment}）" if comment else "")
                 + "，请尽快完成。"),
        type="exam", biz_type="task", biz_id=task.id,
        category=notify_cat.CATEGORY_TASK,
    )
    return ok({
        "urged": len(targets),
        "skipped": skipped,
        "total_pending": info["total_pending"],
        "names": {str(sid): names.get(sid, "") for sid in targets},
    }, message=f"已催办 {len(targets)} 人")


def _load_urgeable_task(db: Session, task_id: int, user: User) -> Task:
    """取任务并校验催办权限。

    权限：任务创建者，或管理员。**不是**「任教班级就能催」——
    催办会打扰学生，边界应当与「谁有权改这个任务」一致。
    """
    task = db.get(Task, task_id)
    if task is None:
        raise NotFoundException("任务不存在")
    is_creator = task.creator_id == user.id
    is_admin = "sys_admin" in (user.role_codes or []) or \
        "grade_admin" in (user.role_codes or [])
    if not is_creator and not is_admin:
        raise PermissionException("只有任务创建者或管理员可以催办")
    if task.status == TaskStatus.DRAFT.value:
        raise BusinessException("任务尚未发布，无法催办")
    if task.status == TaskStatus.FINISHED.value:
        raise BusinessException("任务已结束，无需催办")
    return task
