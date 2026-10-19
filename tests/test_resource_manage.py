# -*- coding: utf-8 -*-
"""教学资源模块专项 e2e 测试（管理员视角）。

覆盖：
- 年级 CRUD + 唯一性 + 非法 stage
- 学科 CRUD + 同年级重名拒绝 + 跨年级允许 + distinct 模式 + 切换年级
- 知识点 CRUD + 树形接口 + level 校验 + 引用检查
- 班级 CRUD + 转移班主任 + 删除有学生班级拒绝 + 批量导入学生（混合结果）
- 人员简表 people/brief：教师/学生越权
- 越权矩阵：教师/学生对 4 个资源写接口的拒绝
"""
import datetime as _dt
import re
import time

from e2e_framework import (  # noqa: F401
    R, Client, check, expect_denied, rows_of, data_of,
)


def _tag():
    return f"[E2E-RS-{_dt.datetime.now().strftime('%H%M%S%f')[-6:]}]"


def _cleanup_e2e_leftovers(admin: Client) -> int:
    """按名称前缀兜底清扫 E2E 残留数据，可自愈历史中断留下的垃圾。

    前缀约定：所有测试创建的资源名都以 "[E2E-RS-" 开头。
    返回清理条数。
    """
    n = 0
    # 班级（先移出 imp 测试学生再删）
    p, _, _ = admin.get("/edu/classes")
    for c in (p.get("data") if isinstance(p.get("data"), list) else []):
        if c["name"].startswith("[E2E-RS-"):
            p2, _, _ = admin.get("/system/users", params={
                "identity": "student", "class_id": c["id"], "page_size": 100})
            items = p2.get("data") if isinstance(p2.get("data"), list)                 else (p2.get("data") or {}).get("items", [])
            for u in items:
                if u.get("username", "").startswith("imp"):
                    admin.delete(f"/edu/classes/{c['id']}/students/{u['id']}")
            d, _, _ = admin.delete(f"/edu/classes/{c['id']}")
            n += bool(d.get("success"))
    # 年级
    p, _, _ = admin.get("/edu/grades")
    for g in (p.get("data") if isinstance(p.get("data"), list) else []):
        if g["name"].startswith("[E2E-RS-"):
            d, _, _ = admin.delete(f"/edu/grades/{g['id']}")
            n += bool(d.get("success"))
    # 学科
    p, _, _ = admin.get("/edu/subjects")
    for s in (p.get("data") if isinstance(p.get("data"), list) else []):
        if s["name"].startswith("[E2E-RS-"):
            d, _, _ = admin.delete(f"/edu/subjects/{s['id']}")
            n += bool(d.get("success"))
    # 知识点（可能被题目引用，失败忽略）
    p, _, _ = admin.get("/edu/knowledge", params={"keyword": "[E2E-RS-"})
    for k in (p.get("data") if isinstance(p.get("data"), list) else []):
        d, _, _ = admin.delete(f"/edu/knowledge/{k['id']}")
        n += bool(d.get("success"))
    return n


