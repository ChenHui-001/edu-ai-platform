"""湖北省学业水平考试命题标准种子数据 + 幂等播种。

设计要点
--------
1. **只播种一次**：以 `sys_config` 标记位判断，已播种过则完全跳过。
   管理员之后在后台改的题型/分值/难度**不会被下一次升级覆盖**——
   这正是需求里「可视化配置、无需改代码」的前提。
2. **按维度幂等**：即使标记位被清，`_existing_keys()` 也会跳过
   (region, stage, subject_name, exam_type) 已存在的记录，
   不会产生重复标准。
3. **难度用百分制整数**：70/20/10 而非 0.7/0.5/0.1。
   历史实现用小数权重再被 `int()` 截断为 0，是"组不出题"的根因之一。
4. **题型 code 必须合法**：只允许 single/multiple/judge/blank/short/calc/
   material/composition。历史提示词里写 `fill`/`solve` 会被静默丢弃，
   导致题量缺口且无任何报错。`_validate_section()` 在播种时就把这类
   错误炸出来，而不是等到组卷时才表现为"少了几道题"。
"""
import json
import logging
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ExamStandard, SysConfig

logger = logging.getLogger(__name__)

# 合法题型（与 QuestionType 严格一致）
VALID_TYPES = {
    "single", "multiple", "judge", "blank",
    "short", "calc", "material", "composition",
}

# 默认难度分布：7:2:1（需求明确要求）
DEFAULT_DIFFICULTY = {"easy": 70, "medium": 20, "hard": 10}

_SEED_MARKER = "exam_standard_seed_v1"


def _sec(code: str, name: str, count: int, score_per: float,
         difficulty: str = "medium", sort: int = 0) -> Dict[str, Any]:
    """构造一个大题定义。score_per 支持小数（如英语 1.5 分/题）。"""
    return {
        "code": code, "name": name, "count": count,
        "score_per": score_per, "difficulty": difficulty, "sort": sort,
    }


# 小学（primary）：语文 / 数学 / 英语 / 科学 —— 均为 100 分制
_PRIMARY: List[Dict[str, Any]] = [
    {
        "subject_name": "语文", "exam_type": "final",
        "name": "湖北省小学语文期末学业水平考试（100分）",
        "total_score": 100, "duration": 90,
        "description": "积累与运用 + 阅读理解 + 习作。以课程标准第二/三学段要求为基准。",
        "sections": [
            _sec("single", "一、选择题（字音字形/词语运用/病句辨析）", 8, 2, "easy", 1),
            _sec("blank", "二、填空题（古诗文积累与课文填空）", 10, 2, "easy", 2),
            _sec("judge", "三、判断题（文学常识与语言规范）", 5, 2, "medium", 3),
            _sec("material", "四、阅读理解（课内+课外短文）", 3, 8, "medium", 4),
            _sec("composition", "五、习作（不少于400字）", 1, 30, "hard", 5),
        ],
    },
    {
        "subject_name": "数学", "exam_type": "final",
        "name": "湖北省小学数学期末学业水平考试（100分）",
        "total_score": 100, "duration": 90,
        "description": "数与代数 / 图形与几何 / 统计与概率 / 综合实践四大领域平衡覆盖。",
        "sections": [
            _sec("single", "一、选择题", 10, 2, "easy", 1),
            _sec("blank", "二、填空题", 10, 2, "easy", 2),
            _sec("judge", "三、判断题", 5, 2, "medium", 3),
            _sec("calc", "四、计算题（含简便运算与解方程）", 4, 6, "medium", 4),
            _sec("short", "五、解决问题", 4, 6.5, "hard", 5),
        ],
    },
    {
        "subject_name": "英语", "exam_type": "final",
        "name": "湖北省小学英语期末学业水平考试（100分）",
        "total_score": 100, "duration": 60,
        "description": "听力理解 + 语言知识 + 读写综合。听力以选择题形式计入单选题型。",
        "sections": [
            _sec("single", "一、选择题（含听力理解与单项选择）", 15, 2, "easy", 1),
            _sec("judge", "二、判断题（看图判断/正误判断）", 10, 1, "easy", 2),
            _sec("blank", "三、填空题（词汇与语法填空）", 10, 2, "medium", 3),
            _sec("material", "四、阅读理解", 2, 10, "medium", 4),
            _sec("composition", "五、书面表达（不少于50词）", 1, 20, "hard", 5),
        ],
    },
    {
        "subject_name": "科学", "exam_type": "final",
        "name": "湖北省小学科学期末学业水平考试（100分）",
        "total_score": 100, "duration": 60,
        "description": "物质科学 / 生命科学 / 地球与宇宙 / 技术与工程四大领域。",
        "sections": [
            _sec("single", "一、选择题", 20, 2, "easy", 1),
            _sec("judge", "二、判断题", 10, 2, "easy", 2),
            _sec("blank", "三、填空题", 10, 2, "medium", 3),
            _sec("short", "四、简答题（实验现象与原理分析）", 2, 10, "hard", 4),
        ],
    },
]

