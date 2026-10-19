# -*- coding: utf-8 -*-
"""教师端「教案管理」模块专项 e2e 测试。

覆盖：
- 列表：教师自己的 + 同科共享的 + only_mine 切换
- CRUD：新建（含阶段）/ 编辑（替换阶段）/ 删除
- 复制：副本归属自己
- 共享：同科可见 + 不可见的边界
- 越权：学生不能读/写
- 跨教师：不能改/删别人的
- 业务校验：缺必填字段、关联对象不存在 → 拒绝
"""
from datetime import datetime

from e2e_framework import (  # noqa: F401
    R, Client, check, expect_denied, rows_of, data_of,
)


def _tag():
    return f"[E2E-LP-{datetime.now().strftime('%H%M%S%f')[-6:]}]"


def run():
    tea1 = Client("teacher1"); tea1.login("teacher1", "Teacher@123")
    tea2 = Client("teacher4"); tea2.login("teacher4", "Teacher@123")
    stu = Client("stu731"); stu.login("stu731", "Student@123")
    admin = Client("admin"); admin.login("admin", "Admin@123456")

    # 找一组合法 (grade_id, subject_id)
    p, _, _ = tea1.get("/edu/grades", params={})
    grades = rows_of(p)
    # 取本年级下的所有学科（不传 distinct，精确 id）
    p, _, _ = tea1.get("/edu/subjects", params={"grade_id": grades[0]["id"]})
    subjects = rows_of(p)
    assert subjects, "本年级没有学科，无法测试"
    assert grades and subjects, "环境缺基础数据"
    g1, s_math = grades[0], subjects[1]  # 一年级数学（数学在 distinct 列表里通常排第 2）

    # ============================================================
    # 1. 列表 + 共享开关
    # ============================================================
    R.set_phase("教案管理 | 1. 列表与共享")

    p, _, _ = tea1.get("/lesson/plans", params={"page_size": 50})
    base = (data_of(p) or {}).get("total") or 0
    check("教师教案列表可读",
          p.get("success") and isinstance(rows_of(p), list),
          f"当前 {base} 份")

    # 新建一份
    p, _, _ = tea1.post("/lesson/plans", _make_payload(tea1, subjects[1]["id"], g1["id"]))
    plan_id = (data_of(p) or {}).get("id")
    check("★ 教师可新建教案（含阶段）",
          p.get("success") and bool(plan_id),
          f"plan_id={plan_id} {p.get('message', '')[:60]}")

    if not plan_id:
        return

    # 默认不共享 → tea2 列表里看不到
    p, _, _ = tea2.get("/lesson/plans", params={"page_size": 50})
    tea2_total_before = (data_of(p) or {}).get("total") or 0
    check("默认不共享 → 同科 teacher4 列表里看不到此教案",
          not any((r or {}).get("id") == plan_id for r in rows_of(p)),
          f"tea2 看到 {tea2_total_before} 份（不含此教案）")

    # 打开共享
    p, _, _ = tea1.post(f"/lesson/plans/{plan_id}/share", {"is_shared": True})
    check("教师可把教案设为共享",
          p.get("success") and (data_of(p) or {}).get("is_shared") is True,
          p.get("message", ""))

    # tea2 列表里现在能看到
    p, _, _ = tea2.get("/lesson/plans", params={"page_size": 50})
    check("★ 共享后 → 同科教师在列表里能看到",
          any((r or {}).get("id") == plan_id for r in rows_of(p)),
          f"tea2 列表里有/无 id={plan_id}")

    # only_mine=true 看自己
    p, _, _ = tea1.get("/lesson/plans", params={"only_mine": True, "page_size": 50})
    check("only_mine=true 时只看自己的",
          all((r or {}).get("creator_id") == tea1.user.get("id") for r in rows_of(p))
          if rows_of(p) else True,
          f"{len(rows_of(p))} 条都是自己的")

    # ============================================================
    # 2. 详情 + 编辑
    # ============================================================
    R.set_phase("教案管理 | 2. 详情与编辑")

    p, _, _ = tea1.get(f"/lesson/plans/{plan_id}")
    det = data_of(p) or {}
    check("教案详情可读",
          p.get("success") and det.get("id") == plan_id,
          f"title={det.get('title')!r}")
    check("★ 详情含教学过程阶段",
          isinstance(det.get("stages"), list) and len(det["stages"]) > 0,
          f"stages={len(det.get('stages') or [])}")
    check("详情含学科年级展示字段",
          det.get("subject_name") and det.get("grade_name"),
          f"subject_name={det.get('subject_name')!r} grade_name={det.get('grade_name')!r}")

    # 改标题
    new_title = f"{_tag()} 已编辑"
    p, _, _ = tea1.put(f"/lesson/plans/{plan_id}", {
        "title": new_title, "objectives": "新教学目标"})
    check("★ 教师可编辑教案标题",
          p.get("success") and (data_of(p) or {}).get("title") == new_title,
          f"{(data_of(p) or {}).get('title')!r}")

    # 编辑 + 替换阶段
    p, _, _ = tea1.put(f"/lesson/plans/{plan_id}", {
        "stages": [
            {"name": "复习", "duration_minutes": 5, "content": "复习上节"},
            {"name": "新授", "duration_minutes": 30, "content": "本节新授"},
        ]})
    new_stages = (data_of(p) or {}).get("stages") or []
    check("★ 编辑可整体替换阶段",
          len(new_stages) == 2 and new_stages[0]["name"] == "复习",
          f"stages={[s['name'] for s in new_stages]}")

    # 业务校验：必填字段缺失
    p, _, _ = tea1.post("/lesson/plans", {"title": "缺字段教案"})
    check("★ 缺 topic / subject_id / grade_id 必填校验失败",
          p.get("success") is not True,
          p.get("message", ""))

    # 关联对象不存在
    p, _, _ = tea1.post("/lesson/plans", _make_payload(tea1, 999999, g1["id"]))
    check("★ 不存在的 subject_id 必须被拒",
          p.get("success") is not True,
          p.get("message", ""))

    # ============================================================
    # 3. 复制
    # ============================================================
    R.set_phase("教案管理 | 3. 复制")

    p, _, _ = tea2.post(f"/lesson/plans/{plan_id}/copy", {})
    new_plan = data_of(p) or {}
    new_id = new_plan.get("id")
    check("★ 同科教师可复制共享教案",
          p.get("success") and bool(new_id) and new_id != plan_id,
          f"new_id={new_id}")
    check("★ 副本标题带「副本」后缀",
          "副本" in (new_plan.get("title") or ""),
          f"title={new_plan.get('title')!r}")
    check("副本归属当前教师",
          new_plan.get("creator_id") == tea2.user.get("id"),
          f"creator_id={new_plan.get('creator_id')}")
    check("★ 副本继承原教案阶段数",
          len(new_plan.get("stages") or []) == len(new_stages),
          f"stages={len(new_plan.get('stages') or [])}")

    # 删除副本避免污染
    if new_id:
        p, _, _ = tea2.delete(f"/lesson/plans/{new_id}")
        check("复制者可以删除自己的副本", p.get("success"),
              p.get("message", ""))

    # ============================================================
    # 4. 越权
    # ============================================================
    R.set_phase("教案管理 | 4. 越权矩阵")

    expect_denied("学生不能读教案列表", stu, "GET", "/lesson/plans")
    expect_denied("学生不能新建教案", stu, "POST", "/lesson/plans",
                  body=_make_payload(stu, subjects[1]["id"], g1["id"]))
    expect_denied("学生不能读教案详情", stu, "GET",
                  f"/lesson/plans/{plan_id}")
    expect_denied("学生不能编辑教案", stu, "PUT",
                  f"/lesson/plans/{plan_id}", body={"title": "hack"})
    expect_denied("学生不能删除教案", stu, "DELETE",
                  f"/lesson/plans/{plan_id}")
    expect_denied("学生不能复制教案", stu, "POST",
                  f"/lesson/plans/{plan_id}/copy", body={})
    expect_denied("学生不能切换共享", stu, "POST",
                  f"/lesson/plans/{plan_id}/share", body={"is_shared": True})

    # 跨教师：tea2 不能改/删 tea1 的教案
    p, _, _ = tea2.put(f"/lesson/plans/{plan_id}", {"title": "hack by tea2"})
    check("★ 跨教师编辑教案被拒",
          p.get("success") is not True,
          p.get("message", ""))
    p, _, _ = tea2.delete(f"/lesson/plans/{plan_id}")
    check("★ 跨教师删除教案被拒",
          p.get("success") is not True,
          p.get("message", ""))

    # 取消共享后 tea2 看不到（虽然他是同科）
    tea1.post(f"/lesson/plans/{plan_id}/share", {"is_shared": False})
    p, _, _ = tea2.get(f"/lesson/plans/{plan_id}")
    check("★ 取消共享后同科教师不可读教案详情",
          p.get("success") is not True,
          p.get("message", ""))

    # 管理员可直接读
    p, _, _ = admin.get(f"/lesson/plans/{plan_id}")
    check("管理员可读任意教案（审计）",
          p.get("success"),
          f"{p.get('code')}")

    # ============================================================
    # 5. 列表筛选
    # ============================================================
    R.set_phase("教案管理 | 5. 列表筛选")

    p, _, _ = tea1.get("/lesson/plans", params={
        "subject_id": subjects[1]["id"], "grade_id": g1["id"],
        "page_size": 50})
    rows = rows_of(p)
    check("按学科+年级筛选返回数据",
          p.get("success") and isinstance(rows, list),
          f"{len(rows)} 份")

    # 关键词
    p, _, _ = tea1.get("/lesson/plans", params={"keyword": _tag()[:8],
                                                  "page_size": 50})
    rows = rows_of(p)
    check("关键词筛选生效",
          p.get("success") and any(_tag()[:8] in (r.get("title") or "")
                                     for r in rows),
          f"命中 {len(rows)} 份")

    # ============================================================
    # 6. 附件（图片 / PPT / 文档）
    # ============================================================
    R.set_phase("教案管理 | 6. 附件全链路")

    def _mp_upload(client, path, content: bytes, filename: str,
                   mime: str = "application/octet-stream"):
        """手工拼 multipart/form-data（e2e 框架无原生 multipart 支持）。"""
        boundary = "----wbE2E" + str(abs(hash((filename, len(content)))))[:10]
        parts = [
            (f"--{boundary}\r\n"
             f'Content-Disposition: form-data; name="file"; '
             f'filename="{filename}"\r\n'
             f"Content-Type: {mime}\r\n\r\n").encode("latin-1"),
            content,
            f"\r\n--{boundary}--\r\n".encode("latin-1"),
        ]
        body = b"".join(parts)
        return client.request(
            "POST", path, raw_body=body,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
            timeout=60)

    # PNG 1x1（真实图片字节头）
    png = (b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
           b"\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
           b"\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r"
           b"\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82")
    # 伪 PPTX（重点在扩展名与流程，不在内容）
    pptx = b"PK\x03\x04" + b"e2e-pptx-placeholder " * 8

    p, _, _ = _mp_upload(tea1, f"/lesson/plans/{plan_id}/attachments",
                         png, f"e2e-board-{_tag()}.png", "image/png")
    att_img = (p.get("data") or {}).get("id")
    check("★ 教师可上传图片附件到教案",
          p.get("success") and bool(att_img),
          f"id={att_img} {p.get('message', '')[:60]}")

    p, _, _ = _mp_upload(tea1, f"/lesson/plans/{plan_id}/attachments",
                         pptx, f"e2e-courseware-{_tag()}.pptx",
                         "application/vnd.openxmlformats-officedocument"
                         ".presentationml.presentation")
    att_ppt = (p.get("data") or {}).get("id")
    check("★ 教师可上传 PPT 附件到教案",
          p.get("success") and bool(att_ppt),
          f"id={att_ppt} {p.get('message', '')[:60]}")

    # 不支持的类型必须被拒
    p, _, _ = _mp_upload(tea1, f"/lesson/plans/{plan_id}/attachments",
                         b"MZ\x90\x00", "e2e-malware.exe", "application/x-msdownload")
    check("★ 非法扩展名附件被拒",
          p.get("success") is not True,
          p.get("message", "")[:60])

    # 详情返回附件列表（含图片与 PPT）
    p, _, _ = tea1.get(f"/lesson/plans/{plan_id}")
    dets = (data_of(p) or {}).get("attachments") or []
    det_ids = {a.get("id") for a in dets}
    check("★ 教案详情聚合返回附件列表",
          att_img in det_ids and att_ppt in det_ids,
          f"详情附件 {len(dets)} 个：ids={sorted(det_ids)}")
    check("详情附件带预览/下载地址",
          all(a.get("preview_url") and a.get("download_url") for a in dets),
          f"首条 keys={list(dets[0].keys())[:8] if dets else '-'}")

    # 独立附件列表端点
    p, _, _ = tea1.get(f"/lesson/plans/{plan_id}/attachments")
    check("教案附件列表端点可达",
          p.get("success") and len(rows_of(p)) == len(dets),
          f"{len(rows_of(p))} 条")

    # 预览 / 下载可达（二进制响应）
    p, _, sc = tea1.request("GET", f"/attachments/{att_img}/preview")
    check("附件预览可达", sc == 200, f"code={sc}")
    p, _, sc = tea1.request("GET", f"/attachments/{att_ppt}/download")
    check("附件下载可达", sc == 200, f"code={sc}")

    # 越权矩阵
    expect_denied("学生不能上传教案附件", stu, "POST",
                  f"/lesson/plans/{plan_id}/attachments")
    expect_denied("学生不能读教案附件列表", stu, "GET",
                  f"/lesson/plans/{plan_id}/attachments")
    expect_denied("学生不能删除教案附件", stu, "DELETE",
                  f"/lesson/plans/{plan_id}/attachments/{att_img or 0}")
    # 未共享教案：同科 teacher4 不可读附件，也不可上传
    p, _, _ = tea2.get(f"/lesson/plans/{plan_id}/attachments")
    check("★ 未共享教案：同科教师不可读附件",
          p.get("success") is not True,
          p.get("message", ""))
    p, _, _ = _mp_upload(tea2, f"/lesson/plans/{plan_id}/attachments",
                         png, "e2e-cross-upload.png", "image/png")
    check("★ 未共享教案：同科教师不可上传附件",
          p.get("success") is not True,
          p.get("message", "")[:60])
    # 跨教师不可删除他人教案的附件
    p, _, _ = tea2.delete(f"/lesson/plans/{plan_id}/attachments/{att_img or 0}")
    check("★ 跨教师删除教案附件被拒",
          p.get("success") is not True,
          p.get("message", "")[:60])

    # 共享后同科教师可读附件（读权，仍无写权）
    tea1.post(f"/lesson/plans/{plan_id}/share", {"is_shared": True})
    p, _, _ = tea2.get(f"/lesson/plans/{plan_id}/attachments")
    check("★ 共享后同科教师可读附件",
          p.get("success") and len(rows_of(p)) >= 2,
          f"{len(rows_of(p))} 条")
    p, _, _ = _mp_upload(tea2, f"/lesson/plans/{plan_id}/attachments",
                         png, "e2e-shared-upload.png", "image/png")
    check("★ 共享只赋予读权：同科教师仍不可上传",
          p.get("success") is not True,
          p.get("message", "")[:60])

    # 删除单个附件
    if att_ppt:
        p, _, _ = tea1.delete(f"/lesson/plans/{plan_id}/attachments/{att_ppt}")
        check("教师可删除自己教案的附件",
              p.get("success"),
              p.get("message", ""))
        p, _, _ = tea1.get(f"/lesson/plans/{plan_id}/attachments")
        check("删除后附件列表不再包含该条",
              att_ppt not in {a.get("id") for a in rows_of(p)},
              f"剩余 {len(rows_of(p))} 条")

    # ============================================================
    # 7. 清理（删除教案 → 附件解绑而非删除）
    # ============================================================
    R.set_phase("教案管理 | 7. 清理与附件解绑")

    # 记录删除前的附件 id
    p, _, _ = tea1.get(f"/lesson/plans/{plan_id}/attachments")
    keep_ids = [a.get("id") for a in rows_of(p)]

    p, _, _ = tea1.delete(f"/lesson/plans/{plan_id}")
    check("★ 教师可删除自己的教案",
          p.get("success"),
          p.get("message", ""))

    # 附件应被解绑（biz 置空），而不是连带删除——教师资产保留
    if keep_ids:
        p, _, _ = admin.get("/attachments", params={"page_size": 100})
        all_ids = {a.get("id") for a in rows_of(p)}
        check("★ 删除教案后附件保留（解绑不删文件）",
              all(i in all_ids for i in keep_ids),
              f"保留附件 {keep_ids}")
        # 清理测试附件，避免污染
        for i in keep_ids:
            admin.delete(f"/attachments/{i}")

    R.env("教案管理", "见细分阶段")
    print(f"\n[完成] 教案管理专项：教师={tea1.user.get('real_name')}")


