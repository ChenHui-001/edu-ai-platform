"""Agent 基类与 LangGraph 编排引擎。

即使未安装 langgraph，也提供等价的顺序编排降级实现。
"""
import time
from typing import Any, Dict, List, Optional, TypedDict

from sqlalchemy.orm import Session

from app.agents.llm import extract_json, llm_client, log_agent_call
from app.core.logger import get_logger

logger = get_logger("agent-base")


class AgentResult(TypedDict, total=False):
    """Agent 统一返回结构。"""

    success: bool
    data: Any
    message: str
    agent: str
    is_fallback: bool
    duration_ms: int


class BaseAgent:
    """所有业务 Agent 的基类。"""

    name: str = "base"
    display_name: str = "基础智能体"
    description: str = ""
    system_prompt: str = ""

    def run(self, db: Session, user_id: Optional[int] = None, **kwargs: Any) -> AgentResult:
        start = time.perf_counter()
        try:
            data = self.execute(db, user_id=user_id, **kwargs)
            if isinstance(data, dict) and "__llm_result__" in data:
                llm_meta = data.pop("__llm_result__")
                if not llm_meta.get("success"):
                    # user_id 必须透传：降级实现要按「当前用户可用」收窄数据范围
                    # （如出题 Agent 复用题库题时不能拿到他人私有题）。它不是
                    # execute 的普通 kwarg，所以这里显式补一次。
                    fallback = self.fallback(db, user_id=user_id, **kwargs)
                    return AgentResult(
                        success=True, data=fallback, message="模型不可用，已使用规则引擎生成",
                        agent=self.name, is_fallback=True,
                        duration_ms=int((time.perf_counter() - start) * 1000),
                    )
                data = llm_meta.get("parsed") if llm_meta.get("parsed") is not None else data
            return AgentResult(
                success=True, data=data, message="ok", agent=self.name,
                duration_ms=int((time.perf_counter() - start) * 1000),
            )
        except Exception as exc:
            logger.opt(exception=True).error(f"{self.name} 执行失败: {exc}")
            log_agent_call(
                agent_name=self.name, user_id=user_id,
                input_text=str(kwargs)[:500], status="failed", error_msg=str(exc)[:500],
                biz_type=self.name,
            )
            return AgentResult(
                success=False, data=None, message=f"{self.display_name}执行失败：{exc}",
                agent=self.name, duration_ms=int((time.perf_counter() - start) * 1000),
            )

    def execute(self, db: Session, user_id: Optional[int] = None, **kwargs: Any) -> Any:
        raise NotImplementedError

    def fallback(self, db: Session, **kwargs: Any) -> Any:
        """规则引擎降级实现，保证无 LLM 时功能可用。"""
        return {}

    # ---------------- LLM 辅助 ----------------
    def call_llm(
        self,
        user_prompt: str,
        *,
        db: Optional[Session] = None,
        user_id: Optional[int] = None,
        context: Optional[List[str]] = None,
        biz_type: Optional[str] = None,
        biz_id: Optional[int] = None,
        json_mode: bool = True,
    ) -> Dict[str, Any]:
        """调用大模型并尝试解析 JSON。"""
        ctx_prompt = user_prompt
        if context:
            ctx_prompt = "【参考资料】\n" + "\n".join(f"- {c}" for c in context[:10]) + "\n\n" + user_prompt

        resp = llm_client.chat(
            self.system_prompt, ctx_prompt,
            user_id=user_id, agent_name=self.name, biz_type=biz_type, biz_id=biz_id,
        )
        if resp["success"] and json_mode:
            parsed = extract_json(resp["content"])
            if parsed is not None:
                return {"success": True, "parsed": parsed, "raw": resp["content"]}
            # 解析失败**不等于**模型没干活：请求成功但正文不是可解析的 JSON。
            # 常见成因是 max_tokens 预算被 reasoning token 吃光（正文为空），
            # 或模型没按 JSON 格式输出。必须带上原因 —— 否则上层只能笼统报
            # 「模型不可用」，把「没配 Key」和「输出被截断」混为一谈，
            # 运维会被引向完全错误的方向。
            empty = not (resp["content"] or "").strip()
            return {
                "success": True,
                "parsed": None,
                "raw": resp["content"],
                "reason": (
                    "模型返回了内容但不是可解析的 JSON"
                    + ("（响应正文为空，通常是 max_tokens 预算被推理 token 耗尽）"
                       if empty else
                       "（可能是输出被 max_tokens 截断，或模型未按 JSON 格式输出）")
                ),
            }
        return {"success": False, "reason": resp.get("reason", "模型调用失败"), "raw": ""}


