"""知识点数据质量巡检：把"结构错乱"与"待复核内容"变成可执行清单。

## 为什么需要

`audit_knowledge_coverage.py` 只回答"哪些学科一条知识点都没有"。但覆盖率
100% 不等于数据可用 —— 生产库 1821 条里有 1498 条是 `source=ai`（模型生成、
未经教研复核），而且导入/历史数据可能留下结构问题：

| 问题 | 后果 |
|---|---|
| 同名节点出现在不同层级 | 树里看起来重复，掌握度统计各算一份，题目挂载歧义 |
| `level=2/3` 但 `parent_id` 为空 | 节点漂在根上，树接口里与单元并列，层级失去意义 |
| `path` 与实际父链不一致 | 按 path 做子树查询（掌握度、复习计划）会漏掉或多算 |
| 单元下没有任何子节点 | 它是"空壳"，AI 挂载考点时挂到单元上，粒度粗到无法分析 |
| 某学科知识点齐全但题目挂载率 0 | 出题没挂考点，等于覆盖率没转化成数据 |

这些都不会报错，只会让「掌握度图谱/复习计划」给出看起来正常但没意义的结果。

用法：
    python tools/audit_kp_quality.py                    # 巡检，打印汇总
    python tools/audit_kp_quality.py --csv kp_review.csv # 导出待复核清单
    python tools/audit_kp_quality.py --strict            # 有严重问题返回 1（CI 用）

退出码：0 = 正常（或非 strict 模式）；1 = strict 且存在严重问题。
"""
import argparse
import csv
import os
import sys
from collections import defaultdict

BACKEND = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
sys.path.insert(0, BACKEND)

from sqlalchemy import func, select  # noqa: E402

from app.core.database import SessionLocal  # noqa: E402
from app.models import Grade, KnowledgePoint, Question, Subject  # noqa: E402

SEVERITY = {"duplicate_name_level": "严重", "orphan_parent": "严重",
            "path_broken": "严重", "hollow_unit": "提示",
            "unmounted_subject": "提示", "ai_source": "待复核"}


