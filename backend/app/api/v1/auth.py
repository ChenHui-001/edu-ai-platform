"""认证相关接口：注册、审批、登录、验证码、密码。"""
from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, Depends, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_client_ip, get_current_admin, get_current_user, get_user_agent
from app.core.database import get_db
from app.core.exception import BusinessException
from app.core.security import (
    create_access_token, decode_token, generate_captcha, store_captcha, verify_captcha,
)
from app.models import Registration, User, UserStatus
from app.services import auth_service
from app.utils.common import dictify, ok

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
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    stmt = select(Registration)
    if status:
        stmt = stmt.where(Registration.status == status)
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
    return ok(dictify(user), message="审批通过" if payload.approved else "已驳回")


# ---------------------------------------------------------------- 登录
@router.post("/login", summary="账号密码登录")
def login(payload: LoginIn, request: Request, db: Session = Depends(get_db)):
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
def logout():
    return ok(message="已退出登录")
