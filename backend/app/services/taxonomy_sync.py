"""Pinned upstream synchronization with previews, backups and taxonomy-only restore."""
import hashlib
import io
import json
import threading
import zipfile
from datetime import datetime
from pathlib import Path

import httpx
from fastapi import HTTPException
from sqlalchemy import delete, select, text

from app.core.config import settings
from app.core.exception import BusinessException, NotFoundException
from app.models import Grade, KnowledgePoint, KnowledgePrerequisite, Question, QuestionKnowledge, Subject, TaxonomySyncRun
from app.services.math_taxonomy_import import (
    SOURCE, _get_or_create_grade, _get_or_create_subject, _new_node,
    _question_fingerprint, _stable_key, parse_chapter,
)
from app.services.taxonomy_source import (
    acyclic, bundle_digest, quality_errors, question_fields, read_source, topic_fields,
)
from app.utils.common import dictify

_sync_lock = threading.Lock()


def sync_dir():
    path = Path(settings.EXPORT_DIR).resolve().parent / "taxonomy-sync"
    path.mkdir(parents=True, exist_ok=True)
    return path


def fetch_source(ref):
    with httpx.Client(timeout=30, follow_redirects=False) as client:
        response = client.get(f"https://api.github.com/repos/xiaoyang111222/cn-math-taxonomy/commits/{ref}",
                              headers={"Accept": "application/vnd.github+json", "User-Agent": "EduMathSync"})
        response.raise_for_status()
        commit = response.json()["sha"]
        if len(commit) != 40 or any(character not in "0123456789abcdef" for character in commit):
            raise BusinessException("上游版本标识异常")
        buffer = io.BytesIO()
        with client.stream("GET", f"https://codeload.github.com/xiaoyang111222/cn-math-taxonomy/zip/{commit}") as stream:
            stream.raise_for_status()
            for chunk in stream.iter_bytes():
                buffer.write(chunk)
                if buffer.tell() > 40 * 1024 * 1024:
                    raise BusinessException("上游压缩包超过大小限制")
    folder = sync_dir() / commit
    folder.mkdir(exist_ok=True)
    targets = {"topics.json", "questions.json", "dependencies.json", "LICENSE"}
    with zipfile.ZipFile(buffer) as archive:
        for member in archive.infolist():
            parts = member.filename.split("/")
            if parts[-1] not in targets or member.file_size > 25 * 1024 * 1024:
                continue
            if parts[-1] != "LICENSE" and len(parts) != 3:
                continue
            destination = folder / ("data" if parts[-1] != "LICENSE" else "")
            destination.mkdir(exist_ok=True)
            (destination / parts[-1]).write_bytes(archive.read(member))
    for name in targets:
        path = folder / ("data" if name != "LICENSE" else "") / name
        if not path.is_file():
            raise BusinessException(f"上游缺少 {name}")
    return commit, folder


def source_data(folder):
    return read_source(folder)


def dataset_snapshot(db):
    math_subjects = select(Subject.id).where(Subject.name == "数学")
    kp_ids = select(KnowledgePoint.id).where(KnowledgePoint.external_source == SOURCE,
                                           KnowledgePoint.subject_id.in_(math_subjects))
    question_ids = select(Question.id).where(Question.external_source == SOURCE,
                                            Question.subject_id.in_(math_subjects))
    return {name: [dictify(item) for item in db.scalars(statement).all()]
            for name, statement in (
                ("knowledge", select(KnowledgePoint).where(KnowledgePoint.id.in_(kp_ids)).order_by(KnowledgePoint.id)),
                ("questions", select(Question).where(Question.id.in_(question_ids)).order_by(Question.id)),
                ("links", select(QuestionKnowledge).where(QuestionKnowledge.question_id.in_(question_ids))
                 .order_by(QuestionKnowledge.id)),
                ("edges", select(KnowledgePrerequisite).where(KnowledgePrerequisite.source == SOURCE,
                    KnowledgePrerequisite.topic_kp_id.in_(kp_ids)).order_by(KnowledgePrerequisite.id)))}


def digest_snapshot(snapshot):
    return hashlib.sha256(json.dumps(snapshot, sort_keys=True, default=str).encode()).hexdigest()


