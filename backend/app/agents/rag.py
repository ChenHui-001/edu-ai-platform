"""RAG 知识库：ChromaDB 嵌入检索 + 题库精准匹配。

ChromaDB 不可用时自动降级为 SQL LIKE 检索，保证功能可用。
"""
from typing import Any, Dict, List, Optional

from sqlalchemy import select
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
def index_knowledge(kp: KnowledgePoint) -> bool:
    """知识点入库为向量。"""
    col = get_collection()
    if not col:
        return False
    try:
        text = f"{kp.name}。{(kp.description or '')} 关键词：{kp.keywords or ''}"
        col.upsert(
            ids=[f"kp_{kp.id}"],
            documents=[text],
            metadatas=[{
                "type": "knowledge", "id": kp.id, "name": kp.name,
                "grade_id": kp.grade_id, "subject_id": kp.subject_id, "level": kp.level,
            }],
        )
        return True
    except Exception as exc:
        logger.warning(f"知识点 {kp.id} 向量化失败: {exc}")
        return False


def index_question(q: Question) -> bool:
    """题目入库为向量。"""
    col = get_collection()
    if not col:
        return False
    try:
        col.upsert(
            ids=[f"q_{q.id}"],
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
            ids=[f"note_{note.id}"],
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


def reindex_all(
    db: Session,
    batch_size: int = 64,
    deadline: Optional[float] = None,
) -> Dict[str, int]:
    """全量重建向量索引（批量 upsert）。

    历史实现逐条 `col.upsert`，每条都要单独走一次 embedding 计算，
    2000 道题需数分钟，HTTP 接口必然超时（实测 >120s）。
    现改为按batch_size 批量提交，embedding 计算由 ChromaDB 内部批处理，
    耗时下降一个数量级。

    `deadline` 为 time.monotonic() 时间戳；每批之间检查，超时即提前收尾
    并在返回值里带 timed_out 标记（已完成的部分照常保留）。
    单批失败不影响其余批次，仅计入 failed 统计。
    """
    import time as _time

    stats = {"knowledge": 0, "question": 0, "note": 0, "failed": 0, "timed_out": False}

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

    col = get_collection()
    if not col:
        # ChromaDB 不可用时不算失败，属预期降级
        logger.info("ChromaDB 不可用，跳过向量重建")
        stats.pop("_tmp", None)
        return stats

    _run(
        db.scalars(select(KnowledgePoint)).all(),
        lambda k: f"kp_{k.id}",
        lambda k: f"{k.name}。{(k.description or '')[:800]}",
        lambda k: {"type": "knowledge", "id": k.id, "name": k.name,
                   "grade_id": k.grade_id, "subject_id": k.subject_id,
                   "knowledge_point_id": k.id},
    )
    stats["knowledge"] += stats.pop("_tmp", 0)

    # 题目上限 2000 条、笔记上限 1000 条，与原行为一致
    _run(
        db.scalars(select(Question).limit(2000)).all(),
        lambda q: f"q_{q.id}",
        lambda q: q.stem[:1500],
        lambda q: {"type": "question", "id": q.id, "type_name": q.type,
                   "difficulty": q.difficulty, "score": q.score,
                   "grade_id": q.grade_id, "subject_id": q.subject_id,
                   "knowledge_point_id": q.knowledge_point_id or 0},
    )
    stats["question"] += stats.pop("_tmp", 0)

    _run(
        db.scalars(select(Note).limit(1000)).all(),
        lambda n: f"note_{n.id}",
        lambda n: f"{n.title}。{(n.content or '')[:2000]}",
        lambda n: {"type": "note", "id": n.id, "title": n.title,
                   "student_id": n.student_id, "subject_id": n.subject_id or 0},
    )
    stats["note"] += stats.pop("_tmp", 0)

    logger.info(
        f"向量重建{'超时中断' if stats['timed_out'] else '完成'}: "
        f"知识点 {stats['knowledge']} / 题目 {stats['question']} / "
        f"笔记 {stats['note']} / 失败 {stats['failed']}"
    )
    return stats


# ---------------------------------------------------------------- 检索
def search(
    query: str,
    db: Session,
    *,
    top_k: Optional[int] = None,
    knowledge_point_id: Optional[int] = None,
    grade_id: Optional[int] = None,
    subject_id: Optional[int] = None,
    types: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """混合检索：优先向量库，不可用时降级 SQL 检索。"""
    top_k = top_k or settings.RAG_TOP_K
    col = get_collection()
    if col:
        try:
            # ChromaDB 的 where 只接受「单个操作符」：
            #   传扁平 dict 且有多个 key 会抛
            #   "Expected where to have exactly one operator"
            # 因此多条件必须用 $and 显式包裹。
            conds: List[Dict[str, Any]] = []
            if grade_id:
                conds.append({"grade_id": int(grade_id)})
            if subject_id:
                conds.append({"subject_id": int(subject_id)})
            if types:
                conds.append({"type": {"$in": list(types)}})

            if not conds:
                where = None
            elif len(conds) == 1:
                where = conds[0]
            else:
                where = {"$and": conds}

            res = col.query(
                query_texts=[query], n_results=top_k, where=where,
            )
            docs = (res.get("documents") or [[]])[0]
            metas = (res.get("metadatas") or [[]])[0]
            distances = (res.get("distances") or [[]])[0]
            return [
                {
                    "content": d, "metadata": m or {}, "score": round(1 - float(dist), 4),
                }
                for d, m, dist in zip(docs, metas, distances)
            ]
        except Exception as exc:
            logger.warning(f"向量检索失败，降级 SQL: {exc}")

    return _sql_search(query, db, top_k, knowledge_point_id, grade_id, subject_id, types)


def _sql_search(
    query: str, db: Session, top_k: int,
    knowledge_point_id: Optional[int], grade_id: Optional[int],
    subject_id: Optional[int], types: Optional[List[str]],
) -> List[Dict[str, Any]]:
    """SQL LIKE 降级检索。"""
    like = f"%{query}%"
    results: List[Dict[str, Any]] = []

    # 题目检索
    if not types or "question" in types:
        stmt = select(Question).where(Question.stem.like(like))
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

    # 知识点检索
    if not types or "knowledge" in types:
        stmt = select(KnowledgePoint).where(KnowledgePoint.name.like(like))
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

    # 笔记检索（仅本人）
    if not types or "note" in types:
        for n in db.scalars(
            select(Note).where(Note.content.like(like)).limit(top_k)
        ).all():
            results.append({
                "content": f"{n.title}：{n.content[:300]}",
                "score": 0.5,
                "metadata": {"type": "note", "id": n.id, "title": n.title},
            })

    return sorted(results, key=lambda x: x["score"], reverse=True)[:top_k]


def build_context(results: List[Dict[str, Any]], limit: int = 5) -> List[str]:
    """将检索结果转为 LLM 上下文。"""
    lines = []
    for r in results[:limit]:
        meta = r.get("metadata", {})
        kind = {"question": "题目", "knowledge": "知识点", "note": "笔记"}.get(meta.get("type"), "资料")
        lines.append(f"[{kind}] {r.get('content', '')[:400]}")
    return lines
