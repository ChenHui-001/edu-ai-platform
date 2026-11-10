"""P0-4 反向验证：智能组卷 Agent 默认参数必须真的出题，且纯预览不能崩。

三条断言：
1. `_split_counts` 对「比例」与「题量」两种入参都给出正确整数且合计对齐。
2. 不传 type_ratio（走默认比例）时 `_compose` 能抽出题（旧实现恒 0 题）。
3. save=False 时 run() 不抛异常（旧实现 `paper.id` → AttributeError）。
"""
import os
import sys
import tempfile

BACKEND = os.path.join(os.path.dirname(__file__), "..", "backend")
sys.path.insert(0, BACKEND)

os.environ.setdefault("LLM_ENABLED", "false")
os.environ.setdefault("CAPTCHA_ENFORCED", "false")
os.environ["SEED_BASE_DATA"] = "true"

_tmp = tempfile.mkdtemp(prefix="p0_4_")
os.environ["DATABASE_URL"] = f"sqlite:///{os.path.join(_tmp, 'verify.db').replace(os.sep, '/')}"

from app.core.database import Base, SessionLocal, engine  # noqa: E402
import app.models  # noqa: F401,E402
from app.models import Question, User  # noqa: E402
from app.services.init_db import init_grades_subjects  # noqa: E402
from app.agents.paper_agent import PaperComposerAgent, _split_counts  # noqa: E402

failures = []


def check(cond, msg):
    if cond:
        print(f"[PASS] {msg}")
    else:
        print(f"[FAIL] {msg}")
        failures.append(msg)


def seed_questions(db, grade_id, subject_id, owner_id, per_type=12):
    for qtype in ("single", "blank", "short"):
        for i in range(per_type):
            diff = ("easy", "medium", "hard")[i % 3]
            db.add(Question(
                type=qtype, stem=f"{qtype}-{i} 题干", options='[{"key":"A","text":"1"}]',
                answer="A", score=5, difficulty=diff,
                grade_id=grade_id, subject_id=subject_id, owner_id=owner_id,
                status="published", bank_type="public",
            ))
    db.commit()