def _make_payload(tea, subject_id, grade_id) -> dict:
    """生成一个完整的教案 payload。"""
    return {
        "title": f"{_tag()} {tea.user.get('real_name', '教师')} 教案",
        "topic": "解一元一次方程——移项",
        "subject_id": subject_id,
        "grade_id": grade_id,
        "textbook_version": "人教版",
        "duration_minutes": 45,
        "period": "第 1 课时",
        "objectives": "理解移项的概念；能解简单一元一次方程。",
        "key_points": "移项规则的运用。",
        "difficulties": "移项时变号容易出错。",
        "board_design": "解方程 = 找等式的平衡点 → 移项（变号）",
        "homework": "课本练习 1-3 题",
        "stages": [
            {"name": "导入", "duration_minutes": 3,
             "content": "复习上节，引入新问题。"},
            {"name": "新课讲授", "duration_minutes": 25,
             "content": "教师演示移项；学生分组练习。"},
            {"name": "课堂练习", "duration_minutes": 10,
             "content": "课堂练习 5 道。"},
            {"name": "课堂小结", "duration_minutes": 5,
             "content": "回顾本节要点。"},
            {"name": "布置作业", "duration_minutes": 2,
             "content": "课后习题。"},
        ],
    }


if __name__ == "__main__":
    run()