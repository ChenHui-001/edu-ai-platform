"""试卷管理模块缺陷复现与回归验证。

覆盖审计发现的问题，每条断言对应一个真实缺陷：
  P0-1 改卷丢作答：PUT /papers/{id} 传 items 会整批删题项，Student Answer 因
       paper_item_id ON DELETE CASCADE 被级联清空（paper_compose 已修，此处未修）。
  P1-2 跨年级越权：_paper_visibility_clause / _assert_paper_readable 只要
       is_shared=True 就放行所有人，定向共享变成全员可读、跨年级可读。
  P1-3 导出 XSS：/export?fmt=html|word 手拼 HTML 未转义，
       题干里的 <script> 会被 PaperEdit 用 document.write 打开并执行。
  P1-4 假 PDF：/export?fmt=pdf 返回的是 HTML，前端却命名 .pdf，打不开。
  P2-5 答案未解码：导出的答案是库里的 JSON 原文（"B" 带引号）。
  P2-6 零分卷：全部题目分值为 0 时试卷可创建，但发布任务必失败（及格分校验）。

用法：python tools/verify_paper_manage.py
退出码 0 = 全部通过。
"""
import io
import os
import socket
import subprocess
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND = os.path.join(ROOT, "backend")
PY = sys.executable

PASSED, FAILED = [], []


def check(name, ok, detail=""):
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  -> {detail}" if detail and not ok else ""))
    (PASSED if ok else FAILED).append(name)
    return ok


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def wait_health(base, timeout=120):
    import httpx
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = httpx.get(f"{base}/api/v1/health", timeout=3)
            if r.status_code == 200 and (r.json().get("data") or {}).get("server_time"):
                return True
        except Exception:
            pass
        time.sleep(1.5)
    return False


def data_of(payload):
    return (payload or {}).get("data") or {}


