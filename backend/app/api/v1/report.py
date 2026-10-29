"""数据报表接口：学生端、教师端、管理员端。"""
import io
from datetime import timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from sqlalchemy import case, desc, func, or_, select
from sqlalchemy.orm import Session

from app.api.deps import (
    DataScope, get_current_admin, get_current_manager, get_current_teacher,
    get_current_user, get_data_scope,
)
from app.core.database import get_db
from app.core.exception import BusinessException, NotFoundException, PermissionException
from app.models import (
    AgentCallLog, Answer, Class, ErrorLog, Grade, KnowledgeMastery, KnowledgePoint,
    Note, Paper, Question, StudyRecord, Submission, Subject, Task, User, WrongQuestion,
)
from app.utils.common import dictify, now_local, ok

router = APIRouter(prefix="/report", tags=["数据报表"])


# ================================================================ 学生端
@router.get("/student/overview", summary="个人学习总览")
def student_overview(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    today = now_local().strftime("%Y-%m-%d")
    since7 = (now_local() - timedelta(days=7)).strftime("%Y-%m-%d")
    since30 = (now_local() - timedelta(days=30)).strftime("%Y-%m-%d")

    def _study(days_field: str = "7"):
        return db.scalar(
            select(func.coalesce(func.sum(StudyRecord.study_seconds), 0)).where(
                StudyRecord.student_id == user.id, StudyRecord.study_date >= days_field
            )
        ) or 0

    total_q = db.scalar(
        select(func.coalesce(func.sum(StudyRecord.question_count), 0)).where(
            StudyRecord.student_id == user.id
        )
    ) or 0
    total_right = db.scalar(
        select(func.coalesce(func.sum(StudyRecord.correct_count), 0)).where(
            StudyRecord.student_id == user.id
        )
    ) or 0

    subs = db.scalars(
        select(Submission).where(
            Submission.student_id == user.id, Submission.score.isnot(None)
        )
    ).all()

    return ok({
        "student": {"id": user.id, "name": user.real_name, "class_id": user.class_id},
        "study_minutes_today": _study(today) // 60,
        "study_minutes_7d": _study(since7) // 60,
        "study_minutes_30d": _study(since30) // 60,
        "question_total": total_q,
        "accuracy": round(total_right / total_q * 100, 2) if total_q else 0,
        "wrong_unmastered": db.scalar(
            select(func.count()).select_from(WrongQuestion).where(
                WrongQuestion.student_id == user.id, WrongQuestion.is_mastered.is_(False)
            )
        ) or 0,
        "wrong_mastered": db.scalar(
            select(func.count()).select_from(WrongQuestion).where(
                WrongQuestion.student_id == user.id, WrongQuestion.is_mastered.is_(True)
            )
        ) or 0,
        "note_count": db.scalar(
            select(func.count()).select_from(Note).where(Note.student_id == user.id)
        ) or 0,
        "exam_count": len(subs),
        "avg_score": round(sum(s.score for s in subs) / len(subs), 2) if subs else 0,
        "pass_count": sum(1 for s in subs if s.is_passed),
    })


@router.get("/student/score-trend", summary="成绩趋势")
def score_trend(
    subject_id: Optional[int] = None, limit: int = Query(20, le=100),
    db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    """成绩趋势。

    此前没有声明 `subject_id`，而个人报表页把它当作筛选条件传了过来 ——
    FastAPI 对未声明的 query 参数不报错，直接丢弃，于是「切学科后趋势图不变」。
    过滤条件落在 Task 上（学科归属在任务/试卷，不在答卷）。
    """
    stmt = select(Submission).where(
        Submission.student_id == user.id, Submission.score.isnot(None)
    )
    if subject_id:
        stmt = stmt.where(Submission.task_id.in_(
            select(Task.id).where(Task.subject_id == subject_id)
        ))
    subs = db.scalars(stmt.order_by(Submission.id).limit(limit)).all()
    # 一次预取本页提交涉及的任务，避免循环内逐条 db.get(Task) 的 N+1
    task_ids = {s.task_id for s in subs if s.task_id}
    task_map: Dict[int, Task] = {
        t.id: t for t in db.scalars(
            select(Task).where(Task.id.in_(task_ids))
        ).all()
    } if task_ids else {}
    items = []
    for s in subs:
        task = task_map.get(s.task_id)
        items.append({
            "id": s.id, "name": task.title if task else "练习",
            "type": task.type if task else "practice",
            "score": s.score, "total_score": task.total_score if task else None,
            "rate": round(s.score / task.total_score * 100, 2) if task and task.total_score else 0,
            "class_rank": s.class_rank, "date": dictify(s.submit_time),
        })
    return ok(items)


@router.get("/student/knowledge-radar", summary="知识点掌握雷达图")
def knowledge_radar(
    subject_id: Optional[int] = None, db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(KnowledgeMastery).where(KnowledgeMastery.student_id == user.id)
    if subject_id:
        stmt = stmt.where(KnowledgeMastery.subject_id == subject_id)
    rows = db.scalars(stmt).all()

    # 一次预取知识点，避免循环内逐条 db.get(KnowledgePoint) 的 N+1
    kp_ids = {m.knowledge_point_id for m in rows if m.knowledge_point_id}
    kp_map: Dict[int, KnowledgePoint] = {
        kp.id: kp for kp in db.scalars(
            select(KnowledgePoint).where(KnowledgePoint.id.in_(kp_ids))
        ).all()
    } if kp_ids else {}
    items = []
    for m in rows:
        kp = kp_map.get(m.knowledge_point_id)
        if kp:
            items.append({"id": kp.id, "name": kp.name, "mastery": round(m.mastery, 2)})
    items.sort(key=lambda x: x["mastery"])
    return ok(items[:20])


@router.get("/student/wrong-analysis", summary="错题分析")
def wrong_analysis(
    subject_id: Optional[int] = None, db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    base = select(WrongQuestion).where(WrongQuestion.student_id == user.id)
    if subject_id:
        base = base.where(WrongQuestion.subject_id == subject_id)

    # 以下三块统计必须复用 base 的过滤条件。
    # 原实现只对 total 用了 base，choropleth 三块仍按 student_id 全量统计 ——
    # 页面切学科后「错题总数」变成了 0，饼图/排行/趋势却纹丝不动，数据自相矛盾。
    scoped = base.where().subquery()
    reason_dist = db.execute(
        select(WrongQuestion.error_reason, func.count()).where(
            WrongQuestion.id.in_(select(scoped.c.id))
        ).group_by(WrongQuestion.error_reason)
    ).all()

    kp_rank = db.execute(
        select(KnowledgePoint.name, func.count())
        .join(WrongQuestion, WrongQuestion.knowledge_point_id == KnowledgePoint.id)
        .where(WrongQuestion.id.in_(select(scoped.c.id)))
        .group_by(KnowledgePoint.name)
        .order_by(desc(func.count()))
        .limit(10)
    ).all()

    since = (now_local() - timedelta(days=30)).strftime("%Y-%m-%d")
    trend = db.execute(
        select(WrongQuestion.last_wrong_at, func.count()).where(
            WrongQuestion.id.in_(select(scoped.c.id)),
            WrongQuestion.last_wrong_at >= since,
        ).group_by(func.date(WrongQuestion.last_wrong_at))
        .order_by(func.date(WrongQuestion.last_wrong_at))
    ).all()

    return ok({
        "reason_distribution": [
            {"reason": r or "未标注", "count": c} for r, c in reason_dist
        ],
        "knowledge_rank": [{"name": n, "count": c} for n, c in kp_rank],
        "trend": [{"date": str(d), "count": c} for d, c in trend],
        "total": db.scalar(select(func.count()).select_from(base.subquery())) or 0,
    })


@router.get("/student/learning-suggestion", summary="个性化学习建议")
def learning_suggestion(
    db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    from app.agents.study_agent import StudyPlannerAgent

    res = StudyPlannerAgent().run(db, user_id=user.id, student_id=user.id, days=7)
    data = res.get("data") or {}
    return ok({
        "summary": data.get("summary"),
        "weak_points": data.get("weak_points", []),
        "advice": data.get("advice", []),
        "daily_plan": data.get("daily_plan", [])[:3],
    })


# ================================================================ 教师端
@router.get("/teacher/class-overview", summary="班级学情概览")
def class_overview(
    class_id: int, task_id: Optional[int] = None, db: Session = Depends(get_db),
    _: User = Depends(get_current_teacher), scope: DataScope = Depends(get_data_scope),
):
    if not scope.is_super:
        allowed = scope.class_ids()
        if allowed is not None and class_id not in allowed:
            raise BusinessException("无权查看该班级数据")

    k = db.get(Class, class_id)
    if not k:
        raise NotFoundException("班级不存在")
    students = db.scalars(select(User).where(User.class_id == class_id)).all()

    stmt = select(Submission).where(
        Submission.student_id.in_([s.id for s in students] or [0]),
        Submission.score.isnot(None),
    )
    if task_id:
        stmt = stmt.where(Submission.task_id == task_id)
    subs = db.scalars(stmt).all()
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
        # participated_students 语义明确（有提交的学生数）；
        # active_students 为历史键名，保留以兼容旧前端
        "participated_students": len(submitted_students),
        "active_students": len(submitted_students),
    })


def _submission_rates(db: Session, subs) -> Dict[int, float]:
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


@router.get("/teacher/student-comparison", summary="学生横向对比")
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

    # ---- 4) 下发任务（只取本班相关，避免随全校数据线性增长）----
    # 旧实现无差条件地拉全站已发布非练习下发记录，再在内存按学生/班级归并；
    # 学校规模大时这里会加载数十万行。补齐「本班学生 或 本班班级」过滤后，
    # 结果与内存归并完全等价（完成率只关心这些学生的下发）。
    assign_rows = db.execute(
        select(TaskAssignment.student_id, TaskAssignment.class_id, TaskAssignment.task_id)
        .join(TaskModel, TaskModel.id == TaskAssignment.task_id)
        .where(TaskModel.status == TaskStatus.PUBLISHED.value,
               TaskModel.type != "practice",
               or_(TaskAssignment.student_id.in_(sids),
                   TaskAssignment.class_id == class_id))
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


@router.get("/teacher/student-detail", summary="学生个体分析")
def student_detail(
    student_id: int, db: Session = Depends(get_db),
    user: User = Depends(get_current_teacher), scope: DataScope = Depends(get_data_scope),
):
    stu = db.get(User, student_id)
    if not stu:
        raise NotFoundException("学生不存在")
    # 数据范围校验：只能看任教班级（或所辖年级）的学生，防止遍历 student_id
    if not scope.is_super:
        allowed = scope.class_ids()
        if allowed is not None and stu.class_id not in allowed:
            raise BusinessException("无权查看该学生数据")

    subs = db.scalars(
        select(Submission).where(
            Submission.student_id == student_id, Submission.score.isnot(None)
        ).order_by(Submission.id)
    ).all()

    masteries = db.scalars(
        select(KnowledgeMastery).where(KnowledgeMastery.student_id == student_id)
    ).all()
    # 一次预取知识点，避免循环内 db.get(KnowledgePoint) 的 N+1
    kp_ids = {m.knowledge_point_id for m in masteries if m.knowledge_point_id}
    kp_map: Dict[int, KnowledgePoint] = {
        kp.id: kp for kp in db.scalars(
            select(KnowledgePoint).where(KnowledgePoint.id.in_(kp_ids))
        ).all()
    } if kp_ids else {}
    kp_items = []
    for m in masteries:
        kp = kp_map.get(m.knowledge_point_id)
        if kp:
            kp_items.append({"name": kp.name, "mastery": round(m.mastery, 2)})
    kp_items.sort(key=lambda x: x["mastery"])

    # 一次预取本学生全部提交涉及的任务：下面 score_trend 与 summary 都要用满分，
    # 原实现每条提交（乃至每个字段）都 db.get(Task) 一次，构成 N+1。
    task_ids = {s.task_id for s in subs if s.task_id}
    task_map: Dict[int, Task] = {
        t.id: t for t in db.scalars(
            select(Task).where(Task.id.in_(task_ids))
        ).all()
    } if task_ids else {}
    score_trend = []
    for s in subs:
        task = task_map.get(s.task_id)
        total_score = (task.total_score or 0) if task else 0
        score_trend.append({
            "name": task.title if task else "",
            "score": s.score,
            "total_score": task.total_score if task else 0,
            "score_rate": round((s.score or 0) / total_score * 100, 2) if total_score else 0,
            "rank": s.class_rank,
            "date": dictify(s.submit_time),
        })
    # 平均得分率分母：只累加「任务存在」的满分（与旧实现口径一致）
    rated_total = sum(
        (task_map.get(x.task_id).total_score or 0)
        for x in subs if task_map.get(x.task_id)
    )

    wrong = db.scalars(
        select(WrongQuestion).where(
            WrongQuestion.student_id == student_id, WrongQuestion.is_mastered.is_(False)
        ).limit(20)
    ).all()

    return ok({
        "student": {
            "id": stu.id, "name": stu.real_name, "username": stu.username,
            "class_id": stu.class_id, "grade_id": stu.grade_id,
        },
        # 趋势必须带满分与得分率：否则 30 分卷与 100 分卷会画在同一条
        # 折线上，视觉上「成绩暴跌」而实际是试卷分值不同。
        "score_trend": score_trend,
        "knowledge_mastery": kp_items,
        "weak_points": kp_items[:5],
        "wrong_questions": [
            {"id": w.id, "question_id": w.question_id, "error_count": w.error_count,
             "error_reason": w.error_reason}
            for w in wrong
        ],
        "summary": {
            "submit_count": len(subs),
            "avg_score": round(sum(s.score for s in subs) / len(subs), 2) if subs else 0,
            # 平均得分率：跨不同满分试卷唯一可比的汇总口径
            "avg_score_rate": round(
                sum(s.score or 0 for s in subs) / max(rated_total, 1) * 100, 2
            ) if subs else 0,
        },
    })


@router.get("/teacher/knowledge-effect", summary="知识点教学效果评估")
def knowledge_effect(
    subject_id: Optional[int] = None, class_id: Optional[int] = None,
    task_id: Optional[int] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_teacher), scope: DataScope = Depends(get_data_scope),
):
    """知识点教学效果评估。

    支持三类过滤（可组合）：
    - task_id：只统计该任务下的作答（前端「教学报表-选任务」主路径）
    - class_id：只统计该班级学生的作答
    - subject_id：按学科过滤题目
    此前前端传 class_id/task_id 但后端只声明 subject_id，参数被 FastAPI
    静默丢弃，导致「选择任务」后展示的仍是全库聚合数据（假过滤）。

    数据范围：本接口此前**完全没有 DataScope** —— 不传参即聚合全校作答，
    传任意 class_id 就读他班，传任意 task_id 就读他班学情结论（水平越权）。
    现在按同文件 class_overview / student_comparison / student_detail 的
    同一套口径收敛。注意 class_id / task_id 是**可空**的（前两处是必填），
    所以不能照抄 `class_id not in allowed`，必须逐个判「传了才校验」。
    """
    if not scope.is_super:
        allowed = scope.class_ids()
        # ① 显式传了班级：必须是本人任教/管辖的班级
        if class_id is not None and allowed is not None and class_id not in allowed:
            raise BusinessException("无权查看该班级数据")
        # ② 显式传了任务：任务学情结论属他班数据，只有发布者（或超管）可读。
        # 与 grading.py 的报告/批改类端点保持同一归属口径（Task.creator_id）。
        if task_id is not None:
            task = db.get(Task, task_id)
            if not task:
                raise NotFoundException("任务不存在")
            if task.creator_id != user.id:
                raise PermissionException("只能查看自己发布任务的学情数据")

    stmt = (
        select(
            KnowledgePoint.name,
            func.count(Answer.id),
            func.sum(case((Answer.is_correct.is_(True), 1), else_=0)),
        )
        .join(Question, Question.knowledge_point_id == KnowledgePoint.id)
        .join(Answer, Answer.question_id == Question.id)
    )
    if subject_id:
        stmt = stmt.where(Question.subject_id == subject_id)
    if class_id or task_id:
        from app.models import Submission as _Sub
        stmt = stmt.join(_Sub, Answer.submission_id == _Sub.id)
        if task_id:
            stmt = stmt.where(_Sub.task_id == task_id)
        if class_id:
            stmt = stmt.join(User, _Sub.student_id == User.id).where(
                User.class_id == class_id)
    elif not scope.is_super:
        # ③ 两个过滤都没传：非超管不能退化成全校聚合。这里选择「把查询收敛到
        # 本人可访问班级」而不是直接 403 —— 前端未选班级时页面仍需渲染出
        # 本人任教范围的效果图，静默拒绝会造成空白页；而放行全校又会泄数据。
        # 收敛后 allowed 为空列表时 IN () 恒假，等价于「无可统计数据」。
        from app.models import Submission as _Sub
        stmt = stmt.join(_Sub, Answer.submission_id == _Sub.id).join(
            User, _Sub.student_id == User.id).where(
            User.class_id.in_(allowed or []))
    rows = db.execute(stmt.group_by(KnowledgePoint.name)).all()

    items = []
    for name, total, right in rows:
        acc = round((right or 0) / total * 100, 2) if total else 0
        items.append({"name": name, "answer_count": total, "accuracy": acc})
    items.sort(key=lambda x: x["accuracy"])
    return ok({
        "items": items,
        "weak": items[:5],
        "good": list(reversed(items[-5:])),
        "avg_accuracy": round(sum(i["accuracy"] for i in items) / len(items), 2) if items else 0,
    })


# ================================================================ 管理员端
@router.get("/admin/overview", summary="系统总览")
def admin_overview(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_manager),
):
    # 参数名必须为 user：export_excel 会以 admin_overview(db, user=...) 复用本函数
    def _count(model, *where):
        stmt = select(func.count()).select_from(model)
        for w in where:
            stmt = stmt.where(w)
        return db.scalar(stmt) or 0

    from app.models import Note

    since7 = now_local() - timedelta(days=7)
    active_7d = db.scalar(
        select(func.count(func.distinct(User.id))).where(User.last_login_at >= since7)
    ) or 0

    # 用 SQL 聚合代替「全表加载到内存再求平均」：
    # 提交量大时前者是 O(1) 内存，后者会吃掉数百 MB。
    avg_raw = db.scalar(
        select(func.avg(Submission.score)).where(Submission.score.isnot(None))
    ) or 0
    avg_rate = db.scalar(
        select(func.avg(Submission.score * 100.0 / func.nullif(Task.total_score, 0)))
        .join(Task, Task.id == Submission.task_id)
        .where(Submission.score.isnot(None), Task.total_score > 0)
    ) or 0

    return ok({
        "user": {
            "total": _count(User),
            "student": _count(User, User.identity == "student"),
            "teacher": _count(User, User.identity == "teacher"),
            "active_7d": active_7d,
            "pending": _count(User, User.status == "pending"),
        },
        "content": {
            "question": _count(Question),
            "published_question": _count(Question, Question.status == "published"),
            "paper": _count(Paper),
            "note": _count(Note),
            "knowledge_point": _count(KnowledgePoint),
        },
        "exam": {
            "task": _count(Task),
            "submission": _count(Submission),
            "avg_score": round(float(avg_raw), 2),
            # 全校平均得分率：跨不同满分试卷唯一可比的汇总指标
            "avg_score_rate": round(float(avg_rate), 2),
        },
        "ai": {
            "calls": _count(AgentCallLog),
            "failed": _count(AgentCallLog, AgentCallLog.status == "failed"),
            "fallback": _count(AgentCallLog, AgentCallLog.is_fallback.is_(True)),
        },
        "org": {"grade": _count(Grade), "subject": _count(Subject), "class": _count(Class)},
    })


@router.get("/admin/grade-comparison", summary="各年级教学数据对比")
def grade_comparison(db: Session = Depends(get_db), _: User = Depends(get_current_manager)):
    """各年级对比。

    重写原因（原实现三处问题）：
    1. outerjoin 的 ON 条件用 `Submission.task_id.in_(子查询)`，与 Grade 无关联
       → 中间结果 = 年级 × 题目 × 提交的笛卡尔积，数据量大时直接拖垮；
    2. user_count 未过滤 identity，教师/管理员被算进学生数（实测 53 vs 51）；
    3. avg_score 跨试卷混算原始分（30 分卷与 100 分卷混合）。
    """
    grades = db.scalars(select(Grade).order_by(Grade.grade_num)).all()

    # 批量聚合，避免逐年级多次查询
    q_counts = dict(db.execute(
        select(Question.grade_id, func.count()).group_by(Question.grade_id)
    ).all())
    t_by_grade = dict(db.execute(
        select(Task.grade_id, func.count()).group_by(Task.grade_id)
    ).all())
    stu_counts = dict(db.execute(
        select(User.grade_id, func.count())
        .where(User.identity == "student").group_by(User.grade_id)
    ).all())
    # 提交数：按任务所属年级
    sub_counts = dict(db.execute(
        select(Task.grade_id, func.count(Submission.id))
        .join(Submission, Submission.task_id == Task.id)
        .group_by(Task.grade_id)
    ).all())
    # 得分率均值：逐份提交 (score / total_score)，再做年级平均
    avg_rates = dict(db.execute(
        select(Task.grade_id,
               func.avg(Submission.score * 100.0 / func.nullif(Task.total_score, 0)))
        .join(Submission, Submission.task_id == Task.id)
        .where(Submission.score.isnot(None), Task.total_score > 0)
        .group_by(Task.grade_id)
    ).all())

    items = []
    for g in grades:
        items.append({
            "grade_name": g.name,
            "question_count": q_counts.get(g.id, 0),
            "task_count": t_by_grade.get(g.id, 0),
            "submission_count": sub_counts.get(g.id, 0),
            # 学生数（不含教师/管理员）
            "user_count": stu_counts.get(g.id, 0),
            "avg_score_rate": round(float(avg_rates.get(g.id) or 0), 2),
        })
    return ok(items)


@router.get("/admin/subject-comparison", summary="各学科教学数据对比")
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
    ])


