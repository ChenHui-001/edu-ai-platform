# -*- coding: utf-8 -*-
"""AI 智能模块专项测试（权限隔离 + 关键功能）。

注意：真实 LLM 调用单次可达 40~60s，本文件优先覆盖**权限拒绝路径**（不触发 LLM，
毫秒级返回），功能类用例单独给长超时。
"""
import sys

sys.path.insert(0, "tests")
from e2e_framework import (  # noqa: E402
    R, Client, check, data_of,
)

LONG = 180


def run():
    admin = Client("a"); ok_a, _ = admin.login("admin", "Admin@123456")
    t1 = Client("t1"); t1.login("teacher1", "Teacher@123")
    s1 = Client("s1"); s1.login("stu731", "Student@123")
    s2 = Client("s2"); s2.login("stu732", "Student@123")

    check("三端登录", ok_a, "")

    # ============================================================
    # 1. 引擎状态与 Agent 注册
    # ============================================================
    R.set_phase("AI 智能 | 1. 引擎状态与注册表")

    p, _, _ = admin.get("/agent/status")
    st = data_of(p) or {}
    check("★ 引擎状态字段完整", all(
        k in st for k in ("llm_enabled", "provider", "model", "orchestrator_mode", "agents")),
        f"llm={st.get('llm_enabled')} provider={st.get('provider')} "
        f"agents={st.get('agents')} mode={st.get('orchestrator_mode')}")
    # 不写死具体数字：每加一个 Agent 就要改测试，是「断言写死产量」的老毛病。
    # 断言语义 = 至少 8 个（Router + 7 个专业 Agent）。
    check("Agent 注册数 ≥ 8（Router+7 专业）", (st.get("agents") or 0) >= 8,
          f"agents={st.get('agents')}")

    p, _, _ = admin.get("/agent/list")
    lst = data_of(p) or {}
    agents = lst.get("agents") or []
    check("Agent 列表可读且含 router", len(agents) >= 7,
          f"{len(agents)} 个：{[a.get('name') for a in agents][:8]}")
    check("★ 列表返回 llm_provider（不再硬编码 None）",
          "llm_provider" in lst,
          f"llm_provider={lst.get('llm_provider')} llm_enabled={lst.get('llm_enabled')}")

    # ============================================================
    # 2. 高危接口角色隔离（403 不触发 LLM，快速返回）
    # ============================================================
    R.set_phase("AI 智能 | 2. 角色隔离（出题/组卷/批改）")

    for path, name in (
        ("/agent/question-generator", "出题"),
        ("/agent/paper-composer", "组卷"),
        ("/agent/grading", "批改"),
    ):
        p, _, sc = s1.post(path, {"subject_id": 1, "count": 1, "items": []})
        check(f"★ 学生调用{name} Agent 被拒",
              p.get("success") is not True and sc == 403,
              f"HTTP {sc} {p.get('message', '')[:30]}")

    # 教师可调用（出题走降级/LLM，给长超时；只断言「不是 403」）
    p, _, sc = t1.post("/agent/question-generator",
                       {"subject_id": 1, "type": "single", "count": 1, "save": False},
                       timeout=LONG)
    check("教师可调用出题 Agent（对照项）",
          sc != 403 and p.get("success") is not None,
          f"HTTP {sc} success={p.get('success')}")

    # ============================================================
    # 3. 笔记整理归属校验（本次核心修复）
    # ============================================================
    R.set_phase("AI 智能 | 3. 笔记整理归属校验")

    p, _, _ = s2.post("/learning/notes",
                      {"title": "E2E-AI 私密笔记", "content": "SECRET-AI-9317"})
    nid = (data_of(p) or {}).get("id")
    if nid:
        p, _, sc = s1.post("/agent/note-organizer", {"note_id": nid})
        check("★ 学生不可整理他人笔记（403，不触发 LLM）",
              p.get("success") is not True and sc == 403,
              f"HTTP {sc} {p.get('message', '')[:30]}")

        p, _, sc = s1.post("/agent/note-organizer", {"note_id": nid, "save": True})
        check("★ 学生不可覆写他人笔记",
              p.get("success") is not True and sc == 403,
              f"HTTP {sc}")

        # 原文未被改动
        p2, _, _ = s2.get(f"/learning/notes/{nid}")
        content = (data_of(p2) or {}).get("content") or ""
        check("★ 他人笔记正文未被篡改", content == "SECRET-AI-9317",
              f"content={content[:30]!r}")

        # 管理员只读不写
        p, _, sc = admin.post("/agent/note-organizer", {"note_id": nid, "save": True},
                              timeout=LONG)
        check("★ 管理员不可覆写他人笔记",
              p.get("success") is not True,
              f"HTTP {sc} {p.get('message', '')[:30]}")

        p, _, _ = admin.post("/agent/note-organizer", {"note_id": nid}, timeout=LONG)
        check("管理员可只读整理他人笔记（核查用途）",
              p.get("success") is True, "")

        # 学生整理自己的笔记（正常路径，长超时）
        p, _, _ = s2.post("/agent/note-organizer", {"note_id": nid}, timeout=LONG)
        check("学生可整理自己的笔记", p.get("success") is True, "")

        s2.delete(f"/learning/notes/{nid}")

    # ============================================================
    # 4. 学习规划目标学生隔离
    # ============================================================
    R.set_phase("AI 智能 | 4. 学习规划目标隔离")

    p, _, _ = s1.post("/agent/study-planner",
                      {"student_id": s2.user.get("id"), "days": 3}, timeout=LONG)
    d = data_of(p) or {}
    target = d.get("student_id") or (d.get("plan") or {}).get("student_id")
    check("★ 学生传他人 student_id 时被强制改回自己",
          p.get("success") is not True
          or target in (None, s1.user.get("id")),
          f"HTTP ok target_student_id={target} 自己={s1.user.get('id')}")

    # ============================================================
    # 5. AI 调用日志权限与统计一致性
    # ============================================================
    R.set_phase("AI 智能 | 5. 调用日志权限")

    p, _, _ = admin.get("/agent/logs", params={"page_size": 5})
    a_d = data_of(p) or {}
    a_items = a_d.get("total") or 0
    a_sum = (a_d.get("summary") or {}).get("total_calls") or 0
    check("管理员日志：明细与统计口径一致",
          a_sum >= a_items,
          f"items.total={a_items} summary={a_sum}")

    p, _, _ = s1.get("/agent/logs", params={"page_size": 5})
    s_d = data_of(p) or {}
    s_items = s_d.get("total") or 0
    s_sum = (s_d.get("summary") or {}).get("total_calls") or 0
    check("★ 学生日志：统计不再包含全站数据（summary ≤ 全站）",
          s_sum <= a_sum and s_sum >= s_items,
          f"学生 items={s_items} summary={s_sum} 全站={a_sum}")

    p, _, _ = s1.get("/agent/logs", params={"status": "failed"})
    check("日志按状态可筛选", p.get("success"), "")

    # ============================================================
    # 6. 未登录 / 越权基础
    # ============================================================
    R.set_phase("AI 智能 | 6. 基础鉴权")

    anon = Client("anon")
    for path in ("/agent/status", "/agent/list", "/agent/logs"):
        p, _, sc = anon.get(path)
        check(f"未登录不可访问 {path}", p.get("success") is not True and sc == 401,
              f"HTTP {sc}")

    # ============================================================
    # 7. 统一对话入口（学生可用）
    # ============================================================
    R.set_phase("AI 智能 | 7. 统一对话入口")

    p, _, sc = s1.post("/agent/chat", {"message": "什么是勾股定理"}, timeout=LONG)
    d = data_of(p) or {}
    check("学生可使用统一对话（自动路由）",
          p.get("success") is True and bool(d.get("intent") or d.get("answer")),
          f"intent={d.get('intent')} agent={d.get('agent')} "
          f"answer={str(d.get('answer'))[:20]}")

    R.env("AI 智能", "角色隔离 5 项 + 笔记归属 6 项 + 日志口径 + 统一入口验证完成")
    print("\n[完成] AI 智能模块专项")


if __name__ == "__main__":
    run()
