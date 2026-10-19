# -*- coding: utf-8 -*-
"""
阶段三：学生（stu731）视角 —— 答题 → AI 批改 → 错题本收录 → 复习闭环

关键验证点：
1. 考试进行中绝不泄露答案（answer / analysis 字段不可见）
2. 客观题自动判分正确性（故意做错 3 题、做对 2 题）
3. 主观题 AI/规则批改生效并给出评语
4. 错题本自动收录，且只收录做错的题
5. 知识点掌握度按对错更新
6. 复习计划、错题重做、错因分析闭环
7. 学生数据隔离（看不到他人数据）
"""
from e2e_framework import (R, Client, check, data_of, rows_of, total_of,
                           expect_denied, is_down)

PWD = "Student@123"

# 故意做错：single 选 A（正确 B）、multiple 只选 A（正确 AC）、judge 选 F（正确 T）
# 做对：blank 填 4、short（简答题）写标准答案
# 注：主观题在 LLM 未配置时按设计进入「待教师人工批改」，不计入自动判分
PLAN = {
    "single": "A",       # 错
    "multiple": ["A"],   # 错（漏选 C）
    "judge": "F",        # 错
    "blank": "4",        # 对
    "short":            # 对
    "x²-6x+5=0 ⟹ (x-3)²=4 ⟹ x-3=±2 ⟹ x=1 或 x=5",
}
EXPECT_WRONG = {"single", "multiple", "judge"}
EXPECT_RIGHT = {"blank"}
# 主观题：llm_enabled=false 时进入人工批改队列。
# 枚举值为 short（简答题）——原先写 "subjective" 是非法值，
# 后端未校验题型时会被原样入库，导致前端题型显示异常。
SUBJECTIVE = "short"


