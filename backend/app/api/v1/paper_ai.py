"""试卷 AI 接口：智能分析 / 候选题推荐（prefix `/question/papers`，路径 `/{paper_id}/ai/*`）。

契约见 docs/PAPER_V2.md §3：

- 权限：`paper:ai`（teacher/sys_admin）+ 试卷可读校验（创建者 / 公开共享 /
  `PaperShare` 接收人 / sys_admin）；学生无 `paper:ai`，403。
- `check_agent_rate`；无 LLM 时规则结果照常返回并标记 `is_fallback=true`；
  LLM 失败只降级，绝不 500；两个接口都**只读**（不落库、不改试卷）。
- 为与 question.py 的 paper 权限口径保持一致，本文件本地实现可读校验
  （不 import 并行改造中的 question.py 私有 helper），逻辑与
  `_assert_paper_readable` 相同。
"""
import json
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, Body, Depends
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.agents.llm import extract_json, get_llm, is_available
from app.api.deps import require_perm
from app.core.database import get_db
from app.core.exception import BusinessException, NotFoundException, PermissionException
from app.core.logger import get_logger
from app.core.rate_limit import check_agent_rate
from app.models import (
    Grade, KnowledgePoint, Paper, PaperItem, PaperShare, Question, QuestionBankType,
    QuestionStatus, Subject, User,
)
from app.utils.common import ok

logger = get_logger("paper-ai")

router = APIRouter(prefix="/question/papers", tags=["试卷 AI"])

PAPER_AI_PERM = "paper:ai"
DIFFICULTIES = ("easy", "medium", "hard")
DIFFICULTY_LABEL = {"easy": "简单", "medium": "中等", "hard": "困难"}
QUESTION_TYPE_LABEL = {
    "single": "单选题", "multiple": "多选题", "judge": "判断题", "blank": "填空题",
    "short": "简答题", "calc": "计算题", "material": "材料分析题", "composition": "作文题",
}
QUESTION_TYPE_ALIAS = {"subjective": "short", "essay": "composition"}
DEFAULT_RECOMMEND_COUNT = 5
MAX_RECOMMEND_COUNT = 20
MAX_SUGGESTIONS = 6
MAX_STEM_PROMPT_CHARS = 1200


# ================================================================ 通用工具
def _codes(user: User) -> set:
    return set(user.role_codes or [])


def _normalize_type(value: Any, default: str = "single") -> str:
    qtype = str(value or default).strip().lower()
    qtype = QUESTION_TYPE_ALIAS.get(qtype, qtype)
    return qtype if qtype in QUESTION_TYPE_LABEL else default


def _normalize_difficulty(value: Any) -> str:
    diff = str(value or "").strip().lower()
    return diff if diff in DIFFICULTIES else "unknown"


def _to_int(value: Any, default: Optional[int] = None) -> Optional[int]:
    if value in (None, ""):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _clean_str(value: Any, limit: Optional[int] = None) -> str:
    text = str(value or "").strip()
    return text[:limit] if limit else text


def _load(v: Optional[str]) -> Any:
    """DB JSON 文本 -> Python 对象（与 question.py 阅读口径一致）。"""
    if not v:
        return None
    try:
        return json.loads(v)
    except (TypeError, ValueError):
        return v


def _has_answer(q: Question) -> bool:
    value = _load(q.answer)
    if isinstance(value, (list, tuple, dict)):
        return bool(value)
    return bool(str(value or "").strip())


def _paper_items(db: Session, paper: Paper) -> List[PaperItem]:
    """按 sort_order 返回试卷题目项（用一次查询，不依赖惰性加载状态）。"""
    return list(db.scalars(
        select(PaperItem).where(PaperItem.paper_id == paper.id)
        .order_by(PaperItem.sort_order, PaperItem.id)
    ).all())


def _load_questions(db: Session, items: List[PaperItem]) -> List[Question]:
    """批量取试卷题目（含被删除题目的防御式跳过）。"""
    qids = [it.question_id for it in items if it.question_id]
    if not qids:
        return []
    rows = db.scalars(select(Question).where(Question.id.in_(qids))).all()
    found = {q.id: q for q in rows}
    return [found[qid] for qid in qids if qid in found]


