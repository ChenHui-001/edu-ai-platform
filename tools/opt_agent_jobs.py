# -*- coding: utf-8 -*-
"""优化项 2：Agent 长任务异步化 + 轮询。

场景：出题（20 题）/ 组卷 在真实 LLM 下 40-60s，同步 HTTP 易被网关截断。
方案：提交即返回 job_id，后台线程执行，前端轮询 /agent/jobs/{id}。

设计取舍：
- 用 threading.Thread 而非 FastAPI BackgroundTasks：BackgroundTasks 在响应后
  仍占用该请求线程，长任务会拖慢整体吞吐；独立线程 + 独立 DB Session 更可控。
- 任务结果落库（sys_agent_job.result），前端刷新页面后仍可查回。
"""
import io

f = "backend/app/api/v1/agent.py"
s = io.open(f, encoding="utf-8").read()

JOBS_API = '''

# ---------------------------------------------------------------- 异步任务（长任务）
JOB_AGENTS = {"question", "paper"}


def _run_job(job_id: int) -> None:
    """后台执行任务（独立 Session，避免请求结束后 Session 已关闭）。"""
    from app.core.database import SessionLocal
    from app.models import AgentJob

    db = SessionLocal()
    try:
        job = db.get(AgentJob, job_id)
        if not job:
            return
        job.status = "running"
        job.started_at = utcnow()
        db.commit()

        params = json.loads(job.params or "{}")
        res: Dict[str, Any]
        if job.agent == "question":
            from app.agents.question_agent import QuestionGeneratorAgent

            res = QuestionGeneratorAgent().run(
                db, user_id=job.user_id,
                grade_id=params.get("grade_id"),
                subject_id=int(params.get("subject_id", 0)),
                knowledge_point_id=params.get("knowledge_point_id"),
                question_type=params.get("type", "single"),
                count=int(params.get("count", 5)),
                difficulty=params.get("difficulty", "medium"),
                save=bool(params.get("save", False)),
            )
        else:
            from app.agents.paper_agent import PaperComposerAgent

            res = PaperComposerAgent().run(
                db, user_id=job.user_id, request=params.get("request", ""),
                grade_id=params.get("grade_id"), subject_id=params.get("subject_id"),
                total_score=float(params.get("total_score", 100)),
                difficulty_ratio=params.get("difficulty_ratio"),
                type_ratio=params.get("type_ratio"),
                knowledge_point_ids=params.get("knowledge_point_ids"),
                paper_name=params.get("paper_name"),
                save=bool(params.get("save", False)),
            )

        job.result = json.dumps(res, ensure_ascii=False, default=str)
        job.status = "success" if res.get("success") else "failed"
        job.error = None if res.get("success") else (res.get("message") or "")[:500]
        _warn_if_slow(res, f"job:{job.agent}")
    except Exception as exc:  # noqa: BLE001
        logger.exception("异步任务 %s 执行失败", job_id)
        job = db.get(AgentJob, job_id)
        if job:
            job.status = "failed"
            job.error = str(exc)[:500]
    finally:
        job.finished_at = utcnow()
        try:
            db.commit()
        except Exception:  # noqa: BLE001
            db.rollback()
        db.close()


@router.post("/jobs", summary="提交长任务（异步出题/组卷）")
def create_job(
    data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    user: User = Depends(get_current_teacher),
):
    """提交长任务，立即返回 job_id；用 GET /agent/jobs/{id} 轮询结果。"""
    from app.models import AgentJob

    agent = (data.get("agent") or "").strip()
    if agent not in JOB_AGENTS:
        raise BusinessException(f"不支持的任务类型 {agent!r}，可选：{sorted(JOB_AGENTS)}")
    params = data.get("params") or {}
    if not isinstance(params, dict):
        raise BusinessException("params 必须是对象")
    check_agent_rate(db, user.id)

    job = AgentJob(user_id=user.id, agent=agent, status="pending",
                   params=json.dumps(params, ensure_ascii=False))
    db.add(job)
    db.commit()
    db.refresh(job)

    import threading

    threading.Thread(target=_run_job, args=(job.id,), daemon=True).start()
    return ok({"job_id": job.id, "status": job.status},
              message="任务已提交，请轮询 /agent/jobs/%d 获取结果" % job.id)


@router.get("/jobs/{job_id}", summary="查询任务状态与结果")
def get_job(
    job_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_teacher),
):
    from app.models import AgentJob

    job = db.get(AgentJob, job_id)
    if not job:
        raise NotFoundException("任务不存在")
    if job.user_id != user.id and "sys_admin" not in user.role_codes:
        raise PermissionException("无权查看该任务")
    d = dictify(job)
    d["result"] = json.loads(job.result) if job.result else None
    return ok(d)


@router.get("/jobs", summary="我的任务列表")
def list_jobs(
    params: PageParams = Depends(), status: Optional[str] = None,
    db: Session = Depends(get_db), user: User = Depends(get_current_teacher),
):
    from app.models import AgentJob

    stmt = select(AgentJob).where(AgentJob.user_id == user.id)
    if status:
        stmt = stmt.where(AgentJob.status == status)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(
        stmt.order_by(desc(AgentJob.created_at)).offset(params.offset).limit(params.page_size)
    ).all()
    items = [dictify(r) for r in rows]
    return ok({"items": items, "total": total, "page": params.page})
'''

# 插入到「调用日志」段之前
ANCHOR = "# ---------------------------------------------------------------- 调用日志"
assert ANCHOR in s
s = s.replace(ANCHOR, JOBS_API.strip("\n") + "\n\n\n" + ANCHOR, 1)

# 依赖导入：json / utcnow / SessionLocal
if "import json" not in s:
    s = s.replace("from typing import Any, Dict, List, Optional",
                  "import json\nfrom typing import Any, Dict, List, Optional")
s = s.replace("from app.utils.common import PageParams, dictify, fail, ok",
              "from app.utils.common import PageParams, dictify, fail, ok, utcnow")

io.open(f, "w", encoding="utf-8", newline="\n").write(s)
print("异步任务接口已添加")
