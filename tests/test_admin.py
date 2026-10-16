# -*- coding: utf-8 -*-
"""
阶段一：管理员（admin）视角 —— 系统全貌巡检

覆盖：
- 环境探活与认证安全（弱口令、越权、伪造 Token）
- 组织架构（年级 / 学科 / 班级 / 知识点）
- 用户与角色 RBAC（权限点、角色复制、数据范围）
- 注册审批流
- 日志审计（登录 / 操作 / 错误）
- 定时任务与执行记录
- 附件与系统配置
- 管理员报表（总览 / 年级对比 / 学科对比 / 运行时）
- Agent 状态
"""
import time

from e2e_framework import (R, Client, check, data_of, rows_of, total_of,
                           expect_denied, is_down, BASE)

ACCT = {"admin": "Admin@123456", "teacher1": "Teacher@123", "stu731": "Student@123"}


def run():
    admin = Client("admin")
    anon = Client("匿名")

    # ---------------------------------------------------------- 0 探活
    R.set_phase("阶段一 · 管理员视角 | 0. 环境探活")
    p, _, _ = admin.get("/health")
    if is_down(p):
        R.env("服务可访问", f"{BASE} 不可达 —— 请先执行 start.bat 启动服务")
        return None
    h = data_of(p) or {}
    check("服务健康", h.get("status") == "healthy",
          f"{BASE} -> {h.get('status')} db={h.get('database')} llm={h.get('llm_enabled')}")
    R.context["health"] = h

    # ---------------------------------------------------------- 1 认证
    R.set_phase("阶段一 · 管理员视角 | 1. 认证与令牌安全")

    expect_denied("未登录访问受保护接口被拒绝", anon, "GET", "/system/users")

    ok, detail = admin.login("admin", "wrong-password-xxx")
    check("错误密码登录被拒绝", not ok and not admin.unreachable, detail)

    ok, detail = admin.login("admin", "admin123")
    check("弱口令 admin123 被拒绝", not ok and not admin.unreachable, detail)

    ok, detail = admin.login("no_such_user_zzz", "Admin@123456")
    check("不存在的账号登录被拒绝", not ok and not admin.unreachable, detail)

    ok, detail = admin.login("admin", ACCT["admin"])
    check("admin 使用正确密码登录成功", ok, detail)
    if not ok:
        return admin
    R.context["admin_id"] = admin.user["id"]

    p, _, _ = anon.get("/auth/captcha")
    cap = data_of(p) or {}
    check("验证码接口可用", p.get("success") and bool(cap.get("captcha_id") or cap.get("key")),
          f"字段={list(cap.keys())}")

    p, _, _ = admin.get("/system/permissions")
    pd = data_of(p)
    if isinstance(pd, list):
        n_perm = len(pd)
    elif isinstance(pd, dict):
        flat = pd.get("items") or pd.get("permissions") or []
        n_perm = len(flat)
    else:
        n_perm = 0
    check("权限点可读取", p.get("success") and n_perm > 0, f"权限点 {n_perm} 个")

    me = admin.permission or {}
    R.context["admin_roles"] = me.get("roles", [])
    check("admin 角色为 sys_admin", "sys_admin" in (me.get("roles") or []),
          f"roles={me.get('roles')}")
    pset = set(me.get("permissions") or [])
    check("admin 拥有通配权限 *", "*" in pset, f"权限点数={len(pset)}")

    # ---------------------------------------------------------- 2 组织架构
    R.set_phase("阶段一 · 管理员视角 | 2. 组织架构（年级/学科/班级/知识点）")

    p, _, _ = admin.get("/edu/grades")
    grades = rows_of(p)
    check("年级列表", p.get("success") and len(grades) == 9, f"{len(grades)} 个年级")

    p, _, _ = admin.get("/edu/subjects")
    subs = rows_of(p)
    check("学科列表", p.get("success") and len(subs) > 0, f"{len(subs)} 个学科条目")

    dup = {}
    for s in subs:
        dup.setdefault(s.get("name"), []).append(s.get("grade_id"))
    multi = {k: v for k, v in dup.items() if len(v) > 1}
    check("学科按年级维度独立建模", len(multi) > 0,
          f"同名跨年级学科 {len(multi)} 种，如 数学出现 {len(multi.get('数学', []))} 次")

    p, _, _ = admin.get("/edu/classes")
    classes = rows_of(p)
    check("班级列表", p.get("success") and len(classes) == 4, f"{len(classes)} 个班级")

    p, _, _ = admin.get("/edu/knowledge/list")
    kps = rows_of(p)
    check("知识点列表可读取", p.get("success"), f"知识点 {len(kps)} 条")
    if not kps:
        R.issue("高", "知识点库为空，AI 组卷与错题归因均无法工作",
                "edu_knowledge_point 表 0 条。智能组卷需要 knowledge_point_ids 作为选题依据，"
                "错题本的知识点归因、知识掌握地图也都依赖知识点。"
                "初始化脚本只播种了年级/学科/班级/用户，遗漏了知识点。",
                "GET /api/v1/edu/knowledge/list -> items=[]")

        gid = next((g["id"] for g in grades if g["name"] == "七年级"), grades[0]["id"])
        sid = next((s["id"] for s in subs
                    if s.get("grade_id") == gid and s["name"] == "数学"), None)
        if sid:
            # 首次调用会触发 Chroma 向量库冷启动，单独放宽超时并记录耗时
            p, ms, _ = admin.post("/edu/knowledge", {
                "name": "一元一次方程", "subject_id": sid, "grade_id": gid,
                "level": 1, "description": "自动化测试创建",
            }, timeout=120)
            d = data_of(p) or {}
            if is_down(p):
                R.env("知识点可创建", f"请求超时/不可达（{ms}ms）")
            elif p.get("success") and d.get("id"):
                R.context["kp_id"] = d["id"]
                R.context["kp_subject_id"] = sid
                R.context["kp_grade_id"] = gid
                check("知识点可创建（管理员可写教学接口）", True,
                      f"id={d['id']} {d.get('name')} 耗时 {ms}ms")
                if ms > 3000:
                    R.issue("中", "知识点首次写入严重慢（Chroma 冷启动阻塞请求）",
                            f"首次 POST /edu/knowledge 耗时 {ms}ms，超过默认 30s 超时。"
                            "原因是 index_knowledge 在请求线程内同步初始化 ChromaDB 与 "
                            "embedding 模型，未做预热与懒加载。生产环境首次建知识点"
                            "或 AI 组卷时会表现为接口长时间无响应。",
                            "POST /api/v1/edu/knowledge (首次调用)")
                p2, _, _ = admin.get("/edu/knowledge/list")
                kps2 = rows_of(p2)
                check("新建知识点出现在列表中",
                      any(k["id"] == d["id"] for k in kps2), f"共 {len(kps2)} 条")
            else:
                check("知识点可创建（管理员可写教学接口）", False, p.get("message"))
                R.issue("高", "知识点创建接口失败",
                        f"POST /edu/knowledge -> {p.get('message')}", "POST /api/v1/edu/knowledge")

    # 服务端有 REINDEX_TIMEOUT_SEC(默认 90s) 硬超时，
    # 客户端留 20s 余量；超时会返回 success=true + timed_out 标记，
    # 不应判定为「接口不可达」。
    p, ms, _ = admin.post("/edu/knowledge/reindex", {}, timeout=110)
    d = p.get("data") or {}
    check("知识点向量重建索引接口可调用", p.get("success"),
          f"{ms}ms {p.get('message', '')}")
    if d.get("timed_out"):
        R.env("向量重建超时（已按预期中断并返回部分结果）",
              f"{ms}ms 知识点={d.get('knowledge')} 题目={d.get('question')}；"
              "多因首次运行需下载 embedding 模型")

    # ---------------------------------- 2b 资源权限矩阵（本轮收紧回归）
    # 设计：年级/学科/班级/导入学生 = manager 角色（sys_admin+grade_admin），
    #       知识点写 = 权限点 resource:knowledge:write（teacher/grade_admin 均授）。
    # 教师对全校性基础数据只读；班级菜单可见但只读（有 list 无 write）。
    R.set_phase("阶段一 · 管理员视角 | 2b. 资源权限矩阵")
    tea2b = Client("teacher1")
    ok_t, d_t = tea2b.login("teacher1", ACCT["teacher1"])
    check("teacher1 登录（权限矩阵用）", ok_t, d_t)
    if ok_t:
        # 教师写班级 → 403（require_perm class:write，teacher 无该权限点）
        expect_denied("教师新增班级被拒", tea2b, "POST", "/edu/classes",
                      body={"name": "越权班级", "grade_id": 1})
        expect_denied("教师修改班级被拒", tea2b, "PUT", "/edu/classes/1",
                      body={"name": "越权改名"})
        expect_denied("教师删除班级被拒", tea2b, "DELETE", "/edu/classes/1")
        expect_denied("教师批量导入学生被拒（创建账号属敏感操作）",
                      tea2b, "POST", "/edu/classes/1/students",
                      body=[{"username": "hack001", "real_name": "越权"}])
        # 教师写知识点 → 通过（knowledge:write 已授教师，建题需补知识点）
        p, _, _ = tea2b.post("/edu/knowledge", {
            "name": f"权限回归点{int(time.time()) % 100000}", "subject_id": 1,
            "grade_id": 1, "level": 2, "description": "教师建题补点用"})
        kd = data_of(p) or {}
        check("教师可创建知识点（knowledge:write 已授）",
              p.get("success") and bool(kd.get("id")),
              f"{p.get('code')} {p.get('message', '')}")
        if kd.get("id"):
            stu_c = Client("stu731")
            stu_c.login("stu731", ACCT["stu731"])
            expect_denied("学生删知识点被拒", stu_c, "DELETE",
                          f"/edu/knowledge/{kd['id']}")
            p, _, _ = admin.delete(f"/edu/knowledge/{kd['id']}")
            check("未引用知识点可删除", p.get("success"), p.get("message", ""))
        # admin 删有学生的班级 → 400 保护
        p, _, _ = admin.get("/edu/classes")
        cls = rows_of(p)
        if cls:
            p, _, _ = admin.delete(f"/edu/classes/{cls[0]['id']}")
            check("★ 有学生的班级删除被拒（悬空保护）",
                  p.get("success") is False and "学生" in str(p.get("message", "")),
                  f"{p.get('code')} {p.get('message', '')}")

    # ---------------------------------------------------------- 3 用户与角色
    R.set_phase("阶段一 · 管理员视角 | 3. 用户与角色 RBAC")

    p, _, _ = admin.get("/system/users", params={"page_size": 100})
    users = rows_of(p)
    total = total_of(p)
    check("用户列表", p.get("success") and total >= 17, f"total={total}")
    roles_seen = {u.get("role_name") or u.get("identity") for u in users}
    roles_seen.discard(None)
    check("用户列表覆盖多角色", len(roles_seen) >= 3, f"{sorted(roles_seen)}")

    t1 = next((u for u in users if u["username"] == "teacher1"), None)
    s731 = next((u for u in users if u["username"] == "stu731"), None)
    check("teacher1 存在", t1 is not None,
          f"id={t1 and t1['id']} class_id={t1 and t1.get('class_id')}")
    check("stu731 存在", s731 is not None,
          f"id={s731 and s731['id']} class_id={s731 and s731.get('class_id')}")
    R.context["teacher1_id"] = t1 and t1["id"]
    R.context["stu731_id"] = s731 and s731["id"]
    R.context["class_teacher1"] = t1 and t1.get("class_id")
    R.context["class_stu731"] = s731 and s731.get("class_id")

    if t1 and s731 and t1.get("class_id") != s731.get("class_id"):
        # 这是数据权限设计的正确表现（教师只能管自己班），不是缺陷。
        # 已在 docs/QUICKSTART.md 中把体验路线更正为 teacher4 → stu731。
        print(f"  \033[90m[INFO]\033[0m 任课班级隔离正常：teacher1=班级"
              f"{t1.get('class_id')}，stu731=班级{s731.get('class_id')}（teacher4 任教）；"
              "体验路线已在 QUICKSTART.md 更正")

    p, _, _ = admin.get("/system/roles")
    roles = rows_of(p)
    check("角色列表", p.get("success") and len(roles) >= 4, f"{len(roles)} 个角色")

    if roles:
        p, _, _ = admin.get("/system/permissions", params={"role_id": roles[0]["id"]})
        check("可查询指定角色的权限点", p.get("success") and data_of(p) is not None,
              f"role_id={roles[0]['id']} name={roles[0].get('name')}")

        # 用时间戳避免重名（上一轮遗留的副本会让本次复制失败）
        p, _, _ = admin.post(f"/system/roles/{roles[0]['id']}/copy",
                             {"name": f"E2E测试角色副本{int(time.time())}"})
        d = data_of(p) or {}
        new_rid = d.get("id")
        check("角色复制", p.get("success") and bool(new_rid), f"新角色 id={new_rid}")
        if new_rid:
            p, _, _ = admin.delete(f"/system/roles/{new_rid}")
            check("角色删除（测试数据清理）", p.get("success"), p.get("message", ""))

    # 越权矩阵
    stu = Client("stu731")
    ok, detail = stu.login("stu731", ACCT["stu731"])
    check("stu731 登录成功", ok, detail)
    if ok:
        expect_denied("学生访问用户管理接口被拒绝", stu, "GET", "/system/users")
        expect_denied("学生访问系统配置接口被拒绝", stu, "GET", "/system/config")
        expect_denied("学生访问题库管理接口被拒绝", stu, "GET", "/question/questions")

    tea = Client("teacher1")
    ok, detail = tea.login("teacher1", ACCT["teacher1"])
    check("teacher1 登录成功", ok, detail)
    if ok:
        expect_denied("教师访问用户管理接口被拒绝", tea, "GET", "/system/users")
        expect_denied("教师访问注册审批接口被拒绝", tea, "GET", "/auth/registrations")
        expect_denied("教师访问角色管理接口被拒绝", tea, "POST", "/system/roles",
                      body={"name": "越权角色", "code": "hack"})

    bad = Client("伪造")
    bad.token = admin.token[:-6] + "AAAAAA"
    expect_denied("篡改签名的 Token 被拒绝", bad, "GET", "/system/users")

    none_tok = Client("空token")
    expect_denied("空 Token 被拒绝", none_tok, "GET", "/system/users")

    wrong_scheme = Client("错误前缀")
    wrong_scheme.token = "Basic " + admin.token
    expect_denied("错误认证前缀被拒绝", wrong_scheme, "GET", "/system/users")

    # ---------------------------------------------------------- 4 注册审批
    R.set_phase("阶段一 · 管理员视角 | 4. 注册审批流")

    p, _, _ = admin.get("/auth/registrations")
    regs = rows_of(p)
    check("注册审批列表", p.get("success"), f"待审 {len(regs)} 条")

    uname = f"e2e_reg_{int(time.time())}"
    p, _, _ = anon.post("/auth/register", {
        "username": uname, "password": "E2e@Test123", "real_name": "自动化注册用户",
        "identity": "student", "class_id": R.context.get("class_stu731") or 1,
        "grade_id": 7, "email": f"{uname}@test.local",
    })
    check("匿名提交注册申请", p.get("success"), p.get("message", ""))

    p, _, _ = admin.get("/auth/registrations")
    regs2 = rows_of(p)
    target = next((r for r in regs2 if r.get("username") == uname), None)
    check("新注册进入待审批队列", target is not None, f"username={uname}")

    if target:
        p, _, _ = admin.post("/auth/registrations/audit", {
            "registration_id": target["id"], "approved": True, "reason": "E2E 通过",
        })
        check("审批通过", p.get("success"), p.get("message", ""))
        newc = Client("newuser")
        ok, detail = newc.login(uname, "E2e@Test123")
        check("审批后新账号可登录", ok, detail)
        if ok and newc.user:
            p, _, _ = admin.delete(f"/system/users/{newc.user['id']}")
            check("测试账号清理", p.get("success"), p.get("message", ""))
    else:
        R.issue("中", "注册申请未进入待审批队列",
                "POST /auth/register 返回成功，但管理员审批列表里查不到该用户名，"
                "可能注册流程未落库或列表过滤异常。", "POST /api/v1/auth/register")

    # 未审批账号不可登录
    uname2 = f"e2e_pend_{int(time.time())}"
    p, _, _ = anon.post("/auth/register", {
        "username": uname2, "password": "E2e@Test123", "real_name": "待审用户",
        "identity": "student", "class_id": R.context.get("class_stu731") or 1,
        "grade_id": 7, "email": f"{uname2}@test.local",
    })
    pend = Client("pending")
    ok2, detail2 = pend.login(uname2, "E2e@Test123")
    check("未审批账号无法登录", not ok2 and not pend.unreachable, detail2)

    # ---------------------------------------------------------- 5 日志审计
    R.set_phase("阶段一 · 管理员视角 | 5. 日志审计")

    for path, name in [("/logs/login", "登录日志"), ("/logs/operation", "操作日志"),
                       ("/logs/error", "错误日志")]:
        p, _, _ = admin.get(path, params={"page_size": 20})
        d = data_of(p) or {}
        items = d.get("items", [])
        check(f"{name}可查询", p.get("success"), f"{d.get('total', len(items))} 条")

    p, _, _ = admin.get("/logs/login", params={"page_size": 50})
    li = rows_of(p)
    check("本次 admin 登录被记录进登录日志",
          any(x.get("username") == "admin" for x in li),
          f"最近记录={li[0].get('username') if li else '-'}"
          f" status={li[0].get('status') if li else '-'}")

    p, _, _ = admin.get("/logs/login", params={"status": "failed"})
    fl = rows_of(p)
    check("可按失败状态筛选登录日志", p.get("success"),
          f"失败记录 {len(fl)} 条（应含前面的错误密码尝试）")

    p, _, _ = admin.get("/logs/operation", params={"page_size": 20})
    oi = rows_of(p)
    check("操作日志记录写操作", len(oi) > 0,
          f"最近模块={oi[0].get('module') if oi else '-'} "
          f"动作={oi[0].get('action') if oi else '-'}")

    p, _, _ = admin.get("/logs/error", params={"page_size": 20})
    ei = rows_of(p)
    check("错误日志可查询", p.get("success"), f"{len(ei)} 条")

    # 只对最近 1 小时内的错误报问题，历史遗留（已修复）不算缺陷
    import datetime as _dt
    now = _dt.datetime.now()
    fresh = []
    for e in ei:
        raw = str(e.get("created_at") or "")
        try:
            ts = _dt.datetime.fromisoformat(raw)
        except ValueError:
            continue
        if (now - ts).total_seconds() <= 3600:
            fresh.append(e)
    check("本轮测试未产生新的系统错误", not fresh,
          f"最近 1 小时新增 {len(fresh)} 条" if fresh
          else f"历史遗留 {len(ei)} 条（均早于本次测试）")
    if fresh:
        R.issue("高", f"本轮测试产生 {len(fresh)} 条系统错误",
                "；".join(f"{e.get('path')} -> {str(e.get('message'))[:100]}"
                         for e in fresh[:3]),
                "GET /api/v1/logs/error")
    elif ei:
        print(f"  \033[90m[INFO]\033[0m 历史错误 {len(ei)} 条（修复前遗留）："
              f"{ei[0].get('path')} -> {str(ei[0].get('message'))[:60]}")

    # ---------------------------------------------------------- 6 定时任务
    R.set_phase("阶段一 · 管理员视角 | 6. 定时任务与执行记录")

    p, _, _ = admin.get("/jobs")
    jobs = rows_of(p)
    check("定时任务列表", p.get("success"), f"{len(jobs)} 个任务")

    p, _, _ = admin.get("/jobs/status")
    check("调度器状态可读", p.get("success"), str(data_of(p))[:140])

    if jobs:
        jid = jobs[0]["id"]
        p, _, _ = admin.get(f"/jobs/{jid}/executions")
        ex = data_of(p) or {}
        check("任务执行记录可查", p.get("success"),
              f"job={jobs[0].get('name')} 记录 {total_of(p)} 条")

        p, _, _ = admin.put(f"/jobs/{jid}/toggle")
        check("任务可停用/启用（PUT toggle）", p.get("success"), p.get("message", ""))
        if p.get("success"):
            st1 = (data_of(p) or {}).get("is_active")
            # toggle 是反向开关，恢复原状
            p2, _, _ = admin.put(f"/jobs/{jid}/toggle")
            st2 = (data_of(p2) or {}).get("is_active")
            check("任务状态可切换并恢复", p2.get("success") and st1 != st2,
                  f"{st1} -> {st2}")
    else:
        R.issue("中", "定时任务列表为空",
                "APScheduler 未播种任何任务或任务表为空，"
                "错题提醒、复习计划推送、统计汇总等自动化能力不会运行。",
                "GET /api/v1/jobs -> items=[]")

    # ---------------------------------------------------------- 7 附件与配置
    R.set_phase("阶段一 · 管理员视角 | 7. 附件、配置与通知")

    p, _, _ = admin.get("/attachments")
    atts = data_of(p) or {}
    check("附件列表", p.get("success"), f"{total_of(p)} 个附件")

    p, _, _ = admin.get("/system/config")
    cfg = data_of(p) or {}
    check("系统配置可读", p.get("success") and len(cfg) > 0,
          f"运行态 {len([k for k in cfg if k != 'editable'])} 项，"
          f"可编辑 {len(cfg.get('editable') or [])} 项")

    # 密钥类字段绝不能出现在响应里
    leaked = [k for k in cfg if any(x in k.lower() for x in
                                     ("secret", "password", "api_key", "token"))]
    check("系统配置已脱敏（无密钥泄露）", not leaked,
          f"疑似泄露字段={leaked}" if leaked else "无密钥字段")

    # 管理员可在线写配置（无需重启容器）
    import time as _t
    key = f"e2e_setting_{int(_t.time())}"
    p2, _, _ = admin.put("/system/config", {
        "key": key, "value": "42", "value_type": "int",
        "label": "E2E 测试参数", "category": "basic",
    })
    check("系统配置可在线修改", p2.get("success"),
          f"key={key} value={(data_of(p2) or {}).get('value')} {p2.get('message', '')}")

    p3, _, _ = admin.get("/system/config")
    ed = {c["key"]: c for c in ((data_of(p3) or {}).get("editable") or [])}
    check("新配置项出现在配置列表", key in ed,
          f"可编辑项 {len(ed)} 个，含新项={key in ed}")

    p4, _, _ = admin.put("/system/config", {"key": key, "value": "43",
                                           "value_type": "int"})
    check("配置项可二次修改", p4.get("success") and (data_of(p4) or {}).get("value") == "43",
          f"value={(data_of(p4) or {}).get('value')}")

    p5, _, _ = admin.delete(f"/system/config/{key}")
    check("配置项可删除（测试数据清理）", p5.get("success"), p5.get("message", ""))

    # 教师/学生不得改配置
    if tea.token:
        expect_denied("教师不能修改系统配置", tea, "PUT", "/system/config",
                      body={"key": "hacked", "value": "1"})

    p, _, _ = admin.get("/system/notifications")
    nf = data_of(p) or {}
    check("通知列表", p.get("success"), f"{total_of(p)} 条通知")

    p, _, _ = admin.get("/agent/status")
    ag = data_of(p) or {}
    check("Agent 状态可读", p.get("success"),
          f"LLM={ag.get('llm_enabled')} 降级={ag.get('fallback_enabled')}")

    p, _, _ = admin.get("/agent/list")
    ad = data_of(p) or {}
    al = ad.get("agents", []) if isinstance(ad, dict) else rows_of(p)
    check("Agent 列表（应 ≥7 个）", p.get("success") and len(al) >= 7,
          f"{len(al)} 个: {[a.get('name') for a in al]}")

    # ---------------------------------------------------------- 8 报表
    R.set_phase("阶段一 · 管理员视角 | 8. 管理员报表")

    for path, name in [("/report/admin/overview", "系统总览"),
                       ("/report/admin/grade-comparison", "年级对比"),
                       ("/report/admin/subject-comparison", "学科对比"),
                       ("/report/admin/system-runtime", "系统运行时")]:
        p, _, _ = admin.get(path)
        d = data_of(p)
        check(f"{name}报表", p.get("success") and d is not None,
              f"字段={list(d.keys())[:6] if isinstance(d, dict) else type(d).__name__}")

    p, _, _ = admin.get("/report/admin/overview")
    ov = data_of(p) or {}
    for k in ("user_count", "question_count", "task_count"):
        if k in ov and ov[k] in (0, 0.0, None):
            R.issue("低", f"管理员总览 {k} 为 0", f"overview 关键字段={ov}")

    for rt in ("admin_overview", "class_overview"):
        p, _, _ = admin.get("/report/export/excel", params={"report_type": rt})
        if rt == "admin_overview":
            check("报表 Excel 导出（admin_overview）", p.get("success"),
                  f"code={p.get('code')} {p.get('message', '')}")
        else:
            print(f"  [90m[INFO][0m class_overview 需 class_id，code={p.get('code')}")

    # ---------------------------------------------------------- 9 登出
    R.set_phase("阶段一 · 管理员视角 | 9. 登出后会话失效")
    p, _, _ = admin.post("/auth/logout", {})
    check("登出接口调用成功", p.get("success"), p.get("message", ""))
    p2, _, _ = admin.get("/system/users")
    still_valid = p2.get("success") is True
    check("登出后原 Token 立即失效", not still_valid,
          "仍可访问 —— 无状态 JWT 无法服务端吊销，需引入黑名单或短有效期+刷新令牌轮换"
          if still_valid else "已失效")
    if still_valid:
        R.issue("中", "登出后原 Token 仍然有效",
                "POST /auth/logout 返回成功，但原 access_token 仍能访问受保护接口。"
                "JWT 为无状态设计，缺少服务端吊销名单；"
                "用户点击「退出登录」后若 Token 泄露则仍可被冒用。",
                "POST /auth/logout -> 随后 GET /system/users 仍 success=true")

    return None
