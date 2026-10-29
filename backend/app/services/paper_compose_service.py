"""标准组卷引擎（V3）。

替代 `paper_agent.PaperComposerAgent._compose` 的规则抽题部分，修掉三个已实证缺陷：

1. **`int()` 截断小数权重** —— 旧实现 `DIFFICULTY_WEIGHT = {"easy":0.3,...}`
   经 `int(v)` 变成 0，`total_items = sum(int(v)) = 0`，再用 `or 10` 兜底，
   于是「按题型分布抽题」永远抽 0 题。本模块一律用**整数**（百分制）与
   整数题量，且用 `round()` 分配余数，不丢题。
2. **放宽难度时丢失 kp 过滤** —— 旧实现 `if picked < qty` 分支重建 stmt 时
   漏了 `knowledge_point_id.in_(kp_ids)`，导致"指定知识点组卷"在题库不足时
   悄悄抽到范围外的题。本模块所有分支共用同一个 `_base_stmt()`。
3. **大题号恒为「一、」** —— 旧实现 `section_name` 硬编码 `f"一、{...}"`，
   单选/填空/简答三节全叫「一、」。本模块按 `section_sort` 生成中文序号。

设计约束
--------
- **纯函数式**：不 commit、不写库，只返回结构化计划。落库由调用方负责，
  这样"预览"与"保存"走同一条路径，不会出现两条路径行为不一致。
- **标准驱动**：题型结构全部来自 `ExamStandard.sections`，不硬编码。
  管理员改标准 → 组卷行为立刻改变，无需改代码。
- **来源三策略**：bank_only / ai_only / bank_first（默认）。
  `bank_first` 在题库不足时标记缺口，由上层决定是否调 AI 补。
"""
import json
import logging
import math
from typing import Any, Dict, List, Optional, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    ExamStandard, KnowledgePoint, PaperItem, Question, QuestionStatus,
    Task,
)

logger = logging.getLogger(__name__)

TYPE_LABEL = {
    "single": "单选题", "multiple": "多选题", "judge": "判断题", "blank": "填空题",
    "short": "简答题", "calc": "计算题", "material": "材料分析题", "composition": "作文题",
}
# 中文大题序号：组卷可能超过 10 个大题（极少但存在），补到 20
CN_NUM = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十",
          "十一", "十二", "十三", "十四", "十五", "十六", "十七", "十八",
          "十九", "二十"]

SOURCE_BANK_ONLY = "bank_only"
SOURCE_AI_ONLY = "ai_only"
SOURCE_BANK_FIRST = "bank_first"
VALID_SOURCES = {SOURCE_BANK_ONLY, SOURCE_AI_ONLY, SOURCE_BANK_FIRST}

DEFAULT_DIFFICULTY = {"easy": 70, "medium": 20, "hard": 10}


class ComposeError(Exception):
    """组卷参数错误（由上层转 BusinessException）。"""


# ---------------------------------------------------------------- 参数解析
def normalize_difficulty(ratio: Any) -> Dict[str, int]:
    """难度分布归一化为百分制整数。

    容错三种历史写法：
    - 小数权重 {"easy":0.3,...}      → 乘 100 并取整（旧默认值）
    - 整数 {"easy":3,"medium":5,...} → 视为比例，按合计折算到 100
    - 百分数 {"easy":70,...}         → 原样使用
    合计不为 100 时按比例折算并补齐余数，保证 sum==100。
    """
    if not ratio:
        return dict(DEFAULT_DIFFICULTY)
    if not isinstance(ratio, dict):
        raise ComposeError("难度分布格式错误")

    raw: Dict[str, float] = {}
    for key in ("easy", "medium", "hard"):
        try:
            raw[key] = float(ratio.get(key) or 0)
        except (TypeError, ValueError):
            raise ComposeError(f"难度 {key} 必须为数字")
        if raw[key] < 0:
            raise ComposeError(f"难度 {key} 不能为负")

    total = sum(raw.values())
    if total <= 0:
        return dict(DEFAULT_DIFFICULTY)

    # 已经是百分制就原样用；否则按比例折算
    if abs(total - 100) < 0.01:
        result = {k: int(round(v)) for k, v in raw.items()}
        # 各档独立 round 可能使合计偏离 100（如 33.34/33.33/33.33 → 33/33/33=99）。
        # 把差额补给**小数部分最大**的档（drift<0 时从最小者扣），保证三档之和
        # 精确为 100（BUG-014）。不修的话前端会看到难度占比合计 99%/101%。
        drift = 100 - sum(result.values())
        if drift:
            order = sorted(
                ("easy", "medium", "hard"),
                key=lambda k: raw[k] - int(raw[k]),
                reverse=drift > 0,
            )
            for i in range(abs(drift)):
                result[order[i % len(order)]] += 1 if drift > 0 else -1
        return {k: max(0, v) for k, v in result.items()}

    scaled = {k: v / total * 100 for k, v in raw.items()}
    result = {k: int(math.floor(v)) for k, v in scaled.items()}
    # 余数补给小数部分最大的项，保证合计精确为 100
    remain = 100 - sum(result.values())
    if remain > 0:
        order = sorted(scaled.items(), key=lambda kv: kv[1] - math.floor(kv[1]), reverse=True)
        for i in range(remain):
            result[order[i % len(order)][0]] += 1
    return result


