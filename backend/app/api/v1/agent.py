"""AI Agent 中心接口：统一编排 + 6 个专属 Agent + 调用日志。"""
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, Query
from sqlalchemy import desc, func, or_, select
from sqlalchemy.orm import Session

from app.agents.base import AGENT_REGISTRY, get_orchestrator
from app.agents.llm import is_available
from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.exception import BusinessException, NotFoundException
from app.models import AgentCallLog, User
from app.utils.common import PageParams, dictify, fail, ok

router = APIRouter(prefix="/agent", tags=["AI Agent 中心"])


# ---------------------------------------------------------------- 概览
@router.get("/list", summary="Agent 列表")
def list_agents(user: User = Depends(get_current_user)):
    orch = get_orchestrator()
    items = [
        {
            "name": a.name, "display_name": a.display_name,
            "description": a.description,
            "is_fallback": a.name == "router",
        }
        for a in AGENT_REGISTRY.values()
    ]
    return ok({
        "agents": items,
        "orchestrator_mode": orch.mode,
        "llm_enabled": is_available(),
        "llm_provider": None,
    })


@router.get("/status", summary="AI 引擎状态")
def agent_status(_: User = Depends(get_current_user)):
    from app.core.config import settings

    orch = get_orchestrator()
    from app.agents.rag import get_collection

    col = get_collection()
    return ok({
        "llm_enabled": is_available(),
        "provider": settings.LLM_PROVIDER,
        "model": settings.LLM_MODEL,
        "orchestrator_mode": orch.mode,
        "vector_db": "ChromaDB" if col else "SQL 降级检索",
        "agents": len(AGENT_REGISTRY),
        "tip": "" if is_available() else "未配置 LLM_API_KEY，所有 Agent 将使用规则引擎降级运行",
    })


