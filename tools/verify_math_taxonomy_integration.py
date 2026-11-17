#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""cn-math-taxonomy 集成验证。

覆盖四层：
  1. 外部图谱导入（题型/难度映射、幂等、去重、先修边合法性）
  2. 诊断算法（先修优先、回溯、确认、重放一致性、根因）
  3. HTTP API（学生隔离、教师数据范围、成环/跨年级校验）
  4. 真实数据规模（可选，需 --source-dir 或 CN_MATH_TAXONOMY_DATA）

用法：
    python tools/verify_math_taxonomy_integration.py
    python tools/verify_math_taxonomy_integration.py --source-dir C:/path/to/cn-math-taxonomy

脚本使用独立临时 SQLite，不触碰 ./data 下的业务库。
"""
import argparse
import asyncio
import json
import os
import shutil
import sys
import tempfile
import traceback
from typing import Any, Dict, List

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND = os.path.join(ROOT, "backend")

DEFAULT_SOURCE = os.environ.get(
    "CN_MATH_TAXONOMY_DATA",
    r"C:\Users\王\AppData\Local\Temp\cn-math-taxonomy-analysis",
)

PASSED: List[str] = []
FAILED: List[str] = []


def check(name: str, condition: Any, detail: Any = "") -> None:
    if condition:
        PASSED.append(name)
        print(f"  [PASS] {name}")
    else:
        FAILED.append(f"{name}: {detail}")
        print(f"  [FAIL] {name} -- {detail}")


def write_json(path: str, payload: Any) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)


def build_synthetic_source(root: str) -> str:
    """构造 2 个年级、2 个学科、3 条先修边的最小图谱。"""
    data_dir = os.path.join(root, "data")
    os.makedirs(data_dir, exist_ok=True)
    topics = [
        {
            "id": "syn_a", "subject": "math", "grade": 1,
            "chapter": "一年级上册 第1单元 加法", "name": "认识加法",
            "type": "conceptual", "domain": "数与代数",
        },
        {
            "id": "syn_b", "subject": "math", "grade": 1,
            "chapter": "一年级上册 第1单元 加法", "name": "加法计算",
            "type": "procedural", "domain": "数与代数",
        },
        {
            "id": "syn_p", "subject": "math", "grade": 1,
            "chapter": "一年级上册 第1单元 加法", "name": "数数",
            "type": "conceptual", "domain": "数与代数",
        },
        {
            "id": "syn_c", "subject": "math", "grade": 1,
            "chapter": "一年级上册 第2单元 减法", "name": "认识减法",
            "type": "procedural", "domain": "数与代数",
        },
        {
            "id": "syn_d", "subject": "english", "grade": 1,
            "chapter": "一年级上册 第1单元 字母", "name": "字母 A",
            "type": "conceptual", "domain": "字母",
        },
        {
            "id": "syn_e", "subject": "math", "grade": 2,
            "chapter": "二年级上册 第1单元 乘法", "name": "认识乘法",
            "type": "conceptual", "domain": "数与代数",
        },
    ]
    deps = [
        {"topicId": "syn_b", "prerequisiteId": "syn_a",
         "strength": "soft", "reason": "先认识加法再计算"},
        {"topicId": "syn_c", "prerequisiteId": "syn_b",
         "strength": "hard", "reason": "加法是减法的前置"},
        {"topicId": "syn_b", "prerequisiteId": "syn_p",
         "strength": "hard", "reason": "数数是加法的基础"},
    ]
    questions = [
        {"id": "syn_a_q1", "topicId": "syn_a", "type": "numeric",
         "difficulty": "basic", "prompt": "1 + 2 = ?", "answer": "3"},
        {"id": "syn_a_q2", "topicId": "syn_a", "type": "choice",
         "difficulty": "standard", "prompt": "下面哪个结果是 3？",
         "choices": ["1", "2", "3"], "answer": "3"},
        {"id": "syn_a_q3", "topicId": "syn_a", "type": "self",
         "difficulty": "challenge", "prompt": "说说你对加法的理解", "answer": None},
        {"id": "syn_b_q1", "topicId": "syn_b", "type": "numeric",
         "difficulty": "basic", "prompt": "2 + 3 = ?", "answer": "5"},
        {"id": "syn_b_q2", "topicId": "syn_b", "type": "numeric",
         "difficulty": "standard", "prompt": "4 + 5 = ?", "answer": "9"},
        {"id": "syn_b_q3", "topicId": "syn_b", "type": "numeric",
         "difficulty": "challenge", "prompt": "7 + 8 = ?", "answer": "15"},
        {"id": "syn_p_q1", "topicId": "syn_p", "type": "numeric",
         "difficulty": "basic", "prompt": "数一数：1、2、__", "answer": "3"},
        {"id": "syn_p_q2", "topicId": "syn_p", "type": "numeric",
         "difficulty": "basic", "prompt": "3 后面是几？", "answer": "4"},
        {"id": "syn_c_q1", "topicId": "syn_c", "type": "choice",
         "difficulty": "standard", "prompt": "3 - 1 = ?",
         "choices": ["1", "2", "3"], "answer": "2"},
        {"id": "syn_c_q2", "topicId": "syn_c", "type": "choice",
         "difficulty": "standard", "prompt": "5 - 2 = ?",
         "choices": ["2", "3", "4"], "answer": "3"},
        {"id": "syn_d_q1", "topicId": "syn_d", "type": "numeric",
         "difficulty": "basic", "prompt": "字母 A 后面是？", "answer": "B"},
        {"id": "syn_e_q1", "topicId": "syn_e", "type": "numeric",
         "difficulty": "basic", "prompt": "2 × 3 = ?", "answer": "6"},
        {"id": "syn_dup", "topicId": "syn_a", "type": "numeric",
         "difficulty": "basic", "prompt": "1 + 2 = ?", "answer": "3"},
    ]
    write_json(os.path.join(data_dir, "topics.json"), topics)
    write_json(os.path.join(data_dir, "dependencies.json"), deps)
    write_json(os.path.join(data_dir, "questions.json"), questions)
    write_json(os.path.join(data_dir, "README.json"), {"note": "synthetic fixture"})
    return root


def test_importer(db: Any, models: Dict[str, Any], source_dir: str) -> Dict[str, Any]:
    from app.services.math_taxonomy_import import import_math_taxonomy

    print("\n[1] 导入器：映射 / 幂等 / 去重")
    stats = import_math_taxonomy(
        db, source_dir, grades=[1, 2], subject="math",
        bank_type="private", status="published",
    )
    check("导入无错误", not stats["errors"], stats["errors"])
    check("知识点数量", stats["knowledge_points_created"] == 5,
          stats["knowledge_points_created"])
    check("单元数量", stats["units_created"] == 3, stats["units_created"])
    check("章节数量", stats["chapters_created"] == 3, stats["chapters_created"])
    check("先修边数量", stats["prerequisites_created"] == 3,
          stats["prerequisites_created"])
    check("题目数量", stats["questions_created"] == 11,
          stats["questions_created"])
    check("题干重复跳过", stats["questions_skipped_duplicate"] == 1,
          stats["questions_skipped_duplicate"])
    check("授权识别", stats["license"].startswith("unknown"), stats["license"])

    Question = models["Question"]
    by_ext = {
        q.external_id: q for q in db.query(Question).all() if q.external_id
    }
    check("题型 numeric→blank", by_ext["syn_a_q1"].type == "blank",
          by_ext["syn_a_q1"].type)
    check("题型 choice→single", by_ext["syn_a_q2"].type == "single",
          by_ext["syn_a_q2"].type)
    check("题型 self→short", by_ext["syn_a_q3"].type == "short",
          by_ext["syn_a_q3"].type)
    check("难度 basic→easy", by_ext["syn_a_q1"].difficulty == "easy",
          by_ext["syn_a_q1"].difficulty)
    check("难度 standard→medium", by_ext["syn_a_q2"].difficulty == "medium",
          by_ext["syn_a_q2"].difficulty)
    check("难度 challenge→hard", by_ext["syn_a_q3"].difficulty == "hard",
          by_ext["syn_a_q3"].difficulty)
    options = json.loads(by_ext["syn_a_q2"].options or "[]")
    check("选项可读", options and options[2]["key"] == "C"
          and options[2]["text"] == "3", options)
    extra = json.loads(by_ext["syn_a_q1"].extra_json or "{}")
    check("extra_json 可读", extra.get("externalType") == "numeric", extra)
    check("题目默认私有已发布",
          by_ext["syn_a_q1"].bank_type == "private"
          and by_ext["syn_a_q1"].status == "published",
          (by_ext["syn_a_q1"].bank_type, by_ext["syn_a_q1"].status))

    second = import_math_taxonomy(
        db, source_dir, grades=[1, 2], subject="math",
        bank_type="private", status="published",
    )
    check("二次导入知识点 0 新增", second["knowledge_points_created"] == 0,
          second["knowledge_points_created"])
    check("二次导入先修 0 新增", second["prerequisites_created"] == 0,
          second["prerequisites_created"])
    check("二次导入题目 0 新增", second["questions_created"] == 0,
          second["questions_created"])
    check("二次导入按外部 ID 跳过", second["questions_skipped_existing"] == 11,
          second["questions_skipped_existing"])

    KnowledgePoint = models["KnowledgePoint"]
    Prerequisite = models["KnowledgePrerequisite"]
    nodes = {kp.id: kp for kp in db.query(KnowledgePoint).all()}
    edges = db.query(Prerequisite).all()
    check("无悬空先修边",
          all(e.topic_kp_id in nodes and e.prerequisite_kp_id in nodes
              for e in edges), "dangling")
    check("无自环先修边",
          all(e.topic_kp_id != e.prerequisite_kp_id for e in edges), "self loop")
    adjacency: Dict[int, set] = {}
    for edge in edges:
        adjacency.setdefault(edge.topic_kp_id, set()).add(edge.prerequisite_kp_id)

    def has_cycle() -> bool:
        visiting, done = set(), set()

        def walk(node: int) -> bool:
            if node in visiting:
                return True
            if node in done:
                return False
            visiting.add(node)
            for nxt in adjacency.get(node, ()):
                if walk(nxt):
                    return True
            visiting.discard(node)
            done.add(node)
            return False

        return any(walk(node) for node in list(adjacency))

    check("先修图无环", not has_cycle(), "cycle detected")
    return stats


def test_diagnosis(db: Any, models: Dict[str, Any]) -> Dict[str, Any]:
    from app.services.knowledge_diagnosis import (
        apply_answer, build_graph, create_session, next_item, replay,
        summarize,
    )

    print("\n[2] 诊断算法：先修优先 / 回溯 / 确认 / 重放")
    graph = build_graph(db, "数学")
    by_name = {node["name"]: node["id"] for node in graph["nodes"]}
    b_id, a_id, p_id, c_id = (
        by_name["加法计算"], by_name["认识加法"], by_name["数数"], by_name["认识减法"])

    prereq_ids = [edge["id"] for edge in graph["prereqs"][b_id]]
    check("硬先修排在软先修之前",
          graph["by_id"][prereq_ids[0]]["name"] == "数数"
          and graph["by_id"][prereq_ids[1]]["name"] == "认识加法",
          prereq_ids)

    state = create_session(
        graph, [b_id], mode="target", limit=8, confirm=2, seed="verify")
    item = next_item(graph, state)
    check("首题命中目标节点", item and item["topic_id"] == b_id,
          item and item["topic_id"])

    state = apply_answer(graph, state, b_id, "wrong")
    check("首次答错保留重测机会",
          b_id not in state["status"]
          and next_item(graph, state)["topic_id"] == b_id,
          state["status"])
    state = apply_answer(graph, state, b_id, "wrong")
    check("二次答错判薄弱", state["status"][b_id]["s"] == "weak",
          state["status"])
    check("答错后回溯硬先修",
          next_item(graph, state)["topic_id"] == p_id,
          next_item(graph, state)["topic_id"])

    summary = summarize(graph, state)
    root_ids = [root["id"] for root in summary["roots"]]
    check("根因指向薄弱目标", root_ids == [b_id], root_ids)
    pending = [p["id"] for p in summary["roots"][0]["pending_prereqs"]]
    check("待测先修按硬→软排列", pending == [p_id, a_id], pending)

    for node_id, qids in ((p_id, None), (a_id, None)):
        for _ in range(2):
            item = next_item(graph, state)
            check("先修作答顺序", item["topic_id"] == node_id,
                  item and item["topic_id"])
            state = apply_answer(graph, state, node_id, "correct",
                                 qid=item["question"]["qid"])
    check("先修连续答对后掌握",
          state["status"][p_id]["s"] == "mastered"
          and state["status"][a_id]["s"] == "mastered",
          state["status"])

    check("薄弱目标保留在会话结论中", state["status"][b_id]["s"] == "weak",
          state["status"])

    replayed = replay(
        graph, [b_id], state["answers"], mode="target", limit=8,
        confirm=2, seed="verify",
    )
    check("会话重放与内存状态一致",
          replayed["status"] == state["status"]
          and replayed["stack"] == state["stack"],
          (replayed["status"], state["status"]))
    final = summarize(graph, state)
    check("最终统计掌握 2 个", final["counts"]["mastered"] == 2,
          final["counts"])
    check("最终薄弱 1 个", final["counts"]["weak"] == 1, final["counts"])
    check("最终根因保留目标节点",
          [root["id"] for root in final["roots"]] == [b_id], final["roots"])
    check("建议路径包含薄弱目标",
          any(item["id"] == b_id for item in final["path"]), final["path"])

    screen = create_session(
        graph, [b_id, c_id], mode="screen", limit=10, confirm=2, seed="screen")
    check("筛查模式范围仅目标节点",
          set(screen["scope"]) == {b_id, c_id}, screen["scope"])
    return {
        "b_id": b_id, "a_id": a_id, "p_id": p_id, "c_id": c_id,
        "graph": graph,
    }


async def test_api(app: Any, ids: Dict[str, int], tokens: Dict[str, str]) -> None:
    import httpx

    print("\n[3] HTTP API：隔离 / 校验")
    transport = httpx.ASGITransport(app=app)
    headers = {name: {"Authorization": f"Bearer {token}"}
               for name, token in tokens.items()}

    async with httpx.AsyncClient(
            transport=transport, base_url="http://verify") as client:
        res = await client.get(
            "/api/v1/edu/knowledge/diagnosis/targets",
            params={"grade_id": ids["grade1"], "subject_id": ids["subject_math"]},
            headers=headers["student1"])
        payload = res.json()
        names = {item["name"] for item in (payload.get("data") or {}).get("items", [])}
        check("学生可读取本年级诊断目标",
              res.status_code == 200 and "加法计算" in names,
              (res.status_code, names))
        check("目标列表不含其他年级",
              "认识乘法" not in names, names)

        res = await client.post(
            "/api/v1/edu/knowledge/diagnosis/sessions",
            json={"target_kp_ids": [ids["b"]], "mode": "target",
                  "limit": 8, "confirm": 2},
            headers=headers["student1"])
        body = res.json()
        check("学生可创建诊断会话", res.status_code == 200,
              (res.status_code, body))
        session_id = (body.get("data") or {}).get("id")
        next_topic = ((body.get("data") or {}).get("next") or {}).get(
            "knowledge_point_id")
        check("创建会话返回首题", session_id and next_topic == ids["b"],
              (session_id, next_topic))

        res = await client.get(
            f"/api/v1/edu/knowledge/diagnosis/sessions/{session_id}",
            headers=headers["student2"])
        check("其他学生不可读取会话", res.status_code == 403, res.status_code)

        res = await client.get(
            f"/api/v1/edu/knowledge/diagnosis/sessions/{session_id}",
            headers=headers["teacher"])
        check("无班级教师不可跨数据范围", res.status_code == 403,
              res.status_code)

        # 会话作答：syn_c 的硬先修是 syn_b
        res = await client.post(
            "/api/v1/edu/knowledge/diagnosis/sessions",
            json={"target_kp_ids": [ids["c"]], "mode": "target",
                  "limit": 8, "confirm": 1},
            headers=headers["student1"])
        api_session = (res.json().get("data") or {})
        api_session_id = api_session.get("id")
        current = api_session.get("next") or {}
        for _ in range(2):
            res = await client.post(
                f"/api/v1/edu/knowledge/diagnosis/sessions/{api_session_id}/answers",
                json={"knowledge_point_id": current["knowledge_point_id"],
                      "question_id": current["question"]["id"],
                      "answer": "zzz"},
                headers=headers["student1"])
            data = res.json().get("data") or {}
            current = data.get("next") or {}
        check("API 答错后切换到硬先修",
              current.get("knowledge_point_id") == ids["b"],
              current.get("knowledge_point_id"))
        res = await client.get(
            f"/api/v1/edu/knowledge/diagnosis/sessions/{api_session_id}/summary",
            headers=headers["student1"])
        summary = res.json().get("data") or {}
        check("API 诊断返回薄弱根因",
              summary.get("roots") and summary["roots"][0]["id"] == ids["c"],
              summary.get("roots"))

        res = await client.post(
            f"/api/v1/edu/knowledge/{ids['a']}/prerequisites",
            json={"prerequisite_id": ids["c"]},
            headers=headers["admin"])
        check("成环先修被拒绝", res.status_code == 400, res.status_code)
        check("成环错误文案可读",
              "环" in (res.json().get("message") or ""), res.json())

        res = await client.post(
            f"/api/v1/edu/knowledge/{ids['a']}/prerequisites",
            json={"prerequisite_id": ids["e"]},
            headers=headers["admin"])
        check("跨年级未确认被拒绝", res.status_code == 400, res.status_code)

        res = await client.post(
            f"/api/v1/edu/knowledge/{ids['a']}/prerequisites",
            json={"prerequisite_id": ids["e"], "allow_cross_grade": True,
                  "strength": "soft", "reason": "跨年级验证"},
            headers=headers["admin"])
        check("跨年级显式确认后可新增", res.status_code == 200,
              (res.status_code, res.json()))

        res = await client.get(
            f"/api/v1/edu/knowledge/{ids['a']}/prerequisites",
            headers=headers["student1"])
        items = (res.json().get("data") or {}).get("items") or []
        check("学生可读取先修关系",
              res.status_code == 200
              and any(i["knowledge_point_id"] == ids["e"] for i in items),
              items)

        res = await client.post(
            f"/api/v1/edu/knowledge/{ids['a']}/prerequisites",
            json={"prerequisite_id": ids["e"], "allow_cross_grade": True},
            headers=headers["student1"])
        check("学生不可写先修关系", res.status_code == 403, res.status_code)


def test_real_data(source_dir: str) -> None:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from app.core.database import Base
    from app.models import Role, User
    from app.services.math_taxonomy_import import import_math_taxonomy

    data_ok = os.path.isfile(os.path.join(source_dir, "data", "topics.json")) \
        or os.path.isfile(os.path.join(source_dir, "topics.json"))
    if not data_ok:
        print(f"\n[4] 真实数据：跳过（未找到 {source_dir}）")
        return

    print("\n[4] 真实数据：规模 / 幂等 / 图完整性")
    tmp = tempfile.mkdtemp(prefix="math_taxonomy_real_")
    engine = create_engine(f"sqlite:///{os.path.join(tmp, 'real.db')}")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        role = Role(code="sys_admin", name="系统管理员", is_active=True,
                    data_scope="all")
        user = User(username="real_owner", password="x", real_name="real_owner",
                    identity="sys_admin", status="active")
        user.roles.append(role)
        session.add(user)
        session.commit()
        stats = import_math_taxonomy(
            session, source_dir, grades=list(range(1, 10)), subject="math")
        check("真实数据知识点 599", stats["knowledge_points_created"] == 599,
              stats["knowledge_points_created"])
        check("真实数据先修边 1067", stats["prerequisites_created"] == 1067,
              stats["prerequisites_created"])
        check("真实数据题目 2520", stats["questions_created"] == 2520,
              stats["questions_created"])
        check("真实数据题干重复 23",
              stats["questions_skipped_duplicate"] == 23,
              stats["questions_skipped_duplicate"])
        check("真实数据导入无错误", not stats["errors"], stats["errors"][:3])
        check("真实数据许可识别", "CC BY-NC" in stats["license"],
              stats["license"])
        second = import_math_taxonomy(
            session, source_dir, grades=list(range(1, 10)), subject="math")
        check("真实数据二次导入 0 新增",
              second["knowledge_points_created"] == 0
              and second["prerequisites_created"] == 0
              and second["questions_created"] == 0,
              {k: second[k] for k in (
                  "knowledge_points_created", "prerequisites_created",
                  "questions_created")})
    finally:
        session.close()
        engine.dispose()
        shutil.rmtree(tmp, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", default=DEFAULT_SOURCE)
    parser.add_argument("--skip-real", action="store_true")
    args = parser.parse_args()

    tmp = tempfile.mkdtemp(prefix="math_taxonomy_verify_")
    db_path = os.path.join(tmp, "verify.db")
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    os.environ["SECRET_KEY"] = "verify-only-secret-key-0123456789"
    os.environ["APP_ENV"] = "test"
    os.environ["DEBUG"] = "false"
    sys.path.insert(0, BACKEND)

    from app.core.database import Base, SessionLocal, engine
    from app.core.security import create_access_token
    from app.models import (
        Grade, KnowledgePoint, KnowledgePrerequisite, Question, Role, Subject,
        User,
    )
    from app.models.system import UserStatus

    Base.metadata.create_all(engine)
    db = SessionLocal()
    models = {
        "Grade": Grade, "KnowledgePoint": KnowledgePoint,
        "KnowledgePrerequisite": KnowledgePrerequisite, "Question": Question,
        "Role": Role, "Subject": Subject, "User": User,
    }
    app = None
    try:
        admin_role = Role(code="sys_admin", name="系统管理员", is_active=True,
                          data_scope="all")
        teacher_role = Role(code="teacher", name="教师", is_active=True,
                            data_scope="taught_class")
        student_role = Role(code="student", name="学生", is_active=True,
                            data_scope="self")
        db.add_all([admin_role, teacher_role, student_role])
        db.flush()
        admin = User(
            username="verify_admin", password="x", real_name="verify_admin",
            identity="sys_admin", status=UserStatus.ACTIVE.value, grade_id=None,
        )
        admin.roles.append(admin_role)
        db.add(admin)
        db.commit()

        source = build_synthetic_source(os.path.join(tmp, "synthetic"))
        test_importer(db, models, source)
        ids = test_diagnosis(db, models)

        grade1 = db.query(Grade).filter(Grade.grade_num == 1).first()
        grade2 = db.query(Grade).filter(Grade.grade_num == 2).first()
        subject_math = db.query(Subject).filter(
            Subject.grade_id == grade1.id, Subject.name == "数学").first()
        if not subject_math:
            subject_math = db.query(Subject).filter(
                Subject.grade_id == grade1.id).first()

        def make_user(username: str, identity: str, grade_id: Any,
                      role: Role) -> User:
            user = User(
                username=username, password="x", real_name=username,
                identity=identity, status=UserStatus.ACTIVE.value,
                grade_id=grade_id,
            )
            user.roles.append(role)
            db.add(user)
            db.flush()
            return user

        student1 = make_user("verify_stu1", "student", grade1.id, student_role)
        student2 = make_user("verify_stu2", "student", grade1.id, student_role)
        teacher = make_user("verify_teacher", "teacher", None, teacher_role)
        admin = db.query(User).filter(User.username == "verify_admin").first()
        db.commit()

        e_id = db.query(KnowledgePoint).filter(
            KnowledgePoint.external_id == "syn_e").first().id
        ids.update({
            "grade1": grade1.id, "grade2": grade2.id,
            "subject_math": subject_math.id, "e": e_id,
            "a": ids["a_id"], "b": ids["b_id"],
            "c": ids["c_id"], "p": ids["p_id"],
        })
        tokens = {
            "student1": create_access_token(student1.id, role="student"),
            "student2": create_access_token(student2.id, role="student"),
            "teacher": create_access_token(teacher.id, role="teacher"),
            "admin": create_access_token(admin.id, role="sys_admin"),
        }

        from app.main import app as fastapi_app
        app = fastapi_app
        asyncio.run(test_api(app, ids, tokens))

        if not args.skip_real:
            test_real_data(args.source_dir)
    except Exception:  # noqa: BLE001 验证脚本需要完整堆栈
        traceback.print_exc()
        FAILED.append("unexpected exception")
    finally:
        db.close()
        engine.dispose()
        shutil.rmtree(tmp, ignore_errors=True)

    print("\n" + "=" * 60)
    print(f"通过 {len(PASSED)} 项，失败 {len(FAILED)} 项")
    if FAILED:
        for item in FAILED:
            print(f"  - {item}")
        return 1
    print("全部通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
