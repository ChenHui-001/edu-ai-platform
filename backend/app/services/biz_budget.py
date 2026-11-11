"""按 `biz_type` 细化 LLM 预算（F-06）。

## 为什么需要

全局只有一套 `llm_temperature` / `llm_max_tokens`，但各业务对这两项的要求
互相冲突：

- **出题**（`question_generate`）：要低温度（题干稳定、不代表达意就不该发散）
  和大预算（一次要出 JSON 数组，多道题的题干+选项+解析）；
- **路由**（`router`）：只要输出一个 JSON 意图对象，几百 token 就够；
  按出题的预算给它，等于每次多花钱买一段没人看的空白；
- **答疑**（`tutor`）：要高一点温度（讲解自然）但不能太长；
- **批改**（`grading`）：低温度 + 中等预算。

一刀切只能互相将就：把全局温度压到 0.3 救出题，答疑就变得生硬；把
`max_tokens` 调到 8192 救解答题，路由任务每次也按 8192 预留。

## 存哪、长什么样

`sys_config.llm_biz_budgets`，**JSON 对象**（存字符串）：

```json
{"question_generate": {"temperature": 0.3, "max_tokens": 6144},
 "router": {"max_tokens": 256},
 "grading": {"reasoning_effort": "low"}}
```

三个字段都可选，也可以只配其中一个 `biz_type`。**没配的 biz_type 走全局配置**
（行为与改动前完全一致），所以这个功能天然可回滚：清空该配置即恢复原状。

## 为什么只允许 temperature / max_tokens / reasoning_effort

模型与地址的粒度已经由「场景路由」承担（`llm_model_fast` / `llm_base_url_fast`）。
再按 biz_type 分模型，会让「这个请求到底用了哪个模型」在每个业务上都不一样，
排障成本陡增，而收益只是省钱 —— 那不是这一步要解决的问题。

## `max_tokens` 仍受代码级硬顶约束

这里只做 64~32768 的**基本合法性**校验；真正的上限由
`agents/llm._apply_cap` 在读取处收敛（`settings.LLM_MAX_TOKENS` 是代码级硬顶，
DB 里的更大值一律被压回）。放在读取处而不是这里，是为了让「改硬顶」只有
一个地方要改，也不必让本模块依赖 settings。
"""
import json
from typing import Any, Dict, Iterable, Optional

# sys_config 里的键名
CONFIG_KEY = "llm_biz_budgets"

F_TEMPERATURE = "temperature"
F_MAX_TOKENS = "max_tokens"
F_EFFORT = "reasoning_effort"

# 允许出现的字段（多余字段一律拒绝，不静默忽略）
ALLOWED_FIELDS = (F_TEMPERATURE, F_MAX_TOKENS, F_EFFORT)

TEMPERATURE_RANGE = (0.0, 2.0)
MAX_TOKENS_RANGE = (64, 32768)
# 空串是**有意义**的取值：表示「这个 biz_type 显式不带 reasoning_effort」，
# 用来抵消场景级 `llm_fast_reasoning_effort` 的默认值（例如某个网关对
# effort 字段报错，但别的 biz_type 又想用）。
ALLOWED_EFFORTS = ("", "minimal", "low", "medium", "high")

# 已知 biz_type：仅用于前端下拉与提示，**不是白名单** ——
# biz_type 是调用方自由字符串，未列出的照样可以配（写进覆盖表即可生效）。
KNOWN_BIZ_TYPES = (
    "question_generate",
    "question_variants",
    "grading",
    "paper_parse",
    "lesson_head",
    "lesson_body",
    "study_plan",
    "tutor",
    "router",
    "note",
)


class BizBudgetError(ValueError):
    """覆盖表格式非法。消息可直接展示给管理员。"""


def _as_number(value: Any, field: str, biz_type: str) -> Any:
    # bool 是 int 的子类，`{"max_tokens": true}` 会被当成 1 —— 必须显式排除
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise BizBudgetError(f"{biz_type}.{field} 必须是数字，当前 {value!r}")
    return value


