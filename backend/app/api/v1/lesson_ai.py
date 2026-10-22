"""AI 教案生成接口（/api/v1/lesson/ai/*）。

为什么走异步任务而不是同步返回：

真实 LLM 下教案要分两段生成（目标+重难点 / 过程+练习），实测 25~60s。
同步 HTTP 在这个时长上不可靠：nginx 默认 proxy_read_timeout 60s、
浏览器/中间网关也常见 30s 上限，超时后前端拿到的是 502/Network Error，
而服务端其实还在写库 —— 用户看到「生成失败」，实际后端产生了重复教案。
因此沿用出题/组卷的 `AgentJob` 模式：提交即返回 job_id，前端轮询。

任务表复用 `sys_agent_job`（`agent="lesson"`），不新建表：
- 已有的权限校验、日志、过期清理逻辑全部可复用
- 新增的 progress/stage 两列已在 db_migrations 登记

保存动作与生成动作**分离**：生成只产出内容，用户预览、修改、确认后才落库。
理由：AI 教案可信度不足以「不问就存」，且生成失败时教案库不应该被脏数据污染。
"""
import json
import threading
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.agents.lesson_agent import LessonPlanAgent, render_markdown
from app.api.deps import get_current_teacher
from app.core.database import get_db
from app.core.exception import BusinessException, NotFoundException, PermissionException
from app.core.rate_limit import check_agent_rate
from app.models import AgentJob, Grade, KnowledgePoint, LessonPlan, LessonStage, Subject, User
from app.utils.common import now_local, ok

router = APIRouter(prefix="/lesson/ai", tags=["AI 教案"])

# 任务百分比 -> 面向用户的中文进度文案。
# 存在意义：LLM 等待期前端必须能说明「在做什么」，否则 40s 进度条不动
# 会被当成卡死。百分比由 Agent 主动上报，这里只做兜底展示。
PROGRESS_HINTS: List[tuple] = [
    (0, "任务排队中"),
    (15, "解析教学条件"),
    (45, "拟定教学目标与重难点"),
    (80, "展开教学过程与师生活动"),
    (95, "校验并补全教案结构"),
    (100, "生成完成"),
]

# 入参上限（P1）：教案 prompt 直接拼接这些文本，超长入参会把单次请求放大成
# 巨额 token 成本（甚至打爆模型上下文）。正常教案「课题」十几个字、
# 「教学目标/补充要求」几百字，上限只拦截异常入参。
MAX_TOPIC_CHARS = 200
MAX_TEXT_CHARS = 8000

# 任务超时判定：超过该时长仍是 running，视为僵尸任务。
# daemon 线程在进程重启后不会恢复，没有这个判定会让前端永久转圈。
JOB_TIMEOUT_SECONDS = 300


def _hint(pct: int) -> str:
    text = PROGRESS_HINTS[0][1]
    for threshold, label in PROGRESS_HINTS:
        if pct >= threshold:
            text = label
    return text


def _job_progress(job: AgentJob) -> Dict[str, Any]:
    """把任务状态整理成前端轮询所需的完整结构。"""
    pct = int(job.progress or 0)
    if job.status == "success":
        pct = 100
    elif job.status == "failed":
        pct = min(pct, 99)

    # 僵尸任务：进程重启导致后台线程丢失，status 永远停在 running。
    timed_out = False
    if job.status in ("pending", "running") and job.created_at:
        elapsed = (now_local() - job.created_at).total_seconds()
        if elapsed > JOB_TIMEOUT_SECONDS:
            timed_out = True

    d = {
        "job_id": job.id,
        "status": "failed" if timed_out else job.status,
        "progress": pct,
        "stage": job.stage or _hint(pct),
        "error": ("生成超时（超过 %d 秒未完成），请重试或减少课时后重试"
                  % JOB_TIMEOUT_SECONDS) if timed_out else job.error,
        "created_at": job.created_at.strftime("%Y-%m-%d %H:%M:%S") if job.created_at else None,
        "finished_at": (job.finished_at.strftime("%Y-%m-%d %H:%M:%S")
                        if job.finished_at else None),
    }
    if job.result:
        try:
            d["result"] = json.loads(job.result)
        except (ValueError, TypeError):
            d["result"] = None
    else:
        d["result"] = None
    return d


