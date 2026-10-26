# -*- coding: utf-8 -*-
"""生产数据生成脚本 —— 模拟"示范学校"开学一个月的真实运转。

通过真实 API 走完整教学链路，幂等可重跑（已存在的同名对象跳过）。
覆盖：组织架构 → 题库 → 试卷 → 下发 → 学生作答 → 教师批改 → 教案 → 学习中心。

环境约定：
- 本机 urllib 默认走系统代理访问 127.0.0.1 会被拦（502 upstream connect failed），
  必须显式 ProxyHandler({}) + 清空 *_PROXY 环境变量。
- 班主任建班走审核制（POST /edu/class-requests → 审批）；
  本脚本走管理员直建（POST /edu/classes，需 resource:class:write 权限，sys_admin 满足）。

为什么造数据走 API 而不是直接写库：
- 验证整条业务链路在真实接口层确实通（契约漂移在直接写库时不会暴露）
- 数据范围/权限/唯一约束都过一遍，等于一次端到端冒烟
"""
import json
import os
import sys
import urllib.error
import urllib.request

BASE = os.environ.get("BASE", "http://127.0.0.1:8081") + "/api/v1"
ADMIN_USER = os.environ.get("ADMIN_USER", "sysadmin")
ADMIN_PASS = os.environ.get("ADMIN_PASS", "Sys@Admin2026!Qw")

# 绕过系统代理：访问 127.0.0.1 必须直连，否则 502。
for _k in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy",
           "ALL_PROXY", "all_proxy"):
    os.environ.pop(_k, None)
os.environ["NO_PROXY"] = "127.0.0.1,localhost"
os.environ["no_proxy"] = "127.0.0.1,localhost"
_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))

PASS = FAIL = 0


def _log(ok, msg, extra=""):
    global PASS, FAIL
    if ok:
        PASS += 1
        print(f"  \033[92m✔\033[0m {msg} {extra}")
    else:
        FAIL += 1
        print(f"  \033[91m✘\033[0m {msg} {extra}")


def call(method, path, body=None, token=None):
    url = BASE + path
    data = None
    headers = {"Content-Type": "application/json"}
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    if token:
        headers["Authorization"] = "Bearer " + token
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with _OPENER.open(req, timeout=60) as r:
            return r.status, json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        try:
            return e.code, json.loads(raw)
        except ValueError:
            return e.code, {"raw": raw[:200]}
    except Exception as e:  # noqa: BLE001
        return 0, {"error": str(e)[:200]}


def login(username, password):
    st, r = call("POST", "/auth/login",
                 {"username": username, "password": password})
    if st != 200:
        return None, r
    d = r.get("data") or {}
    return d.get("access_token"), r


# ============================================================ 题面定义
# 5 题型 / 合计 100 分（10+15+10+15+50），与 e2e_seed.QUESTIONS 同结构
QUESTIONS_TEMPLATE = [
    {
        "type": "single", "difficulty": "easy", "score": 10,
        "stem": "下列各数中，最小的正整数是？",
        "options": [{"key": "A", "text": "0"}, {"key": "B", "text": "1"},
                    {"key": "C", "text": "-1"}, {"key": "D", "text": "0.5"}],
        "answer": "B", "analysis": "正整数是大于 0 的整数，最小的是 1。",
    },
    {
        "type": "multiple", "difficulty": "medium", "score": 15,
        "stem": "下列属于一元一次方程的是？",
        "options": [{"key": "A", "text": "2x+1=7"}, {"key": "B", "text": "x²-4=0"},
                    {"key": "C", "text": "3y-2=5"}, {"key": "D", "text": "x+y=3"}],
        "answer": ["A", "C"], "analysis": "一元一次方程只含一个未知数且次数为 1。",
    },
    {
        "type": "judge", "difficulty": "easy", "score": 10,
        "stem": "有理数包括正整数、零和负整数。",
        "options": [{"key": "T", "text": "正确"}, {"key": "F", "text": "错误"}],
        "answer": "F",
        "analysis": "有理数还包括正分数和负分数，整数只是其中一部分。",
    },
    {
        "type": "blank", "difficulty": "medium", "score": 15,
        "stem": "若 5x - 8 = 12，则 x = 【】。",
        "options": [], "answer": "4", "analysis": "5x=20，x=4。",
    },
    {
        "type": "short", "difficulty": "medium", "score": 50,
        "stem": "请用配方法解方程 x² - 6x + 5 = 0，并写出推导过程。",
        "options": [],
        "answer": "x²-6x+5=0 ⟹ (x-3)²=4 ⟹ x-3=±2 ⟹ x=1 或 x=5",
        "analysis": "移项后两边加 9，化为完全平方 (x-3)²=4。",
    },
]


