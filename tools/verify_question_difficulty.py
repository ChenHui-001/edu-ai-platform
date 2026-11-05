"""出题 Agent 的「难度不可信」验证（不依赖大模型、不起服务）。

2026-11-04 生产实测：补 198 道题，**全部是 easy**，尽管调用方按学科比例
轮转了 easy/medium/hard 并逐次传进提示词。直接原因有两层：

1. 提示词里的 `"difficulty": "medium"` 位于**输出格式示例**中，模型把它当成
   "模板值"照抄，无视下面那句「难度要求：困难」。
2. 代码里 `difficulty=it.get("difficulty", difficulty)` —— 模型给了值就用模型的，
   只有模型**不给**时才用调用方要求。等于把决定权交给了不可信的模型输出。

修复后：难度一律以**调用方要求**为准，模型自报仅作为未指定时的补充。
这与重生接口的「难度不符一律不采纳」是同一条口径。

本脚本让假 LLM 返回「难度一律写 easy」的合法 JSON，走**真实的**
`QuestionGeneratorAgent.execute`（含解析、知识点校验、落库），
检查最终落库的 difficulty 是调用方要求的那个值。

用法：python tools/verify_question_difficulty.py
"""
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "backend"))

FAILED = []


def check(name, ok, detail=""):
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  -> {detail}" if detail else ""))
    if not ok:
        FAILED.append(name)
    return ok


# 假模型返回的合法 JSON 正文：难度一律写 easy（复刻生产行为）
def fake_payload(n, tag):
    items = []
    for i in range(n):
        items.append({
            "type": "single",
            "stem": f"[{tag}] 难度可信性验证题 {i}",
            "options": [{"key": k, "text": t}
                        for k, t in zip("ABCD", ("甲", "乙", "丙", "丁"))],
            "answer": "A",
            "analysis": "验证用解析",
            "difficulty": "easy",      # ← 模型自报，必须被忽略
            "score": 3,
            "knowledge_point_id": 0,
            "knowledge_point_name": "",
            "answer_min_words": 0,
        })
    import json
    return json.dumps(items, ensure_ascii=False)


def main() -> int:
    import app.agents.llm as llm_mod
    from sqlalchemy import create_engine, select
    from sqlalchemy.orm import sessionmaker

    from app.core.database import Base
    from app.core.security import hash_password
    from app.models import Grade, Question, Subject, User
    from app.agents.question_agent import QuestionGeneratorAgent

    tmp = tempfile.mkdtemp(prefix="qdiff_")
    engine = create_engine(f"sqlite:///{os.path.join(tmp, 'q.db')}")
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()

    grade = Grade(name="七年级", stage="junior", grade_num=7)
    db.add(grade)
    db.flush()
    subject = Subject(name="数学", grade_id=grade.id)
    db.add(subject)
    db.flush()
    teacher = User(username="t_diff", password=hash_password("x"),
                   real_name="难度验证教师", identity="teacher",
                   status="active", grade_id=grade.id)
    db.add(teacher)
    db.commit()

    print("\n=== 出题难度以调用方要求为准（不信模型自报）===")
    print("  假模型返回的每道题都写 difficulty=easy，看落库是否被纠正\n")

    orig_chat = llm_mod.LLMClient.chat

    for asked, label in (("hard", "困难"), ("medium", "中等"), ("easy", "简单")):
        tag = f"ask-{asked}"

        def fake_chat(self, system_prompt, user_prompt, **kw):
            # 注意：chat 是 LLMClient 的实例方法，签名是
            #   chat(self, system_prompt, user_prompt, *, user_id=..., ...)
            # patch 必须挂在类上（base.call_llm 走的是模块级单例 llm_client）。
            return {"success": True, "content": fake_payload(3, tag),
                    "empty": False,
                    "usage": {"input_tokens": 10, "output_tokens": 100}}

        llm_mod.LLMClient.chat = fake_chat
        try:
            res = QuestionGeneratorAgent().run(
                db, user_id=teacher.id, grade_id=grade.id, subject_id=subject.id,
                question_type="single", count=3, difficulty=asked, save=True,
                source="ai_test")
        finally:
            llm_mod.LLMClient.chat = orig_chat

        rows = db.scalars(select(Question).where(Question.source == "ai_test")
                          .order_by(Question.id.desc())).all()
        mine = [q for q in rows if q.stem.startswith(f"[{tag}]")]
        if not mine:
            check(f"要求 {label}({asked}) 时有题目落库", False,
                  f"res={str(res)[:160]}")
            continue
        diffs = {q.difficulty for q in mine}
        check(f"要求 {label}({asked}) → 落库难度为 {asked}",
              diffs == {asked}, f"实际 {diffs}（模型自报 easy）")

    # 汇总：三档都在库里，说明难度确实可区分，而不是全被压成同一个值
    all_rows = db.scalars(select(Question).where(Question.source == "ai_test")).all()
    all_diffs = {q.difficulty for q in all_rows}
    check("三轮不同要求产出三种难度（难度真的可区分）",
          all_diffs == {"easy", "medium", "hard"}, str(sorted(all_diffs)))

    print("\n" + "=" * 58)
    if FAILED:
        print(f"失败 {len(FAILED)} 项：")
        for f in FAILED:
            print("  -", f)
        return 1
    print("全部通过：难度以调用方要求为准，模型自报不再覆盖")
    return 0


if __name__ == "__main__":
    sys.exit(main())