def preview_report(db, folder):
    topics, questions, edges = source_data(folder)
    before = dataset_snapshot(db)
    old_topics = {item["external_id"]: item for item in before["knowledge"] if item["level"] == 3}
    old_questions = {item["external_id"]: item for item in before["questions"]}
    ids = {str(item["id"]) for item in topics}
    qids = {str(item["id"]) for item in questions}
    old_nodes = {item["id"]: item for item in before["knowledge"]}
    grade_numbers = dict(db.execute(select(Grade.id, Grade.grade_num)).all())
    def topic_changed(item):
        existing = old_topics[str(item["id"])]
        volume, chapter = parse_chapter(item.get("chapter") or "")
        term = topic_fields(item)["term"]
        expected_parent = "cnm_c:" + _stable_key(int(item["grade"]), term, volume, chapter)
        return (any(existing.get(key) != value for key, value in topic_fields(item).items())
                or grade_numbers.get(existing["grade_id"]) != int(item["grade"])
                or old_nodes.get(existing["parent_id"], {}).get("external_id") != expected_parent
                or not existing["is_active"] or existing["status"] != "published")
    updated_topics = [item for item in topics if str(item["id"]) in old_topics and topic_changed(item)]
    topics_by_id = {str(item["id"]): item for item in topics}
    def question_changed(item):
        existing = old_questions[str(item["id"])]
        return (any(existing.get(key) != value for key, value in question_fields(item).items())
                or old_nodes.get(existing["knowledge_point_id"], {}).get("external_id") != str(item["topicId"])
                or grade_numbers.get(existing["grade_id"]) != int(topics_by_id[str(item["topicId"])]["grade"])
                or existing["status"] != "published" or existing["bank_type"] != "public")
    updated_questions = [item for item in questions if str(item["id"]) in old_questions and question_changed(item)]
    errors = quality_errors(topics, questions, edges)
    old_edges = {(old_nodes[item["topic_kp_id"]]["external_id"],
                  old_nodes[item["prerequisite_kp_id"]]["external_id"]): item for item in before["edges"]
                 if item["topic_kp_id"] in old_nodes and item["prerequisite_kp_id"] in old_nodes}
    new_edges = {(str(item["topicId"]), str(item["prerequisiteId"])): item for item in edges}
    return {"knowledge": len(topics), "questions": len(questions), "edges": len(edges),
            "added_knowledge": len(ids - old_topics.keys()), "updated_knowledge": len(updated_topics),
            "archived_knowledge": len(old_topics.keys() - ids),
            "added_questions": len(qids - old_questions.keys()), "updated_questions": len(updated_questions),
            "archived_questions": len(old_questions.keys() - qids),
            "added_edges": len(new_edges.keys() - old_edges.keys()),
            "updated_edges": sum(any(old_edges[pair].get(key) != new_edges[pair].get(key)
                                      for key in ("strength", "reason"))
                                 for pair in new_edges.keys() & old_edges.keys()),
            "removed_edges": len(old_edges.keys() - new_edges.keys()),
            "errors": errors[:50], "license": "CC BY-NC 4.0", "base_digest": digest_snapshot(before),
            "bundle_digest": bundle_digest(folder)}


def run_out(item):
    return {"id": item.id, "action": item.action, "source_commit": item.source_commit,
            "status": item.status, "report": json.loads(item.report), "created_at": item.created_at}


def history(db):
    return [run_out(item) for item in db.scalars(
        select(TaxonomySyncRun).order_by(TaxonomySyncRun.id.desc()).limit(50)).all()]


def preview(db, user, ref):
    user_id = user.id
    try:
        commit, folder = fetch_source(ref)
        report = preview_report(db, folder)
        item = TaxonomySyncRun(user_id=user.id, action="preview", source_commit=commit,
                               report=json.dumps(report, ensure_ascii=False), bundle_path=str(folder))
        db.add(item)
        db.commit()
        return run_out(item)
    except Exception as exc:
        db.rollback()
        db.add(TaxonomySyncRun(user_id=user_id, action="preview", source_commit="", status="failed",
                              report=json.dumps({"errors": [f"读取上游失败（{type(exc).__name__}）"], "ref": ref},
                                                ensure_ascii=False)))
        db.commit()
        if isinstance(exc, BusinessException):
            raise
        raise BusinessException(f"读取上游失败（{type(exc).__name__}），请重试")


