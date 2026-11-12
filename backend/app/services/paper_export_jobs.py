"""异步导出链路：任务状态维护 + 后台渲染（自 api/v1/paper_compose.py 下沉，Q-05）。

- `_requested_export`：取卷并做可读性校验（导出权限在提交时校验）。
- `_run_export_job`：后台线程渲染 docx/pdf/答题卡并写文件（独立 Session）。
- `_touch_job` / `_fail_job` / `_cancelled_job`：`sys_agent_job` 状态更新助手，
  导出与组卷两条异步链路共用（进度写失败只记日志，不影响主任务）。

调用方（paper_compose 的同步导出端点、`create_export_job` 的后台线程、组卷
任务的 `_touch_job` 等）经 paper_compose 的同名再导出继续工作，行为不变。
"""
import json
import logging
from typing import Any

from sqlalchemy.orm import Session

from app.core.exception import BusinessException, NotFoundException
from app.models import Paper, User
from app.services import agent_job_state, export_job
from app.services.paper_access import _assert_readable
from app.services.paper_export_service import (
    build_answer_sheet, build_docx, build_pdf,
)
from app.services.paper_items import _build_preview
from app.utils.common import now_local

logger = logging.getLogger(__name__)


def _touch_job(job_id: int, **fields: Any) -> None:
    """用独立 Session 更新任务状态（后台线程 / 请求线程不能共用 Session）。

    进度写失败不影响组卷本身 —— 只是前端看不到最新百分比，不该让整个任务
    因此失败，所以异常只记日志。
    """
    from app.core.database import SessionLocal
    from app.models import AgentJob

    db = SessionLocal()
    try:
        job = db.get(AgentJob, job_id)
        if not job:
            return
        for key, value in fields.items():
            setattr(job, key, value)
        db.commit()
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"更新组卷任务 {job_id} 状态失败: {exc}")
    finally:
        db.close()


def _fail_job(job_id: int, message: str) -> None:
    _touch_job(job_id, status=agent_job_state.STATUS_FAILED, error=message[:2000],
               finished_at=now_local())


def _cancelled_job(job_id: int) -> None:
    """把任务落成 `cancelled`（F-04）。

    与 `_fail_job` 分开：取消不是故障，`error` 留空、`progress` 停在原位，
    否则前端会把"你点了取消"渲染成红色错误，也会污染任务成功率统计。
    """
    _touch_job(job_id, status=agent_job_state.STATUS_CANCELLED, stage="已取消",
               error=None, finished_at=now_local())


def _requested_export(db: Session, paper_id: int, user: User) -> Paper:
    paper = db.get(Paper, paper_id)
    if not paper:
        raise NotFoundException("试卷不存在")
    _assert_readable(db, paper, user)
    return paper


def _run_export_job(job_id: int) -> None:
    """后台渲染导出文件。独立 Session —— 请求一结束原来的就关了。"""
    from app.core.database import SessionLocal
    from app.models import AgentJob

    db = SessionLocal()
    try:
        job = db.get(AgentJob, job_id)
        if not job:
            return
        params = json.loads(job.params or "{}")
        job.status = agent_job_state.STATUS_RUNNING[1]
        job.started_at = now_local()
        job.progress = 10
        job.stage = "准备数据"
        db.commit()

        paper = db.get(Paper, int(params.get("paper_id") or 0))
        if not paper:
            raise BusinessException("试卷不存在（可能已被删除）")

        kind = str(params.get("kind") or export_job.KIND_PDF)
        mode = str(params.get("mode") or "teacher")
        layout = str(params.get("layout") or "a4_single")
        seal = bool(params.get("with_seal_line", True))
        page_no = bool(params.get("with_page_number", True))

        preview = _build_preview(db, paper, mode=mode)
        _touch_job(job_id, progress=45, stage="渲染文件")

        if kind == export_job.KIND_ANSWER_SHEET:
            buf = build_answer_sheet(preview, layout=layout)
            ext = "pdf"
            fname = f"paper_{paper.id}_answersheet.pdf"
        elif kind == export_job.KIND_DOCX:
            buf = build_docx(preview, mode=mode, layout=layout,
                             with_seal_line=seal, with_page_number=page_no)
            ext = "docx"
            fname = f"paper_{paper.id}_{mode}.docx"
        else:
            buf = build_pdf(preview, mode=mode, layout=layout,
                            with_seal_line=seal, with_page_number=page_no)
            ext = "pdf"
            fname = f"paper_{paper.id}_{mode}.pdf"

        data = buf.getvalue() if hasattr(buf, "getvalue") else bytes(buf)
        _touch_job(job_id, progress=85, stage="写入文件")
        result = export_job.write_file(job_id, kind, data, filename=fname)
        result["ext"] = ext

        db.expire_all()
        job = db.get(AgentJob, job_id)
        if job:
            job.result = json.dumps(result, ensure_ascii=False)
            job.status = agent_job_state.STATUS_SUCCEEDED
            job.progress = 100
            job.stage = "完成"
            job.finished_at = now_local()
            db.commit()
    except agent_job_state.JobCancelled:
        logger.info(f"导出任务 {job_id} 已被用户取消")
        _cancelled_job(job_id)
    except BusinessException as exc:
        _fail_job(job_id, str(exc))
    except Exception as exc:  # noqa: BLE001
        logger.exception(f"异步导出失败（job={job_id}）")
        _fail_job(job_id, f"{type(exc).__name__}: {exc}")
    finally:
        db.close()
