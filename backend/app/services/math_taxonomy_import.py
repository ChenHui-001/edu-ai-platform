"""外部知识图谱导入：cn-math-taxonomy → 本地知识点树 / 先修图 / 题库。

设计边界：
- 外部 `parent_id`（若有）不能当先修关系；本地 parent_id 只表示教材包含树。
- 先修边单独落 `edu_knowledge_prerequisite`。
- 所有导入节点/题目保留 `external_source + external_id`，重复导入幂等。
- 导入器只读取调用方给定的数据目录，不把外部数据硬编码进业务代码。

数据许可：上游仓库为 CC BY-NC 4.0，商业使用需单独授权。导入属于数据
接入动作，是否用于商业产品由部署方确认；本模块只保留来源与许可标识，
不替部署方改变许可义务。
"""
import hashlib
import json
import os
import re
from typing import Any, Dict, Optional, Sequence, Set, Tuple

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Grade, KnowledgePoint, KnowledgePrerequisite, Question, Subject, User,
)
from app.utils.options import normalize_options

SOURCE = "cn-math-taxonomy"
LICENSE = "CC BY-NC 4.0"
SOURCE_URL = "https://github.com/xiaoyang111222/cn-math-taxonomy"

SUBJECT_NAMES = {
    "math": "数学",
    "english": "英语",
    "chinese": "语文",
    "science": "科学",
    "morality": "道德与法治",
    "physics": "物理",
    "chemistry": "化学",
    "biology": "生物",
    "history": "历史",
    "geography": "地理",
}

PREFIX_SUBJECT = {
    "cnm_": "math",
    "cne_": "english",
    "cnc_": "chinese",
    "cns_": "science",
    "cnd_": "morality",
    "cnp_": "physics",
    "cnk_": "chemistry",
    "cnb_": "biology",
    "cnh_": "history",
    "cng_": "geography",
}

MORALITY_JUNIOR = "政治"
GRADE_NAMES = {
    1: "一年级", 2: "二年级", 3: "三年级", 4: "四年级", 5: "五年级",
    6: "六年级", 7: "七年级", 8: "八年级", 9: "九年级",
}

QUESTION_TYPE_MAP = {
    "numeric": "blank",
    "choice": "single",
    "short": "short",
    "self": "short",
}
DIFFICULTY_MAP = {
    "basic": "easy",
    "standard": "medium",
    "medium": "medium",
    "challenge": "hard",
    "advanced": "hard",
}
TOPIC_DIFFICULTY = {
    "conceptual": "easy",
    "procedural": "medium",
    "application": "medium",
    "reasoning": "hard",
    "modeling": "hard",
}

_CHAPTER_RE = re.compile(
    r"^(?P<volume>[一二三四五六七八九]年级[上下全]册)\s+"
    r"(?P<unit>第\d+单元|预备单元\d|综合与实践|复习)\s+(?P<title>.+)$"
)


def subject_of(topic: Dict[str, Any]) -> str:
    """外部 topic 的学科。缺失 subject 时按 ID 前缀判定。

    上游并非只有数学缺 subject：道德与法治等同样缺。不能把缺失一律当数学。
    """
    explicit = str(topic.get("subject") or "").strip().lower()
    if explicit in SUBJECT_NAMES:
        return explicit
    tid = str(topic.get("id") or "")
    for prefix, subject in PREFIX_SUBJECT.items():
        if tid.startswith(prefix):
            return subject
    return "math"


def local_subject_name(subject: str, grade_num: int) -> str:
    """平台内的学科名。7-9 年级道德与法治使用平台已有的「政治」。"""
    if subject == "morality" and grade_num >= 7:
        return MORALITY_JUNIOR
    return SUBJECT_NAMES.get(subject, subject)


def parse_chapter(chapter: str) -> Tuple[str, str]:
    """把「一年级上册 第1单元 5以内数的认识和加、减法」拆成单元/章节名。"""
    text = str(chapter or "").strip()
    match = _CHAPTER_RE.match(text)
    if match:
        return (
            f"{match.group('volume')} {match.group('unit')}",
            match.group("title").strip(),
        )
    if " " in text:
        volume, rest = text.split(" ", 1)
        return volume, rest
    return "未分单元", text or "未命名章节"


def _stable_key(*parts: Any) -> str:
    raw = "|".join(str(p) for p in parts)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def _question_fingerprint(stem: str) -> str:
    """与 `api/v1/question.py::_fingerprint` 保持完全一致，避免两套查重口径。"""
    norm = re.sub(r"\s+", "", re.sub(r"[（(].*?[)）]", "", stem))
    return hashlib.md5(norm.encode()).hexdigest()


