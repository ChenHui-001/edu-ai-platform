"""知识点 level3 播种验证：隔离临时库，验证数量、幂等、父子关系、可命题。

关注三件事，任何一件不成立，level3 就等于白补：
  1. 真的建出来了（数量 > 0，且都挂在 level2 下）
  2. 重跑不产生重复（幂等）
  3. path 正确、能按 level3 叶子筛题（组卷/AI 出题依赖这一点）

用法：python tools/verify_kp_level3.py
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
    from sqlalchemy import create_engine, func, select
    from sqlalchemy.orm import sessionmaker

    from app.models import Base, KnowledgePoint, Subject
    from app.services.init_db import init_grades_subjects, init_knowledge_points
    from app.services.knowledge_level3_seed import (
        LEVEL3_POINTS, seed_knowledge_level3,
    )

    tmpdir = tempfile.mkdtemp(prefix="kp_l3_")
    db_path = os.path.join(tmpdir, "test.db")
    engine = create_engine(f"sqlite:///{db_path}",
                           connect_args={"check_same_thread": False})
    with engine.connect() as conn:
        conn.exec_driver_sql("PRAGMA foreign_keys=ON")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        print("\n=== 1. 建基础数据（年级/学科/level1-2）===")
        init_grades_subjects(db)
        init_knowledge_points(db)
        l1 = db.scalar(select(func.count()).select_from(KnowledgePoint)
                       .where(KnowledgePoint.level == 1)) or 0
        l2 = db.scalar(select(func.count()).select_from(KnowledgePoint)
                       .where(KnowledgePoint.level == 2)) or 0
        l3 = db.scalar(select(func.count()).select_from(KnowledgePoint)
                       .where(KnowledgePoint.level == 3)) or 0
        check("level1 已建", l1 > 0, f"{l1}")
        check("level2 已建", l2 > 0, f"{l2}")
        check("播种前 level3 = 0", l3 == 0, f"{l3}")

        print("\n=== 2. 首次播种 level3 ===")
        stat = seed_knowledge_level3(db)
        print(f"  {stat}")
        l3 = db.scalar(select(func.count()).select_from(KnowledgePoint)
                       .where(KnowledgePoint.level == 3)) or 0
        check("level3 已建出", l3 > 0, str(stat))
        check("新增数与统计一致", stat["created"] == l3, f"{stat['created']} vs {l3}")
        check("父级缺失为 0（种子章节全部命中）", stat["missing"] == 0, str(stat))

        expect = sum(len(pts) for g in LEVEL3_POINTS.values()
                     for ch in g.values() for pts in ch.values())
        check(f"level3 数量等于种子声明（{expect}）", l3 == expect, f"{l3} vs {expect}")

        print("\n=== 3. 父级与 path 正确性 ===")
        leaf = db.scalars(select(KnowledgePoint)
                          .where(KnowledgePoint.level == 3).limit(1)).first()
        check("level3 有 parent_id", leaf is not None and leaf.parent_id is not None)
        parent = db.get(KnowledgePoint, leaf.parent_id)
        check("父节点是 level2 章节", parent is not None and parent.level == 2,
              f"level={parent.level if parent else None}")
        check("path 以父 path 为前缀",
              bool(leaf.path and parent.path and leaf.path.startswith(parent.path + "/")),
              f"{leaf.path} vs {parent.path}")
        check("code 带 L3 标识", "-L3-" in (leaf.code or ""), str(leaf.code))
        check("同名同父不重复",
              (db.scalar(select(func.count()).select_from(KnowledgePoint).where(
                  KnowledgePoint.parent_id == parent.id,
                  KnowledgePoint.name == leaf.name)) or 0) == 1)

        print("\n=== 4. 幂等：重跑不新增 ===")
        stat2 = seed_knowledge_level3(db)
        print(f"  {stat2}")
        l3_again = db.scalar(select(func.count()).select_from(KnowledgePoint)
                             .where(KnowledgePoint.level == 3)) or 0
        check("重跑 created=0", stat2["created"] == 0, str(stat2))
        check("重跑 skipped=首次数量", stat2["skipped"] == l3, f"{stat2['skipped']} vs {l3}")
        check("level3 总数不变", l3_again == l3, f"{l3} -> {l3_again}")

        print("\n=== 5. 叶子可用于筛题（组卷/AI 出题依赖）===")
        # 按学科取一层叶子，确认 level=3 能被直接筛出来（不再恒空）
        subj = db.scalars(select(Subject).where(Subject.name == "数学").limit(1)).first()
        leaves = db.scalars(
            select(KnowledgePoint).where(
                KnowledgePoint.subject_id == subj.id,
                KnowledgePoint.level == 3,
                KnowledgePoint.is_active.is_(True),
            ).limit(5)).all()
        check("按学科可筛出 level3 叶子", len(leaves) > 0, str(len(leaves)))
        check("叶子都带年级", all(x.grade_id for x in leaves))
        check("叶子都有难度标注", all(x.difficulty in ("easy", "medium", "hard")
                                for x in leaves),
              str([x.difficulty for x in leaves]))

        print("\n=== 6. 覆盖度：种子声明的章节是否全部覆盖 ===")
        covered = db.scalar(select(func.count(func.distinct(KnowledgePoint.parent_id)))
                            .where(KnowledgePoint.level == 3)) or 0
        total_ch = sum(len(ch) for g in LEVEL3_POINTS.values() for ch in g.values())
        check(f"覆盖全部 {total_ch} 个章节", covered == total_ch, f"{covered}")

        print("\n" + "=" * 58)
        if FAILED:
            print(f"失败 {len(FAILED)} 项：{FAILED}")
            return 1
        print(f"全部通过：level3 共 {l3} 个考点，覆盖 {covered} 个章节，幂等可重跑")
        return 0
    finally:
        db.close()
        engine.dispose()
        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
