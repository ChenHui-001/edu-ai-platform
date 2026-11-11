"""试卷导出异步化（F-05）：文件落盘、短时效下载、过期清理。

## 为什么导出值得异步

导出是**自包含的重活**：`_build_preview` 要把整卷（题干、选项、答案、解析、
大题结构）拉齐再渲染，PDF 路径上大卷实测数十秒。同步端点把它整个压在
一个 HTTP 请求里，三个后果都是真出现过的：

1. 反代/网关读到一半就断，前端拿到的是「下载失败」而不是「还在跑」——
   用户重试一次就多跑一次渲染，越急越慢；
2. 单 worker 部署下（本项目的硬约束），一个渲染中的请求会占住工作线程，
   其它接口一起排队；
3. 没有任何进度可言，用户无法区分「在渲染」与「卡死了」。

改成「提交任务 → 轮询状态 → 短时效链接下载」，与组卷/教案共用
`sys_agent_job`，**不新增表、不引队列、不引 Redis**。

## 文件落在哪、活多久

写 `settings.EXPORT_DIR`（容器内 `/app/data/exports`，命名卷）。文件名带
job_id 与随机后缀，不可枚举。**30 分钟过期**：过期后下载接口回 410，
磁盘文件由下一次导出任务顺手清理。

刻意不引调度任务：为了清临时文件多一条 cron，就把「定时任务注册表」这个
需要人工对齐的地方又多扩一格（见 `tools/check_job_handlers.py` 的由来）。

## 为什么不复用 `sys_attachment`

`sys_attachment` 是「用户上传 / 业务附件」的登记表，带 `is_temp`、`biz_type`
与上传者语义。导出产物是**可再生成的中间物**：登记进去会让附件管理页出现
一堆用户从没上传过的文件，也会被 `is_temp` 清理任务按另一套规则误删。
"""
import os
import secrets
from datetime import timedelta
from typing import Any, Dict, Optional, Tuple

from fastapi import HTTPException

from app.core.config import settings
from app.core.logger import get_logger
from app.models import AgentJob
from app.services import agent_job_state
from app.utils.common import now_local

logger = get_logger("export_job")

EXPORT_JOB_AGENT = "paper_export"

KIND_DOCX = "docx"
KIND_PDF = "pdf"
KIND_ANSWER_SHEET = "answer_sheet"
KINDS = (KIND_DOCX, KIND_PDF, KIND_ANSWER_SHEET)

MEDIA_TYPES = {
    KIND_DOCX: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    KIND_PDF: "application/pdf",
    KIND_ANSWER_SHEET: "application/pdf",
}

EXTENSIONS = {KIND_DOCX: "docx", KIND_PDF: "pdf", KIND_ANSWER_SHEET: "pdf"}

# 下载链接有效期。够用户读完提示、点下载、断点重试；又不至于让
# `data/exports` 变成一个长期留档（导出物随时可再生成，没有存档价值）。
TTL_MINUTES = 30

DOWNLOAD_URL_TPL = "/question/papers/export/jobs/{job_id}/file"


def options_for(kind: str, mode: str = "teacher", layout: str = "a4_single",
                with_seal_line: bool = True,
                with_page_number: bool = True) -> Dict[str, Any]:
    """把导出参数规范成落库 JSON。

    答题卡没有教师卷/学生卷之分，也没有密封线页码 —— 但仍然记 `mode`，
    因为「提交时传了什么」要原样可复现，否则同一份 job 重跑可能出不同文件。
    """
    if kind not in KINDS:
        raise ValueError(f"不支持的导出类型：{kind}")
    return {
        "kind": kind,
        "mode": mode if kind != KIND_ANSWER_SHEET else "student",
        "layout": layout,
        "with_seal_line": bool(with_seal_line),
        "with_page_number": bool(with_page_number),
    }


def _export_dir() -> str:
    path = os.path.abspath(settings.EXPORT_DIR)
    os.makedirs(path, exist_ok=True)
    return path


def target_path(job_id: int, kind: str) -> Tuple[str, str]:
    """返回 `(绝对路径, 下载文件名)`。

    磁盘名带随机后缀（防枚举 + 防同名覆盖），下载名保持业务可读
    （老师收到的附件应该叫 `paper_12_teacher.docx`，不是一串哈希）。
    """
    ext = EXTENSIONS.get(kind, "bin")
    disk_name = f"job{int(job_id)}_{secrets.token_hex(6)}.{ext}"
    return os.path.join(_export_dir(), disk_name), f"paper_export_{job_id}.{ext}"


