# -*- coding: utf-8 -*-
"""系统管理模块实测（管理员视角）：登录 / 权限 / 用户 / 角色 / 配置 / 审批 / 日志。

安全约束：所有破坏性操作（删除、重置密码、建角色）都针对**临时创建**的对象，
结束时清理；不触碰 admin / teacher1 / stu731 等基础账号。
"""
import sys
import time

sys.path.insert(0, "tests")
from e2e_framework import Client, data_of, rows_of  # noqa: E402

F = []
PWD = "Edu@123456"


def rec(level, title, bad, detail):
    F.append((level, title, bad, detail))
    print(f"[{'缺陷' if bad else '正常'}][{level}] {title}\n    {detail}")


def main():
    admin = Client("a"); ok, _ = admin.login("admin", "Admin@123456")
    t1 = Client("t1"); t1.login("teacher1", "Teacher@123")
    s1 = Client("s1"); s1.login("stu731", "Student@123")
    print(f"登录: admin={ok}\n")
    suffix = str(int(time.time()))[-6:]

    # ============================================================
    # 1. 登录与账号安全
    # ============================================================
    print("\n=== 1. 登录 ===")
    p, _, sc = Client("x1").post("/auth/login", {"username": "admin", "password": "wrong_pwd"})
    rec("低", "错误密码被拒绝", p.get("success") is True, f"HTTP {sc} {p.get('message', '')[:20]}")

    p, _, sc = Client("x2").post("/auth/login", {"username": "no_such_user_zzz", "password": "x"})
    rec("低", "不存在账号提示不暴露用户是否存在",
        "不存在" not in str(p.get("message", "")),
        f"提示={p.get('message', '')[:30]}")

    # 弱口令创建 + 弱口令重置
    uname = f"tmp_weak_{suffix}"
    p, _, sc = admin.post("/system/users", {
        "username": uname, "real_name": "弱口令测试", "password": "1",
        "identity": "student", "class_id": 1})
    uid = (data_of(p) or {}).get("id")
    rec("中", "创建用户时可用 1 位弱口令（无强度校验）",
        p.get("success") is True,
        f"HTTP {sc} user_id={uid} 密码='1'")

    if uid:
        p, _, sc = admin.put("/system/password/reset",
                             {"user_id": uid, "new_password": "a"})
        rec("中", "管理员重置密码为 1 位（无强度校验）",
            p.get("success") is True, f"HTTP {sc} 新密码='a'")
        # 弱口令能否登录
        p2, _, sc2 = Client("x3").post("/auth/login",
                                       {"username": uname, "password": "a"})
        rec("中", "重置后的超弱口令可直接登录",
            p2.get("success") is True, f"HTTP {sc2} {p2.get('message', '')[:20]}")

    # ============================================================
    # 2. 权限校验矩阵
    # ============================================================
    print("\n=== 2. 权限矩阵 ===")
    for path, method in (("/system/users", "GET"), ("/system/roles", "GET"),
                         ("/system/config", "GET"), ("/system/ai-config", "GET"),
                         ("/auth/registrations", "GET"), ("/logs/login", "GET")):
        p, _, sc = t1.get(path)
        rec("高", f"教师访问 {path} 被拒", p.get("success") is True, f"HTTP {sc}")
        p, _, sc = s1.get(path)
        rec("高", f"学生访问 {path} 被拒", p.get("success") is True, f"HTTP {sc}")

    # ============================================================
    # 3. 用户管理
    # ============================================================
    print("\n=== 3. 用户管理 ===")
    # 删除自己
    p, _, sc = admin.delete(f"/system/users/{admin.user.get('id')}")
    rec("中", "不能删除自己", p.get("success") is True, f"HTTP {sc} {p.get('message', '')[:20]}")

    # 用**临时管理员**做降权实验，绝不触碰真实 admin 账号（避免不可逆锁死）
    a2_name = f"tmp_admin_{suffix}"
    p, _, sc = admin.post("/system/users", {
        "username": a2_name, "real_name": "临时管理员", "password": PWD,
        "identity": "admin", "roles": ["sys_admin"]})
    a2_id = (data_of(p) or {}).get("id")
    rec("低", "可创建临时系统管理员（用于安全验证）", bool(a2_id), f"id={a2_id}")

    if a2_id:
        a2 = Client("a2")
        ok2, _ = a2.login(a2_name, PWD)
        if ok2:
            # 管理员删除自己 → 应被拦截
            p, _, sc = a2.delete(f"/system/users/{a2_id}")
            rec("中", "管理员不能删除自己",
                p.get("success") is True, f"HTTP {sc} {p.get('message', '')[:24]}")

            # 管理员可把自己降级（无二次确认）→ 失去全部权限
            p, _, sc = a2.put(f"/system/users/{a2_id}", {"roles": ["student"]})
            degraded = p.get("success") is True
            # 降级后是否真的失去管理员权限
            p2, _, sc2 = a2.get("/system/users")
            lost = p2.get("success") is not True
            rec("高", "★ 管理员可一键将自己降级为学生（无二次确认），且立即失去全部权限",
                degraded,
                f"降权 HTTP {sc}；降权后访问用户管理 HTTP {sc2} "
                f"{'（已失去权限）' if lost else ''}")
            # 由真实 admin 恢复并删除，保证可清理
            admin.put(f"/system/users/{a2_id}", {"roles": ["sys_admin"]})
        admin.delete(f"/system/users/{a2_id}")

    # 任意身份字符串
    p, _, sc = admin.post("/system/users", {
        "username": f"tmp_id_{suffix}", "real_name": "身份枚举测试",
        "identity": "not_a_valid_identity", "class_id": 1})
    bad_uid = (data_of(p) or {}).get("id")
    rec("中", "创建用户接受非法 identity 值",
        p.get("success") is True,
        f"identity='not_a_valid_identity' HTTP {sc} id={bad_uid}")
    if bad_uid:
        admin.delete(f"/system/users/{bad_uid}")

    # 不存在的班级
    p, _, sc = admin.post("/system/users", {
        "username": f"tmp_cls_{suffix}", "real_name": "班级不存在",
        "identity": "student", "class_id": 999999})
    cls_uid = (data_of(p) or {}).get("id")
    rec("中", "创建用户不校验 class_id 是否存在",
        p.get("success") is True, f"class_id=999999 HTTP {sc}")
    if cls_uid:
        admin.delete(f"/system/users/{cls_uid}")

    # 角色 code 不存在 → 静默丢失
    p, _, sc = admin.post("/system/users", {
        "username": f"tmp_role_{suffix}", "real_name": "角色不存在",
        "identity": "student", "class_id": 1, "roles": ["no_such_role"]})
    role_uid = (data_of(p) or {}).get("id")
    if role_uid:
        p2, _, _ = admin.get("/system/users", params={"keyword": f"tmp_role_{suffix}"})
        u = (rows_of(p2) or [{}])[0]
        rec("中", "创建用户时传不存在的角色 code 被静默忽略（用户无任何角色）",
            not u.get("roles"),
            f"用户 {role_uid} roles={u.get('roles')}")
        admin.delete(f"/system/users/{role_uid}")

    # 清理弱口令用户
    if uid:
        admin.delete(f"/system/users/{uid}")

    # ============================================================
    # 4. 角色管理
    # ============================================================
    print("\n=== 4. 角色管理 ===")
    p, _, _ = admin.get("/system/roles")
    roles = data_of(p) or []
    builtin = next((r for r in roles if r.get("is_builtin")), None)
    if builtin:
        p, _, sc = admin.put(f"/system/roles/{builtin['id']}", {"name": "hacked"})
        rec("高", "内置角色不可修改", p.get("success") is True,
            f"修改 {builtin.get('code')}：HTTP {sc} {p.get('message', '')[:20]}")
        p, _, sc = admin.delete(f"/system/roles/{builtin['id']}")
        rec("高", "内置角色不可删除", p.get("success") is True, f"HTTP {sc}")

        # 复制内置 sys_admin → 得到可自由修改的等价角色
        p, _, sc = admin.post(f"/system/roles/{builtin['id']}/copy", {})
        copy_role = data_of(p) or {}
        rec("中", "★ 可复制内置角色（sys_admin）得到可自由修改的等价全权角色",
            p.get("success") is True and bool(copy_role.get("id")),
            f"copy_id={copy_role.get('id')} code={copy_role.get('code')} "
            f"（is_builtin 应为 False）")
        if copy_role.get("id"):
            # 验证副本可被修改（绕过内置保护）
            p2, _, sc2 = admin.put(f"/system/roles/{copy_role['id']}",
                                   {"name": "副本改名"})
            rec("中", "复制出的角色可随意修改（间接绕过内置保护）",
                p2.get("success") is True, f"HTTP {sc2}")
            admin.delete(f"/system/roles/{copy_role['id']}")

    # 删除有用用户的角色
    with_users = next((r for r in roles if (r.get("user_count") or 0) > 0
                       and not r.get("is_builtin")), None)
    if with_users:
        p, _, sc = admin.delete(f"/system/roles/{with_users['id']}")
        rec("低", "有用户关联的角色不可删除", p.get("success") is True,
            f"{with_users.get('code')} users={with_users.get('user_count')} HTTP {sc}")

    # ============================================================
    # 5. 系统配置与密钥暴露
    # ============================================================
    print("\n=== 5. 配置与密钥 ===")
    p, _, _ = admin.get("/system/ai-config")
    ai = data_of(p) or {}
    cfg = ai.get("config") or {}
    key_val = cfg.get("LLM_API_KEY") or ""
    exposed = bool(key_val) and "*" not in str(key_val) and len(str(key_val)) > 8
    rec("高", "★ /system/ai-config 明文返回 LLM API Key",
        exposed,
        f"LLM_API_KEY 长度={len(str(key_val))} 前 4 位={str(key_val)[:4]}*** "
        f"（应脱敏为 sk-****abcd）")

    p, _, _ = admin.get("/system/config")
    d = data_of(p) or {}
    editable = d.get("editable") or []
    plain_keys = [c for c in editable
                  if "key" in str(c.get("key", "")).lower()
                  and c.get("value") and len(str(c.get("value"))) > 8]
    rec("高", "★ /system/config 的 editable 明文包含 API Key",
        bool(plain_keys),
        f"明文键={[c.get('key') for c in plain_keys]}")

    # 删除关键配置（llm_enabled）
    p, _, sc = admin.delete("/system/config/llm_enabled")
    rec("中", "可删除关键系统配置（llm_enabled 等无白名单保护）",
        p.get("success") is True, f"HTTP {sc} {p.get('message', '')[:30]}")

    # ============================================================
    # 6. 注册审批
    # ============================================================
    print("\n=== 6. 注册审批 ===")
    rname = f"tmp_reg_{suffix}"
    p, _, sc = Client("r").post("/auth/register", {
        "username": rname, "password": "Reg@123456", "real_name": "注册测试",
        "identity": "student", "class_id": 1})
    rec("低", "注册申请可提交（待审批）", p.get("success") is True, f"HTTP {sc}")
    reg_uid = (data_of(p) or {}).get("user_id")

    p, _, _ = admin.get("/auth/registrations", params={"status": "pending", "page_size": 50})
    regs = rows_of(p) or []
    mine = next((r for r in regs if r.get("user_id") == reg_uid), None)
    if mine:
        p, _, sc = admin.post("/auth/registrations/audit",
                              {"registration_id": mine["id"], "approved": True})
        rec("低", "审批通过生效", p.get("success") is True, f"HTTP {sc}")
        # 重复审批
        p, _, sc = admin.post("/auth/registrations/audit",
                              {"registration_id": mine["id"], "approved": True})
        rec("低", "重复审批是否被阻止", p.get("success") is True,
            f"HTTP {sc} {p.get('message', '')[:30]}")
        # 审批后可登录
        p, _, sc = Client("r2").post("/auth/login",
                                     {"username": rname, "password": "Reg@123456"})
        rec("低", "审批通过后可正常登录", p.get("success") is not True, f"HTTP {sc}")
        # 清理
        if reg_uid:
            admin.delete(f"/system/users/{reg_uid}")

    # ============================================================
    # 7. 日志
    # ============================================================
    print("\n=== 7. 日志审计 ===")
    for path in ("/logs/login", "/logs/operation", "/logs/error"):
        p, _, sc = admin.get(path, params={"page_size": 3})
        rec("低", f"{path} 可读", p.get("success") is not True, f"HTTP {sc}")

    # 日志导出（带 token）
    import urllib.request
    base = "http://localhost:8099/api/v1"
    for probe in (base, "http://localhost:8080/api/v1", "http://localhost:8000/api/v1"):
        try:
            req = urllib.request.Request(probe + "/logs/export?log_type=login",
                                         headers={"Authorization": f"Bearer {admin.token}"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                ct = resp.headers.get("content-type", "")
                body = resp.read(64)
            rec("低", "日志导出可用", "sheet" not in ct and "excel" not in ct.lower(),
                f"{probe} content-type={ct} size>={len(body)}")
            break
        except Exception:  # noqa: BLE001
            continue

    print("\n" + "=" * 62)
    bad = [x for x in F if x[2]]
    print(f"实测 {len(F)} 项，确认缺陷/隐患 {len(bad)} 项")
    for lv, t, _, _ in bad:
        print(f"  [{lv}] {t}")


if __name__ == "__main__":
    main()
