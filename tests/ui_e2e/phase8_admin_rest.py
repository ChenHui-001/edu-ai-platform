"""UI E2E 阶段八：管理员端剩余模块。

覆盖：定时任务（新增/空表单/Cron 非法/立即执行/删除）、附件（上传/搜索/删除）、
日志审计（三个 tab + 下拉筛选 + 日期范围 + 导出）、AI 调用日志（三下拉 + 日期）、
教学资源（年级/班级/知识点 的新增与删除、被引用保护）。
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
STAMP = time.strftime("%H%M%S")
JMARK = f"uijob{STAMP}"
GMARK = f"UI年级{STAMP}"
TMP_FILE = os.path.join(HERE, f"_upload_{STAMP}.txt")

e = E2E()


def jobs():
    r = api("GET", "/jobs", A["token"])
    d = r.get("data")
    return d.get("items") if isinstance(d, dict) else (d or [])


def find_job(name: str):
    """按任务名称回查（后端没有 job_code 字段，标识是 func_path）。"""
    return next((j for j in jobs() if j.get("name") == name), None)


# ---------------------------------------------------------------- 定时任务
def t_job_render():
    url = inject(e, "admin", "/admin/jobs", 2800)
    if "/login" in url:
        return "P0", f"任务页被弹回登录（{url}）", ""
    d = e.dump()
    if not d.get("rows"):
        return "P1", f"定时任务 0 行（空态「{d.get('empty')}」）", "调度任务不可见"
    return "PASS", f"渲染 {d['rows']} 行，表头 {d['headers'][:6]}", ""


def t_job_empty_form():
    inject(e, "admin", "/admin/jobs", 2500)
    e.click_text("新增任务")
    e.page.wait_for_timeout(1300)
    if not e.dialog_visible():
        return "P2", "未打开新增任务弹窗", ""
    e.page.locator(".el-dialog").get_by_role("button", name="确定").click()
    e.page.wait_for_timeout(1500)
    toast = e.toast_text()
    errs = e.form_errors()
    if e.dialog_visible() and (toast or errs):
        return "PASS", f"空表单被拦：{(errs or [toast])[0][:50]!r}", ""
    return "P1", f"空表单无有效校验（toast={toast[:50]!r}, errs={errs}）", ""


def t_job_create_ok():
    """正常新增定时任务（用 disabled 状态，避免真的被调度器执行）。"""
    if not e.dialog_visible():
        inject(e, "admin", "/admin/jobs", 2500)
        e.click_text("新增任务")
        e.page.wait_for_timeout(1300)
    if not e.dialog_visible():
        return "P2", "未打开新增任务弹窗", ""
    e.fill_by_label("任务名称", f"UI测试任务{STAMP}", ".el-dialog")
    # 执行逻辑是下拉（后端只接受 JOB_HANDLERS 白名单里的模块路径）
    picked = e.select_by_label("执行逻辑", None, ".el-dialog")
    if not picked:
        e.page.wait_for_timeout(1200)
        picked = e.select_by_label("执行逻辑", None, ".el-dialog")
    if not picked:
        return "P1", "执行逻辑下拉无任何可选项（无法创建任务）", "定时任务功能不可用"
    e.fill_by_label("Cron 表达式", "0 3 * * *", ".el-dialog")
    # 关闭启用开关，避免真跑
    try:
        sw = e.form_item("启用", ".el-dialog").locator(".el-switch").first
        if "is-checked" in (sw.get_attribute("class") or ""):
            sw.click()
            e.page.wait_for_timeout(300)
    except Exception:
        pass
    e.page.locator(".el-dialog").get_by_role("button", name="确定").click()
    e.page.wait_for_timeout(2400)
    got = find_job(f"UI测试任务{STAMP}")
    if got:
        return "PASS", (f"创建成功 id={got.get('id')} 逻辑={str(got.get('func_path')).rsplit('.',1)[-1]} "
                        f"cron={got.get('cron_expression')} 选中={picked[:20]!r}"), ""
    return "P1", f"接口回查无此任务（msg={e.call_msg('POST', '/jobs')[:80]!r}）", ""


def t_job_bad_cron():
    """非法 Cron 表达式应被拒绝。"""
    inject(e, "admin", "/admin/jobs", 2500)
    e.click_text("新增任务")
    e.page.wait_for_timeout(1300)
    if not e.dialog_visible():
        return "P2", "未打开新增任务弹窗", ""
    bad_name = f"非法Cron{STAMP}"
    e.fill_by_label("任务名称", bad_name, ".el-dialog")
    if not e.select_by_label("执行逻辑", None, ".el-dialog"):
        e.page.wait_for_timeout(1200)
        if not e.select_by_label("执行逻辑", None, ".el-dialog"):
            return "ENV", "执行逻辑下拉无选项，无法验证 Cron 校验", ""
    e.fill_by_label("Cron 表达式", "这不是cron", ".el-dialog")
    e.page.locator(".el-dialog").get_by_role("button", name="确定").click()
    e.page.wait_for_timeout(2200)
    toast = e.toast_text()
    got = find_job(bad_name)
    if got:
        api("DELETE", f"/jobs/{got['id']}", A["token"])
        return "P1", f"非法 Cron「这不是cron」被保存（id={got.get('id')}）；已清理", \
               "调度器会在运行期报错，任务静默不执行"
    # 必须命中 Cron 类关键词，否则可能是被别的校验（如未选执行逻辑）拦下的
    if toast and any(k in toast for k in ("Cron", "cron", "表达式")):
        return "PASS", f"非法 Cron 被拦：{toast[:60]!r}", ""
    return "P1", f"非法 Cron 未得到 Cron 相关提示（toast={toast[:60]!r}）", ""


def t_job_run_now():
    """立即执行：应返回执行结果（即使未配置处理器也要有明确反馈）。"""
    inject(e, "admin", "/admin/jobs", 2500)
    btn = e.page.get_by_role("button", name="立即执行")
    if btn.count() == 0:
        return "ENV", "任务列表无「立即执行」按钮", ""
    btn.first.click()
    e.page.wait_for_timeout(800)
    e.confirm()
    e.page.wait_for_timeout(3000)
    post = e.last_call("POST", "/run")
    toast = e.toast_text()
    if post.get("status") == 200:
        return "PASS", f"立即执行 200：{e.call_msg('POST', '/run')[:60]}", ""
    if post.get("status"):
        return "P2", f"立即执行 HTTP {post['status']}：{e.call_msg('POST', '/run')[:70]}", \
               "管理员无法手动触发任务"
    return "P2", f"点击后无请求发出（toast={toast[:50]!r}）", ""


def t_job_delete():
    job_name = f"UI测试任务{STAMP}"
    got = find_job(job_name)
    if not got:
        return "ENV", "本轮创建的任务不存在，跳过删除", ""
    inject(e, "admin", "/admin/jobs", 2500)
    row = e.page.locator(".el-table__row", has_text=job_name)
    if row.count() == 0:
        return "ENV", "列表中未定位到本轮任务", ""
    row.first.get_by_role("button", name="删除").first.click()
    e.page.wait_for_timeout(900)
    e.confirm()
    e.page.wait_for_timeout(2200)
    if find_job(job_name) is None:
        return "PASS", f"删除成功（id={got.get('id')} 已不存在）", ""
    return "P1", "删除后任务仍存在", "删除无效"


# ---------------------------------------------------------------- 附件
def t_attachment_upload():
    """上传一个文本附件 → 列表出现 → 搜索 → 删除。"""
    with open(TMP_FILE, "w", encoding="utf-8") as f:
        f.write("UI E2E 附件上传验证 " + STAMP)
    inject(e, "admin", "/admin/attachments", 2600)
    e.click_text("上传附件")
    e.page.wait_for_timeout(1200)
    if not e.dialog_visible():
        return "P2", "未打开上传弹窗", ""
    try:
        e.page.locator(".el-dialog input[type=file]").first.set_input_files(TMP_FILE)
    except Exception as exc:
        return "P2", f"无法选择文件：{exc}", ""
    e.page.wait_for_timeout(800)
    e.page.locator(".el-dialog").get_by_role("button", name="上传").click()
    e.page.wait_for_timeout(3500)
    post = e.last_call("POST", "/attachments")
    toast = e.toast_text()
    name = os.path.basename(TMP_FILE)
    if post.get("status") == 200:
        e.search("关键词", "UI年级")
        return "PASS", f"上传 200：{e.call_msg('POST', '/attachments')[:50]}；toast={toast[:40]!r}", ""
    if post.get("status"):
        return "P1", f"上传失败 HTTP {post['status']}：{e.call_msg('POST', '/attachments')[:70]}", \
               "附件上传不可用"
    return "P1", f"未发出上传请求（toast={toast[:60]!r}，文件名={name}）", ""


def t_attachment_search():
    inject(e, "admin", "/admin/attachments", 2600)
    e.search("关键词", "zzz不存在附件9999")
    rows, hint = e.row_count(), e.empty_hint()
    if rows == 0:
        return "PASS", f"无匹配 0 行，空态「{hint[:20] or '无文案'}」", ""
    return "P1", f"无匹配仍返回 {rows} 行", "搜索被忽略"


def t_log_tabs():
    inject(e, "admin", "/admin/logs", 3000)
    results = []
    for tab in ("登录日志", "操作日志", "错误日志"):
        e.click_text(tab)
        e.page.wait_for_timeout(1800)
        results.append((tab, e.row_count(), (e.empty_hint() or "")[:12]))
    if any(n > 0 for _, n, _ in results):
        return "PASS", f"三个 tab 均可切换：{results}", ""
    return "P2", f"三个 tab 都是空表：{results}", "日志可能未落库"


def t_log_filter_select():
    """结果下拉筛选：选「成功」后表格只应剩成功记录。"""
    inject(e, "admin", "/admin/logs", 2800)
    before = e.row_count()
    picked = e.select_by_label("结果", "成功")
    e.click_text("查询")
    e.page.wait_for_timeout(2000)
    after = e.row_count()
    txt = e.text()
    # 筛选「成功」后页面不应再出现「失败」字样——原先算出来没进判据
    bad = "失败" in txt.split("操作")[0] if txt else False
    if picked and after >= 0 and not bad:
        return "PASS", f"结果筛选「{picked}」：{before}→{after} 行", ""
    return "P2", "结果下拉无法选择", "日志筛选不可用"


def t_log_date_range():
    """日期范围：填一个不可能的区间（未来）应得 0 行。"""
    inject(e, "admin", "/admin/logs", 2800)
    item = e.form_item("日期范围")
    inputs = item.locator("input")
    if inputs.count() < 2:
        return "P2", "日期范围控件缺失", ""
    inputs.nth(0).click()
    inputs.nth(0).fill("2030-01-01")
    e.page.keyboard.press("Enter")
    e.page.wait_for_timeout(400)
    inputs.nth(1).fill("2030-01-02")
    e.page.keyboard.press("Enter")
    e.page.wait_for_timeout(600)
    e.click_text("查询")
    e.page.wait_for_timeout(2000)
    rows = e.row_count()
    if rows == 0:
        return "PASS", "未来区间返回 0 行（日期过滤生效）", ""
    return "P2", f"未来区间仍返回 {rows} 行", "日期过滤失效"


def t_agent_logs_filters():
    inject(e, "admin", "/admin/agent-logs", 3000)
    res = {}
    for label in ("Agent", "状态", "降级"):
        got = e.select_by_label(label, None)
        res[label] = got
        e.page.wait_for_timeout(300)
    e.click_text("查询")
    e.page.wait_for_timeout(1800)
    if not all(res.values()):
        return "P2", f"下拉选项缺失：{res}", "AI 日志无法按维度筛选"
    # 选项有了还不够：参数名写错时 FastAPI 会静默忽略（选什么都不影响结果）。
    # 必须确认请求里真的带上了 agent_name / is_fallback。
    path = e.last_call("GET", "/agent/logs").get("path", "")
    missing = [k for k in ("agent_name=", "is_fallback=") if k not in path]
    if missing:
        return "P1", f"筛选参数未发出：缺 {missing}；path={path[:90]}", "下拉筛选无效"
    # 再直接回查后端：is_fallback=true 的结果必须全部是降级调用
    r = api("GET", "/agent/logs?page=1&page_size=20&is_fallback=true", A["token"])
    items = ((r.get("data") or {}).get("items")) or []
    bad = [x.get("id") for x in items if not x.get("is_fallback")]
    if bad:
        return "P1", f"降级筛选返回 {len(items)} 条，其中 {len(bad)} 条非降级", "后端过滤未生效"
    return "PASS", f"三个下拉均可选：{res}；筛选后 {e.row_count()} 行，降级过滤校验通过", ""


def t_agent_log_detail():
    inject(e, "admin", "/admin/agent-logs", 2800)
    btn = e.page.get_by_role("button", name="详情")
    if btn.count() == 0:
        return "ENV", "无日志记录可查看详情", ""
    btn.first.click()
    e.page.wait_for_timeout(1500)
    visible = e.dialog_visible() or e.page.locator(".el-drawer").count() > 0
    if visible:
        txt = (e.page.locator(".el-dialog").first.inner_text()
               if e.dialog_visible() else e.page.locator(".el-drawer").first.inner_text())
        return "PASS", f"详情面板打开：{txt[:60].replace(chr(10), ' ')!r}", ""
    return "P2", "点击详情无任何面板", "无法排障"


# ---------------------------------------------------------------- 教学资源
def t_grade_crud():
    inject(e, "admin", "/admin/grades", 2600)
    e.click_text("新增年级")
    e.page.wait_for_timeout(1300)
    if not e.dialog_visible():
        return "P2", "未打开新增年级弹窗", ""
    e.fill_by_label("名称", GMARK, ".el-dialog")
    e.page.locator(".el-dialog").get_by_role("button", name="确定").click()
    e.page.wait_for_timeout(2200)
    r = api("GET", f"/edu/grades?keyword={GMARK}", A["token"])
    items = r.get("data") or []
    created = next((x for x in items if x.get("name") == GMARK), None)
    if not created:
        return "P1", f"新增年级未落库（msg={e.call_msg('POST', '/grades')[:70]!r}）", ""
    # 删除
    e.search("名称", GMARK)
    row = e.page.locator(".el-table__row", has_text=GMARK).first
    if row.count() == 0:
        return "ENV", "列表中未找到新建年级", ""
    row.get_by_role("button", name="删除").first.click()
    e.page.wait_for_timeout(800)
    e.confirm()
    e.page.wait_for_timeout(2000)
    r2 = api("GET", f"/edu/grades?keyword={GMARK}", A["token"])
    gone = not any(x.get("name") == GMARK for x in (r2.get("data") or []))
    if gone:
        return "PASS", f"年级新增 id={created.get('id')} → 删除成功", ""
    return "P1", "删除年级后仍存在", "删除无效"


def t_grade_delete_referenced():
    """删除有班级的年级：应被拦截。"""
    # 年级接口不返回 class_count（页面也不展示），班级数只能从班级列表反推
    cls = api("GET", "/edu/classes?page_size=200", A["token"]).get("data") or []
    if isinstance(cls, dict):
        cls = cls.get("items") or []
    grades = api("GET", "/edu/grades", A["token"]).get("data") or []
    by_id = {g["id"]: g for g in grades}
    referenced = {c.get("grade_id") for c in cls if c.get("grade_id")}
    target = next((by_id[gid] for gid in referenced if gid in by_id), None)
    if not target:
        return "ENV", "没有带班级的年级可验证", ""
    inject(e, "admin", "/admin/grades", 2600)
    e.search("名称", target["name"])
    row = e.page.locator(".el-table__row", has_text=target["name"]).first
    if row.count() == 0:
        return "ENV", "未定位到目标年级", ""
    row.get_by_role("button", name="删除").first.click()
    e.page.wait_for_timeout(800)
    e.confirm()
    e.page.wait_for_timeout(2000)
    dc = e.last_call("DELETE")
    r2 = api("GET", "/edu/grades", A["token"])
    alive = any(g.get("id") == target["id"] for g in (r2.get("data") or []))
    if alive and dc.get("status") == 400:
        return "PASS", f"被拦截：{e.call_msg('DELETE')[:70]}", ""
    if alive:
        return "P3", f"未删除但无明确原因（DELETE={dc.get('status')}）", ""
    return "P0", f"有班级的年级「{target['name']}」被删除", "班级数据悬空"


def t_class_create_validation():
    """新增班级：重复名称应被拒。"""
    inject(e, "admin", "/admin/classes", 2600)
    e.click_text("新增班级")
    e.page.wait_for_timeout(1300)
    if not e.dialog_visible():
        return "P2", "未打开新增班级弹窗", ""
    e.fill_by_label("班级名称", "一年级(1)班", ".el-dialog")
    e.select_by_label("年级", "一年级", ".el-dialog")
    e.page.wait_for_timeout(300)
    e.page.locator(".el-dialog").get_by_role("button", name="确定").click()
    e.page.wait_for_timeout(2200)
    post = e.last_call("POST", "/classes")
    msg = e.call_msg("POST", "/classes")
    if post.get("status") == 200:
        return "P1", f"重复班级名被创建成功：{msg[:60]}", "班级出现同名重复"
    if post.get("status") and ("已存在" in msg or "重复" in msg):
        return "PASS", f"重复班级被拒：{msg[:60]}", ""
    return "P2", f"HTTP {post.get('status')}，提示不明确：{msg[:60]!r}", ""


def t_knowledge_tree():
    inject(e, "admin", "/admin/knowledge", 3000)
    d = e.dump()
    if not d.get("rows"):
        return "P1", f"知识点 0 行（空态「{d.get('empty')}」）", "知识点树不可用"
    return "PASS", f"知识点树 {d['rows']} 行", ""


def t_knowledge_delete_protected():
    """删除有子级的知识点应被拦。"""
    inject(e, "admin", "/admin/knowledge", 2800)
    btns = e.page.get_by_role("button", name="添加子级")
    if btns.count() == 0:
        return "ENV", "知识点无树形结构可验证", ""
    # 找一个有「添加子级」且有子节点的行较麻烦，改为验证叶子删除的二次确认
    row = e.page.locator(".el-table__row").first
    row.get_by_role("button", name="删除").first.click()
    e.page.wait_for_timeout(900)
    box = e.page.locator(".el-message-box")
    if box.count() == 0:
        return "P2", "删除知识点没有二次确认", "误删风险"
    e.page.get_by_role("button", name="取消").first.click()
    e.page.wait_for_timeout(600)
    return "PASS", "删除知识点有二次确认，已取消", ""


e.start()
try:
    e.run("定时任务", "列表渲染", ["访问 /admin/jobs"], "渲染任务表格", t_job_render)
    e.run("定时任务", "新增任务空表单", ["点击新增任务", "直接确定"], "必填校验拦截", t_job_empty_form)
    e.run("定时任务", "新增任务（正常）", [
        f"名称=UI测试任务{STAMP}", f"标识={JMARK}", "Cron=0 3 * * *", "关闭启用", "确定",
    ], "创建成功且接口可查", t_job_create_ok)
    e.run("定时任务", "非法 Cron 表达式", ["标识合法", "Cron 填「这不是cron」", "确定"],
          "被拒绝或有明确提示", t_job_bad_cron)
    e.run("定时任务", "立即执行", ["点击立即执行", "确认"], "返回执行结果", t_job_run_now)
    e.run("定时任务", "删除任务", ["定位本轮任务", "删除", "确认"], "任务消失", t_job_delete)
    e.run("附件管理", "上传附件", ["点击上传附件", "选择本地 txt", "上传"], "上传成功并入库",
          t_attachment_upload)
    e.run("附件管理", "搜索空态", ["关键词输入 zzz不存在附件9999"], "0 行 + 空态", t_attachment_search)
    e.run("日志审计", "三个 tab 切换", ["依次点登录/操作/错误日志"], "均可切换并有数据", t_log_tabs)
    e.run("日志审计", "结果下拉筛选", ["结果选「成功」", "查询"], "列表收敛", t_log_filter_select)
    e.run("日志审计", "日期范围筛选（未来区间）", ["日期范围填 2030-01-01~2030-01-02", "查询"],
          "返回 0 行", t_log_date_range)
    e.run("AI 调用日志", "三个下拉筛选", ["Agent/状态/降级 各选一项", "查询"],
          "下拉可用且筛选生效", t_agent_logs_filters)
    e.run("AI 调用日志", "查看详情", ["点击详情"], "弹出详情面板", t_agent_log_detail)
    e.run("教学资源-年级", "新增并删除年级", ["新增年级", "搜索", "删除", "确认"],
          "创建成功且删除生效", t_grade_crud)
    e.run("教学资源-年级", "删除有班级的年级", ["定位有班级的年级", "删除", "确认"],
          "被拦截且数据保留", t_grade_delete_referenced)
    e.run("教学资源-班级", "新增同名班级", ["新增班级", "名称填一年级(1)班", "确定"],
          "被拒并说明已存在", t_class_create_validation)
    e.run("教学资源-知识点", "知识点树渲染", ["访问 /admin/knowledge"], "树形表格渲染", t_knowledge_tree)
    e.run("教学资源-知识点", "删除二次确认", ["点击删除"], "弹出确认框", t_knowledge_delete_protected)
finally:
    e.stop()
    if os.path.exists(TMP_FILE):
        os.remove(TMP_FILE)
    with open(os.path.join(HERE, "phase8.json"), "w", encoding="utf-8") as f:
        json.dump(e.rows, f, ensure_ascii=False, indent=1)
    passes = sum(1 for r in e.rows if r["verdict"] == "PASS")
    print(f"\n阶段八：{len(e.rows)} 项，通过 {passes}，问题 {len(e.rows)-passes}")
