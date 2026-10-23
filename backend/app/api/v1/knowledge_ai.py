"""知识点 AI 接口：生成预览 / 批量补全建议（`/edu/knowledge/ai`）。

契约见 docs/KNOWLEDGE_V2_RAG_AI.md §2：
- 需 `resource:knowledge:write` + 知识点写 scope。权限判定**复用**
  `knowledge.py` 的 helper（`_assert_write` / `_write_predicate`），
  不复制一份会漂移的权限逻辑；
- 调用 `check_agent_rate`；单次 ids ≤ 50；
- 无 LLM（`llm.is_available() == False`）时返回**规则引擎降级结果**并标记
  `is_fallback=true`，任何 LLM 侧异常同样降级，绝不 500；
- 两个接口都只返回预览，不落库（前端确认后走现有 POST/PUT 应用）。
"""
import json
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.llm import extract_json, get_llm, is_available
from app.api.deps import require_perm
from app.api.v1.knowledge import (
    VALID_DIFFICULTY, WRITE_PERM, _assert_write, _clean_str, _to_int,
    _write_predicate,
)
from app.core.database import get_db
from app.core.exception import BusinessException, NotFoundException, PermissionException
from app.core.logger import get_logger
from app.core.rate_limit import check_agent_rate
from app.models import Grade, KnowledgePoint, Subject, User
from app.utils.common import ok

logger = get_logger("knowledge-ai")

router = APIRouter(prefix="/edu/knowledge/ai", tags=["知识点 AI"])

MAX_IDS = 50
MIN_GENERATE_COUNT = 3
MAX_GENERATE_COUNT = 12
DEFAULT_GENERATE_COUNT = 5
MAX_TOPIC_CHARS = 200
MAX_UNIT_NAME_CHARS = 128
MAX_DESC_CHARS = 1000
MAX_KEYWORDS_CHARS = 255

GENERATE_SYSTEM_PROMPT = """你是九年义务教育阶段的资深教研员，负责规划知识点树。

要求：
1. 严格贴合指定年级与学科的课程标准，不超纲、不使用该年级未学的知识。
2. 知识点名称简短（2~24 字）、互相独立且不重复，能直接挂到知识点树。
3. 难度只用 easy / medium / hard 三个取值。
4. 关键词用中文逗号分隔，2~4 个。
5. 只输出 JSON，不要 markdown 代码块或任何解释性文字。"""

GENERATE_USER_TEMPLATE = """年级：{grade_name}
学科：{subject_name}
教材版本：{textbook_version}
学期：{term_label}
单元名称：{unit_name}
单元主题/范围：{topic}
需要生成 {count} 个知识点。{existing_hint}
只输出 JSON：
{{"unit_name":"单元名称","unit_description":"单元简介（50 字以内）","points":[{{"name":"知识点名称","description":"一句话说明","keywords":"关键词1,关键词2","difficulty":"easy|medium|hard"}}]}}"""

ENRICH_SYSTEM_PROMPT = """你是九年义务教育阶段的资深教研员，负责补全知识点资料。

对每个输入知识点，补全或润色以下字段：
- description：面向教师与学生的一句话说明（30~120 字，讲清定义/性质/典型应用）；
- keywords：2~5 个中文关键词，中文逗号分隔；
- difficulty：只能取 easy / medium / hard。

要求：不改变知识点的 id 与 name；只输出 JSON，不要 markdown 代码块或解释文字。"""

ENRICH_USER_TEMPLATE = """待补全的知识点（JSON 数组）：
{payload}

只输出 JSON：
{{"items":[{{"id":1,"description":"...","keywords":"...","difficulty":"medium"}}]}}"""

# 规则降级模板：无 LLM 时仍给出可用的「生成预览」结构。
FALLBACK_POINT_TEMPLATES = (
    ("核心概念", "理解{name}的定义与基本性质，能用自己的话复述关键结论。", "easy"),
    ("典型例题", "掌握{name}的常见考法，能独立完成基础到中档例题。", "medium"),
    ("常见误区", "辨析{name}中易混淆的概念与易错步骤，避免典型失分点。", "medium"),
    ("拓展应用", "能运用{name}解决跨情境问题，并说明解题依据。", "hard"),
    ("综合练习", "完成{name}的综合练习，能梳理知识结构并自查掌握情况。", "medium"),
    ("知识迁移", "把{name}与其他知识点建立联系，形成结构化理解。", "hard"),
    ("易错点辨析", "能识别{name}的易错表述并说明正确做法。", "easy"),
    ("实际应用", "能在生活或跨学科情境中应用{name}。", "medium"),
)


