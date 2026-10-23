"""题库 AI 接口：变式生成 / 批量补全 / 批量质检（prefix `/question/questions/ai`）。

契约见 docs/QUESTION_BANK_V2.md §4：

- 统一：`question:bank:write` + 题目归属校验（owner / sys_admin / grade_admin）、
  `check_agent_rate`、ids ≤ 50；无 LLM 时规则降级并返回 `is_fallback=true`，
  任何 AI 侧异常都降级，绝不 500；**只返回预览，不落库**。
- 本文件不修改 `question.py` 的既有行为，只新增只读查询 + LLM 调用；
  变式/补全/质检结果由前端确认后走既有 POST/PUT 落库。

LLM 调用方式与 `app/agents/question_agent.py` 保持一致：先 `is_available()`
判断，再 `get_llm().chat(...)` + `extract_json(...)`；解析失败按降级处理。
"""
import hashlib
import json
import re
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, Body, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.llm import extract_json, get_llm, is_available
from app.api.deps import require_perm
from app.core.database import get_db
from app.core.exception import BusinessException, NotFoundException, PermissionException
from app.core.logger import get_logger
from app.core.rate_limit import check_agent_rate
from app.models import Grade, KnowledgePoint, Question, Subject, User
from app.utils.common import ok

logger = get_logger("question-ai")

router = APIRouter(prefix="/question/questions/ai", tags=["题库 AI"])

WRITE_PERM = "question:bank:write"
MAX_IDS = 50
MAX_VARIANTS = 10
DEFAULT_VARIANTS = 3
LLM_CHUNK_SIZE = 10
SHORT_STEM_CHARS = 8
MAX_STEM_PROMPT_CHARS = 1500
MAX_ANALYSIS_PROMPT_CHARS = 600

# 题型/难度枚举与 question.py 保持一致（本地常量：本文件不改 question.py，
# 也不依赖其私有 helper，避免并行改造期间互相耦合）
QUESTION_TYPES = (
    "single", "multiple", "judge", "blank", "short", "calc", "material", "composition",
)
QUESTION_TYPE_ALIAS = {"subjective": "short", "essay": "composition"}
DIFFICULTIES = ("easy", "medium", "hard")
SEVERITIES = ("error", "warning", "info")

# 规则质检：题干占位符/未填写标记（只做明确标记，避免误伤正常题干）
PLACEHOLDER_MARKS = (
    "待补充", "待完善", "待填写", "此处填写", "请补充", "TODO", "todo",
    "xxx", "XXX", "xxxx", "占位符", "占位题", "示例题目",
)
EMPTY_STEM_MARKS = {"题干", "题目", "问题", "题目内容", "题干内容", "?"}

# 规则变式的安全改写对（只换人称/情境实体，不改变题目数量关系与答案）
STEAM_SWAPS = (
    ("小明", "小红"), ("小红", "小明"), ("小刚", "小强"), ("小强", "小刚"),
    ("甲", "乙"), ("乙", "甲"), ("一班", "二班"), ("二班", "一班"),
    ("商店", "超市"), ("超市", "商店"), ("苹果", "梨"), ("梨", "苹果"),
)

VARIANT_SYSTEM_PROMPT = """你是中国九年义务教育的资深命题专家，负责基于原题生成「同考点变式题」。

要求：
1. 与原题保持相同的题型、考点与难度层级，不超纲。
2. 通过替换情境、人称或调整数据生成新题；答案必须与新题一致且可解。
3. 变式之间不要重复，也不要与原题完全一样。
4. 只输出 JSON 数组，不要任何解释文字或 markdown 代码块。

输出格式：
[
  {
    "type": "single",
    "stem": "题干",
    "options": [{"key":"A","text":"选项"},{"key":"B","text":"选项"}],
    "answer": "A",
    "analysis": "解析",
    "difficulty": "medium",
    "score": 5,
    "knowledge_point_id": 0
  }
]
type 取值：single/multiple/judge/blank/short/calc/material/composition；difficulty：easy/medium/hard。"""

