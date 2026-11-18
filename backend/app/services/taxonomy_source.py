"""Validated canonical upstream records used by preview and apply."""
import hashlib
import json
from collections import deque
from pathlib import Path
from types import SimpleNamespace

from app.core.exception import BusinessException
from app.services.math_taxonomy_import import (
    DIFFICULTY_MAP, QUESTION_TYPE_MAP, TOPIC_DIFFICULTY, _q_extra, _question_fingerprint,
    subject_of,
)
from app.services.question_quality import issues_for
from app.utils.options import normalize_options


def bundle_digest(folder):
    digest = hashlib.sha256()
    for name in ("LICENSE", "data/topics.json", "data/questions.json", "data/dependencies.json"):
        digest.update(name.encode())
        digest.update((Path(folder) / name).read_bytes())
    return digest.hexdigest()


def read_source(folder):
    data = {}
    for name in ("topics", "dependencies", "questions"):
        value = json.loads((Path(folder) / "data" / f"{name}.json").read_text(encoding="utf-8"))
        if not isinstance(value, list) or len(value) > 50000 or any(not isinstance(item, dict) for item in value):
            raise BusinessException(f"{name} 必须为有界对象数组")
        data[name] = value
    topics = sorted((item for item in data["topics"] if subject_of(item) == "math"
                     and str(item.get("grade", "")).isdigit() and 1 <= int(item["grade"]) <= 9
                     and not item.get("external")), key=lambda item: (int(item["grade"]), str(item.get("id"))))
    if not topics:
        raise BusinessException("上游没有数学知识点，拒绝清空数据集")
    ids = [str(item.get("id") or "") for item in topics]
    if len(set(ids)) != len(ids) or any(not item or len(item) > 64 for item in ids):
        raise BusinessException("知识点标识为空、重复或过长")
    if any(not isinstance(item.get("name"), str) or not item["name"].strip() for item in topics):
        raise BusinessException("知识点名称为空")
    ids = set(ids)
    questions, seen, qids = [], set(), set()
    for item in data["questions"]:
        if str(item.get("topicId")) not in ids:
            continue
        qid = str(item.get("id") or "")
        if not qid or len(qid) > 80 or qid in qids:
            raise BusinessException("题目标识为空、重复或过长")
        qids.add(qid)
        fingerprint = _question_fingerprint(str(item.get("prompt") or item.get("stem") or ""))
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        questions.append(item)
    edges, pairs = [], set()
    for item in data["dependencies"]:
        pair = (str(item.get("topicId")), str(item.get("prerequisiteId")))
        if not set(pair).issubset(ids):
            continue
        if item.get("strength", "hard") not in ("hard", "soft"):
            raise BusinessException("先修强度必须为 hard 或 soft")
        if pair not in pairs:
            pairs.add(pair)
            edges.append({**item, "strength": item.get("strength") or "hard"})
    return topics, questions, edges


def topic_fields(topic):
    criteria = topic.get("mastery_criteria")
    description = [str(topic.get("description") or "").strip()]
    if isinstance(criteria, list) and criteria:
        description.append("掌握标准：" + "；".join(str(item) for item in criteria))
    return {"name": topic["name"][:128], "description": "\n".join(filter(None, description)) or None,
            "difficulty": TOPIC_DIFFICULTY.get(topic.get("type"), "medium"),
            "keywords": "，".join(filter(None, [str(topic.get("domain") or ""), "外部图谱",
                                            str(topic.get("type") or "")]))[:255],
            "term": 2 if topic.get("semester") == "下" else 1}


def question_fields(item):
    return {"stem": str(item.get("prompt") or item.get("stem") or ""),
            "answer": json.dumps(item.get("answer"), ensure_ascii=False),
            "options": json.dumps(normalize_options(item.get("choices")), ensure_ascii=False),
            "analysis": item.get("explanation"),
            "extra_json": json.dumps(_q_extra(item), ensure_ascii=False),
            "type": QUESTION_TYPE_MAP.get(item.get("type"), "short"),
            "difficulty": DIFFICULTY_MAP.get(item.get("difficulty"), "medium")}


def acyclic(node_ids, pairs):
    adjacent = {node: set() for node in node_ids}
    incoming = {node: 0 for node in node_ids}
    for target, prerequisite in pairs:
        if target not in incoming or prerequisite not in incoming:
            continue
        if target not in adjacent[prerequisite]:
            adjacent[prerequisite].add(target)
            incoming[target] += 1
    queue = deque(node for node, count in incoming.items() if not count)
    visited = 0
    while queue:
        node = queue.popleft()
        visited += 1
        for target in adjacent[node]:
            incoming[target] -= 1
            if not incoming[target]:
                queue.append(target)
    return visited == len(incoming)


def quality_errors(topics, questions, edges):
    errors = []
    for item in questions:
        fields = question_fields(item)
        fields["knowledge_point_id"] = 1
        if item.get("type") not in QUESTION_TYPE_MAP:
            errors.append(f"题目 {item['id']} 类型不支持")
        errors.extend(f"题目 {item['id']}：{issue}" for issue in issues_for(SimpleNamespace(**fields))["errors"])
    if not acyclic({str(item["id"]) for item in topics},
                   [(str(item["topicId"]), str(item["prerequisiteId"])) for item in edges]):
        errors.append("先修关系存在环")
    return errors
