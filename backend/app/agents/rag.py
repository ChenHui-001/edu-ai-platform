"""RAG 知识库：ChromaDB 嵌入检索 + 题库精准匹配。

ChromaDB 不可用时自动降级为 SQL LIKE 检索，保证功能可用。
"""
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logger import get_logger
from app.models import Attachment, KnowledgePoint, Note, Question
from app.services.attachment_parser import extract_text

logger = get_logger("rag")

_collection = None
_chroma_failed = False
_warmup_started = False
_chroma_ready = False
_warming = False


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


def start_chroma_warmup() -> None:
    """后台预热 Chroma/embedding 模型。

    关键：**不能把首次向量检索放在 AI 请求线程里**。全新容器若没有模型缓存，
    Chroma 会在第一次 query 时下载 ~79MB 模型，AI 答疑请求会被拖到分钟级。
    这里启动后台线程预热；预热期间 search 直接走 SQL 降级，AI 立即返回。
    """
    global _warmup_started
    if _warmup_started:
        return
    _warmup_started = True
    import threading

    def _warm() -> None:
        global _chroma_ready, _warming
        _warming = True
        try:
            col = get_collection()
            if col:
                # 触发 embedding 模型加载/下载（只在后台线程发生）
                col.query(query_texts=["warmup"], n_results=1)
                _chroma_ready = True
                logger.info("ChromaDB embedding 预热完成")
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"ChromaDB 预热失败，继续 SQL 降级: {exc}")
        finally:
            _warming = False

    threading.Thread(target=_warm, name="chroma-warmup", daemon=True).start()


# ---------------------------------------------------------------- 写入
KNOWLEDGE_ID_PREFIX = "kp_"
QUESTION_ID_PREFIX = "q_"
NOTE_ID_PREFIX = "note_"
ATTACHMENT_ID_PREFIX = "att_"
ATTACHMENT_CHUNK_SIZE = 900
ATTACHMENT_MAX_CHUNKS = 40


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


def delete_attachment_index(att_id: int) -> bool:
    """删除附件全部 chunk 向量（附件删除/隐藏/知识点下架后调用）。"""
    col = get_collection()
    if not col:
        return False
    try:
        col.delete(where={"attachment_id": int(att_id)})
        return True
    except Exception as exc:
        logger.warning(f"附件 {att_id} 向量索引删除失败: {exc}")
        return False


def _attachment_chunks(text: str) -> List[str]:
    """按段落/长度切分附件文本，避免单条向量过大。"""
    text = (text or "").strip()
    if not text:
        return []
    chunks: List[str] = []
    buf = ""
    for para in text.replace("\r\n", "\n").split("\n"):
        para = para.strip()
        if not para:
            continue
        if len(para) > ATTACHMENT_CHUNK_SIZE:
            if buf:
                chunks.append(buf)
                buf = ""
            chunks.extend(para[i:i + ATTACHMENT_CHUNK_SIZE]
                          for i in range(0, len(para), ATTACHMENT_CHUNK_SIZE))
            continue
        if len(buf) + len(para) + 1 > ATTACHMENT_CHUNK_SIZE and buf:
            chunks.append(buf)
            buf = para
        else:
            buf = f"{buf}\n{para}" if buf else para
        if len(chunks) >= ATTACHMENT_MAX_CHUNKS:
            break
    if buf and len(chunks) < ATTACHMENT_MAX_CHUNKS:
        chunks.append(buf)
    return chunks[:ATTACHMENT_MAX_CHUNKS]


def _attachment_metadata(
    att: Attachment, kp: KnowledgePoint, index: int,
) -> Dict[str, Any]:
    return {
        "type": "attachment",
        "id": int(att.id),
        "attachment_id": int(att.id),
        "knowledge_point_id": int(kp.id),
        "filename": att.filename or "",
        "path": kp.path or "",
        "name": kp.name,
        "grade_id": int(kp.grade_id),
        "subject_id": int(kp.subject_id),
        "term": int(kp.term or 1),
        "status": kp.status or "published",
        "chunk_index": int(index),
        "ext": (att.filename or "").rsplit(".", 1)[-1].lower() if "." in (att.filename or "") else "",
    }