# ================================================================ 通用工具
def _unique_ids(raw: Any) -> List[int]:
    """校验 ids：整数数组、去重、1~50 条。"""
    if not isinstance(raw, list) or not raw:
        raise BusinessException("请选择要补全的知识点")
    ids: List[int] = []
    for item in raw:
        value = _to_int(item)
        if value is None or value <= 0:
            raise BusinessException("ids 必须为正整数列表")
        if value not in ids:
            ids.append(value)
    if len(ids) > MAX_IDS:
        raise BusinessException(f"单次最多补全 {MAX_IDS} 个知识点")
    return ids


def _call_llm_json(
    system_prompt: str, user_prompt: str, *,
    user_id: Optional[int], agent_name: str, biz_type: str,
) -> Optional[Any]:
    """调用 LLM 并解析 JSON；不可用/失败/解析失败统一返回 None 由调用方降级。"""
    try:
        resp = get_llm().chat(
            system_prompt, user_prompt,
            user_id=user_id, agent_name=agent_name, biz_type=biz_type,
        )
        if not resp.get("success"):
            return None
        return extract_json(resp.get("content") or "")
    except Exception as exc:  # noqa: BLE001  AI 侧异常一律降级，不 500
        logger.warning(f"知识点 AI 调用失败，降级规则引擎: {exc}")
        return None


def _normalize_keywords(value: Any) -> str:
    if isinstance(value, list):
        value = ",".join(str(v).strip() for v in value if str(v).strip())
    return (_clean_str(value) or "")[:MAX_KEYWORDS_CHARS]


def _normalize_difficulty(value: Any, default: str = "medium") -> str:
    diff = str(value or default).strip().lower()
    return diff if diff in VALID_DIFFICULTY else default


# ================================================================ 生成预览
def _existing_names(db: Session, grade_id: int, subject_id: int) -> List[str]:
    """同级已有知识点名称（提示模型避免重复；降级模板也用它去重）。"""
    rows = db.scalars(
        select(KnowledgePoint.name).where(
            KnowledgePoint.grade_id == grade_id,
            KnowledgePoint.subject_id == subject_id,
            KnowledgePoint.is_active.is_(True),
        ).order_by(KnowledgePoint.id).limit(50)
    ).all()
    return [str(name) for name in rows if name]


def _fallback_generate(
    grade: Grade, subject: Subject, topic: str, unit_name: str,
    term: int, count: int, existing: List[str],
) -> Dict[str, Any]:
    """规则引擎降级：基于单元主题 + 同级已有名称生成模板预览。"""
    base = (unit_name or topic or f"{subject.name}单元").strip()
    base = base[:MAX_UNIT_NAME_CHARS]
    used = set(existing)
    points: List[Dict[str, str]] = []
    for idx in range(count):
        label, desc_tpl, difficulty = FALLBACK_POINT_TEMPLATES[
            idx % len(FALLBACK_POINT_TEMPLATES)]
        name = f"{base}{label}"
        tail = 2
        while name in used and tail <= 9:
            name = f"{base}{label}{tail}"
            tail += 1
        used.add(name)
        points.append({
            "name": name[:128],
            "description": desc_tpl.format(name=name)[:MAX_DESC_CHARS],
            "keywords": ",".join([base, label])[:MAX_KEYWORDS_CHARS],
            "difficulty": difficulty,
        })
    return {
        "unit_name": base,
        "unit_description": (
            f"围绕「{base}」的单元知识点预览（规则引擎生成，"
            f"未启用大模型，共 {count} 条）。"
        )[:MAX_DESC_CHARS],
        "points": points,
        "grade_id": grade.id,
        "subject_id": subject.id,
        "term": term,
        "is_fallback": True,
    }


def _normalize_generated_points(raw: Any, count: int) -> List[Dict[str, str]]:
    """校验/裁剪模型输出：名称必填、难度枚举、关键词统一为逗号串。"""
    items = raw if isinstance(raw, list) else []
    points: List[Dict[str, str]] = []
    seen = set()
    for item in items:
        if not isinstance(item, dict):
            continue
        name = _clean_str(item.get("name"))
        if not name:
            continue
        name = name[:128]
        if name in seen:
            continue
        seen.add(name)
        points.append({
            "name": name,
            "description": (_clean_str(item.get("description")) or "")[:MAX_DESC_CHARS],
            "keywords": _normalize_keywords(item.get("keywords")),
            "difficulty": _normalize_difficulty(item.get("difficulty")),
        })
        if len(points) >= count:
            break
    return points


