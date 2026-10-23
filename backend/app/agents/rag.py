"""RAG 知识库：ChromaDB 嵌入检索 + 题库精准匹配。

ChromaDB 不可用时自动降级为 SQL LIKE 检索，保证功能可用。
"""
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logger import get_logger
from app.models import KnowledgePoint, Note, Question

logger = get_logger("rag")

_collection = None
_chroma_failed = False


def get_collection():
    """懒加载 ChromaDB 集合。"""
    global _collection, _chroma_failed
    if _collection is not None or _chroma_failed:
        return _collection
    try:
        import chromadb
        from chromadb.config import Settings as ChromaSettings

        client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIR,
            settings=ChromaSettings(anonymized_telemetry=False, allow_reset=True),
        )
        _collection = client.get_or_create_collection(
            name=settings.CHROMA_COLLECTION,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info("ChromaDB 向量库就绪")
    except Exception as exc:
        _chroma_failed = True
        logger.warning(f"ChromaDB 不可用，RAG 降级为 SQL 检索: {exc}")
    return _collection


# ---------------------------------------------------------------- 写入
KNOWLEDGE_ID_PREFIX = "kp_"
QUESTION_ID_PREFIX = "q_"
NOTE_ID_PREFIX = "note_"


def _delete_index_ids(ids: List[str], label: str) -> bool:
    """从向量库删除索引（异常只告警不阻断业务删除）。"""
    col = get_collection()
    if not col:
        return False
    try:
        col.delete(ids=list(ids))
        return True
    except Exception as exc:
        logger.warning(f"{label} 向量索引删除失败: {exc}")
        return False


def delete_knowledge_index(kp_id: int) -> bool:
    """删除知识点向量索引（知识点删除/下架后调用）。"""
    try:
        return _delete_index_ids(
            [f"{KNOWLEDGE_ID_PREFIX}{int(kp_id)}"], f"知识点 {kp_id}")
    except (TypeError, ValueError):
        return False


def delete_question_index(q_id: int) -> bool:
    """删除题目向量索引（题目删除/下架后调用）。"""
    try:
        return _delete_index_ids(
            [f"{QUESTION_ID_PREFIX}{int(q_id)}"], f"题目 {q_id}")
    except (TypeError, ValueError):
        return False


def delete_note_index(note_id: int) -> bool:
    """删除笔记向量索引（笔记删除后调用）。"""
    try:
        return _delete_index_ids(
            [f"{NOTE_ID_PREFIX}{int(note_id)}"], f"笔记 {note_id}")
    except (TypeError, ValueError):
        return False


def _knowledge_document(kp: KnowledgePoint) -> str:
    """知识点向量文档。写入与全量重建共用，避免两条路径字段漂移。"""
    return f"{kp.name}。{(kp.description or '')[:800]} 关键词：{kp.keywords or ''}"


def _knowledge_metadata(kp: KnowledgePoint) -> Dict[str, Any]:
    """知识点向量 metadata（契约字段：path/status/term/textbook_version 等）。"""
    return {
        "type": "knowledge",
        "id": int(kp.id),
        "knowledge_point_id": int(kp.id),
        "name": kp.name,
        "path": kp.path or "",
        "grade_id": int(kp.grade_id),
        "subject_id": int(kp.subject_id),
        "term": int(kp.term or 1),
        "status": kp.status or "published",
        "level": int(kp.level or 1),
        "textbook_version": kp.textbook_version or "",
    }


def _is_indexable_knowledge(kp: KnowledgePoint) -> bool:
    """只索引 published 且未停用的知识点（draft/archived 不进语义检索）。"""
    return bool(getattr(kp, "is_active", True)) and (
        (getattr(kp, "status", "published") or "published") == "published")


def index_knowledge(kp: KnowledgePoint) -> bool:
    """知识点入库为向量。

    只索引 published 节点；节点从 published 变为 draft/archived 时顺带删除旧向量，
    否则语义检索会命中已下架内容（删除接口只是兜底，状态变更同样要生效）。
    """
    if not _is_indexable_knowledge(kp):
        deleted = delete_knowledge_index(kp.id)
        logger.info(
            f"知识点 {kp.id} 非 published，跳过索引"
            f"{'（已清理旧向量）' if deleted else ''}")
        return False
    col = get_collection()
    if not col:
        return False
    try:
        col.upsert(
            ids=[f"{KNOWLEDGE_ID_PREFIX}{kp.id}"],
            documents=[_knowledge_document(kp)],
            metadatas=[_knowledge_metadata(kp)],
        )
        return True
    except Exception as exc:
        logger.warning(f"知识点 {kp.id} 向量化失败: {exc}")
        return False


def index_question(q: Question) -> bool:
    """题目入库为向量（只索引 published；下架/草稿清理旧向量）。"""
    if (getattr(q, "status", "published") or "published") != "published":
        delete_question_index(q.id)
        return False
    col = get_collection()
    if not col:
        return False
    try:
        col.upsert(
            ids=[f"{QUESTION_ID_PREFIX}{q.id}"],
            documents=[q.stem[:1500]],
            metadatas=[{
                "type": "question", "id": q.id, "type_name": q.type,
                "difficulty": q.difficulty, "score": q.score,
                "grade_id": q.grade_id, "subject_id": q.subject_id,
                "knowledge_point_id": q.knowledge_point_id or 0,
            }],
        )
        return True
    except Exception as exc:
        logger.warning(f"题目 {q.id} 向量化失败: {exc}")
        return False


def index_note(note: Note) -> bool:
    """笔记入库为向量。"""
    col = get_collection()
    if not col:
        return False
    try:
        col.upsert(
            ids=[f"{NOTE_ID_PREFIX}{note.id}"],
            documents=[f"{note.title}。{note.content[:2000]}"],
            metadatas=[{
                "type": "note", "id": note.id, "title": note.title,
                "student_id": note.student_id, "subject_id": note.subject_id or 0,
            }],
        )
        return True
    except Exception as exc:
        logger.warning(f"笔记 {note.id} 向量化失败: {exc}")
        return False


def _coverage(index_count: int, db_total: int) -> float:
    """索引覆盖率（百分比，保留 1 位小数）。db_total=0 视为全覆盖。"""
    if db_total <= 0:
        return 100.0 if index_count <= 0 else 0.0
    percent = index_count / db_total * 100
    return round(min(100.0, max(0.0, percent)), 1)


def _purge_stale_knowledge(col, valid_ids) -> int:
    """清理知识点残留向量（已删除/下架的 kp_ 文档）。返回清理条数。"""
    try:
        got = col.get(where={"type": "knowledge"}, include=[])
    except Exception as exc:
        logger.warning(f"读取知识点向量失败，跳过残留清理: {exc}")
        return 0
    stale: List[str] = []
    for doc_id in got.get("ids") or []:
        text = str(doc_id)
        if not text.startswith(KNOWLEDGE_ID_PREFIX):
            continue
        try:
            if int(text[len(KNOWLEDGE_ID_PREFIX):]) not in valid_ids:
                stale.append(text)
        except ValueError:
            continue
    if not stale:
        return 0
    try:
        col.delete(ids=stale)
        logger.info(f"清理知识点残留向量 {len(stale)} 条")
        return len(stale)
    except Exception as exc:
        logger.warning(f"清理知识点残留向量失败: {exc}")
        return 0


def knowledge_index_stats(db: Session) -> Dict[str, Any]:
    """知识点 RAG 索引状态（GET /edu/knowledge/rag-status 使用）。"""
    db_total = int(db.scalar(
        select(func.count()).select_from(KnowledgePoint).where(
            KnowledgePoint.is_active.is_(True),
            KnowledgePoint.status == "published",
        )
    ) or 0)
    stats: Dict[str, Any] = {
        "db_total": db_total,
        "index_count": 0,
        "coverage_percent": _coverage(0, db_total),
        "chroma_available": False,
    }
    col = get_collection()
    if not col:
        return stats
    stats["chroma_available"] = True
    try:
        got = col.get(where={"type": "knowledge"}, include=[])
        ids = got.get("ids") or []
        stats["index_count"] = len({
            str(i) for i in ids if str(i).startswith(KNOWLEDGE_ID_PREFIX)
        })
    except Exception as exc:
        logger.warning(f"读取知识点向量索引失败: {exc}")
        return stats
    stats["coverage_percent"] = _coverage(stats["index_count"], db_total)
    return stats


def reindex_all(
    db: Session,
    batch_size: int = 64,
    deadline: Optional[float] = None,
) -> Dict[str, Any]:
    """全量重建向量索引（批量 upsert）。

    历史实现逐条 `col.upsert`，每条都要单独走一次 embedding 计算，
    2000 道题需数分钟，HTTP 接口必然超时（实测 >120s）。
    现改为按batch_size 批量提交，embedding 计算由 ChromaDB 内部批处理，
    耗时下降一个数量级。

    `deadline` 为 time.monotonic() 时间戳；每批之间检查，超时即提前收尾
    并在返回值里带 timed_out 标记（已完成的部分照常保留）。
    单批失败不影响其余批次，仅计入 failed 统计。

    重建范围（与写入路径一致）：published 且未停用的知识点、published 题目、
    未删除笔记。知识点阶段完整跑完时会清理「已删除/下架」知识点的残留向量，
    使索引与 DB 对齐；返回值在原有 stats 字段外追加
    `db_total/index_count/coverage_percent/chroma_available/purged`。
    """
    import time as _time

    stats: Dict[str, Any] = {
        "knowledge": 0, "question": 0, "note": 0, "failed": 0,
        "timed_out": False, "purged": 0,
    }

    def _expired() -> bool:
        return deadline is not None and _time.monotonic() > deadline

    def _upsert_batch(col, ids, documents, metadatas) -> int:
        """批量写入，返回成功条数。单批异常时降级为逐条重试。"""
        if not ids:
            return 0
        try:
            col.upsert(ids=ids, documents=documents, metadatas=metadatas)
            return len(ids)
        except Exception as exc:
            logger.warning(f"批量向量化失败({len(ids)} 条)，降级逐条: {exc}")
            ok_n = 0
            for i, doc_id in enumerate(ids):
                try:
                    col.upsert(ids=[doc_id], documents=[documents[i]],
                               metadatas=[metadatas[i]])
                    ok_n += 1
                except Exception:
                    stats["failed"] += 1
            return ok_n

    def _run(rows, id_fn, doc_fn, meta_fn):
        """按批处理一组记录，deadline 到点即停。"""
        for i in range(0, len(rows), batch_size):
            if _expired():
                stats["timed_out"] = True
                logger.warning(
                    f"向量重建超时提前收尾：已完成 {i}/{len(rows)}")
                return
            chunk = rows[i:i + batch_size]
            stats["_tmp"] = stats.get("_tmp", 0) + _upsert_batch(
                col, [id_fn(x) for x in chunk],
                [doc_fn(x) for x in chunk],
                [meta_fn(x) for x in chunk],
            )

    def _finish(col_available: bool) -> Dict[str, Any]:
        stats.pop("_tmp", None)
        db_total = int(db.scalar(
            select(func.count()).select_from(KnowledgePoint).where(
                KnowledgePoint.is_active.is_(True),
                KnowledgePoint.status == "published",
            )
        ) or 0)
        stats["db_total"] = db_total
        stats["chroma_available"] = bool(col_available)
        stats["index_count"] = int(stats.get("knowledge") or 0)
        stats["coverage_percent"] = _coverage(stats["index_count"], db_total)
        return stats

    col = get_collection()
    if not col:
        # ChromaDB 不可用时不算失败，属预期降级
        logger.info("ChromaDB 不可用，跳过向量重建")
        return _finish(False)

    kp_rows = list(db.scalars(select(KnowledgePoint).where(
        KnowledgePoint.is_active.is_(True),
        KnowledgePoint.status == "published",
    )).all())
    _run(kp_rows, lambda k: f"{KNOWLEDGE_ID_PREFIX}{k.id}",
         _knowledge_document, _knowledge_metadata)
    stats["knowledge"] += stats.pop("_tmp", 0)
    # 重建即真源：知识点阶段完整跑完时清理已删除/下架节点的残留向量
    if not stats["timed_out"]:
        stats["purged"] += _purge_stale_knowledge(
            col, {int(k.id) for k in kp_rows})

    # 题目上限 2000 条、笔记上限 1000 条，与原行为一致
    _run(
        db.scalars(select(Question).where(
            Question.status == "published").limit(2000)).all(),
        lambda q: f"{QUESTION_ID_PREFIX}{q.id}",
        lambda q: q.stem[:1500],
        lambda q: {"type": "question", "id": q.id, "type_name": q.type,
                   "difficulty": q.difficulty, "score": q.score,
                   "grade_id": q.grade_id, "subject_id": q.subject_id,
                   "knowledge_point_id": q.knowledge_point_id or 0},
    )
    stats["question"] += stats.pop("_tmp", 0)

    _run(
        db.scalars(select(Note).limit(1000)).all(),
        lambda n: f"{NOTE_ID_PREFIX}{n.id}",
        lambda n: f"{n.title}。{(n.content or '')[:2000]}",
        lambda n: {"type": "note", "id": n.id, "title": n.title,
                   "student_id": n.student_id, "subject_id": n.subject_id or 0},
    )
    stats["note"] += stats.pop("_tmp", 0)

    logger.info(
        f"向量重建{'超时中断' if stats['timed_out'] else '完成'}: "
        f"知识点 {stats['knowledge']} / 题目 {stats['question']} / "
        f"笔记 {stats['note']} / 清理残留 {stats['purged']} / 失败 {stats['failed']}"
    )
    return _finish(True)


# ---------------------------------------------------------------- 检索
def _score_threshold() -> float:
    """检索结果最低相关度（settings.RAG_SCORE_THRESHOLD，默认 0.3）。"""
    try:
        return float(settings.RAG_SCORE_THRESHOLD or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _apply_score_threshold(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """过滤低于阈值的结果：低相关度内容不应进入 LLM 上下文/搜索结果。"""
    threshold = _score_threshold()
    if threshold <= 0:
        return results
    return [
        r for r in results
        if float(r.get("score") or 0.0) >= threshold
    ]


def search(
    query: str,
    db: Session,
    *,
    top_k: Optional[int] = None,
    knowledge_point_id: Optional[int] = None,
    grade_id: Optional[int] = None,
    subject_id: Optional[int] = None,
    types: Optional[List[str]] = None,
    student_id: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """混合检索：优先向量库，不可用时降级 SQL 检索。

    `student_id`：发起检索的用户 id，用于**笔记**的归属过滤。笔记是学生私密
    数据，未传 student_id（系统级检索）时必须跳过 note 类型 —— 宁可少检索
    一种类型，也不能把他人笔记塞进 LLM 上下文（P1 跨用户泄漏）。
    """
    top_k = top_k or settings.RAG_TOP_K

    # 归一化检索类型：未指定 = 全部。note 只允许在已知归属者时参与检索。
    effective_types = list(types) if types else ["question", "knowledge", "note"]
    if "note" in effective_types and not student_id:
        effective_types = [t for t in effective_types if t != "note"]
        if not effective_types:
            logger.warning("RAG 只请求笔记但未提供 student_id，已跳过以防越权")
            return []

    col = get_collection()
    if col:
        try:
            return _apply_score_threshold(_vector_search(
                col, query, top_k=top_k,
                grade_id=grade_id, subject_id=subject_id,
                types=effective_types, student_id=student_id,
            ))
        except Exception as exc:
            logger.warning(f"向量检索失败，降级 SQL: {exc}")

    return _apply_score_threshold(_sql_search(
        query, db, top_k, knowledge_point_id, grade_id, subject_id,
        effective_types, student_id,
    ))


def _vector_search(
    col,
    query: str,
    *,
    top_k: int,
    grade_id: Optional[int],
    subject_id: Optional[int],
    types: List[str],
    student_id: Optional[int],
) -> List[Dict[str, Any]]:
    """向量检索。

    ChromaDB 的 where 只接受「单个操作符」：传扁平 dict 且有多个 key 会抛
    "Expected where to have exactly one operator"，因此多条件必须用 $and 包裹。

    笔记与题目/知识点在同一个 collection，但只有 note 的 metadata 带 student_id。
    若把 student_id 条件与 type 条件写在同一个 where 里，题目/知识点会因缺少
    该字段被一并过滤掉。因此按「非笔记」/「本人笔记」分组查询，再合并排序。
    """
    groups: List[tuple] = []
    non_note = [t for t in types if t != "note"]
    if non_note:
        groups.append((non_note, None))
    if "note" in types and student_id:
        groups.append((["note"], int(student_id)))

    merged: List[Dict[str, Any]] = []
    for group_types, note_owner in groups:
        conds: List[Dict[str, Any]] = []
        # 笔记 metadata 没有 grade_id，硬加会过滤掉全部笔记；subject_id 两者都有
        if grade_id and note_owner is None:
            conds.append({"grade_id": int(grade_id)})
        if subject_id:
            conds.append({"subject_id": int(subject_id)})
        conds.append({"type": {"$in": list(group_types)}})
        if note_owner is not None:
            conds.append({"student_id": note_owner})
        where = conds[0] if len(conds) == 1 else {"$and": conds}

        res = col.query(query_texts=[query], n_results=top_k, where=where)
        docs = (res.get("documents") or [[]])[0]
        metas = (res.get("metadatas") or [[]])[0]
        distances = (res.get("distances") or [[]])[0]
        merged.extend(
            {
                "content": d, "metadata": m or {},
                "score": round(1 - float(dist), 4),
            }
            for d, m, dist in zip(docs, metas, distances)
        )

    merged.sort(key=lambda x: x["score"], reverse=True)
    return _apply_score_threshold(merged)[:top_k]


def _sql_search(
    query: str, db: Session, top_k: int,
    knowledge_point_id: Optional[int], grade_id: Optional[int],
    subject_id: Optional[int], types: Optional[List[str]],
    student_id: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """SQL LIKE 降级检索。"""
    like = f"%{query}%"
    results: List[Dict[str, Any]] = []

    # 题目检索（只检索已发布题目，与索引写入范围一致）
    if not types or "question" in types:
        stmt = select(Question).where(
            Question.stem.like(like),
            Question.status == "published",
        )
        if knowledge_point_id:
            stmt = stmt.where(Question.knowledge_point_id == knowledge_point_id)
        if grade_id:
            stmt = stmt.where(Question.grade_id == grade_id)
        if subject_id:
            stmt = stmt.where(Question.subject_id == subject_id)
        for q in db.scalars(stmt.limit(top_k)).all():
            results.append({
                "content": q.stem, "score": 0.6,
                "metadata": {"type": "question", "id": q.id, "type_name": q.type,
                             "difficulty": q.difficulty, "subject_id": q.subject_id},
            })

    # 知识点检索（只检索 published + 激活节点，与索引写入范围一致）
    if not types or "knowledge" in types:
        stmt = select(KnowledgePoint).where(
            KnowledgePoint.name.like(like),
            KnowledgePoint.is_active.is_(True),
            KnowledgePoint.status == "published",
        )
        if knowledge_point_id:
            stmt = stmt.where(KnowledgePoint.id == knowledge_point_id)
        if grade_id:
            stmt = stmt.where(KnowledgePoint.grade_id == grade_id)
        if subject_id:
            stmt = stmt.where(KnowledgePoint.subject_id == subject_id)
        for kp in db.scalars(stmt.limit(top_k)).all():
            results.append({
                "content": f"{kp.name}：{kp.description or ''}",
                "score": 0.7,
                "metadata": {"type": "knowledge", "id": kp.id, "name": kp.name,
                             "subject_id": kp.subject_id},
            })

    # 笔记检索（强制本人）：必须带 student_id 过滤，否则会把别人的私密笔记
    # 当成参考资料返回。未提供 student_id（系统级检索）时直接跳过。
    if (not types or "note" in types) and student_id:
        for n in db.scalars(
            select(Note).where(
                Note.content.like(like),
                Note.student_id == int(student_id),
            ).limit(top_k)
        ).all():
            results.append({
                "content": f"{n.title}：{n.content[:300]}",
                "score": 0.5,
                "metadata": {"type": "note", "id": n.id, "title": n.title},
            })

    results.sort(key=lambda x: x["score"], reverse=True)
    return _apply_score_threshold(results)[:top_k]


def build_context(results: List[Dict[str, Any]], limit: int = 5) -> List[str]:
    """将检索结果转为 LLM 上下文。"""
    lines = []
    for r in results[:limit]:
        meta = r.get("metadata", {})
        kind = {"question": "题目", "knowledge": "知识点", "note": "笔记"}.get(meta.get("type"), "资料")
        lines.append(f"[{kind}] {r.get('content', '')[:400]}")
    return lines
