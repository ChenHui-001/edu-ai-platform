"""验证「编辑已被引用的试卷 → 学生作答不丢失 + 成绩重算」这条关键路径。

这是用户明确决策的 P0 场景：旧实现（question.py update_paper）直接
`DELETE FROM edu_paper_item`，而 Answer.paper_item_id 是 CASCADE，
实测一份卷 80 条作答、920 分全部归零。本脚本验证新路径确实保住了数据。

用法：python tools/verify_paper_rescore.py
"""
import json
import os
import sys
import tempfile

BACKEND = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
sys.path.insert(0, BACKEND)

DB_PATH = os.path.join(tempfile.gettempdir(), "verify_rescore.db")
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)
os.environ["DATABASE_URL"] = "sqlite:///" + DB_PATH.replace("\\", "/")

from sqlalchemy import select  # noqa: E402

from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.models import (  # noqa: E402
    Answer, Grade, Paper, PaperItem, Question, QuestionStatus, Submission, Subject,
    Task, TaskStatus, User,
)

FAILED = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"  {detail}" if detail else ""))
    if not ok:
        FAILED.append(name)


def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    grade = Grade(name="七年级", stage="junior", grade_num=7)
    db.add(grade)
    db.flush()
    subject = Subject(name="数学", grade_id=grade.id)
    db.add(subject)
    db.flush()
    teacher = User(username="t", password=hash_password("x"), real_name="教师",
                   identity="teacher", status="active")
    student = User(username="s", password=hash_password("x"), real_name="学生",
                   identity="student", status="active", grade_id=grade.id)
    db.add_all([teacher, student])
    db.flush()

    # 5 道题
    qs = []
    for i in range(5):
        q = Question(
            type="single", stem=f"题目{i + 1}", options=json.dumps([{"key": "A", "text": "A"}]),
            answer=json.dumps("A"), analysis="解析", score=10.0,
            difficulty="easy", grade_id=grade.id, subject_id=subject.id,
            knowledge_point_id=None, bank_type="public", owner_id=teacher.id,
            status=QuestionStatus.PUBLISHED.value,
        )
        db.add(q)
        qs.append(q)
    db.flush()

    paper = Paper(name="测试卷", grade_id=grade.id, subject_id=subject.id,
                  total_score=50, duration=60, creator_id=teacher.id, source="manual",
                  status="published")
    db.add(paper)
    db.flush()
    items = []
    for i, q in enumerate(qs, start=1):
        it = PaperItem(paper_id=paper.id, question_id=q.id, sort_order=i,
                       score=10.0, section_name="一、选择题", section_code="single",
                       section_sort=1)
        db.add(it)
        items.append(it)
    db.flush()

    task = Task(title="测试考试", type="exam", paper_id=paper.id,
                subject_id=subject.id, grade_id=grade.id, creator_id=teacher.id,
                status=TaskStatus.PUBLISHED.value, total_score=50, pass_score=30)
    db.add(task)
    db.flush()

    # 3 名学生各答 5 题，每题 10 分；学生1全对(50)，学生2对3题(30)，学生3对1题(10)
    subs = []
    for s_idx, correct_n in enumerate((5, 3, 1), start=1):
        st = User(username=f"s{s_idx}", password=hash_password("x"),
                  real_name=f"学生{s_idx}", identity="student", status="active",
                  grade_id=grade.id)
        db.add(st)
        db.flush()
        sub = Submission(task_id=task.id, student_id=st.id, status="auto_graded",
                         score=correct_n * 10)
        db.add(sub)
        db.flush()
        for i, it in enumerate(items):
            is_ok = i < correct_n
            db.add(Answer(
                submission_id=sub.id, paper_item_id=it.id, question_id=it.question_id,
                content=json.dumps("A"), is_correct=is_ok,
                score=10.0 if is_ok else 0.0, full_score=10.0, grader_type="auto",
            ))
        subs.append(sub)
    db.commit()

    total_before = db.scalar(select(__import__("sqlalchemy").func.count()).select_from(Answer))
    print(f"\n初始：作答 {total_before} 条，提交 3 份")
    print(f"  学生成绩：{[s.score for s in subs]}")

    # ---------------- 关键操作：改卷 ----------------
    # 删掉第 5 题，把第 1 题分值从 10 改成 20（总分变 20+10*3=50 保持整数好算）
    print("\n=== 执行：删除第5题 + 第1题分值 10→20 ===")
    from app.api.v1.paper_compose import _recalculate_after_change, _write_items

    new_items = [
        {"question_id": qs[0].id, "score": 20.0, "section_code": "single",
         "section_name": "一、选择题", "section_sort": 1, "score_override": True},
        {"question_id": qs[1].id, "score": 10.0, "section_code": "single",
         "section_name": "一、选择题", "section_sort": 1, "score_override": False},
        {"question_id": qs[2].id, "score": 10.0, "section_code": "single",
         "section_name": "一、选择题", "section_sort": 1, "score_override": False},
        {"question_id": qs[3].id, "score": 10.0, "section_code": "single",
         "section_name": "一、选择题", "section_sort": 1, "score_override": False},
    ]
    old_items = list(paper.items)  # noqa: F841  保留以便调试
    # 顺序必须与 update_items 一致：先写题项（含作答迁移），再重算分值
    write_stat = _write_items(db, paper, new_items)
    result = _recalculate_after_change(db, paper, new_items)
    db.commit()

    print(f"  写入统计：{write_stat}")
    print(f"  重算结果：{result}")

    # ---------------- 校验 ----------------
    print("\n=== 校验 ===")
    total_after = db.scalar(select(__import__("sqlalchemy").func.count()).select_from(Answer))
    # 保留题的 12 条作答必须还在；被移除的第 5 题那 3 条随题项级联删除（设计如此）
    check("保留题目的作答零丢失（12 条）", total_after == 12,
          f"{total_before} → {total_after}")
    check("被移除题目的作答已作废且如实上报（3 条）",
          write_stat.get("dropped") == 3, f"dropped={write_stat.get('dropped')}")
    check("保住的作答数与迁移数一致", write_stat.get("migrated") == 12,
          f"migrated={write_stat.get('migrated')}")

    # 学生1 原是全对 50 分；改卷后：题1得20 + 题2-4各10 = 50
    db.expire_all()
    s1 = db.get(Submission, subs[0].id)
    check("学生1（全对）成绩按新分值重算=50", abs(float(s1.score or 0) - 50) < 0.01,
          f"实际 {s1.score}")

    s2 = db.get(Submission, subs[1].id)
    # 学生2 原对 3 题（题1,2,3）：题1=20 + 题2,3各10 = 40
    check("学生2（对3题）成绩重算=40", abs(float(s2.score or 0) - 40) < 0.01,
          f"实际 {s2.score}")

    s3 = db.get(Submission, subs[2].id)
    # 学生3 原对 1 题（题1）：题1=20 → 20
    check("学生3（对1题）成绩重算=20", abs(float(s3.score or 0) - 20) < 0.01,
          f"实际 {s3.score}")

    # 被删的第5题的作答：随题项级联删除，不得留下"无对应题目的得分行"
    ans5 = db.scalars(select(Answer).where(Answer.question_id == qs[4].id)).all()
    check("被删题目的作答不留残影（避免成绩单出现无题目得分行）", len(ans5) == 0,
          f"{len(ans5)} 条")

    # 及格判定
    db.expire_all()
    check("及格标记随新总分更新", s1.is_passed is not None, f"s1.is_passed={s1.is_passed}")

    # 卷面总分
    db.refresh(paper)
    check("卷面总分=50", abs(float(paper.total_score) - 50) < 0.01, str(paper.total_score))

    # 题项数量
    cnt = db.scalar(select(__import__("sqlalchemy").func.count()).select_from(PaperItem)
                    .where(PaperItem.paper_id == paper.id))
    check("题项数变为 4", cnt == 4, str(cnt))

    db.close()
    print("\n" + "=" * 58)
    if FAILED:
        print(f"失败 {len(FAILED)} 项：{FAILED}")
        return 1
    print("全部通过：学生作答零丢失，成绩按新分值正确重算")
    return 0


if __name__ == "__main__":
    sys.exit(main())
