"""验证 AI 补题（`_ai_fill_gaps`）的并行化：耗时、顺序确定性、失败隔离。

## 为什么单独一个脚本

并行是**性能属性**，不是接口契约：走 HTTP 只能看到"一次组卷多久"，而真正的
组卷耗时被真实模型耗时主导，无法判定并行是否生效。这里直接对 `_ai_fill_gaps`
注入固定延迟的假 Agent（`time.sleep`），把"是否并行"变成可断言的数字：

- 串行：总耗时 ≈ 大题数 × 单次延迟
- 并行：总耗时 ≈ 单次延迟（上界受 `AI_FILL_CONCURRENCY` 限制）

同时验证两个只有并行才需要担心的点：
1. **合并顺序**：结果按 gap 原始顺序合并，不受线程完成顺序影响（否则同一
   请求两次调用会得到不同的大题顺序）；
2. **失败隔离**：某个大题补题抛异常时，其余大题仍要补齐（串行实现里
   try/except 是自然成立的，改并行后容易漏在 future 里）。

不碰真实库：临时 SQLite，跑完删除。
用法：python tools/verify_ai_fill_parallel.py
退出码 0 = 全部通过。
"""
import os
import sys
import tempfile
import time

BACKEND = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
sys.path.insert(0, BACKEND)

DB_PATH = os.path.join(tempfile.gettempdir(), "verify_ai_fill_parallel.db")
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)
os.environ["DATABASE_URL"] = "sqlite:///" + DB_PATH.replace("\\", "/")
os.environ["LLM_ENABLED"] = "false"
os.environ["SCHEDULER_ENABLED"] = "false"
os.environ["SECRET_KEY"] = "ai-fill-parallel-test-key-0123456789"

from sqlalchemy import select  # noqa: E402

import app.agents.question_agent as qa_mod  # noqa: E402
from app.api.v1.paper_compose import _ai_fill_gaps  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.models import (  # noqa: E402
    Grade, Question, Subject, User,
)
from app.services.paper_compose_service import compose  # noqa: E402

FAILED = []
DELAY = 0.35   # 单次"模型调用"耗时（秒）

SECTIONS = [
    {"code": "single", "name": "单选题", "count": 2, "score_per": 5,
     "difficulty": "medium", "sort": 1},
    {"code": "multiple", "name": "多选题", "count": 2, "score_per": 5,
     "difficulty": "medium", "sort": 2},
    {"code": "judge", "name": "判断题", "count": 2, "score_per": 5,
     "difficulty": "medium", "sort": 3},
]


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"  -> {detail}" if detail else ""))
    if not ok:
        FAILED.append(name)


def seed(db):
    """只建最小前置数据：年级 / 学科 / 两种题型的题 / 一个教师。"""
    grade = Grade(name="七年级", stage="junior", grade_num=7)
    db.add(grade)
    db.flush()
    subject = Subject(name="数学", grade_id=grade.id, textbook_version="人教版")
    db.add(subject)
    db.flush()
    teacher = User(username="t_parallel", password=hash_password("x"),
                   real_name="并行测试教师", identity="teacher", status="active",
                   grade_id=grade.id)
    db.add(teacher)
    db.flush()
    for qtype, n in (("single", 3), ("multiple", 3), ("judge", 3)):
        for i in range(n):
            db.add(Question(
                type=qtype, stem=f"[{qtype}] 并行验证题 {i}", score=5,
                difficulty="medium", grade_id=grade.id, subject_id=subject.id,
                bank_type="public", owner_id=teacher.id, status="published",
                options='[{"key":"A","text":"甲"},{"key":"B","text":"乙"}]',
                answer="A", analysis="验证用",
            ))
    db.commit()
    return grade, subject, teacher