ENRICH_SYSTEM_PROMPT = """你是中国九年义务教育的资深教研员，负责补全题库题目的解析与知识点归属。

对每道题：
1. 给出 1 段面向教师与学生的解析（讲清解题思路、关键步骤与易错点，80~200 字）；
2. 若题目缺少知识点，依据题干与学科推荐最匹配的 knowledge_point_id（不确定则给 0）；
3. difficulty 只能取 easy/medium/hard，可依据题目难度给出建议值。

要求：不改变题目 id 与题干；只输出 JSON，不要 markdown 代码块或解释文字。
输出格式：{"items":[{"id":1,"analysis":"...","knowledge_point_id":0,"knowledge_point_name":"...","difficulty":"medium"}]}"""

QUALITY_SYSTEM_PROMPT = """你是中国九年义务教育的题库质检员，负责识别低质量题目。

请对每道题给出问题列表（没有问题就给空数组），关注：
- 题干表述含糊、歧义、缺少必要条件（ai_ambiguous）；
- 选项设置不合理（如无正确答案、重复选项、单选只有一个选项）（ai_option_problem）；
- 题干与答案/解析明显矛盾（ai_answer_mismatch）；
- 其他明显低质量问题（ai_low_quality）。

只输出 JSON，不要 markdown 代码块或解释文字。
输出格式：{"items":[{"id":1,"issues":[{"code":"ai_ambiguous","message":"...","severity":"warning"}]}]}
severity 取值：error/warning/info；code 必须以上述 ai_ 前缀之一。"""


# ================================================================ 通用工具
def _load(v: Optional[str]) -> Any:
    """DB 中 JSON 文本 -> Python 对象（与 question.py 的阅读口径一致）。"""
    if not v:
        return None
    try:
        return json.loads(v)
    except (TypeError, ValueError):
        return v


def _dump(v: Any) -> Optional[str]:
    if v is None:
        return None
    return v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)


def _fingerprint(stem: str) -> str:
    """题干归一化哈希（与 question.py 查重口径一致：去空白、去括号注释）。"""
    norm = re.sub(r"\s+", "", re.sub(r"[（(].*?[)）]", "", str(stem or "")))
    return hashlib.md5(norm.encode()).hexdigest()


def _plain_stem(stem: Any) -> str:
    """去掉 HTML 标签与空白后的题干正文（用于长度/占位符检查）。"""
    text = re.sub(r"<[^>]+>", "", str(stem or ""))
    return re.sub(r"\s+", "", text)


def _to_int(value: Any, default: Optional[int] = None) -> Optional[int]:
    if value in (None, ""):
        return default
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    return number


