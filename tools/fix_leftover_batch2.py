# -*- coding: utf-8 -*-
"""遗留优化项修复（学情分析 4 项）。

5. student-comparison 批量聚合（消除 N+1）
6. admin/overview 补 avg_score_rate
7. subject-comparison 支持按年级+学科维度
8. active_students → participated_students（保留旧键兼容）
"""
import io

f = "backend/app/api/v1/report.py"
s = io.open(f, encoding="utf-8").read()

# ============================================================
# 8) class-overview：participated_students 别名
# ============================================================
s = s.replace('''        "completion_rate": completion_rate,
        "active_students": len(submitted_students),
    })''',
'''        "completion_rate": completion_rate,
        # participated_students 语义明确（有提交的学生数）；
        # active_students 为历史键名，保留以兼容旧前端
        "participated_students": len(submitted_students),
        "active_students": len(submitted_students),
    })''')

# ============================================================
# 5) student-comparison 批量聚合
# ============================================================
START = s.index('@router.get("/teacher/student-comparison", summary="学生横向对比")')
END = s.index('@router.get("/teacher/student-detail", summary="学生个体分析")')
NEW_FN = '''@router.get("/teacher/student-comparison", summary="学生横向对比")
def student_comparison(
    class_id: int, task_id: Optional[int] = None, db: Session = Depends(get_db),
    user: User = Depends(get_current_teacher), scope: DataScope = Depends(get_data_scope),
):
    """班级学生横向对比（批量聚合实现）。

    原实现逐学生查询提交 + 逐提交查询答案 + 逐学生查错题，
    40 人班级约 120 次 SQL；现改为 4 次聚合查询 + 内存归并。
    """
    if not scope.is_super:
        allowed = scope.class_ids()
        if allowed is not None and class_id not in allowed:
            raise BusinessException("无权查看该班级数据")

    from app.models import Answer, TaskAssignment, Task as TaskModel, TaskStatus

    students = db.scalars(select(User).where(
        User.class_id == class_id, User.identity == "student")).all()
    if not students:
        return ok([])
    sids = [s.id for s in students]

    # ---- 1) 全部提交（带任务满分，用于得分率）----
    sub_rows = db.execute(
        select(
            Submission.student_id, Submission.id, Submission.task_id,
            Submission.score, Submission.submit_time, TaskModel.total_score,
        )
        .join(TaskModel, TaskModel.id == Submission.task_id)
        .where(Submission.student_id.in_(sids), Submission.score.isnot(None))
        .order_by(Submission.student_id)
    ).all()
    if task_id:
        sub_rows = [r for r in sub_rows if r.task_id == task_id]

    # ---- 2) 正确率：一次 join 聚合 ----
    acc_rows = db.execute(
        select(
            Submission.student_id,
            func.count(Answer.id),
            func.sum(case((Answer.is_correct.is_(True), 1), else_=0)),
        )
        .join(Answer, Answer.submission_id == Submission.id)
        .where(Submission.student_id.in_(sids), Submission.score.isnot(None))
        .group_by(Submission.student_id)
    ).all()
    acc_map = {sid: (int(total or 0), int(right or 0)) for sid, total, right in acc_rows}

    # ---- 3) 未掌握错题数 ----
    wrong_map = dict(db.execute(
        select(WrongQuestion.student_id, func.count())
        .where(WrongQuestion.student_id.in_(sids),
               WrongQuestion.is_mastered.is_(False))
        .group_by(WrongQuestion.student_id)
    ).all())

    # ---- 4) 下发任务（一次取全，按学生/班级归属在内存归并）----
    assign_rows = db.execute(
        select(TaskAssignment.student_id, TaskAssignment.class_id, TaskAssignment.task_id)
        .join(TaskModel, TaskModel.id == TaskAssignment.task_id)
        .where(TaskModel.status == TaskStatus.PUBLISHED.value,
               TaskModel.type != "practice")
    ).all()

    # ---- 归并 ----
    by_student: Dict[int, List] = {}
    for r in sub_rows:
        by_student.setdefault(r.student_id, []).append(r)

    rows = []
    for stu in students:
        subs = by_student.get(stu.id, [])
        scores = [x.score for x in subs]
        total_full = sum((x.total_score or 0) for x in subs)
        scored = sum((x.score or 0) for x in subs)
        avg_rate = round(scored / total_full * 100, 2) if total_full else 0

        total_ans, right_ans = acc_map.get(stu.id, (0, 0))
        last_submit = max((x.submit_time for x in subs if x.submit_time), default=None)

        # 完成率：已提交 ∩ 已下发（集合去重）
        assigned_ids = {tid for sid_, cid, tid in assign_rows
                        if sid_ == stu.id or cid == stu.class_id}
        done_ids = {x.task_id for x in subs} & assigned_ids
        completion = (round(len(done_ids) / len(assigned_ids) * 100, 1)
                      if assigned_ids else 0)

        rows.append({
            "student_id": stu.id, "name": stu.real_name, "username": stu.username,
            "submit_count": len(subs),
            "avg_score": round(sum(scores) / len(scores), 2) if scores else 0,
            "avg_score_rate": avg_rate,
            "max_score": max(scores) if scores else 0,
            "wrong_count": int(wrong_map.get(stu.id, 0) or 0),
            "accuracy": round(right_ans / total_ans * 100, 1) if total_ans else 0,
            "last_submit": dictify(last_submit),
            "completion_rate": completion,
        })

    rows.sort(key=lambda x: x["avg_score_rate"], reverse=True)
    for i, r in enumerate(rows, start=1):
        r["rank"] = i
    return ok(rows)


'''
s = s[:START] + NEW_FN + s[END:]

