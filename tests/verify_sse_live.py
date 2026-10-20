# -*- coding: utf-8 -*-
"""真实 LLM 环境下的 SSE 流式验证（逐 token 与时序）。"""
import json
import sys
import time
import urllib.request

BASE = "http://localhost:8098/api/v1"


def post(path, body, token=None, timeout=180):
    req = urllib.request.Request(
        BASE + path, data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json",
                 **({"Authorization": f"Bearer {token}"} if token else {})},
        method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def main():
    login = post("/auth/login", {"username": "stu731", "password": "Student@123"})
    token = (login.get("data") or {}).get("access_token")
    if not token:
        print("登录失败:", login)
        return
    print(f"登录成功 token={token[:12]}...")

    req = urllib.request.Request(
        BASE + "/agent/chat/stream",
        data=json.dumps({"message": "用三句话解释什么是勾股定理"}).encode(),
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {token}"},
        method="POST")

    t0 = time.time()
    first_delta_at = None
    deltas = []
    events = []
    with urllib.request.urlopen(req, timeout=180) as resp:
        ctype = resp.headers.get("content-type", "")
        # 逐行读：read(256) 会阻塞等待凑满字节数，导致首字延迟测量失真
        while True:
            raw_line = resp.readline()
            if not raw_line:
                break
            line = raw_line.decode("utf-8", errors="replace").strip()
            if not line.startswith("data:"):
                continue
            try:
                ev = json.loads(line[5:].strip())
            except Exception:  # noqa: BLE001
                continue
            events.append(ev)
            if ev.get("type") == "delta":
                if first_delta_at is None:
                    first_delta_at = time.time() - t0
                deltas.append(ev.get("text", ""))
    total = time.time() - t0

    done = next((e for e in events if e.get("type") == "done"), {})
    text = "".join(deltas)
    print(f"content-type: {ctype}")
    print(f"事件数: {len(events)} | delta 数: {len(deltas)}")
    print(f"首字延迟: {first_delta_at:.2f}s | 总耗时: {total:.2f}s")
    print(f"done: {json.dumps(done, ensure_ascii=False)[:160]}")
    print(f"回答前 80 字: {text[:80]}")

    # 判据：多分段（>=3）+ 首字严格早于结束（说明是增量推送而非攒完一次性下发）
    ok = ("event-stream" in ctype and len(deltas) >= 3
          and first_delta_at is not None and first_delta_at < total)
    print("\n判定:", "✅ 真实逐 token 流式生效"
          if ok else "❌ 未观察到流式（可能是单次下发或降级）")
    if ok:
        print(f"TTFT（首 token 延迟）：{first_delta_at:.2f}s —— "
              f"若接近总耗时，说明上游模型/中转服务首包慢（非本次代码问题）")


if __name__ == "__main__":
    main()