def normalize_source(db, folder, owner_id):
    topics, questions, edges = source_data(folder)
    before = dataset_snapshot(db)
    nodes = {item.external_id: item for item in db.scalars(
        select(KnowledgePoint).where(KnowledgePoint.external_source == SOURCE)).all()}
    selected_ids = set()
    grade_cache, subject_cache, chapter_counts = {}, {}, {}
    for position, topic in enumerate(topics):
        grade_num = int(topic["grade"])
        if grade_num not in grade_cache:
            grade_cache[grade_num] = _get_or_create_grade(db, grade_num)
        grade = grade_cache[grade_num]
        if grade_num not in subject_cache:
            subject_cache[grade_num] = _get_or_create_subject(db, grade, "math", "人教版")
        subject = subject_cache[grade_num]
        term = 2 if topic.get("semester") == "下" else 1
        volume, chapter = parse_chapter(topic.get("chapter") or "")
        parent = None
        for level, external, name in (
            (1, "cnm_u:" + _stable_key(grade_num, term, volume), volume),
            (2, "cnm_c:" + _stable_key(grade_num, term, volume, chapter), chapter)):
            node = nodes.get(external)
            if not node:
                node = _new_node(db, parent=parent, grade_id=grade.id, subject_id=subject.id,
                                 name=name, level=level, term=term, code=external, external_id=external,
                                 source="import", owner_id=owner_id, description=None,
                                 difficulty="medium", keywords="外部图谱", sort=position,
                                 textbook_version="人教版")
                nodes[external] = node
            node.name, node.status, node.is_active = name, "published", True
            node.grade_id, node.subject_id, node.term = grade.id, subject.id, term
            node.parent_id = parent.id if parent else None
            node.path = f"{parent.path or parent.id}/{node.id}" if parent else str(node.id)
            node.level = level
            parent = node
            selected_ids.add(external)
        external = str(topic["id"])
        node = nodes.get(external)
        if not node:
            node = _new_node(db, parent=parent, grade_id=grade.id, subject_id=subject.id,
                             name=topic["name"], level=3, term=term, code="CNM-" + external[:60],
                             external_id=external, source="import", owner_id=owner_id)
            nodes[external] = node
        for key, value in topic_fields(topic).items():
            setattr(node, key, value)
        node.grade_id, node.subject_id, node.term = grade.id, subject.id, term
        node.parent_id, node.path, node.level = parent.id, f"{parent.path or parent.id}/{node.id}", 3
        chapter_counts[parent.id] = chapter_counts.get(parent.id, 0) + 1
        node.sort = chapter_counts[parent.id]
        node.status, node.is_active = "published", True
        selected_ids.add(node.external_id)
    scoped_node_ids = {row["id"] for row in before["knowledge"]}
    for external, node in nodes.items():
        if node.id in scoped_node_ids and external not in selected_ids:
            node.status = "archived"
            node.is_active = False
    mapped_questions = {item.external_id: item for item in db.scalars(
        select(Question).where(Question.external_source == SOURCE)).all()}
    qids = set()
    for item in questions:
        question = mapped_questions.get(str(item["id"]))
        node = nodes[str(item["topicId"])]
        if not question:
            question = Question(owner_id=owner_id, source="import", external_source=SOURCE,
                                external_id=str(item["id"]), grade_id=node.grade_id, subject_id=node.subject_id)
            db.add(question)
        for key, value in question_fields(item).items():
            setattr(question, key, value)
        question.grade_id, question.subject_id = node.grade_id, node.subject_id
        question.knowledge_point_id, question.status, question.bank_type = node.id, "published", "public"
        question.fingerprint = _question_fingerprint(question.stem)
        db.flush()
        qids.add(question.external_id)
        db.execute(delete(QuestionKnowledge).where(QuestionKnowledge.question_id == question.id,
                   QuestionKnowledge.knowledge_point_id != node.id))
        links = db.scalar(select(QuestionKnowledge).where(
            QuestionKnowledge.question_id == question.id, QuestionKnowledge.knowledge_point_id == node.id))
        if not links:
            db.add(QuestionKnowledge(question_id=question.id, knowledge_point_id=node.id))
    scoped_question_ids = {row["id"] for row in before["questions"]}
    for external, question in mapped_questions.items():
        if question.id in scoped_question_ids and external not in qids:
            question.status = "offline"
    db.execute(delete(KnowledgePrerequisite).where(
        KnowledgePrerequisite.source == SOURCE, KnowledgePrerequisite.topic_kp_id.in_(scoped_node_ids)))
    existing_edges = {(edge.topic_kp_id, edge.prerequisite_kp_id): edge
                      for edge in db.scalars(select(KnowledgePrerequisite)).all()}
    for item in edges:
        pair = (nodes[str(item["topicId"])].id, nodes[str(item["prerequisiteId"])].id)
        existing = existing_edges.get(pair)
        if existing:
            if existing.strength != (item.get("strength") or "hard"):
                raise BusinessException("上游先修关系与手工关系冲突，请先核对")
            continue
        db.add(KnowledgePrerequisite(topic_kp_id=nodes[str(item["topicId"])].id,
               prerequisite_kp_id=nodes[str(item["prerequisiteId"])].id,
               strength=item.get("strength") or "hard", reason=item.get("reason"), source=SOURCE))
    db.flush()
    all_edges = db.scalars(select(KnowledgePrerequisite)).all()
    all_ids = {edge.topic_kp_id for edge in all_edges} | {edge.prerequisite_kp_id for edge in all_edges}
    if not acyclic(all_ids, [(edge.topic_kp_id, edge.prerequisite_kp_id) for edge in all_edges]):
        raise BusinessException("与已有先修关系组合后存在环，已取消同步")
    return {"knowledge": len(topics), "questions": len(questions), "edges": len(edges)}