@router.post("/generate", summary="AI 生成知识点预览")
def ai_generate(
    data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    user: User = Depends(require_perm(WRITE_PERM)),
):
    """生成知识点预览（只预览不落库）。

    无 LLM 时返回规则引擎模板并标记 `is_fallback=true`；LLM 失败同样降级，
    保证前端「AI 生成」始终可用。
    """
    grade_id = _to_int(data.get("grade_id"))
    subject_id = _to_int(data.get("subject_id"))
    if not grade_id or not subject_id:
        raise BusinessException("请选择年级和学科")
    grade = db.get(Grade, grade_id)
    if not grade:
        raise BusinessException("年级不存在")
    subject = db.get(Subject, subject_id)
    if not subject:
        raise BusinessException("学科不存在")
    if subject.grade_id and int(subject.grade_id) != int(grade.id):
        raise BusinessException("学科与年级不匹配")
    # 写 scope：sys_admin 全部 / grade_admin 本年级 / teacher 仅任教 (grade,subject)
    _assert_write(db, user, grade.id, subject.id)

    topic = _clean_str(data.get("topic")) or ""
    unit_name = _clean_str(data.get("unit_name")) or ""
    if len(topic) > MAX_TOPIC_CHARS:
        raise BusinessException(f"主题不能超过 {MAX_TOPIC_CHARS} 个字符")
    if len(unit_name) > MAX_UNIT_NAME_CHARS:
        raise BusinessException(f"单元名称不能超过 {MAX_UNIT_NAME_CHARS} 个字符")
    # topic/unit_name 均为可选（契约），两者都空时按学科默认生成
    textbook_version = (
        _clean_str(data.get("textbook_version"))
        or subject.textbook_version or ""
    )[:64]
    term = _to_int(data.get("term"), 1)
    if term not in (1, 2):
        term = 1
    count = _to_int(data.get("count"), DEFAULT_GENERATE_COUNT) or DEFAULT_GENERATE_COUNT
    if count < MIN_GENERATE_COUNT or count > MAX_GENERATE_COUNT:
        raise BusinessException(
            f"生成数量应在 {MIN_GENERATE_COUNT}~{MAX_GENERATE_COUNT} 之间")

    check_agent_rate(db, user.id)

    existing = _existing_names(db, grade.id, subject.id)
    fallback = _fallback_generate(
        grade, subject, topic, unit_name, term, count, existing)
    if not is_available():
        return ok(fallback, message="当前未启用大模型，已返回规则引擎生成的预览")

    prompt = GENERATE_USER_TEMPLATE.format(
        grade_name=grade.name, subject_name=subject.name,
        textbook_version=textbook_version or "不限",
        term_label="上册" if term == 1 else "下册",
        unit_name=unit_name or topic or "（未指定，请根据学科拟定）",
        topic=topic or unit_name or "（未指定，请根据年级/学科拟定）",
        count=count,
        existing_hint=(
            "\n已有同级知识点（请勿重复）：" + "、".join(existing[:30])
            if existing else ""
        ),
    )
    parsed = _call_llm_json(
        GENERATE_SYSTEM_PROMPT, prompt, user_id=user.id,
        agent_name="knowledge_generate", biz_type="knowledge_generate",
    )
    points = _normalize_generated_points(
        parsed.get("points") if isinstance(parsed, dict) else parsed, count)
    if not points:
        logger.warning("知识点生成 LLM 未返回有效 points，降级规则引擎")
        return ok(fallback, message="AI 返回结果不可用，已降级为规则引擎预览")

    unit = _clean_str(parsed.get("unit_name")) if isinstance(parsed, dict) else None
    description = (
        _clean_str(parsed.get("unit_description")) if isinstance(parsed, dict) else None
    )
    result = {
        "unit_name": (unit or fallback["unit_name"])[:MAX_UNIT_NAME_CHARS],
        "unit_description": (description or fallback["unit_description"])[:MAX_DESC_CHARS],
        "points": points,
        "grade_id": grade.id,
        "subject_id": subject.id,
        "term": term,
        "is_fallback": False,
    }
    return ok(result, message="AI 生成完成（预览，未落库）")


