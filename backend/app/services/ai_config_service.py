"""AI 大模型配置服务：管理员可在线配置 LLM 提供商、API Key、模型等，
保存到 sys_config 表，优先级高于 .env 环境变量，修改后无需重启容器。"""
from __future__ import annotations

from typing import Any, Dict, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exception import BusinessException
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
    """读取当前 AI 配置：sys_config 表 > settings 环境变量。

    注意：max_tokens 施加硬上限。降低默认值（4096→2048）后，**已有库里的旧值
    会继续覆盖新默认值**，优化静默失效（实测 DB 内残留 4096，UI 也显示 4096）。
    因此这里对超出 settings 上限的值做收敛，并在 meta 标记 capped。
    """
    rows = {
        r.key: r for r in db.scalars(
            select(SysConfig).where(SysConfig.key.like(f"{_PREFIX}%"))
        ).all()
    }

    caps = {"llm_max_tokens": int(settings.LLM_MAX_TOKENS or 0)}

    config = {}
    meta = {}
    for key, spec in _FIELDS.items():
        row = rows.get(key)
        if row is not None:
            val = _cast(row.value, row.value_type or spec["type"])
        else:
            val = _cast(spec["default"], spec["type"])
        capped = False
        cap = caps.get(key)
        if cap and isinstance(val, int) and val > cap:
            val = cap
            capped = True
        # 密钥字段脱敏返回：管理员页面/浏览器网络面板不再出现完整凭据
        if "key" in key.lower() and val:
            sv = str(val)
            config[key.upper()] = (sv if len(sv) <= 8 else f"{sv[:4]}****{sv[-4:]}")
        else:
            config[key.upper()] = val
        meta[key] = {
            "label": spec["label"],
            "description": spec["description"],
            "category": spec["category"],
            "is_public": spec["is_public"],
            "has_db_value": row is not None,
            "capped": capped,
            "cap": cap if capped else None,
        }

    return {
        "config": config,
        "meta": meta,
        "providers": PROVIDER_PRESETS,
    }


def save_ai_config(db: Session, data: Dict[str, Any], admin_id: int) -> Dict[str, Any]:
    """保存 AI 配置到 sys_config 表，并触发 LLM 客户端重载。"""
    # 数值范围校验：temperature=0/负数、max_tokens=0、timeout=0 会让 LLM
    # 调用直接异常且难以定位；在入口统一拒绝（掩码回传值跳过）。
    ranges = {
        "llm_temperature": (0.0, 2.0, "温度参数"),
        "llm_max_tokens": (64, 8192, "最大输出长度"),
        "llm_timeout": (5, 600, "超时时间(秒)"),
    }
    for key, (low, high, label) in ranges.items():
        raw = data.get(key, data.get(key.upper()))
        if raw is None:
            continue
        text_value = str(raw)
        if "****" in text_value:
            continue
        try:
            number = float(text_value)
        except (TypeError, ValueError):
            raise BusinessException(f"{label}必须是数字") from None
        if not (low <= number <= high):
            raise BusinessException(f"{label}应在 {low}~{high} 之间，当前 {number}")
    provider = data.get("llm_provider", data.get("LLM_PROVIDER"))
    if provider is not None and str(provider) not in set(PROVIDER_PRESETS) | {"custom"}:
        raise BusinessException(
            f"不支持的模型提供商 {provider!r}，可选：{'/'.join(sorted(PROVIDER_PRESETS))}/custom"
        )

    updated = []
    for key, spec in _FIELDS.items():
        # 接收字段名不区分大小写（前端传 llm_provider 或 LLM_PROVIDER 均可）。
        # 必须按「键是否存在」判断，不能用 `data.get(key) or data.get(key.upper())`：
        # 空字符串是**合法的清空意图**，`or` 会把它当成「未传」而 `continue`，
        # 结果是 API 无法清空密钥 —— 请求返回 success 且 updated 里还有这个 key，
        # 管理员以为已清除，实际旧密钥仍生效（曾导致测试写入的假 Key 永久留在库里）。
        if key in data:
            raw = data[key]
        elif key.upper() in data:
            raw = data[key.upper()]
        else:
            continue
        if raw is None:
            continue
        # 转为字符串存储
        if isinstance(raw, bool):
            val = "true" if raw else "false"
        else:
            val = str(raw)
        # 前端回传的掩码值（含 ****）表示「未修改」，不能写回数据库覆盖真实 key
        if "****" in val:
            continue

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
    """清除 LLM 客户端缓存，使新配置在下次调用时生效。

    必须同时清除**熔断状态**：熔断是对「这份密钥无效」的判定，
    管理员改了密钥后该判定立即失效，否则改对了也一直走规则引擎降级，
    表现为「配置保存成功但 AI 永远不工作」。

    B1 之后熔断状态**不在实例上**了（`services/llm_breaker` 单行表 +
    模块级镜像），所以这里分两件事做：

    1. `llm_breaker.reset_all()` —— 清 DB 行 + 本地镜像（**跨进程立即解除**）；
    2. 清各实例的 `_client` / `_fallback_reason` —— 这两个仍是进程内缓存
       （连接池与最近降级原因），必须重建才能用上新密钥。

    仍然遍历两个实例：虽然熔断已共享，但 `_client`（连接池）是各实例自己的，
    只清一个会出现「部分功能用新密钥、部分用旧连接 + 旧 base_url」的鬼现象。
    """
    try:
        from app.agents import llm as _llm_mod
        from app.services import llm_breaker

        # 先清熔断：让下次 get_client() 的判定立刻放行（同步执行，见其 docstring）。
        llm_breaker.reset_all()

        targets = [_llm_mod.llm_client]
        while_single = getattr(_llm_mod, "_llm_singleton", None)
        if while_single is not None and while_single is not _llm_mod.llm_client:
            targets.append(while_single)
        for c in targets:
            c._client = None
            c._fallback_reason = ""
        logger.info(f"LLM 客户端已重载（{len(targets)} 个实例，熔断/冷却已跨进程复位）")
    except Exception as exc:
        logger.warning(f"重载 LLM 客户端失败: {exc}")