# ---------------------------------------------------------------- 编排引擎
class AgentGraphState(TypedDict, total=False):
    """LangGraph 共享状态。"""

    request: str
    intent: str
    params: Dict[str, Any]
    result: Any
    trace: List[Dict[str, Any]]


class RouterAgent(BaseAgent):
    """路由 Agent：识别需求类型，分发到对应专属 Agent。"""

    name = "router"
    display_name = "需求路由智能体"
    system_prompt = """你是教育系统的需求路由助手。根据用户输入判断应触发的智能体类型。

可选智能体：
- question_generator: 出题、生成题目、出一道题、要几道题
- paper_composer: 组卷、出套卷、试卷、单元测试、模拟卷
- grading_assistant: 批改、评分、帮我改作文、这道题给几分
- study_planner: 学习规划、复习计划、怎么提升、薄弱知识点
- tutor: 答疑、讲解、这道题怎么做、知识点是什么、为什么
- note_organizer: 整理笔记、总结、生成大纲、思维导图

只输出 JSON：{"intent": "意图名", "params": {"关键参数": "值"}, "confidence": 0.0-1.0}
意图必须是上述之一。若都不匹配，intent 为 "chat"。"""

    def execute(self, db: Session, user_id: Optional[int] = None, request: str = "", **kwargs) -> Any:
        result = self.call_llm(
            f"用户输入：{request}", db=db, user_id=user_id, biz_type="router"
        )
        if result["success"] and result.get("parsed"):
            parsed = result["parsed"]
            if isinstance(parsed, dict) and parsed.get("intent"):
                return {
                    "intent": parsed["intent"],
                    "params": parsed.get("params", {}) or {},
                    "confidence": parsed.get("confidence", 0.8),
                    "source": "llm",
                }
        # 关键词兜底
        return {"intent": self._guess_intent(request), "params": {}, "confidence": 0.5, "source": "rule"}

    def _guess_intent(self, request: str) -> str:
        text = request.lower()
        rules = [
            ("paper_composer", ["组卷", "出套", "试卷", "套卷", "单元测试", "模拟卷", "卷子"]),
            ("question_generator", ["出题", "生成题", "出一道", "要几道", "题目"]),
            ("grading_assistant", ["批改", "评分", "给几分", "改作文", "评语"]),
            ("study_planner", ["规划", "复习计划", "怎么提升", "薄弱", "学习计划"]),
            ("note_organizer", ["整理笔记", "总结", "大纲", "思维导图", "提炼"]),
            ("tutor", ["怎么", "为什么", "讲解", "答疑", "是什么", "教我", "不懂"]),
        ]
        for intent, keywords in rules:
            if any(k in text for k in keywords):
                return intent
        return "chat"


