"""答题、判分、错题收录、知识点掌握度更新等核心教学逻辑。"""
import json
from datetime import timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.agents.grading_agent import OBJECTIVE_TYPES, GradingAgent
from app.core.config import settings
from app.core.exception import BusinessException
from app.models import (
    Answer, KnowledgeMastery, KnowledgePoint, Paper, PaperItem, Question, ReviewPlan,
    StudyRecord, Submission, Task, TaskAssignment, TaskStatus, WrongQuestion,
)
from app.utils.common import utcnow


def _content_to_db(content: Any) -> Optional[str]:
    """把学生答案统一落库为字符串。

    Answer.content 是 Text 列，而多选题的作答是 list（如 ["A","C"]），
    直接绑定会触发 sqlite3.ProgrammingError: type 'list' is not supported，
    导致整场考试交卷失败。此处统一 JSON 序列化，读出侧用 _content_from_db 还原。
    """
    if content is None:
        return None
    if isinstance(content, str):
        return content
    return json.dumps(content, ensure_ascii=False)


def _content_from_db(raw: Optional[str]) -> Any:
    """还原落库的学生答案：JSON 数组还原为 list，其余原样返回。"""
    if raw is None:
        return None
    txt = raw.strip()
    if txt.startswith("[") and txt.endswith("]"):
        try:
            return json.loads(txt)
        except json.JSONDecodeError:
            return raw
    return raw


def get_student_submission(db: Session, task_id: int, student_id: int, attempt: int = 1) -> Submission:
    """获取或创建学生作答记录。"""
    sub = db.scalar(
        select(Submission).where(
            Submission.task_id == task_id,
            Submission.student_id == student_id,
            Submission.attempt == attempt,
        )
    )
    if not sub:
        sub = Submission(task_id=task_id, student_id=student_id, attempt=attempt)
        db.add(sub)
        db.flush()
    return sub


def save_answers(
    db: Session, submission: Submission, answers: List[Dict[str, Any]], auto_grade: bool = True
) -> Dict[str, Any]:
    """保存作答并判分（客观题自动判分）。"""
    paper = db.get(Paper, db.get(Task, submission.task_id).paper_id)
    items = {i.id: i for i in paper.items}
    for a in answers:
        if not a.get("paper_item_id"):
            raise BusinessException("答题数据缺少 paper_item_id")
    q_ids = [a["paper_item_id"] for a in answers]
    existing = {
        a.paper_item_id: a for a in db.scalars(
            select(Answer).where(Answer.submission_id == submission.id)
        ).all()
    }

    for a in answers:
        item_id = a["paper_item_id"]
        item = items.get(item_id)
        if not item:
            continue
        content = a.get("content")

        ans = existing.get(item_id)
        if not ans:
            ans = Answer(
                submission_id=submission.id,
                paper_item_id=item_id,
                question_id=item.question_id,
                full_score=item.score,
            )
            db.add(ans)
        ans.content = _content_to_db(content)

    db.flush()

    if auto_grade:
        grading = GradingAgent()
        grade_items = [
            {"question_id": item.question_id, "student_answer": content,
             "full_score": item.score}
            for item_id, content in [(a["paper_item_id"], a.get("content")) for a in answers]
            for item in [items.get(item_id)] if item
        ]
        res = grading.run(db, user_id=submission.student_id, items=grade_items)
        # Agent.run() 返回 AgentResult 包装层，业务数据在 data 字段
        graded = res.get("data") or {}
        summary = graded.get("summary") or {
            "total": len(grade_items), "correct_count": 0, "accuracy": 0.0,
            "total_score": 0.0, "full_score": sum(i.get("full_score", 0) for i in grade_items),
            "score_rate": 0.0, "pending_manual": 0, "objective_count": 0,
            "subjective_count": 0, "ai_graded": 0,
        }
        if not res.get("success"):
            # Agent 执行异常时不阻断答题流程，按未判分处理，交由教师批改
            db.flush()
            return summary

        for r in graded.get("results", []):
            ans = db.scalar(
                select(Answer).where(
                    Answer.submission_id == submission.id,
                    Answer.question_id == r["question_id"],
                )
            )
            if not ans:
                continue
            ans.is_correct = r.get("is_correct")
            ans.score = r.get("score")
            ans.grader_type = r.get("grader_type", "auto")
            ans.teacher_comment = r.get("comment")
            if r.get("error_points"):
                ans.ai_error_points = json.dumps(r["error_points"], ensure_ascii=False)

        results = graded.get("results", [])
        submission.objective_score = sum(
            r.get("score") or 0 for r in results if r.get("grader_type") != "ai"
        )
        submission.score = summary["total_score"]
        submission.status = "auto_graded" if summary["pending_manual"] == 0 else "not_graded"

        # 错题收录 + 知识点掌握度更新
        for r in results:
            # 只有「已判定为错」的客观题才收录错题。
            # 待教师人工批改的主观题虽然 is_correct 也是 False，但那是「尚未判定」
            # 而不是「做错」，若一并收录会导致学生答对却出现在错题本里。
            pending_manual = (
                r.get("question_type") not in OBJECTIVE_TYPES
                and r.get("grader_type") != "ai"
            )
            if r.get("is_correct") is False and r.get("grader_type") != "ai" \
                    and not pending_manual:
                _collect_wrong_question(db, submission, r)
            elif r.get("is_correct"):
                _update_mastery(db, submission.student_id, r["question_id"], True)

        _record_study(db, submission)
        db.flush()
        return summary

    db.flush()
    return {}


