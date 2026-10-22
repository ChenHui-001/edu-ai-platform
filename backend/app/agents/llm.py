"""大模型接入层：兼容通义千问 / DeepSeek / OpenAI / 本地 Ollama 协议。

未配置 API Key 时自动降级为规则引擎，保证系统始终可用（离线部署场景）。
"""
import json
import re
import threading
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.core.logger import get_logger
from app.models import AgentCallLog

logger = get_logger("llm")

PROVIDERS = {
    "deepseek": {
        "base_url": "https://api.deepseek.com/v1",
        "default_model": "deepseek-chat",
        "env_key": "DASHSCOPE_API_KEY",
    },
    "qwen": {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "default_model": "qwen-plus",
        "env_key": "DASHSCOPE_API_KEY",
    },
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "default_model": "gpt-4o-mini",
        "env_key": "OPENAI_API_KEY",
    },
    "ollama": {
        "base_url": "http://localhost:11434/v1",
        "default_model": "qwen2:7b",
        "env_key": "",
    },
}


def is_available() -> bool:
    """LLM 是否可用。未配置 Key 或已熔断时走规则引擎。"""
    # 熔断中：对外统一声称不可用，避免健康检查/状态接口继续报 llm_enabled=true。
    # 直接读模块级单例（而不是调 get_llm()）—— is_available 定义在 get_llm 之前，
    # 且单例为 None 时无需构造（构造本身会读库，形成不必要的开销）。
    if _llm_singleton is not None and _llm_singleton._disabled_reason:
        return False
    enabled = _get_db_value("llm_enabled", "bool", settings.LLM_ENABLED)
    api_key = _get_db_value("llm_api_key", "string", settings.LLM_API_KEY)
    return bool(enabled and api_key)

# sys_config 里的值优先级高于 settings，但部分参数有**硬上限**（成本/稳定性约束）。
# 典型场景：v1.0.38 把 LLM_MAX_TOKENS 默认值 4096→2048，老环境 DB 里仍残留 4096，
# 会继续覆盖新默认值 → 优化静默失效。因此在**读取处**统一收敛，
# 保证 DB 残留值不能突破当前代码允许的上限（与 ai_config_service.get_ai_config 保持一致）。
_CAPS: Dict[str, int] = {"llm_max_tokens": int(settings.LLM_MAX_TOKENS or 0)}

# 进程级单例，声明必须在 is_available() 之前：函数体在调用时才求值，
# 但保持在定义前声明可避免「先使用后声明」的阅读困惑与静态工具告警。
_llm_singleton: Optional["LLMClient"] = None


def _get_db_value(key: str, value_type: str, default: Any) -> Any:
    """从 sys_config 表读取配置值，优先级高于 settings。失败则回退到 settings。"""
    val: Any = default
    try:
        from app.core.database import SessionLocal
        from app.models import SysConfig
        from sqlalchemy import select

        with SessionLocal() as db:
            row = db.scalar(select(SysConfig).where(SysConfig.key == key))
            raw = row.value if row is not None else None
            if raw is None or raw == "":
                return _apply_cap(key, default)
            if value_type == "bool":
                val = raw.lower() in ("true", "1", "yes", "on")
            elif value_type == "int":
                try:
                    val = int(raw)
                except ValueError:
                    val = default
            elif value_type == "float":
                try:
                    val = float(raw)
                except ValueError:
                    val = default
            else:
                val = raw
    except Exception:
        val = default
    return _apply_cap(key, val)


def _apply_cap(key: str, value: Any) -> Any:
    """对配置值施加上限收敛；未配置上限的 key 原样返回。"""
    cap = _CAPS.get(key)
    if cap and isinstance(value, int) and not isinstance(value, bool) and value > cap:
        logger.warning(f"配置 {key}={value} 超过上限 {cap}，已收敛")
        return cap
    return value


