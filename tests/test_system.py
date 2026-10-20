# -*- coding: utf-8 -*-
"""系统管理模块专项测试（阶段十五）：登录安全 / 权限矩阵 / 用户与角色 / 配置密钥。"""
import sys
import time

sys.path.insert(0, "tests")
from e2e_framework import R, Client, check, data_of, rows_of  # noqa: E402

PWD = "Sys@2026Test"


def run():
    admin = Client("a"); admin.login("admin", "Admin@123456")
    t1 = Client("t1"); t1.login("teacher1", "Teacher@123")
    s1 = Client("s1"); s1.login("stu731", "Student@123")
    sfx = str(int(time.time()))[-6:]
    check("管理员/教师/学生登录", bool(admin.token and t1.token and s1.token), "")

    # ============================================================
    # 1. 登录安全
    # ============================================================
    R.set_phase("系统管理 | 1. 登录安全")

    p, _, sc = Client("x1").post("/auth/login", {"username": "admin", "password": "bad"})
    check("错误密码被拒", p.get("success") is not True and sc in (400, 401),
          f"{sc} {p.get('message', '')[:20]}")

    p, _, _ = Client("x2").post("/auth/login", {"username": "no_user_zz", "password": "x"})
    msg = str(p.get("message", ""))
    check("不存在账号不暴露用户存在性",
          "不存在" not in msg, f"提示={msg[:24]}")

    # 锁定策略
    lu = f"tmp_lock_{sfx}"
    p, _, _ = admin.post("/system/users", {
        "username": lu, "real_name": "锁定测试", "password": PWD,
        "identity": "student", "class_id": 1, "must_change_password": False})
    locked = False
    for _ in range(6):
        p2, _, _ = Client("lk").post("/auth/login", {"username": lu, "password": "bad"})
        if "锁定" in str(p2.get("message", "")):
            locked = True
            break
    check("★ 连续错误触发账号锁定", locked,
          "第 5 次后提示账号已锁定" if locked else "未触发")

    # ============================================================
    # 2. 权限矩阵
    # ============================================================
    R.set_phase("系统管理 | 2. 权限矩阵")

    for path in ("/system/users", "/system/roles", "/system/config",
                 "/system/ai-config", "/system/permissions",
                 "/auth/registrations", "/logs/login", "/logs/operation"):
        for label, cli in (("教师", t1), ("学生", s1)):
            p, _, sc = cli.get(path)
            check(f"★ {label}访问 {path} 被拒",
                  p.get("success") is not True and sc in (401, 403), f"{sc}")

    p, _, sc = t1.post("/system/users", {"username": f"x_{sfx}", "real_name": "x"})
    check("★ 教师不能创建用户", p.get("success") is not True and sc in (401, 403), f"{sc}")

    # ============================================================
    # 3. 密码策略（本次修复重点）
    # ============================================================
    R.set_phase("系统管理 | 3. 密码强度策略")

    for bad_pwd, why in (("1", "1 位"), ("12345678", "纯数字"), ("abcdefgh", "纯字母"),
                         ("admin123", "常见弱口令")):
        p, _, sc = admin.post("/system/users", {
            "username": f"tmp_pw_{sfx}_{abs(hash(bad_pwd)) % 1000}",
            "real_name": "弱口令", "password": bad_pwd,
            "identity": "student", "class_id": 1})
        check(f"★ 创建用户拒绝弱口令（{why}）",
              p.get("success") is not True,
              f"{sc} {p.get('message', '')[:24]}")

    # 合规密码可创建
    good_name = f"tmp_ok_{sfx}"
    p, _, _ = admin.post("/system/users", {
        "username": good_name, "real_name": "合规密码", "password": PWD,
        "identity": "student", "class_id": 1, "must_change_password": False})
    good_uid = (data_of(p) or {}).get("id")
    check("合规密码可创建用户", p.get("success") is True, f"id={good_uid}")

    if good_uid:
        p, _, sc = admin.put("/system/password/reset",
                             {"user_id": good_uid, "new_password": "a"})
        check("★ 重置密码拒绝弱口令", p.get("success") is not True,
              f"{sc} {p.get('message', '')[:24]}")

        p, _, sc = admin.put("/system/password/reset",
                             {"user_id": good_uid, "new_password": "Reset@2026"})
        check("★ 重置密码使用 new_password 字段可成功",
              p.get("success") is True, f"{sc} {p.get('message', '')[:24]}")
        p, _, sc = Client("g").post("/auth/login",
                                    {"username": good_name, "password": "Reset@2026"})
        check("重置后可登录（并强制改密）", p.get("success") is True, f"{sc}")

    # ============================================================
    # 4. 用户管理校验
    # ============================================================
    R.set_phase("系统管理 | 4. 用户管理校验")

    p, _, _ = admin.post("/system/users", {
        "username": f"tmp_id_{sfx}", "real_name": "非法身份",
        "identity": "not_valid", "class_id": 1})
    check("★ identity 限定 student/teacher/admin",
          p.get("success") is not True, str(p.get("message"))[:30])

    p, _, _ = admin.post("/system/users", {
        "username": f"tmp_role_{sfx}", "real_name": "角色不存在",
        "identity": "student", "class_id": 1, "roles": ["no_such_role"]})
    check("★ 不存在的角色 code 被拒（不再静默忽略）",
          p.get("success") is not True, str(p.get("message"))[:30])

    p, _, _ = admin.post("/system/users", {
        "username": f"tmp_cls_{sfx}", "real_name": "班级不存在",
        "identity": "student", "class_id": 999999})
    check("不存在的 class_id 被拒", p.get("success") is not True, str(p.get("message"))[:24])

    p, _, _ = admin.delete(f"/system/users/{admin.user.get('id')}")
    check("管理员不能删除自己", p.get("success") is not True, str(p.get("message"))[:16])

    # 自我降权保护
    a2 = f"tmp_adm_{sfx}"
    p, _, _ = admin.post("/system/users", {
        "username": a2, "real_name": "临时管理员", "password": PWD,
        "identity": "admin", "roles": ["sys_admin"], "must_change_password": False})
    a2_id = (data_of(p) or {}).get("id")
    if a2_id:
        c2 = Client("a2"); ok2, _ = c2.login(a2, PWD)
        if ok2:
            p, _, sc = c2.put(f"/system/users/{a2_id}", {"roles": ["student"]})
            check("★ 管理员不能移除自己的系统管理员角色",
                  p.get("success") is not True, f"{sc} {p.get('message', '')[:30]}")
            # 降级他人仍允许
            p, _, _ = c2.put(f"/system/users/{good_uid}", {"roles": ["student"]}) if good_uid else (None, None, None)
            check("管理员可调整他人角色（对照项）",
                  p is None or p.get("success") is True, "")
        admin.delete(f"/system/users/{a2_id}")
    if good_uid:
        admin.delete(f"/system/users/{good_uid}")
    if lu:
        admin.delete(f"/system/users/{lu}")

    # ============================================================
    # 5. 角色管理
    # ============================================================
    R.set_phase("系统管理 | 5. 角色保护")

    p, _, _ = admin.get("/system/roles")
    roles = data_of(p) or []
    builtin = next((r for r in roles if r.get("code") == "sys_admin"), None)
    if builtin:
        p, _, sc = admin.put(f"/system/roles/{builtin['id']}", {"name": "h"})
        check("内置角色不可修改", p.get("success") is not True, f"{sc}")
        p, _, sc = admin.delete(f"/system/roles/{builtin['id']}")
        check("内置角色不可删除", p.get("success") is not True, f"{sc}")
        p, _, sc = admin.post(f"/system/roles/{builtin['id']}/copy", {})
        check("★ 内置角色不可复制（防间接绕过保护）",
              p.get("success") is not True, f"{sc} {p.get('message', '')[:30]}")

    # 自定义角色可复制且返回真实权限
    p, _, _ = admin.post("/system/roles", {
        "code": f"tmp_role_{sfx}", "name": f"临时角色{sfx}",
        "permissions": ["student:practice", "student:exam"]})
    rid = (data_of(p) or {}).get("id")
    if rid:
        p, _, _ = admin.post(f"/system/roles/{rid}/copy", {})
        cp = data_of(p) or {}
        check("★ 复制自定义角色返回真实权限数（此前误报 0）",
              bool(cp.get("id")) and len(cp.get("permissions") or []) == 2,
              f"copy_id={cp.get('id')} perms={len(cp.get('permissions') or [])}")
        if cp.get("id"):
            admin.delete(f"/system/roles/{cp['id']}")
        p, _, _ = admin.delete(f"/system/roles/{rid}")
        check("自定义角色可删除", p.get("success") is True, "")

    # ============================================================
    # 6. 密钥脱敏与配置保护
    # ============================================================
    R.set_phase("系统管理 | 6. 密钥脱敏与配置保护")

    # 先写入一段已知假密钥，再回读断言掩码形态。
    # 原断言 `not keyv or "*" in keyv` 在「未配置密钥」时平凡通过：干净测试库里
    # LLM_API_KEY 为空，用例看着在测脱敏，实际什么都没测（典型的空入参假阳性）。
    FAKE_KEY = "sk-verify-ABCDEFGH-0001"
    admin.put("/system/ai-config", {"llm_api_key": FAKE_KEY})
    p, _, _ = admin.get("/system/ai-config")
    cfg = (data_of(p) or {}).get("config") or {}
    keyv = str(cfg.get("LLM_API_KEY") or "")
    check("★ ai-config 的 API Key 已脱敏",
          bool(keyv) and "****" in keyv and FAKE_KEY not in keyv,
          f"写入={FAKE_KEY} 回读={keyv!r}")
    check("脱敏仍能判断是否已配置",
          ((data_of(p) or {}).get("meta") or {}).get("llm_api_key", {}).get("has_db_value") is True,
          "meta.has_db_value=True")
    # 掩码回传视为「未修改」，不得覆盖真实密钥
    admin.put("/system/ai-config", {"llm_api_key": keyv})
    p2, _, _ = admin.get("/system/ai-config")
    keyv2 = str(((data_of(p2) or {}).get("config") or {}).get("LLM_API_KEY") or "")
    check("回传掩码值不会污染真实密钥", keyv2 == keyv, f"前后一致={keyv2 == keyv}")

    # config 侧：写入已知密钥值后确认脱敏
    admin.put("/system/config", {"key": "smtp_password", "value": "smtp-Pass-XYZ8888",
                                 "category": "mail", "label": "SMTP 密码"})
    p, _, _ = admin.get("/system/config")
    editable = (data_of(p) or {}).get("editable") or []
    leaked = [c.get("key") for c in editable
              if "key" in str(c.get("key", "")).lower()
              and c.get("value") and "*" not in str(c.get("value"))]
    probe = next((c for c in editable if c.get("key") == "smtp_password"), None)
    check("★ config 的 editable 不含明文密钥", not leaked, f"明文键={leaked}")
    check("★ editable 密钥字段为掩码形态",
          probe is not None and "****" in str((probe or {}).get("value")),
          f"smtp_password={(probe or {}).get('value')!r}")

    # 关键配置不可删：必须先建出该行，否则 404「配置项不存在」同样满足
    # `success is not True`，用例会假通过（原写法即有此问题）。
    admin.put("/system/config", {"key": "llm_provider", "value": "deepseek",
                                 "category": "ai", "label": "提供商"})
    p, _, sc = admin.delete("/system/config/llm_provider")
    check("★ 关键配置（llm_*）不可删除",
          p.get("success") is not True and "关键配置" in str(p.get("message") or ""),
          f"{sc} {p.get('message', '')[:40]}")
    p, _, sc = admin.delete("/system/config/smtp_password")
    check("★ 关键配置（smtp_*）不可删除",
          p.get("success") is not True and "关键配置" in str(p.get("message") or ""),
          f"{sc} {p.get('message', '')[:40]}")

    # 还原：清空假密钥，避免影响后续阶段
    admin.put("/system/ai-config", {"llm_api_key": ""})

    # 非关键配置可正常增删
    p, _, _ = admin.put("/system/config", {"key": f"tmp_cfg_{sfx}", "value": "1",
                                           "category": "basic"})
    check("非关键配置可写入", p.get("success") is True, "")
    p, _, _ = admin.delete(f"/system/config/tmp_cfg_{sfx}")
    check("非关键配置可删除", p.get("success") is True, "")

    # ============================================================
    # 7. 注册审批
    # ============================================================
    R.set_phase("系统管理 | 7. 注册与审批")

    rname = f"tmp_reg_{sfx}"
    p, _, _ = Client("r").post("/auth/register", {
        "username": rname, "password": "Reg@2026Test", "real_name": "注册测试",
        "identity": "student", "class_id": 1})
    reg_uid = (data_of(p) or {}).get("user_id")
    check("注册申请可提交", p.get("success") is True, "")

    p, _, _ = Client("r1").post("/auth/login",
                                {"username": rname, "password": "Reg@2026Test"})
    check("★ 待审批账号不能登录", p.get("success") is not True,
          str(p.get("message"))[:24])

    # 注册弱口令被拒
    p, _, _ = Client("r0").post("/auth/register", {
        "username": f"tmp_regw_{sfx}", "password": "123456",
        "real_name": "弱口令", "identity": "student", "class_id": 1})
    check("★ 注册拒绝弱口令", p.get("success") is not True, str(p.get("message"))[:24])

    p, _, _ = admin.get("/auth/registrations",
                        params={"status": "pending", "page_size": 100})
    mine = next((r for r in (rows_of(p) or []) if r.get("user_id") == reg_uid), None)
    if mine:
        p, _, _ = admin.post("/auth/registrations/audit",
                             {"registration_id": mine["id"], "approved": True})
        check("审批通过生效", p.get("success") is True, "")
        p, _, _ = admin.post("/auth/registrations/audit",
                             {"registration_id": mine["id"], "approved": True})
        check("重复审批被拒", p.get("success") is not True, str(p.get("message"))[:20])
        p, _, _ = Client("r3").post("/auth/login",
                                    {"username": rname, "password": "Reg@2026Test"})
        check("审批通过后可登录", p.get("success") is True, "")
        if reg_uid:
            admin.delete(f"/system/users/{reg_uid}")

    # ============================================================
    # 8. 日志
    # ============================================================
    R.set_phase("系统管理 | 8. 日志审计")

    for path in ("/logs/login", "/logs/operation", "/logs/error"):
        p, _, sc = admin.get(path, params={"page_size": 3})
        check(f"{path} 可读", p.get("success") is True, f"{sc}")

    R.env("系统管理", f"登录/权限/密码策略/用户角色/密钥脱敏/审批 验证完成")
    print("\n[完成] 系统管理模块专项")


if __name__ == "__main__":
    run()
