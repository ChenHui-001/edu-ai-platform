"""知识点关系图接口（节点 + 先修边 + 教材层级边）。

独立成模块而不是塞进 `knowledge.py`：
- `knowledge.py` 已到 `tools/check_file_size.py` 的行数预算上限；
- `/knowledge/graph` 必须在 `knowledge.router` 的 `/knowledge/{kp_id}`
  **之前**注册，单独一个路由便于在 `app/api/router.py` 里控制先后。
"""
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.v1.knowledge import _filtered_query, _flat_nodes
from app.core.database import get_db
from app.core.exception import NotFoundException, PermissionException
from app.models import KnowledgePoint, User
from app.services.knowledge_graph import mastery_map, resolve_graph
from app.utils.common import ok

router = APIRouter(prefix="/edu", tags=["知识点"])


@router.get("/knowledge/graph", summary="知识点关系图（先修 + 层级）")
def knowledge_graph(
    grade_id: Optional[int] = None,
    subject_id: Optional[int] = None,
    subject_name: Optional[str] = None,
    term: Optional[int] = None,
    root_id: Optional[int] = None,
    depth: int = Query(2, ge=1, le=4),
    params_limit: int = Query(600, ge=50, le=2000),
    include_hierarchy: bool = True,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """图谱页聚合接口：一次返回节点、先修边与层级边。

    - 不传 `root_id`：返回当前年级/学科的全部可见知识点（超限截断）；
    - 传 `root_id`：以该点为中心沿先修关系上下展开 `depth` 层，
      并补上层级父节点，便于看清「缺哪块基础」；
    - 学生身份额外返回 `mastery`（0-100，未学过为 None）。
    """
    statement = _filtered_query(
        db, user, grade_id=grade_id, subject_id=subject_id,
        term=term, subject_name=subject_name,
    )
    if not root_id:
        statement = statement.limit(params_limit + 1)
    base_rows = list(db.scalars(statement).all())
    if not base_rows:
        return ok({
            "nodes": [], "edges": [], "center": root_id, "depth": depth,
            "truncated": False,
            "counts": {"nodes": 0, "edges": 0, "prereq_edges": 0,
                       "hierarchy_edges": 0},
        })

    universe_rows: List[KnowledgePoint] = list(base_rows)
    if root_id:
        center = db.get(KnowledgePoint, root_id)
        if not center or not center.is_active:
            raise NotFoundException("知识点不存在")
        if center.id not in {row.id for row in base_rows}:
            raise PermissionException("无权查看该知识点")
        universe_rows = list(db.scalars(
            _filtered_query(db, user, subject_id=center.subject_id)).all())

    rows, edges, truncated = resolve_graph(
        db, base_rows, universe_rows,
        center_id=root_id, depth=depth,
        include_hierarchy=include_hierarchy, limit=params_limit,
    )
    node_list: List[Dict[str, Any]] = _flat_nodes(db, rows)

    if getattr(user, "identity", "") == "student":
        mastery = mastery_map(db, user.id, [row.id for row in rows])
        for node in node_list:
            node["mastery"] = mastery.get(int(node["id"]))

    prereq_count = sum(1 for edge in edges if edge["kind"] == "prereq")
    return ok({
        "nodes": node_list,
        "edges": edges,
        "center": int(root_id) if root_id else None,
        "depth": depth if root_id else None,
        "truncated": truncated,
        "counts": {
            "nodes": len(node_list),
            "edges": len(edges),
            "prereq_edges": prereq_count,
            "hierarchy_edges": len(edges) - prereq_count,
        },
    })
