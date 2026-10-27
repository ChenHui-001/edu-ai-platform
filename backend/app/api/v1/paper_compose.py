"""标准组卷 V3 接口：双模式组卷 / 预览编辑 / 版本 / 共享 / 收藏 / 试卷库。

前缀 `/question/papers`（与既有 CRUD 同前缀，但路径全部新增，
不改动 question.py 的任何既有行为）。

路径规划（避开既有路由）：
  既有：GET /papers、POST /papers、PUT /papers/{id}、DELETE /papers/{id}、
        GET /papers/{id}、POST /papers/{id}/copy|share、GET /papers/{id}/export
  新增：POST /papers/compose/preview   自定义参数组卷预览
        POST /papers/compose/ai        AI 一键组卷
        POST /papers/compose/save      保存组卷结果
        GET  /papers/{id}/preview      全卷预览（含大题结构）
        POST /papers/{id}/items        增删改题目（含拖拽排序）
        POST /papers/{id}/items/{item_id}/regenerate  单题 AI 重生
        DELETE /papers/{id}/items/{item_id}
        POST /papers/{id}/sections/rename  大题改名
        POST /papers/{id}/restructure  一键重构（按标准重排大题）
        GET  /papers/{id}/versions     版本列表
        POST /papers/{id}/versions/{v}/restore  版本回溯
        GET  /papers/library           试卷库分类（我的/共享/公共/收藏）
        POST /papers/{id}/favorite     收藏/取消
        POST /papers/{id}/review       审核（申请公共库/通过/驳回）
        GET  /papers/{id}/export/docx  Word 导出
        GET  /papers/{id}/export/pdf   PDF 导出
        GET  /papers/{id}/export/answer-sheet  答题卡导出
"""
import io
import json
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, noload

from app.api.deps import require_perm
from app.core.database import get_db
from app.core.exception import BusinessException, NotFoundException, PermissionException
from app.models import (
    Answer, ExamStandard, Grade, KnowledgePoint, Paper, PaperFavorite, PaperItem,
    PaperShare, PaperStatus, PaperVersion, Question, SharePermission,
    ShareScope, Subject, Submission, Task, User,
)
from app.services import paper_compose_service as compose_svc
from app.services.paper_export_service import (
    build_answer_sheet, build_docx, build_pdf,
)
from app.services import paper_version_service as version_svc
from app.utils.common import PageParams, dictify, ok

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/question/papers", tags=["标准组卷"])

TYPE_LABEL = compose_svc.TYPE_LABEL


# ---------------------------------------------------------------- 权限 helpers
def _is_sys_admin(user: User) -> bool:
    return "sys_admin" in (user.role_codes or [])


def _is_grade_admin(user: User) -> bool:
    return "grade_admin" in (user.role_codes or [])


def _scope_clause(user: User):
    """范围共享的可见性条件（grade / school / public）。

    **年级共享必须限定同年级**：只判断 `share_scope == 'grade'` 会让全校
    甚至跨年级的教师都看到该卷（实测七年级数学卷出现在九年级教师列表）。
    school 共享按「创建者学校 == 查看者学校」判断（库内无学校实体表，
    只能文本比对 `sys_user.school_name`）；任一为空则不匹配——
    宁可看不到，也不要错误放行全校。
    """
    clauses = [Paper.share_scope == ShareScope.PUBLIC.value]
    if user.grade_id:
        clauses.append(and_(
            Paper.share_scope == ShareScope.GRADE.value,
            Paper.grade_id == user.grade_id,
        ))
    if user.school_name:
        creator_ids = select(User.id).where(User.school_name == user.school_name)
        clauses.append(and_(
            Paper.share_scope == ShareScope.SCHOOL.value,
            Paper.creator_id.in_(creator_ids),
        ))
    return or_(*clauses)


def _paper_visibility_clause(user: User):
    """可见性：sys_admin 全量；其他 = 本人 / 被显式分享 / 范围共享。"""
    if _is_sys_admin(user):
        return None
    return or_(
        Paper.creator_id == user.id,
        Paper.id.in_(select(PaperShare.paper_id).where(
            PaperShare.to_user_id == user.id)),
        _scope_clause(user),
    )


def _share_permission(db: Session, paper: Paper, user: User) -> Optional[str]:
    """当前用户对该卷的共享权限（view/reuse/edit）；无权限返回 None。

    优先级：创建者/管理员 = edit > 显式分享记录 > 范围共享（只读）。
    范围共享一律只读：同年级几十位教师都能改同一份卷子会互相破坏。
    """
    if _is_sys_admin(user) or paper.creator_id == user.id:
        return SharePermission.EDIT.value
    share = db.scalar(
        select(PaperShare).where(
            PaperShare.paper_id == paper.id, PaperShare.to_user_id == user.id)
    )
    if share:
        return share.permission or SharePermission.VIEW.value
    # 范围共享必须逐级校验归属，不能只看 share_scope 就放行
    if paper.share_scope == ShareScope.PUBLIC.value:
        return SharePermission.VIEW.value
    if paper.share_scope == ShareScope.GRADE.value and \
            user.grade_id and paper.grade_id == user.grade_id:
        return SharePermission.VIEW.value
    if paper.share_scope == ShareScope.SCHOOL.value and user.school_name:
        creator_school = db.scalar(
            select(User.school_name).where(User.id == paper.creator_id))
        if creator_school and creator_school == user.school_name:
            return SharePermission.VIEW.value
    return None


def _assert_readable(db: Session, paper: Paper, user: User) -> str:
    perm = _share_permission(db, paper, user)
    if not perm:
        raise PermissionException("无权查看该试卷")
    return perm


def _assert_can_edit(db: Session, paper: Paper, user: User) -> None:
    """编辑权：创建者 / sys_admin / 被授予 edit 的分享对象。"""
    perm = _share_permission(db, paper, user)
    if perm != SharePermission.EDIT.value:
        raise PermissionException("只能编辑自己创建的试卷，或经授权的共享试卷")


def _grade_subject(db: Session, grade_id: Any, subject_id: Any):
    try:
        gid = int(grade_id) if grade_id else 0
        sid = int(subject_id) if subject_id else 0
    except (TypeError, ValueError):
        raise BusinessException("请选择年级和学科")
    grade = db.get(Grade, gid) if gid else None
    subject = db.get(Subject, sid) if sid else None
    # 原实现未校验年级存在性，grade_id 不存在时 INSERT 触发 FK 约束 → 500。
    # 这里前置校验并给出可操作提示。
    if not grade:
        raise BusinessException("请选择有效的年级")
    if not subject:
        raise BusinessException("请选择有效的学科")
    if subject.grade_id != grade.id:
        raise BusinessException(
            f"学科「{subject.name}」不属于{grade.name}，请重新选择")
    return grade, subject


def _stage_of(grade: Grade) -> str:
    return grade.stage or ("primary" if (grade.grade_num or 1) <= 6 else "junior")


