"""试卷结构规范对齐验证：九科模板是否与《初中毕业学业水平考试试卷结构规范》一致，
以及阶梯分值（score_pattern）在组卷全链路是否真的生效。

不碰任何真实库（独立临时 SQLite）。用法：
    python tools/verify_exam_structure_spec.py
退出码 0 = 全部通过。
"""
import json
import os
import sys
import tempfile

BACKEND = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
sys.path.insert(0, BACKEND)

DB_PATH = os.path.join(tempfile.gettempdir(), "verify_exam_structure_spec.db")
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)
os.environ["DATABASE_URL"] = "sqlite:///" + DB_PATH.replace("\\", "/")

from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.models import (  # noqa: E402
    ExamStandard, Grade, Question, QuestionStatus, Subject, User,
)
from app.services.exam_structures import (  # noqa: E402
    DIFFICULTY_REFERENCE, EXAM_META, difficulty_gradient, exam_meta,
    normalize_subject, section_total, sections_for,
)
from app.services.paper_compose_service import (  # noqa: E402
    SOURCE_AI_ONLY, SOURCE_BANK_ONLY, _renumber, audit_paper, compose,
    normalize_section_order, parse_score_pattern, parse_sections,
)

FAILED = []


def check(name, cond, detail=""):
    print(("  PASS  " if cond else "  FAIL  ") + name + (f"  {detail}" if detail else ""))
    if not cond:
        FAILED.append(name)


# ---------------------------------------------------------------- 1. 模板对齐
def verify_templates():
    print("\n[1] 九科模板题量/分值对齐规范")
    for subject, meta in EXAM_META.items():
        secs = sections_for("junior", subject)
        count = sum(int(s["count"]) for s in secs)
        total = round(sum(section_total(s) for s in secs), 2)
        check(
            f"{subject} 题量 {count} = 规范 {meta['question_count']}",
            count == meta["question_count"], f"实际 {count}")
        check(
            f"{subject} 卷面 {total} = 规范笔试 {meta['written_score']}",
            abs(total - meta["written_score"]) < 0.01, f"实际 {total}")
        check(
            f"{subject} 卷面分不改动总分时不需要缩放",
            abs(sum(section_total(s) for s in secs) - meta["written_score"]) < 0.01)

    # 英语按笔试 90 建，但对外口径仍是 120（笔试 90 + 听说 30）
    en = exam_meta("junior", "英语")
    check("英语 written_score=90 / total_score=120（听说另计）",
          en["written_score"] == 90 and en["total_score"] == 120, str(en.get("note", ""))[:20])


# ---------------------------------------------------------------- 2. 题型种类
def verify_no_forbidden_types():
    print("\n[2] 不得出现规范里没有的题型")
    for subject in EXAM_META:
        codes = [s["code"] for s in sections_for("junior", subject)]
        if subject not in ("语文", "英语", "数学"):
            check(f"{subject} 无判断题（规范未设）", "judge" not in codes, str(codes))
    for subject in ("地理", "生物"):
        codes = [s["code"] for s in sections_for("junior", subject)]
        check(f"{subject} 无填空题（规范未设）", "blank" not in codes, str(codes))
    yw = [s["code"] for s in sections_for("junior", "语文")]
    check("语文无单选题（积累运用是主观题）", "single" not in yw, str(yw))
    en = [s["code"] for s in sections_for("junior", "英语")]
    check("英语无判断题", "judge" not in en, str(en))


# ---------------------------------------------------------------- 3. 阶梯分值
def verify_pattern_shapes():
    print("\n[3] 阶梯分值结构与规范逐项对齐")
    math = {s["code"]: s for s in sections_for("junior", "数学")}
    check("数学解答题 6/6/6/8/8/8/10/11/12",
          math["calc"].get("score_pattern") == [6, 6, 6, 8, 8, 8, 10, 11, 12],
          str(math["calc"].get("score_pattern")))
    check("数学填空 5 题（旧模板是 6 题）", math["blank"]["count"] == 5)

    chem = {s["code"]: s for s in sections_for("junior", "化学")}
    pat = chem["single"].get("score_pattern") or []
    check("化学选择 1—8 题 1 分 / 9—13 题 2 分",
          pat[:8] == [1] * 8 and pat[8:] == [2] * 5, str(pat))
    check("化学选择小计 18 分", section_total(chem["single"]) == 18)

    hist = {s["code"]: s for s in sections_for("junior", "历史")}
    check("历史非选择 4 题（末题观点论述 11 分）",
          hist["short"]["count"] == 4 and section_total(hist["short"]) == 36,
          str(hist["short"].get("score_pattern")))

    yw = sections_for("junior", "语文")
    check("语文作文 50 分且在全卷最后",
          yw[-1]["code"] == "composition" and section_total(yw[-1]) == 50)
    check("语文含整本书阅读板块",
          any("整本书" in s["name"] for s in yw))


