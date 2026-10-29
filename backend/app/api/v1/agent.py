"""AI Agent 中心接口：统一编排 + 6 个专属 Agent + 调用日志。"""
import json
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.agents.base import AGENT_REGISTRY, get_orchestrator
from app.agents.llm import _get_db_value, is_available
from app.api.deps import (
    get_current_student,
    get_current_teacher,
    get_current_user,
)
from app.core.config import settings
from app.core.database import get_db
from app.core.exception import BusinessException, NotFoundException, PermissionException
from app.core.rate_limit import check_agent_rate
from app.models import AgentCallLog, User
from app.utils.common import PageParams, dictify, fail, now_local, ok

import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent", tags=["AI Agent 中心"])

# 单次 Agent 调用超过该耗时记 warning，便于运维定位模型变慢/网络抖动
SLOW_CALL_MS = 20_000

# 入参上限（P1）：单请求会被放大成 N 次 LLM 往返 / 超大 prompt 打爆上下文与成本。
# 取值远大于正常使用（正常出题 ≤20、批改一份卷子 ≤50 题、需求描述几十字），
# 只拦截明显异常或恶意入参，不影响 E2E 与前端既有调用。
MAX_AGENT_ITEMS = 50
MAX_TEXT_CHARS = 8000


def _limited_text(value: Any, field: str, limit: int = MAX_TEXT_CHARS) -> str:
    """读取文本入参并校验长度，超限抛 BusinessException。"""
    text = str(value or "").strip()
    if len(text) > limit:
        raise BusinessException(
            f"{field}过长（{len(text)} 字符），请控制在 {limit} 字符以内")
    return text


def _limited_items(value: Any, field: str, limit: int = MAX_AGENT_ITEMS) -> List[Any]:
    """读取列表入参并校验元素数量，超限抛 BusinessException。"""
    if value is None:
        return []
    if not isinstance(value, list):
        raise BusinessException(f"{field}必须是数组")
    if len(value) > limit:
        raise BusinessException(f"{field}最多 {limit} 条，当前 {len(value)} 条")
    return value


def _limited_count(
    value: Any, default: int, limit: int = MAX_AGENT_ITEMS, field: str = "数量",
) -> int:
    """读取数量入参并校验范围 [1, limit]。"""
    try:
        count = int(value if value is not None else default)
    except (TypeError, ValueError):
        raise BusinessException(f"{field}必须是整数") from None
    if count < 1 or count > limit:
        raise BusinessException(f"{field}应在 1~{limit} 之间")
    return count


def _audit_write(db: Session, user: User, action: str, detail: str) -> None:
    """Agent 写库审计：save=True 属于「AI 直接改数据」的高风险操作。"""
    try:
        from app.models import OperationLog

        db.add(OperationLog(
            user_id=user.id, username=user.username,
            module="AI智能", action=action, method="POST",
            path="/api/v1/agent", params=detail[:1000], status="success",
        ))
        db.commit()
    except Exception:  # noqa: BLE001
        db.rollback()


def _warn_if_slow(res: dict, agent: str) -> None:
    ms = (res or {}).get("duration_ms") or 0
    if ms >= SLOW_CALL_MS:
        logger.warning("Agent %s 调用耗时 %.1fs（阈值 %.0fs）",
                       agent, ms / 1000, SLOW_CALL_MS / 1000)


