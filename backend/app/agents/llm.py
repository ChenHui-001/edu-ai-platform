"""大模型接入层：兼容通义千问 / DeepSeek / OpenAI / 本地 Ollama 协议。

未配置 API Key 时自动降级为规则引擎，保证系统始终可用（离线部署场景）。
"""
import json
import re
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.core.logger import get_logger
from app.models import AgentCallLog
from app.utils.common import utcnow

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
    """LLM 是否可用。未配置 Key 时走规则引擎。"""
    enabled = _get_db_value("llm_enabled", "bool", settings.LLM_ENABLED)
    api_key = _get_db_value("llm_api_key", "string", settings.LLM_API_KEY)
    return bool(enabled and api_key)


def _get_db_value(key: str, value_type: str, default: Any) -> Any:
    """从 sys_config 表读取配置值，优先级高于 settings。失败则回退到 settings。"""
    try:
        from app.core.database import SessionLocal
        from app.models import SysConfig
        from sqlalchemy import select

        with SessionLocal() as db:
            row = db.scalar(select(SysConfig).where(SysConfig.key == key))
            if row is None or row.value is None or row.value == "":
                return default
            val = row.value
            if value_type == "bool":
                return val.lower() in ("true", "1", "yes", "on")
            if value_type == "int":
                try:
                    return int(val)
                except ValueError:
                    return default
            if value_type == "float":
                try:
                    return float(val)
                except ValueError:
                    return default
            return val
    except Exception:
        return default


class LLMClient:
    """OpenAI 兼容协议客户端，懒加载 langchain-openai。"""

    def __init__(self):
        self._client = None
        self._fallback_reason = ""

    @property
    def provider_cfg(self) -> Dict[str, Any]:
        provider = _get_db_value("llm_provider", "string", settings.LLM_PROVIDER)
        return PROVIDERS.get(provider, PROVIDERS["deepseek"])

    def get_client(self):
        """获取 LangChain ChatOpenAI 实例（失败返回 None）。"""
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
    """写入 AI 调用日志。"""
    try:
        from app.core.database import SessionLocal

        with SessionLocal() as db:
            db.add(
                AgentCallLog(
                    agent_name=agent_name, user_id=user_id,
                    input_text=input_text, output_text=output_text,
                    input_tokens=input_tokens, output_tokens=output_tokens,
                    duration_ms=duration_ms, status=status, error_msg=error_msg,
                    is_fallback=is_fallback, biz_type=biz_type, biz_id=biz_id,
                )
            )
            db.commit()
    except Exception as exc:  # 日志失败不影响主流程
        logger.warning(f"Agent 调用日志写入失败: {exc}")


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