def _resolve_standard(
    db: Session, *, grade: Grade, subject: Subject, standard_id: Optional[int],
) -> Optional[ExamStandard]:
    """选定命题标准：显式指定 > 同学段学科默认 > 同学段学科任一启用标准。"""
    if standard_id:
        std = db.get(ExamStandard, int(standard_id))
        if not std:
            raise BusinessException("指定的命题标准不存在")
        if not std.is_active:
            raise BusinessException("指定的命题标准已停用")
        return std

    stage = _stage_of(grade)
    stmt = select(ExamStandard).where(
        ExamStandard.stage == stage,
        ExamStandard.subject_name == subject.name,
        ExamStandard.is_active.is_(True),
    )
    default = db.scalar(stmt.where(ExamStandard.is_default.is_(True)))
    if default:
        return default
    return db.scalar(stmt.order_by(ExamStandard.sort, ExamStandard.id))


# ---------------------------------------------------------------- 参数解析
def _parse_sections_input(raw: Any) -> Optional[List[Dict[str, Any]]]:
    """前端自定义题型结构：允许只给 code/count/score_per。"""
    if raw in (None, "", []):
        return None
    if not isinstance(raw, list):
        raise BusinessException("题型结构格式错误")
    result: List[Dict[str, Any]] = []
    for idx, item in enumerate(raw, start=1):
        if not isinstance(item, dict):
            raise BusinessException("题型结构格式错误")
        code = str(item.get("code") or item.get("type") or "").strip().lower()
        if code not in TYPE_LABEL:
            raise BusinessException(f"题型不合法：{code!r}")
        try:
            count = int(item.get("count") or 0)
            score_per = float(item.get("score_per") or 0)
        except (TypeError, ValueError):
            raise BusinessException("题型题量/分值必须为数字")
        if count <= 0:
            continue  # 题量 0 视为不需要该题型，忽略而非报错
        if score_per <= 0:
            raise BusinessException(f"题型「{TYPE_LABEL[code]}」单题分值必须大于 0")
        result.append({
            "code": code,
            "name": str(item.get("name") or TYPE_LABEL[code])[:64],
            "count": count,
            "score_per": round(score_per, 2),
            "difficulty": str(item.get("difficulty") or "medium"),
            "sort": idx,
        })
    return result or None


def _compose_from_payload(db: Session, user: User, data: Dict[str, Any]) -> Dict[str, Any]:
    """两种组卷模式共用的参数解析与引擎调用。"""
    grade, subject = _grade_subject(db, data.get("grade_id"), data.get("subject_id"))
    standard = _resolve_standard(
        db, grade=grade, subject=subject, standard_id=data.get("standard_id"))
    sections = _parse_sections_input(data.get("sections")) or compose_svc.parse_sections(standard)
    if not sections:
        raise BusinessException(
            "该学段学科暂未配置命题标准，请先在「命题标准」中配置，或手工指定题型结构")

    source_strategy = str(data.get("source") or compose_svc.SOURCE_BANK_FIRST).strip()
    if source_strategy not in compose_svc.VALID_SOURCES:
        raise BusinessException(f"出题来源仅支持 {'/'.join(sorted(compose_svc.VALID_SOURCES))}")

    kp_ids = data.get("knowledge_point_ids") or []
    if not isinstance(kp_ids, list):
        raise BusinessException("知识点参数格式错误")
    kp_ids = [int(k) for k in kp_ids if k]
    if kp_ids:
        # 知识点必须属于当前年级学科，否则抽题必然为空且无任何提示
        valid = set(db.scalars(
            select(KnowledgePoint.id).where(
                KnowledgePoint.id.in_(kp_ids),
                KnowledgePoint.grade_id == grade.id,
                KnowledgePoint.subject_id == subject.id,
            )).all())
        invalid = [k for k in kp_ids if k not in valid]
        if invalid:
            raise BusinessException(
                f"以下知识点不属于{grade.name}{subject.name}：{invalid}")

    difficulty = data.get("difficulty_ratio")
    try:
        difficulty_norm = compose_svc.normalize_difficulty(difficulty)
    except compose_svc.ComposeError as exc:
        raise BusinessException(str(exc))

    try:
        plan = compose_svc.compose(
            db,
            grade_id=grade.id, subject_id=subject.id,
            standard=standard, sections=sections,
            difficulty_ratio=difficulty_norm,
            kp_ids=kp_ids,
            source_strategy=source_strategy,
            avoid_recent=bool(data.get("avoid_recent", True)),
            recent_n=int(data.get("recent_n") or 3),
            avoid_duplicate_kp=bool(data.get("avoid_duplicate_kp", True)),
            exclude_paper_id=data.get("exclude_paper_id"),
            total_score_override=data.get("total_score") or None,
        )
    except compose_svc.ComposeError as exc:
        raise BusinessException(str(exc))

    reports = compose_svc.build_reports(plan.items, difficulty_norm, sections)
    return {
        "grade": grade, "subject": subject, "standard": standard,
        "sections": sections, "difficulty": difficulty_norm,
        "plan": plan, "reports": reports,
        "source_strategy": source_strategy, "kp_ids": kp_ids,
    }


def _plan_response(ctx: Dict[str, Any], *, ai_message: str = "") -> Dict[str, Any]:
    plan = ctx["plan"]
    std = ctx["standard"]
    body = {
        "grade_id": ctx["grade"].id, "grade_name": ctx["grade"].name,
        "subject_id": ctx["subject"].id, "subject_name": ctx["subject"].name,
        "standard_id": std.id if std else None,
        "standard_name": std.name if std else None,
        "exam_type": std.exam_type if std else None,
        "sections": ctx["sections"],
        "difficulty_ratio": ctx["difficulty"],
        "source": ctx["source_strategy"],
        "knowledge_point_ids": ctx["kp_ids"],
        **plan.to_dict(),
        **ctx["reports"],
        "suggested_duration": std.duration if std else 90,
        "standard_total_score": std.total_score if std else None,
    }
    if ai_message:
        body["message"] = ai_message
    return body


# ---------------------------------------------------------------- 组卷预览
@router.post("/compose/preview", summary="自定义参数组卷（预览，不落库）")
def compose_preview(
    data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    user: User = Depends(require_perm("paper:write")),
):
    """按年级/学科/知识点/题型/分值/难度抽题。

    返回完整预览 + 三份报告。**不写库**——教师确认后再调 `/compose/save`。
    """
    ctx = _compose_from_payload(db, user, data)
    return ok(_plan_response(ctx))