def _collect_wrong_question(db: Session, submission: Submission, result: Dict[str, Any]) -> None:
    """错题自动归档。"""
    q = db.get(Question, result["question_id"])
    if not q:
        return
    task = db.get(Task, submission.task_id)
    exists = db.scalar(
        select(WrongQuestion).where(
            WrongQuestion.student_id == submission.student_id,
            WrongQuestion.question_id == q.id,
        )
    )
    if exists:
        exists.error_count += 1
        exists.last_wrong_at = utcnow()
        exists.is_mastered = False
        exists.mastered_at = None
        exists.source_id = submission.id
    else:
        db.add(
            WrongQuestion(
                student_id=submission.student_id,
                question_id=q.id,
                subject_id=q.subject_id,
                knowledge_point_id=q.knowledge_point_id,
                wrong_answer=str(result.get("student_answer", ""))[:500],
                source_type=(task.type if task else "practice"),
                source_id=submission.id,
                source_name=(task.title if task else "随机练习"),
            )
        )
    # 错题的知识点记为未掌握
    if q.knowledge_point_id:
        _update_mastery(db, submission.student_id, q.knowledge_point_id, False, question_id=q.id)


def _update_mastery(
    db: Session, student_id: int, target_id: int, correct: bool, question_id: Optional[int] = None
) -> None:
    """更新知识点掌握度。"""
    kp_id = target_id
    if question_id:
        q = db.get(Question, question_id)
        if q and q.knowledge_point_id:
            kp_id = q.knowledge_point_id

    kp = db.get(KnowledgePoint, kp_id)
    if not kp:
        return

    row = db.scalar(
        select(KnowledgeMastery).where(
            KnowledgeMastery.student_id == student_id,
            KnowledgeMastery.knowledge_point_id == kp_id,
        )
    )
    if not row:
        row = KnowledgeMastery(
            student_id=student_id, knowledge_point_id=kp_id, subject_id=kp.subject_id
        )
        db.add(row)
        db.flush()

    row.total_count += 1
    if correct:
        row.correct_count += 1
    else:
        row.wrong_count += 1
    row.mastery = round(row.correct_count / row.total_count * 100, 2)
    row.last_practice_at = utcnow()


def _record_study(db: Session, submission: Submission) -> None:
    """记录当日学习行为。"""
    today = utcnow().strftime("%Y-%m-%d")
    row = db.scalar(
        select(StudyRecord).where(
            StudyRecord.student_id == submission.student_id,
            StudyRecord.study_date == today,
        )
    )
    if not row:
        row = StudyRecord(student_id=submission.student_id, study_date=today)
        db.add(row)
        db.flush()
    row.question_count += submission.answers.__len__()
    row.correct_count += sum(1 for a in submission.answers if a.is_correct)


