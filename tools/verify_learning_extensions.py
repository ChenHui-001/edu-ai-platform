"""Behavioral regression of all learning extensions against an isolated database."""
import copy
import json
import os
import sys
import tempfile
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
TEMP = tempfile.TemporaryDirectory(prefix="learning-extensions-", ignore_cleanup_errors=True)
os.environ.update({
    "DATABASE_URL": f"sqlite:///{Path(TEMP.name) / 'test.db'}",
    "SECRET_KEY": "isolated-learning-extensions-test-key",
    "SEED_BASE_DATA": "false", "SEED_DEMO_DATA": "false",
    "SCHEDULER_ENABLED": "false", "LLM_ENABLED": "false",
    "RAG_WARMUP_ENABLED": "false", "DEBUG": "false",
    "UPLOAD_DIR": str(Path(TEMP.name) / "uploads"),
    "EXPORT_DIR": str(Path(TEMP.name) / "exports"),
    "LOG_DIR": str(Path(TEMP.name) / "logs"),
})

from fastapi import Depends
from fastapi.testclient import TestClient
from sqlalchemy import event, func, select

from app.api.deps import DataScope, get_current_user
from app.core.exception import PermissionException
from app.core.config import settings
from app.core.database import Base, SessionLocal, engine, get_db
from app.main import app
from app.models import (
    Class, Grade, KnowledgeMastery, KnowledgePoint, KnowledgePrerequisite, Notification,
    Paper, Question, QuestionKnowledge, RemediationPlan, Role, Subject, Task,
    TeachingAssignment, User,
)
from app.services.catalog_cache import invalidate_catalog
from app.services.knowledge_diagnosis import build_graph, grade_question
from app.services.knowledge_graph import resolve_graph
from app.services.grounded_tutor import readable_question
from app.services.teaching_graph import class_graph
from app.services.question_presentation import presentation_fields
from app.services.question_quality import issues_for
from app.services.readiness import readiness_status
from app.services.remediation import push_plan_reminders
from app.services.taxonomy_source import acyclic, bundle_digest, read_source
import app.services.taxonomy_sync as taxonomy_sync
from app.utils.common import now_local

CHECKS = 0


def check(name, condition):
    global CHECKS
    if not condition:
        raise AssertionError(name)
    CHECKS += 1
    print(f"[OK] {name}")


