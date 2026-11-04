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
# 大题小计一律走 section_total：阶梯分值下 `count * score_per` 会算错
from app.services.exam_structures import section_total

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


def parse_score_pattern(raw: Any, count: int) -> Optional[List[float]]:
    """解析「同一大题内每题分值不同」的分值序列（阶梯分值）。

    真实卷面大量存在这种结构：数学解答题 6/6/6/8/8/8/10/11/12、
    化学选择题 8 题×1 分 + 5 题×2 分、语文各板块小题 2~8 分不等。
    早期只有单一 `score_per`，这些梯度会被抹平成均分，卷面失去区分度。

    校验不通过一律返回 None（退化为均分），**不抛异常** —— 结构里一个字段
    写错不该让整条组卷链路 500，退化成"分值略平"是可接受的降级。
    """
    if not isinstance(raw, (list, tuple)) or not count:
        return None
    try:
        vals = [round(float(x), 2) for x in raw]
    except (TypeError, ValueError):
        return None
    if len(vals) != count or any(v <= 0 for v in vals):
        return None
    return vals


def _section_scores(sec: Dict[str, Any], count: int) -> List[float]:
    """把一个大题展开成「每道题各自的分值」列表，长度恒为 count。

    有 `score_pattern` 且长度匹配时直接用，否则用 `score_per` 均分补齐。
    调用方按位置取分即可，不需要再判断有没有阶梯。
    """
    pattern = sec.get("score_pattern")
    if isinstance(pattern, (list, tuple)) and len(pattern) == count:
        return [round(float(x), 2) for x in pattern]
    return [round(float(sec.get("score_per") or 0), 2)] * max(0, count)


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
        pattern = parse_score_pattern(raw.get("score_pattern"), count)
        # 只给了分值序列、没给 score_per 时按平均值补上：下游多处只读
        # score_per（报告展示、补题默认分值），缺了会变成 0 分。
        if pattern and score_per <= 0:
            score_per = round(sum(pattern) / count, 2)
        if count <= 0 or score_per <= 0:
            continue
        result.append({
            "code": code,
            "name": str(raw.get("name") or TYPE_LABEL[code])[:64],
            "count": count,
            "score_per": score_per,
            **({"score_pattern": pattern} if pattern else {}),
            "difficulty": str(raw.get("difficulty") or "medium"),
            "sort": int(raw.get("sort") or idx),
        })
    result.sort(key=lambda s: s["sort"])
    return result


# 标准试卷的题型顺序。真实卷面的先后由**题型本身**决定，而不是「谁先传进来」：
#   - AI 解析出的 type_ratio 是 dict，顺序取决于模型输出的键序；
#   - 用户自定义 sections 时也可能把作文放前面；
#   - `_parse_sections_input` 按入参顺序赋 sort（1..n）。
# 三种来源都可能让作文不落在末位（用户实测：语文卷作文夹在中间）。
# 因此 sections 一经确定就必须按这张表重排，这是「试卷规范」的一部分。
SECTION_TYPE_ORDER: List[str] = [
    "single", "multiple", "judge", "blank",
    "short", "calc", "material", "composition",
]


def type_rank(code: Any) -> int:
    """题型的规范位次（未知题型排最后，不会插到作文后面）。"""
    try:
        return SECTION_TYPE_ORDER.index(str(code or "").strip().lower())
    except ValueError:
        return len(SECTION_TYPE_ORDER)