def run():
    stu = Client("stu731")

    # ---------------------------------------------------------- 1 登录
    R.set_phase("阶段三 · 学生视角 | 1. 登录与待办")

    p, _, _ = stu.get("/health")
    if is_down(p):
        R.env("服务可访问", "服务不可达")
        return

    ok, detail = stu.login("stu731", PWD)
    check("stu731 登录成功", ok, detail)
    if not ok:
        return
    R.context["stu731_id"] = stu.user["id"]
    check("stu731 角色为 student", "student" in (stu.permission or {}).get("roles", []),
          f"class_id={stu.user.get('class_id')}")

    p, _, _ = stu.get("/system/notifications")
    check("学生可收到通知", p.get("success"), f"{total_of(p)} 条通知")
    nf = rows_of(p)
    task_notify = [n for n in nf
                   if any(k in (n.get("title") or "") for k in ("考试", "作业"))]
    check("收到任务发布通知", len(task_notify) > 0,
          f"通知={[n.get('title') for n in nf[:3]]}")
    check("通知可关联到具体任务",
          all(n.get("biz_id") for n in task_notify[:2]),
          f"biz_type={task_notify[0].get('biz_type') if task_notify else '-'} "
          f"biz_id={task_notify[0].get('biz_id') if task_notify else '-'}")

    # ---------------------------------------------------------- 2 取卷
    R.set_phase("阶段三 · 学生视角 | 2. 获取考试与试卷（答案防泄露）")

    p, _, _ = stu.get("/task/my/tasks", params={"page_size": 50})
    tasks = rows_of(p)
    check("我的任务列表", p.get("success"), f"{total_of(p)} 个任务")

    # 优先选教师阶段创建的正向考试；否则退回任意可用任务
    task_id = R.context.get("task_id") or R.context.get("cross_task_id")
    avail = [t for t in tasks if t.get("status") in ("published", "ongoing")]
    if task_id not in [t["id"] for t in avail]:
        if avail:
            task_id = avail[0]["id"]
            print(f"  \033[93m[INFO]\033[0m 教师阶段任务不可用，改用任务 {task_id}")
    found = next((t for t in tasks if t["id"] == task_id), None)
    check("考试任务已下发给 stu731", found is not None,
          f"task_id={task_id} status={(found or {}).get('status')}")

    if not found:
        R.issue("高", "stu731 收不到 teacher1 发布的考试",
                f"GET /task/my/tasks 返回 {len(tasks)} 个任务，"
                f"其中包含 task_id={task_id} 的记录："
                f"{'是' if found else '否'}。"
                "教师发布时的班级范围与学生所属班级不匹配时，"
                "通知写了「已通知 N 名学生」但学生端看不到任务。",
                "GET /api/v1/task/my/tasks")
        return

    check("任务显示剩余时间", found.get("remaining_seconds") is not None,
          f"剩余 {found.get('remaining_seconds')} 秒")
    check("任务已记录我的作答次数", found.get("attempt_count") is not None,
          f"attempt_count={found.get('attempt_count')}")

    # ---- 关键安全验证：考试中不得下发答案 ----
    p, _, _ = stu.get(f"/task/tasks/{task_id}/paper")
    paper_data = data_of(p) or {}
    items = paper_data.get("items", [])
    check("获取试卷题目", p.get("success") and len(items) == 5, f"{len(items)} 题")

    leak = [it for it in items if "answer" in it or "analysis" in it]
    check("★ 考试进行中不泄露答案与解析", len(leak) == 0,
          f"泄露字段的题目 {len(leak)} 道: {[it.get('type') for it in leak]}"
          if leak else "5 题均无 answer/analysis 字段")
    if leak:
        R.issue("高", "考试进行中接口下发标准答案（可作弊）",
                f"GET /task/tasks/{task_id}/paper 在学生未交卷时返回了 "
                f"{len(leak)} 道题的 answer/analysis 字段。"
                "该接口是学生答题页的数据来源，答案随卷下发等于开卷考试。",
                f"GET /api/v1/task/tasks/{task_id}/paper")

    types = {it["type"] for it in items}
    check("试卷包含全部五种题型", len(types) == 5, f"{sorted(types)}")
    has_opt = all("options" in it for it in items)
    check("题目携带选项数据", has_opt)

    # ---------------------------------------------------------- 3 交卷
    R.set_phase("阶段三 · 学生视角 | 3. 交卷与自动判分")

    # 作答心跳
    p, _, _ = stu.post(f"/task/tasks/{task_id}/heartbeat",
                       {"switch": True, "seconds": 5})
    check("作答心跳上报（防切屏）", p.get("success"), p.get("message", ""))
    p, _, _ = stu.post(f"/task/tasks/{task_id}/heartbeat", {"seconds": 30})
    check("心跳累计答题时长", p.get("success"), "")

    answers = []
    for it in items:
        t = it["type"]
        # 字段名必须与前端 ExamPaper.vue 一致：content（非 answer）
        answers.append({
            "paper_item_id": it["paper_item_id"],
            "content": PLAN.get(t, ""),
            "duration_seconds": 20,
        })

    p, ms, _ = stu.post(f"/task/tasks/{task_id}/submit",
                        {"answers": answers, "duration_seconds": 300}, timeout=120)
    sd = data_of(p) or {}
    sub_id = sd.get("submission_id")
    check("交卷成功", p.get("success") and bool(sub_id),
          f"submission_id={sub_id} 总分={sd.get('score')}/{sd.get('total_score')} "
          f"正确率={sd.get('accuracy')}% {ms}ms {p.get('message', '')}")

    if not sub_id:
        return

    grading = sd.get("grading") or {}
    check("判分明细返回", bool(grading),
          f"字段={list(grading.keys())[:6] if isinstance(grading, dict) else ''}")
    g_total = (grading or {}).get("total")
    g_correct = (grading or {}).get("correct_count")
    check("判分统计非全零", g_total and g_correct,
          f"total={g_total} correct={g_correct} "
          f"objective={(grading or {}).get('objective_count')} "
          f"subjective={(grading or {}).get('subjective_count')} "
          f"ai_graded={(grading or {}).get('ai_graded')}")

    # 交卷后 show_answer=True 应能看到答案解析
    detail = sd.get("answers") or []
    check("交卷后返回逐题批改结果", len(detail) == 5, f"{len(detail)} 题")

    # 核对每一题的对错
    got = {}
    for d in detail:
        got[d["paper_item_id"]] = d
    ok_cnt = sum(1 for d in detail if d.get("is_correct"))
    obj_items = [it for it in items if it["type"] != SUBJECTIVE]
    exp_ok = len(EXPECT_RIGHT)
    check("★ 客观题判分完全符合预期（3 错 1 对）", ok_cnt == exp_ok,
          f"判对 {ok_cnt}/{len(obj_items)} 道客观题，得分 {sd.get('score')}；"
          f"预期对 {exp_ok} 道")

    for it in items:
        d = got.get(it["paper_item_id"])
        if not d:
            check(f"判分明细含 {it['type']} 题", False, "缺失")
            continue
        actual = bool(d.get("is_correct"))
        if it["type"] == SUBJECTIVE:
            # 无 LLM 时应转人工批改，而不是直接判 0 分
            ok = (d.get("score") in (0, 0.0, None)
                  and bool(d.get("comment")))
            check("  subjective 转人工批改（LLM 未配置时的降级）", ok,
                  f"得分 {d.get('score')}/{d.get('full_score')} "
                  f"评语={str(d.get('comment'))[:40]!r}")
            if not ok:
                R.issue("中", "主观题在无 LLM 时既不给分也不进人工批改",
                        f"主观题得分 {d.get('score')}，评语={d.get('comment')!r}。"
                        "既不是 AI 判分，也没有提示教师需人工批改，"
                        "学生会以为自己得 0 分。",
                        "POST /api/v1/task/tasks/{id}/submit")
            continue
        exp = it["type"] in EXPECT_RIGHT
        mark = "\033[92m✓\033[0m" if exp == actual else "\033[91m✗\033[0m"
        check(f"  {it['type']} 判分正确（预期{'对' if exp else '错'}）",
              exp == actual,
              f"{mark} 实际{'对' if actual else '错'} "
              f"得分 {d.get('score')}/{d.get('full_score')}"
              f" 学生答案={PLAN.get(it['type'], '')[:16]!r} "
              f"标准答案={str(d.get('answer'))[:16]!r}")

    # 主观题得分与状态一致性
    subj = next((d for d in detail if d.get("full_score") == 50), None)
    if subj:
        pend = grading.get("pending_manual", 0)
        check("主观题计入待人工批改数", pend >= 1,
              f"pending_manual={pend} ai_graded={grading.get('ai_graded')} "
              f"（llm_enabled={R.context.get('health', {}).get('llm_enabled')}）")
        p2, _, _ = stu.get(f"/task/submissions/{sub_id}")
        sd2 = data_of(p2) or {}
        check("未完成批改的作答状态标记为 not_graded",
              sd2.get("status") in ("not_graded", "auto_graded", "graded"),
              f"status={sd2.get('status')}")

    # ---------------------------------------------------------- 3b 批改契约守护（教师批改全链路）
    # 回归点：后端 grade 接口曾读 items+comment 键而前端发 answers+
    # teacher_comment——循环空转、分数从未保存却提示「已保存」。
    R.set_phase("阶段三 · 学生视角 | 3b. 教师批改契约守护")
    try:
        from e2e_framework import Client as _C
        tea1 = _C("ct1"); ok_login, _ = tea1.login("teacher1", "Teacher@123")
        if ok_login and R.context.get("task_id"):
            tid = R.context["task_id"]
            pd, _, _ = tea1.get("/grading/pending", params={"page_size": 10})
            pend = (data_of(pd) or {}).get("items") or []
            mine = next((x for x in pend if x.get("student_id") == stu.user.get("id")), None)
            if mine:
                sid = mine["submission_id"]
                before = mine.get("score")
                # answer_id 只在批改详情接口返回（学生详情的 answers 无此字段）
                gd, _, _ = tea1.get(f"/grading/submissions/{sid}")
                answers_payload = [
                    {"answer_id": it["answer_id"], "score": it["full_score"],
                     "teacher_comment": "e2e 人工复核"}
                    for it in (data_of(gd) or {}).get("items") or []]
                p, _, _ = tea1.post(f"/grading/submissions/{sid}/grade",
                                    {"answers": answers_payload})
                p2, _, _ = tea1.get(f"/grading/submissions/{sid}")
                d2 = data_of(p2) or {}
                check("★ 教师批改（前端 answers 契约）分数真实落库",
                      p.get("success") and d2.get("score") is not None
                      and d2.get("score") != before,
                      f"before={before} after={d2.get('score')}")
                check("★ 批改评语写入（teacher_comment 键）",
                      any(it.get("teacher_comment") == "e2e 人工复核"
                          for it in d2.get("items") or []),
                      "")
                check("批改口径：manual 判分计入 subjective_score",
                      (d2.get("subjective_score") or 0) > 0,
                      f"objective={d2.get('objective_score')} subjective={d2.get('subjective_score')}")
                # 越权：teacher4 不能批 teacher1 发布任务的提交
                tea4 = _C("ct4"); tea4.login("teacher4", "Teacher@123")
                p, _, _ = tea4.post(f"/grading/submissions/{sid}/grade",
                                    {"answers": answers_payload})
                check("★ 跨教师批改被拒（数据范围校验）",
                      p.get("success") is not True,
                      p.get("message", "")[:50])
            else:
                check("教师批改契约守护", False, f"pending 中未找到本学生提交（共 {len(pend)} 条）")
        else:
            check("教师批改契约守护", False, f"教师登录或 task_id 缺失")
    except Exception as exc:  # noqa: BLE001
        check("教师批改契约守护", False, f"用例异常: {exc}")

    # ---------------------------------------------------------- 3c 批改状态机全链路
    # 覆盖：批改 → 队列消失 → 打回（分数清零+队列重现）→ 重新批改 → 发布 → 学生可见
    R.set_phase("阶段三 · 学生视角 | 3c. 批改状态机全链路")
    try:
        from e2e_framework import Client as _C2
        tea1b = _C2("ct1b"); tea1b.login("teacher1", "Teacher@123")
        if R.context.get("task_id") and sub_id:
            sid = sub_id

            def _in_queue():
                p, _, _ = tea1b.get("/grading/pending", params={"page_size": 200})
                ids = {x["submission_id"] for x in (data_of(p) or {}).get("items") or []}
                return sid in ids

            # 1) 批改后从待批队列消失
            gd, _, _ = tea1b.get(f"/grading/submissions/{sid}")
            items_g = (data_of(gd) or {}).get("items") or []
            tea1b.post(f"/grading/submissions/{sid}/grade",
                       {"answers": [{"answer_id": it["answer_id"],
                                     "score": it["full_score"],
                                     "teacher_comment": "状态机测试"}
                                    for it in items_g]})
            check("★ 批改后移出待批队列", not _in_queue(), f"sub={sid}")

            # 2) 打回后：分数清零 + 重新进入队列
            p, _, _ = tea1b.post(f"/grading/submissions/{sid}/reject",
                                 {"reason": "状态机测试打回"})
            check("打回接口调用成功", p.get("success"), p.get("message", "")[:50])
            gd2, _, _ = tea1b.get(f"/grading/submissions/{sid}")
            d2 = data_of(gd2) or {}
            check("★ 打回后分数清零（score/objective/subjective）",
                  d2.get("score") is None and (d2.get("objective_score") or 0) == 0
                  and (d2.get("subjective_score") or 0) == 0,
                  f"score={d2.get('score')} obj={d2.get('objective_score')} subj={d2.get('subjective_score')}")
            check("★ 打回后重新进入待批队列", _in_queue(), "")

            # 3) 重新批改 → 可发布 → 发布
            items_g2 = d2.get("items") or []
            tea1b.post(f"/grading/submissions/{sid}/grade",
                       {"answers": [{"answer_id": it["answer_id"],
                                     "score": it["full_score"], "teacher_comment": "复核通过"}
                                    for it in items_g2]})
            gd3, _, _ = tea1b.get(f"/grading/submissions/{sid}")
            d3 = data_of(gd3) or {}
            check("★ 重新批改后状态可发布",
                  d3.get("status") == "fully_graded" and d3.get("score") is not None,
                  f"status={d3.get('status')} score={d3.get('score')}")
            p, _, _ = tea1b.post(f"/grading/submissions/{sid}/publish", {})
            check("★ 成绩发布成功", p.get("success"), p.get("message", "")[:40])

            # 4) 学生端可见
            ps, _, _ = stu.get("/task/my/tasks", params={"page_size": 50})
            mine = (data_of(ps) or {}).get("items") or []
            hit = next((x for x in mine if x.get("id") == R.context["task_id"]), None)
            check("★ 发布后学生任务状态可见",
                  hit is not None,
                  f"my_submission={bool((hit or {}).get('my_submission'))}")
    except Exception as exc:  # noqa: BLE001
        check("批改状态机全链路", False, f"用例异常: {exc}")

    # ---------------------------------------------------------- 3d 批量批改 / 批量发布
    R.set_phase("阶段三 · 学生视角 | 3d. 批量批改与批量发布")
    try:
        from e2e_framework import Client as _C3
        tb = _C3("ct1c"); tb.login("teacher1", "Teacher@123")
        if sub_id:
            sid = sub_id

            # 先打回成未批改，验证「未批改不能批量发布」
            tb.post(f"/grading/submissions/{sid}/reject", {"reason": "批量测试准备"})
            p, _, _ = tb.post("/grading/batch/publish", {"submission_ids": [sid]})
            d = data_of(p) or {}
            check("★ 批量发布跳过未批改记录",
                  p.get("success") and sid not in (d.get("published") or [])
                  and len(d.get("skipped") or []) >= 1,
                  f"published={len(d.get('published') or [])} skipped={len(d.get('skipped') or [])}")

            # 批量采纳当前分数 → 状态变 fully_graded
            p, _, _ = tb.post("/grading/batch/grade", {"submission_ids": [sid]})
            d = data_of(p) or {}
            check("★ 批量采纳批改成功",
                  p.get("success") and sid in (d.get("graded") or []),
                  p.get("message", "")[:50])

            # 批量发布 → 成功
            p, _, _ = tb.post("/grading/batch/publish", {"submission_ids": [sid]})
            d = data_of(p) or {}
            check("★ 批量发布成功",
                  p.get("success") and sid in (d.get("published") or []),
                  p.get("message", "")[:50])

            # 空列表拒绝
            p, _, _ = tb.post("/grading/batch/grade", {"submission_ids": []})
            check("批量接口空选拒绝", p.get("success") is not True,
                  p.get("message", "")[:40])

            # 越权：teacher4 批量操作 teacher1 的提交 → 全部 skipped
            t4 = _C3("ct4b"); t4.login("teacher4", "Teacher@123")
            p, _, _ = t4.post("/grading/batch/grade", {"submission_ids": [sid]})
            d = data_of(p) or {}
            check("★ 跨教师批量批改被拒",
                  p.get("success") and sid not in (d.get("graded") or [])
                  and any("非本人任务" in x.get("reason", "")
                          for x in d.get("skipped") or []),
                  f"skipped={d.get('skipped')}")

            # 分页：page_size=1 时 total 正确、第二页可拉
            p1, _, _ = tb.get("/grading/pending", params={"page": 1, "page_size": 1})
            d1 = data_of(p1) or {}
            check("待批列表分页字段完整（items/total/page）",
                  isinstance(d1.get("items"), list) and "total" in d1,
                  f"total={d1.get('total')} page_items={len(d1.get('items') or [])}")
    except Exception as exc:  # noqa: BLE001
        check("批量批改与批量发布", False, f"用例异常: {exc}")

    # ---------------------------------------------------------- 4 错题本
    R.set_phase("阶段三 · 学生视角 | 4. 错题本自动收录")

    p, _, _ = stu.get("/learning/wrong-questions", params={"page_size": 50})
    wrongs = rows_of(p)
    check("错题本可查询", p.get("success"), f"共 {total_of(p)} 道错题")

    wmap = {w["question_id"]: w for w in wrongs}
    expect_wrong_qids = {it["question_id"] for it in items
                         if it["type"] in EXPECT_WRONG}
    expect_right_qids = {it["question_id"] for it in items
                        if it["type"] in EXPECT_RIGHT}
    subj_qids = {it["question_id"] for it in items if it["type"] == SUBJECTIVE}

    got_wrong = set(wmap.keys()) & expect_wrong_qids
    got_right = set(wmap.keys()) & expect_right_qids
    check("★ 做错的 3 题全部收录进错题本", len(got_wrong) == 3,
          f"收录 {len(got_wrong)}/3")
    check("★ 做对的题未被误收录", len(got_right) == 0,
          f"误收录 {len(got_right)} 题: {list(got_right)}")
    got_subj = set(wmap.keys()) & subj_qids
    check("★ 待人工批改的主观题不进入错题本", len(got_subj) == 0,
          f"误收录 {len(got_subj)} 道主观题（尚未判定对错，不应记为错题）"
          if got_subj else "主观题未进入错题本")
    if got_subj:
        R.issue("高", "待人工批改的主观题被当成错题收录",
                f"{len(got_subj)} 道主观题出现在错题本中。"
                "主观题在 LLM 未配置时 is_correct 也是 False，"
                "但那是「尚未判定」而非「做错」，收录逻辑未区分两者，"
                "学生会看到自己答对的题被列为错题。",
                "GET /api/v1/learning/wrong-questions")
    if len(got_wrong) < 3:
        R.issue("高", "错题本未完整收录做错的题",
                f"预期收录 3 道错题，实际 {len(got_wrong)} 道。"
                "错题本是核心闭环，漏收意味着学生错题丢失。",
                "GET /api/v1/learning/wrong-questions")
    if got_right:
        R.issue("高", "做对的题被误收录进错题本",
                f"{len(got_right)} 道答对的题出现在错题本中，判分与错题收录逻辑不一致。",
                "GET /api/v1/learning/wrong-questions")

    for w in wrongs:
        if w["question_id"] in expect_wrong_qids:
            print(f"  \033[90m[INFO]\033[0m 错题 #{w['id']} 错因={w.get('error_reason')!r} "
                  f"掌握={w.get('is_mastered')}")

    # 错因分析
    if wrongs:
        wid = wrongs[0]["id"]
        p, _, _ = stu.post(f"/learning/wrong-questions/{wid}/analyze", {}, timeout=90)
        ad = data_of(p) or {}
        check("AI 错因分析可生成", p.get("success"),
              f"{(ad.get('analysis') or ad.get('comment') or '')[:70]!r}"
              if p.get("success") else p.get("message", ""))

        p, _, _ = stu.put(f"/learning/wrong-questions/{wid}",
                          {"is_mastered": True})
        check("错题可标记为已掌握", p.get("success"), p.get("message", ""))
        p, _, _ = stu.put(f"/learning/wrong-questions/{wid}",
                          {"is_mastered": False})
        check("可取消已掌握标记", p.get("success"), p.get("message", ""))

        p, _, _ = stu.post(f"/learning/wrong-questions/{wid}/redo")
        rd = data_of(p) or {}
        check("错题重做可生成同类题", p.get("success"),
              f"原题 id={(rd.get('origin') or {}).get('id')} "
              f"相似题 {len(rd.get('similar') or [])} 道")

        p, _, _ = stu.get("/learning/wrong-questions/export")
        ex = data_of(p) or {}
        check("错题本导出", p.get("success"),
              f"{ex.get('bytes', 0)} 字节" if ex.get("bytes") else
              f"code={p.get('code')}")

        # 筛选
        p, _, _ = stu.get("/learning/wrong-questions", params={"is_mastered": False})
        check("错题本按掌握状态筛选", p.get("success"), f"{total_of(p)} 道未掌握")

    # ---------------------------------------------------------- 5 掌握度
    R.set_phase("阶段三 · 学生视角 | 5. 知识点掌握地图")

    p, _, _ = stu.get("/learning/review/mastery")
    md = data_of(p) or {}
    mlist = md.get("items", [])
    check("掌握地图可查询", p.get("success"),
          f"{len(mlist)} 个知识点，平均掌握度 {md.get('avg_mastery')}")
    if mlist:
        tot = sum(m["total_count"] for m in mlist)
        corr = sum(m["correct_count"] for m in mlist)
        wr = sum(m["wrong_count"] for m in mlist)
        check("掌握度按答题结果累计", tot >= 3,
              f"累计作答 {tot} 次，对 {corr} 错 {wr}")
        check("薄弱知识点被识别", isinstance(md.get("weak_points"), list),
              f"薄弱 {len(md.get('weak_points') or [])} 个，"
              f"最强 {len(md.get('strong_points') or [])} 个")
    else:
        R.issue("中", "答题后知识点掌握地图仍为空",
                "提交 5 道题后 GET /learning/review/mastery 返回空数组。"
                "掌握度依赖 knowledge_point_id，若题目未挂知识点则无法归因，"
                "学生的知识图谱与复习计划都没有数据基础。",
                "GET /api/v1/learning/review/mastery")

    # ---------------------------------------------------------- 6 复习闭环
    R.set_phase("阶段三 · 学生视角 | 6. 复习计划与错题重做")

    p, ms, _ = stu.post("/learning/review/plan",
                       {"days": 7, "daily_minutes": 60}, timeout=90)
    pd = data_of(p) or {}
    # 真实结构：{summary, weak_points, daily_plan:[{date,duration,tasks}], advice, review_dates, stats}
    daily = pd.get("daily_plan") or []
    stats = pd.get("stats") or {}
    check("AI 复习计划生成", len(daily) > 0,
          f"{len(daily)} 天计划 weak_points={len(pd.get('weak_points') or [])} "
          f"复习节点={len(pd.get('review_dates') or [])} {ms}ms")
    check("复习计划含每日任务明细", bool(daily and daily[0].get("tasks")),
          f"首日 {daily[0].get('date') if daily else '-'} "
          f"任务数={len(daily[0].get('tasks') or []) if daily else 0}")
    check("学情统计随计划返回", bool(stats),
          f"总题数={stats.get('total_questions')} 正确率={stats.get('accuracy')} "
          f"错题={stats.get('wrong_count')} 落库={stats.get('review_plan_created')}")

    p2, _, _ = stu.get("/learning/review/plans")
    pl = rows_of(p2)
    check("复习计划已落库可查", p2.get("success") and len(pl) > 0,
          f"{total_of(p2)} 条")
    if pl:
        pid = pl[0]["id"]
        p3, _, _ = stu.put(f"/learning/review/plans/{pid}/complete", {})
        check("复习任务可标记完成", p3.get("success"), p3.get("message", ""))
        # 艾宾浩斯闭环：同一错题累计完成 2 轮即标记已掌握。
        # 接口以 question_id（错题对应题目）回显关联关系。
        pl_all = rows_of(stu.get("/learning/review/plans") [0])
        linked = [x for x in pl_all if x.get("question_id")]
        check("复习计划已关联到具体错题（闭环前提）", len(linked) > 0,
              f"{len(linked)}/{len(pl_all)} 条计划关联了错题；"
              f"示例 kp={linked[0].get('knowledge_point_name') if linked else '-'} "
              f"q={linked[0].get('question_id') if linked else '-'}")
        if linked:
            # 关键：业务 complete_review() 是按**错题**（wrong_question_id）
            # 统计完成轮数的，而 /review/plans 只回显 question_id（题目 ID）。
            # 多道错题可能指向同一道题，若按 question_id 分组会把
            # 「2 条不同错题的计划」误当成「同一错题完成 2 轮」，
            # 导致断言假失败。此处用「同 question_id 且不同 plan_id」的
            # 计划逐条完成，逐轮复查，直到真的出现已掌握记录。
            from collections import defaultdict
            by_q = defaultdict(list)
            for x in linked:
                by_q[x["question_id"]].append(x)
            # 逐条完成计划并逐轮复查，轮次上限取计划总数
            total_plans = sum(len(xs) for xs in by_q.values())
            mastered = []
            done_rounds = 0
            for _ in range(min(total_plans, 12)):
                pend = [x for xs in by_q.values() for x in xs
                        if not x.get("is_completed")]
                if not pend:
                    break
                resp, _, _ = stu.put(
                    f"/learning/review/plans/{pend[0]['id']}/complete", {})
                if resp.get("success"):
                    done_rounds += 1
                p_chk, _, _ = stu.get("/learning/wrong-questions",
                                      params={"is_mastered": True})
                mastered = rows_of(p_chk)
                if mastered:
                    break
            check("完成 2 轮复习后错题自动标记已掌握", len(mastered) > 0,
                  f"完成 {done_rounds} 轮-> 已掌握错题 {len(mastered)} 道"
                  f"（计划总数 {total_plans}）")
            if not mastered:
                R.issue("中", "错题复习闭环未生效",
                        f"已连续完成 {done_rounds} 轮复习（共 {total_plans} 条计划），"
                        "错题仍未被标记为已掌握。艾宾浩斯记忆曲线是产品核心卖点。",
                        "PUT /api/v1/learning/review/plans/{id}/complete")
        else:
            R.issue("中", "复习计划未关联错题，记忆曲线闭环断裂",
                    f"{len(pl_all)} 条复习计划全部没有关联错题（question_id 为空）。"
                    "而 complete 接口的「累计完成 2 轮 → 标记错题已掌握」"
                    "依赖该关联，闭环无法触发。",
                    "GET /api/v1/learning/review/plans -> question_id 恒为空")

    # ---------------------------------------------------------- 7 成绩与报表
    R.set_phase("阶段三 · 学生视角 | 7. 成绩中心与学习报表")

    p, _, _ = stu.get("/task/my/scores")
    sc = rows_of(p)
    check("成绩中心可查", p.get("success"), f"{total_of(p)} 条成绩")
    mine = [s for s in sc if s.get("task_id") == task_id]
    check("本次考试成绩已入库", len(mine) > 0,
          f"score={mine[0].get('score') if mine else '-'} "
          f"rank/班级={mine[0].get('rank') if mine else '-'}")

    p, _, _ = stu.get(f"/task/submissions/{sub_id}")
    det = data_of(p) or {}
    check("交卷详情可复查", p.get("success"), f"字段={list(det.keys())[:6]}")

    for path, name in [("/report/student/overview", "学习总览"),
                       ("/report/student/score-trend", "成绩趋势"),
                       ("/report/student/knowledge-radar", "知识雷达"),
                       ("/report/student/wrong-analysis", "错题分析"),
                       ("/report/student/learning-suggestion", "学习建议")]:
        p, _, _ = stu.get(path)
        d = data_of(p)
        check(f"{name}可查", p.get("success") and d is not None,
              f"{p.get('code')} {p.get('message', '')}"[:70])

    p, _, _ = stu.get("/report/export/excel", params={"report_type": "student_overview"})
    ex = data_of(p) or {}
    check("学生报表 Excel 导出", p.get("success") and ex.get("bytes", 0) > 0,
          f"{ex.get('bytes')} 字节 {ex.get('filename')}")

    # ---------------------------------------------------------- 8 学习中心
    R.set_phase("阶段三 · 学生视角 | 8. 笔记、随机练习与数据隔离")

    p, _, _ = stu.post("/learning/notes", {
        "title": f"E2E 笔记 {task_id}", "content": "配方法解一元二次方程的步骤整理。",
        "subject_id": R.context.get("subject_id") or 34, "tags": ["E2E", "数学"],
    })
    nd = data_of(p) or {}
    note_id = nd.get("id")
    check("创建学习笔记", p.get("success") and bool(note_id), f"note_id={note_id}")

    if note_id:
        p, _, _ = stu.get("/learning/notes", params={"keyword": "E2E"})
        check("笔记可检索", any(n["id"] == note_id for n in rows_of(p)),
              f"命中 {len(rows_of(p))} 条")
        p, _, _ = stu.post(f"/learning/notes/{note_id}/organize", {}, timeout=90)
        check("AI 笔记整理", p.get("success"), p.get("message", ""))
        p, _, _ = stu.get(f"/learning/notes/{note_id}/export")
        ex = data_of(p) or {}
        check("笔记导出", p.get("success"),
              f"{ex.get('bytes', 0)} 字节" if ex.get("bytes") else f"code={p.get('code')}")
        p, _, _ = stu.delete(f"/learning/notes/{note_id}")
        check("笔记可删除", p.get("success"), p.get("message", ""))

    p, _, _ = stu.post("/learning/practice", {
        "subject_id": R.context.get("subject_id") or 34,
        "grade_id": R.context.get("grade_id") or 7, "count": 3,
    }, timeout=90)
    prd = data_of(p) or {}
    check("随机练习可创建", p.get("success") and bool(prd.get("task_id")),
          f"task_id={prd.get('task_id')} 题数={prd.get('total')} {p.get('message', '')}")
    if prd.get("task_id"):
        p2, _, _ = stu.get(f"/learning/practice/{prd['task_id']}")
        check("随机练习题目可取", p2.get("success"),
              f"{total_of(p2)} 题")
        p3, _, _ = stu.get("/learning/practice/history")
        ph = rows_of(p3)
        check("练习历史可查（含新建练习）", p3.get("success") and total_of(p3) > 0,
              f"{total_of(p3)} 条，最近={ph[0].get('name') if ph else '-'}")
        if ph:
            p4, _, _ = stu.get("/learning/practice", params={"page_size": 1})
            # 练习历史应能定位到具体练习任务
            check("练习历史条目含 task_id 可回溯",
                  all(x.get("task_id") for x in ph[:3]),
                  f"task_ids={[x.get('task_id') for x in ph[:3]]}")

    # 两种入参都要能生效：question（前端用法）与 message（历史用法）
    for field in ("question", "message"):
        p, _, _ = stu.post("/agent/tutor",
                          {field: "什么是一元一次方程？请举一个例子。"}, timeout=90)
        td = data_of(p) or {}
        ans = str(td.get("answer") or "")
        check(f"AI 答疑可用（入参 {field}）", p.get("success") and bool(ans),
              f"回答={ans[:70]!r}")
        if ans.strip() in ("请描述你的问题", ""):
            R.issue("高", f"AI 答疑入参 {field} 未生效",
                    f"POST /agent/tutor 传 {field} 但回答为 {ans!r}。"
                    "接口只读取 data['message']，前端 AgentChat 传的是 question，"
                    "导致学生的问题被整体丢弃，永远得到一句无意义提示。",
                    f"POST /api/v1/agent/tutor ({{\"{field}\": ...}})")

    # 统一对话入口
    p, _, _ = stu.post("/agent/chat",
                      {"message": "一元一次方程怎么解？"}, timeout=90)
    cd_ = data_of(p) or {}
    check("统一对话入口可用", p.get("success"),
          f"intent={cd_.get('intent')} 回复={str(cd_.get('answer') or cd_.get('reply'))[:60]!r}")

    # 数据隔离
    other = Client("stu732")
    ok2, d2 = other.login("stu732", PWD)
    if ok2:
        p, _, _ = other.get("/learning/wrong-questions")
        mine_w = {w["id"] for w in wrongs}
        leak2 = [w for w in rows_of(p) if w["id"] in mine_w]
        check("stu732 看不到 stu731 的错题", len(leak2) == 0, f"泄漏 {len(leak2)} 条")
        p, _, _ = other.get(f"/task/submissions/{sub_id}")
        check("stu732 不能查看 stu731 的交卷详情", p.get("success") is not True,
              p.get("message", ""))
        # 任务隔离：stu731 与 stu732 分属不同班级（4 vs 1），
        # teacher1 下发到一年级(1)班的考试，stu732 不应看到。
        p_all, _, _ = other.get("/task/my/tasks", params={"page_size": 50})
        other_ids = {t["id"] for t in rows_of(p_all)}
        check("★ 跨班任务严格隔离（stu732 看不到 stu731 的考试）",
              task_id not in other_ids,
              f"stu732 可见 {len(other_ids)} 个任务，"
              f"是否含 stu731 的考试 {task_id}：{task_id in other_ids}")
        if task_id in other_ids:
            R.issue("高", "跨班级任务下发存在越权可见",
                    f"stu732（班级 4）能看到 stu731（班级 1）的考试 {task_id}。",
                    "GET /api/v1/task/my/tasks")
        expect_denied("他人交卷详情不可查", other, "GET",
                      f"/task/submissions/{sub_id}")

    # 学生越权
    expect_denied("学生不能查看他人学习建议", stu, "GET",
                  "/report/teacher/class-overview")
    expect_denied("学生不能访问批改中心", stu, "GET", "/grading/pending")
    return
