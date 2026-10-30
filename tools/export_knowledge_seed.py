"""把库里的知识点导出成可跨环境导入的 JSON 种子。

## 解决什么问题

`init_db.KNOWLEDGE_POINTS` 只覆盖 17/59 个「年级×学科」（有教研积累的那部分），
其余 42 个学科在**干净库部署**后一条知识点都没有：AI 出题挂不上考点、掌握度
图谱只有"综合"一个桶、复习计划排不出条目，而且全程不报错。

生产库是 59/59 覆盖的（早前用 AI 补过），但这些数据只存在于那一台机器的 SQLite
里，新环境（CI e2e、灾备重建、新校区实例）拿不到。本脚本把当前库的知识点树
导成 JSON，配合 `audit_knowledge_coverage.py --import-json` 就能一键对齐。

## 为什么不直接写进代码种子

导出的内容 `source` 可能是 `ai`（未经教研复核）。写进 `init_db` 等于把"待复核
的初稿"固化成"出厂数据"，以后没人分得清哪些是人工教研、哪些是模型生成。
JSON 里**保留原始 source**，导入方按需决定是否采用，边界清楚。

用法：
    python tools/export_knowledge_seed.py                     # 导出全部
    python tools/export_knowledge_seed.py --grade 7 --subject 数学
    python tools/export_knowledge_seed.py -o kp_seed.json

输出结构：
    {
      "exported_at": "2026-10-30T14:00:00",
      "counts": {"subjects": 59, "nodes": 1821},
      "subjects": [
        {"grade_num": 7, "grade_name": "七年级", "subject_name": "数学",
         "nodes": [{"name","level","code","term","difficulty","keywords",
                    "description","source","children":[...]}]}
      ]
    }
"""
import argparse
import json
import os
import sys
from collections import defaultdict
from datetime import datetime

BACKEND = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
sys.path.insert(0, BACKEND)

from sqlalchemy import select  # noqa: E402

from app.core.database import SessionLocal  # noqa: E402
from app.models import Grade, KnowledgePoint, Subject  # noqa: E402
from app.utils.common import now_local  # noqa: E402

FIELDS = ("name", "level", "code", "term", "difficulty",
          "keywords", "description", "source", "sort")


def node_payload(kp, children_map):
    data = {f: getattr(kp, f) for f in FIELDS}
    kids = children_map.get(kp.id, [])
    data["children"] = [node_payload(c, children_map) for c in kids]
    return data


def main() -> int:
    ap = argparse.ArgumentParser(description="导出知识点种子 JSON")
    ap.add_argument("--grade", type=int, default=0, help="只导某一年级（按 grade_num）")
    ap.add_argument("--subject", default="", help="只导某个学科（按名称）")
    ap.add_argument("-o", "--out", default="", help="输出文件（默认 data/kp_seed_<时间>.json）")
    args = ap.parse_args()

    db = SessionLocal()
    try:
        grades = {g.id: g for g in db.scalars(select(Grade)).all()}
        subjects = {s.id: s for s in db.scalars(select(Subject)).all()}
        rows = db.scalars(
            select(KnowledgePoint).order_by(
                KnowledgePoint.grade_id, KnowledgePoint.subject_id,
                KnowledgePoint.level, KnowledgePoint.sort, KnowledgePoint.id)
        ).all()

        if args.grade:
            rows = [r for r in rows if grades.get(r.grade_id)
                    and grades[r.grade_id].grade_num == args.grade]
        if args.subject:
            rows = [r for r in rows if subjects.get(r.subject_id)
                    and subjects[r.subject_id].name == args.subject]

        children_map = defaultdict(list)
        roots = defaultdict(list)   # (grade_id, subject_id) → 根节点
        ids = {r.id for r in rows}
        for r in rows:
            # 父级不在本次导出范围内时，该节点升级为根（保证导出是完整树，
            # 不会出现"子节点有、父节点缺"的悬空引用）
            if r.parent_id and r.parent_id in ids:
                children_map[r.parent_id].append(r)
            else:
                roots[(r.grade_id, r.subject_id)].append(r)

        subjects_out = []
        total_nodes = 0
        for (gid, sid), nodes in sorted(roots.items(), key=lambda kv: (kv[0][0], kv[0][1])):
            g, s = grades.get(gid), subjects.get(sid)
            if not g or not s:
                continue
            payload_nodes = [node_payload(n, children_map) for n in nodes]
            total_nodes += sum(_count(n) for n in payload_nodes)
            subjects_out.append({
                "grade_num": g.grade_num, "grade_name": g.name,
                "subject_name": s.name, "nodes": payload_nodes,
            })

        out = {
            "exported_at": now_local().isoformat(timespec="seconds"),
            "counts": {"subjects": len(subjects_out), "nodes": total_nodes},
            "subjects": subjects_out,
        }

        path = args.out or os.path.join(
            "data", f"kp_seed_{datetime.now():%Y%m%d_%H%M}.json")
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(out, fh, ensure_ascii=False, indent=1)
        size = os.path.getsize(path)
        print(f"已导出 {len(subjects_out)} 个学科 / {total_nodes} 个节点")
        print(f"文件：{path}（{size / 1024:.1f} KB）")
        return 0
    finally:
        db.close()


def _count(node) -> int:
    return 1 + sum(_count(c) for c in node.get("children") or [])


if __name__ == "__main__":
    sys.exit(main())