def _llm_runtime_config() -> Dict[str, Any]:
    """LLM 运行态配置（sys_config 优先，回退 .env）。

    状态/列表接口必须反映「AI 配置页」刚保存的值：此前直接读 settings，
    后台改了 provider/model 后 AI 页面仍显示旧值（实测契约漂移）。
    `key_configured` 供前端区分「已配置但被停用/熔断」与「从未配置」。
    """
    provider = str(_get_db_value(
        "llm_provider", "string", settings.LLM_PROVIDER) or settings.LLM_PROVIDER)
    model = str(_get_db_value(
        "llm_model", "string", settings.LLM_MODEL) or settings.LLM_MODEL)
    api_key = str(_get_db_value(
        "llm_api_key", "string", settings.LLM_API_KEY) or "")
    return {
        "provider": provider,
        "model": model,
        "key_configured": bool(api_key.strip()),
        "temperature": _get_db_value(
            "llm_temperature", "float", settings.LLM_TEMPERATURE),
        "max_tokens": _get_db_value(
            "llm_max_tokens", "int", settings.LLM_MAX_TOKENS),
    }


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
    llm = _llm_runtime_config()
    return ok({
        "agents": items,
        "orchestrator_mode": orch.mode,
        "llm_enabled": is_available(),
        # provider/model 一律以 DB 配置为准（后台改配置后 AI 页面立即反映）；
        # 旧键 llm_provider/llm_model 保留，另补 provider/model 兼容状态卡。
        "llm_provider": llm["provider"],
        "llm_model": llm["model"],
        "provider": llm["provider"],
        "model": llm["model"],
        "key_configured": llm["key_configured"],
        "llm_temperature": llm["temperature"],
        "llm_max_tokens": llm["max_tokens"],
    })


@router.get("/status", summary="AI 引擎状态")
def agent_status(_: User = Depends(get_current_user)):
    from app.agents.rag import get_collection
    from app.services.scheduler import scheduler_status

    orch = get_orchestrator()
    col = get_collection()
    sched = scheduler_status()
    llm = _llm_runtime_config()
    available = is_available()
    if available:
        tip = ""
    elif not llm["key_configured"] and llm["provider"] != "ollama":
        tip = "未配置 LLM_API_KEY，所有 Agent 将使用规则引擎降级运行"
    else:
        tip = "LLM 当前不可用（已停用或熔断），所有 Agent 将使用规则引擎降级运行"

    from app.services import llm_breaker

    _breaker_snap = llm_breaker.snapshot()
    # tip 在熔断时可以直接说清是哪种熔断 —— 这是运维最想知道的区别：
    # 「密钥无效」要去改配置，而「限流冷却」只要等，两者处置完全相反。
    if not available and _breaker_snap["breaker"] == "auth":
        tip = "LLM 密钥无效或已过期（鉴权熔断），请到「AI 配置」更新密钥"
    elif _breaker_snap["breaker"] == "rate_limit":
        tip = (f"LLM 限流冷却中，约 {_breaker_snap['cooldown_remaining']}s 后自动恢复，"
               "期间使用规则引擎降级")
    return ok({
        "llm_enabled": available,
        # provider/model 以 DB 配置为准；即使未启用也返回实际配置，
        # 前端状态卡才能显示「已配置但未启用」并给出配置入口。
        "provider": llm["provider"],
        "model": llm["model"],
        # 前端「引擎状态」抽屉按 llm_provider/llm_model 渲染，字段名不一致会
        # 恒显示「未配置（规则引擎）」—— 已配置也看不出来。两套键一起下发。
        "llm_provider": llm["provider"],
        "llm_model": llm["model"],
        "key_configured": llm["key_configured"],
        "llm_temperature": llm["temperature"],
        "llm_max_tokens": llm["max_tokens"],
        "orchestrator_mode": orch.mode,
        # rag.get_collection 返回集合对象，不是字符串 "chroma"；
        # 前端按 vector_db === 'chroma' 判断，这里显式给出标识
        "vector_db": "chroma" if col else "sql",
        "agents": len(AGENT_REGISTRY),
        # 调度器状态此前只有 /jobs/status（仅 admin 可看），管理员打开
        # 「AI 引擎状态」时调度器恒显示「已停止」，与事实不符
        "scheduler_running": bool(sched.get("running")),
        # 熔断/冷却细节（B1）。此前这些状态藏在 LLMClient 实例属性里，
        # 运维看到 llm_enabled=false 完全无法区分「没配 key」「key 无效」
        # 「正在限流冷却」—— 只能翻日志猜。现在直接给出判定依据：
        #   breaker=none        正常
        #   breaker=auth        鉴权熔断（永久，需管理员改密钥）
        #   breaker=rate_limit  限流冷却（倒计时自动恢复）
        "breaker": _breaker_snap["breaker"],
        "breaker_reason": _breaker_snap["reason"],
        "cooldown_remaining": _breaker_snap["cooldown_remaining"],
        "tip": tip,
    })


