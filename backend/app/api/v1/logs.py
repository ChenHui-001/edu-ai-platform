"""日志审计与定时任务管理接口。"""
import io
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, Query
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from sqlalchemy import desc, func, or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin, get_current_manager, get_current_user
from app.core.database import get_db
from app.core.exception import BusinessException, NotFoundException
from app.models import (
    ErrorLog, JobExecutionLog, LoginLog, OperationLog, ScheduledJob, User,
)
from app.utils.common import PageParams, dictify, ok, utcnow

router = APIRouter(prefix="/logs", tags=["日志与任务"])


# ---------------------------------------------------------------- 登录日志
@router.get("/login", summary="登录日志")
def login_logs(
    params: PageParams = Depends(), keyword: Optional[str] = None,
    status: Optional[str] = None, is_abnormal: Optional[bool] = None,
    start_date: Optional[str] = None, end_date: Optional[str] = None,
    db: Session = Depends(get_db), _: User = Depends(get_current_manager),
):
    stmt = select(LoginLog)
    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where(or_(LoginLog.username.like(like), LoginLog.ip.like(like)))
    if status:
        stmt = stmt.where(LoginLog.status == status)
    if is_abnormal is not None:
        stmt = stmt.where(LoginLog.is_abnormal.is_(is_abnormal))
    if start_date:
        stmt = stmt.where(LoginLog.login_at >= start_date)
    if end_date:
        stmt = stmt.where(LoginLog.login_at <= f"{end_date} 23:59:59")

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(
        stmt.order_by(desc(LoginLog.login_at))
        .offset(params.offset).limit(params.page_size)
    ).all()
    return ok({"items": [dictify(r) for r in rows], "total": total, "page": params.page})


# ---------------------------------------------------------------- 操作日志
@router.get("/operation", summary="操作日志")
def operation_logs(
    params: PageParams = Depends(), module: Optional[str] = None,
    username: Optional[str] = None, status: Optional[str] = None,
    start_date: Optional[str] = None, end_date: Optional[str] = None,
    db: Session = Depends(get_db), _: User = Depends(get_current_manager),
):
    stmt = select(OperationLog)
    if module:
        stmt = stmt.where(OperationLog.module == module)
    if username:
        stmt = stmt.where(OperationLog.username.like(f"%{username}%"))
    if status:
        stmt = stmt.where(OperationLog.status == status)
    if start_date:
        stmt = stmt.where(OperationLog.created_at >= start_date)
    if end_date:
        stmt = stmt.where(OperationLog.created_at <= f"{end_date} 23:59:59")

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(
        stmt.order_by(desc(OperationLog.created_at))
        .offset(params.offset).limit(params.page_size)
    ).all()
    modules = [m for (m,) in db.execute(
        select(OperationLog.module).distinct()
    ).all()]
    return ok({
        "items": [dictify(r) for r in rows], "total": total,
        "page": params.page, "modules": modules,
    })


# ---------------------------------------------------------------- 错误日志
@router.get("/error", summary="错误日志")
def error_logs(
    params: PageParams = Depends(), level: Optional[str] = None,
    start_date: Optional[str] = None, end_date: Optional[str] = None,
    db: Session = Depends(get_db), _: User = Depends(get_current_manager),
):
    stmt = select(ErrorLog)
    if level:
        stmt = stmt.where(ErrorLog.level == level)
    if start_date:
        stmt = stmt.where(ErrorLog.created_at >= start_date)
    if end_date:
        stmt = stmt.where(ErrorLog.created_at <= f"{end_date} 23:59:59")

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(
        stmt.order_by(desc(ErrorLog.created_at))
        .offset(params.offset).limit(params.page_size)
    ).all()
    return ok({"items": [dictify(r) for r in rows], "total": total, "page": params.page})


# ---------------------------------------------------------------- 导出
@router.get("/export", summary="导出日志为 Excel")
def export_logs(
    log_type: str = Query("login", description="login/operation/error"),
    db: Session = Depends(get_db), _: User = Depends(get_current_manager),
):
    wb = Workbook()
    ws = wb.active

    if log_type == "login":
        ws.title = "登录日志"
        ws.append(["账号", "登录时间", "IP", "设备", "状态", "信息", "异常"])
        for r in db.scalars(select(LoginLog).order_by(desc(LoginLog.login_at)).limit(10000)).all():
            ws.append([r.username, dictify(r.login_at), r.ip, r.device, r.status,
                       r.message, "是" if r.is_abnormal else "否"])
    elif log_type == "operation":
        ws.title = "操作日志"
        ws.append(["操作人", "模块", "操作", "方法", "路径", "IP", "状态", "耗时(ms)", "时间"])
        for r in db.scalars(
            select(OperationLog).order_by(desc(OperationLog.created_at)).limit(10000)
        ).all():
            ws.append([r.username, r.module, r.action, r.method, r.path, r.ip,
                       r.status, r.duration_ms, dictify(r.created_at)])
    else:
        ws.title = "错误日志"
        ws.append(["级别", "模块", "路径", "信息", "时间"])
        for r in db.scalars(select(ErrorLog).order_by(desc(ErrorLog.created_at)).limit(10000)).all():
            ws.append([r.level, r.module, r.path, r.message, dictify(r.created_at)])

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return StreamingResponse(
        buf, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={log_type}_logs.xlsx"},
    )


