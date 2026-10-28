"""认证服务：注册审批、登录、异常登录检测。"""
from datetime import timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exception import AuthException, BusinessException
from app.core.security import (
    create_access_token, create_refresh_token, hash_password, verify_password,
)
from app.core.logger import get_logger
from app.models import (
    LoginLog, Notification, Permission, Registration, Role, User, UserRole,
    UserStatus,
)
from app.utils.common import now_local

logger = get_logger("auth")

MAX_LOGIN_FAIL = 5
LOCK_MINUTES = 15


# ---------------------------------------------------------------- 注册
def register_user(
    db: Session,
    *,
    username: str,
    password: str,
    real_name: str,
    identity: str,
    school_name: Optional[str] = None,
    grade_id: Optional[int] = None,
    class_id: Optional[int] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    attachments: Optional[str] = None,
    reason: Optional[str] = None,
) -> User:
    """用户注册（学生/教师），进入待审批状态。"""
    if len(password) < settings.PASSWORD_MIN_LENGTH:
        raise BusinessException(f"密码长度不能少于 {settings.PASSWORD_MIN_LENGTH} 位")
    exists = db.scalar(select(User).where(User.username == username))
    if exists:
        raise BusinessException("该账号已被注册")

    user = User(
        username=username,
        password=hash_password(password),
        real_name=real_name,
        identity=identity,
        school_name=school_name,
        grade_id=grade_id,
        class_id=class_id,
        email=email,
        phone=phone,
        status=UserStatus.PENDING.value,
        must_change_password=True,
    )
    db.add(user)
    db.flush()

    # 默认赋予学生/教师角色，审批通过后生效
    default_role = "student" if identity == "student" else "teacher"
    role = db.scalar(select(Role).where(Role.code == default_role))
    if role:
        db.add(UserRole(user_id=user.id, role_id=role.id))

    db.add(
        Registration(
            user_id=user.id,
            identity=identity,
            attachments=attachments,
            reason=reason,
            status=UserStatus.PENDING.value,
        )
    )
    # 通知所有管理员有待审批申请
    admin_ids = db.scalars(
        select(User.id).join(UserRole, UserRole.user_id == User.id)
        .join(Role, Role.id == UserRole.role_id)
        .where(Role.code == "sys_admin", User.status == UserStatus.ACTIVE.value)
    ).all()
    for aid in admin_ids:
        db.add(
            Notification(
                user_id=aid,
                title="新的注册申请待审批",
                content=f"用户 {real_name}（{username}）提交了{'教师' if identity == 'teacher' else '学生'}注册申请",
                type="audit",
                biz_type="registration",
                biz_id=user.id,
            )
        )
    db.commit()
    db.refresh(user)
    logger.info(f"新注册用户 {username} 待审批")
    return user


def audit_registration(
    db: Session, registration_id: int, approved: bool, audit_user_id: int, reason: Optional[str] = None
) -> User:
    """管理员审批注册申请。"""
    reg = db.get(Registration, registration_id)
    if not reg:
        raise BusinessException("注册申请不存在")
    if reg.status != UserStatus.PENDING.value:
        raise BusinessException("该申请已处理")

    user = db.get(User, reg.user_id)
    if not user:
        raise BusinessException("用户不存在")

    reg.status = UserStatus.ACTIVE.value if approved else UserStatus.REJECTED.value
    reg.audit_user_id = audit_user_id
    reg.audit_at = now_local()
    reg.audit_reason = reason
    user.status = reg.status

    db.add(
        Notification(
            user_id=user.id,
            title="注册审批结果通知",
            content=(
                "你的注册申请已通过审批，欢迎使用系统。"
                if approved
                else f"你的注册申请未通过审核。原因：{reason or '资料不符合要求'}"
            ),
            type="audit",
            biz_type="registration",
            biz_id=reg.id,
        )
    )
    db.commit()
    db.refresh(user)
    logger.info(f"注册审批 {registration_id}: {'通过' if approved else '驳回'}")
    return user


