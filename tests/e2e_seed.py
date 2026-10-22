# -*- coding: utf-8 -*-
"""
阶段解耦：单阶段可独立运行所需的**前置数据自建**能力。

## 为什么需要这个模块

`run_all.py` 的 15 个阶段原先是一条**有状态串联**的流水线：阶段二（教师）
建题 → 组卷 → 发布考试，把 `paper_id` / `task_id` 写进 `R.context`，阶段三
（学生）再从 `R.context` 里取。于是：

- `python tests/run_all.py student` 单跑 → `R.context["task_id"]` 为 None →
  用例直接 `return`，只剩 2~3 条「任务不存在」的 FAIL；
- 想在本地快速验证学生侧改动，只能跑 35 分钟全量。

这属于「隐式假设前置阶段已执行」，是反馈回路过长的直接原因之一。

## 设计原则

1. **`R.context` 降级为纯缓存**：有就复用（全量跑时零额外开销），没有就自建。
2. **自建不依赖任何其他阶段**：只用目标学生自己的年级/学科解析数据，
   建题 → 组卷 → 下发一条完整链路，保证被下发的学生真的能取到卷。
3. **幂等**：调用方先看 `R.context`，本模块只在缺失时被调用。
4. **题面/答案单一来源**：`QUESTIONS` 同时被阶段二与本模块使用，
   避免「学生阶段的预期答案」和「教师阶段实际建的题」漂移。
"""
import time

from e2e_framework import R, data_of, rows_of

# ---------------------------------------------------------------- 题面定义
# 五种题型的标准答案设计（故意把答案留給学生阶段做对错混合）
# 分值合计 100：10 + 15 + 10 + 15 + 50
# ⚠️ 学生阶段的断言依赖 `short` 题 full_score == 50，改分值需同步
#    tests/test_student.py 的 `subj = next(... full_score == 50 ...)`。
QUESTIONS = [
    {
        "type": "single", "difficulty": "easy", "score": 10,
        "stem": "【自动化测试】一元一次方程 3x + 5 = 20 的解是？",
        "options": [{"key": "A", "text": "x = 3"}, {"key": "B", "text": "x = 5"},
                    {"key": "C", "text": "x = 15"}, {"key": "D", "text": "x = 25"}],
        "answer": "B", "analysis": "移项得 3x=15，故 x=5。",
    },
    {
        "type": "multiple", "difficulty": "medium", "score": 15,
        "stem": "【自动化测试】下列属于一元一次方程的是？",
        "options": [{"key": "A", "text": "2x+1=7"}, {"key": "B", "text": "x²-4=0"},
                    {"key": "C", "text": "3y-2=5"}, {"key": "D", "text": "x+y=3"}],
        "answer": ["A", "C"], "analysis": "一元一次方程只含一个未知数且未知数次数为1。",
    },
    {
        "type": "judge", "difficulty": "easy", "score": 10,
        "stem": "【自动化测试】方程 x = 3 的解在数轴上表示点 (3, 0)。",
        "options": [{"key": "T", "text": "正确"}, {"key": "F", "text": "错误"}],
        "answer": "T", "analysis": "方程的解对应数轴上的一个点。",
    },
    {
        "type": "blank", "difficulty": "medium", "score": 15,
        "stem": "【自动化测试】若 5x - 8 = 12，则 x = 【】。",
        "options": [], "answer": "4", "analysis": "5x=20，x=4。",
    },
    {
        # 主观题必须用合法枚举 short（不是 subjective）。
        "type": "short", "difficulty": "medium", "score": 50,
        "stem": "【自动化测试】请用配方法解方程 x² - 6x + 5 = 0，并写出推导过程。",
        "options": [], "answer": "x²-6x+5=0 ⟹ (x-3)²=4 ⟹ x-3=±2 ⟹ x=1 或 x=5",
        "analysis": "配方法：移项后两边加 9，化为完全平方。",
    },
]


def resolve_scope(tea, stu):
    """解析目标学生的「年级 + 学科 + 知识点」，返回 dict。

    学科必须取**学生自己年级**的那一条：`Subject` 唯一键是
    `(grade_id, name)`，「数学」在 1~9 年级各有一条、9 个不同 id。
    取错年级会建出一批学生抽不到的题。
    """
    grade_id = (stu.user or {}).get("grade_id") or 7
    subs, _, _ = tea.get("/edu/subjects", params={"grade_id": grade_id})
    items = rows_of(subs)
    subject_id = next((s["id"] for s in items if s.get("name") == "数学"), None)
    if subject_id is None and items:
        subject_id = items[0]["id"]
    if subject_id is None:
        # 兜底用全量列表里的第一条，再退到 1（种子数据必有一条）
        all_subs = rows_of(tea.get("/edu/subjects")[0])
        subject_id = all_subs[0]["id"] if all_subs else 1
    kps, _, _ = tea.get("/edu/knowledge/list",
                        params={"grade_id": grade_id, "subject_id": subject_id})
    kp_list = rows_of(kps)
    return {
        "grade_id": grade_id,
        "subject_id": subject_id,
        "kp_id": kp_list[0]["id"] if kp_list else None,
        "kp_count": len(kp_list),
    }