# 初中（junior）：语文/数学/英语 120 分，物理 70，化学 50，道法/历史 60
_JUNIOR: List[Dict[str, Any]] = [
    {
        "subject_name": "语文", "exam_type": "hsee",
        "name": "湖北省初中学业水平考试语文（120分）",
        "total_score": 120, "duration": 150,
        "description": "积累与运用 + 古诗文阅读 + 现代文阅读 + 写作。",
        "sections": [
            _sec("single", "一、积累与运用（选择题）", 10, 2, "easy", 1),
            _sec("blank", "二、古诗文默写", 6, 2, "easy", 2),
            _sec("material", "三、古诗文阅读", 3, 8, "medium", 3),
            _sec("short", "四、现代文阅读", 3, 8, "medium", 4),
            _sec("composition", "五、写作（不少于600字）", 1, 40, "hard", 5),
        ],
    },
    {
        "subject_name": "数学", "exam_type": "hsee",
        "name": "湖北省初中学业水平考试数学（120分）",
        "total_score": 120, "duration": 120,
        "description": "选择 30 + 填空 18 + 解答 72。解答题按难度梯度递进。",
        "sections": [
            _sec("single", "一、选择题", 10, 3, "easy", 1),
            _sec("blank", "二、填空题", 6, 3, "medium", 2),
            _sec("calc", "三、解答题", 9, 8, "hard", 3),
        ],
    },
    {
        "subject_name": "英语", "exam_type": "hsee",
        "name": "湖北省初中学业水平考试英语（120分）",
        "total_score": 120, "duration": 100,
        "description": "听力与语言知识 55 + 阅读 35 + 书面表达 30。",
        "sections": [
            _sec("single", "一、听力理解与单项选择", 20, 1.5, "easy", 1),
            _sec("blank", "二、词汇与语法填空", 10, 1.5, "medium", 2),
            _sec("judge", "三、正误判断", 10, 1, "easy", 3),
            _sec("material", "四、阅读理解", 5, 7, "medium", 4),
            _sec("composition", "五、书面表达（不少于80词）", 1, 30, "hard", 5),
        ],
    },
    {
        "subject_name": "物理", "exam_type": "hsee",
        "name": "湖北省初中学业水平考试物理（70分）",
        "total_score": 70, "duration": 75,
        "description": "选择题 24 + 填空 10 + 实验探究 20 + 计算 16。",
        "sections": [
            _sec("single", "一、选择题", 8, 3, "easy", 1),
            _sec("blank", "二、填空题", 5, 2, "medium", 2),
            _sec("short", "三、实验探究题", 2, 10, "medium", 3),
            _sec("calc", "四、计算题", 2, 8, "hard", 4),
        ],
    },
    {
        "subject_name": "化学", "exam_type": "hsee",
        "name": "湖北省初中学业水平考试化学（50分）",
        "total_score": 50, "duration": 50,
        "description": "选择题 24 + 填空 8 + 实验与探究 12 + 计算 6。",
        "sections": [
            _sec("single", "一、选择题", 8, 3, "easy", 1),
            _sec("blank", "二、填空题", 4, 2, "medium", 2),
            _sec("material", "三、实验与探究题", 2, 6, "medium", 3),
            _sec("calc", "四、计算题", 1, 6, "hard", 4),
        ],
    },
    {
        "subject_name": "道德与法治", "exam_type": "hsee",
        "name": "湖北省初中学业水平考试道德与法治（60分）",
        "total_score": 60, "duration": 60,
        "description": "选择题 24 + 材料分析 24 + 实践探究 12。",
        "sections": [
            _sec("single", "一、选择题", 12, 2, "easy", 1),
            _sec("material", "二、材料分析题", 3, 8, "medium", 2),
            _sec("short", "三、实践探究题", 2, 6, "hard", 3),
        ],
    },
]