def split_by_difficulty(count: int, ratio: Dict[str, int]) -> Dict[str, int]:
    """按难度比例把 count 道题拆到三档。

    关键：**余数补给占比最大的档位**，而不是逐档 round 后不管。
    如果用 `round` 各档独立取整，3 档合计可能与 count 差 1~2，
    最终题量就不等于教师要求的题量——这正是旧实现丢题的另一种表现。
    """
    if count <= 0:
        return {"easy": 0, "medium": 0, "hard": 0}
    total = sum(ratio.values()) or 100
    result: Dict[str, int] = {}
    for key in ("easy", "medium", "hard"):
        result[key] = int(math.floor(count * ratio.get(key, 0) / total))

    remain = count - sum(result.values())
    if remain > 0:
        # 余数优先给比例最高的档（7:2:1 时给 easy），保证"简单题多"的直觉
        order = sorted(("easy", "medium", "hard"),
                       key=lambda k: ratio.get(k, 0), reverse=True)
        for i in range(remain):
            result[order[i % len(order)]] += 1
    return result


def parse_sections(standard: Optional[ExamStandard]) -> List[Dict[str, Any]]:
    """读取标准的题型结构（含防御式校验）。"""
    if not standard or not standard.sections:
        return []
    try:
        sections = json.loads(standard.sections)
    except (json.JSONDecodeError, TypeError):
        logger.error("命题标准 %s 的 sections 不是合法 JSON", standard.id)
        return []
    if not isinstance(sections, list):
        return []
    result: List[Dict[str, Any]] = []
    for idx, raw in enumerate(sections, start=1):
        if not isinstance(raw, dict):
            continue
        code = str(raw.get("code") or "").strip().lower()
        if code not in TYPE_LABEL:
            logger.error("命题标准 %s 含非法题型 %r，已忽略", standard.id, code)
            continue
        try:
            count = int(raw.get("count") or 0)
            score_per = float(raw.get("score_per") or 0)
        except (TypeError, ValueError):
            continue
        if count <= 0 or score_per <= 0:
            continue
        result.append({
            "code": code,
            "name": str(raw.get("name") or TYPE_LABEL[code])[:64],
            "count": count,
            "score_per": score_per,
            "difficulty": str(raw.get("difficulty") or "medium"),
            "sort": int(raw.get("sort") or idx),
        })
    result.sort(key=lambda s: s["sort"])
    return result


def default_sections(total_score: float = 100, count: int = 20) -> List[Dict[str, Any]]:
    """无标准可用时的兜底结构：单选题为主，分值均摊后补齐总分。"""
    count = max(1, count)
    score_per = round(total_score / count, 2)
    return [{
        "code": "single", "name": "一、单选题",
        "count": count, "score_per": score_per,
        "difficulty": "medium", "sort": 1,
    }]


