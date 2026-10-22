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
    g1 = grades[0]  # 后续用例统一用一年级（subject 取 subjects[1]，即数学）

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

    # 共享范围：仅同科教师可见。teacher4 任教七年级，本教案属一年级，
    # 属跨学科 → 不应出现在其列表中（此前实现只判 is_shared，所有教师可见）。
    p, _, _ = tea2.get("/lesson/plans", params={"page_size": 50})
    cross_visible = any((r or {}).get("id") == plan_id for r in rows_of(p))
    check("★ 跨学科教师看不到他人共享教案（学科隔离生效）",
          not cross_visible,
          f"teacher4(七年级) 列表中含一年级教案={cross_visible}")
    # 自己仍然可见（共享不改变创建者可见性）
    p, _, _ = tea1.get("/lesson/plans", params={"page_size": 50})
    check("共享后创建者本人仍可见",
          any((r or {}).get("id") == plan_id for r in rows_of(p)), "")

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
    # 新结构承载 AI 教案的「教学准备 / 课堂练习 / 师生活动」。
    # 这四类字段老库没有，靠 db_migrations 补列 —— 若迁移漏登记，
    # 这里会在**读写时** 500，而不是悄悄返回 None。
    check("★ 详情含新增章节字段（教学准备/课堂练习/来源标记）",
          all(k in det for k in ("teaching_preparation", "class_exercise",
                                 "ai_generated", "ai_job_id")),
          f"keys 缺失: {[k for k in ('teaching_preparation', 'class_exercise', 'ai_generated', 'ai_job_id') if k not in det]}")
    stage0 = (det.get("stages") or [{}])[0]
    check("★ 阶段含师生活动分列字段",
          "teacher_activity" in stage0 and "student_activity" in stage0,
          f"stage keys={sorted(stage0.keys())}")

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

    # 教学准备 / 课堂练习 必须真正落库并被回读（新增字段的写入链路）
    p, _, _ = tea1.put(f"/lesson/plans/{plan_id}", {
        "teaching_preparation": "教师准备：三角板、课件；学生准备：练习本",
        "class_exercise": "1. 解方程 2x+3=7（答案：x=2）",
    })
    check("教师可写入教学准备/课堂练习", p.get("success"), p.get("message", ""))
    p, _, _ = tea1.get(f"/lesson/plans/{plan_id}")
    d2 = data_of(p) or {}
    # 断言具体内容而非「非空」：字段被后端忽略时 detail 仍返回 200，
    # 只判 success 会让「写入静默丢失」也通过。
    check("★ 教学准备/课堂练习已落库并可回读",
          d2.get("teaching_preparation") == "教师准备：三角板、课件；学生准备：练习本"
          and "2x+3=7" in (d2.get("class_exercise") or ""),
          f"prep={(d2.get('teaching_preparation') or '')[:20]!r} "
          f"exercise_len={len(d2.get('class_exercise') or '')}")

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

    # ============================================================
    # 8. AI 教案生成（异步任务 + 轮询 + 入库 + 导出）
    # ============================================================
    _run_ai_lesson(tea1, stu, subjects[1]["id"], g1["id"])