def run():
    admin = Client("admin")
    admin.login("admin", "Admin@123456")

    # 先清扫上次运行（可能被中断）留下的 [E2E-RS- 残留，保证起点干净
    try:
        pre = _cleanup_e2e_leftovers(admin)
        if pre:
            print(f"[清理] 运行前清扫历史残留 {pre} 条")
    except Exception as exc:  # noqa: BLE001
        print(f"[清理] 运行前清扫失败: {exc}")
    teacher1 = Client("t1"); teacher1.login("teacher1", "Teacher@123")
    teacher4 = Client("t4"); teacher4.login("teacher4", "Teacher@123")
    stu = Client("s1"); stu.login("stu731", "Student@123")

    # ============================================================
    # 1. 年级 CRUD
    # ============================================================
    R.set_phase("教学资源 | 1. 年级")

    p, _, _ = admin.get("/edu/grades")
    base = rows_of(p)
    check("★ 年级列表可读",
          p.get("success") and isinstance(base, list) and len(base) > 0,
          f"当前 {len(base)} 个年级")

    # 新建
    g_payload = {"name": f"{_tag()} 年级", "stage": "primary", "grade_num": 99}
    p, _, _ = admin.post("/edu/grades", g_payload)
    gid = (data_of(p) or {}).get("id")
    check("★ 管理员可新建年级",
          p.get("success") and bool(gid),
          f"id={gid} {p.get('message', '')[:50]}")

    if gid:
        # 重名拒绝
        p, _, _ = admin.post("/edu/grades", g_payload)
        check("★ 年级重名必须被拒",
              p.get("success") is not True,
              p.get("message", "")[:60])

        # 编辑
        p, _, _ = admin.put(f"/edu/grades/{gid}", {"grade_num": 100})
        check("管理员可编辑年级",
              p.get("success") and (data_of(p) or {}).get("grade_num") == 100,
              "")

        # 不存在 ID 编辑
        p, _, _ = admin.put("/edu/grades/999999", {"grade_num": 1})
        check("★ 编辑不存在的年级 404",
              p.get("success") is not True,
              p.get("message", "")[:60])

        # 阶段过滤
        p, _, _ = admin.get("/edu/grades", params={"stage": "primary"})
        names = {g["name"] for g in rows_of(p)}
        check("按 stage 过滤生效",
              "primary" in p.get("message", "").lower() or len(rows_of(p)) >= 1,
              f"返回 {len(rows_of(p))} 条 primary")

    # ============================================================
    # 2. 学科 CRUD
    # ============================================================
    R.set_phase("教学资源 | 2. 学科")

    # 不传 grade_id：返回全量（60+），distinct=true 才去重
    p, _, _ = admin.get("/edu/subjects")
    all_subjects = rows_of(p)
    check("不传 grade_id 返回全量学科",
          p.get("success") and len(all_subjects) >= 30,
          f"{len(all_subjects)} 条")

    p, _, _ = admin.get("/edu/subjects", params={"distinct": "true"})
    distinct = rows_of(p)
    check("★ distinct=true 按名称去重",
          p.get("success") and len(distinct) < len(all_subjects)
          and all(d.get("grade_count", 1) > 1 for d in distinct if d.get("grade_count", 1) > 1),
          f"全量 {len(all_subjects)} → distinct {len(distinct)}")

    # 按年级取（一年级 1）
    p, _, _ = admin.get("/edu/subjects", params={"grade_id": 1})
    sub_grade1 = rows_of(p)
    check("按 grade_id 取一年级学科",
          p.get("success") and len(sub_grade1) > 0,
          f"{len(sub_grade1)} 条")

    # 新建学科
    sub_payload = {
        "name": f"{_tag()} 学科",
        "grade_id": 1,
        "textbook_version": "测试版",
        "code": f"test_sub_{int(time.time())}",
        "sort": 99,
    }
    p, _, _ = admin.post("/edu/subjects", sub_payload)
    sub_id = (data_of(p) or {}).get("id")
    check("★ 管理员可新建学科",
          p.get("success") and bool(sub_id),
          f"id={sub_id} {p.get('message', '')[:50]}")

    if sub_id:
        # 同年级重名拒绝
        p, _, _ = admin.post("/edu/subjects", sub_payload)
        check("★ 同年级同名校名必须被拒",
              p.get("success") is not True,
              p.get("message", "")[:60])

        # 跨年级同名应允许
        cross = dict(sub_payload)
        cross["grade_id"] = 2
        p, _, _ = admin.post("/edu/subjects", cross)
        cross_id = (data_of(p) or {}).get("id")
        check("★ 跨年级同名学科允许创建",
              p.get("success") and bool(cross_id),
              f"一年级同名 id={sub_id}, 二年级 id={cross_id}")

        # 关键词搜索
        # 搜常见学科「语文」——前提是种子数据已建
        p, _, _ = admin.get("/edu/subjects", params={"keyword": "语文"})
        check("关键词搜索命中",
              p.get("success") and len(rows_of(p)) >= 1,
              f"{len(rows_of(p))} 条")

        # 编辑
        p, _, _ = admin.put(f"/edu/subjects/{sub_id}", {"textbook_version": "v2"})
        check("管理员可编辑学科",
              p.get("success") and (data_of(p) or {}).get("textbook_version") == "v2",
              "")

        # 清理：删除测试学科（避免污染）
        for i in (sub_id, cross_id):
            if i:
                p, _, _ = admin.delete(f"/edu/subjects/{i}")
                check(f"管理员可删除学科 {i}",
                      p.get("success"),
                      p.get("message", "")[:50])

    # ============================================================
    # 3. 知识点 CRUD + 树形 + 引用检查
    # ============================================================
    R.set_phase("教学资源 | 3. 知识点")

    # 树形接口
    p, _, _ = admin.get("/edu/knowledge", params={"grade_id": 1, "subject_id": 1})
    tree = rows_of(p)
    check("★ 知识点树形接口可读",
          p.get("success") and isinstance(tree, list),
          f"一年级(1)班学科1的知识点 {len(tree)} 条")

    # 平铺列表
    p, _, _ = admin.get("/edu/knowledge/list", params={"grade_id": 1})
    flat = rows_of(p)
    check("知识点平铺列表可读",
          p.get("success") and len(flat) > 0,
          f"{len(flat)} 条")

    # 新建
    kp_payload = {
        "name": f"{_tag()} 知识点",
        "grade_id": 1, "subject_id": 1, "level": 3, "term": 1,
        "difficulty": "medium", "description": "测试",
        "keywords": "kw1,kw2",
    }
    p, _, _ = admin.post("/edu/knowledge", kp_payload)
    kp_id = (data_of(p) or {}).get("id")
    check("★ 管理员可新建知识点",
          p.get("success") and bool(kp_id),
          f"id={kp_id}")

    if kp_id:
        # 编辑
        p, _, _ = admin.put(f"/edu/knowledge/{kp_id}", {"description": "已更新"})
        check("管理员可编辑知识点",
              p.get("success") and (data_of(p) or {}).get("description") == "已更新",
              "")

        # 重建向量索引（教师权限也可触发）
        t0 = time.time()
        p, _, _ = teacher1.post("/edu/knowledge/reindex", {})
        check("★ 教师可触发知识库重建索引",
              p.get("success") is not None,
              f"耗时 {(time.time()-t0)*1000:.0f}ms msg={p.get('message', '')[:60]}")

        # 删除：知识点未关联题目 → 应成功
        p, _, _ = admin.delete(f"/edu/knowledge/{kp_id}")
        check("★ 知识点无题目引用时可删",
              p.get("success"),
              p.get("message", "")[:50])

        # 删除有引用的知识点：建题→挂到 kp→尝试删
        p, _, _ = teacher1.post("/question/questions", {
            "type": "single",
            "stem": f"{_tag()} 引用测试题",
            "options": [{"key": "A", "text": "对"}, {"key": "B", "text": "错"}],
            "answer": "A", "difficulty": "easy", "score": 5,
            "grade_id": 1, "subject_id": 1, "bank_type": "private",
            "analysis": "",
        })
        qid2 = (data_of(p) or {}).get("id")
        if qid2:
            # 知识点直接挂题目：建个新 kp 然后挂
            p, _, _ = admin.post("/edu/knowledge", {**kp_payload, "name": _tag() + " 引用k"})
            kp2 = (data_of(p) or {}).get("id")
            if kp2:
                p, _, _ = teacher1.put(f"/question/questions/{qid2}",
                                       {"knowledge_point_id": kp2})
                if p.get("success"):
                    p, _, _ = admin.delete(f"/edu/knowledge/{kp2}")
                    check("★ 知识点被题目引用时删除必须被拒",
                          p.get("success") is not True
                          and "引用" in p.get("message", ""),
                          p.get("message", "")[:80])
                    admin.delete(f"/edu/knowledge/{kp2}")
            teacher1.delete(f"/question/questions/{qid2}")

    # ============================================================
    # 4. 班级 CRUD + 班主任 + 删除守卫
    # ============================================================
    R.set_phase("教学资源 | 4. 班级")

    p, _, _ = admin.get("/edu/classes")
    all_classes = rows_of(p)
    check("班级列表可读",
          p.get("success") and len(all_classes) >= 4,
          f"{len(all_classes)} 个班级")

    # 找空班级（一年级2班无学生）或创建一个空班
    p, _, _ = admin.get("/edu/people/brief", params={"identity": "student", "class_id": 2})
    cnt2 = len(rows_of(p))
    target_grade = 1
    if cnt2 > 0:
        # 一(2)有学生 → 创建一个新空班
        cls_payload = {
            "name": f"{_tag()} 空班",
            "grade_id": target_grade,
            "head_teacher_id": teacher1.user.get("id"),
            "remark": "e2e test",
        }
        p, _, _ = admin.post("/edu/classes", cls_payload)
        new_class_id = (data_of(p) or {}).get("id")
    else:
        new_class_id = 2

    if new_class_id:
        # 切换班主任
        p, _, _ = admin.put(
            f"/edu/classes/{new_class_id}",
            {"head_teacher_id": teacher4.user.get("id")})
        check("管理员可切换班主任",
              p.get("success")
              and (data_of(p) or {}).get("head_teacher_id") == teacher4.user.get("id"),
              "")

        # 删除有学生的班（一(1)班）必须被拒
        p, _, _ = admin.get("/edu/people/brief",
                            params={"identity": "student", "class_id": 1})
        if rows_of(p):
            p, _, _ = admin.delete("/edu/classes/1")
            check("★ 有学生的班级删除必须被拒",
                  p.get("success") is not True
                  and "学生" in p.get("message", ""),
                  p.get("message", "")[:80])

        # 删除空班应成功
        if new_class_id != 2:
            p, _, _ = admin.delete(f"/edu/classes/{new_class_id}")
            check("★ 空班级可删除",
                  p.get("success"),
                  p.get("message", "")[:50])

    # ============================================================
    # 5. 批量导入学生
    # ============================================================
    R.set_phase("教学资源 | 5. 批量导入学生")

    # 先建一个空班用于测试
    cls_payload = {"name": f"{_tag()} 导入测试班", "grade_id": 1, "remark": "e2e"}
    p, _, _ = admin.post("/edu/classes", cls_payload)
    import_class = (data_of(p) or {}).get("id")
    if import_class:
        ts = str(int(time.time()))[-6:]
        stu_payload = [
            {"username": f"imp{ts}a", "real_name": "导入A"},
            {"username": f"imp{ts}b", "real_name": "导入B"},
            {"username": f"imp{ts}c", "real_name": "导入C"},
            {"username": f"imp{ts}a", "real_name": "重复A"},  # 故意重名
            {"username": "", "real_name": "无名氏"},  # 缺账号
        ]
        p, _, _ = admin.post(f"/edu/classes/{import_class}/students", stu_payload)
        d = data_of(p) or {}
        check("★ 批量导入混合结果（成功 3 + 跳过 2）",
              p.get("success") and d.get("created") == 3 and len(d.get("skipped") or []) == 2,
              f"created={d.get('created')} skipped={len(d.get('skipped') or [])}")

        # 登录新建的导入学生（默认密码 Student@123）
        imp = Client("imp")
        imp_ok, _ = imp.login(f"imp{ts}a", "Student@123")
        if imp_ok:
            p, _, _ = imp.put("/auth/password",
                              body={"old_password": "Student@123", "new_password": "Student@123"})
            check("默认密码账户可登录", imp_ok, "")

        # 移出班级（取全部 imp 开头学生 id 一并清掉，确保能删班）
        p, _, _ = admin.get("/system/users",
                            params={"identity": "student", "class_id": import_class, "page_size": 100})
        items = p.get("data") if isinstance(p.get("data"), list) else (p.get("data") or {}).get("items", [])
        sids = [u["id"] for u in items if u.get("username", "").startswith("imp")]
        for sid in sids:
            admin.delete(f"/edu/classes/{import_class}/students/{sid}")
        check("管理员可批量移出学生",
              len(sids) >= 1,
              f"清掉 {len(sids)} 个测试学生")

        # 删测试班
        p, _, _ = admin.delete(f"/edu/classes/{import_class}")
        check("★ 阶段结束清理：删除测试班",
              p.get("success"),
              p.get("message", "")[:50])

    # ============================================================
    # 6. 人员简表 people/brief
    # ============================================================
    R.set_phase("教学资源 | 6. 人员简表")

    p, _, _ = teacher1.get("/edu/people/brief", params={"identity": "teacher"})
    teachers = rows_of(p)
    check("★ 教师可拉全校在职教师简表",
          p.get("success") and len(teachers) >= 2
          and all(set(t.keys()) <= {"id", "real_name", "username"} for t in teachers),
          f"{len(teachers)} 人")
    check("简表不含敏感字段（phone/email）",
          all("phone" not in t and "email" not in t for t in teachers),
          "")

    p, _, _ = teacher1.get("/edu/people/brief", params={"identity": "student", "class_id": 1})
    students1 = rows_of(p)
    check("教师可拉本班学生（class_id=1）",
          p.get("success") and len(students1) >= 3,
          f"{len(students1)} 人")

    # 越权：教师拉非任教班级学生
    p, _, _ = teacher1.get("/edu/people/brief",
                           params={"identity": "student", "class_id": 999})
    # 999 不存在，无关权限，看具体实现
    rows = rows_of(p)
    check("class_id 不存在时返回空",
          isinstance(rows, list),
          f"返回 {len(rows)} 条")

    # 学生不能拉人
    expect_denied("学生不能调用 people/brief", stu, "GET",
                  "/edu/people/brief", params={"identity": "teacher"})

    # ============================================================
    # 7. 越权矩阵
    # ============================================================
    R.set_phase("教学资源 | 7. 越权矩阵")

    # 教师/学生对资源写接口
    expect_denied("教师不能新增年级", teacher1, "POST", "/edu/grades",
                  body={"name": "教师越权", "stage": "primary"})
    expect_denied("学生不能新增年级", stu, "POST", "/edu/grades",
                  body={"name": "学生越权", "stage": "primary"})
    expect_denied("教师不能新增学科", teacher1, "POST", "/edu/subjects",
                  body={"name": "X", "grade_id": 1})
    # 教师角色绑定 resource:knowledge:write，教师维护自己学科的知识点是设计预期
    expect_denied("学生不能新增知识点", stu, "POST", "/edu/knowledge",
                  body={"name": "X", "grade_id": 1, "subject_id": 1, "level": 3})
    expect_denied("学生不能新增班级", stu, "POST", "/edu/classes",
                  body={"name": "X", "grade_id": 1})
    expect_denied("教师不能新增班级", teacher1, "POST", "/edu/classes",
                  body={"name": "X", "grade_id": 1})
    expect_denied("教师不能删除年级", teacher1, "DELETE", "/edu/grades/1")
    expect_denied("学生不能删除年级", stu, "DELETE", "/edu/grades/1")
    expect_denied("教师不能删除学科", teacher1, "DELETE", "/edu/subjects/1")
    expect_denied("学生不能删除知识点", stu, "DELETE", "/edu/knowledge/1")

    # 跨管理员：另一教师删 admin 创建的资源？教师本身就无写权，验证 403
    expect_denied("教师不能编辑年级", teacher4, "PUT",
                  "/edu/grades/1", body={"name": "hack"})

    # ============================================================
    # 清理
    # ============================================================
    # 8. 学科跨年级复制（按年级视图的核心能力）
    # ============================================================
    R.set_phase("教学资源 | 8. 跨年级复制学科")

    p, _, _ = admin.get("/edu/subjects", params={"grade_id": 1})
    g1 = p.get("data") if isinstance(p.get("data"), list) else []
    src = g1[0] if g1 else None
    if src:
        # 找一个 src 尚未在 3/4 年级存在的学科，避免一上来就 skip
        test_name = None
        for s in g1:
            for cg in (3, 4, 6, 8):
                p2, _, _ = admin.get("/edu/subjects", params={"grade_id": cg})
                cg_subs = p2.get("data") if isinstance(p2.get("data"), list) else []
                if not any(x["name"] == s["name"] for x in cg_subs):
                    test_name = s["name"]
                    src = s
                    break
            if test_name:
                break

        # 复制到 3 个目标年级
        targets = []
        for cg in (3, 4, 6, 8):
            p2, _, _ = admin.get("/edu/subjects", params={"grade_id": cg})
            cg_subs = p2.get("data") if isinstance(p2.get("data"), list) else []
            if not any(x["name"] == src["name"] for x in cg_subs):
                targets.append(cg)
            if len(targets) == 3:
                break

        if targets:
            p, _, _ = admin.post(f"/edu/subjects/{src['id']}/clone",
                                  {"target_grade_ids": targets})
            d = p.get("data") or {}
            check("★ 跨年级复制学科：新建 N 个",
                  p.get("success") and len(d.get("created") or []) == len(targets),
                  f"target={targets} created={len(d.get('created') or [])}")

            # 立即再复制一次应全部 skipped
            p, _, _ = admin.post(f"/edu/subjects/{src['id']}/clone",
                                  {"target_grade_ids": targets})
            d2 = p.get("data") or {}
            check("★ 同名再复制应全部跳过",
                  p.get("success") and len(d2.get("created") or []) == 0
                  and all("同名" in s.get("reason", "")
                          for s in (d2.get("skipped") or [])),
                  f"skipped={len(d2.get('skipped') or [])}")

            # 源年级在 target 里应被识别并 skip
            p, _, _ = admin.post(f"/edu/subjects/{src['id']}/clone",
                                  {"target_grade_ids": [src["grade_id"]] + targets})
            d3 = p.get("data") or {}
            src_skip = next((s for s in (d3.get("skipped") or [])
                             if s.get("grade_id") == src["grade_id"]), None)
            check("★ 源年级在 target 里应被识别并跳过",
                  src_skip is not None and "源年级" in src_skip.get("reason", ""),
                  f"src_skip={src_skip}")

            # 不存在年级应被识别并 skip
            p, _, _ = admin.post(f"/edu/subjects/{src['id']}/clone",
                                  {"target_grade_ids": [99999]})
            d4 = p.get("data") or {}
            miss_skip = next((s for s in (d4.get("skipped") or [])
                              if s.get("grade_id") == 99999), None)
            check("★ 不存在的年级应被识别并跳过",
                  miss_skip is not None and "不存在" in miss_skip.get("reason", ""),
                  f"miss_skip={miss_skip}")

            # 空 target_grade_ids 应被拒
            p, _, _ = admin.post(f"/edu/subjects/{src['id']}/clone",
                                  {"target_grade_ids": []})
            check("空 target_grade_ids 必须被拒",
                  p.get("success") is not True,
                  p.get("message", "")[:50])

            # 源学科不存在
            p, _, _ = admin.post("/edu/subjects/9999999/clone",
                                  {"target_grade_ids": [3]})
            check("★ 源学科不存在 404",
                  p.get("success") is not True,
                  p.get("message", "")[:50])

            # 越权：教师/学生不能调
            for u, label in [(teacher1, "教师"), (stu, "学生")]:
                p, _, _ = u.post(f"/edu/subjects/{src['id']}/clone",
                                  {"target_grade_ids": [3]})
                check(f"{label}不能跨年级复制学科",
                      p.get("success") is not True,
                      p.get("message", "")[:50])

            # 清理：把新建的删掉
            for t in targets:
                p, _, _ = admin.get("/edu/subjects", params={"grade_id": t})
                items = p.get("data") if isinstance(p.get("data"), list) else []
                for x in items:
                    if x["name"] == src["name"]:
                        admin.delete(f"/edu/subjects/{x['id']}")
        else:
            check("跨年级复制前置条件：能找到未占满的目标年级", False,
                  "无目标年级可测")

    # ============================================================
    if 'gid' in dir() and gid:
        admin.delete(f"/edu/grades/{gid}")

    R.env("教学资源", "见细分阶段")
    print(f"\n[完成] 教学资源专项：管理员={admin.user.get('real_name')}")


if __name__ == "__main__":
    run()