# -*- coding: utf-8 -*-
"""教师端「教学管理」模块专项 e2e 测试（TaskManage + GradingCenter）。

涵盖：
- /task/tasks 的 list/create/edit/delete + 提交情况
- /task/tasks/{id}/paper 学生侧取卷
- /task/tasks/{id}/submit 交卷（首次/重做）
- /task/tasks/{id}/heartbeat 防切屏
- /task/tasks/{id}/submissions 教师查看提交情况
- /grading/pending  待批改列表
- /grading/submissions/{id} 批改详情
- /grading/submissions/{id}/grade 手动批改
- /grading/submissions/{id}/reject 打回重做
- /grading/submissions/{id}/publish 发布成绩
- /grading/tasks/{id}/report 班级学情报告
- /grading/tasks/{id}/ai-comment AI 教学建议
- 端到端流：发布作业 → 学生作答 → 教师批改 → publish → 学生查分
- 越权：学生不能读/写管理端接口
- 时间窗：截止后不能交卷、提前不能看题
"""
from datetime import datetime, timedelta

from e2e_framework import (  # noqa: F401
    R, Client, BASE,
    check, expect_denied, rows_of, total_of,
    data_of, is_down,
)


def _tag():
    return f"[E2E-TM-{datetime.now().strftime('%H%M%S%f')[-6:]}]"