# ---------------------------------------------------------------- 4. 分科难度
def verify_difficulty():
    print("\n[4] 分科难度区间取规范值")
    for subject, ref in DIFFICULTY_REFERENCE.items():
        got = difficulty_gradient(sections_for("junior", subject), subject)
        check(f"{subject} 难度 {ref['easy']}/{ref['medium']}/{ref['hard']}",
              got == ref, str(got))
        check(f"{subject} 难度合计 100", sum(got.values()) == 100)

    # 无规范区间时退回按题序位置推算，且仍合计 100
    fallback = difficulty_gradient(sections_for("junior", "体育"), "体育")
    check("未覆盖学科回落到按题序推算且合计 100", sum(fallback.values()) == 100, str(fallback))


# ------------------------------------------------- 4b. 学科名归一（政治→道德与法治）
def verify_subject_alias():
    print("\n[4b] 学科名归一：平台「政治」须解析到规范「道德与法治」")
    # 平台学科真名是「政治」（init_db），规范叫「道德与法治」。不归一，
    # exam_meta/sections_for 全部落空 → 该科退回 100 分/36 题的通用模板。
    check("normalize_subject 政治 → 道德与法治",
          normalize_subject("政治") == "道德与法治", normalize_subject("政治"))
    check("normalize_subject 思想品德/道法/道德与法制 均归一",
          all(normalize_subject(x) == "道德与法治"
              for x in ("思想品德", "道法", "道德与法制")))
    check("normalize_subject 未命中学科原样返回",
          normalize_subject("信息科技") == "信息科技")
    check("normalize_subject 空值不炸", normalize_subject(None) == "")

    meta = exam_meta("junior", "政治")
    check("exam_meta(政治) 取到规范元信息（60 分 / 60 分钟 / 17 题）",
          bool(meta) and meta["written_score"] == 60
          and meta["duration"] == 60 and meta["question_count"] == 17,
          str(meta))

    secs = sections_for("junior", "政治")
    codes = [s["code"] for s in secs]
    count = sum(int(s["count"]) for s in secs)
    total = round(sum(section_total(s) for s in secs), 2)
    check("政治按规范出 17 题", count == 17, str(count))
    check("政治卷面 60 分", total == 60.0, str(total))
    check("政治不含判断题（规范未设）", "judge" not in codes, str(codes))
    check("政治难度取规范 55/30/15",
          difficulty_gradient(secs, "政治") == {"easy": 55, "medium": 30, "hard": 15},
          str(difficulty_gradient(secs, "政治")))


# ---------------------------------------------------------------- 5. 板块顺序
def verify_section_order():
    print("\n[5] 板块顺序：不按题型码打乱，作文恒在末位")
    secs = normalize_section_order(sections_for("junior", "语文"))
    codes = [s["code"] for s in secs]
    check("语文板块顺序保持 积累→古诗文→现代文→整本书→发言稿→作文",
          codes == ["blank", "material", "short", "material", "short", "composition"],
          str(codes))

    mixed = [
        {"code": "composition", "name": "写作", "count": 1, "score_per": 50, "sort": 1},
        {"code": "single", "name": "单项选择", "count": 10, "score_per": 3, "sort": 2},
        {"code": "blank", "name": "填空", "count": 5, "score_per": 3, "sort": 3},
    ]
    ordered = normalize_section_order(mixed)
    check("作文即使排在第 1 位也会被钉到末位",
          [s["code"] for s in ordered][-1] == "composition",
          str([s["code"] for s in ordered]))

    # 同题型多板块不能被合并成同一个大题号
    items = []
    qid = 1
    for s in secs:
        for _ in range(int(s["count"])):
            items.append({
                "question_id": qid, "type": s["code"], "section_code": s["code"],
                "section_name": s["name"], "section_sort": s["sort"], "score": 0,
            })
            qid += 1
    _renumber(items)
    names = {it["section_name"] for it in items}
    check("语文 6 个大题各自独立编号（同题型不合并）", len(names) == 6, str(sorted(names)))
    check("题号连续 1..25", [it["sort_order"] for it in items] == list(range(1, 26)))


