"""考试题型结构模板（组卷兜底 / 标准草案 / 历史草案升级共用）。

## 为什么单独抽一个模块

`sections_for()` 同时服务三处：
1. 组卷时的**兜底结构**（该学段学科没配命题标准）；
2. 「一键生成命题标准草案」的**模板**；
3. 升级历史草案时的**目标结构**。

三处必须是同一份结构，否则「兜底出的卷」与「按草案出的卷」题型不一致，
教师会当成 bug。此前的实现只有单选/填空/解答三种题型（10/5/5），
用它生成的整卷缺少多选、判断、材料分析，不符合真实考试结构 —— 用户反馈
的「题型过于单一」正是这条路径。

## 初中结构的权威来源

初中 9 个笔试科目的题型、题量与分值，**逐科对齐**
《初中毕业学业水平考试试卷结构规范（通用参考版）》（整理见
`docs/EXAM_STRUCTURE_SPEC_JUNIOR.md`）。规范来自近年各地中考实卷的通行结构，
是"卷面结构"层面的参考值。

对齐后有几个必须守住的点，改动模板时请勿破坏：

1. **题量与分值必须精确对上规范**。每科模板的 `count` 合计 = 规范题量，
   `section_total()` 合计 = 规范卷面分。改任何一个数都要重算另一个。
2. **阶梯分值用 `score_pattern` 表达**。规范里同一大题内每题分值并不相同：
   - 数学解答题 9 题 = 6/6/6/8/8/8/10/11/12（必须保持梯度，不可均分）
   - 化学选择题 13 题 = 8×1 分 + 5×2 分（前易后难）
   - 语文各板块小题分值 2~8 分不等
   只有单一 `score_per` 会把梯度抹平，卷面失去区分度。
3. **不得引入规范里没有的题型**。初中 9 科均**无判断题**（`judge` 只在小学
   模板保留）；地理、生物**无填空题**；语文**没有 10 道单选题**（那 20 分是
   注音/词语/对联/朗读/默写这类主观题）。早期模板按"题库题型配额"凑结构，
   这四个错得最典型。
4. **英语按笔试 90 分建**。规范卷面 120 = 笔试 90 + 听说 30，但系统只能组
   纸笔卷，听说机考由另一场考试组织。按 120 建会多出 30 分无处落地。

小学模板（`_PRIMARY`）不在本次规范覆盖范围内，保持原样。

## 两份数据的关系

`exam_standard_seed` 是**播种用的示例数据**（含地区名、时长、描述），
本模块是**运行时模板**，两者生命周期不同，刻意不互相 import。
一致性靠模板数值本身对齐，改动时请同步检查。
"""
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

Section = Dict[str, Any]

# 初中卷面元信息：卷面分 / 笔试时长 / 规范题量。
# written_score 是"系统能组出来的笔试卷面分"，total_score 是对外口径的卷面分
# —— 二者只在英语不同（120 = 笔试 90 + 听说 30）。
EXAM_META: Dict[str, Dict[str, Any]] = {
    "语文": {"written_score": 120, "total_score": 120, "duration": 150, "question_count": 25},
    "数学": {"written_score": 120, "total_score": 120, "duration": 120, "question_count": 24},
    "英语": {
        "written_score": 90, "total_score": 120, "duration": 100, "question_count": 51,
        "note": "笔试 90 分；听说 30 分由听说机考另行组织，不计入笔试 51 题题号序列",
    },
    "物理": {"written_score": 70, "total_score": 70, "duration": 70, "question_count": 23,
             "note": "与化学合卷，物理部分在前，同一张试卷连续编号"},
    "化学": {"written_score": 50, "total_score": 50, "duration": 50, "question_count": 20,
             "note": "与物理合卷，化学部分在后"},
    "道德与法治": {"written_score": 60, "total_score": 60, "duration": 60, "question_count": 17,
                   "note": "与历史合卷，道德与法治部分在先"},
    "历史": {"written_score": 60, "total_score": 60, "duration": 60, "question_count": 16,
             "note": "与道德与法治合卷，历史部分在后；末题为观点论述题"},
    "地理": {"written_score": 50, "total_score": 50, "duration": 45, "question_count": 13,
             "note": "与生物合卷，地理部分在后"},
    "生物": {"written_score": 50, "total_score": 50, "duration": 45, "question_count": 14,
             "note": "与地理合卷，生物部分在前"},
}

