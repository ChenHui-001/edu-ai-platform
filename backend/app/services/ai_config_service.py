"""AI 大模型配置服务：管理员可在线配置 LLM 提供商、API Key、模型等，
保存到 sys_config 表，优先级高于 .env 环境变量，修改后无需重启容器。"""
from __future__ import annotations

from typing import Any, Dict, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logger import get_logger
from app.models import SysConfig

logger = get_logger("ai_config")

# sys_config 表中 AI 配置的 key 前缀
_PREFIX = "llm_"

# 可配置字段及其默认值（来自 settings 环境变量）
_FIELDS: Dict[str, Dict[str, Any]] = {
    "llm_enabled": {
        "key": "llm_enabled", "type": "bool", "default": str(settings.LLM_ENABLED),
        "label": "启用 AI 大模型", "description": "关闭后所有 AI 功能走规则引擎降级",
        "category": "ai", "is_public": True,
    },
    "llm_provider": {
        "key": "llm_provider", "type": "string", "default": settings.LLM_PROVIDER,
        "label": "大模型提供商", "description": "deepseek / qwen / openai / ollama / custom",
        "category": "ai", "is_public": True,
    },
    "llm_api_key": {
        "key": "llm_api_key", "type": "string", "default": settings.LLM_API_KEY,
        "label": "API Key", "description": "大模型服务密钥（敏感信息，不对外公开）",
        "category": "ai", "is_public": False,
    },
    "llm_base_url": {
        "key": "llm_base_url", "type": "string", "default": settings.LLM_BASE_URL,
        "label": "API 地址", "description": "OpenAI 兼容协议的 base URL",
        "category": "ai", "is_public": True,
    },
    "llm_model": {
        "key": "llm_model", "type": "string", "default": settings.LLM_MODEL,
        "label": "模型名称", "description": "如 deepseek-chat / qwen-plus / gpt-4o-mini",
        "category": "ai", "is_public": True,
    },
    "llm_temperature": {
        "key": "llm_temperature", "type": "float", "default": str(settings.LLM_TEMPERATURE),
        "label": "温度参数", "description": "0~2，值越大回答越有创造性",
        "category": "ai", "is_public": True,
    },
    "llm_max_tokens": {
        "key": "llm_max_tokens", "type": "int", "default": str(settings.LLM_MAX_TOKENS),
        "label": "最大输出长度", "description": "单次回答的最大 token 数",
        "category": "ai", "is_public": True,
    },
    "llm_timeout": {
        "key": "llm_timeout", "type": "int", "default": str(settings.LLM_TIMEOUT),
        "label": "超时时间(秒)", "description": "单次请求超时时间",
        "category": "ai", "is_public": True,
    },
}

# 提供商预设
PROVIDER_PRESETS = {
    "deepseek": {
        "base_url": "https://api.deepseek.com/v1",
        "model": "deepseek-chat",
        "label": "DeepSeek（深度求索）",
    },
    "qwen": {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model": "qwen-plus",
        "label": "通义千问（阿里云）",
    },
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-4o-mini",
        "label": "OpenAI（GPT 系列）",
    },
    "ollama": {
        "base_url": "http://localhost:11434/v1",
        "model": "qwen2:7b",
        "label": "Ollama（本地部署）",
    },
    "custom": {
        "base_url": "",
        "model": "",
        "label": "自定义（OpenAI 兼容协议）",
    },
}


def _cast(value: Optional[str], value_type: str) -> Any:
    """把 sys_config 中的字符串值转为 Python 类型。"""
    if value is None or value == "":
        return None
    if value_type == "bool":
        return value.lower() in ("true", "1", "yes", "on")
    if value_type == "int":
        try:
            return int(value)
        except ValueError:
            return 0
    if value_type == "float":
        try:
            return float(value)
        except ValueError:
            return 0.0
    return value


def get_ai_config(db: Session) -> Dict[str, Any]:
    """读取当前 AI 配置：sys_config 表 > settings 环境变量。"""
    rows = {
        r.key: r for r in db.scalars(
            select(SysConfig).where(SysConfig.key.like(f"{_PREFIX}%"))
        ).all()
    }

    config = {}
    meta = {}
    for key, spec in _FIELDS.items():
        row = rows.get(key)
        if row is not None:
            val = _cast(row.value, row.value_type or spec["type"])
        else:
            val = _cast(spec["default"], spec["type"])
        config[key.upper()] = val
        meta[key] = {
            "label": spec["label"],
            "description": spec["description"],
            "category": spec["category"],
            "is_public": spec["is_public"],
            "has_db_value": row is not None,
        }

    return {
        "config": config,
        "meta": meta,
        "providers": PROVIDER_PRESETS,
    }


