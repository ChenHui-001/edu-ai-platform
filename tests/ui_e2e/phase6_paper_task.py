"""UI E2E 阶段六：教师端试卷管理 + 作业/考试发布。

覆盖：列表 / 搜索 / 下拉筛选 / 手动组卷（含勾选题目的表格多选）/ 删除 /
日期边界（截止早于开始）/ 及格分超总分 / 发布后学生端可见性。

本轮会**保留**一条已发布的考试任务（TASKMARK），供阶段七学生答题闭环使用。
"""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness import E2E, api  # noqa: E402
from session import inject, session  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
T = session("teacher")
STAMP = time.strftime("%H%M%S")
PMARK = f"UIPAPER{STAMP}"
TASKMARK = f"UITASK{STAMP}"

e = E2E()


def papers():
    r = api("GET", "/question/papers?page=1&page_size=50", T["token"])
    d = r.get("data") or {}
    return d.get("items") or d.get("list") or []


def find_paper(name: str):
    for p in papers():
        if p.get("name") == name:
            return p
    return None


def tasks():
    r = api("GET", "/task/tasks?page=1&page_size=50", T["token"])
    d = r.get("data") or {}
    return d.get("items") or d.get("list") or []


def find_task(title: str):
    for t in tasks():
        if t.get("title") == title:
            return t
    return None


def set_dt(label: str, value: str) -> bool:
    """填 el-date-picker（datetime）。"""
    try:
        item = e.form_item(label, ".el-dialog")
        inp = item.locator("input").first
        inp.click()
        inp.fill("")
        inp.type(value, delay=20)
        e.page.wait_for_timeout(300)
        e.page.keyboard.press("Enter")
        e.page.wait_for_timeout(400)
        return inp.input_value().strip() == value
    except Exception:
        return False


# ---------------------------------------------------------------- 用例
def t_list():
    url = inject(e, "teacher", "/teacher/papers", 2800)
    if "/login" in url:
        return "P0", f"试卷页被弹回登录（{url}）", "教师无法进入试卷管理"
    d = e.dump()
    if not d.get("rows"):
        return "P1", f"试卷表格 0 行，空态「{d.get('empty')}」", "试卷列表不可用"
    return "PASS", f"渲染 {d['rows']} 行，表头 {d['headers'][:7]}", ""


def t_search():
    inject(e, "teacher", "/teacher/papers", 2500)
    target = (papers() or [{}])[0].get("name") or ""
    kw = target[:6]
    if not kw:
        return "ENV", "试卷库无数据", ""
    e.search("试卷名称", kw)
    rows = e.row_count()
    # 第 1 列是展开图标列，试卷名称在第 2 列 —— 用错列会读到空串并误判「搜索未收敛」
    names = [x.inner_text().strip() for x in e.page.query_selector_all(".el-table__row td:nth-child(2)")]
    if rows and all(kw in n for n in names):
        return "PASS", f"搜索「{kw}」→ {rows} 行全部匹配：{names[:3]}", ""
    return "P1", f"搜索未收敛：rows={rows} names={names[:4]}", "试卷检索失效"


def t_search_empty():
    inject(e, "teacher", "/teacher/papers", 2400)
    e.search("试卷名称", "zzz不存在的试卷9999")
    rows, hint = e.row_count(), e.empty_hint()
    if rows == 0:
        return "PASS", f"0 行，空态「{hint[:20] or '无文案'}」", ""
    return "P1", f"无匹配仍返回 {rows} 行", "搜索条件被忽略"


def t_create_empty():
    inject(e, "teacher", "/teacher/papers", 2500)
    e.click_text("手动组卷")
    e.page.wait_for_timeout(1400)
    if not e.dialog_visible():
        return "P2", "点击「手动组卷」未弹出对话框", ""
    e.page.locator(".el-dialog").get_by_role("button", name="创建试卷").click()
    e.page.wait_for_timeout(1600)
    toast = e.toast_text()
    still = e.dialog_visible()
    if still and toast:
        return "PASS", f"空表单被拦：{toast[:70]!r}", ""
    if not still:
        return "P0", "空表单提交后弹窗关闭（可能创建了空试卷）", "试卷库出现脏数据"
    return "P1", "无任何反馈", "用户不知缺什么"