def _to_float(value: Any, default: float = 5.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _clean_str(value: Any, limit: Optional[int] = None) -> str:
    text = str(value or "").strip()
    return text[:limit] if limit else text


def _codes(user: User) -> set:
    return set(user.role_codes or [])


def _is_admin_role(user: User) -> bool:
    """sys_admin / grade_admin：可操作公共题与他人的题（审核/治理场景）。"""
    return bool({"sys_admin", "grade_admin"} & _codes(user))


def _can_access_question(q: Question, user: User) -> bool:
    """AI 写操作归属校验：owner 或 sys_admin/grade_admin。"""
    return q.owner_id == user.id or _is_admin_role(user)


def _unique_ids(raw: Any) -> List[int]:
    """ids 校验：正整数数组、去重、1~50 条。"""
    if not isinstance(raw, list) or not raw:
        raise BusinessException("请选择要操作的题目")
    ids: List[int] = []
    for item in raw:
        value = _to_int(item)
        if value is None or value <= 0:
            raise BusinessException("ids 必须为正整数列表")
        if value not in ids:
            ids.append(value)
    if len(ids) > MAX_IDS:
        raise BusinessException(f"单次最多操作 {MAX_IDS} 道题")
    return ids


def _load_questions(db: Session, ids: List[int], user: User) -> List[Question]:
    """按请求顺序取题，全部存在且有权访问，否则 404/403（整体拒绝）。"""
    found = {q.id: q for q in db.scalars(
        select(Question).where(Question.id.in_(ids))
    ).all()}
    missing = [qid for qid in ids if qid not in found]
    if missing:
        raise NotFoundException(f"题目不存在：{missing[:5]}")
    questions = [found[qid] for qid in ids]
    if any(not _can_access_question(q, user) for q in questions):
        raise PermissionException("所选题目中存在无权操作的题目")
    return questions


def _load_question(db: Session, qid: int, user: User) -> Question:
    q = db.get(Question, qid)
    if not q:
        raise NotFoundException("题目不存在")
    if not _can_access_question(q, user):
        raise PermissionException("无权操作该题目")
    return q


def _normalize_type(value: Any, default: str = "single") -> str:
    qtype = str(value or default).strip().lower()
    qtype = QUESTION_TYPE_ALIAS.get(qtype, qtype)
    return qtype if qtype in QUESTION_TYPES else (
        default if default in QUESTION_TYPES else "single")


def _normalize_difficulty(value: Any, default: str = "medium") -> str:
    diff = str(value or default).strip().lower()
    return diff if diff in DIFFICULTIES else default


def _normalize_score(value: Any, default: float = 5.0) -> float:
    score = _to_float(value, default)
    if score <= 0:
        return default
    return round(min(score, 100.0), 2)


def _json_safe(value: Any) -> Any:
    """模型/DB 里的答案可能是对象/数组/字符串，统一转成可 JSON 序列化的值。"""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, list):
        return [_json_safe(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    return str(value)


def _normalize_options(value: Any) -> Optional[List[Dict[str, str]]]:
    """选项统一为 [{key,text}]；无法识别时返回 None（交给前端/人工处理）。"""
    if not isinstance(value, list):
        return None
    options: List[Dict[str, str]] = []
    for index, item in enumerate(value):
        if isinstance(item, dict):
            key = _clean_str(item.get("key")) or chr(65 + index)
            text = _clean_str(item.get("text"))
        else:
            key = chr(65 + index)
            text = _clean_str(item)
        if not text:
            continue
        options.append({"key": key[:8], "text": text[:500]})
    return options or None


def _existing_kp(db: Session, kp_id: Any) -> Optional[KnowledgePoint]:
    value = _to_int(kp_id)
    return db.get(KnowledgePoint, value) if value else None


def _suggest_kp(db: Session, q: Question) -> Optional[KnowledgePoint]:
    """规则补全知识点：优先沿用已有；否则在同年级同学科知识点名里找题干命中。"""
    kp = _existing_kp(db, q.knowledge_point_id)
    if kp:
        return kp
    if not q.subject_id or not q.stem:
        return None
    rows = db.scalars(
        select(KnowledgePoint).where(
            KnowledgePoint.subject_id == q.subject_id,
            KnowledgePoint.is_active.is_(True),
        ).order_by(KnowledgePoint.level.desc()).limit(300)
    ).all()
    stem = str(q.stem)
    matched = [kp for kp in rows if kp.name and kp.name in stem]
    if not matched:
        return None
    return max(matched, key=lambda kp: len(kp.name or ""))


def _answer_text(value: Any) -> str:
    """答案展示文本（规则补解析用）。"""
    if value is None or value == "" or value == [] or value == {}:
        return ""
    if isinstance(value, (list, tuple)):
        return "、".join(_clean_str(v) for v in value if _clean_str(v))[:200]
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False)[:200]
    return str(value)[:200]


def _has_answer(q: Question) -> bool:
    value = _load(q.answer)
    if isinstance(value, (list, tuple, dict)):
        return bool(value)
    return bool(str(value or "").strip())


def _name_maps(
    db: Session, questions: List[Question],
) -> Tuple[Dict[int, str], Dict[int, str], Dict[int, KnowledgePoint]]:
    """批量取年级/学科/知识点名称，避免逐题查库。"""
    grade_ids = {q.grade_id for q in questions if q.grade_id}
    subject_ids = {q.subject_id for q in questions if q.subject_id}
    kp_ids = {q.knowledge_point_id for q in questions if q.knowledge_point_id}
    grades = {
        g.id: g.name for g in db.scalars(
            select(Grade).where(Grade.id.in_(grade_ids))).all()
    } if grade_ids else {}
    subjects = {
        s.id: s.name for s in db.scalars(
            select(Subject).where(Subject.id.in_(subject_ids))).all()
    } if subject_ids else {}
    kps = {
        kp.id: kp for kp in db.scalars(
            select(KnowledgePoint).where(KnowledgePoint.id.in_(kp_ids))).all()
    } if kp_ids else {}
    return grades, subjects, kps


def _call_llm_json(
    system_prompt: str, user_prompt: str, *,
    user_id: Optional[int], agent_name: str, biz_type: str,
) -> Optional[Any]:
    """调用 LLM 并解析 JSON；不可用/失败/解析失败返回 None，由调用方降级。"""
    try:
        resp = get_llm().chat(
            system_prompt, user_prompt,
            user_id=user_id, agent_name=agent_name, biz_type=biz_type,
        )
        if not resp.get("success"):
            return None
        return extract_json(resp.get("content") or "")
    except Exception as exc:  # noqa: BLE001  AI 侧异常一律降级，不 500
        logger.warning(f"题库 AI 调用失败，降级规则引擎: {exc}")
        return None


def _chunks(items: List[Question], size: int = LLM_CHUNK_SIZE) -> List[List[Question]]:
    return [items[i:i + size] for i in range(0, len(items), size)]


def _items_of(parsed: Any) -> List[Any]:
    if isinstance(parsed, dict):
        for key in ("items", "questions", "data"):
            if isinstance(parsed.get(key), list):
                return parsed[key]
        return []
    return parsed if isinstance(parsed, list) else []


# ================================================================ 变式生成
def _rewrite_stem(stem: str, index: int) -> Tuple[str, bool]:
    """规则变式改写题干，返回 (新题干, 是否调整了数字)。

    - 优先换人称/情境实体（答案语义不变）；
    - 否则对数字做 +index 调整（需人工核对答案，调用方会清空 answer）；
    - 都不行则加「变式N：」前缀保证唯一。
    """
    text = str(stem or "").strip()
    for old, new in STEAM_SWAPS:
        if old in text:
            return text.replace(old, new, 1), False

    numeric = {"changed": False}

    def _replace(match: "re.Match") -> str:
        numeric["changed"] = True
        try:
            return str(int(match.group(0)) + index)
        except ValueError:
            return match.group(0)

    changed_text = re.sub(r"\d+", _replace, text)
    if numeric["changed"] and changed_text != text:
        return changed_text, True
    return f"变式{index}：{text}", False


def _fallback_variants(
    q: Question, count: int, difficulty: Optional[str],
) -> List[Dict[str, Any]]:
    """无 LLM 的规则模板：题干改写/换数据，只预览不落库。"""
    options = _load(q.options)
    items: List[Dict[str, Any]] = []
    for index in range(1, count + 1):
        stem, numeric = _rewrite_stem(q.stem, index)
        if numeric:
            answer = None
            note = "规则引擎变式：题干数值已调整，选项与答案需按新数据重新核对后录入。"
        else:
            answer = _json_safe(_load(q.answer))
            note = "规则引擎变式：仅改写题干表述/情境，答案沿用原题，请核对后录入。"
        analysis = _clean_str(q.analysis)
        items.append({
            "type": _normalize_type(q.type),
            "stem": stem,
            "options": options if isinstance(options, list) else None,
            "answer": answer,
            "analysis": (analysis + "\n" if analysis else "") + note,
            "difficulty": _normalize_difficulty(
                difficulty, _normalize_difficulty(q.difficulty)),
            "score": _normalize_score(q.score),
            "knowledge_point_id": q.knowledge_point_id,
        })
    return items


def _normalize_variants(
    parsed: Any, q: Question, count: int, difficulty: Optional[str],
) -> List[Dict[str, Any]]:
    """校验/裁剪模型输出的变式题。"""
    items: List[Dict[str, Any]] = []
    for raw in _items_of(parsed):
        if not isinstance(raw, dict):
            continue
        stem = _clean_str(raw.get("stem"), 3000)
        if not stem:
            continue
        options = _normalize_options(raw.get("options"))
        items.append({
            "type": _normalize_type(raw.get("type"), _normalize_type(q.type)),
            "stem": stem,
            "options": options if options is not None else (
                _load(q.options) if isinstance(_load(q.options), list) else None),
            "answer": _json_safe(raw.get("answer")),
            "analysis": _clean_str(raw.get("analysis"), 3000),
            "difficulty": _normalize_difficulty(
                difficulty or raw.get("difficulty"),
                _normalize_difficulty(q.difficulty)),
            "score": _normalize_score(raw.get("score"), _normalize_score(q.score)),
            "knowledge_point_id": _to_int(
                raw.get("knowledge_point_id"), q.knowledge_point_id),
        })
        if len(items) >= count:
            break
    return items


def _variant_prompt(
    db: Session, q: Question, count: int, difficulty: Optional[str],
) -> str:
    grades, subjects, kps = _name_maps(db, [q])
    kp = kps.get(q.knowledge_point_id) if q.knowledge_point_id else None
    original = {
        "type": _normalize_type(q.type),
        "stem": _clean_str(q.stem, MAX_STEM_PROMPT_CHARS),
        "options": _load(q.options),
        "answer": _load(q.answer),
        "analysis": _clean_str(q.analysis, MAX_ANALYSIS_PROMPT_CHARS),
        "difficulty": _normalize_difficulty(q.difficulty),
        "knowledge_point_name": kp.name if kp else "",
    }
    return (
        f"年级：{grades.get(q.grade_id, '未知')}\n"
        f"学科：{subjects.get(q.subject_id, '未知')}\n"
        f"知识点：{kp.name if kp else '（未关联）'}\n"
        f"要求难度：{difficulty or _normalize_difficulty(q.difficulty)}\n"
        f"请生成 {count} 道同考点变式题。\n\n"
        f"原题（JSON）：\n{json.dumps(original, ensure_ascii=False)}"
    )


@router.post("/variants", summary="AI 生成同考点变式题（预览）")
def question_variants(
    data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    user: User = Depends(require_perm(WRITE_PERM)),
):
    """按原题生成 count 道同考点变式（只预览不落库）。

    无 LLM / LLM 失败时返回规则改写模板并标记 `is_fallback=true`，不报 500。
    """
    qid = _to_int(data.get("id"))
    if not qid:
        raise BusinessException("请指定原题 id")
    q = _load_question(db, qid, user)

    count = _to_int(data.get("count"), DEFAULT_VARIANTS)
    if count is None:
        count = DEFAULT_VARIANTS
    count = max(1, min(count, MAX_VARIANTS))
    raw_difficulty = data.get("difficulty")
    difficulty: Optional[str] = None
    if raw_difficulty not in (None, ""):
        difficulty = str(raw_difficulty).strip().lower()
        if difficulty not in DIFFICULTIES:
            raise BusinessException("难度只能是 easy / medium / hard")

    check_agent_rate(db, user.id)

    fallback = _fallback_variants(q, count, difficulty)
    if not is_available():
        return ok({"items": fallback, "is_fallback": True},
                  message="当前未启用大模型，已返回规则引擎生成的变式预览")

    parsed = _call_llm_json(
        VARIANT_SYSTEM_PROMPT, _variant_prompt(db, q, count, difficulty),
        user_id=user.id, agent_name="question_ai_variants",
        biz_type="question_variants",
    )
    items = _normalize_variants(parsed, q, count, difficulty)
    if not items:
        logger.warning("变式生成 LLM 未返回有效 items，降级规则引擎")
        return ok({"items": fallback, "is_fallback": True},
                  message="AI 返回结果不可用，已降级为规则引擎变式")
    return ok({"items": items, "is_fallback": False},
              message="AI 变式生成完成（预览，未落库）")


# ================================================================ 批量补全
def _fallback_enrich_item(
    q: Question, grades: Dict[int, str],
    subjects: Dict[int, str], kp: Optional[KnowledgePoint],
) -> Dict[str, Any]:
    """规则补全：已有解析沿用；缺解析按答案/知识点拼模板；知识点/难度给建议。"""
    analysis = _clean_str(q.analysis)
    if not analysis:
        answer_text = _answer_text(_load(q.answer))
        kp_text = f"「{kp.name}」" if kp else (
            f"{subjects.get(q.subject_id, '本学科')}基础知识")
        parts = []
        if answer_text:
            parts.append(f"【参考答案】{answer_text}。")
        parts.append(f"本题考查{kp_text}。")
        parts.append("建议先明确已知条件，再按对应规则逐步推导，最后写出结论并检查。")
        analysis = "".join(parts)[:2000]
    return {
        "id": q.id,
        "analysis": analysis,
        "knowledge_point_id": kp.id if kp else q.knowledge_point_id,
        "knowledge_point_name": kp.name if kp else None,
        "difficulty": _normalize_difficulty(q.difficulty),
    }


def _fallback_enrich(db: Session, questions: List[Question]) -> List[Dict[str, Any]]:
    grades, subjects, _kps = _name_maps(db, questions)
    return [
        _fallback_enrich_item(q, grades, subjects, _suggest_kp(db, q))
        for q in questions
    ]


def _enrich_prompt(
    db: Session, questions: List[Question],
) -> str:
    grades, subjects, kps = _name_maps(db, questions)
    payload = [
        {
            "id": q.id,
            "type": _normalize_type(q.type),
            "stem": _clean_str(q.stem, MAX_STEM_PROMPT_CHARS),
            "answer": _load(q.answer),
            "analysis": _clean_str(q.analysis, MAX_ANALYSIS_PROMPT_CHARS),
            "knowledge_point_name": (
                kps.get(q.knowledge_point_id).name
                if q.knowledge_point_id in kps else ""),
            "difficulty": _normalize_difficulty(q.difficulty),
            "grade": grades.get(q.grade_id, ""),
            "subject": subjects.get(q.subject_id, ""),
        }
        for q in questions
    ]
    return ("请补全以下题目的解析/知识点/难度建议：\n"
            + json.dumps(payload, ensure_ascii=False))


def _merge_enrich(
    db: Session, questions: List[Question], parsed: Any,
    fallback: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], bool]:
    """把模型建议按 id 合并回请求顺序；漏掉/非法的字段沿用规则建议。"""
    by_id: Dict[int, Dict[str, Any]] = {}
    for raw in _items_of(parsed):
        if not isinstance(raw, dict):
            continue
        qid = _to_int(raw.get("id"))
        if qid:
            by_id[qid] = raw
    if not by_id:
        return fallback, False

    merged: List[Dict[str, Any]] = []
    for q, base in zip(questions, fallback):
        raw = by_id.get(q.id)
        if not raw:
            merged.append(base)
            continue
        analysis = _clean_str(raw.get("analysis"), 3000) or base["analysis"]
        kp = _existing_kp(db, raw.get("knowledge_point_id"))
        if kp is not None and kp.subject_id and q.subject_id \
                and kp.subject_id != q.subject_id:
            kp = None  # 跨学科知识点建议不可信，回退规则建议
        kp_id = kp.id if kp else base["knowledge_point_id"]
        kp_name = kp.name if kp else base["knowledge_point_name"]
        difficulty = _normalize_difficulty(
            raw.get("difficulty"), base["difficulty"])
        merged.append({
            "id": q.id,
            "analysis": analysis,
            "knowledge_point_id": kp_id,
            "knowledge_point_name": kp_name,
            "difficulty": difficulty,
        })
    return merged, True


