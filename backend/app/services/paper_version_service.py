"""试卷版本快照服务。

原则：**版本只增不改**。每次结构变更写一条新快照，历史快照永不修改，
回溯操作本身也产生新版本。

快照里冗余存 stem/type/difficulty/answer/analysis，而不只存 question_id：
题库题目可能被后续编辑或删除，只存 id 会让历史版本回溯出「空壳卷」。
代价是每份快照几百 KB 量级——用 SQLite 文本字段完全可接受，
而且省掉了「回溯时反查历史题目快照」这套更复杂的机制。
"""
import json
import logging
from typing import Any, Dict, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Paper, PaperVersion

logger = logging.getLogger(__name__)


def build_snapshot(db: Session, paper: Paper) -> Dict[str, Any]:
    """构造整卷快照（标量字段 + 题目明细）。"""
    items = []
    for it in sorted(paper.items, key=lambda x: (x.section_sort or 0, x.sort_order or 0)):
        q = it.question
        items.append({
            "question_id": it.question_id,
            "sort_order": it.sort_order,
            "score": float(it.score or 0),
            "section_name": it.section_name,
            "section_code": it.section_code,
            "section_sort": it.section_sort or 0,
            "score_override": bool(it.score_override),
            # 冗余题目内容：题库改动/删除后仍能还原当时卷面
            "stem": q.stem if q else None,
            "type": q.type if q else None,
            "difficulty": q.difficulty if q else None,
            "answer": q.answer if q else None,
            "analysis": q.analysis if q else None,
            "knowledge_point_id": q.knowledge_point_id if q else None,
        })
    return {
        "paper": {
            "id": paper.id,
            "name": paper.name,
            "grade_id": paper.grade_id,
            "subject_id": paper.subject_id,
            "total_score": float(paper.total_score or 0),
            "duration": paper.duration,
            "difficulty_ratio": paper.difficulty_ratio,
            "exam_type": paper.exam_type,
            "standard_id": paper.standard_id,
            "status": paper.status,
            "description": paper.description,
        },
        "items": items,
    }


def snapshot(db: Session, paper: Paper, user_id: Optional[int],
             change_note: str = "") -> PaperVersion:
    """写入一条版本快照，并把 paper.current_version 推进到该版本号。

    不 commit——由调用方统一提交，保证「改卷 + 快照」在同一事务里，
    不会出现"改了但没快照"或"有快照但没改"的中间态。
    """
    db.flush()  # 保证 paper.items 读到最新
    current = paper.current_version or 1
    # 同版本号重复写入时递增，避免唯一约束冲突（例如连续两次 snapshot）
    existing = db.scalar(select(func.max(PaperVersion.version)).where(
        PaperVersion.paper_id == paper.id)) or 0
    version = max(current, existing + 1) if existing >= current else current

    data = build_snapshot(db, paper)
    row = PaperVersion(
        paper_id=paper.id,
        version=version,
        snapshot=json.dumps(data, ensure_ascii=False),
        change_note=change_note[:255] or None,
        item_count=len(data["items"]),
        total_score=float(data["paper"]["total_score"] or 0),
        created_by=user_id,
    )
    db.add(row)
    paper.current_version = version
    db.flush()
    return row


def prune(db: Session, paper_id: int, keep: int = 30) -> int:
    """保留最近 N 个版本，清理更早的（防止快照无限增长）。

    默认保留 30 个：一天改 5 次也能回溯近一周，足够教学场景。
    """
    total = db.scalar(select(func.count()).select_from(PaperVersion).where(
        PaperVersion.paper_id == paper_id)) or 0
    if total <= keep:
        return 0
    keep_ids = [r for r in db.scalars(
        select(PaperVersion.id).where(PaperVersion.paper_id == paper_id)
        .order_by(PaperVersion.version.desc()).limit(keep)).all()]
    deleted = db.execute(
        PaperVersion.__table__.delete().where(
            PaperVersion.paper_id == paper_id,
            PaperVersion.id.notin_(keep_ids))
    ).rowcount or 0
    db.flush()
    logger.info("试卷 %s 版本快照清理 %s 条（保留最近 %s 条）", paper_id, deleted, keep)
    return deleted
