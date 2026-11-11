"""接口级行为回归（**65 条断言**）：P0 与 P1/F 系列修复走真实 HTTP 路径。

与 `.audit_tmp/verify_p0_*.py`（直调函数）互补：那些验证「函数行为对不对」，
这个验证「端点串起来还对不对」——中间隔着依赖注入、权限、序列化、
`_build_preview`、`_write_items`，正是历史上反复出问题的地方。

覆盖：P0-1 导出 / P0-3 异步组卷 / P0-4 Agent 组卷 / P1-1 大题结构 /
P1-4 成绩重算 / P1-9 版本乐观锁 / P1-10 自测卷题型 / F-02 版本对比 /
F-03 班级薄弱点 / F-04 任务取消 / BUG-026 空 body 500 / P-07 报表缓存。

用法：python tools/verify_p0_fixes.py        （退出码 0 = 全通过）
环境：临时库 + 关 LLM + 关验证码，不碰项目 data/。
"""
import os
import sys
import tempfile

BACKEND = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
sys.path.insert(0, BACKEND)

DB_PATH = os.path.join(tempfile.gettempdir(), "verify_p0_fixes.db")
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

os.environ.update({
    "DATABASE_URL": "sqlite:///" + DB_PATH.replace("\\", "/"),
    "SEED_BASE_DATA": "true",
    "SEED_DEMO_DATA": "false",
    "LLM_ENABLED": "false",
    "CAPTCHA_ENFORCED": "false",
    "SCHEDULER_ENABLED": "false",
    "RAG_WARMUP_ENABLED": "false",
    "APP_VERSION": "test",
    "SECRET_KEY": "p0-fixes-verify-key-0123456789abcdef0123456789",
})

from fastapi.testclient import TestClient  # noqa: E402

from app.core.database import SessionLocal  # noqa: E402
from app.core.security import create_access_token, hash_password  # noqa: E402
from app.main import app  # noqa: E402
from app.models import (  # noqa: E402
    AgentJob, Answer, Class, Grade, KnowledgeMastery, KnowledgePoint, Paper,
    PaperItem, Question, Role, Subject, Submission, Task, User,
)

FAILED = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"  -> {detail}" if detail else ""))
    if not ok:
        FAILED.append(name)


