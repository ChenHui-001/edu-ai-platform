"""知识先修诊断引擎。

移植自 cn-math-taxonomy `diagnose/engine.js` 的核心语义，但改为服务端实现：
- 会话可 JSON 序列化，并按作答历史重放，刷新/撤销不会出现状态漂移；
- 目标模式纳入全部先修祖先，筛查模式只在目标子图内回溯；
- hard 先修优先于 soft，确认失败后才判薄弱并向先修回溯；
- 诊断结果只用于会话展示，不写 `KnowledgeMastery`。
"""
import hashlib
import json
import math
import re
import unicodedata
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Grade, KnowledgePoint, KnowledgePrerequisite, Question, Subject

RESULTS = {"correct", "wrong", "skip"}
DEFAULT_LIMIT = 16
SCREEN_LIMIT = 40
DEFAULT_CONFIRM = 3
DIFF_RANK = {"easy": 0, "basic": 0, "medium": 1, "standard": 1,
             "hard": 2, "challenge": 2, "advanced": 2}


def _json_load(value: Optional[str], default: Any = None) -> Any:
    if not value:
        return default
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return default


def _normalize_text(value: Any) -> str:
    text = unicodedata.normalize("NFKC", str(value if value is not None else ""))
    return re.sub(r"\s+", "", text).strip().lower()