def normalize_section_order(sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """按卷面规范重排大题并重赋 sort（1..n）。

    **只钉一条硬规则：作文/写作必须是最后一题。** 其余大题保持原有相对顺序，
    因为真实卷面的板块顺序由学科决定，不是由题型码决定 —— 语文卷是
    「积累与运用(填空) → 阅读与鉴赏(材料/简答) → 整本书阅读(材料) → 写作」，
    若按题型码排序，`material` 会被整体挪到 `short` 后面，古诗文阅读就跑到
    现代文阅读之后了，与卷面板块完全错乱。

    早期实现按 `type_rank` 全量排序，目的是修「AI 解析出的作文夹在中间」
    （AI 输出是 dict，键序不定）。只钉作文即可达到同样效果，且不破坏板块。

    **稳定排序**：同一题型保持原有相对顺序。英语卷有两个 `blank` 大题
    （阅读还原、选词填空）、语文卷有两个 `material` 大题（古诗文阅读、
    整本书阅读），它们的先后是教师刻意安排的，不能被互换。
    """
    if not sections:
        return sections
    indexed = list(enumerate(sections))
    indexed.sort(key=lambda p: (
        1 if str(p[1].get("code") or "").strip().lower() == "composition" else 0,
        p[0],
    ))
    return [
        {**sec, "sort": new_sort}
        for new_sort, (_, sec) in enumerate(indexed, start=1)
    ]


def default_sections(total_score: float = 100, count: int = 20) -> List[Dict[str, Any]]:
    """无标准可用时的兜底结构：单选题为主，分值均摊后补齐总分。"""
    count = max(1, count)
    score_per = round(total_score / count, 2)
    return [{
        "code": "single", "name": "一、单选题",
        "count": count, "score_per": score_per,
        "difficulty": "medium", "sort": 1,
    }]


def generic_sections(
    total_score: float = 100, stage: Optional[str] = None,
    subject_name: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """通用题型结构（无命题标准可用，或生成标准草案时使用）。

    结构来自 `exam_structures`，按「学段 + 学科」取真实考试模板：
    小学/初中各学科是 4~5 个大题（单选/多选/判断/填空/简答/材料/写作），
    学科未覆盖时退到学段通用的六题型模板。

    **这里曾是"AI 一键组卷题型单一"的根因**：旧实现固定单选 10 / 填空 5 /
    解答 5，只有三种题型；而生产环境的命题标准又是用这个函数批量生成的草案
    （SEED_BASE_DATA=false 时规范种子标准不会播种），于是整卷只有三种题型，
    缺少多选、判断、材料分析，与真实考试结构不符。

    统一到 `exam_structures` 后，兜底卷 / 草案 / 历史草案升级三处结构一致。
    """
    from app.services.exam_structures import sections_for

    return sections_for(stage=stage, subject_name=subject_name, total_score=total_score)


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


def _bank_visibility_clause(viewer_id: Optional[int], allow_all_banks: bool):
    """题库可见范围：公共库 + 本人私有（管理员不限）。

    旧实现的抽题 SQL **完全不看题库归属**，只要 `status=published` 就抽——私有
    题库的"已发布"题（教师自编/校内卷）会被抽进**别的教师**的组卷预览，
    题干、答案、解析全部随预览返回（越权泄露）；而保存时 `_normalize_items`
    又会以"无权使用题目"拒绝，于是出现"预览明明有 12 题、保存报错"的断裂。
    这里把归属条件下沉到 `_base_stmt`，抽题/预览/保存三处口径一致。
    """
    if allow_all_banks:
        return None
    from sqlalchemy import or_ as _or
    if viewer_id:
        return _or(
            Question.bank_type == "public",
            Question.owner_id == viewer_id,
        )
    # 无观看者上下文时只取公共题：宁可少抽，也不越权
    return Question.bank_type == "public"


def _base_stmt(*, grade_id: int, subject_id: int, qtype: str,
               kp_ids: Sequence[int], difficulty: Optional[str],
               exclude_ids: set,
               viewer_id: Optional[int] = None,
               allow_all_banks: bool = False):
    """统一的基础查询。

    **所有**抽题分支（含放宽条件的那一支）都必须走这里，
    否则知识范围会在"放宽"时被悄悄丢掉——这是旧实现的 P1 缺陷。
    题库归属（公共 + 本人私有）同样只在这里过滤一次，避免某条兜底分支绕过。
    """
    stmt = select(Question).where(
        Question.grade_id == grade_id,
        Question.subject_id == subject_id,
        Question.type == qtype,
        Question.status == QuestionStatus.PUBLISHED.value,
    )
    bank_clause = _bank_visibility_clause(viewer_id, allow_all_banks)
    if bank_clause is not None:
        stmt = stmt.where(bank_clause)
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
    viewer_id: Optional[int] = None,
    allow_all_banks: bool = False,
) -> ComposePlan:
    """按标准结构从题库抽题，返回预览计划（不写库）。

    source_strategy:
    - bank_only：只用题库。抽不满就留缺口，不补。
    - ai_only：完全不用题库（返回空计划 + 全部缺口，由上层调 AI 生成）。
    - bank_first：题库优先，缺口标记出来供上层补题。

    viewer_id / allow_all_banks：题库可见范围（公共库 + 本人私有；管理员放开）。
    不传 viewer_id 时只抽公共题——**调用方必须传**，否则教师试卷会悄悄变短。
    """
    if source_strategy not in VALID_SOURCES:
        raise ComposeError(f"出题来源不合法：{source_strategy}")

    plan = ComposePlan()
    kp_ids = [int(k) for k in (kp_ids or []) if k]
    ratio = normalize_difficulty(difficulty_ratio)
    # 结构确定后立刻按题型规范重排：作文必须落在末位，这是卷面规范。
    # 三条来源（用户手填 / 命题标准 / 学段兜底）都过这里，避免某个入口漏掉。
    sections = normalize_section_order(
        sections or parse_sections(standard) or default_sections()
    )

    if source_strategy == SOURCE_AI_ONLY:
        # 全 AI：不需要抽题，只把结构换算成缺口清单
        for sec in sections:
            want = int(sec["count"])
            sec_scores = _section_scores(sec, want)
            plan.gaps.append({
                "code": sec["code"], "name": sec["name"],
                "need": want, "got": 0,
                "score_per": sec["score_per"],
                # 缺口必须带上完整分值序列：补题是按位置逐题给分的，
                # 只留平均值会让数学解答题 6/6/6/8… 的梯度在补题后消失。
                "score_pattern": sec_scores,
                "difficulty": sec.get("difficulty", "medium"),
                # sort 必须带上：上层调 AI 补题后要按它定大题顺序，
                # 缺了会全部落到默认 0，`_renumber` 只能改按题号排，
                # 于是「二、填空题」的题可能因为 id 更小而变成「一、填空题」。
                "sort": sec.get("sort", 0),
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
        # 逐题分值：有阶梯分值序列就按位置取，否则整段均分
        sec_scores = _section_scores(sec, want)
        sec_difficulty = sec.get("difficulty") or "medium"

        picked = _pick_for_section(
            db, grade_id=grade_id, subject_id=subject_id, qtype=code,
            want=want, kp_ids=kp_ids, difficulty_ratio=ratio,
            prefer_difficulty=sec_difficulty, exclude=exclude,
            kp_used=kp_used, kp_cap=kp_cap,
            viewer_id=viewer_id, allow_all_banks=allow_all_banks,
            # 跨大题共享已用题目：两个同题型大题（如语文「古诗文阅读」与
            # 「整本书阅读」都是材料题）各自去重会抽到同一道题，整卷出现重复题。
            # 用 plan 级的集合做全局互斥。
            global_used=plan.used_question_ids,
        )
        # 「忽略近 N 次去重」的兜底在 `_pick_for_section` 第三级内完成；
        # 这里只统计「本应被去重排除、但为了不出白卷而复用」的题量，
        # 由上层如实告知教师（复用老题必须是可见的，不能悄悄发生）。
        if exclude:
            plan.relaxed_count += sum(1 for q in picked if q.id in exclude)

        for pos, q in enumerate(picked):
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
                # 按题序取分：抽题是按题库顺序 append 的，pos 即该题在本大题内
                # 的第几题，与规范「第 22 题 10 分、第 24 题 12 分」一一对应
                "score": round(sec_scores[pos], 2),
                # 卷面槽位：`_renumber` 必须按它排，不能按 question_id 排 ——
                # 分值是按槽位给的，题号重排后分值就与题目错位了
                # （实测 6/8/10/6/8/11/6/8/12 这种乱序）
                "section_pos": pos,
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
                "score_per": sec["score_per"],
                "score_pattern": sec_scores,
                "difficulty": sec_difficulty,
                # 同上：缺口要记住自己属于第几大题，补题时才能排回原位
                "sort": sec.get("sort", 0),
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
    viewer_id: Optional[int] = None, allow_all_banks: bool = False,
    global_used: Optional[set] = None,
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
            # 全局互斥：同一道题不能在两个大题里各出现一次。
            # 第三级兜底（ignore_exclude）也不能突破这一条——重复题比缺题更糟，
            # 卷面上会出现一模一样的题目，打印出来就是事故。
            if global_used is not None and q.id in global_used:
                continue
            # 知识点限流
            kp_id = q.knowledge_point_id
            if kp_id and kp_used.get(kp_id, 0) >= kp_cap:
                continue
            picked.append(q)
            picked_ids.add(q.id)
            if global_used is not None:
                global_used.add(q.id)
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
                       kp_ids=kp_ids, difficulty=diff, exclude_ids=exclude,
                       viewer_id=viewer_id, allow_all_banks=allow_all_banks)
            .limit(need * 4)
        ).all()
        _take(list(rows), need)

    # 2) 放宽难度（知识点范围保持不变）
    if len(picked) < want:
        rows = db.scalars(
            _base_stmt(grade_id=grade_id, subject_id=subject_id, qtype=qtype,
                       kp_ids=kp_ids, difficulty=None, exclude_ids=exclude,
                       viewer_id=viewer_id, allow_all_banks=allow_all_banks)
            .limit((want - len(picked)) * 5)
        ).all()
        _take(list(rows), want - len(picked))

    # 3) 最后兜底：忽略"近 N 次重复"限制（题库实在不足时宁可重复，也不能交白卷）
    if len(picked) < want and exclude:
        rows = db.scalars(
            _base_stmt(grade_id=grade_id, subject_id=subject_id, qtype=qtype,
                       kp_ids=kp_ids, difficulty=None, exclude_ids=set(),
                       viewer_id=viewer_id, allow_all_banks=allow_all_banks)
            .limit((want - len(picked)) * 5)
        ).all()
        _take(list(rows), want - len(picked), ignore_exclude=True)

    return picked


def _on_grid(value: float, unit: float) -> bool:
    """value 是否是 unit 的整数倍（浮点容差内）。"""
    return abs(value / unit - round(value / unit)) < 1e-9


def _distribute_on_grid(items: List[Dict[str, Any]], target: float, unit: float) -> None:
    """最大余数法：把 target 按原分值比例分成 unit 的整数倍，合计**精确**等于 target。

    先按比例取整（floor），再把差额按小数部分从大到小每个补一个 unit。
    余数相同按原顺序，保证同参数重复调用结果一致。
    """
    current = sum(float(i["score"]) for i in items)
    factor = target / current
    exact = [float(i["score"]) * factor / unit for i in items]
    floors = [int(math.floor(x + 1e-9)) for x in exact]
    order = sorted(range(len(items)), key=lambda idx: (-(exact[idx] - floors[idx]), idx))
    diff = int(round(target / unit)) - sum(floors)
    if diff > 0:
        for idx in order[:diff]:
            floors[idx] += 1
    elif diff < 0:
        # 浮点误差可能让 floor 之和超出 1 个单位，从余数最小的往回退
        for idx in reversed(order[: -diff]):
            if floors[idx] > 0:
                floors[idx] -= 1
    for idx, value in enumerate(floors):
        items[idx]["score"] = round(max(0.0, value * unit), 2)


def _rescale_scores(items: List[Dict[str, Any]], target_total: float) -> None:
    """把卷面总分调整到 target_total，按原分值比例缩放。

    只改 score 不动题目：教师改"试卷总分"时不应清空已选题目。

    **按"分值网格"分配，不产生无意义的尾数**：直接比例缩放会把 3 道 5 分题
    摊成 6.67/6.67/6.66，卷面上出现"值 6.67 分"的题既不常见也无法心算核对。
    这里按网格取整后补齐差额：

    - 原分值全为整数、目标也是整数 → 以 **1 分**为网格；
    - 否则若都能落在 **0.5 分**上 → 以 0.5 分为网格（0.5 分小题是常见卷面口径）；
    - 更细（0.25 等）或题量多于总分（网格分配必然出现 0 分题）→ 退回比例法。

    合计始终**精确**等于目标总分，不靠"把误差丢给最后一题"。
    """
    current = sum(float(i["score"]) for i in items)
    if current <= 0 or abs(current - target_total) < 0.01:
        return
    target = float(target_total)
    originals = [float(i["score"]) for i in items]

    for unit in (1.0, 0.5):
        if not _on_grid(target, unit):
            continue
        if any(not _on_grid(s, unit) for s in originals):
            continue
        # 网格分配要求每题至少 1 个 unit，否则必然有题被压成 0 分
        if int(round(target / unit)) < len(items):
            continue
        _distribute_on_grid(items, target, unit)
        return

    factor = target / current
    for it in items:
        it["score"] = round(float(it["score"]) * factor, 2)
    drift = round(target - sum(float(i["score"]) for i in items), 2)
    if drift and items:
        items[-1]["score"] = round(float(items[-1]["score"]) + drift, 2)


def _renumber(items: List[Dict[str, Any]]) -> None:
    """按大题顺序 + 组内顺序重排 sort_order，并生成正确的中文大题号。

    旧实现把 section_name 硬编码成「一、」是显式 bug；这里按 section_sort
    取中文序号，同时把大题名里可能已带的「一、」前缀剥掉再拼，
    避免出现「一、一、单选题」。
    """
    # 排序键：先大题序，再**大题内槽位**，最后题型位次与题号。
    #
    # `section_pos` 是组卷时记下的卷面位置（第几题），必须优先于 question_id：
    # 分值是按槽位分配的（数学解答题第 9 题 12 分、第 1 题 6 分），一旦按
    # question_id 重排，题目与分值就错位了 —— 实测算出 6/8/10/6/8/11/6/8/12
    # 这种乱序，压轴题的 12 分挂在了中间的题上。
    #
    # 缺 `section_pos` 时（前端保存的老数据、手改卷）退到题号排，保持旧行为。
    # 那时第三键从 `question_id` 换到 `type_rank` 是为了兜住「前端保存题项列表
    # 时不传 section_sort（全为 0）」——旧实现会「按 question_id 排」，
    # 作文题按题型自增 id 散落到卷子中间。
    has_section_sort = any(int(i.get("section_sort") or 0) > 0 for i in items)
    has_pos = bool(items) and all(i.get("section_pos") is not None for i in items)
    if has_section_sort:
        if has_pos:
            items.sort(key=lambda i: (
                int(i.get("section_sort") or 0),
                int(i.get("section_pos") or 0),
            ))
        else:
            items.sort(key=lambda i: (
                int(i.get("section_sort") or 0),
                type_rank(i.get("section_code") or i.get("type")),
                int(i.get("question_id") or 0),
            ))
    else:
        items.sort(key=lambda i: (
            type_rank(i.get("section_code") or i.get("type")),
            int(i.get("question_id") or 0),
        ))
    # 分组键：优先用大题序号，其次才退到题型码。
    #
    # **不能只用题型码分组**：真实卷面同一题型会被拆成多个板块 ——
    # 语文「阅读与鉴赏（古诗文）」与「整本书阅读」都是材料题，英语「阅读还原」
    # 与「选词填空」都是填空题。只按 code 分组会把两个板块合并成同一个大题号，
    # 卷面出现「三、阅读与鉴赏（古诗文）」下面跟着整本书阅读的题。
    section_index: Dict[Any, int] = {}
    for it in items:
        code = it.get("section_code") or it.get("type")
        key: Any = code
        if has_section_sort:
            sort_val = int(it.get("section_sort") or 0)
            if sort_val > 0:
                key = ("s", sort_val)
        if key not in section_index:
            section_index[key] = len(section_index) + 1
        idx = section_index[key]
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
        planned_score = {s["code"]: section_total(s) for s in sections_plan}
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


# ---------------------------------------------------------------- 卷面体检
def audit_paper(
    items: List[Dict[str, Any]],
    *,
    total_score: Optional[float] = None,
    has_gaps: bool = False,
) -> List[Dict[str, str]]:
    """检查卷面是否符合「可直接打印」的规范，返回问题列表（空 = 通过）。

    **只报告、不阻断**。组卷过程里已经有硬校验（跨大题去重、题型与大题
    一致），这一层是兜底复核，作用有三：
      1. 防以后新增的组卷入口绕过那些校验（新增路径最容易漏）；
      2. 暴露历史数据问题（早期生成的卷子可能已有重复题）；
      3. 让教师在打印前看到卷面缺陷，而不是发给学生后才发现。

    level 语义：
      error —— 打印出来会出错（重复题、总分对不上、作文不在末位）
      warn  —— 不影响正确性但不合常规（大题顺序、题号跳号、大题混排题型）
    """
    issues: List[Dict[str, str]] = []
    if not items:
        return [{"level": "warn", "code": "empty", "message": "试卷还没有题目"}]

    def _code(it: Dict[str, Any]) -> str:
        return str(it.get("section_code") or it.get("type") or "").strip().lower()

    codes = [_code(it) for it in items]

    # 1) 重复题：一卷之内同一 question_id 只能出现一次
    seen: set = set()
    dups: List[Any] = []
    for it in items:
        qid = it.get("question_id")
        if qid in seen:
            dups.append(qid)
        else:
            seen.add(qid)
    if dups:
        sample = "、".join(str(d) for d in dups[:5])
        more = f" 等 {len(dups)} 道" if len(dups) > 5 else ""
        issues.append({
            "level": "error", "code": "duplicate",
            "message": f"有题目被重复收录（question_id={sample}{more}），打印后会出现两张相同的题目",
        })

    # 2) 作文必须是最后一题（语文/英语卷的硬性卷面规范）
    comp_idx = [i for i, c in enumerate(codes) if c == "composition"]
    if comp_idx and max(comp_idx) != len(codes) - 1:
        issues.append({
            "level": "error", "code": "composition_not_last",
            "message": "作文题不是最后一题，不符合卷面规范",
        })

    # 3) 卷首应为客观题（选择/判断/填空）。
    #
    # 早期这里检查「全卷题型位次必须单调递增」，在板块化卷面上是错的：
    # 语文卷是 积累与运用(填空) → 古诗文阅读(材料) → 现代文阅读(简答) →
    # 整本书阅读(材料) → 写作，材料题必然出现在简答题之后，单调性不成立。
    # 真正有卷面意义的是「开卷不能是作文或材料分析题」。
    if codes and type_rank(codes[0]) > SECTION_TYPE_ORDER.index("blank"):
        issues.append({
            "level": "warn", "code": "section_order",
            "message": f"试卷第一大题是「{TYPE_LABEL.get(codes[0], codes[0])}」，"
                       "常规试卷应以选择/判断/填空题开卷",
        })

    # 4) 题号连续（打印后跳号会被当成漏题）
    sorts = [it.get("sort_order") for it in items]
    if all(isinstance(s, int) for s in sorts) and sorts != list(range(1, len(sorts) + 1)):
        issues.append({
            "level": "warn", "code": "numbering",
            "message": "题号不连续，打印后会出现跳号",
        })

    # 5) 分项合计与试卷总分一致。
    # **有缺口时不检查**：题库不足导致的「计划 25 题只抽到 18 题」本来就会让
    # 合计小于总分，那是缺口问题，已经由 gaps 单独上报；这里再报一次
    # 「总分不一致」只会让教师以为是数据错误。
    if total_score is not None and not has_gaps:
        try:
            subtotal = round(sum(float(it.get("score") or 0) for it in items), 2)
            if abs(subtotal - float(total_score)) > 0.01:
                issues.append({
                    "level": "error", "code": "score_mismatch",
                    "message": f"题目分值合计 {subtotal:g} 分，与试卷总分 {float(total_score):g} 分不一致",
                })
        except (TypeError, ValueError):
            pass

    # 6) 同一大题内不应混排多种题型
    by_section: Dict[str, set] = {}
    for it in items:
        sec = str(it.get("section_name") or it.get("section_code") or "")
        by_section.setdefault(sec, set()).add(_code(it))
    mixed = [sec for sec, types in by_section.items() if len(types) > 1]
    if mixed:
        issues.append({
            "level": "warn", "code": "section_mixed_types",
            "message": f"以下大题混排了多种题型：{'、'.join(mixed[:3])}",
        })

    return issues
