# -*- coding: utf-8 -*-
"""学情分析统计口径修复。

核心问题：多处直接对「原始分」求平均/分档，而系统中试卷满分不同
（实测同班存在 30 分卷与 100 分卷），跨卷平均无意义。

修复原则：以「得分率（score / total_score × 100）」为主指标，
        原始分仅作为参考字段保留。
"""
import io

f = "backend/app/api/v1/report.py"
s = io.open(f, encoding="utf-8").read()

# ============================================================
# 1) class-overview：得分率口径 + 及格率用 is_passed + 补完成率
# ============================================================
OLD = '''    subs = db.scalars(stmt).all()
    scores = [s.score for s in subs]

    # 完成率
    tasks = db.scalars(
        select(Task).where(Task.grade_id == k.grade_id, Task.type != "practice")
    ).all()

    return ok({
        "class": {"id": k.id, "name": k.name, "grade_id": k.grade_id},
        "student_count": len(students),
        "submission_count": len(subs),
        "avg_score": round(sum(scores) / len(scores), 2) if scores else 0,
        "max_score": max(scores) if scores else 0,
        "min_score": min(scores) if scores else 0,
        "pass_rate": round(sum(1 for s in scores if s >= 60) / len(scores) * 100, 2) if scores else 0,
        "score_bands": _score_bands(scores),
        "active_students": len({s.student_id for s in subs}),
    })'''
NEW = '''    subs = db.scalars(stmt).all()
    scores = [s.score for s in subs]

    # ---- 得分率口径 ----
    # 同一班级可能包含不同满分的试卷（随堂练习 30 分、考试 100 分），
    # 直接平均原始分毫无意义（实测 8.33 分 = 30 分卷 10 分与 100 分卷 7 分混合）。
    # 主指标改为得分率，原始分仅作参考。
    rate_map = _submission_rates(db, subs)
    rates = list(rate_map.values())
    avg_rate = round(sum(rates) / len(rates), 2) if rates else 0

    # 及格率：以任务自身的 pass_score 判定（sub.is_passed 已在交卷/批改时按
    # pass_score 计算），不再硬编码 60 分 —— 5 分满分卷永远达不到 60。
    passed = sum(1 for s in subs if s.is_passed)
    pass_rate = round(passed / len(subs) * 100, 2) if subs else 0

    # 完成率：已交卷学生数 / 班级应交人数（此前算了 tasks 但未使用，字段缺失）
    submitted_students = {s.student_id for s in subs}
    completion_rate = (round(len(submitted_students) / len(students) * 100, 2)
                       if students else 0)

    return ok({
        "class": {"id": k.id, "name": k.name, "grade_id": k.grade_id},
        "student_count": len(students),
        "submission_count": len(subs),
        "avg_score": round(sum(scores) / len(scores), 2) if scores else 0,
        "avg_score_rate": avg_rate,
        "max_score": max(scores) if scores else 0,
        "min_score": min(scores) if scores else 0,
        "max_rate": round(max(rates), 2) if rates else 0,
        "min_rate": round(min(rates), 2) if rates else 0,
        "pass_rate": pass_rate,
        "score_bands": _rate_bands(rates),
        "completion_rate": completion_rate,
        "active_students": len(submitted_students),
    })'''
assert OLD in s, "class-overview"
s = s.replace(OLD, NEW)

# 新增辅助函数（得分率 + 按得分率分档），保留旧 _score_bands 供兼容
OLD_BANDS = '''def _score_bands(scores: List[float]) -> Dict[str, int]:'''
NEW_BANDS = '''def _submission_rates(db: Session, subs) -> Dict[int, float]:
    """把提交换算为得分率（0~100）。满分缺失或为 0 时按 0 处理。

    同一学生多次提交时取每份提交各自的得分率（用于分布），
    键为 submission.id 以保唯一。
    """
    if not subs:
        return {}
    task_ids = {s.task_id for s in subs}
    totals = {
        t.id: (t.total_score or 0)
        for t in db.scalars(select(Task).where(Task.id.in_(task_ids))).all()
    }
    out = {}
    for s in subs:
        total = totals.get(s.task_id) or 0
        out[s.id] = round((s.score or 0) / total * 100, 2) if total else 0.0
    return out


def _rate_bands(rates: List[float]) -> Dict[str, int]:
    """按得分率分档（与原始分满分无关，可跨试卷比较）。"""
    bands = {"90-100": 0, "80-89": 0, "70-79": 0, "60-69": 0, "<60": 0}
    for r in rates:
        if r >= 90: bands["90-100"] += 1
        elif r >= 80: bands["80-89"] += 1
        elif r >= 70: bands["70-79"] += 1
        elif r >= 60: bands["60-69"] += 1
        else: bands["<60"] += 1
    return bands


def _score_bands(scores: List[float]) -> Dict[str, int]:'''
assert OLD_BANDS in s, "bands"
s = s.replace(OLD_BANDS, NEW_BANDS, 1)

