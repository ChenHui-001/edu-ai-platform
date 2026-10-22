"""UI E2E 阶段四：管理员端 —— 用户管理 / 角色权限 / 系统配置

重点覆盖输入框、下拉框、搜索、删除（含删除确认与保护性拦截）。
"""
from __future__ import annotations

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness import E2E, api  # noqa: E402
from session import inject, session  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ADMIN = session("admin")
STAMP = time.strftime("%H%M%S")

e = E2E()



def fill_by_label(label: str, value: str, scope: str = ".el-dialog") -> bool:
    """按 el-form-item 的 label 精确填写（弹窗内输入框普遍无 placeholder）。"""
    try:
        item = e.page.locator(f"{scope} .el-form-item", has_text=label).first
        inp = item.locator("input").first
        inp.fill(value, timeout=6000)
        return True
    except Exception:
        return False


def pick_select_by_label(label: str, option_text: str, scope: str = ".el-dialog") -> bool:
    """按 label 定位 el-select 并选中指定选项。"""
    try:
        item = e.page.locator(f"{scope} .el-form-item", has_text=label).first
        item.locator(".el-select").first.click(timeout=6000)
        e.page.wait_for_timeout(600)
        e.page.locator(".el-select-dropdown__item:visible", has_text=option_text).first.click()
        e.page.wait_for_timeout(400)
        return True
    except Exception:
        return False


def t_users_render():
    url = inject(e, "admin", "/admin/users", 2800)
    if "/login" in url:
        return "P0", f"被弹回登录页（{url}）", "用户管理不可访问"
    rows = e.row_count()
    txt = e.text()
    if "用户管理" not in txt:
        return "P2", f"页面标题缺失：{txt[:100]!r}", ""
    if rows == 0:
        return "P1", f"用户表格 0 行（空态：{e.empty_hint()}）", "用户列表无法加载"
    total = ""
    import re
    m = re.search(r"共\s*(\d+)\s*条", txt)
    if m:
        total = f"共 {m.group(1)} 条"
    return "PASS", f"渲染 {rows} 行，{total}", ""


def t_users_search():
    before = e.row_count()
    if not e.fill_placeholder("用户名/姓名/手机号", "teacher"):
        # 尝试通用搜索框
        return "P2", "用户管理页未发现搜索输入框", "无法按账号检索"
    e.page.keyboard.press("Enter")
    e.page.wait_for_timeout(1800)
    after = e.row_count()
    txt = e.text()
    if "teacher" in txt and after >= 1 and after <= before:
        return "PASS", f"搜索「teacher」命中，行数 {before}→{after}", ""
    return "P1", f"搜索未收敛（{before}→{after}）", "用户检索不可用"


def t_users_search_empty():
    e.fill_placeholder("用户名/姓名/手机号", "zzz_no_user_9999")
    e.page.keyboard.press("Enter")
    e.page.wait_for_timeout(1600)
    rows = e.row_count()
    hint = e.empty_hint()
    if rows == 0:
        return "PASS", f"无匹配返回 0 行，空态「{hint[:30] or '无文案'}」", ""
    return "P2", f"无匹配仍返回 {rows} 行", "搜索条件被忽略"


def t_users_create_weak_pwd():
    """新增用户时填弱口令，应被拦住。"""
    inject(e, "admin", "/admin/users", 2400)
    if not e.click_text("新增用户"):
        return "P2", "未找到「新增用户」按钮", "无法创建用户"
    e.page.wait_for_timeout(1300)
    uname = f"uipw{STAMP}"
    fill_by_label("用户名", uname)
    fill_by_label("姓名", "弱口令测试")
    if not fill_by_label("初始密码", "123456"):
        return "ENV", "弹窗内未找到初始密码输入框", ""
    pick_select_by_label("身份", "学生")
    e.page.locator(".el-dialog").get_by_role("button", name="确定").click()
    e.page.wait_for_timeout(2200)
    toast = e.toast_text()
    errs = [x.inner_text().strip() for x in e.page.query_selector_all(".el-form-item__error")]
    blocked = ("8" in toast or "8" in str(errs) or "简单" in toast
               or "字母" in toast or "强度" in toast)
    # 用接口核实是否真的建出了账号
    r = api("GET", f"/system/users?keyword={uname}", ADMIN["token"])
    items = (r.get("data") or {}).get("items") if isinstance(r.get("data"), dict) else None
    created = bool(items)
    if blocked and not created:
        return "PASS", f"弱口令被拦：{(errs or [toast])[0][:70]}", ""
    if created:
        return "P0", f"6 位纯数字密码成功建号（{uname} 已存在于用户列表），toast={toast[:60]!r}", \
               "可批量创建弱口令账号"
    return "P1", f"未见明确拦截原因，toast={toast[:70]!r} errs={errs}", "用户不知为何提交失败"