@router.post("/enrich", summary="AI 批量补全题目解析/知识点（预览）")
def question_enrich(
    data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    user: User = Depends(require_perm(WRITE_PERM)),
):
    """对选中题目返回解析/知识点/难度建议（只预览不落库，ids ≤ 50）。"""
    ids = _unique_ids(data.get("ids"))
    questions = _load_questions(db, ids, user)

    check_agent_rate(db, user.id)

    fallback = _fallback_enrich(db, questions)
    if not is_available():
        return ok({"items": fallback, "is_fallback": True},
                  message="当前未启用大模型，已返回规则引擎补全建议")

    merged: List[Dict[str, Any]] = [dict(item) for item in fallback]
    index_by_id = {item["id"]: idx for idx, item in enumerate(merged)}
    any_ok = False
    for chunk in _chunks(questions):
        parsed = _call_llm_json(
            ENRICH_SYSTEM_PROMPT, _enrich_prompt(db, chunk),
            user_id=user.id, agent_name="question_ai_enrich",
            biz_type="question_enrich",
        )
        chunk_fallback = [merged[index_by_id[q.id]] for q in chunk]
        chunk_merged, chunk_ok = _merge_enrich(db, chunk, parsed, chunk_fallback)
        for q, item in zip(chunk, chunk_merged):
            merged[index_by_id[q.id]] = item
        any_ok = any_ok or chunk_ok

    if not any_ok:
        logger.warning("题目补全 LLM 未返回有效 items，降级规则引擎")
        return ok({"items": fallback, "is_fallback": True},
                  message="AI 返回结果不可用，已降级为规则引擎建议")
    return ok({"items": merged, "is_fallback": False},
              message="AI 补全建议已生成（预览，未落库）")