# ---------------------------------------------------------------- 统一入口
@router.post("/chat", summary="AI 统一对话（自动路由）")
def chat(
    data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """一句话需求，自动路由到最合适的 Agent。"""
    request = _limited_text(data.get("message") or data.get("request"), "需求内容")
    if not request:
        raise BusinessException("请输入你的需求")
    check_agent_rate(db, user.id)

    # student_id 语义：学生只能是自己；教师/管理员可指定目标学生
    # （此前恒为调用者，教师说「给张三出题」会用到教师自己的学情上下文）
    is_staff = bool({"teacher", "grade_admin", "sys_admin"} & set(user.role_codes))
    target_sid = int(data.get("student_id")) if (
        is_staff and data.get("student_id")) else user.id

    orch = get_orchestrator()
    result = orch.run(
        db, user_id=user.id, request=request,
        args={
            "grade_id": data.get("grade_id"), "subject_id": data.get("subject_id"),
            "student_id": target_sid,
        },
    )

    if result.get("intent") == "chat" and not result.get("data"):
        # 兜底走答疑
        from app.agents.tutor_agent import TutorAgent

        r = TutorAgent().run(
            db, user_id=user.id, request=request,
            grade_id=data.get("grade_id"), subject_id=data.get("subject_id"),
            student_id=target_sid,
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


# ---------------------------------------------------------------- 流式对话
def _sse(event: Dict[str, Any]) -> str:
    return "data: " + json.dumps(event, ensure_ascii=False) + "\n\n"


@router.post("/chat/stream", summary="AI 统一对话（SSE 流式）")
def chat_stream(
    data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """流式版统一对话。

    - 文本类意图（答疑/聊天/笔记/规划）：真实逐 token 输出，首字延迟 ~1s
    - 结构化意图（出题/组卷/批改）：先路由再一次性返回结果事件
      （这类结果需要完整 JSON，逐字输出反而增加前端拼接复杂度）
    - LLM 不可用时：直接返回规则引擎降级结果，前端表现与非流式一致
    """
    from fastapi.responses import StreamingResponse

    request = _limited_text(data.get("message") or data.get("request"), "需求内容")
    if not request:
        raise BusinessException("请输入你的需求")
    check_agent_rate(db, user.id)

    is_staff = bool({"teacher", "grade_admin", "sys_admin"} & set(user.role_codes))
    target_sid = int(data.get("student_id")) if (
        is_staff and data.get("student_id")) else user.id

    def gen():
        import time

        start = time.perf_counter()
        # 1) 意图路由（非流式，通常 <50ms）
        try:
            orch = get_orchestrator()
            result = orch.run(
                db, user_id=user.id, request=request,
                args={
                    "grade_id": data.get("grade_id"),
                    "subject_id": data.get("subject_id"),
                    "student_id": target_sid,
                },
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("流式对话路由失败")
            yield _sse({"type": "error", "message": str(exc)[:200]})
            return

        intent = result.get("intent") or "chat"
        # 与非流式 /chat 保持一致：路由到 chat 但无实际结果时兜底走答疑，
        # 否则流式降级只会返回一句「未启用大模型」，附件引用也丢失。
        if intent == "chat" and not result.get("data"):
            from app.agents.tutor_agent import TutorAgent

            tr = TutorAgent().run(
                db, user_id=user.id, request=request,
                grade_id=data.get("grade_id"), subject_id=data.get("subject_id"),
                student_id=target_sid,
            )
            result["data"] = tr.get("data")
            result["agent"] = "tutor"
        yield _sse({"type": "meta", "intent": intent,
                    "agent": result.get("agent"), "request": request})

        TEXT_INTENTS = {"chat", "tutor", "note", "study", "plan"}
        data_block = result.get("data") or {}
        structured = intent not in TEXT_INTENTS or isinstance(data_block, dict) and (
            data_block.get("questions") or data_block.get("paper") or data_block.get("items"))

        # 2a) 结构化结果：一次性下发
        if structured:
            answer = _extract_answer(data_block)
            if answer:
                yield _sse({"type": "delta", "text": answer})
            yield _sse({
                "type": "done",
                "intent": intent, "agent": result.get("agent"),
                "is_fallback": result.get("is_fallback", False),
                "data": data_block,
                "duration_ms": result.get("duration_ms")
                or int((time.perf_counter() - start) * 1000),
            })
            return

        # 2b) 文本意图：走 LLM 流式
        from app.agents.llm import is_available as _llm_on

        if _llm_on():
            from app.agents.llm import get_llm

            engine = get_llm()
            sys_prompt = (
                "你是一位中学教师助手。用简洁、准确的中文回答学生问题；"
                "涉及公式时保持清晰；不确定的内容明确说明。"
            )
            got_any = False
            for ev in engine.stream_chat(sys_prompt, request, user_id=user.id,
                                         agent_name=f"stream_{intent}"):
                if ev.get("type") == "delta":
                    got_any = True
                    yield _sse({"type": "delta", "text": ev["text"]})
                elif ev.get("type") == "error":
                    yield _sse({"type": "error", "message": ev.get("message")})
                    return
            if got_any:
                yield _sse({"type": "done", "intent": intent, "agent": "tutor",
                            "is_fallback": False,
                            "data": data_block,
                            "duration_ms": int((time.perf_counter() - start) * 1000)})
                return

        # 2c) 降级：规则引擎结果一次性下发
        answer = _extract_answer(data_block) or "（当前为规则引擎降级模式，未启用大模型）"
        yield _sse({"type": "delta", "text": answer})
        yield _sse({"type": "done", "intent": intent, "agent": result.get("agent"),
                    "is_fallback": True,
                    "data": data_block,
                    "duration_ms": int((time.perf_counter() - start) * 1000)})

    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache",
                                      "X-Accel-Buffering": "no"})


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
    user: User = Depends(get_current_teacher),
):
    from app.agents.question_agent import QuestionGeneratorAgent

    count = _limited_count(data.get("count", 5), 5, field="出题数量")
    check_agent_rate(db, user.id)
    res = QuestionGeneratorAgent().run(
        db, user_id=user.id,
        grade_id=data.get("grade_id"), subject_id=int(data.get("subject_id", 0)),
        knowledge_point_id=data.get("knowledge_point_id"),
        question_type=data.get("type", "single"),
        count=count,
        difficulty=data.get("difficulty", "medium"),
        save=bool(data.get("save", False)),
    )
    _warn_if_slow(res, "question_generator")
    if data.get("save") and res.get("success"):
        _audit_write(db, user, "AI 生成题目入库",
                     f"subject={data.get('subject_id')} count={data.get('count', 5)} "
                     f"saved={(res.get('data') or {}).get('saved')}")
    # Agent 失败时 success=False / data=None —— 不能再用 ok() 包成 success=true，
    # 否则前端 res.data.data 必崩（典型契约漂移）
    if not res.get("success"):
        return fail(res.get("message", "题目生成失败"))
    return ok(res.get("data"), message=res.get("message", "生成完成"))


@router.post("/paper-composer", summary="智能组卷 Agent")
def paper_composer(
    data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    user: User = Depends(get_current_teacher),
):
    from app.agents.paper_agent import PaperComposerAgent

    request = _limited_text(data.get("request"), "组卷要求")
    check_agent_rate(db, user.id)
    res = PaperComposerAgent().run(
        db, user_id=user.id, request=request,
        grade_id=data.get("grade_id"), subject_id=data.get("subject_id"),
        total_score=float(data.get("total_score", 100)),
        difficulty_ratio=data.get("difficulty_ratio"),
        type_ratio=data.get("type_ratio"),
        knowledge_point_ids=data.get("knowledge_point_ids"),
        paper_name=data.get("paper_name"),
        save=bool(data.get("save", False)),
    )
    _warn_if_slow(res, "paper_composer")
    if not res.get("success"):
        return fail(res.get("message", "组卷失败"))
    if data.get("save"):
        _audit_write(db, user, "AI 组卷入库",
                     f"subject={data.get('subject_id')} "
                     f"paper_id={(res.get('data') or {}).get('paper_id')}")
    return ok(res.get("data"), message=res.get("message", "组卷完成"))


@router.post("/grading", summary="智能批改 Agent")
def agent_grading(
    data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    user: User = Depends(get_current_teacher),
):
    from app.agents.grading_agent import GradingAgent

    items = _limited_items(data.get("items"), "批改题目列表")
    check_agent_rate(db, user.id)
    res = GradingAgent().run(db, user_id=user.id, items=items)
    _warn_if_slow(res, "grading")
    if not res.get("success"):
        return fail(res.get("message", "批改失败"))
    return ok(res.get("data"), message="批改完成")


@router.post("/study-planner", summary="学习规划 Agent")
def study_planner(
    data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    user: User = Depends(get_current_student),
):
    from app.agents.study_agent import StudyPlannerAgent

    # 目标学生：学生身份只能为自己生成；教师/管理员可指定（学情分析场景）。
    # 此前 student_id 完全由客户端决定，学生可传他人 id 读取他人学情。
    is_staff = bool({"teacher", "grade_admin", "sys_admin"} & set(user.role_codes))
    target_sid = user.id
    if is_staff and data.get("student_id"):
        target_sid = int(data["student_id"])

    # 参数校验先于限流计数：非法入参不应该消耗用户额度
    days = _limited_count(data.get("days", 7), 7, limit=90, field="规划天数")
    check_agent_rate(db, user.id)
    res = StudyPlannerAgent().run(
        db, user_id=user.id,
        student_id=target_sid,
        days=days,
        daily_minutes=int(data.get("daily_minutes", 90)),
    )
    _warn_if_slow(res, "study_planner")
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
    question = _limited_text(
        data.get("message") or data.get("question")
        or data.get("question_text") or data.get("content") or "",
        "问题内容",
    )
    check_agent_rate(db, user.id)

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
    user: User = Depends(get_current_student),
):
    """笔记整理。

    ⚠️ 安全边界：note_id 必须校验归属。此前直接把客户端传入的 note_id
    交给 Agent，Agent 内部 `db.get(Note, note_id)` 不做归属判断，
    导致任意用户可读取（并 save=True 覆写）他人私密笔记。
    管理员仅允许「读取整理结果」，不允许写回他人笔记。
    """
    from app.agents.note_agent import NoteOrganizerAgent
    from app.models import Note

    note_id = data.get("note_id")
    save = bool(data.get("save", False))
    if note_id:
        note = db.get(Note, note_id)
        if not note:
            raise NotFoundException("笔记不存在")
        owner = note.student_id == user.id
        is_admin = "sys_admin" in user.role_codes
        if not owner:
            if not is_admin:
                raise PermissionException("无权整理他人笔记")
            if save:
                raise PermissionException("管理员不可覆写他人笔记")

    check_agent_rate(db, user.id)
    content = data.get("content")
    if content is not None:
        content = _limited_text(content, "笔记内容")
    res = NoteOrganizerAgent().run(
        db, user_id=user.id,
        note_id=note_id, content=content,
        title=data.get("title"), save=save,
    )
    _warn_if_slow(res, "note_organizer")
    if save and res.get("success"):
        _audit_write(db, user, "AI 整理笔记写回", f"note_id={note_id}")
    if not res.get("success"):
        return fail(res.get("message", "笔记整理失败"))
    return ok(res.get("data"), message=res.get("message", "整理完成"))


