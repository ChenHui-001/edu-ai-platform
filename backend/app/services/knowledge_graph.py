"""知识点关系图：先修边与教材层级的展开、配色前所需的原始数据。

放在 services 层的原因：`tools/check_api_sql.py` 用棘轮守住「API 层不写
裸查询」，而图谱天然需要多表查询与 BFS 展开；接口层只保留权限收敛与
响应组装，查询逻辑全部在这里。
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import KnowledgeMastery, KnowledgePoint, KnowledgePrerequisite


def prereq_edges(db: Session, ids: Sequence[int]) -> List[KnowledgePrerequisite]:
    """取「后继在本批 id 内」的先修边。

    只按 topic 侧过滤：中心展开时先修端可能在范围外（跨年级回溯），
    由调用方决定是否保留。
    """
    if not ids:
        return []
    return list(db.scalars(
        select(KnowledgePrerequisite).where(
            KnowledgePrerequisite.topic_kp_id.in_(list(ids)),
        ).order_by(KnowledgePrerequisite.id)
    ).all())


def resolve_graph(
    db: Session,
    base_rows: Sequence[KnowledgePoint],
    universe_rows: Sequence[KnowledgePoint],
    *,
    center_id: Optional[int] = None,
    depth: int = 2,
    include_hierarchy: bool = True,
    limit: int = 600,
) -> Tuple[List[KnowledgePoint], List[Dict[str, Any]], bool]:
    """返回 (节点行, 边, 是否被截断)。

    - `center_id` 为空：直接使用 `base_rows`（超出 `limit` 截断）；
    - 否则在同 `subject` 的 `universe_rows` 上沿先修关系做双向 BFS，
      并补回最多 3 层父节点，避免图谱里出现"悬空知识点"。
    """
    truncated = False
    if center_id:
        universe = {row.id: row for row in universe_rows}
        adjacency: Dict[int, Set[int]] = {nid: set() for nid in universe}
        for edge in prereq_edges(db, list(universe)):
            if edge.prerequisite_kp_id not in universe:
                continue
            adjacency[edge.topic_kp_id].add(edge.prerequisite_kp_id)
            adjacency[edge.prerequisite_kp_id].add(edge.topic_kp_id)

        keep: Set[int] = {center_id}
        frontier: Set[int] = {center_id}
        for _ in range(max(1, depth)):
            nxt: Set[int] = set()
            for node_id in sorted(frontier):
                nxt |= adjacency.get(node_id, set()) - keep
            if not nxt:
                break
            capacity = max(0, limit - len(keep))
            if len(nxt) > capacity:
                nxt = set(sorted(nxt)[:capacity])
                truncated = True
            keep |= nxt
            frontier = nxt
            if truncated:
                break

        if include_hierarchy:
            for node_id in list(keep):
                row = universe.get(node_id)
                parent_id = row.parent_id if row else None
                hops = 0
                while parent_id and hops < 3:
                    if parent_id not in keep and len(keep) >= limit:
                        truncated = True
                        break
                    keep.add(parent_id)
                    parent_row = universe.get(parent_id)
                    parent_id = parent_row.parent_id if parent_row else None
                    hops += 1
        rows = [universe[node_id] for node_id in keep if node_id in universe]
    else:
        rows = list(base_rows)
        if len(rows) > limit:
            rows = rows[:limit]
            truncated = True

    rows.sort(key=lambda row: (row.grade_id or 0, row.term or 0, row.sort or 0, row.id))
    keep_ids = {row.id for row in rows}

    edges: List[Dict[str, Any]] = []
    for edge in prereq_edges(db, list(keep_ids)):
        if edge.prerequisite_kp_id not in keep_ids:
            continue
        edges.append({
            "source": int(edge.prerequisite_kp_id),
            "target": int(edge.topic_kp_id),
            "kind": "prereq",
            "strength": "soft" if edge.strength == "soft" else "hard",
            "reason": edge.reason,
        })
    if include_hierarchy:
        for row in rows:
            if row.parent_id and row.parent_id in keep_ids:
                edges.append({
                    "source": int(row.parent_id),
                    "target": int(row.id),
                    "kind": "hierarchy",
                    "strength": None,
                    "reason": None,
                })
    return rows, edges, truncated


def mastery_map(db: Session, student_id: int,
                ids: Sequence[int]) -> Dict[int, float]:
    """学生视角的掌握度（0-100）；未学过的不出现在结果里。"""
    if not ids:
        return {}
    rows = db.scalars(
        select(KnowledgeMastery).where(
            KnowledgeMastery.student_id == student_id,
            KnowledgeMastery.knowledge_point_id.in_(list(ids)),
        )
    ).all()
    return {
        int(row.knowledge_point_id): round(float(row.mastery or 0), 1)
        for row in rows
    }