# ================================================================ 批量质检
def _has_placeholder(stem: str) -> bool:
    text = _plain_stem(stem)
    if not text or text in EMPTY_STEM_MARKS:
        return True
    return any(mark in text for mark in PLACEHOLDER_MARKS)


def _issue(code: str, message: str, severity: str) -> Dict[str, str]:
    return {"code": code, "message": message, "severity": severity}


def _rule_quality(db: Session, questions: List[Question]) -> List[Dict[str, Any]]:
    """确定性质检：缺答案/解析/知识点、难度异常、重复指纹、题干过短/占位符。"""
    fingerprints = {q.id: (q.fingerprint or _fingerprint(q.stem)) for q in questions}
    fp_counts: Dict[str, int] = {}
    for fp in fingerprints.values():
        if fp:
            fp_counts[fp] = fp_counts.get(fp, 0) + 1

    results: List[Dict[str, Any]] = []
    for q in questions:
        issues: List[Dict[str, str]] = []
        plain = _plain_stem(q.stem)
        if not plain:
            issues.append(_issue("empty_stem", "题干为空", "error"))
        elif len(plain) < SHORT_STEM_CHARS:
            issues.append(_issue(
                "short_stem", f"题干过短（{len(plain)} 字），信息可能不完整", "warning"))
        if _has_placeholder(q.stem):
            issues.append(_issue(
                "placeholder_stem", "题干疑似占位符/未填写内容", "error"))
        if not _has_answer(q):
            issues.append(_issue("missing_answer", "缺少答案", "error"))
        if not _clean_str(q.analysis):
            issues.append(_issue("missing_analysis", "缺少解析", "warning"))
        if not q.knowledge_point_id:
            issues.append(_issue("missing_knowledge", "未关联知识点", "warning"))
        if _normalize_difficulty(q.difficulty, default="") not in DIFFICULTIES:
            issues.append(_issue(
                "invalid_difficulty",
                f"难度值异常：{q.difficulty!r}（应为 easy/medium/hard）", "warning"))

        fp = fingerprints.get(q.id)
        if fp:
            duplicate = fp_counts.get(fp, 0) > 1
            if not duplicate:
                duplicate = db.scalar(
                    select(Question.id).where(
                        Question.fingerprint == fp, Question.id != q.id,
                    ).limit(1)
                ) is not None
            if duplicate:
                issues.append(_issue(
                    "duplicate_fingerprint", "与题库中其他题目题干完全重复", "error"))
        results.append({"id": q.id, "issues": issues})
    return results


