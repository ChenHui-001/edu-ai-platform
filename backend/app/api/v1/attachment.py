"""附件管理接口：上传、预览、下载、删除。"""
import hashlib
import os
import threading
import uuid
from typing import Any, Dict, List, Optional
from urllib.parse import quote

from fastapi import APIRouter, Body, Depends, File, Form, Request, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.api.deps import get_client_ip, get_current_teacher, get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.core.exception import BusinessException, NotFoundException, PermissionException
from app.models import Attachment, User
from app.utils.common import PageParams, dictify, now_local, ok

router = APIRouter(prefix="/attachments", tags=["附件管理"])

# 匿名上传限流桶：{ip: [时间戳]}，仅用于注册证明材料，进程内即可
_PUBLIC_UPLOAD_HITS: Dict[str, List] = {}
_PUBLIC_UPLOAD_LOCK = threading.Lock()

PREVIEW_TYPES = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".pdf"}
OFFICE_TYPES = {".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx"}


def _assert_attachment_visible(db: Session, att: Attachment, user: User) -> None:
    """附件读取授权：上传者本人 / 管理端 / 共享教案的同科教师。

    此前预览与下载只校验登录态，遍历自增 id 即可下载任意附件
    （包括匿名上传的注册证明材料、他人教案课件），属于水平越权。
    """
    codes = set(user.role_codes or [])
    if "sys_admin" in codes:
        return
    if att.uploader_id is not None and att.uploader_id == user.id:
        return

    if att.biz_type == "knowledge_point" and att.biz_id:
        from app.models import KnowledgePoint

        kp = db.get(KnowledgePoint, att.biz_id)
        if not kp or not kp.is_active:
            raise PermissionException("无权查看该附件")
        is_student = getattr(user, "identity", "") == "student" or "student" in codes
        if is_student:
            # 学生只能看本年级、已发布知识点下、且显式标记学生可见的附件
            if (kp.status == "published" and user.grade_id == kp.grade_id
                    and att.visible_to_student):
                return
            raise PermissionException("无权查看该附件")
        # 教师/年级管理员：已发布知识点附件可读；草稿/归档仅管理端可读
        if kp.status == "published":
            return
        if {"sys_admin", "grade_admin"} & codes:
            return
        raise PermissionException("无权查看该附件")

    if att.biz_type == "lesson_plan" and att.biz_id:
        from app.models import LessonPlan, TeachingAssignment

        plan = db.get(LessonPlan, att.biz_id)
        if plan:
            if plan.creator_id == user.id:
                return
            if plan.is_shared:
                subject_ids = set(db.scalars(
                    select(TeachingAssignment.subject_id).where(
                        TeachingAssignment.teacher_id == user.id,
                        TeachingAssignment.is_active.is_(True),
                    )
                ).all())
                if plan.subject_id in subject_ids:
                    return

    # 匿名上传（注册证明材料等）与无法归属的业务附件：仅管理端可读
    if att.uploader_id is None and ({"sys_admin", "grade_admin"} & codes):
        return
    raise PermissionException("无权查看该附件")


