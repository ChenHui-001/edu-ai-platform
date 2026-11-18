#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""知识图谱接口行为回归（临时库，不碰真实数据）。

守四件事：
1. `/edu/knowledge/graph` 的节点/先修边/层级边数量与落库数据一致；
2. `root_id` 模式按层数展开、并把单元父节点补回来；
3. 学生视角带 `mastery`，且越权访问其它年级的知识点被拒；
4. 诊断结果 `summarize()` 输出的 `path_links` 与建议路径同源，
   前端画"依赖路径图"不会出现悬空箭头。

用法：python tools/verify_knowledge_graph.py
退出码：0 通过 / 1 失败
"""
import os
import sys
import tempfile

for _stream in (sys.stdout, sys.stderr):
    _reconfigure = getattr(_stream, "reconfigure", None)
    if _reconfigure is not None:
        try:
            _reconfigure(encoding="utf-8", errors="replace")
        except (OSError, ValueError):
            pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND = os.path.join(ROOT, "backend")
sys.path.insert(0, BACKEND)

_tmpdir = tempfile.mkdtemp(prefix="verify-graph-")
os.environ["DATABASE_URL"] = f"sqlite:///{os.path.join(_tmpdir, 'graph.db')}"
os.environ["SECRET_KEY"] = "verify-graph-secret-key-0123456789abcdef"
os.environ["DEBUG"] = "false"
os.environ["SEED_BASE_DATA"] = "false"
os.environ["SEED_DEMO_DATA"] = "false"
os.environ["SCHEDULER_ENABLED"] = "false"

from fastapi import Depends  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import select  # noqa: E402

from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.api.deps import get_current_user  # noqa: E402
from app.core.database import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import (  # noqa: E402
    Grade, KnowledgeMastery, KnowledgePoint, KnowledgePrerequisite, Question,
    Subject, User,
)
from app.services.knowledge_diagnosis import build_graph, summarize  # noqa: E402

FAILS = []


def check(name, condition, detail=""):
    if condition:
        print(f"[OK] {name}")
        return True
    FAILS.append(f"{name}: {detail}")
    print(f"[FAIL] {name} {detail}")
    return False


def seed(db):
    # 年级由启动期基线建好，这里复用；学科在 SEED_BASE_DATA=false 时不存在，按需创建。
    grade1 = db.scalar(select(Grade).where(Grade.name == "一年级"))
    grade2 = db.scalar(select(Grade).where(Grade.name == "二年级"))
    for grade, num in ((grade1, 1), (grade2, 2)):
        if grade is None:
            raise RuntimeError(f"启动基线缺少 {num} 年级")

    def ensure_subject(grade):
        row = db.scalar(select(Subject).where(
            Subject.grade_id == grade.id, Subject.name == "数学"))
        if row is None:
            row = Subject(name="数学", grade_id=grade.id)
            db.add(row)
            db.flush()
        return row

    math1 = ensure_subject(grade1)
    math2 = ensure_subject(grade2)

    unit = KnowledgePoint(
        name="第一单元 10以内加减法", level=1, grade_id=grade1.id,
        subject_id=math1.id, status="published", code="G1-M-U1",
    )
    db.add(unit)
    db.flush()

    base = KnowledgePoint(
        name="10以内加减法", level=2, parent_id=unit.id, path=f"{unit.id}",
        grade_id=grade1.id, subject_id=math1.id, status="published",
        difficulty="easy", code="G1-M-01",
    )
    plus = KnowledgePoint(
        name="20以内进位加法", level=2, parent_id=unit.id, path=f"{unit.id}",
        grade_id=grade1.id, subject_id=math1.id, status="published",
        difficulty="medium", code="G1-M-02",
    )
    word = KnowledgePoint(
        name="实际问题建模", level=2, parent_id=unit.id, path=f"{unit.id}",
        grade_id=grade1.id, subject_id=math1.id, status="published",
        difficulty="hard", code="G1-M-03",
    )
    far = KnowledgePoint(
        name="二年级拓展：两位数加法", level=2, grade_id=grade2.id,
        subject_id=math2.id, status="published", code="G2-M-01",
    )
    draft = KnowledgePoint(
        name="草稿知识点", level=2, grade_id=grade1.id, subject_id=math1.id,
        status="draft", code="G1-M-D",
    )
    db.add_all([base, plus, word, far, draft])
    db.flush()

    db.add_all([
        KnowledgePrerequisite(topic_kp_id=plus.id, prerequisite_kp_id=base.id,
                              strength="hard", source="manual"),
        KnowledgePrerequisite(topic_kp_id=word.id, prerequisite_kp_id=base.id,
                              strength="soft", source="manual"),
        KnowledgePrerequisite(topic_kp_id=far.id, prerequisite_kp_id=plus.id,
                              strength="hard", source="manual"),
    ])
    admin = User(username="graph_admin", password="x", real_name="图谱管理员",
                 identity="sys_admin", status="active")
    student = User(username="graph_student", password="x", real_name="图谱学生",
                   identity="student", status="active", grade_id=grade1.id)
    db.add_all([admin, student])
    db.flush()

    question = Question(
        stem="3 + 2 = ?", type="single", status="published",
        knowledge_point_id=base.id, difficulty="easy",
        grade_id=grade1.id, subject_id=math1.id, owner_id=admin.id,
        options='[{"key": "A", "text": "5"}]', answer="A",
    )
    db.add(question)
    db.add(KnowledgeMastery(student_id=student.id, knowledge_point_id=base.id,
                            subject_id=math1.id, total_count=4, correct_count=1,
                            mastery=25.0))
    db.commit()
    return {
        "grade1": grade1.id, "grade2": grade2.id,
        "math1": math1.id, "math2": math2.id,
        "unit": unit.id, "base": base.id, "plus": plus.id,
        "word": word.id, "far": far.id, "draft": draft.id,
        "admin": admin.id, "student": student.id,
    }


def main():
    Base.metadata.create_all(engine)
    with TestClient(app) as client:
        # 种子必须在应用 lifespan 之后写入：启动期的基线初始化会清空"无学科"的空库，
        # 先播种会被一起清掉（实测知识点被删、年级保留）。
        db = SessionLocal()
        try:
            data = seed(db)
        finally:
            db.close()

        def override_user(user):
            user_id = user

            def _fake_user(db=Depends(get_db)):
                return db.get(User, user_id)

            app.dependency_overrides[get_current_user] = _fake_user

        admin = data["admin"]
        student = data["student"]
        params = {"grade_id": data["grade1"], "subject_id": data["math1"]}
        override_user(admin)
        res = client.get("/api/v1/edu/knowledge/graph", params=params)
        check("全图接口 200", res.status_code == 200, res.text[:200])
        payload = res.json().get("data") or {}
        counts = payload.get("counts") or {}
        check("全图节点数=4（单元+3知识点，草稿不可见）",
              counts.get("nodes") == 4, str(counts))
        check("全图先修边=2", counts.get("prereq_edges") == 2, str(counts))
        check("全图层级边=3", counts.get("hierarchy_edges") == 3, str(counts))
        edges = payload.get("edges") or []
        hard = [e for e in edges if e["kind"] == "prereq" and e["strength"] == "hard"]
        soft = [e for e in edges if e["kind"] == "prereq" and e["strength"] == "soft"]
        check("硬/软先修分类正确", len(hard) == 1 and len(soft) == 1, str(edges))

        res = client.get("/api/v1/edu/knowledge/graph",
                         params={**params, "root_id": data["plus"], "depth": 1})
        payload = res.json().get("data") or {}
        ids = {node["id"] for node in payload.get("nodes") or []}
        check("中心模式 1 层带出直接先修",
              {data["base"], data["plus"]} <= ids, str(ids))
        check("中心模式补回单元父节点", data["unit"] in ids, str(ids))

        res = client.get("/api/v1/edu/knowledge/graph",
                         params={**params, "root_id": data["plus"], "depth": 2})
        payload = res.json().get("data") or {}
        ids2 = {node["id"] for node in payload.get("nodes") or []}
        check("中心模式 2 层带出兄弟节点",
              {data["base"], data["plus"], data["word"]} <= ids2, str(ids2))

        res = client.get("/api/v1/edu/knowledge/graph",
                         params={**params, "root_id": data["plus"], "depth": 1,
                                 "include_hierarchy": False})
        payload2 = res.json().get("data") or {}
        check("关闭层级边后层级边为 0",
              (payload2.get("counts") or {}).get("hierarchy_edges") == 0,
              str(payload2.get("counts")))

        override_user(student)
        res = client.get("/api/v1/edu/knowledge/graph", params=params)
        payload = res.json().get("data") or {}
        node_map = {node["id"]: node for node in payload.get("nodes") or []}
        check("学生视角返回 mastery",
              node_map.get(data["base"], {}).get("mastery") == 25.0,
              str(node_map.get(data["base"])))
        check("学生看不到草稿节点", data["draft"] not in node_map, str(node_map.keys()))

        res = client.get("/api/v1/edu/knowledge/graph",
                         params={**params, "root_id": data["far"]})
        check("跨年级定位被拒绝", res.status_code in (403, 404), f"status={res.status_code}")

        res = client.get("/api/v1/edu/knowledge/graph",
                         params={**params, "root_id": 999999})
        check("不存在的知识点返回 404", res.status_code == 404, f"status={res.status_code}")

    app.dependency_overrides.clear()

    db = SessionLocal()
    try:
        graph = build_graph(db, "数学")
        session = {
            "mode": "target",
            "order": [data["base"], data["plus"], data["word"]],
            "status": {data["base"]: {"s": "weak"}},
            "scope": None,
            "targets": [data["word"]],
            "answers": [],
            "limit": 16,
            "stack": [],
            "attempts": {},
            "confirm": 3,
        }
        summary = summarize(graph, session)
    finally:
        db.close()

    path_ids = {item["id"] for item in summary.get("path") or []}
    links = summary.get("path_links") or []
    check("诊断路径非空", bool(path_ids), str(summary.get("path")))
    check("path_links 两端都在路径内",
          bool(links) and all(
              link["source"] in path_ids and link["target"] in path_ids
              for link in links),
          str(links))

    if FAILS:
        print(f"\n[FAIL] {len(FAILS)} 项未通过")
        for item in FAILS:
            print("  -", item)
        return 1
    print("\n[OK] 知识图谱接口与诊断路径回归全部通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

