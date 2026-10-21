"""UI E2E 阶段五：教师端题库管理。

覆盖：列表渲染 / 下拉框筛选 / 搜索（命中 + 空态）/ 富文本输入 / 空表单校验 /
正常新增 / 删除 / 被引用题目删除保护 / 超长与特殊字符输入。

判定原则（避免假阳性）：
- 「新增成功」必须用接口回查确认落库，不能只看 toast；
- 「删除成功」必须用接口回查确认消失；
- 「被拦截」必须同时确认 (a) 有可读提示 (b) 数据未变。
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
STAMP = time.strftime("%H%M%S")
MARK = f"UIP{STAMP}"          # 埋进题干，便于精确定位

e = E2E()


# ------------------------------------------------------------------ 工具
def q_list(keyword: str = "") -> list:
    r = api("GET", f"/question/questions?page=1&page_size=50&keyword={keyword}", T["token"])
    d = r.get("data") or {}
    return d.get("items") or d.get("list") or []


def find_q(keyword: str):
    for it in q_list(keyword):
        if keyword in (it.get("stem") or ""):
            return it
    return None


def open_question_dialog():
    inject(e, "teacher", "/teacher/questions", 2600)
    if not e.click_text("新增题目"):
        return False
    e.page.wait_for_timeout(1400)
    return e.dialog_visible()


def fill_question(stem: str, grade="七年级", subject="数学", qtype="单选题",
                  score: str = "5", options=("甲选项", "乙选项", "丙选项", "丁选项")):
    """完整填一条单选题；返回缺失步骤列表。"""
    missing = []
    if not e.select_by_label("年级", grade, ".el-dialog"):
        missing.append("年级")
    e.page.wait_for_timeout(500)
    if not e.select_by_label("学科", subject, ".el-dialog"):
        missing.append("学科")
    e.page.wait_for_timeout(400)
    if not e.select_by_label("题型", qtype, ".el-dialog"):
        missing.append("题型")
    e.page.wait_for_timeout(700)
    try:
        e.page.locator(".el-dialog textarea").first.fill(stem, timeout=6000)
    except Exception:
        missing.append("题干")
    # 选项内容（placeholder 固定，可能存在多个）
    try:
        boxes = e.page.get_by_placeholder("选项内容")
        for i, txt in enumerate(options):
            if i < boxes.count():
                boxes.nth(i).fill(txt, timeout=4000)
    except Exception:
        missing.append("选项")
    # 勾第一个「正确」单选
    try:
        e.page.locator(".el-dialog .option-row").first.locator(".el-radio").first.click(timeout=4000)
    except Exception:
        missing.append("正确选项")
    # 分值
    try:
        e.form_item("分值", ".el-dialog").locator("input").first.fill(score, timeout=4000)
        e.page.keyboard.press("Tab")
    except Exception:
        missing.append("分值")
    return missing


# ------------------------------------------------------------------ 用例
def t_render():
    url = inject(e, "teacher", "/teacher/questions", 2800)
    if "/login" in url:
        return "P0", f"题库页被弹回登录（{url}）", "教师无法进入题库"
    d = e.dump()
    if not d.get("rows"):
        return "P1", f"表格 0 行（空态「{d.get('empty')}」）", "题库不可用"
    return "PASS", f"渲染 {d['rows']} 行，表头 {d['headers'][:6]}", ""


def t_select_filter():
    """下拉框：题型筛选「单选题」+ 点查询，应只返回单选题。

    注意：该页下拉变化**不会自动查询**，必须再点「查询」—— 这是交互设计，
    不是缺陷；第一次跑时漏点查询导致误判为「筛选失效」。
    """
    inject(e, "teacher", "/teacher/questions", 2500)
    before = e.row_count()
    picked = e.select_by_label("题型", "单选题")
    if not picked:
        return "P2", "题型下拉框无法选中", "筛选用不了"
    e.curr_query = True
    e.click_text("查询")
    e.page.wait_for_timeout(2000)
    after = e.row_count()
    req = [c for c in e.calls if c["method"] == "GET" and "/questions" in c["path"]]
    qs = req[-1]["path"] if req else ""
    types = [x.inner_text().strip() for x in e.page.query_selector_all(".el-table__row td:nth-child(3)")]
    if "qtype=single" in qs and after > 0 and set(types) == {"单选题"}:
        return "PASS", f"请求带上 qtype=single，{before}→{after} 行，题型列全为单选", ""
    return "P1", f"筛选未生效：qs={qs} 行数={after} 题型集合={set(types)}", "题型筛选失效"


def t_search_hit():
    inject(e, "teacher", "/teacher/questions", 2500)
    if not e.search("题干/解析", "学习中心"):
        return "P2", "未找到搜索框（placeholder=题干/解析）", "无法检索题库"
    rows = e.row_count()
    req = [c for c in e.calls if c["method"] == "GET" and "/questions" in c["path"]]
    qs = req[-1]["path"] if req else ""
    if rows == 0:
        return "P1", f"搜索「学习中心」返回 0 行，请求={qs}", "关键词检索无效"
    stems = [x.inner_text().strip() for x in e.page.query_selector_all(".el-table__row td:nth-child(2)")]
    hit = all("学习中心" in s for s in stems)
    if hit and "keyword=" in qs:
        return "PASS", f"搜索「学习中心」{rows} 行且题干全部包含关键词（请求带 keyword）", ""
    return "P1", f"搜索返回 {rows} 行但未收敛，stems={stems[:3]}", "搜索条件被部分忽略"


def t_search_empty():
    inject(e, "teacher", "/teacher/questions", 2400)
    e.search("题干/解析", "zzz不存在的题干9999")
    rows, hint = e.row_count(), e.empty_hint()
    if rows == 0:
        return "PASS", f"无匹配返回 0 行，空态「{hint[:24] or '无文案'}」", ""
    return "P1", f"无匹配仍返回 {rows} 行", "搜索条件被忽略"


def t_create_empty():
    """空表单直接保存：必须给出必填校验，且不得落库。"""
    if not open_question_dialog():
        return "P2", "点击「新增题目」未弹出对话框", "无法新增题目"
    e.page.locator(".el-dialog").get_by_role("button", name="保存").click()
    e.page.wait_for_timeout(1500)
    errs = e.form_errors()
    still = e.dialog_visible()
    if errs and still:
        return "PASS", f"弹窗未关闭并提示 {len(errs)} 条必填错误：{errs[:3]}", ""
    if not still:
        return "P0", "空表单提交后弹窗关闭（可能创建了空题目）", "题库可能被写入脏数据"
    return "P1", f"弹窗保持但无错误提示（errors={errs}）", "用户不知缺什么"


def t_create_ok():
    stem = f"{MARK} 下列说法正确的是？"
    if not open_question_dialog():
        return "P2", "未能打开新增题目弹窗", "无法新增题目"
    missing = fill_question(stem)
    if missing:
        return "P2", f"表单填充失败字段：{missing}", "自动化无法完成，需人工确认"
    e.page.locator(".el-dialog").get_by_role("button", name="保存").click()
    e.page.wait_for_timeout(2600)
    toast = e.toast_text()
    errs = e.form_errors()
    got = find_q(MARK)
    if got:
        return "PASS", (f"创建成功 id={got.get('id')} 题型={got.get('type')} 分值={got.get('score')} "
                        f"答案={got.get('answer')!r}；toast={toast[:40]!r}"), ""
    if errs:
        return "P1", f"提交被校验拦住：{errs[:3]}", ""
    return "P1", f"接口回查未找到题目（toast={toast[:60]!r}）", "创建结果不确定"


def t_duplicate_check_inline():
    """在已有题目的行上点「查重」：应给出查重结果面板而非报错。"""
    inject(e, "teacher", "/teacher/questions", 2600)
    row = e.page.locator(".el-table__row").first
    if row.count() == 0:
        return "ENV", "题库无数据，跳过", ""
    row.get_by_role("button", name="查重").first.click()
    e.page.wait_for_timeout(2500)
    txt = e.toast_text() + " " + e.text()
    if "重复" in txt or "相似" in txt or "查重" in txt:
        return "PASS", f"查重返回结果：{(e.toast_text() or txt)[:70]!r}", ""
    return "P1", "点击查重后无任何可见反馈", "用户不知道查重是否执行"


def t_delete_custom():
    """删除刚创建的题目：应二次确认并真正消失。"""
    inject(e, "teacher", "/teacher/questions", 2500)
    e.search("题干/解析", MARK)
    if e.row_count() == 0:
        return "ENV", "未搜到本轮创建的题目，跳过删除用例", ""
    before = find_q(MARK)
    e.page.locator(".el-table__row").first.get_by_role("button", name="删除").first.click()
    e.page.wait_for_timeout(1000)
    confirmed = e.confirm()
    e.page.wait_for_timeout(2200)
    after = find_q(MARK)
    if after is None and before is not None:
        return "PASS", f"删除成功（id={before.get('id')} 已不存在），确认框={confirmed}", ""
    return "P1", f"删除后题目仍存在（id={before.get('id') if before else '?'}）", "删除无效"


def t_delete_referenced():
    """删除被试卷引用的题目：后端必须拦截，数据不得变化。

    注意：列表的「使用」列是 Question.usage_count（只有 AI 组卷会累加），
    与后端删除时实时统计的 PaperItem 数量并不一致 —— 这里以 DELETE 的
    真实响应为准，不看 usage_count，否则会误判。
    """
    inject(e, "teacher", "/teacher/questions", 2400)
    e.search("题干/解析", "DEBUG after")
    row = e.page.locator(".el-table__row").first
    if row.count() == 0:
        return "ENV", "未能在列表定位被引用题目", ""
    row.get_by_role("button", name="删除").first.click()
    e.page.wait_for_timeout(900)
    e.confirm()
    e.page.wait_for_timeout(1600)
    dc = e.last_call("DELETE")
    msg = e.call_msg("DELETE")
    # 全量翻页确认题目仍在
    alive = False
    for pg in (1, 2, 3):
        rr = api("GET", f"/question/questions?page={pg}&page_size=50", T["token"])
        its = (rr.get("data") or {}).get("items") or []
        if any("DEBUG after" in (x.get("stem") or "") for x in its):
            alive = True
            break
    if dc.get("status") == 400 and "引用" in msg and alive:
        return "PASS", f"DELETE→{dc['status']}「{msg}」且题目仍在（保护有效）", ""
    if not alive:
        return "P0", f"被引用题目被删除（DELETE {dc.get('status')}）", "试卷缺题、总分虚高"
    return "P1", f"拦截但响应异常：{dc.get('status')} {msg[:80]}", ""


def t_error_presentation():
    """业务校验失败（400 + 可读 message）的呈现方式。

    期望：只弹一条后端文案。
    实测：额外弹「页面出错：Request failed with status code 400」，
         并在页面顶部插入红色「页面运行时错误」条 —— 用户会以为页面崩了。
    """
    inject(e, "teacher", "/teacher/questions", 2400)
    e.search("题干/解析", "DEBUG after")
    row = e.page.locator(".el-table__row").first
    if row.count() == 0:
        return "ENV", "未定位到可触发的题目", ""
    row.get_by_role("button", name="删除").first.click()
    e.page.wait_for_timeout(800)
    e.confirm()
    e.page.wait_for_timeout(1200)
    toast = e.toast_text()
    bar = e.page.query_selector("#global-error-bar")
    bar_txt = (bar.inner_text().strip() if bar else "")
    dup = "页面出错" in toast
    if bar_txt or dup:
        return "P1", (f"业务 400 被当成运行时错误：toast={toast[:90]!r}；"
                      f"顶部红条={bar_txt[:60]!r}"), \
               "全站所有未 catch 的业务错误都会误报「页面运行时错误」，误导用户与排障"
    return "PASS", f"仅提示后端文案：{toast[:80]!r}", ""


def t_long_input():
    """超长题干（约 5700 字）：不得 5xx，且需明确是否接受。"""
    if not open_question_dialog():
        return "P2", "未能打开新增题目弹窗", ""
    stem = f"{MARK}LONG" + "这是一个非常长的题干用于测试输入上限。" * 210
    fill_question(stem)
    filled = e.page.locator(".el-dialog textarea").first.input_value()
    e.page.locator(".el-dialog").get_by_role("button", name="保存").click()
    e.page.wait_for_timeout(2600)
    pc = e.last_call("POST", "/questions")
    st = pc.get("status")
    hit = find_q(f"{MARK}LONG")
    if hit:
        api("DELETE", f"/question/questions/{hit.get('id')}", T["token"])
        return "P3", (f"无长度上限：{len(filled)} 字题干被 POST {st} 接受并落库（id={hit.get('id')}，已清理）"), \
               "可写入超大题干，列表渲染与导出性能受影响"
    if st and st >= 500:
        return "P1", f"超长输入触发 {st}", "服务端异常"
    return "P3", f"未落库，POST={st}，toast={e.toast_text()[:60]!r}", ""


def t_special_chars():
    """特殊字符 / HTML 注入：应原样保存或转义，不得触发脚本执行。"""
    stem = f"{MARK}XSS <script>window.__xss=1</script> <img src=x onerror=alert(1)> 100% 正确"
    if not open_question_dialog():
        return "P2", "未能打开新增题目弹窗", ""
    fill_question(stem)
    e.page.locator(".el-dialog").get_by_role("button", name="保存").click()
    e.page.wait_for_timeout(2600)
    hit = find_q(f"{MARK}XSS")
    xss = e.page.evaluate("() => window.__xss || 0")
    if xss:
        return "P0", "题干中的 <script> 被执行（window.__xss=1）", "存储型 XSS，可窃取令牌"
    if hit:
        api("DELETE", f"/question/questions/{hit.get('id')}", T["token"])
        return "PASS", f"特殊字符被安全保存（id={hit.get('id')}，脚本未执行），已清理", ""
    return "P1", f"含特殊字符的题目未落库，toast={e.toast_text()[:70]!r}", ""


e.start()
try:
    e.run("题库管理", "列表渲染", ["教师访问 /teacher/questions"], "渲染题目表格与分页", t_render)
    e.run("题库管理", "题型下拉框筛选", ["题型下拉选「单选题」", "点击查询"],
          "请求带 qtype=single，列表仅剩单选题", t_select_filter)
    e.run("题库管理", "搜索命中", ["关键词输入「学习中心」", "回车"], "列表收敛为匹配题干", t_search_hit)
    e.run("题库管理", "搜索空态", ["关键词输入 zzz不存在的题干9999", "回车"],
          "0 行并给出空态提示", t_search_empty)
    e.run("题库管理", "新增题目空表单提交", ["点击新增题目", "直接点保存"],
          "必填项逐条报错且弹窗不关闭", t_create_empty)
    e.run("题库管理", "新增单选题（正常流程）", [
        "点击新增题目", "选年级=七年级", "选学科=数学", "选题型=单选题",
        f"题干填 {MARK}...", "填 4 个选项", "勾选正确项", "分值=5", "保存",
    ], "创建成功且列表/接口可查", t_create_ok)
    e.run("题库管理", "题目查重", ["在题目行点击「查重」"], "返回查重结果", t_duplicate_check_inline)
    e.run("题库管理", "删除自建题目", [
        f"搜索 {MARK}", "点击删除", "确认弹窗点确定",
    ], "确认后题目从题库移除", t_delete_custom)
    e.run("题库管理", "删除被试卷引用的题目", [
        "定位已被引用的题目「DEBUG after...」", "点击删除并确认",
    ], "后端 400 拦截且题目仍在", t_delete_referenced)
    e.run("题库管理", "业务校验失败的错误呈现", [
        "触发删除被引用题目（后端 400 + 可读文案）",
    ], "只提示一条后端文案，不误报运行时错误", t_error_presentation)
    e.run("题库管理", "超长题干输入（约 5700 字）", [
        "新增题目", "题干粘贴超长文本", "保存",
    ], "不触发 5xx，有长度限制或明确接受", t_long_input)
    e.run("题库管理", "特殊字符与 HTML 注入", [
        "题干填 <script>window.__xss=1</script><img onerror>", "保存",
    ], "脚本不执行（无存储型 XSS）", t_special_chars)
finally:
    e.stop()
    with open(os.path.join(HERE, "phase5.json"), "w", encoding="utf-8") as f:
        json.dump(e.rows, f, ensure_ascii=False, indent=1)
    passes = sum(1 for r in e.rows if r["verdict"] == "PASS")
    print(f"\n阶段五：{len(e.rows)} 项，通过 {passes}，问题 {len(e.rows)-passes}")
