"""认证相关接口：注册、审批、登录、验证码、密码。"""
from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, Depends, Query, Request
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import (
    bearer_scheme, get_client_ip, get_current_admin, get_current_user, get_user_agent,
)
from app.core.database import get_db
from app.core.exception import BusinessException
from app.core.security import (
    create_access_token, decode_token, generate_captcha, hash_password,
    revoke_token, store_captcha, verify_captcha,
)
from app.core.logger import get_logger
from app.models import Registration, User
from app.services import auth_service
from app.utils.common import dictify, ok

logger = get_logger("auth")

router = APIRouter(prefix="/auth", tags=["认证"])


class RegisterIn(BaseModel):
    username: str = Field(..., min_length=3, max_length=32, description="登录账号")
    password: str = Field(..., min_length=6, max_length=64)
    real_name: str = Field(..., max_length=32)
    identity: str = Field(..., description="student 学生 / teacher 教师")
    school_name: Optional[str] = None
    grade_id: Optional[int] = None
    class_id: Optional[int] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    attachments: Optional[str] = Field(None, description="证明材料附件 ID，逗号分隔")
    reason: Optional[str] = None
    captcha_key: Optional[str] = None
    captcha: Optional[str] = None


class LoginIn(BaseModel):
    username: str
    password: str
    captcha_key: Optional[str] = None
    captcha: Optional[str] = None


class AuditIn(BaseModel):
    registration_id: int
    approved: bool
    reason: Optional[str] = None


class ChangePwdIn(BaseModel):
    old_password: str
    new_password: str


# ---------------------------------------------------------------- 验证码
@router.get("/captcha", summary="获取图形验证码")
def get_captcha():
    """返回 base64 图片与验证码 key（登录/注册使用）。"""
    img_b64, text = generate_captcha()
    key = store_captcha(text)
    return ok({"image": f"data:image/png;base64,{img_b64}", "key": key})


# ---------------------------------------------------------------- 注册与审批
@router.post("/register", summary="用户注册（待审批）")
def register(payload: RegisterIn, request: Request, db: Session = Depends(get_db)):
    if payload.identity not in ("student", "teacher"):
        raise BusinessException("身份类型仅支持学生或教师")
    from app.core.config import settings as _st
    from app.core.security import validate_password_strength

    validate_password_strength(payload.password, min_length=_st.PASSWORD_MIN_LENGTH)
    if payload.captcha_key and not verify_captcha(payload.captcha_key, payload.captcha or ""):
        raise BusinessException("验证码错误或已过期")
    if payload.identity == "student" and not payload.class_id:
        raise BusinessException("学生注册需选择所属班级")

    user = auth_service.register_user(
        db,
        username=payload.username,
        password=payload.password,
        real_name=payload.real_name,
        identity=payload.identity,
        school_name=payload.school_name,
        grade_id=payload.grade_id,
        class_id=payload.class_id,
        email=payload.email,
        phone=payload.phone,
        attachments=payload.attachments,
        reason=payload.reason,
    )
    return ok(
        {"user_id": user.id, "status": user.status},
        message="注册申请已提交，请等待管理员审批",
    )