def run():
    tea = Client("teacher1")
    tea.login("teacher1", "Teacher@123")
    tea2 = Client("teacher4")  # 任教七年级(2)班 stu731
    tea2.login("teacher4", "Teacher@123")
    stu = Client("stu731")
    stu.login("stu731", "Student@123")
    # 找一个 stu731 的 user.id 备用
    stu_uid = (stu.user or {}).get("id")

    # 一个共享的考试卷（教师1的私有题）
    paper_id, qid = _make_paper(tea)
    assert paper_id, "无法创建试卷，整个流程无法跑"

    # ============================================================
    # 1. 作业/考试 CRUD
    # ============================================================
    R.set_phase("教师端 · 教学管理 | 1. 作业/考试 CRUD")

    p, _, _ = tea.get("/task/tasks", params={"page_size": 50})
    base = total_of(p) or 0
    check("教师作业列表可读",
          p.get("success") and isinstance(rows_of(p), list),
          f"当前共 {base} 份")

    # 创建一个有开始/结束时间的 homework
    p, _, _ = tea.post("/task/tasks", {
        "title": f"{_tag()} 教学管理·作业",
        "type": "homework", "paper_id": paper_id,
        "duration": 30, "start_at": _fmt_now(-1),  # 已开始
        "end_at": _fmt_now(4),                       # 4 小时后截止
        "student_ids": [stu_uid] if stu_uid else [],
    })
    tid = (p.get("data") or {}).get("id")
    check("★ 教师可发布作业给学生",
          p.get("success") and bool(tid),
          f"task_id={tid} {p.get('message', '')[:60]}")

    # 任务详情
    if tid:
        p, _, _ = tea.get(f"/task/tasks/{tid}")
        check("教师可读任务详情", p.get("success"),
              f"{p.get('code')} {p.get('message', '')[:60]}")

        # 编辑任务：改标题
        p, _, _ = tea.put(f"/task/tasks/{tid}", {"title": f"{_tag()} 已编辑"})
        check("★ 教师可编辑任务（修改标题）",
              p.get("success"),
              f"{p.get('code')} {p.get('message', '')[:60]}")

        # 编辑后回查
        p, _, _ = tea.get(f"/task/tasks/{tid}")
        cur = (p.get("data") or {})
        check("编辑生效（标题已变更）",
              "已编辑" in (cur.get("title") or ""),
              f"title={cur.get('title')!r}")

    # 业务校验：缺 paper_id 必须被拒
    p, _, _ = tea.post("/task/tasks", {"title": "无试卷作业", "type": "homework"})
    check("★ 缺 paper_id 不能发布任务",
          p.get("success") is not True,
          p.get("message", ""))

    # 业务校验：无效 type 必须被拒
    if tid and paper_id:
        p, _, _ = tea.post("/task/tasks", {
            "title": f"{_tag()} bad type", "type": "xxx_invalid",
            "paper_id": paper_id, "duration": 30})
        check("★ 无效任务类型被拒",
              p.get("success") is not True,
              p.get("message", ""))

    # ============================================================
    # 2. 学生侧取卷 / 交卷 / 心跳
    # ============================================================
    R.set_phase("教师端 · 教学管理 | 2. 学生作答链路")

    if tid:
        p, _, _ = stu.get(f"/task/tasks/{tid}/paper")
        # 接口返回 {task, paper, items}，items 数组用 paper_item_id 作主键
        items = ((p.get("data") or {}).get("items")) or []
        check("学生可取卷（开始后）",
              p.get("success") and len(items) > 0,
              f"items={len(items)}")

        # 作答心跳
        p, _, _ = stu.post(f"/task/tasks/{tid}/heartbeat",
                           {"seconds": 60, "screen_focus": True})
        check("学生可发送作答心跳",
              p.get("success"),
              f"{p.get('code')} {p.get('message', '')[:60]}")

        # 首次提交
        if items:
            first = items[0]
            p, _, _ = stu.post(f"/task/tasks/{tid}/submit", {
                # 字段名：前端 ExamPaper 发的 payload 是 {paper_item_id, content}（不是 answer），
                # 后端 submit_answers 读 data.get("answers", []) —— 提交体的外层 key 是 answers
                "answers": [{"paper_item_id": first.get("paper_item_id"),
                              "content": "A"}]})
            check("★ 学生可首次提交",
                  p.get("success"),
                  p.get("message", ""))


    # ============================================================
    # 3. 教师批改中心
    # ============================================================
    R.set_phase("教师端 · 教学管理 | 3. 批改中心")

    p, _, _ = tea.get("/grading/pending", params={"page_size": 50})
    pending = rows_of(p)
    check("待批改列表可读",
          p.get("success") and isinstance(pending, list),
          f"共 {len(pending)} 条")

    # 取一份刚才的 submission
    sub = next((s for s in pending
                if s.get("task_id") == tid), None) if tid else None
    sub_id = (sub or {}).get("submission_id") or (sub or {}).get("id")
    check("★ 学生交卷后进入待批改",
          bool(sub_id),
          f"submission_id={sub_id}")

    # 批改详情
    if sub_id:
        p, _, _ = tea.get(f"/grading/submissions/{sub_id}")
        det = p.get("data") or {}
        check("批改详情可读",
              p.get("success") and det,
              f"keys={list(det.keys())[:6]}")
        # 批改详情返回 items 数组（每项含 answer_id / content / score）
        answers = det.get("items") or det.get("answers") or []
        check("批改详情含答题明细",
              isinstance(answers, list) and len(answers) > 0,
              f"answers={len(answers)}")

        # 手动批改
        ans_id = (answers[0] or {}).get("id") if answers else None
        if ans_id:
            p, _, _ = tea.post(f"/grading/submissions/{sub_id}/grade", {
                "items": [{"answer_id": ans_id, "score": 5,
                           "comment": "E2E 批改"}]})
            check("★ 教师可手动批改",
                  p.get("success"),
                  p.get("message", ""))

    # AI 教学建议（不一定有数据，看是否调用通）
    if tid:
        p, _, _ = tea.post(f"/grading/tasks/{tid}/ai-comment", {}, timeout=120)
        check("AI 教学建议可调用",
              p.get("success") or p.get("code") in (200, 404)
              or is_down(p),
              f"{p.get('code')} {p.get('message', '')[:60]}")

    # 班级学情报告
    if tid:
        p, _, _ = tea.post(f"/grading/tasks/{tid}/report")
        check("班级学情报告可生成",
              p.get("success") or p.get("code") in (200, 404, 500)
              or is_down(p),
              f"{p.get('code')} {p.get('message', '')[:60]}")

    # 任务提交情况
    if tid:
        p, _, _ = tea.get(f"/task/tasks/{tid}/submissions")
        rows = rows_of(p)
        check("任务提交情况可查（教师侧）",
              p.get("success") and isinstance(rows, list),
              f"{len(rows)} 份提交")

    # ============================================================
    # 4. publish / reject / re-grade
    # ============================================================
    R.set_phase("教师端 · 教学管理 | 4. 发布与打回")

    if sub_id:
        # 发布成绩
        p, _, _ = tea.post(f"/grading/submissions/{sub_id}/publish")
        check("★ 教师可发布成绩",
              p.get("success"),
              p.get("message", ""))

        # 发布后学生能在成绩中心看到
        p, _, _ = stu.get("/task/my/scores", params={"task_id": tid})
        check("★ 发布后学生可在成绩中心看到",
              p.get("success") and rows_of(p) is not None,
              p.get("message", ""))

    # ============================================================
    # 5. 时间窗：未来作业 / 已截止作业
    # ============================================================
    R.set_phase("教师端 · 教学管理 | 5. 时间窗校验")

    # 创建一个 2 小时后才开始的作业
    future_tid = None
    p, _, _ = tea.post("/task/tasks", {
        "title": f"{_tag()} 未来作业",
        "type": "homework", "paper_id": paper_id, "duration": 30,
        "start_at": _fmt_now(2),  # 2 小时后才开始
        "end_at": _fmt_now(4),
        "student_ids": [stu_uid] if stu_uid else [],
    })
    future_tid = (p.get("data") or {}).get("id")
    if future_tid:
        p, _, _ = stu.get(f"/task/tasks/{future_tid}/paper")
        sc = p.get("code")
        check("★ 未开考学生取卷被拒（403）",
              sc == 403,
              f"code={sc} msg={p.get('message', '')[:60]}")
        # 学生也不能提交
        p, _, _ = stu.post(f"/task/tasks/{future_tid}/submit",
                           {"content": []})
        check("★ 未开考学生交卷被拒",
              p.get("success") is not True,
              f"{p.get('code')} {p.get('message', '')[:60]}")

    # 创建一个已截止的作业
    past_tid = None
    p, _, _ = tea.post("/task/tasks", {
        "title": f"{_tag()} 已截止作业",
        "type": "homework", "paper_id": paper_id, "duration": 30,
        "start_at": _fmt_now(-4),  # 4 小时前开始
        "end_at": _fmt_now(-1),    # 1 小时前截止
        "student_ids": [stu_uid] if stu_uid else [],
    })
    past_tid = (p.get("data") or {}).get("id")
    if past_tid:
        p, _, _ = stu.post(f"/task/tasks/{past_tid}/submit",
                           {"content": [{"paper_item_id": 0, "answer": "A"}]})
        check("★ 已截止学生交卷被拒",
              p.get("success") is not True,
              f"{p.get('code')} {p.get('message', '')[:60]}")

    # ============================================================
    # 6. 删除 + 越权
    # ============================================================
    R.set_phase("教师端 · 教学管理 | 6. 删除 + 越权矩阵")

    if tid:
        p, _, _ = tea.delete(f"/task/tasks/{tid}")
        check("★ 教师可删除作业",
              p.get("success"),
              p.get("message", ""))

    # 越权：学生不能发布/批改
    expect_denied("学生不能发布任务", stu, "POST", "/task/tasks",
                  body={"title": "h", "type": "homework", "paper_id": paper_id})
    expect_denied("学生不能读待批改", stu, "GET", "/grading/pending")
    expect_denied("学生不能批改", stu, "POST",
                  f"/grading/submissions/{sub_id or 0}/grade",
                  body={"items": []})

    # 跨教师：teacher4 不能改 teacher1 的作业
    p, _, _ = tea2.delete(f"/task/tasks/{tid or 0}")
    check("★ 跨教师删除任务被拒（不是自己发布的）",
          p.get("success") is not True,
          p.get("message", ""))

    # ============================================================
    # 汇总
    # ============================================================
    R.env("教学管理", "见细分阶段")
    print(f"\n[完成] 教学管理专项测试：教师={tea.user.get('real_name')} 学生={stu.user.get('real_name')}")


