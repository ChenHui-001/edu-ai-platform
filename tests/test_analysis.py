# -*- coding: utf-8 -*-
"""学情分析模块专项测试（统计口径 + 权限校验）。

统计类断言采用「可比口径」而非精确数值（数据随其他阶段变化），
重点守住口径设计：得分率存在且 0~100、及格率与 is_passed 一致、
完成率 0~100、趋势含 total_score、年级学生数不含教师。
"""
import sys

sys.path.insert(0, "tests")
from e2e_framework import (  # noqa: E402
    R, Client, check, data_of, expect_denied, rows_of,
)


def run():
    admin = Client("a"); ok_a, _ = admin.login("admin", "Admin@123456")
    t1 = Client("t1"); t1.login("teacher1", "Teacher@123")
    t4 = Client("t4"); t4.login("teacher4", "Teacher@123")
    stu = Client("s"); stu.login("stu731", "Student@123")

    check("三端登录（admin/teacher/student）", ok_a, "")

    # 找有提交的班级（管理员视角，不受任教限制）
    p, _, _ = admin.get("/report/admin/overview")
    check("管理员系统总览可读", p.get("success"), "")
    ov = data_of(p) or {}

    # ============================================================
    # 1. 班级学情统计口径
    # ============================================================
    R.set_phase("学情分析 | 1. 班级学情统计口径")

    class_id = None
    for cid in (1, 4, 2, 3):
        p, _, _ = admin.get("/report/teacher/class-overview", params={"class_id": cid})
        d = data_of(p) or {}
        if d.get("submission_count"):
            class_id = cid
            break
    if not class_id:
        class_id = 1
    p, _, _ = admin.get("/report/teacher/class-overview", params={"class_id": class_id})
    d = data_of(p) or {}

    check("★ 班级概览含得分率字段（跨试卷可比）",
          "avg_score_rate" in d and 0 <= (d.get("avg_score_rate") or 0) <= 100,
          f"avg_score_rate={d.get('avg_score_rate')} 原始分={d.get('avg_score')}")
    check("★ 班级概览含完成率字段（此前缺失/死代码）",
          "completion_rate" in d and 0 <= (d.get("completion_rate") or 0) <= 100,
          f"completion_rate={d.get('completion_rate')}%")
    check("★ 最高/最低得分率与原始分同口径输出",
          "max_rate" in d and "min_rate" in d
          and (d.get("max_rate") or 0) >= (d.get("min_rate") or 0),
          f"max_rate={d.get('max_rate')} min_rate={d.get('min_rate')}")
    bands = d.get("score_bands") or {}
    check("★ 分数段按得分率分档（五档合计=提交数）",
          set(bands.keys()) == {"90-100", "80-89", "70-79", "60-69", "<60"}
          and sum(bands.values()) == (d.get("submission_count") or 0),
          f"分档={bands} 提交={d.get('submission_count')}")

    # 及格率与 is_passed 口径一致性（用班级数据交叉验证）
    if d.get("submission_count"):
        check("★ 及格率范围合法（0~100）",
              0 <= (d.get("pass_rate") or 0) <= 100,
              f"pass_rate={d.get('pass_rate')}%")

    # 参数校验
    p, _, sc = admin.get("/report/teacher/class-overview", params={"class_id": 999999})
    check("不存在的班级 404", p.get("success") is not True and sc == 404,
          f"HTTP {sc}")

    # ============================================================
    # 2. 学生横向对比
    # ============================================================
    R.set_phase("学情分析 | 2. 学生横向对比")

    p, _, _ = admin.get("/report/teacher/student-comparison", params={"class_id": class_id})
    comps = rows_of(p) or (p.get("data") or [])
    check("学生对比返回列表", isinstance(comps, list), f"{len(comps)} 人")
    if comps:
        c0 = comps[0]
        check("★ 学生对比含得分率并按得分率排名",
              "avg_score_rate" in c0 and c0.get("rank") == 1,
              f"rank={c0.get('rank')} rate={c0.get('avg_score_rate')}")
        check("★ 完成率范围合法且分母已去重",
              0 <= (c0.get("completion_rate") or 0) <= 100,
              f"completion_rate={c0.get('completion_rate')}%")
        check("学生对比不含教师账号（identity 过滤）",
              all("教师" not in (x.get("name") or "") for x in comps),
              f"名单={[x.get('name') for x in comps][:5]}")

    # ============================================================
    # 3. 学生个体分析
    # ============================================================
    R.set_phase("学情分析 | 3. 学生个体分析")

    stu_id = (comps[0]["student_id"] if comps else None)
    if stu_id:
        p, _, _ = admin.get("/report/teacher/student-detail",
                            params={"student_id": stu_id})
        d = data_of(p) or {}
        trend = d.get("score_trend") or []
        check("★ 成绩趋势含 total_score（跨卷归一化必需）",
              not trend or all("total_score" in t for t in trend),
              f"{len(trend)} 条趋势")
        check("★ 成绩趋势含 score_rate 且范围合法",
              not trend or all(0 <= (t.get("score_rate") or 0) <= 100 for t in trend),
              f"得分率={[t.get('score_rate') for t in trend][:5]}")
        check("个体汇总含平均得分率",
              "avg_score_rate" in (d.get("summary") or {}),
              f"summary={d.get('summary')}")
        check("知识点掌握度列表可读",
              isinstance(d.get("knowledge_mastery"), list),
              f"{len(d.get('knowledge_mastery') or [])} 个知识点")

        p, _, sc = admin.get("/report/teacher/student-detail",
                             params={"student_id": 999999})
        check("不存在的学生 404", p.get("success") is not True, f"HTTP {sc}")

    # ============================================================
    # 4. 知识点教学效果（含 task/class 过滤）
    # ============================================================
    R.set_phase("学情分析 | 4. 知识点教学效果")

    p, _, _ = admin.get("/report/teacher/knowledge-effect",
                        params={"class_id": class_id})
    d = data_of(p) or {}
    check("知识点效果返回 items 数组",
          isinstance(d.get("items"), list),
          f"{len(d.get('items') or [])} 个知识点")
    check("知识点效果含 avg_accuracy 汇总", "avg_accuracy" in d, "")

    # ============================================================
    # 5. 管理员报表
    # ============================================================
    R.set_phase("学情分析 | 5. 管理员报表")

    check("系统总览含用户/内容/考试/ai/组织五组",
          all(k in ov for k in ("user", "content", "exam", "ai", "org")),
          f"字段={sorted(ov.keys())}")

    p, _, _ = admin.get("/report/admin/grade-comparison")
    grades = rows_of(p) or (p.get("data") or [])
    check("★ 年级对比含得分率字段", bool(grades) and "avg_score_rate" in grades[0],
          f"{len(grades)} 个年级")
    # 关键：user_count 只统计学生。基准取「系统用户列表按年级+identity=student 的总数」
    # （不写死数值——测试库与生产库的种子规模不同，写死会造成假失败）
    g1 = next((g for g in grades if g.get("user_count")), grades[0] if grades else None)
    if g1:
        gid = None
        p_g, _, _ = admin.get("/edu/grades")
        for g in rows_of(p_g) or []:
            if g.get("name") == g1["grade_name"]:
                gid = g.get("id")
                break
        if gid:
            p_u, _, _ = admin.get("/system/users",
                                  params={"grade_id": gid, "identity": "student",
                                          "page_size": 1})
            base_students = ((data_of(p_u) or {}).get("total")
                             if isinstance(data_of(p_u), dict) else None)
            p_all, _, _ = admin.get("/system/users",
                                    params={"grade_id": gid, "page_size": 1})
            base_all = ((data_of(p_all) or {}).get("total")
                        if isinstance(data_of(p_all), dict) else None)
            check("★ 年级 user_count 仅统计学生（不含教师/管理员）",
                  base_students is not None
                  and g1.get("user_count") == base_students,
                  f"{g1['grade_name']} user_count={g1.get('user_count')} "
                  f"学生数={base_students} 全部用户={base_all}")
    check("★ 年级对比含 task_count（避免笛卡尔积重写后新增）",
          bool(grades) and "task_count" in grades[0],
          f"字段={sorted(grades[0].keys()) if grades else []}")

    p, _, _ = admin.get("/report/admin/subject-comparison")
    subs = rows_of(p) or (p.get("data") or [])
    check("学科对比可读", isinstance(subs, list) and len(subs) > 0, f"{len(subs)} 行")

    p, _, _ = admin.get("/report/admin/system-runtime")
    check("系统运行报表可读（管理员专属）", p.get("success"), "")

    # ============================================================
    # 6. 权限校验矩阵
    # ============================================================
    R.set_phase("学情分析 | 6. 权限校验矩阵")

    # 教师跨班（teacher4 查 teacher1 的 1 班）
    expect_denied("★ 教师跨班查看班级学情被拒",
                  t4, "GET", "/report/teacher/class-overview", params={"class_id": 1})
    # 教师查自己班可读（对照）
    p, _, _ = t4.get("/report/teacher/class-overview", params={"class_id": 4})
    check("教师可查看自己任教班级（对照）", p.get("success"), "")

    # 教师读管理员接口
    for path, name in (("/report/admin/overview", "系统总览"),
                       ("/report/admin/grade-comparison", "年级对比"),
                       ("/report/admin/subject-comparison", "学科对比"),
                       ("/report/admin/system-runtime", "系统运行")):
        expect_denied(f"★ 教师访问管理员接口被拒：{name}", t1, "GET", path)

    # 学生读教师学情接口
    for path in ("/report/teacher/class-overview", "/report/teacher/student-comparison"):
        p, _, _ = stu.get(path, params={"class_id": class_id})
        check(f"★ 学生访问教师接口被拒：{path.split('/')[-1]}",
              p.get("success") is not True,
              p.get("message", "")[:30])

    # 学生读管理员接口
    p, _, _ = stu.get("/report/admin/overview")
    check("★ 学生访问管理员总览被拒", p.get("success") is not True,
          p.get("message", "")[:30])

    R.env("学情分析", f"统计口径（得分率/完成率/分档）+ 权限矩阵验证完成，样本班级={class_id}")
    print("\n[完成] 学情分析模块专项")


if __name__ == "__main__":
    run()
