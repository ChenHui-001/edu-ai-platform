"""系统管理接口：用户、角色、权限、通知。"""
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends
from pydantic import BaseModel
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin, get_current_manager, get_current_user
from app.core.database import get_db
from app.core.exception import BusinessException, NotFoundException
from app.models import (
    Notification, Permission, Role, RolePermission, SysConfig, TeachingAssignment,
    User, UserRole,
)
from app.utils.common import PageParams, dictify, ok

router = APIRouter(prefix="/system", tags=["系统管理"])

# 用户对象序列化时必须剔除的字段。
# `dictify()` 走的是 ORM 全字段导出，因此凡是要把 User 回传给前端的地方
# 都必须经过 `user_dict()`，否则 `password`（PBKDF2 哈希）会原样泄露给
# admin / grade_admin。哈希不可逆，但拿到后可离线爆破，属无必要暴露。
_USER_SECRET_FIELDS = ("password",)


def user_dict(u: User, with_roles: bool = True) -> Dict[str, Any]:
    """安全的用户序列化：剔除密码哈希等敏感字段。"""
    d = dictify(u)
    for f in _USER_SECRET_FIELDS:
        d.pop(f, None)
    if with_roles:
        d["roles"] = u.role_codes
    return d


# ---------------------------------------------------------------- 用户
@router.get("/users", summary="用户列表")
def list_users(
    params: PageParams = Depends(),
    keyword: Optional[str] = None,
    identity: Optional[str] = None,
    status: Optional[str] = None,
    grade_id: Optional[int] = None,
    class_id: Optional[int] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_manager),
):
    stmt = select(User)
    # 年级管理员只能看到本年级用户；此前仅靠 get_current_manager 放行，
    # 实际上可拉全校用户手机号/邮箱/学校等 PII。未配置管辖年级时拒绝。
    codes = set(user.role_codes or [])
    if "sys_admin" not in codes and "grade_admin" in codes:
        gid = user.grade_admin_grade_id or user.grade_id
        stmt = stmt.where(User.grade_id == gid) if gid else stmt.where(User.id == -1)
    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where(or_(User.username.like(like), User.real_name.like(like),
                              User.phone.like(like)))
    if identity:
        stmt = stmt.where(User.identity == identity)
    if status:
        stmt = stmt.where(User.status == status)
    if grade_id:
        stmt = stmt.where(User.grade_id == grade_id)
    if class_id:
        stmt = stmt.where(User.class_id == class_id)

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(
        stmt.order_by(User.id.desc()).offset(params.offset).limit(params.page_size)
    ).all()
    items = []
    for u in rows:
        items.append(user_dict(u))
    return ok({"items": items, "total": total, "page": params.page, "page_size": params.page_size})


@router.post("/users", summary="新增用户")
def create_user(
    data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    from app.core.security import hash_password, validate_password_strength
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
        password=hash_password(raw_pwd),
        real_name=data["real_name"],
        identity=identity,
        status=data.get("status", "active"),
        school_name=data.get("school_name"),
        grade_id=data.get("grade_id"),
        class_id=data.get("class_id"),
        email=data.get("email"),
        phone=data.get("phone"),
        must_change_password=data.get("must_change_password", True),
    )
    db.add(user)
    db.flush()
    for role in roles_db:
        db.add(UserRole(user_id=user.id, role_id=role.id))
    db.commit()
    db.refresh(user)
    return ok(user_dict(user), message="用户创建成功")