# ---------------------------------------------------------------- 统一入口
@router.post("/chat", summary="AI 统一对话（自动路由）")
def chat(
    data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """一句话需求，自动路由到最合适的 Agent。"""
    request = data.get("message") or data.get("request")
    if not request:
        raise BusinessException("请输入你的需求")

    orch = get_orchestrator()
    result = orch.run(
        db, user_id=user.id, request=request,
        args={
            "grade_id": data.get("grade_id"), "subject_id": data.get("subject_id"),
            "student_id": user.id,
        },
    )

    if result.get("intent") == "chat" and not result.get("data"):
        # 兜底走答疑
        from app.agents.tutor_agent import TutorAgent

        r = TutorAgent().run(
            db, user_id=user.id, request=request,
            grade_id=data.get("grade_id"), subject_id=data.get("subject_id"),
            student_id=user.id,
        )
        result["data"] = r.get("data")
        result["agent"] = "tutor"

    return ok({
        "request": request,
        "intent": result.get("intent"),
        "agent": result.get("agent"),
        "answer": _extract_answer(result.get("data")),
        "data": result.get("data"),
        "is_fallback": result.get("is_fallback", False),
        "trace": result.get("trace"),
        "mode": result.get("mode"),
        "duration_ms": result.get("duration_ms"),
    })


def _extract_answer(data: Any) -> str:
    """从各 Agent 返回结构中提取可读文本。"""
    if not isinstance(data, dict):
        return str(data or "")
    for key in ("answer", "summary", "polished_content"):
        if data.get(key):
            return str(data[key])
    return ""


# ---------------------------------------------------------------- 专属 Agent
@router.post("/question-generator", summary="题库生成 Agent")
def question_generator(
    data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    from app.agents.question_agent import QuestionGeneratorAgent

    res = QuestionGeneratorAgent().run(
        db, user_id=user.id,
        grade_id=data.get("grade_id"), subject_id=int(data.get("subject_id", 0)),
        knowledge_point_id=data.get("knowledge_point_id"),
        question_type=data.get("type", "single"),
        count=int(data.get("count", 5)),
        difficulty=data.get("difficulty", "medium"),
        save=bool(data.get("save", False)),
    )
    # Agent 失败时 success=False / data=None —— 不能再用 ok() 包成 success=true，
    # 否则前端 res.data.data 必崩（典型契约漂移）
    if not res.get("success"):
        return fail(res.get("message", "题目生成失败"))
    return ok(res.get("data"), message=res.get("message", "生成完成"))


@router.post("/paper-composer", summary="智能组卷 Agent")
def paper_composer(
    data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    from app.agents.paper_agent import PaperComposerAgent

    res = PaperComposerAgent().run(
        db, user_id=user.id, request=data.get("request", ""),
        grade_id=data.get("grade_id"), subject_id=data.get("subject_id"),
        total_score=float(data.get("total_score", 100)),
        difficulty_ratio=data.get("difficulty_ratio"),
        type_ratio=data.get("type_ratio"),
        knowledge_point_ids=data.get("knowledge_point_ids"),
        paper_name=data.get("paper_name"),
        save=bool(data.get("save", False)),
    )
    if not res.get("success"):
        return fail(res.get("message", "组卷失败"))
    return ok(res.get("data"), message=res.get("message", "组卷完成"))


@router.post("/grading", summary="智能批改 Agent")
def agent_grading(
    data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    from app.agents.grading_agent import GradingAgent

    res = GradingAgent().run(db, user_id=user.id, items=data.get("items", []))
    if not res.get("success"):
        return fail(res.get("message", "批改失败"))
    return ok(res.get("data"), message="批改完成")


@router.post("/study-planner", summary="学习规划 Agent")
def study_planner(
    data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    from app.agents.study_agent import StudyPlannerAgent

    res = StudyPlannerAgent().run(
        db, user_id=user.id,
        student_id=data.get("student_id") or user.id,
        days=int(data.get("days", 7)),
        daily_minutes=int(data.get("daily_minutes", 90)),
    )
    if not res.get("success"):
        return fail(res.get("message", "学习规划失败"))
    return ok(res.get("data"), message=res.get("message", "规划完成"))


@router.post("/tutor", summary="答疑助教 Agent")
def tutor(
    data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    from app.agents.tutor_agent import TutorAgent

    # 兼容 message / question / question_text 三种入参：
    # 前端 AgentChat 与文档示例用 question，历史调用用 message，
    # 只认 message 会把问题整体丢弃，Agent 直接返回「请描述你的问题」。
    question = (
        data.get("message") or data.get("question")
        or data.get("question_text") or data.get("content") or ""
    ).strip()

    res = TutorAgent().run(
        db, user_id=user.id, request=question,
        grade_id=data.get("grade_id"), subject_id=data.get("subject_id"),
        student_id=user.id,
    )
    if not res.get("success"):
        return fail(res.get("message", "答疑失败"))
    return ok(res.get("data"), message=res.get("message", "解答完成"))


@router.post("/note-organizer", summary="笔记整理 Agent")
def note_organizer(
    data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    from app.agents.note_agent import NoteOrganizerAgent

    res = NoteOrganizerAgent().run(
        db, user_id=user.id,
        note_id=data.get("note_id"), content=data.get("content"),
        title=data.get("title"), save=bool(data.get("save", False)),
    )
    if not res.get("success"):
        return fail(res.get("message", "笔记整理失败"))
    return ok(res.get("data"), message=res.get("message", "整理完成"))


# ---------------------------------------------------------------- 调用日志
@router.get("/logs", summary="AI 调用日志")
def agent_logs(
    params: PageParams = Depends(), agent_name: Optional[str] = None,
    status: Optional[str] = None, db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # 权限：管理员看全部，学生只看自己的
    is_admin = {"sys_admin", "grade_admin"} & set(user.role_codes)
    stmt = select(AgentCallLog)
    if not is_admin:
        stmt = stmt.where(AgentCallLog.user_id == user.id)
    if agent_name:
        stmt = stmt.where(AgentCallLog.agent_name == agent_name)
    if status:
        stmt = stmt.where(AgentCallLog.status == status)

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(
        stmt.order_by(desc(AgentCallLog.created_at))
        .offset(params.offset).limit(params.page_size)
    ).all()

    stats = db.execute(
        select(
            func.count(),
            func.avg(AgentCallLog.duration_ms),
            func.sum(AgentCallLog.input_tokens),
            func.sum(AgentCallLog.output_tokens),
        ).select_from(AgentCallLog)
    ).one()

    by_agent = db.execute(
        select(AgentCallLog.agent_name, func.count()).group_by(AgentCallLog.agent_name)
    ).all()

    return ok({
        "items": [dictify(r) for r in rows], "total": total, "page": params.page,
        "summary": {
            "total_calls": stats[0] or 0,
            "avg_duration_ms": round(stats[1] or 0, 1),
            "input_tokens": stats[2] or 0,
            "output_tokens": stats[3] or 0,
        },
        "by_agent": {name: count for name, count in by_agent},
    })