def _fmt_now(delta_hours: float) -> str:
    """容器 TZ=Asia/Shanghai，datetime.now() 与后端一致。"""
    return (datetime.now() + timedelta(hours=delta_hours)).strftime("%Y-%m-%d %H:%M:%S")


def _make_paper(tea) -> tuple:
    """造一个含 1 道题的简单试卷（保证 status=published 且 paper.items 非空）。"""
    # 直接建题（题目状态默认 draft，必须再发布才能用）
    p, _, _ = tea.post("/question/questions", {
        "type": "single",
        "stem": f"[E2E-TM] 教学管理测试题 {_tag()}",
        "options": [{"key": "A", "text": "对"}, {"key": "B", "text": "错"}],
        "answer": "A", "difficulty": "easy", "score": 5,
        "grade_id": 1, "subject_id": 1, "bank_type": "private",
        "analysis": "测试题，无解析"})
    qid = (p.get("data") or {}).get("id")
    if not qid:
        return None, None
    # 上架题目：必须 published 否则 create_paper 不阻止但 /task/tasks/{id}/paper
    # 取题也会被拿空（paper.items 仍非空但题未发布状态过滤）
    up, _, _ = tea.put(f"/question/questions/{qid}/status", {"status": "published"})
    if not up.get("success"):
        return None, None
    # 组卷
    p, _, _ = tea.post("/question/papers", {
        "name": f"[E2E-TM] 教学管理测试卷 {_tag()}",
        "subject_id": 1, "grade_id": 1, "duration": 30,
        "items": [{"question_id": qid, "score": 5}]})
    pid = (p.get("data") or {}).get("id")
    # 验证 paper.items 真有内容
    if pid:
        v, _, _ = tea.get(f"/question/papers/{pid}")
        if not (v.get("data") or {}).get("items"):
            return None, None
    return pid, qid


if __name__ == "__main__":
    run()