def write_file(job_id: int, kind: str, data: bytes,
               filename: Optional[str] = None) -> Dict[str, Any]:
    """把渲染结果落盘，返回可直接塞进 `job.result` 的结果体。"""
    path, disk_download_name = target_path(job_id, kind)
    with open(path, "wb") as f:
        f.write(data)
    return {
        "kind": kind,
        "file": os.path.basename(path),
        "filename": filename or disk_download_name,
        "size": len(data),
        "media_type": MEDIA_TYPES.get(kind, "application/octet-stream"),
        "expires_at": expires_at().isoformat(timespec="seconds"),
        "download_url": DOWNLOAD_URL_TPL.format(job_id=int(job_id)),
    }


def expires_at():
    return now_local() + timedelta(minutes=TTL_MINUTES)


def _result_dict(job: AgentJob) -> Dict[str, Any]:
    import json

    if not job or not job.result:
        return {}
    try:
        data = json.loads(job.result)
    except (TypeError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def resolve_download(job_id: int, user, db) -> Tuple[str, str, str]:
    """校验并定位下载文件，返回 `(绝对路径, 下载文件名, media_type)`。

    四道校验缺一不可：任务存在且是导出任务、**属主本人**（或超管）、
    已完成、未过期。少任何一道，`/export/jobs/{id}/file` 就变成一条
    「猜 id 就能拿别人卷子」的通道 —— 试卷里含答案，这是实打实的泄露。
    """
    job = db.get(AgentJob, int(job_id))
    if not job or job.agent != EXPORT_JOB_AGENT:
        raise HTTPException(status_code=404, detail="导出任务不存在")
    if job.user_id != user.id and "sys_admin" not in getattr(user, "role_codes", []):
        raise HTTPException(status_code=403, detail="无权下载该导出文件")

    status = agent_job_state.effective_status(
        job.status, job.created_at,
        timeout_seconds=agent_job_state.timeout_for(job.agent))
    if status != agent_job_state.STATUS_SUCCEEDED:
        raise HTTPException(status_code=409, detail=f"任务尚未完成（当前 {status}）")

    res = _result_dict(job)
    file_name = str(res.get("file") or "")
    if not file_name:
        raise HTTPException(status_code=404, detail="导出结果已失效，请重新导出")

    path = os.path.join(_export_dir(), os.path.basename(file_name))
    # 目录穿越双保险：`basename` 已经挡掉 `/`，这里再确认落在导出目录内
    if not os.path.abspath(path).startswith(_export_dir() + os.sep):
        raise HTTPException(status_code=400, detail="非法的导出文件路径")
    if not os.path.exists(path):
        raise HTTPException(status_code=410, detail="导出文件已过期，请重新导出")

    finished = job.finished_at or job.created_at
    if finished and now_local() > finished + timedelta(minutes=TTL_MINUTES):
        raise HTTPException(status_code=410, detail="导出文件已过期，请重新导出")

    return path, str(res.get("filename") or file_name), \
        str(res.get("media_type") or "application/octet-stream")


def cleanup_expired(db) -> int:
    """删除过期导出文件，返回删除个数。

    只删**文件**、保留 job 行：任务记录是「导出过什么」的溯源，删掉会让
    用户看到一条 succeeded 但点下载直接 404 的任务，比看一条过期任务更困惑。
    """
    from sqlalchemy import select

    cutoff = now_local() - timedelta(minutes=TTL_MINUTES)
    rows = db.scalars(
        select(AgentJob).where(
            AgentJob.agent == EXPORT_JOB_AGENT,
            AgentJob.finished_at.isnot(None),
            AgentJob.finished_at < cutoff,
        ).limit(200)
    ).all()
    removed = 0
    for job in rows:
        name = str(_result_dict(job).get("file") or "")
        if not name:
            continue
        path = os.path.join(_export_dir(), os.path.basename(name))
        try:
            if os.path.exists(path):
                os.remove(path)
                removed += 1
        except OSError as exc:  # 文件被占用/权限问题不该让导出失败
            logger.warning(f"清理过期导出文件失败 {path}: {exc}")
    if removed:
        logger.info(f"清理过期导出文件 {removed} 个")
    return removed
