# -*- coding: utf-8 -*-
"""优化项 3：SSE 流式输出。

链路：llm.py 新增 stream_chat（LangChain client.stream）
     → /agent/chat/stream（StreamingResponse, text/event-stream）
     → AgentChat.vue 用 fetch + ReadableStream 增量渲染

事件协议：
  data: {"type":"meta","intent":"tutor","agent":"tutor"}
  data: {"type":"delta","text":"勾股定理"}
  data: {"type":"done","duration_ms":1234,"is_fallback":false}
  data: {"type":"error","message":"..."}
"""
import io

# ============================================================
# 1) llm.py 增加流式方法
# ============================================================
f = "backend/app/agents/llm.py"
s = io.open(f, encoding="utf-8").read()

STREAM_METHOD = '''
    def stream_chat(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        user_id: Optional[int] = None,
        agent_name: str = "llm_stream",
    ):
        """流式调用大模型，逐 token yield 文本片段。

        与 chat() 的差异：不返回结构化结果，由调用方拼接；同样写调用日志
        （总耗时与 token 用量在结束时补记），保证「AI 调用日志」页面完整。
        """
        client = self.get_client()
        if client is None:
            yield {"type": "fallback", "reason": self._fallback_reason or "LLM 不可用"}
            return

        import time

        from langchain_core.messages import HumanMessage, SystemMessage

        start = time.perf_counter()
        chunks = []
        usage = {}
        try:
            for chunk in client.stream(
                [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
            ):
                text = getattr(chunk, "content", "") or ""
                meta = getattr(chunk, "usage_metadata", None) or {}
                if meta:
                    usage = meta
                if text:
                    chunks.append(text)
                    yield {"type": "delta", "text": text}
            duration = int((time.perf_counter() - start) * 1000)
            log_agent_call(
                agent_name=agent_name, user_id=user_id,
                input_text=user_prompt[:2000],
                output_text="".join(chunks)[:2000],
                input_tokens=usage.get("input_tokens", 0),
                output_tokens=usage.get("output_tokens", 0),
                duration_ms=duration, status="success",
            )
            yield {"type": "end", "duration_ms": duration, "usage": usage}
        except Exception as exc:  # noqa: BLE001
            duration = int((time.perf_counter() - start) * 1000)
            logger.error("LLM 流式调用失败 [%s]: %s", agent_name, exc)
            log_agent_call(
                agent_name=agent_name, user_id=user_id, input_text=user_prompt[:2000],
                duration_ms=duration, status="failed", is_fallback=True,
                error_msg=str(exc)[:1000],
            )
            yield {"type": "error", "message": f"模型调用失败：{exc}"}

'''
ANCHOR = "def log_agent_call("
assert ANCHOR in s
s = s.replace(ANCHOR, STREAM_METHOD.lstrip("\n") + "\n" + ANCHOR, 1)
io.open(f, "w", encoding="utf-8", newline="\n").write(s)
print("[1] llm.py stream_chat 已添加")

# ============================================================
# 2) /agent/chat/stream
# ============================================================
f2 = "backend/app/api/v1/agent.py"
s2 = io.open(f2, encoding="utf-8").read()

SSE_API = '''

# ---------------------------------------------------------------- 流式对话
def _sse(event: Dict[str, Any]) -> str:
    return "data: " + json.dumps(event, ensure_ascii=False) + "\\n\\n"


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

    request = data.get("message") or data.get("request")
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
                            "duration_ms": int((time.perf_counter() - start) * 1000)})
                return

        # 2c) 降级：规则引擎结果一次性下发
        answer = _extract_answer(data_block) or "（当前为规则引擎降级模式，未启用大模型）"
        yield _sse({"type": "delta", "text": answer})
        yield _sse({"type": "done", "intent": intent, "agent": result.get("agent"),
                    "is_fallback": True,
                    "duration_ms": int((time.perf_counter() - start) * 1000)})

    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache",
                                      "X-Accel-Buffering": "no"})
'''

ANCHOR2 = 'def _extract_answer(data: Any) -> str:'
assert ANCHOR2 in s2
s2 = s2.replace(ANCHOR2, SSE_API.strip("\n") + "\n\n\n" + ANCHOR2, 1)
io.open(f2, "w", encoding="utf-8", newline="\n").write(s2)
print("[2] /agent/chat/stream 已添加")
