"""试卷访问控制 —— 可见性条件与共享权限判定（全仓唯一真源）。

自 `api/v1/paper_compose.py` 下沉（Q-05：拆分超大路由文件）。这些判定被
`question.py`（试卷列表/详情）、`task.py`（提交可见性）、`paper_ai.py` 复用，
必须只有一份实现，避免「列表看不到、详情能打开」的越权漂移。

保留原有的下划线命名：调用方（含跨模块 `from app.api.v1.paper_compose import
_paper_visibility_clause / _assert_readable`）通过 paper_compose 的同名再导出
继续工作，行为与迁移前完全一致。
"""
from typing import Optional

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.core.exception import PermissionException
from app.models import Paper, PaperShare, SharePermission, ShareScope, User


def _is_sys_admin(user: User) -> bool:
    return "sys_admin" in (user.role_codes or [])


def _is_grade_admin(user: User) -> bool:
    return "grade_admin" in (user.role_codes or [])


def _scope_clause(user: User):
    """范围共享的可见性条件（grade / school / public）。

    **年级共享必须限定同年级**：只判断 `share_scope == 'grade'` 会让全校
    甚至跨年级的教师都看到该卷（实测七年级数学卷出现在九年级教师列表）。
    school 共享按「创建者学校 == 查看者学校」判断（库内无学校实体表，
    只能文本比对 `sys_user.school_name`）；任一为空则不匹配——
    宁可看不到，也不要错误放行全校。
    """
    clauses = [Paper.share_scope == ShareScope.PUBLIC.value]
    if user.grade_id:
        clauses.append(and_(
            Paper.share_scope == ShareScope.GRADE.value,
            Paper.grade_id == user.grade_id,
        ))
    if user.school_name:
        creator_ids = select(User.id).where(User.school_name == user.school_name)
        clauses.append(and_(
            Paper.share_scope == ShareScope.SCHOOL.value,
            Paper.creator_id.in_(creator_ids),
        ))
    return or_(*clauses)


def _legacy_shared_clause(user: User):
    """存量兼容：`is_shared=True` 且 `share_scope` 仍是默认 private 的老卷。

    这类卷由旧接口 `/papers/{id}/share` 产生，语义是「共享给同科教师」。
    旧可见性实现只要 `is_shared` 为真就放行**所有人**（跨年级、跨学科都能读到
    标准答案）。这里收窄为**同年级**可见：既贴合「同科」原意，又不再越界。
    返回 None 表示该用户无年级信息、不适用本条。
    """
    if not user.grade_id:
        return None
    return and_(
        Paper.is_shared.is_(True),
        Paper.share_scope == ShareScope.PRIVATE.value,
        Paper.grade_id == user.grade_id,
    )


def _paper_visibility_clause(user: User):
    """可见性：sys_admin 全量；其他 = 本人 / 被显式分享 / 范围共享 / 存量共享。

    **这是全仓唯一的试卷可见性判定**：`question.py` 的试卷列表与详情、
    试卷库分类、导出校验全部复用本函数，避免两套条件漂移出
    「列表看不到但详情能打开」的越权。
    """
    if _is_sys_admin(user):
        return None
    clauses = [
        Paper.creator_id == user.id,
        Paper.id.in_(select(PaperShare.paper_id).where(
            PaperShare.to_user_id == user.id)),
        _scope_clause(user),
    ]
    legacy = _legacy_shared_clause(user)
    if legacy is not None:
        clauses.append(legacy)
    return or_(*clauses)


def _share_permission(db: Session, paper: Paper, user: User) -> Optional[str]:
    """当前用户对该卷的共享权限（view/reuse/edit）；无权限返回 None。

    优先级：创建者/管理员 = edit > 显式分享记录 > 范围共享（只读）。
    范围共享一律只读：同年级几十位教师都能改同一份卷子会互相破坏。
    """
    if _is_sys_admin(user) or paper.creator_id == user.id:
        return SharePermission.EDIT.value
    share = db.scalar(
        select(PaperShare).where(
            PaperShare.paper_id == paper.id, PaperShare.to_user_id == user.id)
    )
    if share:
        return share.permission or SharePermission.VIEW.value
    # 范围共享必须逐级校验归属，不能只看 share_scope 就放行
    if paper.share_scope == ShareScope.PUBLIC.value:
        return SharePermission.VIEW.value
    if paper.share_scope == ShareScope.GRADE.value and \
            user.grade_id and paper.grade_id == user.grade_id:
        return SharePermission.VIEW.value
    if paper.share_scope == ShareScope.SCHOOL.value and user.school_name:
        creator_school = db.scalar(
            select(User.school_name).where(User.id == paper.creator_id))
        if creator_school and creator_school == user.school_name:
            return SharePermission.VIEW.value
    return None


def _assert_readable(db: Session, paper: Paper, user: User) -> str:
    perm = _share_permission(db, paper, user)
    if not perm:
        raise PermissionException("无权查看该试卷")
    return perm


def _assert_can_edit(db: Session, paper: Paper, user: User) -> None:
    """编辑权：创建者 / sys_admin / 被授予 edit 的分享对象。"""
    perm = _share_permission(db, paper, user)
    if perm != SharePermission.EDIT.value:
        raise PermissionException("只能编辑自己创建的试卷，或经授权的共享试卷")
