"""考试题型结构模板（组卷兜底 / 标准草案 / 历史草案升级共用）。

## 为什么单独抽一个模块

`generic_sections()` 同时服务三处：
1. 组卷时的**兜底结构**（该学段学科没配命题标准）；
2. 「一键生成命题标准草案」的**模板**；
3. 升级历史草案时的**目标结构**。

三处必须是同一份结构，否则「兜底出的卷」与「按草案出的卷」题型不一致，
教师会当成 bug。此前的实现只有单选/填空/解答三种题型（10/5/5），
用它生成的整卷缺少多选、判断、材料分析，不符合真实考试结构 —— 用户反馈
的「题型过于单一」正是这条路径。

## 结构来源

小学/初中各学科的结构参考 `exam_standard_seed`（湖北地区标准），
学科未覆盖时退到学段通用的六题型模板（单选/多选/判断/填空/简答/材料）。

两份数据刻意保持独立而不互相 import：`exam_standard_seed` 是**播种用的示例
数据**（含地区名、时长、描述），本模块是**运行时模板**，两者生命周期不同。
一致性靠模板数值本身对齐，改动时请同步检查。
"""
from typing import Any, Dict, List, Optional

Section = Dict[str, Any]

# (code, 大题名, 题量, 每题分值, 难度) —— 分值按该学科常见卷面总分设计，
# 调用方若传了别的总分，由 _scale() 等比缩放。
_PRIMARY: Dict[str, List[tuple]] = {
    # 小学 100 分制
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
    # 初中：语数英 120、物理 70、化学 50、道法 60
    "语文": [
        ("single", "一、积累与运用（选择题）", 10, 2, "easy"),
        ("blank", "二、古诗文默写", 6, 2, "easy"),
        ("material", "三、古诗文阅读", 3, 8, "medium"),
        ("short", "四、现代文阅读", 3, 8, "medium"),
        ("composition", "五、写作", 1, 40, "hard"),
    ],
    "数学": [
        ("single", "一、选择题", 10, 3, "easy"),
        ("blank", "二、填空题", 6, 3, "medium"),
        ("calc", "三、解答题", 9, 8, "hard"),
    ],
    "英语": [
        ("single", "一、听力理解与单项选择", 20, 1.5, "easy"),
        ("blank", "二、词汇与语法填空", 10, 1.5, "medium"),
        ("judge", "三、正误判断", 10, 1, "easy"),
        ("material", "四、阅读理解", 5, 7, "medium"),
        ("composition", "五、书面表达", 1, 30, "hard"),
    ],
    "物理": [
        ("single", "一、选择题", 8, 3, "easy"),
        ("blank", "二、填空题", 5, 2, "medium"),
        ("short", "三、实验探究题", 2, 10, "medium"),
        ("calc", "四、计算题", 2, 8, "hard"),
    ],
    "化学": [
        ("single", "一、选择题", 8, 3, "easy"),
        ("blank", "二、填空题", 4, 2, "medium"),
        ("material", "三、实验与探究题", 2, 6, "medium"),
        ("calc", "四、计算题", 1, 6, "hard"),
    ],
    "道德与法治": [
        ("single", "一、选择题", 12, 2, "easy"),
        ("material", "二、材料分析题", 3, 8, "medium"),
        ("short", "三、实践探究题", 2, 6, "hard"),
    ],
    "历史": [
        ("single", "一、选择题", 12, 2, "easy"),
        ("material", "二、材料解析题", 2, 10, "medium"),
        ("short", "三、综合探究题", 1, 16, "hard"),
    ],
    "地理": [
        ("single", "一、选择题", 12, 2, "easy"),
        ("blank", "二、填空题", 5, 2, "medium"),
        ("short", "三、综合题", 2, 8, "hard"),
    ],
    "生物": [
        ("single", "一、选择题", 12, 2, "easy"),
        ("judge", "二、判断题", 5, 2, "easy"),
        ("short", "三、简答题", 2, 5, "medium"),
        ("material", "四、实验探究题", 1, 6, "hard"),
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


def _to_sections(raw: List[tuple]) -> List[Section]:
    out: List[Section] = []
    for idx, (code, name, count, score_per, difficulty) in enumerate(raw, start=1):
        out.append({
            "code": code, "name": name, "count": int(count),
            "score_per": float(score_per),
            "difficulty": difficulty, "sort": idx,
        })
    return out


def _scale(sections: List[Section], target_total: float) -> List[Section]:
    """把模板等比缩放到目标总分，**保证分项合计精确等于总分**。

    最后一档用「总分 - 前面各档之和」吸收取整误差：早期实现每档独立四舍五入，
    100 分卷实测合计 99.98，教师一眼就会质疑。缩放过后的每档小计再摊回
    单题分值，因此可能出 2.67 分/题这类小数 —— 英语 1.5 分/题本来也是常态，
    比"总分差两分钱"更可接受。
    """
    base_total = sum(s["count"] * s["score_per"] for s in sections)
    if base_total <= 0:
        return sections
    if abs(base_total - target_total) < 0.01:
        return sections

    factor = target_total / base_total
    out: List[Section] = []
    acc = 0.0
    for i, s in enumerate(sections):
        if i == len(sections) - 1:
            sec_total = round(target_total - acc, 2)
        else:
            sec_total = round(s["count"] * s["score_per"] * factor, 2)
        score_per = round(sec_total / s["count"], 2) if s["count"] else 0.0
        acc = round(acc + s["count"] * score_per, 2)
        out.append({**s, "score_per": score_per})
    return out


def sections_for(
    stage: Optional[str] = None,
    subject_name: Optional[str] = None,
    total_score: float = 100,
) -> List[Section]:
    """按学段 + 学科返回标准题型结构；学科未覆盖时退到学段通用六题型模板。

    `stage` 取 primary/junior（与 Grade.stage 一致），缺省按初中处理
    —— 初中题型更全（含多选），误判成初中比误判成小学更接近"标准考试"。
    """
    stage_key = "primary" if str(stage or "").lower() == "primary" else "junior"
    table = _PRIMARY if stage_key == "primary" else _JUNIOR
    raw = table.get(str(subject_name or "").strip()) or table["_generic"]
    return _scale(_to_sections(raw), float(total_score or 100))


def difficulty_gradient(sections: List[Section]) -> Dict[str, int]:
    """由结构反推难度分布（**按题序位置**，前易后难），供组卷对齐。

    为什么要按「题序」而不是按「大题」或「分值」：
    1. 按大题中位归类太粗 —— 初中数学「解答题」一个大题就占 60% 分值，
       整块会被归成同一档，实测算出 hard=0%，与卷面完全不符；
    2. `difficulty_ratio` 本身的语义是**题量比例**（`split_by_difficulty`
       按题数分配），按分值算会与抽题逻辑对不上。

    因此把全卷题目按顺序展开，前 35% 记为 easy、35%~70% medium、后 30% hard
    —— 这既是真实考试的难度梯度（送分题在前、压轴在后），也与抽题口径一致。
    返回百分制整数，余数补到占比最大档，保证合计 = 100。
    """
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
