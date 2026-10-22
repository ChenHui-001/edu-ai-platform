# -*- coding: utf-8 -*-
"""系统管理模块实测 v2（断言语义统一：ok=True 表示符合预期）。

修正 v1 的问题：
- v1 用 bad 作为第三参数，多处传反导致「正常项」被计成缺陷
- 临时管理员因 must_change_password 被 403 拦截，降权实验未真正执行
"""
import sys
import time

sys.path.insert(0, "tests")
from e2e_framework import Client, data_of, rows_of  # noqa: E402

R = []          # [(level, title, ok, detail)]
PWD = "Sys@123456"


def chk(level, title, ok, detail=""):
    R.append((level, title, ok, detail))
    print(f"[{'OK ' if ok else 'BAD'}][{level}] {title} :: {detail}")


def main():
    admin = Client("a"); admin.login("admin", "Admin@123456")
    t1 = Client("t1"); t1.login("teacher1", "Teacher@123")
    s1 = Client("s1"); s1.login("stu731", "Student@123")
    suffix = str(int(time.time()))[-6:]
    print("admin/teacher/student 已登录\n")

    # ============ 1. 登录安全 ============
    print("== 1. 登录 ==")
    p, _, sc = Client("x1").post("/auth/login", {"username": "admin", "password": "bad"})
    chk("低", "错误密码被拒", p.get("success") is not True and sc in (400, 401),
        f"{sc} {p.get('message', '')[:20]}")

    p, _, sc = Client("x2").post("/auth/login", {"username": "zzz_nouser", "password": "x"})
    msg = str(p.get("message", ""))
    chk("低", "不存在账号的提示不暴露用户存在性",
        "不存在" not in msg and "或密码错误" in msg, f"{sc} {msg[:24]}")

    # 锁定策略：用临时账号连错 5 次
    uname = f"tmp_lock_{suffix}"
    p, _, _ = admin.post("/system/users", {
        "username": uname, "real_name": "锁定测试", "password": PWD,
        "identity": "student", "class_id": 1, "must_change_password": False})
    lock_uid = (data_of(p) or {}).get("id")
    locked = False
    for _ in range(6):
        p2, _, _ = Client("lk").post("/auth/login", {"username": uname, "password": "bad"})
        if "锁定" in str(p2.get("message", "")):
            locked = True
            break
    chk("中", "连续错误密码触发账号锁定", locked,
        "第 5~6 次出现锁定提示" if locked else "未触发锁定")

    # ============ 2. 权限矩阵 ============
    print("== 2. 权限矩阵 ==")
    for path in ("/system/users", "/system/roles", "/system/config",
                 "/system/ai-config", "/system/permissions",
                 "/auth/registrations", "/logs/login", "/logs/operation"):
        for label, cli in (("教师", t1), ("学生", s1)):
            p, _, sc = cli.get(path)
            chk("高", f"{label}访问 {path} 被拒",
                p.get("success") is not True and sc in (403, 401),
                f"{sc} {p.get('message', '')[:16]}")

    # 写接口越权
    for label, cli in (("教师", t1), ("学生", s1)):
        p, _, sc = cli.post("/system/users", {"username": f"x_{suffix}_{label}",
                                             "real_name": "x"})
        chk("高", f"{label}不能创建用户",
            p.get("success") is not True and sc in (403, 401), f"{sc}")

    # ============ 3. 用户管理 ============
    print("== 3. 用户管理 ==")
    # 自己删除自己
    p, _, sc = admin.delete(f"/system/users/{admin.user.get('id')}")
    chk("中", "管理员不能删除自己", p.get("success") is not True,
        f"{sc} {p.get('message', '')[:16]}")

    # 密码强度
    p, _, sc = admin.post("/system/users", {
        "username": f"tmp_weak_{suffix}", "real_name": "弱口令",
        "password": "1", "identity": "student", "class_id": 1})
    weak_uid = (data_of(p) or {}).get("id")
    chk("中", "创建用户时应拒绝 1 位弱口令",
        p.get("success") is not True,
        f"{sc} 实际创建成功 id={weak_uid}（无强度校验）" if weak_uid else f"{sc} 已拒绝")

    if weak_uid:
        p, _, sc = admin.put("/system/password/reset",
                             {"user_id": weak_uid, "new_password": "a"})
        can = p.get("success") is True
        chk("中", "管理员重置密码应校验强度",
            not can, f"设为 'a' {'成功（无校验）' if can else '被拒'}")
        p2, _, sc2 = Client("w").post("/auth/login",
                                      {"username": f"tmp_weak_{suffix}", "password": "a"})
        chk("中", "超弱口令应无法登录",
            p2.get("success") is not True, f"{sc2} 实际{'可登录' if p2.get('success') else '被拒'}")
        admin.delete(f"/system/users/{weak_uid}")

    # identity 枚举
    p, _, sc = admin.post("/system/users", {
        "username": f"tmp_id_{suffix}", "real_name": "非法身份",
        "identity": "not_valid", "class_id": 1})
    bad_id_uid = (data_of(p) or {}).get("id")
    chk("中", "identity 应限定为 student/teacher/admin",
        p.get("success") is not True,
        f"{sc} {'接受非法值' if bad_id_uid else '已拒绝'}")
    if bad_id_uid:
        admin.delete(f"/system/users/{bad_id_uid}")

    # class_id 存在性
    p, _, sc = admin.post("/system/users", {
        "username": f"tmp_cls_{suffix}", "real_name": "班级不存在",
        "identity": "student", "class_id": 999999})
    chk("中", "class_id 不存在应被拒", p.get("success") is not True,
        f"{sc} {p.get('message', '')[:20]}")

    # 角色 code 不存在
    p, _, sc = admin.post("/system/users", {
        "username": f"tmp_role_{suffix}", "real_name": "角色不存在",
        "identity": "student", "class_id": 1, "roles": ["no_such_role"]})
    r_uid = (data_of(p) or {}).get("id")
    if r_uid:
        p2, _, _ = admin.get("/system/users", params={"keyword": f"tmp_role_{suffix}"})
        u = (rows_of(p2) or [{}])[0]
        chk("中", "传不存在的角色 code 应报错而非静默忽略",
            bool(u.get("roles")), f"创建成功但 roles={u.get('roles')}（无任何角色）")
        admin.delete(f"/system/users/{r_uid}")

    # 管理员自我降权（用临时管理员，先完成强制改密）
    a2 = f"tmp_admin_{suffix}"
    p, _, _ = admin.post("/system/users", {
        "username": a2, "real_name": "临时管理员", "password": PWD,
        "identity": "admin", "roles": ["sys_admin"], "must_change_password": False})
    a2_id = (data_of(p) or {}).get("id")
    if a2_id:
        c2 = Client("a2"); ok2, _ = c2.login(a2, PWD)
        chk("低", "临时管理员可登录（前置）", ok2, f"id={a2_id}")
        if ok2:
            p, _, sc = c2.put(f"/system/users/{a2_id}", {"roles": ["student"]})
            degraded = p.get("success") is True
            p2, _, sc2 = c2.get("/system/users")
            lost = p2.get("success") is not True
            chk("高", "管理员自我降权应有保护（二次确认/禁止降最后一个管理员）",
                not degraded,
                f"降权{'成功' if degraded else '被拒'}；之后访问用户管理 {sc2}"
                f"{'（已失去权限）' if lost else ''}")
            admin.put(f"/system/users/{a2_id}", {"roles": ["sys_admin"]})
        admin.delete(f"/system/users/{a2_id}")

    # ============ 4. 角色管理 ============
    print("== 4. 角色管理 ==")
    p, _, _ = admin.get("/system/roles")
    roles = data_of(p) or []
    admin_role = next((r for r in roles if r.get("code") == "sys_admin"), None)
    if admin_role:
        p, _, sc = admin.put(f"/system/roles/{admin_role['id']}", {"name": "h"})
        chk("高", "内置角色不可修改", p.get("success") is not True, f"{sc}")
        p, _, sc = admin.delete(f"/system/roles/{admin_role['id']}")
        chk("高", "内置角色不可删除", p.get("success") is not True, f"{sc}")

        # 复制内置角色（间接绕过保护）
        p, _, sc = admin.post(f"/system/roles/{admin_role['id']}/copy", {})
        cp = data_of(p) or {}
        chk("中", "复制 sys_admin 得到的角色应受同等保护或禁止",
            p.get("success") is not True,
            f"复制{'成功' if cp.get('id') else '被拒'} code={cp.get('code')} "
            f"perms={len(cp.get('permissions') or [])} 个")
        if cp.get("id"):
            p2, _, _ = admin.put(f"/system/roles/{cp['id']}", {"name": "副本改名"})
            chk("中", "复制出的角色可被修改（内置保护被间接绕过）",
                p2.get("success") is not True, "修改成功（等价于全权角色可定制）")
            admin.delete(f"/system/roles/{cp['id']}")

    # ============ 5. 配置与密钥 ============
    print("== 5. 配置与密钥 ==")
    p, _, _ = admin.get("/system/ai-config")
    cfg = (data_of(p) or {}).get("config") or {}
    keyv = str(cfg.get("LLM_API_KEY") or "")
    chk("高", "ai-config 的 API Key 应脱敏返回",
        not keyv or "*" in keyv,
        f"明文长度={len(keyv)} 前缀={keyv[:4]}***")

    p, _, _ = admin.get("/system/config")
    editable = (data_of(p) or {}).get("editable") or []
    leaked = [c.get("key") for c in editable
              if "key" in str(c.get("key", "")).lower()
              and c.get("value") and len(str(c.get("value"))) > 8]
    chk("高", "config 的 editable 不应明文暴露密钥",
        not leaked, f"明文键={leaked}")

    # 删除配置（用存在的 key）
    p, _, _ = admin.get("/system/config")
    keys = [c.get("key") for c in ((data_of(p) or {}).get("editable") or [])]
    crit = next((k for k in keys if k in ("llm_enabled", "llm_api_key", "llm_provider")), None)
    if crit:
        p, _, sc = admin.delete(f"/system/config/{crit}")
        ok_del = p.get("success") is True
        chk("中", "关键配置应禁止删除（否则可绕过审计重置系统行为）",
            not ok_del, f"删除 {crit} {'成功' if ok_del else '被拒'}")
    else:
        chk("低", "配置表无关键项可测（跳过删除测试）", True, f"keys={keys[:5]}")

    # ============ 6. 注册审批 ============
    print("== 6. 注册审批 ==")
    rname = f"tmp_reg_{suffix}"
    p, _, sc = Client("r").post("/auth/register", {
        "username": rname, "password": "Reg@123456", "real_name": "注册测试",
        "identity": "student", "class_id": 1})
    reg_uid = (data_of(p) or {}).get("user_id")
    chk("低", "注册申请可提交", p.get("success") is True, f"{sc}")

    # 审批前不能登录
    p, _, sc = Client("r1").post("/auth/login", {"username": rname, "password": "Reg@123456"})
    chk("中", "待审批账号不能登录", p.get("success") is not True,
        f"{sc} {p.get('message', '')[:24]}")

    p, _, _ = admin.get("/auth/registrations", params={"status": "pending", "page_size": 100})
    mine = next((r for r in (rows_of(p) or []) if r.get("user_id") == reg_uid), None)
    if mine:
        p, _, sc = admin.post("/auth/registrations/audit",
                              {"registration_id": mine["id"], "approved": True})
        chk("低", "审批通过生效", p.get("success") is True, f"{sc}")
        p, _, sc = admin.post("/auth/registrations/audit",
                              {"registration_id": mine["id"], "approved": True})
        chk("中", "重复审批应被拒", p.get("success") is not True,
            f"{sc} {p.get('message', '')[:20]}")
        p, _, sc = Client("r3").post("/auth/login", {"username": rname, "password": "Reg@123456"})
        chk("中", "审批通过后可登录", p.get("success") is True, f"{sc}")
        if reg_uid:
            admin.delete(f"/system/users/{reg_uid}")
    if lock_uid:
        admin.delete(f"/system/users/{lock_uid}")

    # ============ 7. 日志 ============
    print("== 7. 日志 ==")
    for path in ("/logs/login", "/logs/operation", "/logs/error"):
        p, _, sc = admin.get(path, params={"page_size": 3})
        chk("低", f"{path} 可读", p.get("success") is True, f"{sc}")

    print("\n" + "=" * 64)
    bad = [x for x in R if not x[2]]
    print(f"实测 {len(R)} 项：符合预期 {len(R) - len(bad)}，存在缺陷 {len(bad)}")
    for lv, t, _, d in bad:
        print(f"  [{lv}] {t}  << {d}")


if __name__ == "__main__":
    main()
