"""认证相关接口：注册、审批、登录、验证码、密码。"""
import random
import threading
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, Depends, Query, Request
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import (
    bearer_scheme, get_client_ip, get_current_admin, get_current_user, get_user_agent,
)
from app.core.config import settings
from app.core.database import get_db
from app.core.exception import BusinessException
from app.core.security import (
    create_access_token, decode_token, generate_captcha, hash_password,
    revoke_token, store_captcha, store_reset_code, validate_password_strength,
    verify_captcha, verify_reset_code,
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
# 取码限流桶：{ip: [时间戳]}，进程内即可。
#
# 为什么这里可以留在内存（而验证码本身必须落库）：本桶守的是**滥用频率**，
# 不是认证正确性。验证码落库后每次 `GET /auth/captcha` 变成 1 次 SQLite 写
# （单写者），匿名端点可被无成本刷成写入瓶颈 —— 这个限额就是为此加的。
# 多 worker 下限额变 N 倍（30×N 次/分钟）仍远小于把 SQLite 打爆的量级，
# 而落库会让"防刷的东西自己产生无鉴权写"形成自激，权衡后保留内存。
_CAPTCHA_HITS: Dict[str, list] = {}
_CAPTCHA_HITS_LOCK = threading.Lock()
_CAPTCHA_IP_LIMIT = 30          # 同 IP 每分钟最多取 30 次
_CAPTCHA_IP_WINDOW = 60         # 窗口秒数


def _check_captcha_rate(ip: str) -> None:
    """按 IP 限制取码频率：同一 IP 每分钟 ≤ 30 次。"""
    now = datetime.now()
    with _CAPTCHA_HITS_LOCK:
        bucket = _CAPTCHA_HITS.setdefault(ip, [])
        bucket[:] = [t for t in bucket if (now - t).total_seconds() < _CAPTCHA_IP_WINDOW]
        if len(bucket) >= _CAPTCHA_IP_LIMIT:
            raise BusinessException("请求过于频繁，请稍后再试")
        bucket.append(now)


@router.get("/captcha", summary="获取图形验证码")
def get_captcha(request: Request, db: Session = Depends(get_db)):
    """返回 base64 图片与验证码 key（登录/注册使用）。"""
    _check_captcha_rate(get_client_ip(request))
    img_b64, text = generate_captcha()
    key = store_captcha(text, db)
    return ok({"image": f"data:image/png;base64,{img_b64}", "key": key})


def _verify_captcha_or_raise(
    db: Session, captcha_key: Optional[str], captcha: Optional[str]
) -> None:
    """按 `settings.CAPTCHA_ENFORCED` 校验图形验证码（登录 / 注册共用，S7）。

    修复前这里是两处**短路绕过**：

        if payload.captcha_key and not verify_captcha(...):
            raise ...

    `and` 的左边一旦为假（请求**不带** `captcha_key`），整个条件恒为
    False，校验被完整跳过。这不是"兼容 API 调用"，这是把开关交给了
    调用方：谁想绕过图形验证码，只要不写这个字段就行。

    现在的行为矩阵：

    | CAPTCHA_ENFORCED | 未带 key | 带 key 且正确 | 带 key 且错误/过期 |
    | ---------------- | -------- | ------------- | ------------------ |
    | `true`（默认）   | **400**  | 通过          | **400**            |
    | `false`（e2e）   | 通过     | 通过          | **400**            |

    第三列两行**完全相同**，这是刻意的：关掉开关只降级到「无验证码」，
    绝不允许降级成「带了错码也放行」。开关单向收紧，不存在"关掉即空操作"。

    为什么错误提示要区分"请输入"和"错误或已过期"：前者是客户端根本没取码
    （典型是 `GET /auth/captcha` 失败后前端静默提交），后者是用户输错。
    两者对用户是**不同的补救动作**（刷新页面重试 vs 看清图片重输），
    合并成一句话会让人反复输入却永远失败。

    校验失败**不消耗**任何东西以外的资源：`verify_captcha` 无论对错都会删掉
    该 key（一次性语义），所以同一个码不能被重放试探。
    """
    if not captcha_key:
        if settings.CAPTCHA_ENFORCED:
            raise BusinessException("请输入图形验证码")
        return
    if not verify_captcha(db, captcha_key, captcha or ""):
        raise BusinessException("验证码错误或已过期")


# ---------------------------------------------------------------- 注册与审批
@router.post("/register", summary="用户注册（待审批）")
def register(payload: RegisterIn, request: Request, db: Session = Depends(get_db)):
    if payload.identity not in ("student", "teacher"):
        raise BusinessException("身份类型仅支持学生或教师")
    from app.core.config import settings as _st
    from app.core.security import validate_password_strength

    validate_password_strength(payload.password, min_length=_st.PASSWORD_MIN_LENGTH)
    _verify_captcha_or_raise(db, payload.captcha_key, payload.captcha)
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
    # 图形验证码校验（S7 已强制化）：默认必须携带且正确。
    # 校验放在 `authenticate` **之前**是必须的 —— 否则密码错误的请求会先把
    # 该账号的 `login_fail_count` 加一并可能触发 15 分钟锁定，攻击者可以用
    # 无验证码的请求把任意已知用户名**锁死**（拒绝服务）。验证码前置后，
    # 拿不到有效码的流量碰不到账号状态。
    _verify_captcha_or_raise(db, payload.captcha_key, payload.captcha)
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
    # 必须传 db：登出时 refresh token 也被吊销，不查库就能拿它反复换新
    # access token（7 天内无法止损）。
    payload = decode_token(token, db)
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
    db: Session = Depends(get_db),
):
    """退出登录并吊销当前访问令牌（以及可选的刷新令牌）。

    只改前端状态的话，原 access_token 在过期前仍可访问任意接口，
    refresh_token 还能换出新令牌；因此这里必须服务端登记吊销。
    前端应把 localStorage 中的 refresh_token 一并提交。

    吊销记录落 `sys_revoked_token`：进程内 dict 在多 worker 下只有当前
    进程认账，其余进程仍认这个 token —— 登出等于没登出。
    """
    token = (
        credentials.credentials
        if credentials
        else request.headers.get("Authorization", "").replace("Bearer ", "").strip()
    )
    revoked = revoke_token(decode_token(token) if token else None, db)

    refresh_raw = (body or {}).get("refresh_token") or ""
    if refresh_raw:
        refresh_payload = decode_token(refresh_raw)
        if refresh_payload and refresh_payload.get("type") == "refresh":
            revoked = revoke_token(refresh_payload, db) or revoked
    return ok({"revoked": revoked}, message="已退出登录")


