"""用户、角色、权限、注册审批模型。"""
import enum
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.utils.common import utcnow


class UserStatus(str, enum.Enum):
    PENDING = "pending"        # 待审批
    ACTIVE = "active"          # 正常
    REJECTED = "rejected"      # 已驳回
    DISABLED = "disabled"      # 已禁用


class IdentityType(str, enum.Enum):
    STUDENT = "student"
    TEACHER = "teacher"
    GRADE_ADMIN = "grade_admin"
    SYS_ADMIN = "sys_admin"


class PermissionType(str, enum.Enum):
    MENU = "menu"        # 菜单权限
    BUTTON = "button"    # 操作权限
    DATA = "data"        # 数据权限


class User(Base):
    __tablename__ = "sys_user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True, comment="登录账号")
    password: Mapped[str] = mapped_column(String(255), comment="加盐哈希密码")
    real_name: Mapped[str] = mapped_column(String(64), index=True, comment="真实姓名")
    email: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, index=True)
    avatar: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    gender: Mapped[str] = mapped_column(String(8), default="unknown")

    identity: Mapped[str] = mapped_column(String(32), default=IdentityType.STUDENT.value, comment="身份类型")
    status: Mapped[str] = mapped_column(String(16), default=UserStatus.PENDING.value, index=True)

    school_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, comment="所属学校")
    grade_id: Mapped[Optional[int]] = mapped_column(ForeignKey("edu_grade.id", ondelete="SET NULL"), nullable=True, index=True)
    class_id: Mapped[Optional[int]] = mapped_column(ForeignKey("edu_class.id", ondelete="SET NULL"), nullable=True, index=True)
    grade_admin_grade_id: Mapped[Optional[int]] = mapped_column(ForeignKey("edu_grade.id", ondelete="SET NULL"), nullable=True, comment="年级管理员管辖年级")

    # 首次登录强制改密
    must_change_password: Mapped[bool] = mapped_column(Boolean, default=False)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_login_ip: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    login_fail_count: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    roles: Mapped[List["Role"]] = relationship(
        secondary="sys_user_role", back_populates="users", lazy="selectin"
    )
    grade: Mapped[Optional["Grade"]] = relationship(foreign_keys=[grade_id])
    klass: Mapped[Optional["Class"]] = relationship(foreign_keys=[class_id])

    @property
    def is_active(self) -> bool:
        return self.status == UserStatus.ACTIVE.value

    @property
    def role_codes(self) -> List[str]:
        return [r.code for r in self.roles]


class Role(Base):
    __tablename__ = "sys_role"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True, comment="角色编码")
    name: Mapped[str] = mapped_column(String(64), comment="角色名称")
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    # 数据权限范围：all / grade / taught_class / self
    data_scope: Mapped[str] = mapped_column(String(32), default="self", comment="数据权限范围")
    is_builtin: Mapped[bool] = mapped_column(Boolean, default=False, comment="内置角色不可删除")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    users: Mapped[List[User]] = relationship(secondary="sys_user_role", back_populates="roles")
    permissions: Mapped[List["Permission"]] = relationship(
        secondary="sys_role_permission", lazy="selectin"
    )


class Permission(Base):
    __tablename__ = "sys_permission"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(128), unique=True, index=True, comment="权限点编码")
    name: Mapped[str] = mapped_column(String(64))
    type: Mapped[str] = mapped_column(String(16), default=PermissionType.BUTTON.value)
    parent_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True, comment="树形父级")
    path: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment="前端路由")
    icon: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    sort: Mapped[int] = mapped_column(Integer, default=0)
    is_hidden: Mapped[bool] = mapped_column(Boolean, default=False)


class UserRole(Base):
    __tablename__ = "sys_user_role"
    __table_args__ = (UniqueConstraint("user_id", "role_id", name="uq_user_role"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("sys_user.id", ondelete="CASCADE"), index=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("sys_role.id", ondelete="CASCADE"), index=True)


class RolePermission(Base):
    __tablename__ = "sys_role_permission"
    __table_args__ = (UniqueConstraint("role_id", "permission_id", name="uq_role_perm"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("sys_role.id", ondelete="CASCADE"), index=True)
    permission_id: Mapped[int] = mapped_column(ForeignKey("sys_permission.id", ondelete="CASCADE"), index=True)


class Registration(Base):
    """注册申请：教师需教师资格证，学生需学生证/班级证明。"""

    __tablename__ = "sys_registration"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("sys_user.id", ondelete="CASCADE"), index=True)
    identity: Mapped[str] = mapped_column(String(32))
    # 证明材料附件 ID 列表（JSON 字符串）
    attachments: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="申请理由")

    status: Mapped[str] = mapped_column(String(16), default=UserStatus.PENDING.value, index=True)
    audit_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("sys_user.id", ondelete="SET NULL"), nullable=True)
    audit_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    audit_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


# 避免循环引用
from app.models.edu import Grade, Class  # noqa: E402,F401