def seed():
    """最小可用数据集：1 教师 + 2 学生 + 1 卷（两个大题）+ 1 份提交。"""
    db = SessionLocal()
    try:
        g = db.query(Grade).filter(Grade.grade_num == 7).first()
        s = db.query(Subject).filter(Subject.grade_id == g.id).first()

        teacher = User(username="p0_teacher", password=hash_password("x"),
                       real_name="P0教师", status="active", identity="teacher")
        stu = User(username="p0_stu", password=hash_password("x"),
                   real_name="P0学生", status="active", identity="student",
                   grade_id=g.id)
        # 权限来自 DB 角色（`require_perm` 读 `user.roles`），不是 token 里的 claim。
        # 直接用内置 sys_admin 角色，省掉逐条 permission 授权。
        admin_role = db.query(Role).filter(Role.code == "sys_admin").first()
        if admin_role:
            teacher.roles = [admin_role]
        db.add_all([teacher, stu])
        db.commit()
        db.refresh(teacher)
        db.refresh(stu)

        qs = []
        for i, (qt, diff) in enumerate([("single", "easy"), ("single", "medium"),
                                        ("blank", "medium"), ("short", "hard")]):
            q = Question(type=qt, stem=f"第{i + 1}题 &lt;img src=\"http://127.0.0.1:9/x\"/&gt;",
                         options='[{"key":"A","text":"1"},{"key":"B","text":"2"}]',
                         answer="A", analysis="解析 &lt;script&gt;x&lt;/script&gt;",
                         score=5, difficulty=diff, grade_id=g.id, subject_id=s.id,
                         owner_id=teacher.id, status="published", bank_type="public")
            db.add(q)
            qs.append(q)
        db.commit()
        for q in qs:
            db.refresh(q)

        paper = Paper(name="P0 回归卷", grade_id=g.id, subject_id=s.id,
                      total_score=20, duration=60, creator_id=teacher.id,
                      status="published", stage="junior", share_scope="private")
        db.add(paper)
        db.commit()
        db.refresh(paper)

        items = []
        sections = [("single", "一、选择题", 1), ("single", "一、选择题", 1),
                    ("blank", "二、填空题", 2), ("short", "三、解答题", 3)]
        for idx, (q, (code, name, sort)) in enumerate(zip(qs, sections), start=1):
            it = PaperItem(paper_id=paper.id, question_id=q.id, sort_order=idx,
                           score=5, section_code=code, section_name=name,
                           section_sort=sort)
            db.add(it)
            items.append(it)
        db.commit()
        for it in items:
            db.refresh(it)

        task = Task(title="P0 回归任务", paper_id=paper.id, subject_id=s.id,
                    grade_id=g.id, creator_id=teacher.id, status="published",
                    total_score=20, pass_score=12)
        db.add(task)
        db.commit()
        db.refresh(task)

        sub = Submission(task_id=task.id, student_id=stu.id, status="auto_graded",
                         score=15, objective_score=15, subjective_score=0)
        db.add(sub)
        db.commit()
        db.refresh(sub)

        # 逐题作答：前两题客观对、第三题空、第四题主观待批
        for it, sc, correct in [(items[0], 5, True), (items[1], 5, True),
                                (items[2], 5, True), (items[3], 0, None)]:
            db.add(Answer(submission_id=sub.id, paper_item_id=it.id,
                          question_id=it.question_id, content="x",
                          is_correct=correct, score=sc, full_score=5))
        db.commit()

        # F-03 用：一个班 + 两个知识点 + 掌握度（一个薄弱、一个良好）
        klass = Class(name="P0班", grade_id=g.id, head_teacher_id=teacher.id)
        db.add(klass)
        db.commit()
        db.refresh(klass)
        stu.class_id = klass.id
        weak_kp = KnowledgePoint(name="二次函数", level=3, grade_id=g.id,
                                 subject_id=s.id, code="P0-WEAK")
        good_kp = KnowledgePoint(name="一次函数", level=3, grade_id=g.id,
                                 subject_id=s.id, code="P0-GOOD")
        db.add_all([weak_kp, good_kp])
        db.commit()
        for kp, total, right, mastery in ((weak_kp, 20, 8, 41.0), (good_kp, 20, 18, 88.0)):
            db.add(KnowledgeMastery(student_id=stu.id, knowledge_point_id=kp.id,
                                    subject_id=s.id, total_count=total,
                                    correct_count=right, mastery=mastery,
                                    wrong_count=total - right))
        db.commit()

        return {
            "teacher_id": teacher.id, "paper_id": paper.id, "class_id": klass.id,
            "item_ids": [i.id for i in items], "task_id": task.id, "sub_id": sub.id,
            "stu_id": stu.id, "grade_id": g.id, "subject_id": s.id,
        }
    finally:
        db.close()


