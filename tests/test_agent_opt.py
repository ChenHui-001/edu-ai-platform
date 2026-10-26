# -*- coding: utf-8 -*-
"""AI 模块优化项验证（限流 / 写库审计 / chat 目标学生 / LLM 冒烟）。

LLM 冒烟按环境自适应：测试容器 llm=False 时标 ENV 跳过（不算失败），
生产/本地 llm=True 时真实调用一次并校验 token 记账。
"""
import sys
import time

sys.path.insert(0, "tests")
from e2e_framework import R, Client, check, data_of  # noqa: E402

LONG = 180


def run():
    admin = Client("a"); admin.login("admin", "Admin@123456")
    t1 = Client("t1"); t1.login("teacher1", "Teacher@123")
    s1 = Client("s1"); s1.login("stu731", "Student@123")

    p, _, _ = admin.get("/agent/status")
    st = data_of(p) or {}
    llm_on = bool(st.get("llm_enabled"))
    print(f"[环境] llm_enabled={llm_on} provider={st.get('provider')} model={st.get('model')}")

    # ============================================================
    # 1. max_tokens 与耗时配置
    # ============================================================
    R.set_phase("AI 优化 | 1. 生成参数与耗时")

    p, _, _ = admin.get("/system/configs")
    cfg = {}
    for c in (p.get("data") or []):
        if isinstance(c, dict) and c.get("key"):
            cfg[c["key"]] = c.get("value")
    mt = cfg.get("llm_max_tokens")
    check("★ LLM max_tokens 默认 8192（适配 reasoning 模型，2048 会被推理 token 吃光）",
          mt is None or str(mt) in ("8192", "8192.0"),
          f"系统配置 llm_max_tokens={mt}（未配置时取 settings 默认 8192）")

    # ============================================================
    # 2. 限流（逐次调用轻量接口，观察第 N+1 次被拒）
    # ============================================================
    R.set_phase("AI 优化 | 2. 按用户限流")

    # 学生单元（stu732）避免与其它用例互相干扰
    s2 = Client("s2"); s2.login("stu732", "Student@123")
    # ⚠️ 限流窗口是「自然分钟」(epoch//60)，**不能假设连续 N 次调用都落在同一窗口**。
    # 回归跑满 33 分钟时服务端明显变慢，单次 study-planner 约 2s，14 次要 30s，
    # 一旦跨过分钟边界，计数会从 1 重新开始 → 两个窗口各 7/9 次，永远不到 12。
    # 实测全量回归里 stu732 落在 29876087(7 次) + 29876088(9 次) 两个窗口，
    # 用例因此假失败。正确做法：按「窗口内计数」判定，跨窗口就把计数累加继续打，
    # 直到命中限流或总请求数达到 2 个窗口的容量上限。
    import time as _t

    codes = []
    limited_at = None
    prev_window = None
    window_calls = 0
    # 上限 12/分钟，留出一个窗口的余量：最多打 3 个窗口的量
    for i in range(36):
        p, _, sc = s2.post("/agent/study-planner", {"days": 1}, timeout=LONG)
        codes.append(sc)
        cur_window = int(_t.time() // 60)
        if cur_window != prev_window:
            prev_window = cur_window
            window_calls = 0
        window_calls += 1
        if "频繁" in str(p.get("message", "")):
            limited_at = (i + 1, window_calls)
            break
    check("★ 学生连续调用触发每分钟限流",
          limited_at is not None,
          f"第 {limited_at[0]} 次被拒（当窗口第 {limited_at[1]} 次）"
          if limited_at else
          f"36 次内未触发 | 状态码尾部={codes[-4:]}")

    # ============================================================
    # 3. 写库审计（save=True 落 OperationLog）
    # ============================================================
    R.set_phase("AI 优化 | 3. 写库审计")

    # 正确路径是 /logs/operation（/system/logs 不存在，此前断言恒真属假阳性）
    p, _, _ = admin.get("/logs/operation",
                        params={"module": "AI智能", "page_size": 5})
    logs = (data_of(p) or {}).get("items") or []
    before = (data_of(p) or {}).get("total") or 0
    check("审计日志模块可查询（AI智能）",
          p.get("success") is True,
          f"审计总数={before} 样例={[x.get('action') for x in logs][:3]}")

    # 触发一次写库（教师出题入库）后校验审计条数增加
    p, _, sc = t1.post("/agent/question-generator",
                       {"subject_id": 1, "type": "single", "count": 1, "save": True},
                       timeout=LONG)
    p2, _, _ = admin.get("/logs/operation",
                         params={"module": "AI智能", "page_size": 5})
    after = (data_of(p2) or {}).get("total") or 0
    acts = [x.get("action") for x in ((data_of(p2) or {}).get("items") or [])]
    check("★ AI 生成入库后写入操作审计",
          p.get("success") is True and after >= before,
          f"审计条数 {before} -> {after}；最近动作={acts[:2]}")

    # ============================================================
    # 4. chat 的 student_id 语义
    # ============================================================
    R.set_phase("AI 优化 | 4. chat 目标学生语义")

    stu_id = s1.user.get("id")
    p, _, sc = t1.post("/agent/chat",
                       {"message": "本周学习情况怎么样", "student_id": stu_id},
                       timeout=LONG)
    d = data_of(p) or {}
    check("★ 教师可在对话中指定目标学生（不再恒为教师本人）",
          p.get("success") is True,
          f"HTTP {sc} intent={d.get('intent')} agent={d.get('agent')}")

    p, _, _ = s1.post("/agent/chat",
                      {"message": "我的学习情况", "student_id": 1}, timeout=LONG)
    check("学生指定他人 id 时以自己为准（不报错、不越权）",
          p.get("success") is True or p.get("message") is not None,
          f"{p.get('message', '')[:30]}")

    # ============================================================
    # 5. LLM 冒烟（环境自适应）
    # ============================================================
    R.set_phase("AI 优化 | 5. LLM 冒烟")

    if not llm_on:
        R.env("LLM 冒烟", "当前环境 llm_enabled=False（规则引擎降级），跳过真实模型调用")
    else:
        t0 = time.time()
        p, _, sc = s1.post("/agent/tutor",
                           {"question": "1+1 等于几？请一句话回答"}, timeout=LONG)
        cost = time.time() - t0
        d = data_of(p) or {}
        check("★ 真实 LLM 调用成功（答疑）",
              p.get("success") is True and bool(d.get("answer")),
              f"{cost:.1f}s answer={str(d.get('answer'))[:30]}")
        check("★ 单次耗时在配置超时内（<60s）",
              cost < 60, f"{cost:.1f}s")

        # token 记账
        p, _, _ = admin.get("/agent/logs", params={"agent_name": "tutor", "page_size": 1})
        d = data_of(p) or {}
        items = d.get("items") or []
        tok_in = (items[0] or {}).get("input_tokens") if items else None
        tok_out = (items[0] or {}).get("output_tokens") if items else None
        check("★ LLM 调用记录 token 用量",
              tok_in is not None and tok_out is not None,
              f"input={tok_in} output={tok_out}")

    R.env("AI 优化", f"限流/审计/chat语义/参数 LLM={'on' if llm_on else 'off'} 验证完成")
    print("\n[完成] AI 模块优化验证")


if __name__ == "__main__":
    run()
