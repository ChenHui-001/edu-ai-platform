"""教学任务的下发名单与催办。

抽成 service 的原因：`api/v1/task.py` 已在文件体积门禁的预算边缘
（1260 行，预算 1260），催办所需的「应交名单 / 待交名单」计算逻辑
必须与既有的提交统计**共用一份实现**——两份算法漂移的后果是
「统计说交了 30 人，催办却催了 31 人」，用户完全无法理解。

因此本模块提供 `pending_students()`，`task.py` 的统计端点改为调用它。
"""
from typing import Any, Dict, Set

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Submission, Task, User

# 待交名单单次返回上限：一次催办几百人会把通知列表刷爆，
# 而且页面也用不完。超出部分用 total_pending 告知总数。
PENDING_PAGE_LIMIT = 50


def assigned_student_ids(db: Session, task: Task) -> Set[int]:
    """应交名单：按「指定学生 + 指定班级」展开。

    班级下发时取该班全部学生 —— 注意要排除非活跃账号，
    否则会给已停用的学生发催办。
    """
    assigned: Set[int] = set()
    class_ids: Set[int] = set()
    for a in task.assignments:
        if a.student_id:
            assigned.add(int(a.student_id))
        elif a.class_id:
            class_ids.add(int(a.class_id))
    if class_ids:
        rows = db.scalars(
            select(User.id).where(User.class_id.in_(class_ids),
                                   User.status == "active")
        ).all()
        assigned.update(int(r) for r in rows)
    return assigned


def submitted_student_ids(db: Session, task_id: int) -> Set[int]:
    """已交名单：只要有任意一次提交记录就算已交。"""
    rows = db.scalars(
        select(Submission.student_id).where(Submission.task_id == task_id)
    ).all()
    return {int(r) for r in rows if r}


def pending_students(db: Session, task: Task,
                     limit: int = PENDING_PAGE_LIMIT) -> Dict[str, Any]:
    """待交名单。

    返回：ids（待交学生 id，最多 limit 个）、names、total_pending（全量待交人数）。
    """
    assigned = assigned_student_ids(db, task)
    submitted = submitted_student_ids(db, task.id)
    pending = sorted(assigned - submitted)

    page = pending[:limit]
    names: Dict[int, str] = {}
    if page:
        rows = db.scalars(select(User).where(User.id.in_(page))).all()
        names = {int(u.id): (u.real_name or u.username or "") for u in rows}
    return {
        "ids": page,
        "names": names,
        "total_pending": len(pending),
        "total_assigned": len(assigned),
        "total_submitted": len(submitted & assigned) if assigned else len(submitted),
    }