def t_users_reset_pwd():
    """重置密码（v1.0.40 修过 password/new_password 契约，验证 UI 是否真能用）。"""
    inject(e, "admin", "/admin/users", 2400)
    if not e.fill_placeholder("用户名/姓名/手机号", "teacher1"):
        return "P2", "无法搜索到目标用户", ""
    e.page.keyboard.press("Enter")
    e.page.wait_for_timeout(1600)
    btn = e.page.get_by_role("button", name="重置密码")
    if btn.count() == 0:
        # 可能在行内下拉菜单里
        more = e.page.get_by_role("button", name="更多")
        if more.count():
            more.first.click()
            e.page.wait_for_timeout(700)
            btn = e.page.get_by_role("button", name="重置密码")
    if btn.count() == 0:
        return "P2", "未找到「重置密码」入口", "管理员无法重置密码"
    btn.first.click()
    e.page.wait_for_timeout(1300)
    # 直接确认（留空应自动生成强密码）
    for label in ("确定", "确认", "重置"):
        b = e.page.get_by_role("button", name=label)
        if b.count() and b.last.is_visible():
            b.last.click()
            break
    e.page.wait_for_timeout(2200)
    toast = e.toast_text()
    if "密码" in toast and ("已重置" in toast or "生成" in toast):
        return "PASS", f"重置成功：「{toast[:80]}」", ""
    if "422" in toast or "校验" in toast:
        return "P0", f"重置密码请求 422（字段契约错位）：{toast[:90]}", "管理员无法重置任何用户密码"
    return "P1", f"未见成功反馈，toast={toast[:80]!r}", "重置密码结果不明确"


def t_roles_render():
    url = inject(e, "admin", "/admin/roles", 2600)
    if "/login" in url:
        return "P0", f"被弹回登录页（{url}）", "角色权限不可访问"
    txt = e.text()
    rows = e.row_count()
    if "角色" not in txt:
        return "P2", f"页面异常：{txt[:100]!r}", ""
    if rows == 0:
        return "P1", "角色列表 0 行", "角色数据未加载"
    return "PASS", f"角色列表渲染 {rows} 行", ""


def t_roles_delete_builtin():
    """删除内置角色必须被拒（入口在点击角色行后的右侧操作区）。"""
    inject(e, "admin", "/admin/roles", 2400)
    row = e.page.locator(".el-table__row", has_text="系统管理员").first
    if row.count() == 0:
        return "ENV", "未找到内置角色「系统管理员」行", ""
    row.click()
    e.page.wait_for_timeout(1200)
    btn = e.page.get_by_role("button", name="删除")
    if btn.count() == 0:
        return "P2", "点击内置角色后仍无「删除」按钮", "内置角色保护无法在 UI 层面验证"
    btn.first.click()
    e.page.wait_for_timeout(1000)
    for label in ("确定", "确认"):
        b = e.page.get_by_role("button", name=label)
        if b.count() and b.last.is_visible():
            b.last.click()
            break
    e.page.wait_for_timeout(2000)
    toast = e.toast_text()
    # 接口核实角色是否还在
    r = api("GET", "/system/roles", ADMIN["token"])
    roles = r.get("data") or []
    still = any(x.get("code") == "sys_admin" for x in roles if isinstance(x, dict))
    if still and ("内置" in toast or "不允许" in toast or "不可" in toast):
        return "PASS", f"内置角色删除被拒且角色仍在：「{toast[:70]}」", ""
    if still:
        return "P3", f"角色未被删除但无明确原因提示（toast={toast[:50]!r}）", "用户不知为何删不掉"
    return "P0", f"内置角色 sys_admin 被删除！toast={toast[:60]!r}", "系统可能失去唯一超管角色"


def t_config_render():
    url = inject(e, "admin", "/admin/settings", 2400)
    if "/dashboard" in url:
        return "P1", "访问 /admin/settings 被兜底重定向到 /dashboard", "配置入口不可达"
    if "/login" in url:
        return "P2", f"配置页路径不可达（最终 {url}）", "系统配置入口异常"
    txt = e.text()
    return "PASS", f"配置页可访问（{url}），可见文本前 80 字：{txt[:80]!r}", ""


e.start()
try:
    e.run("用户管理", "列表加载", ["管理员访问 /admin/users"], "渲染用户表格并显示总数", t_users_render)
    e.run("用户管理", "搜索框检索已有账号", [
        "搜索框输入 teacher", "回车",
    ], "列表收敛为匹配项", t_users_search)
    e.run("用户管理", "搜索框检索不存在账号", [
        "搜索框输入 zzz_no_user_9999", "回车",
    ], "列表为空并给出空态", t_users_search_empty)
    e.run("用户管理", "新增用户填弱口令 123456", [
        "点击新增用户", f"账号填 uipw{STAMP}", "密码填 123456", "提交",
    ], "被密码强度校验拦住（至少 8 位且含字母）", t_users_create_weak_pwd)
    e.run("用户管理", "重置用户密码", [
        "搜索 teacher1", "点击重置密码", "留空自动生成强密码并确认",
    ], "提示重置成功并返回新密码", t_users_reset_pwd)
    e.run("角色权限", "角色列表加载", ["访问 /admin/roles"], "渲染角色列表", t_roles_render)
    e.run("角色权限", "删除内置角色", [
        "定位「系统管理员」行", "点击删除并确认",
    ], "拒绝删除并说明内置角色不可删", t_roles_delete_builtin)
    e.run("系统配置", "系统配置页可访问", ["访问系统配置页"], "页面正常渲染配置项", t_config_render)
finally:
    e.stop()
    with open(os.path.join(HERE, "phase4.json"), "w", encoding="utf-8") as f:
        json.dump(e.rows, f, ensure_ascii=False, indent=1)
    passes = sum(1 for r in e.rows if r["verdict"] == "PASS")
    print(f"\n阶段四：{len(e.rows)} 项，通过 {passes}，问题 {len(e.rows)-passes}")