# 各科难度结构参考区间（规范表 5-3，百分制）。规范注明"为参考区间，不作为刚性指标"。
# 按学科取用，而不是全卷统一按题序切 —— 化学是 70/20/10（中等偏易），
# 数学是 50/30/20（中等偏上），用同一套比例会让抽题难度与卷面定位矛盾。
DIFFICULTY_REFERENCE: Dict[str, Dict[str, int]] = {
    "语文": {"easy": 30, "medium": 50, "hard": 20},
    "数学": {"easy": 50, "medium": 30, "hard": 20},
    "英语": {"easy": 45, "medium": 40, "hard": 15},
    # 规范给的是难题 10%—20%，取 20 才能与 50+30 凑满 100
    "物理": {"easy": 50, "medium": 30, "hard": 20},
    "化学": {"easy": 70, "medium": 20, "hard": 10},
    "道德与法治": {"easy": 55, "medium": 30, "hard": 15},
    "历史": {"easy": 55, "medium": 30, "hard": 15},
    "地理": {"easy": 50, "medium": 35, "hard": 15},
    "生物": {"easy": 55, "medium": 30, "hard": 15},
}

# 学科名归一。平台内建学科用的是「政治」（见 `init_db._SUBJECT_SEED`，7/8/9 年级
# 都只有「政治」，没有「道德与法治」），而规范 / 教材 / 中考口径统一叫
# 「道德与法治」。两侧不归一，`EXAM_META.get("政治")` 就落空 —— 该科退回
# 学段通用六题型模板（100 分 / 36 题 / 含判断题），与规范完全不符。
# 线上确实存在这张标准（一键生成草案按学科名造出来的），所以必须在查表前归一到
# 规范名，而不是去改学科主数据（学科名被知识点、试卷、题库广泛引用，改名波及面大）。
SUBJECT_ALIASES: Dict[str, str] = {
    "政治": "道德与法治",
    "思想品德": "道德与法治",
    "道法": "道德与法治",
    "道德与法制": "道德与法治",  # 常见错字（制/治）
}


def normalize_subject(name: Optional[str]) -> str:
    """把学科名归一到规范口径（见 `SUBJECT_ALIASES`）。

    未命中的学科原样返回 —— 归一只做「同义合并」，不做「未知填充」。
    """
    key = str(name or "").strip()
    return SUBJECT_ALIASES.get(key, key)


# (code, 大题名, 题量, 每题分值或分值序列, 难度)
# 第 4 位传 list 即表示该大题内每题分值不同（阶梯分值），长度必须等于题量。
_PRIMARY: Dict[str, List[tuple]] = {
    # 小学 100 分制（不在初中规范覆盖范围内，保持原结构）
    "语文": [
        ("single", "一、选择题（字音字形/词语运用）", 8, 2, "easy"),
        ("blank", "二、填空题（古诗文积累）", 10, 2, "easy"),
        ("judge", "三、判断题（文学常识与语言规范）", 5, 2, "medium"),
        ("material", "四、阅读理解（课内+课外短文）", 3, 8, "medium"),
        ("composition", "五、习作", 1, 30, "hard"),
    ],
    "数学": [
        ("single", "一、选择题", 10, 2, "easy"),
        ("blank", "二、填空题", 10, 2, "easy"),
        ("judge", "三、判断题", 5, 2, "medium"),
        ("calc", "四、计算题", 4, 6, "medium"),
        ("short", "五、解决问题", 4, 6.5, "hard"),
    ],
    "英语": [
        ("single", "一、选择题（含听力理解）", 15, 2, "easy"),
        ("judge", "二、判断题", 10, 1, "easy"),
        ("blank", "三、词汇与语法填空", 10, 2, "medium"),
        ("material", "四、阅读理解", 2, 10, "medium"),
        ("composition", "五、书面表达", 1, 20, "hard"),
    ],
    "科学": [
        ("single", "一、选择题", 20, 2, "easy"),
        ("judge", "二、判断题", 10, 2, "easy"),
        ("blank", "三、填空题", 10, 2, "medium"),
        ("short", "四、简答题（实验现象与原理）", 2, 10, "hard"),
    ],
    # 学科未单独配置时的六题型模板（100 分）
    "_generic": [
        ("single", "一、单选题", 10, 3, "easy"),
        ("multiple", "二、多选题", 5, 2, "easy"),
        ("judge", "三、判断题", 8, 2, "easy"),
        ("blank", "四、填空题", 8, 2, "medium"),
        ("short", "五、简答题", 4, 5, "medium"),
        ("material", "六、材料分析题", 1, 8, "hard"),
    ],
}