# ---------------------------------------------------------------- 后台执行
def _run_lesson_job(job_id: int) -> None:
    """后台线程主体（独立 Session —— 请求的 Session 在响应后已关闭）。"""
    import logging

    from app.core.database import SessionLocal

    logger = logging.getLogger(__name__)
    db = SessionLocal()
    job: Optional[AgentJob] = None

    def update(pct: int, stage: str) -> None:
        """进度回调：独立提交，确保前端轮询立刻能看到变化。"""
        nonlocal job
        if job is None:
            job = db.get(AgentJob, job_id)
            if job is None:
                return
        job.progress = max(0, min(100, int(pct)))
        job.stage = stage[:64]
        try:
            db.commit()
        except Exception:  # noqa: BLE001  进度写失败不该中断生成
            db.rollback()

    try:
        job = db.get(AgentJob, job_id)
        if not job:
            return
        job.status = "running"
        job.started_at = now_local()
        job.progress = 5
        job.stage = "解析教学条件"
        db.commit()

        params = json.loads(job.params or "{}")
        res = LessonPlanAgent().run(db, user_id=job.user_id, **params)

        job = db.get(AgentJob, job_id)
        if job is None:
            return
        if res.get("success"):
            job.result = json.dumps(res.get("data"), ensure_ascii=False, default=str)
            job.status = "success"
            job.error = None
            job.progress = 100
            job.stage = "生成完成"
        else:
            # 失败也要留下可读原因：Agent 的 message 已经是面向用户的中文
            job.status = "failed"
            job.error = (res.get("message") or "教案生成失败")[:500]
            job.stage = "生成失败"
    except Exception as exc:  # noqa: BLE001
        logger.exception("AI 教案任务 %s 执行失败", job_id)
        try:
            job = db.get(AgentJob, job_id)
            if job:
                job.status = "failed"
                job.error = f"生成失败：{exc}"[:500]
                job.stage = "生成失败"
        except Exception:  # noqa: BLE001
            db.rollback()
    finally:
        try:
            job = db.get(AgentJob, job_id)
            if job is not None:
                job.finished_at = now_local()
                db.commit()
        except Exception:  # noqa: BLE001
            db.rollback()
        db.close()