def _run_ai_lesson(tea, stu, subject_id, grade_id):
    """AI 教案：提交 → 轮询 → 结构校验 → 入库 → 导出 + 权限/异常边界。

    设计要点：
    - 生成走异步任务，必须**轮询到终态**再断言；只看提交接口返回 200
      无法证明后台线程真的跑通（早期 e2e 里「提交成功即通过」是最常见的假绿）。
    - 结构断言不写死环节名与时长数值，只断言「可上课」的语义条件：
      环节数够、总时长等于课时、师生活动非空、必填章节非空。
    - 无 LLM 时走规则引擎，结果依然必须满足上述条件 —— 这正是 fallback 的验收标准。
    """
    R.set_phase("AI 教案 | 8. 生成任务与结构完整性")

    # ---- 8.1 权限：学生不能提交 ----
    p, _, sc = stu.post("/lesson/ai/generate",
                        {"topic": "测试", "grade_id": grade_id, "subject_id": subject_id})
    check("★ 学生调用 AI 教案生成被拒",
          p.get("success") is not True and sc == 403,
          f"HTTP {sc} {p.get('message', '')[:30]}")

    # ---- 8.2 参数校验：学科与年级不匹配必须拒 ----
    # 学科按年级配置（unique(grade_id,name)），跨年级传 id 会生成整份错年级教案
    p, _, _ = tea.post("/lesson/ai/generate",
                       {"topic": "测试", "grade_id": grade_id, "subject_id": 999999})
    check("★ 不存在的学科 id 被拒", p.get("success") is not True, p.get("message", ""))

    p, _, _ = tea.post("/lesson/ai/generate", {"topic": "", "grade_id": grade_id,
                                               "subject_id": subject_id})
    check("空主题被拒", p.get("success") is not True, p.get("message", ""))

    p, _, _ = tea.post("/lesson/ai/generate",
                       {"topic": "x", "grade_id": grade_id, "subject_id": subject_id,
                        "duration_minutes": 3})
    check("★ 课时越界（<15 分钟）被拒", p.get("success") is not True, p.get("message", ""))

    # ---- 8.3 正常提交并轮询至终态 ----
    topic = f"{_tag()} AI 勾股定理"
    p, _, _ = tea.post("/lesson/ai/generate", {
        "topic": topic, "grade_id": grade_id, "subject_id": subject_id,
        "duration_minutes": 45, "period": "第 1 课时",
    })
    job_id = (data_of(p) or {}).get("job_id")
    check("★ 教师可提交 AI 教案生成任务",
          p.get("success") and bool(job_id),
          f"job_id={job_id} {p.get('message', '')[:40]}")
    if not job_id:
        return

    # 轮询：epoll 到 success/failed；LLM 下最长 60s，给足 120s
    job = _poll_job(tea, job_id, timeout=120)
    check("★ 生成任务最终成功（非超时/失败）",
          job.get("status") == "success",
          f"status={job.get('status')} err={(job.get('error') or '')[:60]}")

    result = job.get("result") or {}
    gen = result.get("generation") or {}

    # ---- 8.4 结构完整性：这是「可直接使用」的硬门槛 ----
    if job.get("status") == "success":
        check("★ 生成结果显示完成进度 100%",
              job.get("progress") == 100,
              f"progress={job.get('progress')} stage={job.get('stage')}")

        # 必备章节（用户明确要求：目标/重难点/准备/过程/练习/作业/板书）
        required = ("objectives", "key_points", "difficulties", "teaching_preparation",
                    "class_exercise", "homework", "board_design")
        empty = [k for k in required if len(str(result.get(k) or "").strip()) < 8]
        check("★ 七类必备章节全部非空",
              not empty,
              f"空章节={empty}" if empty else "目标/重难点/准备/练习/作业/板书齐备")

        stages = result.get("stages") or []
        check("★ 教学过程至少 4 个环节",
              len(stages) >= 4,
              f"{len(stages)} 个：{[s.get('name') for s in stages][:6]}")

        # 时长必须精确等于课时 —— 合计不等意味着课上不完
        total = sum(int(s.get("duration_minutes") or 0) for s in stages)
        check("★ 各环节时长合计精确等于课时（45 分钟）",
              total == 45,
              f"合计 {total} 分钟")

        # 师生活动分列非空：否则退化成流程提纲
        no_act = [s.get("name") for s in stages
                  if not (s.get("teacher_activity") and s.get("student_activity"))]
        check("★ 每个环节都有教师活动与学生活动",
              not no_act,
              f"缺活动环节={no_act}" if no_act else "全部齐备")

        check("生成结果带回年级/学科名称（前端免二次查询）",
              bool(result.get("grade_name")) and bool(result.get("subject_name")),
              f"{result.get('grade_name')}/{result.get('subject_name')}")
        # 生成元信息必须存在，前端要靠它提示「哪几节是补的」
        check("★ 生成结果含质量元信息（mode/missing/quality）",
              all(k in gen for k in ("mode", "missing", "quality")),
              f"mode={gen.get('mode')} quality={gen.get('quality')} "
              f"missing={gen.get('missing')}")

    # ---- 8.5 越权：别的教师读不到 ----
    other = Client("t_ai_other"); other.login("teacher4", "Teacher@123")
    p, _, sc = other.get(f"/lesson/ai/jobs/{job_id}")
    check("★ 其他教师无法查看他人生成任务",
          p.get("success") is not True and sc == 403,
          f"HTTP {sc}")

    # ---- 8.6 导出 ----
    p, _, sc = tea.get(f"/lesson/ai/jobs/{job_id}/export")
    # 导出返回 text/markdown（非 JSON）：框架会包成
    # {"data": {"bytes": N, "content_type": ..., "filename": ...}}。
    # 因此断言「是二进制流 + 类型是 markdown + 有实际字节」，
    # 而不是去 body 里找 "#"（那样永远找不到，是恒假断言）。
    meta = (data_of(p) or {}) if isinstance(p, dict) else {}
    check("★ 生成结果可导出为 Markdown",
          sc == 200 and (meta.get("bytes") or 0) > 200
          and "markdown" in str(meta.get("content_type") or ""),
          f"HTTP {sc} bytes={meta.get('bytes')} type={meta.get('content_type')}")

    # ---- 8.7 入库（含用户覆盖字段）----
    override_board = "用户手改的板书内容"
    p, _, _ = tea.post(f"/lesson/ai/jobs/{job_id}/save", {"board_design": override_board})
    plan_id = (data_of(p) or {}).get("plan_id")
    check("★ 生成结果可保存到教案库",
          p.get("success") and bool(plan_id),
          f"plan_id={plan_id} {p.get('message', '')[:40]}")

    if plan_id:
        p, _, _ = tea.get(f"/lesson/plans/{plan_id}")
        saved = data_of(p) or {}
        check("★ 入库后 ai_generated=1 且记录来源任务",
              saved.get("ai_generated") in (1, True) and saved.get("ai_job_id") == job_id,
              f"ai_generated={saved.get('ai_generated')} ai_job_id={saved.get('ai_job_id')}")
        check("★ 用户在预览界面的修改优先于生成结果",
              saved.get("board_design") == override_board,
              f"board_design={(saved.get('board_design') or '')[:30]!r}")
        check("★ 入库后保留完整的教学过程与师生活动",
              len(saved.get("stages") or []) >= 4
              and all(s.get("teacher_activity") for s in (saved.get("stages") or [])),
              f"{len(saved.get('stages') or [])} 个环节")
        check("★ 入库后教学准备/课堂练习不为空",
              len(saved.get("teaching_preparation") or "") >= 8
              and len(saved.get("class_exercise") or "") >= 8,
              f"prep={len(saved.get('teaching_preparation') or '')} "
              f"exercise={len(saved.get('class_exercise') or '')}")
        # 清理
        tea.delete(f"/lesson/plans/{plan_id}")

    # ---- 8.8 失败任务的保存/导出必须被拒 ----
    p, _, _ = tea.post("/lesson/ai/jobs/999999/save", {})
    check("★ 不存在的任务保存被拒", p.get("success") is not True, p.get("message", ""))

    # ---- 8.9 生成记录列表 ----
    p, _, _ = tea.get("/lesson/ai/jobs", params={"limit": 10})
    items = rows_of(p)
    check("★ 生成记录列表可读且含刚提交的任务",
          p.get("success") and isinstance(items, list)
          and any(i.get("job_id") == job_id for i in items),
          f"{len(items)} 条")


def _poll_job(tea, job_id, timeout=120, interval=1.0):
    """轮询任务至终态。返回最后一次 job 数据（含 status/result/error）。"""
    import time as _t

    deadline = _t.time() + timeout
    job = {}
    while _t.time() < deadline:
        p, _, _ = tea.get(f"/lesson/ai/jobs/{job_id}")
        job = data_of(p) or {}
        if job.get("status") in ("success", "failed"):
            return job
        _t.sleep(interval)
    return job


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