def finalize_submission(
    db: Session, submission: Submission, *, duration_seconds: Optional[int] = None
) -> Dict[str, Any]:
    """交卷：完成判分、计算排名、更新错题本与掌握度、生成复习计划。"""
    task = db.get(Task, submission.task_id)
    paper = db.get(Paper, task.paper_id) if task else None

    # 统一重算分数
    answers = db.scalars(
        select(Answer).where(Answer.submission_id == submission.id)
    ).all()
    objective = sum(a.score or 0 for a in answers if a.grader_type != "ai")
    subjective = sum(a.score or 0 for a in answers if a.grader_type == "ai")
    submission.objective_score = objective
    submission.subjective_score = subjective
    submission.score = round(objective + subjective, 2)
    submission.duration_seconds = duration_seconds or submission.duration_seconds
    submission.submit_time = utcnow()
    submission.is_passed = submission.score >= (task.pass_score if task else settings.PASS_SCORE)
    # 主观题 AI 判分完成同样属于「自动判分完成」；
    # 人工复核 / 改分经批改中心接口把状态推进为 fully_graded。
    submission.status = "auto_graded"

    db.flush()

    if task:
        submission.is_passed = submission.score >= task.pass_score

    # 班级排名
    submission.class_rank = _calc_rank(db, submission)
    _record_study(db, submission)
    db.commit()
    db.refresh(submission)
    return {
        "score": submission.score,
        "objective_score": submission.objective_score,
        "subjective_score": submission.subjective_score,
        "is_passed": submission.is_passed,
        "class_rank": submission.class_rank,
    }


def _calc_rank(db: Session, submission: Submission) -> Optional[int]:
    """班级排名计算。"""
    task = db.get(Task, submission.task_id)
    if not task:
        return None
    # 找出该任务下同班学生
    from app.models import User

    class_ids = db.scalars(
        select(User.class_id).where(
            User.class_id.isnot(None),
            User.id.in_(select(Submission.student_id).where(Submission.task_id == task.id)),
        )
    ).all()
    peers = db.scalars(
        select(Submission).where(
            Submission.task_id == task.id,
            Submission.student_id.in_(select(User.id).where(User.class_id.in_(class_ids))),
            Submission.score.isnot(None),
        )
    ).all()
    scores = sorted([s.score for s in peers if s.score is not None], reverse=True)
    if submission.score in scores:
        return scores.index(submission.score) + 1
    return len(scores) + 1


def generate_review_plan_for_wrong(db: Session, wrong: WrongQuestion) -> List[ReviewPlan]:
    """按艾宾浩斯遗忘曲线为错题生成复习计划。"""
    created: List[ReviewPlan] = []
    today = utcnow()
    for stage, interval in enumerate(settings.REVIEW_INTERVALS, start=1):
        date = (today + timedelta(days=interval)).strftime("%Y-%m-%d")
        exists = db.scalar(
            select(ReviewPlan).where(
                ReviewPlan.student_id == wrong.student_id,
                ReviewPlan.wrong_question_id == wrong.id,
                ReviewPlan.stage == stage,
            )
        )
        if exists:
            continue
        plan = ReviewPlan(
            student_id=wrong.student_id,
            wrong_question_id=wrong.id,
            knowledge_point_id=wrong.knowledge_point_id or 0,
            subject_id=wrong.subject_id,
            stage=stage,
            scheduled_date=date,
        )
        db.add(plan)
        created.append(plan)
    return created


def create_practice_paper(
    db: Session,
    *,
    creator_id: int,
    grade_id: int,
    subject_id: int,
    count: int = 10,
    question_types: Optional[List[str]] = None,
    difficulty: Optional[str] = None,
    knowledge_point_ids: Optional[List[int]] = None,
) -> Paper:
    """随机练习：即时生成一份练习试卷。"""
    stmt = select(Question).where(
        Question.subject_id == subject_id,
        Question.status == "published",
    )
    if grade_id:
        stmt = stmt.where(Question.grade_id == grade_id)
    if question_types:
        stmt = stmt.where(Question.type.in_(question_types))
    if difficulty:
        stmt = stmt.where(Question.difficulty == difficulty)
    if knowledge_point_ids:
        stmt = stmt.where(Question.knowledge_point_id.in_(knowledge_point_ids))

    questions = list(
        db.scalars(stmt.order_by(func.random()).limit(count * 3)).all()
    )
    if len(questions) < count:
        # 放宽条件：只放宽「题型 / 难度 / 知识点」，**绝不放宽年级**。
        # 原实现这里把 grade_id 一起丢掉了，只按 subject_id 查：
        # 由于 Subject 的唯一键是 (grade_id, name)，subject_id 本身已经绑定了
        # 某个具体年级，丢掉 grade_id 就等于允许「七年级学生拿到一年级语文题」。
        # 实测 stu731（七年级）请求语文时，严格条件 0 条 → 降级后抽到
        # grade_id=1 的 5 道题，卷面却标着七年级，学生完全做不了。
        relaxed = select(Question).where(
            Question.subject_id == subject_id,
            Question.status == "published",
        )
        if grade_id:
            relaxed = relaxed.where(Question.grade_id == grade_id)
        questions = list(
            db.scalars(relaxed.limit(count * 2)).all()
        )
    questions = questions[:count]
    if not questions:
        raise BusinessException("该学科在该年级暂无题目，请先向老师申请添加")

    paper = Paper(
        name=f"随机练习-{utcnow():%m%d%H%M}",
        grade_id=grade_id, subject_id=subject_id,
        total_score=sum(q.score for q in questions),
        duration=max(10, count * 2), creator_id=creator_id, source="manual",
    )
    db.add(paper)
    db.flush()
    for i, q in enumerate(questions, start=1):
        db.add(PaperItem(paper_id=paper.id, question_id=q.id, sort_order=i, score=q.score))
    db.commit()
    db.refresh(paper)
    return paper


