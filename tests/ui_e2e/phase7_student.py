"""UI E2E 阶段七：学生端答题闭环 + 学习中心。

闭环链路：教师发布考试 → stu101 登录 → 待完成列表可见 → 开始答题
→ 空卷交卷（应有未答提醒）→ 逐题作答交卷（结果页 + 接口记录）
→ 已交卷后再进入被拦 → 已完成/成绩中心可查。

另覆盖：学习笔记（新建/空标题/搜索/删除/超长）、随机练习（下拉生成）。

说明：为了不让学生的一次作答消耗掉后续用例，本阶段用 API 预置**两个**
独立任务（答题用 / 空卷用），阶段六已单独验证「UI 发布」链路本身。
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
NMARK = f"UINOTE{STAMP}"
T_ANSWER = f"UIANS{STAMP}"
T_EMPTY = f"UIEMPTY{STAMP}"

e = E2E()


def ts(offset: int) -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time() + offset))


def pick_paper(min_items: int = 2):
    r = api("GET", "/question/papers?page=1&page_size=50", T["token"])
    items = (r.get("data") or {}).get("items") or []
    for p in items:
        if (p.get("item_count") or 0) >= min_items:
            return p
    return None


def create_task(title: str, paper_id: int) -> dict:
    body = {
        "title": title, "type": "exam", "paper_id": paper_id, "class_ids": [1],
        "duration": 60, "pass_score": 6,
        "start_at": ts(-3600), "end_at": ts(86400),
    }
    for attempt in (1, 2):
        r = api("POST", "/task/tasks", T["token"], body)
        if (r.get("data") or {}).get("id"):
            return r["data"]
        print(f"[setup] 创建任务 {title} 第 {attempt} 次失败: "
              f"code={r.get('code')} msg={r.get('message')!r}")
    return {}


def my_tasks(status: str = "published"):
    r = api("GET", f"/task/my/tasks?page=1&page_size=50&status={status}", S["token"])
    return (r.get("data") or {}).get("items") or []


PAPER = pick_paper()
TID_ANSWER = (create_task(T_ANSWER, PAPER["id"]) if PAPER else {}).get("id")
TID_EMPTY = (create_task(T_EMPTY, PAPER["id"]) if PAPER else {}).get("id")
print(f"[setup] paper={PAPER and PAPER['id']} task_answer={TID_ANSWER} task_empty={TID_EMPTY}")


def open_exam(tid: int):
    return inject(e, "student1", f"/student/exam/{tid}", 3200)


# ---------------------------------------------------------------- 用例
def t_pending_visible():
    url = inject(e, "student1", "/student/exams", 3000)
    if "/login" in url:
        return "P0", f"学生端被弹回登录（{url}）", "学生无法进入考试列表"
    txt = e.text()
    if T_ANSWER and T_ANSWER in txt:
        cards = e.page.locator(".task-card").count()
        return "PASS", f"待完成列表出现下发的「{T_ANSWER}」（共 {cards} 张卡片）", ""
    return "P1", f"待完成列表未出现 {T_ANSWER}：{txt[:120]!r}", "下发链路断开"


def t_start_exam():
    inject(e, "student1", "/student/exams", 2800)
    btn = e.page.get_by_role("button", name="开始答题")
    if btn.count() == 0:
        return "P1", "待完成列表没有「开始答题」按钮", "学生无法进入答题页"
    btn.first.click()
    e.page.wait_for_timeout(3200)
    if "/student/exam/" not in e.page.url:
        return "P1", f"未进入答题页（final={e.page.url.replace('http://localhost:5173', '')}）", ""
    cards = e.page.locator(".q-card").count()
    if cards == 0:
        return "P1", "答题页 0 道题", "考试是空卷"
    cd = e.page.locator(".countdown").first.inner_text().replace("\n", " ")
    return "PASS", f"进入答题页 {e.page.url.split('/')[-1]}，{cards} 题，{cd}", ""


def t_empty_submit():
    """空卷交卷：确认框必须提示「还有 N 题未作答」。"""
    if not TID_EMPTY:
        return "ENV", "预置任务失败", ""
    open_exam(TID_EMPTY)
    e.reset_evidence()
    e.page.get_by_role("button", name="交卷").first.click()
    e.page.wait_for_timeout(1200)
    dlg = e.page.locator(".el-dialog").first
    txt = dlg.inner_text().replace("\n", " ") if dlg.count() else ""
    warned = "未作答" in txt or "未答" in txt
    confirm = e.page.get_by_role("button", name="确认交卷")
    if confirm.count() == 0:
        return "P1", f"确认框无「确认交卷」（{txt[:70]!r}）", "无法交卷"
    confirm.first.click()
    e.page.wait_for_timeout(3000)
    post = e.last_call("POST", "/submit")
    hero = e.page.locator(".result-hero")
    score = hero.first.inner_text().replace("\n", " ") if hero.count() else ""
    if warned and post.get("status") == 200:
        return "PASS", f"确认框提示未答（「{txt[:60]}」）→ 交卷 200 → 结果页「{score[:40]}」", ""
    if not warned:
        return "P1", f"空卷交卷没有任何未答提醒（确认框：{txt[:70]!r}）", "学生容易误交白卷"
    return "P1", f"交卷失败：{json.dumps(post, ensure_ascii=False)[:120]}", ""


def t_answer_and_submit():
    """逐题作答后交卷，必须 POST 200 且结果页给出分数。"""
    if not TID_ANSWER:
        return "ENV", "预置任务失败", ""
    open_exam(TID_ANSWER)
    n = e.page.locator(".q-card").count()
    if n == 0:
        return "ENV", "答题页 0 题", ""
    for i in range(n):
        card = e.page.locator(".q-card").nth(i)
        radio, check = card.locator(".el-radio"), card.locator(".el-checkbox")
        if radio.count():
            radio.first.click()
        elif check.count():
            check.first.click()
        else:
            ta = card.locator("textarea, input")
            if ta.count():
                ta.first.fill("这是学生的作答内容，用于验证主观题提交与批改流程。")
        e.page.wait_for_timeout(200)
    answered = e.page.locator(".bar-progress").first.inner_text().replace("\n", " ")
    e.reset_evidence()
    e.page.get_by_role("button", name="交卷").first.click()
    e.page.wait_for_timeout(1000)
    c = e.page.get_by_role("button", name="确认交卷")
    if c.count() == 0:
        return "P1", "确认框无「确认交卷」", "无法交卷"
    c.first.click()
    e.page.wait_for_timeout(3500)
    post = e.last_call("POST", "/submit")
    hero = e.page.locator(".result-hero")
    score = hero.first.inner_text().replace("\n", " ") if hero.count() else ""
    if post.get("status") == 200 and hero.count():
        return "PASS", f"{answered}；交卷 200；结果页「{score[:50]}」", ""
    if post.get("status") and post["status"] >= 400:
        return "P0", f"交卷失败 HTTP {post['status']}：{e.call_msg('POST', '/submit')[:80]}", \
               "学生无法提交答卷"
    return "P1", f"交卷后无结果页（POST={post.get('status')}，toast={e.toast_text()[:60]!r}）", ""


def t_reenter_after_submit():
    """已交卷的考试重新进入：应被拦回列表，而不是再给一张全新试卷。"""
    if not TID_ANSWER:
        return "ENV", "预置任务失败", ""
    open_exam(TID_ANSWER)
    e.page.wait_for_timeout(1500)
    url = e.page.url
    cards = e.page.locator(".q-card").count()
    toast = e.toast_text()
    if "/student/exam/" not in url:
        return "PASS", f"已交卷再进入被拦回列表（toast={toast[:50]!r}）", ""
    if cards:
        return "P2", f"已交卷仍可重新作答 {cards} 题（交卷时才会被后端 400）", \
               "学生白做一场，作答内容全部丢弃"
    return "P1", f"停在答题页但无题目（{url[-30:]}）", ""


def t_tabs_separated():
    """「待完成 / 已完成」必须按是否交卷真正分流。"""
    inject(e, "student1", "/student/exams", 3000)
    pending_txt = e.text()
    e.click_text("已完成")
    e.page.wait_for_timeout(2200)
    done_txt = e.text()
    if T_EMPTY and T_EMPTY in done_txt and T_EMPTY not in pending_txt:
        return "PASS", f"已交卷的 {T_EMPTY} 只在「已完成」中，不在「待完成」", ""
    if T_EMPTY and T_EMPTY in pending_txt:
        return "P2", f"已交卷任务仍留在「待完成」中（{T_EMPTY}）", \
               "学生点进去才被告知不能重复作答"
    return "P1", f"已完成 tab 未见 {T_EMPTY}", ""


def t_done_tab():
    inject(e, "student1", "/student/exams", 2800)
    e.click_text("已完成")
    e.page.wait_for_timeout(2200)
    badges = [x.inner_text().replace("\n", " ").strip()
              for x in e.page.query_selector_all(".score-badge")]
    if not badges:
        return "P1", "已完成 tab 没有任何得分信息", "学生查不到成绩"
    dash = [b for b in badges if "得分 -" in b.replace(" ", "")]
    if dash:
        return "P2", f"得分显示为「-」：{badges[:3]}", "已完成列表看不到实际分数"
    return "PASS", f"已完成 tab 得分：{badges[:3]}", ""


def t_score_center():
    inject(e, "student1", "/student/scores", 2800)
    rows = e.row_count()
    d = e.dump()
    if rows == 0:
        return "P1", f"成绩中心 0 行（空态「{d.get('empty')}」）", "学生看不到自己的成绩"
    scores = [x.inner_text().strip() for x in e.page.query_selector_all(".el-table__row td:nth-child(3)")]
    return "PASS", f"成绩中心 {rows} 行，得分列={scores[:4]}", ""


def t_wrongbook():
    inject(e, "student1", "/student/wrong", 3000)
    txt = e.text()
    if "错题本" not in txt:
        return "P2", f"错题本页异常：{txt[:80]!r}", ""
    cards = e.page.locator(".el-card").count()
    hint = e.empty_hint()
    return "PASS", f"错题本可访问（卡片 {cards}，空态「{hint[:16] or '无'}」）", ""


def t_notes_crud():
    inject(e, "student1", "/student/notes", 2800)
    e.click_text("新建笔记")
    e.page.wait_for_timeout(1400)
    if not e.dialog_visible():
        return "P2", "未打开新建笔记弹窗", ""
    e.page.locator(".el-dialog").get_by_role("button", name="保存").click()
    e.page.wait_for_timeout(1200)
    empty_toast = e.toast_text()
    empty_errs = e.form_errors()
    still = e.dialog_visible()
    e.fill_by_label("标题", NMARK, ".el-dialog")
    e.page.locator(".el-dialog textarea").first.fill(
        "这是一条用于 UI 验证的笔记正文，包含检索关键词 学习中心 。")
    e.select_by_label("学科", None, ".el-dialog")
    e.page.wait_for_timeout(300)
    e.page.keyboard.press("Escape")
    e.page.wait_for_timeout(400)
    e.page.locator(".el-dialog").get_by_role("button", name="保存").click()
    e.page.wait_for_timeout(2400)
    ok_empty = bool(empty_toast or empty_errs) and still
    if NMARK in e.text():
        msg = (empty_errs or [empty_toast])[0][:40] if (empty_errs or empty_toast) else "无提示"
        return ("PASS" if ok_empty else "P3",
                f"笔记创建成功；空标题提交被拦={ok_empty}（{msg}）", "")
    return "P1", f"笔记未出现在列表（toast={e.toast_text()[:70]!r}）", ""


def t_notes_search_delete():
    inject(e, "student1", "/student/notes", 2600)
    if not e.search("标题 / 内容", NMARK):
        return "P2", "未找到笔记搜索框", ""
    if NMARK not in e.text():
        return "P1", f"搜索「{NMARK}」未命中", "笔记检索失效"
    btn = e.page.get_by_role("button", name="删除")
    if btn.count() == 0:
        return "P2", "笔记卡片没有删除按钮", ""
    btn.first.click()
    e.page.wait_for_timeout(900)
    e.confirm()
    e.page.wait_for_timeout(2000)
    e.search("标题 / 内容", NMARK)
    if NMARK not in e.text():
        return "PASS", "搜索命中 → 删除 → 再次搜索已消失", ""
    return "P1", "删除后笔记仍可搜到", "删除无效"


def t_note_long_input():
    inject(e, "student1", "/student/notes", 2600)
    e.click_text("新建笔记")
    e.page.wait_for_timeout(1300)
    if not e.dialog_visible():
        return "P2", "未打开新建弹窗", ""
    e.fill_by_label("标题", f"{NMARK}LONG", ".el-dialog")
    body = "长文本测试。" * 3500
    e.page.locator(".el-dialog textarea").first.fill(body)
    e.page.locator(".el-dialog").get_by_role("button", name="保存").click()
    e.page.wait_for_timeout(3000)
    pc = e.last_call("POST", "/notes")
    st = pc.get("status")
    if st and st >= 500:
        return "P1", f"超长正文触发 {st}", "服务端异常"
    if f"{NMARK}LONG" in e.text():
        try:
            r = api("GET", f"/learning/notes?page=1&page_size=50&keyword={NMARK}LONG", S["token"])
            for it in ((r.get("data") or {}).get("items") or []):
                api("DELETE", f"/learning/notes/{it['id']}", S["token"])
        except Exception:
            pass
        return "P3", f"{len(body)} 字正文被接受（POST={st}），无长度上限；已清理", \
               "超长正文影响列表渲染"
    return "P3", f"未落库（POST={st}），toast={e.toast_text()[:60]!r}", ""


def t_practice_generate():
    inject(e, "student1", "/student/practice", 2800)
    subj = e.select_by_label("学科", None)
    if not subj:
        return "P2", "学科下拉无选项", ""
    e.page.wait_for_timeout(700)
    grade = e.select_by_label("年级", None)
    e.page.wait_for_timeout(500)
    num = e.input_value("题目数量")
    e.click_text("生成练习")
    e.page.wait_for_timeout(4000)
    card = e.page.locator(".q-card").count()
    toast = e.toast_text()
    if card:
        return "PASS", f"学科={subj} 年级={grade} 题量={num} → 生成 {card} 题", ""
    if toast:
        return "P2", f"生成失败：{toast[:80]!r}（学科={subj} 年级={grade}）", "学生无法自练"
    return "P1", "点击生成后无任何反馈", ""


e.start()
try:
    e.run("学生端-考试", "待完成列表出现下发的考试", ["stu101 会话注入", "访问 /student/exams"],
          "列表中可见本轮下发的考试", t_pending_visible)
    e.run("学生端-考试", "开始答题进入答题页", ["点击开始答题"], "进入答题页并渲染题目", t_start_exam)
    e.run("学生端-考试", "空卷直接交卷", ["不答题点交卷", "确认交卷"],
          "确认框提示未答数量，允许交卷得 0 分", t_empty_submit)
    e.run("学生端-考试", "逐题作答并交卷", ["每題选答", "交卷", "确认"],
          "交卷 200 并显示成绩", t_answer_and_submit)
    e.run("学生端-考试", "已交卷后重新进入答题页", ["直接访问 /student/exam/:id"],
          "被拦回列表，不重复给出试卷", t_reenter_after_submit)
    e.run("学生端-考试", "已完成 tab 得分显示", ["切到已完成 tab"], "显示具体得分", t_done_tab)
    e.run("学生端-考试", "待完成/已完成按交卷状态分流", [
        "查看待完成 tab", "切到已完成 tab", "比对已交卷任务出现在哪个 tab",
    ], "已交卷任务只出现在「已完成」", t_tabs_separated)
    e.run("学生端-成绩", "成绩中心列表", ["访问 /student/scores"], "列出本人成绩", t_score_center)
    e.run("学生端-错题", "错题本可访问", ["访问 /student/wrong"], "渲染错题本", t_wrongbook)
    e.run("学生端-笔记", "新建笔记（含空标题校验）", [
        "新建笔记", "空标题保存", "填标题+正文+学科", "保存",
    ], "空标题被拦，正常内容落库", t_notes_crud)
    e.run("学生端-笔记", "搜索并删除笔记", ["搜索笔记标题", "删除", "确认"],
          "搜索命中且删除后消失", t_notes_search_delete)
    e.run("学生端-笔记", "超长正文（约 2 万字）", ["新建笔记", "长文本正文", "保存"],
          "不触发 5xx", t_note_long_input)
    e.run("学生端-练习", "随机练习生成", ["选学科/年级", "生成练习"], "生成题目", t_practice_generate)
finally:
    e.stop()
    for tid in (TID_ANSWER, TID_EMPTY):
        if tid:
            api("DELETE", f"/task/tasks/{tid}", T["token"])
    with open(os.path.join(HERE, "phase7.json"), "w", encoding="utf-8") as f:
        json.dump(e.rows, f, ensure_ascii=False, indent=1)
    passes = sum(1 for r in e.rows if r["verdict"] == "PASS")
    print(f"\n阶段七：{len(e.rows)} 项，通过 {passes}，问题 {len(e.rows)-passes}")
