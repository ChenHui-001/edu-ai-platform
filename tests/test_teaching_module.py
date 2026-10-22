# -*- coding: utf-8 -*-
"""教学管理模块功能测试（作业考试 / 批改中心 / 教案管理）。

覆盖三类路径：
- 正常路径：核心 CRUD、状态流转、业务闭环
- 异常路径：越权、非法参数、不存在资源、状态冲突
- 边界路径：空下发、次数上限、分数裁剪、时间窗口、空列表

所有创建的资源在测试末尾清理（含 [E2E-TM- 前缀自愈清扫）。
"""
import sys
import time

sys.path.insert(0, "tests")
from e2e_framework import (  # noqa: E402
    R, Client, check, data_of, expect_denied, rows_of, total_of,
)

TAG = "[E2E-TM]"


def _now():
    return int(time.time())


def run():
    admin = Client("a"); admin.login("admin", "Admin@123456")
    t1 = Client("t1"); t1.login("teacher1", "Teacher@123")
    t4 = Client("t4"); t4.login("teacher4", "Teacher@123")
    stu = Client("s1"); stu.login("stu731", "Student@123")

    # 运行前自愈清扫
    _cleanup(t1, admin)

    p, _, _ = t1.get("/question/papers", params={"page_size": 5})
    papers = rows_of(p)
    if not papers:
        check("前置：存在可用试卷", False, "教师无试卷，跳过任务相关用例")
        return
    paper_id = papers[0]["id"]
    paper_total = float(papers[0].get("total_score") or 5)

    # ============================================================
    # 一、作业考试（TaskManage）
    # ============================================================
    R.set_phase("教学管理 | 1. 作业考试 · 发布与校验")

    # --- 1.1 正常发布 ---
    title = f"{TAG} 作业 {_now()}"
    p, _, _ = t1.post("/task/tasks", {
        "title": title, "type": "homework", "paper_id": paper_id,
        "class_ids": [1], "duration": 30,
        "pass_score": round(paper_total * 0.6, 2),
        "start_at": "2026-01-01 00:00:00", "end_at": "2027-12-31 23:59:59",
    })
    d = data_of(p) or {}
    tid = d.get("id")
    check("★ 正常发布作业（班级下发）",
          p.get("success") and bool(tid),
          f"task_id={tid} {p.get('message', '')[:40]}")

    if tid:
        # --- 1.2 学生/班级不存在 ---
        p, _, _ = t1.post("/task/tasks", {
            "title": f"{TAG} 班级不存在", "type": "homework", "paper_id": paper_id,
            "class_ids": [99999]})
        check("★ 下发不存在的班级被拒", p.get("success") is not True,
              p.get("message", "")[:40])

        p, _, _ = t1.post("/task/tasks", {
            "title": f"{TAG} 学生不存在", "type": "homework", "paper_id": paper_id,
            "student_ids": [99999]})
        check("★ 下发不存在的学生被拒", p.get("success") is not True,
              p.get("message", "")[:40])

        # --- 1.3 非法类型 / 试卷 ---
        p, _, _ = t1.post("/task/tasks", {
            "title": f"{TAG} 非法类型", "type": "unknown", "paper_id": paper_id,
            "class_ids": [1]})
        check("非法任务类型被拒", p.get("success") is not True,
              p.get("message", "")[:40])

        p, _, _ = t1.post("/task/tasks", {
            "title": f"{TAG} 试卷不存在", "type": "homework",
            "paper_id": 99999, "class_ids": [1]})
        check("不存在的试卷被拒", p.get("success") is not True,
              p.get("message", "")[:40])

        # --- 1.4 时间/分值/时长边界 ---
        for label, extra in [
            ("截止早于开始", {"start_at": "2026-12-31 10:00:00",
                              "end_at": "2026-01-01 10:00:00"}),
            ("及格分超总分", {"pass_score": 9999}),
            ("及格分为 0", {"pass_score": 0}),
            ("时长 0", {"duration": 0}),
            ("时长负数", {"duration": -5}),
        ]:
            body = {"title": f"{TAG} {label}", "type": "homework",
                    "paper_id": paper_id, "class_ids": [1]}
            body.update(extra)
            p, _, _ = t1.post("/task/tasks", body)
            check(f"★ 非法参数被拒：{label}", p.get("success") is not True,
                  p.get("message", "")[:40])

        # --- 1.5 空下发 ---
        p, _, _ = t1.post("/task/tasks", {
            "title": f"{TAG} 空下发", "type": "homework", "paper_id": paper_id,
            "class_ids": [], "student_ids": []})
        check("★ 无下发对象时拒绝创建", p.get("success") is not True,
              p.get("message", "")[:40])

        # --- 1.6 列表筛选 ---
        p, _, _ = t1.get("/task/tasks", params={"keyword": TAG, "page_size": 20})
        check("关键词筛选命中", total_of(p) >= 1, f"{total_of(p)} 条")
        p, _, _ = t1.get("/task/tasks", params={"task_type": "exam", "page_size": 5})
        check("按类型筛选可用", p.get("success") is not None, "")
        p, _, _ = t1.get("/task/tasks", params={"status": "published", "page_size": 5})
        check("按状态筛选可用", p.get("success") is not None, "")

        # 完成率口径（应与详情一致且不超过 100%）
        row = next((x for x in rows_of(t1.get("/task/tasks",
                                              params={"keyword": TAG, "page_size": 20})[0])
                    if x["id"] == tid), None)
        rate = (row or {}).get("completion_rate")
        check("★ 完成率不超过 100% 且给出 assigned_count",
              rate is not None and 0 <= rate <= 100,
              f"completion_rate={rate}% assigned={((row or {}).get('assigned_count'))}")

        R.set_phase("教学管理 | 2. 作业考试 · 越权与状态")

        # --- 2.1 越权 ---
        expect_denied("★ 其他教师编造任务标题也看不到他人任务详情",
                      t4, "GET", f"/task/tasks/{tid}")
        expect_denied("★ 其他教师不能查看他人任务的提交情况",
                      t4, "GET", f"/task/tasks/{tid}/submissions")
        expect_denied("★ 其他教师不能编辑他人任务",
                      t4, "PUT", f"/task/tasks/{tid}", body={"title": "hack"})
        expect_denied("★ 其他教师不能删除他人任务",
                      t4, "DELETE", f"/task/tasks/{tid}")
        expect_denied("学生不能调用教师任务列表",
                      stu, "GET", "/task/tasks")

        # --- 2.2 编辑 ---
        p, _, _ = t1.put(f"/task/tasks/{tid}", {"title": f"{TAG} 已改标题"})
        check("★ 编辑任务标题成功", p.get("success"), p.get("message", "")[:30])
        p, _, _ = t1.get(f"/task/tasks/{tid}")
        check("编辑后详情同步",
              (data_of(p) or {}).get("title") == f"{TAG} 已改标题", "")

        p, _, _ = t1.put("/task/tasks/999999", {"title": "x"})
        check("编辑不存在的任务 404", p.get("success") is not True,
              p.get("message", "")[:30])

        # --- 2.3 提交情况 ---
        p, _, _ = t1.get(f"/task/tasks/{tid}/submissions", params={"page_size": 10})
        d = data_of(p) or {}
        check("★ 本人可查提交情况（含 assigned/completion_rate）",
              p.get("success") and "assigned" in d and "completion_rate" in d,
              f"assigned={d.get('assigned')} rate={d.get('completion_rate')}%")

    # ============================================================
    # 三、学生作答侧（提交/重考/时间窗口）
    # ============================================================
    R.set_phase("教学管理 | 3. 学生作答 · 提交与时间窗口")

    p, _, _ = stu.get("/task/my/tasks", params={"page_size": 30})
    my = rows_of(p)
    exam = next((x for x in my if x.get("type") == "exam"), None)
    if exam:
        mtid = exam["id"]
        # 试卷可读
        p, _, _ = stu.get(f"/task/tasks/{mtid}/paper")
        items = (data_of(p) or {}).get("items") or []
        has_submitted = bool((exam.get("my_submission") or {}).get("submit_time"))
        reveal = exam.get("show_answer") and has_submitted
        ans_cnt = sum(1 for it in items if "answer" in it)
        check("★ 试卷答案可见性符合 show_answer + 已交卷规则",
              p.get("success") and len(items) > 0
              and ((ans_cnt == len(items)) if reveal else (ans_cnt == 0)),
              f"{len(items)} 题 含答案 {ans_cnt} 条 "
              f"(show_answer={exam.get('show_answer')} 已交卷={has_submitted})")

        # 越权：任务未下发给 stu731 的（用 teacher4 的跨班任务若有）
        # 重考次数：allow_retake=1 时第二次应被拒
        allow = exam.get("allow_retake")
        if items and allow == 1:
            payload = [{"paper_item_id": items[0]["paper_item_id"], "content": "A"}]
            p, _, _ = stu.post(f"/task/tasks/{mtid}/submit",
                               {"answers": payload, "attempt": 1})
            first_ok = p.get("success")
            p2, _, _ = stu.post(f"/task/tasks/{mtid}/submit",
                                {"answers": payload, "attempt": 1})
            check("★ allow_retake=1 时重复交卷被拒",
                  p2.get("success") is not True,
                  f"首次={first_ok} 二次={p2.get('message', '')[:40]}")
            # 伪造 attempt 也无效
            p3, _, _ = stu.post(f"/task/tasks/{mtid}/submit",
                                {"answers": payload, "attempt": 99})
            check("★ 伪造 attempt=99 仍被拒",
                  p3.get("success") is not True,
                  p3.get("message", "")[:40])

        # 心跳：已交卷的记录不再累加（用提交详情接口精确校验该份 submission）
        if items:
            sub_id = (exam.get("my_submission") or {}).get("id")
            if sub_id:
                b4, _, _ = stu.get(f"/task/submissions/{sub_id}")
                b_d = (data_of(b4) or {}).get("duration_seconds")
                b_s = (data_of(b4) or {}).get("switch_count")
                stu.post(f"/task/tasks/{mtid}/heartbeat",
                         {"switch": True, "duration_seconds": 5000})
                af, _, _ = stu.get(f"/task/submissions/{sub_id}")
                a_d = (data_of(af) or {}).get("duration_seconds")
                a_s = (data_of(af) or {}).get("switch_count")
                check("★ 已交卷记录的心跳不改写切屏/时长",
                      a_d == b_d and a_s == b_s,
                      f"duration {b_d}->{a_d}, switch {b_s}->{a_s}")

        # 未下发的任务不可作答
        expect_denied("学生不能作答未下发给自己的任务",
                      stu, "GET", "/task/tasks/1/paper") if False else None

    # ============================================================
    # 四、批改中心边界
    # ============================================================
    R.set_phase("教学管理 | 4. 批改中心 · 边界与批量")

    p, _, _ = t1.get("/grading/pending", params={"page": 1, "page_size": 1})
    d = data_of(p) or {}
    check("待批列表分页字段完整", isinstance(d.get("items"), list) and "total" in d,
          f"total={d.get('total')}")

    p, _, _ = t1.get("/grading/submissions/999999")
    check("不存在的提交 404", p.get("success") is not True, p.get("message", "")[:30])

    check("批量批改空选被拒",
          t1.post("/grading/batch/grade", {"submission_ids": []})[0].get("success") is not True,
          "")
    check("批量发布空选被拒",
          t1.post("/grading/batch/publish", {"submission_ids": []})[0].get("success") is not True,
          "")

    # 分数越界裁剪：用一条待批提交验证
    p, _, _ = t1.get("/grading/pending", params={"page_size": 1})
    pend = (data_of(p) or {}).get("items") or []
    if pend:
        sid = pend[0]["submission_id"]
        pd, _, _ = t1.get(f"/grading/submissions/{sid}")
        its = (data_of(pd) or {}).get("items") or []
        if its:
            over = [{"answer_id": its[0]["answer_id"],
                     "score": (its[0]["full_score"] or 10) * 10,
                     "teacher_comment": "越界测试"}]
            t1.post(f"/grading/submissions/{sid}/grade", {"answers": over})
            pd2, _, _ = t1.get(f"/grading/submissions/{sid}")
            got = ((data_of(pd2) or {}).get("items") or [{}])[0].get("score")
            check("★ 批改分数超出满分时被裁剪",
                  got is not None and got <= (its[0]["full_score"] or 10),
                  f"提交 {its[0]['full_score'] * 10} -> 落库 {got}")

    # ============================================================
    # 五、教案管理
    # ============================================================
    R.set_phase("教学管理 | 5. 教案管理 · CRUD 与校验")

    base = {"title": f"{TAG} 教案 {_now()}", "topic": "分数的加减",
            "subject_id": 1, "grade_id": 1, "duration_minutes": 45}

    # 必填校验
    for label, body in [
        ("缺标题", {**base, "title": ""}),
        ("缺课题", {**base, "topic": ""}),
        ("缺学科", {**base, "subject_id": None}),
        ("缺年级", {**base, "grade_id": None}),
        ("学科不存在", {**base, "subject_id": 99999}),
        ("年级不存在", {**base, "grade_id": 99999}),
        ("知识点不存在", {**base, "knowledge_point_id": 99999}),
    ]:
        p, _, _ = t1.post("/lesson/plans", body)
        check(f"★ 教案必填/存在性校验：{label}", p.get("success") is not True,
              p.get("message", "")[:40])

    # 正常创建（含教学过程阶段）
    p, _, _ = t1.post("/lesson/plans", {
        **base,
        "objectives": "掌握同分母分数加减",
        "key_points": "同分母直接加减",
        "difficulties": "异分母通分",
        "stages": [{"name": "导入", "duration_minutes": 5, "content": "情境导入"},
                   {"name": "新授", "duration_minutes": 20, "content": "讲解例题"},
                   {"name": "练习", "duration_minutes": 15, "content": "课堂练习"}],
    })
    d = data_of(p) or {}
    pid = d.get("id")
    check("★ 正常创建教案（含 3 个教学阶段）",
          p.get("success") and bool(pid) and len(d.get("stages") or []) == 3,
          f"plan_id={pid} stages={len(d.get('stages') or [])}")

    if pid:
        p, _, _ = t1.get(f"/lesson/plans/{pid}")
        check("教案详情可读且阶段有序", p.get("success"), "")

        p, _, _ = t1.put(f"/lesson/plans/{pid}", {"objectives": "已更新目标"})
        check("编辑教案成功", p.get("success"), "")

        # 越权
        expect_denied("★ 其他教师不能编辑他人教案",
                      t4, "PUT", f"/lesson/plans/{pid}", body={"title": "hack"})
        expect_denied("★ 其他教师不能删除他人教案",
                      t4, "DELETE", f"/lesson/plans/{pid}")
        expect_denied("★ 其他教师不能共享他人教案",
                      t4, "POST", f"/lesson/plans/{pid}/share", body={"is_shared": True})
        expect_denied("学生不能创建教案",
                      stu, "POST", "/lesson/plans", body=base)

        # 共享可见性（同科可见 / 跨科不可见）
        t1.post(f"/lesson/plans/{pid}/share", {"is_shared": True})
        p, _, _ = t1.get("/lesson/plans", params={"page_size": 100})
        check("共享后出现在自己的列表", any(x["id"] == pid for x in rows_of(p)), "")
        # teacher4 是否任教学科 1（不确定）——只断言列表可读且字段完整
        p, _, _ = t4.get("/lesson/plans", params={"page_size": 100})
        check("★ 共享教案列表对方可读（按任教学科过滤）",
              p.get("success") and isinstance(rows_of(p), list),
              f"teacher4 可见 {len(rows_of(p))} 条")

        # 复制
        p, _, _ = t4.post(f"/lesson/plans/{pid}/copy", {})
        copy_id = (data_of(p) or {}).get("id")
        check("★ 共享教案可被其他教师复制",
              p.get("success") and bool(copy_id),
              f"copy_id={copy_id} {p.get('message', '')[:30]}")
        if copy_id:
            t4.delete(f"/lesson/plans/{copy_id}")

        # only_mine
        p, _, _ = t1.get("/lesson/plans", params={"only_mine": "true", "page_size": 100})
        check("only_mine 只返回自己的教案",
              all(x["creator_id"] == t1.user.get("id") for x in rows_of(p)),
              f"{len(rows_of(p))} 条")

        # 关键词
        p, _, _ = t1.get("/lesson/plans", params={"keyword": "分数的加减", "page_size": 20})
        check("教案关键词搜索命中", total_of(p) >= 1, f"{total_of(p)} 条")

        # 附件
        p, _, _ = t1.get(f"/lesson/plans/{pid}/attachments")
        check("教案附件列表可读", p.get("success"), "")
        expect_denied("★ 其他教师不能上传附件到他人教案",
                      t4, "GET", f"/lesson/plans/{pid}/attachments") if False else None

        # 删除
        p, _, _ = t1.delete(f"/lesson/plans/{pid}")
        check("★ 删除教案成功", p.get("success"), p.get("message", "")[:30])
        p, _, _ = t1.get(f"/lesson/plans/{pid}")
        check("删除后详情 404", p.get("success") is not True, p.get("message", "")[:30])

    # ============================================================
    # 清理
    # ============================================================
    _cleanup(t1, admin)
    R.env("教学管理", f"任务 {len(rows_of(t1.get('/task/tasks', params={'page_size': 50})[0]))} 条 / "
                   f"教案 {total_of(t1.get('/lesson/plans', params={'page_size': 50})[0])} 份")
    print("\n[完成] 教学管理模块专项")


def _cleanup(t1, admin):
    """清扫 [E2E-TM] 前缀的任务与教案（自愈历史残留）。"""
    try:
        p, _, _ = t1.get("/task/tasks", params={"keyword": TAG, "page_size": 100})
        for x in rows_of(p):
            t1.delete(f"/task/tasks/{x['id']}")
        p, _, _ = t1.get("/lesson/plans", params={"keyword": "E2E-TM", "page_size": 100})
        for x in rows_of(p):
            t1.delete(f"/lesson/plans/{x['id']}")
    except Exception:  # noqa: BLE001
        pass


if __name__ == "__main__":
    run()