@router.post("/compose/ai", summary="AI 一键智能组卷")
def compose_ai(
    data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    user: User = Depends(require_perm("paper:ai")),
):
    """极简参数 + 自然语言 → 全卷。

    AI 只负责**把自然语言翻译成结构化参数**（年级/学科/题型/难度/知识点），
    实际抽题仍走确定性引擎。这样：
    - 模型抖动不会导致卷子结构乱掉（结构由命题标准保证）；
    - 解析失败时可完整降级到"按标准 + 默认难度"的纯规则组卷。

    若 `count` 未指定，自动采用命题标准的题量结构。
    """
    from app.agents.paper_agent import PaperComposerAgent

    request = str(data.get("request") or "").strip()
    if not request:
        raise BusinessException("请描述您的组卷需求")

    parsed: Dict[str, Any] = {}
    parse_error = ""
    if request:
        agent = PaperComposerAgent()
        try:
            res = agent.call_llm(
                request, db=db, user_id=user.id,
                biz_type="paper_parse", json_mode=True)
            if res.get("success") and isinstance(res.get("parsed"), dict):
                parsed = res["parsed"].get("params") or {}
            else:
                parse_error = res.get("reason") or res.get("message") or ""
        except Exception as exc:  # noqa: BLE001
            # AI 解析只是"翻译参数"，失败不该阻断组卷
            logger.warning("AI 组卷参数解析失败，降级为规则组卷: %s", exc)
            parse_error = str(exc)

    merged = dict(data)
    for key in ("grade_id", "subject_id", "standard_id", "difficulty_ratio",
                "knowledge_point_ids", "source", "total_score"):
        if not merged.get(key) and parsed.get(key):
            merged[key] = parsed[key]
    # AI 给的 sections 只在用户没指定时采用
    if not merged.get("sections") and parsed.get("sections"):
        merged["sections"] = parsed["sections"]
    # 题型分布（type_ratio）→ sections：AI 常用 {"single":10} 形式
    if not merged.get("sections") and parsed.get("type_ratio"):
        merged["sections"] = _type_ratio_to_sections(
            parsed["type_ratio"], merged.get("total_score") or 100)

    if not merged.get("grade_id") or not merged.get("subject_id"):
        raise BusinessException(
            "无法从描述中识别年级或学科，请明确指定" +
            (f"（AI 解析提示：{parse_error}）" if parse_error else ""))

    ctx = _compose_from_payload(db, user, merged)
    message = ""
    if parse_error:
        message = f"AI 参数解析未成功（{parse_error}），已按命题标准与默认难度组卷"
    return ok(_plan_response(ctx, ai_message=message))


def _type_ratio_to_sections(type_ratio: Any, total_score: float) -> List[Dict[str, Any]]:
    """把 {"single":10,"blank":5} 转成 sections（分值按题量均摊。

    **非法题型直接丢弃并记日志**——旧实现把 `fill`/`solve` 这类不在枚举里的
    key 静默忽略，导致"要求 10 题只出 4 题"且毫无提示。
    这里至少把丢弃行为写进日志，并在 sections 为空时由上层报错。
    """
    if not isinstance(type_ratio, dict):
        return []
    result: List[Dict[str, Any]] = []
    dropped: List[str] = []
    total_count = 0
    for code, qty in type_ratio.items():
        key = str(code or "").strip().lower()
        if key not in TYPE_LABEL:
            dropped.append(key)
            continue
        try:
            count = int(qty or 0)
        except (TypeError, ValueError):
            dropped.append(key)
            continue
        if count <= 0:
            continue
        result.append({"code": key, "name": TYPE_LABEL[key], "count": count,
                       "difficulty": "medium", "sort": len(result) + 1})
        total_count += count
    if dropped:
        logger.warning("AI 返回了非法题型，已丢弃：%s（合法值 %s）",
                       dropped, sorted(TYPE_LABEL))
    if not result or total_count <= 0:
        return []
    score_per = round(float(total_score) / total_count, 2)
    for s in result:
        s["score_per"] = score_per
    return result


@router.post("/compose/save", summary="保存组卷结果为新试卷")
def compose_save(
    data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    user: User = Depends(require_perm("paper:write")),
):
    """把预览结果落库。

    两种入参：
    1. 传 `items`（前端已编辑过的最终题目列表）→ 直接用；
    2. 不传 `items`，传组卷参数 → 重新跑一次引擎（服务端权威结果）。

    总分一律由题分求和，**忽略客户端 total_score**（防伪造，与既有口径一致）。
    """
    name = str(data.get("name") or "").strip()
    if not name:
        raise BusinessException("请填写试卷名称")
    if len(name) > 128:
        raise BusinessException("试卷名称不能超过 128 个字符")

    ctx = _compose_from_payload(db, user, data)

    items = data.get("items")
    if items is None:
        items = ctx["plan"].items
    if not isinstance(items, list) or not items:
        raise BusinessException("试卷没有题目，无法保存")

    # 复用 ctx 里的年级/学科做题目归属校验
    grade, subject = ctx["grade"], ctx["subject"]
    normalized = _normalize_items(db, user, items, grade.id, subject.id)
    total = round(sum(i["score"] for i in normalized), 2)

    std = ctx["standard"]
    paper = Paper(
        name=name, grade_id=grade.id, subject_id=subject.id,
        total_score=total,
        duration=int(data.get("duration") or (std.duration if std else 90)),
        difficulty_ratio=json.dumps(ctx["difficulty"], ensure_ascii=False),
        knowledge_coverage=json.dumps(
            ctx["reports"]["knowledge_report"], ensure_ascii=False),
        difficulty_report=json.dumps(
            ctx["reports"]["difficulty_report"], ensure_ascii=False),
        type_report=json.dumps(ctx["reports"]["type_report"], ensure_ascii=False),
        description=str(data.get("description") or "")[:2000] or None,
        exam_type=(std.exam_type if std else data.get("exam_type")),
        stage=_stage_of(grade),
        textbook_version=subject.textbook_version,
        standard_id=std.id if std else None,
        status=PaperStatus.DRAFT.value,
        share_scope=ShareScope.PRIVATE.value,
        generation_params=json.dumps({
            "mode": data.get("mode") or "custom",
            "source": ctx["source_strategy"],
            "sections": ctx["sections"],
            "difficulty_ratio": ctx["difficulty"],
            "knowledge_point_ids": ctx["kp_ids"],
            "standard_id": std.id if std else None,
            "avoid_recent": bool(data.get("avoid_recent", True)),
        }, ensure_ascii=False),
        creator_id=user.id,
        source="ai" if (data.get("mode") == "ai") else "manual",
        current_version=1,
    )
    db.add(paper)
    db.flush()
    _write_items(db, paper, normalized)
    # 初始版本快照：便于"改坏了回溯到刚组出来的样子"
    version_svc.snapshot(db, paper, user.id, change_note="组卷创建")
    db.commit()
    db.refresh(paper)
    return ok({
        "id": paper.id, "name": paper.name, "total_score": paper.total_score,
        "item_count": len(normalized), "version": paper.current_version,
        "gaps": ctx["plan"].gaps,
    }, message="试卷已保存")


# ---------------------------------------------------------------- 题目规范化
def _normalize_items(
    db: Session, user: User, raw_items: List[Any], grade_id: int, subject_id: int,
) -> List[Dict[str, Any]]:
    """校验并规范化题目列表。

    比旧实现多做的三件事：
    1. 去重（同一题不能在一卷里出现两次）；
    2. 校验题目年级/学科归属，避免跨学科混排；
    3. 保留 section_code / section_sort，让大题分组稳定（旧实现只存名称，
       改名就散架）。
    """
    seen: set = set()
    result: List[Dict[str, Any]] = []
    for idx, raw in enumerate(raw_items, start=1):
        if not isinstance(raw, dict):
            raise BusinessException(f"第 {idx} 道题目数据格式错误")
        try:
            qid = int(raw.get("question_id") or raw.get("id"))
        except (TypeError, ValueError):
            raise BusinessException(f"第 {idx} 道题目的 question_id 无效")
        if qid in seen:
            raise BusinessException(f"试卷中题目重复（question_id={qid}）")
        seen.add(qid)
        q = db.get(Question, qid)
        if not q:
            raise BusinessException(f"题目不存在或已删除（id={qid}）")
        if not _is_sys_admin(user) and not (
                q.bank_type == "public" or q.owner_id == user.id):
            raise BusinessException(f"无权使用题目（id={qid}）：仅可选公共题或本人私有题")
        if q.grade_id != grade_id or q.subject_id != subject_id:
            raise BusinessException(f"题目年级/学科与试卷不一致（id={qid}）")

        try:
            score = float(raw.get("score") if raw.get("score") is not None else (q.score or 5))
        except (TypeError, ValueError):
            raise BusinessException(f"题目分值必须为数字（id={qid}）")
        if score < 0 or score > 1000:
            raise BusinessException(f"题目分值需在 0~1000 之间（id={qid}）")

        result.append({
            "question_id": qid,
            "score": round(score, 2),
            "type": q.type,
            "section_code": str(raw.get("section_code") or q.type)[:32],
            "section_name": str(raw.get("section_name") or TYPE_LABEL.get(q.type, "综合题"))[:64],
            "section_sort": int(raw.get("section_sort") or 0),
            "score_override": bool(raw.get("score_override", False)),
        })
    return result


