# -*- coding: utf-8 -*-
"""AI 结构性优化验证（阶段十四）：限流 DB 化 / 异步任务 / SSE 流式。"""
import json
import sys
import time

sys.path.insert(0, "tests")
from e2e_framework import R, Client, check, data_of  # noqa: E402

LONG = 180


def run():
    admin = Client("a"); admin.login("admin", "Admin@123456")
    t1 = Client("t1"); t1.login("teacher1", "Teacher@123")
    s1 = Client("s1"); s1.login("stu731", "Student@123")

    # ============================================================
    # 1. 限流 DB 共享（跨 client 会话一致）
    # ============================================================
    R.set_phase("AI 优化2 | 1. 限流 DB 化")

    # 用独立学生账号，避免与其它用例共用配额
    s3 = Client("s3"); s3.login("stu733", "Student@123")
    ok3 = bool(s3.token)
    if not ok3:
        s3 = s1

    hit = None
    # ⚠️ 限流窗口是「自然分钟」(epoch//60)：不能假设连续 N 次调用必落在同一窗口。
    # 回归整跑时服务端变慢，单次 study-planner 约 2s，14 次要 30s，跨分钟边界后
    # 计数从 1 重新开始 → 两个窗口各 10/4 次，永远到不了 12，用例假失败。
    # 因此给足 3 个窗口的余量（36 次），仍以「命中限流文案」为唯一判据。
    for i in range(36):
        p, _, sc = s3.post("/agent/study-planner", {"days": 1}, timeout=LONG)
        msg = str(p.get("message") or "")
        if "频繁" in msg:
            hit = (i + 1, msg)
            s3._hit_window = int(time.time() // 60)
            break

    check("★ 连续调用触发 DB 限流（每分钟 12 次）",
          hit is not None,
          f"第 {hit[0]} 次被拒：{hit[1][:40]}" if hit else "36 次内未触发")

    # 换一个 client 实例（新连接）验证计数是共享的而非连接级。
    # 若上一轮恰好跨到新的分钟窗口，新窗口计数会从 1 开始，此时「同一连接」也
    # 不会被拒 —— 那样测的就不是「跨连接共享」。所以先确认仍在限流窗口内，
    # 已经跨窗口就跳过（ENV），而不是让它变成假失败。
    if hit:
        import time as _t

        hit_window = getattr(s3, "_hit_window", None)
        if hit_window is not None and int(_t.time() // 60) != hit_window:
            R.env("限流计数跨连接共享", "触发限流后已进入新的分钟窗口，跳过")
        else:
            s3b = Client("s3b"); s3b.login("stu733", "Student@123")
            p, _, _ = s3b.post("/agent/study-planner", {"days": 1}, timeout=LONG)
            check("★ 限流计数跨连接共享（DB 存储生效）",
                  "频繁" in str(p.get("message") or ""),
                  f"新连接请求返回：{str(p.get('message'))[:40]}")

    # ============================================================
    # 2. 异步任务 + 轮询
    # ============================================================
    R.set_phase("AI 优化2 | 2. 异步任务与轮询")

    p, _, sc = t1.post("/agent/jobs", {
        "agent": "question",
        "params": {"subject_id": 1, "type": "single", "count": 2, "save": False},
    })
    jid = (data_of(p) or {}).get("job_id")
    check("★ 提交长任务立即返回 job_id",
          p.get("success") is True and bool(jid),
          f"HTTP {sc} job_id={jid} status={(data_of(p) or {}).get('status')}")

    if jid:
        # 轮询至终态
        final = None
        for _ in range(60):     # 最长 120s
            time.sleep(2)
            p2, _, _ = t1.get(f"/agent/jobs/{jid}")
            d = data_of(p2) or {}
            if d.get("status") in ("success", "failed"):
                final = d
                break
        check("★ 任务轮询到终态", final is not None,
              f"status={(final or {}).get('status')} "
              f"error={str((final or {}).get('error'))[:40]}")
        if final:
            check("任务结果已落库（可刷新后查回）",
                  final.get("result") is not None or final.get("error"),
                  f"result_keys={list((final.get('result') or {}).keys())[:5]}")
            check("任务含耗时字段（started/finished）",
                  final.get("created_at") and final.get("finished_at") is not None,
                  f"created={final.get('created_at')} finished={final.get('finished_at')}")

        # 权限：他人任务不可看
        p3, _, sc3 = s1.get(f"/agent/jobs/{jid}")
        check("★ 学生不可查看教师的任务", p3.get("success") is not True,
              f"HTTP {sc3}")

        # 越权提交：学生不能提交长任务
        p4, _, sc4 = s1.post("/agent/jobs", {"agent": "paper", "params": {}})
        check("★ 学生不可提交长任务", p4.get("success") is not True and sc4 == 403,
              f"HTTP {sc4}")

        # 非法 agent
        p5, _, _ = t1.post("/agent/jobs", {"agent": "unknown", "params": {}})
        check("非法任务类型被拒", p5.get("success") is not True,
              str(p5.get("message"))[:40])

        # 不存在的任务
        p6, _, sc6 = t1.get("/agent/jobs/999999")
        check("不存在的任务 404", p6.get("success") is not True and sc6 == 404,
              f"HTTP {sc6}")

        # 任务列表
        p7, _, _ = t1.get("/agent/jobs", params={"page_size": 5})
        d7 = data_of(p7) or {}
        check("我的任务列表可读", isinstance(d7.get("items"), list) and "total" in d7,
              f"{d7.get('total')} 条")

    # ============================================================
    # 3. SSE 流式
    # ============================================================
    R.set_phase("AI 优化2 | 3. SSE 流式对话")

    st = data_of(admin.get("/agent/status")[0]) or {}
    llm_on = bool(st.get("llm_enabled"))

    # 用 requests 直接读流（e2e_framework 的 Client 会等待完整响应）
    import urllib.error
    import urllib.request

    # ⚠️ 地址必须优先取 `BASE`（已按 E2E_BASE / HOST_PORT 探测好，含 /api/v1），
    # 不能写死端口列表。以前这里只探 8099/8080/8000：一旦回归跑在其他端口
    # （手动隔离库时的 8001/8002、CI 自定义端口），就会连到**另一个库的实例**，
    # 于是本次登录拿到的 Token 在那边无效 → 401，用例报「SSE 接口不可访问」，
    # 而实际接口完全正常。这类「连错服务」的假失败特别难查，因为症状像鉴权 bug。
    from e2e_framework import BASE as _BASE

    api_base = _BASE
    try:
        with urllib.request.urlopen(api_base + "/health", timeout=3) as r:
            if r.status != 200:
                api_base = None
    except Exception:  # noqa: BLE001
        api_base = None

    if api_base:
        req = urllib.request.Request(
            api_base + "/agent/chat/stream",
            data=json.dumps({"message": "什么是勾股定理"}).encode(),
            headers={"Content-Type": "application/json",
                     "Authorization": f"Bearer {s1.token}"},
            method="POST")
        try:
            with urllib.request.urlopen(req, timeout=LONG) as resp:
                ctype = resp.headers.get("content-type", "")
                raw = resp.read().decode("utf-8", errors="replace")
            events = []
            for line in raw.split("\n"):
                if line.startswith("data:"):
                    try:
                        events.append(json.loads(line[5:].strip()))
                    except Exception:  # noqa: BLE001
                        pass
            types = [e.get("type") for e in events]
            check("★ SSE 返回 text/event-stream", "event-stream" in ctype, ctype)
            check("★ SSE 事件序列含 meta/delta/done",
                  "meta" in types and "delta" in types and "done" in types,
                  f"{len(events)} 个事件 types={types[:6]}")
            text = "".join(e.get("text", "") for e in events if e.get("type") == "delta")
            check("★ 流式内容非空且可拼接",
                  len(text) > 0,
                  f"{len(text)} 字：{text[:40]}")
            done_ev = next((e for e in events if e.get("type") == "done"), {})
            check("done 事件含耗时与降级标记",
                  "duration_ms" in done_ev and "is_fallback" in done_ev,
                  f"duration={done_ev.get('duration_ms')} fallback={done_ev.get('is_fallback')}")
        except urllib.error.HTTPError as exc:
            check("★ SSE 接口可访问", False, f"HTTP {exc.code}")
        except Exception as exc:  # noqa: BLE001
            check("★ SSE 接口可访问", False, str(exc)[:80])
    else:
        R.env("SSE", "未找到可用服务地址，跳过流式验证")

    R.env("AI 优化2", f"限流DB/异步任务/SSE 验证完成（LLM={'on' if llm_on else 'off'}）")
    print("\n[完成] AI 结构性优化验证")


if __name__ == "__main__":
    run()