def t_create_ok():
    if not e.dialog_visible():
        inject(e, "teacher", "/teacher/papers", 2500)
        e.click_text("手动组卷")
        e.page.wait_for_timeout(1500)
    if not e.dialog_visible():
        return "P2", "未打开手动组卷弹窗", ""
    e.fill_by_label("试卷名称", PMARK, ".el-dialog")
    # 一年级语文：与 teacher1 任教的「一年级(1)班」一致，后面要下发给该班
    if not e.select_by_label("学科", "语文", ".el-dialog"):
        return "P2", "学科下拉无法选择", ""
    e.page.wait_for_timeout(1200)      # 学科变化会触发题库加载
    e.select_by_label("年级", "一年级", ".el-dialog")
    e.page.wait_for_timeout(1200)
    # 勾选前两条题目
    boxes = e.page.locator(".el-dialog .el-table__body-wrapper tbody tr .el-checkbox")
    n = boxes.count()
    if n == 0:
        return "P2", "组卷弹窗内题库表格为空，无法选题", ""
    for i in range(min(2, n)):
        boxes.nth(i).click()
        e.page.wait_for_timeout(250)
    add = e.page.get_by_role("button", name="加入所选")
    if add.count() and add.first.is_visible():
        add.first.click()
        e.page.wait_for_timeout(700)
    e.page.locator(".el-dialog").get_by_role("button", name="创建试卷").click()
    e.page.wait_for_timeout(2600)
    pc = e.last_call("POST", "/papers")
    got = find_paper(PMARK)
    if got:
        return "PASS", (f"创建成功 id={got.get('id')} 题量={got.get('item_count')} "
                        f"总分={got.get('total_score')} 时长={got.get('duration')}"), ""
    return "P1", f"接口回查无此试卷（POST={pc.get('status')} msg={e.call_msg('POST', '/papers')[:80]!r}）", ""


def t_delete_paper():
    """新建一张一次性试卷并删除（不动 PMARK，它要给阶段七用）。"""
    throwaway = f"{PMARK}DEL"
    inject(e, "teacher", "/teacher/papers", 2500)
    e.click_text("手动组卷")
    e.page.wait_for_timeout(1500)
    if not e.dialog_visible():
        return "P2", "未打开手动组卷弹窗", ""
    e.fill_by_label("试卷名称", throwaway, ".el-dialog")
    e.select_by_label("学科", "数学", ".el-dialog")
    e.page.wait_for_timeout(1200)
    e.select_by_label("年级", "七年级", ".el-dialog")
    e.page.wait_for_timeout(1500)
    boxes = e.page.locator(".el-dialog .el-table__body-wrapper tbody tr .el-checkbox")
    if boxes.count() == 0:
        return "ENV", "题库为空，无法造删除用例的数据", ""
    boxes.first.click()
    e.page.wait_for_timeout(300)
    add = e.page.get_by_role("button", name="加入所选")
    if add.count():
        add.first.click()
        e.page.wait_for_timeout(600)
    e.page.locator(".el-dialog").get_by_role("button", name="创建试卷").click()
    e.page.wait_for_timeout(2400)
    before = find_paper(throwaway)
    if not before:
        return "ENV", "一次性试卷未创建成功，跳过删除验证", ""
    e.search("试卷名称", throwaway)
    if e.row_count() == 0:
        return "ENV", "搜索不到一次性试卷", ""
    e.page.locator(".el-table__row").first.get_by_role("button", name="删除").first.click()
    e.page.wait_for_timeout(900)
    e.confirm()
    e.page.wait_for_timeout(2000)
    after = find_paper(throwaway)
    if after is None:
        return "PASS", f"删除成功（id={before.get('id')} 已不存在）", ""
    return "P1", f"删除后试卷仍存在（id={before.get('id')}）", "删除无效"


def t_pass_score_adapt():
    """选 5 分小卷时及格分必须自动收敛。

    修复前：前端把默认 pass_score=60 硬发给后端，后端按总分校验 →
    400「及格分应在 0~5.0 之间，当前 60.0」，即「小分卷永远发不出去」。
    后端只在**未传** pass_score 时才折算 60%，所以前端必须自己收敛。
    """
    inject(e, "teacher", "/teacher/tasks", 2600)
    e.click_text("发布作业 / 考试")
    e.page.wait_for_timeout(1500)
    if not e.dialog_visible():
        return "P2", "未打开发布弹窗", ""
    got = e.select_by_label("试卷", "5分", ".el-dialog")
    if not got:
        return "ENV", "试卷下拉里没有总分为 5 分的试卷", ""
    e.page.wait_for_timeout(700)
    ps = e.input_value("及格分", ".el-dialog")
    total = 5.0
    try:
        val = float(ps)
    except Exception:
        return "P1", f"及格分读不到（{ps!r}）", ""
    if 0 < val <= total:
        return "PASS", f"选「{got}」后及格分自动收敛为 {val}（≤ 总分 {total}）", ""
    return "P1", f"选「{got}」（总分 {total}）后及格分仍为 {val} → 提交必 400", \
           "总分 < 60 的随堂练习无法发布"