def _write_items(db: Session, paper: Paper, items: List[Dict[str, Any]],
                 *, migrate_answers: bool = True) -> Dict[str, int]:
    """写入题项（插入新 → 迁移作答 → 删旧），并重排大题序号。

    **顺序至关重要**：`Answer.paper_item_id` 是 ON DELETE CASCADE。
    旧实现直接 `DELETE FROM edu_paper_item` 再插新行，学生的作答会随旧题项
    一起被数据库级联清空（实测一份卷 80 条作答、920 分全部归零）。
    正确顺序是：
      1. 记下旧题项 id（question_id → [item_id]）
      2. 插入新题项（拿到新 id）
      3. 把旧作答的 paper_item_id 改指向新题项（按 question_id 对应）
      4. 最后才删除旧题项——此时已无作答指向它们，级联删除无害

    返回 `{"migrated": 保住的作答数, "dropped": 随题目移除而作废的作答数}`。
    **被移除题目的作答无法保留**：`paper_item_id` 非空且 CASCADE，
    题项删除后作答必然被级联清除。这里不假装保住，而是如实计数上报，
    让调用方能告诉教师「这次修改作废了 N 条作答」。
    """
    # 1) 旧题项快照：question_id → 旧 item id 列表
    old_rows = db.execute(
        select(PaperItem.id, PaperItem.question_id).where(
            PaperItem.paper_id == paper.id)
    ).all()
    old_by_question: Dict[int, List[int]] = {}
    for item_id, qid in old_rows:
        old_by_question.setdefault(int(qid), []).append(int(item_id))
    old_ids = [r[0] for r in old_rows]

    # 2) 插入新题项
    compose_svc._renumber(items)
    new_map: Dict[int, int] = {}   # question_id → 新 item id
    for idx, it in enumerate(items, start=1):
        row = PaperItem(
            paper_id=paper.id, question_id=it["question_id"],
            sort_order=idx, score=it["score"],
            section_name=it.get("section_name"),
            section_code=it.get("section_code"),
            section_sort=it.get("section_sort") or 0,
            score_override=bool(it.get("score_override", False)),
        )
        db.add(row)
        db.flush()
        new_map[int(it["question_id"])] = int(row.id)
        q = db.get(Question, it["question_id"])
        if q:
            q.usage_count += 1

    # 3) 迁移作答：把旧 item 上的 Answer 改挂到同 question_id 的新 item
    migrated = 0
    dropped = 0
    if migrate_answers and old_ids:
        for qid, new_item_id in new_map.items():
            for old_item_id in old_by_question.get(qid, []):
                if old_item_id == new_item_id:
                    continue
                res = db.execute(
                    Answer.__table__.update()
                    .where(Answer.paper_item_id == old_item_id)
                    .values(paper_item_id=new_item_id)
                )
                migrated += res.rowcount or 0
        # 未能迁移的（题目已被移除）：作答即将随旧题项级联删除，先计数
        kept_new_ids = set(new_map.values())
        orphans = [i for i in old_ids if i not in kept_new_ids]
        if orphans:
            dropped = int(db.scalar(
                select(func.count()).select_from(Answer)
                .where(Answer.paper_item_id.in_(orphans))) or 0)
        db.flush()

    # 4) 删除旧题项（此时已无作答指向，级联删除安全）
    if old_ids:
        db.execute(PaperItem.__table__.delete().where(PaperItem.id.in_(old_ids)))
        db.flush()

    paper.total_score = round(sum(float(i["score"]) for i in items), 2)
    return {"migrated": migrated, "dropped": dropped}


# ---------------------------------------------------------------- 预览 / 编辑
@router.get("/{paper_id}/preview", summary="试卷预览（按大题分组，含答案解析）")
def preview_paper(
    paper_id: int, mode: str = Query("teacher", pattern="^(teacher|student)$"),
    db: Session = Depends(get_db),
    user: User = Depends(require_perm("paper:list")),
):
    """整卷预览。`mode=student` 不返回答案与解析（学生卷/教师卷双版本）。"""
    paper = db.get(Paper, paper_id)
    if not paper:
        raise NotFoundException("试卷不存在")
    _assert_readable(db, paper, user)
    return ok(_build_preview(db, paper, mode=mode))


def _build_preview(db: Session, paper: Paper, *, mode: str = "teacher") -> Dict[str, Any]:
    grade = db.get(Grade, paper.grade_id)
    subject = db.get(Subject, paper.subject_id)

    # 按 section_code 归组（缺失时回落到题型），保持 section_sort 顺序
    groups: Dict[str, Dict[str, Any]] = {}
    order: List[str] = []
    for it in sorted(paper.items, key=lambda x: (x.section_sort or 0, x.sort_order or 0)):
        q = it.question
        if not q:
            continue
        code = it.section_code or q.type
        if code not in groups:
            groups[code] = {
                "section_code": code,
                "section_name": it.section_name or TYPE_LABEL.get(code, "综合题"),
                "section_sort": it.section_sort or 0,
                "items": [],
            }
            order.append(code)
        kp = db.get(KnowledgePoint, q.knowledge_point_id) if q.knowledge_point_id else None
        entry = {
            "paper_item_id": it.id,
            "question_id": q.id,
            "sort_order": it.sort_order,
            "score": it.score,
            "type": q.type,
            "type_label": TYPE_LABEL.get(q.type, q.type),
            "difficulty": q.difficulty,
            "difficulty_label": {"easy": "简单", "medium": "中等", "hard": "困难"}.get(
                q.difficulty, q.difficulty),
            "stem": q.stem,
            "options": _load_json(q.options),
            "knowledge_point_id": q.knowledge_point_id,
            "knowledge_point_name": kp.name if kp else None,
        }
        if mode == "teacher":
            entry["answer"] = _load_json(q.answer)
            entry["analysis"] = q.analysis
        groups[code]["items"].append(entry)

    sections = [groups[c] for c in order]
    for idx, sec in enumerate(sections, start=1):
        sec["section_index"] = idx
        sec["item_count"] = len(sec["items"])
        sec["section_score"] = round(sum(float(i["score"]) for i in sec["items"]), 2)

    d = dictify(paper)
    d.update({
        "grade_name": grade.name if grade else None,
        "subject_name": subject.name if subject else None,
        "stage": paper.stage or (_stage_of(grade) if grade else None),
        "sections": sections,
        "item_count": sum(s["item_count"] for s in sections),
        "score_sum": round(sum(float(i["score"]) for s in sections for i in s["items"]), 2),
        "mode": mode,
        "difficulty_report": _load_json(paper.difficulty_report),
        "knowledge_coverage": _load_json(paper.knowledge_coverage),
        "type_report": _load_json(paper.type_report),
        "generation_params": _load_json(paper.generation_params),
        "creator_name": db.scalar(select(User.real_name).where(User.id == paper.creator_id)),
    })
    return d


