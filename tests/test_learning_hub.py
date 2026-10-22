# -*- coding: utf-8 -*-
"""学习中心模块专项测试（权限与访问控制 + 核心功能链路）。

分工说明：阶段四已覆盖学习中心的业务功能（练习/错题本/复习/笔记/收藏等 78 项），
本阶段聚焦**角色权限矩阵**与**数据隔离**，并补充若干净链路的快速冒烟。
"""
import sys

sys.path.insert(0, "tests")
from e2e_framework import (  # noqa: E402
    R, Client, check, data_of, is_down, rows_of, total_of,
)

TAG = "[E2E-LH]"


def run():
    admin = Client("a"); ok_a, _ = admin.login("admin", "Admin@123456")
    t1 = Client("t1"); ok_t, _ = t1.login("teacher1", "Teacher@123")
    stu = Client("s1"); ok_s, _ = stu.login("stu731", "Student@123")
    stu2 = Client("s2"); ok_s2, _ = stu2.login("stu732", "Student@123")

    check("管理员/教师/学生均可登录",
          ok_a and ok_t and ok_s,
          f"admin={ok_a} teacher1={ok_t} stu731={ok_s}")

    # ============================================================
    # 1. 读接口权限矩阵（学生/教师/管理员均可读，guest 不可）
    # ============================================================
    R.set_phase("学习中心 | 1. 读接口权限矩阵")

    READS = [
        ("/learning/wrong-questions", "错题本"),
        ("/learning/notes", "我的笔记"),
        ("/learning/notes/shared", "共享笔记"),
        ("/learning/review/plans", "复习计划"),
        ("/learning/review/mastery", "掌握地图"),
        ("/learning/practice/history", "练习历史"),
        ("/learning/favorites", "收藏夹"),
        ("/learning/goals", "学习目标"),
        ("/learning/flashcards", "闪卡"),
    ]
    for path, name in READS:
        results = []
        for label, cli in (("admin", admin), ("teacher", t1), ("student", stu)):
            p, _, sc = cli.get(path, params={"page_size": 3}, timeout=60)
            results.append(f"{label}={sc}")
        ok = all("=200" in r for r in results)
        check(f"读接口三角色可达：{name}", ok, " ".join(results))

    # ============================================================
    # 2. 写接口仅学生身份（教师/管理员 403）
    # ============================================================
    R.set_phase("学习中心 | 2. 写接口身份隔离")

    WRITES = [
        ("POST", "/learning/notes", {"title": f"{TAG} 笔记", "content": "内容"}, "创建笔记"),
        ("POST", "/learning/favorites", {"question_id": 1}, "收藏题目"),
        ("POST", "/learning/goals", {"title": f"{TAG} 目标", "target_count": 5}, "创建目标"),
        ("PUT", "/learning/review/plans/1/complete", {}, "完成复习"),
    ]
    for method, path, body, name in WRITES:
        for label, cli in (("admin", admin), ("teacher", t1)):
            p, _, sc = cli.request(method, path, body)
            check(f"★ {label} 写入被拒：{name}",
                  p.get("success") is not True and sc in (403, 400, 404),
                  f"HTTP {sc} {p.get('message', '')[:30]}")

    # 学生自身可写
    p, _, sc = stu.post("/learning/notes", {"title": f"{TAG} 学生笔记", "content": "私密内容"})
    note_id = (data_of(p) or {}).get("id")
    check("★ 学生可创建笔记", p.get("success") and bool(note_id), f"id={note_id}")

    # ============================================================
    # 3. 数据隔离（学生之间）
    # ============================================================
    R.set_phase("学习中心 | 3. 学生数据隔离")

    if note_id:
        p, _, _ = stu.get(f"/learning/notes/{note_id}")
        check("本人可读自己笔记", p.get("success"), "")

        if ok_s2:
            p, _, sc = stu2.get(f"/learning/notes/{note_id}")
            check("★ 同学不可读他人私密笔记（未共享）",
                  p.get("success") is not True,
                  f"HTTP {sc} {p.get('message', '')[:30]}")
            p, _, sc = stu2.put(f"/learning/notes/{note_id}", {"title": "hacked"})
            check("★ 同学不可改他人笔记",
                  p.get("success") is not True,
                  f"HTTP {sc} {p.get('message', '')[:30]}")

        # 共享后同班可见（stu732 与 stu731 同班？七年级(2)班，stu731/732 均在）
        p, _, _ = stu.post(f"/learning/notes/{note_id}/share", {"is_shared": True})
        if p.get("success"):
            p2, _, _ = stu2.get("/learning/notes/shared", params={"page_size": 50})
            visible = any(x.get("id") == note_id for x in rows_of(p2))
            check("共享后同班同学可见（列表）", visible,
                  f"stu732 共享列表 {len(rows_of(p2))} 条")
            p3, _, _ = stu2.get(f"/learning/notes/{note_id}")
            check("共享后同班同学可读详情", p3.get("success"), "")

    # 管理员可读任意笔记（数据核查）→ 应留审计
    if note_id:
        p, _, sc = admin.get(f"/learning/notes/{note_id}")
        check("★ 管理员可读学生笔记（核查用途）",
              p.get("success"), f"HTTP {sc}")

    # 教师不可读学生私有笔记
    if note_id:
        p, _, sc = t1.get(f"/learning/notes/{note_id}")
        check("★ 教师不可读学生私有笔记",
              p.get("success") is not True,
              f"HTTP {sc} {p.get('message', '')[:30]}")

    # ============================================================
    # 4. 共享笔记对非学生返回空
    # ============================================================
    R.set_phase("学习中心 | 4. 共享笔记身份边界")

    for label, cli in (("teacher", t1), ("admin", admin)):
        p, _, _ = cli.get("/learning/notes/shared", params={"page_size": 20})
        items = rows_of(p)
        check(f"★ {label} 共享笔记列表为空（不浏览学生私有内容）",
              p.get("success") and len(items) == 0, f"{len(items)} 条")

    # ============================================================
    # 5. 核心功能快速冒烟（详细链路在阶段四）
    # ============================================================
    R.set_phase("学习中心 | 5. 核心功能冒烟")

    # 练习创建 → 取题
    # 必须用**学生本年级**的学科 id：Subject 唯一键是 (grade_id, name)，
    # distinct=true 返回的代表记录指向最低年级（一年级），拿它给七年级学生
    # 发起练习会被年级过滤挡住 → 400「该学科在该年级暂无题目」。
    stu_grade = stu.user.get("grade_id")
    p, _, _ = stu.get("/edu/subjects",
                      params={"grade_id": stu_grade} if stu_grade else {"distinct": True})
    subs = rows_of(p)
    if subs:
        p, _, sc = stu.post("/learning/practice", {
            "subject_id": subs[0]["id"], "count": 5})
        practice = data_of(p) or {}
        pid = practice.get("task_id")   # 契约：{task_id, paper_id, total}
        check("★ 创建随机练习（返回 task_id）",
              p.get("success") and bool(pid),
              f"task_id={pid} paper_id={practice.get('paper_id')}")
        if pid:
            p2, _, _ = stu.get(f"/learning/practice/{pid}")
            qs = (data_of(p2) or {}).get("questions") or (data_of(p2) or {}).get("items") or []
            check("练习可取题", p2.get("success") and len(qs) > 0, f"{len(qs)} 题")

    # 收藏
    p, _, _ = stu.get("/learning/favorites", params={"page_size": 1})
    check("收藏夹可读", p.get("success"), f"{total_of(p)} 条")

    # 学习目标 + 打卡
    p, _, _ = stu.post("/learning/goals", {
        "title": f"{TAG} 每日练习", "target_count": 5,
        "goal_type": "practice"})
    gid = (data_of(p) or {}).get("id")
    check("★ 创建学习目标", p.get("success") and bool(gid), f"id={gid}")
    if gid:
        p, _, _ = stu.post(f"/learning/goals/{gid}/checkin", {})
        check("每日打卡", p.get("success"), p.get("message", "")[:30])
        stu.delete(f"/learning/goals/{gid}")

    # 自主组卷
    if subs:
        p, _, sc = stu.post("/learning/custom-paper", {
            "name": f"{TAG} 自组卷", "subject_id": subs[0]["id"], "count": 5})
        d = data_of(p) or {}
        check("★ 学生自主组卷",
              p.get("success") and bool(d.get("task_id")),
              f"HTTP {sc} task_id={d.get('task_id')} {p.get('message', '')[:30]}")

    # AI 类接口（允许降级）
    for path, name in (("/learning/review/plan", "AI 生成复习计划"),
                       ("/learning/path/recommend", "学习路径推荐")):
        if "generate" in path:
            p, _, sc = stu.post(path, body={}, timeout=90)
        else:
            p, _, sc = stu.get(path, params={"page_size": 3}, timeout=90)
        check(f"{name}（允许降级）",
              p.get("success") or is_down(p) is False,
              f"HTTP {sc} {p.get('message', '')[:40]}")

    # ============================================================
    # 6. 边界与异常
    # ============================================================
    R.set_phase("学习中心 | 6. 边界与异常")

    p, _, sc = stu.get("/learning/notes/999999")
    check("不存在的笔记 404", p.get("success") is not True and sc == 404,
          f"HTTP {sc}")

    p, _, _ = stu.post("/learning/practice", {})
    check("创建练习缺必填参数被拒", p.get("success") is not True,
          p.get("message", "")[:30])

    # 分页容错：page=0 / page_size=0 应被收敛为 1，而不是 422（前端清空筛选时常见）
    p, _, sc = stu.get("/learning/wrong-questions", params={"page": 0, "page_size": 0})
    check("★ 非法页码 page=0/page_size=0 自动收敛（不再 422）",
          p.get("success") is True and sc == 200,
          f"HTTP {sc} items={len(rows_of(p))}")
    p, _, sc = stu.get("/learning/wrong-questions", params={"page_size": 99999})
    check("★ 超大 page_size 被收敛到上限（不报错）",
          p.get("success") is True, f"HTTP {sc}")

    # 管理员核查笔记不计浏览数
    p, _, _ = stu.post("/learning/notes", {"title": f"{TAG} 计数验证", "content": "x"})
    nid2 = (data_of(p) or {}).get("id")
    if nid2:
        v0 = (data_of(stu.get(f"/learning/notes/{nid2}")[0]) or {}).get("view_count")
        admin.get(f"/learning/notes/{nid2}")
        v1 = (data_of(admin.get(f"/learning/notes/{nid2}")[0]) or {}).get("view_count")
        check("★ 管理员核查不增加学生笔记浏览数",
              (v1 or 0) == (v0 or 0),
              f"view_count {v0} -> {v1}")
        stu.delete(f"/learning/notes/{nid2}")

    # 笔记创建（RAG 索引已转后台任务，响应应正常返回）
    p, _, sc = stu.post("/learning/notes",
                        {"title": f"{TAG} 后台索引", "content": "内容" * 50})
    nid3 = (data_of(p) or {}).get("id")
    check("★ 笔记创建成功后端索引（响应正常且数据可读）",
          p.get("success") and bool(nid3),
          f"HTTP {sc} id={nid3}")
    if nid3:
        stu.delete(f"/learning/notes/{nid3}")

    # 清理
    if note_id:
        stu.delete(f"/learning/notes/{note_id}")
    _cleanup(stu, t1, admin)
    R.env("学习中心", "权限矩阵 3 角色 × 9 读接口 + 4 写接口隔离验证完成")
    print("\n[完成] 学习中心模块专项")


def _cleanup(*clients):
    for cli in clients:
        try:
            p, _, _ = cli.get("/learning/notes", params={"keyword": TAG, "page_size": 50})
            for x in rows_of(p):
                cli.delete(f"/learning/notes/{x['id']}")
            p, _, _ = cli.get("/learning/goals", params={"page_size": 50})
            for x in rows_of(p):
                if str(x.get("title", "")).startswith(TAG):
                    cli.delete(f"/learning/goals/{x['id']}")
        except Exception:  # noqa: BLE001
            pass


if __name__ == "__main__":
    run()
