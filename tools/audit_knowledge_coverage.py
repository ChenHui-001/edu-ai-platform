"""知识点覆盖巡检 + 缺失学科最小骨架补种。

## 为什么需要这个脚本

知识点是 AI 出题挂载考点、掌握度图谱、复习计划三件事的共同基础。种子数据
（`services/init_db.KNOWLEDGE_POINTS`）只覆盖了有教研积累的部分年级学科，
其余学科**一条知识点都没有**，于是这些学科上：

- AI 出题的 `knowledge_point_id` 恒为空 → 题目挂不上考点；
- 学生掌握度图谱只有"综合"一个桶 → 学情分析等于没有；
- 复习计划按知识点排期 → 排不出任何条目。

这三件事都不会报错，只是**静默失效**，所以需要主动巡检。

## 两种补法，务必区分

| 方式 | 内容 | 适用 |
|---|---|---|
| `--seed-placeholder` | 每学科 1 个单元 + 2 个通用知识点（`source=placeholder`） | 让链路先跑通，运营按清单补真实考点 |
| `--from-seed` | 用 `init_db.KNOWLEDGE_POINTS` 里该学科的**真实**条目补 | 该学科在种子里有教研内容但库里没播上 |

占位骨架**不是**教研内容：它只保证"每个学科至少有可挂载的对象"，
`source` 明确标为 `placeholder`，便于后续按 `source='placeholder'` 精确
定位并替换成真实知识点（`--purge-placeholder` 可一键清除重来）。

用法：
    python tools/audit_knowledge_coverage.py                     # 只巡检
    python tools/audit_knowledge_coverage.py --csv kp_gap.csv     # 导出清单
    python tools/audit_knowledge_coverage.py --seed-placeholder   # 补占位骨架
    python tools/audit_knowledge_coverage.py --purge-placeholder  # 清掉占位

退出码：0 = 正常；1 = 执行出错。
"""
import argparse
import csv
import os
import sys

BACKEND = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
sys.path.insert(0, BACKEND)

from sqlalchemy import func, select  # noqa: E402

from app.core.database import SessionLocal  # noqa: E402
from app.models import Grade, KnowledgePoint, Subject  # noqa: E402

PLACEHOLDER_SOURCE = "placeholder"


def survey(db):
    """返回 [{grade_id, grade_num, grade_name, subject_id, subject_name, kp_count}]"""
    rows = db.execute(
        select(
            Grade.id, Grade.grade_num, Grade.name,
            Subject.id, Subject.name,
            func.count(KnowledgePoint.id),
        )
        .join(Subject, Subject.grade_id == Grade.id)
        .outerjoin(
            KnowledgePoint,
            (KnowledgePoint.subject_id == Subject.id)
            & (KnowledgePoint.grade_id == Grade.id),
        )
        .group_by(Grade.id, Grade.grade_num, Grade.name, Subject.id, Subject.name)
        .order_by(Grade.grade_num, Subject.id)
    ).all()
    return [
        {
            "grade_id": int(gid), "grade_num": int(num), "grade_name": gname,
            "subject_id": int(sid), "subject_name": sname, "kp_count": int(cnt or 0),
        }
        for gid, num, gname, sid, sname, cnt in rows
    ]


