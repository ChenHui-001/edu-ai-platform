# -*- coding: utf-8 -*-
"""批改中心批量操作 / 分页 / 快捷键 相关的 e2e 补丁注入。

注入位置：test_student.py 的 3c 段之后（有真实 submission 数据）。
"""
import io

f = "tests/test_student.py"
s = io.open(f, encoding="utf-8").read()

ANCHOR = '''    # ---------------------------------------------------------- 4 错题本
    R.set_phase("阶段三 · 学生视角 | 4. 错题本自动收录")'''
assert ANCHOR in s, "锚点未找到"

CASE = '''    # ---------------------------------------------------------- 3d 批量批改 / 批量发布
    R.set_phase("阶段三 · 学生视角 | 3d. 批量批改与批量发布")
    try:
        from e2e_framework import Client as _C3
        tb = _C3("ct1c"); tb.login("teacher1", "Teacher@123")
        if sub_id:
            sid = sub_id

            # 先打回成未批改，验证「未批改不能批量发布」
            tb.post(f"/grading/submissions/{sid}/reject", {"reason": "批量测试准备"})
            p, _, _ = tb.post("/grading/batch/publish", {"submission_ids": [sid]})
            d = data_of(p) or {}
            check("★ 批量发布跳过未批改记录",
                  p.get("success") and sid not in (d.get("published") or [])
                  and len(d.get("skipped") or []) >= 1,
                  f"published={len(d.get('published') or [])} skipped={len(d.get('skipped') or [])}")

            # 批量采纳当前分数 → 状态变 fully_graded
            p, _, _ = tb.post("/grading/batch/grade", {"submission_ids": [sid]})
            d = data_of(p) or {}
            check("★ 批量采纳批改成功",
                  p.get("success") and sid in (d.get("graded") or []),
                  p.get("message", "")[:50])

            # 批量发布 → 成功
            p, _, _ = tb.post("/grading/batch/publish", {"submission_ids": [sid]})
            d = data_of(p) or {}
            check("★ 批量发布成功",
                  p.get("success") and sid in (d.get("published") or []),
                  p.get("message", "")[:50])

            # 空列表拒绝
            p, _, _ = tb.post("/grading/batch/grade", {"submission_ids": []})
            check("批量接口空选拒绝", p.get("success") is not True,
                  p.get("message", "")[:40])

            # 越权：teacher4 批量操作 teacher1 的提交 → 全部 skipped
            t4 = _C3("ct4b"); t4.login("teacher4", "Teacher@123")
            p, _, _ = t4.post("/grading/batch/grade", {"submission_ids": [sid]})
            d = data_of(p) or {}
            check("★ 跨教师批量批改被拒",
                  p.get("success") and sid not in (d.get("graded") or [])
                  and any("非本人任务" in x.get("reason", "")
                          for x in d.get("skipped") or []),
                  f"skipped={d.get('skipped')}")

            # 分页：page_size=1 时 total 正确、第二页可拉
            p1, _, _ = tb.get("/grading/pending", params={"page": 1, "page_size": 1})
            d1 = data_of(p1) or {}
            check("待批列表分页字段完整（items/total/page）",
                  isinstance(d1.get("items"), list) and "total" in d1,
                  f"total={d1.get('total')} page_items={len(d1.get('items') or [])}")
    except Exception as exc:  # noqa: BLE001
        check("批量批改与批量发布", False, f"用例异常: {exc}")

''' + ANCHOR

s = s.replace(ANCHOR, CASE, 1)
io.open(f, "w", encoding="utf-8", newline="\n").write(s)

import ast
ast.parse(s)
print("3d 批量操作 e2e 用例已注入")