# ---------------------------------------------------------------- 异步任务（长任务）
JOB_AGENTS = {"question", "paper"}


def _run_job(job_id: int) -> None:
    """后台执行任务（独立 Session，避免请求结束后 Session 已关闭）。"""
    from app.core.database import SessionLocal
    from app.models import AgentJob

    db = SessionLocal()
    try:
        job = db.get(AgentJob, job_id)
        if not job:
            return
        job.status = "running"
        job.started_at = now_local()
        db.commit()

        params = json.loads(job.params or "{}")
        res: Dict[str, Any]
        if job.agent == "question":
            from app.agents.question_agent import QuestionGeneratorAgent

            res = QuestionGeneratorAgent().run(
                db, user_id=job.user_id,
                grade_id=params.get("grade_id"),
                subject_id=int(params.get("subject_id", 0)),
                knowledge_point_id=params.get("knowledge_point_id"),
                question_type=params.get("type", "single"),
                count=int(params.get("count", 5)),
                difficulty=params.get("difficulty", "medium"),
                save=bool(params.get("save", False)),
            )
        else:
            from app.agents.paper_agent import PaperComposerAgent

            res = PaperComposerAgent().run(
                db, user_id=job.user_id, request=params.get("request", ""),
                grade_id=params.get("grade_id"), subject_id=params.get("subject_id"),
                total_score=float(params.get("total_score", 100)),
                difficulty_ratio=params.get("difficulty_ratio"),
                type_ratio=params.get("type_ratio"),
                knowledge_point_ids=params.get("knowledge_point_ids"),
                paper_name=params.get("paper_name"),
                save=bool(params.get("save", False)),
            )

        job.result = json.dumps(res, ensure_ascii=False, default=str)
        job.status = "success" if res.get("success") else "failed"
        job.error = None if res.get("success") else (res.get("message") or "")[:500]
        _warn_if_slow(res, f"job:{job.agent}")
    except Exception as exc:  # noqa: BLE001
        logger.exception("异步任务 %s 执行失败", job_id)
        job = db.get(AgentJob, job_id)
        if job:
            job.status = "failed"
            job.error = str(exc)[:500]
    finally:
        job.finished_at = now_local()
        try:
            db.commit()
        except Exception:  # noqa: BLE001
            db.rollback()
        db.close()