def index_attachment(
    db: Session, att: Attachment, deadline: Optional[float] = None,
) -> bool:
    """解析附件文本并写入 Chroma（后台调用；失败只告警，不影响上传/下载）。"""
    if not att or not att.id or att.is_temp:
        return False
    kp = db.get(KnowledgePoint, att.biz_id) if att.biz_id else None
    # 只有「已发布知识点 + 学生可见附件」进入 AI 检索：隐藏附件是教师私有资料，
    # 学生/教师共用同一个 RAG 检索通道，不能让隐藏内容进入上下文造成越权泄漏。
    if not kp or not _is_indexable_knowledge(kp) or not att.visible_to_student:
        delete_attachment_index(att.id)
        return False
    if deadline is not None:
        import time as _time
        if _time.monotonic() > deadline:
            return False
    text = extract_text(att.file_path, att.filename)
    chunks = _attachment_chunks(text)
    if not chunks:
        delete_attachment_index(att.id)
        return False
    col = get_collection()
    if not col:
        return False
    if deadline is not None:
        import time as _time
        if _time.monotonic() > deadline:
            return False
    try:
        # 先清理旧 chunk，避免文件更新后旧内容残留
        col.delete(where={"attachment_id": int(att.id)})
        ids = [f"{ATTACHMENT_ID_PREFIX}{int(att.id)}_{i}" for i in range(len(chunks))]
        documents = [f"资料《{att.filename}》\n{c}" for c in chunks]
        metadatas = [_attachment_metadata(att, kp, i) for i in range(len(chunks))]
        col.upsert(ids=ids, documents=documents, metadatas=metadatas)
        return True
    except Exception as exc:
        logger.warning(f"附件 {att.id} 向量化失败: {exc}")
        return False


def index_attachment_by_id(db: Session, att_id: int) -> bool:
    """按 id 索引附件（供 BackgroundTasks/reindex 使用）。"""
    att = db.get(Attachment, att_id)
    return index_attachment(db, att) if att else False


def index_attachment_background(att_id: int) -> bool:
    """后台线程/任务入口：自建 DB session，避免复用已关闭的请求 session。"""
    from app.core.database import SessionLocal

    db = SessionLocal()
    try:
        return index_attachment_by_id(db, att_id)
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"附件 {att_id} 后台索引失败: {exc}")
        return False
    finally:
        db.close()


def reindex_attachments_for_kp(kp_id: int) -> int:
    """知识点发布/移动后重建其附件索引（后台调用，失败不影响业务）。"""
    from app.core.database import SessionLocal

    db = SessionLocal()
    n = 0
    try:
        atts = db.scalars(select(Attachment).where(
            Attachment.biz_type == "knowledge_point",
            Attachment.biz_id == int(kp_id),
            Attachment.is_temp.is_(False),
        )).all()
        for att in atts:
            n += bool(index_attachment(db, att))
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"知识点 {kp_id} 附件索引重建失败: {exc}")
    finally:
        db.close()
    return n


def delete_knowledge_attachments_index(db: Session, kp_id: int) -> int:
    """知识点删除/下架时清理其所有附件向量。"""
    att_ids = db.scalars(select(Attachment.id).where(
        Attachment.biz_type == "knowledge_point",
        Attachment.biz_id == int(kp_id),
    )).all()
    n = 0
    for att_id in att_ids:
        n += bool(delete_attachment_index(att_id))
    return n