@router.post("/public-upload", summary="注册证明材料上传（匿名，仅图片）")
async def public_upload(
    file: UploadFile = File(...), db: Session = Depends(get_db),
    request: Request = None,
):
    """注册页在**未登录**状态上传证明材料。

    原先注册页复用 /attachments/upload（需登录）→ 401，证明材料永远传不上去。
    此处做严格收敛，避免变成公开图床：
      - 仅允许图片类型（jpg/jpeg/png/webp/gif），不接受 pdf/office
      - 单文件上限 min(MAX_UPLOAD_SIZE, 5MB)
      - uploader_id 留空、is_temp=True（由定时任务清理）
      - 同一 IP 10 分钟内最多 10 次
    """
    ip = get_client_ip(request) if request is not None else "unknown"
    now = now_local()
    with _PUBLIC_UPLOAD_LOCK:
        bucket = _PUBLIC_UPLOAD_HITS.setdefault(ip, [])
        bucket[:] = [t for t in bucket if (now - t).total_seconds() < 600]
        if len(bucket) >= 10:
            raise BusinessException("上传过于频繁，请 10 分钟后再试")
        bucket.append(now)

    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
        raise BusinessException("证明材料仅支持 jpg/png/webp/gif 图片")

    content = await file.read()
    max_bytes = min(settings.MAX_UPLOAD_SIZE, 5) * 1024 * 1024
    if len(content) > max_bytes:
        raise BusinessException(f"文件大小超过限制（{max_bytes // 1024 // 1024}MB）")
    if not content:
        raise BusinessException("文件为空")

    digest = hashlib.md5(content).hexdigest()[:12]
    stored_name = f"{uuid.uuid4().hex}_{digest}{ext}"
    day_dir = now_local().strftime("%Y%m%d")
    dir_path = os.path.join(settings.UPLOAD_DIR, day_dir)
    os.makedirs(dir_path, exist_ok=True)
    full_path = os.path.abspath(os.path.join(dir_path, stored_name))
    if not full_path.startswith(os.path.abspath(settings.UPLOAD_DIR)):
        raise BusinessException("非法文件路径")
    with open(full_path, "wb") as f:
        f.write(content)

    att = Attachment(
        filename=file.filename, stored_name=stored_name, file_path=full_path,
        file_size=len(content), file_type=file.content_type,
        category="register", biz_type="register", biz_id=None,
        uploader_id=None, is_temp=True,
    )
    db.add(att)
    db.commit()
    db.refresh(att)
    return ok({"id": att.id, "filename": att.filename, "size": att.file_size},
              message="上传成功")


@router.post("/upload", summary="上传附件")
async def upload(
    file: UploadFile = File(...), category: str = Form("common"),
    biz_type: Optional[str] = Form(None), biz_id: Optional[int] = Form(None),
    db: Session = Depends(get_db), user: User = Depends(get_current_teacher),
):
    # 上传属于教师/管理端能力：此前只校验登录，学生账号也能上传任意文件，
    # 与学生端「只能提交文本作答/学习数据」的权限模型不符。
    # 绑定业务对象时校验归属：避免绕过 lesson.py 的专用端点把附件挂到
    # 他人教案下（列表按 biz_type+biz_id 聚合，会直接暴露）。
    # 与 PUT /{id}/bind 共用同一份判定，防止两处漂移。
    _assert_biz_owned(db, biz_type, biz_id, user)
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in settings.ALLOWED_UPLOAD_TYPES:
        raise BusinessException(
            f"不支持的文件类型 {ext}，允许：{'、'.join(settings.ALLOWED_UPLOAD_TYPES)}"
        )

    content = await file.read()
    max_bytes = settings.MAX_UPLOAD_SIZE * 1024 * 1024
    if len(content) > max_bytes:
        raise BusinessException(f"文件大小超过限制（{settings.MAX_UPLOAD_SIZE}MB）")

    # 文件名加密存储，防路径遍历与重名覆盖
    digest = hashlib.md5(content).hexdigest()[:12]
    stored_name = f"{uuid.uuid4().hex}_{digest}{ext}"
    day_dir = now_local().strftime("%Y%m%d")
    dir_path = os.path.join(settings.UPLOAD_DIR, day_dir)
    os.makedirs(dir_path, exist_ok=True)

    full_path = os.path.abspath(os.path.join(dir_path, stored_name))
    # 双保险：确保写入路径在上传目录内
    if not full_path.startswith(os.path.abspath(settings.UPLOAD_DIR)):
        raise BusinessException("非法文件路径")
    with open(full_path, "wb") as f:
        f.write(content)

    att = Attachment(
        filename=file.filename, stored_name=stored_name, file_path=full_path,
        file_size=len(content), file_type=file.content_type,
        category=category, biz_type=biz_type, biz_id=biz_id, uploader_id=user.id,
        is_temp=not biz_id,
    )
    db.add(att)
    db.commit()
    db.refresh(att)

    return ok({
        "id": att.id, "filename": att.filename, "size": att.file_size,
        "ext": ext, "previewable": ext in PREVIEW_TYPES or ext in OFFICE_TYPES,
        "url": f"/api/v1/attachments/{att.id}/preview",
        "download_url": f"/api/v1/attachments/{att.id}/download",
    }, message="上传成功")