def ensure_exam_chain(tea, stu, tag=None, quiet=False):
    """保证「一张已下发给 stu 的可用考试」存在，返回定位用的 dict。

    返回字段：`task_id` / `paper_id` / `subject_id` / `grade_id` / `qids` / `tag`

    失败时返回 `{"task_id": None, ...}` 并把原因写进 `error`，
    由调用方决定是 `R.env()`（环境/前置缺失）还是 `R.issue()`（真缺陷）。
    """
    scope = resolve_scope(tea, stu)
    tag = tag or f"SEED{int(time.time()) % 100000}"
    result = {
        "task_id": None, "paper_id": None, "qids": {}, "tag": tag,
        "subject_id": scope["subject_id"], "grade_id": scope["grade_id"],
        "kp_id": scope["kp_id"], "error": None,
    }

    if not quiet:
        print(f"  \033[93m[INFO]\033[0m 阶段解耦：自建前置考试"
              f"（年级={scope['grade_id']} 学科={scope['subject_id']} "
              f"知识点={scope['kp_count']} 条 tag={tag}）")

    # ---- 1) 建题
    qids = {}
    for q in QUESTIONS:
        body = dict(q)
        body["stem"] = body["stem"].replace("【自动化测试】", f"【{tag}】")
        body["subject_id"] = scope["subject_id"]
        body["grade_id"] = scope["grade_id"]
        body["knowledge_point_id"] = scope["kp_id"]
        body["bank_type"] = "private"
        p, _, _ = tea.post("/question/questions", body, timeout=60)
        d = data_of(p) or {}
        if p.get("success") and d.get("id"):
            qids[q["type"]] = d["id"]
    result["qids"] = qids
    if len(qids) < 5:
        result["error"] = (f"自建题目仅成功 {len(qids)}/5，"
                           f"题型={sorted(qids)}；建题接口可能对当前账号不可用")
        return result

    # ---- 2) 组卷（分值布局必须与学生阶段的断言一致）
    items = [{"question_id": qids["single"], "score": 10, "section_name": "选择题"},
             {"question_id": qids["multiple"], "score": 15, "section_name": "选择题"},
             {"question_id": qids["judge"], "score": 10, "section_name": "判断题"},
             {"question_id": qids["blank"], "score": 15, "section_name": "填空题"},
             {"question_id": qids["short"], "score": 50, "section_name": "解答题"}]
    p, _, _ = tea.post("/question/papers", {
        "name": f"【{tag}】阶段三前置卷（自建）",
        "subject_id": scope["subject_id"], "grade_id": scope["grade_id"],
        "duration": 60, "items": items,
    })
    paper_id = (data_of(p) or {}).get("id")
    result["paper_id"] = paper_id
    if not paper_id:
        result["error"] = f"自建试卷失败：{p.get('message')}"
        return result

    # ---- 3) 下发（按 student_ids 精确指定，避开任教班级不匹配）
    stu_id = (stu.user or {}).get("id")
    if not stu_id:
        result["error"] = "目标学生未登录，拿不到 user.id，无法精确下发"
        return result
    p, _, _ = tea.post("/task/tasks", {
        "title": f"【{tag}】阶段三前置考试（自建）", "type": "exam",
        "paper_id": paper_id, "duration": 60, "allow_retake": 1,
        "show_answer": True, "anti_cheat": True, "pass_score": 60,
        "class_ids": [], "student_ids": [stu_id],
        "description": "阶段解耦自建的前置考试",
    })
    task_id = (data_of(p) or {}).get("id")
    result["task_id"] = task_id
    if not task_id:
        result["error"] = f"自建考试下发失败：{p.get('message')}"
        return result

    # 写入上下文，供同阶段后续用例复用（阶段名基于「缓存」，不构成依赖）
    R.context["task_id"] = task_id
    R.context["paper_id"] = paper_id
    R.context["subject_id"] = scope["subject_id"]
    R.context["grade_id"] = scope["grade_id"]
    R.context["qids"] = qids
    return result