# ---------------------------------------------------------------- 定时任务
jobs_router = APIRouter(prefix="/jobs", tags=["定时任务"])


@jobs_router.get("", summary="任务列表")
def list_jobs(
    params: PageParams = Depends(), is_active: Optional[bool] = None,
    db: Session = Depends(get_db), _: User = Depends(get_current_admin),
):
    stmt = select(ScheduledJob)
    if is_active is not None:
        stmt = stmt.where(ScheduledJob.is_active.is_(is_active))
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(
        stmt.order_by(ScheduledJob.id).offset(params.offset).limit(params.page_size)
    ).all()
    return ok({"items": [dictify(r) for r in rows], "total": total, "page": params.page})


@jobs_router.post("", summary="新增自定义任务")
def create_job(
    data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    from app.services.task_jobs import JOB_HANDLERS

    if not data.get("name") or not data.get("cron_expression"):
        raise BusinessException("任务名称和 Cron 表达式不能为空")
    if data.get("func_path") not in JOB_HANDLERS:
        raise BusinessException(
            f"执行逻辑标识无效，可用值：{'、'.join(JOB_HANDLERS.keys())}"
        )
    if not _valid_cron(data["cron_expression"]):
        raise BusinessException("Cron 表达式格式错误（需 5 段：分 时 日 月 周）")

    job = ScheduledJob(
        name=data["name"], description=data.get("description"),
        func_path=data["func_path"], cron_expression=data["cron_expression"],
        is_builtin=False, is_active=bool(data.get("is_active", True)),
        retry_times=int(data.get("retry_times", 2)),
    )
    db.add(job)
    db.commit()

    from app.services.scheduler import add_job

    if job.is_active:
        add_job(job)
    return ok(dictify(job), message="任务创建成功")


@jobs_router.put("/{job_id}", summary="编辑任务")
def update_job(
    job_id: int, data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    job = db.get(ScheduledJob, job_id)
    if not job:
        raise NotFoundException("任务不存在")
    if "cron_expression" in data:
        if not _valid_cron(data["cron_expression"]):
            raise BusinessException("Cron 表达式格式错误")
        job.cron_expression = data["cron_expression"]
    for f in ("name", "description", "retry_times"):
        if f in data:
            setattr(job, f, data[f])

    from app.services.scheduler import add_job, remove_job

    remove_job(job_id)
    db.commit()
    if job.is_active:
        add_job(job)
    return ok(dictify(job), message="任务已更新")


@jobs_router.put("/{job_id}/toggle", summary="启用 / 停用任务")
def toggle_job(
    job_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_admin),
):
    job = db.get(ScheduledJob, job_id)
    if not job:
        raise NotFoundException("任务不存在")
    job.is_active = not job.is_active

    from app.services.scheduler import add_job, remove_job

    if job.is_active:
        add_job(job)
    else:
        remove_job(job_id)
    db.commit()
    return ok({"is_active": job.is_active}, message="已启用" if job.is_active else "已停用")


@jobs_router.post("/{job_id}/run", summary="手动执行任务")
def run_job_now(
    job_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_admin),
):
    from app.services.scheduler import run_job_now as _run

    try:
        result = _run(job_id)
        return ok(result, message="任务执行成功")
    except Exception as exc:
        raise BusinessException(f"任务执行失败：{exc}")


@jobs_router.delete("/{job_id}", summary="删除任务")
def delete_job(
    job_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_admin),
):
    job = db.get(ScheduledJob, job_id)
    if not job:
        raise NotFoundException("任务不存在")
    if job.is_builtin:
        raise BusinessException("内置任务不可删除，可选择停用")

    from app.services.scheduler import remove_job

    remove_job(job_id)
    db.delete(job)
    db.commit()
    return ok(message="任务已删除")


@jobs_router.get("/status", summary="调度器状态")
def scheduler_status(_: User = Depends(get_current_admin)):
    from app.services.scheduler import scheduler_status as _status

    return ok(_status())


@jobs_router.get("/{job_id}/executions", summary="任务执行记录")
def job_executions(
    job_id: int, params: PageParams = Depends(), db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    stmt = select(JobExecutionLog).where(JobExecutionLog.job_id == job_id)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(
        stmt.order_by(desc(JobExecutionLog.started_at))
        .offset(params.offset).limit(params.page_size)
    ).all()
    return ok({"items": [dictify(r) for r in rows], "total": total, "page": params.page})


def _valid_cron(expr: str) -> bool:
    parts = expr.split()
    if len(parts) != 5:
        return False
    return all(p == "*" or _valid_field(p) for p in parts)


def _valid_field(field: str) -> bool:
    import re

    return bool(re.fullmatch(r"[\d\*\-,/]+", field))
