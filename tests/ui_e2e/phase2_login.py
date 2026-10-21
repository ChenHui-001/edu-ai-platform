"""UI E2E 阶段二：登录（真实验证码）+ 管理员审批

验证码为一次性资源，从 captcha_pool.json 预取（已人工识别），
在页面内 route 拦截 /auth/captcha 回放同一张，保证「页面上看到的」与「提交的」一致。
"""
from __future__ import annotations

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness import API, E2E, api, api_login  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
POOL = json.load(open(os.path.join(HERE, "captcha_pool.json"), encoding="utf-8"))
P1 = json.load(open(os.path.join(HERE, "phase1.json"), encoding="utf-8"))
NEW_USER = P1["result"]["new_user"]
NEW_PWD = P1["result"]["new_pwd"]

e = E2E()
result = {"new_user": NEW_USER, "new_pwd": NEW_PWD}


def use_captcha(idx: int):
    """让页面的 /auth/captcha 固定返回池中第 idx 张（已识别）。"""
    item = POOL[idx]
    payload = {
        "code": 200, "message": "操作成功", "success": True,
        "data": {"key": item["key"], "image": "data:image/png;base64," +
                 _b64(item["file"])},
    }
    e.page.route("**/api/v1/auth/captcha*",
                 lambda route: route.fulfill(status=200, content_type="application/json",
                                             body=json.dumps(payload)))
    return item


def _b64(fn: str) -> str:
    import base64
    with open(os.path.join(HERE, fn), "rb") as f:
        return base64.b64encode(f.read()).decode()


def login_ui(username: str, password: str, idx: int, captcha_override=None):
    """真实 UI 登录。返回 (toast, url)。

    注意：验证码一次性，**每条用例必须用不同的 idx**，否则会拿到
    「验证码错误或已过期」，把「密码错误」误判成通过（首轮即踩过）。
    """
    item = use_captcha(idx)
    e.goto("/login", 1600)
    e.fill_placeholder("请输入账号", username)
    e.fill_placeholder("请输入密码", password)
    e.fill_placeholder("验证码", captcha_override or item["code"])
    e.click_text("登 录")
    e.page.wait_for_timeout(2600)
    return e.toast_text(), e.page.url


# ---------------------------------------------------------------- 用例
def t_captcha_wrong():
    toast, url = login_ui("admin", "Admin@123456", 0, captcha_override="ZZZZ")
    if "验证码" in toast:
        return "PASS", f"验证码错误被拒：「{toast[:60]}」，仍停留 {url}", ""
    return "P1", f"验证码错误未被拦截，toast={toast[:70]!r}", "可绕过图形验证码"


def t_login_wrong_pwd():
    toast, url = login_ui("admin", "WrongPwd@123", 2)
    # 必须先排除验证码干扰，否则「验证码错误」也会命中「错误」二字 → 假通过
    if "验证码" in toast:
        return "ENV", f"验证码环节先失败（{toast[:40]}），未能验证密码校验", ""
    if "密码" in toast:
        return "PASS", f"错误密码被拒：「{toast[:60]}」", ""
    return "P1", f"错误密码未被拦截，toast={toast[:70]!r}", "账号可被爆破"


def t_login_not_approved():
    toast, url = login_ui(NEW_USER, NEW_PWD, 3)
    if "审批" in toast:
        return "PASS", f"未审批账号被正确拦截：「{toast[:70]}」", ""
    if "验证码" in toast:
        return "ENV", f"验证码先失败（{toast[:40]}）", ""
    return "P1", f"未审批账号未被拦截，toast={toast[:70]!r} url={url}", "未审批账号可登录"


def t_login_admin_ok():
    """最后执行：真实登录管理员并确认落地页。"""
    toast, url = login_ui("admin", "Admin@123456", 1)
    if "/dashboard" in url or ("登录成功" in toast and "/login" not in url):
        return "PASS", f"登录成功，跳转 {url}", ""
    if "验证码" in toast:
        return "ENV", f"验证码失败：{toast[:40]}", ""
    return "P1", f"管理员登录未跳转，toast={toast[:70]!r} url={url}", "登录主流程异常"


# ---------------------------------------------------------------- 执行
e.start()
try:
    e.run("登录", "验证码错误", [
        "访问 /login", "填 admin / 正确密码", "验证码填 ZZZZ（故意错）", "点击登录",
    ], "提示验证码错误，不发放令牌", t_captcha_wrong)

    e.run("登录", "密码错误", [
        "访问 /login", "填 admin / 错误密码", "填入正确验证码", "点击登录",
    ], "提示账号或密码错误", t_login_wrong_pwd)

    e.run("登录", "未审批账号登录（注册闭环）", [
        f"用刚注册的 {NEW_USER} 登录", "填正确密码与验证码", "点击登录",
    ], "提示账号正在审批中，拒绝登录", t_login_not_approved)

    e.run("登录", "管理员正常登录", [
        "访问 /login", "admin / Admin@123456", "填正确验证码", "点击登录",
    ], "登录成功并进入工作台", t_login_admin_ok)
finally:
    e.stop()
    with open(os.path.join(HERE, "phase2.json"), "w", encoding="utf-8") as f:
        json.dump({"result": result, "rows": e.rows}, f, ensure_ascii=False, indent=1)
    passes = sum(1 for r in e.rows if r["verdict"] == "PASS")
    print(f"\n阶段二：{len(e.rows)} 项，通过 {passes}，问题 {len(e.rows)-passes}")