@router.post("/batch", summary="批量上传")
async def batch_upload(
    files: List[UploadFile] = File(...), category: str = Form("common"),
    db: Session = Depends(get_db), user: User = Depends(get_current_teacher),
):
    results = []
    for f in files:
        try:
            ext = os.path.splitext(f.filename or "")[1].lower()
            if ext not in settings.ALLOWED_UPLOAD_TYPES:
                results.append({"filename": f.filename, "success": False, "reason": "类型不支持"})
                continue
            content = await f.read()
            if len(content) > settings.MAX_UPLOAD_SIZE * 1024 * 1024:
                results.append({"filename": f.filename, "success": False, "reason": "文件过大"})
                continue
            digest = hashlib.md5(content).hexdigest()[:12]
            stored_name = f"{uuid.uuid4().hex}_{digest}{ext}"
            day_dir = now_local().strftime("%Y%m%d")
            dir_path = os.path.join(settings.UPLOAD_DIR, day_dir)
            os.makedirs(dir_path, exist_ok=True)
            full_path = os.path.abspath(os.path.join(dir_path, stored_name))
            with open(full_path, "wb") as fp:
                fp.write(content)
            att = Attachment(
                filename=f.filename, stored_name=stored_name, file_path=full_path,
                file_size=len(content), file_type=f.content_type,
                category=category, uploader_id=user.id,
            )
            db.add(att)
            db.flush()
            results.append({"filename": f.filename, "success": True, "id": att.id})
        except Exception as exc:
            results.append({"filename": f.filename, "success": False, "reason": str(exc)})
    db.commit()
    ok_count = sum(1 for r in results if r["success"])
    return ok({"results": results, "success": ok_count}, message=f"成功上传 {ok_count} 个文件")