@router.post("/jobs", summary="提交长任务（异步出题/组卷）")
def create_job(
    data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    user: User = Depends(get_current_teacher),
):
    """提交长任务，立即返回 job_id；用 GET /agent/jobs/{id} 轮询结果。"""
    from app.models import AgentJob

    agent = (data.get("agent") or "").strip()
    if agent not in JOB_AGENTS:
        raise BusinessException(f"不支持的任务类型 {agent!r}，可选：{sorted(JOB_AGENTS)}")
    params = data.get("params") or {}
    if not isinstance(params, dict):
        raise BusinessException("params 必须是对象")
    # 异步任务入口同样要受限：否则 /agent/grading、/agent/paper-composer 的
    # 入参上限可被 /agent/jobs 绕过（后台线程会照常发起 N 次 LLM 调用）。
    for key, label in (("request", "组卷要求"), ("topic", "教学主题"),
                       ("message", "需求内容")):
        if key in params:
            _limited_text(params.get(key), label)
    if "count" in params:
        _limited_count(params.get("count"), 5, field="出题数量")
    if "items" in params:
        _limited_items(params.get("items"), "批改题目列表")
    check_agent_rate(db, user.id)

    job = AgentJob(user_id=user.id, agent=agent, status="pending",
                   params=json.dumps(params, ensure_ascii=False))
    db.add(job)
    db.commit()
    db.refresh(job)

    import threading

    threading.Thread(target=_run_job, args=(job.id,), daemon=True).start()
    return ok({"job_id": job.id, "status": job.status},
              message="任务已提交，请轮询 /agent/jobs/%d 获取结果" % job.id)