# ---------------------------------------------------------------- 6. 解析与校验
def verify_parsing():
    print("\n[6] 分值序列解析与标准校验")
    check("合法序列通过", parse_score_pattern([6, 7, 8], 3) == [6.0, 7.0, 8.0])
    check("长度不符丢弃（退化为均分）", parse_score_pattern([6, 7], 3) is None)
    check("含 0 分丢弃", parse_score_pattern([6, 0, 8], 3) is None)
    check("非数字丢弃", parse_score_pattern(["a", 7, 8], 3) is None)

    std = ExamStandard(
        name="x", stage="junior", subject_name="数学", exam_type="hsee",
        total_score=120, duration=120,
        sections=json.dumps([
            {"code": "single", "name": "单选", "count": 10, "score_per": 3,
             "difficulty": "easy", "sort": 1},
            {"code": "blank", "name": "填空", "count": 5, "score_per": 3,
             "difficulty": "easy", "sort": 2},
            {"code": "calc", "name": "解答题", "count": 9, "score_per": 8.33,
             "score_pattern": [6, 6, 6, 8, 8, 8, 10, 11, 12],
             "difficulty": "hard", "sort": 3},
        ], ensure_ascii=False),
    )
    parsed = parse_sections(std)
    check("parse_sections 保留 score_pattern",
          parsed[2].get("score_pattern") == [6, 6, 6, 8, 8, 8, 10, 11, 12])
    check("parse_sections 小计 120（不因平均值丢分）",
          round(sum(section_total(s) for s in parsed), 2) == 120)


# ---------------------------------------------------------------- 7. 真实组卷
def seed_bank(db):
    grade = Grade(name="九年级", stage="junior", grade_num=9)
    db.add(grade)
    db.flush()
    subject = Subject(name="数学", grade_id=grade.id, textbook_version="人教版")
    db.add(subject)
    db.flush()
    teacher = User(username="t_spec", password=hash_password("x"),
                   real_name="教师", identity="teacher", status="active")
    db.add(teacher)
    db.flush()

    # 按数学模板的题量备题：single 10 / blank 5 / calc 9
    for code, n in (("single", 10), ("blank", 5), ("calc", 9)):
        for i in range(n):
            db.add(Question(
                stem=f"{code} 第 {i + 1} 题（结构规范验证用）",
                type=code, difficulty=["easy", "medium", "hard"][i % 3],
                score=0, answer="A", grade_id=grade.id, subject_id=subject.id,
                status=QuestionStatus.PUBLISHED.value,
                bank_type="public", owner_id=teacher.id,
                source="manual", usage_count=0,
            ))
    db.commit()
    return grade, subject, teacher


def verify_compose_uses_pattern():
    print("\n[7] 组卷按题序赋分（阶梯分值端到端）")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        grade, subject, teacher = seed_bank(db)
        secs = normalize_section_order(sections_for("junior", "数学"))
        plan = compose(
            db, grade_id=grade.id, subject_id=subject.id, sections=secs,
            source_strategy=SOURCE_BANK_ONLY, viewer_id=teacher.id,
            avoid_recent=False, avoid_duplicate_kp=False,
        )
        calc = [it for it in plan.items if it["section_code"] == "calc"]
        calc.sort(key=lambda it: it["sort_order"])
        scores = [it["score"] for it in calc]
        check("解答题抽出 9 道", len(calc) == 9, f"实际 {len(calc)}")
        check("解答题分值呈 6/6/6/8/8/8/10/11/12 梯度",
              scores == [6, 6, 6, 8, 8, 8, 10, 11, 12], str(scores))
        check("整卷合计 120 分",
              round(sum(it["score"] for it in plan.items), 2) == 120,
              str(round(sum(it["score"] for it in plan.items), 2)))
        check("整卷 24 题", len(plan.items) == 24, f"实际 {len(plan.items)}")

        issues = audit_paper(plan.items, total_score=120, has_gaps=bool(plan.gaps))
        check("卷面体检无 error", not [i for i in issues if i["level"] == "error"],
              str([i["message"] for i in issues if i["level"] == "error"]))

        # 缺口路径：题库不足时缺口必须带上完整分值序列，补题才能保住梯度
        plan2 = compose(
            db, grade_id=grade.id, subject_id=subject.id, sections=secs,
            source_strategy=SOURCE_AI_ONLY, viewer_id=teacher.id,
        )
        calc_gap = [g for g in plan2.gaps if g["code"] == "calc"]
        check("全 AI 模式的缺口带出完整分值序列",
              calc_gap and calc_gap[0].get("score_pattern") == [6, 6, 6, 8, 8, 8, 10, 11, 12],
              str(calc_gap[0].get("score_pattern") if calc_gap else None))
    finally:
        db.close()


def main():
    verify_templates()
    verify_no_forbidden_types()
    verify_pattern_shapes()
    verify_difficulty()
    verify_subject_alias()
    verify_section_order()
    verify_parsing()
    verify_compose_uses_pattern()

    print("\n" + "=" * 60)
    if FAILED:
        print(f"失败 {len(FAILED)} 项：")
        for name in FAILED:
            print(f"  - {name}")
        return 1
    print("全部通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
