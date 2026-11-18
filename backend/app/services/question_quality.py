"""Deterministic question quality checks, scoped inventory and guarded publication."""
import json
import re
from collections import Counter

from sqlalchemy import or_, select

from app.core.exception import BusinessException, PermissionException
from app.models import KnowledgePoint, Question
from app.utils.answer import normalize_answer
from app.utils.options import normalize_options


def decode(value):
    try:
        return json.loads(value) if isinstance(value, str) else value
    except (ValueError, TypeError):
        return value


def issues_for(question):
    errors, warnings = [], []
    answer = decode(question.answer)
    options = normalize_options(decode(question.options))
    if not str(question.stem or "").strip():
        errors.append("题干为空")
    if answer in (None, "", []):
        errors.append("缺少标准答案")
    if question.type in {"single", "multiple", "judge"}:
        raw_options = decode(question.options)
        if isinstance(raw_options, list):
            raw_keys = [str(item.get("key") or item.get("value") or chr(65 + index)).strip().upper()
                        for index, item in enumerate(raw_options) if isinstance(item, dict)]
            if len(raw_keys) != len(set(raw_keys)):
                errors.append("选项编号重复")
        if len(options) < 2:
            errors.append("选项少于两项")
        keys = [str(item["key"]) for item in options]
        if len(set(keys)) != len(keys):
            errors.append("选项编号重复")
        if any(not str(item["text"]).strip() for item in options):
            errors.append("存在空选项")
        tokens = normalize_answer(question.type, answer)
        if not tokens.issubset(set(keys)):
            errors.append("答案包含不存在的选项")
        if question.type in {"single", "judge"} and len(tokens) != 1:
            errors.append("单选或判断题必须只有一个答案")
        match = re.search(r"(?:答案为|正确选项为|答案是)\s*([A-H](?:[,、，][A-H])*)", question.analysis or "")
        if match and normalize_answer(question.type, match.group(1)) != tokens:
            errors.append("答案与解析中声明的选项冲突")
    if not question.knowledge_point_id:
        warnings.append("未关联知识点")
    if not str(question.analysis or "").strip():
        warnings.append("缺少解析")
    return {"errors": errors, "warnings": warnings}


def assert_publishable(question):
    issues = issues_for(question)
    if issues["errors"]:
        raise BusinessException("质检未通过：" + "；".join(issues["errors"]))


def check_publication(question, status, can_audit):
    if status != "published":
        return
    if question.bank_type == "public" and not can_audit:
        raise PermissionException("公共题库上架需管理员审核")
    if str(question.source or "").startswith("ai"):
        assert_publishable(question)


def visible_questions(db, user, subject_id=None):
    statement = select(Question)
    if "sys_admin" not in user.role_codes:
        statement = statement.where(or_(Question.bank_type == "public", Question.owner_id == user.id))
    if "grade_admin" in user.role_codes and "sys_admin" not in user.role_codes:
        statement = statement.where(Question.grade_id == (user.grade_admin_grade_id or user.grade_id or -1))
    elif "sys_admin" not in user.role_codes:
        from app.models import TeachingAssignment
        statement = statement.where(Question.subject_id.in_(select(TeachingAssignment.subject_id).where(
            TeachingAssignment.teacher_id == user.id, TeachingAssignment.is_active.is_(True))))
    if subject_id:
        statement = statement.where(Question.subject_id == subject_id)
    return list(db.scalars(statement.order_by(Question.id).limit(5001)).all())


def inventory(db, user, subject_id=None):
    from app.api.deps import has_perm
    rows = visible_questions(db, user, subject_id)
    can_audit = bool({"sys_admin", "grade_admin"} & set(user.role_codes)) or has_perm(user, "question:bank:audit")
    fingerprints = Counter(re.sub(r"\s+", "", item.stem or "").lower() for item in rows)
    items = []
    for question in rows[:5000]:
        issues = issues_for(question)
        if fingerprints[re.sub(r"\s+", "", question.stem or "").lower()] > 1:
            issues["warnings"].append("题干重复，请核查是否为有效变式")
        from app.services.question_presentation import presentation_fields
        items.append({"id": question.id, "stem": question.stem, "status": question.status,
                      "source": question.source, "knowledge_point_id": question.knowledge_point_id,
                      "can_edit": can_audit or (question.bank_type == "private" and question.owner_id == user.id),
                      **presentation_fields(question.extra_json), **issues})
    counts = Counter(item.knowledge_point_id for item in rows
                     if item.status == "published" and item.bank_type == "public"
                     and not issues_for(item)["errors"])
    statement = select(KnowledgePoint).where(
        KnowledgePoint.status == "published", KnowledgePoint.is_active.is_(True))
    if subject_id:
        statement = statement.where(KnowledgePoint.subject_id == subject_id)
    if "sys_admin" not in user.role_codes:
        from app.models import TeachingAssignment
        if "grade_admin" in user.role_codes:
            statement = statement.where(KnowledgePoint.grade_id == (user.grade_admin_grade_id or user.grade_id or -1))
        else:
            statement = statement.where(KnowledgePoint.subject_id.in_(select(TeachingAssignment.subject_id).where(
                TeachingAssignment.teacher_id == user.id, TeachingAssignment.is_active.is_(True))))
    nodes = list(db.scalars(statement.limit(5000)).all())
    parents = {item.parent_id for item in nodes if item.parent_id}
    gaps = [{"id": item.id, "name": item.name, "question_count": counts[item.id]}
            for item in nodes if item.id not in parents and counts[item.id] < 3]
    return {"items": items, "gaps": gaps, "total_scanned": min(len(rows), 5000),
            "truncated": len(rows) > 5000,
            "errors": sum(bool(item["errors"]) for item in items)}


def publish(db, user, ids):
    from app.api.deps import has_perm
    if not ({"sys_admin", "grade_admin"} & set(user.role_codes)
            or has_perm(user, "question:bank:audit")):
        raise PermissionException("需要题库审核权限")
    allowed = {item.id: item for item in visible_questions(db, user)}
    for question_id in set(ids):
        if question_id not in allowed:
            raise PermissionException("包含无权审核的题目")
        assert_publishable(allowed[question_id])
    for question_id in set(ids):
        allowed[question_id].status = "published"
    db.commit()
    return {"published": len(set(ids))}


def save_visual(db, user, question_id, visual):
    from app.api.deps import has_perm
    question = next((item for item in visible_questions(db, user) if item.id == question_id), None)
    if not question:
        raise PermissionException("无权修改该题目")
    if question.bank_type == "public" and not (
        {"sys_admin", "grade_admin"} & set(user.role_codes) or has_perm(user, "question:bank:audit")
    ):
        raise PermissionException("公共题目图形需要题库审核权限")
    extra = decode(question.extra_json) or {}
    if not isinstance(extra, dict):
        extra = {}
    if visual is None:
        extra.pop("visual", None)
    else:
        extra["visual"] = visual.model_dump()
    question.extra_json = json.dumps(extra, ensure_ascii=False)
    db.commit()
    return {"id": question.id, "visual": extra.get("visual")}