@router.get("/jobs/{job_id}", summary="查询任务状态与结果")
def get_job(
    job_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_teacher),
):
    from app.models import AgentJob
    from app.services import agent_job_state

    job = db.get(AgentJob, job_id)
    if not job:
        raise NotFoundException("任务不存在")
    if job.user_id != user.id and "sys_admin" not in user.role_codes:
        raise PermissionException("无权查看该任务")
    d = dictify(job)
    d["result"] = json.loads(job.result) if job.result else None
    # B2：僵尸任务判定（进程重启导致后台线程丢失，status 永久停在 running）。
    # 此前这个端点**完全没有**超时判定，而 lesson_ai 那边有 —— 同一个表、
    # 同一种后台线程模式却是两套行为，前端在出题/组卷页会无限轮询。
    # 判据单点定义在 `services/agent_job_state`，两处都调它。
    return ok(agent_job_state.apply_timeout(job, d))


@router.get("/jobs", summary="我的任务列表")
def list_jobs(
    params: PageParams = Depends(), status: Optional[str] = None,
    db: Session = Depends(get_db), user: User = Depends(get_current_teacher),
):
    from app.models import AgentJob
    from app.services import agent_job_state

    base = select(AgentJob).where(AgentJob.user_id == user.id)
    # B2：按状态筛选要在**库里**先过滤，再叠加超时判定 —— 但僵尸任务在库里的
    # 真实 status 仍是 running，所以 `?status=failed` 查不到它们，
    # 而 `?status=running` 会把它们列出来（随后被呈现为 failed）。
    # 这个不一致必须在**筛 failed 时**补一条：库里的 running 且已超时的行
    # 也应算 failed，否则用户按"失败"筛选看不到真正卡死的那些。
    if status == "failed":
        from datetime import timedelta

        from sqlalchemy import or_

        cutoff = now_local() - timedelta(seconds=agent_job_state.JOB_TIMEOUT_SECONDS)
        base = base.where(or_(
            AgentJob.status == "failed",
            (AgentJob.status.in_(agent_job_state.STATUS_RUNNING))
            & (AgentJob.created_at < cutoff),
        ))
    elif status in agent_job_state.STATUS_RUNNING:
        # 查"运行中"时要把已超时的剔掉：它们呈现为 failed，列在运行中里
        # 会让用户以为还在跑（就是本 bug 的表现形态）。
        from datetime import timedelta

        cutoff = now_local() - timedelta(seconds=agent_job_state.JOB_TIMEOUT_SECONDS)
        base = base.where(
            AgentJob.status == status,
            AgentJob.created_at >= cutoff,
        )
    elif status:
        base = base.where(AgentJob.status == status)

    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0
    rows = db.scalars(
        base.order_by(desc(AgentJob.created_at))
        .offset(params.offset).limit(params.page_size)
    ).all()
    items = [agent_job_state.apply_timeout(r, dictify(r)) for r in rows]
    return ok({"items": items, "total": total, "page": params.page})


