# -*- coding: utf-8 -*-
"""教学管理模块缺陷验证脚本（只读 + 可控副作用，产出一份缺陷清单）。

对每个疑点做最小实测，输出 [确认]/[未复现] 与证据，供报告引用。
"""
import sys
import time

sys.path.insert(0, "tests")
from e2e_framework import Client  # noqa: E402

FINDINGS = []


def record(level, title, confirmed, evidence):
    FINDINGS.append({
        "level": level, "title": title,
        "confirmed": confirmed, "evidence": evidence,
    })
    tag = "确认" if confirmed else "未复现"
    print(f"[{tag}][{level}] {title}\n    {evidence}")


def main():
    admin = Client("a"); admin.login("admin", "Admin@123456")
    t1 = Client("t1"); t1.login("teacher1", "Teacher@123")
    t4 = Client("t4"); t4.login("teacher4", "Teacher@123")
    stu = Client("s1"); stu.login("stu731", "Student@123")

    # 前置：拿到 teacher1 的任务（含提交）
    p, _, _ = t1.get("/task/tasks", params={"page_size": 20})
    tasks = (p.get("data") or {}).get("items") or []
    tid = tasks[0]["id"] if tasks else None
    if not tid:
        print("无任务数据，先创建一个")
        p, _, _ = t1.get("/question/papers", params={"page_size": 5})
        papers = (p.get("data") or {}).get("items") or []
        if papers:
            p, _, _ = t1.post("/task/tasks", {
                "title": f"缺陷验证任务 {int(time.time())}", "type": "homework",
                "paper_id": papers[0]["id"], "class_ids": [1]})
            tid = (p.get("data") or {}).get("id")
    print(f"基准任务 tid={tid}\n")

    # ============ 1. task_submissions 越权 ============
    if tid:
        p, _, sc = t4.get(f"/task/tasks/{tid}/submissions", params={"page_size": 5})
        d = p.get("data") or {}
        leaked = bool(d.get("items"))
        record("高", "任意教师可查看他人任务的提交情况（含学生姓名/分数/切屏次数）",
               sc == 200 and p.get("success"),
               f"teacher4 请求 teacher1 任务 {tid} 提交列表 -> HTTP {sc}, "
               f"success={p.get('success')}, 返回 {len(d.get('items') or [])} 条提交, "
               f"assigned={d.get('assigned')}")

    # ============ 2. attempt 绕过 allow_retake ============
    # 找一个已发布、下发给 stu731 的任务
    p, _, _ = stu.get("/task/my/tasks", params={"page_size": 20})
    my = (p.get("data") or {}).get("items") or []
    target = next((x for x in my if x.get("type") == "exam"), None) or (my[0] if my else None)
    if target:
        mtid = target["id"]
        allow = target.get("allow_retake")
        p1, _, _ = stu.get(f"/task/tasks/{mtid}/paper")
        items = (p1.get("data") or {}).get("items") or []
        if items and allow == 1:
            payload = [{"paper_item_id": items[0]["paper_item_id"], "content": "A"}]
            p2, _, sc2 = stu.post(f"/task/tasks/{mtid}/submit",
                                  {"answers": payload, "duration_seconds": 60, "attempt": 5})
            ok2 = p2.get("success") is True
            record("高", "交卷 attempt 由客户端指定，可绕过 allow_retake=1 的限制重复交卷",
                   ok2,
                   f"任务 {mtid} allow_retake={allow}，直接提交 attempt=5 -> "
                   f"success={p2.get('success')} msg={p2.get('message', '')[:40]}")
        else:
            record("高", "交卷 attempt 可绕过重考次数限制", False,
                   f"跳过：任务 allow_retake={allow} items={len(items)}")

    # ============ 3. 孤儿任务（无下发对象仍发布）============
    p, _, _ = t1.get("/question/papers", params={"page_size": 5})
    papers = (p.get("data") or {}).get("items") or []
    if papers:
        p, _, sc = t1.post("/task/tasks", {
            "title": f"孤儿任务验证 {int(time.time())}", "type": "homework",
            "paper_id": papers[0]["id"], "class_ids": [], "student_ids": []})
        oid = (p.get("data") or {}).get("id")
        record("中", "发布任务时 class_ids 与 student_ids 均为空仍可成功（学生看不到的孤儿任务）",
               p.get("success") is True and bool(oid),
               f"空下发对象 -> success={p.get('success')} task_id={oid} "
               f"msg={p.get('message', '')[:40]}")
        if oid:
            t1.delete(f"/task/tasks/{oid}")

    # ============ 4. 非法参数不校验 ============
    if papers:
        pid = papers[0]["id"]
        bad = [
            ("pass_score=9999", {"pass_score": 9999}),
            ("duration=0", {"duration": 0}),
            ("end_at < start_at", {"start_at": "2026-12-31 10:00:00",
                                    "end_at": "2026-01-01 10:00:00"}),
        ]
        hits = []
        for label, extra in bad:
            body = {"title": f"非法参数验证 {label} {int(time.time())}",
                    "type": "homework", "paper_id": pid, "class_ids": [1]}
            body.update(extra)
            p, _, st = t1.post("/task/tasks", body)
            if p.get("success"):
                hits.append(label)
                nid = (p.get("data") or {}).get("id")
                if nid:
                    t1.delete(f"/task/tasks/{nid}")
        record("中", "任务发布不校验 pass_score 范围 / duration / 起止时间先后",
               bool(hits), f"以下非法参数被接受并创建成功：{hits}")

    # ============ 5. 共享教案跨学科可见 ============
    p, _, _ = t1.get("/lesson/plans", params={"page_size": 20})
    mine = (p.get("data") or {}).get("items") or []
    shared = next((x for x in mine if x.get("is_shared")), None)
    if not shared and mine:
        # 造一个共享教案
        p, _, _ = t1.post("/lesson/plans", {
            "title": f"共享验证 {int(time.time())}", "topic": "测试",
            "subject_id": 1, "grade_id": 1})
        pl = (p.get("data") or {}).get("id")
        if pl:
            t1.post(f"/lesson/plans/{pl}/share", {"is_shared": True})
            p, _, _ = t1.get(f"/lesson/plans/{pl}")
            shared = p.get("data")
            shared["_created"] = True
    if shared:
        p, _, _ = t4.get("/lesson/plans", params={"page_size": 100})
        items = (p.get("data") or {}).get("items") or []
        hit = [x for x in items if x.get("id") == shared.get("id")]
        record("中", "共享教案对所有教师可见（注释称「同科教师」，实现未按学科过滤）",
               bool(hit),
               f"teacher4 列表可见 teacher1 共享教案 id={shared.get('id')} "
               f"subject_id={shared.get('subject_id')}（不同学科也应可见）")
        if shared.get("_created"):
            t1.delete(f"/lesson/plans/{shared['id']}")

    # ============ 6. completion_rate 口径不一致 ============
    if tid:
        p, _, _ = t1.get("/task/tasks", params={"keyword": "", "page_size": 20})
        row = next((x for x in (p.get("data") or {}).get("items") or []
                    if x["id"] == tid), None)
        p2, _, _ = t1.get(f"/task/tasks/{tid}/submissions", params={"page_size": 5})
        stats = p2.get("data") or {}
        list_rate = (row or {}).get("completion_rate")
        detail_rate = stats.get("completion_rate")
        record("中", "任务列表与提交详情的完成率口径不一致（列表按 assignments 条数，详情展开班级成员）",
               list_rate != detail_rate,
               f"列表 completion_rate={list_rate}% "
               f"(分母 assignments={len(row.get('assignments') or []) if row else '-'}) "
               f"vs 详情={detail_rate}% (assigned={stats.get('assigned')}人)")

    # ============ 7. 交卷后心跳仍可改数据 ============
    if target:
        before = None
        p, _, _ = stu.get("/task/my/tasks", params={"page_size": 20})
        mt = next((x for x in (p.get("data") or {}).get("items") or []
                   if x["id"] == target["id"]), None)
        if mt and mt.get("my_submission"):
            before = (mt["my_submission"].get("switch_count"), mt["my_submission"].get("duration_seconds"))
            stu.post(f"/task/tasks/{target['id']}/heartbeat",
                     {"switch": True, "duration_seconds": 99999})
            p2, _, _ = stu.get("/task/my/tasks", params={"page_size": 20})
            mt2 = next((x for x in (p2.get("data") or {}).get("items") or []
                        if x["id"] == target["id"]), None)
            after = (mt2["my_submission"].get("switch_count"),
                     mt2["my_submission"].get("duration_seconds"))
            record("低", "已交卷后心跳仍可累加切屏次数、覆盖答题时长（数据可被篡改）",
                   before != after, f"交卷后心跳：{before} -> {after}")

    print("\n" + "=" * 60)
    print(f"缺陷验证完成：确认 {sum(1 for f in FINDINGS if f['confirmed'])} / "
          f"{len(FINDINGS)} 项")


if __name__ == "__main__":
    main()