def install_fake_agent(fail_types=()):
    """把 Agent.run 换成"睡固定时长再返回该题型全部题"的假实现。"""
    def fake_run(self, db, user_id=None, grade_id=None, subject_id=None,
                 question_type="single", count=5, difficulty="medium",
                 save=False, **kwargs):
        time.sleep(DELAY)
        if question_type in fail_types:
            raise RuntimeError(f"模拟模型在 {question_type} 上超时")
        rows = db.scalars(
            select(Question).where(
                Question.subject_id == subject_id,
                Question.type == question_type,
                Question.status == "published",
            ).limit(count)
        ).all()
        return {"success": True, "data": {"questions": [
            {"id": r.id, "stem": r.stem, "type": r.type} for r in rows
        ]}}

    qa_mod.QuestionGeneratorAgent.run = fake_run


def set_concurrency(value):
    old = getattr(settings, "AI_FILL_CONCURRENCY", 3)
    settings.AI_FILL_CONCURRENCY = value
    return old


def build_plan(db, grade, subject, teacher):
    plan = compose(
        db, grade_id=grade.id, subject_id=subject.id,
        sections=SECTIONS, source_strategy="ai_only",
        viewer_id=teacher.id,
    )
    return plan


def build_plan_one(db, grade, subject, teacher, *, code="single", count=12,
                   name="单选题"):
    """只有一个大题的 plan：把"补题批次 / 重试次数"变成可数的调用序列。"""
    secs = [{"code": code, "name": name, "count": count, "score_per": 5,
             "difficulty": "medium", "sort": 1}]
    return compose(
        db, grade_id=grade.id, subject_id=subject.id,
        sections=secs, source_strategy="ai_only", viewer_id=teacher.id,
    )


EMPTY_REASON = "响应正文为空，通常是 max_tokens 预算被推理 token 耗尽"


def install_empty_agent(calls, *, succeed_after=0, type_filter=None):
    """前 `succeed_after` 次返回**空正文**（预算被推理吃光），之后返回真题。

    用 `served` 游标保证不同批次返回**不同的题**，否则同一道 published 题会被
    反复采纳，测出来的是"重复题"而不是"批次行为"。
    """
    state = {"served": 0}

    def fake_run(self, db, user_id=None, grade_id=None, subject_id=None,
                 question_type="single", count=5, difficulty="medium",
                 save=False, **kwargs):
        calls.append((question_type, count))
        if len(calls) <= succeed_after:
            return {"success": True, "data": {"questions": [], "reason": EMPTY_REASON}}
        asked = type_filter if type_filter else question_type
        rows = db.scalars(
            select(Question).where(
                Question.subject_id == subject_id,
                Question.type == asked,
                Question.status == "published",
            ).order_by(Question.id)
        ).all()
        picked = rows[state["served"]: state["served"] + count]
        state["served"] += len(picked)
        return {"success": True, "data": {"questions": [
            {"id": r.id, "stem": r.stem, "type": r.type} for r in picked
        ]}}

    qa_mod.QuestionGeneratorAgent.run = fake_run


