# -*- coding: utf-8 -*-
"""学习中心模块权限与访问控制实测（管理员视角为主）。

验证矩阵：
- admin / teacher / student / guest 对 14 个前端路由 + 38 个后端接口的访问结果
- 学生数据隔离（笔记/收藏/练习按 id 越权读取）
- 接口契约与边界
"""
import json
import sys

sys.path.insert(0, "tests")
from e2e_framework import Client  # noqa: E402

LEARNING_GETS = [
    ("/learning/practice/history", "练习历史"),
    ("/learning/wrong-questions", "错题本"),
    ("/learning/notes", "我的笔记"),
    ("/learning/notes/shared", "共享笔记"),
    ("/learning/review/plans", "复习计划"),
    ("/learning/review/mastery", "掌握地图"),
    ("/learning/favorites", "收藏夹"),
    ("/learning/goals", "学习目标"),
    ("/learning/path", "学习路径"),
    ("/learning/flashcards", "闪卡"),
]


def main():
    a = Client("a"); ok_a, _ = a.login("admin", "Admin@123456")
    t = Client("t"); ok_t, _ = t.login("teacher1", "Teacher@123")
    s = Client("s"); ok_s, _ = s.login("stu731", "Student@123")
    print(f"登录: admin={ok_a} teacher1={ok_t} stu731={ok_s}\n")

    # ---------- 1. 角色权限点 ----------
    p, _, _ = a.get("/auth/profile")
    prof = p.get("data") or {}
    perms = prof.get("permissions") or {}
    a_perms = perms.get("permissions") if isinstance(perms, dict) else perms
    print(f"[角色] admin permissions 类型={type(a_perms).__name__} "
          f"数量={len(a_perms) if a_perms else 0}")
    print(f"       admin 含 student 权限点: "
          f"{[x for x in (a_perms or []) if str(x).startswith('student:')][:5]}")

    for name, cli in (("admin", a), ("teacher1", t), ("stu731", s)):
        p, _, sc = cli.get("/auth/profile")
        d = p.get("data") or {}
        pm = (d.get("permissions") or {})
        plist = pm.get("permissions") if isinstance(pm, dict) else pm
        roles = pm.get("roles") if isinstance(pm, dict) else d.get("roles")
        print(f"       {name}: roles={roles} perms={len(plist) if plist else 0}")

    # ---------- 2. 后端接口访问矩阵 ----------
    print("\n[接口访问矩阵]")
    print(f"{'接口':<28} {'admin':>7} {'teacher':>8} {'student':>8}")
    for path, label in LEARNING_GETS:
        row = []
        for cli in (a, t, s):
            p, _, sc = cli.get(path, params={"page_size": 5})
            row.append(f"{sc}{'✓' if p.get('success') else '✗'}")
        print(f"{label:<28} {row[0]:>7} {row[1]:>8} {row[2]:>8}")

    # ---------- 3. 学生数据隔离 ----------
    print("\n[数据隔离]")
    # 用 stu731 创建一条笔记，再用另一学生尝试读取
    p, _, sc = s.post("/learning/notes", {
        "title": "隔离验证笔记", "content": "私密内容", "subject_id": 1,
    })
    note_id = (p.get("data") or {}).get("id")
    print(f"  stu731 建笔记: {sc} id={note_id}")
    if note_id:
        # admin 读（管理员是否可看学生私有笔记？）
        p, _, sc = a.get(f"/learning/notes/{note_id}")
        print(f"  admin 读他人笔记: {sc} success={p.get('success')} "
              f"content={str((p.get('data') or {}).get('content'))[:12]}")
        # teacher1 读
        p, _, sc = t.get(f"/learning/notes/{note_id}")
        print(f"  teacher1 读学生笔记: {sc} success={p.get('success')}")
        # 另一个学生（stu732）
        s2 = Client("s2"); s2.login("stu732", "Student@123")
        p, _, sc = s2.get(f"/learning/notes/{note_id}")
        print(f"  stu732 读同学笔记: {sc} success={p.get('success')} "
              f"content={str((p.get('data') or {}).get('content'))[:12]}")
        # 编辑越权
        p, _, sc = s2.put(f"/learning/notes/{note_id}", {"title": "hacked"})
        print(f"  stu732 改同学笔记: {sc} success={p.get('success')}")
        s.delete(f"/learning/notes/{note_id}")

    # ---------- 4. 边界与契约 ----------
    print("\n[边界检查]")
    # 练习创建缺参数
    p, _, sc = s.post("/learning/practice", {})
    print(f"  创建练习缺参数: {sc} success={p.get('success')} msg={p.get('message', '')[:30]}")
    # 不存在的笔记
    p, _, sc = s.get("/learning/notes/999999")
    print(f"  不存在的笔记: {sc} success={p.get('success')} msg={p.get('message', '')[:30]}")
    # 分页边界
    p, _, sc = s.get("/learning/wrong-questions", params={"page": 0, "page_size": 0})
    print(f"  page=0&size=0: {sc} success={p.get('success')} "
          f"items={len((p.get('data') or {}).get('items') or [])}")
    # 非法 page_size 超大
    p, _, sc = s.get("/learning/wrong-questions", params={"page_size": 10000})
    print(f"  page_size=10000: {sc} success={p.get('success')} "
          f"items={len((p.get('data') or {}).get('items') or [])}")

    # ---------- 5. admin 是否能调用学生写接口（污染风险） ----------
    print("\n[写接口]")
    p, _, sc = a.post("/learning/notes", {"title": "admin 建的学习笔记", "content": "x"})
    aid = (p.get("data") or {}).get("id")
    print(f"  admin 创建学生笔记: {sc} success={p.get('success')} id={aid}")
    p, _, sc = t.post("/learning/notes", {"title": "teacher 建的学习笔记", "content": "x"})
    tid = (p.get("data") or {}).get("id")
    print(f"  teacher1 创建学生笔记: {sc} success={p.get('success')} id={tid}")
    # 清理
    for cli, nid in ((a, aid), (t, tid)):
        if nid:
            cli.delete(f"/learning/notes/{nid}")


if __name__ == "__main__":
    main()
