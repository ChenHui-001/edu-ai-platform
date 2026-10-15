"""系统管理接口：用户、角色、权限、通知。"""
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin, get_current_user
from app.core.database import get_db
from app.core.exception import BusinessException, NotFoundException
from app.models import (
    Notification, Permission, Role, RolePermission, SysConfig, TeachingAssignment,
    User, UserRole,
)
from app.utils.common import PageParams, dictify, ok, utcnow

router = APIRouter(prefix="/system", tags=["系统管理"])


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
    _: User = Depends(get_current_admin),
):
    stmt = select(User)
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
        d = dictify(u)
        d["roles"] = u.role_codes
        items.append(d)
    return ok({"items": items, "total": total, "page": params.page, "page_size": params.page_size})


@router.post("/users", summary="新增用户")
def create_user(
    data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    from app.core.security import hash_password

    if not data.get("username") or not data.get("real_name"):
        raise BusinessException("账号和姓名不能为空")
    if db.scalar(select(User).where(User.username == data["username"])):
        raise BusinessException("该账号已存在")

    user = User(
        username=data["username"],
        password=hash_password(data.get("password", "Edu@123456")),
        real_name=data["real_name"],
        identity=data.get("identity", "student"),
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
    for code in data.get("roles", ["student"]):
        role = db.scalar(select(Role).where(Role.code == code))
        if role:
            db.add(UserRole(user_id=user.id, role_id=role.id))
    db.commit()
    db.refresh(user)
    return ok(dictify(user), message="用户创建成功")


@router.put("/users/{user_id}", summary="编辑用户")
def update_user(
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
    return ok(dictify(user), message="用户信息已更新")


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
    user_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_admin),
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
    from app.services.auth_service import reset_password_by_admin

    reset_password_by_admin(db, payload.user_id, payload.new_password)
    return ok(message="密码已重置，用户下次登录须修改密码")


@router.get("/roles", summary="角色列表")
def list_roles(db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    roles = db.scalars(select(Role).order_by(Role.sort)).all()
    return ok([
        {"id": r.id, "code": r.code, "name": r.name, "description": r.description,
         "data_scope": r.data_scope, "is_builtin": r.is_builtin, "is_active": r.is_active,
         "sort": r.sort, "user_count": len(r.users),
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
    role = Role(
        code=data["code"], name=data["name"], description=data.get("description"),
        data_scope=data.get("data_scope", "self"),
        is_builtin=False, is_active=data.get("is_active", True),
        sort=data.get("sort", 99),
    )
    db.add(role)
    db.flush()
    _assign_perms(db, role.id, data.get("permissions", []))
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
    for f in ("name", "description", "data_scope", "is_active", "sort"):
        if f in data:
            setattr(role, f, data[f])
    if "permissions" in data:
        db.execute(RolePermission.__table__.delete().where(RolePermission.role_id == role_id))
        _assign_perms(db, role_id, data["permissions"])
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
        is_builtin=False, sort=src.sort + 1,
    )
    db.add(new)
    db.flush()
    _assign_perms(db, new.id, [p.code for p in src.permissions])
    db.commit()
    return ok(dictify(new), message="角色复制成功")


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


def _assign_perms(db: Session, role_id: int, codes: List[str]) -> None:
    for code in codes:
        p = db.scalar(select(Permission).where(Permission.code == code))
        if p:
            db.add(RolePermission(role_id=role_id, permission_id=p.id))


# ---------------------------------------------------------------- 权限树
@router.get("/permissions", summary="权限点树")
def list_permissions(
    type: Optional[str] = None, db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    stmt = select(Permission)
    if type:
        stmt = stmt.where(Permission.type == type)
    perms = db.scalars(stmt.order_by(Permission.sort)).all()
    return ok([dictify(p) for p in perms])


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
    editable = []
    for c in db.scalars(select(SysConfig).order_by(SysConfig.category, SysConfig.id)).all():
        editable.append({
            "key": c.key, "value": c.value, "value_type": c.value_type,
            "category": c.category, "label": c.label or c.key,
            "description": c.description, "is_public": c.is_public,
            "updated_at": dictify(c.updated_at),
        })

    return ok({
        # 运行态只读项（来自环境变量 / settings）
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "debug": settings.DEBUG,
        "database": settings.DATABASE_URL.split("://")[0],
        "llm_provider": settings.LLM_PROVIDER,
        "llm_model": settings.LLM_MODEL,
        "llm_enabled": bool(settings.LLM_API_KEY),
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
    payload: AiTestIn, _: User = Depends(get_current_admin),
):
    """用给定配置临时测试 LLM 连接（不写入数据库）。"""
    from app.services.ai_config_service import test_ai_connection
    result = test_ai_connection(payload.model_dump())
    return ok(result)