def seed(db):
    grades = []
    for number in (1, 2):
        grade = db.scalar(select(Grade).where(Grade.grade_num == number))
        grades.append(grade)
    subject = Subject(name="数学", grade_id=grades[0].id)
    other_subject = Subject(name="语文", grade_id=grades[0].id)
    db.add_all([subject, other_subject])
    db.flush()
    klass = Class(name="扩展测试班", grade_id=grades[0].id)
    other_class = Class(name="无权限班", grade_id=grades[0].id)
    db.add_all([klass, other_class])
    db.flush()
    users = {}
    for identity in ("sys_admin", "teacher", "student"):
        role = db.scalar(select(Role).where(Role.code == identity))
        user = User(username=f"extensions_{identity}", real_name=identity, password="test-only",
                    identity=identity, status="active", roles=[role])
        if identity == "student":
            user.grade_id, user.class_id = grades[0].id, klass.id
        users[identity] = user
        db.add(user)
    stranger = User(username="extensions_stranger", real_name="other", password="test-only",
                    identity="student", status="active", grade_id=grades[0].id, class_id=other_class.id,
                    roles=[db.scalar(select(Role).where(Role.code == "student"))])
    untested = User(username="extensions_untested", real_name="untested", password="test-only",
                    identity="student", status="active", grade_id=grades[0].id, class_id=klass.id,
                    roles=[db.scalar(select(Role).where(Role.code == "student"))])
    db.add_all([stranger, untested])
    db.flush()
    db.add(TeachingAssignment(teacher_id=users["teacher"].id, class_id=klass.id,
                             grade_id=grades[0].id, subject_id=subject.id, is_active=True))
    node = KnowledgePoint(name="加法扩展", grade_id=grades[0].id, subject_id=subject.id,
                          level=1, status="published", is_active=True, description="把两部分合起来。")
    db.add(node)
    db.flush()
    questions = []
    for position in range(6):
        question = Question(stem=f"扩展测试 {position}：$1+1$ 等于几？", type="single",
                            answer='"A"', options='[{"key":"A","text":"2"},{"key":"B","text":"3"}]',
                            analysis="答案为 A。", grade_id=grades[0].id, subject_id=subject.id,
                            knowledge_point_id=node.id, owner_id=users["sys_admin"].id,
                            bank_type="public", status="published",
                            extra_json='{"visual":{"kind":"fraction","numerator":1,"denominator":2},"accept":["secret"]}')
        questions.append(question)
        db.add(question)
    private = Question(stem="私有题", type="single", answer='"B"', options=questions[0].options,
                       grade_id=grades[0].id, subject_id=subject.id, knowledge_point_id=node.id,
                       owner_id=users["sys_admin"].id, bank_type="private", status="published")
    bad = Question(stem="AI 待审题", type="single", answer='"Z"', options=questions[0].options,
                   grade_id=grades[0].id, subject_id=subject.id, knowledge_point_id=node.id,
                   owner_id=users["sys_admin"].id, bank_type="public", status="draft", source="ai_import")
    db.add_all([private, bad])
    db.commit()
    return {"subject": subject.id, "other_subject": other_subject.id, "grade": grades[0].id,
            "class": klass.id, "other_class": other_class.id, "node": node.id,
            "admin": users["sys_admin"].id, "teacher": users["teacher"].id,
            "student": users["student"].id, "stranger": stranger.id,
            "questions": [question.id for question in questions], "private": private.id, "bad": bad.id}


