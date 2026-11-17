"""知识先修诊断与先修关系管理 API。"""
import json
import uuid
from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import (
    DataScope, get_current_user, get_data_scope, has_perm, require_perm,
)
from app.api.v1.knowledge import WRITE_PERM, _assert_write, _forced_grade, _is_student_user
from app.core.database import get_db
from app.core.exception import BusinessException, NotFoundException, PermissionException
from app.models import (
    KnowledgePoint, KnowledgePrerequisite, Subject,
    TaxonomyDiagnosisSession, User,
)
from app.schemas.taxonomy import (
    DiagnosisAnswerIn, DiagnosisSessionCreateIn, PrerequisiteCreateIn,
)
from app.services.knowledge_diagnosis import (
    DEFAULT_CONFIRM, RESULTS, apply_answer, build_graph, create_session,
    edge_exists, edge_list, edge_out, find_edge, grade_num_of, grade_question,
    next_item, next_question, public_question, replay, summarize, target_nodes,
    would_create_cycle,
)
from app.utils.common import now_local, ok

router = APIRouter(prefix="/edu", tags=["知识诊断"])


def _json_load(value: Optional[str], default: Any) -> Any:
    if not value:
        return default
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return default


def _json_dump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def _subject_name(db: Session, subject_id: int) -> str:
    subject = db.get(Subject, subject_id)
    if not subject:
        raise NotFoundException("学科不存在")
    return subject.name


def _get_session(
    db: Session, user: User, scope: DataScope, session_id: int,
) -> TaxonomyDiagnosisSession:
    record = db.get(TaxonomyDiagnosisSession, session_id)
    if not record:
        raise NotFoundException("诊断会话不存在")
    if record.user_id == user.id:
        return record
    allowed = scope.student_ids()
    if allowed is not None and record.user_id not in allowed:
        raise PermissionException("无权查看该诊断会话")
    return record


def _graph_for(db: Session, record: TaxonomyDiagnosisSession):
    return build_graph(db, _subject_name(db, record.subject_id))


def _state_for(db: Session, record: TaxonomyDiagnosisSession):
    graph = _graph_for(db, record)
    targets = _json_load(record.targets_json, [])
    answers = _json_load(record.answers_json, [])
    state = replay(
        graph, targets, answers, mode=record.mode,
        limit=record.question_limit, confirm=record.confirm_count,
        seed=record.seed or "default",
    )
    return graph, state


def _next_payload(graph, state) -> Optional[Dict[str, Any]]:
    item = next_item(graph, state)
    if not item:
        return None
    node = graph["by_id"].get(item["topic_id"]) or {}
    return {
        "knowledge_point_id": item["topic_id"],
        "name": node.get("name"),
        "chapter": node.get("chapter"),
        "grade_num": node.get("grade_num"),
        "attempt": item["attempt"],
        "question": public_question(item["question"]),
    }


def _session_out(record: TaxonomyDiagnosisSession, graph, state) -> Dict[str, Any]:
    summary = summarize(graph, state)
    return {
        "id": record.id,
        "student_id": record.user_id,
        "subject_id": record.subject_id,
        "grade_id": record.grade_id,
        "mode": record.mode,
        "limit": record.question_limit,
        "confirm": record.confirm_count,
        "seed": record.seed,
        "asked": summary["asked"],
        "finished": summary["finished"],
        "limit_reached": summary["limit_reached"],
        "progress": round(
            summary["asked"] * 100 / max(1, record.question_limit), 1),
        "next": _next_payload(graph, state),
        "summary": summary,
        "created_at": record.created_at,
        "finished_at": record.finished_at,
    }


def _resolve_student(
    db: Session, user: User, scope: DataScope, student_id: Optional[int],
) -> User:
    if user.identity == "student":
        if student_id not in (None, user.id):
            raise PermissionException("学生只能为自己的账号创建诊断")
        return user
    if not student_id:
        raise BusinessException("教师/管理员创建诊断时必须指定 student_id")
    student = db.get(User, int(student_id))
    if not student or student.identity != "student":
        raise NotFoundException("学生不存在")
    allowed = scope.student_ids()
    if allowed is not None and student.id not in allowed:
        raise PermissionException("无权为该学生创建诊断")
    return student