_JUNIOR: Dict[str, List[tuple]] = {
    # ---- 语文 120 分 / 150 分钟 / 25 题 ----------------------------------
    # 板块：积累与运用 20（16.7%）｜阅读与鉴赏 45（37.5%）｜表达与交流 55（45.8%）
    # 注意：规范里语文**没有单选题**，积累与运用是注音/词语/对联/朗读/默写。
    "语文": [
        ("blank", "一、积累与运用", 5, [3, 3, 3, 3, 8], "easy"),
        ("material", "二、阅读与鉴赏（古诗文）", 7, [2, 2, 4, 3, 2, 2, 3], "medium"),
        ("short", "三、阅读与鉴赏（现代文）", 7, [2, 2, 3, 3, 3, 3, 3], "medium"),
        # 整本书阅读是规范明列的**必考板块**（书目以统编教材指定目录为准）
        ("material", "四、整本书阅读", 4, [2, 2, 2, 2], "medium"),
        ("short", "五、表达与交流（专题学习活动发言稿）", 1, 5, "medium"),
        ("composition", "六、写作", 1, 50, "hard"),
    ],
    # ---- 数学 120 分 / 120 分钟 / 24 题（10＋5＋9）------------------------
    # 解答题分值阶梯 6-6-6-8-8-8-10-11-12：必须保留梯度，均分会抹掉区分度。
    "数学": [
        ("single", "一、单项选择题", 10, 3, "easy"),
        ("blank", "二、填空题", 5, 3, "easy"),
        ("calc", "三、解答题", 9, [6, 6, 6, 8, 8, 8, 10, 11, 12], "hard"),
    ],
    # ---- 英语 笔试 90 分 / 100 分钟 / 51 题 -------------------------------
    # 规范卷面 120 = 笔试 90 + 听说 30，听说机考另行组织，故模板只建笔试。
    # 规范明确"不设孤立语法题"，故无单句语法单选题；完形、阅读还原、
    # 选词填空、任务型阅读这四个板块早期模板全缺。
    "英语": [
        ("single", "一、完形填空", 15, 1, "medium"),
        ("material", "二、阅读理解", 15, 2, "medium"),
        ("blank", "三、阅读还原（六选五）", 5, 2, "medium"),
        ("blank", "四、选词填空", 10, 1, "medium"),
        ("short", "五、任务型阅读", 5, 2, "hard"),
        ("composition", "六、书面表达", 1, 15, "hard"),
    ],
    # ---- 物理 70 分 / 70 分钟 / 23 题 ------------------------------------
    "物理": [
        ("single", "一、单项选择题", 12, 2, "easy"),
        # 规范为"4 题 10 空，每空 1 分"：一题多空，系统记 4 道题共 10 分
        ("blank", "二、填空题", 4, [3, 3, 2, 2], "easy"),
        ("material", "三、探究实践题", 5, [4, 4, 4, 4, 5], "medium"),
        ("calc", "四、综合应用题", 2, [7, 8], "hard"),
    ],
    # ---- 化学 50 分 / 50 分钟 / 20 题 ------------------------------------
    # 选择题内部分段计分：1—8 题每题 1 分、9—13 题每题 2 分，形成梯度。
    "化学": [
        ("single", "一、单项选择题", 13, [1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2], "easy"),
        ("material", "二、非选择题", 7, [4, 4, 4, 5, 5, 5, 5], "hard"),
    ],
    # ---- 道德与法治 60 分 / 60 分钟 / 17 题 ------------------------------
    "道德与法治": [
        ("single", "一、单项选择题", 14, 2, "easy"),
        ("material", "二、非选择题", 3, [10, 10, 12], "medium"),
    ],
    # ---- 历史 60 分 / 60 分钟 / 16 题 ------------------------------------
    # 末题是观点论述题（史论结合、不少于 120 字），分值最高，故排在最后且分值最大。
    "历史": [
        ("single", "一、单项选择题", 12, 2, "easy"),
        ("short", "二、非选择题", 4, [8, 9, 8, 11], "medium"),
    ],
    # ---- 地理 50 分 / 45 分钟 / 13 题 ------------------------------------
    "地理": [
        ("single", "一、单项选择题", 10, 2, "easy"),
        ("material", "二、综合题", 3, 10, "hard"),
    ],
    # ---- 生物 50 分 / 45 分钟 / 14 题 ------------------------------------
    "生物": [
        ("single", "一、单项选择题", 10, 2, "easy"),
        ("material", "二、非选择题（实验探究与综合应用）", 4, [7, 8, 7, 8], "medium"),
    ],
    # 学科未单独配置时的六题型模板（120 分）
    "_generic": [
        ("single", "一、单选题", 12, 3, "easy"),
        ("multiple", "二、多选题", 5, 3, "easy"),
        ("judge", "三、判断题", 6, 2, "easy"),
        ("blank", "四、填空题", 8, 3, "medium"),
        ("short", "五、简答题", 4, 6, "medium"),
        ("material", "六、材料分析题", 1, 9, "hard"),
    ],
}

