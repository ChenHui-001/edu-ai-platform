"""依赖注入：认证、当前用户、权限校验、数据权限范围。"""
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exception import AuthException, PermissionException
from app.core.security import decode_token
from app.models import User, UserRole
from app.utils.common import utcnow

bearer_scheme = HTTPBearer(auto_error=False)

# 角色编码常量
ROLE_SYS_ADMIN = "sys_admin"
ROLE_GRADE_ADMIN = "grade_admin"
ROLE_TEACHER = "teacher"
ROLE_STUDENT = "student"
ROLE_GUEST = "guest"

# 首次登录强制改密白名单：这些路径在 must_change_password=True 时仍可访问，
# 使改密闭环本身可用（需求 4.1.1「首次登录强制修改密码」）。
_FORCE_PWD_WHITELIST = (
    "/api/v1/auth/password",
    "/api/v1/auth/profile",
    "/api/v1/auth/logout",
    "/api/v1/auth/refresh",
    "/api/v1/auth/captcha",
    "/api/v1/health",
    "/docs",
    "/openapi.json",
    "/redoc",
)


def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """解析 Bearer Token 获取当前用户。"""
    token = (
        credentials.credentials
        if credentials
        else request.headers.get("Authorization", "").replace("Bearer ", "").strip()
    )
    if not token:
        raise AuthException("未提供认证令牌")

    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise AuthException("令牌无效或已过期")

    # 过期判断必须用**显式 UTC** 解释时间戳。
    # 原写法 datetime.fromtimestamp(ts) 会按服务器本地时区解析，
    # 容器 TZ=Asia/Shanghai 时比 UTC 快 8 小时，
    # 导致 token 实际过期后近 8 小时才被判过期（且刷新时机错位）。
    #
    # 注意：utcnow() 返回的是 naive UTC，这里用 .replace(tzinfo=None)
    # 去掉 tzinfo，保证两者类型一致可比较
    # （直接用 tz=timezone.utc 会得到 aware 对象，与 naive 比较抛
    #  TypeError: can't compare offset-naive and offset-aware datetimes）。
    if datetime.fromtimestamp(payload["exp"], timezone.utc).replace(tzinfo=None) < utcnow():
        raise AuthException("令牌已过期，请重新登录")

    user = db.scalar(select(User).where(User.id == int(payload["sub"])))
    if not user:
        raise AuthException("用户不存在")
    if not user.is_active:
        raise AuthException(f"账号状态异常：{user.status}")
    # 首次登录强制改密：非白名单路径一律拦截
    path = (request.url.path or "").rstrip("/")
    if user.must_change_password and not any(
        path == w.rstrip("/") or path.startswith(w.rstrip("/") + "/")
        for w in _FORCE_PWD_WHITELIST
    ):
        raise PermissionException("首次登录或密码已被重置，请先修改密码")
    return user


def get_current_admin(user: User = Depends(get_current_user)) -> User:
    """系统管理员（含全量数据与系统级配置：角色、审批、AI 配置、系统配置）。"""
    if ROLE_SYS_ADMIN not in user.role_codes:
        raise PermissionException("需要系统管理员权限")
    return user


def get_current_manager(user: User = Depends(get_current_user)) -> User:
    """系统管理员或年级管理员（系统管理类）。

    与 `get_current_admin` 的区别：本依赖额外放开给年级管理员，
    用于**只读与本年级范围内**的管理动作——用户列表、日志审计、
    附件、系统报表等。这些功能前端菜单本就对 grade_admin 可见，
    若接口一律要求 sys_admin，会出现「菜单点得进去、接口一律 403」的错配。

    注意：角色权限、注册审批、AI/系统配置、定时任务写操作等
    仍必须走 `get_current_admin`，不在本依赖范围内。
    """
    if not ({ROLE_SYS_ADMIN, ROLE_GRADE_ADMIN} & set(user.role_codes)):
        raise PermissionException("需要系统管理员或年级管理员权限")
    return user


def get_current_teacher(user: User = Depends(get_current_user)) -> User:
    """教师及以上（管理员也可访问教学接口）。"""
    codes = user.role_codes
    if not ({ROLE_TEACHER, ROLE_GRADE_ADMIN, ROLE_SYS_ADMIN} & set(codes)):
        raise PermissionException("需要教师权限")
    return user


def get_current_student(user: User = Depends(get_current_user)) -> User:
    """学生及以上。"""
    codes = user.role_codes
    if not ({ROLE_STUDENT, ROLE_TEACHER, ROLE_GRADE_ADMIN, ROLE_SYS_ADMIN} & set(codes)):
        raise PermissionException("需要学生权限")
    return user