@router.get("/knowledge/diagnosis/targets", summary="可诊断知识点（按年级/学科）")
def diagnosis_targets(
    grade_id: Optional[int] = None,
    subject_id: int = Query(...),
    keyword: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    grade_id = _forced_grade(user, grade_id)
    if not grade_id or grade_id < 0:
        return ok({"items": [], "total": 0})
    subject = db.get(Subject, int(subject_id))
    if not subject:
        raise NotFoundException("学科不存在")
    if _is_student_user(user) and subject.grade_id != grade_id:
        raise PermissionException("学生只能查看本年级学科")
    graph = build_graph(db, subject.name)
    kw = str(keyword or "").strip().lower()
    items = []
    for node_id in graph["order"]:
        node = graph["by_id"][node_id]
        if node.get("grade_num") != int(grade_id):
            continue
        if not graph["bank"].get(node_id):
            continue
        if kw and kw not in str(node.get("name") or "").lower() \
                and kw not in str(node.get("chapter") or "").lower():
            continue
        items.append({
            "id": node_id,
            "name": node.get("name"),
            "chapter": node.get("chapter"),
            "external_id": node.get("external_id"),
            "question_count": len(graph["bank"].get(node_id, [])),
        })
    return ok({"items": items, "total": len(items)})


@router.post("/knowledge/diagnosis/sessions", summary="创建诊断会话")
def create_diagnosis_session(
    data: DiagnosisSessionCreateIn = Body(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    scope: DataScope = Depends(get_data_scope),
):
    payload = data.model_dump()
    raw_targets = payload.get("target_kp_ids") or payload.get("targets") or []
    if not isinstance(raw_targets, list):
        raise BusinessException("target_kp_ids 必须是数组")
    try:
        target_ids = list(dict.fromkeys(int(x) for x in raw_targets))
    except (TypeError, ValueError):
        raise BusinessException("目标知识点 ID 必须是整数")
    if not target_ids:
        raise BusinessException("至少选择一个目标知识点")
    if len(target_ids) > 30:
        raise BusinessException("单次诊断最多选择 30 个目标知识点")

    student = _resolve_student(db, user, scope, payload.get("student_id"))
    nodes = target_nodes(db, target_ids)
    node_map = {node.id: node for node in nodes}
    if len(node_map) != len(target_ids):
        raise BusinessException("目标知识点不存在")
    for node in nodes:
        if not node.is_active or node.status != "published":
            raise BusinessException(f"知识点「{node.name}」未发布，不能诊断")
        if student.grade_id and node.grade_id != student.grade_id:
            raise PermissionException("学生只能诊断本年级知识点")
    subject_ids = {node.subject_id for node in nodes}
    if len(subject_ids) != 1:
        raise BusinessException("一次诊断只能针对同一学科")
    subject_id = subject_ids.pop()
    if payload.get("subject_id") not in (None, "") \
            and int(payload["subject_id"]) != subject_id:
        raise BusinessException("目标知识点与 subject_id 不一致")
    mode = str(payload.get("mode") or "target").strip().lower()
    if mode not in {"target", "screen"}:
        raise BusinessException("mode 只能是 target / screen")
    try:
        limit = int(payload.get("limit") or (40 if mode == "screen" else 16))
        confirm = int(payload.get("confirm") or DEFAULT_CONFIRM)
    except (TypeError, ValueError):
        raise BusinessException("limit/confirm 必须是整数")
    if limit < 1 or limit > 100:
        raise BusinessException("limit 必须在 1-100 之间")
    if confirm < 1 or confirm > 10:
        raise BusinessException("confirm 必须在 1-10 之间")

    subject_name = _subject_name(db, subject_id)
    graph = build_graph(db, subject_name)
    missing = [nid for nid in target_ids if nid not in graph["by_id"]]
    if missing:
        raise BusinessException(f"知识点不可诊断：{missing[:5]}")
    seed = str(payload.get("seed") or f"{user.id}-{uuid.uuid4().hex[:8]}")
    try:
        state = create_session(
            graph, target_ids, mode=mode, limit=limit, confirm=confirm, seed=seed)
    except ValueError as exc:
        raise BusinessException(str(exc))
    if not any(graph["bank"].get(nid) for nid in target_ids):
        raise BusinessException("所选知识点暂无可用题目，无法诊断")

    record = TaxonomyDiagnosisSession(
        user_id=student.id,
        subject_id=subject_id,
        grade_id=student.grade_id or nodes[0].grade_id,
        targets_json=_json_dump(target_ids),
        mode=mode,
        question_limit=limit,
        confirm_count=confirm,
        answers_json="[]",
        status_json="{}",
        seed=seed,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return ok(_session_out(record, graph, state), message="诊断会话已创建")


@router.get("/knowledge/diagnosis/sessions/{session_id}", summary="诊断会话详情")
def get_diagnosis_session(
    session_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    scope: DataScope = Depends(get_data_scope),
):
    record = _get_session(db, user, scope, session_id)
    graph, state = _state_for(db, record)
    return ok(_session_out(record, graph, state))


@router.get("/knowledge/diagnosis/sessions/{session_id}/next", summary="下一道诊断题")
def get_next_diagnosis_item(
    session_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    scope: DataScope = Depends(get_data_scope),
):
    record = _get_session(db, user, scope, session_id)
    graph, state = _state_for(db, record)
    summary = summarize(graph, state)
    return ok({
        "finished": summary["finished"],
        "limit_reached": summary["limit_reached"],
        "asked": summary["asked"],
        "next": _next_payload(graph, state),
    })


@router.post("/knowledge/diagnosis/sessions/{session_id}/answers", summary="提交诊断作答")
def answer_diagnosis(
    session_id: int,
    data: DiagnosisAnswerIn = Body(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    scope: DataScope = Depends(get_data_scope),
):
    payload = data.model_dump()
    record = _get_session(db, user, scope, session_id)
    graph, state = _state_for(db, record)
    item = next_item(graph, state)
    if not item:
        raise BusinessException("诊断会话已结束")
    try:
        topic_id = int(payload.get("knowledge_point_id"))
    except (TypeError, ValueError):
        raise BusinessException("knowledge_point_id 必须是整数")
    if topic_id != item["topic_id"]:
        raise BusinessException("当前作答知识点与待答题不一致，请刷新下一题")
    question = item["question"]
    qid = payload.get("question_id")
    if qid not in (None, "") and str(qid) != str(question["qid"]):
        raise BusinessException("题目已变化，请刷新下一题")

    answer_text = payload.get("answer")
    result = grade_question(question, answer_text)
    supplied = str(payload.get("result") or "").strip().lower()
    if supplied not in RESULTS:
        supplied = ""
    if result is None:
        if not supplied:
            raise BusinessException("该题需要自评，请在 result 中传 correct / wrong / skip")
        result = supplied
    elif result != "skip" and supplied == "skip":
        result = "skip"
    new_state = apply_answer(
        graph, state, topic_id, result, qid=question["qid"],
        text=str(answer_text) if answer_text is not None else None,
        prompt=question.get("stem"),
    )
    record.answers_json = _json_dump(new_state.get("answers") or [])
    record.status_json = _json_dump({
        str(k): v for k, v in (new_state.get("status") or {}).items()
    })
    record.finished_at = now_local() if next_question(graph, new_state) is None else None
    db.commit()
    db.refresh(record)
    return ok({
        "result": result,
        "correct": result == "correct" if result != "skip" else None,
        "question_id": str(question["qid"]),
        "reference_answer": question.get("answer"),
        "analysis": question.get("analysis"),
        "asked": len(new_state.get("answers") or []),
        "summary": summarize(graph, new_state),
        "next": _next_payload(graph, new_state),
    }, message="作答已记录")


@router.get("/knowledge/diagnosis/sessions/{session_id}/summary", summary="诊断结果")
def diagnosis_summary(
    session_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    scope: DataScope = Depends(get_data_scope),
):
    record = _get_session(db, user, scope, session_id)
    graph, state = _state_for(db, record)
    return ok(summarize(graph, state))


def _node_for_read(
    db: Session, user: User, kp_id: int,
) -> KnowledgePoint:
    kp = db.get(KnowledgePoint, kp_id)
    if not kp or not kp.is_active:
        raise NotFoundException("知识点不存在")
    if _is_student_user(user):
        if not user.grade_id or kp.grade_id != user.grade_id or kp.status != "published":
            raise PermissionException("学生只能查看本年级已发布知识点")
    return kp


@router.get("/knowledge/{kp_id}/prerequisites", summary="知识点先修关系")
def list_prerequisites(
    kp_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    kp = _node_for_read(db, user, kp_id)
    items = edge_list(db, kp, "prerequisites")
    return ok({
        "node": {"id": kp.id, "name": kp.name},
        "items": items,
        "total": len(items),
        "can_edit": has_perm(user, WRITE_PERM),
    })


@router.get("/knowledge/{kp_id}/dependents", summary="知识点后继关系")
def list_dependents(
    kp_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    kp = _node_for_read(db, user, kp_id)
    items = edge_list(db, kp, "dependents")
    return ok({
        "node": {"id": kp.id, "name": kp.name},
        "items": items,
        "total": len(items),
        "can_edit": has_perm(user, WRITE_PERM),
    })


@router.post("/knowledge/{kp_id}/prerequisites", summary="新增先修关系")
def add_prerequisite(
    kp_id: int,
    data: PrerequisiteCreateIn = Body(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_perm(WRITE_PERM)),
):
    kp = db.get(KnowledgePoint, kp_id)
    if not kp:
        raise NotFoundException("知识点不存在")
    _assert_write(db, user, kp.grade_id, kp.subject_id)
    try:
        prerequisite_id = int(data.prerequisite_id)
    except (TypeError, ValueError):
        raise BusinessException("prerequisite_id 必须是整数")
    pre = db.get(KnowledgePoint, prerequisite_id)
    if not pre or not pre.is_active:
        raise NotFoundException("先修知识点不存在")
    _node_for_read(db, user, pre.id)
    if pre.id == kp.id:
        raise BusinessException("不能把知识点自己设为先修")
    topic_subject = db.get(Subject, kp.subject_id)
    pre_subject = db.get(Subject, pre.subject_id)
    if not topic_subject or not pre_subject or topic_subject.name != pre_subject.name:
        raise BusinessException("先修关系必须发生在同一学科")
    if pre.grade_id != kp.grade_id and not data.allow_cross_grade:
        raise BusinessException(
            "跨年级先修需要显式确认（allow_cross_grade=true）")
    if edge_exists(db, kp.id, pre.id):
        raise BusinessException("该先修关系已存在")
    if would_create_cycle(db, kp.subject_id, kp.id, pre.id):
        raise BusinessException("该先修关系会形成环，已拒绝")
    strength = str(data.strength or "hard").strip().lower()
    if strength not in {"hard", "soft"}:
        raise BusinessException("strength 只能是 hard / soft")
    reason = str(data.reason or "").strip() or None
    edge = KnowledgePrerequisite(
        topic_kp_id=kp.id,
        prerequisite_kp_id=pre.id,
        strength=strength,
        reason=reason[:2000] if reason else None,
        source="manual",
    )
    db.add(edge)
    db.commit()
    db.refresh(edge)
    data_out = edge_out(edge, pre)
    data_out["grade_num"] = grade_num_of(db, pre.grade_id)
    return ok(data_out, message="先修关系已新增")


@router.delete(
    "/knowledge/{kp_id}/prerequisites/{prerequisite_id}",
    summary="删除先修关系",
)
def remove_prerequisite(
    kp_id: int,
    prerequisite_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_perm(WRITE_PERM)),
):
    kp = db.get(KnowledgePoint, kp_id)
    if not kp:
        raise NotFoundException("知识点不存在")
    _assert_write(db, user, kp.grade_id, kp.subject_id)
    edge = find_edge(db, kp.id, prerequisite_id)
    if not edge:
        raise NotFoundException("先修关系不存在")
    db.delete(edge)
    db.commit()
    return ok(message="先修关系已删除")