# ---------------------------------------------------------------- 登录
def authenticate(
    db: Session, username: str, password: str, ip: str, device: str
) -> Tuple[User, str, str]:
    """账号密码登录，返回 (用户, access_token, refresh_token)。"""
    user = db.scalar(select(User).where(User.username == username))

    def _fail(msg: str):
        db.add(
            LoginLog(
                user_id=user.id if user else None,
                username=username,
                status="failed",
                message=msg,
                ip=ip,
                device=device,
            )
        )
        db.commit()
        raise AuthException(msg)

    if not user:
        _fail("账号或密码错误")

    # 锁定检查
    if user.locked_until and user.locked_until > now_local():
        _fail(f"账号已锁定，请于 {user.locked_until.strftime('%H:%M')} 后重试")
    if not user.is_active:
        if user.status == UserStatus.PENDING.value:
            _fail("账号正在审批中，请耐心等待管理员审核")
        _fail(f"账号状态异常：{user.status}")

    if not verify_password(password, user.password):
        user.login_fail_count += 1
        abnormal = False
        if user.login_fail_count >= MAX_LOGIN_FAIL:
            user.locked_until = now_local() + timedelta(minutes=LOCK_MINUTES)
            user.login_fail_count = 0
            abnormal = True
        db.add(
            LoginLog(
                user_id=user.id, username=username, status="failed",
                message="密码错误", ip=ip, device=device, is_abnormal=abnormal,
            )
        )
        db.commit()
        raise AuthException("账号或密码错误")

    # 异地登录检测：IP 变化且 24 小时内有其他 IP 成功登录
    prev_ip = user.last_login_ip
    is_abnormal = bool(
        prev_ip
        and prev_ip != ip
        and user.last_login_at
        and (now_local() - user.last_login_at) < timedelta(days=1)
    )

    user.login_fail_count = 0
    user.last_login_at = now_local()
    user.last_login_ip = ip
    db.add(
        LoginLog(
            user_id=user.id, username=username, status="success",
            message="登录成功", ip=ip, device=device, is_abnormal=is_abnormal,
        )
    )
    db.commit()
    db.refresh(user)

    if is_abnormal:
        # 必须用赋值前取到的 prev_ip：user.last_login_ip 在上面 8 行处已经被
        # 写成本次 IP，再读它打出来的永远是「X -> X」，唯一的溯源线索作废。
        logger.warning(f"用户 {username} 异地登录：{prev_ip} -> {ip}")
        db.add(
            Notification(
                user_id=user.id,
                title="异常登录提醒",
                content=(
                    f"检测到您的账号在新 IP（{ip}，上次为 {prev_ip}）登录，"
                    "如非本人操作请立即修改密码。"
                ),
                type="system",
            )
        )
        db.commit()

    token = create_access_token(user.id, role=",".join(user.role_codes), extra={"name": user.real_name})
    return user, token, create_refresh_token(user.id)


def change_password(db: Session, user: User, old_password: str, new_password: str) -> None:
    """修改密码。"""
    if not verify_password(old_password, user.password):
        raise BusinessException("原密码错误")
    from app.core.security import validate_password_strength

    validate_password_strength(new_password, min_length=settings.PASSWORD_MIN_LENGTH)
    user.password = hash_password(new_password)
    user.must_change_password = False
    db.commit()


def reset_password_by_admin(db: Session, user_id: int, new_password: str) -> None:
    """管理员重置密码，强制下次登录修改。"""
    user = db.get(User, user_id)
    if not user:
        raise BusinessException("用户不存在")
    user.password = hash_password(new_password)
    user.must_change_password = True
    user.login_fail_count = 0
    user.locked_until = None
    db.commit()


# ---------------------------------------------------------------- 权限上下文
def build_permission_context(user: User) -> Dict[str, Any]:
    """构造登录后返回的权限上下文（前端按钮级权限控制）。"""
    menus: List[Dict[str, Any]] = []
    perms: List[str] = []
    for role in user.roles:
        # 停用角色不下发任何权限点，否则前端仍会显示可点的按钮，
        # 而后端 has_perm 已拒绝 —— 形成「菜单进得去、接口 403」的错配。
        if not role.is_active:
            continue
        for p in role.permissions:
            if p.type == "menu":
                menus.append({"code": p.code, "name": p.name, "path": p.path, "icon": p.icon})
            perms.append(p.code)
    is_super = "sys_admin" in user.role_codes
    if is_super:
        # 超级管理员拥有全部权限：perms 通配，menus 取全部菜单权限点，
        # 否则因 perms=["*"] 跳过角色-权限关联，管理员登录后菜单为空。
        perms = ["*"]
        if not menus:
            from app.core.database import SessionLocal
            _db = SessionLocal()
            try:
                for p in _db.scalars(
                    select(Permission).where(Permission.type == "menu").order_by(Permission.sort)
                ).all():
                    menus.append({"code": p.code, "name": p.name, "path": p.path, "icon": p.icon})
            finally:
                _db.close()
    return {
        "roles": user.role_codes,
        "permissions": sorted(set(perms)),
        "menus": menus,
        "identity": user.identity,
    }
