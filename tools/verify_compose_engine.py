"""组卷引擎验证：在独立临时库上造数据，逐项验证已实证的三个缺陷是否修复。

不碰任何真实库。用法：
    python tools/verify_compose_engine.py
退出码 0 = 全部通过。
"""
import json
import os
import sys
import tempfile

BACKEND = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
sys.path.insert(0, BACKEND)

DB_PATH = os.path.join(tempfile.gettempdir(), "verify_compose_engine.db")
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)
os.environ["DATABASE_URL"] = "sqlite:///" + DB_PATH.replace("\\", "/")

from sqlalchemy import select  # noqa: E402

from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.models import (  # noqa: E402
    ExamStandard, Grade, KnowledgePoint, PaperItem, Question, QuestionStatus,
    Subject, Task, TaskStatus, User,
)
from app.services.paper_compose_service import (  # noqa: E402
    SOURCE_AI_ONLY, SOURCE_BANK_FIRST, SOURCE_BANK_ONLY,
    compose, normalize_difficulty, parse_sections, split_by_difficulty,
)
from app.core.security import hash_password  # noqa: E402

FAILED = []


def check(name, cond, detail=""):
    print(("  PASS  " if cond else "  FAIL  ") + name + (f"  {detail}" if detail else ""))
    if not cond:
        FAILED.append(name)


def seed(db):
    grade = Grade(name="七年级", stage="junior", grade_num=7)
    other_grade = Grade(name="八年级", stage="junior", grade_num=8)
    db.add_all([grade, other_grade])
    db.flush()
    subject = Subject(name="数学", grade_id=grade.id, textbook_version="人教版")
    other_subject = Subject(name="语文", grade_id=grade.id)
    db.add_all([subject, other_subject])
    db.flush()

    # 知识点：kp_a 有 6 道题，kp_b 有 6 道题（各难度 2 道）
    kp_a = KnowledgePoint(name="有理数", level=1, grade_id=grade.id, subject_id=subject.id, term=1)
    kp_b = KnowledgePoint(name="整式加减", level=1, grade_id=grade.id, subject_id=subject.id, term=1)
    db.add_all([kp_a, kp_b])
    db.flush()

    teacher = User(username="t1", password=hash_password("x"),
                   real_name="教师一", identity="teacher", status="active")
    db.add(teacher)
    db.flush()

    created = []
    for kp in (kp_a, kp_b):
        for diff in ("easy", "medium", "hard"):
            for i in range(2):
                q = Question(
                    type="single", stem=f"{kp.name}-{diff}-{i} 下列选项正确的是？",
                    options=json.dumps([{"key": "A", "text": "1"}, {"key": "B", "text": "2"}]),
                    answer=json.dumps("A"), analysis="解析略", score=3.0,
                    difficulty=diff, grade_id=grade.id, subject_id=subject.id,
                    knowledge_point_id=kp.id, bank_type="public", owner_id=teacher.id,
                    status=QuestionStatus.PUBLISHED.value,
                )
                db.add(q)
                created.append(q)
    # 一道"非本学科"的题，用于验证年级/学科过滤
    db.add(Question(
        type="single", stem="语文题", options=None, answer=json.dumps("A"),
        score=3.0, difficulty="easy", grade_id=grade.id, subject_id=other_subject.id,
        knowledge_point_id=None, bank_type="public", owner_id=teacher.id,
        status=QuestionStatus.PUBLISHED.value,
    ))
    db.commit()
    return dict(grade=grade, other_grade=other_grade, subject=subject,
                other_subject=other_subject, kp_a=kp_a, kp_b=kp_b,
                teacher=teacher, questions=created)