@router.get("", summary="附件列表")
def list_attachments(
    params: PageParams = Depends(), category: Optional[str] = None,
    biz_type: Optional[str] = None, biz_id: Optional[int] = None,
    keyword: Optional[str] = None, is_temp: Optional[bool] = None,
    db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    stmt = select(Attachment)
    if category:
        stmt = stmt.where(Attachment.category == category)
    if biz_type:
        stmt = stmt.where(Attachment.biz_type == biz_type)
    if biz_id:
        stmt = stmt.where(Attachment.biz_id == biz_id)
    # 页面上的「文件名」搜索框与「状态」下拉此前没有对应入参：
    # FastAPI 会静默忽略未声明的 query 参数，于是前端无论填什么都返回全量，
    # 表现为「搜索框是摆设」。这两个条件必须与前端 query 字段同名。
    if keyword:
        stmt = stmt.where(Attachment.filename.contains(keyword))
    if is_temp is not None:
        stmt = stmt.where(Attachment.is_temp.is_(is_temp))
    if "sys_admin" not in user.role_codes:
        stmt = stmt.where(Attachment.uploader_id == user.id)

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(
        stmt.order_by(desc(Attachment.created_at))
        .offset(params.offset).limit(params.page_size)
    ).all()
    items = []
    for a in rows:
        d = dictify(a)
        d.pop("file_path", None)
        ext = os.path.splitext(a.filename or "")[1].lower()
        d["ext"] = ext
        d["previewable"] = ext in PREVIEW_TYPES or ext in OFFICE_TYPES
        d["preview_url"] = f"/api/v1/attachments/{a.id}/preview"
        d["download_url"] = f"/api/v1/attachments/{a.id}/download"
        items.append(d)
    return ok({"items": items, "total": total, "page": params.page})


@router.get("/{att_id}/preview", summary="在线预览")
def preview(
    att_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    att = db.get(Attachment, att_id)
    if not att:
        raise NotFoundException("附件不存在")
    _assert_attachment_visible(db, att, user)
    if not os.path.exists(att.file_path):
        raise NotFoundException("文件已被清理")
    att.download_count += 1
    db.commit()

    ext = os.path.splitext(att.stored_name)[1].lower()
    media = {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
        ".gif": "image/gif", ".webp": "image/webp", ".pdf": "application/pdf",
    }.get(ext, "application/octet-stream")
    return FileResponse(
        att.file_path, media_type=media,
        headers={"Content-Disposition": f"inline; filename*=UTF-8''{quote(att.filename or 'attachment')}"},
    )


@router.get("/{att_id}/download", summary="下载附件")
def download(
    att_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    att = db.get(Attachment, att_id)
    if not att:
        raise NotFoundException("附件不存在")
    _assert_attachment_visible(db, att, user)
    if not os.path.exists(att.file_path):
        raise NotFoundException("文件已被清理")
    att.download_count += 1
    db.commit()
    return FileResponse(
        att.file_path, filename=att.filename, media_type="application/octet-stream",
    )


def _assert_biz_owned(
    db: Session, biz_type: Optional[str], biz_id: Optional[int], user: User,
) -> None:
    """校验附件要绑定的业务对象存在且属于当前用户。

    **上传与「转正」(PUT /{id}/bind) 必须共用这一份判定。**
    历史缺口：upload 校验了教案归属，但 bind 完全没有 ——
    先上传一个临时附件，再 bind 到他人的 biz_id，附件就会出现在
    他人教案的附件列表里（列表按 biz_type+biz_id 聚合）。
    """
    if not biz_type or not biz_id:
        return
    is_admin = "sys_admin" in (user.role_codes or [])
    if biz_type == "lesson_plan":
        from app.models import LessonPlan

        plan = db.get(LessonPlan, biz_id)
        if not plan:
            raise BusinessException("教案不存在")
        if plan.creator_id != user.id and not is_admin:
            raise PermissionException("只能绑定到自己的教案")
    elif biz_type == "knowledge_point":
        # 知识点附件属教研资料，读写权限由知识库端点单独判定；
        # 这里只拦「挂到不存在的 id」，避免产生悬空引用。
        from app.models import KnowledgePoint

        if not db.get(KnowledgePoint, biz_id):
            raise BusinessException("知识点不存在")
    elif biz_type != "register":
        raise BusinessException(f"不支持的绑定类型：{biz_type}")


@router.put("/{att_id}/bind", summary="绑定业务（转正式附件）")
def bind(
    att_id: int, data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    att = db.get(Attachment, att_id)
    if not att:
        raise NotFoundException("附件不存在")
    if att.uploader_id != user.id and "sys_admin" not in user.role_codes:
        raise PermissionException("无权操作该附件")
    biz_type = data.get("biz_type")
    biz_id = data.get("biz_id")
    _assert_biz_owned(db, biz_type, biz_id, user)
    att.biz_type = biz_type
    att.biz_id = biz_id
    att.is_temp = False
    db.commit()
    return ok(message="附件已绑定")


@router.delete("/{att_id}", summary="删除附件")
def delete(
    att_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    att = db.get(Attachment, att_id)
    if not att:
        raise NotFoundException("附件不存在")
    if att.uploader_id != user.id and "sys_admin" not in user.role_codes:
        raise PermissionException("无权删除该附件")
    try:
        if os.path.exists(att.file_path):
            os.remove(att.file_path)
    except OSError:
        pass
    db.delete(att)
    db.commit()
    return ok(message="附件已删除")