def _db_config_value(db: Optional[Session], key: str, default: Any) -> Any:
    """读取 sys_config 配置值（DB > env）。

    测试连接时前端不回显真实 key，只回传掩码/空值，因此必须能从已保存配置
    取值；显式清空的 `llm_api_key`（value=""）表示管理员关闭了 AI，不能再
    回落到 .env 的旧 key。
    """
    if db is None:
        try:
            from app.agents.llm import _get_db_value

            return _get_db_value(key, "string", default)
        except Exception:  # noqa: BLE001  配置读取失败不应让测试接口 500
            return default
    try:
        row = db.scalar(select(SysConfig).where(SysConfig.key == key))
        if row is None:
            return default
        if row.value is None or row.value == "":
            return "" if key == "llm_api_key" else default
        return row.value
    except Exception:  # noqa: BLE001
        return default


def test_ai_connection(
    data: Dict[str, Any], db: Optional[Session] = None,
) -> Dict[str, Any]:
    """用给定配置测试 LLM 连接（不写入数据库，直接临时调用一次）。

    前端配置页不会把已保存的 API Key 回显到输入框，所以 `llm_api_key`
    为空或含掩码 `****` 时要从 sys_config（已保存配置）读取真实 key；
    显式清空（DB 值为空串）则视为未配置。返回 `duration_ms` 供 UI 展示耗时。
    """
    import time

    started = time.perf_counter()

    def _done(payload: Dict[str, Any]) -> Dict[str, Any]:
        payload["duration_ms"] = int((time.perf_counter() - started) * 1000)
        return payload

    def _pick(*names: str) -> Optional[str]:
        """取显式传入的参数；None 视为未传，空串视为显式空值。"""
        for name in names:
            if name in data and data.get(name) is not None:
                return str(data.get(name)).strip()
        return None

    provider = _pick("llm_provider", "LLM_PROVIDER")
    if not provider:
        provider = str(_db_config_value(
            db, "llm_provider", settings.LLM_PROVIDER) or settings.LLM_PROVIDER).strip()

    api_key = _pick("llm_api_key", "LLM_API_KEY") or ""
    if not api_key or "****" in api_key:
        # 掩码/空值 = 使用已保存的 key；DB 显式空串则表示已清除，不回落到 env
        api_key = str(_db_config_value(
            db, "llm_api_key", settings.LLM_API_KEY) or "").strip()

    # base_url：显式传入（含空串）优先；未传时取 DB 已保存值，非 custom
    # 提供商再回退 .env（custom 不能拿 .env 里别的厂商地址冒充有效配置）
    base_url = _pick("llm_base_url", "LLM_BASE_URL")
    if base_url is None:
        saved_base = str(_db_config_value(db, "llm_base_url", "") or "").strip()
        base_url = saved_base or (
            str(settings.LLM_BASE_URL or "").strip() if provider != "custom" else "")

    model = _pick("llm_model", "LLM_MODEL")
    if not model:
        model = str(_db_config_value(
            db, "llm_model", settings.LLM_MODEL) or "").strip()

    if not api_key and provider != "ollama":
        return _done({
            "success": False,
            "message": f"未配置 API Key，{PROVIDER_PRESETS.get(provider, {}).get('label', provider)} 无法连接",
        })

    # 补充默认值
    preset = PROVIDER_PRESETS.get(provider) or PROVIDER_PRESETS["custom"]
    if not base_url:
        base_url = preset["base_url"]
    if not model:
        model = preset["model"]
    if not base_url:
        return _done({
            "success": False,
            "message": "自定义提供商必须填写 API 地址（llm_base_url）",
        })

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

        return _done({
            "success": True,
            "message": f"连接成功，模型 {model} 回复：{content}",
            "model": model,
            "base_url": base_url,
            "usage": {
                "input_tokens": usage.get("input_tokens", 0),
                "output_tokens": usage.get("output_tokens", 0),
            },
        })
    except ImportError:
        return _done({
            "success": False,
            "message": "langchain-openai 未安装，无法测试连接。请确认依赖已安装。",
        })
    except Exception as exc:
        msg = str(exc)
        # 常见错误精简
        if "401" in msg or "Unauthorized" in msg or "invalid_api_key" in msg:
            return _done({"success": False, "message": f"API Key 无效或已过期：{msg[:150]}"})
        if "Connection" in msg or "connect" in msg.lower() or "timed out" in msg.lower():
            return _done({"success": False, "message": f"网络连接失败，请检查 Base URL：{msg[:150]}"})
        return _done({"success": False, "message": f"连接测试失败：{msg[:200]}"})