# ---------------------------------------------------------------- 找回密码
# 限流桶保留在内存：守的是**滥用频率**而非认证正确性。多 worker 下限额变
# N 倍（5×N 次/10min），仍远低于 6 位码 10^6 的可用爆破量级；若落库，
# 等于给一个匿名端点引入无鉴权的写放大面（每次请求都写一行），
# 与"防刷"的初衷相反。验证码本身（正确性相关）已落 `sys_reset_code`。
_RESET_RATE_LOCK = threading.Lock()
_RESET_RATE_STORE: Dict[str, list] = {}  # {target: [request_time, ...]}


def _check_reset_request_rate(target: str) -> None:
    """按目标账号限制找回密码请求频率（10 分钟最多 5 次）。"""
    now = datetime.now()
    with _RESET_RATE_LOCK:
        bucket = _RESET_RATE_STORE.setdefault(target, [])
        bucket[:] = [t for t in bucket if (now - t).total_seconds() < 600]
        if len(bucket) >= 5:
            raise BusinessException("请求过于频繁，请 10 分钟后再试")
        bucket.append(now)


def _send_reset_code_email(db: Session, target: str, code: str) -> bool:
    """通过 sys_config 中配置的 SMTP 发送验证码；未配置或发送失败返回 False。"""
    if "@" not in target:
        return False  # 当前仅支持邮箱通道；短信通道未实现
    from app.models import SysConfig

    cfg = {c.key: (c.value or "") for c in db.scalars(select(SysConfig)).all()}
    host = cfg.get("smtp_host", "").strip()
    sender = (cfg.get("smtp_from") or cfg.get("smtp_user") or "").strip()
    if not host or not sender:
        return False
    try:
        port = int(cfg.get("smtp_port") or 465)
    except (TypeError, ValueError):
        port = 465
    smtp_user = cfg.get("smtp_user", "").strip()
    smtp_pwd = cfg.get("smtp_password", "")
    try:
        import smtplib
        from email.message import EmailMessage

        msg = EmailMessage()
        msg["Subject"] = "找回密码验证码"
        msg["From"] = sender
        msg["To"] = target
        msg.set_content(
            f"你的找回密码验证码是：{code}，5 分钟内有效。\n"
            "如非本人操作，请忽略本邮件。"
        )
        if port == 465:
            server = smtplib.SMTP_SSL(host, port, timeout=10)
        else:
            server = smtplib.SMTP(host, port, timeout=10)
            server.starttls()
        with server:
            if smtp_user and smtp_pwd:
                server.login(smtp_user, smtp_pwd)
            server.send_message(msg)
        return True
    except Exception as exc:  # noqa: BLE001 邮件通道失败不暴露内部细节
        logger.error(f"找回密码邮件发送失败: {exc}")
        return False