def _load_json(path: str) -> Any:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _resolve_source_layout(source_dir: str) -> Tuple[str, str]:
    """兼容「仓库根目录」与「data 子目录」两种传入方式。

    返回 (数据目录, 许可文件所在目录)。上游数据固定在 data/ 下，而 LICENSE
    和 README 在仓库根目录；允许直接传 data/ 便于联调，但许可要从父目录读。
    """
    root = os.path.abspath(source_dir)
    if os.path.isfile(os.path.join(root, "topics.json")):
        return root, os.path.dirname(root) \
            if os.path.isfile(os.path.join(os.path.dirname(root), "LICENSE")) else root
    data_dir = os.path.join(root, "data")
    if os.path.isfile(os.path.join(data_dir, "topics.json")):
        return data_dir, root
    return root, root


def _read_license(source_dir: str) -> str:
    """读取上游许可声明，作为导入统计的一部分交给运维留档。"""
    for name in ("LICENSE", "LICENSE.md", "README.md"):
        path = os.path.join(source_dir, name)
        if not os.path.isfile(path):
            continue
        try:
            text = open(path, encoding="utf-8", errors="replace").read(8000)
        except OSError:
            continue
        if "CC BY-NC" in text or "Attribution-NonCommercial" in text:
            return LICENSE
    return "unknown（请在上游仓库确认许可）"


def _parse_grades(values: Optional[Sequence[int]]) -> Set[int]:
    if not values:
        return set(range(1, 10))
    return {int(v) for v in values if 1 <= int(v) <= 9}


def _get_or_create_grade(db: Session, grade_num: int) -> Grade:
    grade = db.scalar(select(Grade).where(Grade.grade_num == grade_num))
    if grade:
        return grade
    grade = Grade(
        name=GRADE_NAMES[grade_num],
        stage="primary" if grade_num <= 6 else "junior",
        grade_num=grade_num,
        is_active=True,
        sort=grade_num,
    )
    db.add(grade)
    db.flush()
    return grade


def _get_or_create_subject(
    db: Session, grade: Grade, subject: str, textbook_version: Optional[str],
) -> Subject:
    name = local_subject_name(subject, grade.grade_num)
    row = db.scalar(select(Subject).where(
        Subject.grade_id == grade.id, Subject.name == name))
    if row:
        return row
    row = Subject(
        name=name,
        code=subject,
        textbook_version=textbook_version,
        grade_id=grade.id,
        is_active=True,
        sort=0,
    )
    db.add(row)
    db.flush()
    return row


def _resolve_owner_id(db: Session, owner_id: Optional[int]) -> int:
    if owner_id:
        if not db.get(User, int(owner_id)):
            raise ValueError(f"题目所有者不存在：{owner_id}")
        return int(owner_id)
    owner = db.scalar(
        select(User.id)
        .where(User.roles.any(code="sys_admin"), User.status == "active")
        .order_by(User.id)
    )
    if owner:
        return int(owner)
    owner = db.scalar(select(User.id).order_by(User.id))
    if owner:
        return int(owner)
    raise ValueError("导入题目需要至少一个用户作为 owner，请先初始化管理员或显式传 owner_id")


def _new_node(
    db: Session, *, parent: Optional[KnowledgePoint], grade_id: int, subject_id: int,
    name: str, level: int, term: int, code: str, external_id: str, source: str,
    owner_id: int, description: Optional[str] = None, difficulty: str = "medium",
    keywords: Optional[str] = None, sort: int = 0, textbook_version: Optional[str] = None,
) -> KnowledgePoint:
    node = KnowledgePoint(
        name=name[:128],
        grade_id=grade_id,
        subject_id=subject_id,
        parent_id=parent.id if parent else None,
        term=term,
        code=code[:64],
        description=description,
        difficulty=difficulty,
        keywords=(keywords or "")[:255] or None,
        sort=sort,
        is_active=True,
        textbook_version=textbook_version,
        status="published",
        source=source,
        owner_id=owner_id,
        external_source=SOURCE,
        external_id=external_id[:64],
        level=level,
    )
    db.add(node)
    db.flush()
    if parent:
        node.level = (parent.level or 0) + 1
        node.path = f"{parent.path or parent.id}/{node.id}"
    else:
        node.level = 1
        node.path = str(node.id)
    db.flush()
    return node


def _would_create_cycle(
    adjacency: Dict[int, Set[int]], topic_id: int, prerequisite_id: int,
) -> bool:
    """加入 topic -> prerequisite 后是否成环（沿 prerequisite 方向 DFS）。"""
    if topic_id == prerequisite_id:
        return True
    stack = [prerequisite_id]
    seen: Set[int] = set()
    while stack:
        cur = stack.pop()
        if cur == topic_id:
            return True
        if cur in seen:
            continue
        seen.add(cur)
        stack.extend(adjacency.get(cur, ()))
    return False