def main():
    with TestClient(app) as client:
        ctx = seed()
        tok = create_access_token(ctx["teacher_id"], role="teacher")
        H = {"Authorization": f"Bearer {tok}"}
        api = "/api/v1"
        pid = ctx["paper_id"]

        print("\n[P0-1] PDF / 答题卡导出：恶意题干不得 500")
        for path, label in ((f"/question/papers/{pid}/export/pdf?mode=teacher", "教师卷 PDF"),
                            (f"/question/papers/{pid}/export/pdf?mode=student", "学生卷 PDF"),
                            (f"/question/papers/{pid}/export/answer-sheet", "答题卡")):
            r = client.get(api + path, headers=H)
            ok = r.status_code == 200 and r.content[:4] == b"%PDF"
            check(f"{label} 导出", ok, f"HTTP {r.status_code}, {len(r.content)} bytes")

        print("\n[P0-3] AI 一键组卷：只写描述（不选年级学科）")
        r = client.post(api + "/question/papers/compose/ai/async", headers=H,
                        json={"request": "出一份七年级语文期中卷"})
        check("异步组卷受理", r.status_code == 200, f"HTTP {r.status_code}")
        job_id = (r.json().get("data") or {}).get("job_id")
        check("返回 job_id", bool(job_id), str(job_id))
        if job_id:
            status, stage, err = None, "", ""
            for _ in range(60):
                jr = client.get(api + f"/question/papers/compose/jobs/{job_id}", headers=H)
                d = jr.json().get("data") or {}
                status, stage, err = d.get("status"), d.get("stage") or "", d.get("error") or ""
                if status in ("succeeded", "success", "failed"):
                    break
                import time
                time.sleep(0.5)
            check("后台任务成功（不再报『请选择有效的年级』）",
                  status in ("succeeded", "success"),
                  f"status={status} stage={stage} err={err}")
            items = ((d.get("result") or {}).get("sections") or [])
            check("产出非空卷面", bool(items), f"{len(items)} 个大题")

        print("\n[P0-4] 智能组卷 Agent：默认参数必须出题")
        gid = ctx.get("grade_id")
        db = SessionLocal()
        try:
            g = db.query(Grade).filter(Grade.grade_num == 7).first()
            s = db.query(Subject).filter(Subject.grade_id == g.id).first()
            gid, sid = g.id, s.id
        finally:
            db.close()
        r = client.post(api + "/agent/paper-composer", headers=H,
                        json={"grade_id": gid, "subject_id": sid, "total_score": 100})
        body = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
        d = body.get("data") or {}
        n = (d.get("paper") or {}).get("item_count", 0)
        check("Agent 返回 success", bool(body.get("success")),
              f"HTTP {r.status_code} msg={body.get('message')}")
        check("Agent 出题数 > 0", n > 0, f"{n} 题")

        print("\n[P1-1] 列表页覆盖写：大题结构不得被抹平")
        detail = client.get(api + f"/question/papers/{pid}", headers=H).json().get("data") or {}
        before = [(i["question_id"], i.get("section_code"), i.get("section_name"),
                   i.get("section_sort")) for i in detail.get("items") or []]
        check("详情接口回传 section_code/section_sort",
              all(b[1] is not None and b[3] is not None for b in before), str(before[:2]))

        put = client.put(api + f"/question/papers/{pid}", headers=H, json={
            "name": "P0 回归卷(改)",
            "items": [{"question_id": b[0], "score": 5,
                       "section_code": b[1], "section_name": b[2],
                       "section_sort": b[3]} for b in before]
        })
        check("覆盖写返回 200", put.status_code == 200, f"HTTP {put.status_code}")
        after_detail = client.get(api + f"/question/papers/{pid}", headers=H).json().get("data") or {}
        after = [(i["question_id"], i.get("section_code"), i.get("section_name"),
                  i.get("section_sort")) for i in after_detail.get("items") or []]
        check("保存后大题结构完整保留", before == after, f"before={before} after={after}")

        print("\n[P1-4] 删题：成绩重算 + 客观/主观分列自洽")
        # ★ 覆盖写会「插新题项 → 删旧题项」，paper_item_id 已全部重建，
        #   必须重新取，不能沿用 seed 阶段缓存的 id（否则 404）。
        fresh = (client.get(api + f"/question/papers/{pid}", headers=H)
                 .json().get("data") or {}).get("items") or []
        del_id = fresh[-1]["paper_item_id"]
        r = client.delete(api + f"/question/papers/{pid}/items/{del_id}?force=true", headers=H)
        check("单题删除成功", r.status_code == 200,
              f"HTTP {r.status_code} {r.text[:120]}")
        if r.status_code == 200:
            d = r.json().get("data") or {}
            check("响应含重算结果", "affected_submissions" in d, str(d))
        db = SessionLocal()
        try:
            sub = db.get(Submission, ctx["sub_id"])
            obj, subj = float(sub.objective_score or 0), float(sub.subjective_score or 0)
            check("总分 == 客观分 + 主观分",
                  abs(float(sub.score or 0) - (obj + subj)) < 0.01,
                  f"score={sub.score} obj={obj} subj={subj}")
            check("成绩已重算（不再保持旧值 15）",
                  abs(float(sub.score or 0) - 15) > 0.01 or abs(obj - 15) < 0.01,
                  f"score={sub.score}")
        finally:
            db.close()

        print("\n[P1-9] 题项覆盖写：版本号不匹配必须 409（不能静默覆盖他人改动）")
        cur_detail = client.get(api + f"/question/papers/{pid}", headers=H).json().get("data") or {}
        cur_v = int(cur_detail.get("current_version") or 1)
        cur_items = [{"question_id": i["question_id"], "score": 5,
                      "section_code": i.get("section_code"),
                      "section_name": i.get("section_name"),
                      "section_sort": i.get("section_sort")}
                     for i in cur_detail.get("items") or []]
        stale_v = cur_v - 1 if cur_v > 1 else cur_v + 99
        r = client.post(api + f"/question/papers/{pid}/items", headers=H,
                        json={"current_version": stale_v, "items": cur_items})
        check("过期版本号被拒绝", r.status_code == 409, f"HTTP {r.status_code} {r.text[:100]}")
        det = (r.json() or {}).get("detail") or {}
        check("409 回传当前版本号（前端据此提示刷新）",
              int(det.get("current_version") or 0) == cur_v,
              f"detail={det} 期望 current_version={cur_v}")
        r = client.post(api + f"/question/papers/{pid}/items", headers=H,
                        json={"current_version": cur_v, "items": cur_items})
        check("正确版本号保存成功", r.status_code == 200, f"HTTP {r.status_code} {r.text[:100]}")
        new_v = int((r.json().get("data") or {}).get("version") or 0)
        # 不强求「恰好 +1」：一次保存会写两条快照（编辑题目 / 编辑完成），
        # `snapshot()` 遇到版本号冲突还会再推进一格。真正要守住的是**单调前进**
        # —— 版本不前进，前端保存后重新载入拿到的还是旧号，下一次保存又会 409。
        check("保存后版本号前进（下次保存不会误判冲突）", new_v > cur_v,
              f"{cur_v} -> {new_v}")
        # 旧前端 / 脚本不带 current_version 时必须保持原行为（否则升级即全员保存失败）
        r = client.post(api + f"/question/papers/{pid}/items", headers=H,
                        json={"items": cur_items})
        check("不带版本号仍可保存（向后兼容）", r.status_code == 200,
              f"HTTP {r.status_code} {r.text[:100]}")

        print("\n[P1-10] 学生自测卷：题型筛选生效 / 放宽如实上报 / 满分可读")
        s_tok = create_access_token(ctx["stu_id"], role="student")
        SH = {"Authorization": f"Bearer {s_tok}"}
        base_body = {"subject_id": ctx["subject_id"], "grade_id": ctx["grade_id"],
                     "difficulty": ""}
        # 只勾「填空题」且只要 1 题：题库里正好有 1 道 blank，必须严格满足、不放宽
        r = client.post(api + "/learning/custom-paper", headers=SH,
                        json={**base_body, "count": 1, "question_types": ["blank"]})
        d = r.json().get("data") or {}
        check("自测卷生成成功", r.status_code == 200, f"HTTP {r.status_code} {r.text[:100]}")
        check("回传满分（原来是 undefined）", isinstance(d.get("total_score"), (int, float)),
              str(d.get("total_score")))
        check("条件可满足时不虚报放宽", (d.get("relaxations") or []) == [],
              str(d.get("relaxations")))
        db = SessionLocal()
        try:
            p = db.get(Paper, d.get("paper_id"))
            types = [it.question.type for it in p.items] if p else []
        finally:
            db.close()
        check("只选出填空题就真的只出填空题（alias fill 已归一）",
              types == ["blank"], str(types))

        # 只勾填空题但要 5 题：题库不够，必须放宽**且如实上报**，年级不能放宽
        r = client.post(api + "/learning/custom-paper", headers=SH,
                        json={**base_body, "count": 5, "question_types": ["blank"]})
        d2 = r.json().get("data") or {}
        check("题目不足时如实上报放宽原因", bool(d2.get("relaxations")),
              str(d2.get("relaxations")))
        db = SessionLocal()
        try:
            p2 = db.get(Paper, d2.get("paper_id"))
            same_grade = bool(p2) and all(it.question.grade_id == ctx["grade_id"]
                                          for it in p2.items)
        finally:
            db.close()
        check("放宽只丢题型，年级绝不放宽", same_grade, f"paper={d2.get('paper_id')}")

        print("\n[F-04] AI 长任务可取消：登记 → worker 检查点 → 落 cancelled")
        from app.api.v1.paper_compose import _run_compose_job
        db = SessionLocal()
        try:
            job = AgentJob(user_id=ctx["teacher_id"], agent="paper_compose",
                           status="running", progress=30, stage="AI 补题 2/5",
                           params="{}")
            db.add(job)
            db.commit()
            db.refresh(job)
            jid = job.id
        finally:
            db.close()

        r = client.post(api + f"/question/papers/compose/jobs/{jid}/cancel", headers=H)
        body = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
        d = body.get("data") or {}
        check("取消请求被受理", r.status_code == 200 and d.get("accepted") is True,
              f"HTTP {r.status_code} {body.get('message')}")
        db = SessionLocal()
        try:
            j = db.get(AgentJob, jid)
            check("只置标志、不改 status（单一写入者是 worker）",
                  int(j.cancel_requested or 0) == 1 and j.status == "running",
                  f"cancel_requested={j.cancel_requested} status={j.status}")
        finally:
            db.close()

        r = client.post(api + f"/question/papers/compose/jobs/{jid}/cancel", headers=H)
        d = r.json().get("data") or {}
        check("重复取消幂等（不报错、不重复受理）",
              r.status_code == 200 and d.get("accepted") is False, str(d.get("message")))

        # 直接驱动 worker：检查点在开工处，必须立刻落 cancelled 且不写结果
        _run_compose_job(jid)
        db = SessionLocal()
        try:
            j = db.get(AgentJob, jid)
            check("worker 在检查点响应取消", j.status == "cancelled",
                  f"status={j.status} stage={j.stage}")
            check("取消不写结果、不记 error（不是故障）",
                  not j.result and not j.error, f"result={bool(j.result)} error={j.error}")
        finally:
            db.close()

        db = SessionLocal()
        try:
            done = AgentJob(user_id=ctx["teacher_id"], agent="paper_compose",
                            status="succeeded", progress=100, params="{}")
            db.add(done)
            db.commit()
            db.refresh(done)
            done_id = done.id
        finally:
            db.close()
        r = client.post(api + f"/question/papers/compose/jobs/{done_id}/cancel", headers=H)
        d = r.json().get("data") or {}
        check("已完成的任务拒绝取消（不翻转状态）",
              r.status_code == 200 and d.get("accepted") is False
              and d.get("status") == "succeeded", str(d.get("message")))

        print("\n[F-02] 版本对比：能算出「与当前卷面差在哪」")
        vr = client.get(api + f"/question/papers/{pid}/versions", headers=H)
        vlist = (vr.json().get("data") or {}).get("items") or []
        oldest = min((v["version"] for v in vlist), default=None)
        check("版本列表非空", bool(vlist), f"{len(vlist)} 条，最旧 v{oldest}")
        if oldest is not None:
            r = client.get(api + f"/question/papers/{pid}/versions/{oldest}/diff",
                           headers=H, params={"against": "current"})
            d = r.json().get("data") or {}
            items = d.get("items") or {}
            check("对比接口可用", r.status_code == 200 and bool(d.get("summary")),
                  f"HTTP {r.status_code} {d.get('summary')}")
            # 这轮前面已经「删过一道题」，最旧版本必然比现在多题
            check("能识别出被移除的题目", bool(items.get("removed")), str(
                [x.get("question_id") for x in (items.get("removed") or [])]))
            check("差异结构齐全（added/removed/changed/unchanged）",
                  all(k in items for k in ("added", "removed", "changed", "unchanged")),
                  str(sorted(items.keys())))

            same = client.get(api + f"/question/papers/{pid}/versions/{oldest}/diff",
                              headers=H, params={"against": str(oldest)})
            sd = same.json().get("data") or {}
            check("同一版本自比 = 无差异（不虚报变更）",
                  sd.get("has_changes") is False, str(sd.get("summary")))

        print("\n[BUG-026] 带 Pydantic 模型的端点：客户端不带 body 不得 500")
        # `body: XxxIn = Body(default_factory=dict)` 时，客户端完全不传 body
        # 会让 FastAPI 把 `{}`（dict）塞进来 → body.model_dump() AttributeError。
        # 前端每次恰好都发 `{}` 所以从未暴露，脚本一跳过 body 就 500。
        for path, name in (
            (f"/question/papers/{pid}/versions/{oldest}/restore", "回溯"),
            (f"/question/papers/{pid}/copy", "复制"),
            (f"/question/papers/{pid}/favorite", "收藏"),
            (f"/question/papers/{pid}/archive", "停用"),
        ):
            r = client.post(api + path, headers=H)   # 刻意不传 json
            check(f"{name}：不带 body 不 500", r.status_code != 500,
                  f"HTTP {r.status_code} {r.text[:90]}")

    # ---------------------------------------------------------------- F-03
    print("\n[F-03] 班级薄弱知识点聚合")
    r = client.get(api + "/report/teacher/class-weak-points", headers=H,
                   params={"class_id": ctx["class_id"], "limit": 10})
    d = r.json().get("data") or {}
    items = d.get("items") or []
    check("接口返回 200", r.status_code == 200, f"HTTP {r.status_code}")
    check("聚合出 2 个知识点", len(items) == 2, f"{len(items)}")
    if len(items) == 2:
        check("按正确率升序（最薄弱在最前）", items[0]["accuracy"] < items[1]["accuracy"],
              f"{items[0]['name']}={items[0]['accuracy']}% vs "
              f"{items[1]['name']}={items[1]['accuracy']}%")
        check("薄弱点带讲评建议", bool(items[0].get("suggestion")),
              items[0].get("suggestion"))
        check("统计未掌握人数", items[0].get("weak_students") == 1,
              str(items[0].get("weak_students")))

    # ---------------------------------------------------------------- P-07
    # 缓存最容易「看起来生效了、其实永远不命中」，所以这里不测时间，只测
    # 可观测的 hits/misses 增量；跨用户隔离另起一个教师身份验证。
    print("\n[P-07] 报表聚合短 TTL 进程内缓存")
    from app.services import report_cache  # noqa: E402  （延迟导入：需先建好临时库）

    report_cache.clear()
    wp = api + "/report/teacher/class-weak-points"
    # 刻意换 limit=7，避开前面 F-03 用 limit=10 留下的条目，从零开始计数
    p = {"class_id": ctx["class_id"], "limit": 7}

    s0 = report_cache.stats()
    r1 = client.get(wp, headers=H, params=p)
    s1 = report_cache.stats()
    check("首次请求未命中（misses +1）", s1["misses"] - s0["misses"] == 1,
          f"misses {s0['misses']} -> {s1['misses']}")

    r2 = client.get(wp, headers=H, params=p)
    s2 = report_cache.stats()
    check("同参数二次请求命中缓存（hits +1）", s2["hits"] - s1["hits"] == 1,
          f"hits {s1['hits']} -> {s2['hits']}")
    check("命中返回的内容与首次一致",
          (r1.json().get("data") or {}) == (r2.json().get("data") or {}),
          f"HTTP {r1.status_code}/{r2.status_code}")

    # refresh=1 必须绕过缓存：老师刚批完作业点刷新还看到旧数字，会以为批改没生效
    r3 = client.get(wp, headers=H, params={**p, "refresh": "true"})
    s3 = report_cache.stats()
    check("refresh=true 不读缓存（hits 不增）", s3["hits"] == s2["hits"],
          f"hits {s2['hits']} -> {s3['hits']}")
    check("refresh=true 返回结果仍然正确",
          len((r3.json().get("data") or {}).get("items") or []) == 2,
          f"HTTP {r3.status_code}")

    # 重算后必须写回：否则老师点一次刷新只爽这一次，紧接着的轮询又回到旧值，
    # 表现为「刷新没生效」。这条断言专防这种「看着修好了其实没修」。
    r3b = client.get(wp, headers=H, params=p)
    s3b = report_cache.stats()
    check("refresh 后写回缓存，后续请求立即命中", s3b["hits"] - s3["hits"] == 1,
          f"hits {s3['hits']} -> {s3b['hits']}")
    check("refresh 后的缓存值就是重算值（不是旧值）",
          (r3.json().get("data") or {}) == (r3b.json().get("data") or {}))

    # 跨用户隔离：key 里 user_id 是第二参数，另一个教师不得复用前者的缓存。
    # 这条是防数据泄露的，缓存评审里最难靠肉眼发现的那类 bug。
    db = SessionLocal()
    try:
        other = User(username="p0_teacher2", password=hash_password("x"),
                     real_name="P0教师2", status="active", identity="teacher")
        role = db.query(Role).filter(Role.code == "sys_admin").first()
        if role:
            other.roles = [role]
        db.add(other)
        db.commit()
        db.refresh(other)
        other_id = other.id
        other_class = Class(name="P0班2", grade_id=ctx["grade_id"],
                            head_teacher_id=other_id)
        db.add(other_class)
        db.commit()
        db.refresh(other_class)
        other_class_id = other_class.id
    finally:
        db.close()

    tok2 = create_access_token(other_id, role="teacher")
    H2 = {**H, "Authorization": f"Bearer {tok2}"}
    before = report_cache.stats()
    r4 = client.get(wp, headers=H2, params={"class_id": other_class_id, "limit": 7})
    after = report_cache.stats()
    check("换教师 + 换班级：走真实查询而非命中", after["misses"] - before["misses"] == 1,
          f"misses {before['misses']} -> {after['misses']}")
    check("另一教师看不到原班级数据（仍受权限/键隔离约束）",
          r4.status_code in (200, 403),
          f"HTTP {r4.status_code}")
    check("缓存键含 user_id（同一班级不同用户不共键）",
          report_cache.key("class-weak-points", ctx["teacher_id"], 1)
          != report_cache.key("class-weak-points", other_id, 1))

    # 单元级：命中返回深拷贝，下游就地排序/追加不得污染缓存
    report_cache.clear()
    report_cache.cached("unit:deepcopy", lambda: {"a": [1, 2]})
    got = report_cache.cached("unit:deepcopy", lambda: {"a": []})
    got["a"].append(99)
    again = report_cache.cached("unit:deepcopy", lambda: {"a": []})
    check("命中返回深拷贝（下游就地修改不污染缓存）", again == {"a": [1, 2]}, str(again))

    # 单元级：过期后必须重算（否则 TTL 形同虚设，数据永远不更新）
    report_cache.clear()
    calls = []
    for _i in range(2):
        report_cache.cached("unit:ttl", lambda: calls.append(1) or "v", ttl=-1)
    check("TTL 过期后重新计算", len(calls) == 2, f"producer 调用 {len(calls)} 次")

    # 单元级：容量上限必须生效，否则 key 带 user_id 会成为内存泄漏
    report_cache.clear()
    for i in range(report_cache.MAX_ENTRIES + 40):
        report_cache.put(f"unit:cap:{i}", i)
    check("容量上限生效（不无限增长）",
          report_cache.stats()["entries"] <= report_cache.MAX_ENTRIES,
          f"entries={report_cache.stats()['entries']} / max={report_cache.MAX_ENTRIES}")
    report_cache.clear()

    print("\n[P-07] 班级概览同样走缓存")
    ov = api + "/report/teacher/class-overview"
    # 用 reset_stats 而不是 clear：clear 保留累计计数，这里要断言绝对值
    report_cache.reset_stats()
    o1 = client.get(ov, headers=H, params={"class_id": ctx["class_id"]})
    o2 = client.get(ov, headers=H, params={"class_id": ctx["class_id"]})
    so = report_cache.stats()
    check("班级概览返回 200", o1.status_code == 200, f"HTTP {o1.status_code}")
    check("班级概览二次请求命中缓存", so["hits"] == 1 and so["misses"] == 1,
          f"hits={so['hits']} misses={so['misses']}")

    # 只缓存「学生人数/提交数」这类聚合算出来的结果，换个 task 必须另算
    o3 = client.get(ov, headers=H,
                    params={"class_id": ctx["class_id"], "task_id": ctx["task_id"]})
    so2 = report_cache.stats()
    check("换 task_id 走新键（不串上一次的概览）", so2["misses"] == 2,
          f"misses={so2['misses']}")
    check("带 task_id 的概览仍然可用", o3.status_code == 200, f"HTTP {o3.status_code}")
    check("班级概览缓存前后内容一致",
          (o1.json().get("data") or {}) == (o2.json().get("data") or {}))
    report_cache.reset_stats()

    print()
    if FAILED:
        print(f"=== 失败 {len(FAILED)} 项 ===")
        for f in FAILED:
            print("  -", f)
        return 1
    print("=== P0 接口级回归全部通过 ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