def generic_sections(total_score: float = 100) -> List[Dict[str, Any]]:
    """通用题型结构（无命题标准可用时）：单选 40% / 填空 20% / 解答 40%。

    **这是 A（组卷兜底）与 B（标准草案生成）共用的唯一实现**：两处各写一套
    必然漂移——兜底卷与按草案生成的卷结构不一致，教师会以为是 bug。

    题量刻意取 10/5/5（共 20 题）：这样每档 `score_per = 总分×占比/题量`
    恰好等于「总分×0.04 / 0.04 / 0.08」，对任意整数总分都能精确到两位小数，
    不会出现「合计 99.98 分、与总分差两分钱」这种教师一眼就会质疑的问题。
    （早期用 10/6/4，20÷6 除不尽，实测合计 99.98。）

    它不是权威结构，只保证「结构完整、总分对得上、题型不至于单一」，
    因此调用方必须把「已使用通用结构」明确告诉教师。
    """
    plan = [
        ("single", "一、单选题", 0.40, 10, "easy"),
        ("blank", "二、填空题", 0.20, 5, "medium"),
        ("short", "三、解答题", 0.40, 5, "medium"),
    ]
    total = float(total_score or 100)
    out: List[Dict[str, Any]] = []
    prev_sum = 0.0
    for idx, (code, name, share, count, diff) in enumerate(plan, start=1):
        if idx == len(plan):
            # 最后一档用「总分 - 前面各档之和」，吸收任何取整误差
            sec_total = round(total - prev_sum, 2)
        else:
            sec_total = round(total * share, 2)
        score_per = round(sec_total / count, 2) if count else 0
        prev_sum = round(prev_sum + count * score_per, 2)
        out.append({
            "code": code, "name": name, "count": count,
            "score_per": score_per, "difficulty": diff, "sort": idx,
        })
    return out


# ---------------------------------------------------------------- 组卷引擎
class ComposePlan:
    """组卷结果（预览态）。"""

    def __init__(self) -> None:
        self.items: List[Dict[str, Any]] = []
        self.gaps: List[Dict[str, Any]] = []       # 题库缺口（供 AI 补题/提示）
        self.used_question_ids: set = set()
        self.kp_coverage: Dict[str, int] = {}
        self.excluded_count = 0                    # 因"近 3 次重复"被排除的题量
        # 去重把某大题整段清空时，放宽去重后复用的题量（0 = 没放宽）
        self.relaxed_count = 0

    @property
    def total_score(self) -> float:
        return round(sum(float(i["score"]) for i in self.items), 2)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "items": self.items,
            "item_count": len(self.items),
            "total_score": self.total_score,
            "gaps": self.gaps,
            "kp_coverage": self.kp_coverage,
            "excluded_count": self.excluded_count,
            "relaxed_count": self.relaxed_count,
        }


def _recent_question_ids(
    db: Session, *, grade_id: int, subject_id: int, exclude_paper_id: Optional[int],
    recent_n: int = 3,
) -> set:
    """近 N 次被使用的题目 id（用于「不与近 3 次考试重复」）。

    口径：取本年级本学科**最近 N 份已下发任务**所用试卷里的全部题目。
    用 Task.created_at 排序而非 Paper.updated_at——学生真正"考过"的是任务，
    教师改卷不改时间线。
    """
    if recent_n <= 0:
        return set()
    stmt = (
        select(Task.paper_id)
        .where(Task.grade_id == grade_id, Task.subject_id == subject_id)
        .order_by(Task.created_at.desc())
        .limit(recent_n)
    )
    if exclude_paper_id:
        stmt = stmt.where(Task.paper_id != exclude_paper_id)
    paper_ids = [r for r in db.scalars(stmt).all() if r]
    if not paper_ids:
        return set()
    rows = db.scalars(
        select(PaperItem.question_id).where(PaperItem.paper_id.in_(paper_ids))
    ).all()
    return {int(r) for r in rows if r}


def _base_stmt(*, grade_id: int, subject_id: int, qtype: str,
               kp_ids: Sequence[int], difficulty: Optional[str],
               exclude_ids: set):
    """统一的基础查询。

    **所有**抽题分支（含放宽条件的那一支）都必须走这里，
    否则知识范围会在"放宽"时被悄悄丢掉——这是旧实现的 P1 缺陷。
    """
    stmt = select(Question).where(
        Question.grade_id == grade_id,
        Question.subject_id == subject_id,
        Question.type == qtype,
        Question.status == QuestionStatus.PUBLISHED.value,
    )
    if kp_ids:
        stmt = stmt.where(Question.knowledge_point_id.in_(list(kp_ids)))
    if difficulty:
        stmt = stmt.where(Question.difficulty == difficulty)
    if exclude_ids:
        stmt = stmt.where(Question.id.notin_(list(exclude_ids)))
    # 使用次数少的优先：避免同一批题反复出现在每张卷子里
    return stmt.order_by(Question.usage_count.asc(), Question.id.asc())