def _validate_standard(raw: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """播种前校验：题型合法 + 小计与总分一致。

    这两点是最容易静默出错的地方：
    - 非法题型被组卷引擎忽略 → 题目数量比预期少，且没有任何报错；
    - 小计不等于总分 → 卷面分与「总分 100」矛盾，及格线计算随之失真。
    """
    sections = raw.get("sections") or []
    if not sections:
        return False, "sections 为空"
    subtotal = 0.0
    for s in sections:
        code = s.get("code")
        if code not in VALID_TYPES:
            return False, f"非法题型 code={code!r}，合法值 {sorted(VALID_TYPES)}"
        try:
            count = int(s.get("count") or 0)
            score_per = float(s.get("score_per") or 0)
        except (TypeError, ValueError):
            return False, f"题型 {code} 的 count/score_per 非数值"
        if count <= 0 or score_per <= 0:
            return False, f"题型 {code} 的题量与单题分值必须为正"
        subtotal += count * score_per
    total = float(raw.get("total_score") or 0)
    if abs(round(subtotal, 2) - total) > 0.01:
        return False, f"小计 {round(subtotal, 2)} ≠ 总分 {total}"
    return True, None


def _existing_keys(db: Session) -> set:
    rows = db.execute(select(
        ExamStandard.region, ExamStandard.stage,
        ExamStandard.subject_name, ExamStandard.exam_type,
    )).all()
    return {(r[0], r[1], r[2], r[3]) for r in rows}


def seed_exam_standards(db: Session, *, force: bool = False) -> Dict[str, Any]:
    """幂等播种湖北命题标准。

    force=True 时忽略标记位（仅用于测试 / 管理员主动重置），
    但仍会跳过已存在的四元维度，不会产生重复记录。

    返回 {created, skipped, errors, already_seeded}。
    """
    marker = db.scalar(select(SysConfig.value).where(SysConfig.key == _SEED_MARKER))
    if marker and not force:
        return {"created": 0, "skipped": 0, "errors": [], "already_seeded": True}

    existing = _existing_keys(db)
    created = 0
    skipped = 0
    errors: List[str] = []

    for stage, group in (("primary", _PRIMARY), ("junior", _JUNIOR)):
        for raw in group:
            key = ("hubei", stage, raw["subject_name"], raw["exam_type"])
            if key in existing:
                skipped += 1
                continue
            ok_, err = _validate_standard(raw)
            if not ok_:
                errors.append(f"{raw['subject_name']}: {err}")
                logger.error("命题标准种子校验失败 %s: %s", raw.get("name"), err)
                continue
            db.add(ExamStandard(
                name=raw["name"], region="hubei", stage=stage,
                subject_name=raw["subject_name"], exam_type=raw["exam_type"],
                total_score=float(raw["total_score"]), duration=int(raw["duration"]),
                sections=json.dumps(raw["sections"], ensure_ascii=False),
                difficulty_ratio=json.dumps(DEFAULT_DIFFICULTY, ensure_ascii=False),
                description=raw.get("description"),
                is_active=True, is_default=True, source="seed",
                sort=len(group),
            ))
            created += 1
            existing.add(key)

    # 标记位：只有确实播种成功才写，避免"标记已写但一条没进"的假象
    if created and not errors:
        row = db.scalar(select(SysConfig).where(SysConfig.key == _SEED_MARKER))
        if row:
            row.value = "1"
        else:
            db.add(SysConfig(key=_SEED_MARKER, value="1", value_type="string",
                             category="system", is_public=False))
    db.commit()
    if created:
        logger.warning("命题标准播种完成：新增 %s 条（跳过 %s 条已存在）", created, skipped)
    return {"created": created, "skipped": skipped,
            "errors": errors, "already_seeded": False}