def t_class_dropdown():
    """发布弹窗的「下发班级」下拉必须有班级可选，且只列本人任教的班。

    修复前两处问题：
    1) 前端 `c.data?.items` 读取一个数组响应 → 恒 undefined → 下拉 0 项，
       无任何报错，教师完全无法发布任务；
    2) 修好之后仍列出**全部**班级，教师选中非任教班级会被后端 400
       「只能给自己任教的班级下发」—— 下拉必须用 mine=true 只列任教班级。
    """
    inject(e, "teacher", "/teacher/tasks", 2600)
    e.click_text("发布作业 / 考试")
    e.page.wait_for_timeout(1500)
    if not e.dialog_visible():
        return "P2", "未打开发布弹窗", ""
    item = e.form_item("下发班级", ".el-dialog")
    item.locator(".el-select").first.click()
    e.page.wait_for_timeout(900)
    opts = e.page.locator(".el-select-dropdown__item:visible")
    names = [(opts.nth(i).inner_text().strip()) for i in range(opts.count())]
    e.page.keyboard.press("Escape")
    if not names:
        return "P0", "下发班级下拉 0 选项 → 教师无法发布作业/考试", \
               "核心教学流程在 UI 层完全不可用"
    foreign = [n for n in names if "一年级(1)班" not in n]
    if not any("一年级(1)班" in n for n in names):
        return "P1", f"下拉里没有 teacher1 任教的「一年级(1)班」：{names}", "无法给自己班上布置"
    if foreign:
        return "P1", f"下拉列出了非任教班级 {foreign[:3]}（选中必 400）", \
               "教师会选中无权限的班级再被后端拒绝"
    return "PASS", f"可选班级：{names}（仅任教班级）", ""


def t_publish_date_inverted():
    """截止时间早于开始时间：应被拦截（否则任务一发布即处于已结束状态）。

    注意：此用例必须让**其他字段全部合法**，否则「被拦截」可能来自
    「请选择下发班级」这类无关校验 —— 那是最容易骗过自己的假阳性。
    """
    inject(e, "teacher", "/teacher/tasks", 2600)
    e.click_text("发布作业 / 考试")
    e.page.wait_for_timeout(1500)
    if not e.dialog_visible():
        return "P2", "未打开发布弹窗", ""
    title = f"{TASKMARK}DT"
    e.fill_by_label("任务标题", title, ".el-dialog")
    if not e.select_by_label("试卷", None, ".el-dialog"):
        return "P2", "试卷下拉无选项", ""
    e.page.wait_for_timeout(400)
    picked = e.select_by_label("下发班级", "一年级(1)班", ".el-dialog")
    if not picked:
        return "P2", "下发班级下拉无法选中（前置缺陷，见阶段六 P0 用例）", ""
    e.page.keyboard.press("Escape")
    e.page.wait_for_timeout(300)
    start = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d 10:00:00")
    end = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d 10:00:00")
    ok_start = set_dt("开始时间", start)
    ok_end = set_dt("截止时间", end)
    e.page.locator(".el-dialog").get_by_role("button", name="确定").click()
    e.page.wait_for_timeout(2400)
    toast = e.toast_text()
    got = find_task(title)
    if got:
        api("DELETE", f"/task/tasks/{got['id']}", T["token"])
        return "P1", (f"截止早于开始仍发布成功（task={got['id']}，开始={start} 截止={end}）；已清理。"
                      f"toast={toast[:50]!r}"), \
               "任务一发布即已结束，学生看不到也答不了"
    time_hint = any(k in toast for k in ("时间", "日期", "截止", "开始"))
    if time_hint:
        return "PASS", f"被时间校验拦截：{toast[:80]!r}（日期填入={ok_start}/{ok_end}）", ""
    return "BLOCKED", (f"未创建但提示与本用例无关：{toast[:80]!r}"
                       f"（日期填入={ok_start}/{ok_end}），无法判定时间校验是否存在"), ""