@router.post("/forgot-password", summary="找回密码（发送验证码）")
def forgot_password(payload: Dict[str, Any] = Body(...), db: Session = Depends(get_db)):
    """通过邮箱找回密码：
    - 账号存在且系统配置了 SMTP 时发送 6 位验证码（5 分钟有效）
    - 未配置邮件通道时明确提示联系管理员，且**不生成/记录验证码**
    - 响应文案不泄露账号是否存在
    """
    target = (payload.get("email") or payload.get("phone") or "").strip()
    if not target:
        raise BusinessException("请提供邮箱或手机号")
    _check_reset_request_rate(target)
    user = db.scalar(
        select(User).where((User.email == target) | (User.phone == target))
    )
    if not user:
        # 安全考虑：不泄露账号是否存在
        return ok({"sent": True}, message="若该账号存在，验证码已发送")

    code = f"{random.randint(0, 999999):06d}"
    if not _send_reset_code_email(db, target, code):
        # 不落库、不写日志、不返回验证码：避免"假发送"与验证码进日志。
        return ok(
            {"sent": False},
            message="验证码已发送（若系统已配置邮件服务）。"
                    "当前未检测到可用的邮件配置，请联系管理员重置密码",
        )

    # 落 sys_reset_code（同 target 覆盖写，旧码立刻失效）。
    # 进程内 dict 在多 worker 下会让"发送在 A、校验在 B"，找回密码随机失败。
    store_reset_code(db, target, code)
    return ok({"sent": True}, message="验证码已发送，5 分钟内有效")


@router.post("/reset-password", summary="重置密码（验证码）")
def reset_password(payload: Dict[str, Any] = Body(...), db: Session = Depends(get_db)):
    """用验证码重置密码（无需登录）：
    - 校验验证码通过后重置密码
    - 与修改密码接口共用同一强度策略，禁止 123456 这类弱口令绕过
    """
    target = (payload.get("email") or payload.get("phone") or "").strip()
    code = (payload.get("code") or "").strip()
    new_pwd = (payload.get("new_password") or "").strip()
    if not target or not code or not new_pwd:
        raise BusinessException("请提供邮箱/手机号、验证码和新密码")
    validate_password_strength(new_pwd, min_length=settings.PASSWORD_MIN_LENGTH)
    # 一次性消费：无论校验成败都删掉该 target 的记录（防同一码被反复试）。
    if not verify_reset_code(db, target, code):
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
