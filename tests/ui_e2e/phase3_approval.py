"""UI E2E 阶段三：管理员审批注册申请 → 新账号登录闭环

会话通过 session.inject 注入（等价已登录），审批操作走真实 UI 点击。
"""
from __future__ import annotations

import base64
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness import E2E, api  # noqa: E402
from session import inject, session  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
P1 = json.load(open(os.path.join(HERE, "phase1.json"), encoding="utf-8"))
NEW_USER = P1["result"]["new_user"]
NEW_PWD = P1["result"]["new_pwd"]

e = E2E()
ADMIN = session("admin")


def pending_of(username: str):
    r = api("GET", "/auth/registrations?status=pending", ADMIN["token"])
    items = (r.get("data") or {}).get("items") or []
    return [x for x in items if x.get("username") == username]


# ---------------------------------------------------------------- 用例
def t_page_render():
    url = inject(e, "admin", "/admin/registrations", 2600)
    txt = e.text()
    rows = e.row_count()
    if "/login" in url:
        return "P0", f"被弹回登录页（{url}）", "审批页不可访问"
    if "注册审批" not in txt:
        return "P2", f"页面标题「注册审批」缺失：{txt[:100]!r}", "页面标识不一致"
    if rows == 0:
        return "P1", f"表格 0 行（空态：{e.empty_hint()}）", "审批列表无法加载"
    # 是否有操作按钮
    n_pass = e.page.get_by_role("button", name="通过").count()
    n_rej = e.page.get_by_role("button", name="拒绝").count()
    return "PASS", f"渲染 {rows} 行 待审批记录，「通过」{n_pass} 个 /「拒绝」{n_rej} 个", ""


def t_empty_state():
    """筛选无结果时的空态与提示。"""
    inject(e, "admin", "/admin/registrations", 2400)
    filled = e.fill_placeholder("请输入账号", "no_such_user_zzz")
    if not filled:
        # 页面上可能没有搜索框，直接看是否支持搜索
        return "P2", "审批页未找到账号搜索框（输入框无 placeholder），无法按账号筛选", \
               "待审批量大时难以定位"
    e.page.keyboard.press("Enter")
    e.page.wait_for_timeout(1600)
    rows = e.row_count()
    hint = e.empty_hint()
    if rows == 0 and hint:
        return "PASS", f"无匹配时展示空态：「{hint[:40]}」", ""
    if rows == 0:
        return "P3", "无匹配时表格为空但无空态文案", "用户无法判断是「无数据」还是「未加载」"
    return "P2", f"搜索不存在的账号仍返回 {rows} 行", "筛选未生效"


def t_reject_needs_reason():
    """拒绝时不填理由应被拦住。"""
    inject(e, "admin", "/admin/registrations", 2400)
    btn = e.page.get_by_role("button", name="拒绝")
    if btn.count() == 0:
        return "ENV", "当前无待审批记录，无法验证", ""
    btn.first.click()
    e.page.wait_for_timeout(1200)
    before = pending_of(NEW_USER)
    # 直接点弹窗里的确定/提交，不填原因
    for label in ("确定", "提交", "确 定"):
        b = e.page.get_by_role("button", name=label)
        if b.count() and b.first.is_visible():
            b.first.click()
            break
    e.page.wait_for_timeout(1600)
    toast = e.toast_text()
    after = pending_of(NEW_USER)
    if len(after) == len(before) or "原因" in toast:
        return "PASS", f"未填理由的拒绝被拦（toast={toast[:50]!r}，待审数未变）", ""
    return "P1", f"未填理由即完成拒绝，申请状态已变（toast={toast[:50]!r}）", "可无理由驳回，审批不可追溯"


def t_approve():
    inject(e, "admin", "/admin/registrations", 2400)
    if e.fill_placeholder("请输入账号", NEW_USER):
        e.page.keyboard.press("Enter")
        e.page.wait_for_timeout(1600)
    rows = e.row_count()
    if rows == 0:
        return "P0", f"按账号 {NEW_USER} 搜索后无结果（无法定位待审批项）", "审批流程阻断"
    btn = e.page.get_by_role("button", name="通过")
    if btn.count() == 0:
        return "P0", "无「通过」按钮", "审批无法操作"
    btn.first.click()
    e.page.wait_for_timeout(1500)
    for label in ("确定", "提交", "通 过", "通过"):
        b = e.page.get_by_role("button", name=label)
        try:
            if b.count() and b.last.is_visible():
                b.last.click()
                break
        except Exception:
            continue
    e.page.wait_for_timeout(2200)
    toast = e.toast_text()
    still = pending_of(NEW_USER)
    if not still:
        return "PASS", f"审批通过生效，待审列表中已无该账号（toast={toast[:40]!r}）", ""
    return "P0", f"审批未生效，账号仍在 pending（toast={toast[:60]!r}）", "「通过」按钮无效"


def t_new_user_login():
    """审批通过后用新账号真实登录。"""
    pool_file = os.path.join(HERE, "captcha_pool_p3.json")
    if not os.path.exists(pool_file):
        return "ENV", "验证码池未准备，跳过", ""
    item = json.load(open(pool_file, encoding="utf-8"))[0]
    payload = {"code": 200, "message": "ok", "success": True,
               "data": {"key": item["key"],
                        "image": "data:image/png;base64," + base64.b64encode(
                            open(os.path.join(HERE, item["file"]), "rb").read()).decode()}}
    e.page.route("**/api/v1/auth/captcha*",
                 lambda r: r.fulfill(status=200, content_type="application/json",
                                     body=json.dumps(payload)))
    e.goto("/login", 1600)
    e.fill_placeholder("请输入账号", NEW_USER)
    e.fill_placeholder("请输入密码", NEW_PWD)
    e.fill_placeholder("验证码", item["code"])
    e.click_text("登 录")
    e.page.wait_for_timeout(3200)
    url = e.page.url
    toast = e.toast_text()
    if "/login" not in url:
        body = e.text()
        return "PASS", f"登录成功，落地 {url}；页面首行「{body.strip().splitlines()[0][:40] if body.strip() else ''}」", ""
    return "P1", f"审批通过后仍无法登录，toast={toast[:70]!r}", "审批通过未生效"


e.start()
try:
    e.run("注册审批", "审批页加载与列表渲染", ["管理员会话访问 /admin/registrations"],
          "展示待审批列表，含通过/拒绝操作", t_page_render)
    e.run("注册审批", "搜索框筛选不存在的账号", [
        "在账号搜索框输入 no_such_user_zzz", "回车",
    ], "列表为空并给出空态提示", t_empty_state)
    e.run("注册审批", "拒绝申请不填理由", [
        "点击「拒绝」", "弹窗内不填理由直接提交",
    ], "提示必须填写理由，申请状态不变", t_reject_needs_reason)
    e.run("注册审批", "审批通过新注册账号", [
        f"搜索 {NEW_USER}", "点击「通过」并确认",
    ], "该申请移出待审列表", t_approve)
    e.run("注册审批→登录", "审批通过后新账号登录", [
        f"用 {NEW_USER} 走真实验证码登录",
    ], "登录成功进入学生工作台", t_new_user_login)
finally:
    e.stop()
    with open(os.path.join(HERE, "phase3.json"), "w", encoding="utf-8") as f:
        json.dump(e.rows, f, ensure_ascii=False, indent=1)
    passes = sum(1 for r in e.rows if r["verdict"] == "PASS")
    print(f"\n阶段三：{len(e.rows)} 项，通过 {passes}，问题 {len(e.rows)-passes}")
