"""Diagnosis-driven learning plans with snapshot quizzes and optimistic concurrency."""
import json
import uuid
from datetime import timedelta

from fastapi import HTTPException
from sqlalchemy import select, update

from app.core.exception import BusinessException, NotFoundException, PermissionException
from app.models import KnowledgePoint, RemediationPlan, TaxonomyDiagnosisSession
from app.services.grading_service import _update_mastery
from app.services.knowledge_diagnosis import build_graph, grade_question, public_question, replay, summarize
from app.utils.common import now_local


def get_plan(db, user, plan_id):
    plan = db.get(RemediationPlan, plan_id)
    if not plan:
        raise NotFoundException("学习计划不存在")
    if plan.student_id != user.id:
        raise PermissionException("只能操作自己的学习计划")
    return plan


def plan_out(plan):
    payload = json.loads(plan.payload)
    quiz = payload.get("quiz")
    if quiz:
        payload["quiz"] = {**quiz, "questions": [public_question(item) for item in quiz["questions"]]}
    return {"id": plan.id, "title": plan.title, "version": plan.version,
            "diagnosis_id": plan.diagnosis_id, **payload}


def list_plans(db, user):
    return [plan_out(plan) for plan in db.scalars(
        select(RemediationPlan).where(RemediationPlan.student_id == user.id)
        .order_by(RemediationPlan.id.desc()).limit(100)).all()]


def create_plan(db, user, diagnosis_id):
    record = db.get(TaxonomyDiagnosisSession, diagnosis_id)
    if not record:
        raise NotFoundException("诊断不存在")
    if record.user_id != user.id:
        raise PermissionException("只能使用自己的诊断")
    existing = db.scalar(select(RemediationPlan).where(
        RemediationPlan.student_id == user.id, RemediationPlan.diagnosis_id == diagnosis_id))
    if existing:
        return plan_out(existing)
    from app.models import Subject

    graph = build_graph(db, db.get(Subject, record.subject_id).name)
    state = replay(graph, json.loads(record.targets_json), json.loads(record.answers_json),
                   mode=record.mode, limit=record.question_limit, confirm=record.confirm_count,
                   seed=record.seed)
    summary = summarize(graph, state)
    if not summary["finished"]:
        raise BusinessException("请先完成诊断")
    candidates = summary.get("path") or summary.get("pending") or []
    steps = []
    for item in candidates:
        if item.get("status") == "mastered":
            continue
        node = graph["by_id"].get(item["id"])
        if node:
            steps.append({"id": item["id"], "name": node["name"],
                          "explanation": node.get("description") or "先阅读知识资料，再完成专项练习。",
                          "status": "learning", "practice_score": None, "retest_score": None,
                          "review_round": 0, "review_due": None})
    if not steps:
        raise BusinessException("当前诊断没有需要补弱的知识点")
    payload = {"steps": steps, "quiz": None, "history": [], "completed": False}
    plan = RemediationPlan(student_id=user.id, diagnosis_id=record.id,
                           title="诊断补弱计划", payload=json.dumps(payload, ensure_ascii=False))
    db.add(plan)
    db.commit()
    return plan_out(plan)


def save_plan(db, plan, payload, expected_version):
    result = db.execute(update(RemediationPlan).where(
        RemediationPlan.id == plan.id, RemediationPlan.version == expected_version
    ).values(payload=json.dumps(payload, ensure_ascii=False),
             version=expected_version + 1, updated_at=now_local()))
    if result.rowcount != 1:
        db.rollback()
        raise HTTPException(409, "计划已更新，请刷新后重试")
    db.flush()
    db.refresh(plan)