def _load_json(value: Optional[str]) -> Any:
    if not value:
        return None
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return value


@router.post("/{paper_id}/items", summary="保存题目列表（增删/排序/改分）")
def update_items(
    paper_id: int, data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    user: User = Depends(require_perm("paper:write")),
):
    """整卷题目覆盖写。

    **被任务引用时会重算成绩**（用户决策：允许改并重算）。
    重算口径：按 question_id 匹配旧题项 → 保留学生作答（Answer 迁移到新 paper_item_id）
    → 按新分值重算主观题得分与提交总分。
    题目被移除时，其作答随题项级联删除（`paper_item_id` 非空 FK），
    返回值里的 `dropped_answers` 如实上报作废条数，前端需提示教师。
    """
    paper = db.get(Paper, paper_id)
    if not paper:
        raise NotFoundException("试卷不存在")
    _assert_can_edit(db, paper, user)

    raw_items = data.get("items")
    items = _normalize_items(db, user, raw_items, paper.grade_id, paper.subject_id)
    if not items:
        raise BusinessException("请至少保留一道题目")

    # 快照：改之前先存一份，便于回溯
    version_svc.snapshot(db, paper, user.id, change_note="编辑题目")

    # 顺序不可颠倒：_write_items 负责「插新→迁移作答→删旧」，
    # 必须先把作答迁移到新题项，之后才能按新分值重算（否则算的是已删的行）。
    write_stat = _write_items(db, paper, items)
    affected = _recalculate_after_change(db, paper, items)
    if "name" in data:
        name = str(data.get("name") or "").strip()
        if not name:
            raise BusinessException("试卷名称不能为空")
        paper.name = name[:128]
    if "description" in data:
        paper.description = str(data.get("description") or "")[:2000] or None
    if "duration" in data:
        try:
            paper.duration = max(1, min(300, int(data.get("duration"))))
        except (TypeError, ValueError):
            raise BusinessException("考试时长必须为整数")

    paper.current_version = (paper.current_version or 1) + 1
    version_svc.snapshot(db, paper, user.id, change_note="编辑完成")
    db.commit()
    msg = "试卷已更新"
    if write_stat.get("dropped"):
        msg += f"；移除的题目导致 {write_stat['dropped']} 条学生作答被作废"
    return ok({
        "id": paper.id, "total_score": paper.total_score,
        "item_count": len(items), "version": paper.current_version,
        "dropped_answers": write_stat.get("dropped", 0),
        **affected,
    }, message=msg)