def _assert_paper_readable(db: Session, paper: Paper, user: User) -> None:
    """可读校验：创建者 / 公开共享 / PaperShare 接收人 / sys_admin。"""
    if paper.creator_id == user.id or "sys_admin" in _codes(user):
        return
    if paper.is_shared:
        return
    shared = db.scalar(
        select(PaperShare.id).where(
            PaperShare.paper_id == paper.id,
            PaperShare.to_user_id == user.id,
        )
    )
    if not shared:
        raise PermissionException("无权查看该试卷")


def _load_paper(db: Session, paper_id: int, user: User) -> Paper:
    paper = db.get(Paper, paper_id)
    if not paper:
        raise NotFoundException("试卷不存在")
    _assert_paper_readable(db, paper, user)
    return paper


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
        logger.warning(f"试卷 AI 调用失败，降级规则引擎: {exc}")
        return None


ANALYZE_SYSTEM_PROMPT = """你是中国九年义务教育的资深教研员，负责审阅试卷并给出改进建议。

关注：难度结构是否合理（易/中/难比例）、题型是否多样、知识点覆盖是否均衡、
是否存在缺答案/缺解析/重复题/总分异常等问题。

要求：只输出 JSON，不要 markdown 代码块或解释文字。
输出格式：{"suggestions":["建议1","建议2"]}（建议 3~6 条，每条 40 字以内）"""

RECOMMEND_SYSTEM_PROMPT = """你是中国九年义务教育的资深命题教师，负责为试卷补充题目。

对每道候选题给出「为什么推荐」的一句话理由（结合试卷薄弱知识点或难度缺口，40 字以内）。

要求：只输出 JSON，不要 markdown 代码块或解释文字。
输出格式：{"items":[{"question_id":1,"reason":"推荐理由"}]}"""


# ================================================================ 分析
def _difficulty_ratio(questions: List[Question]) -> Dict[str, float]:
    total = len(questions)
    counts = {diff: 0 for diff in DIFFICULTIES}
    unknown = 0
    for q in questions:
        diff = _normalize_difficulty(q.difficulty)
        if diff in counts:
            counts[diff] += 1
        else:
            unknown += 1
    ratio = {
        diff: (round(counts[diff] / total, 4) if total else 0.0)
        for diff in DIFFICULTIES
    }
    if unknown:
        ratio["unknown"] = round(unknown / total, 4)
    return ratio


def _type_distribution(questions: List[Question]) -> Dict[str, int]:
    distribution: Dict[str, int] = {}
    for q in questions:
        qtype = _normalize_type(q.type)
        distribution[qtype] = distribution.get(qtype, 0) + 1
    return distribution


def _knowledge_coverage(
    db: Session, questions: List[Question],
) -> Tuple[List[Dict[str, Any]], Dict[int, KnowledgePoint]]:
    counts: Dict[int, int] = {}
    for q in questions:
        if q.knowledge_point_id:
            counts[q.knowledge_point_id] = counts.get(q.knowledge_point_id, 0) + 1
    if not counts:
        return [], {}
    kps = {
        kp.id: kp for kp in db.scalars(
            select(KnowledgePoint).where(KnowledgePoint.id.in_(counts))
        ).all()
    }
    total = len(questions)
    coverage = [
        {
            "knowledge_point_id": kp_id,
            "name": kps[kp_id].name if kp_id in kps else None,
            "count": count,
            "ratio": round(count / total, 4) if total else 0.0,
        }
        for kp_id, count in counts.items()
    ]
    coverage.sort(key=lambda x: (-x["count"], x["knowledge_point_id"]))
    return coverage, kps


def _issue(code: str, message: str, severity: str) -> Dict[str, str]:
    return {"code": code, "message": message, "severity": severity}