def start_quiz(db, user, plan_id, data):
    plan = get_plan(db, user, plan_id)
    payload = json.loads(plan.payload)
    if payload["quiz"]:
        return plan_out(plan)
    if plan.version != data.version:
        raise HTTPException(409, "计划已更新，请刷新后重试")
    if len(payload["history"]) >= 200:
        raise BusinessException("本计划已达到测验上限，请重新诊断生成计划")
    step = next((item for item in payload["steps"] if item["id"] == data.step_id), None)
    if not step:
        raise NotFoundException("计划知识点不存在")
    if data.stage != "review":
        earlier = payload["steps"][:payload["steps"].index(step)]
        if any(item["status"] in ("learning", "retest") for item in earlier):
            raise BusinessException("请先完成前置知识点的练习与复测")
    if data.stage == "retest" and step["status"] != "retest":
        raise BusinessException("请先完成专项练习")
    if data.stage == "practice" and step["status"] != "learning":
        raise BusinessException("当前步骤无需重复练习")
    if data.stage == "review":
        if step["status"] != "review" or not step["review_due"] or step["review_due"] > now_local().isoformat():
            raise BusinessException("尚未到复习时间")
    graph = build_graph(db, _subject_name(db, step["id"]))
    bank = [item for item in graph["bank"].get(step["id"], [])
            if item["type"] in {"single", "multiple", "judge", "fill", "blank"}
            and item.get("answer") not in (None, "")]
    if not bank:
        raise BusinessException("该知识点暂无可自动判分的已发布题目，请联系教师补题")
    previous = {qid for entry in payload["history"] for qid in entry.get("question_ids", [])}
    bank.sort(key=lambda item: (item["qid"] in previous, item["qid"]))
    questions = bank[:5]
    payload["quiz"] = {"id": uuid.uuid4().hex, "step_id": step["id"], "stage": data.stage,
                       "questions": questions,
                       "reused_questions": sum(item["qid"] in previous for item in questions)}
    save_plan(db, plan, payload, data.version)
    db.commit()
    return plan_out(plan)


def _subject_name(db, kp_id):
    from app.models import Subject

    node = db.get(KnowledgePoint, kp_id)
    if not node or not node.is_active or node.status != "published":
        raise BusinessException("知识点已下架，请重新诊断")
    return db.get(Subject, node.subject_id).name


def submit_quiz(db, user, plan_id, data):
    plan = get_plan(db, user, plan_id)
    payload = json.loads(plan.payload)
    previous = next((item for item in payload["history"] if item["quiz_id"] == data.quiz_id), None)
    if previous:
        return {"plan": plan_out(plan), "result": previous}
    quiz = payload.get("quiz")
    if not quiz or quiz["id"] != data.quiz_id:
        raise BusinessException("当前测验不存在")
    grades = []
    for question in quiz["questions"]:
        result = grade_question(question, data.answers.get(question["qid"]))
        grades.append({"question_id": question["qid"], "correct": result == "correct",
                       "result": result, "answer": question["answer"], "analysis": question.get("analysis")})
    score = round(sum(item["correct"] for item in grades) * 100 / len(grades), 1)
    step = next(item for item in payload["steps"] if item["id"] == quiz["step_id"])
    stage = quiz["stage"]
    if stage == "practice":
        step["practice_score"] = score
        step["status"] = "retest"
    else:
        step["retest_score"] = score
        if score >= 80:
            step["review_round"] = step["review_round"] + 1 if stage == "review" else 0
            step["status"] = "completed" if step["review_round"] >= 3 else "review"
            interval = (1, 3, 7)[min(step["review_round"], 2)]
            step["review_due"] = None if step["status"] == "completed" else (
                now_local() + timedelta(days=interval)).isoformat()
            step.pop("review_notified_due", None)
        else:
            step["status"] = "learning"
            step["review_due"] = None
    record = {"quiz_id": quiz["id"], "stage": stage, "step_id": step["id"], "score": score,
              "results": grades, "question_ids": [item["qid"] for item in quiz["questions"]],
              "reused_questions": quiz["reused_questions"], "at": now_local().isoformat()}
    payload["history"].append(record)
    payload["quiz"] = None
    payload["completed"] = all(item["status"] == "completed" for item in payload["steps"])
    save_plan(db, plan, payload, data.version)
    for item in grades:
        if item["result"] != "skip":
            _update_mastery(db, user.id, step["id"], item["correct"])
    db.commit()
    return {"plan": plan_out(plan), "result": record}


def push_plan_reminders(db):
    from app.services.notification import notify
    sent = 0
    due_now = now_local().isoformat()
    for plan in db.scalars(select(RemediationPlan).order_by(RemediationPlan.id)).yield_per(100):
        payload = json.loads(plan.payload)
        due = [step for step in payload["steps"] if step["status"] == "review"
               and step.get("review_due") and step["review_due"] <= due_now
               and step.get("review_notified_due") != step["review_due"]]
        if not due:
            continue
        for step in due:
            step["review_notified_due"] = step["review_due"]
        result = db.execute(update(RemediationPlan).where(
            RemediationPlan.id == plan.id, RemediationPlan.version == plan.version
        ).values(payload=json.dumps(payload, ensure_ascii=False), version=plan.version + 1))
        if result.rowcount == 1 and notify(
            db, plan.student_id, title="补弱计划到期复习", content="、".join(step["name"] for step in due),
            type="review", biz_type="remediation", biz_id=plan.id, category="review"
        ) is not None:
            sent += 1
    return sent