def main():
    for directory in (settings.UPLOAD_DIR, settings.EXPORT_DIR, settings.LOG_DIR):
        Path(directory).mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(engine)
    with TestClient(app) as client:
        with SessionLocal() as db:
            ids = seed(db)

        def as_user(user_id):
            def override(db=Depends(get_db)):
                return db.get(User, user_id)
            app.dependency_overrides[get_current_user] = override

        def call(method, path, data=None, expected=200):
            response = client.request(method, "/api/v1" + path, json=data)
            if response.status_code != expected:
                raise AssertionError(f"{method} {path}: {response.status_code} {response.text[:1000]}")
            check(f"{method} {path} -> {expected}", response.status_code == expected)
            return response.json().get("data")

        as_user(ids["student"])
        check("readiness includes schema and writable directories", readiness_status()["ready"])
        with patch.object(settings, "EXPORT_DIR", str(Path(TEMP.name) / "missing")):
            check("missing directory is not ready", not readiness_status()["ready"])
            call("GET", "/ready", expected=503)
        call("GET", "/ready")
        with SessionLocal() as db:
            invalidate_catalog()
            query_counts = []
            def count_query(connection, cursor, statement, parameters, context, executemany):
                query_counts.append(statement)
            event.listen(engine, "before_cursor_execute", count_query)
            graph = build_graph(db, "数学")
            first_queries = len(query_counts)
            query_counts.clear()
            build_graph(db, "数学")
            check("catalog cache removes repeated SQL", first_queries >= 3 and len(query_counts) == 0)
            event.remove(engine, "before_cursor_execute", count_query)
            check("private questions are excluded", all(
                item["db_id"] != ids["private"] for item in graph["bank"][ids["node"]]))
            graph["nodes"].clear()
            check("cached catalog is not mutable by callers", bool(build_graph(db, "数学")["nodes"]))
            check("only display extras are public", "accept" not in presentation_fields(
                db.get(Question, ids["questions"][0]).extra_json))
            try:
                readable_question(db, db.get(User, ids["student"]), ids["private"])
            except PermissionException as exc:
                check("tutor service rejects private questions directly", "公共题目" in str(exc))
            else:
                raise AssertionError("tutor service leaked private question")
            node = db.get(KnowledgePoint, ids["node"])
            others = [KnowledgePoint(name=f"fan-{position}", subject_id=ids["subject"],
                      grade_id=ids["grade"], status="published") for position in range(65)]
            db.add_all(others)
            db.flush()
            db.add_all([KnowledgePrerequisite(topic_kp_id=other.id, prerequisite_kp_id=node.id)
                        for other in others])
            db.commit()
            rows, edges, truncated = resolve_graph(db, [node], [node, *others],
                                                   center_id=node.id, limit=10, depth=2)
            check("center BFS cap includes ancestors", len(rows) == 10 and truncated)
            check("all graph edges have visible endpoints", all(
                edge["source"] in {row.id for row in rows} and edge["target"] in {row.id for row in rows}
                for edge in edges))
            check("multiple selection compares sets", grade_question(
                {"type": "multiple", "answer": ["A", "C"]}, ["C", "A"]) == "correct")
            check("multiple selection rejects missing option", grade_question(
                {"type": "multiple", "answer": ["A", "C"]}, ["A"]) == "wrong")

        diagnosis = call("POST", "/edu/knowledge/diagnosis/sessions",
                         {"subject_id": ids["subject"], "grade_id": ids["grade"],
                          "targets": [ids["node"]], "limit": 3, "confirm": 1})
        next_item = diagnosis["next"]
        diagnosis_id = diagnosis["id"]
        diagnosis = call("POST", f"/edu/knowledge/diagnosis/sessions/{diagnosis_id}/answers",
                         {"knowledge_point_id": ids["node"], "question_id": next_item["question"]["id"], "answer": "B"})
        diagnosis = call("GET", f"/edu/knowledge/diagnosis/sessions/{diagnosis_id}")
        for attempt in range(10):
            if diagnosis["finished"]:
                break
            item = diagnosis["next"]
            call("POST", f"/edu/knowledge/diagnosis/sessions/{diagnosis_id}/answers",
                 {"knowledge_point_id": item["knowledge_point_id"],
                  "question_id": item["question"]["id"], "answer": "B"})
            diagnosis = call("GET", f"/edu/knowledge/diagnosis/sessions/{diagnosis_id}")
        check("diagnosis completed", diagnosis["finished"])
        plan = call("POST", "/learning/remediation", {"diagnosis_id": diagnosis["id"]})
        repeated = call("POST", "/learning/remediation", {"diagnosis_id": diagnosis["id"]})
        check("plan creation idempotent", repeated["id"] == plan["id"])
        with SessionLocal() as db:
            check("diagnosis and explanation do not update mastery", db.scalar(
                select(func.count(KnowledgeMastery.id))) == 0)
        as_user(ids["stranger"])
        call("GET", f"/learning/remediation/{plan['id']}", expected=403)
        as_user(ids["student"])
        quiz_path = f"/learning/remediation/{plan['id']}/quizzes"
        answers_path = f"/learning/remediation/{plan['id']}/answers"
        call("POST", quiz_path, {"step_id": ids["node"], "stage": "retest", "version": plan["version"]}, 400)
        call("POST", quiz_path, {"step_id": ids["node"], "stage": "practice", "version": 999}, 409)
        plan = call("POST", quiz_path, {"step_id": ids["node"], "stage": "practice", "version": plan["version"]})
        check("quiz does not leak answers", all("answer" not in item and "analysis" not in item
                                               for item in plan["quiz"]["questions"]))
        restored_plan = call("GET", f"/learning/remediation/{plan['id']}")
        check("quiz persists on reload", restored_plan["quiz"]["id"] == plan["quiz"]["id"])
        quiz_id = plan["quiz"]["id"]
        answer_data = {"quiz_id": quiz_id, "answers": {item["id"]: "A" for item in plan["quiz"]["questions"]},
                       "version": plan["version"]}
        call("POST", answers_path, {**answer_data, "answers": {"nested": {"value": "A"}}}, 422)
        call("POST", answers_path, {**answer_data, "version": 999}, 409)
        result = call("POST", answers_path, answer_data)
        plan = result["plan"]
        check("real answers update practice state", result["result"]["score"] == 100 and plan["steps"][0]["status"] == "retest")
        with SessionLocal() as db:
            total = db.scalar(select(KnowledgeMastery.total_count).where(KnowledgeMastery.student_id == ids["student"]))
        call("POST", answers_path, answer_data)
        with SessionLocal() as db:
            check("repeated submission does not double mastery", total == db.scalar(
                select(KnowledgeMastery.total_count).where(KnowledgeMastery.student_id == ids["student"])))
        plan = call("POST", quiz_path, {"step_id": ids["node"], "stage": "retest", "version": plan["version"]})
        answer_data = {"quiz_id": plan["quiz"]["id"], "answers": {item["id"]: "A" for item in plan["quiz"]["questions"]},
                       "version": plan["version"]}
        plan = call("POST", answers_path, answer_data)["plan"]
        check("retest schedules review", plan["steps"][0]["status"] == "review" and plan["steps"][0]["review_due"])
        call("POST", quiz_path, {"step_id": ids["node"], "stage": "review", "version": plan["version"]}, 400)
        for round_index in range(3):
            with SessionLocal() as db:
                record = db.get(RemediationPlan, plan["id"])
                payload = json.loads(record.payload)
                payload["steps"][0]["review_due"] = (now_local() - timedelta(minutes=1)).isoformat()
                record.payload = json.dumps(payload)
                db.commit()
                push_plan_reminders(db)
                db.commit()
                notice_count = db.scalar(select(func.count(Notification.id)).where(
                    Notification.biz_type == "remediation"))
                push_plan_reminders(db)
                db.commit()
                check(f"review reminder round {round_index} deduplicated", notice_count == db.scalar(
                    select(func.count(Notification.id)).where(Notification.biz_type == "remediation")))
            plan = call("GET", f"/learning/remediation/{plan['id']}")
            plan = call("POST", quiz_path, {"step_id": ids["node"], "stage": "review", "version": plan["version"]})
            plan = call("POST", answers_path, {"quiz_id": plan["quiz"]["id"],
                         "answers": {item["id"]: "A" for item in plan["quiz"]["questions"]},
                         "version": plan["version"]})["plan"]
        check("all review rounds complete the plan", plan["completed"])
        with SessionLocal() as db:
            record = db.get(RemediationPlan, plan["id"])
            payload = json.loads(record.payload)
            payload["steps"][0]["status"] = "learning"
            payload["completed"] = False
            record.payload = json.dumps(payload)
            record.version += 1
            db.commit()
            total = db.scalar(select(KnowledgeMastery.total_count).where(KnowledgeMastery.student_id == ids["student"]))
        plan = call("GET", f"/learning/remediation/{plan['id']}")
        plan = call("POST", quiz_path, {"step_id": ids["node"], "stage": "practice", "version": plan["version"]})
        call("POST", answers_path, {"quiz_id": plan["quiz"]["id"], "answers": {}, "version": plan["version"]})
        with SessionLocal() as db:
            check("skipped answers do not update formal mastery", total == db.scalar(
                select(KnowledgeMastery.total_count).where(KnowledgeMastery.student_id == ids["student"])))

        as_user(ids["teacher"])
        graph = call("GET", f"/teaching/graph?class_id={ids['class']}&subject_id={ids['subject']}")
        detail = next(item for item in graph["nodes"] if item["id"] == ids["node"])
        check("class graph separates unknown students", detail["tracked_students"] == 1 and detail["unknown_students"] == 1)
        with SessionLocal() as db:
            teacher = db.get(User, ids["teacher"])
            direct = class_graph(db, teacher, DataScope(teacher, db), ids["class"], ids["subject"])
            check("class graph service and API share analytics", direct == graph)
        call("GET", f"/teaching/graph?class_id={ids['other_class']}&subject_id={ids['subject']}", expected=403)
        call("GET", f"/teaching/graph?class_id={ids['class']}&subject_id={ids['other_subject']}", expected=403)
        assignment = {"class_id": ids["class"], "subject_id": ids["subject"],
                      "knowledge_point_ids": [ids["node"]], "count": 5}
        published = call("POST", "/teaching/graph/assign", assignment)
        with SessionLocal() as db:
            task = db.get(Task, published["task_id"])
            check("targeted assignment contains real paper items", len(task.paper.items) == 5)
            check("paper usage updated", db.get(Paper, published["paper_id"]).use_count == 1)
        as_user(ids["student"])
        call("POST", "/teaching/graph/assign", assignment, 403)
        task_paper = call("GET", f"/task/tasks/{published['task_id']}/paper")
        check("targeted paper is student-readable", len(task_paper["items"]) == 5)
        check("paper carries visual, not private answer extras", task_paper["items"][0].get("visual") and
              "accept" not in task_paper["items"][0] and "answer" not in task_paper["items"][0])
        submission = call("POST", f"/task/tasks/{published['task_id']}/submit", {
            "answers": [{"paper_item_id": item["paper_item_id"], "content": "A"} for item in task_paper["items"]]
        })
        check("targeted assignment is actually graded", submission["score"] == 25 and len(submission["answers"]) == 5)
        finished_paper = call("GET", f"/task/tasks/{published['task_id']}/paper")
        check("submitted paper reveals correct answers and rendered visuals", all(
            item["answer"] == "A" and item.get("visual") for item in finished_paper["items"]))
        practice = call("POST", "/learning/practice", {"subject_id": ids["subject"], "grade_id": ids["grade"],
                       "count": 2, "knowledge_point_ids": [ids["node"]], "question_types": ["single"]})
        practice_paper = call("GET", f"/learning/practice/{practice['task_id']}")
        check("random practice also carries safe drawing fields", all(
            item.get("visual") and "answer" not in item and "extra_json" not in item
            for item in practice_paper["items"]))

        as_user(ids["teacher"])
        report = call("GET", "/question/quality")
        check("quality detects bad AI answer", any(item["id"] == ids["bad"] and item["errors"] for item in report["items"]))
        call("POST", "/question/quality/publish", {"ids": [ids["bad"]]}, 403)
        call("PUT", f"/question/quality/{ids['questions'][0]}/visual",
             {"visual": {"kind": "fraction", "numerator": 1, "denominator": 3}}, 403)
        as_user(ids["admin"])
        call("POST", "/question/quality/publish", {"ids": [ids["bad"]]}, 400)
        call("PUT", f"/question/quality/{ids['questions'][0]}/visual",
             {"visual": {"kind": "fraction", "numerator": 1, "denominator": 3}})
        for invalid in (
            {"kind": "fraction", "numerator": 1.5, "denominator": 2},
            {"kind": "fraction", "numerator": 5, "denominator": 2},
            {"kind": "number_line", "min": 1, "max": 1},
            {"kind": "polygon", "points": [{"x": 0, "y": 0}]},
            {"kind": "number_line", "min": 0, "max": 10, "onload": "bad"},
        ):
            call("PUT", f"/question/quality/{ids['questions'][0]}/visual", {"visual": invalid}, 422)
        with SessionLocal() as db:
            check("visual save preserves grading extras", "accept" in json.loads(db.get(Question, ids["questions"][0]).extra_json))
            bad = db.get(Question, ids["bad"])
            bad.answer, bad.analysis = '"A"', "正确选项为 B"
            check("quality detects declared explanation conflict", bool(issues_for(bad)["errors"]))
            bad.analysis = "答案为 A"
            db.commit()
        call("POST", "/question/quality/publish", {"ids": [ids["bad"]]})

        as_user(ids["student"])
        for stage in ("hint", "steps", "answer"):
            reply = call("POST", "/learning/tutor", {"question_id": ids["questions"][0], "stage": stage})
            check(f"{stage} has server-owned references", reply["references"][0]["id"] == ids["questions"][0])
            if stage != "answer":
                check(f"{stage} reports fallback truthfully", reply["is_fallback"])
        call("POST", "/learning/tutor", {"question_id": ids["private"]}, 403)
        feedback = call("POST", "/learning/tutor/feedback",
                        {"question_id": ids["questions"][0], "stage": "hint", "content": "请核对提示"})
        as_user(ids["teacher"])
        feedbacks = call("GET", "/learning/tutor/feedback")["items"]
        check("assigned teacher sees student feedback without grade_id", feedback["id"] in {item["id"] for item in feedbacks})
        call("PUT", f"/learning/tutor/feedback/{feedback['id']}", {"correction": "教师核对：先合并两部分。"})
        as_user(ids["student"])
        reply = call("POST", "/learning/tutor", {"question_id": ids["questions"][0], "stage": "hint"})
        check("teacher correction replaces next tutoring response", reply["teacher_reviewed"] and "先合并" in reply["answer"])
        with SessionLocal() as db:
            task = db.get(Task, published["task_id"])
            task.type = "exam"
            db.commit()
        call("POST", "/learning/tutor", {"question_id": ids["questions"][0]}, 403)
        call("GET", "/learning/tutor/feedback", expected=403)
        call("GET", "/system/taxonomy-sync", expected=403)
        verify_sync(client, call, as_user, ids)
    app.dependency_overrides.clear()
    engine.dispose()
    if not Path(TEMP.name).resolve().is_relative_to(Path(tempfile.gettempdir()).resolve()):
        raise RuntimeError("Unexpected test directory")
    TEMP.cleanup()
    print(f"[OK] learning extensions: {CHECKS}/{CHECKS}")