def _recalculate_after_change(
    db: Session, paper: Paper, new_items: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """按新分值重算受影响提交的成绩。

    前提：作答已由 `_write_items` 迁移到新题项（paper_item_id 已指向新行）。
    本函数只负责「改分」与「重算总分」，不碰题项增删——职责单一，
    避免和迁移逻辑互相覆盖（曾经两处都做删除，导致顺序一错就清空数据）。
    """
    task_ids = [r for r in db.scalars(
        select(Task.id).where(Task.paper_id == paper.id)).all()]
    if not task_ids:
        return {"affected_submissions": 0, "recalculated": False}

    submission_ids = [r for r in db.scalars(
        select(Submission.id).where(Submission.task_id.in_(task_ids))).all()]
    if not submission_ids:
        return {"affected_submissions": 0, "recalculated": False}

    # 当前卷的题项 → 新分值（按 paper_item_id 索引，因为作答已挂到新行）
    rows = db.execute(
        select(PaperItem.id, PaperItem.question_id).where(
            PaperItem.paper_id == paper.id)
    ).all()
    score_by_q = {int(i["question_id"]): float(i["score"]) for i in new_items}

    rescored = 0
    for item_id, qid in rows:
        new_full = score_by_q.get(int(qid))
        if new_full is None:
            continue
        answers = db.scalars(
            select(Answer).where(Answer.paper_item_id == int(item_id))).all()
        for ans in answers:
            old_full = float(ans.full_score or 0)
            got = float(ans.score or 0)
            ans.full_score = new_full
            if ans.is_correct is True:
                # 客观题：对就满分
                ans.score = new_full
            elif ans.is_correct is False:
                ans.score = 0
            elif old_full > 0:
                # 主观题：按得分率折算，保留教师给的相对评价
                ans.score = round(new_full * (got / old_full), 2)
            else:
                ans.score = 0
            rescored += 1
    db.flush()

    # 重算每份提交的总分与及格标记
    for sub_id in submission_ids:
        sub = db.get(Submission, sub_id)
        if not sub:
            continue
        total = round(sum(float(a.score or 0) for a in sub.answers), 2)
        sub.score = total
        task = db.get(Task, sub.task_id)
        if task and task.total_score:
            sub.is_passed = total >= float(task.pass_score or 0)

    return {
        "affected_submissions": len(submission_ids),
        "recalculated": True,
        "rescored_answers": rescored,
    }


@router.post("/{paper_id}/items/{item_id}/regenerate", summary="AI 重新生成单题")
def regenerate_item(
    paper_id: int, item_id: int, data: Dict[str, Any] = Body(default={}),
    db: Session = Depends(get_db),
    user: User = Depends(require_perm("paper:ai")),
):
    """替换单题为 AI 新生成的同题型同难度题目。

    返回**新的 question_id 与题干**，由前端确认后再调 `/items` 保存，
    避免"点一下就自动改卷"的误操作。
    """
    paper = db.get(Paper, paper_id)
    if not paper:
        raise NotFoundException("试卷不存在")
    _assert_can_edit(db, paper, user)

    item = db.get(PaperItem, item_id)
    if not item or item.paper_id != paper_id:
        raise NotFoundException("题目项不存在")
    old = item.question
    if not old:
        raise BusinessException("原题目已被删除，无法参考生成")

    from app.agents.question_agent import QuestionGeneratorAgent

    kp_id = old.knowledge_point_id
    agent = QuestionGeneratorAgent()
    res = agent.run(
        db, user_id=user.id, grade_id=paper.grade_id, subject_id=paper.subject_id,
        count=1, difficulty=old.difficulty, qtype=old.type,
        knowledge_point_id=kp_id, save=True,
    )
    data_ = res.get("data") or {}
    questions = data_.get("questions") or []
    if not questions:
        raise BusinessException(
            "AI 生成未成功：" + (res.get("message") or "请检查模型配置后重试"))

    q = questions[0]
    new_qid = q.get("id") or q.get("question_id")
    if not new_qid:
        raise BusinessException("AI 生成成功但未落库，请检查题库权限配置")
    # 回读落库后的完整题目：agent 返回的 dict 字段不全（可能缺 options/answer/解析），
    # 前端要拿这些字段直接渲染替换后的题面，缺了就只能显示空白。
    new_q = db.get(Question, int(new_qid))
    kp_name = None
    if new_q and new_q.knowledge_point_id:
        kp_name = db.scalar(
            select(KnowledgePoint.name).where(KnowledgePoint.id == new_q.knowledge_point_id))
    return ok({
        "old_question_id": old.id,
        "question_id": int(new_qid),
        "stem": new_q.stem if new_q else q.get("stem"),
        "type": new_q.type if new_q else q.get("type"),
        "difficulty": new_q.difficulty if new_q else q.get("difficulty"),
        "options": _load_json(new_q.options) if new_q else q.get("options"),
        "answer": _load_json(new_q.answer) if new_q else q.get("answer"),
        "analysis": new_q.analysis if new_q else q.get("analysis"),
        "knowledge_point_name": kp_name,
        "score": item.score,
        "section_code": item.section_code,
        "section_name": item.section_name,
        "is_fallback": bool(data_.get("is_fallback")),
    }, message="已生成替换题目，确认后保存")


@router.delete("/{paper_id}/items/{item_id}", summary="移除单题")
def remove_item(
    paper_id: int, item_id: int, db: Session = Depends(get_db),
    user: User = Depends(require_perm("paper:write")),
):
    paper = db.get(Paper, paper_id)
    if not paper:
        raise NotFoundException("试卷不存在")
    _assert_can_edit(db, paper, user)
    item = db.get(PaperItem, item_id)
    if not item or item.paper_id != paper_id:
        raise NotFoundException("题目项不存在")
    if len(paper.items) <= 1:
        raise BusinessException("试卷至少保留一道题目")

    version_svc.snapshot(db, paper, user.id, change_note="移除题目")
    db.delete(item)
    db.flush()
    # 重排剩余题项，避免 sort_order 出现空洞
    remaining = [it for it in paper.items if it.id != item_id]
    items = [{
        "question_id": it.question_id, "score": it.score,
        "section_code": it.section_code, "section_name": it.section_name,
        "section_sort": it.section_sort,
    } for it in remaining]
    db.flush()
    paper.total_score = round(sum(float(i["score"]) for i in items), 2)
    paper.current_version = (paper.current_version or 1) + 1
    version_svc.snapshot(db, paper, user.id, change_note="移除题目完成")
    db.commit()
    return ok({"id": paper.id, "total_score": paper.total_score,
               "item_count": len(items)}, message="题目已移除")


@router.post("/{paper_id}/sections/rename", summary="大题改名")
def rename_section(
    paper_id: int, data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    user: User = Depends(require_perm("paper:write")),
):
    """按 section_code 批量改大题名（改名不打散分组）。"""
    paper = db.get(Paper, paper_id)
    if not paper:
        raise NotFoundException("试卷不存在")
    _assert_can_edit(db, paper, user)

    code = str(data.get("section_code") or "").strip()
    name = str(data.get("section_name") or "").strip()
    if not code:
        raise BusinessException("请指定大题标识 section_code")
    if not name:
        raise BusinessException("大题名称不能为空")

    rows = [it for it in paper.items if (it.section_code or it.question.type) == code]
    if not rows:
        raise BusinessException("该大题不存在")
    for it in rows:
        it.section_name = name[:64]
    paper.current_version = (paper.current_version or 1) + 1
    db.commit()
    return ok({"section_code": code, "section_name": name[:64],
               "affected": len(rows)}, message="大题名称已更新")


@router.post("/{paper_id}/restructure", summary="一键重构大题结构")
def restructure_paper(
    paper_id: int, data: Dict[str, Any] = Body(default={}),
    db: Session = Depends(get_db),
    user: User = Depends(require_perm("paper:write")),
):
    """按题型重新归组并重排大题序号。

    适用场景：教师增删题目后，大题编号错乱 / 同名大题分裂成多个。
    只调整分组与序号，**不改题目内容与分值**。
    """
    paper = db.get(Paper, paper_id)
    if not paper:
        raise NotFoundException("试卷不存在")
    _assert_can_edit(db, paper, user)

    items = [{
        "question_id": it.question_id, "score": it.score,
        "section_code": it.section_code or (it.question.type if it.question else "single"),
        "section_name": it.section_name
        or TYPE_LABEL.get(it.question.type if it.question else "single", "综合题"),
        "section_sort": it.section_sort or 0,
        "score_override": it.score_override,
    } for it in paper.items]

    # 以标准大题名重建（若指定了标准）
    standard = db.get(ExamStandard, paper.standard_id) if paper.standard_id else None
    sec_names = {s["code"]: s["name"] for s in compose_svc.parse_sections(standard)}
    for it in items:
        code = it["section_code"]
        if code in sec_names:
            it["section_name"] = sec_names[code]

    version_svc.snapshot(db, paper, user.id, change_note="重构前")
    compose_svc._renumber(items)
    for it_row, it in zip(
        sorted(paper.items, key=lambda x: (x.section_sort or 0, x.sort_order or 0)), items):
        it_row.section_name = it["section_name"]
        it_row.section_code = it["section_code"]
        it_row.section_sort = it["section_sort"]
        it_row.sort_order = it["sort_order"]

    paper.current_version = (paper.current_version or 1) + 1
    version_svc.snapshot(db, paper, user.id, change_note="重构完成")
    db.commit()
    return ok({"sections": sorted({i["section_name"] for i in items}),
               "version": paper.current_version}, message="大题结构已重构")


# ---------------------------------------------------------------- 版本
@router.get("/{paper_id}/versions", summary="版本列表")
def list_versions(
    paper_id: int, db: Session = Depends(get_db),
    user: User = Depends(require_perm("paper:list")),
):
    paper = db.get(Paper, paper_id)
    if not paper:
        raise NotFoundException("试卷不存在")
    _assert_readable(db, paper, user)
    rows = db.scalars(
        select(PaperVersion).where(PaperVersion.paper_id == paper_id)
        .order_by(PaperVersion.version.desc())).all()
    return ok({
        "current_version": paper.current_version,
        "items": [{
            "id": v.id, "version": v.version, "change_note": v.change_note,
            "item_count": v.item_count, "total_score": v.total_score,
            "created_at": v.created_at,
            "created_by_name": db.scalar(
                select(User.real_name).where(User.id == v.created_by)),
        } for v in rows],
    })


@router.get("/{paper_id}/versions/{version}", summary="版本详情")
def get_version(
    paper_id: int, version: int, db: Session = Depends(get_db),
    user: User = Depends(require_perm("paper:list")),
):
    paper = db.get(Paper, paper_id)
    if not paper:
        raise NotFoundException("试卷不存在")
    _assert_readable(db, paper, user)
    row = db.scalar(select(PaperVersion).where(
        PaperVersion.paper_id == paper_id, PaperVersion.version == version))
    if not row:
        raise NotFoundException("版本不存在")
    return ok({
        "version": row.version, "change_note": row.change_note,
        "created_at": row.created_at,
        "snapshot": _load_json(row.snapshot),
    })


@router.post("/{paper_id}/versions/{version}/restore", summary="回溯到指定版本")
def restore_version(
    paper_id: int, version: int, db: Session = Depends(get_db),
    user: User = Depends(require_perm("paper:write")),
):
    """把试卷恢复到历史版本。

    回溯本身也产生一个新版本（不改历史），符合"版本只增不改"的原则。
    题库中已删除的题目会被跳过并如实报告，不会静默丢题。
    """
    paper = db.get(Paper, paper_id)
    if not paper:
        raise NotFoundException("试卷不存在")
    _assert_can_edit(db, paper, user)

    row = db.scalar(select(PaperVersion).where(
        PaperVersion.paper_id == paper_id, PaperVersion.version == version))
    if not row:
        raise NotFoundException("版本不存在")
    snapshot = _load_json(row.snapshot) or {}
    raw_items = snapshot.get("items") or []

    version_svc.snapshot(db, paper, user.id, change_note=f"回溯前（v{version}）")

    restore_items: List[Dict[str, Any]] = []
    missing: List[int] = []
    for it in raw_items:
        qid = it.get("question_id")
        if not qid:
            continue
        if not db.get(Question, int(qid)):
            missing.append(int(qid))
            continue
        restore_items.append({
            "question_id": int(qid),
            "score": float(it.get("score") or 5),
            "section_code": it.get("section_code") or it.get("type"),
            "section_name": it.get("section_name"),
            "section_sort": int(it.get("section_sort") or 0),
            "score_override": bool(it.get("score_override", False)),
        })
    if not restore_items:
        raise BusinessException("该版本的题目在题库中已全部删除，无法回溯")

    _write_items(db, paper, restore_items)
    paper_data = snapshot.get("paper") or {}
    if paper_data.get("name"):
        paper.name = str(paper_data["name"])[:128]
    if paper_data.get("duration"):
        paper.duration = int(paper_data["duration"])
    paper.current_version = (paper.current_version or 1) + 1
    version_svc.snapshot(db, paper, user.id, change_note=f"回溯到 v{version}")
    db.commit()
    body = {"id": paper.id, "restored_from": version,
            "current_version": paper.current_version,
            "item_count": len(restore_items)}
    if missing:
        body["missing_question_ids"] = missing
        body["warning"] = f"{len(missing)} 道题在题库中已删除，已跳过"
    return ok(body, message=f"已回溯到版本 v{version}")


# ---------------------------------------------------------------- 试卷库
@router.get("/library/list", summary="试卷库（我的/共享/公共/收藏）")
def paper_library(
    params: PageParams = Depends(),
    scope: str = Query("mine", pattern="^(mine|shared|public|favorite)$"),
    grade_id: Optional[int] = None,
    subject_id: Optional[int] = None,
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_perm("paper:list")),
):
    """三类目录 + 收藏。

    - mine：我创建的
    - shared：别人共享给我的（含范围共享）
    - public：公共库（审核通过的）
    - favorite：我收藏的
    """
    stmt = select(Paper)
    if scope == "mine":
        stmt = stmt.where(Paper.creator_id == user.id)
    elif scope == "shared":
        stmt = stmt.where(Paper.creator_id != user.id).where(or_(
            Paper.id.in_(select(PaperShare.paper_id).where(
                PaperShare.to_user_id == user.id)),
            Paper.share_scope.in_([ShareScope.GRADE.value, ShareScope.SCHOOL.value]),
        ))
    elif scope == "public":
        stmt = stmt.where(
            Paper.share_scope == ShareScope.PUBLIC.value,
            Paper.status == PaperStatus.PUBLISHED.value,
        )
    else:  # favorite
        stmt = stmt.where(Paper.id.in_(
            select(PaperFavorite.paper_id).where(PaperFavorite.user_id == user.id)))

    if grade_id:
        stmt = stmt.where(Paper.grade_id == grade_id)
    if subject_id:
        stmt = stmt.where(Paper.subject_id == subject_id)
    if keyword:
        stmt = stmt.where(Paper.name.like(f"%{keyword}%"))
    if status:
        stmt = stmt.where(Paper.status == status)

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(
        stmt.options(noload(Paper.items))
        .order_by(Paper.updated_at.desc(), Paper.id.desc())
        .offset(params.offset).limit(params.page_size)).all()

    ids = [p.id for p in rows]
    counts = dict(db.execute(
        select(PaperItem.paper_id, func.count()).where(PaperItem.paper_id.in_(ids))
        .group_by(PaperItem.paper_id)).all()) if ids else {}
    fav = set(db.scalars(
        select(PaperFavorite.paper_id).where(
            PaperFavorite.user_id == user.id, PaperFavorite.paper_id.in_(ids))
    ).all()) if ids else set()

    grade_names = {g.id: g.name for g in db.scalars(
        select(Grade).where(Grade.id.in_({p.grade_id for p in rows}))).all()} if rows else {}
    subject_names = {s.id: s.name for s in db.scalars(
        select(Subject).where(Subject.id.in_({p.subject_id for p in rows}))).all()} if rows else {}
    creator_names = {u.id: u.real_name for u in db.scalars(
        select(User).where(User.id.in_({p.creator_id for p in rows}))).all()} if rows else {}

    items = []
    for p in rows:
        d = dictify(p)
        d.update({
            "item_count": counts.get(p.id, 0),
            "grade_name": grade_names.get(p.grade_id),
            "subject_name": subject_names.get(p.subject_id),
            "creator_name": creator_names.get(p.creator_id),
            "is_favorite": p.id in fav,
            "is_mine": p.creator_id == user.id,
            "ai_source": (p.source or "").startswith("ai"),
        })
        items.append(d)
    return ok({"items": items, "total": total, "page": params.page, "scope": scope})


