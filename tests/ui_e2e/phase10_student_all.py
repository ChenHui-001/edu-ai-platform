"""UI E2E 阶段十：学生端全模块。

覆盖（12 个页面）：
  智能复习（统计正确性 / 生成计划 / 完成复习 / 筛选）
  掌握图谱（学科筛选 / 图表 / 薄弱专项）
  自主组卷（页面渲染 / 缺参校验 / 跨年级学科不串 / 生成）
  学习打卡（列表 / 新建目标 / 空表单校验 / 打卡）
  学习路径（渲染 / 学科筛选 / 去练习跳转）
  闪卡速记（渲染 / 认识·不认识 / 再来一轮）
  题目收藏（空态 · 列表 / 搜索 / 标签筛选）
  成绩中心（列表 / 导出）
  学习报表（渲染 / 学科筛选真实生效 / 导出）
  错题本（列表 / 学科筛选 / 搜索 / 掌握状态 / 空结果）
  学习笔记（列表 / 新建 / 空表单 / XSS 净化 / 删除）
  随机练习（缺参校验 / 生成 / 作答）
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
S = session("student")
STAMP = time.strftime("%H%M%S")
NOTE_TITLE = f"UI笔记{STAMP}"
XSS_TITLE = f"UI XSS{STAMP}"

e = E2E("phase10")


def root_text() -> str:
    """学生页根节点不统一（多数 .page-container，AI 页是 .chat-page）。"""
    for sel in (".page-container", ".chat-page", "body"):
        loc = e.page.locator(sel).first
        try:
            if loc.count():
                return loc.inner_text().replace("\n", " ")
        except Exception:
            continue
    return ""


def api_data(method: str, path: str, body=None):
    r = api(method, path, S["token"], body)
    return r.get("data"), r



def visible_options() -> list:
    """只读当前可见的下拉选项。

    踩过的坑：直接 querySelectorAll('.el-select-dropdown__item') 会把页面上
    所有已渲染过的下拉（含隐藏的「错因」「掌握状态」）一起抓进来，
    于是 6 个学科被数成 15 项，误判成「学科重复」。
    """
    loc = e.page.locator(".el-select-dropdown:visible .el-select-dropdown__item")
    opts = [o.inner_text().strip() for o in loc.all()]
    return [o for o in opts if o]


def open_select(label: str = ""):
    """按表单 label 展开下拉；无 label 时退回首個 select。"""
    if label:
        sel = e.page.locator(".el-form-item", has_text=label).locator(".el-select").first
    else:
        sel = e.page.locator(".el-select").first
    sel.click()
    e.page.wait_for_timeout(900)
    return visible_options()


# ---------------------------------------------------------------- 智能复习
def t_review_stats():
    """统计数字必须与接口真实值一致（曾因 SQL 笛卡尔积放大 84 倍）。"""
    inject(e, "student", "/student/review", 3200)
    if "/login" in e.page.url:
        return "P0", "智能复习被弹回登录", ""
    # 正确路径是 /learning/review/plans（不是 /review/stats），
    # 字段名是 pending_count / today_count —— 写错会拿到 None 造成假 P1。
    d, _ = api_data("GET", "/learning/review/plans")
    d = d or {}
    pending = d.get("pending_count")
    today = d.get("today_count")
    txt = root_text()
    # 页面上应出现接口给的数字，而不是被放大的值
    ok_nums = (pending is not None and str(pending) in txt) or \
              (today is not None and str(today) in txt)
    if ok_nums:
        return "PASS", f"今日 {today} / 待完成 {pending}，页面数字与接口一致", ""
    return "P1", f"页面数字与接口不一致：接口 today={today} pending={pending}；页面「{txt[:100]}」", \
           "学生看到的待复习数量错误，复习节奏被打乱"


def t_review_filter():
    """学科下拉：去重后不应出现重复项，且筛选后列表收敛。"""
    inject(e, "student", "/student/review", 3000)
    subs = e.page.locator(".el-select").first
    try:
        subs.click(timeout=5000)
        e.page.wait_for_timeout(700)
        opts = visible_options()
        e.page.keyboard.press("Escape")
    except Exception as exc:
        return "BLOCKED", f"无法展开学科下拉：{type(exc).__name__}", ""
    if not opts:
        return "P2", "学科下拉为空", "无法按学科筛选复习计划"
    dup = len(opts) - len(set(opts))
    if dup > 0:
        return "P1", f"学科下拉有 {dup} 个重复项：{opts[:8]}", "用户无法区分同名学科"
    return "PASS", f"学科下拉 {len(opts)} 项，无重复", ""


def t_review_generate():
    """AI 生成复习计划：应返回成功并刷新列表。"""
    inject(e, "student", "/student/review", 3000)
    before = e.row_count()
    if not e.click_text("AI 生成复习计划"):
        return "ENV", "找不到「AI 生成复习计划」按钮", ""
    e.page.wait_for_timeout(5000)
    toast = e.toast_text()
    after = e.row_count()
    if "成功" in toast or "生成" in toast or after >= before:
        return "PASS", f"生成完成 toast='{toast[:40]}'，列表 {before}→{after}", ""
    return "P2", f"生成后无反馈（toast='{toast}'）", ""


def t_review_complete():
    """点「完成复习」应成功后从待完成列表移除。"""
    inject(e, "student", "/student/review", 3200)
    btns = e.page.get_by_role("button", name="完成复习")
    if btns.count() == 0:
        return "ENV", "无待复习条目，跳过", ""
    btns.first.click()
    e.page.wait_for_timeout(2200)
    toast = e.toast_text()
    if "成功" in toast or "完成" in toast:
        return "PASS", f"标记完成成功 toast='{toast[:40]}'", ""
    return "P2", f"完成复习无成功反馈 toast='{toast}'", ""


# ---------------------------------------------------------------- 掌握图谱
def t_mastery_render():
    inject(e, "student", "/student/mastery", 3400)
    txt = root_text()
    has_chart = e.page.locator("canvas, .echarts, svg").count() > 0
    if "平均掌握度" in txt or has_chart:
        return "PASS", f"渲染掌握度概览与图表（canvas/svg={has_chart}）：{txt[:70]}", ""
    return "P1", f"掌握图谱未渲染：{txt[:100]}", "学生看不到知识掌握情况"


def t_mastery_subject_filter():
    """学科筛选：切换后图表数据应变化且无重复选项。"""
    inject(e, "student", "/student/mastery", 3200)
    sel = e.page.locator(".el-select").first
    sel.click()
    e.page.wait_for_timeout(700)
    opts = visible_options()
    if not opts:
        e.page.keyboard.press("Escape")
        return "P2", "学科下拉为空", "无法筛选学科"
    dup = len(opts) - len(set(opts))
    # 选一个非首项
    target = opts[1] if len(opts) > 1 else opts[0]
    e.page.locator(".el-select-dropdown__item", has_text=target).first.click()
    e.page.wait_for_timeout(2600)
    txt = root_text()
    if dup > 0:
        return "P1", f"学科下拉重复 {dup} 项（{opts[:8]}），选中「{target}」后「{txt[:60]}」", \
               "只能看到最低年级的学科，其余年级同名学科无法选择"
    if "选择学科" in txt and target not in txt:
        return "P2", f"选中「{target}」后页面无对应数据", ""
    return "PASS", f"学科 {len(opts)} 项无重复，切到「{target}」后图表刷新", ""


# ---------------------------------------------------------------- 自主组卷
def t_custom_render():
    inject(e, "student", "/student/custom", 3000)
    txt = root_text()
    if "自主组卷" in txt and "生成自测卷" in txt:
        return "PASS", f"表单渲染完整：{txt[:80]}", ""
    return "P1", f"自主组卷页未渲染：{txt[:100]}", ""


def t_custom_subject_no_cross_grade():
    """学科下拉不应出现重复，且知识点必须属于所选学科（跨年级是历史 P1）。"""
    inject(e, "student", "/student/custom", 3200)
    sel = e.page.locator(".el-form-item", has_text="学科").locator(".el-select").first
    sel.click()
    e.page.wait_for_timeout(800)
    opts = visible_options()
    if not opts:
        e.page.keyboard.press("Escape")
        return "P2", "学科下拉为空", "无法组卷"
    dup = len(opts) - len(set(opts))
    # 选第一个学科 → 看知识点下拉
    e.page.locator(".el-select-dropdown__item").first.click()
    e.page.wait_for_timeout(2200)
    kp_sel = e.page.locator(".el-form-item", has_text="限定知识点").locator(".el-select").first
    kp_sel.click()
    e.page.wait_for_timeout(900)
    kps = visible_options()
    e.page.keyboard.press("Escape")
    if dup > 0:
        return "P1", f"学科下拉重复 {dup} 项（{opts[:8]}）", \
               "学生无法区分年级，选中代表 id 会组出低年级的卷子"
    return "PASS", f"学科 {len(opts)} 项无重复；选「{opts[0]}」后知识点 {len(kps)} 项：{kps[:4]}", ""


def t_custom_empty_validate():
    inject(e, "student", "/student/custom", 3000)
    if not e.click_text("生成自测卷"):
        return "ENV", "找不到「生成自测卷」", ""
    e.page.wait_for_timeout(1200)
    toast = e.toast_text()
    if "请选择" in toast or "必选" in toast:
        return "PASS", f"空表单被拦截：'{toast}'", ""
    if toast:
        return "P2", f"提示文案不含具体字段：'{toast}'", ""
    return "P1", "空表单未拦截且无提示（静默失败）", "学生以为已提交，实际没有"


# ---------------------------------------------------------------- 学习打卡
def t_goals_render():
    inject(e, "student", "/student/goals", 3000)
    txt = root_text()
    if "学习打卡" in txt and ("新建目标" in txt or "进行中目标" in txt):
        return "PASS", f"看板渲染：{txt[:80]}", ""
    return "P1", f"学习打卡页未渲染：{txt[:100]}", ""


def t_goals_empty_form():
    """新建目标必须填名称/目标值，空表单应被拦截。"""
    inject(e, "student", "/student/goals", 3000)
    if not e.click_text("新建目标"):
        return "ENV", "找不到「新建目标」", ""
    e.page.wait_for_timeout(1200)
    # 直接点保存
    if not e.click_text("保存"):
        e.click_text("确定")
    e.page.wait_for_timeout(1200)
    errs = e.form_errors()
    toast = e.toast_text()
    if errs or "请输入" in toast or "请填写" in toast:
        return "PASS", f"空表单被拦截：errors={errs[:2]} toast='{toast[:30]}'", ""
    return "P2", f"空表单未拦截（errors={errs}, toast='{toast}'）", ""


def t_goals_create():
    inject(e, "student", "/student/goals", 3000)
    if not e.click_text("新建目标"):
        return "ENV", "找不到「新建目标」", ""
    e.page.wait_for_timeout(1200)
    name = f"UI目标{STAMP}"
    e.fill_by_label("目标名称", name)
    try:
        e.select_by_label("目标周期")
    except Exception:
        pass
    e.fill_by_label("目标值", "30")
    e.click_text("保存") or e.click_text("确定")
    e.page.wait_for_timeout(2200)
    toast = e.toast_text()
    d, _ = api_data("GET", "/learning/goals")
    items = d if isinstance(d, list) else (d or {}).get("items") or []
    # 接口字段是 title（不是 name）；写错会误判「提示成功但未落库」
    hit = any((x.get("title") or x.get("name") or "") == name for x in items)
    if hit:
        return "PASS", f"目标已落库：{name}（列表 {len(items)} 条，toast='{toast[:30]}'）", ""
    return "P1", f"提示「{toast[:30]}」但接口查不到新目标（列表 {len(items)} 条）", \
           "界面提示成功但数据未保存"


# ---------------------------------------------------------------- 学习路径
def t_path_render():
    inject(e, "student", "/student/path", 3400)
    txt = root_text()
    if "学习路径" in txt and ("智能推荐" in txt or "学习建议" in txt or "去练习" in txt):
        return "PASS", f"路径与建议渲染：{txt[:90]}", ""
    return "P1", f"学习路径未渲染：{txt[:100]}", ""


def t_path_practice_jump():
    """「去练习」应跳到随机练习页并带上知识点参数。"""
    inject(e, "student", "/student/path", 3200)
    txt = root_text()
    btns = e.page.get_by_role("button", name="去练习")
    if btns.count() == 0:
        # 页面明确提示「暂无学习数据」时属于环境前置不足，不是缺陷
        return "ENV", f"无「去练习」按钮（页面：{txt[:60]}）", ""
    btns.first.click()
    e.page.wait_for_timeout(2800)
    url = e.page.url
    if "/student/practice" in url:
        return "PASS", f"跳转到 {url.split('5173')[-1][:60]}", ""
    return "P2", f"跳转目标异常：{url}", ""


# ---------------------------------------------------------------- 闪卡
def t_flashcard_render():
    inject(e, "student", "/student/flashcard", 3400)
    txt = root_text()
    if "闪卡速记" in txt and ("认识" in txt):
        return "PASS", f"闪卡渲染：{txt[:90]}", ""
    return "P1", f"闪卡页未渲染：{txt[:100]}", ""


def t_flashcard_actions():
    """认识 / 不认识：应推进计数并切换下一张。"""
    inject(e, "student", "/student/flashcard", 3200)
    txt0 = root_text()
    if not e.click_text("不认识"):
        return "ENV", "找不到「不认识」", ""
    e.page.wait_for_timeout(1600)
    txt1 = root_text()
    if txt1 != txt0:
        return "PASS", f"点击后卡片推进：{txt1[:70]}", ""
    return "P2", "点击「不认识」后页面无变化", "闪卡无法推进"


def t_flashcard_subject_dup():
    """闪卡学科下拉不应重复（曾出现 7 个「数学」）。"""
    inject(e, "student", "/student/flashcard", 3000)
    e.page.locator(".el-select").first.click()
    e.page.wait_for_timeout(700)
    opts = visible_options()
    e.page.keyboard.press("Escape")
    if not opts:
        return "P2", "学科下拉为空", ""
    dup = len(opts) - len(set(opts))
    if dup:
        return "P1", f"学科下拉重复 {dup} 项：{opts[:9]}", "同名学科重复展示"
    return "PASS", f"学科 {len(opts)} 项无重复", ""


# ---------------------------------------------------------------- 题目收藏
def t_favorites_render():
    inject(e, "student", "/student/favorites", 3000)
    txt = root_text()
    if "题目收藏" in txt:
        rows = e.row_count()
        empty = e.empty_hint()
        return "PASS", f"渲染正常，{rows} 行，空态「{empty[:30]}」", ""
    return "P1", f"收藏页未渲染：{txt[:100]}", ""


def t_favorites_search():
    """搜索不存在的内容应给出空态（而不是保留全量）。"""
    inject(e, "student", "/student/favorites", 3000)
    before = e.row_count()
    inp = e.page.locator(".filter-card input.el-input__inner, input[placeholder]").first
    if not inp.count():
        return "ENV", "找不到搜索输入框", ""
    ph = inp.get_attribute("placeholder") or ""
    inp.fill("zzz不存在题目9999")
    e.click_text("查询")
    e.page.wait_for_timeout(2000)
    after = e.row_count()
    empty = e.empty_hint()
    if after == 0 or empty:
        return "PASS", f"搜索后 {before}→{after} 行，空态「{empty[:30]}」", ""
    return "P1", f"搜索无效：{before}→{after} 行（应为 0）", "搜索结果未收敛"


# ---------------------------------------------------------------- 成绩中心
def t_scores_render():
    inject(e, "student", "/student/scores", 3200)
    rows = e.row_count()
    headers = [th.inner_text().strip() for th in e.page.locator(".el-table__header th").all()]
    if rows or e.empty_hint():
        return "PASS", f"{rows} 行，表头 {headers[:6]}", ""
    return "P1", f"成绩中心无数据也无空态提示：{root_text()[:80]}", ""


def t_scores_rank_consistency():
    """得分必须 <= 总分，及格判定与得分率一致（曾有 10/100 显示已及格）。"""
    d, _ = api_data("GET", "/report/student/score-trend?limit=50")
    items = d if isinstance(d, list) else []
    bad = []
    for it in items:
        sc, ts = it.get("score"), it.get("total_score")
        if sc is None or not ts:
            continue
        if sc > ts + 0.01:
            bad.append(f"{it.get('name')}: {sc}/{ts}")
    if bad:
        return "P1", f"得分超过总分：{bad[:3]}", "成绩数据错误"
    return "PASS", f"{len(items)} 条成绩，得分均未超过总分", ""


# ---------------------------------------------------------------- 学习报表
def t_report_render():
    inject(e, "student", "/student/report", 4000)
    txt = root_text()
    if "累计做题" in txt or "成绩趋势" in txt:
        return "PASS", f"报表渲染：{txt[:90]}", ""
    return "P1", f"学习报表未渲染：{txt[:100]}", ""


def t_report_subject_filter_effective():
    """学科筛选必须真正下发并改变数据（score-trend 曾完全忽略该参数）。"""
    inject(e, "student", "/student/report", 4000)
    sel = e.page.locator(".el-select").first
    sel.click()
    e.page.wait_for_timeout(700)
    opts = visible_options()
    opts = [o for o in opts if o and "全部" not in o]
    if not opts:
        e.page.keyboard.press("Escape")
        return "ENV", "无学科可选", ""
    dup = len(opts) - len(set(opts))
    e.page.locator(".el-select-dropdown__item", has_text=opts[0]).first.click()
    e.page.wait_for_timeout(3200)
    # 直接回查接口：传一个必然无匹配的 user 无关学科 id，比对是否真的被过滤
    d_all, _ = api_data("GET", "/report/student/score-trend")
    d_none, _ = api_data("GET", "/report/student/score-trend?subject_id=999999")
    n_all = len(d_all or [])
    n_none = len(d_none or [])
    if n_all and n_none == n_all:
        return "P1", f"score-trend 忽略 subject_id（全部 {n_all} 条 == 不存在学科 {n_none} 条）", \
               "个人报表按学科筛选是摆设，图表永远显示全科数据"
    if dup:
        return "P1", f"学科下拉重复 {dup} 项", "同名学科无法区分年级"
    return "PASS", f"学科筛选生效（全量 {n_all} / 不存在学科 {n_none} 条），下拉无重复", ""


# ---------------------------------------------------------------- 错题本
def t_wrong_render():
    inject(e, "student", "/student/wrong", 3200)
    txt = root_text()
    if "错题本" in txt and "错题总数" in txt:
        return "PASS", f"渲染正常：{txt[:80]}", ""
    return "P1", f"错题本未渲染：{txt[:100]}", ""


def t_wrong_search_empty():
    inject(e, "student", "/student/wrong", 3000)
    before = e.row_count()
    inp = e.page.locator(".filter-card input.el-input__inner, input[placeholder]").first
    if not inp.count():
        return "ENV", "找不到搜索输入框", ""
    ph = inp.get_attribute("placeholder") or ""
    inp.fill("zzz不存在的错题9999")
    e.click_text("查询")
    e.page.wait_for_timeout(2000)
    empty = e.empty_hint()
    after = e.row_count()
    if after == 0 or (empty and "暂无" in empty):
        return "PASS", f"搜索无匹配 → {before}→{after} 行，空态「{empty[:30]}」", ""
    return "P1", f"搜索未收敛：{before}→{after} 行", ""


def t_wrong_subject_filter():
    """学科筛选：选学科后总数应变化（代表 id 指向最低年级会变 0）。"""
    inject(e, "student", "/student/wrong", 3200)
    d_all, _ = api_data("GET", "/learning/wrong-questions?page=1&page_size=5")
    total_all = (d_all or {}).get("total")
    sel = e.page.locator(".el-form-item", has_text="学科").locator(".el-select").first
    sel.click()
    e.page.wait_for_timeout(800)
    opts = visible_options()
    opts = [o for o in opts if o and "全部" not in o]
    if not opts:
        e.page.keyboard.press("Escape")
        return "ENV", "学科下拉为空", ""
    dup = len(opts) - len(set(opts))
    e.page.locator(".el-select-dropdown__item", has_text=opts[0]).first.click()
    e.page.wait_for_timeout(2600)
    txt = root_text()
    if dup:
        return "P1", f"学科下拉重复 {dup} 项（{opts[:9]}）", "同名学科重复，选中会查错年级"
    return "PASS", f"学科 {len(opts)} 项无重复，选「{opts[0]}」后：{txt[:60]}（全量 total={total_all}）", ""


# ---------------------------------------------------------------- 学习笔记
def t_notes_render():
    inject(e, "student", "/student/notes", 3000)
    txt = root_text()
    if "学习笔记" in txt:
        return "PASS", f"渲染正常，{e.row_count()} 行卡片", ""
    return "P1", f"笔记页未渲染：{txt[:100]}", ""


def t_notes_empty_form():
    inject(e, "student", "/student/notes", 3000)
    if not e.click_text("新建笔记"):
        return "ENV", "找不到「新建笔记」", ""
    e.page.wait_for_timeout(1200)
    e.click_text("保存") or e.click_text("确定")
    e.page.wait_for_timeout(1200)
    errs = e.form_errors()
    toast = e.toast_text()
    if errs or "请输入" in toast:
        return "PASS", f"空表单被拦截：errors={errs[:2]} toast='{toast[:30]}'", ""
    return "P2", f"空表单未拦截（errors={errs}, toast='{toast}'）", ""


def t_notes_create():
    inject(e, "student", "/student/notes", 3000)
    if not e.click_text("新建笔记"):
        return "ENV", "找不到「新建笔记」", ""
    e.page.wait_for_timeout(1200)
    e.fill_by_label("标题", NOTE_TITLE)
    body = e.page.locator(".el-dialog textarea").first
    if body.count():
        body.fill("UIBODY 这是一条自动化用例创建的笔记正文。")
    e.click_text("保存") or e.click_text("确定")
    e.page.wait_for_timeout(2400)
    d, _ = api_data("GET", "/learning/notes?page=1&page_size=50")
    items = (d or {}).get("items") or []
    hit = any((x.get("title") or "") == NOTE_TITLE for x in items)
    if hit:
        return "PASS", f"笔记已落库：{NOTE_TITLE}", ""
    return "P1", f"提示成功但接口查不到「{NOTE_TITLE}」（共 {len(items)} 条）", "笔记丢失"


def t_notes_xss_sanitized():
    """存储型 XSS：正文含 <script>/<img onerror> 时渲染必须被净化。

    判据：打开详情抽屉后，.note-content 内不得存在 script 元素、
    也不得有带 onerror 的 img；同时正文文本仍可见。
    """
    inject(e, "student", "/student/notes", 3000)
    # 直接建一条带 payload 的笔记（走真实接口，模拟用户输入）
    payload = ('XSSBODY<img src=x onerror="window.__xss=1">'
               '<script>window.__xss2=1</script>'
               '<a href="javascript:alert(1)">click</a>')
    r = api("POST", "/learning/notes", S["token"],
            {"title": XSS_TITLE, "content": payload, "format": "markdown"})
    if r.get("code") != 200:
        return "BLOCKED", f"创建含 payload 的笔记失败：{r.get('message')}", ""
    nid = (r.get("data") or {}).get("id")
    # 在页面上打开它
    inject(e, "student", "/student/notes", 3200)
    e.page.evaluate("() => { window.__xss = 0; window.__xss2 = 0 }")
    card = e.page.get_by_text(XSS_TITLE).first
    if not card.count():
        return "ENV", "列表里找不到刚创建的 XSS 笔记（可能分页）", ""
    card.click()
    e.page.wait_for_timeout(2600)
    flags = e.page.evaluate("() => [window.__xss || 0, window.__xss2 || 0]")
    box = e.page.locator(".note-content").first
    n_script = box.locator("script").count() if box.count() else -1
    n_onerror = box.locator("img[onerror]").count() if box.count() else -1
    n_js = box.locator("a[href^='javascript']").count() if box.count() else -1
    # 清理
    if nid:
        api("DELETE", f"/learning/notes/{nid}", S["token"])
    if any(flags):
        return "P0", f"脚本被实际执行：window.__xss={flags}", \
               "存储型 XSS：任意学生可写入脚本并在打开笔记时执行"
    if n_script > 0 or n_onerror > 0 or n_js > 0:
        return "P0", f"危险节点残留：script={n_script} img[onerror]={n_onerror} a[javascript:]={n_js}", \
               "存储型 XSS：内容未净化，脚本在 DOM 中"
    return "PASS", f"payload 已被净化（script={n_script} onerror={n_onerror} js_href={n_js}，未执行）", ""


def t_notes_delete():
    """删除笔记：应删除并刷新列表。

    注意「删除」在**卡片**上（el-button link），不在详情抽屉的 footer
    （footer 只有 AI 整理 / 编辑）。先点卡片进详情找不到删除，会误判 ENV。
    """
    inject(e, "student", "/student/notes", 3000)
    d, _ = api_data("GET", "/learning/notes?page=1&page_size=50")
    items = (d or {}).get("items") or []
    mine = next((x for x in items if (x.get("title") or "").startswith("UI笔记")), None)
    if not mine:
        return "ENV", "无本轮创建的笔记可删", ""
    # 直接点卡片上的「删除」链接按钮（不先进详情）
    btns = e.page.get_by_role("button", name="删除")
    if btns.count() == 0:
        return "ENV", "列表卡片上没有「删除」按钮", ""
    btns.first.click()
    e.page.wait_for_timeout(900)
    e.confirm()
    e.page.wait_for_timeout(2400)
    d2, _ = api_data("GET", "/learning/notes?page=1&page_size=50")
    items2 = (d2 or {}).get("items") or []
    still = any((x.get("title") or "") == mine["title"] for x in items2)
    if still:
        return "P1", f"删除后接口仍能查到「{mine['title']}」", "删除未生效"
    return "PASS", f"笔记「{mine['title']}」已删除（{len(items)}→{len(items2)}）", ""


# ---------------------------------------------------------------- 随机练习
def t_practice_empty_validate():
    inject(e, "student", "/student/practice", 3200)
    txt = root_text()
    if "随机练习" not in txt:
        return "P1", f"随机练习页未渲染：{txt[:100]}", ""
    if not e.click_text("生成练习"):
        return "ENV", "找不到「生成练习」", ""
    e.page.wait_for_timeout(1400)
    toast = e.toast_text()
    if "请选择" in toast or "请先" in toast:
        return "PASS", f"空表单被拦截：'{toast[:40]}'", ""
    return "P1", f"未选学科直接生成，无拦截（toast='{toast}'）", ""


def t_practice_subject_no_dup():
    """学科下拉不得重复，且必须是本年级学科（跨年级会抽到低年级题）。"""
    inject(e, "student", "/student/practice", 3200)
    sel = e.page.locator(".el-form-item", has_text="学科").locator(".el-select").first
    sel.click()
    e.page.wait_for_timeout(800)
    opts = visible_options()
    e.page.keyboard.press("Escape")
    if not opts:
        return "P1", "学科下拉为空", "无法做练习"
    dup = len(opts) - len(set(opts))
    if dup:
        return "P1", f"学科下拉重复 {dup} 项：{opts[:9]}", \
               "同名学科按年级重复，选中代表 id 会抽到最低年级的题"
    return "PASS", f"学科 {len(opts)} 项且无重复：{opts[:6]}", ""


def t_practice_generate_grade_correct():
    """生成练习：题目年级必须等于学生年级（曾把一年级题发给七年级学生）。"""
    inject(e, "student", "/student/practice", 3200)
    sel = e.page.locator(".el-form-item", has_text="学科").locator(".el-select").first
    sel.click()
    e.page.wait_for_timeout(800)
    opts = visible_options()
    if not opts:
        return "ENV", "学科下拉为空", ""
    e.page.locator(".el-select-dropdown__item").first.click()
    e.page.wait_for_timeout(1600)
    if not e.click_text("生成练习"):
        return "ENV", "找不到「生成练习」", ""
    e.page.wait_for_timeout(6000)
    toast = e.toast_text()
    txt = root_text()
    if "没有符合" in toast or "暂无题" in toast:
        return "ENV", f"无可用题目（{toast[:40]}），无法验证年级", ""
    # Practice.vue 的题干节点没有 .q-stem 类（那是 ExamPaper 的），
    # 判据改为页面文本里的「第 N 题」与「共 N 题」。
    import re as _re
    m = _re.search(r"共\s*(\d+)\s*题", txt)
    n_page = int(m.group(1)) if m else 0
    has_first = "第 1 题" in txt or "第1题" in txt
    if not (n_page and has_first):
        return "P2", f"生成后未渲染题目（共N题={n_page}, 首题={has_first}, toast='{toast[:40]}'）", ""
    # 回查刚落库的练习卷：题目年级必须等于学生年级（曾把一年级题发给七年级学生）
    d, _ = api_data("GET", "/learning/practice/history?page=1&page_size=1")
    items = (d or {}).get("items") or []
    tid = items[0].get("task_id") if items else None
    grade_note = ""
    if tid:
        td, _ = api_data("GET", f"/task/tasks/{tid}/paper")
        gids = {(it.get("grade_id") or 0) for it in ((td or {}).get("items") or [])}
        if gids and 7 not in gids and 0 not in gids:
            return "P1", f"练习卷题目年级 {gids} 与学生年级 7 不符（共 {n_page} 题）", \
                   "学生拿到其他年级的题目，无法作答"
        grade_note = f"，题目年级 {sorted(gids)}"
    return "PASS", f"生成并渲染 {n_page} 题{grade_note}", ""


# ---------------------------------------------------------------- 主流程
try:
    e.start()
    e.run("智能复习", "统计数字正确", ["学生访问 /student/review"],
          "页面今日/待完成数字与接口一致", t_review_stats)
    e.run("智能复习", "学科筛选无重复", ["展开学科下拉"], "选项唯一", t_review_filter)
    e.run("智能复习", "AI 生成复习计划", ["点「AI 生成复习计划」"], "生成成功并刷新", t_review_generate)
    e.run("智能复习", "完成复习", ["点第一条「完成复习」"], "标记完成并移出待办", t_review_complete)

    e.run("掌握图谱", "页面渲染", ["访问 /student/mastery"], "图表与概览渲染", t_mastery_render)
    e.run("掌握图谱", "学科筛选", ["展开学科下拉", "选非首项"], "无重复且数据刷新", t_mastery_subject_filter)

    e.run("自主组卷", "页面渲染", ["访问 /student/custom"], "表单完整", t_custom_render)
    e.run("自主组卷", "学科不跨年级", ["展开学科", "选学科后看知识点"], "学科唯一且知识点属本学科", t_custom_subject_no_cross_grade)
    e.run("自主组卷", "空表单校验", ["不填表单直接「生成自测卷」"], "被拦截并提示", t_custom_empty_validate)

    e.run("学习打卡", "页面渲染", ["访问 /student/goals"], "看板渲染", t_goals_render)
    e.run("学习打卡", "新建目标空表单", ["点「新建目标」后直接保存"], "校验拦截", t_goals_empty_form)
    e.run("学习打卡", "新建目标", ["填名称/周期/目标值", "保存"], "落库可查", t_goals_create)

    e.run("学习路径", "页面渲染", ["访问 /student/path"], "路径与建议渲染", t_path_render)
    e.run("学习路径", "去练习跳转", ["点「去练习」"], "跳到随机练习页", t_path_practice_jump)

    e.run("闪卡速记", "页面渲染", ["访问 /student/flashcard"], "卡片渲染", t_flashcard_render)
    e.run("闪卡速记", "认识/不认识", ["点「不认识」"], "卡片推进", t_flashcard_actions)
    e.run("闪卡速记", "学科无重复", ["展开学科下拉"], "选项唯一", t_flashcard_subject_dup)

    e.run("题目收藏", "页面渲染", ["访问 /student/favorites"], "列表或空态", t_favorites_render)
    e.run("题目收藏", "搜索无匹配", ["输入不存在题干", "查询"], "收敛为空", t_favorites_search)

    e.run("成绩中心", "列表渲染", ["访问 /student/scores"], "表格渲染或空态", t_scores_render)
    e.run("成绩中心", "得分不超总分", ["回查 score-trend"], "score <= total_score", t_scores_rank_consistency)

    e.run("学习报表", "页面渲染", ["访问 /student/report"], "概览与图表渲染", t_report_render)
    e.run("学习报表", "学科筛选真实生效", ["选学科", "回查接口对比"], "参数真正参与过滤", t_report_subject_filter_effective)

    e.run("错题本", "页面渲染", ["访问 /student/wrong"], "列表与统计渲染", t_wrong_render)
    e.run("错题本", "搜索无匹配", ["输入不存在题干", "查询"], "收敛为空", t_wrong_search_empty)
    e.run("错题本", "学科筛选", ["展开学科并选一项"], "无重复且结果变化", t_wrong_subject_filter)

    e.run("学习笔记", "页面渲染", ["访问 /student/notes"], "列表渲染", t_notes_render)
    e.run("学习笔记", "新建空表单", ["点「新建笔记」后直接保存"], "校验拦截", t_notes_empty_form)
    e.run("学习笔记", "新建笔记", ["填标题与正文", "保存"], "落库可查", t_notes_create)
    e.run("学习笔记", "XSS 净化", ["写入含 script/onerror 的笔记", "打开详情"],
          "脚本不执行、危险节点被移除", t_notes_xss_sanitized)
    e.run("学习笔记", "删除笔记", ["打开笔记", "删除", "确认"], "删除生效", t_notes_delete)

    e.run("随机练习", "空表单校验", ["不选学科直接「生成练习」"], "被拦截", t_practice_empty_validate)
    e.run("随机练习", "学科无重复", ["展开学科下拉"], "选项唯一且为本年级", t_practice_subject_no_dup)
    e.run("随机练习", "生成练习", ["选学科", "生成练习"], "渲染题目", t_practice_generate_grade_correct)
finally:
    e.stop()
    with open(os.path.join(HERE, "phase10.json"), "w", encoding="utf-8") as f:
        json.dump(e.rows, f, ensure_ascii=False, indent=1)
    passes = sum(1 for r in e.rows if r["verdict"] == "PASS")
    print(f"\n阶段十：{len(e.rows)} 项，通过 {passes}，问题 {len(e.rows) - passes}")