def _paper_issues(
    paper: Paper, items: List[PaperItem], questions: List[Question],
) -> List[Dict[str, str]]:
    issues: List[Dict[str, str]] = []
    qcount = len(questions)
    if not qcount:
        issues.append(_issue("empty_paper", "试卷暂无题目", "error"))
        return issues
    if len(items) != qcount:
        issues.append(_issue(
            "missing_question",
            f"{len(items) - qcount} 道题已被删除或不存在，请重新选题", "error"))

    missing_answer = sum(1 for q in questions if not _has_answer(q))
    if missing_answer:
        issues.append(_issue(
            "missing_answer", f"{missing_answer} 道题缺少答案", "error"))
    missing_analysis = sum(1 for q in questions if not _clean_str(q.analysis))
    if missing_analysis:
        issues.append(_issue(
            "missing_analysis", f"{missing_analysis} 道题缺少解析", "warning"))
    missing_knowledge = sum(1 for q in questions if not q.knowledge_point_id)
    if missing_knowledge:
        issues.append(_issue(
            "missing_knowledge", f"{missing_knowledge} 道题未关联知识点", "warning"))

    invalid_difficulty = sum(
        1 for q in questions if _normalize_difficulty(q.difficulty) == "unknown")
    if invalid_difficulty:
        issues.append(_issue(
            "invalid_difficulty",
            f"{invalid_difficulty} 道题难度值异常（应为 easy/medium/hard）",
            "warning"))

    seen_ids = set()
    duplicate_ids = 0
    for it in items:
        if it.question_id in seen_ids:
            duplicate_ids += 1
        seen_ids.add(it.question_id)
    if duplicate_ids:
        issues.append(_issue(
            "duplicate_question", f"试卷内重复引用同一道题 {duplicate_ids} 次", "error"))

    seen_fp = set()
    duplicate_stem = 0
    for q in questions:
        fp = q.fingerprint or _fingerprint(q.stem)
        if not fp:
            continue
        if fp in seen_fp:
            duplicate_stem += 1
        seen_fp.add(fp)
    if duplicate_stem:
        issues.append(_issue(
            "duplicate_stem", f"{duplicate_stem} 道题与其他题题干重复", "warning"))

    item_total = round(sum(float(it.score or 0) for it in items), 2)
    if abs(item_total - float(paper.total_score or 0)) > 0.01:
        issues.append(_issue(
            "paper_total_mismatch",
            f"试卷总分 {paper.total_score} 与题目分值合计 {item_total} 不一致",
            "warning"))
    return issues


def _fingerprint(stem: str) -> str:
    import hashlib
    import re

    norm = re.sub(r"\s+", "", re.sub(r"[（(].*?[)）]", "", str(stem or "")))
    return hashlib.md5(norm.encode()).hexdigest() if norm else ""


def _rule_suggestions(
    paper: Paper, items: List[PaperItem], questions: List[Question],
    analysis: Dict[str, Any],
) -> List[str]:
    suggestions: List[str] = []
    qcount = len(questions)
    if not qcount:
        return ["试卷暂无题目：请先添加题目，再做难度结构与知识点覆盖检查。"]
    ratio = analysis.get("difficulty_ratio") or {}
    if qcount >= 5 and float(ratio.get("hard") or 0) < 0.1:
        suggestions.append("难题占比偏低，建议补充 1~2 道 hard 难度题以提升区分度。")
    if float(ratio.get("easy") or 0) > 0.6:
        suggestions.append("简单题占比偏高，建议增加中等/困难题，平衡难度梯度。")
    if analysis.get("knowledge_point_count", 0) < min(3, qcount):
        suggestions.append("知识点覆盖偏集中，建议补充不同知识点的题目。")
    missing_analysis = sum(1 for q in questions if not _clean_str(q.analysis))
    if missing_analysis:
        suggestions.append(f"{missing_analysis} 道题缺少解析，建议补全解题思路与易错点。")
    missing_answer = sum(1 for q in questions if not _has_answer(q))
    if missing_answer:
        suggestions.append(f"{missing_answer} 道题缺少答案，发布前必须补齐标准答案。")
    if any(i["code"] == "duplicate_question" for i in analysis.get("issues") or []):
        suggestions.append("试卷内存在重复题，建议替换或删除重复项。")
    if any(i["code"] == "paper_total_mismatch"
           for i in analysis.get("issues") or []):
        suggestions.append("试卷总分与题目分值合计不一致，建议重新核算总分。")
    return suggestions[:MAX_SUGGESTIONS]