@router.post("/{paper_id}/favorite", summary="收藏/取消收藏")
def toggle_favorite(
    paper_id: int, data: Dict[str, Any] = Body(default={}),
    db: Session = Depends(get_db),
    user: User = Depends(require_perm("paper:list")),
):
    paper = db.get(Paper, paper_id)
    if not paper:
        raise NotFoundException("试卷不存在")
    _assert_readable(db, paper, user)

    exists = db.scalar(select(PaperFavorite).where(
        PaperFavorite.paper_id == paper_id, PaperFavorite.user_id == user.id))
    want = data.get("favorite")
    if want is None:
        want = exists is None

    if want and not exists:
        db.add(PaperFavorite(paper_id=paper_id, user_id=user.id))
        db.commit()
        return ok({"favorite": True}, message="已收藏")
    if not want and exists:
        db.delete(exists)
        db.commit()
        return ok({"favorite": False}, message="已取消收藏")
    return ok({"favorite": bool(exists)}, message="状态未变化")


# ---------------------------------------------------------------- 共享与审核
@router.post("/{paper_id}/share-scope", summary="设置共享范围（私有/年级/全校）")
def set_share_scope(
    paper_id: int, data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    user: User = Depends(require_perm("paper:write")),
):
    """设置试卷可见范围。

    - `private`：仅创建者
    - `grade`：同年级同学科教师（只读）
    - `school`：同校同学科教师（只读）
    - `public`：公共库全站可读——**不走这里**，必须经审核流
      （`/review` 提交 + 管理员 approve），否则等于绕过审核。

    范围共享一律只读；要给别人编辑权，用显式分享记录（`permission=edit`）。
    """
    paper = db.get(Paper, paper_id)
    if not paper:
        raise NotFoundException("试卷不存在")
    _assert_can_edit(db, paper, user)

    scope = str(data.get("scope") or "").strip().lower()
    if scope == ShareScope.PUBLIC.value:
        raise BusinessException(
            "公共库需走审核流程：先「提交审核」再由管理员通过，不能直接设为公开")
    if scope not in (ShareScope.PRIVATE.value, ShareScope.GRADE.value,
                     ShareScope.SCHOOL.value):
        raise BusinessException("scope 仅支持 private / grade / school")

    # 年级共享要求试卷本身有年级（Paper.grade_id 非空，建卷时已强制）
    if scope == ShareScope.GRADE.value and not paper.grade_id:
        raise BusinessException("该试卷未设置年级，无法按年级共享")
    if scope == ShareScope.SCHOOL.value and not user.school_name:
        raise BusinessException("当前账号未填写所属学校，无法按全校共享")

    paper.share_scope = scope
    paper.is_shared = scope != ShareScope.PRIVATE.value
    db.commit()
    label = {ShareScope.PRIVATE.value: "仅自己可见",
             ShareScope.GRADE.value: "同年级教师可查看",
             ShareScope.SCHOOL.value: "同校教师可查看"}[scope]
    return ok({"share_scope": paper.share_scope, "is_shared": paper.is_shared},
              message=f"共享范围已设为：{label}")