# ================================================================ 批量补全
def _fallback_enrich_items(
    kps: List[KnowledgePoint], subject_names: Dict[int, str],
    grade_names: Dict[int, str],
) -> List[Dict[str, Any]]:
    """规则引擎降级：只补缺失字段，已有内容原样保留。"""
    items: List[Dict[str, Any]] = []
    for kp in kps:
        grade_name = grade_names.get(kp.grade_id) or "本"
        subject_name = subject_names.get(kp.subject_id) or "本学科"
        description = kp.description or (
            f"「{kp.name}」是{grade_name}{subject_name}中的核心知识点，"
            f"需掌握其定义、基本性质与典型应用场景。"
        )
        keywords = kp.keywords or f"{kp.name},{subject_name}"
        items.append({
            "id": kp.id,
            "name": kp.name,
            "description": description[:MAX_DESC_CHARS],
            "keywords": _normalize_keywords(keywords),
            "difficulty": _normalize_difficulty(kp.difficulty),
        })
    return items


def _merge_enrich_items(
    kps: List[KnowledgePoint], raw: Any, fallback: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """把模型建议合并回请求顺序；模型漏掉的节点用规则建议兜底。"""
    by_id: Dict[int, Dict[str, Any]] = {}
    if isinstance(raw, list):
        for item in raw:
            if not isinstance(item, dict):
                continue
            kp_id = _to_int(item.get("id"))
            if kp_id:
                by_id[kp_id] = item
    merged: List[Dict[str, Any]] = []
    for kp, base in zip(kps, fallback):
        suggestion = by_id.get(kp.id)
        if not suggestion:
            merged.append(base)
            continue
        merged.append({
            "id": kp.id,
            "name": kp.name,
            "description": (
                _clean_str(suggestion.get("description")) or base["description"]
            )[:MAX_DESC_CHARS],
            "keywords": _normalize_keywords(
                suggestion.get("keywords") or base["keywords"]),
            "difficulty": _normalize_difficulty(
                suggestion.get("difficulty"), base["difficulty"]),
        })
    return merged


@router.post("/enrich", summary="AI 批量补全知识点建议")
def ai_enrich(
    data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    user: User = Depends(require_perm(WRITE_PERM)),
):
    """对选中知识点返回补全建议（只预览不落库）。

    ids 必须全部存在且在写 scope 内；任一越权整体 403（与批量操作契约一致）。
    """
    ids = _unique_ids(data.get("ids"))
    found = {kp.id: kp for kp in db.scalars(
        select(KnowledgePoint).where(KnowledgePoint.id.in_(ids))
    ).all()}
    missing = [kp_id for kp_id in ids if kp_id not in found]
    if missing:
        raise NotFoundException(f"知识点不存在：{missing[:5]}")
    kps = [found[kp_id] for kp_id in ids]

    pred = _write_predicate(db, user)
    for kp in kps:
        if not pred(kp.grade_id, kp.subject_id):
            raise PermissionException("所选知识点中存在无权维护的节点")

    check_agent_rate(db, user.id)

    grade_ids = {kp.grade_id for kp in kps}
    subject_ids = {kp.subject_id for kp in kps}
    grade_names = {
        g.id: g.name for g in db.scalars(
            select(Grade).where(Grade.id.in_(grade_ids))).all()
    } if grade_ids else {}
    subject_names = {
        s.id: s.name for s in db.scalars(
            select(Subject).where(Subject.id.in_(subject_ids))).all()
    } if subject_ids else {}
    fallback = _fallback_enrich_items(kps, subject_names, grade_names)

    if not is_available():
        return ok({"items": fallback, "is_fallback": True},
                  message="当前未启用大模型，已返回规则引擎补全建议")

    payload = json.dumps([
        {
            "id": kp.id, "name": kp.name, "path": kp.path or str(kp.id),
            "description": kp.description or "", "keywords": kp.keywords or "",
            "difficulty": kp.difficulty,
        }
        for kp in kps
    ], ensure_ascii=False)
    prompt = ENRICH_USER_TEMPLATE.format(payload=payload)
    parsed = _call_llm_json(
        ENRICH_SYSTEM_PROMPT, prompt, user_id=user.id,
        agent_name="knowledge_enrich", biz_type="knowledge_enrich",
    )
    raw_items = parsed.get("items") if isinstance(parsed, dict) else parsed
    if not raw_items:
        logger.warning("知识点补全 LLM 未返回有效 items，降级规则引擎")
        return ok({"items": fallback, "is_fallback": True},
                  message="AI 返回结果不可用，已降级为规则引擎建议")

    return ok({"items": _merge_enrich_items(kps, raw_items, fallback),
               "is_fallback": False}, message="AI 补全建议已生成（预览，未落库）")