VALID_CODES = {
    "single", "multiple", "judge", "blank", "short", "calc", "material", "composition",
}


def section_total(sec: Section) -> float:
    """一个大题的分值小计。

    有 `score_pattern` 时以序列之和为准，否则用 `count * score_per`。
    **所有合计都必须走这里**：阶梯分值下 `score_per` 只是平均值（可能是
    1.3846 这样的无限小数），用 `count * score_per` 会算出 17.94 而不是 18，
    整卷总分校验随之误报。
    """
    pattern = sec.get("score_pattern")
    if pattern:
        return round(sum(float(x) for x in pattern), 2)
    return round(int(sec.get("count") or 0) * float(sec.get("score_per") or 0), 2)


def _to_sections(raw: List[tuple]) -> List[Section]:
    out: List[Section] = []
    for idx, (code, name, count, score, difficulty) in enumerate(raw, start=1):
        count = int(count)
        pattern: Optional[List[float]] = None
        if isinstance(score, (list, tuple)):
            pattern = [round(float(x), 2) for x in score]
            if len(pattern) != count:
                # 模板写错（题量与分值序列长度不符）时退化成均分：
                # 抛异常会让整条组卷链路 500，而"分值略平"只是结构偏差。
                logger.error(
                    "模板 %r 的 score_pattern 长度 %s 与题量 %s 不符，已退化为均分",
                    name, len(pattern), count)
                pattern = None
        if pattern:
            sec_total = round(sum(pattern), 2)
            score_per = round(sec_total / count, 2) if count else 0.0
        else:
            score_per = round(float(score), 2)
        out.append({
            "code": code, "name": name, "count": count,
            "score_per": score_per,
            **({"score_pattern": pattern} if pattern else {}),
            "difficulty": difficulty, "sort": idx,
        })
    return out


def _scale(sections: List[Section], target_total: float) -> List[Section]:
    """把模板等比缩放到目标总分，**保证分项合计精确等于总分**。

    最后一档用「总分 - 前面各档之和」吸收取整误差：早期实现每档独立四舍五入，
    100 分卷实测合计 99.98，教师一眼就会质疑。缩放过后的每档小计再摊回
    单题分值，因此可能出 2.67 分/题这类小数 —— 英语 1.5 分/题本来也是常态，
    比"总分差两分钱"更可接受。

    阶梯分值（`score_pattern`）按**同一个比例**缩放，相对梯度不变，
    末题吸收舍入误差。
    """
    base_total = sum(section_total(s) for s in sections)
    if base_total <= 0:
        return sections
    if abs(base_total - target_total) < 0.01:
        return sections

    factor = target_total / base_total
    out: List[Section] = []
    acc = 0.0
    for i, s in enumerate(sections):
        count = int(s["count"])
        if i == len(sections) - 1:
            sec_total = round(target_total - acc, 2)
        else:
            sec_total = round(section_total(s) * factor, 2)

        pattern = s.get("score_pattern")
        if pattern:
            old_sum = sum(float(x) for x in pattern)
            ratio = sec_total / old_sum if old_sum else 1.0
            new_pattern = [round(float(x) * ratio, 2) for x in pattern]
            drift = round(sec_total - sum(new_pattern), 2)
            if drift:
                new_pattern[-1] = round(new_pattern[-1] + drift, 2)
            out.append({
                **s, "score_pattern": new_pattern,
                "score_per": round(sec_total / count, 2) if count else 0.0,
            })
        else:
            score_per = round(sec_total / count, 2) if count else 0.0
            out.append({**s, "score_per": score_per})
        acc = round(acc + section_total(out[-1]), 2)
    return out