@router.get("/admin/system-runtime", summary="系统运行报表")
def system_runtime(db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    from app.services.scheduler import scheduler_status

    since = now_local() - timedelta(days=1)
    return ok({
        "scheduler": scheduler_status(),
        "ai_calls_24h": db.scalar(
            select(func.count()).select_from(AgentCallLog).where(AgentCallLog.created_at >= since)
        ) or 0,
        "ai_failed_24h": db.scalar(
            select(func.count()).select_from(AgentCallLog).where(
                AgentCallLog.created_at >= since, AgentCallLog.status == "failed"
            )
        ) or 0,
        "api_error_24h": db.scalar(
            select(func.count()).select_from(ErrorLog).where(
                ErrorLog.created_at >= since
            )
        ) or 0,
    })


# ================================================================ 导出
@router.get("/export/excel", summary="报表导出 Excel")
def export_excel(
    report_type: str = Query(..., description="student_overview / class_overview / admin_overview"),
    class_id: Optional[int] = None,
    student_id: Optional[int] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    wb = Workbook()
    ws = wb.active
    ws.title = "报表"

    # 权限按报表类型分别校验：此前统一 get_current_user，
    # 学生可传 report_type=admin_overview 导出全校统计（依赖被内部函数调用绕过）。
    codes = set(user.role_codes or [])
    is_manager = bool({"sys_admin", "grade_admin"} & codes)
    is_teacher = bool({"teacher", "grade_admin", "sys_admin"} & codes)

    if report_type == "student_overview":
        # 个人报表：任何登录用户只能导出自己的（内部按当前 user 取数）
        data = student_overview(db, user)["data"]
        ws.append(["个人学习总览"])
        ws.append([])
        for k, v in data.get("student", {}).items():
            ws.append([k, v])
        for k in ("study_minutes_7d", "question_total", "accuracy", "wrong_unmastered",
                  "wrong_mastered", "note_count", "exam_count", "avg_score", "pass_count"):
            ws.append([k, data.get(k)])
    elif report_type == "class_overview" and class_id:
        if not is_teacher:
            raise PermissionException("需要教师权限才能导出班级报表")
        data = class_overview(class_id, db=db, user=user, scope=_scope_for(user, db))["data"]
        ws.append([f"班级学情报表 - {data['class']['name']}"])
        ws.append([])
        for k, v in data.items():
            if isinstance(v, dict):
                ws.append([k, json_dumps(v)])
            else:
                ws.append([k, v])
    elif report_type == "admin_overview":
        if not is_manager:
            raise PermissionException("需要系统管理员或年级管理员权限才能导出系统报表")
        data = admin_overview(db, user=user)["data"]
        ws.append(["系统总览报表"])
        ws.append([])
        for section, vals in data.items():
            ws.append([f"【{section}】"])
            if isinstance(vals, dict):
                for k, v in vals.items():
                    ws.append([k, v])
            else:
                ws.append([section, vals])
            ws.append([])
    else:
        raise BusinessException(
            "无效的报表类型，可选：student_overview / class_overview / admin_overview"
        )

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return StreamingResponse(
        buf, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=report_{report_type}.xlsx"},
    )


def json_dumps(v: Any) -> str:
    import json

    return json.dumps(v, ensure_ascii=False)


def _scope_for(user: User, db: Session) -> DataScope:
    return DataScope(user, db)