def _num(value: Any) -> Optional[float]:
    text = _normalize_text(value)
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _rand01(seed: str, key: str) -> float:
    digest = hashlib.sha256(f"{seed}|{key}".encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") / float(2 ** 64)


def _q_order(question: Question) -> Tuple[int, int]:
    ext = str(question.external_id or "")
    match = re.search(r"_q(\d+)$", ext)
    return (0, int(match.group(1))) if match else (1, int(question.id))


def _question_extra(row: Question) -> Dict[str, Any]:
    data = _json_load(row.extra_json, {})
    return data if isinstance(data, dict) else {}


def _question_options(row: Question) -> List[Dict[str, str]]:
    data = _json_load(row.options, [])
    out: List[Dict[str, str]] = []
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and item.get("key") is not None:
                out.append({
                    "key": str(item.get("key")),
                    "text": str(item.get("text") or ""),
                })
    return out


def _node_ref(graph: Dict[str, Any], node_id: int,
              status: Optional[str] = None) -> Dict[str, Any]:
    node = graph["by_id"].get(node_id) or {}
    data = {
        "id": node_id,
        "name": node.get("name") or f"知识点 {node_id}",
        "grade_num": node.get("grade_num"),
        "chapter": node.get("chapter"),
        "external_id": node.get("external_id"),
    }
    if status:
        data["status"] = status
    return data


def build_graph(db: Session, subject_name: str) -> Dict[str, Any]:
    """构造学科全量先修图与题库。跨年级节点必须一起纳入。"""
    subject_ids = list(db.scalars(
        select(Subject.id).where(Subject.name == subject_name)).all())
    if not subject_ids:
        return {
            "nodes": [], "by_id": {}, "index": {}, "prereqs": {},
            "dependents": {}, "bank": {}, "order": [], "subject_ids": [],
        }
    rows = list(db.scalars(
        select(KnowledgePoint).where(
            KnowledgePoint.subject_id.in_(subject_ids),
            KnowledgePoint.is_active.is_(True),
            KnowledgePoint.status == "published",
        )
    ).all())
    grades = {
        g.id: g for g in db.scalars(
            select(Grade).where(Grade.id.in_({r.grade_id for r in rows}))
        ).all()
    } if rows else {}
    parent_names = {r.id: r.name for r in rows}

    def sort_key(row: KnowledgePoint) -> Tuple[int, int, int, int]:
        grade_num = getattr(grades.get(row.grade_id), "grade_num", 99)
        return (grade_num or 99, row.term or 0, row.sort or 0, row.id)

    rows.sort(key=sort_key)
    by_id: Dict[int, Dict[str, Any]] = {}
    for row in rows:
        parent = next((r for r in rows if r.id == row.parent_id), None)
        by_id[row.id] = {
            "id": row.id,
            "name": row.name,
            "grade_num": getattr(grades.get(row.grade_id), "grade_num", None),
            "term": row.term,
            "sort": row.sort,
            "level": row.level,
            "description": row.description,
            "external_id": row.external_id,
            "chapter": parent.name if parent else None,
            "parent_name": parent_names.get(row.parent_id),
        }
    order = [row.id for row in rows]
    index = {node_id: pos for pos, node_id in enumerate(order)}
    prereqs: Dict[int, List[Dict[str, Any]]] = {node_id: [] for node_id in order}
    dependents: Dict[int, List[int]] = {node_id: [] for node_id in order}
    if order:
        edges = db.scalars(
            select(KnowledgePrerequisite).where(
                KnowledgePrerequisite.topic_kp_id.in_(order),
                KnowledgePrerequisite.prerequisite_kp_id.in_(order),
            ).order_by(KnowledgePrerequisite.id)
        ).all()
        for edge in edges:
            prereqs[edge.topic_kp_id].append({
                "id": edge.prerequisite_kp_id,
                "strength": "soft" if edge.strength == "soft" else "hard",
                "reason": edge.reason,
            })
            dependents[edge.prerequisite_kp_id].append(edge.topic_kp_id)
    for node_id in order:
        prereqs[node_id].sort(
            key=lambda e: (0 if e["strength"] == "hard" else 1,
                           index.get(e["id"], 10 ** 9)))
        dependents[node_id].sort(key=lambda nid: index.get(nid, 10 ** 9))

    bank: Dict[int, List[Dict[str, Any]]] = {node_id: [] for node_id in order}
    if order:
        questions = list(db.scalars(
            select(Question).where(
                Question.knowledge_point_id.in_(order),
                Question.status == "published",
            )
        ).all())
        questions.sort(key=_q_order)
        for row in questions:
            if row.knowledge_point_id not in bank:
                continue
            bank[row.knowledge_point_id].append({
                "qid": str(row.id),
                "db_id": row.id,
                "topic_id": row.knowledge_point_id,
                "difficulty": row.difficulty or "medium",
                "type": row.type,
                "stem": row.stem,
                "options": _question_options(row),
                "answer": _json_load(row.answer, row.answer),
                "analysis": row.analysis,
                "extra": _question_extra(row),
            })

    graph = {
        "nodes": [by_id[nid] for nid in order],
        "by_id": by_id,
        "index": index,
        "prereqs": prereqs,
        "dependents": dependents,
        "bank": bank,
        "order": order,
        "subject_ids": subject_ids,
        "_anc": {},
        "_hard_anc": {},
    }
    # 建图即验证无环：坏数据在创建会话前失败，避免诊断过程中随机 500。
    for node_id in order:
        ancestor_set(graph, node_id)
    return graph


def ancestor_set(
    graph: Dict[str, Any], node_id: int, _path: Optional[Set[int]] = None,
) -> Set[int]:
    memo = graph["_anc"]
    if node_id in memo:
        return set(memo[node_id])
    path = set(_path or ())
    if node_id in path:
        raise ValueError("先修图存在环")
    path.add(node_id)
    out: Set[int] = set()
    for edge in graph["prereqs"].get(node_id, []):
        pre_id = int(edge["id"])
        if pre_id in out:
            continue
        out.add(pre_id)
        out.update(ancestor_set(graph, pre_id, path))
    memo[node_id] = frozenset(out)
    return out


def hard_ancestor_set(
    graph: Dict[str, Any], node_id: int, _path: Optional[Set[int]] = None,
) -> Set[int]:
    memo = graph["_hard_anc"]
    if node_id in memo:
        return set(memo[node_id])
    path = set(_path or ())
    if node_id in path:
        raise ValueError("先修图存在环")
    path.add(node_id)
    out: Set[int] = set()
    for edge in graph["prereqs"].get(node_id, []):
        if edge["strength"] != "hard":
            continue
        pre_id = int(edge["id"])
        if pre_id in out:
            continue
        out.add(pre_id)
        out.update(hard_ancestor_set(graph, pre_id, path))
    memo[node_id] = frozenset(out)
    return out


def topo_sort(graph: Dict[str, Any], ids: Iterable[int]) -> List[int]:
    node_set = set(ids)
    indeg = {
        nid: sum(1 for e in graph["prereqs"].get(nid, []) if e["id"] in node_set)
        for nid in node_set
    }
    ready = [nid for nid in node_set if indeg[nid] == 0]
    ready.sort(key=lambda nid: graph["index"].get(nid, 10 ** 9))
    order: List[int] = []
    while ready:
        nid = ready.pop(0)
        order.append(nid)
        for dep in graph["dependents"].get(nid, []):
            if dep not in node_set:
                continue
            indeg[dep] -= 1
            if indeg[dep] == 0:
                ready.append(dep)
                ready.sort(key=lambda x: graph["index"].get(x, 10 ** 9))
    if len(order) != len(node_set):
        raise ValueError("先修子图存在环")
    return order


def is_testable(graph: Dict[str, Any], node_id: int) -> bool:
    return bool(graph["bank"].get(node_id))


def _need_confirm(graph: Dict[str, Any], session: Dict[str, Any], node_id: int) -> int:
    bank_len = len(graph["bank"].get(node_id, []))
    confirm = int(session.get("confirm") or DEFAULT_CONFIRM)
    return max(1, min(confirm, bank_len or 1))


def create_session(
    graph: Dict[str, Any], targets: Iterable[int], *,
    mode: str = "target", limit: Optional[int] = None,
    confirm: Optional[int] = None, seed: str = "default",
    avoid: Optional[Iterable[str]] = None,
) -> Dict[str, Any]:
    target_ids = list(dict.fromkeys(int(t) for t in targets))
    if not target_ids:
        raise ValueError("至少需要一个目标知识点")
    for node_id in target_ids:
        if node_id not in graph["by_id"]:
            raise ValueError(f"未知知识点：{node_id}")
    screen = mode == "screen"
    default_limit = SCREEN_LIMIT if screen else DEFAULT_LIMIT
    question_limit = max(1, min(int(limit if limit is not None else default_limit), 100))
    confirm_count = max(1, min(int(confirm if confirm is not None else DEFAULT_CONFIRM), 10))
    if screen:
        sub_nodes = topo_sort(graph, target_ids)
    else:
        scope = set(target_ids)
        for node_id in target_ids:
            scope.update(ancestor_set(graph, node_id))
        sub_nodes = topo_sort(graph, scope)
    pos = {nid: idx for idx, nid in enumerate(sub_nodes)}
    stack = [nid for nid in target_ids if is_testable(graph, nid)]
    stack.sort(key=lambda nid: pos.get(nid, -1), reverse=True)
    return {
        "targets": target_ids,
        "limit": question_limit,
        "confirm": confirm_count,
        "order": sub_nodes,
        "status": {},
        "stack": stack,
        "answers": [],
        "attempts": {},
        "mode": "screen" if screen else "target",
        "scope": target_ids[:] if screen else None,
        "seed": str(seed),
        "avoid": list(dict.fromkeys(str(x) for x in (avoid or []))),
    }


def _clone_session(session: Dict[str, Any]) -> Dict[str, Any]:
    return {
        **session,
        "targets": list(session.get("targets") or []),
        "order": list(session.get("order") or []),
        "stack": list(session.get("stack") or []),
        "status": {int(k): dict(v) for k, v in (session.get("status") or {}).items()},
        "answers": [dict(a) for a in (session.get("answers") or [])],
        "attempts": {
            int(k): [dict(a) for a in v]
            for k, v in (session.get("attempts") or {}).items()
        },
        "scope": list(session["scope"]) if session.get("scope") is not None else None,
        "avoid": list(session.get("avoid") or []),
    }


def _rank(question: Dict[str, Any]) -> int:
    return DIFF_RANK.get(str(question.get("difficulty") or ""), 1)


def pick_question(
    graph: Dict[str, Any], session: Dict[str, Any],
    node_id: int, attempt: int,
) -> Optional[Dict[str, Any]]:
    all_questions = graph["bank"].get(node_id, [])
    tried = {
        str(a.get("qid"))
        for a in (session.get("attempts") or {}).get(node_id, [])
        if a.get("qid") is not None
    }
    pool = [q for q in all_questions if str(q["qid"]) not in tried]
    if not pool:
        return None
    avoid = set(session.get("avoid") or [])

    def fresh_first(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        fresh = [q for q in rows if str(q["qid"]) not in avoid]
        return fresh or rows

    def pick_rank(rows: List[Dict[str, Any]], ranks: List[int]) -> List[Dict[str, Any]]:
        for rank in ranks:
            hit = [q for q in rows if _rank(q) == rank]
            if hit:
                return fresh_first(hit)
        return fresh_first(rows)

    attempts = (session.get("attempts") or {}).get(node_id, [])
    had_fail = any(a.get("result") != "correct" for a in attempts)
    if attempt <= 1 or not had_fail:
        candidates = pick_rank(pool, [1, 0] if attempt <= 1 else [2, 1, 0])
    else:
        first_qid = str(attempts[0].get("qid")) if attempts else ""
        first = next(
            (q for q in all_questions if str(q["qid"]) == first_qid), None)
        base_rank = _rank(first) if first else 1
        tiers = [
            [q for q in pool if _rank(q) == 0],
            [q for q in pool if _rank(q) == base_rank],
            [q for q in pool if _rank(q) < base_rank],
        ]
        candidates = next((tier for tier in tiers if tier), [])
        if not candidates:
            lowest = min(_rank(q) for q in pool)
            candidates = [q for q in pool if _rank(q) == lowest]
        candidates = fresh_first(candidates)
    if not candidates:
        return None
    idx = min(
        len(candidates) - 1,
        int(_rand01(str(session.get("seed") or "default"),
                    f"{node_id}|{attempt}") * len(candidates)),
    )
    return candidates[idx]


def question_by_id(
    graph: Dict[str, Any], qid: Any, node_id: int,
) -> Optional[Dict[str, Any]]:
    qid_str = str(qid)
    for question in graph["bank"].get(node_id, []):
        if str(question["qid"]) == qid_str:
            return question
    return None


def apply_answer(
    graph: Dict[str, Any], session: Dict[str, Any], node_id: int,
    result: str, *, qid: Optional[Any] = None,
    text: Optional[str] = None, prompt: Optional[str] = None,
) -> Dict[str, Any]:
    if result not in RESULTS:
        raise ValueError("作答结果必须是 correct / wrong / skip")
    if node_id not in graph["by_id"]:
        raise ValueError(f"未知知识点：{node_id}")
    state = _clone_session(session)
    attempts = list(state["attempts"].get(node_id, []))
    question = (
        question_by_id(graph, qid, node_id) if qid is not None
        else pick_question(graph, state, node_id, len(attempts) + 1)
    )
    if qid is not None and question is None:
        return state
    if node_id in state["status"]:
        state["status"].pop(node_id, None)
        state["attempts"][node_id] = []
        attempts = []
    record = {
        "id": node_id,
        "qid": str(question["qid"]) if question else None,
        "result": result,
    }
    if text:
        record["text"] = str(text)[:4000]
    if prompt:
        record["prompt"] = str(prompt)[:1000]
    state["answers"].append(record)
    attempts.append({"qid": record["qid"], "result": result})
    state["attempts"][node_id] = attempts
    fails = sum(1 for a in attempts if a.get("result") != "correct")
    corrects = sum(1 for a in attempts if a.get("result") == "correct")
    need = _need_confirm(graph, state, node_id)
    if result == "correct":
        if fails == 0 and corrects >= need:
            state["status"][node_id] = {"s": "mastered", "src": "direct"}
            ancestors = (
                hard_ancestor_set(graph, node_id)
                if state["mode"] == "screen" else ancestor_set(graph, node_id)
            )
            for ancestor in ancestors:
                state["status"].setdefault(
                    ancestor, {"s": "mastered", "src": "inferred"})
        elif fails > 0:
            state["status"][node_id] = {"s": "shaky", "src": "direct"}
    elif fails == 1 and pick_question(graph, state, node_id, len(attempts) + 1):
        pass
    else:
        state["status"][node_id] = {"s": "weak", "src": "direct"}
        scope = set(state["scope"]) if state.get("scope") else None
        pushed: List[int] = []
        for edge in graph["prereqs"].get(node_id, []):
            pre_id = edge["id"]
            if not is_testable(graph, pre_id):
                continue
            if pre_id in state["status"]:
                continue
            if scope is not None and pre_id not in scope:
                continue
            pushed.append(pre_id)
        pushed_set = set(pushed)
        state["stack"] = pushed + [
            nid for nid in state["stack"] if nid not in pushed_set]
    return state


def replay(
    graph: Dict[str, Any], targets: Iterable[int],
    answers: Iterable[Dict[str, Any]], *,
    mode: str = "target", limit: Optional[int] = None,
    confirm: Optional[int] = None, seed: str = "default",
    avoid: Optional[Iterable[str]] = None,
) -> Dict[str, Any]:
    session = create_session(
        graph, targets, mode=mode, limit=limit, confirm=confirm,
        seed=seed, avoid=avoid,
    )
    for answer in answers or []:
        if not isinstance(answer, dict) or answer.get("exclude"):
            continue
        try:
            node_id = int(answer.get("id"))
        except (TypeError, ValueError):
            continue
        result = answer.get("result")
        if result not in RESULTS:
            continue
        session = apply_answer(
            graph, session, node_id, result,
            qid=answer.get("qid"),
            text=answer.get("text"),
            prompt=answer.get("prompt"),
        )
    return session


def next_question(graph: Dict[str, Any], session: Dict[str, Any]) -> Optional[int]:
    if len(session.get("answers") or []) >= int(session.get("limit") or 0):
        return None
    for node_id in session.get("stack") or []:
        if node_id not in session["status"] and is_testable(graph, node_id):
            return node_id
    return None


def next_item(graph: Dict[str, Any], session: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    node_id = next_question(graph, session)
    if node_id is None:
        return None
    attempt = len((session.get("attempts") or {}).get(node_id, [])) + 1
    question = pick_question(graph, session, node_id, attempt)
    if not question:
        return None
    return {"topic_id": node_id, "question": question, "attempt": attempt}


def status_of(session: Dict[str, Any], node_id: int) -> str:
    status = session["status"].get(node_id)
    if status:
        return status["s"]
    return "weak" if is_unconfirmed(session, node_id) else "unknown"


def is_unconfirmed(session: Dict[str, Any], node_id: int) -> bool:
    attempts = (session.get("attempts") or {}).get(node_id) or []
    if node_id in session["status"] or not attempts:
        return False
    return any(a.get("result") != "correct" for a in attempts)


def summarize(graph: Dict[str, Any], session: Dict[str, Any]) -> Dict[str, Any]:
    nodes = list(session.get("order") or [])
    statuses = {node_id: status_of(session, node_id) for node_id in nodes}
    mastered = [n for n in nodes if statuses[n] == "mastered"]
    shaky = [n for n in nodes if statuses[n] == "shaky"]
    weak = [n for n in nodes if statuses[n] == "weak"]
    unconfirmed = [n for n in weak if is_unconfirmed(session, n)]
    untested = [n for n in nodes if statuses[n] == "unknown"]
    scope = set(session["scope"]) if session.get("scope") else None

    def in_scope(node_id: int) -> bool:
        return scope is None or node_id in scope

    roots: List[Dict[str, Any]] = []
    weak_set = set(weak)
    for node_id in weak:
        if any(edge["id"] in weak_set for edge in graph["prereqs"].get(node_id, [])):
            continue
        unknown = [
            edge["id"] for edge in graph["prereqs"].get(node_id, [])
            if statuses.get(edge["id"]) == "unknown"
        ]
        roots.append({
            **_node_ref(graph, node_id, "weak"),
            "pending_prereqs": [
                _node_ref(graph, nid) for nid in unknown
                if is_testable(graph, nid) and in_scope(nid)
            ],
            "out_of_scope_prereqs": [
                _node_ref(graph, nid) for nid in unknown
                if is_testable(graph, nid) and not in_scope(nid)
            ],
            "external_prereqs": [
                _node_ref(graph, nid) for nid in unknown
                if not is_testable(graph, nid)
            ],
        })

    in_sub = set(nodes)
    reach: Set[int] = set()
    queue: List[int] = [r["id"] for r in roots] + shaky
    reach.update(queue)
    while queue:
        node_id = queue.pop(0)
        for dep in graph["dependents"].get(node_id, []):
            if dep in in_sub and dep not in reach:
                reach.add(dep)
                queue.append(dep)
    root_set = {r["id"] for r in roots}
    target_set = set() if scope is not None else set(session.get("targets") or [])
    topo_pos = {nid: idx for idx, nid in enumerate(nodes)}
    path_ids = [
        nid for nid in nodes
        if nid in reach and statuses[nid] != "mastered"
    ]
    path_ids.sort(key=lambda nid: (
        graph["by_id"].get(nid, {}).get("grade_num") or 0,
        topo_pos[nid],
    ))
    path = [
        {
            **_node_ref(graph, nid, statuses[nid]),
            "is_root": nid in root_set,
            "is_target": nid in target_set,
        }
        for nid in path_ids
    ]

    pending = [
        nid for nid in (session.get("stack") or [])
        if nid not in session["status"] and is_testable(graph, nid)
    ]
    next_node = next_question(graph, session)

    chapters: Dict[str, Dict[str, Any]] = {}
    for node_id in nodes:
        node = graph["by_id"].get(node_id) or {}
        key = str(node.get("chapter") or "未分章节")
        item = chapters.setdefault(key, {
            "chapter": key, "total": 0, "mastered": 0, "shaky": 0,
            "weak": 0, "untested": 0, "weak_ids": [], "shaky_ids": [],
            "_order": len(chapters),
        })
        item["total"] += 1
        status = statuses[node_id]
        if status == "mastered":
            item["mastered"] += 1
        elif status == "shaky":
            item["shaky"] += 1
            item["shaky_ids"].append(node_id)
        elif status == "weak":
            item["weak"] += 1
            item["weak_ids"].append(node_id)
        else:
            item["untested"] += 1
    chapter_list = sorted(
        chapters.values(),
        key=lambda c: (-c["weak"], -c["shaky"], c["_order"]),
    )
    for item in chapter_list:
        item.pop("_order", None)

    return {
        "mode": session.get("mode") or "target",
        "targets": [_node_ref(graph, nid) for nid in session.get("targets") or []],
        "asked": len(session.get("answers") or []),
        "limit": session.get("limit"),
        "finished": next_node is None,
        "limit_reached": (
            len(session.get("answers") or []) >= int(session.get("limit") or 0)
            and bool(pending)
        ),
        "counts": {
            "mastered": len(mastered),
            "shaky": len(shaky),
            "weak": len(weak),
            "unconfirmed": len(unconfirmed),
            "untested": len(untested),
        },
        "mastered": [_node_ref(graph, nid, "mastered") for nid in mastered],
        "shaky": [_node_ref(graph, nid, "shaky") for nid in shaky],
        "weak": [_node_ref(graph, nid, "weak") for nid in weak],
        "unconfirmed": [_node_ref(graph, nid, "weak") for nid in unconfirmed],
        "untested": [_node_ref(graph, nid, "unknown") for nid in untested],
        "roots": roots,
        "path": path,
        "chapters": chapter_list,
        "pending": [_node_ref(graph, nid) for nid in pending],
        "next_topic_id": next_node,
    }


def grade_question(question: Dict[str, Any], answer_text: Any) -> Optional[str]:
    """自动判分；返回 None 表示需要人工/自评。"""
    qtype = str(question.get("type") or "")
    if qtype == "self":
        return None
    reference = question.get("answer")
    if reference in (None, ""):
        return None
    text = _normalize_text(answer_text)
    if not text:
        return "skip"
    extra = question.get("extra") or {}
    if qtype in {"single", "multiple", "judge"}:
        options = question.get("options") or []
        for option in options:
            key = _normalize_text(option.get("key"))
            label = _normalize_text(option.get("text"))
            if text == key or (label and text == label):
                answer_key = _normalize_text(reference)
                if answer_key == key:
                    return "correct"
                if _normalize_text(option.get("text")) == answer_key:
                    return "correct"
        return "wrong"
    accepted = extra.get("accept")
    candidates = [reference]
    if isinstance(accepted, list):
        candidates.extend(accepted)
    normalized = {_normalize_text(x) for x in candidates if x is not None}
    if text in normalized:
        return "correct"
    answer_num, ref_num = _num(answer_text), _num(reference)
    if answer_num is not None and ref_num is not None:
        return "correct" if math.isclose(answer_num, ref_num) else "wrong"
    return "wrong"


def public_question(question: Dict[str, Any]) -> Dict[str, Any]:
    """学生端题目：不包含答案与解析。"""
    return {
        "id": question["qid"],
        "stem": question["stem"],
        "type": question["type"],
        "difficulty": question["difficulty"],
        "options": question.get("options") or [],
        "topic_id": question["topic_id"],
    }