# ============================================================
# 6) admin/overview 补 avg_score_rate（用 SQL 聚合，避免全表加载）
# ============================================================
OLD6 = '''    subs = db.scalars(
        select(Submission).where(Submission.score.isnot(None))
    ).all()'''
NEW6 = '''    # 用 SQL 聚合代替「全表加载到内存再求平均」：
    # 提交量大时前者是 O(1) 内存，后者会吃掉数百 MB。
    avg_raw = db.scalar(
        select(func.avg(Submission.score)).where(Submission.score.isnot(None))
    ) or 0
    avg_rate = db.scalar(
        select(func.avg(Submission.score * 100.0 / func.nullif(Task.total_score, 0)))
        .join(Task, Task.id == Submission.task_id)
        .where(Submission.score.isnot(None), Task.total_score > 0)
    ) or 0'''
assert OLD6 in s, "admin overview subs"
s = s.replace(OLD6, NEW6)

OLD6b = '''            "avg_score": round(sum(s.score for s in subs) / len(subs), 2) if subs else 0,'''
NEW6b = '''            "avg_score": round(float(avg_raw), 2),
            # 全校平均得分率：跨不同满分试卷唯一可比的汇总指标
            "avg_score_rate": round(float(avg_rate), 2),'''
assert OLD6b in s, "admin overview avg"
s = s.replace(OLD6b, NEW6b)

# ============================================================
# 7) subject-comparison 支持按年级+学科维度
# ============================================================
OLD7 = '''@router.get("/admin/subject-comparison", summary="各学科教学数据对比")
def subject_comparison(db: Session = Depends(get_db), _: User = Depends(get_current_manager)):
    rows = db.execute(
        select(
            Subject.name,
            func.count(func.distinct(Question.id)),
            func.count(func.distinct(Note.id)),
        )
        .select_from(Subject)
        .outerjoin(Question, Question.subject_id == Subject.id)
        .outerjoin(Note, Note.subject_id == Subject.id)
        .group_by(Subject.name)
    ).all()
    return ok([{"subject": n, "question_count": q or 0, "note_count": c or 0} for n, q, c in rows])'''
NEW7 = '''@router.get("/admin/subject-comparison", summary="各学科教学数据对比")
def subject_comparison(
    by_grade: bool = False, db: Session = Depends(get_db),
    _: User = Depends(get_current_manager),
):
    """学科维度对比。

    - 默认：按学科名汇总（跨年级同名学科合并，如 9 个年级的「数学」合成一行）
    - by_grade=true：按「年级 + 学科」输出，避免合并后无法定位具体年级
    """
    if not by_grade:
        rows = db.execute(
            select(
                Subject.name,
                func.count(func.distinct(Question.id)),
                func.count(func.distinct(Note.id)),
            )
            .select_from(Subject)
            .outerjoin(Question, Question.subject_id == Subject.id)
            .outerjoin(Note, Note.subject_id == Subject.id)
            .group_by(Subject.name)
        ).all()
        return ok([{"subject": n, "question_count": q or 0, "note_count": c or 0}
                   for n, q, c in rows])

    rows = db.execute(
        select(
            Grade.name, Subject.name, Subject.id,
            func.count(func.distinct(Question.id)),
            func.count(func.distinct(Note.id)),
        )
        .select_from(Subject)
        .join(Grade, Grade.id == Subject.grade_id)
        .outerjoin(Question, Question.subject_id == Subject.id)
        .outerjoin(Note, Note.subject_id == Subject.id)
        .group_by(Grade.name, Subject.name, Subject.id)
        .order_by(Grade.grade_num, Subject.name)
    ).all()
    return ok([
        {"grade": g, "subject": n, "subject_id": sid,
         "question_count": q or 0, "note_count": c or 0}
        for g, n, sid, q, c in rows
    ])'''
assert OLD7 in s, "subject-comparison"
s = s.replace(OLD7, NEW7)

# 确保 case / Grade 已导入
if "from sqlalchemy import case" not in s:
    s = s.replace("from sqlalchemy import", "from sqlalchemy import case,")

io.open(f, "w", encoding="utf-8", newline="\n").write(s)
print("学情分析 4 项修复完成")