@router.get("/{paper_id}/share-info", summary="查看共享范围与协作者")
def share_info(
    paper_id: int, db: Session = Depends(get_db),
    user: User = Depends(require_perm("paper:list")),
):
    paper = db.get(Paper, paper_id)
    if not paper:
        raise NotFoundException("试卷不存在")
    _assert_readable(db, paper, user)
    rows = db.scalars(
        select(PaperShare).where(PaperShare.paper_id == paper_id)).all()
    names = dict(db.execute(
        select(User.id, User.real_name).where(
            User.id.in_([r.to_user_id for r in rows]))).all()) if rows else {}
    return ok({
        "share_scope": paper.share_scope or ShareScope.PRIVATE.value,
        "can_edit": _share_permission(db, paper, user) == SharePermission.EDIT.value,
        "members": [{
            "user_id": r.to_user_id,
            "name": names.get(r.to_user_id),
            "permission": r.permission or SharePermission.VIEW.value,
        } for r in rows],
    })


@router.post("/{paper_id}/review", summary="提交审核 / 审核通过 / 驳回")
def review_paper(
    paper_id: int, data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    user: User = Depends(require_perm("paper:write")),
):
    """公共库审核流。

    action:
    - submit：教师申请进公共库（draft/published → pending）
    - approve：管理员通过（pending → published，share_scope=public）
    - reject：管理员驳回（pending → rejected），需给意见
    """
    paper = db.get(Paper, paper_id)
    if not paper:
        raise NotFoundException("试卷不存在")
    action = str(data.get("action") or "").strip().lower()
    if action not in ("submit", "approve", "reject"):
        raise BusinessException("action 仅支持 submit / approve / reject")

    if action == "submit":
        _assert_can_edit(db, paper, user)
        if paper.status == PaperStatus.PENDING.value:
            raise BusinessException("该试卷已在审核中，请等待审核结果")
        if paper.share_scope == ShareScope.PUBLIC.value and \
                paper.status == PaperStatus.PUBLISHED.value:
            raise BusinessException("该试卷已进入公共库")
        paper.status = PaperStatus.PENDING.value
        paper.review_comment = None
        db.commit()
        return ok({"status": paper.status}, message="已提交审核")

    if not _is_sys_admin(user) and not _is_grade_admin(user):
        raise PermissionException("仅管理员可审核试卷")
    if paper.status != PaperStatus.PENDING.value:
        raise BusinessException("该试卷不在待审核状态")

    paper.review_by = user.id
    paper.review_at = __import__("app.utils.common", fromlist=["now_local"]).now_local()
    if action == "approve":
        paper.status = PaperStatus.PUBLISHED.value
        paper.share_scope = ShareScope.PUBLIC.value
        paper.is_shared = True
        db.commit()
        return ok({"status": paper.status, "share_scope": paper.share_scope},
                  message="审核通过，已进入公共库")
    comment = str(data.get("comment") or "").strip()
    if not comment:
        raise BusinessException("驳回时必须填写审核意见")
    paper.status = PaperStatus.REJECTED.value
    paper.review_comment = comment[:2000]
    db.commit()
    return ok({"status": paper.status, "review_comment": paper.review_comment},
              message="已驳回")


# ---------------------------------------------------------------- 导出
def _requested_export(db: Session, paper_id: int, user: User) -> Paper:
    paper = db.get(Paper, paper_id)
    if not paper:
        raise NotFoundException("试卷不存在")
    _assert_readable(db, paper, user)
    return paper


@router.get("/{paper_id}/export/docx", summary="导出 Word（教师卷/学生卷）")
def export_docx(
    paper_id: int,
    mode: str = Query("teacher", pattern="^(teacher|student)$"),
    layout: str = Query("a4_single", pattern="^(a3_double|a4_single)$"),
    with_seal_line: bool = True,
    with_page_number: bool = True,
    db: Session = Depends(get_db),
    user: User = Depends(require_perm("paper:export")),
):
    paper = _requested_export(db, paper_id, user)
    preview = _build_preview(db, paper, mode=mode)
    buf = build_docx(preview, mode=mode, layout=layout,
                     with_seal_line=with_seal_line, with_page_number=with_page_number)
    fname = f"paper_{paper_id}_{mode}.docx"
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename={fname}"},
    )


@router.get("/{paper_id}/export/pdf", summary="导出 PDF（教师卷/学生卷）")
def export_pdf(
    paper_id: int,
    mode: str = Query("teacher", pattern="^(teacher|student)$"),
    layout: str = Query("a4_single", pattern="^(a3_double|a4_single)$"),
    with_seal_line: bool = True,
    with_page_number: bool = True,
    db: Session = Depends(get_db),
    user: User = Depends(require_perm("paper:export")),
):
    paper = _requested_export(db, paper_id, user)
    preview = _build_preview(db, paper, mode=mode)
    buf = build_pdf(preview, mode=mode, layout=layout,
                    with_seal_line=with_seal_line, with_page_number=with_page_number)
    fname = f"paper_{paper_id}_{mode}.pdf"
    return StreamingResponse(
        buf, media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={fname}"},
    )


@router.get("/{paper_id}/export/answer-sheet", summary="导出答题卡")
def export_answer_sheet(
    paper_id: int,
    layout: str = Query("a4_single", pattern="^(a3_double|a4_single)$"),
    db: Session = Depends(get_db),
    user: User = Depends(require_perm("paper:export")),
):
    paper = _requested_export(db, paper_id, user)
    preview = _build_preview(db, paper, mode="student")
    buf = build_answer_sheet(preview, layout=layout)
    return StreamingResponse(
        buf, media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=paper_{paper_id}_answersheet.pdf"},
    )


@router.get("/{paper_id}/export/html", summary="导出可打印 HTML")
def export_html(
    paper_id: int,
    mode: str = Query("teacher", pattern="^(teacher|student)$"),
    layout: str = Query("a4_single", pattern="^(a3_double|a4_single)$"),
    db: Session = Depends(get_db),
    user: User = Depends(require_perm("paper:export")),
):
    """HTML 预览版：不依赖 Word/PDF 引擎，浏览器直接打印。"""
    paper = _requested_export(db, paper_id, user)
    preview = _build_preview(db, paper, mode=mode)
    from app.services.paper_export_service import build_print_html
    html = build_print_html(preview, mode=mode, layout=layout)
    return StreamingResponse(
        io.BytesIO(html.encode("utf-8")), media_type="text/html; charset=utf-8",
        headers={"Content-Disposition": f"inline; filename=paper_{paper_id}.html"},
    )
