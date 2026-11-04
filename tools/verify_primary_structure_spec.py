"""小学试卷结构规范对齐验证：五科模板是否与《小学学业水平考试规范》一致。

覆盖点与《初中》版同构，但小学的判定规则不同：
- 只有语文 / 数学 / 英语有纸笔卷，且只针对三至六年级；
- 英语必须**不含听力**（系统无音频能力，按笔试折算 100）；
- 语文 / 数学 / 英语**不得出现判断题**（规范表 4-1/4-2/4-3 均未列）；
- 英语笔试 ≤20 题是硬上限；
- 难度必须取小学区间 65/25/10，不能串到初中的同名学科。

不碰任何真实库（独立临时 SQLite）。用法：
    python tools/verify_primary_structure_spec.py
退出码 0 = 全部通过。
"""
import os
import sys
import tempfile

BACKEND = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
sys.path.insert(0, BACKEND)

DB_PATH = os.path.join(tempfile.gettempdir(), "verify_primary_structure_spec.db")
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)
os.environ["DATABASE_URL"] = "sqlite:///" + DB_PATH.replace("\\", "/")

from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.models import (  # noqa: E402
    Grade, Question, QuestionStatus, Subject, User,
)
from app.services.exam_structures import (  # noqa: E402
    difficulty_gradient, exam_meta, normalize_subject,
    section_total, sections_for,
)
from app.services.paper_compose_service import (  # noqa: E402
    SOURCE_BANK_ONLY, audit_paper, compose, normalize_section_order,
)

FAILED = []

# 规范里真正有纸笔卷的三科（表 2-1 / 表 2-5）
PAPER_SUBJECTS = ["语文", "数学", "英语"]

# 规范表 4-1 / 4-2 / 4-3 的板块分值（五、六年级口径）
# 英语是按去掉听力后 60 分笔试等比例折算到 100 的结果
EXPECTED = {
    # 语文：积累 30 / 阅读 40 / 口语 6 / 习作 24
    "语文": {"blank": 30, "material": 40, "short": 6, "composition": 24},
    # 数学：概念 20（填空10+选择10）/ 计算 24 / 操作 10 / 解决问题 40 / 探究 6
    "数学": {"blank": 10, "single": 10, "calc": 24, "material": 16, "short": 40},
    # 英语：词汇语法 40 / 阅读 50 / 书面表达 10（听力已排除）
    "英语": {"blank": 40, "material": 50, "composition": 10},
}


def check(name, cond, detail=""):
    print(("  PASS  " if cond else "  FAIL  ") + name + (f"  {detail}" if detail else ""))
    if not cond:
        FAILED.append(name)


# ---------------------------------------------------------------- 1. 模板对齐
def verify_templates():
    print("\n[1] 三科卷面结构与规范一致（100 分制、五、六年级口径）")
    for subj, want in EXPECTED.items():
        secs = sections_for("primary", subj)
        total = round(sum(section_total(s) for s in secs), 2)
        check(f"{subj} 卷面 100 分", total == 100.0, str(total))

        by_code = {}
        for s in secs:
            by_code[s["code"]] = round(by_code.get(s["code"], 0) + section_total(s), 2)
        check(f"{subj} 板块分值 {want}", by_code == want, str(by_code))

    # 语文：习作必须最后，且作文 24 分（口语 6 分单列）
    secs = sections_for("primary", "语文")
    check("语文末板块是习作", secs[-1]["code"] == "composition", secs[-1]["name"])
    check("语文习作 24 分 + 口语交际 6 分",
          section_total(secs[-1]) == 24 and any(
              s["code"] == "short" and section_total(s) == 6 for s in secs))

    # 数学：大题数 ≤8（规范表 6-3）
    maths = sections_for("primary", "数学")
    check("数学大题数 ≤8", len(maths) <= 8, f"实际 {len(maths)}")

    # 语文：积累板块 8—10 题
    acc = [s for s in sections_for("primary", "语文") if s["code"] == "blank"][0]
    check("语文积累与运用 8—10 题", 8 <= int(acc["count"]) <= 10, f"实际 {acc['count']}")


# ---------------------------------------------------------------- 2. 无判断题
def verify_no_judge():
    print("\n[2] 语文/数学/英语不含判断题（规范未列该题型）")
    for subj in PAPER_SUBJECTS:
        codes = [s["code"] for s in sections_for("primary", subj)]
        check(f"{subj} 无 judge", "judge" not in codes, str(codes))

    # 科学维持原状（规范为非纸笔，产品决定保留练习卷），判断题仍在 —— 记录现状
    sci = [s["code"] for s in sections_for("primary", "科学")]
    check("科学维持原状（含 judge，属产品决定而非规范对齐）", "judge" in sci, str(sci))


# ---------------------------------------------------------------- 3. 英语专项
def verify_english():
    print("\n[3] 英语：排除听力、笔试 ≤20 题")
    secs = sections_for("primary", "英语")
    n = sum(int(s["count"]) for s in secs)
    check("英语题量 ≤20（规范硬上限）", n <= 20, f"实际 {n}")
    check("英语无独立听力板块",
          not any("听力" in str(s.get("name") or "") for s in secs),
          str([s["name"] for s in secs]))
    check("英语含书面表达", any(s["code"] == "composition" for s in secs))
    # 折算比例：词汇语法 40 / 阅读 50 / 书面 10 ≈ 规范 25 : 30 : 5
    check("英语折算比例接近规范 25:30:5",
          abs(40 / 25 - 50 / 30) < 0.2 and abs(50 / 30 - 10 / 5) < 0.7,
          "40:50:10")


