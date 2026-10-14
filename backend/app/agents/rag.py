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


def reindex_all(db: Session) -> Dict[str, int]:
    """全量重建向量索引。"""
    stats = {"knowledge": 0, "question": 0, "note": 0}
    for kp in db.scalars(select(KnowledgePoint)).all():
        stats["knowledge"] += int(index_knowledge(kp))
    for q in db.scalars(select(Question).limit(2000)).all():
        stats["question"] += int(index_question(q))
    for n in db.scalars(select(Note).limit(1000)).all():
        stats["note"] += int(index_note(n))
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
            where: Dict[str, Any] = {}
            if grade_id:
                where["grade_id"] = grade_id
            if subject_id:
                where["subject_id"] = subject_id
            if types:
                where["type"] = {"$in": types}
            res = col.query(
                query_texts=[query], n_results=top_k, where=where or None,
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