def lock_run(db, run_id):
    if db.get_bind().dialect.name == "sqlite":
        db.rollback()
        db.execute(text("BEGIN IMMEDIATE"))
    return db.scalar(select(TaxonomySyncRun).where(TaxonomySyncRun.id == run_id).with_for_update())


def apply(db, user, preview_id):
    owner_id = user.id
    if not _sync_lock.acquire(blocking=False):
        raise HTTPException(409, "已有同步任务正在执行")
    try:
        item = lock_run(db, preview_id)
        if not item:
            raise NotFoundException("同步预览不存在")
        if item.status == "applied":
            return run_out(item)
        if item.action != "preview" or item.status != "preview":
            raise BusinessException("只能应用尚未执行的预览")
        folder = Path(item.bundle_path).resolve()
        if not folder.is_relative_to(sync_dir()) or folder.name != item.source_commit:
            raise BusinessException("预览数据路径异常")
        report = json.loads(item.report)
        if report["errors"]:
            raise BusinessException("上游质量检查未通过")
        if report["bundle_digest"] != bundle_digest(folder):
            raise HTTPException(409, "预览源文件已变化，请重新预览")
        before = dataset_snapshot(db)
        if report["base_digest"] != digest_snapshot(before):
            raise HTTPException(409, "数据已变化，请重新预览")
        backup = sync_dir() / f"before-{item.id}.json"
        backup.write_text(json.dumps(before, ensure_ascii=False, default=str), encoding="utf-8")
        stats = normalize_source(db, folder, owner_id)
        item.backup_path, item.status, item.action = str(backup), "applied", "sync"
        report["import"] = stats
        item.report = json.dumps(report, ensure_ascii=False)
        db.commit()
        return run_out(item)
    except Exception:
        db.rollback()
        raise
    finally:
        _sync_lock.release()


def restore(db, user, run_id):
    if not _sync_lock.acquire(blocking=False):
        raise HTTPException(409, "已有同步任务正在执行")
    try:
        item = lock_run(db, run_id)
        if not item or not item.backup_path or item.status != "applied":
            raise NotFoundException("同步备份不存在")
        latest = db.scalar(select(TaxonomySyncRun.id).where(
            TaxonomySyncRun.status == "applied").order_by(TaxonomySyncRun.id.desc()).limit(1))
        if latest != run_id:
            raise BusinessException("请按同步历史从最近一次开始恢复")
        path = Path(item.backup_path).resolve()
        if not path.is_relative_to(sync_dir()):
            raise BusinessException("备份路径异常")
        snapshot = json.loads(path.read_text(encoding="utf-8"))
        current = dataset_snapshot(db)
        for key, model in (("knowledge", KnowledgePoint), ("questions", Question)):
            ids = {row["id"] for row in snapshot[key]}
            current_ids = {row["id"] for row in current[key]}
            for node in db.scalars(select(model).where(model.id.in_(current_ids))).all():
                if node.id not in ids:
                    node.status = "archived" if key == "knowledge" else "offline"
                    if key == "knowledge":
                        node.is_active = False
            for row in snapshot[key]:
                node = db.get(model, row["id"])
                if not node:
                    raise BusinessException("备份中的数据已被删除，无法安全恢复")
                for column in model.__table__.columns:
                    if column.name not in row or column.name in ("id", "usage_count"):
                        continue
                    value = row[column.name]
                    if value is not None and column.type.python_type == datetime:
                        value = datetime.fromisoformat(value)
                    setattr(node, column.name, value)
        question_ids = {row["id"] for row in current["questions"]}
        db.execute(delete(QuestionKnowledge).where(QuestionKnowledge.question_id.in_(question_ids)))
        for row in snapshot["links"]:
            db.add(QuestionKnowledge(question_id=row["question_id"], knowledge_point_id=row["knowledge_point_id"]))
        knowledge_ids = {row["id"] for row in current["knowledge"]}
        db.execute(delete(KnowledgePrerequisite).where(KnowledgePrerequisite.source == SOURCE,
                   KnowledgePrerequisite.topic_kp_id.in_(knowledge_ids)))
        for row in snapshot["edges"]:
            row.pop("id", None)
            row["created_at"] = datetime.fromisoformat(row["created_at"])
            db.add(KnowledgePrerequisite(**row))
        item.status = "restored"
        db.commit()
        return run_out(item)
    except Exception:
        db.rollback()
        raise
    finally:
        _sync_lock.release()
