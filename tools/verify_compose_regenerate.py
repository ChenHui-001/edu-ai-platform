"""验证「保存前重新生成」接口：单题 / 整大题 / 不重复 / 难度题型精确 / 编辑不丢。

## 为什么不用真实模型

要验证的是**编排正确性**（换对了行、没覆盖别的题、难度/题型没漂、卷内不重复），
不是模型出题质量。注入假 Agent 才能把每个断言变成确定的数字；真实模型每次
结果不同，断言只能写"大概"。

用法：python tools/verify_compose_regenerate.py
退出码 0 = 全部通过。
"""
import os
import sys
import tempfile

BACKEND = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
sys.path.insert(0, BACKEND)

DB_PATH = os.path.join(tempfile.gettempdir(), "verify_regen.db")
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)
os.environ["DATABASE_URL"] = "sqlite:///" + DB_PATH.replace("\\", "/")
os.environ["LLM_ENABLED"] = "false"
os.environ["SCHEDULER_ENABLED"] = "false"
os.environ["SECRET_KEY"] = "ai-fill-parallel-test-key-0123456789"

import app.agents.question_agent as qa_mod  # noqa: E402
from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.models import Grade, KnowledgePoint, Question, Subject, User  # noqa: E402
from app.api.v1 import paper_compose as pc  # noqa: E402
from app.schemas.legacy_bodies import ComposeRegenerateIn  # noqa: E402


def _regen(payload, **kw):
    """把 dict 包成请求模型再调端点。

    走 HTTP 时 FastAPI 负责这层转换；直调函数必须自己包 ——
    否则端点第一行 `body.model_dump()` 直接 AttributeError。
    """
    return pc.compose_regenerate(ComposeRegenerateIn(**payload), **kw)


FAILED = []
CALLS = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"  -> {detail}" if detail else ""))
    if not ok:
        FAILED.append(name)


def seed(db):
    grade = Grade(name="七年级", stage="junior", grade_num=7)
    db.add(grade)
    db.flush()
    subject = Subject(name="数学", grade_id=grade.id, textbook_version="人教版")
    db.add(subject)
    db.flush()
    teacher = User(username="t_regen", password=hash_password("x"),
                   real_name="重生测试教师", identity="teacher", status="active",
                   grade_id=grade.id)
    db.add(teacher)
    db.flush()
    # 知识点必须真实存在：Question.knowledge_point_id 是非空外键，
    # 测试里用假 id 会直接撞 FK 约束，把"编排错误"伪装成"生成失败"。
    for kid, name in ((1659, "三边关系"), (1660, "内角和"), (1667, "全等判定")):
        db.add(KnowledgePoint(id=kid, name=name, grade_id=grade.id,
                              subject_id=subject.id, level=1, is_active=True))
    db.commit()
    return grade, subject, teacher


def install_fake_agent(*, ignore_difficulty=False, ignore_type=False, empty_until=0):
    """假出题器：每次按请求的题型/难度真落一批 draft 题，并返回其 id。

    - ignore_difficulty=True：故意返回难度不对的题（模拟模型不听话）
    - ignore_type=True：故意返回别题型（模拟 fallback 混题型）
    - empty_until=N：前 N 次调用返回空正文（模拟推理吃光预算）
    """
    state = {"run": 0, "seq": 0}

    def fake_run(self, db, user_id=None, grade_id=None, subject_id=None,
                 question_type="single", count=1, difficulty="medium",
                 knowledge_point_ids=None, save=False, source="ai", **kwargs):
        state["run"] += 1
        CALLS.append({
            "type": question_type, "count": count, "difficulty": difficulty,
            "kp_ids": list(knowledge_point_ids or []), "source": source,
        })
        if state["run"] <= empty_until:
            return {"success": True, "data": {
                "questions": [],
                "reason": "响应正文为空，通常是 max_tokens 预算被推理 token 耗尽",
            }}
        out_type = "blank" if ignore_type else question_type
        out_diff = "hard" if (ignore_difficulty and difficulty != "hard") else difficulty
        saved = []
        for _ in range(count):
            state["seq"] += 1
            q = Question(
                type=out_type,
                stem=f"【重生题#{state['seq']}】{question_type}/{difficulty} 第 {state['seq']} 道",
                score=5, difficulty=out_diff, grade_id=grade_id,
                subject_id=subject_id,
                knowledge_point_id=(knowledge_point_ids or [None])[0],
                bank_type="private", owner_id=user_id, status="draft",
                options='[{"key":"A","text":"甲"},{"key":"B","text":"乙"}]',
                answer="A", analysis="验证用解析", source=source,
            )
            db.add(q)
            saved.append(q)
        db.commit()
        return {"success": True, "data": {"questions": [
            {"id": q.id, "stem": q.stem, "type": q.type, "difficulty": q.difficulty}
            for q in saved
        ], "saved": len(saved)}}

    qa_mod.QuestionGeneratorAgent.run = fake_run
    return state