def verify_sync(client, call, as_user, ids):
    commit = "a" * 40
    folder = taxonomy_sync.sync_dir() / commit
    (folder / "data").mkdir(parents=True)
    (folder / "LICENSE").write_text("CC BY-NC 4.0", encoding="utf-8")
    topics = [{"id": "cnm_test_a", "subject": "math", "grade": 1, "name": "上游加法",
               "chapter": "一年级上册 第1单元 加法"},
              {"id": "cnm_test_b", "subject": "math", "grade": 1, "name": "上游减法",
               "chapter": "一年级上册 第2单元 减法"}]
    questions = [{"id": "cnm_test_a_q1", "topicId": "cnm_test_a", "type": "numeric",
                  "prompt": "上游 1+2=?", "answer": "3", "explanation": "合计为3"}]
    dependencies = [{"topicId": "cnm_test_b", "prerequisiteId": "cnm_test_a", "strength": "hard"}]

    def write_source(new_topics, new_questions, new_dependencies):
        for key, value in (("topics", new_topics), ("questions", new_questions), ("dependencies", new_dependencies)):
            (folder / "data" / f"{key}.json").write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")

    as_user(ids["admin"])
    write_source(topics, questions, dependencies)
    with patch.object(taxonomy_sync, "fetch_source", return_value=(commit, folder)):
        preview = call("POST", "/system/taxonomy-sync/preview", {"ref": commit})
        check("preview pins immutable commit and source digest", preview["source_commit"] == commit and
              preview["report"]["bundle_digest"] == bundle_digest(folder))
        check("preview reports added content", preview["report"]["added_knowledge"] == 2 and preview["report"]["added_questions"] == 1)
        applied = call("POST", "/system/taxonomy-sync/apply", {"preview_id": preview["id"]})
        check("sync creates backup and history", applied["status"] == "applied")
        call("POST", "/system/taxonomy-sync/apply", {"preview_id": preview["id"]})
        with SessionLocal() as db:
            check("sync is idempotent", db.scalar(select(func.count(Question.id)).where(Question.external_source == "cn-math-taxonomy")) == 1)
            original = taxonomy_sync.dataset_snapshot(db)
            question = db.scalar(select(Question).where(Question.external_id == questions[0]["id"]))
            check("upstream question has knowledge association", db.scalar(select(func.count(QuestionKnowledge.id)).where(
                QuestionKnowledge.question_id == question.id)) == 1)
        updated_topics = copy.deepcopy(topics[:1])
        updated_topics[0]["name"] = "上游加法已修改"
        updated_questions = copy.deepcopy(questions)
        updated_questions[0]["answer"] = "4"
        write_source(updated_topics, updated_questions, [])
        preview2 = call("POST", "/system/taxonomy-sync/preview", {"ref": commit})
        check("preview reports update and archive", preview2["report"]["updated_questions"] == 1 and
              preview2["report"]["archived_knowledge"] == 1)
        check("preview includes prerequisite deletions", preview2["report"]["removed_edges"] == 1)
        call("POST", "/system/taxonomy-sync/apply", {"preview_id": preview2["id"]})
        with SessionLocal() as db:
            check("deleted upstream node is archived", not db.scalar(select(KnowledgePoint).where(
                KnowledgePoint.external_id == "cnm_test_b")).is_active)
        call("POST", f"/system/taxonomy-sync/{preview['id']}/restore", {}, 400)
        call("POST", f"/system/taxonomy-sync/{preview2['id']}/restore", {})
        with SessionLocal() as db:
            snapshot = taxonomy_sync.dataset_snapshot(db)
            check("restore recovers answers and hierarchy", snapshot["questions"][0]["answer"] == original["questions"][0]["answer"]
                  and snapshot["knowledge"][0]["name"] == original["knowledge"][0]["name"])
            check("restore recovers prerequisite and question links", len(snapshot["edges"]) == len(original["edges"])
                  and len(snapshot["links"]) == len(original["links"]))
        call("POST", "/system/taxonomy-sync/apply", {"preview_id": preview2["id"]}, 400)
        preview3 = call("POST", "/system/taxonomy-sync/preview", {"ref": commit})
        write_source(topics, questions, dependencies)
        call("POST", "/system/taxonomy-sync/apply", {"preview_id": preview3["id"]}, 409)
        preview4 = call("POST", "/system/taxonomy-sync/preview", {"ref": commit})
        with SessionLocal() as db:
            node = db.scalar(select(KnowledgePoint).where(KnowledgePoint.external_id == "cnm_test_a"))
            node.description = "管理员在预览后更新"
            db.commit()
        call("POST", "/system/taxonomy-sync/apply", {"preview_id": preview4["id"]}, 409)
        cycles = dependencies + [{"topicId": "cnm_test_a", "prerequisiteId": "cnm_test_b", "strength": "hard"}]
        write_source(topics, questions, cycles)
        cyclic = call("POST", "/system/taxonomy-sync/preview", {"ref": commit})
        check("preview quality rejects cyclic prerequisites", "先修关系存在环" in cyclic["report"]["errors"])
        call("POST", "/system/taxonomy-sync/apply", {"preview_id": cyclic["id"]}, 400)
        check("cycle checker supports large chains without recursion", acyclic(
            set(range(5000)), [(index + 1, index) for index in range(4999)]))
        invalid_topics = topics + [topics[0]]
        write_source(invalid_topics, questions, dependencies)
        call("POST", "/system/taxonomy-sync/preview", {"ref": commit}, 400)
        call("GET", "/system/taxonomy-sync")
        write_source(topics, questions, dependencies)
        check("canonical upstream records are deterministic", read_source(folder) == read_source(folder))
        invalidate_catalog()


if __name__ == "__main__":
    main()
