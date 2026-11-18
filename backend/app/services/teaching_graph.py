"""Class-scoped graph analytics and targeted homework publication."""
from collections import Counter
from datetime import timedelta

from sqlalchemy import func, select

from app.core.exception import BusinessException, NotFoundException, PermissionException
from app.models import (Class, KnowledgePoint, Paper, PaperItem, Question,
                        Task, TaskAssignment, TeachingAssignment, WrongQuestion)
from app.services.class_analytics import class_student_ids, weak_points
from app.services.knowledge_graph import resolve_graph
from app.services.notification import notify_many
from app.services.question_access import question_usable_error
from app.utils.common import now_local


def assert_class(db, user, scope, class_id, subject_id):
    allowed = scope.class_ids()
    if allowed is not None and class_id not in allowed:
        raise PermissionException("无权访问该班级")
    klass = db.get(Class, class_id)
    if not klass:
        raise NotFoundException("班级不存在")
    from app.models import Subject

    subject = db.get(Subject, subject_id)
    if not subject or subject.grade_id != klass.grade_id:
        raise BusinessException("学科与班级年级不一致")
    if scope.is_teacher and not scope.is_super and not scope.is_grade_admin:
        assignment = db.scalar(select(TeachingAssignment).where(
            TeachingAssignment.teacher_id == user.id, TeachingAssignment.class_id == class_id,
            TeachingAssignment.subject_id == subject_id, TeachingAssignment.is_active.is_(True)))
        if not assignment:
            raise PermissionException("只能操作自己任教的学科")
    return klass


def class_graph(db, user, scope, class_id, subject_id):
    klass = assert_class(db, user, scope, class_id, subject_id)
    students = class_student_ids(db, class_id)
    points = list(db.scalars(select(KnowledgePoint).where(
        KnowledgePoint.subject_id == subject_id, KnowledgePoint.grade_id == klass.grade_id,
        KnowledgePoint.status == "published", KnowledgePoint.is_active.is_(True)
    ).order_by(KnowledgePoint.sort, KnowledgePoint.id).limit(601)).all())
    rows, edges, truncated = resolve_graph(db, points, points, limit=600)
    stats = {item["knowledge_point_id"]: item for item in weak_points(db, students, subject_id=subject_id)}
    wrong_rows = db.scalars(select(WrongQuestion).where(
        WrongQuestion.student_id.in_(students), WrongQuestion.subject_id == subject_id,
        WrongQuestion.is_mastered.is_(False))).all()
    reasons = {}
    for wrong in wrong_rows:
        reasons.setdefault(wrong.knowledge_point_id, Counter()).update([wrong.error_reason or "未分类"])
    nodes = []
    child_counts = Counter(child.parent_id for child in rows)
    question_counts = dict(db.execute(select(Question.knowledge_point_id, func.count(Question.id)).where(
        Question.knowledge_point_id.in_([row.id for row in rows]), Question.status == "published",
        Question.bank_type == "public").group_by(Question.knowledge_point_id)).all())
    for row in rows:
        item = stats.get(row.id, {})
        nodes.append({"id": row.id, "name": row.name, "difficulty": row.difficulty,
                      "child_count": child_counts[row.id], "question_count": question_counts.get(row.id, 0),
                      "mastery": item.get("avg_mastery"), "weak_students": item.get("weak_students", 0),
                      "tracked_students": item.get("tracked_students", 0),
                      "unknown_students": max(0, len(students) - item.get("tracked_students", 0)),
                      "error_reasons": dict(reasons.get(row.id, {}))})
    return {"nodes": nodes, "edges": edges, "student_count": len(students), "truncated": truncated}


def assign_homework(db, user, scope, data):
    klass = assert_class(db, user, scope, data.class_id, data.subject_id)
    requested = set(data.knowledge_point_ids)
    nodes = list(db.scalars(select(KnowledgePoint).where(
        KnowledgePoint.id.in_(requested), KnowledgePoint.subject_id == data.subject_id,
        KnowledgePoint.grade_id == klass.grade_id, KnowledgePoint.status == "published",
        KnowledgePoint.is_active.is_(True))).all())
    if {item.id for item in nodes} != requested:
        raise BusinessException("包含不存在或跨学科的知识点")
    bank = list(db.scalars(select(Question).where(
        Question.knowledge_point_id.in_(requested), Question.status == "published",
        Question.subject_id == data.subject_id, Question.grade_id == klass.grade_id
    ).order_by(Question.id)).all())
    bank = [item for item in bank if question_usable_error(
        item, user_id=user.id, is_admin=scope.is_super) is None]
    if any(not any(item.knowledge_point_id == node for item in bank) for node in requested):
        raise BusinessException("部分知识点没有可用题目，请先补题")
    if data.count < len(requested):
        raise BusinessException("题量不能小于选中的知识点数量")
    chosen = []
    for node in sorted(requested):
        chosen.append(next(item for item in bank if item.knowledge_point_id == node))
    chosen.extend(item for item in bank if item not in chosen)
    chosen = chosen[:data.count]
    total = sum(item.score or 5 for item in chosen)
    paper = Paper(name="班级专项补弱练习", grade_id=klass.grade_id, subject_id=data.subject_id,
                  creator_id=user.id, total_score=total, duration=30, status="published")
    db.add(paper)
    db.flush()
    for position, question in enumerate(chosen):
        db.add(PaperItem(paper_id=paper.id, question_id=question.id,
                         score=question.score or 5, sort_order=position + 1))
        question.usage_count = (question.usage_count or 0) + 1
    paper.use_count = (paper.use_count or 0) + 1
    task = Task(title=paper.name, type="homework", paper_id=paper.id, subject_id=data.subject_id,
                grade_id=klass.grade_id, creator_id=user.id, status="published", total_score=total,
                pass_score=total * .6, duration=30, show_answer=True,
                start_at=now_local(), end_at=now_local() + timedelta(days=data.due_days))
    db.add(task)
    db.flush()
    db.add(TaskAssignment(task_id=task.id, class_id=klass.id, notified=True))
    students = class_student_ids(db, klass.id)
    notify_many(db, students, title="专项补弱作业", content=task.title,
                type="exam", biz_type="task", biz_id=task.id, category="task")
    db.commit()
    return {"task_id": task.id, "paper_id": paper.id, "question_count": len(chosen),
            "requested_count": data.count}
