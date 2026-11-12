"""异步组卷的后台 runner（自 api/v1/paper_compose.py 下沉，Q-05）。

与 `paper_export_jobs.py` 对称：那个跑导出、这个跑组卷，两者共用
`sys_agent_job` 表与 `_touch_job` 系列状态助手。

`_run_compose_job` 只做"调度"：读任务 → 解析参数 → 调引擎 → 落结果，
不含任何组卷算法（算法在 `paper_compose_engine.py`）。单独成文件是为了让
「请求线程」与「后台线程」的边界一眼可见：这里全程用独立 Session。
"""
import json
import logging

from app.core.exception import BusinessException
from app.services import agent_job_state
from app.services.paper_compose_engine import (
    _ai_resolve_params, _compose_from_payload, _plan_response,
)
from app.services.paper_export_jobs import _cancelled_job, _fail_job, _touch_job
from app.utils.common import now_local

logger = logging.getLogger(__name__)


def _run_compose_job(job_id: int) -> None:
    """后台执行组卷。独立 Session —— 请求结束 Session 就关了。"""
    from app.core.database import SessionLocal
    from app.models import AgentJob, User

    db = SessionLocal()

    def check_cancel() -> None:
        """检查点：已请求取消就抛 `JobCancelled` 中断。

        只能在**批次之间**检查 —— LLM 往返本身不可中断（同步 HTTP 调用），
        所以取消的实际延迟 = 当前批次剩余时间（实测单批 60~100s）。
        这一点必须在前端如实说明，不能让用户以为点了就立刻停。
        """
        if agent_job_state.cancel_requested(db, job_id):
            raise agent_job_state.JobCancelled()

    try:
        job = db.get(AgentJob, job_id)
        if not job:
            return
        # 排队期就被取消：连 running 都不用写，直接落 cancelled
        check_cancel()
        job.status = agent_job_state.STATUS_RUNNING[1]
        job.started_at = now_local()
        job.progress = 5
        job.stage = "解析参数"
        db.commit()

        params = json.loads(job.params or "{}")
        user = db.get(User, job.user_id)
        if not user:
            raise BusinessException("任务发起人不存在")

        def on_progress(done: int, total: int) -> None:
            # 补题占 15%~90%：那里是大头，其余阶段（解析/报告/落库）都很快
            check_cancel()
            pct = 15 + int(75 * done / max(1, total))
            _touch_job(job_id, progress=pct, stage=f"AI 补题 {done}/{total} 个大题")

        # 与同步接口 /compose/ai 共用同一份解析（P0-3）。
        # 旧实现直接把 task.params 丢给 _compose_from_payload，
        # 「只写描述、不选年级」在这里必然抛"请选择有效的年级"。
        merged, parse_error, request = _ai_resolve_params(db, user, params)
        if not merged.get("grade_id") or not merged.get("subject_id"):
            raise BusinessException(
                "无法从描述中识别年级或学科，请明确指定" +
                (f"（AI 解析提示：{parse_error}）" if parse_error else ""))
        _touch_job(job_id, progress=12, stage="解析参数完成")

        ctx = _compose_from_payload(db, user, merged, on_progress=on_progress)
        _touch_job(job_id, progress=92, stage="生成报告")

        body = _plan_response(ctx)
        payload = json.dumps(body, ensure_ascii=False, default=str)

        # 落结果前再查一次：卷子已经生成、用户却在这几十毫秒里点了取消，
        # 让他白等一张不要的卷子没有意义
        check_cancel()

        # 重新取一次：期间 on_progress 用别的连接改过这一行（旧对象可能过期）
        db.expire_all()
        job = db.get(AgentJob, job_id)
        if job:
            job.result = payload
            # 写值统一走常量（Q-07）：历史上这里写 succeeded、教案侧写 success
            job.status = agent_job_state.STATUS_SUCCEEDED
            job.progress = 100
            job.stage = "完成"
            job.finished_at = now_local()
            db.commit()
    except agent_job_state.JobCancelled:
        logger.info(f"组卷任务 {job_id} 已被用户取消")
        _cancelled_job(job_id)
    except BusinessException as exc:
        _fail_job(job_id, str(exc))
    except Exception as exc:  # noqa: BLE001
        logger.exception(f"异步组卷失败（job={job_id}）")
        _fail_job(job_id, f"{type(exc).__name__}: {exc}")
    finally:
        db.close()