def _q_extra(question: Dict[str, Any]) -> Dict[str, Any]:
    excluded = {"prompt", "answer", "explanation", "type", "difficulty", "id", "topicId",
                "choices"}
    extra = {k: v for k, v in question.items() if k not in excluded}
    extra["topicId"] = question.get("topicId")
    extra["externalType"] = question.get("type")
    extra["license"] = LICENSE
    extra["sourceUrl"] = SOURCE_URL
    return extra


def import_math_taxonomy(
    db: Session,
    source_dir: str,
    *,
    grades: Optional[Sequence[int]] = None,
    subject: str = "math",
    dry_run: bool = False,
    limit: Optional[int] = None,
    owner_id: Optional[int] = None,
    bank_type: str = "private",
    status: str = "published",
    textbook_version: Optional[str] = "人教版",
) -> Dict[str, Any]:
    """导入外部图谱，返回可审计统计。

    `dry_run=True` 会在事务内完整执行后回滚，用于上线前核对数量与错误。
    调用方负责保证 `source_dir` 指向已审阅的上游数据目录。
    """
    source_dir = os.path.abspath(source_dir)
    data_dir, license_dir = _resolve_source_layout(source_dir)
    for name in ("topics.json", "dependencies.json", "questions.json"):
        if not os.path.isfile(os.path.join(data_dir, name)):
            raise ValueError(f"数据目录缺少 {name}：{data_dir}")

    topics_all = _load_json(os.path.join(data_dir, "topics.json"))
    deps_all = _load_json(os.path.join(data_dir, "dependencies.json"))
    questions_all = _load_json(os.path.join(data_dir, "questions.json"))
    if not isinstance(topics_all, list) or not isinstance(deps_all, list) \
            or not isinstance(questions_all, list):
        raise ValueError("topics/dependencies/questions 必须是 JSON 数组")

    allowed_grades = _parse_grades(grades)
    topics = [
        t for t in topics_all
        if isinstance(t, dict)
        and subject_of(t) == subject
        and str(t.get("id") or "").strip()
        and not t.get("external")
        and str(t.get("grade") or "").isdigit()
        and int(t["grade"]) in allowed_grades
    ]
    topics.sort(key=lambda t: (int(t.get("grade") or 0), str(t.get("id") or "")))
    if limit is not None:
        topics = topics[:max(0, int(limit))]

    stats: Dict[str, Any] = {
        "source": SOURCE,
        "source_url": SOURCE_URL,
        "license": _read_license(license_dir),
        "source_dir": data_dir,
        "subject": subject,
        "grades": sorted(allowed_grades),
        "dry_run": dry_run,
        "topics_selected": len(topics),
        "nodes_created": 0,
        "knowledge_points_created": 0,
        "knowledge_points_reused": 0,
        "units_created": 0,
        "chapters_created": 0,
        "prerequisites_created": 0,
        "prerequisites_updated": 0,
        "prerequisites_skipped": 0,
        "questions_created": 0,
        "questions_skipped_existing": 0,
        "questions_skipped_duplicate": 0,
        "skipped": 0,
        "errors": [],
        "warnings": [],
    }
    if not topics:
        stats["warnings"].append("没有符合学科/年级条件的外部知识点")
        if dry_run:
            db.rollback()
        return stats

    owner = _resolve_owner_id(db, owner_id)
    existing_nodes: Dict[str, KnowledgePoint] = {
        str(kp.external_id): kp
        for kp in db.scalars(
            select(KnowledgePoint).where(KnowledgePoint.external_source == SOURCE)
        ).all()
        if kp.external_id
    }
    grade_cache: Dict[int, Grade] = {}
    subject_cache: Dict[Tuple[int, str], Subject] = {}
    chapter_cache: Dict[str, KnowledgePoint] = {}
    topic_nodes: Dict[str, KnowledgePoint] = {}
    chapter_counts: Dict[str, int] = {}

    try:
        for topic in topics:
            grade_num = int(topic["grade"])
            ext_topic_id = str(topic["id"]).strip()
            grade = grade_cache.get(grade_num)
            if not grade:
                grade = _get_or_create_grade(db, grade_num)
                grade_cache[grade_num] = grade
            subj_key = (grade.id, subject)
            local_subject = subject_cache.get(subj_key)
            if not local_subject:
                local_subject = _get_or_create_subject(
                    db, grade, subject, textbook_version)
                subject_cache[subj_key] = local_subject

            term = 2 if str(topic.get("semester") or "上") == "下" else 1
            volume, chapter_title = parse_chapter(str(topic.get("chapter") or ""))
            unit_name = volume
            chapter_key = _stable_key(grade_num, term, volume, chapter_title)

            node = existing_nodes.get(ext_topic_id)
            if node and node.subject_id == local_subject.id:
                stats["knowledge_points_reused"] += 1
                topic_nodes[ext_topic_id] = node
                continue
            if node:
                stats["warnings"].append(
                    f"{ext_topic_id} 已映射到其他年级/学科，本次跳过")
                stats["skipped"] += 1
                continue

            chapter_node = chapter_cache.get(chapter_key)
            if not chapter_node:
                unit_ext = f"cnm_u:{_stable_key(grade_num, term, volume)}"
                unit_node = existing_nodes.get(unit_ext)
                if not unit_node:
                    unit_node = _new_node(
                        db, parent=None, grade_id=grade.id, subject_id=local_subject.id,
                        name=unit_name, level=1, term=term,
                        code=f"CNM-U-{grade_num}-{term}-{_stable_key(volume)[:8]}",
                        external_id=unit_ext, source="import", owner_id=owner,
                        description=f"{SOURCE} 教材单元",
                        difficulty="medium", keywords="外部图谱,单元",
                        sort=len(chapter_cache) + 1,
                        textbook_version=textbook_version,
                    )
                    existing_nodes[unit_ext] = unit_node
                    stats["units_created"] += 1
                    stats["nodes_created"] += 1
                chapter_ext = f"cnm_c:{chapter_key}"
                chapter_node = existing_nodes.get(chapter_ext)
                if not chapter_node:
                    chapter_node = _new_node(
                        db, parent=unit_node, grade_id=grade.id,
                        subject_id=local_subject.id, name=chapter_title, level=2,
                        term=term,
                        code=f"CNM-C-{grade_num}-{term}-{chapter_key[:10]}",
                        external_id=chapter_ext, source="import", owner_id=owner,
                        description=f"{SOURCE} 教材章节",
                        difficulty="medium", keywords="外部图谱,章节",
                        sort=len(chapter_cache) + 1,
                        textbook_version=textbook_version,
                    )
                    existing_nodes[chapter_ext] = chapter_node
                    stats["chapters_created"] += 1
                    stats["nodes_created"] += 1
                chapter_cache[chapter_key] = chapter_node

            chapter_counts[chapter_key] = chapter_counts.get(chapter_key, 0) + 1
            sort_idx = chapter_counts[chapter_key]
            criteria = topic.get("mastery_criteria") or []
            description_parts = [
                str(topic.get("description") or "").strip(),
                ("掌握标准：" + "；".join(str(x) for x in criteria if x))
                if isinstance(criteria, list) and criteria else "",
            ]
            keywords = "，".join(filter(None, [
                str(topic.get("domain") or "").strip(),
                "外部图谱",
                str(topic.get("type") or "").strip(),
            ]))
            leaf = _new_node(
                db, parent=chapter_node, grade_id=grade.id,
                subject_id=local_subject.id, name=str(topic.get("name") or ext_topic_id),
                level=3, term=term,
                code=f"CNM-{ext_topic_id}",
                external_id=ext_topic_id, source="import", owner_id=owner,
                description="\n".join(x for x in description_parts if x) or None,
                difficulty=TOPIC_DIFFICULTY.get(
                    str(topic.get("type") or ""), "medium"),
                keywords=keywords, sort=sort_idx,
                textbook_version=textbook_version,
            )
            existing_nodes[ext_topic_id] = leaf
            topic_nodes[ext_topic_id] = leaf
            stats["knowledge_points_created"] += 1
            stats["nodes_created"] += 1

        # 先修边：只接受本次已映射的两个端点，拒绝自环/跨学科/成环。
        existing_edges = {
            (row.topic_kp_id, row.prerequisite_kp_id): row
            for row in db.scalars(select(KnowledgePrerequisite)).all()
        }
        subject_names = {
            s.id: s.name for s in subject_cache.values()
        }
        adjacency: Dict[int, Set[int]] = {}
        for (topic_id, prereq_id) in existing_edges:
            adjacency.setdefault(topic_id, set()).add(prereq_id)

        invalid_topic_ids = {str(t.get("id")) for t in topics}
        seen_pairs: Set[Tuple[int, int]] = set()
        for dep in deps_all:
            if not isinstance(dep, dict):
                continue
            ext_topic = str(dep.get("topicId") or "").strip()
            ext_pre = str(dep.get("prerequisiteId") or "").strip()
            if ext_topic not in invalid_topic_ids or ext_pre not in invalid_topic_ids:
                continue
            topic_node = topic_nodes.get(ext_topic)
            pre_node = topic_nodes.get(ext_pre)
            if not topic_node or not pre_node:
                stats["prerequisites_skipped"] += 1
                continue
            pair = (topic_node.id, pre_node.id)
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)
            if topic_node.id == pre_node.id:
                stats["prerequisites_skipped"] += 1
                stats["errors"].append(f"拒绝自环先修边：{ext_topic}")
                continue
            # Subject 在本平台按「年级 × 学科」各存一行，subject_id 不同不代表
            # 跨学科。跨年级先修是正常且必需的，必须按学科名称判定。
            if subject_names.get(topic_node.subject_id) != subject_names.get(pre_node.subject_id):
                stats["prerequisites_skipped"] += 1
                stats["errors"].append(
                    f"拒绝跨学科先修边：{ext_topic} -> {ext_pre}")
                continue
            strength = "soft" if str(dep.get("strength")) == "soft" else "hard"
            reason = str(dep.get("reason") or "").strip() or None
            edge = existing_edges.get(pair)
            if edge:
                if edge.source == SOURCE and (
                    edge.strength != strength or (edge.reason or "") != (reason or "")
                ):
                    edge.strength = strength
                    edge.reason = reason
                    stats["prerequisites_updated"] += 1
                else:
                    stats["prerequisites_skipped"] += 1
                continue
            if _would_create_cycle(adjacency, topic_node.id, pre_node.id):
                stats["prerequisites_skipped"] += 1
                stats["errors"].append(
                    f"拒绝成环先修边：{ext_topic} -> {ext_pre}")
                continue
            db.add(KnowledgePrerequisite(
                topic_kp_id=topic_node.id,
                prerequisite_kp_id=pre_node.id,
                strength=strength,
                reason=reason,
                source=SOURCE,
            ))
            adjacency.setdefault(topic_node.id, set()).add(pre_node.id)
            stats["prerequisites_created"] += 1

        # 题目：external_id 已存在即跳过；题干 fingerprint 重复也跳过。
        existing_question_ids = {
            str(q.external_id)
            for q in db.scalars(
                select(Question).where(Question.external_source == SOURCE)
            ).all()
            if q.external_id
        }
        selected_grade_ids = {g.id for g in grade_cache.values()}
        existing_fps: Set[str] = set(
            db.scalars(
                select(Question.fingerprint).where(
                    Question.grade_id.in_(selected_grade_ids),
                    Question.fingerprint.isnot(None),
                )
            ).all()
        ) if selected_grade_ids else set()

        for item in questions_all:
            if not isinstance(item, dict):
                continue
            ext_topic = str(item.get("topicId") or "").strip()
            if ext_topic not in topic_nodes:
                continue
            ext_qid = str(item.get("id") or "").strip()
            prompt = str(item.get("prompt") or "").strip()
            if not ext_qid or not prompt:
                stats["skipped"] += 1
                continue
            if ext_qid in existing_question_ids:
                stats["questions_skipped_existing"] += 1
                continue
            fp = _question_fingerprint(prompt)
            if fp in existing_fps:
                stats["questions_skipped_duplicate"] += 1
                continue
            node = topic_nodes[ext_topic]
            qtype = QUESTION_TYPE_MAP.get(str(item.get("type") or ""), "short")
            difficulty = DIFFICULTY_MAP.get(
                str(item.get("difficulty") or ""), "medium")
            options = normalize_options(item.get("choices"))
            answer = item.get("answer")
            question = Question(
                type=qtype,
                stem=prompt,
                options=json.dumps(options, ensure_ascii=False) if options else None,
                answer=json.dumps(answer, ensure_ascii=False)
                if answer is not None and not isinstance(answer, str)
                else (answer if answer is None else str(answer)),
                analysis=str(item.get("explanation") or "") or None,
                score=5.0,
                difficulty=difficulty,
                grade_id=node.grade_id,
                subject_id=node.subject_id,
                knowledge_point_id=node.id,
                bank_type=bank_type,
                owner_id=owner,
                status=status,
                fingerprint=fp,
                source="import",
                external_source=SOURCE,
                external_id=ext_qid,
                extra_json=json.dumps(_q_extra(item), ensure_ascii=False),
            )
            db.add(question)
            existing_question_ids.add(ext_qid)
            existing_fps.add(fp)
            stats["questions_created"] += 1

        db.flush()
        if dry_run:
            db.rollback()
        else:
            db.commit()
        return stats
    except Exception:
        db.rollback()
        raise