# ============================================================
# 2) student-comparison：得分率 + 完成率分母去重
# ============================================================
OLD2 = '''        subs = db.scalars(stmt).all()
        scores = [x.score for x in subs]'''
NEW2 = '''        subs = db.scalars(stmt).all()
        scores = [x.score for x in subs]
        # 得分率（跨卷可比）：个人所有提交的加权平均得分率
        total_full = sum((db.get(Task, x.task_id).total_score or 0)
                         for x in subs if db.get(Task, x.task_id))
        total_scored = sum(x.score or 0 for x in subs)
        avg_rate = round(total_scored / total_full * 100, 2) if total_full else 0'''
assert OLD2 in s, "comparison rates"
s = s.replace(OLD2, NEW2)

OLD3 = '''        # 真实完成率：已提交任务数 / 下发且已发布的任务数
        assigned = db.scalar(
            select(func.count()).select_from(TaskAssignment)
            .join(TaskModel, TaskModel.id == TaskAssignment.task_id)
            .where(
                TaskModel.status == TaskStatus.PUBLISHED.value,
                TaskModel.type != "practice",
                (TaskAssignment.student_id == s.id)
                | (TaskAssignment.class_id == s.class_id),
            )
        ) or 0'''
NEW3 = '''        # 真实完成率：已提交任务数 / 下发且已发布的任务数。
        # 必须 COUNT(DISTINCT task_id)：同一任务若既有班级下发又有个人下发
        # （跨班补发场景很常见），COUNT(*) 会重复计数导致完成率偏低。
        assigned = db.scalar(
            select(func.count(func.distinct(TaskAssignment.task_id)))
            .select_from(TaskAssignment)
            .join(TaskModel, TaskModel.id == TaskAssignment.task_id)
            .where(
                TaskModel.status == TaskStatus.PUBLISHED.value,
                TaskModel.type != "practice",
                (TaskAssignment.student_id == s.id)
                | (TaskAssignment.class_id == s.class_id),
            )
        ) or 0'''
assert OLD3 in s, "comparison completion"
s = s.replace(OLD3, NEW3)

s = s.replace('''            "avg_score": round(sum(scores) / len(scores), 2) if scores else 0,
            "max_score": max(scores) if scores else 0,
            "wrong_count": wrong,''',
'''            "avg_score": round(sum(scores) / len(scores), 2) if scores else 0,
            "avg_score_rate": avg_rate,
            "max_score": max(scores) if scores else 0,
            "wrong_count": wrong,''')

# 排序与排名改按得分率（跨卷公平）
s = s.replace('''    rows.sort(key=lambda x: x["avg_score"], reverse=True)''',
'''    # 按得分率排序：原始分排名会让「100 分卷考 60」排在「30 分卷考 25」之后
    rows.sort(key=lambda x: x["avg_score_rate"], reverse=True)''')

# ============================================================
# 3) student-detail：趋势补 total_score / score_rate
# ============================================================
OLD4 = '''        "score_trend": [
            {
                "name": (db.get(Task, s.task_id).title if db.get(Task, s.task_id) else ""),
                "score": s.score, "rank": s.class_rank,
                "date": dictify(s.submit_time),
            }
            for s in subs
        ],'''
NEW4 = '''        # 趋势必须带满分与得分率：否则 30 分卷与 100 分卷会画在同一条
        # 折线上，视觉上「成绩暴跌」而实际是试卷分值不同。
        "score_trend": [
            {
                "name": (db.get(Task, s.task_id).title if db.get(Task, s.task_id) else ""),
                "score": s.score,
                "total_score": (db.get(Task, s.task_id).total_score
                                if db.get(Task, s.task_id) else 0),
                "score_rate": (round((s.score or 0) /
                                     (db.get(Task, s.task_id).total_score or 1) * 100, 2)
                               if db.get(Task, s.task_id)
                               and (db.get(Task, s.task_id).total_score or 0) else 0),
                "rank": s.class_rank,
                "date": dictify(s.submit_time),
            }
            for s in subs
        ],'''
assert OLD4 in s, "student trend"
s = s.replace(OLD4, NEW4)

# 汇总补得分率
s = s.replace('''        "summary": {
            "submit_count": len(subs),
            "avg_score": round(sum(s.score for s in subs) / len(subs), 2) if subs else 0,
        },''',
'''        "summary": {
            "submit_count": len(subs),
            "avg_score": round(sum(s.score for s in subs) / len(subs), 2) if subs else 0,
            # 平均得分率：跨不同满分试卷唯一可比的汇总口径
            "avg_score_rate": round(
                sum(s.score or 0 for s in subs) /
                max(sum((db.get(Task, x.task_id).total_score or 0)
                        for x in subs if db.get(Task, x.task_id)), 1) * 100, 2
            ) if subs else 0,
        },''')

io.open(f, "w", encoding="utf-8", newline="\n").write(s)
print("report.py：class-overview / student-comparison / student-detail 修复完成")