def main() -> int:
    ap = argparse.ArgumentParser(description="知识点数据质量巡检")
    ap.add_argument("--csv", default="", help="把待复核清单导出到 CSV")
    ap.add_argument("--strict", action="store_true", help="存在严重问题时返回 1")
    ap.add_argument("--limit", type=int, default=8, help="每类问题最多展示 N 条")
    args = ap.parse_args()

    db = SessionLocal()
    try:
        grades = {g.id: g for g in db.scalars(select(Grade)).all()}
        subjects = {s.id: s for s in db.scalars(select(Subject)).all()}
        nodes = db.scalars(select(KnowledgePoint)).all()
        by_id = {n.id: n for n in nodes}

        # 每个学科的题目总数 / 已挂知识点数，用于"覆盖率是否转化成数据"
        mount = {
            int(sid): (int(total or 0), int(mounted or 0))
            for sid, total, mounted in db.execute(
                select(
                    Question.subject_id,
                    func.count(Question.id),
                    func.count(Question.knowledge_point_id),
                ).group_by(Question.subject_id)
            ).all()
        }

        issues = defaultdict(list)
        per_subject = defaultdict(list)
        for n in nodes:
            per_subject[(n.grade_id, n.subject_id)].append(n)

        # 1) 同名跨层
        for (_gid, _sid), group in per_subject.items():
            seen = {}
            for n in group:
                key = n.name.strip()
                prev = seen.get(key)
                if prev is not None and prev != n.level:
                    issues["duplicate_name_level"].append(
                        (n.grade_id, n.subject_id, f"「{n.name}」同时是 level{prev} 与 level{n.level}（id={n.id}）"))
                seen[key] = n.level

        # 2/3) 父级缺失、path 断裂
        for n in nodes:
            if n.level >= 2 and not n.parent_id:
                issues["orphan_parent"].append(
                    (n.grade_id, n.subject_id, f"「{n.name}」(id={n.id}) level={n.level} 但无父级"))
                continue
            if n.parent_id:
                parent = by_id.get(n.parent_id)
                if parent is None:
                    issues["orphan_parent"].append(
                        (n.grade_id, n.subject_id, f"「{n.name}」(id={n.id}) 的父级 {n.parent_id} 不存在"))
                    continue
                if parent.level != n.level - 1:
                    issues["orphan_parent"].append(
                        (n.grade_id, n.subject_id,
                         f"「{n.name}」(id={n.id}, level{n.level}) 的父级是 level{parent.level}"))
                expect = f"{parent.path or parent.id}/{n.id}"
                if n.path != expect:
                    issues["path_broken"].append(
                        (n.grade_id, n.subject_id,
                         f"「{n.name}」(id={n.id}) path={n.path!r} 期望 {expect!r}"))

        # 4) 空壳单元
        has_child = {n.parent_id for n in nodes if n.parent_id}
        for n in nodes:
            if n.level == 1 and n.id not in has_child:
                issues["hollow_unit"].append(
                    (n.grade_id, n.subject_id, f"单元「{n.name}」(id={n.id}) 下没有任何子节点"))

        # 5) 覆盖率未转化成数据：有知识点但题目一条都没挂
        for (gid, sid), group in per_subject.items():
            total, mounted = mount.get(int(sid), (0, 0))
            if total > 0 and mounted == 0:
                issues["unmounted_subject"].append(
                    (gid, sid, f"{total} 道题全部未挂知识点（覆盖率没转化成数据）"))

        ai_nodes = [n for n in nodes if (n.source or "") == "ai"]

        # ---------------------------------------------------------- 输出
        print("=" * 68)
        print("  知识点数据质量巡检")
        print("=" * 68)
        print(f"节点总数            : {len(nodes)}")
        print(f"年级学科组合        : {len(per_subject)}")
        src = defaultdict(int)
        for n in nodes:
            src[n.source or "(空)"] += 1
        print("来源分布            : " + "  ".join(f"{k}={v}" for k, v in sorted(src.items())))
        print()
        for key in ("duplicate_name_level", "orphan_parent", "path_broken",
                    "hollow_unit", "unmounted_subject"):
            rows = issues[key]
            flag = "✓" if not rows else "!"
            print(f"[{flag}] {key:<22} {SEVERITY[key]:<4} {len(rows):>4} 条")
            for gid, sid, text in rows[: args.limit]:
                print(f"      - {_label(grades, subjects, gid, sid)}  {text}")
            if len(rows) > args.limit:
                print(f"      … 其余 {len(rows) - args.limit} 条（--limit 调整）")
        print(f"[{'!' if ai_nodes else '✓'}] {'ai_source':<22} {'待复核':<4} {len(ai_nodes):>4} 条"
              "   （模型生成、未经教研确认）")

        if args.csv:
            with open(args.csv, "w", encoding="utf-8-sig", newline="") as fh:
                w = csv.writer(fh)
                w.writerow(["类型", "严重程度", "年级", "学科", "知识点id", "名称",
                            "层级", "来源", "说明"])
                for key, rows in issues.items():
                    for gid, sid, text in rows:
                        w.writerow([key, SEVERITY[key], _gname(grades, gid),
                                    _sname(subjects, sid), "", "", "", "", text])
                for n in ai_nodes:
                    w.writerow(["ai_source", "待复核", _gname(grades, n.grade_id),
                                _sname(subjects, n.subject_id), n.id, n.name,
                                n.level, n.source, "模型生成，需教研复核"])
            print(f"\n待复核清单已导出：{args.csv}")

        severe = sum(len(issues[k]) for k in
                     ("duplicate_name_level", "orphan_parent", "path_broken"))
        print(f"\n严重问题合计：{severe} 条")
        if args.strict and severe:
            return 1
        return 0
    finally:
        db.close()


def _gname(grades, gid):
    g = grades.get(gid)
    return g.name if g else f"#{gid}"


def _sname(subjects, sid):
    s = subjects.get(sid)
    return s.name if s else f"#{sid}"


def _label(grades, subjects, gid, sid):
    return f"{_gname(grades, gid)}/{_sname(subjects, sid)}"


if __name__ == "__main__":
    sys.exit(main())