# ---------------------------------------------------------------- 调用日志
@router.get("/logs", summary="AI 调用日志")
def agent_logs(
    params: PageParams = Depends(), agent_name: Optional[str] = None,
    status: Optional[str] = None, is_fallback: Optional[bool] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # 权限：管理员看全部，学生只看自己的
    is_admin = {"sys_admin", "grade_admin"} & set(user.role_codes)
    stmt = select(AgentCallLog)
    if not is_admin:
        stmt = stmt.where(AgentCallLog.user_id == user.id)
    if agent_name:
        stmt = stmt.where(AgentCallLog.agent_name == agent_name)
    # 「降级」下拉此前没有对应入参，FastAPI 静默忽略 → 选什么都不影响结果
    if is_fallback is not None:
        stmt = stmt.where(AgentCallLog.is_fallback.is_(is_fallback))
    if status:
        stmt = stmt.where(AgentCallLog.status == status)

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(
        stmt.order_by(desc(AgentCallLog.created_at))
        .offset(params.offset).limit(params.page_size)
    ).all()

    # 统计必须与明细同权：非管理员只看自己的汇总，
    # 否则 items 只有自己 14 条、summary 却是全站 38 次（实测泄漏）。
    stat_stmt = select(
        func.count(),
        func.avg(AgentCallLog.duration_ms),
        func.sum(AgentCallLog.input_tokens),
        func.sum(AgentCallLog.output_tokens),
    ).select_from(AgentCallLog)
    by_stmt = select(AgentCallLog.agent_name, func.count()).group_by(
        AgentCallLog.agent_name)
    if not is_admin:
        stat_stmt = stat_stmt.where(AgentCallLog.user_id == user.id)
        by_stmt = by_stmt.where(AgentCallLog.user_id == user.id)
    stats = db.execute(stat_stmt).one()
    by_agent = db.execute(by_stmt).all()

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