def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    ctx = seed(db)

    print("\n=== 1. 难度归一化（修复 int(0.3)=0 导致组不出题）===")
    d = normalize_difficulty({"easy": 0.3, "medium": 0.5, "hard": 0.2})
    check("小数权重 0.3/0.5/0.2 → 30/50/20", d == {"easy": 30, "medium": 50, "hard": 20}, str(d))
    check("合计恒为 100", sum(d.values()) == 100, str(sum(d.values())))
    d2 = normalize_difficulty(None)
    check("缺省 → 7:2:1", d2 == {"easy": 70, "medium": 20, "hard": 10}, str(d2))

    print("\n=== 2. 题量拆分不丢题 ===")
    for cnt in (1, 3, 7, 10, 23, 46):
        s = split_by_difficulty(cnt, {"easy": 70, "medium": 20, "hard": 10})
        check(f"count={cnt} 拆分合计={sum(s.values())}", sum(s.values()) == cnt, str(s))

    print("\n=== 3. 知识点过滤在放宽难度时不被丢弃（P1 旧缺陷）===")
    # 只指定 kp_a，要求 8 道单选（kp_a 只有 6 道，必须出现缺口而不是越界抽题）
    plan = compose(
        db, grade_id=ctx["grade"].id, subject_id=ctx["subject"].id,
        sections=[{"code": "single", "name": "单选题", "count": 8,
                   "score_per": 3, "difficulty": "medium", "sort": 1}],
        kp_ids=[ctx["kp_a"].id], difficulty_ratio={"easy": 70, "medium": 20, "hard": 10},
        source_strategy=SOURCE_BANK_FIRST, avoid_recent=False, avoid_duplicate_kp=False,
    )
    kps = {i["knowledge_point_id"] for i in plan.items}
    check("抽到的题全部属于指定知识点", kps <= {ctx["kp_a"].id}, f"实际知识点={kps}")
    check("题库不足时如实留缺口", len(plan.items) == 6 and plan.gaps and plan.gaps[0]["need"] == 8,
          f"抽出{len(plan.items)}题, gaps={plan.gaps}")

    print("\n=== 4. 大题号不再是恒为「一、」（P1 旧缺陷）===")
    plan2 = compose(
        db, grade_id=ctx["grade"].id, subject_id=ctx["subject"].id,
        sections=[{"code": "single", "name": "选择题", "count": 3, "score_per": 3,
                   "difficulty": "easy", "sort": 1}],
        source_strategy=SOURCE_BANK_FIRST, avoid_recent=False, avoid_duplicate_kp=False,
    )
    names = [i["section_name"] for i in plan2.items]
    check("大题名带正确中文序号", all(n.startswith("一、") for n in names), str(set(names)))
    check("没有出现双重前缀「一、一、」", not any("一、一、" in n for n in names), str(set(names)))

    # 多题型场景：必须递增成一、二，而不是两节都叫「一、」
    # 注意：库里只有 single 题型有题，这里直接构造 items 验证 _renumber，
    # 因为 _renumber 是纯函数，不依赖数据库。
    from app.services.paper_compose_service import _renumber
    raw_items = [
        {"question_id": 1, "type": "single", "score": 3, "section_code": "single",
         "section_name": "选择题", "section_sort": 1},
        {"question_id": 2, "type": "blank", "score": 2, "section_code": "blank",
         "section_name": "填空题", "section_sort": 2},
        {"question_id": 3, "type": "short", "score": 6, "section_code": "short",
         "section_name": "简答题", "section_sort": 3},
    ]
    _renumber(raw_items)
    seq = [i["section_name"] for i in raw_items]
    check("多题型序号不重复", len(set(seq)) == len(seq), str(seq))
    check("三节依次为 一/二/三", seq == ["一、选择题", "二、填空题", "三、简答题"], str(seq))

    # 已带旧前缀的名字不应变成「一、一、」
    prefixed = [{"question_id": 1, "type": "single", "score": 3,
                 "section_code": "single", "section_name": "一、单选题", "section_sort": 1}]
    _renumber(prefixed)
    check("旧前缀被剥离后重拼", prefixed[0]["section_name"] == "一、单选题",
          prefixed[0]["section_name"])

    print("\n=== 5. 不与近 3 次考试重复 ===")
    paper_ids = []
    for n in range(3):
        from app.models import Paper
        p = db.execute(select(Question).limit(4).where(
            Question.grade_id == ctx["grade"].id)).scalars().all()
        paper = Paper(name=f"历史卷{n}", grade_id=ctx["grade"].id,
                      subject_id=ctx["subject"].id, total_score=100,
                      duration=60, creator_id=ctx["teacher"].id, source="manual")
        db.add(paper)
        db.flush()
        for idx, q in enumerate(p, start=1):
            db.add(PaperItem(paper_id=paper.id, question_id=q.id,
                             sort_order=idx, score=3, section_name="一、选择题"))
        db.add(Task(title=f"历史任务{n}", type="exam", paper_id=paper.id,
                    subject_id=ctx["subject"].id, grade_id=ctx["grade"].id,
                    creator_id=ctx["teacher"].id, status=TaskStatus.PUBLISHED.value,
                    total_score=100, pass_score=60))
        paper_ids.append(paper.id)
    db.commit()

    plan3 = compose(
        db, grade_id=ctx["grade"].id, subject_id=ctx["subject"].id,
        sections=[{"code": "single", "name": "选择题", "count": 6, "score_per": 3,
                   "difficulty": "easy", "sort": 1}],
        source_strategy=SOURCE_BANK_FIRST, avoid_recent=True, recent_n=3,
        avoid_duplicate_kp=False,
    )
    recent = set()
    for pid in paper_ids:
        recent |= {r for r in db.scalars(
            select(PaperItem.question_id).where(PaperItem.paper_id == pid)).all()}
    overlap = {i["question_id"] for i in plan3.items} & recent
    check("组出的题与近 3 次考试无重复", not overlap,
          f"重复 {len(overlap)} 道；排除池 {plan3.excluded_count} 道")

    print("\n=== 6. 来源策略 ===")
    plan_ai = compose(db, grade_id=ctx["grade"].id, subject_id=ctx["subject"].id,
                      sections=[{"code": "single", "name": "选择题", "count": 5,
                                 "score_per": 2, "difficulty": "easy", "sort": 1}],
                      source_strategy=SOURCE_AI_ONLY)
    check("ai_only 不抽题库题", len(plan_ai.items) == 0 and len(plan_ai.gaps) == 1, str(plan_ai.to_dict()["item_count"]))
    plan_bank = compose(db, grade_id=ctx["grade"].id, subject_id=ctx["subject"].id,
                        sections=[{"code": "single", "name": "选择题", "count": 5,
                                   "score_per": 2, "difficulty": "easy", "sort": 1}],
                        source_strategy=SOURCE_BANK_ONLY, avoid_recent=False,
                        avoid_duplicate_kp=False)
    check("bank_only 只抽题库题", len(plan_bank.items) > 0, f"{len(plan_bank.items)} 题")

    print("\n=== 7. 试卷总分缩放 ===")
    plan4 = compose(db, grade_id=ctx["grade"].id, subject_id=ctx["subject"].id,
                    sections=[{"code": "single", "name": "选择题", "count": 4,
                               "score_per": 3, "difficulty": "easy", "sort": 1}],
                    source_strategy=SOURCE_BANK_ONLY, avoid_recent=False,
                    avoid_duplicate_kp=False, total_score_override=100)
    check("缩放后卷面总分=100", abs(plan4.total_score - 100) < 0.01, str(plan4.total_score))

    print("\n=== 8. 跨年级/学科隔离 ===")
    plan5 = compose(db, grade_id=ctx["other_grade"].id, subject_id=ctx["subject"].id,
                    sections=[{"code": "single", "name": "选择题", "count": 5,
                               "score_per": 3, "difficulty": "easy", "sort": 1}],
                    source_strategy=SOURCE_BANK_ONLY, avoid_recent=False)
    check("八年级无题时不串用七年级题", len(plan5.items) == 0, f"{len(plan5.items)} 题")

    print("\n=== 9. 命题标准解析 ===")
    std = ExamStandard(
        name="测试标准", stage="junior", subject_name="数学", exam_type="final",
        total_score=100, duration=90,
        sections=json.dumps([
            {"code": "single", "name": "一、选择题", "count": 10, "score_per": 3, "sort": 1},
            {"code": "fill", "name": "非法题型", "count": 5, "score_per": 2, "sort": 2},
        ], ensure_ascii=False),
    )
    db.add(std)
    db.commit()
    parsed = parse_sections(std)
    check("非法题型 fill 被过滤", len(parsed) == 1 and parsed[0]["code"] == "single", str(parsed))

    db.close()
    print("\n" + "=" * 60)
    if FAILED:
        print(f"失败 {len(FAILED)} 项：{FAILED}")
        return 1
    print("全部通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
