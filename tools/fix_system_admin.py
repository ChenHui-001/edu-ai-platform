# -*- coding: utf-8 -*-
"""系统管理模块缺陷修复（11 项）。

高：密钥明文返回 / 管理员自我降权无保护
中：密码强度缺失 / identity 无枚举 / role code 静默忽略 / 复制内置角色绕过保护 / 关键配置可删
"""
import io

# ============================================================
# 1) 密码强度校验工具（新增）
# ============================================================
f = "backend/app/core/security.py"
s = io.open(f, encoding="utf-8").read()
if "def validate_password_strength" not in s:
    s = s.rstrip() + '''


# 常见弱口令（命中即拒绝，避免 P@ssw0rd 这类"看起来合规"的密码）
_WEAK_PASSWORDS = {
    "12345678", "123456789", "password", "passw0rd", "qwerty123", "abc12345",
    "admin123", "admin@123", "a1234567", "11111111", "88888888", "edu@123456",
}


def validate_password_strength(password: str, *, min_length: int = 8) -> None:
    """密码强度校验：长度 + 字母数字组合 + 弱口令黑名单。

    此前仅 change_password 校验长度，创建用户/管理员重置密码完全不校验，
    实测可把密码设为 "1" 并直接登录。
    """
    from app.core.exception import BusinessException

    pwd = password or ""
    if len(pwd) < min_length:
        raise BusinessException(f"密码长度不能少于 {min_length} 位")
    if len(pwd) > 64:
        raise BusinessException("密码长度不能超过 64 位")
    if pwd.lower() in _WEAK_PASSWORDS:
        raise BusinessException("密码过于简单（常见弱口令），请更换")
    has_alpha = any(c.isalpha() for c in pwd)
    has_digit = any(c.isdigit() for c in pwd)
    if not (has_alpha and has_digit):
        raise BusinessException("密码需同时包含字母和数字")
'''
    io.open(f, "w", encoding="utf-8", newline="\n").write(s)
    print("[1] validate_password_strength 已添加")

# ============================================================
# 2) system.py：密码强度 / identity 白名单 / role 校验 / 自我降权保护
# ============================================================
f2 = "backend/app/api/v1/system.py"
s2 = io.open(f2, encoding="utf-8").read()

# ---- create_user ----
OLD = '''    from app.core.security import hash_password

    if not data.get("username") or not data.get("real_name"):
        raise BusinessException("账号和姓名不能为空")
    if db.scalar(select(User).where(User.username == data["username"])):
        raise BusinessException("该账号已存在")

    user = User(
        username=data["username"],
        password=hash_password(data.get("password", "Edu@123456")),'''
NEW = '''    from app.core.security import hash_password, validate_password_strength
    from app.core.config import settings as _st

    if not data.get("username") or not data.get("real_name"):
        raise BusinessException("账号和姓名不能为空")
    if db.scalar(select(User).where(User.username == data["username"])):
        raise BusinessException("该账号已存在")

    # 身份白名单：此前接受任意字符串，会写出 identity='xxx' 的脏用户
    identity = data.get("identity") or "student"
    if identity not in ("student", "teacher", "admin"):
        raise BusinessException("身份仅支持 student / teacher / admin")

    raw_pwd = data.get("password") or _st.DEFAULT_USER_PASSWORD
    validate_password_strength(raw_pwd, min_length=_st.PASSWORD_MIN_LENGTH)

    # 角色编码必须真实存在：此前静默跳过，用户最终无任何角色、登录后空权限
    role_codes = data.get("roles") or ["student"]
    roles_db = db.scalars(select(Role).where(Role.code.in_(role_codes))).all()
    missing = set(role_codes) - {r.code for r in roles_db}
    if missing:
        raise BusinessException(f"以下角色不存在：{', '.join(sorted(missing))}")

    user = User(
        username=data["username"],
        password=hash_password(raw_pwd),'''
assert OLD in s2, "create_user head"
s2 = s2.replace(OLD, NEW)

s2 = s2.replace('''        identity=data.get("identity", "student"),
        status=data.get("status", "active"),''',
'''        identity=identity,
        status=data.get("status", "active"),''')

# 角色绑定改用已校验的 list
s2 = s2.replace('''    db.add(user)
    db.flush()
    for code in data.get("roles", ["student"]):
        role = db.scalar(select(Role).where(Role.code == code))
        if role:
            db.add(UserRole(user_id=user.id, role_id=role.id))''',
'''    db.add(user)
    db.flush()
    for role in roles_db:
        db.add(UserRole(user_id=user.id, role_id=role.id))''')

