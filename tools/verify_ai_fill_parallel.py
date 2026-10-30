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