def t_publish_ok():
    """正常发布一场考试给七年级(2)班（stu731 所在班），供阶段七答题。"""
    inject(e, "teacher", "/teacher/tasks", 2600)
    e.click_text("发布作业 / 考试")
    e.page.wait_for_timeout(1500)
    if not e.dialog_visible():
        return "P2", "未打开发布弹窗", ""
    e.fill_by_label("任务标题", TASKMARK, ".el-dialog")
    # 类型选「考试」
    try:
        e.page.locator(".el-dialog .el-radio-button", has_text="考试").first.click()
    except Exception:
        pass
    e.page.wait_for_timeout(400)
    if not e.select_by_label("试卷", PMARK, ".el-dialog"):
        return "P2", f"试卷下拉无法选中 {PMARK}", ""
    e.page.wait_for_timeout(800)
    pass_score = e.input_value("及格分", ".el-dialog")
    start = (datetime.now() - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
    end = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S")
    set_dt("开始时间", start)
    set_dt("截止时间", end)
    # 多选班级：teacher1 任教一年级(1)班（stu101 所在班），阶段七用它答题
    picked = e.select_by_label("下发班级", "一年级(1)班", ".el-dialog")
    if not picked:
        return "P2", "下发班级下拉无法选中", ""
    e.page.keyboard.press("Escape")
    e.page.wait_for_timeout(300)
    e.page.locator(".el-dialog").get_by_role("button", name="确定").click()
    e.page.wait_for_timeout(2800)
    pc = e.last_call("POST", "/tasks")
    got = find_task(TASKMARK)
    if got:
        return "PASS", (f"发布成功 id={got.get('id')} 类型={got.get('type')} "
                        f"班级={picked} 及格分={pass_score} 截止={got.get('end_at')} "
                        f"下发={got.get('assignment_count')}人"), ""
    return "P1", f"接口回查无此任务（POST={pc.get('status')} msg={e.call_msg('POST', '/tasks')[:90]!r} toast={e.toast_text()[:60]!r}）", ""


def t_task_search():
    inject(e, "teacher", "/teacher/tasks", 2500)
    e.search("任务标题", TASKMARK[:10])
    rows = e.row_count()
    titles = [x.inner_text().strip() for x in e.page.query_selector_all(".el-table__row td:nth-child(1)")]
    if rows and any(TASKMARK[:10] in t for t in titles):
        return "PASS", f"搜索命中 {rows} 行：{titles[:3]}", ""
    return "P1", f"搜索未命中（rows={rows}）", "任务检索失效"


def t_task_type_filter():
    inject(e, "teacher", "/teacher/tasks", 2500)
    before = e.row_count()
    picked = e.select_by_label("类型", "考试")
    e.click_text("查询")
    e.page.wait_for_timeout(1800)
    types = [x.inner_text().strip() for x in e.page.query_selector_all(".el-table__row td:nth-child(2)")]
    if types and set(types) == {"考试"}:
        return "PASS", f"选「考试」后 {before}→{len(types)} 行，类型列全为考试", ""
    return "P1", f"类型筛选未生效：{set(types)}", "任务类型筛选失效"


e.start()
try:
    e.run("试卷管理", "列表渲染", ["访问 /teacher/papers"], "渲染试卷表格", t_list)
    e.run("试卷管理", "按名称搜索", ["搜索框输入已有试卷名片段", "回车"], "列表收敛", t_search)
    e.run("试卷管理", "搜索空态", ["输入 zzz不存在的试卷9999"], "0 行 + 空态", t_search_empty)
    e.run("试卷管理", "手动组卷空表单", ["点击手动组卷", "直接点创建试卷"],
          "提示缺试卷名称/未选题", t_create_empty)
    e.run("试卷管理", "手动组卷（选题 2 道）", [
        f"试卷名称={PMARK}", "学科=数学", "年级=七年级", "勾选 2 道题", "加入所选", "创建试卷",
    ], "创建成功且题量/总分正确", t_create_ok)
    e.run("试卷管理", "删除自建试卷（一次性）", [
        "新建一次性试卷", "搜索", "点击删除", "确认",
    ], "试卷消失", t_delete_paper)
    e.run("作业考试", "发布弹窗的班级下拉可选项", [
        "打开「发布作业 / 考试」", "展开「下发班级」下拉",
    ], "下拉列出可下发的班级", t_class_dropdown)
    e.run("作业考试", "选 5 分小卷时及格分自适应", [
        "发布作业/考试", "试卷下拉选一张总分为 5 分的卷",
    ], "及格分自动收敛到 ≤5，不触发 400", t_pass_score_adapt)
    e.run("作业考试", "发布时截止时间早于开始时间", [
        "发布作业/考试", "开始=明天", "截止=昨天", "确定",
    ], "被拦截并提示时间非法", t_publish_date_inverted)
    e.run("作业考试", "发布考试给一年级(1)班", [
        "发布作业/考试", f"标题={TASKMARK}", "类型=考试", "选试卷",
        "开始=1小时前", "截止=2天后", "下发班级=一年级(1)班", "确定",
    ], "任务创建成功并生成学生下发记录", t_publish_ok)
    e.run("作业考试", "按标题搜索任务", ["搜索 UITASK 前缀"], "命中本轮任务", t_task_search)
    e.run("作业考试", "类型下拉筛选考试", ["类型选「考试」", "查询"], "列表仅剩考试", t_task_type_filter)
finally:
    e.stop()
    with open(os.path.join(HERE, "phase6.json"), "w", encoding="utf-8") as f:
        json.dump(e.rows, f, ensure_ascii=False, indent=1)
    passes = sum(1 for r in e.rows if r["verdict"] == "PASS")
    print(f"\n阶段六：{len(e.rows)} 项，通过 {passes}，问题 {len(e.rows)-passes}")