@router.put("/users/{user_id}", summary="编辑用户")
def update_user(
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
    return ok(user_dict(user), message="用户信息已更新")


@router.delete("/users/{user_id}", summary="删除用户")
def delete_user(
    user_id: int, db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    if user_id == admin.id:
        raise BusinessException("不能删除自己")
    user = db.get(User, user_id)
    if not user:
        raise NotFoundException("用户不存在")
    db.delete(user)
    db.commit()
    return ok(message="用户已删除")


@router.get("/users/{user_id}/teachings", summary="教师授课关系")
def user_teachings(
    user_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_manager),
):
    rows = db.scalars(
        select(TeachingAssignment).where(TeachingAssignment.teacher_id == user_id)
    ).all()
    return ok([dictify(r) for r in rows])


# ---------------------------------------------------------------- 角色
class ResetPwdIn(BaseModel):
    user_id: int
    new_password: str


@router.put("/password/reset", summary="重置用户密码（管理员）")
def reset_password(
    payload: ResetPwdIn, db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    from app.core.config import settings as _st
    from app.core.security import validate_password_strength
    from app.services.auth_service import reset_password_by_admin

    # 此前完全不校验，实测可重置为 "a" 并直接登录
    validate_password_strength(payload.new_password,
                               min_length=_st.PASSWORD_MIN_LENGTH)
    reset_password_by_admin(db, payload.user_id, payload.new_password)
    return ok(message="密码已重置，用户下次登录须修改密码")


@router.get("/roles", summary="角色列表")
def list_roles(db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    roles = db.scalars(select(Role).order_by(Role.sort)).all()
    # user_count 一次聚合查出。原写法 len(r.users) 会对每个角色
    # 单独发一条 SELECT（N+1），角色多时列表接口线性变慢。
    counts = dict(db.execute(
        select(UserRole.role_id, func.count()).group_by(UserRole.role_id)
    ).all())
    return ok([
        {"id": r.id, "code": r.code, "name": r.name, "description": r.description,
         "data_scope": r.data_scope, "is_builtin": r.is_builtin, "is_active": r.is_active,
         "sort": r.sort, "user_count": counts.get(r.id, 0),
         "permissions": [p.code for p in r.permissions]}
        for r in roles
    ])


@router.post("/roles", summary="新增角色")
def create_role(
    data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    if not data.get("code") or not data.get("name"):
        raise BusinessException("角色编码和名称不能为空")
    if db.scalar(select(Role).where(Role.code == data["code"])):
        raise BusinessException("角色编码已存在")
    # 角色编码规范：仅小写字母/数字/下划线，防止后续按 code 做权限判断时出错
    import re as _re
    if not _re.fullmatch(r"[a-z][a-z0-9_]{1,62}", data["code"].strip()):
        raise BusinessException("角色编码仅允许小写字母开头，含小写字母/数字/下划线，2-63 位")
    role = Role(
        code=data["code"].strip(), name=data["name"].strip(), description=data.get("description"),
        data_scope=data.get("data_scope", "self"),
        is_builtin=False, is_active=data.get("is_active", True),
        sort=data.get("sort", 99),
    )
    db.add(role)
    db.flush()
    unknown = _assign_perms(db, role.id, data.get("permissions", []))
    if unknown:
        raise BusinessException(f"以下权限码不存在：{', '.join(sorted(unknown))}")
    db.commit()
    return ok(dictify(role), message="角色创建成功")


@router.put("/roles/{role_id}", summary="编辑角色")
def update_role(
    role_id: int, data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    role = db.get(Role, role_id)
    if not role:
        raise NotFoundException("角色不存在")
    # 与前端「内置角色不可修改」语义对齐：此前仅前端隐藏按钮，
    # 直接调 API 仍可改动 sys_admin 等内置角色的权限。
    if role.is_builtin:
        raise BusinessException("内置角色不可修改")
    for f in ("name", "description", "data_scope", "is_active", "sort"):
        if f in data:
            setattr(role, f, data[f])
    if "permissions" in data:
        db.execute(RolePermission.__table__.delete().where(RolePermission.role_id == role_id))
        unknown = _assign_perms(db, role_id, data["permissions"])
        if unknown:
            # 未知权限码不能静默丢弃：会让管理员以为已授权实际没授上
            raise BusinessException(f"以下权限码不存在：{', '.join(sorted(unknown))}")
    db.commit()
    return ok(dictify(role), message="角色已更新")


@router.post("/roles/{role_id}/copy", summary="复制角色")
def copy_role(
    role_id: int, db: Session = Depends(get_db),
    _: User = Depends(get_current_admin), data: Dict[str, Any] = Body(default={}),
):
    src = db.get(Role, role_id)
    if not src:
        raise NotFoundException("角色不存在")
    # 内置角色不可修改是安全边界，允许复制等于提供「可修改的等价全权角色」，
    # 间接绕过该保护（实测 sys_admin 副本拥有全部 60 个权限且可随意改）。
    if src.is_builtin:
        raise BusinessException("内置角色不可复制，请直接新建角色并按需勾选权限")

    # code/name 都有唯一约束，固定加 "_copy" 后缀会导致第二次复制必然冲突。
    # 这里按序号自动去重，保证可以反复复制。
    base_code = (data.get("code") or f"{src.code}_copy").strip()[:48]
    base_name = (data.get("name") or f"{src.name}副本").strip()[:48]
    code, name = base_code, base_name
    n = 1
    while db.scalar(select(Role.id).where(
        (Role.code == code) | (Role.name == name)
    )):
        n += 1
        code = f"{base_code}{n}"
        name = f"{base_name}{n}"

    new = Role(
        code=code, name=name,
        description=src.description, data_scope=src.data_scope,
        is_builtin=False, is_active=src.is_active, sort=src.sort + 1,
    )
    db.add(new)
    db.flush()
    _assign_perms(db, new.id, [p.code for p in src.permissions])
    db.commit()
    db.refresh(new)
    d = dictify(new)
    # 关系对象需显式读取，否则前端拿到空 permissions（实测副本实际 60 个权限但返回 0）
    d["permissions"] = [p.code for p in new.permissions]
    d["user_count"] = 0
    return ok(d, message="角色复制成功")


@router.delete("/roles/{role_id}", summary="删除角色")
def delete_role(
    role_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_admin),
):
    role = db.get(Role, role_id)
    if not role:
        raise NotFoundException("角色不存在")
    if role.is_builtin:
        raise BusinessException("内置角色不可删除，可选择停用")
    if role.users:
        raise BusinessException(f"该角色下还有 {len(role.users)} 个用户，请先调整用户角色")
    db.delete(role)
    db.commit()
    return ok(message="角色已删除")


def _assign_perms(db: Session, role_id: int, codes: List[str]) -> List[str]:
    """为角色绑定权限点，返回**不存在**的权限码列表。

    原实现对未知 code 静默跳过 —— 管理员提交了一个打错的权限码
    不会有任何反馈，授权结果与界面勾选不一致且无从排查。
    现在返回未知码，由调用方决定报错或记日志；
    同时去重，避免同一 code 重复插入触发唯一约束 500。
    """
    unknown: List[str] = []
    seen: set = set()
    for code in codes:
        if code in seen:
            continue
        seen.add(code)
        p = db.scalar(select(Permission).where(Permission.code == code))
        if p:
            db.add(RolePermission(role_id=role_id, permission_id=p.id))
        else:
            unknown.append(code)
    return unknown


# ---------------------------------------------------------------- 权限树
@router.get("/permissions", summary="权限点列表 / 树")
def list_permissions(
    type: Optional[str] = None,
    role_id: Optional[int] = None,
    tree: bool = False,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_manager),
):
    """查询权限点。

    - `role_id`：只返回该角色已绑定的权限点（此前该参数被静默忽略，
      前端与 e2e 传了都拿全量列表，属契约缺口）；
    - `tree=true`：组装成 {key,label,children} 树供 el-tree 渲染。
      分组节点 key 为 `{type}:group`（前端过滤 `:group:` 恰好命中）；
      叶子 key 即权限 code。此前返回扁平列表，
      前端期望的分组树形从未真正渲染过。
    """
    stmt = select(Permission)
    if role_id is not None:
        stmt = stmt.join(RolePermission, RolePermission.permission_id == Permission.id).where(
            RolePermission.role_id == role_id
        )
    if type:
        stmt = stmt.where(Permission.type == type)
    perms = db.scalars(stmt.order_by(Permission.sort, Permission.id)).all()

    if not tree:
        return ok([dictify(p) for p in perms])

    groups: Dict[str, list] = {}
    label_map = {"menu": "菜单权限", "button": "操作权限", "data": "数据权限"}
    for p in perms:
        groups.setdefault(p.type, []).append({
            "key": p.code, "label": f"{p.name}（{p.code}）",
            "code": p.code, "type": p.type,
        })
    # 固定分组顺序，菜单在前
    ordered = ["menu", "button", "data"]
    nodes = []
    for gtype in ordered:
        if gtype not in groups:
            continue
        nodes.append({
            "key": f"{gtype}:group",
            "label": label_map.get(gtype, gtype),
            "children": groups[gtype],
        })
    return ok(nodes)


# ---------------------------------------------------------------- 通知
@router.get("/notifications", summary="我的通知")
def my_notifications(
    params: PageParams = Depends(), is_read: Optional[bool] = None,
    db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    stmt = select(Notification).where(Notification.user_id == user.id)
    if is_read is not None:
        stmt = stmt.where(Notification.is_read.is_(is_read))
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(
        stmt.order_by(Notification.created_at.desc())
        .offset(params.offset).limit(params.page_size)
    ).all()
    unread = db.scalar(
        select(func.count()).select_from(Notification).where(
            Notification.user_id == user.id, Notification.is_read.is_(False)
        )
    ) or 0
    return ok({"items": [dictify(r) for r in rows], "total": total,
               "unread": unread, "page": params.page})


@router.put("/notifications/{notif_id}/read", summary="标记通知已读")
def read_notification(
    notif_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    n = db.get(Notification, notif_id)
    if not n or n.user_id != user.id:
        raise NotFoundException("通知不存在")
    n.is_read = True
    db.commit()
    return ok(message="已读")


@router.put("/notifications/read-all", summary="全部标记已读")
def read_all(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    db.execute(
        Notification.__table__.update()
        .where(Notification.user_id == user.id, Notification.is_read.is_(False))
        .values(is_read=True)
    )
    db.commit()
    return ok(message="全部已读")


# ---------------------------------------------------------------- 配置
@router.get("/config", summary="系统配置（可编辑项 + 运行态只读项）")
def get_config(db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    from app.core.config import settings

    # 可在线编辑项：来自 sys_config 表，由管理员通过 PUT /config 维护
    def _mask(k: str, v):
        """密钥类配置脱敏：仅保留前缀与后 4 位，前端不再拿到可用凭据。

        空值必须原样返回空串：此前 `len(sv) <= 8` 会把 "" 也渲染成 `****`，
        管理员无法区分「已配置」和「已清空」（把密钥清空后界面仍显示有值）。
        """
        if v is None:
            return None
        sv = str(v)
        if sv == "":
            return ""
        low = k.lower()
        if any(t in low for t in ("api_key", "secret", "password", "token")):
            if len(sv) <= 8:
                return "****"
            return f"{sv[:4]}****{sv[-4:]}"
        return v

    editable = []
    for c in db.scalars(select(SysConfig).order_by(SysConfig.category, SysConfig.id)).all():
        editable.append({
            "key": c.key, "value": _mask(c.key, c.value), "value_type": c.value_type,
            "category": c.category, "label": c.label or c.key,
            "description": c.description, "is_public": c.is_public,
            "updated_at": dictify(c.updated_at),
        })

    # 运行态项：LLM 三项必须走 sys_config 优先的取值路径，否则管理员在
    # 「AI 配置」页改完 provider/model/key 后，这一页仍显示 .env 的旧值。
    from app.agents.llm import _get_db_value as _cfg_val, is_available as _llm_available

    return ok({
        # 运行态只读项（sys_config 优先，回落 settings）
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "debug": settings.DEBUG,
        "database": settings.DATABASE_URL.split("://")[0],
        "llm_provider": _cfg_val("llm_provider", "string", settings.LLM_PROVIDER),
        "llm_model": _cfg_val("llm_model", "string", settings.LLM_MODEL),
        "llm_enabled": _llm_available(),
        "max_upload_size": settings.MAX_UPLOAD_SIZE,
        "scheduler_enabled": settings.SCHEDULER_ENABLED,
        "log_retention_days": settings.LOG_RETENTION_DAYS,
        "review_intervals": settings.REVIEW_INTERVALS,
        # 可编辑配置项
        "editable": editable,
    })


class ConfigUpdateIn(BaseModel):
    key: str
    value: Optional[str] = None
    value_type: str = "string"
    label: Optional[str] = None
    description: Optional[str] = None
    category: str = "basic"
    is_public: bool = False


@router.put("/config", summary="更新系统配置（管理员）")
def update_config(
    payload: ConfigUpdateIn, db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """新增或更新一项可在线调整的系统配置。

    这些配置保存在 sys_config 表中，业务侧通过 config_service.get(key) 读取，
    优先级高于 settings 默认值，因此修改后无需重启容器。
    """
    row = db.scalar(select(SysConfig).where(SysConfig.key == payload.key))
    if row:
        row.value = payload.value
        row.value_type = payload.value_type
        if payload.label:
            row.label = payload.label
        if payload.description:
            row.description = payload.description
        row.category = payload.category
        row.is_public = payload.is_public
        row.updated_by = admin.id
    else:
        row = SysConfig(
            key=payload.key, value=payload.value, value_type=payload.value_type,
            label=payload.label, description=payload.description,
            category=payload.category, is_public=payload.is_public,
            updated_by=admin.id,
        )
        db.add(row)
    db.commit()
    db.refresh(row)
    return ok({
        "key": row.key, "value": row.value, "value_type": row.value_type,
        "category": row.category, "updated_at": dictify(row.updated_at),
    }, message="配置已保存")


@router.delete("/config/{key}", summary="删除系统配置")
def delete_config(
    key: str, db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    row = db.scalar(select(SysConfig).where(SysConfig.key == key))
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
    return ok(message="配置已删除")


# ---------------------------------------------------------------- AI 大模型配置
@router.get("/ai-config", summary="AI 大模型配置")
def get_ai_config_route(db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    """获取当前 AI 大模型配置（sys_config 表 > .env 环境变量）。"""
    from app.services.ai_config_service import get_ai_config
    return ok(get_ai_config(db))


class AiConfigIn(BaseModel):
    llm_enabled: Optional[bool] = None
    llm_provider: Optional[str] = None
    llm_api_key: Optional[str] = None
    llm_base_url: Optional[str] = None
    llm_model: Optional[str] = None
    llm_temperature: Optional[float] = None
    llm_max_tokens: Optional[int] = None
    llm_timeout: Optional[int] = None


@router.put("/ai-config", summary="保存 AI 大模型配置")
def save_ai_config_route(
    payload: AiConfigIn, db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """保存 AI 大模型配置到 sys_config 表，保存后自动重载 LLM 客户端。"""
    from app.services.ai_config_service import save_ai_config
    data = {k: v for k, v in payload.model_dump().items() if v is not None}
    result = save_ai_config(db, data, admin.id)
    return ok(result, message="AI 配置已保存并重载")


class AiTestIn(BaseModel):
    llm_provider: Optional[str] = None
    llm_api_key: Optional[str] = None
    llm_base_url: Optional[str] = None
    llm_model: Optional[str] = None


@router.post("/ai-config/test", summary="测试 AI 大模型连接")
def test_ai_config_route(
    payload: AiTestIn, db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """用给定配置临时测试 LLM 连接（不写入数据库）。

    前端不会回显已保存的 API Key：payload.llm_api_key 为空/掩码时，
    `test_ai_connection` 会用 db 读取 sys_config 中已保存的 key。
    """
    from app.services.ai_config_service import test_ai_connection
    # exclude_none：未填写的字段不参与覆盖，便于「空 key 用已保存配置」的语义
    result = test_ai_connection(payload.model_dump(exclude_none=True), db=db)
    return ok(result)