def main() -> int:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        grade, subject, teacher = seed(db)
        install_fake_agent()
        print(f"\n=== AI 补题并行验证（单次模拟耗时 {DELAY}s，3 个大题）===")

        # ---- 1. 串行基线 ----
        old_conc = set_concurrency(1)
        plan = build_plan(db, grade, subject, teacher)
        check("准备：ai_only 产出 3 个缺口", len(plan.gaps) == 3, str(len(plan.gaps)))
        t0 = time.time()
        note_serial = _ai_fill_gaps(db, teacher, plan=plan, grade=grade,
                                    subject=subject,
                                    difficulty_norm={"easy": 30, "medium": 50, "hard": 20})
        serial_elapsed = time.time() - t0
        serial_items = len(plan.items)
        check(f"串行（并发=1）耗时约 3×{DELAY}s",
              serial_elapsed >= DELAY * 3 * 0.9,
              f"{serial_elapsed:.2f}s items={serial_items} note={note_serial[:60]}")
        check("串行也能补满 6 题", serial_items == 6, str(serial_items))

        # ---- 2. 并行 ----
        set_concurrency(3)
        plan2 = build_plan(db, grade, subject, teacher)
        t0 = time.time()
        _ai_fill_gaps(db, teacher, plan=plan2, grade=grade,
                      subject=subject,
                      difficulty_norm={"easy": 30, "medium": 50, "hard": 20})
        par_elapsed = time.time() - t0
        check("并行（并发=3）耗时接近单次调用而非 3 倍",
              par_elapsed < serial_elapsed * 0.75,
              f"并行 {par_elapsed:.2f}s vs 串行 {serial_elapsed:.2f}s")
        check("并行补满 6 题（结果与串行一致）",
              len(plan2.items) == serial_items == 6,
              f"{len(plan2.items)} vs {serial_items}")

        # ---- 3. 顺序确定性 ----
        codes = [i["section_code"] for i in plan2.items]
        check("合并顺序按大纲原序（不看线程完成顺序）",
              codes == ["single", "single", "multiple", "multiple", "judge", "judge"],
              str(codes))
        sorts = [i["section_sort"] for i in plan2.items]
        check("大题序号随缺口排序（1→2→3）",
              sorts == [1, 1, 2, 2, 3, 3], str(sorts))
        # 重复跑一次，顺序必须完全一致（并行最容易在这里翻车）
        plan3 = build_plan(db, grade, subject, teacher)
        _ai_fill_gaps(db, teacher, plan=plan3, grade=grade, subject=subject,
                      difficulty_norm={"easy": 30, "medium": 50, "hard": 20})
        check("重复调用结果顺序稳定",
              [i["section_code"] for i in plan3.items] == codes,
              str([i["section_code"] for i in plan3.items]))

        # ---- 4. 失败隔离 ----
        install_fake_agent(fail_types=("multiple",))
        plan4 = build_plan(db, grade, subject, teacher)
        note_fail = _ai_fill_gaps(db, teacher, plan=plan4, grade=grade,
                                  subject=subject,
                                  difficulty_norm={"easy": 30, "medium": 50, "hard": 20})
        filled_codes = [i["section_code"] for i in plan4.items]
        check("单大题失败不影响其余大题补齐",
              filled_codes.count("single") == 2 and filled_codes.count("judge") == 2
              and "multiple" not in filled_codes, str(filled_codes))
        check("失败原因如实回传（含大题名）",
              "多选题" in note_fail and ("补题失败" in note_fail or "仍缺" in note_fail),
              note_fail[:160])
        check("失败的大题仍留在缺口清单",
              any(g["code"] == "multiple" for g in plan4.gaps),
              str([g["code"] for g in plan4.gaps]))

        # ---- 5. 熔断 / 冷却期直接跳过（不打上游）----
        from app.services import llm_breaker

        orig_snapshot = llm_breaker.snapshot
        try:
            llm_breaker.snapshot = lambda: {
                "breaker": "rate_limit", "reason": "429", "streak": 1,
                "cooldown_remaining": 42,
            }
            plan5 = build_plan(db, grade, subject, teacher)
            note5 = _ai_fill_gaps(db, teacher, plan=plan5, grade=grade,
                                  subject=subject,
                                  difficulty_norm={"easy": 30, "medium": 50, "hard": 20})
            check("限流冷却期不发起补题（避免并发加速熔断升级）",
                  plan5.items == [] and "冷却" in note5, note5[:120])

            llm_breaker.snapshot = lambda: {
                "breaker": "auth", "reason": "401 鉴权失败", "streak": 3,
                "cooldown_remaining": 0,
            }
            plan6 = build_plan(db, grade, subject, teacher)
            note6 = _ai_fill_gaps(db, teacher, plan=plan6, grade=grade,
                                  subject=subject,
                                  difficulty_norm={"easy": 30, "medium": 50, "hard": 20})
            check("鉴权熔断期不发起补题并说明原因",
                  plan6.items == [] and "熔断" in note6, note6[:120])
        finally:
            llm_breaker.snapshot = orig_snapshot

        # ---- 6. 空正文（推理 token 吃光预算）：分档上限 + 减半重试 ----
        # 生产事故现场（2026-11-04）：初中数学三个大题并发补题，10 道单选与
        # 9 道解答两次调用都是 out=8192 / 正文 0，而 5 道填空正常。根因是推理
        # 模型的 thinking token 与正文共享 max_tokens，批次越大越先撞满。
        set_concurrency(1)

        # 6a. 一直空正文：只重试一次，且批次必须**减半**
        calls_a = []
        install_empty_agent(calls_a, succeed_after=999)
        plan_a = build_plan_one(db, grade, subject, teacher, code="single", count=12)
        note_a = _ai_fill_gaps(db, teacher, plan=plan_a, grade=grade, subject=subject,
                               difficulty_norm={"easy": 30, "medium": 50, "hard": 20})
        check("单选题单批上限 = 5（不再是 10）",
              calls_a[0][1] == 5, str(calls_a))
        check("空正文只重试一次（共 2 次调用，不无限重试）",
              len(calls_a) == 2, str(calls_a))
        check("重试时批次减半（5 → 2）",
              len(calls_a) > 1 and calls_a[1][1] < calls_a[0][1], str(calls_a))
        gap_a = plan_a.gaps[0] if plan_a.gaps else {}
        check("缺口上挂出真实原因（不再只说『题库不足』）",
              "预算" in str(gap_a.get("reason")), str(gap_a.get("reason")))
        check("缺口上挂出下一步动作",
              bool(gap_a.get("action")) and "稍后重试" in str(gap_a.get("action")),
              str(gap_a.get("action")))
        check("缺口标注 ai_tried=True（AI 确实试过，不是没开）",
              gap_a.get("ai_tried") is True, str(gap_a.get("ai_tried")))
        check("缺口补齐 miss 字段（ai_only 整段都是缺口）",
              gap_a.get("miss") == 12, str(gap_a.get("miss")))
        check("note 里原因只出现一次（不重复刷屏）",
              note_a.count("预算被推理") <= 1, note_a[:160])

        # 6b. 首次空正文、重试成功：缺口应被补满且不再留 gap
        calls_b = []
        install_empty_agent(calls_b, succeed_after=1)
        plan_b = build_plan_one(db, grade, subject, teacher, code="single", count=2)
        _ai_fill_gaps(db, teacher, plan=plan_b, grade=grade, subject=subject,
                      difficulty_norm={"easy": 30, "medium": 50, "hard": 20})
        check("空正文后减半重试能补齐（take=2 时 2→1）",
              len(calls_b) >= 2 and calls_b[0][1] == 2 and calls_b[1][1] == 1,
              str(calls_b))
        check("重试成功后缺口清零", plan_b.gaps == [], str(plan_b.gaps))
        check("重试成功后试卷题目数正确", len(plan_b.items) == 2, str(len(plan_b.items)))

        # 6c. 重题型的单批上限必须显著小于 10（解答题一题就含完整解题过程）
        calls_c = []
        install_empty_agent(calls_c, succeed_after=0, type_filter="single")
        plan_c = build_plan_one(db, grade, subject, teacher, code="calc",
                                count=12, name="解答题")
        _ai_fill_gaps(db, teacher, plan=plan_c, grade=grade, subject=subject,
                      difficulty_norm={"easy": 30, "medium": 50, "hard": 20})
        check("解答题单批上限 = 3", calls_c[0][1] == 3, str(calls_c[:2]))

        # 6c-2. 困难题的批量必须比同题型的中等题更小。
        # 生产实测（2026-11-05 验收 2.5.4）：同一提示词下 easy 的 reasoning 只占
        # 80 token、正文 494 字正常；hard 直接 output=8192 / reasoning=8191 /
        # 正文 0 字，整批作废。难度是独立于题型的第三个变量，只按题型分档时
        # 困难题单批仍按 5 道发 → 必然 100% 失败再靠「减半重试」兜底，
        # 白烧一次 60~90s 的模型往返。
        hard_calls = []

        def install_hard_agent(calls):
            def fake_run(self, db, user_id=None, grade_id=None, subject_id=None,
                         question_type="single", count=5, difficulty="medium",
                         save=False, **kwargs):
                calls.append((question_type, count, difficulty))
                q = Question(
                    type="single", stem=f"困难题批量验证 {len(calls)}",
                    options='[{"key":"A","text":"甲"},{"key":"B","text":"乙"}]',
                    answer="A", analysis="验证", score=3, difficulty="hard",
                    grade_id=grade.id, subject_id=subject.id, bank_type="public",
                    owner_id=teacher.id, status="draft", source="ai_fill",
                    fingerprint=f"hard-{len(calls)}",
                )
                db.add(q)
                db.commit()
                db.refresh(q)
                return {"success": True, "data": {"questions": [
                    {"id": q.id, "question_id": q.id, "stem": q.stem,
                     "type": "single", "difficulty": "hard", "score": 3,
                     "answer": "A", "analysis": "验证",
                     "options": [{"key": "A", "text": "甲"}]}]}}
            return fake_run

        orig_run = qa_mod.QuestionGeneratorAgent.run
        qa_mod.QuestionGeneratorAgent.run = install_hard_agent(hard_calls)
        try:
            plan_h = build_plan_one(db, grade, subject, teacher, code="single",
                                    count=4, name="困难单选题")
            for g in plan_h.gaps:
                g["difficulty"] = "hard"
            _ai_fill_gaps(db, teacher, plan=plan_h, grade=grade, subject=subject,
                          difficulty_norm={"easy": 0, "medium": 0, "hard": 100})
        finally:
            qa_mod.QuestionGeneratorAgent.run = orig_run
        hard_batches = [c[1] for c in hard_calls if c[2] == "hard"]
        check("困难题单批上限 = 2（同一题型中等题为 5）",
              bool(hard_batches) and hard_batches[0] == 2, str(hard_calls[:3]))
        check("困难题补题时确实把 difficulty=hard 传下去",
              any(c[2] == "hard" for c in hard_calls), str(hard_calls[:3]))

        # 6d. 同一大题补多批：published 题不得跨批次重复采纳。
        # 会把 `used_ids` 当快照传进来、补题过程中不回写，第一批选中的 published
        # 题在第二批还能被再选一次（卷内出现两道同样的题）。假 agent 用「每批都
        # 从头返回同一批题」来复现最恶劣的情况。
        def install_repeat_agent(calls):
            def fake_run(self, db, user_id=None, grade_id=None, subject_id=None,
                         question_type="single", count=5, difficulty="medium",
                         save=False, **kwargs):
                calls.append((question_type, count))
                rows = db.scalars(
                    select(Question).where(
                        Question.subject_id == subject_id,
                        Question.type == question_type,
                        Question.status == "published",
                    ).order_by(Question.id).limit(count)
                ).all()
                return {"success": True, "data": {"questions": [
                    {"id": r.id, "stem": r.stem, "type": r.type} for r in rows
                ]}}
            qa_mod.QuestionGeneratorAgent.run = fake_run

        calls_d = []
        install_repeat_agent(calls_d)
        # 题库只有 3 道 single，缺口要 8 道 → 必然跨批次（cap=5：5+3）
        plan_d = build_plan_one(db, grade, subject, teacher, code="single", count=8)
        _ai_fill_gaps(db, teacher, plan=plan_d, grade=grade, subject=subject,
                      difficulty_norm={"easy": 30, "medium": 50, "hard": 20})
        picked_d = [i["question_id"] for i in plan_d.items]
        check("跨批次不重复采纳 published 题",
              len(picked_d) == len(set(picked_d)), str(picked_d))
        check("题库只有 3 道可复用题 → 缺口如实上报，不硬凑",
              len(picked_d) <= 3 and bool(plan_d.gaps),
              f"items={len(picked_d)} gaps={len(plan_d.gaps)}")

        install_fake_agent()
        set_concurrency(old_conc)

        print("\n" + "=" * 60)
        if FAILED:
            print(f"失败 {len(FAILED)} 项：")
            for f in FAILED:
                print("  -", f)
            print(f"\n串行 {serial_elapsed:.2f}s / 并行 {par_elapsed:.2f}s"
                  f"（加速 {serial_elapsed / max(par_elapsed, 0.01):.1f}×）")
            return 1
        print(f"全部通过：串行 {serial_elapsed:.2f}s → 并行 {par_elapsed:.2f}s"
              f"（加速 {serial_elapsed / max(par_elapsed, 0.01):.1f}×）")
        return 0
    finally:
        db.close()
        try:
            os.remove(DB_PATH)
        except OSError:
            pass


if __name__ == "__main__":
    sys.exit(main())