def compose(
    db: Session,
    *,
    grade_id: int,
    subject_id: int,
    standard: Optional[ExamStandard] = None,
    sections: Optional[List[Dict[str, Any]]] = None,
    difficulty_ratio: Optional[Dict[str, int]] = None,
    kp_ids: Optional[Sequence[int]] = None,
    source_strategy: str = SOURCE_BANK_FIRST,
    avoid_recent: bool = True,
    recent_n: int = 3,
    avoid_duplicate_kp: bool = True,
    exclude_paper_id: Optional[int] = None,
    total_score_override: Optional[float] = None,
) -> ComposePlan:
    """按标准结构从题库抽题，返回预览计划（不写库）。

    source_strategy:
    - bank_only：只用题库。抽不满就留缺口，不补。
    - ai_only：完全不用题库（返回空计划 + 全部缺口，由上层调 AI 生成）。
    - bank_first：题库优先，缺口标记出来供上层补题。
    """
    if source_strategy not in VALID_SOURCES:
        raise ComposeError(f"出题来源不合法：{source_strategy}")

    plan = ComposePlan()
    kp_ids = [int(k) for k in (kp_ids or []) if k]
    ratio = normalize_difficulty(difficulty_ratio)
    sections = sections or parse_sections(standard) or default_sections()

    if source_strategy == SOURCE_AI_ONLY:
        # 全 AI：不需要抽题，只把结构换算成缺口清单
        for sec in sections:
            plan.gaps.append({
                "code": sec["code"], "name": sec["name"],
                "need": int(sec["count"]), "got": 0,
                "score_per": sec["score_per"],
                "difficulty": sec.get("difficulty", "medium"),
            })
        return plan

    exclude = set()
    if avoid_recent:
        exclude = _recent_question_ids(
            db, grade_id=grade_id, subject_id=subject_id,
            exclude_paper_id=exclude_paper_id, recent_n=recent_n,
        )
        plan.excluded_count = len(exclude)

    # 知识点重复控制：同一知识点最多出 ceil(count / kp 数) 题；
    # 未指定知识点时按"总题量 / 5"限流，避免一张卷子全考同一个点。
    total_need = sum(int(s["count"]) for s in sections)
    if avoid_duplicate_kp:
        if kp_ids:
            kp_cap = max(1, math.ceil(total_need / max(1, len(kp_ids))))
        else:
            kp_cap = max(1, math.ceil(total_need / 5))
    else:
        kp_cap = total_need
    kp_used: Dict[int, int] = {}

    for sec in sections:
        code = sec["code"]
        want = int(sec["count"])
        score_per = float(sec["score_per"])
        sec_difficulty = sec.get("difficulty") or "medium"

        picked = _pick_for_section(
            db, grade_id=grade_id, subject_id=subject_id, qtype=code,
            want=want, kp_ids=kp_ids, difficulty_ratio=ratio,
            prefer_difficulty=sec_difficulty, exclude=exclude,
            kp_used=kp_used, kp_cap=kp_cap,
        )
        # 「忽略近 N 次去重」的兜底在 `_pick_for_section` 第三级内完成；
        # 这里只统计「本应被去重排除、但为了不出白卷而复用」的题量，
        # 由上层如实告知教师（复用老题必须是可见的，不能悄悄发生）。
        if exclude:
            plan.relaxed_count += sum(1 for q in picked if q.id in exclude)

        for q in picked:
            kp_name = plan.kp_coverage
            kp = db.get(KnowledgePoint, q.knowledge_point_id) if q.knowledge_point_id else None
            label = kp.name if kp else "综合"
            kp_name[label] = kp_name.get(label, 0) + 1
            plan.used_question_ids.add(q.id)
            plan.items.append({
                "question_id": q.id,
                "type": q.type,
                "type_label": TYPE_LABEL.get(q.type, q.type),
                "stem": q.stem,
                "difficulty": q.difficulty,
                "score": round(score_per, 2),
                "section_code": code,
                "section_name": sec["name"],
                "section_sort": sec["sort"],
                "knowledge_point_id": q.knowledge_point_id,
                "knowledge_point_name": label,
            })

        if len(picked) < want:
            plan.gaps.append({
                "code": code, "name": sec["name"],
                "need": want, "got": len(picked),
                "score_per": score_per,
                "difficulty": sec_difficulty,
            })

    # 卷面总分与标准总分不符时，按比例把差额摊到各题（保持题型内均分）
    if total_score_override and plan.items:
        _rescale_scores(plan.items, float(total_score_override))

    _renumber(plan.items)
    return plan


