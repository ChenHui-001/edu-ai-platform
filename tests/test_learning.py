# -*- coding: utf-8 -*-
"""阶段四 · 学习中心（学生端）端到端测试。

覆盖学习中心 9 大功能域：随机练习 / 错题本 / 智能复习 / 学习笔记 /
收藏夹 / 自主组卷 / 学习目标打卡 / 学习路径 / 知识闪卡。
另含 2026-10-16 修复项的回归用例：
  - /learning/practice/{id} 越权（未发布考试题目泄露）→ 404
  - /learning/practice 缺 subject_id → 400（原 KeyError 500）
  - count / limit / question_ids 上限 clamp
  - 笔记导出 HTML 转义（存储型 XSS）
  - 打卡 actual_value 负数归零、幂等
依赖：服务可用 + 种子账号（stu731/stu732/stu101/teacher1）。
单独运行：python tests/run_all.py learning
"""
import time

from e2e_framework import R, Client, check, data_of, rows_of, total_of, expect_denied

STU_PWD = "Student@123"


def run():
    stu = Client("stu731")
    peer = Client("stu732")     # 同班（七年级(2)班）：共享笔记对照
    other = Client("stu101")    # 异班（一年级(1)班）：越权对照
    tea = Client("teacher1")

    # ---------------------------------------------------------- 0 登录
    R.set_phase("阶段四 · 学习中心 | 0. 登录")
    ok, d = stu.login("stu731", STU_PWD)
    check("stu731 登录", ok, d)
    if not ok:
        return
    ok2, d2 = peer.login("stu732", STU_PWD)
    check("stu732 登录（同班对照）", ok2, d2)
    ok3, d3 = other.login("stu101", STU_PWD)
    check("stu101 登录（异班对照）", ok3, d3)
    okt, dt = tea.login("teacher1", "Teacher@123")
    check("teacher1 登录（越权对照用）", okt, dt)
    R.context["learning_stu_id"] = stu.user.get("id")

    # ------------------------------------- 0b 前置：确保题库有可用题
    # 测试不依赖既有种子数据 —— 全新库也要能独立跑通。
    #
    # 注意：学科必须用**学生自己年级**的那一条。Subject 的唯一键是
    # (grade_id, name)，「语文」在 1~9 年级各有一条、9 个不同 id。
    # 这里原来硬编码 subject_id=1 / grade_id=1（一年级语文），而 stu731 是
    # 七年级学生 —— 随机练习按学年过滤后必然「该学科在该年级暂无题目」，
    # 3 条用例连带失败。改为按学生 grade_id 动态解析。
    R.set_phase("阶段四 · 学习中心 | 0b. 前置题目（自建）")
    stu_grade = stu.user.get("grade_id") or 7
    subj_list, _, _ = tea.get("/edu/subjects", params={"grade_id": stu_grade})
    subj_items = rows_of(subj_list)
    subj_id = next((s["id"] for s in subj_items
                    if s.get("name") == "语文"), None) or (subj_items[0]["id"] if subj_items else 1)
    R.context["stu_grade_id"] = stu_grade
    R.context["stu_subject_id"] = subj_id
    # 该学科该年级现有题数；不足 6 道就补，保证 count 边界用例有题可抽
    p, _, _ = tea.get("/question/questions",
                      params={"page": 1, "page_size": 1,
                              "subject_id": subj_id, "grade_id": stu_grade})
    have = total_of(p) or 0
    if have < 6:
        tag = f"LC{int(time.time()) % 100000}"
        for i in range(6 - have):
            tea.post("/question/questions", {
                "type": "single", "difficulty": "easy", "score": 5,
                "stem": f"【{tag}】学习中心前置题 {i}: 3+{i}=?",
                "options": [{"key": "A", "text": str(3 + i)}, {"key": "B", "text": "99"},
                            {"key": "C", "text": "0"}, {"key": "D", "text": "1"}],
                "answer": "A", "subject_id": subj_id, "grade_id": stu_grade,
                "knowledge_point_id": None, "bank_type": "public",
            })
        # 已进入此分支说明自建请求已发出且拿到响应，这里仅记录规模信息；
        # 真正的判据是后续"随机练习能否出卷"，故允许 info-only。
        check(f"前置题目已自建（年级 {stu_grade} / 学科 {subj_id}）", True, tag)  # allow-info-only
    else:
        check("题库已有题目（复用现有数据）",
              True, f"total={have} 年级={stu_grade} 学科={subj_id}")

    # ------------------------------------------------- 1 随机练习全流程
    R.set_phase("阶段四 · 学习中心 | 1. 随机练习（全流程）")

    # 1a 缺 subject_id → 应 400（回归：原 KeyError 直接 500）
    p, _, _ = stu.post("/learning/practice", {"count": 3})
    check("★ 缺 subject_id 返回 400 而非 500（回归）",
          p.get("success") is False and "学科" in str(p.get("message", "")),
          f"{p.get('code')} {p.get('message', '')}")

    # 1b count 边界：负数 clamp 到 1；超大 clamp 到 50
    SID = R.context.get("stu_subject_id") or 1
    # 顺带守住跨年级防护：拿**别年级**的学科 id 请求，必须明确拒绝而不是
    # 悄悄抽出一堆该学生做不了的题（这正是曾经的真实缺陷）。
    #
    # ⚠️ 但「拒绝」并非唯一正确结果 —— 后端 `create_practice` 现在的做法是
    # **按学科名回查学生本年级的同名学科并自动纠正**（review.py:219-223），
    # 这样前端传了 distinct 代表 id（指向最低年级）也能正常出卷。所以本用例
    # 不能只认 `success is False`：
    #   - 返回成功 → 必须校验**抽出来的题确实是学生本年级的**（防串题）
    #   - 返回失败 → 必须是明确的「暂无题目」类提示，不能是 500
    # 曾因只认「失败」而在有题的数据集上假失败（CI 全新库里七年级语文有题，
    # 接口正确纠正后返回 200 生成练习 → 用例判 FAIL）。
    other_subj = 1 if SID != 1 else 2
    p, _, sc = stu.post("/learning/practice", {"subject_id": other_subj, "count": 3})
    _d = data_of(p) or {}
    if p.get("success") is True:
        # 纠正成功：拿返回的 task 取题，再用教师端题库按 id 反查 grade_id，
        # 必须全部是学生自己的年级（防「卷面标七年级、实抽一年级题」串题）。
        _tid = _d.get("task_id")
        _pp, _, _ = stu.get(f"/learning/practice/{_tid}") if _tid else ({}, 0, 0)
        _qids = {it.get("question_id")
                 for it in ((data_of(_pp) or {}).get("items") or [])}
        _qp, _, _ = tea.get("/question/questions", params={"page_size": 200})
        _grades = {q.get("grade_id") for q in rows_of(_qp)
                   if q.get("id") in _qids and q.get("grade_id") is not None}
        _mine = R.context.get("stu_grade_id")
        check("★ 跨年级学科 id 被纠正到本年级（不返回别年级题目）",
              bool(_grades) and _grades <= {_mine},
              f"抽到的题年级={sorted(_grades)}，学生年级={_mine}")
    else:
        check("★ 跨年级学科 id 被拒（不返回别年级题目）",
              sc != 500 and "题目" in str(p.get("message", "")),
              f"{p.get('code')} {p.get('message', '')[:40]}")

    p, _, _ = stu.post("/learning/practice", {"subject_id": SID, "count": -5})
    d1 = data_of(p) or {}
    check("count=-5 被 clamp（练习生成成功且 ≥1 题）",
          p.get("success") and (d1.get("total") or 0) >= 1,
          f"total={d1.get('total')} {p.get('message', '')}")
    p, _, _ = stu.post("/learning/practice", {"subject_id": SID, "count": 999})
    d2 = data_of(p) or {}
    check("count=999 被 clamp 至 ≤50",
          p.get("success") and 0 < (d2.get("total") or 0) <= 50,
          f"total={d2.get('total')}")
    task_id = d2.get("task_id")

    # 1c 取题 + 交卷（故意答错，制造错题供错题本用例使用）
    if task_id:
        p, _, _ = stu.get(f"/learning/practice/{task_id}")
        paper = data_of(p) or {}
        items = paper.get("items") or []
        check("练习取题成功且不含答案字段",
              p.get("success") and len(items) > 0
              and all("answer" not in it and "analysis" not in it for it in items),
              f"{len(items)} 题")
        # 交卷必须带 paper_item_id（阅卷按卷面题目定位）；content 故意填错制造错题
        answers = [{"paper_item_id": it["paper_item_id"], "content": "ZZ_wrong"}
                   for it in items]
        p, _, _ = stu.post(f"/task/tasks/{task_id}/submit", {"answers": answers})
        check("练习交卷成功", p.get("success"), p.get("message", ""))
    else:
        R.env("练习取题与交卷", "practice 任务未创建，跳过")

    # 1d 练习历史：含 submission_id（本轮新增字段，前端跳详情依赖）
    p, _, _ = stu.get("/learning/practice/history", params={"page": 1, "page_size": 5})
    hist = rows_of(p)
    check("练习历史可读且含 submission_id 字段",
          p.get("success") and len(hist) > 0 and "submission_id" in hist[0],
          f"{len(hist)} 条")

    # 1e ★ 越权回归：未发布考试经 /learning/practice 泄露（高危修复）
    p, _, _ = tea.get("/question/papers", params={"page": 1, "page_size": 1})
    papers = rows_of(p)
    if papers:
        pid = papers[0]["id"]
        p, _, _ = tea.post("/task/tasks", {
            "title": f"【LC安全】未发布考试 {int(time.time()) % 100000}",
            "type": "exam", "paper_id": pid, "duration": 30,
            "class_ids": [], "student_ids": [],
            "publish_at": "2099-01-01 00:00:00",
        })
        exam_tid = (data_of(p) or {}).get("id")
        if exam_tid:
            p1, _, _ = stu.get(f"/learning/practice/{exam_tid}")
            check("★ 未发布考试经 /learning/practice 取题被拒（越权回归）",
                  p1.get("success") is not True,
                  f"{p1.get('code')} {p1.get('message', '')}")
            expect_denied("★ 官方入口同样拒绝（下发校验）", stu, "GET",
                          f"/task/tasks/{exam_tid}/paper")
    else:
        R.env("越权回归用例", "无试卷可建考试，跳过")

    # ---------------------------------------------------------- 2 错题本
    R.set_phase("阶段四 · 学习中心 | 2. 错题本")
    p, _, _ = stu.get("/learning/wrong-questions", params={"page": 1, "page_size": 10})
    wrongs = rows_of(p)
    check("错题列表可读（练习答错已收录）",
          p.get("success") and len(wrongs) > 0,
          f"{len(wrongs)} 条")
    if wrongs:
        w0 = wrongs[0]
        check("错题列表字段完整（stem/options/type）",
              all(k in w0 for k in ("stem", "type", "error_count", "is_mastered")),
              f"keys={sorted(w0.keys())[:8]}")
        wid = w0["id"]

        p, _, _ = stu.put(f"/learning/wrong-questions/{wid}",
                          {"error_reason": "概念不清", "is_mastered": False})
        check("标注错因", p.get("success"), p.get("message", ""))

        p, _, _ = stu.post(f"/learning/wrong-questions/{wid}/analyze")
        check("AI 错因分析（LLM 未配置走降级）", p.get("success"), p.get("message", ""))

        p, _, _ = stu.post(f"/learning/wrong-questions/{wid}/redo")
        d = data_of(p) or {}
        check("错题重做返回原题+同类题",
              p.get("success") and "origin" in d and "similar" in d,
              f"similar={len(d.get('similar') or [])}")

        p, _, _ = stu.post(f"/learning/wrong-questions/{wid}/variant")
        d = data_of(p) or {}
        # 变式练习按「同学科 + 同题型 + 同知识点」找相似题。
        # 种子数据里一个知识点每种题型往往只有 1 道题（就是原题本身），
        # 排除原题后自然为 0 —— 此时返回 400「暂无可用的变式题目」是
        # **正确行为**，不能算失败。真正的判据是：要么出卷成功，要么给出
        # 明确的可读提示，绝不能 500 或静默返回空 data。
        ok_variant = bool(p.get("success") and d.get("task_id"))
        clear_reason = (p.get("success") is False
                        and "变式" in str(p.get("message", "")))
        check("错题变式练习生成（或明确提示无同类题）",
              ok_variant or clear_reason,
              f"source={d.get('source')} total={d.get('total')} "
              f"msg={str(p.get('message', ''))[:30]!r}")

        p, _, _ = stu.get("/learning/wrong-questions/export",
                          params={"fmt": "markdown"})
        d = data_of(p) or {}
        check("导出错题 markdown", p.get("success") and d.get("content"), f"{len(d.get('content') or '')} 字")

        p, _, _ = stu.get("/learning/wrong-questions/export", params={"fmt": "html"})
        check("导出错题 html", p.get("success"), p.get("message", ""))

        p, _, _ = stu.get("/learning/wrong-questions/export", params={"fmt": "docx"})
        check("非法导出格式被 422 拒绝", p.get("success") is False, p.get("message", ""))

        # 越权：他人错题
        p2, _, _ = peer.get("/learning/wrong-questions", params={"page": 1, "page_size": 1})
        peer_wrongs = rows_of(p2)
        if peer_wrongs and peer_wrongs[0]["id"] != wid:
            # 后端对「非本人错题」统一抛 NotFound(404)：不向他人暴露记录是否存在，
            # 因此这里必须放行 404（403 反而不是当前实现的拒绝码）。
            expect_denied("他人错题不可标注", stu, "PUT",
                          f"/learning/wrong-questions/{peer_wrongs[0]['id']}",
                          body={"error_reason": "hack"},
                          allow_statuses=(404,))

    # ---------------------------------------------------------- 3 智能复习
    R.set_phase("阶段四 · 学习中心 | 3. 智能复习")
    p, _, _ = stu.get("/learning/review/plans")
    d = data_of(p) or {}
    plans = d.get("items") or []
    check("复习计划可读（含全量统计）",
          p.get("success") and isinstance(d.get("today_count"), int)
          and isinstance(d.get("pending_count"), int),
          f"plans={len(plans)} today={d.get('today_count')} pending={d.get('pending_count')}")

    pending = [x for x in plans if not x.get("is_completed")]
    if pending:
        pid0 = pending[0]["id"]
        p, _, _ = stu.put(f"/learning/review/plans/{pid0}/complete",
                          {"correct_rate": 80})
        check("完成复习（闭环推进）", p.get("success"), p.get("message", ""))
        # 非本人计划 → 后端抛 NotFound(404)，属「不暴露存在性」的数据隔离策略
        expect_denied("他人复习计划不可完成", peer, "PUT",
                      f"/learning/review/plans/{pid0}/complete", body={},
                      allow_statuses=(404,))
    else:
        R.env("复习闭环用例", "无待完成计划，跳过")

    p, _, _ = stu.get("/learning/review/mastery")
    d = data_of(p) or {}
    items = d.get("items") or []
    check("掌握地图可读且 level 已计算（回归：原恒 null）",
          p.get("success") and (not items or all(x.get("level") for x in items)),
          f"{len(items)} 点，avg={d.get('avg_mastery')}")

    p, _, _ = stu.post("/learning/review/plan", {"days": 7})
    check("AI 生成复习计划（LLM 未配置走规则降级）", p.get("success"), p.get("message", ""))
    p, _, _ = stu.post("/learning/review/plan", {"days": 10 ** 6})
    check("days 超大值被 clamp 不 500", p.get("success"), f"{p.get('code')} {p.get('message', '')}")
    p, _, _ = stu.post("/learning/review/plan", {"days": "abc"})
    check("days 非整数返回 400", p.get("success") is False, p.get("message", ""))

    # ---------------------------------------------------------- 4 学习笔记
    R.set_phase("阶段四 · 学习中心 | 4. 学习笔记")
    p, _, _ = stu.post("/learning/notes", {
        "title": "【LC】笔记", "content": "正常内容\n<script>alert('xss')</script>",
        "tags": ["重点", "错题"], "subject_id": 1,
    })
    d = data_of(p) or {}
    note_id = d.get("id")
    check("创建笔记（tags 数组）", p.get("success") and bool(note_id), p.get("message", ""))

    p, _, _ = stu.get("/learning/notes", params={"page": 1, "page_size": 5})
    items = rows_of(p)
    mine = next((x for x in items if x.get("id") == note_id), None)
    check("列表含预览且不含正文（防大字段泄漏）",
          mine is not None and "content" not in mine and "content_preview" in mine,
          "content_preview 存在" if mine else "未找到")

    p, _, _ = stu.get(f"/learning/notes/{note_id}")
    d = data_of(p) or {}
    check("详情 view_count 自增", d.get("view_count", 0) >= 1, f"view={d.get('view_count')}")

    p, _, _ = stu.put(f"/learning/notes/{note_id}", {"is_favorite": True, "tags": ["复习"]})
    check("更新笔记（收藏+tags）", p.get("success"), p.get("message", ""))

    # XSS 回归：导出 HTML 中 <script> 必须被转义
    p, _, _ = stu.get(f"/learning/notes/{note_id}/export")
    d = data_of(p) or {}
    html = d.get("html") or ""
    check("★ 导出 HTML 已转义 script（XSS 回归）",
          p.get("success") and "<script>" not in html and "&lt;script&gt;" in html,
          f"len={len(html)}")
    check("导出文件名以 .html 结尾", (d.get("filename") or "").endswith(".html"),
          d.get("filename", ""))

    # 分享 → 同班可见、异班不可见
    p, _, _ = stu.put(f"/learning/notes/{note_id}/share", {"shared": True})
    check("分享笔记", p.get("success"), p.get("message", ""))
    p, _, _ = peer.get("/learning/notes/shared", params={"page": 1, "page_size": 50})
    shared = rows_of(p)
    check("同班同学可见共享笔记", any(x.get("id") == note_id for x in shared),
          f"{len(shared)} 条共享")
    p, _, _ = other.get("/learning/notes/shared", params={"page": 1, "page_size": 50})
    check("异班学生看不到该共享", not any(x.get("id") == note_id for x in rows_of(p)),
          f"{len(rows_of(p))} 条")

    p, _, _ = peer.get(f"/learning/notes/{note_id}")
    check("未共享/非本人详情被拒（同班也不行）",
          p.get("success") is False, f"{p.get('code')}")

    p, _, _ = stu.post(f"/learning/notes/{note_id}/organize")
    check("AI 整理笔记（降级可用）", p.get("success"), p.get("message", ""))

    p, _, _ = stu.delete(f"/learning/notes/{note_id}")
    check("删除笔记", p.get("success"), p.get("message", ""))
    p, _, _ = stu.get(f"/learning/notes/{note_id}")
    check("删除后详情 404", p.get("success") is False, p.get("message", ""))

    # ---------------------------------------------------------- 5 收藏夹
    R.set_phase("阶段四 · 学习中心 | 5. 收藏夹")
    # 取一题收藏（用练习历史里的题目，或错题本题目）
    p, _, _ = stu.get("/learning/wrong-questions", params={"page_size": 1})
    wr = rows_of(p)
    qid = wr[0]["question_id"] if wr else None
    if qid:
        p, _, _ = stu.post("/learning/favorites", {"question_id": qid, "tag": "高频"})
        check("收藏题目", p.get("success"), p.get("message", ""))
        p, _, _ = stu.post("/learning/favorites", {"question_id": qid, "tag": "必考"})
        check("重复收藏幂等（更新标签）", p.get("success"),
              p.get("message", ""))
        p, _, _ = stu.get(f"/learning/favorites/check/{qid}")
        d = data_of(p) or {}
        check("收藏状态检查", d.get("favorited") is True, f"tag={d.get('tag')}")

        p, _, _ = stu.get("/learning/favorites", params={"page": 1, "page_size": 10, "tag": "必考"})
        check("按标签过滤收藏", p.get("success") and len(rows_of(p)) >= 1,
              f"tags={ (data_of(p) or {}).get('tags') }")

        # 上限回归：>50 道 → 400
        p, _, _ = stu.post("/learning/favorites/practice",
                           {"question_ids": list(range(1, 60))})
        check("★ 收藏练习 >50 题被拒（上限回归）",
              p.get("success") is False and "50" in str(p.get("message", "")),
              p.get("message", ""))
        # 正常：收藏练习
        p, _, _ = stu.post("/learning/favorites/practice", {})
        d = data_of(p) or {}
        check("收藏夹一键生成练习", p.get("success") and d.get("task_id"),
              f"total={d.get('total')}")

        # 批量收藏状态（替代逐题串行 N+1 的回归用例）
        p, _, _ = stu.post("/learning/favorites", {"question_id": qid, "tag": "批量"})
        p, _, _ = stu.get("/learning/favorites/check-batch",
                          params={"question_ids": f"{qid},999999"})
        d = data_of(p) or {}
        check("★ 批量收藏状态接口（N+1 回归）",
              p.get("success")
              and d.get(str(qid), {}).get("favorited") is True
              and d.get("999999", {}).get("favorited") is False,
              f"keys={list(d.keys())[:3]}")
        p, _, _ = stu.delete(f"/learning/favorites/by-question/{qid}")
        check("按题目取消收藏（幂等）", p.get("success"), p.get("message", ""))

    # ---------------------------------------------------------- 6 自主组卷
    R.set_phase("阶段四 · 学习中心 | 6. 自主组卷")
    # 同样必须用学生本年级的学科 id，否则抽题被年级过滤挡住（不是缺陷）
    p, _, _ = stu.post("/learning/custom-paper", {
        "name": "【LC】自测卷", "subject_id": R.context.get("stu_subject_id") or 1,
        "count": 5, "difficulty": "easy"})
    d = data_of(p) or {}
    check("随机模式组卷", p.get("success") and d.get("task_id"),
          f"total={d.get('total')}")
    p, _, _ = stu.post("/learning/custom-paper", {
        "subject_id": 1, "count": 5,
        "question_ids": list(range(1, 60))})
    check("★ 手动选题 >50 题被拒（上限回归）",
          p.get("success") is False and "50" in str(p.get("message", "")),
          p.get("message", ""))
    p, _, _ = stu.post("/learning/custom-paper", {
        "subject_id": 999999, "count": 5})
    check("无匹配题目返回 400 而非空卷", p.get("success") is False, p.get("message", ""))
    p, _, _ = stu.post("/learning/custom-paper", {
        "subject_id": 1, "count": "abc"})
    check("count 非整数返回 400", p.get("success") is False, p.get("message", ""))

    # ---------------------------------------------------------- 7 目标打卡
    R.set_phase("阶段四 · 学习中心 | 7. 学习目标")
    p, _, _ = stu.post("/learning/goals", {
        "title": "【LC】每日 10 题", "target_value": 10, "unit": "questions"})
    g = data_of(p) or {}
    gid = g.get("id")
    check("创建学习目标", p.get("success") and bool(gid), p.get("message", ""))

    p, _, _ = stu.get("/learning/goals")
    d = data_of(p) or {}
    check("目标列表含日历与 max_streak",
          isinstance(d.get("calendar"), dict) and "max_streak" in d,
          f"goals={len(d.get('items') or [])}")
    # 时区回归：打卡发生在"今天"，calendar 键必须是本地（北京）日期。
    # 若后端仍用 UTC，北京时间 0:00-8:00 会落在"昨天"，
    # 且 today_checked 之后日历当天格子缺失。
    mine_goal = next((x for x in (d.get("items") or [])
                      if x.get("today_checked")), None)
    if mine_goal and d.get("calendar"):
        local_today = time.strftime("%Y-%m-%d")
        check("★ 打卡日历使用本地日期（时区回归）",
              local_today in d["calendar"],
              f"keys={sorted(d['calendar'])[-2:]} today={local_today}")

    p, _, _ = stu.post(f"/learning/goals/{gid}/checkin", {"actual_value": -3})
    d = data_of(p) or {}
    check("负数打卡归零（回归）", p.get("success") and d.get("actual_value") == 0,
          f"actual={d.get('actual_value')}")
    p, _, _ = stu.post(f"/learning/goals/{gid}/checkin", {"actual_value": 10})
    d = data_of(p) or {}
    check("打卡幂等（同日取最大值）", p.get("success") and d.get("actual_value") == 10
          and d.get("streak", 0) >= 1,
          f"actual={d.get('actual_value')} streak={d.get('streak')}")
    p, _, _ = stu.get("/learning/goals")
    items = (data_of(p) or {}).get("items") or []
    mine = next((x for x in items if x.get("id") == gid), {})
    check("列表回显今日已打卡", mine.get("today_checked") is True,
          f"today={mine.get('today_value')}")

    # 非本人目标 → NotFound(404)：数据隔离不暴露目标是否存在
    expect_denied("他人目标不可打卡", peer, "POST",
                  f"/learning/goals/{gid}/checkin", body={"actual_value": 1},
                  allow_statuses=(404,))
    expect_denied("他人目标不可删除", peer, "DELETE", f"/learning/goals/{gid}",
                  allow_statuses=(404,))

    p, _, _ = stu.delete(f"/learning/goals/{gid}")
    check("删除目标", p.get("success"), p.get("message", ""))

    # ---------------------------------------------------------- 8 路径与闪卡
    R.set_phase("阶段四 · 学习中心 | 8. 学习路径 / 闪卡")
    p, _, _ = stu.get("/learning/path/recommend")
    d = data_of(p) or {}
    check("学习路径推荐可读（空数据有引导 message）",
          p.get("success") and "recommendations" in d
          and (d.get("ai_advice") or d.get("message")),
          f"avg={d.get('avg_mastery')} weak={d.get('weak_count')}")

    p, _, _ = stu.get("/learning/flashcards")
    d = data_of(p) or {}
    check("闪卡默认可取", p.get("success") and len(d.get("items") or []) > 0,
          f"{len(d.get('items') or [])} 张")

    p, _, _ = stu.get("/learning/flashcards", params={"limit": 99999})
    d = data_of(p) or {}
    check("★ limit 超大被 clamp ≤100（回归）", len(d.get("items") or []) <= 100,
          f"total={d.get('total')}")
    p, _, _ = stu.get("/learning/flashcards", params={"limit": 0})
    check("limit=0 clamp 至 1", len(rows_of(p)) >= 1, "")

    # ---------------------------------------------------------- 9 越权矩阵
    R.set_phase("阶段四 · 学习中心 | 9. 越权矩阵")
    p, _, _ = stu.post("/learning/notes", {"title": "越权对照", "content": "x"})
    nid = (data_of(p) or {}).get("id")
    if nid:
        # 笔记详情：非本人且非管理员 → PermissionException(403)
        expect_denied("他人笔记详情不可读", peer, "GET", f"/learning/notes/{nid}")
        # 笔记写操作：非本人 → NotFound(404)，不暴露笔记存在性
        expect_denied("他人笔记不可更新", peer, "PUT", f"/learning/notes/{nid}",
                      body={"title": "hack"}, allow_statuses=(404,))
        expect_denied("他人笔记不可删除", peer, "DELETE", f"/learning/notes/{nid}",
                      allow_statuses=(404,))
        stu.delete(f"/learning/notes/{nid}")

    print("\n学习中心专项测试完成。")
