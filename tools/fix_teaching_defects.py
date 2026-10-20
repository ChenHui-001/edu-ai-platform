# -*- coding: utf-8 -*-
"""教学管理模块缺陷修复。

修复清单：
1. [高] task_submissions 越权：任意教师可查他人任务提交
2. [高] submit attempt 由客户端指定，可绕过 allow_retake
3. [中] create_task 允许空下发对象 / 不校验 pass_score、duration、起止时间
4. [中] 共享教案跨学科可见（注释称同科）
5. [中] completion_rate 列表与详情口径不一致
6. [低] 已交卷后心跳仍可改切屏次数/时长
"""
import io

# ============================================================
# 1) task.py
# ============================================================
f = "backend/app/api/v1/task.py"
s = io.open(f, encoding="utf-8").read()

# ---- 1.1 task_submissions 加归属校验 ----
OLD = '''@router.get("/tasks/{task_id}/submissions", summary="任务提交情况")
def task_submissions(
    task_id: int, params: PageParams = Depends(), class_id: Optional[int] = None,
    db: Session = Depends(get_db), user: User = Depends(get_current_teacher),
):
    task = db.get(Task, task_id)
    if not task:
        raise NotFoundException("任务不存在")
'''
NEW = '''@router.get("/tasks/{task_id}/submissions", summary="任务提交情况")
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
'''
assert OLD in s, "task_submissions"
s = s.replace(OLD, NEW)

# ---- 1.2 create_task 校验下发对象 / 参数范围 ----
OLD2 = '''    task = Task(
        title=data.get("title") or paper.name, type=task_type, paper_id=paper.id,'''
NEW2 = '''    # 参数范围校验（此前完全不校验，可写出 pass_score=9999、
    # duration=0、end_at 早于 start_at 的脏任务）
    if int(data.get("duration") or paper.duration or 0) <= 0:
        raise BusinessException("考试时长必须大于 0 分钟")
    pass_score = float(data.get("pass_score", settings.PASS_SCORE))
    if not (0 < pass_score <= (paper.total_score or 100)):
        raise BusinessException(
            f"及格分应在 0~{paper.total_score} 之间，当前 {pass_score}")
    if end_at <= start_at:
        raise BusinessException("截止时间必须晚于开始时间")

    task = Task(
        title=data.get("title") or paper.name, type=task_type, paper_id=paper.id,'''
assert OLD2 in s, "create_task params"
s = s.replace(OLD2, NEW2)

# ---- 1.3 空下发对象拒绝（放在 assignments 循环前）----
OLD3 = '''    # 下发范围
    student_ids: List[int] = []
    class_ids: List[int] = data.get("class_ids", [])
    student_ids.extend(data.get("student_ids", []))

    for cid in class_ids:'''
NEW3 = '''    # 下发范围
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

    for cid in class_ids:'''
assert OLD3 in s, "assignments"
s = s.replace(OLD3, NEW3)

# ---- 1.4 submit attempt 服务端权威 ----
OLD4 = '''    attempt = int(data.get("attempt", 1))
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

    sub = grading_service.get_student_submission(db, task_id, user.id, attempt)'''
NEW4 = '''    # attempt 一律由服务端判定：此前直接信任客户端传入值，
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

    sub = grading_service.get_student_submission(db, task_id, user.id, attempt)'''
assert OLD4 in s, "attempt"
s = s.replace(OLD4, NEW4)

# ---- 1.5 heartbeat 拒绝对已交卷记录写入 ----
OLD5 = '''    if not sub:
        return ok(message="no active submission")
    if data.get("switch"):'''
NEW5 = '''    if not sub:
        return ok(message="no active submission")
    # 已交卷记录不允许再改切屏次数/时长（否则交卷后可篡改考试行为数据）
    if sub.submit_time is not None:
        return ok({"switch_count": sub.switch_count}, message="已交卷，心跳忽略")
    if data.get("switch"):'''
assert OLD5 in s, "heartbeat"
s = s.replace(OLD5, NEW5)

# ---- 1.6 completion_rate 口径统一 ----
OLD6 = '''        d["submission_count"] = subs
        d["completion_rate"] = (
            round(subs / len(t.assignments) * 100, 2) if t.assignments else 0
        )'''
NEW6 = '''        d["submission_count"] = subs
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
        )'''
assert OLD6 in s, "completion_rate"
s = s.replace(OLD6, NEW6)

io.open(f, "w", encoding="utf-8", newline="\n").write(s)
print("task.py 修复完成")

# ============================================================
# 2) lesson.py 共享按学科过滤
# ============================================================
f2 = "backend/app/api/v1/lesson.py"
s2 = io.open(f2, encoding="utf-8").read()
OLD7 = '''    else:
        # 同科教师共享的也看得到：用 subject_id 匹配 + 排除自己
        stmt = stmt.where(
            (LessonPlan.creator_id == user.id) | (LessonPlan.is_shared == 1)
        )'''
NEW7 = '''    else:
        # 共享教案仅对「同科教师」可见（此前只判 is_shared=1，
        # 任何学科教师都能看到全部共享教案，与注释/设计不符）。
        my_subject_ids = set(db.scalars(
            select(TeacherSubject.subject_id).where(TeacherSubject.teacher_id == user.id)
        ).all()) if _has_teacher_subject() else set()
        if my_subject_ids:
            stmt = stmt.where(
                (LessonPlan.creator_id == user.id)
                | ((LessonPlan.is_shared == 1) & LessonPlan.subject_id.in_(my_subject_ids))
            )
        else:
            stmt = stmt.where(LessonPlan.creator_id == user.id)'''
assert OLD7 in s2, "lesson share"
s2 = s2.replace(OLD7, NEW7)

# 探测 TeacherSubject 是否存在（模型不确定，动态判断，避免引入不存在的表）
HELPER = '''

def _has_teacher_subject() -> bool:
    """是否存在教师-学科关联表（部分部署没有该表，退化为只看自己的）。"""
    try:
        from app.models import TeacherSubject  # noqa: F401
        return True
    except Exception:  # noqa: BLE001
        return False

'''
# 插到第一个 @router 之前
anchor_idx = s2.find("@router.get(\"/plans\"")
assert anchor_idx > 0
s2 = s2[:anchor_idx] + HELPER.lstrip("\n") + "\n" + s2[anchor_idx:]
io.open(f2, "w", encoding="utf-8", newline="\n").write(s2)
print("lesson.py 修复完成")