def exam_meta(stage: Optional[str], subject_name: Optional[str]) -> Optional[Dict[str, Any]]:
    """该学段学科的卷面元信息（卷面分/时长/题量）。

    小学暂无规范来源，返回 None，由调用方沿用"100 分 / 90 分钟"的旧口径。
    """
    if str(stage or "").lower() == "primary":
        return None
    return EXAM_META.get(normalize_subject(subject_name))


def sections_for(
    stage: Optional[str] = None,
    subject_name: Optional[str] = None,
    total_score: Optional[float] = None,
) -> List[Section]:
    """按学段 + 学科返回标准题型结构；学科未覆盖时退到学段通用六题型模板。

    `stage` 取 primary/junior（与 Grade.stage 一致），缺省按初中处理
    —— 初中题型更全，误判成初中比误判成小学更接近"标准考试"。

    `total_score` 不传时按该科**笔试卷面分**自动取（英语 90，其余见 EXAM_META）：
    早期所有科目默认 100 分，物理 70 分卷会被放大成 100 分卷，题量没变但每题
    分值虚高，与规范不符。
    """
    stage_key = "primary" if str(stage or "").lower() == "primary" else "junior"
    table = _PRIMARY if stage_key == "primary" else _JUNIOR
    # 归一后再查表：「政治」→「道德与法治」，否则该科落到 _generic
    # （100 分 / 36 题 / 含判断题），与规范的 60 分 / 17 题相差极大。
    subject = normalize_subject(subject_name)
    raw = table.get(subject) or table["_generic"]

    target = total_score
    if target in (None, 0):
        meta = exam_meta(stage_key, subject)
        target = float(meta["written_score"]) if meta else float(
            sum(section_total(s) for s in _to_sections(raw)) or 100)
    return _scale(_to_sections(raw), float(target))


def difficulty_gradient(
    sections: List[Section], subject_name: Optional[str] = None,
) -> Dict[str, int]:
    """返回难度分布（百分制整数，合计恒为 100），供组卷对齐。

    优先取规范的**分科难度区间**（`DIFFICULTY_REFERENCE`，规范表 5-3）：
    化学 70/20/10（中等偏易）、数学 50/30/20（中等偏上），若全卷统一按题序
    切分，抽题结果的难度重心会与该科的实际定位矛盾。

    学科不在表内时才退回**按题序位置**推算（前 35% easy / 35%~70% medium /
    后 30% hard）—— 这既是真实考试的难度梯度（送分题在前、压轴在后），
    也与 `split_by_difficulty` 按题数分配的语义一致。

    为什么不用"按大题中位归类"：初中数学「解答题」一个大题就占 60% 分值，
    整块会被归成同一档，实测算出 hard=0%，与卷面完全不符。
    """
    ref = DIFFICULTY_REFERENCE.get(normalize_subject(subject_name))
    if ref:
        pct = {k: int(ref.get(k, 0)) for k in ("easy", "medium", "hard")}
        drift = 100 - sum(pct.values())
        if drift:
            pct[max(pct, key=lambda k: pct[k])] += drift
        return pct

    total_count = sum(int(s["count"]) for s in sections)
    if total_count <= 0:
        return {"easy": 40, "medium": 40, "hard": 20}

    counts: Dict[str, int] = {"easy": 0, "medium": 0, "hard": 0}
    idx = 0
    for s in sections:
        for _ in range(int(s["count"])):
            pos = (idx + 0.5) / total_count
            if pos <= 0.35:
                counts["easy"] += 1
            elif pos <= 0.70:
                counts["medium"] += 1
            else:
                counts["hard"] += 1
            idx += 1

    pct = {k: int(round(v * 100 / total_count)) for k, v in counts.items()}
    drift = 100 - sum(pct.values())
    if drift:
        biggest = max(pct, key=lambda k: pct[k])
        pct[biggest] += drift
    return pct


def legacy_draft_codes() -> List[str]:
    """旧版 generic_sections 的题型序列（单选/填空/解答）。

    用于识别「由旧模板批量生成的命题标准草案」——迁移时只替换精确匹配这个
    序列的记录，管理员手工配过的结构一律不动。
    """
    return ["single", "blank", "short"]