def _normalize_one(biz_type: str, spec: Any) -> Dict[str, Any]:
    if not isinstance(spec, dict):
        raise BizBudgetError(f"{biz_type} 的配置必须是对象，当前 {type(spec).__name__}")
    unknown = sorted(set(spec) - set(ALLOWED_FIELDS))
    if unknown:
        raise BizBudgetError(
            f"{biz_type} 含未知字段 {unknown}；只支持 {list(ALLOWED_FIELDS)}")
    out: Dict[str, Any] = {}
    if F_TEMPERATURE in spec:
        val = _as_number(spec[F_TEMPERATURE], F_TEMPERATURE, biz_type)
        low, high = TEMPERATURE_RANGE
        if not (low <= float(val) <= high):
            raise BizBudgetError(f"{biz_type}.temperature 应在 {low}~{high}，当前 {val}")
        out[F_TEMPERATURE] = float(val)
    if F_MAX_TOKENS in spec:
        val = _as_number(spec[F_MAX_TOKENS], F_MAX_TOKENS, biz_type)
        low, high = MAX_TOKENS_RANGE
        if not (low <= int(val) <= high):
            raise BizBudgetError(f"{biz_type}.max_tokens 应在 {low}~{high}，当前 {val}")
        out[F_MAX_TOKENS] = int(val)
    if F_EFFORT in spec:
        val = spec[F_EFFORT]
        if not isinstance(val, str):
            raise BizBudgetError(f"{biz_type}.{F_EFFORT} 必须是字符串，当前 {val!r}")
        val = val.strip().lower()
        if val not in ALLOWED_EFFORTS:
            raise BizBudgetError(
                f"{biz_type}.{F_EFFORT} 只支持 {list(ALLOWED_EFFORTS)}，当前 {val!r}")
        out[F_EFFORT] = val
    return out


def normalize(raw: Any) -> Dict[str, Dict[str, Any]]:
    """把任意输入（JSON 串 / dict / None）规范成 `{biz_type: {字段: 值}}`。

    - `None` / 空串 / `{}` → `{}`（表示不使用覆盖）
    - 字段为空的 biz_type 会被丢弃（避免存一堆 `{}` 占位）
    - 非法输入抛 `BizBudgetError`，消息可直接给管理员看

    调用方（`agents/llm.resolve_biz_budget`）对异常的处理是**记 warning 后
    当没有配置**：一个写坏的覆盖表不应该让整站 AI 全部不可用。
    """
    if raw is None:
        return {}
    if isinstance(raw, str):
        text = raw.strip()
        if not text:
            return {}
        try:
            raw = json.loads(text)
        except json.JSONDecodeError as exc:
            raise BizBudgetError(f"不是合法 JSON：{exc.msg}（第 {exc.lineno} 行第 {exc.colno} 列）") from None
    if not isinstance(raw, dict):
        raise BizBudgetError(f"顶层必须是对象（biz_type → 配置），当前 {type(raw).__name__}")

    out: Dict[str, Dict[str, Any]] = {}
    for key, spec in raw.items():
        biz_type = str(key).strip()
        if not biz_type:
            raise BizBudgetError("biz_type 不能为空字符串")
        one = _normalize_one(biz_type, spec)
        if one:
            out[biz_type] = one
    return out


def dumps(table: Dict[str, Dict[str, Any]]) -> str:
    """规范化后写回 sys_config 的形态（空表存空串，语义等同"未配置"）。"""
    if not table:
        return ""
    return json.dumps(table, ensure_ascii=False, sort_keys=True)


def describe(table: Dict[str, Dict[str, Any]], biz_types: Optional[Iterable[str]] = None) -> str:
    """给日志/UI 用的一行摘要，例如 `question_generate(t=0.3, mt=6144); router(mt=256)`。"""
    parts = []
    for biz_type in sorted(table):
        spec = table[biz_type]
        bits = []
        if F_TEMPERATURE in spec:
            bits.append(f"t={spec[F_TEMPERATURE]}")
        if F_MAX_TOKENS in spec:
            bits.append(f"mt={spec[F_MAX_TOKENS]}")
        if F_EFFORT in spec:
            bits.append(f"effort={spec[F_EFFORT] or '-'}")
        parts.append(f"{biz_type}({', '.join(bits)})")
    return "; ".join(parts)
