"""学生端「模拟考试」按钮诊断：查看解析 / 重考。

只读诊断，不改数据。目的是把「点不动」拆成可验证的假设：
  H1 submit_time 被序列化成对象/空串 → 前端 `!!submit_time` 判定两边都错
  H2 attempt >= max_attempt → 重考必然被 ExamPaper 立刻弹回列表
  H3 submissionDetail 报错（权限/字段） → 查看解析静默失败
  H4 字段名不匹配（my_submission.id vs submission_id）

用法：python tools/diagnose_student_exam.py <base_url>
"""
import json
import sys

import httpx

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8099").rstrip("/")
API = f"{BASE}/api/v1"

CREDS = [
    ("s711", "Student@2026!Xy"),
    ("s711", "Student@123456"),
    ("stu7101", "Student@123456"),
    ("admin", "Admin@123456"),
]


def login(username, password):
    r = httpx.post(f"{API}/auth/login",
                   json={"username": username, "password": password}, timeout=20)
    if r.status_code != 200:
        return None
    d = r.json().get("data") or {}
    return d.get("access_token") or d.get("token")


def main():
    tok = None
    for u, p in CREDS:
        tok = login(u, p)
        if tok:
            print(f"登录成功：{u}")
            break
    if not tok:
        print("无法登录，退出")
        return 2

    H = {"Authorization": f"Bearer {tok}"}

    print("\n=== 1. my/tasks 返回结构 ===")
    r = httpx.get(f"{API}/task/my/tasks", headers=H,
                  params={"page": 1, "page_size": 50}, timeout=20)
    if r.status_code != 200:
        print(f"  my/tasks 失败 {r.status_code} {r.text[:200]}")
        return 1
    items = (r.json().get("data") or {}).get("items") or []
    print(f"  任务数：{len(items)}")
    if not items:
        print("  当前账号没有任务下发，无法诊断（需要一位有考试任务的学生账号）")
        return 1

    for t in items[:5]:
        sub = t.get("my_submission")
        print(f"\n  task={t['id']} 「{t.get('title')}」")
        print(f"    allow_retake = {t.get('allow_retake')!r}")
        print(f"    attempt_count = {t.get('attempt_count')!r}")
        print(f"    my_submission = {json.dumps(sub, ensure_ascii=False, default=str)[:260]}")
        if sub:
            print(f"    submit_time = {sub.get('submit_time')!r}  (type={type(sub.get('submit_time')).__name__})")
            print(f"    attempt     = {sub.get('attempt')!r}")
            print(f"    has id      = {'id' in sub}")
            print(f"    H1 submit_time 真值判定 -> {bool(sub.get('submit_time'))}")
            if sub.get('submit_time') and not isinstance(sub.get('submit_time'), str):
                print("    !! H1 命中：submit_time 不是字符串，前端直接渲染会变成 [object Object]")
        else:
            print("    !! 无提交记录")

    print("\n=== 2. task_paper 的 max_attempt 与次数耗尽判定（H2）===")
    for t in items[:5]:
        tid = t["id"]
        r = httpx.get(f"{API}/task/tasks/{tid}/paper", headers=H, timeout=20)
        if r.status_code != 200:
            print(f"  task={tid} paper 失败 {r.status_code} {r.text[:160]}")
            continue
        d = r.json().get("data") or {}
        task = d.get("task") or {}
        sub = task.get("my_submission")
        mx = task.get("max_attempt")
        print(f"  task={tid} allow_retake={task.get('allow_retake')!r} "
              f"max_attempt={mx!r} sub_attempt={None if not sub else sub.get('attempt')!r} "
              f"sub_submit_time={None if not sub else sub.get('submit_time')!r}")
        if sub and sub.get("submit_time") and mx:
            used_up = int(sub.get("attempt") or 1) >= int(mx)
            print(f"    -> 前端判定「次数已用完」= {used_up}"
                  + ("   !! H2 命中：点重考会被立刻 replace 回列表" if used_up else ""))

    print("\n=== 3. submissionDetail（查看解析依赖）===")
    for t in items[:5]:
        sub = t.get("my_submission")
        if not sub or "id" not in sub:
            continue
        sid = sub["id"]
        r = httpx.get(f"{API}/task/submissions/{sid}", headers=H, timeout=30)
        print(f"  sid={sid} -> {r.status_code}")
        if r.status_code != 200:
            print(f"    !! H3 命中：{r.text[:260]}")
            continue
        d = r.json().get("data") or {}
        ans = d.get("answers") or []
        print(f"    字段：{sorted(d.keys())}")
        print(f"    answers={len(ans)}；有 answer 字段的={sum(1 for a in ans if a.get('answer') is not None)}")
        print(f"    H4 顶层有 submission_id? {'submission_id' in d}"
              f"（前端读 my_submission.id，此处返回 id={d.get('id')}）")
        if ans:
            print(f"    首条 keys: {sorted(ans[0].keys())}")
        if not ans:
            print("    !! answers 为空：查看解析会显示「答对 0/0 题」")

    print("\n=== 4. 前端判定复现 ===")
    for t in items:
        sub = t.get("my_submission")
        done_flag = bool(sub and sub.get("submit_time"))
        print(f"  task={t['id']} 前端「已完成」判定 = {done_flag}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