# ---------------------------------------------------------------- 4. 难度
def verify_difficulty():
    print("\n[4] 难度取小学区间 65/25/10，不串初中同名学科")
    for subj in PAPER_SUBJECTS:
        got = difficulty_gradient(sections_for("primary", subj), subj, stage="primary")
        check(f"{subj} 难度 65/25/10",
              got == {"easy": 65, "medium": 25, "hard": 10}, str(got))
        check(f"{subj} 难度合计 100", sum(got.values()) == 100)

    # 初中同名学科不能被小学口径污染
    jy = difficulty_gradient(sections_for("junior", "语文"), "语文", stage="junior")
    check("初中语文仍是 30/50/20（学段隔离）",
          jy == {"easy": 30, "medium": 50, "hard": 20}, str(jy))

    # 小学道德与法治不得继承初中道法的 55/30/15
    df = difficulty_gradient(sections_for("primary", "道德与法治"), "道德与法治",
                             stage="primary")
    check("小学道法不回落到初中 55/30/15", df != {"easy": 55, "medium": 30, "hard": 15}, str(df))
    check("小学道法走位置法兜底且合计 100", sum(df.values()) == 100, str(df))


# ---------------------------------------------------------------- 5. 元信息
def verify_meta():
    print("\n[5] 卷面元信息（分值/时长/题量）")
    want = {"语文": (100, 90, 22), "数学": (100, 90, 26), "英语": (100, 60, 19)}
    for subj, (score, dur, cnt) in want.items():
        meta = exam_meta("primary", subj)
        ok = bool(meta) and meta["written_score"] == score \
            and meta["duration"] == dur and meta["question_count"] == cnt
        check(f"{subj} 元信息 {score}分/{dur}分钟/{cnt}题", ok, str(meta))

    # 科学/道法按规范无纸笔卷，刻意不登记元信息（调用方沿用 100/90）
    for subj in ("科学", "道德与法治"):
        check(f"{subj} 无纸笔元信息（维持现状）", exam_meta("primary", subj) is None)

    # 元信息里的题量必须与模板题量一致，否则卷面体检会对不上
    for subj in PAPER_SUBJECTS:
        meta = exam_meta("primary", subj)
        real = sum(int(s["count"]) for s in sections_for("primary", subj))
        check(f"{subj} 元信息题量 = 模板题量", meta["question_count"] == real,
              f"{meta['question_count']} vs {real}")


# ---------------------------------------------------------------- 6. 学科归一
def verify_subject_alias():
    print("\n[6] 学科名归一在小学段同样生效")
    check("normalize_subject 政治 → 道德与法治",
          normalize_subject("政治") == "道德与法治")
    # 小学段：政治归一后仍落在 _generic（规范未给小学道法纸笔结构）
    a = [s["code"] for s in sections_for("primary", "政治")]
    b = [s["code"] for s in sections_for("primary", "道德与法治")]
    check("小学 政治 与 道德与法治 走同一结构", a == b, f"{a} vs {b}")


# ---------------------------------------------------------------- 7. 端到端组卷
def seed_bank(db):
    grade = Grade(name="六年级", stage="primary", grade_num=6)
    db.add(grade)
    db.flush()
    subject = Subject(name="数学", grade_id=grade.id, textbook_version="人教版")
    db.add(subject)
    db.flush()
    teacher = User(username="t_pri", password=hash_password("x"),
                   real_name="教师", identity="teacher", status="active")
    db.add(teacher)
    db.flush()

    # 按数学模板备题：blank 5 / single 5 / calc 8 / material 3 / short 5
    for code, n in (("blank", 5), ("single", 5), ("calc", 8),
                    ("material", 3), ("short", 5)):
        for i in range(n):
            db.add(Question(
                stem=f"{code} 第 {i + 1} 题（小学结构验证用）",
                type=code, difficulty=["easy", "medium", "hard"][i % 3],
                score=0, answer="A", grade_id=grade.id, subject_id=subject.id,
                status=QuestionStatus.PUBLISHED.value,
                bank_type="public", owner_id=teacher.id,
                source="manual", usage_count=0,
            ))
    db.commit()
    return grade, subject, teacher


def verify_compose():
    print("\n[7] 小学卷端到端组卷")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        grade, subject, teacher = seed_bank(db)
        secs = normalize_section_order(sections_for("primary", "数学"))
        plan = compose(
            db, grade_id=grade.id, subject_id=subject.id, sections=secs,
            source_strategy=SOURCE_BANK_ONLY, viewer_id=teacher.id,
            avoid_recent=False, avoid_duplicate_kp=False,
        )
        total = round(sum(it["score"] for it in plan.items), 2)
        check("整卷 100 分", total == 100.0, str(total))
        check("整卷 26 题", len(plan.items) == 26, f"实际 {len(plan.items)}")
        check("作文/习作类题型不出现在数学卷",
              not any(it["section_code"] == "composition" for it in plan.items))

        # 顺序：概念填空（一）→ 概念选择（二）→ 计算（三）→ 操作（四）→ 解决问题（五）→ 探究（六）
        sec_order = []
        for it in sorted(plan.items, key=lambda x: x["sort_order"]):
            if it["section_code"] not in sec_order:
                sec_order.append(it["section_code"])
        check("大题顺序 填空→选择→计算→操作→解决问题→探究",
              sec_order == ["blank", "single", "calc", "material", "short"],
              str(sec_order))

        issues = audit_paper(plan.items, total_score=100, has_gaps=bool(plan.gaps))
        check("卷面体检无 error", not [i for i in issues if i["level"] == "error"],
              str([i["message"] for i in issues if i["level"] == "error"]))
    finally:
        db.close()


def main():
    verify_templates()
    verify_no_judge()
    verify_english()
    verify_difficulty()
    verify_meta()
    verify_subject_alias()
    verify_compose()

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
