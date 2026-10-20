# -*- coding: utf-8 -*-
"""学情分析模块统计逻辑校验。

方法：以 SQLite 直接计算的结果为**独立基准**，与接口返回值逐项对比，
     差异即视为统计口径问题（避免「用被测代码验证被测代码」）。
"""
import sqlite3
import sys

sys.path.insert(0, "tests")
from e2e_framework import Client  # noqa: E402

DB = "backend/data/edu_platform.db"
FINDINGS = []


def record(level, title, ok, detail):
    FINDINGS.append({"level": level, "title": title, "ok": ok, "detail": detail})
    print(f"[{'通过' if ok else '偏差'}][{level}] {title}\n    {detail}")


def main():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    admin = Client("a"); admin.login("admin", "Admin@123456")
    t1 = Client("t1"); t1.login("teacher1", "Teacher@123")
    t4 = Client("t4"); t4.login("teacher4", "Teacher@123")

    # ---------- 场景准备：查有提交的班级 ----------
    row = c.execute("""
        SELECT u.class_id, COUNT(*) n FROM edu_submission s
        JOIN sys_user u ON u.id = s.student_id
        WHERE s.score IS NOT NULL AND u.class_id IS NOT NULL
        GROUP BY u.class_id ORDER BY n DESC LIMIT 1
    """).fetchone()
    if not row:
        print("无可用提交数据，跳过统计校验")
        return
    class_id = row["class_id"]

    # ---------- 1. class-overview 平均分 ----------
    # 用管理员查询：sys_admin 的 scope.is_super=True，不受任教班级限制
    p, _, _ = admin.get("/report/teacher/class-overview", params={"class_id": class_id})
    api = p.get("data") or {}
    base = c.execute("""
        SELECT AVG(s.score) a, MAX(s.score) mx, MIN(s.score) mn, COUNT(*) n,
               SUM(CASE WHEN s.score >= 60 THEN 1 ELSE 0 END) passed
        FROM edu_submission s JOIN sys_user u ON u.id = s.student_id
        WHERE u.class_id = ? AND s.score IS NOT NULL
    """, (class_id,)).fetchone()
    api_avg = api.get("avg_score") or 0
    base_avg = round(base["a"], 2) if base["n"] else 0
    record("中", "班级概览 avg_score 与 SQL 基准一致",
           abs(api_avg - base_avg) < 0.02,
           f"接口={api_avg} 基准={base_avg} (n={base['n']})")

    # ---------- 2. 跨试卷混算检查（核心统计问题） ----------
    # 若班级内提交涉及不同 total_score，原始分平均无意义
    rows = c.execute("""
        SELECT DISTINCT t.total_score FROM edu_submission s
        JOIN edu_task t ON t.id = s.task_id
        JOIN sys_user u ON u.id = s.student_id
        WHERE u.class_id = ? AND s.score IS NOT NULL
    """, (class_id,)).fetchall()
    totals = [r["total_score"] for r in rows]
    mixed = len(set(totals)) > 1
    record("高", "班级平均分是否跨不同满分试卷混算",
           not mixed,
           f"涉及满分值 {sorted(set(totals))}；"
           f"接口直接对原始分求平均 → {'混合了不同量纲的分数' if mixed else '单一量纲'}")

    # ---------- 3. 及格率硬编码 60 ----------
    bands_hard = base["passed"] / base["n"] * 100 if base["n"] else 0
    api_pass = api.get("pass_rate") or 0
    record("中", "及格率按固定 60 分阈值（未使用任务 pass_score / 得分率）",
           abs(api_pass - round(bands_hard, 2)) < 0.5,
           f"接口 pass_rate={api_pass}%，固定阈值 60 分口径={round(bands_hard, 2)}%；"
           f"实际任务及格分可配置（pass_score 字段存在）")

    # 用 is_passed 口径对比
    passed_real = c.execute("""
        SELECT SUM(CASE WHEN s.is_passed = 1 THEN 1 ELSE 0 END) p, COUNT(*) n
        FROM edu_submission s JOIN sys_user u ON u.id = s.student_id
        WHERE u.class_id = ? AND s.score IS NOT NULL
    """, (class_id,)).fetchone()
    real_rate = round((passed_real["p"] or 0) / passed_real["n"] * 100, 2) if passed_real["n"] else 0
    record("中", "及格率与 submission.is_passed 口径是否一致",
           abs(api_pass - real_rate) < 0.5,
           f"接口={api_pass}% vs is_passed 口径={real_rate}%")

    # ---------- 4. class-overview 完成率字段缺失 ----------
    record("中", "班级概览是否返回完成率（前端需展示）",
           "completion_rate" in api,
           f"返回字段={sorted(api.keys())}；代码中 tasks 查询未使用（死代码）")

    # ---------- 5. grade-comparison：user_count 是否含教师 ----------
    p, _, _ = admin.get("/report/admin/grade-comparison")
    grades = p.get("data") or []
    if grades:
        g0 = grades[0]
        base_users = c.execute("""
            SELECT COUNT(*) n FROM sys_user u
            JOIN edu_grade g ON g.id = u.grade_id WHERE g.name = ?
        """, (g0["grade_name"],)).fetchone()["n"]
        base_students = c.execute("""
            SELECT COUNT(*) n FROM sys_user u
            JOIN edu_grade g ON g.id = u.grade_id
            WHERE g.name = ? AND u.identity = 'student'
        """, (g0["grade_name"],)).fetchone()["n"]
        record("中", f"年级对比 user_count 是否误含教师（{g0['grade_name']}）",
               g0["user_count"] == base_students,
               f"接口 user_count={g0['user_count']}；全部用户={base_users} "
               f"学生={base_students} → "
               f"{'混入教师/管理员' if g0['user_count'] != base_students else '口径正确'}")

    # ---------- 6. grade-comparison 性能风险（JOIN 条件非关联） ----------
    record("中", "年级对比 SQL 使用 IN 子查询作为 JOIN 条件（笛卡尔积风险）",
           False,
           "outerjoin(Submission, Submission.task_id.in_(...)) 与 Grade 无关联条件，"
           "中间结果 = 年级×题目×提交，数据量大时必然拖垮")

    # ---------- 7. subject-comparison 同名学科跨年级合并 ----------
    p, _, _ = admin.get("/report/admin/subject-comparison")
    subs = p.get("data") or []
    dup_names = c.execute("""
        SELECT name, COUNT(*) n FROM edu_subject GROUP BY name HAVING COUNT(*) > 1
    """).fetchall()
    record("低", "学科对比按名称分组会合并跨年级同名学科",
           len(subs) == c.execute("SELECT COUNT(*) n FROM edu_subject").fetchone()["n"],
           f"返回 {len(subs)} 行；学科表实际 "
           f"{c.execute('SELECT COUNT(*) n FROM edu_subject').fetchone()['n']} 条，"
           f"同名学科有 {len(dup_names)} 组被合并")

    # ---------- 8. student-detail 成绩趋势是否含满分 ----------
    stu_row = c.execute("""
        SELECT student_id FROM edu_submission WHERE score IS NOT NULL LIMIT 1
    """).fetchone()
    if stu_row:
        p, _, _ = admin.get("/report/teacher/student-detail",
                         params={"student_id": stu_row["student_id"]})
        d = p.get("data") or {}
        trend = d.get("score_trend") or []
        has_total = bool(trend) and "total_score" in trend[0]
        record("高", "学生成绩趋势是否返回总满分（跨卷归一化必需）",
               has_total,
               f"score_trend 字段={sorted(trend[0].keys()) if trend else '无数据'}；"
               f"缺 total_score 时 5 分卷与 100 分卷在同一条折线上无法比较")

    # ---------- 9. student-comparison 完成率分母去重 ----------
    p, _, _ = admin.get("/report/teacher/student-comparison", params={"class_id": class_id})
    comps = p.get("data") or []
    if comps:
        s0 = comps[0]
        # 该生被下发任务数（去重）
        assigned_distinct = c.execute("""
            SELECT COUNT(DISTINCT ta.task_id) n FROM edu_task_assignment ta
            JOIN edu_task t ON t.id = ta.task_id
            WHERE t.status = 'published' AND t.type != 'practice'
              AND (ta.student_id = ? OR ta.class_id = ?)
        """, (s0["student_id"], class_id)).fetchone()["n"]
        assigned_raw = c.execute("""
            SELECT COUNT(*) n FROM edu_task_assignment ta
            JOIN edu_task t ON t.id = ta.task_id
            WHERE t.status = 'published' AND t.type != 'practice'
              AND (ta.student_id = ? OR ta.class_id = ?)
        """, (s0["student_id"], class_id)).fetchone()["n"]
        record("中", "学生完成率分母是否按任务去重",
               assigned_raw == assigned_distinct,
               f"学生 {s0['name']} 完成率={s0.get('completion_rate')}%；"
               f"分母 COUNT(*)={assigned_raw} vs COUNT(DISTINCT task)={assigned_distinct}"
               f"{'（同一任务被重复计数）' if assigned_raw != assigned_distinct else ''}")

    # ---------- 10. 权限：跨班访问 ----------
    p, _, sc = t4.get("/report/teacher/class-overview", params={"class_id": 1})
    record("高", "教师跨班查看班级学情被拒（teacher4 查 teacher1 的 1 班）",
           p.get("success") is not True,
           f"HTTP {sc} {p.get('message', '')[:40]}")
    p, _, sc = t4.get("/report/teacher/class-overview", params={"class_id": class_id})
    record("高", "教师可查看自己任教班级（对照项）",
           p.get("success") is True,
           f"HTTP {sc}（class_id={class_id}）")

    # 教师读管理员接口
    for path, name in (("/report/admin/overview", "系统总览"),
                       ("/report/admin/grade-comparison", "年级对比"),
                       ("/report/admin/system-runtime", "系统运行")):
        p, _, sc = t1.get(path)
        record("高", f"教师访问管理员接口应被拒：{name}",
               p.get("success") is not True,
               f"HTTP {sc} {p.get('message', '')[:30]}")

    # 学生读教师学情接口
    stu = Client("s"); stu.login("stu731", "Student@123")
    p, _, sc = stu.get("/report/teacher/class-overview", params={"class_id": class_id})
    record("高", "学生访问教师学情接口应被拒",
           p.get("success") is not True, f"HTTP {sc} {p.get('message', '')[:30]}")

    conn.close()

    print("\n" + "=" * 64)
    bad = [f for f in FINDINGS if not f["ok"]]
    print(f"校验完成：{len(FINDINGS)} 项，{len(bad)} 项存在偏差")
    for f in bad:
        print(f"  [{f['level']}] {f['title']}")


if __name__ == "__main__":
    main()