AI_ISSUE_CODES = {"ai_ambiguous", "ai_option_problem", "ai_answer_mismatch", "ai_low_quality"}


def _quality_prompt(db: Session, questions: List[Question]) -> str:
    grades, subjects, _kps = _name_maps(db, questions)
    payload = [
        {
            "id": q.id,
            "type": _normalize_type(q.type),
            "stem": _clean_str(q.stem, MAX_STEM_PROMPT_CHARS),
            "options": _load(q.options),
            "answer": _load(q.answer),
            "analysis": _clean_str(q.analysis, MAX_ANALYSIS_PROMPT_CHARS),
            "grade": grades.get(q.grade_id, ""),
            "subject": subjects.get(q.subject_id, ""),
        }
        for q in questions
    ]
    return ("请对以下题目做质量检查：\n"
            + json.dumps(payload, ensure_ascii=False))


def _merge_quality_issues(
    questions: List[Question], parsed: Any,
) -> Tuple[Dict[int, List[Dict[str, str]]], bool]:
    """把模型问题列表按 id 合并（code 限定 ai_ 前缀，severity 白名单）。

    第二个返回值表示「本次 LLM 解析成功」——模型检查后没发现问题同样是成功，
    不能因为 issues 为空就误报 is_fallback=true。
    """
    by_id: Dict[int, List[Dict[str, str]]] = {}
    for raw in _items_of(parsed):
        if not isinstance(raw, dict):
            continue
        qid = _to_int(raw.get("id"))
        if not qid:
            continue
        issues: List[Dict[str, str]] = []
        for item in raw.get("issues") or []:
            if not isinstance(item, dict):
                continue
            message = _clean_str(item.get("message"), 300)
            if not message:
                continue
            code = _clean_str(item.get("code"))
            if code not in AI_ISSUE_CODES:
                code = "ai_low_quality"
            severity = _clean_str(item.get("severity"))
            issues.append(_issue(
                code, message, severity if severity in SEVERITIES else "warning"))
        if issues:
            by_id.setdefault(qid, []).extend(issues)
    return by_id, isinstance(parsed, (dict, list))