# ---------------------------------------------------------------- 提交生成
@router.post("/generate", summary="提交 AI 教案生成任务")
def generate_lesson(
    data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    user: User = Depends(get_current_teacher),
):
    """提交生成任务，立即返回 job_id。

    必填：topic / grade_id / subject_id
    可选：knowledge_point_id / duration_minutes / period / objectives /
          textbook_version / difficulty / extra_requirements
    """
    topic = (data.get("topic") or "").strip()
    if not topic:
        raise BusinessException("教学主题不能为空")
    if len(topic) > MAX_TOPIC_CHARS:
        raise BusinessException(f"教学主题最长 {MAX_TOPIC_CHARS} 字符")

    # 长文本入参在提交时就校验（而不是等异步任务里 LLM 失败）
    objectives = (data.get("objectives") or "").strip()
    extra_requirements = (data.get("extra_requirements") or "").strip()
    if len(objectives) > MAX_TEXT_CHARS:
        raise BusinessException(
            f"教学目标过长（{len(objectives)} 字符），请控制在 {MAX_TEXT_CHARS} 字符以内")
    if len(extra_requirements) > MAX_TEXT_CHARS:
        raise BusinessException(
            f"补充要求过长（{len(extra_requirements)} 字符），"
            f"请控制在 {MAX_TEXT_CHARS} 字符以内")

    grade_id = data.get("grade_id")
    subject_id = data.get("subject_id")
    if not grade_id:
        raise BusinessException("请选择年级")
    if not subject_id:
        raise BusinessException("请选择学科")

    # 条件在提交前就校验：异步任务里再报错，用户要等一轮轮询才知道参数错了。
    grade = db.get(Grade, int(grade_id))
    if not grade:
        raise BusinessException("年级不存在")
    subject = db.get(Subject, int(subject_id))
    if not subject:
        raise BusinessException("学科不存在")
    if subject.grade_id and int(subject.grade_id) != int(grade.id):
        raise BusinessException(
            f"学科「{subject.name}」不属于{grade.name}。学科是按年级配置的，"
            f"请用 /edu/subjects?grade_id={grade.id} 重新选择")

    kp_id = data.get("knowledge_point_id")
    if kp_id:
        kp = db.get(KnowledgePoint, int(kp_id))
        if not kp:
            raise BusinessException("知识点不存在")
        if grade.id and kp.grade_id and int(kp.grade_id) != int(grade.id):
            raise BusinessException("该知识点不属于所选年级")

    try:
        minutes = int(data.get("duration_minutes") or 45)
    except (TypeError, ValueError):
        raise BusinessException("课时长度必须是分钟数") from None
    if minutes < 15 or minutes > 180:
        raise BusinessException("课时长度应在 15~180 分钟之间")

    check_agent_rate(db, user.id)

    params = {
        "topic": topic,
        "grade_id": int(grade.id),
        "subject_id": int(subject.id),
        "knowledge_point_id": int(kp_id) if kp_id else None,
        "duration_minutes": minutes,
        "period": (data.get("period") or "").strip() or None,
        "objectives": objectives,
        "textbook_version": (data.get("textbook_version") or "").strip() or None,
        "difficulty": (data.get("difficulty") or "").strip(),
        "extra_requirements": extra_requirements,
    }

    job = AgentJob(
        user_id=user.id, agent="lesson", status="pending",
        progress=0, stage="任务排队中",
        params=json.dumps(params, ensure_ascii=False),
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    threading.Thread(target=_run_lesson_job, args=(job.id,), daemon=True).start()
    return ok(
        {"job_id": job.id, "status": job.status, "progress": 0, "stage": job.stage,
         "poll_url": f"/api/v1/lesson/ai/jobs/{job.id}"},
        message="任务已提交，请轮询生成进度",
    )


# ---------------------------------------------------------------- 轮询进度
@router.get("/jobs/{job_id}", summary="查询 AI 教案生成进度")
def get_lesson_job(
    job_id: int, db: Session = Depends(get_db),
    user: User = Depends(get_current_teacher),
):
    job = db.get(AgentJob, job_id)
    if not job or job.agent != "lesson":
        raise NotFoundException("任务不存在")
    if job.user_id != user.id and "sys_admin" not in user.role_codes:
        raise PermissionException("无权查看该任务")
    return ok(_job_progress(job))


@router.get("/jobs", summary="我的 AI 教案生成记录")
def list_lesson_jobs(
    limit: int = Query(20, ge=1, le=100), db: Session = Depends(get_db),
    user: User = Depends(get_current_teacher),
):
    from sqlalchemy import desc as _desc, select as _select

    rows = db.scalars(
        _select(AgentJob).where(
            AgentJob.user_id == user.id, AgentJob.agent == "lesson",
        ).order_by(_desc(AgentJob.created_at)).limit(limit)
    ).all()
    items = []
    for job in rows:
        d = _job_progress(job)
        d.pop("result", None)  # 列表不返回完整教案正文，避免响应体过大
        try:
            p = json.loads(job.params or "{}")
            # 失败任务可能在写 params 前就挂了，标题留空会让列表出现空白行
            d["topic"] = p.get("topic") or "（未命名）"
            d["duration_minutes"] = p.get("duration_minutes")
        except (ValueError, TypeError):
            d["topic"] = "（未命名）"
        items.append(d)
    return ok({"items": items, "total": len(items)})


# ---------------------------------------------------------------- 保存入教案库
@router.post("/jobs/{job_id}/save", summary="把生成结果保存到教案库")
def save_lesson_from_job(
    job_id: int, data: Dict[str, Any] = Body(default={}),
    db: Session = Depends(get_db), user: User = Depends(get_current_teacher),
):
    """保存 AI 生成结果。

    请求体可覆盖任意字段（用户在预览界面改过的内容优先），
    未传的字段取生成结果原值 —— 前端只需提交被修改的部分。
    """
    job = db.get(AgentJob, job_id)
    if not job or job.agent != "lesson":
        raise NotFoundException("任务不存在")
    if job.user_id != user.id and "sys_admin" not in user.role_codes:
        raise PermissionException("无权保存该任务的结果")
    if job.status != "success" or not job.result:
        raise BusinessException("该任务尚未生成成功，无法保存")

    try:
        plan = json.loads(job.result)
    except (ValueError, TypeError):
        raise BusinessException("生成结果已损坏，请重新生成") from None
    if not isinstance(plan, dict) or not plan.get("topic"):
        raise BusinessException("生成结果不完整，请重新生成")

    override = data if isinstance(data, dict) else {}

    def pick(key: str, default: Any = None) -> Any:
        if key in override and override[key] is not None:
            return override[key]
        return plan.get(key, default)

    title = (str(pick("title") or "").strip() or str(plan.get("topic")))[:128]
    topic = (str(pick("topic") or "").strip())[:128]
    if not topic:
        raise BusinessException("课题不能为空")

    # 学科/年级以生成结果为准；用户覆盖时也要重新校验存在性与归属关系，
    # 否则会写出 subject_id 属于别的年级的脏数据。
    grade_id = int(pick("grade_id") or 0)
    subject_id = int(pick("subject_id") or 0)
    if not grade_id or not subject_id:
        raise BusinessException("生成结果缺少年级或学科，无法保存")
    grade = db.get(Grade, grade_id)
    subject = db.get(Subject, subject_id)
    if not grade or not subject:
        raise BusinessException("年级或学科不存在")
    if subject.grade_id and int(subject.grade_id) != int(grade.id):
        raise BusinessException("学科与年级不匹配，无法保存")

    kp_id = pick("knowledge_point_id")
    if kp_id and not db.get(KnowledgePoint, int(kp_id)):
        kp_id = None

    try:
        minutes = int(pick("duration_minutes") or 45)
    except (TypeError, ValueError):
        minutes = 45
    minutes = max(15, min(180, minutes))

    lp = LessonPlan(
        title=title, topic=topic,
        subject_id=subject_id, grade_id=grade_id,
        textbook_version=pick("textbook_version"),
        knowledge_point_id=int(kp_id) if kp_id else None,
        duration_minutes=minutes,
        period=pick("period"),
        objectives=str(pick("objectives") or ""),
        key_points=str(pick("key_points") or ""),
        difficulties=str(pick("difficulties") or ""),
        teaching_preparation=str(pick("teaching_preparation") or "") or None,
        class_exercise=str(pick("class_exercise") or "") or None,
        board_design=str(pick("board_design") or "") or None,
        homework=str(pick("homework") or "") or None,
        reflection=str(pick("reflection") or "") or None,
        creator_id=user.id, is_shared=0,
        ai_generated=1, ai_job_id=job.id,
    )
    db.add(lp)
    db.flush()

    stages = pick("stages") or []
    if isinstance(stages, list):
        for i, s in enumerate(stages):
            if not isinstance(s, dict):
                continue
            name = str(s.get("name") or "").strip()
            if not name:
                continue
            try:
                dur = int(s.get("duration_minutes") or 5)
            except (TypeError, ValueError):
                dur = 5
            db.add(LessonStage(
                lesson_id=lp.id, name=name[:32], duration_minutes=max(1, dur),
                content=str(s.get("content") or ""),
                teacher_activity=s.get("teacher_activity"),
                student_activity=s.get("student_activity"),
                sort_order=i,
            ))

    # 审计：AI 产物入库是「AI 直接写业务数据」，与出题 save=True 同类风险
    try:
        from app.models import OperationLog

        db.add(OperationLog(
            user_id=user.id, username=user.username,
            module="AI智能", action="AI 教案入库", method="POST",
            path="/api/v1/lesson/ai", params=f"job_id={job.id} plan_id={lp.id}",
            status="success",
        ))
    except Exception:  # noqa: BLE001  审计失败不阻断主流程
        pass

    db.commit()
    db.refresh(lp)
    return ok({"plan_id": lp.id, "title": lp.title},
              message="已保存到教案库")


# ---------------------------------------------------------------- 导出
@router.get("/jobs/{job_id}/export", summary="导出生成的教案（Markdown）")
def export_lesson(
    job_id: int, db: Session = Depends(get_db),
    user: User = Depends(get_current_teacher),
):
    """导出为 Markdown 文件（可直接用 Word 打开，也可粘贴到公众号/教研平台）。"""
    job = db.get(AgentJob, job_id)
    if not job or job.agent != "lesson":
        raise NotFoundException("任务不存在")
    if job.user_id != user.id and "sys_admin" not in user.role_codes:
        raise PermissionException("无权导出该任务的结果")
    if job.status != "success" or not job.result:
        raise BusinessException("该任务尚未生成成功，无法导出")

    try:
        plan = json.loads(job.result)
    except (ValueError, TypeError):
        raise BusinessException("生成结果已损坏，请重新生成") from None

    md = render_markdown(plan)
    # 文件名用课题，去掉路径分隔符等非法字符；RFC 5987 编码兼容中文
    import re
    from urllib.parse import quote

    safe = re.sub(r'[\\/:*?"<>|\r\n\t]', "_", str(plan.get("title") or plan.get("topic") or "教案"))
    safe = safe.strip()[:60] or "教案"
    filename = f"{safe}.md"
    return Response(
        content=md.encode("utf-8"),
        media_type="text/markdown; charset=utf-8",
        headers={
            "Content-Disposition":
                f"attachment; filename=\"lesson.md\"; filename*=UTF-8''{quote(filename)}",
        },
    )


# ---------------------------------------------------------------- 预填条件
@router.get("/options", summary="可选条件（学科按年级过滤）")
def get_options(
    grade_id: Optional[int] = None, db: Session = Depends(get_db),
    user: User = Depends(get_current_teacher),
):
    """返回表单所需的年级/学科/知识点候选。

    学科必须按年级过滤：`/edu/subjects` 不传 grade_id 会返回 60+ 同名记录
    （学科按 (grade_id, name) 唯一），直接喂给下拉框用户无法分辨。
    """
    from sqlalchemy import select as _select

    grades = db.scalars(
        _select(Grade).where(Grade.is_active.is_(True)).order_by(Grade.grade_num)
    ).all()
    result: Dict[str, Any] = {
        "grades": [{"id": g.id, "name": g.name, "grade_num": g.grade_num} for g in grades],
        "subjects": [], "knowledge_points": [],
    }
    if grade_id:
        subs = db.scalars(
            _select(Subject).where(
                Subject.grade_id == int(grade_id), Subject.is_active.is_(True),
            ).order_by(Subject.sort, Subject.id)
        ).all()
        result["subjects"] = [{"id": s.id, "name": s.name,
                               "textbook_version": s.textbook_version} for s in subs]
        sub_ids = [s.id for s in subs]
        if sub_ids:
            kps = db.scalars(
                _select(KnowledgePoint).where(
                    KnowledgePoint.subject_id.in_(sub_ids),
                    KnowledgePoint.is_active.is_(True),
                ).order_by(KnowledgePoint.sort, KnowledgePoint.id).limit(500)
            ).all()
            result["knowledge_points"] = [
                {"id": k.id, "name": k.name, "subject_id": k.subject_id,
                 "level": k.level, "difficulty": k.difficulty} for k in kps
            ]
    return ok(result)