def _filter_valid_attachment_results(
    db: Session, results: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """兜底过滤：向量可能残留已删除/隐藏/下架知识点的附件，不能进 LLM 上下文。"""
    filtered: List[Dict[str, Any]] = []
    for r in results:
        meta = r.get("metadata") or {}
        if meta.get("type") != "attachment":
            filtered.append(r)
            continue
        att = db.get(Attachment, meta.get("attachment_id") or meta.get("id") or 0)
        if not att or not att.visible_to_student or att.is_temp:
            continue
        kp = db.get(KnowledgePoint, att.biz_id) if att.biz_id else None
        if not kp or not _is_indexable_knowledge(kp):
            continue
        meta["filename"] = att.filename or ""
        meta["name"] = kp.name
        meta["knowledge_point_id"] = kp.id
        filtered.append(r)
    return filtered


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
    attachment_total = int(db.scalar(
        select(func.count()).select_from(Attachment).join(
            KnowledgePoint, KnowledgePoint.id == Attachment.biz_id).where(
                Attachment.biz_type == "knowledge_point",
                Attachment.is_temp.is_(False),
                Attachment.visible_to_student.is_(True),
                KnowledgePoint.is_active.is_(True),
                KnowledgePoint.status == "published",
            )
    ) or 0)
    stats: Dict[str, Any] = {
        "db_total": db_total,
        "index_count": 0,
        "coverage_percent": _coverage(0, db_total),
        "chroma_available": False,
        "attachment_total": attachment_total,
        "attachment_index_count": 0,
        "attachment_coverage_percent": _coverage(0, attachment_total),
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
    try:
        got_att = col.get(where={"type": "attachment"}, include=[])
        att_ids = got_att.get("ids") or []
        unique_att = set()
        for doc_id in att_ids:
            s = str(doc_id)
            if not s.startswith(ATTACHMENT_ID_PREFIX):
                continue
            tail = s[len(ATTACHMENT_ID_PREFIX):]
            unique_att.add(tail.split("_", 1)[0])
        stats["attachment_index_count"] = len(unique_att)
    except Exception as exc:
        logger.warning(f"读取附件向量索引失败: {exc}")
    stats["coverage_percent"] = _coverage(stats["index_count"], db_total)
    stats["attachment_coverage_percent"] = _coverage(
        stats["attachment_index_count"], attachment_total)
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
        "knowledge": 0, "question": 0, "note": 0, "attachment": 0,
        "failed": 0, "timed_out": False, "purged": 0,
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
        attachment_total = int(db.scalar(
            select(func.count()).select_from(Attachment).join(
                KnowledgePoint, KnowledgePoint.id == Attachment.biz_id).where(
                    Attachment.biz_type == "knowledge_point",
                    Attachment.is_temp.is_(False),
                    Attachment.visible_to_student.is_(True),
                    KnowledgePoint.is_active.is_(True),
                    KnowledgePoint.status == "published",
                )
        ) or 0)
        stats["db_total"] = db_total
        stats["chroma_available"] = bool(col_available)
        stats["index_count"] = int(stats.get("knowledge") or 0)
        stats["coverage_percent"] = _coverage(stats["index_count"], db_total)
        stats["attachment_total"] = attachment_total
        stats["attachment_index_count"] = int(stats.get("attachment") or 0)
        stats["attachment_coverage_percent"] = _coverage(
            stats["attachment_index_count"], attachment_total)
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

    # 知识点附件：解析文本后按 chunk 写入；deadline 到点即停止，避免拖死接口
    att_rows = list(db.scalars(select(Attachment).where(
        Attachment.biz_type == "knowledge_point",
        Attachment.is_temp.is_(False),
        Attachment.visible_to_student.is_(True),
    )).all())
    for att in att_rows:
        if _expired():
            stats["timed_out"] = True
            logger.warning("附件索引超时提前收尾")
            break
        if index_attachment(db, att, deadline=deadline):
            stats["attachment"] += 1

    logger.info(
        f"向量重建{'超时中断' if stats['timed_out'] else '完成'}: "
        f"知识点 {stats['knowledge']} / 题目 {stats['question']} / "
        f"笔记 {stats['note']} / 附件 {stats['attachment']} / "
        f"清理残留 {stats['purged']} / 失败 {stats['failed']}"
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
    effective_types = list(types) if types else ["question", "knowledge", "note", "attachment"]
    if "note" in effective_types and not student_id:
        effective_types = [t for t in effective_types if t != "note"]
        if not effective_types:
            logger.warning("RAG 只请求笔记但未提供 student_id，已跳过以防越权")
            return []

    col = get_collection() if not _warming else None
    if col:
        try:
            return _filter_valid_attachment_results(db, _apply_score_threshold(
                _vector_search(
                    col, query, top_k=top_k,
                    grade_id=grade_id, subject_id=subject_id,
                    types=effective_types, student_id=student_id,
                )))
        except Exception as exc:
            logger.warning(f"向量检索失败，降级 SQL: {exc}")

    return _filter_valid_attachment_results(db, _apply_score_threshold(_sql_search(
        query, db, top_k, knowledge_point_id, grade_id, subject_id,
        effective_types, student_id,
    )))


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
        kind = {"question": "题目", "knowledge": "知识点", "note": "笔记",
                "attachment": "资料"}.get(meta.get("type"), "资料")
        lines.append(f"[{kind}] {r.get('content', '')[:400]}")
    return lines
