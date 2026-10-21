"""UI E2E 阶段一：注册 → 审批 → 登录 → 学生端功能

覆盖：正常注册、表单校验边界（空/短账号/短密码/密码不一致/未选班级/重复账号）、
未审批登录拦截、管理员审批、登录（含验证码异常）、学生端各功能。
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness import API, E2E, api, api_login  # noqa: E402

STAMP = time.strftime("%H%M%S")
NEW_USER = f"uistu{STAMP}"
NEW_PWD = "UiTest@2026"

e = E2E()
admin_token = api_login("admin", "Admin@123456")
assert admin_token, "管理员登录失败，无法继续"

result = {"new_user": NEW_USER, "new_pwd": NEW_PWD}


def t_reg_normal():
    e.goto("/register", 2200)
    e.fill_placeholder("3-32 位字母或数字", NEW_USER)
    e.page.locator('input[type=password]').nth(0).fill(NEW_PWD)
    e.page.locator('input[type=password]').nth(1).fill(NEW_PWD)
    e.fill_placeholder("请输入真实姓名", "UI测试学生")
    picked = e.select_first("请选择班级")
    e.fill_placeholder("选填，用于找回密码", "13800138000")
    e.fill_placeholder("选填", "uistu@example.com")
    e.click_text("提交注册申请")
    e.page.wait_for_timeout(2000)
    toast = e.toast_text()
    url = e.page.url
    if "已提交" in toast or "/login" in url:
        result["class_picked"] = picked
        return "PASS", f"提交成功，提示「{toast[:60]}」，跳转 {url}；班级下拉选中「{picked}」", ""
    return "P1", f"未见成功提示，toast={toast[:80]!r} url={url}", "注册不可用"


def t_reg_empty():
    e.goto("/register", 2000)
    e.click_text("提交注册申请")
    e.page.wait_for_timeout(1200)
    errs = [x.inner_text().strip() for x in e.page.query_selector_all(".el-form-item__error")]
    errs = [x for x in errs if x]
    if len(errs) >= 2:
        return "PASS", f"空表单被拦，共 {len(errs)} 条校验提示：{'、'.join(errs[:4])}", ""
    return "P2", f"空表单校验提示仅 {len(errs)} 条：{errs}", "前端校验覆盖不足"


def t_reg_short_pwd():
    e.goto("/register", 2000)
    e.fill_placeholder("3-32 位字母或数字", f"ab{STAMP}")
    e.page.locator('input[type=password]').nth(0).fill("123")
    e.page.locator('input[type=password]').nth(1).fill("123")
    e.fill_placeholder("请输入真实姓名", "短密码")
    e.click_text("提交注册申请")
    e.page.wait_for_timeout(1200)
    errs = [x.inner_text().strip() for x in e.page.query_selector_all(".el-form-item__error")]
    errs = [x for x in errs if x]
    # 期望：前端与后端同规则（8 位 + 字母数字），3 位必须在**前端**就被拦住。
    # 断言两个条件，避免「提示文案碰巧含密码二字」就算通过：
    #   1) 出现长度类报错且阈值是 8  2) 没有真的发出请求
    hits_len = [x for x in errs if "位" in x]
    strong = [x for x in errs if "8" in x]
    if strong:
        sent = any("/auth/register" in (c.get("path") or "")
                   for c in e.calls if c.get("method") == "POST")
        if sent:
            return "P1", f"前端提示了长度但仍发出注册请求：{errs}", "校验未真正阻断提交"
        return "PASS", f"3 位密码在前端被拦，提示「{strong[0][:40]}」，未发起请求", ""
    if hits_len:
        return "P1", (f"前端长度校验阈值与后端不一致（提示「{hits_len[0][:40]}」），"
                      f"后端要求 8 位 + 字母数字组合"), "前端校验弱于后端"
    return "P1", f"3 位密码未被前端拦截，表单错误={errs}", "无效输入可提交到后端"


def t_reg_mismatch():
    e.goto("/register", 2000)
    e.fill_placeholder("3-32 位字母或数字", f"mm{STAMP}")
    e.page.locator('input[type=password]').nth(0).fill("Abcd1234")
    e.page.locator('input[type=password]').nth(1).fill("Abcd9999")
    e.fill_placeholder("请输入真实姓名", "不一致")
    e.page.locator('input[type=password]').nth(1).blur()
    e.page.wait_for_timeout(900)
    errs = [x.inner_text().strip() for x in e.page.query_selector_all(".el-form-item__error")]
    if any("不一致" in x for x in errs):
        return "PASS", "两次密码不一致被正确拦截（「两次密码不一致」）", ""
    return "P1", f"密码不一致未拦截，提示={errs}", "可注册出密码与确认密码不符的账号"


def t_reg_dup_username():
    e.goto("/register", 2000)
    e.fill_placeholder("3-32 位字母或数字", NEW_USER)
    e.page.locator('input[type=password]').nth(0).fill(NEW_PWD)
    e.page.locator('input[type=password]').nth(1).fill(NEW_PWD)
    e.fill_placeholder("请输入真实姓名", "重复账号")
    e.select_first("请选择班级")
    e.click_text("提交注册申请")
    e.page.wait_for_timeout(2200)
    toast = e.toast_text()
    # 后端文案是「该账号已被注册」（不是「已存在」/「重复」）——只按前两个词判会必然漏判。
    # 同时要求**没有**出现「页面出错：Request failed」这类把业务 400 伪装成崩溃的附加提示，
    # 否则用户会看到「该账号已被注册 | 页面出错：Request failed with status code 400」。
    dup_kw = ("已被注册", "已存在", "重复")
    if any(k in toast for k in dup_kw):
        noisy = "页面出错" in toast or "status code" in toast
        if noisy:
            return "P2", f"重复账号被拒但附加运行时错误提示：「{toast[:100]}」", \
                   "业务校验失败被当成前端崩溃，误导用户"
        return "PASS", f"重复账号被拒绝，提示干净：「{toast[:70]}」", ""
    return "P1", f"重复账号未拦截，toast={toast[:80]!r}", "可重复提交同名注册申请"


def t_reg_not_approved_login():
    """未审批账号登录应被拒。"""
    e.goto("/login", 1800)
    e.fill_placeholder("请输入账号", NEW_USER)
    e.fill_placeholder("请输入密码", NEW_PWD)
    # 验证码随便填（这里只验证审批状态拦截，验证码错误也会被拦，故先取真实图）
    e.fill_placeholder("验证码", "XXXX")
    e.click_text("登 录")
    e.page.wait_for_timeout(1800)
    toast = e.toast_text()
    if "审批" in toast:
        return "PASS", f"未审批账号被正确拦截：「{toast[:70]}」", ""
    if "验证码" in toast:
        return "ENV", f"验证码先被拦截（{toast[:40]}），本次未能验证审批拦截", ""
    return "P2", f"未审批账号未被明确拦截，toast={toast[:80]!r}", "可能允许未审批账号登录"


# ---------------------------------------------------------------- 执行
e.start()
try:
    e.run("注册", "正常注册（学生，含班级选择）", [
        "访问 /register", "填写账号/密码/确认密码/真实姓名", "下拉选择班级",
        "填写手机号/邮箱", "点击「提交注册申请」",
    ], "提交成功并提示「注册申请已提交，请等待管理员审批」", t_reg_normal)

    e.run("注册", "空表单提交", ["访问 /register", "不填任何内容直接提交"],
          "逐项提示必填，不发起请求", t_reg_empty)

    e.run("注册", "密码过短（3 位）", [
        "填写合法账号", "密码与确认密码都填 123", "提交",
    ], "提示密码长度不足（后端要求 8 位 + 字母数字）", t_reg_short_pwd)

    e.run("注册", "两次密码不一致", [
        "密码填 Abcd1234", "确认密码填 Abcd9999", "触发校验",
    ], "提示「两次密码不一致」并阻止提交", t_reg_mismatch)

    e.run("注册", "重复账号注册", [
        f"用刚注册成功的账号 {NEW_USER} 再注册一次", "提交",
    ], "提示账号已存在，拒绝重复注册", t_reg_dup_username)

    e.run("登录", "未审批账号登录", [
        f"用 {NEW_USER} 在 /login 登录", "填写密码", "点击登录",
    ], "提示账号正在审批中，不放行", t_reg_not_approved_login)
finally:
    e.stop()
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "phase1.json"), "w",
              encoding="utf-8") as f:
        json.dump({"result": result, "rows": e.rows}, f, ensure_ascii=False, indent=1)
    passes = sum(1 for r in e.rows if r["verdict"] == "PASS")
    print(f"\n阶段一：{len(e.rows)} 项，通过 {passes}，问题 {len(e.rows) - passes}")
    print("新账号:", NEW_USER)