# ---- update_user：身份枚举 + 角色校验 + 自我降权保护 ----
OLD2 = '''def update_user(
    user_id: int, data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db), _: User = Depends(get_current_admin),
):
    user = db.get(User, user_id)
    if not user:
        raise NotFoundException("用户不存在")
    for f in ("real_name", "email", "phone", "status", "school_name", "grade_id",
              "class_id", "avatar", "identity"):
        if f in data:
            setattr(user, f, data[f])
    if "roles" in data:
        db.execute(UserRole.__table__.delete().where(UserRole.user_id == user_id))
        for code in data["roles"]:
            role = db.scalar(select(Role).where(Role.code == code))
            if role:
                db.add(UserRole(user_id=user_id, role_id=role.id))
    db.commit()
    return ok(dictify(user), message="用户信息已更新")'''
NEW2 = '''def update_user(
    user_id: int, data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db), admin: User = Depends(get_current_admin),
):
    user = db.get(User, user_id)
    if not user:
        raise NotFoundException("用户不存在")

    if "identity" in data and data["identity"] not in ("student", "teacher", "admin"):
        raise BusinessException("身份仅支持 student / teacher / admin")

    # 自我降权保护：移除自己的 sys_admin 会立即失去全部管理权限，
    # 且无法自助恢复（实测降权后所有管理接口立即 403）。
    if user_id == admin.id and "roles" in data:
        if "sys_admin" not in set(data["roles"] or []):
            raise BusinessException(
                "不能移除自己的系统管理员角色（如需移交，请由另一位管理员操作）")

    # 角色编码存在性校验
    roles_db = []
    if "roles" in data:
        codes = list(dict.fromkeys(data["roles"] or []))
        roles_db = db.scalars(select(Role).where(Role.code.in_(codes))).all()
        missing = set(codes) - {r.code for r in roles_db}
        if missing:
            raise BusinessException(f"以下角色不存在：{', '.join(sorted(missing))}")

    for f in ("real_name", "email", "phone", "status", "school_name", "grade_id",
              "class_id", "avatar", "identity"):
        if f in data:
            setattr(user, f, data[f])
    if "roles" in data:
        db.execute(UserRole.__table__.delete().where(UserRole.user_id == user_id))
        for role in roles_db:
            db.add(UserRole(user_id=user_id, role_id=role.id))
    db.commit()
    return ok(dictify(user), message="用户信息已更新")'''
assert OLD2 in s2, "update_user"
s2 = s2.replace(OLD2, NEW2)

# ---- reset_password：强度校验 ----
OLD3 = '''    from app.services.auth_service import reset_password_by_admin

    reset_password_by_admin(db, payload.user_id, payload.new_password)'''
NEW3 = '''    from app.core.config import settings as _st
    from app.core.security import validate_password_strength
    from app.services.auth_service import reset_password_by_admin

    # 此前完全不校验，实测可重置为 "a" 并直接登录
    validate_password_strength(payload.new_password,
                               min_length=_st.PASSWORD_MIN_LENGTH)
    reset_password_by_admin(db, payload.user_id, payload.new_password)'''
assert OLD3 in s2, "reset pwd"
s2 = s2.replace(OLD3, NEW3)

# ---- copy_role：禁止复制内置角色 + 返回真实权限 ----
OLD4 = '''    src = db.get(Role, role_id)
    if not src:
        raise NotFoundException("角色不存在")
'''
NEW4 = '''    src = db.get(Role, role_id)
    if not src:
        raise NotFoundException("角色不存在")
    # 内置角色不可修改是安全边界，允许复制等于提供「可修改的等价全权角色」，
    # 间接绕过该保护（实测 sys_admin 副本拥有全部 60 个权限且可随意改）。
    if src.is_builtin:
        raise BusinessException("内置角色不可复制，请直接新建角色并按需勾选权限")
'''
assert OLD4 in s2, "copy role guard"
s2 = s2.replace(OLD4, NEW4, 1)

# copy 返回补充真实权限列表（此前 dictify 关系未加载 → 前端看到 0 个权限）
OLD5 = '''    _assign_perms(db, new.id, [p.code for p in src.permissions])
    db.commit()
    return ok(dictify(new), message="角色复制成功")'''
NEW5 = '''    _assign_perms(db, new.id, [p.code for p in src.permissions])
    db.commit()
    db.refresh(new)
    d = dictify(new)
    # 关系对象需显式读取，否则前端拿到空 permissions（实测副本实际 60 个权限但返回 0）
    d["permissions"] = [p.code for p in new.permissions]
    d["user_count"] = 0
    return ok(d, message="角色复制成功")'''
assert OLD5 in s2, "copy role return"
s2 = s2.replace(OLD5, NEW5)

# ---- delete_config：关键配置白名单 ----
OLD6 = '''    row = db.scalar(select(SysConfig).where(SysConfig.key == key))
    if not row:
        raise NotFoundException("配置项不存在")
    db.delete(row)
    db.commit()
    return ok(message="配置已删除")'''