def _build_analysis(
    db: Session, paper: Paper, items: List[PaperItem],
) -> Dict[str, Any]:
    questions = _load_questions(db, items)
    coverage, _kps = _knowledge_coverage(db, questions)
    item_total = round(sum(float(it.score or 0) for it in items), 2)
    analysis: Dict[str, Any] = {
        "question_count": len(questions),
        "total_score": float(paper.total_score or 0),
        "item_score_sum": item_total,
        "difficulty_ratio": _difficulty_ratio(questions),
        "type_distribution": _type_distribution(questions),
        "knowledge_coverage": coverage,
        "knowledge_point_count": len(coverage),
        "uncovered_question_count": sum(1 for q in questions if not q.knowledge_point_id),
        "issues": _paper_issues(paper, items, questions),
    }
    return analysis


def _normalize_suggestions(parsed: Any) -> Optional[List[str]]:
    """解析 LLM 建议；无法识别返回 None。"""
    if isinstance(parsed, dict):
        raw = parsed.get("suggestions", parsed.get("items"))
    else:
        raw = parsed
    if not isinstance(raw, list):
        return None
    suggestions: List[str] = []
    for item in raw:
        if isinstance(item, dict):
            text = _clean_str(item.get("text") or item.get("suggestion")
                              or item.get("message"), 200)
        else:
            text = _clean_str(item, 200)
        if text and text not in suggestions:
            suggestions.append(text)
        if len(suggestions) >= MAX_SUGGESTIONS:
            break
    return suggestions


def _analyze_prompt(
    paper: Paper, analysis: Dict[str, Any], questions: List[Question],
) -> str:
    payload = {
        "paper_name": paper.name,
        "question_count": analysis["question_count"],
        "total_score": analysis["total_score"],
        "difficulty_ratio": analysis["difficulty_ratio"],
        "type_distribution": analysis["type_distribution"],
        "knowledge_coverage": analysis["knowledge_coverage"][:10],
        "issues": analysis["issues"],
        "stems": [_clean_str(q.stem, 160) for q in questions[:20]],
    }
    return ("请审阅以下试卷统计并给出改进建议：\n"
            + json.dumps(payload, ensure_ascii=False))


@router.post("/{paper_id}/ai/analyze", summary="AI 分析试卷（规则 + 建议）")
def analyze_paper(
    paper_id: int, db: Session = Depends(get_db),
    user: User = Depends(require_perm(PAPER_AI_PERM)),
):
    """分析试卷难度/题型/知识点覆盖并对问题给出建议（只读，不落库）。

    规则分析始终执行；LLM 可用且成功时补充建议并返回 `is_fallback=false`，
    无 LLM 或 LLM 失败时返回规则结果 + `is_fallback=true`，不报 500。
    """
    paper = _load_paper(db, paper_id, user)
    items = _paper_items(db, paper)

    check_agent_rate(db, user.id)

    analysis = _build_analysis(db, paper, items)
    questions = _load_questions(db, items)
    suggestions = _rule_suggestions(paper, items, questions, analysis)
    is_fallback = True
    if is_available() and analysis["question_count"]:
        parsed = _call_llm_json(
            ANALYZE_SYSTEM_PROMPT,
            _analyze_prompt(paper, analysis, questions),
            user_id=user.id, agent_name="paper_ai_analyze",
            biz_type="paper_analyze",
        )
        llm_suggestions = _normalize_suggestions(parsed)
        if parsed is not None and llm_suggestions is not None:
            is_fallback = False
            for text in llm_suggestions:
                if text not in suggestions:
                    suggestions.append(text)
            suggestions = suggestions[:MAX_SUGGESTIONS]

    return ok({
        "analysis": analysis,
        "suggestions": suggestions,
        "is_fallback": is_fallback,
    }, message=("试卷分析完成（规则引擎，未启用大模型）" if is_fallback
                else "试卷分析完成"))