def _pick_for_section(
    db: Session, *, grade_id: int, subject_id: int, qtype: str, want: int,
    kp_ids: Sequence[int], difficulty_ratio: Dict[str, int],
    prefer_difficulty: str, exclude: set,
    kp_used: Dict[int, int], kp_cap: int,
) -> List[Question]:
    """单个大题抽题：先按难度配额抽，不够再放宽难度（**保留**知识点过滤）。

    三级兜底，每一级都走 `_base_stmt`：
    1. 严格：题型 + 难度配额 + 知识点范围
    2. 放宽难度：题型 + 知识点范围（知识点不能放宽——那是教师的硬约束）
    3. 最后兜底：题型 + 知识点范围，忽略近 N 次去重（题库实在不足时，
       宁可重复也不能交空白卷；但会在 gaps 里体现缺口）
    """
    picked: List[Question] = []
    picked_ids: set = set()

    def _take(candidates: List[Question], limit: int, *,
              ignore_exclude: bool = False) -> None:
        for q in candidates:
            if len(picked) >= want:
                return
            # ignore_exclude=True 用于第三级兜底：SQL 已经不再过滤"近 N 次重复"，
            # 这里若仍按 exclude 丢弃，整个兜底就是空操作（实测：小题库开去重后
            # 整卷 0 题，且 gaps 显示"题库仅有 0 题"，实际有题只是全被排除）。
            if q.id in picked_ids or (not ignore_exclude and q.id in exclude):
                continue
            # 知识点限流
            kp_id = q.knowledge_point_id
            if kp_id and kp_used.get(kp_id, 0) >= kp_cap:
                continue
            picked.append(q)
            picked_ids.add(q.id)
            if kp_id:
                kp_used[kp_id] = kp_used.get(kp_id, 0) + 1

    # 1) 严格：按难度配额
    quota = split_by_difficulty(want, difficulty_ratio)
    for diff in ("easy", "medium", "hard"):
        need = quota.get(diff, 0)
        if need <= 0:
            continue
        rows = db.scalars(
            _base_stmt(grade_id=grade_id, subject_id=subject_id, qtype=qtype,
                       kp_ids=kp_ids, difficulty=diff, exclude_ids=exclude)
            .limit(need * 4)
        ).all()
        _take(list(rows), need)

    # 2) 放宽难度（知识点范围保持不变）
    if len(picked) < want:
        rows = db.scalars(
            _base_stmt(grade_id=grade_id, subject_id=subject_id, qtype=qtype,
                       kp_ids=kp_ids, difficulty=None, exclude_ids=exclude)
            .limit((want - len(picked)) * 5)
        ).all()
        _take(list(rows), want - len(picked))

    # 3) 最后兜底：忽略"近 N 次重复"限制（题库实在不足时宁可重复，也不能交白卷）
    if len(picked) < want and exclude:
        rows = db.scalars(
            _base_stmt(grade_id=grade_id, subject_id=subject_id, qtype=qtype,
                       kp_ids=kp_ids, difficulty=None, exclude_ids=set())
            .limit((want - len(picked)) * 5)
        ).all()
        _take(list(rows), want - len(picked), ignore_exclude=True)

    return picked


def _rescale_scores(items: List[Dict[str, Any]], target_total: float) -> None:
    """把卷面总分调整到 target_total，按原分值比例缩放。

    只改 score 不动题目：教师改"试卷总分"时不应清空已选题目。
    """
    current = sum(float(i["score"]) for i in items)
    if current <= 0 or abs(current - target_total) < 0.01:
        return
    factor = target_total / current
    for it in items:
        it["score"] = round(float(it["score"]) * factor, 2)
    # 缩放误差补到最后一题，保证合计精确
    drift = round(target_total - sum(float(i["score"]) for i in items), 2)
    if drift and items:
        items[-1]["score"] = round(float(items[-1]["score"]) + drift, 2)