NEW6 = '''    row = db.scalar(select(SysConfig).where(SysConfig.key == key))
    if not row:
        raise NotFoundException("配置项不存在")
    # 关键前缀禁止删除：删掉 llm_enabled / llm_api_key 会让系统行为静默回落到
    # 环境变量默认值，等于绕过配置审计（实测删除 llm_provider 成功）。
    PROTECTED_PREFIXES = ("llm_", "security_", "password_", "smtp_", "secret_")
    if key.lower().startswith(PROTECTED_PREFIXES):
        raise BusinessException(
            f"「{key}」属于关键配置，不允许删除；如需恢复默认请修改其值")
    db.delete(row)
    db.commit()
    return ok(message="配置已删除")'''
assert OLD6 in s2, "delete config"
s2 = s2.replace(OLD6, NEW6)

# ---- get_config：脱敏 ----
OLD7 = '''    editable = []
    for c in db.scalars(select(SysConfig).order_by(SysConfig.category, SysConfig.id)).all():
        editable.append({
            "key": c.key, "value": c.value, "value_type": c.value_type,'''
NEW7 = '''    def _mask(k: str, v):
        """密钥类配置脱敏：仅保留前缀与后 4 位，前端不再拿到可用凭据。"""
        if v is None:
            return None
        low = k.lower()
        if any(t in low for t in ("api_key", "secret", "password", "token")):
            sv = str(v)
            if len(sv) <= 8:
                return "****"
            return f"{sv[:4]}****{sv[-4:]}"
        return v

    editable = []
    for c in db.scalars(select(SysConfig).order_by(SysConfig.category, SysConfig.id)).all():
        editable.append({
            "key": c.key, "value": _mask(c.key, c.value), "value_type": c.value_type,'''
assert OLD7 in s2, "get_config mask"
s2 = s2.replace(OLD7, NEW7)

io.open(f2, "w", encoding="utf-8", newline="\n").write(s2)
print("[2] system.py 修复完成")

# ============================================================
# 3) ai_config_service：脱敏 + 掩码保存保护
# ============================================================
f3 = "backend/app/services/ai_config_service.py"
s3 = io.open(f3, encoding="utf-8").read()

OLD8 = '''        config[key.upper()] = val'''
NEW8 = '''        # 密钥字段脱敏返回：管理员页面/浏览器网络面板不再出现完整凭据
        if "key" in key.lower() and val:
            sv = str(val)
            config[key.upper()] = (sv if len(sv) <= 8 else f"{sv[:4]}****{sv[-4:]}")
            meta_key = f"{key}_has_value"
        else:
            config[key.upper()] = val
            meta_key = None'''
assert OLD8 in s3, "ai config mask"
s3 = s3.replace(OLD8, NEW8)

# 保存时忽略掩码值
OLD9 = '''        # 转为字符串存储
        if isinstance(raw, bool):
            val = "true" if raw else "false"
        else:
            val = str(raw)'''
NEW9 = '''        # 转为字符串存储
        if isinstance(raw, bool):
            val = "true" if raw else "false"
        else:
            val = str(raw)
        # 前端回传的掩码值（含 ****）表示「未修改」，不能写回数据库覆盖真实 key
        if "****" in val:
            continue'''
assert OLD9 in s3, "ai config save guard"
s3 = s3.replace(OLD9, NEW9)
io.open(f3, "w", encoding="utf-8", newline="\n").write(s3)
print("[3] ai_config_service 脱敏完成")

# ============================================================
# 4) 注册密码强度
# ============================================================
f4 = "backend/app/api/v1/auth.py"
s4 = io.open(f4, encoding="utf-8").read()
OLD10 = '''    if payload.identity not in ("student", "teacher"):
        raise BusinessException("身份类型仅支持学生或教师")'''
NEW10 = '''    if payload.identity not in ("student", "teacher"):
        raise BusinessException("身份类型仅支持学生或教师")
    from app.core.config import settings as _st
    from app.core.security import validate_password_strength

    validate_password_strength(payload.password, min_length=_st.PASSWORD_MIN_LENGTH)'''
assert OLD10 in s4, "register pwd"
s4 = s4.replace(OLD10, NEW10)

# change_password 也走统一强度校验
OLD11 = '''    if len(new_password) < settings.PASSWORD_MIN_LENGTH:
        raise BusinessException(f"新密码长度不能少于 {settings.PASSWORD_MIN_LENGTH} 位")'''
NEW11 = '''    from app.core.security import validate_password_strength

    validate_password_strength(new_password, min_length=settings.PASSWORD_MIN_LENGTH)'''
io.open(f4, "w", encoding="utf-8", newline="\n").write(s4)

f5 = "backend/app/services/auth_service.py"
s5 = io.open(f5, encoding="utf-8").read()
s5 = s5.replace(OLD11, NEW11)
io.open(f5, "w", encoding="utf-8", newline="\n").write(s5)
print("[4] 注册/改密强度校验接入")