# ================================================================ 推荐
def _accessible_question_filter(user: User):
    """候选题可见性：sys_admin 全量；其他教师只看公共题库 + 本人私有题。"""
    if "sys_admin" in _codes(user):
        return None
    return or_(
        Question.bank_type == QuestionBankType.PUBLIC.value,
        Question.owner_id == user.id,
    )


def _recommend_rules(
    db: Session, paper: Paper, user: User, count: int,
) -> List[Dict[str, Any]]:
    """规则推荐：优先补「覆盖不足的知识点」+「占比最低的难度」。"""
    items = _paper_items(db, paper)
    in_paper_ids = {it.question_id for it in items}
    questions = _load_questions(db, items)
    coverage, kps = _knowledge_coverage(db, questions)

    # 难度缺口：卷内占比最低的难度优先补
    ratio = _difficulty_ratio(questions)
    gap_difficulties = sorted(
        DIFFICULTIES, key=lambda d: (float(ratio.get(d) or 0), DIFFICULTIES.index(d)))
    target_diff = gap_difficulties[0]

    # 薄弱知识点 = 卷内覆盖题数最少的 1~3 个；无覆盖时退化为无偏好
    weak_kp_ids: List[int] = []
    if coverage:
        min_count = min(x["count"] for x in coverage)
        weak_kp_ids = [
            x["knowledge_point_id"] for x in coverage
            if x["count"] == min_count
        ][:3]
    weak_kp_names = {
        kp_id: (kps[kp_id].name if kp_id in kps else None) for kp_id in weak_kp_ids
    }

    stmt = select(Question).where(
        Question.grade_id == paper.grade_id,
        Question.subject_id == paper.subject_id,
        Question.status == QuestionStatus.PUBLISHED.value,
    )
    if in_paper_ids:
        stmt = stmt.where(Question.id.notin_(in_paper_ids))
    access = _accessible_question_filter(user)
    if access is not None:
        stmt = stmt.where(access)
    # 多取一些再按「知识点/难度匹配」排序，避免直接 DB 排序丢失规则优先级
    candidates = db.scalars(
        stmt.order_by(Question.usage_count.asc(), Question.id.asc())
        .limit(max(count * 20, 100))
    ).all()

    def rank(q: Question) -> Tuple[int, int]:
        score = 0
        if q.difficulty == target_diff:
            score += 100
        elif q.difficulty in gap_difficulties[:2]:
            score += 40
        if q.knowledge_point_id in weak_kp_ids:
            score += 30
        if q.knowledge_point_id:
            score += 5
        return (-score, q.usage_count or 0)

    candidates.sort(key=rank)
    picked = candidates[:count]

    kp_ids = {q.knowledge_point_id for q in picked if q.knowledge_point_id}
    if kp_ids:
        kp_map = {
            kp.id: kp for kp in db.scalars(
                select(KnowledgePoint).where(KnowledgePoint.id.in_(kp_ids))
            ).all()
        }
    else:
        kp_map = {}

    results: List[Dict[str, Any]] = []
    for q in picked:
        kp = kp_map.get(q.knowledge_point_id) if q.knowledge_point_id else None
        reasons: List[str] = []
        if kp and q.knowledge_point_id in weak_kp_ids:
            reasons.append(f"补充「{kp.name}」覆盖（卷内仅 {coverage_count(coverage, q.knowledge_point_id)} 题）")
        if q.difficulty == target_diff:
            reasons.append(
                f"补齐{DIFFICULTY_LABEL.get(target_diff, target_diff)}难度"
                f"（卷内占比 {float(ratio.get(target_diff) or 0):.0%}）")
        if not reasons:
            reasons.append("同年级同学科已发布题目，可用于扩充题量")
        results.append({
            "question_id": q.id,
            "stem": q.stem,
            "type": _normalize_type(q.type),
            "difficulty": _normalize_difficulty(q.difficulty),
            "score": float(q.score or 0),
            "knowledge_point_name": kp.name if kp else None,
            "reason": "；".join(reasons)[:120],
        })
    return results