ITEMS = [
    # 一、单选题 3 道（easy / medium / hard 各一）
    {"question_id": 9001, "type": "single", "stem": "原单选1", "difficulty": "easy",
     "score": 3, "section_code": "single", "section_name": "一、单项选择题",
     "section_sort": 1, "section_pos": 0, "knowledge_point_id": 1659,
     "knowledge_point_name": "三边关系", "answer": "A", "analysis": "原解析"},
    {"question_id": 9002, "type": "single", "stem": "原单选2", "difficulty": "medium",
     "score": 3, "section_code": "single", "section_name": "一、单项选择题",
     "section_sort": 1, "section_pos": 1, "knowledge_point_id": 1659,
     "knowledge_point_name": "三边关系"},
    {"question_id": 9003, "type": "single", "stem": "原单选3", "difficulty": "hard",
     "score": 3, "section_code": "single", "section_name": "一、单项选择题",
     "section_sort": 1, "section_pos": 2, "knowledge_point_id": 1660,
     "knowledge_point_name": "内角和"},
    # 三、解答题 2 道（阶梯分值 6 / 8）
    {"question_id": 9101, "type": "calc", "stem": "原解答1（教师已改过）",
     "difficulty": "medium", "score": 6, "section_code": "calc",
     "section_name": "三、解答题", "section_sort": 3, "section_pos": 0,
     "knowledge_point_id": 1667, "knowledge_point_name": "全等判定",
     "answer": "教师手改答案", "analysis": "教师手改解析"},
    {"question_id": 9102, "type": "calc", "stem": "原解答2", "difficulty": "hard",
     "score": 8, "section_code": "calc", "section_name": "三、解答题",
     "section_sort": 3, "section_pos": 1, "knowledge_point_id": 1667,
     "knowledge_point_name": "全等判定"},
]


def build_payload(db, grade, subject, **kw):
    return {"grade_id": grade.id, "subject_id": subject.id,
            "items": [dict(i) for i in ITEMS], **kw}