def save_ai_config(db: Session, data: Dict[str, Any], admin_id: int) -> Dict[str, Any]:
    """保存 AI 配置到 sys_config 表，并触发 LLM 客户端重载。"""
    updated = []
    for key, spec in _FIELDS.items():
        # 接收字段名不区分大小写（前端传 llm_provider 或 LLM_PROVIDER 均可）
        raw = data.get(key) or data.get(key.upper())
        if raw is None:
            continue
        # 转为字符串存储
        if isinstance(raw, bool):
            val = "true" if raw else "false"
        else:
            val = str(raw)

        row = db.scalar(select(SysConfig).where(SysConfig.key == key))
        if row:
            row.value = val
            row.value_type = spec["type"]
            row.label = spec["label"]
            row.description = spec["description"]
            row.category = spec["category"]
            row.is_public = spec["is_public"]
            row.updated_by = admin_id
        else:
            row = SysConfig(
                key=key, value=val, value_type=spec["type"],
                label=spec["label"], description=spec["description"],
                category=spec["category"], is_public=spec["is_public"],
                updated_by=admin_id,
            )
            db.add(row)
        updated.append(key)

    db.commit()

    # 触发 LLM 客户端重载（清除缓存的客户端实例，下次调用时重建）
    _reload_llm_client()

    logger.info(f"AI 配置已更新 by user#{admin_id}: {updated}")
    return {"updated": updated, "count": len(updated)}


def _reload_llm_client() -> None:
    """清除 LLM 客户端缓存，使新配置在下次调用时生效。"""
    try:
        from app.agents.llm import llm_client
        llm_client._client = None
        llm_client._fallback_reason = ""
        logger.info("LLM 客户端已重载，等待下次调用时生效新配置")
    except Exception as exc:
        logger.warning(f"重载 LLM 客户端失败: {exc}")


def test_ai_connection(data: Dict[str, Any]) -> Dict[str, Any]:
    """用给定配置测试 LLM 连接（不写入数据库，直接临时调用一次）。"""
    provider = data.get("llm_provider") or data.get("LLM_PROVIDER") or "deepseek"
    api_key = data.get("llm_api_key") or data.get("LLM_API_KEY") or ""
    base_url = data.get("llm_base_url") or data.get("LLM_BASE_URL") or ""
    model = data.get("llm_model") or data.get("LLM_MODEL") or ""

    if not api_key and provider != "ollama":
        return {
            "success": False,
            "message": f"未配置 API Key，{PROVIDER_PRESETS.get(provider, {}).get('label', provider)} 无法连接",
        }

    # 补充默认值
    preset = PROVIDER_PRESETS.get(provider, PROVIDER_PRESETS["deepseek"])
    if not base_url:
        base_url = preset["base_url"]
    if not model:
        model = preset["model"]

    try:
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import HumanMessage

        client = ChatOpenAI(
            api_key=api_key or "ollama",  # ollama 不需要 key
            base_url=base_url,
            model=model,
            temperature=0.1,
            max_tokens=50,
            timeout=15,
        )
        resp = client.invoke([HumanMessage(content="请回复：连接成功")])
        content = str(resp.content)[:200]
        usage = getattr(resp, "usage_metadata", None) or {}

        return {
            "success": True,
            "message": f"连接成功，模型 {model} 回复：{content}",
            "model": model,
            "base_url": base_url,
            "usage": {
                "input_tokens": usage.get("input_tokens", 0),
                "output_tokens": usage.get("output_tokens", 0),
            },
        }
    except ImportError:
        return {
            "success": False,
            "message": "langchain-openai 未安装，无法测试连接。请确认依赖已安装。",
        }
    except Exception as exc:
        msg = str(exc)
        # 常见错误精简
        if "401" in msg or "Unauthorized" in msg or "invalid_api_key" in msg:
            return {"success": False, "message": f"API Key 无效或已过期：{msg[:150]}"}
        if "Connection" in msg or "connect" in msg.lower() or "timed out" in msg.lower():
            return {"success": False, "message": f"网络连接失败，请检查 Base URL：{msg[:150]}"}
        return {"success": False, "message": f"连接测试失败：{msg[:200]}"}