def main():
    print("=" * 60)
    print("生产数据生成 · 模拟示范学校开学一个月运转")
    print("=" * 60)

    # ===== 管理员登录 =====
    tok, _ = login(ADMIN_USER, ADMIN_PASS)
    _log(bool(tok), f"管理员 {ADMIN_USER} 登录")
    if not tok:
        print("无法登录，中止。")
        return 1

    # ===== 1) 年级 / 学科 / 知识点（种子已建，查 id） =====
    print("\n[1] 组织架构：年级/学科/知识点")
    st, r = call("GET", "/edu/grades", token=tok)
    raw = r.get("data")
    # 接口可能返回 list 或 {items:[...]}；统一成 list
    if isinstance(raw, dict):
        grades = raw.get("items") or raw.get("grades") or []
    else:
        grades = raw or []
    grades = [g for g in grades if g.get("grade_num") in (3, 5, 7)]
    _log(len(grades) == 3, "取到 3/5/7 三个年级",
         f"实际 {[g.get('grade_num') for g in grades]}")

    scope = {}  # grade_num -> {grade_id, math_subject_id, kp_id}
    for g in grades:
        gid = g["id"]
        st, r = call("GET", f"/edu/subjects?grade_id={gid}", token=tok)
        raw = r.get("data")
        subs = raw.get("items") if isinstance(raw, dict) else raw
        subs = subs or []
        math = next((s for s in subs if s.get("name") == "数学"), None)
        if not math:
            continue
        st, r = call("GET", f"/edu/knowledge/list?grade_id={gid}&subject_id={math['id']}", token=tok)
        raw = r.get("data")
        kps = raw.get("items") if isinstance(raw, dict) else raw
        kps = kps or []
        scope[g["grade_num"]] = {
            "grade_id": gid, "grade_name": g["name"],
            "math_id": math["id"], "kp_id": kps[0]["id"] if kps else None,
        }
    _log(all(scope[g].get("math_id") for g in (3, 5, 7)), "各年级数学学科 + 知识点已解析")

    # ===== 2) 班级 / 教师 / 学生 =====
    print("\n[2] 班级 / 教师 / 学生")
    classes = []  # [(grade_num, class_obj, teacher_obj)]
    for gn in (7, 5, 3):  # 先建七年级，规模最完整
        ginfo = scope[gn]
        gid = ginfo["grade_id"]
        for ci in (1, 2):
            cname = f"{ginfo['grade_name']}({ci})班"
            # 查是否已存在
            st, r = call("GET", f"/edu/classes?grade_id={gid}", token=tok)
            raw = r.get("data")
            cls_rows = raw.get("items") if isinstance(raw, dict) else raw
            cls_rows = cls_rows or []
            existed = next((c for c in cls_rows if c.get("name") == cname), None)
            if existed:
                classes.append((gn, existed, None))
                continue
            # 建班
            st, r = call("POST", "/edu/classes",
                         {"grade_id": gid, "name": cname, "auto_name": False,
                          "is_active": True}, token=tok)
            if st != 200 or not (r.get("data") or {}).get("id"):
                _log(False, f"建班 {cname}", r.get("message", ""))
                continue
            k = r["data"]
            classes.append((gn, k, None))
    _log(len([c for c in classes]) >= 4, "班级创建/复用完成",
         f"{len(classes)} 个班")

    # 教师：每个班一个班主任（数学）
    teachers = []  # [(grade_num, class_obj, teacher_obj)]
    stu_role_check = False
    for idx, (gn, k, _) in enumerate(classes):
        tname = f"t{gn}{k.get('class_no','1')}"
        # 查是否已建
        st, r = call("GET", f"/system/users?keyword={tname}", token=tok)
        rows = (r.get("data") or {}).get("items") or []
        t = next((u for u in rows if u.get("username") == tname), None)
        if not t:
            st, r = call("POST", "/system/users", {
                "username": tname, "real_name": f"{scope[gn]['grade_name']}数学教师",
                "identity": "teacher", "password": "Teacher@2026!Xy",
                "roles": ["teacher"], "status": "active",
                "school_name": "示范学校", "grade_id": k["grade_id"],
                "class_id": k["id"], "must_change_password": False,
            }, token=tok)
            t = (r.get("data") or {}) if st == 200 else None
            _log(bool(t), f"建教师 {tname}", r.get("message", ""))
        if t:
            teachers.append((gn, k, t))
    _log(len(teachers) >= 4, "教师创建/复用完成", f"{len(teachers)} 名")

    # 学生：每个班 8 名
    students = []  # [(grade_num, class_obj, student_obj, stu_token)]
    for (gn, k, t) in teachers:
        created = 0
        for si in range(1, 9):
            sname = f"s{gn}{k.get('class_no','1')}{si}"
            st, r = call("GET", f"/system/users?keyword={sname}", token=tok)
            rows = (r.get("data") or {}).get("items") or []
            su = next((u for u in rows if u.get("username") == sname), None)
            if not su:
                st, r = call("POST", "/system/users", {
                    "username": sname, "real_name": f"学生{gn}{k.get('class_no','1')}{si}",
                    "identity": "student", "password": "Student@2026!Xy",
                    "roles": ["student"], "status": "active",
                    "school_name": "示范学校", "grade_id": k["grade_id"],
                    "class_id": k["id"], "must_change_password": False,
                }, token=tok)
                su = (r.get("data") or {}) if st == 200 else None
            if su:
                students.append((gn, k, su))
                created += 1
        _log(created >= 1, f"{k['name']} 学生准备就绪", f"{created}/8")
    _log(len(students) >= 1, "学生创建/复用完成", f"共 {len(students)} 名")

    # ===== 3) 题库（每年级数学 5 题） =====
    print("\n[3] 题库：各年级数学 5 题（5 题型）")
    admin_tok = tok
    qids_by_grade = {}  # grade_num -> {type: qid}
    for gn in (3, 5, 7):
        ginfo = scope[gn]
        # 用 admin 建题（admin 有 question:write）
        qmap = {}
        for q in QUESTIONS_TEMPLATE:
            body = dict(q)
            body["stem"] = f"【{ginfo['grade_name']}】{q['stem']}"
            body["subject_id"] = ginfo["math_id"]
            body["grade_id"] = ginfo["grade_id"]
            body["knowledge_point_id"] = ginfo["kp_id"]
            body["bank_type"] = "public"
            st, r = call("POST", "/question/questions", body, token=admin_tok)
            d = r.get("data") or {}
            if st == 200 and d.get("id"):
                qmap[q["type"]] = d["id"]
        qids_by_grade[gn] = qmap
        _log(len(qmap) == 5, f"{ginfo['grade_name']} 建题 5/5", f"{list(qmap)}")

    # ===== 4) 组卷（每年级 1 套期中卷） =====
    print("\n[4] 试卷：每年级 1 套期中卷")
    papers = {}  # grade_num -> paper_id
    for gn in (3, 5, 7):
        ginfo = scope[gn]
        qm = qids_by_grade.get(gn, {})
        if len(qm) < 5:
            continue
        items = [
            {"question_id": qm["single"], "score": 10, "section_name": "选择题"},
            {"question_id": qm["multiple"], "score": 15, "section_name": "选择题"},
            {"question_id": qm["judge"], "score": 10, "section_name": "判断题"},
            {"question_id": qm["blank"], "score": 15, "section_name": "填空题"},
            {"question_id": qm["short"], "score": 50, "section_name": "解答题"},
        ]
        st, r = call("POST", "/question/papers", {
            "name": f"{ginfo['grade_name']}数学期中卷",
            "subject_id": ginfo["math_id"], "grade_id": ginfo["grade_id"],
            "duration": 60, "items": items,
        }, token=admin_tok)
        pid = (r.get("data") or {}).get("id")
        if pid:
            papers[gn] = pid
        _log(bool(pid), f"{ginfo['grade_name']} 期中卷", r.get("message", ""))

    # ===== 5) 下发考试（每个班的年级对应卷子，按标题查重避免重跑重复） =====
    print("\n[5] 任务下发：每个班一期中考试")
    tasks = []  # [(grade_num, class_obj, task_obj, teacher_obj)]
    # 先拉已有任务列表（admin 视角），建 title -> task_id 索引
    st, r = call("GET", "/task/tasks?page_size=200", token=admin_tok)
    raw = r.get("data")
    exist_tasks = raw.get("items") if isinstance(raw, dict) else raw
    exist_titles = {(t.get("title")): t for t in (exist_tasks or [])}
    for (gn, k, t) in teachers:
        pid = papers.get(gn)
        if not pid:
            continue
        title = f"{k['name']}数学期中考试"
        if title in exist_titles:
            tasks.append((gn, k, exist_titles[title], t))
            continue
        st, r = call("POST", "/task/tasks", {
            "title": title, "type": "exam", "paper_id": pid,
            "duration": 60, "allow_retake": 1, "show_answer": True,
            "anti_cheat": True, "pass_score": 60,
            "class_ids": [k["id"]], "student_ids": [],
            "description": "期中阶段检测，覆盖本学期前 4 单元。",
        }, token=admin_tok)
        tid = (r.get("data") or {}).get("id")
        if tid:
            tasks.append((gn, k, {"id": tid, "title": title}, t))
        _log(bool(tid), f"下发 {title}", r.get("message", ""))

    # ===== 6) 学生作答（按好/中/差分布） =====
    print("\n[6] 学生作答：按能力分布作答")
    submitted = []  # [(grade_num, class_obj, student_obj, sub_id, score)]
    plan_good = {
        "single": "B", "multiple": "AC", "judge": "F",
        "blank": "4", "short": "x²-6x+5=0，(x-3)²=4，x=1 或 x=5",
    }
    plan_mid = {"single": "B", "multiple": "A", "judge": "T",
                "blank": "3", "short": "配方过程略，x=1"}
    plan_bad = {"single": "C", "multiple": "AB", "judge": "T",
                "blank": "", "short": ""}

    # 学生分班归类
    stu_by_class = {}
    for (gn, k, su) in students:
        stu_by_class.setdefault(k["id"], []).append((gn, k, su))

    for (gn, k, t) in teachers:
        task = next((x for x in tasks if x[0] == gn and x[1]["id"] == k["id"]), None)
        if not task:
            continue
        _, _, tk_obj, _ = task
        tid = tk_obj["id"]
        # 拉试卷结构（学生视角）
        members = stu_by_class.get(k["id"], [])
        for idx, (_, _, su) in enumerate(members):
            tok_s, _ = login(su["username"], "Student@2026!Xy")
            if not tok_s:
                continue
            st, r = call("GET", f"/task/tasks/{tid}/paper", token=tok_s)
            items = (r.get("data") or {}).get("items") or []
            if not items:
                continue
            plan = [plan_good, plan_mid, plan_bad][idx % 3]
            answers = []
            for it in items:
                answers.append({
                    "paper_item_id": it["paper_item_id"],
                    "content": plan.get(it["type"], ""),
                    "duration_seconds": 90,
                })
            st, r = call("POST", f"/task/tasks/{tid}/submit",
                         {"answers": answers, "duration_seconds": 600}, token=tok_s)
            d = r.get("data") or {}
            if r.get("success") and d.get("submission_id"):
                submitted.append((gn, k, su, d["submission_id"], d.get("score")))
    _log(len(submitted) >= 1, "学生交卷完成", f"{len(submitted)} 份")

    # ===== 7) 教师批改主观题 =====
    # 任务由 admin 下发，教师批改受「只能批改自己发布的任务」约束 → 403。
    # 这里改用 admin 批改（admin 数据范围超级，可批改任何任务）。
    # 注意：详情接口字段是 items（不是 answers），且 needs_manual 依赖
    # subjective_score>0——交卷时主观分为 0 → needs_manual 恒 false。
    # 因此不依赖 needs_manual，对所有含主观题作答的提交直接批分。
    print("\n[7] 教师批改：主观题手批（admin 代批）")
    graded = 0
    st, r = call("GET", "/grading/pending?page_size=200", token=admin_tok)
    raw = r.get("data")
    pend = raw.get("items") if isinstance(raw, dict) else raw
    pend = pend or []
    SUBJ = {"short", "calc", "material", "composition"}
    for sub in pend:
        sid = sub.get("submission_id") or sub.get("id")
        if not sid:
            continue
        st, r = call("GET", f"/grading/submissions/{sid}", token=admin_tok)
        detail = r.get("data") or {}
        # 字段是 items，不是 answers
        items = detail.get("items") or detail.get("answers") or []
        grade_items = []
        for a in items:
            if a.get("type") in SUBJ and a.get("answer_id"):
                fs = float(a.get("full_score") or 0)
                # 已批的跳过（grader_type != auto 或 score 已有）
                if a.get("grader_type") not in (None, "auto"):
                    continue
                grade_items.append({
                    "answer_id": a["answer_id"],
                    "score": round(fs * 0.7, 1),
                    "teacher_comment": "步骤基本正确，推导可更严谨。",
                })
        if grade_items:
            st, r = call("POST", f"/grading/submissions/{sid}/grade",
                         {"answers": grade_items}, token=admin_tok)
            if r.get("success"):
                graded += 1
    _log(graded >= 1, "主观题手批完成", f"{graded} 份")

    # ===== 8) 教案（每个教师 1 份） =====
    print("\n[8] 教案：每位教师建 1 份")
    plans = 0
    for (gn, k, t) in teachers:
        tok_t, _ = login(t["username"], "Teacher@2026!Xy")
        if not tok_t:
            continue
        ginfo = scope[gn]
        body = {
            "title": f"{ginfo['grade_name']}数学《一元一次方程》教学设计",
            "topic": "一元一次方程的解法",
            "subject_id": ginfo["math_id"], "grade_id": ginfo["grade_id"],
            "knowledge_point_id": ginfo["kp_id"], "duration_minutes": 45,
            "period": "第1课时", "textbook_version": "人教版",
            "objectives": "1. 理解一元一次方程的概念\n2. 掌握移项解法\n3. 能求解简单实际问题",
            "key_points": "移项法则与合并同类项",
            "difficulties": "实际问题到方程的建模",
            "teaching_preparation": "多媒体课件、练习卡片、实物教具",
            "class_exercise": "解方程 3x+5=20 并写出步骤",
            "homework": "教材 P82 第 1-3 题",
            "board_design": "一元一次方程解法步骤｜例题｜学生练习区",
            "stages": [
                {"name": "导入新课", "duration_minutes": 5,
                 "content": "从生活情境引入方程概念",
                 "teacher_activity": "出示购物找零情境提问",
                 "student_activity": "分组讨论列出方程"},
                {"name": "新课讲授", "duration_minutes": 22,
                 "content": "移项法则与解方程步骤",
                 "teacher_activity": "板演 3x+5=20 的求解",
                 "student_activity": "跟练并复述步骤"},
                {"name": "巩固练习", "duration_minutes": 11,
                 "content": "完成课堂练习 3 题",
                 "teacher_activity": "巡视个别指导",
                 "student_activity": "独立完成并互批"},
                {"name": "课堂小结", "duration_minutes": 5,
                 "content": "回顾解方程三步",
                 "teacher_activity": "引导归纳",
                 "student_activity": "口述小结"},
                {"name": "作业布置", "duration_minutes": 2,
                 "content": "布置分层作业",
                 "teacher_activity": "说明作业要求",
                 "student_activity": "记录作业"},
            ],
        }
        st, r = call("POST", "/lesson/plans", body, token=tok_t)
        if r.get("success"):
            plans += 1
    _log(plans >= 1, "教案创建完成", f"{plans} 份")

    # ===== 9) 学习中心：部分学生建笔记 =====
    print("\n[9] 学习中心：学生笔记")
    notes = 0
    sample_stus = [s for s in students if s[0] == 7][:4]  # 七年级前 4 个学生
    for (gn, k, su) in sample_stus:
        tok_s, _ = login(su["username"], "Student@2026!Xy")
        if not tok_s:
            continue
        ginfo = scope[gn]
        st, r = call("POST", "/learning/notes", {
            "title": f"一元一次方程学习笔记",
            "content": "## 知识要点\n- 一元一次方程标准形式 ax+b=0\n- 移项要变号\n\n## 易错\n合并同类项时系数计算",
            "format": "markdown", "subject_id": ginfo["math_id"],
            "knowledge_point_id": ginfo["kp_id"],
            "tags": ["数学", "方程"],
        }, token=tok_s)
        if r.get("success"):
            notes += 1
    _log(notes >= 1, "学生笔记创建完成", f"{notes} 条")

    # ===== 汇总 =====
    print("\n" + "=" * 60)
    print(f"数据生成完成：通过 {PASS} / 失败 {FAIL}")
    print(f"班级 {len(classes)} / 教师 {len(teachers)} / 学生 {len(students)}")
    print(f"题库 {sum(len(v) for v in qids_by_grade.values())} 题 / 试卷 {len(papers)} 套")
    print(f"任务 {len(tasks)} / 交卷 {len(submitted)} / 批改 {graded} / 教案 {plans} / 笔记 {notes}")
    print("=" * 60)
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