def create_practice_task(db: Session, student_id: int, paper: Paper) -> Task:
    """为随机练习创建任务记录。"""
    task = Task(
        title=paper.name, type="practice", paper_id=paper.id,
        subject_id=paper.subject_id, grade_id=paper.grade_id,
        creator_id=student_id, status=TaskStatus.PUBLISHED.value,
        start_at=utcnow(), end_at=utcnow() + timedelta(days=1),
        duration=paper.duration, total_score=paper.total_score,
        show_answer=True,
    )
    db.add(task)
    db.flush()
    db.add(TaskAssignment(task_id=task.id, student_id=student_id))
    db.commit()
    db.refresh(task)
    return task


def grade_summary(db: Session, submission: Submission) -> Dict[str, Any]:
    """生成班级学情报告（批改完成后）。"""
    task = db.get(Task, submission.task_id)
    if not task:
        return {}

    subs = db.scalars(
        select(Submission).where(
            Submission.task_id == task.id, Submission.score.isnot(None)
        )
    ).all()
    scores = [s.score for s in subs if s.score is not None]
    if not scores:
        return {}

    total = len(scores)
    avg = round(sum(scores) / total, 2)
    # 分数段分布
    bands = {"90-100": 0, "80-89": 0, "70-79": 0, "60-69": 0, "<60": 0}
    for s in scores:
        if s >= 90: bands["90-100"] += 1
        elif s >= 80: bands["80-89"] += 1
        elif s >= 70: bands["70-79"] += 1
        elif s >= 60: bands["60-69"] += 1
        else: bands["<60"] += 1

    # 逐题正确率
    q_stats = []
    paper = db.get(Paper, task.paper_id)
    for item in paper.items:
        q = item.question
        total_a = db.scalar(
            select(func.count()).select_from(Answer).where(
                Answer.question_id == q.id,
                Answer.submission_id.in_(select(Submission.id).where(Submission.task_id == task.id)),
            )
        ) or 0
        right_a = db.scalar(
            select(func.count()).select_from(Answer).where(
                Answer.question_id == q.id, Answer.is_correct.is_(True),
                Answer.submission_id.in_(select(Submission.id).where(Submission.task_id == task.id)),
            )
        ) or 0
        kp = db.get(KnowledgePoint, q.knowledge_point_id) if q.knowledge_point_id else None
        q_stats.append({
            "question_id": q.id, "stem": q.stem[:80], "type": q.type,
            "knowledge_point": kp.name if kp else "综合",
            "answer_count": total_a, "correct_count": right_a,
            "accuracy": round(right_a / total_a * 100, 2) if total_a else 0.0,
        })
    q_stats.sort(key=lambda x: x["accuracy"])

    return {
        "class_size": total,
        "avg_score": avg,
        "max_score": max(scores),
        "min_score": min(scores),
        "pass_rate": round(sum(1 for s in scores if s >= 60) / total * 100, 2),
        "completion_rate": 100.0,
        "score_bands": bands,
        "question_stats": q_stats,
        "weak_questions": [q for q in q_stats if q["accuracy"] < 60][:5],
        "weak_knowledge": _weak_knowledge(q_stats),
    }


@staticmethod
def _weak_knowledge(q_stats: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        agg: Dict[str, List[int]] = {}
        for q in q_stats:
            kp = q["knowledge_point"]
            agg.setdefault(kp, [0, 0])
            agg[kp][0] += q["correct_count"]
            agg[kp][1] += q["answer_count"]
        out = [
            {"name": k, "accuracy": round(v[0] / v[1] * 100, 2) if v[1] else 0}
            for k, v in agg.items()
        ]
        out.sort(key=lambda x: x["accuracy"])
        return out[:5]
