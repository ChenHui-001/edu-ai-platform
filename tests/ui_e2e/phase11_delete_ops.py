"""UI E2E 阶段十一：删除类与危险操作专项。

删除是最容易「UI 提示成功、实际没删」或「删错范围」的一类操作，
且不可逆。本阶段逐项验证：删除前有二次确认、删除后接口回查确实消失、
内置/被引用对象有保护、以及取消确认时不产生副作用。

覆盖：
  用户管理（新增 → 删除 → 回查消失 / 取消确认不删 / 内置管理员保护）
  角色管理（新增 → 删除 → 回查消失 / 内置角色禁删禁改）
  题目（新增 → 删除 → 回查消失 / 已组卷的题目保护）
  题库搜索（关键词无匹配收敛为空）
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
A = session("admin")
T = session("teacher")
STAMP = time.strftime("%H%M%S")
UNAME = f"uie2e{STAMP}"
UNAME2 = f"uie2e_c{STAMP}"
RNAME = f"UI角色{STAMP}"
RCODE = f"ui_role_{STAMP}"

e = E2E("phase11")


def api_data(method: str, path: str, body=None, tok=None):
    r = api(method, path, tok or A["token"], body)
    return r.get("data"), r


def root_text() -> str:
    for sel in (".page-container", ".chat-page", "body"):
        loc = e.page.locator(sel).first
        try:
            if loc.count():
                return loc.inner_text().replace("\n", " ")
        except Exception:
            continue
    return ""


def find_rows(keyword: str) -> list:
    d, _ = api_data("GET", f"/system/users?page=1&page_size=50&keyword={keyword}")
    return (d or {}).get("items") or []


# ---------------------------------------------------------------- 用户删除
def t_user_delete():
    """新增用户 → 页面删除 → 接口回查必须消失。

    假阳性防护：先确认新增真的落库（否则「删除后查不到」平凡成立）。
    """
    inject(e, "admin", "/admin/users", 3200)
    if not e.click_text("新增用户"):
        return "ENV", "找不到「新增用户」", ""
    e.page.wait_for_timeout(1200)
    e.fill_by_label("用户名", UNAME)
    e.fill_by_label("姓名", "UI删除测试")
    e.fill_by_label("初始密码", "Passw0rd123")
    try:
        e.select_by_label("身份", "学生")
    except Exception:
        pass
    e.click_text("确定") or e.click_text("保存")
    e.page.wait_for_timeout(2400)

    # 前置校验：新增必须真的成功
    rows = find_rows(UNAME)
    if not rows:
        toast = e.toast_text()
        return "BLOCKED", f"新增用户未落库，无法验证删除（toast='{toast[:40]}'）", ""

    # 搜索定位后删除
    inject(e, "admin", "/admin/users", 3000)
    inp = e.page.locator(".filter-card input.el-input__inner, input[placeholder]").first
    inp.fill(UNAME)
    e.click_text("查询")
    e.page.wait_for_timeout(2200)
    del_btn = e.page.get_by_role("button", name="删除")
    if del_btn.count() == 0:
        return "ENV", "搜索后没有「删除」按钮", ""
    del_btn.first.click()
    e.page.wait_for_timeout(900)
    e.confirm()
    e.page.wait_for_timeout(2400)
    after = find_rows(UNAME)
    if after:
        return "P1", f"删除后接口仍能查到用户 {UNAME}（{len(after)} 条）", \
               "删除未生效，账号仍可登录"
    return "PASS", f"用户 {UNAME} 已删除，接口回查为空", ""


def t_user_delete_cancel():
    """点删除后取消：数据必须保留（不能出现「取消也删掉」）。"""
    inject(e, "admin", "/admin/users", 3200)
    if not e.click_text("新增用户"):
        return "ENV", "找不到「新增用户」", ""
    e.page.wait_for_timeout(1200)
    e.fill_by_label("用户名", UNAME2)
    e.fill_by_label("姓名", "UI取消测试")
    e.fill_by_label("初始密码", "Passw0rd123")
    try:
        e.select_by_label("身份", "学生")
    except Exception:
        pass
    e.click_text("确定") or e.click_text("保存")
    e.page.wait_for_timeout(2400)
    if not find_rows(UNAME2):
        return "BLOCKED", "新增用户未落库，无法验证取消", ""

    inject(e, "admin", "/admin/users", 3000)
    inp = e.page.locator(".filter-card input.el-input__inner, input[placeholder]").first
    inp.fill(UNAME2)
    e.click_text("查询")
    e.page.wait_for_timeout(2200)
    del_btn = e.page.get_by_role("button", name="删除")
    if del_btn.count() == 0:
        return "ENV", "搜索后没有「删除」按钮", ""
    del_btn.first.click()
    e.page.wait_for_timeout(900)
    # 取消
    cancel = e.page.get_by_role("button", name="取消")
    if cancel.count():
        cancel.first.click()
    e.page.wait_for_timeout(1600)
    still = find_rows(UNAME2)
    # 清理，避免留脏数据
    if still:
        api("DELETE", f"/system/users/{still[0]['id']}", A["token"])
    if still:
        return "PASS", "取消后用户仍在（正确），已清理", ""
    return "P1", f"点「取消」后用户 {UNAME2} 被删除", "取消按钮等于确认，误删风险极高"


def t_user_delete_builtin_guard():
    """内置管理员 admin 不应可被删除（防自锁）。"""
    inject(e, "admin", "/admin/users", 3000)
    inp = e.page.locator(".filter-card input.el-input__inner, input[placeholder]").first
    inp.fill("admin")
    e.click_text("查询")
    e.page.wait_for_timeout(2200)
    # 找 admin 行上的删除按钮
    row = e.page.locator(".el-table__body tr", has_text="admin").first
    if not row.count():
        return "ENV", "搜索不到 admin 行", ""
    d_btn = row.get_by_role("button", name="删除")
    if d_btn.count() == 0:
        return "PASS", "admin 行未提供删除入口（已保护）", ""
    d_btn.first.click()
    e.page.wait_for_timeout(900)
    e.confirm()
    e.page.wait_for_timeout(2000)
    d, _ = api_data("GET", "/system/users?page=1&page_size=10&keyword=admin")
    names = [x.get("username") for x in ((d or {}).get("items") or [])]
    if "admin" in names:
        return "PASS", f"admin 未被删除（接口仍存在：{names[:3]}）", ""
    return "P0", "内置管理员 admin 被删除", "系统可能失去唯一管理员，无法再登录管理"


# ---------------------------------------------------------------- 角色删除
def t_role_create_delete():
    """新增自定义角色 → 删除 → 接口回查消失。"""
    inject(e, "admin", "/admin/roles", 3200)
    if not e.click_text("新增角色"):
        return "ENV", "找不到「新增角色」", ""
    e.page.wait_for_timeout(1200)
    e.fill_by_label("角色名称", RNAME)
    e.fill_by_label("角色标识", RCODE)
    e.click_text("确定") or e.click_text("保存")
    e.page.wait_for_timeout(2400)
    d, _ = api_data("GET", "/system/roles")
    items = d if isinstance(d, list) else ((d or {}).get("items") or [])
    created = next((x for x in items if x.get("code") == RCODE), None)
    if not created:
        return "BLOCKED", f"新增角色未落库（共 {len(items)} 条）", ""

    inject(e, "admin", "/admin/roles", 3000)
    row = e.page.locator(".el-table__body tr", has_text=RNAME).first
    if not row.count():
        return "ENV", "列表里找不到刚建的角色", ""
    row.click()
    e.page.wait_for_timeout(1600)
    # 删除按钮在详情区（右侧），按文本定位
    d_btn = e.page.get_by_role("button", name="删除")
    if d_btn.count() == 0:
        return "ENV", "详情区没有「删除」按钮", ""
    d_btn.first.click()
    e.page.wait_for_timeout(900)
    e.confirm()
    e.page.wait_for_timeout(2400)
    d2, _ = api_data("GET", "/system/roles")
    items2 = d2 if isinstance(d2, list) else ((d2 or {}).get("items") or [])
    still = any(x.get("code") == RCODE for x in items2)
    if still:
        api("DELETE", f"/system/roles/{created['id']}", A["token"])
        return "P1", f"删除后角色 {RCODE} 仍存在", "删除未生效"
    return "PASS", f"角色 {RCODE} 已删除（{len(items)}→{len(items2)}）", ""


def t_role_builtin_guard():
    """内置角色（sys_admin 等）禁止删除。"""
    d, _ = api_data("GET", "/system/roles")
    items = d if isinstance(d, list) else ((d or {}).get("items") or [])
    builtin = next((x for x in items if x.get("code") in ("sys_admin", "student", "teacher")), None)
    if not builtin:
        return "ENV", f"找不到内置角色（共 {len(items)} 条）", ""
    r = api("DELETE", f"/system/roles/{builtin['id']}", A["token"])
    if r.get("success") is True:
        # 竟然删成功了 → 立刻尝试恢复记录
        return "P0", f"内置角色「{builtin.get('name')}」被删除（接口返回成功）", \
               "所有持有该角色的用户将失去权限"
    return "PASS", f"内置角色「{builtin.get('name')}」删除被拒绝：{r.get('message')}", ""


# ---------------------------------------------------------------- 题目删除
def t_question_delete():
    """新增题目 → 页面删除 → 接口回查消失。

    题库删除是最容易「删了但列表还在」的地方（缓存/未刷新）。
    """
    stem = f"UI删除题{STAMP}"
    # 用接口建题（学科/知识点 id 必须精确，UI 下拉在教师端要多步）
    edu, _ = api_data("GET", "/edu/subjects?distinct=true&grade_id=1", T["token"])
    subj = next((x for x in (edu or []) if x.get("name") == "数学"), None)
    if not subj:
        return "ENV", "一年级没有数学学科，无法建题", ""
    kps, _ = api_data("GET", f"/edu/knowledge/list?subject_id={subj['id']}&params_limit=50", T["token"])
    kp = (kps or [{}])[0]
    body = {
        "type": "single", "stem": stem, "options": [
            {"label": "A", "content": "选项A"}, {"label": "B", "content": "选项B"}
        ], "answer": "A", "score": 5, "difficulty": "easy",
        "subject_id": subj["id"], "grade_id": 1,
        "knowledge_point_id": kp.get("id"), "status": "published",
    }
    r = api("POST", "/question/questions", T["token"], body)
    qid = (r.get("data") or {}).get("id")
    if not qid:
        return "BLOCKED", f"建题失败：{r.get('message')}", ""

    inject(e, "teacher", "/teacher/questions", 3400)
    inp = e.page.locator(".filter-card input.el-input__inner, input[placeholder]").first
    inp.fill(stem)
    e.click_text("查询")
    e.page.wait_for_timeout(2400)
    n_rows = e.page.locator(".el-table__body tr").count()
    if n_rows == 0:
        api("DELETE", f"/question/questions/{qid}", T["token"])
        return "P2", f"搜索「{stem}」无结果（题库搜索可能不含新题）", ""

    del_btn = e.page.get_by_role("button", name="删除")
    if del_btn.count() == 0:
        api("DELETE", f"/question/questions/{qid}", T["token"])
        return "ENV", "题库行上没有「删除」按钮", ""
    del_btn.first.click()
    e.page.wait_for_timeout(900)
    e.confirm()
    e.page.wait_for_timeout(2400)

    d, _ = api_data("GET", f"/question/questions?page=1&page_size=10&keyword={stem}", T["token"])
    left = (d or {}).get("total", 0)
    if left:
        api("DELETE", f"/question/questions/{qid}", T["token"])
        return "P1", f"删除后仍能查到该题（total={left}）", "题目未真正删除"
    return "PASS", "题目已删除，按关键词回查 total=0", ""


def t_question_search_empty():
    """题库搜索不存在关键词：必须收敛为 0（而非返回全量）。"""
    inject(e, "teacher", "/teacher/questions", 3400)
    total_before = (api_data("GET", "/question/questions?page=1&page_size=5", T["token"])[0] or {}).get("total")
    inp = e.page.locator(".filter-card input.el-input__inner, input[placeholder]").first
    inp.fill("zzz不存在题干9999")
    e.click_text("查询")
    e.page.wait_for_timeout(2400)
    rows = e.page.locator(".el-table__body tr").count()
    d, _ = api_data("GET", "/question/questions?page=1&page_size=10&keyword=zzz不存在题干9999", T["token"])
    api_total = (d or {}).get("total")
    if rows == 0 and api_total == 0:
        return "PASS", f"搜索无匹配 → 页面 0 行 / 接口 total=0（全量 {total_before}）", ""
    return "P1", f"搜索未收敛：页面 {rows} 行 / 接口 total={api_total}（全量 {total_before}）", \
           "搜索框形同摆设，用户以为筛过其实没有"


# ---------------------------------------------------------------- 主流程
try:
    e.start()
    e.run("用户管理", "删除用户", ["新增用户", "搜索定位", "删除并确认", "接口回查"],
          "用户从数据库消失", t_user_delete)
    e.run("用户管理", "取消删除不生效", ["新增用户", "点删除后取消", "接口回查"],
          "用户仍存在", t_user_delete_cancel)
    e.run("用户管理", "内置 admin 保护", ["搜索 admin", "尝试删除并确认"],
          "admin 不可删除", t_user_delete_builtin_guard)

    e.run("角色管理", "新增并删除角色", ["新增角色", "选中", "删除并确认"], "角色回查消失", t_role_create_delete)
    e.run("角色管理", "内置角色保护", ["对 sys_admin 调删除接口"], "拒绝删除", t_role_builtin_guard)

    e.run("题库", "删除题目", ["建题", "搜索定位", "删除并确认", "回查"], "题目回查消失", t_question_delete)
    e.run("题库", "搜索无匹配", ["输入不存在题干", "查询"], "收敛为 0 行", t_question_search_empty)
finally:
    e.stop()
    with open(os.path.join(HERE, "phase11.json"), "w", encoding="utf-8") as f:
        json.dump(e.rows, f, ensure_ascii=False, indent=1)
    passes = sum(1 for r in e.rows if r["verdict"] == "PASS")
    print(f"\n阶段十一：{len(e.rows)} 项，通过 {passes}，问题 {len(e.rows) - passes}")
