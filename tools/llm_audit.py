"""AI 大模型配置生效范围核查工具。

用途：验证管理员在「系统设置 → AI 大模型配置」里保存的 provider /
model / api_key 等，是否真的作用到了全部 AI 场景，并列出未覆盖项。

原理：写入一个假 API Key —— 若各Agent 真的发起了调用，会在
容器日志/ sys_agent_call_log 里留下 401 失败记录；
若日志空白，说明场景压根没走 LLM（存在遗漏）。

用法：
    python tools/llm_audit.py[base_url]
    # 例：python tools/llm_audit.py http://localhost:8080

注意：脚本会临时写入 sys_config 的 llm_* 配置，结束时会清空 API Key。
"""
import json
import sys
import urllib.error
import urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8080"
B = BASE.rstrip("/") + "/api/v1"
op = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def call(path, data=None, token=None, timeout=120, method=None):
    is_get = method is None and data is None
    body = None if is_get else json.dumps(data if data is not None else {}).encode()
    req = urllib.request.Request(
        B + path, data=body, method=method or ("GET" if is_get else "POST"),
        headers={"Content-Type": "application/json",
                 **({"Authorization": "Bearer " + token} if token else {})})
    try:
        return json.load(op.open(req, timeout=timeout))
    except urllib.error.HTTPError as e:
        return {"_http": e.code, "_body": e.read().decode()[:300]}
    except Exception as e:
        return {"_err": f"{type(e).__name__}: {e}"}


def login(u, p):
    return (call("/auth/login", {"username": u, "password": p}).get("data") or {}).get("access_token")


def line(t):
    print("\n" + "=" * 70)
    print("  " + t)
    print("=" * 70)


admin = login("admin", "Admin@123456")
teacher = login("teacher1", "Teacher@123")
stu = login("stu731", "Student@123")
print(f"登录: admin={'OK' if admin else 'FAIL'} "
      f"teacher={'OK' if teacher else 'FAIL'} stu={'OK' if stu else 'FAIL'}")

line("1. 写入 LLM 配置（用假 key，只验证『是否会尝试调用』）")
save = call("/system/ai-config", {
    "llm_enabled": True, "llm_provider": "deepseek",
    "llm_api_key": "sk-FAKE-0000", "llm_base_url": "https://api.deepseek.com/v1",
    "llm_model": "deepseek-chat", "llm_temperature": 0.7,
    "llm_max_tokens": 1024, "llm_timeout": 15,
}, token=admin, method="PUT")
print("  PUT ->", save.get("message"))

line("2. Agent 引擎状态接口（前端『AI 引擎』面板读的就是它）")
st = call("/agent/status", token=admin)
print("  ", json.dumps(st.get("data") or st, ensure_ascii=False)[:700])

line("3. 七个 Agent 场景实测")
cases = [
    ("答疑助教 /agent/tutor", "/agent/tutor", {"question": "什么是一元一次方程？"}, stu),
    ("统一对话 /agent/chat", "/agent/chat", {"message": "出5道一元一次方程题"}, teacher),
    ("题库生成 /agent/question-generator", "/agent/question-generator",
     {"grade_id": 7, "subject_id": 1, "question_type": "single", "count": 1}, teacher),
    ("智能组卷 /agent/paper-composer", "/agent/paper-composer",
     {"grade_id": 7, "subject_id": 1, "total_score": 100}, teacher),
    ("智能批改 /agent/grading", "/agent/grading", {"submission_id": 1}, teacher),
    ("学习规划 /agent/study-planner", "/agent/study-planner", {"days": 7}, stu),
    ("笔记整理 /agent/note-organizer", "/agent/note-organizer",
     {"title": "测试", "content": "ax+b=0 的解法"}, stu),
]
for name, path, payload, tok in cases:
    r = call(path, payload, token=tok)
    d = r.get("data") or {}
    print(f"\n  [{name}]")
    print(f"      success={r.get('success')} data.success={d.get('success')} "
          f"is_fallback={d.get('is_fallback')}")
    note = r.get("_err") or r.get("_body") or d.get("reason") or ""
    if note:
        print(f"      说明: {str(note)[:130]}")
    for k in ("answer", "advice", "outline", "plan", "mindmap"):
        if d.get(k):
            print(f"      {k}: {str(d[k])[:90]}")
            break

line("4. 学习中心内嵌的 LLM 场景（不经 /agent/* 直连）")
nid = (call("/learning/notes", {"title": "核查", "content": "ax+b=0"},
            token=stu).get("data") or {}).get("id")
scenarios = [
    ("笔记整理", f"/learning/notes/{nid}/organize", {}, stu),
    ("复习计划", "/learning/review/plan", {"days": 7, "daily_minutes": 60}, stu),
    ("学习路径", "/learning/path/recommend", {}, stu),
    ("学情建议", "/grading/tasks/1/ai-comment", {}, teacher),
    ("错题变式", "/learning/wrong-questions/1/variant", {}, stu),
]
for name, path, payload, tok in scenarios:
    if not path:
        print(f"\n  [{name}] 跳过（前置资源未创建）")
        continue
    r = call(path, payload, token=tok)
    d = r.get("data") or {}
    print(f"\n  [{name}]")
    print(f"      success={r.get('success')} is_fallback={d.get('is_fallback')}")
    note = r.get("_err") or r.get("_body") or ""
    if note:
        print(f"      说明: {str(note)[:130]}")
    for k in ("outline", "mindmap", "daily_plan", "stages", "advice", "variants"):
        if d.get(k):
            print(f"      {k}: {str(d[k])[:80]}")
            break

line("5. AI 调用日志（确认是否真发起调用并记录了失败原因）")
lg = call("/agent/logs", {"page_size": 30}, token=admin)
rows = (lg.get("data") or {}).get("items") or []
print(f"  日志条数: {len(rows)}")
for r in rows[:12]:
    print(f"    agent={str(r.get('agent_name')):<16} status={str(r.get('status')):<8} "
          f"fallback={r.get('is_fallback')} err={str(r.get('error_msg'))[:45]}")

line("6. 恢复（清空 key）")
rst = call("/system/ai-config", {"llm_enabled": True, "llm_api_key": ""},
           token=admin, method="PUT")
print("  ", rst.get("message"))
print("\n完成。")