def get_current_student_self(user: User = Depends(get_current_user)) -> User:
    """仅学生本人（写入型学习数据：笔记/练习/收藏/目标/复习）。

    学习中心是学生个人空间，教师与管理员不应在此创建数据——
    否则会在学生表里留下「教师身份的学生笔记」等错位记录。
    """
    if user.identity != "student":
        raise PermissionException("该功能仅学生可用")
    return user


class DataScope:
    """数据权限范围计算：严格隔离教师/学生可见数据。"""

    def __init__(self, user: User, db: Session):
        self.user = user
        self.db = db
        self.codes = user.role_codes

    @property
    def is_super(self) -> bool:
        return ROLE_SYS_ADMIN in self.codes

    @property
    def is_grade_admin(self) -> bool:
        return ROLE_GRADE_ADMIN in self.codes

    @property
    def is_teacher(self) -> bool:
        return ROLE_TEACHER in self.codes

    @property
    def is_student(self) -> bool:
        return ROLE_STUDENT in self.codes

    def grade_ids(self) -> Optional[List[int]]:
        """可访问的年级 ID 列表；None 表示不受限。"""
        if self.is_super:
            return None
        ids: List[int] = []
        if self.is_grade_admin and self.user.grade_admin_grade_id:
            ids.append(self.user.grade_admin_grade_id)
        if self.user.grade_id:
            ids.append(self.user.grade_id)
        return ids or None

    def class_ids(self) -> Optional[List[int]]:
        """可访问的班级 ID 列表；None 表示不受限。

        教师仅能查看自己授课班级；学生仅本人所在班级。
        """
        if self.is_super:
            return None
        if self.is_grade_admin:
            return None  # 年级管理员：本年级所有数据
        if self.is_teacher:
            from app.models import TeachingAssignment

            rows = self.db.scalars(
                select(TeachingAssignment.class_id).where(
                    TeachingAssignment.teacher_id == self.user.id,
                    TeachingAssignment.is_active.is_(True),
                )
            ).all()
            ids = [r for r in rows if r]
            if self.user.klass and self.user.class_id:  # noqa: E501 班主任
                ids.append(self.user.class_id)
            return list(set(ids))
        # 学生：仅本人所在班级
        return [self.user.class_id] if self.user.class_id else []

    def student_ids(self) -> Optional[List[int]]:
        """可访问的学生 ID 列表；None 表示不受限。"""
        if self.is_super or self.is_grade_admin:
            return None
        if self.is_teacher:
            class_ids = self.class_ids() or []
            if not class_ids:
                return []
            from app.models import User as U

            return list(
                self.db.scalars(select(U.id).where(U.class_id.in_(class_ids))).all()
            )
        return [self.user.id]


def get_data_scope(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> DataScope:
    """数据权限依赖。"""
    return DataScope(user, db)


def has_perm(user: User, perm_code: str) -> bool:
    """判断用户是否拥有指定权限点。"""
    if ROLE_SYS_ADMIN in user.role_codes:
        return True
    for role in user.roles:
        for p in role.permissions:
            if p.code == perm_code:
                return True
    return False


def require_perm(*perm_codes: str):
    """权限点校验依赖工厂。"""

    def _checker(user: User = Depends(get_current_user)) -> User:
        if not any(has_perm(user, c) for c in perm_codes):
            raise PermissionException(f"缺少权限：{' 或 '.join(perm_codes)}")
        return user

    return _checker


def get_client_ip(request: Request) -> str:
    """获取真实客户端 IP（兼容 Nginx 反代）。"""
    xff = request.headers.get("X-Forwarded-For")
    if xff:
        return xff.split(",")[0].strip()
    return request.headers.get("X-Real-IP") or (request.client.host if request.client else "unknown")


def get_user_agent(request: Request) -> str:
    ua = request.headers.get("User-Agent", "")
    os_name = "Windows"
    for token, name in [("Windows", "Windows"), ("Android", "Android"), ("iPhone", "iOS"),
                        ("Mac OS", "macOS"), ("Linux", "Linux")]:
        if token in ua:
            os_name = name
            break
    browser = "Unknown"
    for token, name in [("Edg", "Edge"), ("Chrome", "Chrome"), ("Firefox", "Firefox"),
                        ("Safari", "Safari"), ("360", "360浏览器")]:
        if token in ua:
            browser = name
            break
    return f"{browser} / {os_name}"
