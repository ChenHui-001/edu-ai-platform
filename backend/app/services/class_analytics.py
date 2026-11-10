"""班级维度学情聚合（报表用）。

**为什么单独成模块**：`tools/check_api_sql.py` 明令「新逻辑请放 services/」，
API 层只允许调用现成的服务函数。这里的聚合逻辑一放回 `api/v1/report.py`
就会顶高「API 层直接 SQL」棘轮；而且班级薄弱点这套口径将来会被
「年级薄弱点」「学科薄弱点」复用，放在 service 里天然可共享。
"""
from typing import Any, Dict, List, Optional

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.models import (
    KnowledgeMastery, KnowledgePoint, Subject, User,
)


def class_student_ids(db: Session, class_id: int) -> List[int]:
    """班级内的**学生** id 列表。

    刻意过滤 `identity == "student"`：班级表里可能挂着教师/班主任账号，
    不过滤会把教职工算进「学生人数」和作答分母（与 `class_overview` 同口径）。
    """
    return list(db.scalars(select(User.id).where(
        User.class_id == class_id, User.identity == "student")).all())


def weak_points(
    db: Session,
    student_ids: List[int],
    *,
    subject_id: Optional[int] = None,
    min_answers: int = 1,
) -> List[Dict[str, Any]]:
    """按知识点聚合班级掌握情况，正确率升序（最薄弱在最前）。

    数据源是 `edu_knowledge_mastery`（学生 × 知识点的累计计数），
    不是现算 `edu_answer`：累计表已经做过增量归并，读一条聚合 SQL 就够，
    也不会因为历史作答被清理而让口径漂移。

    `min_answers` 是**噪声闸门**：只有 1 个学生做了 1 道题时正确率非 0 即 100，
    按它排名会得到一份完全随机的「薄弱清单」，教师据此备课等于瞎猜。
    """
    if not student_ids:
        return []

    stmt = (
        select(
            KnowledgeMastery.knowledge_point_id,
            func.sum(KnowledgeMastery.total_count),
            func.sum(KnowledgeMastery.correct_count),
            func.avg(KnowledgeMastery.mastery),
            func.count(KnowledgeMastery.id),
            func.sum(case((KnowledgeMastery.mastery < 60, 1), else_=0)),
        )
        .where(KnowledgeMastery.student_id.in_(student_ids))
        .group_by(KnowledgeMastery.knowledge_point_id)
    )
    if subject_id:
        stmt = stmt.where(KnowledgeMastery.subject_id == subject_id)
    rows = db.execute(stmt).all()

    kp_ids = [r[0] for r in rows if r[0]]
    if not kp_ids:
        return []

    kp_map = {kp.id: kp for kp in db.scalars(
        select(KnowledgePoint).where(KnowledgePoint.id.in_(kp_ids))).all()}
    subj_ids = {kp.subject_id for kp in kp_map.values() if kp.subject_id}
    subj_names = dict(db.execute(
        select(Subject.id, Subject.name).where(Subject.id.in_(subj_ids))
    ).all()) if subj_ids else {}

    items: List[Dict[str, Any]] = []
    for kp_id, total, right, avg_mastery, tracked, weak_students in rows:
        total = int(total or 0)
        if total < min_answers:
            continue
        kp = kp_map.get(kp_id)
        if not kp:
            # 知识点已删但掌握度残留：跳过，而不是给前端一个 name=None 的行
            continue
        accuracy = round(int(right or 0) / total * 100, 2) if total else 0.0
        items.append({
            "knowledge_point_id": kp_id,
            "name": kp.name,
            "code": kp.code,
            "subject_id": kp.subject_id,
            "subject_name": subj_names.get(kp.subject_id, ""),
            "answer_count": total,
            "correct_count": int(right or 0),
            "accuracy": accuracy,
            # mastery 是 0-100 的平滑值（受作答分布影响），与硬正确率并列展示
            "avg_mastery": round(float(avg_mastery or 0), 1),
            "tracked_students": int(tracked or 0),
            "weak_students": int(weak_students or 0),
            "suggestion": suggestion_for(accuracy),
        })

    items.sort(key=lambda x: (x["accuracy"], -x["answer_count"]))
    return items


def suggestion_for(accuracy: float) -> str:
    """按正确率分档给讲评建议。只做阈值文案，不假装是 AI 诊断。"""
    if accuracy < 40:
        return "低于 40%，建议整节重讲并配基础题再练"
    if accuracy < 60:
        return "低于 60%，建议讲评课重点讲解典型错误"
    if accuracy < 80:
        return "60%~80%，建议针对性布置变式练习"
    return "已达 80% 以上，可作为巩固内容"