def _renumber(items: List[Dict[str, Any]]) -> None:
    """按大题顺序 + 组内顺序重排 sort_order，并生成正确的中文大题号。

    旧实现把 section_name 硬编码成「一、」是显式 bug；这里按 section_sort
    取中文序号，同时把大题名里可能已带的「一、」前缀剥掉再拼，
    避免出现「一、一、单选题」。
    """
    items.sort(key=lambda i: (i.get("section_sort", 0), i.get("question_id", 0)))
    section_index: Dict[str, int] = {}
    for it in items:
        code = it.get("section_code") or it.get("type")
        if code not in section_index:
            section_index[code] = len(section_index) + 1
        idx = section_index[code]
        prefix = CN_NUM[idx - 1] if idx <= len(CN_NUM) else str(idx)
        raw_name = str(it.get("section_name") or TYPE_LABEL.get(code, "综合题"))
        # 剥掉旧前缀（一、/1、/（一）等）
        name = raw_name
        for sep in ("、", "."):
            head, _, tail = name.partition(sep)
            if head in CN_NUM or head.isdigit():
                name = tail.strip() or raw_name
                break
        it["section_name"] = f"{prefix}、{name}"
        it["section_sort"] = idx
        it["section_index"] = idx
    for i, it in enumerate(items, start=1):
        it["sort_order"] = i


# ---------------------------------------------------------------- 报告
def build_reports(
    items: List[Dict[str, Any]], difficulty_target: Optional[Dict[str, int]] = None,
    sections_plan: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """生成三份报告：难度分布 / 知识点覆盖 / 题型结构。

    需求要求「生成覆盖率、难度、题型三份报告」，因此统一在此产出，
    避免前端各算一套导致口径漂移。
    """
    difficulty_target = difficulty_target or DEFAULT_DIFFICULTY
    n = len(items) or 1

    diff_count: Dict[str, int] = {}
    type_count: Dict[str, int] = {}
    type_score: Dict[str, float] = {}
    kp_count: Dict[str, int] = {}
    for it in items:
        diff = it.get("difficulty") or "medium"
        diff_count[diff] = diff_count.get(diff, 0) + 1
        t = it.get("type") or "single"
        type_count[t] = type_count.get(t, 0) + 1
        type_score[t] = round(type_score.get(t, 0) + float(it.get("score") or 0), 2)
        kp = it.get("knowledge_point_name") or "综合"
        kp_count[kp] = kp_count.get(kp, 0) + 1

    total_score = round(sum(float(i.get("score") or 0) for i in items), 2)

    difficulty_report = {
        "distribution": diff_count,
        "ratio": {k: round(v / n * 100, 1) for k, v in diff_count.items()},
        "target_ratio": difficulty_target,
        "actual_vs_target": {
            k: {
                "target": difficulty_target.get(k, 0),
                "actual": round(diff_count.get(k, 0) / n * 100, 1),
            }
            for k in ("easy", "medium", "hard")
        },
        "item_count": len(items),
        "avg_score": round(total_score / n, 2),
    }

    knowledge_report = {
        "points": [{"name": k, "count": v} for k, v in
                   sorted(kp_count.items(), key=lambda kv: -kv[1])],
        "total_points": len(kp_count),
        "covered_questions": sum(v for k, v in kp_count.items() if k != "综合"),
        "uncovered_questions": kp_count.get("综合", 0),
        "coverage_rate": round(
            (sum(v for k, v in kp_count.items() if k != "综合") / n) * 100, 1),
        "balance": _balance_text(kp_count),
    }

    if sections_plan:
        planned = {s["code"]: int(s["count"]) for s in sections_plan}
        planned_score = {s["code"]: round(int(s["count"]) * float(s["score_per"]), 2)
                         for s in sections_plan}
    else:
        planned = {}
        planned_score = {}

    type_report = {
        "distribution": type_count,
        "score_distribution": type_score,
        "planned": planned,
        "planned_score": planned_score,
        "matched": {k: {"planned": planned.get(k), "actual": type_count.get(k, 0)}
                    for k in set(list(planned) + list(type_count))},
        "total_score": total_score,
    }

    return {
        "difficulty_report": difficulty_report,
        "knowledge_report": knowledge_report,
        "type_report": type_report,
    }


def _balance_text(coverage: Dict[str, int]) -> str:
    if not coverage:
        return "暂无知识点覆盖数据"
    vals = list(coverage.values())
    if len(vals) <= 1:
        return "知识点高度集中，建议补充不同知识点的题目"
    spread = max(vals) - min(vals)
    if spread <= 1:
        return "知识点分布均衡"
    if spread <= 2:
        return "知识点分布基本均衡"
    return "知识点分布不均，建议人工调整部分题目"
