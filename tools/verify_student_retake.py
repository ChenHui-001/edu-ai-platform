"""学生端「查看解析 / 重考」端到端验证。

针对用户报告的两个按钮失效，逐项复现并验证修复：
  A. 查看解析：交卷后 `submissionDetail` 必须返回逐题 answer/analysis，
     前端弹窗才有的可展示（原实现只弹 6 秒 toast，且异常未捕获）。
  B. 重考：allow_retake>1 时首次交卷后必须**还能再进一次**并成功交卷，
     且 attempt 由服务端递增到 2（前端不再硬编码 attempt=1）。
  C. 次数耗尽：allow_retake=1 交卷后，剩余次数必须算成 0，
     `/paper` 也必须暴露 attempt>=max_attempt（前端据此显示「已用完」而非弹回列表）。
  D. 「我的答案」不丢失：详情接口要回传 content，否则结果页/解析里客观题显示未作答。

用法：python tools/verify_student_retake.py
退出码 0 = 全部通过。
"""
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
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  {detail}" if detail and not ok else ""))
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
    tmpdir = tempfile.mkdtemp(prefix="retake_")
    db_path = os.path.join(tmpdir, "test.db")
    log_path = os.path.join(tmpdir, "server.log")

    env = dict(os.environ)
    env.update({
        "LLM_ENABLED": "false", "APP_VERSION": "2.1.0",
        "DATABASE_URL": f"sqlite:///{db_path}",
        "SECRET_KEY": "retake-test-key-0123456789abcdef",
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

        # ---------------- 准备账号与数据 ----------------
        print("\n=== 0. 准备（管理员 + 教师 + 学生 + 试卷 + 任务）===")

        def login(u, p):
            r = httpx.post(f"{api}/auth/login", json={"username": u, "password": p}, timeout=30)
            if r.status_code != 200:
                return None
            d = data_of(r.json())
            return d.get("access_token") or d.get("token")

        adm = login("admin", "Admin@123456")
        if not adm:
            print("管理员登录失败，无法继续")
            return 1
        HA = {"Authorization": f"Bearer {adm}"}

        grades = httpx.get(f"{api}/edu/grades", headers=HA, timeout=30)
        # /edu/grades 的 data 直接是 list（不是 {items:[...]}），兼容两种形态
        g_data = data_of(grades.json())
        g_items = g_data if isinstance(g_data, list) else (g_data.get("items") or [])
        grade = next((g for g in g_items if g.get("grade_num") == 7), g_items[0])
        subs = httpx.get(f"{api}/edu/subjects", headers=HA,
                         params={"grade_id": grade["id"]}, timeout=30)
        s_data = data_of(subs.json())
        s_items = s_data if isinstance(s_data, list) else (s_data.get("items") or [])
        subject = next((s for s in s_items if s["name"] == "数学"), s_items[0])
        print(f"  年级={grade['name']} 学科={subject['name']}")

        # 学生 + 班级
        uniq = str(int(time.time()))[-6:]
        cls = data_of(httpx.post(f"{api}/edu/classes", headers=HA, json={
            "name": f"验证班{uniq}", "grade_id": grade["id"], "head_teacher_id": None,
        }, timeout=30).json())
        cls_id = cls.get("id")
        # 用户创建端点的真实前缀是 /system（不是 /sys），此前写成 /sys/users
        # 导致 404→无 id→学生登录失败→后续全 401，21 项断言集体误报。
        stu = data_of(httpx.post(f"{api}/system/users", headers=HA, json={
            "username": f"rs{uniq}", "real_name": f"重考学生{uniq}",
            "password": "Student@123456", "identity": "student",
            "grade_id": grade["id"], "class_id": cls_id, "status": "active",
            "roles": ["student"],
            # 默认 True 会让 get_current_user 把后续所有请求拦成 403
            # 「首次登录请先修改密码」，测试账号必须显式关闭。
            "must_change_password": False,
        }, timeout=30).json())
        stu_id = stu.get("id")
        check("创建学生成功", bool(stu_id), str(stu)[:160])
        stu_tok = login(f"rs{uniq}", "Student@123456")
        HS = {"Authorization": f"Bearer {stu_tok}"}
        check("学生可登录", bool(stu_tok))

        # 教师 + 题目 + 试卷
        # 必须显式传 roles=["teacher"]：create_user 默认 roles=["student"]，
        # 漏传会得到一个「identity=teacher、角色却是 student」的畸形账号，
        # 后续出题/组卷/发布任务全被 403 拦掉。
        tea = data_of(httpx.post(f"{api}/system/users", headers=HA, json={
            "username": f"rt{uniq}", "real_name": f"验证教师{uniq}",
            "password": "Teacher@123456", "identity": "teacher",
            "grade_id": grade["id"], "status": "active",
            "roles": ["teacher"], "must_change_password": False,
        }, timeout=30).json())
        tea_tok = login(f"rt{uniq}", "Teacher@123456")
        HT = {"Authorization": f"Bearer {tea_tok}"}
        check("教师可登录", bool(tea_tok), str(tea)[:120])

        qids = []
        for q in [
            {"type": "single", "difficulty": "easy", "score": 40,
             "stem": "【重考验证】3x + 5 = 20 的解是？",
             "options": [{"key": "A", "text": "x=3"}, {"key": "B", "text": "x=5"},
                         {"key": "C", "text": "x=15"}],
             "answer": "B", "analysis": "移项得 3x=15，故 x=5。"},
            {"type": "judge", "difficulty": "easy", "score": 30,
             "stem": "【重考验证】方程 x=3 的解在数轴上是一个点。",
             "options": [{"key": "T", "text": "正确"}, {"key": "F", "text": "错误"}],
             "answer": "T", "analysis": "解对应数轴上的点。"},
            {"type": "blank", "difficulty": "medium", "score": 30,
             "stem": "【重考验证】若 5x - 8 = 12，则 x = 【】。",
             "options": [], "answer": "4", "analysis": "5x=20，x=4。"},
        ]:
            q.update({"grade_id": grade["id"], "subject_id": subject["id"],
                      "bank_type": "public"})
            r = httpx.post(f"{api}/question/questions", headers=HT, json=q, timeout=30)
            qid = data_of(r.json()).get("id")
            if qid:
                qids.append(qid)
        check("创建 3 道题", len(qids) == 3, str(len(qids)))

        def make_task(allow_retake, title):
            p = data_of(httpx.post(f"{api}/question/papers", headers=HT, json={
                "name": title, "grade_id": grade["id"], "subject_id": subject["id"],
                "type": "exam", "items": [{"question_id": q, "score": s}
                                          for q, s in zip(qids, [40, 30, 30])],
            }, timeout=30).json())
            pid = p.get("id")
            t = data_of(httpx.post(f"{api}/task/tasks", headers=HT, json={
                "title": title, "type": "exam", "paper_id": pid, "duration": 60,
                "allow_retake": allow_retake, "show_answer": True,
                "student_ids": [stu_id], "class_ids": [],
            }, timeout=30).json())
            return pid, t.get("id")

        # ---------------- B. 重考（allow_retake=2）----------------
        print("\n=== 1. 重考路径（allow_retake=2，应能考两次）===")
        _, tid2 = make_task(2, f"重考验证卷{uniq}")
        check("创建 allow_retake=2 的任务", bool(tid2), str(tid2))

        def take_exam(tid, answers_map=None):
            """完整作答一次：取卷 → 交卷 → 返回 (paper数据, submit结果)"""
            pp = httpx.get(f"{api}/task/tasks/{tid}/paper", headers=HS, timeout=30)
            d = data_of(pp.json())
            items = d.get("items") or []
            payload = []
            for it in items:
                c = (answers_map or {}).get(it["type"])
                if c is not None:
                    payload.append({"paper_item_id": it["paper_item_id"], "content": c})
            sr = httpx.post(f"{api}/task/tasks/{tid}/submit", headers=HS, json={
                "answers": payload, "duration_seconds": 60,
            }, timeout=60)
            return d, sr

        d1, r1 = take_exam(tid2, {"single": "B", "judge": "T", "blank": "4"})
        check("第 1 次交卷成功", r1.status_code == 200, r1.text[:200])
        sub1 = data_of(r1.json())
        # 交卷响应本身不带 attempt（finalize 只回分数类字段），
        # 真实次数要从取卷接口的 my_submission.attempt 读。
        check("第 1 次交卷拿到 submission_id", bool(sub1.get("submission_id")),
              str(sub1.get("submission_id")))

        # 关键：交卷后取卷，应仍允许进入（还有 1 次）
        d2 = data_of(httpx.get(f"{api}/task/tasks/{tid2}/paper", headers=HS,
                               timeout=30).json())
        task2 = d2.get("task") or {}
        used = int((task2.get("my_submission") or {}).get("attempt") or 0)
        mx = int(task2.get("max_attempt") or 1)
        check("第 1 次后 attempt(1) < max_attempt(2)", used < mx, f"used={used} max={mx}")
        check("前端判定「还有剩余次数」= True", mx - used > 0, f"left={mx - used}")

        d3, r2 = take_exam(tid2, {"single": "A", "judge": "T", "blank": "4"})
        check("第 2 次交卷成功（重考真的能交）", r2.status_code == 200, r2.text[:220])
        sub2 = data_of(r2.json())
        check("第 2 次是新的 submission", sub2.get("submission_id") != sub1.get("submission_id"),
              f"{sub1.get('submission_id')} vs {sub2.get('submission_id')}")

        # 用完两次后应拒绝
        _, r3 = take_exam(tid2, {"single": "B", "judge": "T", "blank": "4"})
        check("第 3 次被拒（次数用完）", r3.status_code == 400, r3.text[:200])
        check("拒绝原因含「次数」", "次" in (r3.text or ""), r3.text[:160])

        # 用完后的取卷状态：前端据此显示「已用完」
        d4 = data_of(httpx.get(f"{api}/task/tasks/{tid2}/paper", headers=HS,
                               timeout=30).json())
        t4 = d4.get("task") or {}
        used4 = int((t4.get("my_submission") or {}).get("attempt") or 0)
        mx4 = int(t4.get("max_attempt") or 1)
        check("次数用完后 used >= max", used4 >= mx4, f"used={used4} max={mx4}")

        # ---------------- A/D. 查看解析 ----------------
        print("\n=== 2. 查看解析（逐题答案 + 解析必须完整）===")
        sid = sub2.get("submission_id")
        rd = httpx.get(f"{api}/task/submissions/{sid}", headers=HS, timeout=30)
        check("详情接口 200", rd.status_code == 200, rd.text[:200])
        dd = data_of(rd.json())
        answers = dd.get("answers") or []
        check("返回逐题作答", len(answers) == 3, str(len(answers)))
        check("每条含 answer 字段", all("answer" in a for a in answers))
        check("每条含 analysis 字段", all("analysis" in a for a in answers))
        check("每条含 content（我的答案，不能丢）",
              all(a.get("content") is not None for a in answers),
              str([a.get("content") for a in answers]))
        with_ans = [a for a in answers if a.get("analysis")]
        check("解析内容非空", len(with_ans) == 3, f"{len(with_ans)}/3")
        check("答案内容非空", all(str(a.get("answer") or "").strip() for a in answers))
        check("详情返回 task_title（弹窗标题用）", bool(dd.get("task_title")),
              str(dd.get("task_title")))
        check("详情返回 score", dd.get("score") is not None, str(dd.get("score")))
        check("详情返回 is_correct", all(a.get("is_correct") is not None for a in answers))

        # 第 2 次答错一题，验证解析能区分对错
        wrongs = [a for a in answers if a.get("is_correct") is False]
        check("答错的题能被识别（第2次故意答错单选题）", len(wrongs) >= 1,
              f"错 {len(wrongs)} 题")

        # ---------------- C. 次数耗尽（allow_retake=1）----------------
        print("\n=== 3. allow_retake=1 交卷后必须显示「已用完」===")
        _, tid1 = make_task(1, f"单次考试{uniq}")
        d5, r5 = take_exam(tid1, {"single": "B", "judge": "T", "blank": "4"})
        check("单次任务交卷成功", r5.status_code == 200, r5.text[:200])
        d6 = data_of(httpx.get(f"{api}/task/tasks/{tid1}/paper", headers=HS,
                               timeout=30).json())
        t6 = d6.get("task") or {}
        used6 = int((t6.get("my_submission") or {}).get("attempt") or 0)
        mx6 = int(t6.get("max_attempt") or 1)
        check("max_attempt=1", mx6 == 1, str(mx6))
        check("used >= max（前端显示已用完，不显示重考按钮）", used6 >= mx6,
              f"used={used6} max={mx6}")

        # my/tasks 必须给出 attempt_count，否则前端算不出剩余次数
        mt = httpx.get(f"{api}/task/my/tasks", headers=HS,
                       params={"page": 1, "page_size": 50}, timeout=30)
        check("my/tasks 可读", mt.status_code == 200, mt.text[:160])
        items = data_of(mt.json()).get("items") or []
        target = next((x for x in items if x["id"] == tid1), None)
        check("my/tasks 含 attempt_count（剩余次数依赖它）",
              target is not None and "attempt_count" in target,
              str(sorted(target.keys()))[:200] if target else "任务不在列表")
        if target:
            check("attempt_count=1", int(target.get("attempt_count") or 0) == 1,
                  str(target.get("attempt_count")))
            check("my_submission 非空（「已完成」tab 依赖）",
                  bool(target.get("my_submission")))
            check("allow_retake=1 但前端应算 left=0",
                  int(target.get("allow_retake") or 1) - int(target.get("attempt_count") or 0) <= 0)

        print("\n" + "=" * 58)
        if FAILED:
            print(f"失败 {len(FAILED)} 项：")
            for f in FAILED:
                print("  -", f)
            print(f"\n服务日志：{log_path}")
            return 1
        print(f"全部通过：{len(PASSED)} 项（查看解析 + 重考 + 次数耗尽）")
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