def main() -> int:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        grade, subject, teacher = seed(db)
        print("\n=== 保存前重新生成验证 ===")

        # ---- 1. 单题重生：只换那一行，其余原样 ----
        install_fake_agent()
        CALLS.clear()
        # index=3 = 第 4 题 = 9101（教师手改过题干/答案/解析、分值 6、槽位 0）
        payload = build_payload(db, grade, subject, mode="item", index=3)
        # 直调函数要自己包成模型：走 HTTP 时 FastAPI 会做这层转换，
        # 传 dict 进来端点第一行 body.model_dump() 就 AttributeError
        res = _regen(payload, db=db, user=teacher)
        data = res["data"]
        items = data["items"]
        check("单题重生 replaced=1", data["replaced"] == 1, str(data["replaced"]))
        check("被替换行换了 question_id", items[3]["question_id"] != 9101,
              str(items[3]["question_id"]))
        check("被替换行保留原分值 6 分（阶梯分值不能重算）",
              items[3]["score"] == 6, str(items[3]["score"]))
        check("被替换行保留原槽位 section_pos=0",
              items[3]["section_pos"] == 0, str(items[3]["section_pos"]))
        check("被替换行保留原大题归属",
              items[3]["section_code"] == "calc" and items[3]["section_name"] == "三、解答题",
              f"{items[3]['section_code']}/{items[3]['section_name']}")
        check("其余 4 题完全没动（含另一道解答题 9102）",
              [i["question_id"] for i in items if i["question_id"] != items[3]["question_id"]]
              == [9001, 9002, 9003, 9102],
              str([i["question_id"] for i in items]))
        check("难度沿用原题 medium（不是默认值兜底）",
              items[3]["difficulty"] == "medium", str(items[3]["difficulty"]))
        check("调用参数带原知识点 id=1667",
              CALLS and CALLS[0]["kp_ids"] == [1667], str(CALLS[:1]))
        check("调用参数题型=calc", CALLS and CALLS[0]["type"] == "calc", str(CALLS[:1]))
        check("来源标记 ai_regen（与组卷补题 ai_fill 分开，便于清理）",
              CALLS and CALLS[0]["source"] == "ai_regen", str(CALLS[:1]))

        # ---- 2. 整大题重生：按难度分组，数量对齐 ----
        install_fake_agent()
        CALLS.clear()
        payload = build_payload(db, grade, subject, mode="section", section_code="single")
        res = _regen(payload, db=db, user=teacher)
        data = res["data"]
        items = data["items"]
        singles = [i for i in items if i["section_code"] == "single"]
        check("整段重生 replaced=3", data["replaced"] == 3, str(data["replaced"]))
        check("单选大题 3 道题全部换新",
              all(i["question_id"] not in (9001, 9002, 9003) for i in singles),
              str([i["question_id"] for i in singles]))
        check("按难度分组调用（3 次，easy/medium/hard 各一）",
              len(CALLS) == 3 and {c["difficulty"] for c in CALLS} == {"easy", "medium", "hard"},
              str([(c["type"], c["difficulty"]) for c in CALLS]))
        check("空前缀的解答题完全没被碰",
              [i["question_id"] for i in items if i["section_code"] == "calc"]
              == [9101, 9102],
              str([i["question_id"] for i in items if i["section_code"] == "calc"]))
        check("卷内 question_id 无重复",
              len({i["question_id"] for i in items}) == len(items),
              str([i["question_id"] for i in items]))
        check("难度分布与替换前一致（3 easy/medium/hard 各 1）",
              sorted(i["difficulty"] for i in singles) == ["easy", "hard", "medium"],
              str(sorted(i["difficulty"] for i in singles)))
        check("题型没串（单选大题里不出现填空）",
              all(i["type"] == "single" for i in singles),
              str([i["type"] for i in singles]))

        # ---- 3. 禁止复用旧题：换出来的 id 不能等于原题 ----
        check("新题 id 与旧题无交集（重生不是原地返回同一道）",
              not ({i["question_id"] for i in singles} & {9001, 9002, 9003}),
              str([i["question_id"] for i in singles]))

        # ---- 4. 模型难度不听话：宁可不换也不降级 ----
        install_fake_agent(ignore_difficulty=True)
        CALLS.clear()
        before = _regen(
            build_payload(db, grade, subject, mode="item", index=0),
            db=db, user=teacher)["data"]
        # 全部返回 hard，而原题是 easy → 一道都不该被采纳
        check("难度不符的题一个都不采纳（replaced=0）",
              before["replaced"] == 0, str(before["replaced"]))
        check("原题完整保留（不做降级替换）",
              before["items"][0]["question_id"] == 9001,
              str(before["items"][0]["question_id"]))
        check("失败项如实上报 pending",
              len(before["pending"]) == 1 and before["pending"][0]["index"] == 0,
              str(before["pending"]))
        check("失败原因可读（含难度要求）",
              "困难" in str(before["pending"][0]["reason"])
              or "符合" in str(before["pending"][0]["reason"]),
              str(before["pending"][0]["reason"]))
        check("难度不符时会多试几轮（不只看一次就放弃）",
              len(CALLS) >= 2, str(len(CALLS)))

        # ---- 5. 模型混题型：过滤掉 ----
        install_fake_agent(ignore_type=True)
        CALLS.clear()
        r5 = _regen(
            build_payload(db, grade, subject, mode="item", index=1),
            db=db, user=teacher)["data"]
        check("题型不符的题被过滤（replaced=0）", r5["replaced"] == 0, str(r5["replaced"]))
        check("原题保留", r5["items"][1]["question_id"] == 9002,
              str(r5["items"][1]["question_id"]))

        # ---- 6. 空正文（预算被推理吃光）：批次减半且如实报错 ----
        # 必须用"同题型同难度且题量 > 单批上限"的场景：难度混排会被拆成多个
        # need=1 的组，每批本来就是 1 道，减半无从体现。
        install_fake_agent(empty_until=99)
        CALLS.clear()
        flat = {"grade_id": grade.id, "subject_id": subject.id, "mode": "section",
                "section_code": "calc",
                "items": [dict(ITEMS[3], question_id=9200 + n, difficulty="medium",
                               section_pos=n) for n in range(4)]}
        r6 = _regen(flat, db=db, user=teacher)["data"]
        check("空正文时一道也不采纳", r6["replaced"] == 0, str(r6["replaced"]))
        check("空正文原因翻译成中文可读",
              "预算" in str(r6["pending"][0]["reason"]),
              str(r6["pending"][0]["reason"]))
        check("空正文后批次减半（首轮 3 → 次轮 ≤1）",
              len(CALLS) >= 2 and CALLS[1]["count"] < CALLS[0]["count"],
              str([(c["type"], c["count"]) for c in CALLS]))

        # ---- 7. 参数校验 ----
        for bad, label in (
            (build_payload(db, grade, subject, mode="item", index=99), "index 越界"),
            (build_payload(db, grade, subject, mode="section", section_code="judge"),
             "大题不存在"),
            (build_payload(db, grade, subject, mode="xxx"), "mode 非法"),
            ({"grade_id": grade.id, "subject_id": subject.id, "mode": "item",
              "index": 0, "items": []}, "items 为空"),
        ):
            try:
                _regen(bad, db=db, user=teacher)
                check(f"{label} 应被拒绝", False, "未抛异常")
            except Exception as exc:  # noqa: BLE001
                check(f"{label} 被拒绝且提示可读",
                      len(str(exc)) > 4, str(exc)[:70])

        print("\n" + "=" * 60)
        if FAILED:
            print(f"失败 {len(FAILED)} 项：")
            for f in FAILED:
                print("  -", f)
            return 1
        print("全部通过")
        return 0
    finally:
        db.close()
        try:
            os.remove(DB_PATH)
        except OSError:
            pass


if __name__ == "__main__":
    sys.exit(main())
