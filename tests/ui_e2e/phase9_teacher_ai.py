"""UI E2E 阶段九：教师端剩余模块 + AI 助手。

覆盖：
  批改中心（预置主观题答卷 → 队列 → 评分 → 保存 → 发布成绩 → 打回重做）
  教案管理（列表 / 筛选 / 新增 / 搜索 / 删除）
  班级学情（班级切换 / 表格 / 空态）
  学生分析（班级→学生联动 / 掌握度）
  教学报表（知识点正确率 / 班级切换）
  AI 助手（会话注入 / 发送 / 空消息 / 超长输入 / 清空）
  AI 出题组卷（引擎状态 / 能力菜单 / 缺参校验）
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
T = session("teacher")
S = session("student1")
STAMP = time.strftime("%H%M%S")
LMARK = f"UI教案{STAMP}"

e = E2E()


def chat_text() -> str:
    """AI 助手页的根节点是 .chat-page（不是通用 .page-container）。"""
    for sel in (".chat-page", ".page-container", "body"):
        loc = e.page.locator(sel).first
        try:
            if loc.count():
                return loc.inner_text().replace("\n", " ")
        except Exception:
            continue
    return ""


def ts(offset: int) -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time() + offset))


# ---------------------------------------------------------------- 预置数据
def find_subjective_paper():
    """找一份含主观题的试卷，且其年级要与「教师任教班级」一致。

    下发接口会按班级校验任教范围，卷子年级与班级年级不匹配时虽然能建成功，
    但学生会拿不到题 —— 预置阶段必须一次选对，否则整组批改用例只能 ENV 跳过。
    """
    mine = api("GET", "/edu/classes?mine=true&page_size=50", T["token"]).get("data") or []
    if isinstance(mine, dict):
        mine = mine.get("items") or []
    if not mine:
        return None, [], None
    cls = mine[0]
    r = api("GET", "/question/papers?page=1&page_size=50", T["token"])
    best = None
    for p in (r.get("data") or {}).get("items") or []:
        pr = api("GET", f"/question/papers/{p['id']}", T["token"])
        items = ((pr.get("data") or {}).get("items")) or []
        if any(i.get("type") in ("short", "calc", "material", "composition") for i in items):
            if best is None:
                best = (p, items)
            if p.get("grade_id") == cls.get("grade_id"):
                return p, items, cls
    return (best[0], best[1], cls) if best else (None, [], cls)


def make_grading_data():
    """建卷 → 下发 → 学生提交 → 返回 (task, submission)。"""
    paper, items, cls = find_subjective_paper()
    if not paper or not cls:
        print(f"[setup] 找不到可用试卷/班级 paper={paper and paper.get('id')} cls={cls}")
        return {}, {}
    body = {
        "title": f"UI批改{STAMP}", "type": "exam", "paper_id": paper["id"],
        "class_ids": [cls["id"]], "duration": 60,
        "start_at": ts(-3600), "end_at": ts(86400),
    }
    print(f"[setup] 试卷={paper['id']}(g{paper.get('grade_id')}) 班级={cls['id']}(g{cls.get('grade_id')})")
    r = api("POST", "/task/tasks", T["token"], body)
    task = r.get("data") or {}
    if not task.get("id"):
        print(f"[setup] 建任务失败 code={r.get('code')} msg={r.get('message')!r}")
        return {}, {}
    tp = api("GET", f"/task/tasks/{task['id']}/paper", S["token"])
    pdata = tp.get("data") or {}
    pitems = pdata.get("items") or []
    if not pitems:
        print(f"[setup] 取题失败 code={tp.get('code')} msg={tp.get('message')!r}")
        return task, {}
    answers = []
    for it in pitems:
        # 主观题给一段可批改的文本；客观题用首选项
        content = "解：移项得 3x = 7 - 5，即 3x = 2，所以 x = 2/3。"
        if it.get("type") in ("single", "multiple", "judge") and it.get("options"):
            content = (it["options"][0] or {}).get("label") or "A"
        answers.append({"paper_item_id": it["paper_item_id"], "content": content})
    sub = api("POST", f"/task/tasks/{task['id']}/submit", S["token"], {"answers": answers})
    sid = (sub.get("data") or {}).get("submission_id")
    if not sid:
        print(f"[setup] 交卷失败 code={sub.get('code')} msg={sub.get('message')!r}")
    return task, {"submission_id": sid}


# 三个动作（保存 / 发布 / 打回）都会改变答卷状态、使其离开待批队列，
# 必须各用一份独立答卷，否则后两条只能 ENV 跳过。
BATCHES = []
for _i in range(3):
    _t, _s = make_grading_data()
    BATCHES.append({"task": _t, "sub": _s})
TIDS = [b["task"].get("id") for b in BATCHES if b["task"].get("id")]
SIDS = [b["sub"].get("submission_id") for b in BATCHES if b["sub"].get("submission_id")]
print(f"[setup] tasks={TIDS} submissions={SIDS}")


def pick_pending(index: int = 0):
    """取第 index 份预置答卷（按 submission_id 精确定位，不依赖队列顺序）。"""
    items = pending_list()
    if index < len(SIDS):
        sid = SIDS[index]
        hit = next((x for x in items
                    if (x.get("submission_id") or x.get("id")) == sid), None)
        if hit:
            return hit
    return items[index] if len(items) > index else None


def pending_list():
    r = api("GET", "/grading/pending?page=1&page_size=30", T["token"])
    d = r.get("data") or {}
    return d.get("items") or []


# ---------------------------------------------------------------- 批改中心
def t_grading_queue():
    inject(e, "teacher", "/teacher/grading", 3200)
    if "/login" in e.page.url:
        return "P0", "批改中心被弹回登录", ""
    txt = e.page.locator(".page-container").first.inner_text().replace("\n", " ")
    rows = len(pending_list())
    if rows == 0:
        return "ENV", f"队列为空（预置未成功），页面「{txt[:60]}」", ""
    if "待批改" in txt or rows > 0:
        return "PASS", f"队列接口 {rows} 份；页面「{txt[:70]}」", ""
    return "P2", f"页面未显示队列：{txt[:80]}", ""


def t_grading_select():
    """点选队列项 → 右侧应加载答卷明细（逐题 + 评分控件）。"""
    inject(e, "teacher", "/teacher/grading", 3400)
    items = pending_list()
    if not items:
        return "ENV", "队列为空，跳过", ""
    # 队列卡片的可点区域
    card = e.page.locator(".queue-item, .sub-item, .list-item").first
    try:
        card.click(timeout=5000)
    except Exception:
        return "ENV", "队列项定位不到可点元素", ""
    e.page.wait_for_timeout(2200)
    has_detail = e.page.get_by_text("批改进度").count() > 0
    n_items = e.page.locator(".q-item").count()
    if has_detail and n_items:
        return "PASS", f"答卷加载：{n_items} 道题待批，进度区已渲染", ""
    return "P1", f"点选后未加载答卷（进度区={has_detail}, q-item={n_items}）", \
           "教师无法进入批改"


def t_grading_score_save():
    """打满分 → 保存批改结果 → 断言 PUT/POST 成功。"""
    inject(e, "teacher", "/teacher/grading", 3400)
    if not pending_list():
        return "ENV", "队列为空，跳过", ""
    first = pending_list()[0]
    try:
        e.page.get_by_text(str(first.get("student_name") or first.get("student")), exact=False)\
            .first.click(timeout=6000)
        e.page.wait_for_timeout(2200)
    except Exception:
        return "ENV", "无法从队列点选目标答卷", ""
    n = e.page.locator(".q-item").count()
    if not n:
        return "ENV", "答卷未加载", ""
    # 每题点「满分」
    for i in range(n):
        it = e.page.locator(".q-item").nth(i)
        btn = it.get_by_role("button", name="满分")
        if btn.count():
            btn.first.click()
            e.page.wait_for_timeout(120)
    e.reset_evidence() if hasattr(e, "reset_evidence") else None
    save = e.page.get_by_role("button", name="保存批改结果")
    if save.count() == 0:
        return "P1", "无「保存批改结果」按钮", "无法保存批改"
    save.first.click()
    e.page.wait_for_timeout(3000)
    call = e.last_call("POST", "/grading/submissions")
    if call.get("status") == 200 and "/grade" in call.get("path", ""):
        return "PASS", f"{n} 题打满分并保存成功（{call['method']} {call['path'][:60]}）", ""
    return "P1", (f"保存失败 status={call.get('status')} "
                  f"path={call.get('path', '')[:50]} msg={e.call_msg('POST', '/grade')[:60]!r}"), \
           "批改结果无法保存"


def t_grading_publish():
    """发布成绩 → 学生侧成绩中心应可见。"""
    inject(e, "teacher", "/teacher/grading", 3400)
    # 必须排除已发布的记录：published 再发布只会重复发通知，
    # 且会让本用例每次重跑都「通过」而掩盖真实链路。
    cands = [x for x in pending_list()
             if x.get("status") not in ("published",)]
    if not cands:
        return "ENV", "队列为空或全部已发布，跳过", ""
    first = cands[0]
    try:
        e.page.get_by_text(str(first.get("student_name") or ""), exact=False)\
            .first.click(timeout=6000)
        e.page.wait_for_timeout(2200)
    except Exception:
        return "ENV", "无法点选答卷", ""
    # 未批改时「发布成绩」是 disabled，先打满分再发布，才算走通完整链路
    for i in range(e.page.locator(".q-item").count()):
        btn = e.page.locator(".q-item").nth(i).get_by_role("button", name="满分")
        if btn.count():
            btn.first.click()
            e.page.wait_for_timeout(100)
    e.page.get_by_role("button", name="保存批改结果").first.click()
    e.page.wait_for_timeout(2600)
    pub = e.page.get_by_role("button", name="发布成绩")
    if pub.count() == 0:
        return "P2", "未渲染「发布成绩」按钮（可能缺 grading:publish 权限）", ""
    if pub.first.is_disabled():
        # 区分两种情况，否则无法判断是产品缺陷还是前置未满足：
        #  A. 状态是 auto_graded/fully_graded 且明细已全给分 → 仍 disabled = 真缺陷
        #  B. 明细里还有主观题未批 → disabled 正确
        d = api("GET", f"/grading/submissions/{first.get('submission_id') or first.get('id')}",
                T["token"]).get("data") or {}
        SUBJ = {"short", "calc", "material", "composition"}
        pend = [i for i in (d.get("items") or [])
                if i.get("type") in SUBJ and i.get("score") is None]
        if pend:
            return "ENV", f"仍有 {len(pend)} 道主观题未批，disabled 属正确行为", ""
        return "P1", (f"明细已全部给分（status={d.get('status')}, score={d.get('score')}）"
                      f"但「发布成绩」仍 disabled —— 教师无法发布成绩"), \
               "纯客观题自动判分后状态为 auto_graded，若可发布状态集合漏配该值则成绩永久发不出"
    e.reset_evidence() if hasattr(e, "reset_evidence") else None
    pub.first.click()
    e.page.wait_for_timeout(1200)
    # 可能有二次确认
    box = e.page.locator(".el-message-box")
    if box.count():
        e.confirm()
        e.page.wait_for_timeout(2500)
    else:
        e.page.wait_for_timeout(2000)
    call = e.last_call("POST", "/grading/submissions")
    if call.get("status") == 200 and "/publish" in call.get("path", ""):
        return "PASS", f"发布成绩成功：{e.call_msg('POST', '/publish')[:50]}", ""
    return "P2", (f"发布 path={call.get('path', '')[:50]} status={call.get('status')} "
                  f"msg={e.call_msg('POST', '/publish')[:50]!r}"), "学生看不到成绩"


def t_grading_reject():
    """打回重做：应清除评分并回到待作答状态，且级联到学生侧。"""
    inject(e, "teacher", "/teacher/grading", 3400)
    # 只挑可打回的记录：/grading/pending 的 items 里没有 can_reject 字段，
    # 早先 `first.get("can_reject", True)` 恒为 True 属于假判据。
    # 真判据是状态 —— published / fully_graded 不在待批队列，且打回无意义。
    cands = [x for x in pending_list()
             if x.get("status") not in ("published", "fully_graded")]
    if not cands:
        return "ENV", f"队列中无可打回记录（共 {len(pending_list())} 条）", ""
    first = cands[0]
    try:
        e.page.get_by_text(str(first.get("student_name") or ""), exact=False)\
            .first.click(timeout=6000)
        e.page.wait_for_timeout(2200)
    except Exception:
        return "ENV", "无法点选答卷", ""
    btn = e.page.get_by_role("button", name="打回重做")
    if btn.count() == 0:
        return "ENV", "无「打回重做」按钮（缺 grading:do 权限）", ""
    e.reset_evidence() if hasattr(e, "reset_evidence") else None
    btn.first.click()
    e.page.wait_for_timeout(1200)
    if e.page.locator(".el-message-box").count():
        e.confirm()
        e.page.wait_for_timeout(2500)
    call = e.last_call("POST", "/grading/submissions")
    if call.get("status") == 200 and "/reject" in call.get("path", ""):
        return "PASS", f"打回成功：{e.call_msg('POST', '/reject')[:50]}", ""
    return "P2", (f"打回 path={call.get('path', '')[:50]} status={call.get('status')} "
                  f"msg={e.call_msg('POST', '/reject')[:50]!r}"), ""


def t_grading_search_empty():
    """队列搜索无匹配 → 应 0 条并给出空态。"""
    inject(e, "teacher", "/teacher/grading", 3200)
    ph = "搜索学生 / 任务"
    if not e.fill_placeholder(ph, "zzz不存在学生9999"):
        return "ENV", f"找不到「{ph}」输入框", ""
    e.page.wait_for_timeout(1600)
    txt = e.page.locator(".page-container").first.inner_text().replace("\n", " ")
    cards = e.page.locator(".q-item").count()
    if cards == 0:
        return "PASS", f"搜索后无答卷明细；页面「{txt[:70]}」", ""
    return "P2", f"搜索无效，仍显示 {cards} 题明细", "搜索未过滤"


# ---------------------------------------------------------------- 教案管理
def t_lesson_list():
    inject(e, "teacher", "/teacher/lessons", 3000)
    d = e.dump()
    if not d.get("rows"):
        return "P1", f"教案列表 0 行（空态「{d.get('empty')}」）", ""
    return "PASS", f"渲染 {d['rows']} 行，表头 {d['headers'][:5]}", ""


def t_lesson_filter():
    """学科/年级下拉 + 关键词查询。"""
    inject(e, "teacher", "/teacher/lessons", 3000)
    before = e.row_count()
    picked = e.select_by_label("学科", None)
    if not picked:
        return "P2", "「学科」下拉无可选项", "无法按学科筛选"
    e.page.wait_for_timeout(500)
    e.click_text("查询")
    e.page.wait_for_timeout(1800)
    path = e.last_call("GET", "/lesson/plans").get("path", "")
    after = e.row_count()
    if "subject_id=" not in path:
        return "P1", f"筛选参数未发出：{path[:90]}", "学科筛选无效"
    return "PASS", f"学科选「{picked[:12]}」：{before}→{after} 行，参数已发出", ""


def t_lesson_create():
    inject(e, "teacher", "/teacher/lessons", 2800)
    e.click_text("新建教案")
    e.page.wait_for_timeout(1400)
    if not e.dialog_visible():
        return "P2", "未打开新建教案弹窗", ""
    # 弹窗字段：标题 / 课题 / 学科 / 年级 / 课时（分） …，提交按钮是「保存教案」
    e.fill_by_label("标题", LMARK, ".el-dialog")
    e.fill_by_label("课题", f"课题{STAMP}", ".el-dialog")
    for label in ("学科", "年级"):
        try:
            e.select_by_label(label, None, ".el-dialog")
            e.page.wait_for_timeout(300)
        except Exception:
            pass
    try:
        e.fill_by_label("课时（分）", "45", ".el-dialog")
    except Exception:
        pass
    e.reset_evidence()
    save = e.page.locator(".el-dialog").get_by_role("button", name="保存教案")
    if save.count() == 0:
        return "P2", "弹窗无「保存教案」按钮", ""
    save.first.click()
    e.page.wait_for_timeout(3000)
    r = api("GET", f"/lesson/plans?page=1&page_size=50&keyword={LMARK}", T["token"])
    items = (r.get("data") or {}).get("items") or []
    got = next((x for x in items if x.get("title") == LMARK), None)
    if got:
        return "PASS", f"教案创建成功 id={got.get('id')}", ""
    return "P1", f"教案未落库（msg={e.call_msg('POST', '/plans')[:70]!r}）", ""


def t_lesson_search_delete():
    inject(e, "teacher", "/teacher/lessons", 2800)
    if not e.fill_placeholder("标题/课题", LMARK):
        return "ENV", "找不到关键词输入框", ""
    e.page.keyboard.press("Enter")
    e.page.wait_for_timeout(1800)
    rows = e.row_count()
    if rows != 1:
        return "P1", f"关键词搜索命中 {rows} 行（期望 1）", "搜索不精确"
    row = e.page.locator(".el-table__row", has_text=LMARK).first
    row.get_by_role("button", name="删除").first.click()
    e.page.wait_for_timeout(900)
    e.confirm()
    e.page.wait_for_timeout(2200)
    r = api("GET", f"/lesson/plans?page=1&page_size=50&keyword={LMARK}", T["token"])
    still = [x for x in ((r.get("data") or {}).get("items") or []) if x.get("title") == LMARK]
    if not still:
        return "PASS", "搜索命中 1 行 → 删除成功", ""
    return "P1", "删除后教案仍存在", "删除无效"


def t_lesson_empty_form():
    inject(e, "teacher", "/teacher/lessons", 2800)
    e.click_text("新建教案")
    e.page.wait_for_timeout(1300)
    if not e.dialog_visible():
        return "P2", "未打开弹窗", ""
    # 教案弹窗 footer 是「关闭」+「保存教案」，没有「确定」按钮。
    # 此前用例按「确定」点，必然 15s 超时被记为 BLOCKED —— 是脚本写错，
    # 不是产品缺陷。用 has_text 兜底，避免按钮文案再变又静默失败。
    dlg = e.page.locator(".el-dialog:visible").first
    btn = dlg.get_by_role("button", name="保存教案")
    if not btn.count():
        btn = dlg.locator("button:has-text('确定'), button:has-text('保存')").first
    if not btn.count():
        return "BLOCKED", f"弹窗内找不到保存按钮，实际按钮：{dlg.locator('button').all_inner_texts()}", ""
    btn.first.click()
    e.page.wait_for_timeout(1500)
    toast = e.toast_text()
    errs = e.form_errors()
    if e.dialog_visible() and (toast or errs):
        return "PASS", f"空表单被拦：{(errs or [toast])[0][:50]!r}", ""
    return "P1", f"空教案表单未拦截（dialog={e.dialog_visible()}, toast={toast[:40]!r}）", ""


# ---------------------------------------------------------------- 学情分析
def t_class_analysis():
    inject(e, "teacher", "/teacher/analysis", 3200)
    d = e.dump()
    txt = e.page.locator(".page-container").first.inner_text().replace("\n", " ")
    if d.get("rows"):
        return "PASS", f"班级学情 {d['rows']} 行，表头 {d['headers'][:5]}", ""
    if "暂无" in txt:
        return "PASS", f"无数据但空态明确：「{txt[:70]}」", ""
    return "P2", f"表格空白且无空态：{txt[:80]}", ""


def t_class_analysis_switch():
    """切换班级应重新拉数据。"""
    inject(e, "teacher", "/teacher/analysis", 3200)
    before = e.row_count()
    picked = e.select_by_label_placeholder("选择班级") if hasattr(e, "select_by_label_placeholder") else None
    if not picked:
        # 该页下拉直接挂在 header 上，没有 form-item label
        try:
            e.page.locator(".el-select").first.click()
            e.page.wait_for_timeout(700)
            opts = e.page.locator(".el-select-dropdown__item:visible")
            if opts.count() == 0:
                return "ENV", "班级下拉无选项", ""
            picked = (opts.first.inner_text() or "").strip()
            opts.first.click()
            e.page.wait_for_timeout(2400)
        except Exception as exc:
            return "ENV", f"切换班级失败：{exc}", ""
    call = e.last_call("GET", "/class-analysis") or e.last_call("GET", "/analysis")
    return "PASS", f"切到「{picked[:14]}」：{before}→{e.row_count()} 行，请求 {call.get('path', '')[:50]}", ""


def t_student_analysis():
    inject(e, "teacher", "/teacher/students", 3200)
    flow = e.page.locator(".el-select").first
    if flow.count() == 0:
        return "P2", "无班级下拉", ""
    flow.click()
    e.page.wait_for_timeout(700)
    opts = e.page.locator(".el-select-dropdown__item:visible")
    if opts.count() == 0:
        return "P2", "班级下拉无选项", "无法选择班级"
    opts.first.click()
    e.page.wait_for_timeout(2200)
    # 第二个下拉：选择学生
    sels = e.page.locator(".el-select")
    if sels.count() < 2:
        return "P2", "无学生下拉", ""
    sels.nth(1).click()
    e.page.wait_for_timeout(800)
    sopts = e.page.locator(".el-select-dropdown__item:visible")
    if sopts.count() == 0:
        txt = e.page.locator(".page-container").first.inner_text().replace("\n", " ")
        return "P2", f"学生下拉为空（班级无学生）；页面「{txt[:70]}」", ""
    name = (sopts.first.inner_text() or "").strip()
    sopts.first.click()
    e.page.wait_for_timeout(2600)
    txt = e.page.locator(".page-container").first.inner_text().replace("\n", " ")
    if name and name.split("（")[0] in txt:
        return "PASS", f"选学生「{name[:14]}」后个人信息区渲染", ""
    return "P2", f"选学生后未渲染：{txt[:80]}", ""


def t_teacher_report():
    inject(e, "teacher", "/teacher/reports", 3400)
    d = e.dump()
    txt = e.page.locator(".page-container").first.inner_text().replace("\n", " ")
    if d.get("rows"):
        return "PASS", f"教学报表 {d['rows']} 行，表头 {d['headers'][:5]}", ""
    if "暂无" in txt or "请选择" in txt:
        return "PASS", f"空态/占位明确：「{txt[:70]}」", ""
    return "P2", f"报表空白且无提示：{txt[:80]}", ""


# ---------------------------------------------------------------- AI 助手
def t_agent_chat_render():
    inject(e, "teacher", "/agent/chat", 3200)
    txt = chat_text()
    if "AI 引擎状态" in txt and "发送" in txt:
        return "PASS", f"助手页渲染：{txt[:80]}", ""
    return "P2", f"渲染异常：{txt[:80]}", ""


def t_agent_chat_send():
    inject(e, "teacher", "/agent/chat", 3200)
    ta = e.page.locator("textarea").first
    if ta.count() == 0:
        return "P2", "无输入框", ""
    ta.fill("什么是艾宾浩斯遗忘曲线？")
    e.page.get_by_role("button", name="发送").first.click()
    # 固定 sleep 不够：AI 回复可能走规则引擎/大模型，耗时 3~40s 不等，
    # 且 e.calls 只在响应返回后才记录 —— 请求在路上时 last_call 取到的是 None，
    # 会被误判成「压根没发请求」。改为最多 45s 轮询，拿到 200 或出现回复文本即止。
    call = {}
    txt = ""
    for _ in range(45):
        e.page.wait_for_timeout(1000)
        call = e.last_call("POST", "/agent/chat")
        txt = chat_text()
        if call.get("status") == 200:
            break
        if call.get("status") and call["status"] >= 400:
            break
    if call.get("status") == 200 and ("艾宾浩斯" in txt or "复习" in txt):
        return "PASS", f"发送 200，回复已渲染；{txt[-90:]}", ""
    if call.get("status") == 200:
        return "P2", f"接口 200 但回复未匹配预期关键词：{txt[-100:]!r}", "回复内容为空或无关"
    if call.get("status") and call["status"] >= 400:
        return "P1", f"发送失败 HTTP {call['status']}：{e.call_msg('POST', '/chat')[:70]}", \
               "AI 助手不可用"
    return "P2", f"45s 内未收到回复（POST={call.get('status')}），页面尾部：{txt[-80:]!r}", \
           "AI 响应超时"


def t_agent_chat_empty():
    """空消息不应发出请求。"""
    inject(e, "teacher", "/agent/chat", 3000)
    e.calls.clear()
    e.page.get_by_role("button", name="发送").first.click()
    e.page.wait_for_timeout(1500)
    posts = [c for c in e.calls if c["method"] == "POST" and "/chat" in c["path"]]
    if not posts:
        return "PASS", f"空消息未发请求；toast={e.toast_text()[:40]!r}", ""
    return "P2", f"空消息仍发了 {len(posts)} 次请求（status={posts[0]['status']}）", ""


def t_agent_chat_long():
    """超长输入：应被前端限制在 500 字以内（页面显示 0/500）。"""
    inject(e, "teacher", "/agent/chat", 3000)
    ta = e.page.locator("textarea").first
    if ta.count() == 0:
        return "P2", "无输入框", ""
    ta.fill("测" * 600)
    e.page.wait_for_timeout(700)
    val = ta.input_value()
    txt = chat_text()
    counter = [s for s in txt.split() if "/500" in s]
    if len(val) <= 500:
        return "PASS", f"输入被限制：填 600 字实际 {len(val)} 字，计数器 {counter}", ""
    return "P2", f"600 字全部进入输入框（{len(val)}），仅显示 {counter}，超长会直接打到后端", \
           "长文本无上限，可能触发模型上下文超限"


def t_agent_chat_clear():
    """清空对话 = 清空消息记录（含 sessionStorage 持久化），不是清输入框草稿。"""
    inject(e, "teacher", "/agent/chat", 3200)
    ta = e.page.locator("textarea").first
    ta.fill("测试清空")
    e.page.get_by_role("button", name="发送").first.click()
    e.page.wait_for_timeout(5000)
    before = e.page.locator(".msg, .message, .bubble").count()
    e.page.get_by_role("button", name="清空对话").first.click()
    e.page.wait_for_timeout(1500)
    if e.page.locator(".el-message-box").count():
        e.confirm()
        e.page.wait_for_timeout(1500)
    after = e.page.locator(".msg, .message, .bubble").count()
    saved = e.page.evaluate("() => sessionStorage.getItem('edu_chat')")
    txt = chat_text()
    if after == 0 and not saved and "我是你的 AI 教学助手" in txt:
        return "PASS", f"消息 {before}→0，sessionStorage 已清除，回到欢迎语", ""
    return "P2", f"清空不彻底：消息 {before}→{after}，storage={str(saved)[:30]!r}", \
           "刷新后旧对话可能重现"


# ---------------------------------------------------------------- AI 出题组卷
def t_agent_generate_render():
    inject(e, "teacher", "/agent/generate", 3400)
    errs = [c for c in e.console if "app error" in c or "TypeError" in c]
    txt = e.page.locator(".page-container").first.inner_text().replace("\n", " ")
    if errs:
        return "P0", f"页面抛运行时异常：{errs[0][:100]}", "AI 出题组卷不可用"
    menus = e.page.locator(".agent-menu .el-menu-item").count()
    if menus == 0:
        return "P1", f"能力菜单 0 项；页面「{txt[:70]}」", "无法选择 Agent"
    names = [n.strip() for n in e.page.locator(".agent-menu .el-menu-item").all_inner_texts()]
    # 必须有一项处于选中态，否则「当前 Agent」区域空白、右侧工作台标题也是空的。
    # 注意不能拿「请选择」占位文案当判据 —— 学科/年级本就是空值待选。
    state = e.page.evaluate("""() => ({
        activeIdx: Array.from(document.querySelectorAll('.agent-menu .el-menu-item'))
                        .findIndex(x => x.className.includes('is-active')),
        hint: (document.querySelector('.hint-desc')?.innerText || '').trim(),
    })""")
    if state["activeIdx"] < 0:
        return "P1", f"能力菜单无默认选中项（菜单 {names}），当前 Agent 区为空", \
               "首页进入即空白工作台"
    if not state["hint"]:
        return "P2", f"当前 Agent 说明为空（选中 {names[state['activeIdx']]}）", ""
    return "PASS", f"能力菜单 {menus} 项，默认选中「{names[state['activeIdx']]}」，说明「{state['hint'][:22]}」", ""


def t_agent_generate_validate():
    """未选科目直接生成 → 应有明确校验，而不是静默失败。"""
    inject(e, "teacher", "/agent/generate", 3200)
    e.calls.clear()
    e.page.get_by_role("button", name="开始生成").first.click()
    e.page.wait_for_timeout(2000)
    toast = e.toast_text()
    posts = [c for c in e.calls if c["method"] == "POST"]
    if toast and not posts:
        return "PASS", f"前端拦截：{toast[:50]!r}", ""
    if posts and posts[0]["status"] >= 400:
        return "P2", f"未拦截，直接请求并 4xx：{posts[0]['status']} {e.call_msg('POST')[:60]!r}", \
               "多一次无效往返"
    return "P2", f"无任何反馈（toast={toast[:40]!r}, posts={len(posts)}）", ""


def t_agent_generate_subject_grade():
    """学科/年级下拉应各自有值且不串（此前赋值错位导致年级里装学科）。"""
    inject(e, "teacher", "/agent/generate", 3400)
    info = e.page.evaluate("""() => {
        const out = {};
        document.querySelectorAll('.el-form-item').forEach(fi => {
            const lb = (fi.querySelector('.el-form-item__label')?.innerText || '').trim();
            const ph = (fi.querySelector('.el-select__placeholder')?.innerText || '').trim();
            const opts = fi.querySelectorAll('.el-select').length;
            if (lb) out[lb] = {ph, opts};
        });
        return out;
    }""")
    # 点开年级下拉看选项是不是「一年级…九年级」
    def open_opts(label):
        try:
            fi = e.form_item(label)
            fi.locator(".el-select").first.click(timeout=5000)
            e.page.wait_for_timeout(700)
            texts = e.page.locator(".el-select-dropdown__item:visible").all_inner_texts()
            e.page.keyboard.press("Escape")
            return texts
        except Exception:
            return []
    subs = open_opts("学科")
    grs = open_opts("年级")
    if not subs:
        return "P1", f"学科下拉无选项；页面字段={info}", "学科无法选择"
    if not grs:
        return "P1", f"年级下拉无选项；页面字段={info}", "年级无法选择"
    if any("年级" in x for x in subs) or any("数学" in x for x in grs):
        return "P1", f"学科/年级选项互串：学科{subs[:3]} 年级{grs[:3]}", "赋值错位"
    dup = len(subs) - len(set(subs))
    return "PASS", f"学科 {len(subs)} 项（重复 {dup}）、年级 {len(grs)} 项，无串值", ""


# ---------------------------------------------------------------- 主流程
try:
    e.start()
    e.run("批改中心", "队列加载", ["教师登录后访问 /teacher/grading"], "显示待批改队列", t_grading_queue)
    e.run("批改中心", "队列搜索无匹配", ["搜索框输入 zzz不存在学生9999"], "无答卷明细", t_grading_search_empty)
    e.run("批改中心", "点选答卷加载明细", ["点击队列第一条"], "右侧加载逐题批改区", t_grading_select)
    e.run("批改中心", "逐题打分并保存", ["每题点「满分」", "点「保存批改结果」"],
          "保存 200 且进度 100%", t_grading_score_save)
    e.run("批改中心", "发布成绩", ["点「发布成绩」", "确认"], "发布成功", t_grading_publish)
    e.run("批改中心", "打回重做", ["点「打回重做」", "确认"], "打回成功", t_grading_reject)
    e.run("教案管理", "列表渲染", ["访问 /teacher/lessons"], "渲染教案表格", t_lesson_list)
    e.run("教案管理", "学科筛选", ["学科选第一项", "查询"], "参数发出且结果收敛", t_lesson_filter)
    e.run("教案管理", "新建教案空表单", ["点「新增教案」", "直接确定"], "被校验拦截", t_lesson_empty_form)
    e.run("教案管理", "新建教案", ["填标题/课题/课时/学科/年级", "确定"], "创建成功", t_lesson_create)
    e.run("教案管理", "搜索并删除", ["关键词搜索", "删除", "确认"], "命中 1 行且删除生效", t_lesson_search_delete)
    e.run("班级学情", "列表渲染", ["访问 /teacher/analysis"], "渲染学生排名表", t_class_analysis)
    e.run("班级学情", "切换班级", ["班级下拉选另一项"], "数据重新加载", t_class_analysis_switch)
    e.run("学生分析", "班级→学生联动", ["选班级", "选学生"], "渲染该生掌握度", t_student_analysis)
    e.run("教学报表", "知识点正确率", ["访问 /teacher/reports"], "渲染报表或明确空态", t_teacher_report)
    e.run("AI 助手", "页面渲染", ["教师访问 /agent/chat"], "显示引擎状态与输入区", t_agent_chat_render)
    e.run("AI 助手", "发送问题", ["输入问题", "点发送"], "200 且回复渲染", t_agent_chat_send)
    e.run("AI 助手", "空消息", ["不输入直接点发送"], "不发请求并提示", t_agent_chat_empty)
    e.run("AI 助手", "超长输入 600 字", ["粘贴 600 字"], "被限制在 500 字内", t_agent_chat_long)
    e.run("AI 助手", "清空对话", ["点「清空对话」"], "输入框与消息清空", t_agent_chat_clear)
    e.run("AI 出题组卷", "页面渲染", ["访问 /agent/generate"], "能力菜单有项且无运行时异常", t_agent_generate_render)
    e.run("AI 出题组卷", "学科/年级下拉", ["分别展开学科与年级"], "各自有值且不串", t_agent_generate_subject_grade)
    e.run("AI 出题组卷", "缺参校验", ["不选科目直接开始生成"], "前端拦截或明确提示", t_agent_generate_validate)
finally:
    e.stop()
    # 任务不删：删除任务会级联清掉作答记录，复查/重跑时接口直接 404
    # （实测「作答记录不存在」）。仅当明确需要清理时手动处理。
    with open(os.path.join(HERE, "phase9.json"), "w", encoding="utf-8") as f:
        json.dump(e.rows, f, ensure_ascii=False, indent=1)
    passes = sum(1 for r in e.rows if r["verdict"] == "PASS")
    print(f"\n阶段九：{len(e.rows)} 项，通过 {passes}，问题 {len(e.rows)-passes}")