def main():
    import httpx

    port = free_port()
    base = f"http://127.0.0.1:{port}"
    tmpdir = tempfile.mkdtemp(prefix="papermanage_")
    db_path = os.path.join(tmpdir, "test.db")
    log_path = os.path.join(tmpdir, "server.log")

    env = dict(os.environ)
    env.update({
        "LLM_ENABLED": "false", "APP_VERSION": "2.1.1",
        "DATABASE_URL": f"sqlite:///{db_path}",
        "SECRET_KEY": "paper-manage-test-key-0123456789",
        "TZ": "Asia/Shanghai",
    })
    logf = open(log_path, "w", encoding="utf-8")
    proc = subprocess.Popen(
        [PY, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(port)],
        cwd=BACKEND, env=env, stdout=logf, stderr=subprocess.STDOUT,
    )

    try:
        if not wait_health(base):
            print(f"服务未就绪，日志：{log_path}")
            print(open(log_path, encoding="utf-8", errors="replace").read()[-2500:])
            return 1
        api = f"{base}/api/v1"

        def login(u, p):
            r = httpx.post(f"{api}/auth/login", json={"username": u, "password": p}, timeout=30)
            if r.status_code != 200:
                return None
            d = data_of(r.json())
            return d.get("access_token")

        adm = login("admin", "Admin@123456")
        if not adm:
            print("管理员登录失败")
            return 1
        HA = {"Authorization": f"Bearer {adm}"}

        # ---------------- 0. 准备 ----------------
        print("\n=== 0. 准备（三教师 + 学生 + 题库 + 试卷 + 任务）===")
        g_data = data_of(httpx.get(f"{api}/edu/grades", headers=HA, timeout=30).json())
        g_items = g_data if isinstance(g_data, list) else (g_data.get("items") or [])
        g7 = next((g for g in g_items if g.get("grade_num") == 7), g_items[0])
        g9 = next((g for g in g_items if g.get("grade_num") == 9), g_items[-1])

        def subjects_of(grade_id):
            d = data_of(httpx.get(f"{api}/edu/subjects", headers=HA,
                                  params={"grade_id": grade_id}, timeout=30).json())
            return d if isinstance(d, list) else (d.get("items") or [])

        s7 = next((s for s in subjects_of(g7["id"]) if s["name"] == "数学"), None)
        s9 = next((s for s in subjects_of(g9["id"]) if s["name"] == "数学"), None)
        print(f"  七年级数学={s7['id']}  九年级数学={s9['id']}")

        uniq = str(int(time.time()))[-6:]

        def make_user(prefix, real, identity, grade_id, class_id=None, roles=None):
            body = {
                "username": f"{prefix}{uniq}", "real_name": real,
                "password": "Pass@123456", "identity": identity,
                "grade_id": grade_id, "status": "active",
                "roles": roles or [identity], "must_change_password": False,
            }
            if class_id:
                body["class_id"] = class_id
            return data_of(httpx.post(f"{api}/system/users", headers=HA,
                                      json=body, timeout=30).json())

        cls = data_of(httpx.post(f"{api}/edu/classes", headers=HA, json={
            "name": f"试卷验证班{uniq}", "grade_id": g7["id"], "head_teacher_id": None,
        }, timeout=30).json())
        cls_id = cls.get("id")

        ta = make_user("pa", f"甲教师{uniq}", "teacher", g7["id"])
        tb = make_user("pb", f"乙教师{uniq}", "teacher", g7["id"])
        tc = make_user("pc", f"丙教师{uniq}", "teacher", g9["id"])
        stu = make_user("ps", f"试卷学生{uniq}", "student", g7["id"], cls_id)
        check("准备账号（3 教师 + 1 学生）",
              all(x.get("id") for x in (ta, tb, tc, stu)),
              str([x.get("id") for x in (ta, tb, tc, stu)]))

        tok_a, tok_b, tok_c = (login(f"pa{uniq}", "Pass@123456"),
                               login(f"pb{uniq}", "Pass@123456"),
                               login(f"pc{uniq}", "Pass@123456"))
        tok_s = login(f"ps{uniq}", "Pass@123456")
        HAa = {"Authorization": f"Bearer {tok_a}"}
        HAb = {"Authorization": f"Bearer {tok_b}"}
        HAc = {"Authorization": f"Bearer {tok_c}"}
        HS = {"Authorization": f"Bearer {tok_s}"}
        check("三个教师 + 学生均可登录", all([tok_a, tok_b, tok_c, tok_s]))

        def new_question(stem, answer, qtype="single", score=10, grade_id=None, subj_id=None, tok=None):
            body = {
                "type": qtype, "difficulty": "easy", "score": score, "stem": stem,
                "options": [{"key": "A", "text": "甲"}, {"key": "B", "text": "乙"}],
                "answer": answer, "analysis": "验证用解析。",
                "grade_id": grade_id or g7["id"], "subject_id": subj_id or s7["id"],
                "bank_type": "public",
            }
            r = httpx.post(f"{api}/question/questions", headers=tok or HAa, json=body, timeout=30)
            return data_of(r.json()).get("id")

        q1 = new_question("【试卷管理】1+1=？", "B")
        # 多选题答案是数组：库里以 JSON 形式存 ["A","B"]，导出若不解码就会
        # 原样带出方括号和引号（单选答案存的是纯字符串，看不出这个问题）
        q2 = new_question("【试卷管理】多选题（选 A、B）", ["A", "B"], qtype="multiple")
        q3 = new_question("【试卷管理】3+3=？", "B")
        check("创建 3 道题", all([q1, q2, q3]), str([q1, q2, q3]))

        paper = data_of(httpx.post(f"{api}/question/papers", headers=HAa, json={
            "name": f"试卷管理验证卷{uniq}", "grade_id": g7["id"], "subject_id": s7["id"],
            "type": "exam", "duration": 60,
            "items": [{"question_id": q, "score": 10} for q in (q1, q2, q3)],
        }, timeout=30).json())
        pid = paper.get("id")
        check("创建试卷", bool(pid), str(paper)[:160])

        task = data_of(httpx.post(f"{api}/task/tasks", headers=HAa, json={
            "title": f"试卷管理任务{uniq}", "type": "exam", "paper_id": pid,
            "duration": 60, "allow_retake": 1, "show_answer": True,
            "student_ids": [stu.get("id")], "class_ids": [],
        }, timeout=30).json())
        tid = task.get("id")
        check("发布任务", bool(tid), str(task)[:160])

        tp = data_of(httpx.get(f"{api}/task/tasks/{tid}/paper", headers=HS, timeout=30).json())
        # 多选题必须提交数组，否则判分不满分，后续「分数不被清零」断言会误判
        payload = [{
            "paper_item_id": it["paper_item_id"],
            "content": ["A", "B"] if it.get("type") == "multiple" else "B",
        } for it in (tp.get("items") or [])]
        sub = data_of(httpx.post(f"{api}/task/tasks/{tid}/submit", headers=HS,
                                 json={"answers": payload, "duration_seconds": 60},
                                 timeout=60).json())
        sid = sub.get("submission_id")
        check("学生交卷成功", bool(sid), str(sub)[:160])

        def answer_count():
            d = data_of(httpx.get(f"{api}/task/submissions/{sid}", headers=HS, timeout=30).json())
            return len(d.get("answers") or []), d.get("score")

        before_cnt, before_score = answer_count()
        check("交卷后作答 3 条、30 分", before_cnt == 3 and before_score == 30,
              f"cnt={before_cnt} score={before_score}")

        # ---------------- P0-1 改卷是否丢作答 ----------------
        print("\n=== 1. [P0] 编辑试卷（题目不变）不得清空学生作答 ===")
        detail = data_of(httpx.get(f"{api}/question/papers/{pid}", headers=HAa, timeout=30).json())
        same_items = [{"question_id": it["question_id"], "score": it["score"]}
                      for it in (detail.get("items") or [])]
        r = httpx.put(f"{api}/question/papers/{pid}", headers=HAa,
                      json={"items": same_items}, timeout=30)
        check("编辑试卷请求成功", r.status_code == 200, r.text[:200])
        after_cnt, after_score = answer_count()
        check("题目未变时学生作答不丢（仍 3 条）", after_cnt == 3, f"{before_cnt} -> {after_cnt}")
        check("分数不被清零（仍 30 分）", after_score == 30, f"{before_score} -> {after_score}")

        # 移除一道题：应只作废那一题的作答（3 -> 2），其余保留
        fewer = same_items[:2]
        r = httpx.put(f"{api}/question/papers/{pid}", headers=HAa,
                      json={"items": fewer}, timeout=30)
        cnt2, _ = answer_count()
        check("移除 1 题后仅该题作答作废（3 -> 2）", cnt2 == 2, f"cnt={cnt2}")
        body = (r.json() or {}).get("data") or {}
        check("移除题目如实上报作废条数", "dropped_answers" in body or "作废" in (r.json().get("message") or ""),
              str(r.json())[:200])

        # ---------------- P1-2 跨年级越权 ----------------
        print("\n=== 2. [P1] 定向共享不得变成全员可读 ===")
        rs = httpx.post(f"{api}/question/papers/{pid}/share", headers=HAa,
                        json={"user_ids": [tb.get("id")]}, timeout=30)
        check("共享给同年级教师成功", rs.status_code == 200, rs.text[:200])

        rb = httpx.get(f"{api}/question/papers/{pid}", headers=HAb, timeout=30)
        check("被共享者可以读（含答案）", rb.status_code == 200, str(rb.status_code))
        rc = httpx.get(f"{api}/question/papers/{pid}", headers=HAc, timeout=30)
        check("无关的九年级教师不可读（应 403）", rc.status_code == 403, f"实际 {rc.status_code}")
        lc = data_of(httpx.get(f"{api}/question/papers", headers=HAc,
                               params={"page": 1, "page_size": 50}, timeout=30).json())
        leaked = [x for x in (lc.get("items") or []) if x.get("id") == pid]
        check("试卷列表不出现跨年级共享卷", not leaked, f"泄漏 {len(leaked)} 条")

        # ---------------- P1-3 导出 XSS ----------------
        print("\n=== 3. [P1] 导出 HTML 必须转义题干 ===")
        # 两种载荷都要覆盖：
        #   实体编码 &lt;script&gt; —— paper_export_service._plain 会把它反解成真标签
        #   裸标签 <script>      —— 题干原样落库时直接注入
        xss_q = new_question("&lt;script&gt;alert(1)&lt;/script&gt;安全题干", "B")
        raw_q = new_question("<script>alert(2)</script>裸标签题干", "B")
        xss_paper = data_of(httpx.post(f"{api}/question/papers", headers=HAa, json={
            "name": f"转义验证卷{uniq}", "grade_id": g7["id"], "subject_id": s7["id"],
            "items": [{"question_id": xss_q, "score": 10},
                      {"question_id": raw_q, "score": 10}],
        }, timeout=30).json())
        xpid = xss_paper.get("id")
        check("创建含脚本片段的试卷", bool(xpid))

        # 旧导出端点（question.py 手拼 HTML）
        rh = httpx.get(f"{api}/question/papers/{xpid}/export", headers=HAa,
                       params={"fmt": "html"}, timeout=30)
        check("旧端点导出 HTML 返回 200", rh.status_code == 200, str(rh.status_code))
        check("[旧端点] 不出现可执行 script", "<script>alert(" not in rh.text,
              (rh.text[:0] or "") + str(rh.text.count("<script>")) + " 处 <script>")

        # 新导出端点（paper_compose → paper_export_service._plain）
        rn = httpx.get(f"{api}/question/papers/{xpid}/export/html", headers=HAa,
                       params={"mode": "teacher"}, timeout=30)
        check("新端点导出 HTML 返回 200", rn.status_code == 200, str(rn.status_code))
        check("[新端点] 不出现可执行 script（实体反解不得还原成标签）",
              "<script>alert(" not in rn.text, f"{rn.text.count('<script>')} 处 <script>")
        # Word 导出走同一套 _plain，也要确认没有注入
        rw = httpx.get(f"{api}/question/papers/{xpid}/export", headers=HAa,
                       params={"fmt": "word"}, timeout=30)
        check("Word 导出不得残留可执行 script", "<script>alert(" not in rw.text,
              f"{rw.text.count('<script>')} 处 <script>")

        # ---------------- P1-4 真 PDF ----------------
        print("\n=== 4. [P1] fmt=pdf 必须返回真正的 PDF ===")
        rp = httpx.get(f"{api}/question/papers/{pid}/export", headers=HAa,
                       params={"fmt": "pdf"}, timeout=60)
        check("PDF 导出返回 200", rp.status_code == 200, str(rp.status_code))
        check("响应以 %PDF 魔数开头", rp.content[:4] == b"%PDF",
              repr(rp.content[:16]))

        # ---------------- P2-5 答案解码 ----------------
        print("\n=== 5. [P2] 导出的答案不得是 JSON 原文 ===")
        from openpyxl import load_workbook
        rx = httpx.get(f"{api}/question/papers/{pid}/export", headers=HAa,
                       params={"fmt": "excel"}, timeout=60)
        check("Excel 导出返回 200", rx.status_code == 200, str(rx.status_code))
        wb = load_workbook(io.BytesIO(rx.content))
        cells = [str(c.value) for row in wb.active.iter_rows() for c in row if c.value]
        # 答案行带缩进（"    答案：B"），不能用 startswith 判定
        ans_cells = [c for c in cells if "答案：" in c]
        check("Excel 含答案行", bool(ans_cells), str(cells[:6]))
        check('答案不带 JSON 引号（"B" -> B）',
              bool(ans_cells) and not any('"' in c for c in ans_cells), str(ans_cells[:3]))

        # ---------------- P2-6 零分卷 ----------------
        print("\n=== 6. [P2] 全 0 分试卷应被拒绝 ===")
        rz = httpx.post(f"{api}/question/papers", headers=HAa, json={
            "name": f"零分卷{uniq}", "grade_id": g7["id"], "subject_id": s7["id"],
            "items": [{"question_id": q1, "score": 0}],
        }, timeout=30)
        check("零分卷创建被拒（应 400）", rz.status_code == 400, f"实际 {rz.status_code}")

        print("\n" + "=" * 58)
        if FAILED:
            print(f"失败 {len(FAILED)} 项：")
            for f in FAILED:
                print("  -", f)
            print(f"\n服务日志：{log_path}")
            return 1
        print(f"全部通过：{len(PASSED)} 项（试卷管理缺陷回归）")
        return 0
    finally:
        try:
            proc.terminate()
            proc.wait(timeout=15)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
        logf.close()
        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
