"""大模型接入层：兼容通义千问 / DeepSeek / OpenAI / 本地 Ollama 协议。

未配置 API Key 时自动降级为规则引擎，保证系统始终可用（离线部署场景）。
"""
import json
import re
import threading
from datetime import timedelta
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.core.logger import get_logger
from app.models import AgentCallLog
from app.services import llm_breaker
from app.utils.common import now_local

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
    """LLM 是否可用。未配置 Key 或**鉴权已熔断**时走规则引擎。

    限流冷却（429/quota）**不改变本函数语义**：冷却只让 get_client() 短路，
    「已配置密钥」这一事实仍然成立。否则一次限流就会让状态接口/健康检查
    长期报 llm_enabled=false，看起来像配置丢失。鉴权失败（401/403）属于
    配置错误，必须持久反映为不可用，直到管理员改配置触发重载。

    B1 之后熔断状态是**进程无关**的（`services/llm_breaker`）：
    不再需要遍历 `(_llm_singleton, llm_client)` 两个实例各查一遍 ——
    两份实例状态曾经会不同步（一处熔断、另一处还在用无效密钥撞 401），
    现在全进程只有一份本地镜像 + 一份 DB 行，天然一致。
    """
    from app.services import llm_breaker

    if llm_breaker.auth_disabled():
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
            # 显式清空 API Key 必须生效：管理员在配置页把密钥清空，
            # 语义是「关闭 AI」；此前空串会回落到 .env 的 LLM_API_KEY，
            # 导致 UI 显示已清空、实际旧 Key 仍在使用。
            if key == "llm_api_key" and row is not None and raw == "":
                return ""
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
    直到管理员改配置（`llm_breaker.reset_all()` 清空熔断状态）。

    限流冷却（P1）：429 / RATE_LIMITED / quota 是**暂态**故障 —— 配额按分钟
    或按日恢复，长时间永久熔断会让 AI 一整天不可用，只能等管理员手动保存配置。
    因此改「永久熔断」为**指数退避冷却**：30s → 60s → 120s → 240s → 300s（上限）。
    冷却期内 `get_client()` 返回 None 并写入 `_fallback_reason`（含剩余秒数），
    到期后自动恢复真实调用；只要有一次调用成功，退避计数与冷却立即清零。

    熔断状态的**存储位置**（B1）：`services/llm_breaker` —— 模块级本地镜像
    （同进程立刻生效）+ `sys_llm_breaker` 单行表（跨进程/跨 worker 生效）。
    不再放实例属性：进程里有两个 `LLMClient()` 实例，各熔各的会漏。
    """

    # 鉴权失败特征：401/403、密钥无效。命中 → 永久熔断（直到管理员改配置）。
    _AUTH_ERROR_MARKS = ("401", "403", "UNAUTHORIZED", "Unauthorized",
                         "invalid_api_key", "Incorrect API key", "authentication")
    # 限流/配额特征：命中 → 冷却退避（可自动恢复），**不**写 _disabled_reason。
    _RATE_LIMIT_MARKS = ("429", "RATE_LIMITED", "rate limit", "Rate limit",
                         "too many requests", "Too Many Requests",
                         "配额", "quota")

    # 冷却退避：30 * 2^(n-1)，上限 300s，避免一次 429 导致全天不可用
    _COOLDOWN_BASE_SECONDS = 30
    _COOLDOWN_MAX_SECONDS = 300

    def __init__(self):
        self._client = None
        self._fallback_reason = ""
        # 熔断/冷却状态**不在实例上**了（B1）。它曾经是：
        #     self._disabled_reason = ""     # 鉴权熔断（401/403，永久）
        #     self._cooldown_until = 0.0     # 限流冷却（429，指数退避，monotonic）
        #     self._rate_limit_streak = 0
        # 三个问题：
        # 1. 进程里有**两个实例**（模块级 llm_client 与 get_llm() 单例），
        #    各熔各的 → 一处熔断、另一处继续撞 401，另半边功能静默拖慢；
        # 2. 多 worker 时各进程各熔各的 → N 倍无谓 401 往返；
        # 3. `_cooldown_until` 存 `time.monotonic()`，跨进程比较无意义。
        # 现在统一走 `services/llm_breaker`（单行表 + 模块级本地镜像）。
        # 实例上只保留 `_client` 与 `_fallback_reason` —— 这两个才是真正的
        # 进程内缓存（连接池与最近一次降级原因），不需要跨进程。
        from app.services import llm_breaker  # noqa: F401  确保模块可导入

    @property
    def provider_cfg(self) -> Dict[str, Any]:
        provider = _get_db_value("llm_provider", "string", settings.LLM_PROVIDER)
        return PROVIDERS.get(provider, PROVIDERS["deepseek"])

    def _is_auth_error(self, exc: Exception) -> bool:
        msg = str(exc)
        return any(m in msg for m in self._AUTH_ERROR_MARKS)

    def _is_rate_limit_error(self, exc: Exception) -> bool:
        msg = str(exc)
        return any(m in msg for m in self._RATE_LIMIT_MARKS)

    def _cooldown_remaining(self) -> int:
        """剩余冷却秒数（向上取整）；0 表示未处于冷却期。

        B1：状态来自 `services/llm_breaker`（本地镜像 + DB 合并），
        不再读实例上的 monotonic 时间戳 —— 跨进程比较时那是错的。
        """
        state = llm_breaker.load()
        if not state or state["kind"] != llm_breaker.KIND_RATE_LIMIT:
            return 0
        expire = state["expire_at"]
        if not expire:
            return 0
        left = (expire - now_local()).total_seconds()
        if left <= 0:
            # 冷却自然到期：清掉状态，退避计数保留到下一次成功再清零
            llm_breaker.clear_rate_limit_async()
            return 0
        return int(left + 0.999)

    def _mark_disabled(self, exc: Exception) -> None:
        """鉴权失败：永久熔断，直到管理员改配置（`reset_all` 复位）。"""
        reason = (
            f"LLM 密钥无效或已过期（{str(exc)[:80]}），已暂停真实调用，"
            "请到「系统管理 → AI 配置」更新密钥后重试")
        # 鉴权错误优先于限流：`save_auth` 内部会清掉 cooling 语义
        # （auth 行 expire_at 恒为 NULL，见 models/ops.py:LlmBreakerState）。
        llm_breaker.save_auth(reason)
        logger.warning(reason)

    def _start_rate_limit_cooldown(self, exc: Exception) -> None:
        """限流/配额不足：进入指数退避冷却，到期自动恢复。

        streak 从**当前共享状态**读回再 +1（而不是实例自增）：
        各进程各自自增会互相覆盖成 1、2、1、2，退避永远停在 30s。
        DB 侧由 `llm_breaker` 用一条 `streak = streak + 1` 原子递增，
        本地镜像用这里算出的同源值，两者不会漂移。
        """
        state = llm_breaker.load()
        streak = 1
        if state and state["kind"] == llm_breaker.KIND_RATE_LIMIT:
            streak = max(1, int(state["streak"] or 0) + 1)
        backoff = min(
            self._COOLDOWN_MAX_SECONDS,
            self._COOLDOWN_BASE_SECONDS * (2 ** (streak - 1)),
        )
        llm_breaker.save_rate_limit(
            f"LLM 限流/配额不足（{str(exc)[:80]}），冷却 {backoff}s",
            self._COOLDOWN_BASE_SECONDS, self._COOLDOWN_MAX_SECONDS,
            streak=streak, expire_at=now_local() + timedelta(seconds=backoff),
        )
        logger.warning(
            f"LLM 限流/配额不足（{str(exc)[:80]}），进入冷却退避 {backoff}s"
            f"（连续第 {streak} 次），冷却期内走规则引擎降级")

    def _reset_rate_limit(self) -> None:
        """调用成功后清空限流冷却与退避计数（**不动 auth 熔断**）。"""
        state = llm_breaker.load()
        if state and state["kind"] == llm_breaker.KIND_RATE_LIMIT:
            logger.info("LLM 调用成功，限流冷却与退避计数已清零")
            llm_breaker.clear_rate_limit_async()

    def get_client(self):
        """获取 LangChain ChatOpenAI 实例（失败返回 None）。

        检查顺序很重要：**熔断/冷却判断必须在返回缓存客户端之前**。
        反过来的话，进程里已有 `_client` 时永远查不到熔断标记，
        熔断形同虚设（实测：写入无效密钥后交卷仍耗时 105s）。
        """
        # 鉴权熔断优先级最高：已确认配置无效，连缓存客户端也不能用。
        # B1：状态来自共享层（本地镜像立刻生效 + DB 跨进程生效），
        # 不再读实例属性 —— 那两个实例各自的 `_disabled_reason` 曾经会不同步。
        state = llm_breaker.load()
        if state and state["kind"] == llm_breaker.KIND_AUTH:
            self._fallback_reason = state["reason"]
            return None
        # 限流冷却：暂态故障，冷却期内短路；到期后自动恢复真实调用
        if state and state["kind"] == llm_breaker.KIND_RATE_LIMIT:
            remaining = self._cooldown_remaining()
            if remaining > 0:
                self._fallback_reason = (
                    f"LLM 限流冷却中，约 {remaining}s 后自动恢复"
                    f"（连续第 {state['streak']} 次退避，期间使用规则引擎）")
                logger.warning(self._fallback_reason)
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
                # 显式限制重试：langchain-openai 默认 max_retries=2，
                # 配合 60s 超时会把单次交卷放大到最坏 180s。
                max_retries=1,
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
            # 真实调用成功 → 限流冷却与退避计数清零（此前可能因 429 处于冷却，
            # 恢复后要立刻回到正常路径，不能继续按旧退避成长）
            self._reset_rate_limit()
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
            # 鉴权失败立即永久熔断：同一份无效密钥重试必然还是失败，
            # 不熔断就会让「一份 6 道主观题的卷子」白等 6 轮网络往返。
            # 限流/配额是暂态故障，改为冷却退避：到期自动恢复，不再永久禁用。
            if self._is_auth_error(exc):
                self._mark_disabled(exc)
            elif self._is_rate_limit_error(exc):
                self._start_rate_limit_cooldown(exc)
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
            # 流式调用完整成功 → 同步清空限流冷却
            self._reset_rate_limit()
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
            # 占位符必须是 `{}`：项目 logger 是 Loguru（app/core/logger），
            # 用 stdlib 的 `%s` 不会报错，但模板与参数**双双被丢弃** ——
            # 日志里留下字面量 "%s"，真正的 agent_name 与异常信息全部丢失。
            logger.error("LLM 流式调用失败 [{}]: {}", agent_name, exc)
            # 与 chat() 一致：鉴权失败永久熔断；限流/配额改为冷却退避
            if self._is_auth_error(exc):
                self._mark_disabled(exc)
            elif self._is_rate_limit_error(exc):
                self._start_rate_limit_cooldown(exc)
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
# 尾随逗号：模型输出 JSON 数组/对象末尾经常多打一个逗号（如 {"a":1,}），
# 标准 JSON 解析器直接报错 → 明明有完整输出却被判为「无法解析」→ 静默降级。
_TRAILING_COMMA = re.compile(r",\s*([}\]])")


def _loads_lenient(text: str) -> Optional[Any]:
    """宽容 JSON 解析：先原样解析，失败则去掉尾随逗号再解析。"""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    fixed = _TRAILING_COMMA.sub(r"\1", text)
    if fixed != text:
        try:
            return json.loads(fixed)
        except json.JSONDecodeError:
            pass
    return None


def _find_balanced(text: str, open_ch: str, close_ch: str) -> Optional[str]:
    """从 text 中提取第一个**结构完整**的 JSON 片段（括号配对，跳过字符串内容）。

    不用贪婪正则 r'\\[[\\s\\S]*\\]'：输出被 max_tokens 截断时，贪婪正则会
    匹配到「半个数组」，再从残缺数组里捞出一个完整的小对象，把「输出被截断」
    伪装成「解析成功但内容为空」——上层拿到空题目却不报错。配对扫描只接受
    结构闭合的片段，截断时返回 None，交给上层按「解析失败」处理。
    """
    start = text.find(open_ch)
    if start < 0:
        return None
    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == open_ch:
            depth += 1
        elif ch == close_ch:
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    return None


def extract_json(content: str) -> Optional[Any]:
    """从模型输出中提取 JSON（兼容 ```json 包裹、额外文字、尾随逗号）。"""
    if not content:
        return None
    text = content.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.MULTILINE).strip()
    parsed = _loads_lenient(text)
    if parsed is not None:
        return parsed
    # 模型常在 JSON 前后夹带说明文字。按「首个完整片段」提取：
    # 文本以 [ 或 { 开头时只找同类型的外层结构（被截断就找不到 → 判失败），
    # 否则两种都找（兼容「说明 + JSON + 说明」）。
    stripped = text.lstrip()
    if stripped.startswith("["):
        candidates = (("[", "]"),)
    elif stripped.startswith("{"):
        candidates = (("{", "}"),)
    else:
        candidates = (("[", "]"), ("{", "}"))
    for open_ch, close_ch in candidates:
        snippet = _find_balanced(text, open_ch, close_ch)
        if snippet:
            parsed = _loads_lenient(snippet)
            if parsed is not None:
                return parsed
    return None


def build_messages(system: str, user: str, context: Optional[List[str]] = None) -> tuple:
    """拼装上下文消息。"""
    if context:
        ctx = "\n".join(f"- {c}" for c in context[:10])
        user = f"【参考资料】\n{ctx}\n\n【任务】\n{user}"
    return system, user


llm_client = LLMClient()
