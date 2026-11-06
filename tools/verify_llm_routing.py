#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""场景级模型路由（方案 C）回归验证 —— 不触真实大模型、不写库。

覆盖：
  1. biz_type 路由判定（快场景白名单 / 默认场景 / 关闭路由）
  2. 快场景带 reasoning_effort=low、默认场景不带
  3. llm_model_fast 为空时复用主模型；配置后只影响快场景
  4. 两个场景各自缓存、互不串味；reset_clients 全清
  5. 熔断短路在双场景缓存下仍然生效（不能绕过）
  6. chat() 确实把 biz_type 解析后的场景传给了 get_client

用法：python tools/verify_llm_routing.py
"""
import os
import sys
import types
from unittest.mock import MagicMock, patch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "backend"))

FAILED = []


def check(name, ok, detail=""):
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  -> {detail}" if detail else ""))
    if not ok:
        FAILED.append(name)
    return ok


# 本地可能没装 langchain_openai（验证只需要捕获构造参数，不需要真客户端）
try:
    import langchain_openai  # noqa: F401
except ImportError:
    _fake = types.ModuleType("langchain_openai")
    _fake.ChatOpenAI = MagicMock()
    sys.modules["langchain_openai"] = _fake

from app.agents import llm as llm_mod  # noqa: E402
from app.agents.llm import LLMClient, resolve_scenario  # noqa: E402

BASE = {
    "llm_provider": "custom",
    "llm_api_key": "unit-test-key",
    "llm_base_url": "https://unit.example/v1",
    "llm_model": "primary-model",
    "llm_model_fast": "",
    "llm_base_url_fast": "",
    "llm_fast_biz_types": "question_generate,question_variants",
    "llm_fast_reasoning_effort": "low",
}


class Probe:
    """在受控配置下构造客户端，记录 ChatOpenAI 的调用参数。"""

    def __init__(self, cfg=None, breaker=None):
        self.cfg = dict(BASE)
        self.cfg.update(cfg or {})
        self.breaker = breaker
        self.calls = []

    def __enter__(self):
        self.patches = [
            patch.object(llm_mod, "_get_db_value",
                         side_effect=lambda key, _t, default: self.cfg.get(key, default)),
            patch.object(llm_mod, "is_available", return_value=True),
            patch.object(llm_mod.llm_breaker, "load", return_value=self.breaker),
            patch("langchain_openai.ChatOpenAI", side_effect=self._factory),
        ]
        for p in self.patches:
            p.start()
        return self

    def _factory(self, **kwargs):
        self.calls.append(kwargs)
        return MagicMock(name="ChatOpenAI-%d" % len(self.calls))

    def __exit__(self, *args):
        for p in reversed(self.patches):
            p.stop()
        return False


def main():
    print("\n=== 1. biz_type 场景判定 ===")
    with Probe() as p:
        check("question_generate → fast",
              resolve_scenario("question_generate") == llm_mod.SCENARIO_FAST)
        check("question_variants → fast",
              resolve_scenario("question_variants") == llm_mod.SCENARIO_FAST)
        check("lesson_plan → default",
              resolve_scenario("lesson_plan") == llm_mod.SCENARIO_DEFAULT)
        check("未标 biz_type → default",
              resolve_scenario(None) == llm_mod.SCENARIO_DEFAULT)

    print("\n=== 2. 默认配置：同模型 + 低推理档 ===")
    with Probe() as p:
        c = LLMClient()
        c.get_client(resolve_scenario("question_generate"))
        c.get_client(resolve_scenario("lesson_plan"))
        fast, default = p.calls[0], p.calls[1]
        check("快场景带 reasoning_effort=low",
              fast.get("reasoning_effort") == "low",
              str(fast.get("reasoning_effort")))
        check("默认场景不带该参数（行为不变）",
              "reasoning_effort" not in default
              and "model_kwargs" not in default,
              str(default.get("reasoning_effort")))
        check("快场景未配模型时复用主模型",
              fast.get("model") == "primary-model", str(fast.get("model")))
        check("两个场景共用同一 base_url / max_tokens / timeout",
              all(fast.get(k) == default.get(k)
                  for k in ("base_url", "max_tokens", "timeout")),
              str({k: fast.get(k) for k in ("base_url", "max_tokens", "timeout")}))

    print("\n=== 3. 配置独立模型后只影响快场景 ===")
    with Probe({"llm_model_fast": "MiniMax-M2.5-highspeed",
                "llm_base_url_fast": "https://fast.example/v1"}) as p:
        c = LLMClient()
        c.get_client(resolve_scenario("question_generate"))
        c.get_client(resolve_scenario("lesson_plan"))
        fast, default = p.calls[0], p.calls[1]
        check("快场景用独立模型", fast.get("model") == "MiniMax-M2.5-highspeed",
              str(fast.get("model")))
        check("快场景用独立 base_url", fast.get("base_url") == "https://fast.example/v1",
              str(fast.get("base_url")))
        check("默认场景仍是主模型/主地址",
              default.get("model") == "primary-model"
              and default.get("base_url") == "https://unit.example/v1")

    print("\n=== 4. 缓存隔离与关闭路由 ===")
    with Probe() as p:
        c = LLMClient()
        c.get_client("fast")
        c.get_client("fast")
        c.get_client("default")
        check("同场景二次调用不重建客户端", len(p.calls) == 2, str(len(p.calls)))
        c.reset_clients()
        c.get_client("fast")
        check("reset_clients 后重新构造", len(p.calls) == 3, str(len(p.calls)))
        check("reset_clients 清掉了降级原因", c._fallback_reason == "")

    with Probe({"llm_fast_biz_types": ""}) as p:
        check("清空白名单 → 全部走 default",
              resolve_scenario("question_generate") == llm_mod.SCENARIO_DEFAULT)
    with Probe({"llm_fast_biz_types": "my_biz, question_generate"}) as p:
        check("自定义白名单生效（含空格容错）",
              resolve_scenario("my_biz") == llm_mod.SCENARIO_FAST
              and resolve_scenario("question_generate") == llm_mod.SCENARIO_FAST
              and resolve_scenario("lesson_plan") == llm_mod.SCENARIO_DEFAULT)
    with Probe({"llm_fast_reasoning_effort": ""}) as p:
        c = LLMClient()
        c.get_client("fast")
        check("推理档留空 → 不传该参数（兼容不认识的网关）",
              "reasoning_effort" not in p.calls[0]
              and "model_kwargs" not in p.calls[0],
              str(p.calls[0].get("reasoning_effort")))

    print("\n=== 5. 熔断仍短路（双场景缓存下不能绕过） ===")
    with Probe(breaker={"kind": llm_mod.llm_breaker.KIND_AUTH,
                        "reason": "unit-test auth breaker"}) as p:
        c = LLMClient()
        check("auth 熔断下 fast 返回 None", c.get_client("fast") is None)
        check("auth 熔断下 default 返回 None", c.get_client("default") is None)
        check("熔断期间不构造任何客户端", len(p.calls) == 0, str(len(p.calls)))

    print("\n=== 6. chat() 把场景传给 get_client ===")
    with Probe() as p:
        c = LLMClient()
        seen = {}
        # 让 get_client 返回 None 走降级分支：不触真实 invoke，
        # 也不写调用日志（log_agent_call 是异步落库），只验证场景解析。
        with patch.object(c, "get_client",
                          side_effect=lambda s: (seen.setdefault("s", s), None)[1]), \
                patch.object(llm_mod, "log_agent_call", return_value=None):
            r = c.chat("sys", "user", biz_type="question_generate")
        check("chat(question_generate) 解析为 fast",
              seen.get("s") == llm_mod.SCENARIO_FAST, str(seen))
        check("降级分支仍返回 is_fallback=True", r.get("is_fallback") is True)

    print("\n" + "=" * 60)
    if FAILED:
        print(f"失败 {len(FAILED)} 项：")
        for f in FAILED:
            print("  -", f)
        return 1
    print("全部通过：场景级模型路由按预期工作")
    return 0


if __name__ == "__main__":
    sys.exit(main())