@router.post("/quality", summary="AI 批量质检题目（预览）")
def question_quality(
    data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    user: User = Depends(require_perm(WRITE_PERM)),
):
    """对选中题目做质量检查（只预览不落库，ids ≤ 50）。

    规则检查始终执行（缺答案/解析/知识点、难度异常、重复、过短/占位符）；
    LLM 可用时追加语义质量建议，`is_fallback=false` 表示 AI 也参与了检查。
    """
    ids = _unique_ids(data.get("ids"))
    questions = _load_questions(db, ids, user)

    check_agent_rate(db, user.id)

    results = _rule_quality(db, questions)
    is_fallback = True
    if is_available():
        by_id: Dict[int, List[Dict[str, str]]] = {}
        any_ok = False
        for chunk in _chunks(questions):
            parsed = _call_llm_json(
                QUALITY_SYSTEM_PROMPT, _quality_prompt(db, chunk),
                user_id=user.id, agent_name="question_ai_quality",
                biz_type="question_quality",
            )
            chunk_issues, chunk_ok = _merge_quality_issues(chunk, parsed)
            for qid, issues in chunk_issues.items():
                by_id.setdefault(qid, []).extend(issues)
            any_ok = any_ok or chunk_ok
        if any_ok:
            is_fallback = False
            result_by_id = {item["id"]: item for item in results}
            for qid, issues in by_id.items():
                if qid in result_by_id:
                    result_by_id[qid]["issues"].extend(issues)

    return ok({"items": results, "is_fallback": is_fallback},
              message=("质检完成（规则引擎，未启用大模型）" if is_fallback
                       else "质检完成"))
