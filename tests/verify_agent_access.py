# -*- coding: utf-8 -*-
"""AI 智能模块权限与功能实测（管理员视角）。"""
import sys
import time

sys.path.insert(0, "tests")
from e2e_framework import Client  # noqa: E402

F = []


def rec(level, title, bad, detail):
    F.append((level, title, bad, detail))
    print(f"[{'缺陷' if bad else '正常'}][{level}] {title}\n    {detail}")


def main():
    admin = Client("a"); admin.login("admin", "Admin@123456")
    t1 = Client("t1"); t1.login("teacher1", "Teacher@123")
    s1 = Client("s1"); s1.login("stu731", "Student@123")
    s2 = Client("s2"); s2.login("stu732", "Student@123")

    # ---------- 基础状态 ----------
    p, _, _ = admin.get("/agent/status")
    st = p.get("data") or {}
    print(f"[状态] {st}\n")

    # ---------- 1. 学生调用出题（save=True 写题库）----------
    p, _, sc = s1.post("/agent/question-generator", {
        "subject_id": 1, "type": "single", "count": 1, "save": True})
    d = p.get("data") or {}
    saved = d.get("saved") if isinstance(d, dict) else None
    rec("高", "学生可调用出题 Agent 并写入题库（save=True）",
        p.get("success") is True,
        f"HTTP {sc} success={p.get('success')} saved={saved} msg={p.get('message', '')[:30]}")

    # ---------- 2. 学生组卷（save=True 建试卷）----------
    p, _, sc = s1.post("/agent/paper-composer", {
        "request": "七年级数学 5 题", "subject_id": 1, "grade_id": 7, "save": True})
    d = p.get("data") or {}
    pid = d.get("paper_id") if isinstance(d, dict) else None
    rec("高", "学生可调用组卷 Agent 并创建试卷（save=True）",
        p.get("success") is True and bool(pid),
        f"HTTP {sc} paper_id={pid} msg={p.get('message', '')[:30]}")

    # ---------- 3. 学生调用批改 Agent ----------
    p, _, sc = s1.post("/agent/grading", {"items": [
        {"stem": "1+1=?", "type": "single", "answer": "A", "student_answer": "B",
         "full_score": 5}]})
    rec("中", "学生可调用批改 Agent（应仅教师）",
        p.get("success") is True,
        f"HTTP {sc} msg={p.get('message', '')[:30]}")

    # ---------- 4. 学生生成他人学习规划 ----------
    p, _, _ = s1.get("/task/my/tasks", params={"page_size": 5})
    p2, _, sc = s1.post("/agent/study-planner", {"student_id": 999, "days": 7})
    rec("中", "学生可指定任意 student_id 生成学习规划",
        p2.get("success") is True or sc == 200,
        f"HTTP {sc} success={p2.get('success')} msg={p2.get('message', '')[:40]}")

    # ---------- 5. note-organizer 读取/覆写他人笔记 ----------
    p, _, _ = s2.post("/learning/notes", {"title": "stu732 私密笔记", "content": "私密内容 XYZ"})
    nid = (p.get("data") or {}).get("id")
    if nid:
        p, _, sc = s1.post("/agent/note-organizer", {"note_id": nid})
        d = p.get("data") or {}
        leaked = "XYZ" in str(d.get("summary", "")) or "XYZ" in str(d.get("polished_content", ""))
        rec("高", "★ 学生可读取他人私密笔记内容（note-organizer 无归属校验）",
            p.get("success") is True,
            f"HTTP {sc} success={p.get('success')} 内容命中={leaked}")
        # 覆写
        s1.post("/agent/note-organizer", {"note_id": nid, "save": True})
        p, _, _ = s2.get(f"/learning/notes/{nid}")
        after = ((p.get("data") or {}).get("content") or "")
        rec("高", "★ 学生可覆写他人笔记正文（save=True）",
            after != "私密内容 XYZ",
            f"覆写后内容片段={after[:40]!r}")
        s2.delete(f"/learning/notes/{nid}")

    # ---------- 6. /agent/logs 统计是否越权 ----------
    p, _, _ = s1.get("/agent/logs", params={"page_size": 3})
    d = p.get("data") or {}
    sm = d.get("summary") or {}
    rec("中", "学生可见全站 AI 调用统计（summary/by_agent 未按用户过滤）",
        (sm.get("total_calls") or 0) > (d.get("total") or 0),
        f"items.total={d.get('total')} summary.total_calls={sm.get('total_calls')} "
        f"by_agent={list((d.get('by_agent') or {}).keys())[:4]}")

    # ---------- 7. 教师调出题（应允许）----------
    p, _, sc = t1.post("/agent/question-generator", {
        "subject_id": 1, "type": "single", "count": 1, "save": False})
    rec("低", "教师可调用出题 Agent（对照项）",
        p.get("success") is not True,
        f"HTTP {sc} success={p.get('success')} msg={p.get('message', '')[:30]}")

    # ---------- 8. 未登录 ----------
    anon = Client("anon")
    p, _, sc = anon.get("/agent/status")
    rec("低", "未登录不可访问 agent 状态",
        p.get("success") is True,
        f"HTTP {sc}")

    print("\n" + "=" * 60)
    bad = [x for x in F if x[2]]
    print(f"实测 {len(F)} 项，确认缺陷 {len(bad)} 项")
    for lv, t, _, _ in bad:
        print(f"  [{lv}] {t}")


if __name__ == "__main__":
    main()