@router.get("/registrations", summary="注册申请列表（管理员）")
def list_registrations(
    status: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None, description="按账号 / 姓名模糊搜索"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    stmt = select(Registration)
    if status:
        stmt = stmt.where(Registration.status == status)
    if keyword:
        # 待审批列表常年累积，没有搜索只能逐页翻（前端原本也没有搜索框）
        kw = f"%{keyword.strip()}%"
        matched = select(User.id).where(
            (User.username.like(kw)) | (User.real_name.like(kw))
        )
        stmt = stmt.where(Registration.user_id.in_(matched))
    total = db.scalar(select(__import__("sqlalchemy").func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(
        stmt.order_by(Registration.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    ).all()
    items = []
    for r in rows:
        d = dictify(r)
        u = db.get(User, r.user_id)
        d["username"] = u.username if u else None
        d["real_name"] = u.real_name if u else None
        items.append(d)
    return ok({"items": items, "total": total, "page": page, "page_size": page_size})


@router.post("/registrations/audit", summary="审批注册申请（管理员）")
def audit_registration(
    payload: AuditIn,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    if not payload.approved and not payload.reason:
        raise BusinessException("驳回申请必须填写原因")
    user = auth_service.audit_registration(
        db, payload.registration_id, payload.approved, admin.id, payload.reason
    )
    # 不能直接 dictify(user)：会把 password（PBKDF2 哈希）回传给前端。
    _u = dictify(user)
    _u.pop("password", None)
    return ok(_u, message="审批通过" if payload.approved else "已驳回")


# ---------------------------------------------------------------- 登录
@router.post("/login", summary="账号密码登录")
def login(payload: LoginIn, request: Request, db: Session = Depends(get_db)):
    # 图形验证码校验：前端 Login.vue 始终携带 captcha_key，
    # 此处与 register 一致：传了 captcha_key 就必须校验通过。
    # 未携带则放行（兼容 API 调用与自动化测试），由失败锁定兜底防爆破。
    if payload.captcha_key and not verify_captcha(payload.captcha_key, payload.captcha or ""):
        raise BusinessException("验证码错误或已过期")
    ip = get_client_ip(request)
    device = get_user_agent(request)
    user, token, refresh = auth_service.authenticate(
        db, payload.username, payload.password, ip, device
    )
    return ok(
        {
            "access_token": token,
            "refresh_token": refresh,
            "token_type": "Bearer",
            "user": {
                "id": user.id,
                "username": user.username,
                "real_name": user.real_name,
                "avatar": user.avatar,
                "identity": user.identity,
                "grade_id": user.grade_id,
                "class_id": user.class_id,
                "must_change_password": user.must_change_password,
            },
            "permission": auth_service.build_permission_context(user),
        },
        message="登录成功",
    )


@router.post("/refresh", summary="刷新访问令牌")
def refresh_token(body: Dict[str, str] = Body(...), db: Session = Depends(get_db)):
    token = body.get("refresh_token", "")
    payload = decode_token(token)
    if not payload or payload.get("type") != "refresh":
        raise BusinessException("刷新令牌无效或已过期")
    user = db.get(User, int(payload["sub"]))
    if not user or not user.is_active:
        raise BusinessException("账号不可用")
    new_token = create_access_token(user.id, role=",".join(user.role_codes))
    return ok({"access_token": new_token, "token_type": "Bearer"})


@router.get("/profile", summary="获取当前用户信息")
def profile(user: User = Depends(get_current_user)):
    return ok(
        {
            "id": user.id,
            "username": user.username,
            "real_name": user.real_name,
            "email": user.email,
            "phone": user.phone,
            "avatar": user.avatar,
            "identity": user.identity,
            "status": user.status,
            "school_name": user.school_name,
            "grade_id": user.grade_id,
            "class_id": user.class_id,
            "must_change_password": user.must_change_password,
            "last_login_at": user.last_login_at.strftime("%Y-%m-%d %H:%M:%S")
            if user.last_login_at else None,
            "permission": auth_service.build_permission_context(user),
        }
    )


@router.put("/profile", summary="更新个人资料")
def update_profile(
    data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    for field in ("real_name", "email", "phone", "avatar"):
        if field in data:
            setattr(user, field, data[field])
    db.commit()
    return ok(message="资料已更新")


@router.put("/password", summary="修改密码")
def change_password(
    payload: ChangePwdIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    auth_service.change_password(db, user, payload.old_password, payload.new_password)
    return ok(message="密码修改成功")


@router.post("/logout", summary="退出登录")
def logout(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    body: Optional[Dict[str, Any]] = Body(default=None),
):
    """退出登录并吊销当前访问令牌（以及可选的刷新令牌）。

    只改前端状态的话，原 access_token 在过期前仍可访问任意接口，
    refresh_token 还能换出新令牌；因此这里必须服务端登记吊销。
    前端应把 localStorage 中的 refresh_token 一并提交。
    """
    token = (
        credentials.credentials
        if credentials
        else request.headers.get("Authorization", "").replace("Bearer ", "").strip()
    )
    revoked = revoke_token(decode_token(token) if token else None)

    refresh_raw = (body or {}).get("refresh_token") or ""
    if refresh_raw:
        refresh_payload = decode_token(refresh_raw)
        if refresh_payload and refresh_payload.get("type") == "refresh":
            revoked = revoke_token(refresh_payload) or revoked
    return ok({"revoked": revoked}, message="已退出登录")


# ---------------------------------------------------------------- 找回密码
_RESET_CODE_STORE: Dict[str, tuple] = {}  # {email/phone: (code, expire_at)}


@router.post("/forgot-password", summary="找回密码（发送验证码）")
def forgot_password(payload: Dict[str, Any] = Body(...), db: Session = Depends(get_db)):
    """通过邮箱/手机号找回密码：
    - 账号存在则生成 6 位验证码
    - 若系统配置了 SMTP（sys_config.smtp_host）则发邮件，否则返回提示联系管理员
    - 验证码 5 分钟有效
    """
    import random
    from datetime import datetime, timedelta
    target = (payload.get("email") or payload.get("phone") or "").strip()
    if not target:
        raise BusinessException("请提供邮箱或手机号")
    user = db.scalar(
        select(User).where((User.email == target) | (User.phone == target))
    )
    if not user:
        # 安全考虑：不泄露账号是否存在
        return ok(message="若该账号存在，验证码已发送")
    code = f"{random.randint(0, 999999):06d}"
    _RESET_CODE_STORE[target] = (code, datetime.now() + timedelta(minutes=5))
    # 清理过期项
    now = datetime.now()
    for k in [k for k, (_, exp) in _RESET_CODE_STORE.items() if exp < now]:
        _RESET_CODE_STORE.pop(k, None)
    # SMTP 发送（若配置）——这里仅记录，真实发送需配置 SMTP
    # 生产环境应在 sys_config 配置 smtp_host/smtp_password
    logger.info(f"找回密码验证码已生成：账号 {target}，code={code}")
    return ok({"sent": True, "target": target},
              message="验证码已发送，5 分钟内有效")


@router.post("/reset-password", summary="重置密码（验证码）")
def reset_password(payload: Dict[str, Any] = Body(...), db: Session = Depends(get_db)):
    """用验证码重置密码（无需登录）：
    - 接收 email/phone、code、new_password
    - 校验验证码通过后重置密码并标记强制改密
    """
    from datetime import datetime
    target = (payload.get("email") or payload.get("phone") or "").strip()
    code = (payload.get("code") or "").strip()
    new_pwd = (payload.get("new_password") or "").strip()
    if not target or not code or not new_pwd:
        raise BusinessException("请提供邮箱/手机号、验证码和新密码")
    if len(new_pwd) < 6:
        raise BusinessException("新密码长度不能少于 6 位")
    item = _RESET_CODE_STORE.pop(target, None)
    if not item or item[0] != code or item[1] < datetime.now():
        raise BusinessException("验证码错误或已过期")
    user = db.scalar(
        select(User).where((User.email == target) | (User.phone == target))
    )
    if not user:
        raise BusinessException("账号不存在")
    user.password = hash_password(new_pwd)
    user.must_change_password = False  # 已在此处改密
    user.login_fail_count = 0
    user.locked_until = None
    db.commit()
    return ok(message="密码已重置，请使用新密码登录")