class LLMClient:
    """OpenAI 兼容协议客户端，懒加载 langchain-openai。

    认证失败熔断：密钥无效（401/403）属于**配置错误**，不是瞬时故障，
    重试同一个无效密钥不可能成功。此前没有熔断，交一份 6 道简答题的卷子
    会连续发起 6 次 LLM 往返，每次都要等 5~6 秒才拿到 401
    → 单次交卷从 0.5s 涨到 33s，直接超过前端 30s 超时（实测 P1）。
    现在首个 401 即记下原因并短路，后续调用直接走规则引擎降级，
    直到管理员改配置（`_reload` 清空熔断状态）。
    """

    # 触发熔断的错误特征。
    # 401/403 是鉴权失败，429 是配额/限流——这两类都**不是瞬时抖动**：
    # 同一个密钥、同一时刻重试必然还是同样的结果，继续重试只会白等网络往返。
    # 实测：无效密钥返回 429 RATE_LIMITED，一次往返 1.5s；
    # 一份 6 道简答题的卷子 = 6 次串行往返，交卷从 0.5s 涨到 116s（前端超时）。
    # 真正的网络抖动（超时/连接重置）不在熔断范围，那些是有可能恢复的。
    _AUTH_ERROR_MARKS = ("401", "403", "429", "UNAUTHORIZED", "Unauthorized",
                         "invalid_api_key", "Incorrect API key", "authentication",
                         "RATE_LIMITED", "rate limit", "配额", "quota")

    def __init__(self):
        self._client = None
        self._fallback_reason = ""
        # 熔断状态：非空表示已判定配置不可用，跳过真实网络调用
        self._disabled_reason = ""

    @property
    def provider_cfg(self) -> Dict[str, Any]:
        provider = _get_db_value("llm_provider", "string", settings.LLM_PROVIDER)
        return PROVIDERS.get(provider, PROVIDERS["deepseek"])

    def _is_auth_error(self, exc: Exception) -> bool:
        msg = str(exc)
        return any(m in msg for m in self._AUTH_ERROR_MARKS)

    def get_client(self):
        """获取 LangChain ChatOpenAI 实例（失败返回 None）。

        检查顺序很重要：**熔断判断必须在返回缓存客户端之前**。
        反过来的话，进程里已有 `_client` 时永远查不到熔断标记，
        熔断形同虚设（实测：写入无效密钥后交卷仍耗时 105s）。
        """
        # 熔断优先级最高：已确认配置无效，连缓存客户端也不能用
        if self._disabled_reason:
            self._fallback_reason = self._disabled_reason
            return None
        if self._client is not None:
            return self._client
        if not is_available():
            self._fallback_reason = "未配置 LLM_API_KEY，使用规则引擎降级"
            return None
        try:
            from langchain_openai import ChatOpenAI

            cfg = self.provider_cfg
            provider = _get_db_value("llm_provider", "string", settings.LLM_PROVIDER)
            api_key = _get_db_value("llm_api_key", "string", settings.LLM_API_KEY)
            base_url = _get_db_value("llm_base_url", "string", settings.LLM_BASE_URL) or cfg["base_url"]
            model = _get_db_value("llm_model", "string", settings.LLM_MODEL) or cfg["default_model"]
            temperature = _get_db_value("llm_temperature", "float", settings.LLM_TEMPERATURE)
            max_tokens = _get_db_value("llm_max_tokens", "int", settings.LLM_MAX_TOKENS)
            timeout = _get_db_value("llm_timeout", "int", settings.LLM_TIMEOUT)
            self._client = ChatOpenAI(
                api_key=api_key or "ollama",
                base_url=base_url,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=timeout,
            )
            logger.info(f"LLM 客户端就绪: {provider} / {model}")
            return self._client
        except ImportError as exc:
            self._fallback_reason = f"langchain-openai 未安装: {exc}"
            logger.warning(self._fallback_reason)
            return None
        except Exception as exc:
            self._fallback_reason = f"LLM 初始化失败: {exc}"
            logger.error(self._fallback_reason)
            return None

    def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        user_id: Optional[int] = None,
        agent_name: str = "llm",
        biz_type: Optional[str] = None,
        biz_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """调用大模型，返回 {success, content, is_fallback, reason, usage}。"""
        client = self.get_client()
        if client is None:
            # 客户端不可用（未配置 key / 初始化失败）时同样要写日志，
            # 否则「AI 调用日志」页面在降级期间完全空白，
            # 运维无法区分「没调用过」与「调用了但降级了」。
            reason = self._fallback_reason or "LLM 不可用"
            log_agent_call(
                agent_name=agent_name, user_id=user_id,
                input_text=user_prompt[:2000], duration_ms=0,
                status="skipped", is_fallback=True,
                error_msg=reason[:1000], biz_type=biz_type, biz_id=biz_id,
            )
            return {
                "success": False,
                "content": "",
                "is_fallback": True,
                "reason": reason,
                "usage": {},
            }

        import time

        from langchain_core.messages import HumanMessage, SystemMessage

        start = time.perf_counter()
        try:
            resp = client.invoke(
                [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
            )
            duration = int((time.perf_counter() - start) * 1000)
            usage = getattr(resp, "usage_metadata", None) or {}
            log_agent_call(
                agent_name=agent_name, user_id=user_id, input_text=user_prompt[:2000],
                output_text=str(resp.content)[:2000],
                input_tokens=usage.get("input_tokens", 0),
                output_tokens=usage.get("output_tokens", 0),
                duration_ms=duration, status="success", biz_type=biz_type, biz_id=biz_id,
            )
            return {
                "success": True,
                "content": str(resp.content),
                "is_fallback": False,
                "duration_ms": duration,
                "usage": usage,
            }
        except Exception as exc:
            duration = int((time.perf_counter() - start) * 1000)
            logger.error(f"LLM 调用失败 [{agent_name}]: {exc}")
            # 鉴权失败立即熔断：同一份无效密钥重试必然还是失败，
            # 不熔断就会让「一份 6 道主观题的卷子」白等 6 轮网络往返。
            if self._is_auth_error(exc):
                self._disabled_reason = (
                    f"LLM 密钥无效或已过期（{str(exc)[:80]}），已暂停真实调用，"
                    "请到「系统管理 → AI 配置」更新密钥后重试")
                logger.warning(self._disabled_reason)
            log_agent_call(
                agent_name=agent_name, user_id=user_id, input_text=user_prompt[:2000],
                duration_ms=duration, status="failed", is_fallback=True,
                error_msg=str(exc)[:1000], biz_type=biz_type, biz_id=biz_id,
            )
            return {
                "success": False,
                "content": "",
                "is_fallback": True,
                "reason": f"模型调用失败：{exc}",
                "usage": {},
            }


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
            if self._is_auth_error(exc):
                self._disabled_reason = (
                    f"LLM 密钥无效或已过期（{str(exc)[:80]}），已暂停真实调用，"
                    "请到「系统管理 → AI 配置」更新密钥后重试")
                logger.warning(self._disabled_reason)
            log_agent_call(
                agent_name=agent_name, user_id=user_id, input_text=user_prompt[:2000],
                duration_ms=duration, status="failed", is_fallback=True,
                error_msg=str(exc)[:1000],
            )
            yield {"type": "error", "message": f"模型调用失败：{exc}"}


def get_llm() -> "LLMClient":
    """进程级 LLMClient 单例（复用 ChatOpenAI 连接池与配置）。"""
    global _llm_singleton
    if _llm_singleton is None:
        _llm_singleton = LLMClient()
    return _llm_singleton


def log_agent_call(
    *,
    agent_name: str,
    user_id: Optional[int] = None,
    input_text: Optional[str] = None,
    output_text: Optional[str] = None,
    input_tokens: int = 0,
    output_tokens: int = 0,
    duration_ms: Optional[int] = None,
    status: str = "success",
    error_msg: Optional[str] = None,
    is_fallback: bool = False,
    biz_type: Optional[str] = None,
    biz_id: Optional[int] = None,
) -> None:
    """写入 AI 调用日志（**后台线程异步落库**，绝不阻塞调用方）。

    为什么必须异步：交卷流程里 `save_answers()` 先 `db.flush()` 写 Answer，
    此时业务事务已经持有 SQLite 的 RESERVED 写锁，直到 `finalize_submission()`
    的 `db.commit()` 才释放。而 AI 调用日志发生在两者之间（主观题判分阶段），
    若在这里同步写库，会用**另一个 Session** 去抢同一把写锁 —— 必然抢不到，
    于是等满 `busy_timeout`（5s）抛 `database is locked`，重试 3 次再等 3×5s。

    实测代价：一道简答题就固定 +16.5s（3 次重试 + 退避），32 题卷子交卷
    16.4s 全部耗在这里，前端 30s 超时直接判失败。日志是旁路数据，没有理由
    让主流程为它等锁。

    改为 daemon 线程 + 单独连接：主流程立即返回，写成功与否都不再影响响应时间。
    """
    payload = dict(
        agent_name=agent_name, user_id=user_id,
        input_text=input_text, output_text=output_text,
        input_tokens=input_tokens, output_tokens=output_tokens,
        duration_ms=duration_ms, status=status, error_msg=error_msg,
        is_fallback=is_fallback, biz_type=biz_type, biz_id=biz_id,
    )

    def _write() -> None:
        import time as _time

        from app.core.database import SessionLocal

        last_exc: Optional[Exception] = None
        for attempt in range(3):
            try:
                with SessionLocal() as db:
                    db.add(AgentCallLog(**payload))
                    db.commit()
                return
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                if "locked" not in str(exc).lower() and "busy" not in str(exc).lower():
                    break  # 非锁冲突，重试无意义
                _time.sleep(0.1 * (attempt + 1))
        logger.warning(f"Agent 调用日志写入失败: {last_exc}")

    try:
        threading.Thread(
            target=_write, name="agent-call-log", daemon=True
        ).start()
    except Exception as exc:  # noqa: BLE001  线程都起不来时降级为同步写
        logger.warning(f"日志线程启动失败，改为同步写入: {exc}")
        _write()


# ---------------------------------------------------------------- JSON 解析
def extract_json(content: str) -> Optional[Any]:
    """从模型输出中提取 JSON（兼容 ```json 包裹、额外文本）。"""
    if not content:
        return None
    text = content.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.MULTILINE).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # 提取第一个 JSON 对象或数组
    for pattern in (r"\{[\s\S]*\}", r"\[[\s\S]*\]"):
        m = re.search(pattern, text)
        if m:
            try:
                return json.loads(m.group())
            except json.JSONDecodeError:
                continue
    return None


def build_messages(system: str, user: str, context: Optional[List[str]] = None) -> tuple:
    """拼装上下文消息。"""
    if context:
        ctx = "\n".join(f"- {c}" for c in context[:10])
        user = f"【参考资料】\n{ctx}\n\n【任务】\n{user}"
    return system, user


llm_client = LLMClient()