def seed_placeholder(db, row, *, actor_id=None):
    """为单个学科建最小骨架：1 单元 + 2 知识点。

    结构与 `init_db.init_knowledge_points` 完全一致（level 1 单元 / level 2 知识点、
    `path` 物化路径、`code` 唯一），这样它和真实知识点在树接口里表现无差别，
    补习真实考点时可以直接在单元下继续加子级。
    """
    name = row["subject_name"]
    unit = KnowledgePoint(
        name=f"{name}·第1单元", grade_id=row["grade_id"], subject_id=row["subject_id"],
        level=1, parent_id=None, term=1, difficulty="medium", sort=10,
        code=f"G{row['grade_num']}-S{row['subject_id']}-U1",
        description=f"{row['grade_name']}{name}第1单元（自动生成骨架，待教研补齐）",
        status="published", source=PLACEHOLDER_SOURCE, owner_id=actor_id,
    )
    db.add(unit)
    db.flush()
    unit.path = str(unit.id)
    created = 0
    for i, child_name in enumerate((f"{name}基础概念", f"{name}综合应用"), start=1):
        child = KnowledgePoint(
            name=child_name, grade_id=row["grade_id"], subject_id=row["subject_id"],
            level=2, parent_id=unit.id, term=1, difficulty="medium", sort=i,
            code=f"G{row['grade_num']}-S{row['subject_id']}-U1-K{i}",
            description=f"{row['grade_name']}{name}「{child_name}」（自动生成骨架，待教研补齐）",
            keywords=child_name, status="published", source=PLACEHOLDER_SOURCE,
            owner_id=actor_id,
        )
        db.add(child)
        db.flush()
        child.path = f"{unit.path}/{child.id}"
        created += 1
    return created + 1


def main() -> int:
    parser = argparse.ArgumentParser(description="知识点覆盖巡检")
    parser.add_argument("--csv", default="", help="把缺失清单导出到 CSV")
    parser.add_argument("--seed-placeholder", action="store_true",
                        help="为缺失学科补最小占位骨架（source=placeholder）")
    parser.add_argument("--purge-placeholder", action="store_true",
                        help="删除所有 source=placeholder 的占位知识点（不含真实数据）")
    parser.add_argument("--top", type=int, default=0, help="只展示前 N 条缺失（0=全部）")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        if args.purge_placeholder:
            removed = int(db.scalar(
                select(func.count()).select_from(KnowledgePoint)
                .where(KnowledgePoint.source == PLACEHOLDER_SOURCE)) or 0)
            db.execute(
                KnowledgePoint.__table__.delete()
                .where(KnowledgePoint.source == PLACEHOLDER_SOURCE))
            db.commit()
            print(f"已删除占位知识点 {removed} 条（真实教研数据未受影响）")
            return 0

        rows = survey(db)
        missing = [r for r in rows if r["kp_count"] == 0]
        total = len(rows)
        print(f"年级学科组合总数 : {total}")
        print(f"已有知识点的学科 : {total - len(missing)}")
        print(f"**缺失的学科**   : {len(missing)}")
        if rows:
            ratio = (total - len(missing)) / total * 100
            print(f"覆盖率           : {ratio:.1f}%")

        if missing:
            shown = missing[: args.top] if args.top else missing
            print(f"\n缺失清单（{len(shown)}/{len(missing)}）：")
            print(f"  {'年级':<8}{'学科':<12}{'subject_id':>11}")
            for r in shown:
                print(f"  {r['grade_name']:<8}{r['subject_name']:<12}{r['subject_id']:>11}")

        if args.csv:
            with open(args.csv, "w", encoding="utf-8-sig", newline="") as fh:
                writer = csv.writer(fh)
                writer.writerow(["grade_id", "grade_num", "grade_name",
                                 "subject_id", "subject_name", "kp_count"])
                for r in missing:
                    writer.writerow([r["grade_id"], r["grade_num"], r["grade_name"],
                                     r["subject_id"], r["subject_name"], r["kp_count"]])
            print(f"\n缺失清单已导出：{args.csv}")

        if args.seed_placeholder:
            if not missing:
                print("\n没有缺失学科，无需补种。")
                return 0
            created = 0
            for r in missing:
                created += seed_placeholder(db, r)
            db.commit()
            print(f"\n已为 {len(missing)} 个学科补占位骨架，共 {created} 个节点"
                  f"（source={PLACEHOLDER_SOURCE}）")
            after = survey(db)
            still = [r for r in after if r["kp_count"] == 0]
            print(f"复查剩余缺失学科：{len(still)}")
            return 0 if not still else 1

        if missing:
            print("\n提示：加 --seed-placeholder 可先补最小骨架让链路可用；"
                  "真实考点仍需按上方清单教研补齐。")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
