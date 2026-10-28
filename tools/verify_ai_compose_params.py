"""AI 组卷参数可信化验证（不依赖大模型、不起服务）。

用户反馈「管理员点 AI 一键组卷没反应」，实测最终报 400：
    学科「数学」不属于七年级，请重新选择

根因：提示词只写「subject_id: 学科ID」，模型看不到我们的主键空间，只能瞎猜。
实测它对七年级数学卷返回 `subject_id=2` —— 那是**一年级**数学的 id。
（`Grade.id` 恰好等于年级序号，所以年级蒙对了，学科必然错。）

修复后按「年级 + 学科名称」重新解析，id 只作线索。本脚本直接调用解析函数，
用「模型会给出的各种形态」逐一验证，锁死这个回归。

用法：python tools/verify_ai_compose_params.py
"""
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "backend"))

FAILED = []


def check(name, ok, detail=""):
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  {detail}" if detail and not ok else ""))
    if not ok:
        FAILED.append(name)
    return ok


def main():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from app.core.database import Base
    from app.models import Grade, Subject
    from app.api.v1.paper_compose import _resolve_ai_grade, _resolve_ai_subject

    tmp = tempfile.mkdtemp(prefix="aiparam_")
    engine = create_engine(f"sqlite:///{os.path.join(tmp, 'test.db')}")
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()

    # 复刻真实 id 分布：Grade.id == grade_num；学科 id 与年级无规律对应
    for num in range(1, 10):
        names = ["一年级", "二年级", "三年级", "四年级", "五年级",
                 "六年级", "七年级", "八年级", "九年级"]
        db.add(Grade(id=num, name=names[num - 1], grade_num=num,
                     stage="primary" if num <= 6 else "junior"))
    db.flush()
    # 一年级数学 id=2、七年级数学 id=34（与生产库一致的关键事实）
    db.add_all([
        Subject(id=2, name="数学", grade_id=1),
        Subject(id=34, name="数学", grade_id=7),
        Subject(id=35, name="语文", grade_id=7),
        Subject(id=40, name="物理", grade_id=8),
        Subject(id=51, name="数学", grade_id=9),
    ])
    db.commit()

    print("\n=== 1. 模型猜错 id（本轮真实故障）===")
    parsed = {"grade_id": 7, "subject_id": 2}     # 2 = 一年级数学
    g = _resolve_ai_grade(db, parsed, "出一份七年级数学期末试卷")
    s = _resolve_ai_subject(db, g, parsed, "出一份七年级数学期末试卷")
    check("年级解析为七年级", g is not None and g.grade_num == 7, str(g and g.name))
    check("学科解析为七年级数学（id=34），不是一年级数学（id=2）",
          s is not None and s.id == 34, str(s and (s.id, s.name, s.grade_id)))

    print("\n=== 2. 模型按新提示词只给名称 ===")
    parsed = {"grade_num": 7, "subject_name": "数学"}
    g = _resolve_ai_grade(db, parsed, "")
    s = _resolve_ai_subject(db, g, parsed, "")
    check("grade_num + subject_name 可正确落库记录",
          g is not None and g.grade_num == 7 and s is not None and s.id == 34)

    print("\n=== 3. 模型什么都没给，只能从需求文本推断 ===")
    g = _resolve_ai_grade(db, {}, "出一份初二物理单元测试卷")
    s = _resolve_ai_subject(db, g, {}, "出一份初二物理单元测试卷")
    check("「初二」识别为八年级", g is not None and g.grade_num == 8, str(g and g.name))
    check("文本中的学科「物理」被识别", s is not None and s.name == "物理", str(s and s.name))

    print("\n=== 4. 数字年级写法 ===")
    g = _resolve_ai_grade(db, {}, "7年级数学随堂练习")
    check("「7年级」识别为七年级", g is not None and g.grade_num == 7)

    print("\n=== 5. grade_id=0（模型表示不确定）时仍能兜住 ===")
    g = _resolve_ai_grade(db, {"grade_id": 0}, "九年级数学中考模拟")
    s = _resolve_ai_subject(db, g, {"grade_id": 0}, "九年级数学中考模拟")
    check("grade_id=0 不作为有效年级，回落到文本",
          g is not None and g.grade_num == 9, str(g and g.name))
    check("九年级数学解析正确（同名的九年级数学 id=51）",
          s is not None and s.id == 51, str(s and (s.id, s.grade_id)))

    print("\n=== 6. 真的识别不出来时必须返回 None（让上层报「请明确指定」）===")
    g = _resolve_ai_grade(db, {}, "出一份随堂练习")
    s = _resolve_ai_subject(db, g, {}, "出一份随堂练习")
    check("无年级信息返回 None", g is None, str(g and g.name))
    check("无学科信息返回 None", s is None, str(s and s.name))

    print("\n=== 7. 同名学科必须按年级区分（不可跨年级串用）===")
    g1 = _resolve_ai_grade(db, {"grade_num": 1}, "")
    s1 = _resolve_ai_subject(db, g1, {"subject_name": "数学"}, "")
    g9 = _resolve_ai_grade(db, {"grade_num": 9}, "")
    s9 = _resolve_ai_subject(db, g9, {"subject_name": "数学"}, "")
    check("一年级数学命中 id=2", s1 is not None and s1.id == 2, str(s1 and s1.id))
    check("九年级数学命中 id=51", s9 is not None and s9.id == 51, str(s9 and s9.id))
    check("两者不是同一条记录", s1 is not None and s9 is not None and s1.id != s9.id)

    print("\n" + "=" * 58)
    if FAILED:
        print(f"失败 {len(FAILED)} 项：")
        for f in FAILED:
            print("  -", f)
        return 1
    print("全部通过：AI 组卷参数按「年级+学科名」解析，不再信任模型给的 id")
    return 0


if __name__ == "__main__":
    sys.exit(main())