def main():
    # ---- 1) 语义归一
    r = _split_counts({"single": 0.5, "blank": 0.2, "short": 0.3}, default_total=10)
    check(r == {"single": 5, "blank": 2, "short": 3}, f"默认比例 → {r}（应为 5/2/3）")

    c = _split_counts({"single": 5, "blank": 3, "short": 2}, default_total=10)
    check(c == {"single": 5, "blank": 3, "short": 2}, f"显式题量 → {c}（应原样保留）")

    # 数值 >1 一律按题量理解（50 题也可能是真实题量），语义歧义时不做猜测
    p = _split_counts({"single": 5, "blank": 3, "short": 2}, default_total=20)
    check(sum(p.values()) == 10, f"题量优先 → {p}（合计应=10，不被 default_total 改写）")

    check(_split_counts({}, 10) == {}, "空入参 → {}（不崩）")

    # ---- 2/3) 真跑 run()
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    init_grades_subjects(db)
    db.commit()

    u = User(username="p04", password="x", real_name="验证", status="active")
    db.add(u)
    db.commit()
    db.refresh(u)

    g = db.query(app.models.Grade).filter(app.models.Grade.grade_num == 7).first()
    s = db.query(app.models.Subject).filter(app.models.Subject.grade_id == g.id).first()
    seed_questions(db, g.id, s.id, u.id)

    agent = PaperComposerAgent()

    # 只传必填，type_ratio/difficulty_ratio 全走默认（旧实现 0 题）
    try:
        res = agent.run(db, user_id=u.id, grade_id=g.id, subject_id=s.id,
                        total_score=100, save=False)
        check(bool(res.get("success")), f"save=False 执行成功（message={res.get('message')}）")
        data = res.get("data") or {}
        n = (data.get("paper") or {}).get("item_count", 0)
        check(n > 0, f"默认参数出题数 = {n}（旧实现恒 0）")
        tr = (data.get("difficulty_report") or {}).get("target_ratio", {})
        check(all(v > 0 for v in tr.values()) and tr,
              f"目标难度占比非零 = {tr}（旧实现 int(0.3)=0）")
    except Exception as exc:
        check(False, f"save=False 抛异常：{type(exc).__name__}: {exc}")

    # 显式题量 + 落库
    try:
        res2 = agent.run(db, user_id=u.id, grade_id=g.id, subject_id=s.id,
                         total_score=100, save=True,
                         type_ratio={"single": 5, "blank": 3, "short": 2})
        check(bool(res2.get("success")), f"save=True 执行成功（message={res2.get('message')}）")
        d2 = res2.get("data") or {}
        n2 = (d2.get("paper") or {}).get("item_count", 0)
        pid = (d2.get("paper") or {}).get("id")
        check(n2 == 10, f"显式题量 5/3/2 → 出题 {n2}（应为 10）")
        check(bool(pid), f"save=True 已落库 paper.id={pid}")
    except Exception as exc:
        check(False, f"save=True 抛异常：{type(exc).__name__}: {exc}")

    # ---- 5) P1-7：提示词要求输出 grade_num / subject_name，必须能反查成 id
    g7 = db.query(app.models.Grade).filter(app.models.Grade.grade_num == 7).first()
    s7 = db.query(app.models.Subject).filter(app.models.Subject.grade_id == g7.id).first()
    rg, rs = PaperComposerAgent._resolve_grade_subject(
        db, None, None, {"grade_num": 7, "subject_name": s7.name})
    check(rg == g7.id and rs == s7.id,
          f"名称/序号 → id 反查：grade={rg}(期望 {g7.id}) subject={rs}(期望 {s7.id})")

    # ---- 6) P1-6：他人私有题不得进入预览
    other = User(username="p04_other", password="x", real_name="别人", status="active")
    db.add(other)
    db.commit()
    db.refresh(other)
    private_q = Question(
        type="single", stem="他人私有题", answer="A", score=5, difficulty="easy",
        grade_id=g.id, subject_id=s.id, owner_id=other.id,
        status="published", bank_type="private")
    db.add(private_q)
    db.commit()
    db.refresh(private_q)

    plan = agent._compose(
        db, user_id=u.id, grade_id=g.id, subject_id=s.id, total_score=100,
        difficulty_ratio={"easy": 0.3, "medium": 0.5, "hard": 0.2},
        type_ratio={"single": 10, "blank": 0, "short": 0}, kp_ids=[])
    ids = {i["question_id"] for i in plan["items"]}
    check(private_q.id not in ids,
          f"他人私有题被过滤（{private_q.id} 未出现在 {len(ids)} 题中）")

    plan_own = agent._compose(
        db, user_id=other.id, grade_id=g.id, subject_id=s.id, total_score=100,
        difficulty_ratio={"easy": 0.3, "medium": 0.5, "hard": 0.2},
        type_ratio={"single": 10, "blank": 0, "short": 0}, kp_ids=[])
    own_ids = {i["question_id"] for i in plan_own["items"]}
    check(private_q.id in own_ids, "本人私有题仍可用（过滤不能过严）")

    # ---- 7) P1-11：知识点约束优先保留，放宽必须显式上报
    kp_a = app.models.KnowledgePoint(name="KP-A", level=3, grade_id=g.id,
                                     subject_id=s.id, code="VA")
    kp_b = app.models.KnowledgePoint(name="KP-B", level=3, grade_id=g.id,
                                     subject_id=s.id, code="VB")
    db.add_all([kp_a, kp_b])
    db.commit()
    db.refresh(kp_a)
    db.refresh(kp_b)
    # 把所有 single 题挂到 KP-A，然后只请求 KP-B（题库里没有）→ 必须先放宽难度、
    # 再放宽知识点，且把放宽行为写进 relaxations
    for q in db.query(Question).filter(Question.type == "single").all():
        q.knowledge_point_id = kp_a.id
    db.commit()
    plan_kp = agent._compose(
        db, user_id=u.id, grade_id=g.id, subject_id=s.id, total_score=100,
        difficulty_ratio={"easy": 0.3, "medium": 0.5, "hard": 0.2},
        type_ratio={"single": 6, "blank": 0, "short": 0}, kp_ids=[kp_b.id])
    check(bool(plan_kp["items"]), f"知识点无匹配时仍能出题（{len(plan_kp['items'])} 题）")
    check(bool(plan_kp.get("relaxations")),
          f"放宽已显式上报：{plan_kp.get('relaxations')}")

    # ---- 4) 直击 _ai_fill 的 paper=None 分支（旧实现 paper.id → AttributeError）
    try:
        fill = agent._ai_fill(
            db, user_id=u.id, request=None, grade_id=g.id, subject_id=s.id,
            plan={"items": []}, total_score=100, paper_name=None, save=False,
            difficulty_ratio={"easy": 0.3, "medium": 0.5, "hard": 0.2},
        )
        cnt = len((fill.get("paper") or {}).get("items") or [])
        check(True, f"_ai_fill(save=False) 不抛异常，补题 {cnt} 道（旧实现 AttributeError）")
    except Exception as exc:
        check(False, f"_ai_fill(save=False) 抛异常：{type(exc).__name__}: {exc}")

    db.close()
    print("\n=== " + ("全部通过" if not failures else f"失败 {len(failures)} 项") + " ===")
    sys.exit(1 if failures else 0)

if __name__ == "__main__":
    main()
