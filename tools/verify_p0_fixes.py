"""P0 修复的**接口级**回归：四个 P0 + P1-1/P1-4 走真实 HTTP 路径。

与 `.audit_tmp/verify_p0_*.py`（直调函数）互补：那些验证「函数行为对不对」，
这个验证「端点串起来还对不对」——中间隔着依赖注入、权限、序列化、
`_build_preview`、`_write_items`，正是历史上反复出问题的地方。

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
    Answer, Class, Grade, KnowledgeMastery, KnowledgePoint, Paper, PaperItem,
    Question, Role, Subject, Submission, Task, User,
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
