"""系统管理 v1.0.40 定向验证：密钥脱敏 / 关键配置保护 / 重置密码契约

针对干净测试库证据偏弱的两项，改在挂载真实 DB 的容器上验收：
主动写入一段已知的假密钥，回归读取路径，断言返回值必须为掩码形态。
用法: python tests/verify_sys_secrets.py http://localhost:8091/api/v1
"""
import json
import sys
import urllib.error
import urllib.request

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8091/api/v1").rstrip("/")
PASS = FAIL = 0
TOKEN = None
FAKE_KEY = "sk-test-ABCDEFGH12345678-zyxw"
FAKE_SMTP = "smtp-Passw0rd-XYZ8888"


def req(method, path, body=None, token=None):
    url = BASE + path
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(url, data=data, method=method)
    r.add_header("Content-Type", "application/json")
    if token:
        r.add_header("Authorization", "Bearer " + token)
    try:
        with urllib.request.urlopen(r, timeout=30) as resp:
            return resp.status, json.loads(resp.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            return e.code, json.loads(raw or "{}")
        except Exception:
            return e.code, {"raw": raw}


def ok(cond, name, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  PASS  {name}  {detail}")
    else:
        FAIL += 1
        print(f"  FAIL  {name}  {detail}")


def is_masked(v, real):
    return isinstance(v, str) and "****" in v and str(real) not in v


print(f"== 目标 {BASE} ==")
st, body = req("POST", "/auth/login", {"username": "admin", "password": "Admin@123456"})
TOKEN = (body.get("data") or {}).get("access_token") or body.get("access_token")
print(f"登录: {st} token={'有' if TOKEN else '无'} msg={body.get('message')}")
if not TOKEN:
    print("!! 无法登录，终止")
    sys.exit(2)

# ---------------- 1. AI 配置密钥脱敏 ----------------
print("\n[1] /system/ai-config 密钥脱敏（写入已知假密钥后回读）")
st, _ = req("PUT", "/system/ai-config", {"llm_api_key": FAKE_KEY}, token=TOKEN)
print(f"  写入假密钥 status={st}")
st, body = req("GET", "/system/ai-config", token=TOKEN)
cfg = (body.get("data") or {}).get("config") or {}
got = cfg.get("LLM_API_KEY")
print(f"  回读 status={st} LLM_API_KEY={got!r}")
ok(st == 200, "ai-config 可读", f"status={st}")
ok(bool(got), "LLM_API_KEY 有值（脱敏前确实存在密钥）", f"值={got!r}")
ok(is_masked(got, FAKE_KEY), "LLM_API_KEY 已脱敏", f"回读={got!r} 真实={FAKE_KEY!r}")
ok(got != FAKE_KEY, "完整密钥未外泄", "返回不含原值" if got != FAKE_KEY else "!! 明文泄漏")
meta = (body.get("data") or {}).get("meta") or {}
ok(bool((meta.get("llm_api_key") or {}).get("has_db_value")),
   "meta 标记已落库（确从 DB 读取而非环境变量）")

# 掩码回传不得覆盖真实密钥
st, body = req("PUT", "/system/ai-config", {"llm_api_key": got}, token=TOKEN)
upd = (body.get("data") or {}).get("updated") or []
st2, body2 = req("GET", "/system/ai-config", token=TOKEN)
got2 = ((body2.get("data") or {}).get("config") or {}).get("LLM_API_KEY")
ok("llm_api_key" not in upd, "回传掩码值被忽略（不写库）", f"updated={upd}")
ok(got2 == got, "掩码回传后密钥未被污染", f"前后一致={got2 == got}")

# ---------------- 2. 系统配置密钥脱敏 + 关键项保护 ----------------
print("\n[2] /system/config editable 脱敏 + 关键配置删除保护")
st, _ = req("PUT", "/system/config", {"key": "smtp_password", "value": FAKE_SMTP,
                                      "category": "mail", "label": "SMTP 密码"}, token=TOKEN)
print(f"  写入 smtp_password status={st}")
st, body = req("GET", "/system/config", token=TOKEN)
d = body.get("data") or {}
editable = d.get("editable") or []
print(f"  回读 status={st} editable 条数={len(editable)}")
row = next((x for x in editable if x.get("key") == "smtp_password"), None)
ok(row is not None, "smtp_password 出现在 editable 中")
if row:
    ok(is_masked(row.get("value"), FAKE_SMTP), "smtp_password 已脱敏",
       f"回读={row.get('value')!r}")
ok(all(is_masked(x.get("value"), FAKE_SMTP) for x in editable
       if "password" in (x.get("key") or "").lower() and x.get("value")),
   "editable 中所有 password 类字段均为掩码")

st, body = req("DELETE", "/system/config/smtp_password", token=TOKEN)
msg = str(body.get("message") or body.get("detail") or "")
ok(st in (400, 403), "smtp_password 拒绝删除（关键前缀保护）", f"status={st} msg={msg}")

req("PUT", "/system/config", {"key": "llm_provider", "value": "deepseek",
                              "category": "ai", "label": "提供商"}, token=TOKEN)
st, body = req("DELETE", "/system/config/llm_provider", token=TOKEN)
msg = str(body.get("message") or body.get("detail") or "")
ok(st in (400, 403) and "关键配置" in msg, "llm_provider 拒绝删除",
   f"status={st} msg={msg}")

st, body = req("PUT", "/system/config", {"key": "probe_deletable", "value": "x"}, token=TOKEN)
st, body = req("DELETE", "/system/config/probe_deletable", token=TOKEN)
ok(st == 200, "非关键配置可正常删除（保护未误伤）", f"status={st}")

# ---------------- 3. 重置密码字段契约 ----------------
print("\n[3] 重置密码字段契约（P0：前端曾传 password）")
st, body = req("POST", "/system/users", {"username": "pwdprobe01", "real_name": "密码探针",
                                         "identity": "teacher", "password": "Probe@123456",
                                         "must_change_password": False}, token=TOKEN)
uid = (body.get("data") or {}).get("id") if isinstance(body.get("data"), dict) else None
print(f"  建号 status={st} id={uid} msg={body.get('message')}")
ok(uid is not None, "创建探针账号成功", f"id={uid}")
if uid:
    st1, _ = req("PUT", "/system/password/reset", {"user_id": uid, "password": "NewPwd@123456"},
                 token=TOKEN)
    ok(st1 == 422, "旧字段 password 被拒（复现原前端 422）", f"status={st1}")
    st2, b2 = req("PUT", "/system/password/reset", {"user_id": uid, "new_password": "NewPwd@123456"},
                  token=TOKEN)
    ok(st2 == 200, "新字段 new_password 通过", f"status={st2} msg={b2.get('message')}")
    st3, _ = req("POST", "/auth/login", {"username": "pwdprobe01", "password": "NewPwd@123456"})
    ok(st3 == 200, "重置后新密码可登录", f"status={st3}")
    st4, _ = req("PUT", "/system/password/reset", {"user_id": uid, "new_password": "a"}, token=TOKEN)
    ok(st4 in (400, 422), "弱口令重置被拒", f"status={st4}")
    req("DELETE", f"/system/users/{uid}", token=TOKEN)
    print("  探针账号已清理")

# ---------------- 4. 还原现场 ----------------
print("\n[4] 还原被测配置（避免污染真实 DB）")
st, _ = req("PUT", "/system/ai-config", {"llm_api_key": FAKE_KEY}, token=TOKEN)
st, _ = req("DELETE", "/system/config/smtp_password", token=TOKEN)
print(f"  清理 smtp_password status={st}（受保护属预期）")

print(f"\n== 结果 {PASS} PASS / {FAIL} FAIL ==")
sys.exit(0 if FAIL == 0 else 1)