class Orchestrator:
    """多 Agent 编排引擎。

    优先使用 LangGraph 状态图；未安装时自动降级为等价顺序编排。
    """

    def __init__(self):
        self.router = RouterAgent()
        self.graph = self._build_langgraph()
        self.mode = "langgraph" if self.graph is not None else "sequential"

    def _build_langgraph(self):
        """构建 LangGraph 状态图。"""
        try:
            from langgraph.graph import END, START, StateGraph

            builder = StateGraph(AgentGraphState)

            def node_route(state: AgentGraphState) -> AgentGraphState:
                db, user_id, request = state["params"].get("db"), state["params"].get("user_id"), state["request"]
                r = self.router.run(db, user_id=user_id, request=request)
                state["intent"] = (r.get("data") or {}).get("intent", "chat")
                state["trace"] = [{"step": "route", "intent": state["intent"]}]
                return state

            def node_dispatch(state: AgentGraphState) -> AgentGraphState:
                agent = AGENT_REGISTRY.get(state["intent"])
                db = state["params"].get("db")
                user_id = state["params"].get("user_id")
                if not agent:
                    state["result"] = {"agent": "router", "message": "暂不支持该需求，请换个说法"}
                    return state
                r = agent.run(db, user_id=user_id, request=state["request"], **state["params"].get("args", {}))
                state["result"] = {"agent": r["agent"], "data": r["data"],
                                   "is_fallback": r.get("is_fallback", False)}
                state["trace"].append({"step": state["intent"], "ok": r["success"]})
                return state

            builder.add_node("route", node_route)
            builder.add_node("dispatch", node_dispatch)
            builder.add_edge(START, "route")
            builder.add_edge("route", "dispatch")
            builder.add_edge("dispatch", END)
            return builder.compile()
        except ImportError:
            logger.info("langgraph 未安装，使用顺序编排降级模式")
            return None
        except Exception as exc:
            logger.warning(f"LangGraph 构建失败，降级为顺序编排: {exc}")
            return None

    def run(
        self, db: Session, user_id: Optional[int], request: str, args: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """执行编排。"""
        start = time.perf_counter()
        args = args or {}
        state: Dict[str, Any] = {
            "request": request,
            "params": {"db": db, "user_id": user_id, "args": args},
            "trace": [],
        }

        if self.graph is not None:
            try:
                final = self.graph.invoke(state)
                return {
                    "success": True,
                    "intent": final.get("intent"),
                    "agent": (final.get("result") or {}).get("agent"),
                    "data": (final.get("result") or {}).get("data"),
                    "is_fallback": (final.get("result") or {}).get("is_fallback", False),
                    "trace": final.get("trace", []),
                    "mode": "langgraph",
                    "duration_ms": int((time.perf_counter() - start) * 1000),
                }
            except Exception as exc:
                logger.opt(exception=True).warning(f"LangGraph 执行失败，降级顺序编排: {exc}")

        # 顺序编排降级
        routed = self.router.run(db, user_id=user_id, request=request)
        intent = (routed.get("data") or {}).get("intent", "chat")
        trace = [{"step": "route", "intent": intent}]
        agent = AGENT_REGISTRY.get(intent)
        if not agent:
            return {
                "success": True, "intent": intent, "agent": "router", "data": None,
                "message": "暂不支持该需求，请换个说法", "trace": trace, "mode": "sequential",
                "duration_ms": int((time.perf_counter() - start) * 1000),
            }
        r = agent.run(db, user_id=user_id, request=request, **args)
        trace.append({"step": intent, "ok": r["success"]})
        return {
            "success": r["success"],
            "intent": intent,
            "agent": r["agent"],
            "data": r["data"],
            "message": r.get("message"),
            # AgentResult 是 total=False 的 TypedDict，Agent.run() 成功分支
            # 不会写入 is_fallback，必须用 .get 兜底，否则 /agent/chat 直接 500。
            "is_fallback": r.get("is_fallback", False),
            "trace": trace,
            "mode": "sequential",
            "duration_ms": int((time.perf_counter() - start) * 1000),
        }


# ---------------------------------------------------------------- 注册表
AGENT_REGISTRY: Dict[str, BaseAgent] = {}


def register_agent(agent: BaseAgent) -> None:
    AGENT_REGISTRY[agent.name] = agent


def load_agents() -> Dict[str, BaseAgent]:
    """加载全部业务 Agent。"""
    from app.agents.grading_agent import GradingAgent
    from app.agents.lesson_agent import LessonPlanAgent
    from app.agents.note_agent import NoteOrganizerAgent
    from app.agents.paper_agent import PaperComposerAgent
    from app.agents.question_agent import QuestionGeneratorAgent
    from app.agents.study_agent import StudyPlannerAgent
    from app.agents.tutor_agent import TutorAgent

    # RouterAgent 必须一并注册：/agent/list 用 name=="router" 标识兜底模式，
    # 缺失会导致前端 Agent 中心少显示一个，且 is_fallback 永远为 false。
    for cls in (
        RouterAgent, QuestionGeneratorAgent, PaperComposerAgent, GradingAgent,
        StudyPlannerAgent, TutorAgent, NoteOrganizerAgent, LessonPlanAgent,
    ):
        register_agent(cls())
    return AGENT_REGISTRY


orchestrator: Optional[Orchestrator] = None


def get_orchestrator() -> Orchestrator:
    """获取全局编排器（懒初始化）。"""
    global orchestrator
    if orchestrator is None:
        load_agents()
        orchestrator = Orchestrator()
    return orchestrator