def coverage_count(coverage: List[Dict[str, Any]], kp_id: int) -> int:
    for item in coverage:
        if item.get("knowledge_point_id") == kp_id:
            return int(item.get("count") or 0)
    return 0


def _recommend_prompt(
    paper: Paper, analysis: Dict[str, Any], candidates: List[Dict[str, Any]],
) -> str:
    payload = {
        "paper_name": paper.name,
        "difficulty_ratio": analysis["difficulty_ratio"],
        "weak_knowledge_coverage": analysis["knowledge_coverage"][:10],
        "candidates": [
            {
                "question_id": item["question_id"],
                "type": item["type"],
                "difficulty": item["difficulty"],
                "knowledge_point_name": item["knowledge_point_name"],
                "stem": _clean_str(item["stem"], MAX_STEM_PROMPT_CHARS),
            }
            for item in candidates
        ],
    }
    return ("请为以下试卷的候选题各写一句推荐理由：\n"
            + json.dumps(payload, ensure_ascii=False))


def _merge_recommend_reasons(
    candidates: List[Dict[str, Any]], parsed: Any,
) -> Tuple[List[Dict[str, Any]], bool]:
    """用 LLM 理由覆盖规则理由；id 不匹配/理由为空时保留规则理由。"""
    raw_items: List[Any] = []
    if isinstance(parsed, dict):
        raw_items = parsed.get("items") or parsed.get("candidates") or []
    elif isinstance(parsed, list):
        raw_items = parsed
    reason_by_id: Dict[int, str] = {}
    for raw in raw_items:
        if not isinstance(raw, dict):
            continue
        qid = _to_int(raw.get("question_id") or raw.get("id"))
        reason = _clean_str(raw.get("reason"), 120)
        if qid and reason:
            reason_by_id[qid] = reason
    if not reason_by_id:
        return candidates, False
    merged: List[Dict[str, Any]] = []
    for item in candidates:
        copy = dict(item)
        if copy["question_id"] in reason_by_id:
            copy["reason"] = reason_by_id[copy["question_id"]]
        merged.append(copy)
    return merged, True


@router.post("/{paper_id}/ai/recommend", summary="AI 推荐候选题")
def recommend_questions(
    paper_id: int, data: Dict[str, Any] = Body(default={}),
    db: Session = Depends(get_db),
    user: User = Depends(require_perm(PAPER_AI_PERM)),
):
    """基于试卷薄弱知识点/难度缺口推荐候选题（只读，不落库）。

    候选范围：同年级同学科、published、当前用户可访问（公共题库/本人私有）、
    且不在卷中的题目。无 LLM 时返回规则推荐 + `is_fallback=true`；
    LLM 可用时仅优化推荐理由。
    """
    if not isinstance(data, dict):
        raise BusinessException("请求体必须为对象")
    count = _to_int(data.get("count"), DEFAULT_RECOMMEND_COUNT)
    if count is None:
        count = DEFAULT_RECOMMEND_COUNT
    count = max(1, min(count, MAX_RECOMMEND_COUNT))

    paper = _load_paper(db, paper_id, user)
    items = _paper_items(db, paper)

    check_agent_rate(db, user.id)

    candidates = _recommend_rules(db, paper, user, count)
    is_fallback = True
    if candidates and is_available():
        analysis = _build_analysis(db, paper, items)
        parsed = _call_llm_json(
            RECOMMEND_SYSTEM_PROMPT,
            _recommend_prompt(paper, analysis, candidates),
            user_id=user.id, agent_name="paper_ai_recommend",
            biz_type="paper_recommend",
        )
        merged, ok_llm = _merge_recommend_reasons(candidates, parsed)
        if ok_llm:
            candidates = merged
            is_fallback = False

    return ok({"items": candidates, "is_fallback": is_fallback},
              message=("候选题目已推荐（规则引擎，未启用大模型）" if is_fallback
                       else "候选题目已推荐"))
