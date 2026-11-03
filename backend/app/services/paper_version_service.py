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

# 每份试卷保留的版本数上限。
#
# 快照里冗余存了题干/答案/解析全文，一条几十 KB。而 snapshot() 在每次「编辑题目 /
# 移除题目 / 重构大题 / 回溯」时都会写一条 —— 一份反复打磨的卷子很容易攒到几十个
# 版本，版本抽屉一次全量读出来会明显变慢，DB 也会持续膨胀。
#
# 只保留最近 N 条，外加 version 最小的那条（首次组卷的原始结构，回溯时常被当作
# 「回到最初」的锚点）。删除不影响版本号递增：后续仍按 max(version)+1 生成。
KEEP_RECENT_VERSIONS = 20


def _prune_versions(db: Session, paper_id: int) -> int:
    """裁剪超出保留上限的历史版本，返回删除条数。

    保留策略：最近 KEEP_RECENT_VERSIONS 条 + version 最小的一条。
    早期版本连题干都被冗余保存过，删掉它们不会影响回溯到较新版本，
    因为每个版本的 snapshot 都是**自包含**的（不依赖前序版本）。
    """
    rows = db.scalars(
        select(PaperVersion)
        .where(PaperVersion.paper_id == paper_id)
        .order_by(PaperVersion.version.desc())
    ).all()
    if len(rows) <= KEEP_RECENT_VERSIONS:
        return 0
    keep_ids = {r.id for r in rows[:KEEP_RECENT_VERSIONS]}
    keep_ids.add(min(rows, key=lambda r: r.version).id)
    removed = 0
    for old in rows[KEEP_RECENT_VERSIONS:]:
        if old.id not in keep_ids:
            db.delete(old)
            removed += 1
    if removed:
        db.flush()
        logger.info(f"试卷 {paper_id} 版本裁剪：删除 {removed} 条历史快照")
    return removed


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
    # 裁剪必须在 flush 之后：此时新版本已入库，按 version 倒序切片才是准的。
    _prune_versions(db, paper.id)
    return row


