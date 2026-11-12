"""标准组卷 V3 接口：双模式组卷 / 预览编辑 / 版本 / 共享 / 收藏 / 试卷库。

前缀 `/question/papers`（与既有 CRUD 同前缀，但路径全部新增，
不改动 question.py 的任何既有行为）。

路径规划（避开既有路由）：
  既有：GET /papers、POST /papers、PUT /papers/{id}、DELETE /papers/{id}、
        GET /papers/{id}、POST /papers/{id}/copy|share、GET /papers/{id}/export
  新增：POST /papers/compose/preview   自定义参数组卷预览
        POST /papers/compose/ai        AI 一键组卷
        POST /papers/compose/save      保存组卷结果
        GET  /papers/{id}/preview      全卷预览（含大题结构）
        POST /papers/{id}/items        增删改题目（含拖拽排序）
        POST /papers/{id}/items/{item_id}/regenerate  单题 AI 重生
        DELETE /papers/{id}/items/{item_id}
        POST /papers/{id}/sections/rename  大题改名
        POST /papers/{id}/restructure  一键重构（按标准重排大题）
        GET  /papers/{id}/versions     版本列表
        POST /papers/{id}/versions/{v}/restore  版本回溯
        GET  /papers/library           试卷库分类（我的/共享/公共/收藏）
        POST /papers/{id}/favorite     收藏/取消
        POST /papers/{id}/review       审核（申请公共库/通过/驳回）
        GET  /papers/{id}/export/docx  Word 导出
        GET  /papers/{id}/export/pdf   PDF 导出
        GET  /papers/{id}/export/answer-sheet  答题卡导出
"""
import io
import json
import threading
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Annotated, Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, Query
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import func, select
from sqlalchemy.orm import Session, noload

from app.api.deps import require_perm
from app.core.config import settings
from app.core.database import get_db
from app.core.exception import (
    BusinessException, ConflictException, NotFoundException, PermissionException,
)
from app.models import (
    Answer, ExamStandard, Grade, KnowledgePoint, Paper, PaperFavorite, PaperItem,
    PaperShare, PaperStatus, PaperVersion, Question, SharePermission,
    ShareScope, Subject, Submission, Task, User,
)
from app.services import agent_job_state
from app.services import export_job
from app.schemas.legacy_bodies import (
    ComposeAiAsyncIn,
    ComposeAiIn,
    ComposePreviewIn,
    ComposeRegenerateIn,
    ComposeSaveIn,
    RegenerateItemIn,
    RenameSectionIn,
    RestoreVersionIn,
    RestructurePaperIn,
    ReviewPaperIn,
    SetShareScopeIn,
    ToggleFavoriteIn,
    UpdateItemsIn,
)
from app.services import paper_compose_service as compose_svc
# Q-05：题项写入/预览已下沉到 services/paper_items.py；此处再导出，保持
# question.py 的 `from app.api.v1.paper_compose import _write_items/_build_preview`
# 及本文件内部调用不变。
from app.services.paper_items import (  # noqa: F401
    _build_preview, _load_json, _normalize_items, _stage_of, _write_items,
)
# Q-05：导出链路已下沉到 services/paper_export_jobs.py；此处再导出，保持
# 同步导出端点、create_export_job 后台线程与组卷任务的 _touch_job 等调用不变。
from app.services.paper_export_jobs import (  # noqa: F401
    _cancelled_job, _fail_job, _requested_export, _run_export_job, _touch_job,
)
# Q-05：组卷引擎主流程已下沉到 services/paper_compose_engine.py；此处再导出，
# 保持 `_regen_one`/`_ai_resolve_params` 的内部调用与回归脚本的引用不变。
from app.services.paper_compose_engine import (  # noqa: F401
    _ai_fill_gaps, _compose_from_payload, _existing_stem_keys, _fill_fail_hint,
    _fill_one_gap, _gap_action, _grade_subject, _is_budget_failure,
    _is_similar_stem, _mark_gaps_reason, _parse_sections_input,
    _resolve_standard, _stem_key,
)
# 引擎剩余部分（AI 参数解析 / 预览态重生 / 响应拼装）同在 paper_compose_engine；
# 后台组卷 runner 在 paper_compose_jobs。此处再导出保持调用点与回归脚本不变。
from app.services.paper_compose_engine import (  # noqa: F401
    REGEN_MAX_COUNT, _ai_resolve_params, _diff_label, _plan_response,
    _regen_forbid_ids, _regen_one, _regen_stem_keys, _regen_targets,
    _resolve_ai_grade, _resolve_ai_subject, _type_ratio_to_sections,
)
from app.services.paper_compose_jobs import _run_compose_job  # noqa: F401
from app.services import llm_breaker
from app.services.paper_export_service import (
    build_answer_sheet, build_docx, build_pdf,
)
from app.services import paper_version_service as version_svc
from app.utils.common import PageParams, dictify, ok

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/question/papers", tags=["标准组卷"])

TYPE_LABEL = compose_svc.TYPE_LABEL

# AI 补题的单批题量上限，**按题型分档**。
#
# 推理模型（生产用 MiniMax-M3.1-Flash 一类）的 thinking token 与正文**共享**
# `LLM_MAX_TOKENS`（默认 8192），批次越大，推理阶段越容易先把预算烧光、正文
# 返回空串——HTTP 200、无异常，只有 content 是空字符串。
#
# 生产实测（2026-11-04 15:24，初中数学三个大题并发补题，`sys_agent_call_log`）：
#   5 道填空  → out=4689，正文 1995 字符 → 成功
#   10 道单选 → out=8192（打满），正文 0 字符 → 失败
#   9 道解答  → out=8192（打满），正文 0 字符 → 失败
#
# 所以「统一 10 道」对重题型必然撞墙。单题正文量越大的题型，单批越小：
# 作文一题就上千字、解答题要完整解题过程、材料题自带长材料 + 多小问。
# 批量策略已抽到 services/ai_fill_batch.py（与 HTTP 路由无关）。
# 这里 re-import 保留模块级名字，兼容既有调用点与验证脚本。
from app.services.ai_fill_batch import (  # noqa: E402,F401
    FILL_BATCH_BY_TYPE, FILL_BATCH_DEFAULT, FILL_BATCH_HARD_DIVISOR,
    _fill_batch_cap,
)


# ---------------------------------------------------------------- 权限 helpers
# 已下沉到 services/paper_access.py（Q-05：拆分超大路由文件）。此处再导出，
# 保持既有 `from app.api.v1.paper_compose import _paper_visibility_clause /
# _assert_readable` 跨模块引用，以及本文件内部的 `_is_sys_admin(...)` 等调用不变。
from app.services.paper_access import (  # noqa: F401
    _assert_can_edit,
    _assert_readable,
    _is_grade_admin,
    _is_sys_admin,
    _legacy_shared_clause,
    _paper_visibility_clause,
    _scope_clause,
    _share_permission,
)


# ---------------------------------------------------------------- 组卷预览
@router.post("/compose/regenerate", summary="组卷预览：重新生成单题或某题型")
def compose_regenerate(
    body: ComposeRegenerateIn = Body(...), db: Session = Depends(get_db),
    user: User = Depends(require_perm("paper:ai")),
):
    """在**保存之前**替换预览里的某些题目（不写试卷，只把新题返回给前端）。

    请求体：
    ```json
    {
      "grade_id": 3, "subject_id": 21,
      "mode": "item" | "section",
      "index": 5,                    // mode=item：要替换的题在下表 items 里的下标
      "section_code": "single",      // mode=section：要整段重生的大题
      "items": [ {...当前预览的完整题目...} ]
    }
    ```

    响应：
    ```json
    {
      "mode": "section", "replaced": 9,
      "items": [...替换后的完整题目（含 section_pos / section_sort / section_name）...],
      "pending": [{ "index": 3, "reason": "..." }],   // 没换成的，前端保留原题
      "message": "..."
    }
    ```

    设计取舍：**沿用原题的分值/槽位/大题归属**，只换题目内容。分值是按槽位给的
    （阶梯分值 6/6/6/8…），换题时若重算分，压轴题的 12 分会被抹成均分。
    """
    data = body.model_dump(exclude_unset=True)
    from app.core.database import SessionLocal

    grade, subject = _grade_subject(db, data.get("grade_id"), data.get("subject_id"))
    raw_items = data.get("items")
    if not isinstance(raw_items, list) or not raw_items:
        raise BusinessException("缺少当前试卷题目列表，无法重新生成")
    items: List[Dict[str, Any]] = [dict(it) for it in raw_items if isinstance(it, dict)]
    if not items:
        raise BusinessException("缺少当前试卷题目列表，无法重新生成")

    mode = str(data.get("mode") or "item").strip().lower()
    if mode not in ("item", "section"):
        raise BusinessException("重新生成方式仅支持 item / section")

    user_id = int(user.id)
    is_admin = _is_sys_admin(user)
    grade_id = int(grade.id)
    subject_id = int(subject.id)

    if mode == "item":
        try:
            index = int(data.get("index"))
        except (TypeError, ValueError):
            raise BusinessException("请指定要重新生成的题目位置")
        if index < 0 or index >= len(items):
            raise BusinessException(f"题目位置越界（index={index}，共 {len(items)} 题）")
        targets = [index]
    else:
        code = str(data.get("section_code") or "").strip().lower()
        if not code:
            raise BusinessException("请指定要重新生成的大题")
        targets = _regen_targets(items, code)
        if not targets:
            raise BusinessException(f"试卷中没有「{code}」大题")
    if len(targets) > REGEN_MAX_COUNT:
        raise BusinessException(
            f"单次最多重新生成 {REGEN_MAX_COUNT} 题（当前 {len(targets)} 题），请分大题操作")

    # 熔断/冷却期直接拒绝：重生是即时交互，转圈 1 分钟后报错比立刻告知更糟
    state = llm_breaker.snapshot()
    if state.get("breaker") == "auth":
        raise BusinessException(
            "AI 重新生成不可用：模型鉴权失败处于熔断状态"
            f"（{state.get('reason') or '密钥无效'}），请先修复密钥")
    remaining = int(state.get("cooldown_remaining") or 0)
    if remaining > 0:
        raise BusinessException(
            f"AI 重新生成暂不可用：模型限流冷却中（剩余 {remaining}s），请稍后重试")

    forbid_ids = _regen_forbid_ids(items)
    # 近似去重对照集：覆盖本次要重生的所有题型（一次取全，避免每题都扫一遍库）
    qtypes = {str(items[i].get("section_code") or items[i].get("type") or "single").lower()
              for i in targets}
    forbid_keys = _regen_stem_keys(db, grade_id=grade_id, subject_id=subject_id,
                                   qtypes=qtypes)
    db.commit()   # 结束只读事务，避免下面各线程各自提交时等锁

    # ---- 按「题型 + 难度」分组批量生成 ----
    # 逐题一次模型调用在整段重生时是最坏形态：9 道解答题 × 单次 60~90s = 13 分钟，
    # 前端必超时。分组后 9 道解答题只需 2~3 批（受 FILL_BATCH_BY_TYPE 的 calc=3 限制），
    # 组间并行（同补题口径，AI_FILL_CONCURRENCY），总耗时 ≈ 单组耗时 × 组数/并发。
    # 分组维度必须同时含难度：同一大题里 easy/medium/hard 混排时，把 9 道塞进一批
    # 会让模型按"多数难度"出题，替换后整卷难度分布就偏了。
    groups: Dict[tuple, List[int]] = {}
    for i in targets:
        src = items[i]
        qtype = str(src.get("section_code") or src.get("type") or "single").strip().lower()
        difficulty = str(src.get("difficulty") or "medium").strip().lower()
        groups.setdefault((qtype, difficulty), []).append(i)

    def _run_group(key: tuple, idxs: List[int]) -> Dict[str, Any]:
        qtype, difficulty = key
        # 知识点沿用：同组内若题目挂了不同知识点，按"出现最多的那个"生成 ——
        # 一组一调用拿不到逐题不同的知识点，取众数至少保证考点不跑到别的章节。
        kp_counter: Dict[int, int] = {}
        for i in idxs:
            kp = items[i].get("knowledge_point_id")
            if kp:
                kp_counter[int(kp)] = kp_counter.get(int(kp), 0) + 1
        kp_ids = ([max(kp_counter, key=kp_counter.get)] if kp_counter else [])
        return _regen_one(
            db_factory=SessionLocal, user_id=user_id, is_admin=is_admin,
            grade_id=grade_id, subject_id=subject_id, qtype=qtype,
            difficulty=difficulty, kp_ids=kp_ids, need=len(idxs),
            forbid_ids=set(forbid_ids), forbid_keys=list(forbid_keys),
        )

    tasks = sorted(groups.items(), key=lambda kv: min(kv[1]))
    workers = max(1, min(int(settings.AI_FILL_CONCURRENCY or 1), len(tasks), 4))
    if workers == 1:
        results = [_run_group(k, v) for k, v in tasks]
    else:
        with ThreadPoolExecutor(max_workers=workers,
                                thread_name_prefix="regen") as pool:
            futs = {pool.submit(_run_group, k, v): n for n, (k, v) in enumerate(tasks)}
            done: Dict[int, Dict[str, Any]] = {}
            for fut in as_completed(futs):
                done[futs[fut]] = fut.result()
            results = [done[n] for n in range(len(tasks))]

    pending: List[Dict[str, Any]] = []
    replaced = 0

    for (key, idxs), res in zip(tasks, results):
        got = res.get("items") or []
        # 组内按卷面顺序取用；不够分的其余位置如实上报，前端保留原题
        for pos, i in enumerate(idxs):
            if pos >= len(got):
                pending.append({
                    "index": i,
                    "reason": res.get("reason") or "本次未能生成符合要求的新题",
                })
                continue
            new = got[pos]
            src = items[i]
            merged = dict(src)
            merged.update({
                "question_id": new["question_id"],
                "type": new["type"],
                "type_label": new.get("type_label")
                or TYPE_LABEL.get(new["type"], new["type"]),
                "stem": new["stem"],
                "difficulty": new["difficulty"],
                "options": new.get("options"),
                "answer": new.get("answer"),
                "analysis": new.get("analysis"),
                "knowledge_point_id": new.get("knowledge_point_id"),
                "knowledge_point_name": new.get("knowledge_point_name"),
            })
            # 分值/槽位/大题归属一律保留原值（见函数 docstring 的取舍说明）：
            # 重算分会把压轴题的 12 分抹成均分。
            items[i] = merged
            replaced += 1

    message = f"已重新生成 {replaced} 题"
    if pending:
        first = pending[0]
        message += (f"，{len(pending)} 题未能生成"
                    f"（{first['reason']}），可对该题单独重试")
    return ok({
        "mode": mode,
        "replaced": replaced,
        "items": items,
        "pending": pending,
        "reports": compose_svc.build_reports(items),
        # 卷面体检的基准分用「各题分值之和」：重生不改变分值，这一步只是复核
        # 换题后有没有引入重复题 / 作文离位这类问题。
        "issues": compose_svc.audit_paper(
            items, total_score=round(sum(float(i.get("score") or 0) for i in items), 2) or None),
    }, message=message)


# ---------------------------------------------------------------- 组卷预览
@router.post("/compose/preview", summary="自定义参数组卷（预览，不落库）")
def compose_preview(
    body: ComposePreviewIn = Body(...), db: Session = Depends(get_db),
    user: User = Depends(require_perm("paper:write")),
):
    """按年级/学科/知识点/题型/分值/难度抽题。

    返回完整预览 + 三份报告。**不写库**——教师确认后再调 `/compose/save`。
    """
    data = body.model_dump(exclude_unset=True)
    ctx = _compose_from_payload(db, user, data)
    return ok(_plan_response(ctx))


@router.post("/compose/ai", summary="AI 一键智能组卷")
def compose_ai(
    body: ComposeAiIn = Body(...), db: Session = Depends(get_db),
    user: User = Depends(require_perm("paper:ai")),
):
    """极简参数 + 自然语言 → 全卷。

    AI 只负责**把自然语言翻译成结构化参数**（年级/学科/题型/难度/知识点），
    实际抽题仍走确定性引擎。这样：
    - 模型抖动不会导致卷子结构乱掉（结构由命题标准保证）；
    - 解析失败时可完整降级到"按标准 + 默认难度"的纯规则组卷。

    若 `count` 未指定，自动采用命题标准的题量结构。
    """
    data = body.model_dump(exclude_unset=True)
    if not str(data.get("request") or "").strip() and not (
            data.get("grade_id") and data.get("subject_id")):
        # 快速失败，不必进 LLM 解析（与 _ai_resolve_params 同一判定，这里只为省一次调用）
        raise BusinessException("请填写组卷需求描述，或至少选择年级与学科")

    merged, parse_error, request = _ai_resolve_params(db, user, data)
    if not merged.get("grade_id") or not merged.get("subject_id"):
        raise BusinessException(
            "无法从描述中识别年级或学科，请明确指定" +
            (f"（AI 解析提示：{parse_error}）" if parse_error else ""))

    ctx = _compose_from_payload(db, user, merged)
    message = ""
    if parse_error:
        message = f"AI 参数解析未成功（{parse_error}），已按命题标准与默认难度组卷"
    elif not request and not ctx.get("standard_fallback"):
        # 让教师知道"没写描述"不等于"没生效"：结构来自命题标准，不是随手拼的。
        # ★ 必须排除 fallback 场景：那里根本没有标准，再说"按命题标准生成"
        #   会与紧随其后的"尚未配置命题标准"自相矛盾（实测同一条 message 里两句并列）。
        message = "未填写需求描述，已按所选年级学科的命题标准生成题型结构与分值"
    return ok(_plan_response(ctx, ai_message=message))


@router.post("/compose/save", summary="保存组卷结果为新试卷")
def compose_save(
    body: ComposeSaveIn = Body(...), db: Session = Depends(get_db),
    user: User = Depends(require_perm("paper:write")),
):
    """把预览结果落库。

    两种入参：
    1. 传 `items`（前端已编辑过的最终题目列表）→ 直接用；
    2. 不传 `items`，传组卷参数 → 重新跑一次引擎（服务端权威结果）。

    总分一律由题分求和，**忽略客户端 total_score**（防伪造，与既有口径一致）。
    """
    data = body.model_dump(exclude_unset=True)
    name = str(data.get("name") or "").strip()
    if not name:
        raise BusinessException("请填写试卷名称")
    if len(name) > 128:
        raise BusinessException("试卷名称不能超过 128 个字符")

    ctx = _compose_from_payload(db, user, data)

    items = data.get("items")
    if items is None:
        items = ctx["plan"].items
    if not isinstance(items, list) or not items:
        raise BusinessException("试卷没有题目，无法保存")

    # 复用 ctx 里的年级/学科做题目归属校验
    grade, subject = ctx["grade"], ctx["subject"]
    normalized = _normalize_items(db, user, items, grade.id, subject.id)
    total = round(sum(i["score"] for i in normalized), 2)

    std = ctx["standard"]
    paper = Paper(
        name=name, grade_id=grade.id, subject_id=subject.id,
        total_score=total,
        duration=int(data.get("duration") or (std.duration if std else 90)),
        difficulty_ratio=json.dumps(ctx["difficulty"], ensure_ascii=False),
        knowledge_coverage=json.dumps(
            ctx["reports"]["knowledge_report"], ensure_ascii=False),
        difficulty_report=json.dumps(
            ctx["reports"]["difficulty_report"], ensure_ascii=False),
        type_report=json.dumps(ctx["reports"]["type_report"], ensure_ascii=False),
        description=str(data.get("description") or "")[:2000] or None,
        exam_type=(std.exam_type if std else data.get("exam_type")),
        stage=_stage_of(grade),
        textbook_version=subject.textbook_version,
        standard_id=std.id if std else None,
        status=PaperStatus.DRAFT.value,
        share_scope=ShareScope.PRIVATE.value,
        generation_params=json.dumps({
            "mode": data.get("mode") or "custom",
            "source": ctx["source_strategy"],
            "sections": ctx["sections"],
            "difficulty_ratio": ctx["difficulty"],
            "knowledge_point_ids": ctx["kp_ids"],
            "standard_id": std.id if std else None,
            "avoid_recent": bool(data.get("avoid_recent", True)),
            # 缺口必须一起落库（P2-8）：前端编辑页的「缺口提示」读的就是
            # 这里，而旧实现只在**本次响应**里返回 gaps，页面一刷新就没了，
            # 教师只在下单那一瞬间看得到「第 3 大题还差 2 题」。
            "gaps": ctx["plan"].gaps,
        }, ensure_ascii=False),
        creator_id=user.id,
        source="ai" if (data.get("mode") == "ai") else "manual",
        current_version=1,
    )
    db.add(paper)
    db.flush()
    _write_items(db, paper, normalized)
    # 初始版本快照：便于"改坏了回溯到刚组出来的样子"
    version_svc.snapshot(db, paper, user.id, change_note="组卷创建")
    db.commit()
    db.refresh(paper)
    return ok({
        "id": paper.id, "name": paper.name, "total_score": paper.total_score,
        "item_count": len(normalized), "version": paper.current_version,
        "gaps": ctx["plan"].gaps,
        # 保存后的体检用**落库后的真实题项**（_write_items 已重排题号），
        # 而不是入参 normalized —— 入参顺序可能被重排，按它检查会误报题号不连续。
        "issues": compose_svc.audit_paper(
            [{
                "question_id": it.question_id,
                "type": it.question.type if it.question else None,
                "section_code": it.section_code,
                "section_name": it.section_name,
                "score": float(it.score or 0),
                "sort_order": it.sort_order,
            } for it in sorted(paper.items, key=lambda x: x.sort_order or 0)],
            total_score=float(paper.total_score or 0) or None,
        ),
    }, message="试卷已保存")


# ---------------------------------------------------------------- 题目规范化
# ---------------------------------------------------------------- 预览 / 编辑
@router.get("/{paper_id}/preview", summary="试卷预览（按大题分组，含答案解析）")
def preview_paper(
    paper_id: int, mode: str = Query("teacher", pattern="^(teacher|student)$"),
    db: Session = Depends(get_db),
    user: User = Depends(require_perm("paper:list")),
):
    """整卷预览。`mode=student` 不返回答案与解析（学生卷/教师卷双版本）。"""
    paper = db.get(Paper, paper_id)
    if not paper:
        raise NotFoundException("试卷不存在")
    _assert_readable(db, paper, user)
    return ok(_build_preview(db, paper, mode=mode))


@router.post("/{paper_id}/items", summary="保存题目列表（增删/排序/改分）")
def update_items(
    paper_id: int, body: UpdateItemsIn = Body(...), db: Session = Depends(get_db),
    user: User = Depends(require_perm("paper:write")),
):
    """整卷题目覆盖写。

    **被任务引用时会重算成绩**（用户决策：允许改并重算）。
    重算口径：按 question_id 匹配旧题项 → 保留学生作答（Answer 迁移到新 paper_item_id）
    → 按新分值重算主观题得分与提交总分。
    题目被移除时，其作答随题项级联删除（`paper_item_id` 非空 FK），
    返回值里的 `dropped_answers` 如实上报作废条数，前端需提示教师。
    """
    data = body.model_dump(exclude_unset=True)
    paper = db.get(Paper, paper_id)
    if not paper:
        raise NotFoundException("试卷不存在")
    _assert_can_edit(db, paper, user)

    # 乐观锁：前端把读到的 current_version 带回来，不匹配说明期间有人保存过。
    # 没有这道判定时，后保存者会用陈旧题表整卷覆盖，先保存者的改动被静默丢弃，
    # 双方都收到「已保存」（P1-9）。不带该字段的调用方（旧前端/脚本）保持原行为。
    client_version = data.get("current_version")
    if client_version is not None:
        try:
            client_version = int(client_version)
        except (TypeError, ValueError):
            raise BusinessException("current_version 必须是整数")
        server_version = int(paper.current_version or 1)
        if client_version != server_version:
            raise ConflictException(
                f"该试卷已被他人修改（你基于 v{client_version}，当前已是 "
                f"v{server_version}）。请刷新页面确认最新内容后再保存。",
                detail={"current_version": server_version,
                        "your_version": client_version},
            )

    raw_items = data.get("items")
    items = _normalize_items(db, user, raw_items, paper.grade_id, paper.subject_id)
    if not items:
        raise BusinessException("请至少保留一道题目")

    # 快照：改之前先存一份，便于回溯
    version_svc.snapshot(db, paper, user.id, change_note="编辑题目")

    # 顺序不可颠倒：_write_items 负责「插新→迁移作答→删旧」，
    # 必须先把作答迁移到新题项，之后才能按新分值重算（否则算的是已删的行）。
    write_stat = _write_items(db, paper, items)
    affected = _recalculate_after_change(db, paper, items)
    if "name" in data:
        name = str(data.get("name") or "").strip()
        if not name:
            raise BusinessException("试卷名称不能为空")
        paper.name = name[:128]
    if "description" in data:
        paper.description = str(data.get("description") or "")[:2000] or None
    if "duration" in data:
        try:
            paper.duration = max(1, min(300, int(data.get("duration"))))
        except (TypeError, ValueError):
            raise BusinessException("考试时长必须为整数")

    paper.current_version = (paper.current_version or 1) + 1
    version_svc.snapshot(db, paper, user.id, change_note="编辑完成")
    db.commit()
    msg = "试卷已更新"
    if write_stat.get("dropped"):
        msg += f"；移除的题目导致 {write_stat['dropped']} 条学生作答被作废"
    return ok({
        "id": paper.id, "total_score": paper.total_score,
        "item_count": len(items), "version": paper.current_version,
        "dropped_answers": write_stat.get("dropped", 0),
        # 保存后体检：编辑页保存完就能看到"这份卷子还能不能直接打印"。
        # 用落库后的题项（已重排题号），不用入参 items。
        "issues": compose_svc.audit_paper(
            [{
                "question_id": it.question_id,
                "type": it.question.type if it.question else None,
                "section_code": it.section_code,
                "section_name": it.section_name,
                "score": float(it.score or 0),
                "sort_order": it.sort_order,
            } for it in sorted(paper.items, key=lambda x: x.sort_order or 0)],
            total_score=float(paper.total_score or 0) or None,
        ),
        **affected,
    }, message=msg)


def _recalculate_after_change(
    db: Session, paper: Paper, new_items: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """按新分值重算受影响提交的成绩。

    前提：作答已由 `_write_items` 迁移到新题项（paper_item_id 已指向新行）。
    本函数只负责「改分」与「重算总分」，不碰题项增删——职责单一，
    避免和迁移逻辑互相覆盖（曾经两处都做删除，导致顺序一错就清空数据）。
    """
    task_ids = [r for r in db.scalars(
        select(Task.id).where(Task.paper_id == paper.id)).all()]
    if not task_ids:
        return {"affected_submissions": 0, "recalculated": False}

    submission_ids = [r for r in db.scalars(
        select(Submission.id).where(Submission.task_id.in_(task_ids))).all()]
    if not submission_ids:
        return {"affected_submissions": 0, "recalculated": False}

    # 当前卷的题项 → 新分值（按 paper_item_id 索引，因为作答已挂到新行）
    rows = db.execute(
        select(PaperItem.id, PaperItem.question_id).where(
            PaperItem.paper_id == paper.id)
    ).all()
    score_by_q = {int(i["question_id"]): float(i["score"]) for i in new_items}

    rescored = 0
    for item_id, qid in rows:
        new_full = score_by_q.get(int(qid))
        if new_full is None:
            continue
        answers = db.scalars(
            select(Answer).where(Answer.paper_item_id == int(item_id))).all()
        for ans in answers:
            old_full = float(ans.full_score or 0)
            got = float(ans.score or 0)
            ans.full_score = new_full
            if ans.is_correct is True:
                # 客观题：对就满分
                ans.score = new_full
            elif ans.is_correct is False:
                ans.score = 0
            elif old_full > 0:
                # 主观题：按得分率折算，保留教师给的相对评价
                ans.score = round(new_full * (got / old_full), 2)
            else:
                ans.score = 0
            rescored += 1
    db.flush()

    # 重算每份提交的总分与及格标记
    untouched = 0
    for sub_id in submission_ids:
        sub = db.get(Submission, sub_id)
        if not sub:
            continue
        answers = list(sub.answers or [])
        if not answers:
            # **无逐题作答行**（历史造数 / 外部导入）不能重算：`sum([])==0`
            # 会把总分写成 0，而 objective_score 保留旧值，
            # 成绩单就变成「总分 0 / 客观分 90 / 已自动批改」三行并列（P1-4）。
            # 这里跳过并如实上报，交给人工核对。
            untouched += 1
            continue
        # 客观题 = 已判对错（is_correct 非空）；主观题 = 尚未判分（is_correct 为空）。
        # 旧实现只写 `sub.score`，两个分列留在旧值上，总分与分列自相矛盾。
        objective = round(sum(
            float(a.score or 0) for a in answers if a.is_correct is not None), 2)
        subjective = round(sum(
            float(a.score or 0) for a in answers if a.is_correct is None), 2)
        total = round(objective + subjective, 2)
        sub.score = total
        sub.objective_score = objective
        sub.subjective_score = subjective
        task = db.get(Task, sub.task_id)
        if task and task.total_score:
            sub.is_passed = total >= float(task.pass_score or 0)

    return {
        "affected_submissions": len(submission_ids),
        "recalculated": True,
        "rescored_answers": rescored,
        # 跳过重算的提交数：没有逐题作答行，总分保持原值不动
        "skipped_no_answer": untouched,
    }


@router.post("/{paper_id}/items/{item_id}/regenerate", summary="AI 重新生成单题")
def regenerate_item(
    paper_id: int, item_id: int, body: RegenerateItemIn = Body(default_factory=RegenerateItemIn),
    db: Session = Depends(get_db),
    user: User = Depends(require_perm("paper:ai")),
):
    """替换单题为 AI 新生成的同题型同难度题目。

    返回**新的 question_id 与题干**，由前端确认后再调 `/items` 保存，
    避免"点一下就自动改卷"的误操作。
    """
    paper = db.get(Paper, paper_id)
    if not paper:
        raise NotFoundException("试卷不存在")
    _assert_can_edit(db, paper, user)

    item = db.get(PaperItem, item_id)
    if not item or item.paper_id != paper_id:
        raise NotFoundException("题目项不存在")
    old = item.question
    if not old:
        raise BusinessException("原题目已被删除，无法参考生成")

    from app.agents.question_agent import QuestionGeneratorAgent

    kp_id = old.knowledge_point_id
    agent = QuestionGeneratorAgent()
    res = agent.run(
        db, user_id=user.id, grade_id=paper.grade_id, subject_id=paper.subject_id,
        count=1, difficulty=old.difficulty, qtype=old.type,
        knowledge_point_id=kp_id, save=True,
    )
    data_ = res.get("data") or {}
    questions = data_.get("questions") or []
    if not questions:
        raise BusinessException(
            "AI 生成未成功：" + (res.get("message") or "请检查模型配置后重试"))

    q = questions[0]
    new_qid = q.get("id") or q.get("question_id")
    if not new_qid:
        raise BusinessException("AI 生成成功但未落库，请检查题库权限配置")
    # 回读落库后的完整题目：agent 返回的 dict 字段不全（可能缺 options/answer/解析），
    # 前端要拿这些字段直接渲染替换后的题面，缺了就只能显示空白。
    new_q = db.get(Question, int(new_qid))
    kp_name = None
    if new_q and new_q.knowledge_point_id:
        kp_name = db.scalar(
            select(KnowledgePoint.name).where(KnowledgePoint.id == new_q.knowledge_point_id))
    return ok({
        "old_question_id": old.id,
        "question_id": int(new_qid),
        "stem": new_q.stem if new_q else q.get("stem"),
        "type": new_q.type if new_q else q.get("type"),
        "difficulty": new_q.difficulty if new_q else q.get("difficulty"),
        "options": _load_json(new_q.options) if new_q else q.get("options"),
        "answer": _load_json(new_q.answer) if new_q else q.get("answer"),
        "analysis": new_q.analysis if new_q else q.get("analysis"),
        "knowledge_point_name": kp_name,
        "score": item.score,
        "section_code": item.section_code,
        "section_name": item.section_name,
        "is_fallback": bool(data_.get("is_fallback")),
    }, message="已生成替换题目，确认后保存")


@router.delete("/{paper_id}/items/{item_id}", summary="移除单题")
def remove_item(
    paper_id: int, item_id: int,
    # 用 Annotated 承载 Query 元数据：`force: bool = Query(False)` 的 **Python 级
    # 默认值**是 Query 实例（真值），绕过 HTTP 直接调用本函数时 `not force`
    # 永远为假，作答守卫会被静默跳过。
    force: Annotated[bool, Query(description="确认作废该题已有学生作答")] = False,
    db: Session = Depends(get_db),
    user: User = Depends(require_perm("paper:write")),
):
    """移除单题。**有学生作答时默认拒绝**，避免级联删除静默毁掉作答记录。

    `Answer.paper_item_id` 是 `ON DELETE CASCADE` 且非空：删掉 PaperItem
    会把该题项下所有 `edu_answer` 一起清掉，成绩、批注、错题记录全部归零。
    `_write_items` 已经用 `dropped` 如实上报这条代价，但这个单题删除入口
    此前直接 `db.delete(item)` 且只回「题目已移除」——教师点一下，
    学生做过的题就没了，界面上还看不出发生了什么（实测 1 行 → 0 行）。

    口径与 `_write_items` 对齐：
      * 删前统计作答数；有作答且未带 `force=true` → 400 并写明后果，
        前端据此弹二次确认；
      * 带 `force=true` 才允许删，并在响应里回传 `dropped`（作废条数）。
    """
    paper = db.get(Paper, paper_id)
    if not paper:
        raise NotFoundException("试卷不存在")
    _assert_can_edit(db, paper, user)
    item = db.get(PaperItem, item_id)
    if not item or item.paper_id != paper_id:
        raise NotFoundException("题目项不存在")
    if len(paper.items) <= 1:
        raise BusinessException("试卷至少保留一道题目")

    # 必须在 db.delete 之前数：删除会级联清空，事后再查就是 0。
    dropped = int(db.scalar(
        select(func.count()).select_from(Answer)
        .where(Answer.paper_item_id == item_id)) or 0)
    if dropped and not force:
        raise BusinessException(
            f"该题已有 {dropped} 条学生作答，移除会将其永久删除"
            "（成绩/批注/错题一并作废）。确认请带 force=true 重试。")

    version_svc.snapshot(db, paper, user.id, change_note="移除题目")
    removed_qid = int(item.question_id)
    db.delete(item)
    db.flush()
    # 逐题移除同样要让引用计数回到真实值：删掉最后一个引用后应归零，
    # 否则该题的 usage_count 会永久停在旧值上，一直排在"少用优先"的末尾。
    from app.services.question_usage import recount_usage
    recount_usage(db, {removed_qid})
    db.flush()
    # 重排剩余题项，避免 sort_order 出现空洞
    remaining = [it for it in paper.items if it.id != item_id]
    items = [{
        "question_id": it.question_id, "score": it.score,
        "section_code": it.section_code, "section_name": it.section_name,
        "section_sort": it.section_sort,
    } for it in remaining]
    db.flush()
    paper.total_score = round(sum(float(i["score"]) for i in items), 2)
    # 删题后必须重算成绩：作答被级联删除，`Submission.score` 若保持原值，
    # 就会与「试卷总分已变」对不上（P1-4 两条删题路径口径不一致）。
    # 剩余题项沿用原 id，作答仍挂在正确行上，可直接复用同一套重算逻辑。
    rescore = _recalculate_after_change(db, paper, items)
    paper.current_version = (paper.current_version or 1) + 1
    version_svc.snapshot(db, paper, user.id, change_note="移除题目完成")
    db.commit()
    return ok({"id": paper.id, "total_score": paper.total_score,
               "item_count": len(items), "dropped": dropped,
               **rescore},
              message=("题目已移除" if not dropped else
                       f"题目已移除，同时作废 {dropped} 条学生作答"))


@router.post("/{paper_id}/sections/rename", summary="大题改名")
def rename_section(
    paper_id: int, body: RenameSectionIn = Body(...), db: Session = Depends(get_db),
    user: User = Depends(require_perm("paper:write")),
):
    """按 section_code 批量改大题名（改名不打散分组）。"""
    data = body.model_dump(exclude_unset=True)
    paper = db.get(Paper, paper_id)
    if not paper:
        raise NotFoundException("试卷不存在")
    _assert_can_edit(db, paper, user)

    code = str(data.get("section_code") or "").strip()
    name = str(data.get("section_name") or "").strip()
    if not code:
        raise BusinessException("请指定大题标识 section_code")
    if not name:
        raise BusinessException("大题名称不能为空")

    rows = [it for it in paper.items if (it.section_code or it.question.type) == code]
    if not rows:
        raise BusinessException("该大题不存在")
    for it in rows:
        it.section_name = name[:64]
    paper.current_version = (paper.current_version or 1) + 1
    db.commit()
    return ok({"section_code": code, "section_name": name[:64],
               "affected": len(rows)}, message="大题名称已更新")


@router.post("/{paper_id}/restructure", summary="一键重构大题结构")
def restructure_paper(
    paper_id: int, body: RestructurePaperIn = Body(default_factory=RestructurePaperIn),
    db: Session = Depends(get_db),
    user: User = Depends(require_perm("paper:write")),
):
    """按题型重新归组并重排大题序号。

    适用场景：教师增删题目后，大题编号错乱 / 同名大题分裂成多个。
    只调整分组与序号，**不改题目内容与分值**。
    """
    paper = db.get(Paper, paper_id)
    if not paper:
        raise NotFoundException("试卷不存在")
    _assert_can_edit(db, paper, user)

    items = [{
        "question_id": it.question_id, "score": it.score,
        "section_code": it.section_code or (it.question.type if it.question else "single"),
        "section_name": it.section_name
        or TYPE_LABEL.get(it.question.type if it.question else "single", "综合题"),
        "section_sort": it.section_sort or 0,
        # 沿用已落库的题序：本接口只重建大题名/大题号，不应顺手重排题目，
        # 否则阶梯分值（第 9 题 12 分）会换到别的题上
        "section_pos": it.sort_order or 0,
        "score_override": it.score_override,
    } for it in paper.items]

    # 以标准大题名重建（若指定了标准）
    standard = db.get(ExamStandard, paper.standard_id) if paper.standard_id else None
    sec_names = {s["code"]: s["name"] for s in compose_svc.parse_sections(standard)}
    for it in items:
        code = it["section_code"]
        if code in sec_names:
            it["section_name"] = sec_names[code]

    version_svc.snapshot(db, paper, user.id, change_note="重构前")
    compose_svc._renumber(items)
    for it_row, it in zip(
        sorted(paper.items, key=lambda x: (x.section_sort or 0, x.sort_order or 0)), items):
        it_row.section_name = it["section_name"]
        it_row.section_code = it["section_code"]
        it_row.section_sort = it["section_sort"]
        it_row.sort_order = it["sort_order"]

    paper.current_version = (paper.current_version or 1) + 1
    version_svc.snapshot(db, paper, user.id, change_note="重构完成")
    db.commit()
    return ok({"sections": sorted({i["section_name"] for i in items}),
               "version": paper.current_version}, message="大题结构已重构")


# ---------------------------------------------------------------- 版本
@router.get("/{paper_id}/versions", summary="版本列表")
def list_versions(
    paper_id: int, db: Session = Depends(get_db),
    user: User = Depends(require_perm("paper:list")),
):
    paper = db.get(Paper, paper_id)
    if not paper:
        raise NotFoundException("试卷不存在")
    _assert_readable(db, paper, user)
    rows = db.scalars(
        select(PaperVersion).where(PaperVersion.paper_id == paper_id)
        .order_by(PaperVersion.version.desc())).all()
    return ok({
        "current_version": paper.current_version,
        "items": [{
            "id": v.id, "version": v.version, "change_note": v.change_note,
            "item_count": v.item_count, "total_score": v.total_score,
            "created_at": v.created_at,
            "created_by_name": db.scalar(
                select(User.real_name).where(User.id == v.created_by)),
        } for v in rows],
    })


@router.get("/{paper_id}/versions/{version}", summary="版本详情")
def get_version(
    paper_id: int, version: int, db: Session = Depends(get_db),
    user: User = Depends(require_perm("paper:list")),
):
    paper = db.get(Paper, paper_id)
    if not paper:
        raise NotFoundException("试卷不存在")
    _assert_readable(db, paper, user)
    row = db.scalar(select(PaperVersion).where(
        PaperVersion.paper_id == paper_id, PaperVersion.version == version))
    if not row:
        raise NotFoundException("版本不存在")
    return ok({
        "version": row.version, "change_note": row.change_note,
        "created_at": row.created_at,
        "snapshot": _load_json(row.snapshot),
    })


@router.get("/{paper_id}/versions/{version}/diff", summary="版本对比（回溯前先看差异）")
def diff_version(
    paper_id: int, version: int,
    against: str = Query("current", description="current（默认，与当前卷面对比）或版本号"),
    db: Session = Depends(get_db),
    user: User = Depends(require_perm("paper:list")),
):
    """对比某个历史版本与当前（或另一版本）的差异（F-02）。

    为什么值得做：回溯是不可逆操作（有学生提交时还要二次确认），而旧版本
    抽屉只显示「v3 · 编辑题目 · 18 题」——教师根本不知道 v3 与现在是"差一道题"
    还是"整卷重排"，只能盲选。快照里已冗余存了题干/答案/解析，算差异是免费的。

    `against=current` 走**现算**快照（`build_snapshot`），不读库里的最新版本行：
    最新一行可能是「回溯前」这类中间快照，与用户看到的卷面并不一致。
    """
    paper = db.get(Paper, paper_id)
    if not paper:
        raise NotFoundException("试卷不存在")
    _assert_readable(db, paper, user)

    before = version_svc.load_snapshot(db, paper_id, version)
    if before is None:
        raise NotFoundException("版本不存在")

    target = str(against or "current").strip().lower()
    if target in ("", "current", "now"):
        after = version_svc.build_snapshot(db, paper)
        after_label = f"当前（v{paper.current_version or 1}）"
    else:
        try:
            other = int(target)
        except (TypeError, ValueError):
            raise BusinessException("against 必须是 current 或一个版本号")
        after = version_svc.load_snapshot(db, paper_id, other)
        if after is None:
            raise NotFoundException("用于对比的版本不存在")
        after_label = f"v{other}"

    return ok(version_svc.diff_snapshots(
        before, after, before_label=f"v{version}", after_label=after_label))


@router.post("/{paper_id}/versions/{version}/restore", summary="回溯到指定版本")
def restore_version(
    paper_id: int, version: int, body: RestoreVersionIn = Body(default_factory=RestoreVersionIn),
    db: Session = Depends(get_db),
    user: User = Depends(require_perm("paper:write")),
):
    """把试卷恢复到历史版本。

    回溯本身也产生一个新版本（不改历史），符合"版本只增不改"的原则。
    题库中已删除的题目会被跳过并如实报告，不会静默丢题。

    **有学生提交时默认拒绝**：回溯会重写题项（插新 → 迁同题作答 → 删旧），
    旧版本里不存在的题目，其实作答无法迁移，只能丢弃 —— 学生的分数会变。
    这类操作不可逆，必须由调用方显式带 force=true 二次确认。
    """
    data = body.model_dump(exclude_unset=True)
    paper = db.get(Paper, paper_id)
    if not paper:
        raise NotFoundException("试卷不存在")
    _assert_can_edit(db, paper, user)

    row = db.scalar(select(PaperVersion).where(
        PaperVersion.paper_id == paper_id, PaperVersion.version == version))
    if not row:
        raise NotFoundException("版本不存在")

    sub_cnt = db.scalar(
        select(func.count()).select_from(Submission)
        .join(Task, Task.id == Submission.task_id)
        .where(Task.paper_id == paper_id)
    ) or 0
    if sub_cnt and not bool(data.get("force")):
        raise BusinessException(
            f"该试卷已有 {sub_cnt} 份学生提交。回溯会重写题目结构："
            f"旧版本中不存在的题目，其作答将被丢弃，相关学生分数会随之变化。"
            f"如确认承担此风险，请二次确认后重试。"
        )
    snapshot = _load_json(row.snapshot) or {}
    raw_items = snapshot.get("items") or []

    version_svc.snapshot(db, paper, user.id, change_note=f"回溯前（v{version}）")

    restore_items: List[Dict[str, Any]] = []
    missing: List[int] = []
    for it in raw_items:
        qid = it.get("question_id")
        if not qid:
            continue
        if not db.get(Question, int(qid)):
            missing.append(int(qid))
            continue
        restore_items.append({
            "question_id": int(qid),
            "score": float(it.get("score") or 5),
            "section_code": it.get("section_code") or it.get("type"),
            "section_name": it.get("section_name"),
            "section_sort": int(it.get("section_sort") or 0),
            "score_override": bool(it.get("score_override", False)),
        })
    if not restore_items:
        raise BusinessException("该版本的题目在题库中已全部删除，无法回溯")

    _write_items(db, paper, restore_items)
    paper_data = snapshot.get("paper") or {}
    # ★ 快照里存了 8 个卷级字段，旧实现只还原 name/duration —— 回溯产出的是
    #   「旧题项 + 新卷级元数据」的混合体：卷面说明、命题标准、难度分布都对不上，
    #   而 UI 写着"已回溯到 vN"，教师会以为完全回到历史状态（P1-5）。
    restored_fields: List[str] = []
    kept_fields: List[str] = []

    if paper_data.get("name"):
        paper.name = str(paper_data["name"])[:128]
        restored_fields.append("name")
    if paper_data.get("duration"):
        paper.duration = int(paper_data["duration"])
        restored_fields.append("duration")
    if paper_data.get("description") is not None:
        paper.description = paper_data["description"]
        restored_fields.append("description")
    if paper_data.get("difficulty_ratio") is not None:
        # 该列是 Text（存 JSON 字符串）；快照里可能已是 str 或 list/dict
        raw_ratio = paper_data["difficulty_ratio"]
        paper.difficulty_ratio = (
            raw_ratio if isinstance(raw_ratio, str)
            else json.dumps(raw_ratio, ensure_ascii=False))
        restored_fields.append("difficulty_ratio")
    if paper_data.get("exam_type"):
        paper.exam_type = paper_data["exam_type"]
        restored_fields.append("exam_type")
    std_id = paper_data.get("standard_id")
    if std_id:
        if db.get(ExamStandard, int(std_id)):
            paper.standard_id = int(std_id)
            restored_fields.append("standard_id")
        else:
            # 命题标准已被删除：保留当前值并说明，不能写一个悬空外键
            kept_fields.append("standard_id（原命题标准已删除，保留当前值）")
    # status 刻意不还原：把已发布/已归档的卷改回旧状态会绕过发布审批，
    # 属于状态机越权。这里如实告知，而不是悄悄回滚。
    kept_fields.append("status（不随回溯回滚，避免绕过发布审批）")

    paper.current_version = (paper.current_version or 1) + 1
    version_svc.snapshot(db, paper, user.id, change_note=f"回溯到 v{version}")
    db.commit()
    body = {"id": paper.id, "restored_from": version,
            "current_version": paper.current_version,
            "item_count": len(restore_items),
            "restored_fields": restored_fields,
            "kept_fields": kept_fields,
            # 总分一律按**已恢复的题项**重算（题库删题后历史总分不可信），
            # 与快照值不同就一并回传，让调用方能解释差异
            "total_score": paper.total_score,
            "snapshot_total_score": (snapshot.get("paper") or {}).get("total_score")}
    snap_total = (snapshot.get("paper") or {}).get("total_score")
    if snap_total is not None and abs(float(snap_total) - float(paper.total_score or 0)) > 0.01:
        # `_write_items` 按恢复后的题项重算总分，所以两者不同只可能是
        # 「快照里的部分题目在题库中已被删除、无法还原」
        body["total_score_note"] = (
            f"总分已按恢复后的题项重算为 {paper.total_score}，"
            f"与快照记录的 {snap_total} 不同（部分题目在题库中已删除）")
    if missing:
        body["missing_question_ids"] = missing
        body["warning"] = f"{len(missing)} 道题在题库中已删除，已跳过"
    return ok(body, message=f"已回溯到版本 v{version}")


# ---------------------------------------------------------------- 试卷库
@router.get("/library/list", summary="试卷库（我的/共享/公共/收藏）")
def paper_library(
    params: PageParams = Depends(),
    scope: str = Query("mine", pattern="^(mine|shared|public|favorite)$"),
    grade_id: Optional[int] = None,
    subject_id: Optional[int] = None,
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_perm("paper:list")),
):
    """三类目录 + 收藏。

    - mine：我创建的
    - shared：别人共享给我的（含范围共享）
    - public：公共库（审核通过的）
    - favorite：我收藏的
    """
    stmt = select(Paper)
    if scope == "mine":
        stmt = stmt.where(Paper.creator_id == user.id)
    elif scope == "shared":
        # 旧实现只写了 `share_scope in (grade, school)` —— 任何 teacher 都能在
        # 「共享给我」里看到**全校所有年级/所有学校的**范围共享卷（含标准答案），
        # 点进详情又被 `_assert_readable` 按年级/学校逐级校验拒掉（403）。
        # 这正是 `_paper_visibility_clause` 文档里禁止的「列表看得到、详情打不开」漂移。
        # 这里改为复用唯一可见性判定，并排除自己创建的卷。
        stmt = stmt.where(Paper.creator_id != user.id)
        shared_vis = _paper_visibility_clause(user)
        if shared_vis is not None:
            stmt = stmt.where(shared_vis)
    elif scope == "public":
        stmt = stmt.where(
            Paper.share_scope == ShareScope.PUBLIC.value,
            Paper.status == PaperStatus.PUBLISHED.value,
        )
    else:  # favorite
        stmt = stmt.where(Paper.id.in_(
            select(PaperFavorite.paper_id).where(PaperFavorite.user_id == user.id)))
        # 收藏后共享范围可能被撤回：仍用同一可见性判定过滤，避免收藏夹里留下打不开的卷
        fav_vis = _paper_visibility_clause(user)
        if fav_vis is not None:
            stmt = stmt.where(fav_vis)

    if grade_id:
        stmt = stmt.where(Paper.grade_id == grade_id)
    if subject_id:
        stmt = stmt.where(Paper.subject_id == subject_id)
    if keyword:
        stmt = stmt.where(Paper.name.like(f"%{keyword}%"))
    if status:
        stmt = stmt.where(Paper.status == status)

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(
        stmt.options(noload(Paper.items))
        .order_by(Paper.updated_at.desc(), Paper.id.desc())
        .offset(params.offset).limit(params.page_size)).all()

    ids = [p.id for p in rows]
    counts = dict(db.execute(
        select(PaperItem.paper_id, func.count()).where(PaperItem.paper_id.in_(ids))
        .group_by(PaperItem.paper_id)).all()) if ids else {}
    fav = set(db.scalars(
        select(PaperFavorite.paper_id).where(
            PaperFavorite.user_id == user.id, PaperFavorite.paper_id.in_(ids))
    ).all()) if ids else set()

    grade_names = {g.id: g.name for g in db.scalars(
        select(Grade).where(Grade.id.in_({p.grade_id for p in rows}))).all()} if rows else {}
    subject_names = {s.id: s.name for s in db.scalars(
        select(Subject).where(Subject.id.in_({p.subject_id for p in rows}))).all()} if rows else {}
    creator_names = {u.id: u.real_name for u in db.scalars(
        select(User).where(User.id.in_({p.creator_id for p in rows}))).all()} if rows else {}

    items = []
    for p in rows:
        d = dictify(p)
        d.update({
            "item_count": counts.get(p.id, 0),
            "grade_name": grade_names.get(p.grade_id),
            "subject_name": subject_names.get(p.subject_id),
            "creator_name": creator_names.get(p.creator_id),
            "is_favorite": p.id in fav,
            "is_mine": p.creator_id == user.id,
            "ai_source": (p.source or "").startswith("ai"),
        })
        items.append(d)
    return ok({"items": items, "total": total, "page": params.page, "scope": scope})


@router.post("/{paper_id}/favorite", summary="收藏/取消收藏")
def toggle_favorite(
    paper_id: int, body: ToggleFavoriteIn = Body(default_factory=ToggleFavoriteIn),
    db: Session = Depends(get_db),
    user: User = Depends(require_perm("paper:list")),
):
    data = body.model_dump(exclude_unset=True)
    paper = db.get(Paper, paper_id)
    if not paper:
        raise NotFoundException("试卷不存在")
    _assert_readable(db, paper, user)

    exists = db.scalar(select(PaperFavorite).where(
        PaperFavorite.paper_id == paper_id, PaperFavorite.user_id == user.id))
    want = data.get("favorite")
    if want is None:
        want = exists is None

    if want and not exists:
        db.add(PaperFavorite(paper_id=paper_id, user_id=user.id))
        db.commit()
        return ok({"favorite": True}, message="已收藏")
    if not want and exists:
        db.delete(exists)
        db.commit()
        return ok({"favorite": False}, message="已取消收藏")
    return ok({"favorite": bool(exists)}, message="状态未变化")


# ---------------------------------------------------------------- 共享与审核
@router.post("/{paper_id}/share-scope", summary="设置共享范围（私有/年级/全校）")
def set_share_scope(
    paper_id: int, body: SetShareScopeIn = Body(...), db: Session = Depends(get_db),
    user: User = Depends(require_perm("paper:write")),
):
    """设置试卷可见范围。

    - `private`：仅创建者
    - `grade`：同年级同学科教师（只读）
    - `school`：同校同学科教师（只读）
    - `public`：公共库全站可读——**不走这里**，必须经审核流
      （`/review` 提交 + 管理员 approve），否则等于绕过审核。

    范围共享一律只读；要给别人编辑权，用显式分享记录（`permission=edit`）。
    """
    data = body.model_dump(exclude_unset=True)
    paper = db.get(Paper, paper_id)
    if not paper:
        raise NotFoundException("试卷不存在")
    _assert_can_edit(db, paper, user)

    scope = str(data.get("scope") or "").strip().lower()
    if scope == ShareScope.PUBLIC.value:
        raise BusinessException(
            "公共库需走审核流程：先「提交审核」再由管理员通过，不能直接设为公开")
    if scope not in (ShareScope.PRIVATE.value, ShareScope.GRADE.value,
                     ShareScope.SCHOOL.value):
        raise BusinessException("scope 仅支持 private / grade / school")

    # 年级共享要求试卷本身有年级（Paper.grade_id 非空，建卷时已强制）
    if scope == ShareScope.GRADE.value and not paper.grade_id:
        raise BusinessException("该试卷未设置年级，无法按年级共享")
    if scope == ShareScope.SCHOOL.value and not user.school_name:
        raise BusinessException("当前账号未填写所属学校，无法按全校共享")

    paper.share_scope = scope
    paper.is_shared = scope != ShareScope.PRIVATE.value
    db.commit()
    label = {ShareScope.PRIVATE.value: "仅自己可见",
             ShareScope.GRADE.value: "同年级教师可查看",
             ShareScope.SCHOOL.value: "同校教师可查看"}[scope]
    return ok({"share_scope": paper.share_scope, "is_shared": paper.is_shared},
              message=f"共享范围已设为：{label}")


@router.get("/{paper_id}/share-info", summary="查看共享范围与协作者")
def share_info(
    paper_id: int, db: Session = Depends(get_db),
    user: User = Depends(require_perm("paper:list")),
):
    paper = db.get(Paper, paper_id)
    if not paper:
        raise NotFoundException("试卷不存在")
    _assert_readable(db, paper, user)
    rows = db.scalars(
        select(PaperShare).where(PaperShare.paper_id == paper_id)).all()
    names = dict(db.execute(
        select(User.id, User.real_name).where(
            User.id.in_([r.to_user_id for r in rows]))).all()) if rows else {}
    return ok({
        "share_scope": paper.share_scope or ShareScope.PRIVATE.value,
        "can_edit": _share_permission(db, paper, user) == SharePermission.EDIT.value,
        "members": [{
            "user_id": r.to_user_id,
            "name": names.get(r.to_user_id),
            "permission": r.permission or SharePermission.VIEW.value,
        } for r in rows],
    })


@router.post("/{paper_id}/review", summary="提交审核 / 审核通过 / 驳回")
def review_paper(
    paper_id: int, body: ReviewPaperIn = Body(...), db: Session = Depends(get_db),
    user: User = Depends(require_perm("paper:write")),
):
    """公共库审核流。

    action:
    - submit：教师申请进公共库（draft/published → pending）
    - approve：管理员通过（pending → published，share_scope=public）
    - reject：管理员驳回（pending → rejected），需给意见
    """
    data = body.model_dump(exclude_unset=True)
    paper = db.get(Paper, paper_id)
    if not paper:
        raise NotFoundException("试卷不存在")
    action = str(data.get("action") or "").strip().lower()
    if action not in ("submit", "approve", "reject"):
        raise BusinessException("action 仅支持 submit / approve / reject")

    if action == "submit":
        _assert_can_edit(db, paper, user)
        if paper.status == PaperStatus.PENDING.value:
            raise BusinessException("该试卷已在审核中，请等待审核结果")
        if paper.share_scope == ShareScope.PUBLIC.value and \
                paper.status == PaperStatus.PUBLISHED.value:
            raise BusinessException("该试卷已进入公共库")
        paper.status = PaperStatus.PENDING.value
        paper.review_comment = None
        db.commit()
        return ok({"status": paper.status}, message="已提交审核")

    if not _is_sys_admin(user) and not _is_grade_admin(user):
        raise PermissionException("仅管理员可审核试卷")
    if paper.status != PaperStatus.PENDING.value:
        raise BusinessException("该试卷不在待审核状态")

    paper.review_by = user.id
    paper.review_at = __import__("app.utils.common", fromlist=["now_local"]).now_local()
    if action == "approve":
        paper.status = PaperStatus.PUBLISHED.value
        paper.share_scope = ShareScope.PUBLIC.value
        paper.is_shared = True
        db.commit()
        return ok({"status": paper.status, "share_scope": paper.share_scope},
                  message="审核通过，已进入公共库")
    comment = str(data.get("comment") or "").strip()
    if not comment:
        raise BusinessException("驳回时必须填写审核意见")
    paper.status = PaperStatus.REJECTED.value
    paper.review_comment = comment[:2000]
    db.commit()
    return ok({"status": paper.status, "review_comment": paper.review_comment},
              message="已驳回")


# ---------------------------------------------------------------- 导出
@router.get("/{paper_id}/export/docx", summary="导出 Word（教师卷/学生卷）")
def export_docx(
    paper_id: int,
    mode: str = Query("teacher", pattern="^(teacher|student)$"),
    layout: str = Query("a4_single", pattern="^(a3_double|a4_single)$"),
    with_seal_line: bool = True,
    with_page_number: bool = True,
    db: Session = Depends(get_db),
    user: User = Depends(require_perm("paper:export")),
):
    paper = _requested_export(db, paper_id, user)
    preview = _build_preview(db, paper, mode=mode)
    buf = build_docx(preview, mode=mode, layout=layout,
                     with_seal_line=with_seal_line, with_page_number=with_page_number)
    fname = f"paper_{paper_id}_{mode}.docx"
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename={fname}"},
    )


@router.get("/{paper_id}/export/pdf", summary="导出 PDF（教师卷/学生卷）")
def export_pdf(
    paper_id: int,
    mode: str = Query("teacher", pattern="^(teacher|student)$"),
    layout: str = Query("a4_single", pattern="^(a3_double|a4_single)$"),
    with_seal_line: bool = True,
    with_page_number: bool = True,
    db: Session = Depends(get_db),
    user: User = Depends(require_perm("paper:export")),
):
    paper = _requested_export(db, paper_id, user)
    preview = _build_preview(db, paper, mode=mode)
    buf = build_pdf(preview, mode=mode, layout=layout,
                    with_seal_line=with_seal_line, with_page_number=with_page_number)
    fname = f"paper_{paper_id}_{mode}.pdf"
    return StreamingResponse(
        buf, media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={fname}"},
    )


@router.get("/{paper_id}/export/answer-sheet", summary="导出答题卡")
def export_answer_sheet(
    paper_id: int,
    layout: str = Query("a4_single", pattern="^(a3_double|a4_single)$"),
    db: Session = Depends(get_db),
    user: User = Depends(require_perm("paper:export")),
):
    paper = _requested_export(db, paper_id, user)
    preview = _build_preview(db, paper, mode="student")
    buf = build_answer_sheet(preview, layout=layout)
    return StreamingResponse(
        buf, media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=paper_{paper_id}_answersheet.pdf"},
    )


@router.get("/{paper_id}/export/html", summary="导出可打印 HTML")
def export_html(
    paper_id: int,
    mode: str = Query("teacher", pattern="^(teacher|student)$"),
    layout: str = Query("a4_single", pattern="^(a3_double|a4_single)$"),
    db: Session = Depends(get_db),
    user: User = Depends(require_perm("paper:export")),
):
    """HTML 预览版：不依赖 Word/PDF 引擎，浏览器直接打印。"""
    paper = _requested_export(db, paper_id, user)
    preview = _build_preview(db, paper, mode=mode)
    from app.services.paper_export_service import build_print_html
    html = build_print_html(preview, mode=mode, layout=layout)
    return StreamingResponse(
        io.BytesIO(html.encode("utf-8")), media_type="text/html; charset=utf-8",
        headers={"Content-Disposition": f"inline; filename=paper_{paper_id}.html"},
    )


# ---------------------------------------------------------------- 导出（异步，F-05）
# 同步端点保持不动（小卷用它们更快，且契约已在用）；异步版只是把「渲染 +
# 生成文件」从请求线程挪到后台线程，再给一个 30 分钟有效的下载链接。
# 复用 sys_agent_job：不新增表，也不必再造一套轮询协议。
class ExportJobIn(BaseModel):
    """导出任务入参。`kind` 决定产物，其余字段与同步端点同名同义。"""
    model_config = ConfigDict(extra="ignore")

    kind: str = Field(default="pdf", description="docx / pdf / answer_sheet")
    mode: str = Field(default="teacher", pattern="^(teacher|student)$")
    layout: str = Field(default="a4_single", pattern="^(a3_double|a4_single)$")
    with_seal_line: bool = True
    with_page_number: bool = True

    @field_validator("kind")
    @classmethod
    def _known_kind(cls, v: str) -> str:
        if v not in export_job.KINDS:
            raise ValueError(f"kind 只支持 {'/'.join(export_job.KINDS)}")
        return v


@router.post("/{paper_id}/export/jobs", summary="提交导出任务（异步，推荐）")
def create_export_job(
    paper_id: int,
    body: ExportJobIn = Body(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_perm("paper:export")),
):
    """提交导出任务，立即返回 job_id；轮询 `GET /export/jobs/{id}` 取下载链接。

    权限**在提交时**校验（`_requested_export` 会走 `_assert_readable`），
    下载时再校验一次属主 —— 只靠前者的话，一个知道 job_id 的人就能拿到
    别人导出好的卷子（卷子含答案）。
    """
    from app.models import AgentJob

    paper = _requested_export(db, paper_id, user)
    opts = export_job.options_for(
        body.kind, body.mode, body.layout,
        body.with_seal_line, body.with_page_number)
    # 顺手清理过期文件：不引调度任务，每次导出做一点，成本可忽略
    export_job.cleanup_expired(db)

    params = {"paper_id": paper.id}
    params.update(opts)
    job = AgentJob(
        user_id=user.id, agent=export_job.EXPORT_JOB_AGENT,
        status=agent_job_state.STATUS_PENDING, progress=0, stage="排队中",
        params=json.dumps(params, ensure_ascii=False),
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    threading.Thread(target=_run_export_job, args=(job.id,), daemon=True).start()
    return ok({"job_id": job.id, "status": job.status,
               "poll": f"/question/papers/export/jobs/{job.id}"},
              message=f"已提交导出，请轮询 /question/papers/export/jobs/{job.id}")


@router.get("/export/jobs/{job_id}", summary="查询导出任务状态")
def get_export_job(
    job_id: int, db: Session = Depends(get_db),
    user: User = Depends(require_perm("paper:export")),
):
    from app.models import AgentJob

    job = db.get(AgentJob, job_id)
    if not job or job.agent != export_job.EXPORT_JOB_AGENT:
        raise NotFoundException("导出任务不存在")
    if job.user_id != user.id and "sys_admin" not in user.role_codes:
        raise PermissionException("无权查看该导出任务")

    d = dictify(job)
    d["result"] = json.loads(job.result) if job.result else None
    return ok(agent_job_state.apply_timeout(
        job, d, timeout_seconds=agent_job_state.timeout_for(job.agent)))


@router.get("/export/jobs/{job_id}/file", summary="下载导出文件（30 分钟有效）")
def download_export_job(
    job_id: int, db: Session = Depends(get_db),
    user: User = Depends(require_perm("paper:export")),
):
    """短时效下载：过期回 410，未完成回 409，非属主回 403。"""
    path, filename, media_type = export_job.resolve_download(job_id, user, db)
    return FileResponse(path, media_type=media_type, filename=filename)


# ---------------------------------------------------------------- 异步组卷
# 为什么要异步：一组标准卷（5 个大题）在题库空时要并发补 5~6 批题，
# 实测单批 60~100s（生产 sys_agent_call_log 平均 100.7s），最坏 2 轮 ×240s
# 远超浏览器/网关的耐心。同步接口只会在前端等到超时、后端还在跑，
# 用户重试一次就多一份卷子。
#
# 复用 sys_agent_job（与 AI 出题/教案同一张表）：
#   POST /compose/ai/async  → {job_id}
#   GET  /compose/jobs/{id} → {status, progress, stage, result}
# 进度条只有补题阶段有意义（那里占 90% 的时间），其余阶段粗粒度推进。
COMPOSE_JOB_AGENT = "paper_compose"


@router.post("/compose/ai/async", summary="AI 一键组卷（异步任务，推荐）")
def compose_ai_async(
    body: ComposeAiAsyncIn = Body(...), db: Session = Depends(get_db),
    user: User = Depends(require_perm("paper:ai")),
):
    """提交组卷任务，立即返回 job_id；轮询 `/compose/jobs/{id}` 取结果。

    入参与同步接口 `/compose/ai` 完全一致，**包括"只写描述、不选年级学科"**：
    两者的参数解析共用 `_ai_resolve_params`，异步只是把等待从 HTTP 请求里挪走。
    """
    data = body.model_dump(exclude_unset=True)
    from app.models import AgentJob

    request = str(data.get("request") or "").strip()
    if not request and not (data.get("grade_id") and data.get("subject_id")):
        raise BusinessException("请填写组卷需求描述，或至少选择年级与学科")
    if len(request) > 2000:
        raise BusinessException("组卷需求描述过长（上限 2000 字）")

    job = AgentJob(
        user_id=user.id, agent=COMPOSE_JOB_AGENT, status="pending",
        progress=0, stage="排队中",
        params=json.dumps(data, ensure_ascii=False),
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    threading.Thread(target=_run_compose_job, args=(job.id,), daemon=True).start()
    return ok({"job_id": job.id, "status": job.status},
              message=f"已提交，请轮询 /question/papers/compose/jobs/{job.id}")


@router.get("/compose/jobs/{job_id}", summary="查询组卷任务状态与结果")
def get_compose_job(
    job_id: int, db: Session = Depends(get_db),
    user: User = Depends(require_perm("paper:ai")),
):
    from app.models import AgentJob
    from app.services import agent_job_state

    job = db.get(AgentJob, job_id)
    if not job or job.agent != COMPOSE_JOB_AGENT:
        raise NotFoundException("任务不存在")
    if job.user_id != user.id and "sys_admin" not in user.role_codes:
        raise PermissionException("无权查看该任务")

    d = dictify(job)
    d["result"] = json.loads(job.result) if job.result else None
    # 僵尸任务判定：进程重启会丢后台线程，status 永停 running。
    # 判据单点定义在 agent_job_state（与 /agent/jobs 同一套）。
    return ok(agent_job_state.apply_timeout(job, d))


@router.post("/compose/jobs/{job_id}/cancel", summary="取消组卷任务")
def cancel_compose_job(
    job_id: int, db: Session = Depends(get_db),
    user: User = Depends(require_perm("paper:ai")),
):
    """请求取消组卷任务（F-04）。

    **协作式取消，不是立刻杀线程**：LLM 往返是同步 HTTP 调用，无法中断。
    这里只登记请求，worker 在批次边界（`on_progress`）看到就中止并写
    `cancelled`。前端必须继续轮询到终态，不能点完就当作已停止。

    幂等：已结束 / 已登记过取消都返回 200 + 说明，不报错 —— 用户连点两下
    取消按钮不该看到红色报错。
    """
    from app.models import AgentJob
    from app.services import agent_job_state

    job = db.get(AgentJob, job_id)
    if not job or job.agent != COMPOSE_JOB_AGENT:
        raise NotFoundException("任务不存在")
    if job.user_id != user.id and "sys_admin" not in user.role_codes:
        raise PermissionException("无权操作该任务")

    # 僵尸任务直接说清楚：对一个后台线程早已消失的任务登记取消，
    # 用户会看到"正在等待当前批次结束"，而那个批次永远不会结束。
    if agent_job_state.is_timed_out(
            job.status, job.created_at,
            timeout_seconds=agent_job_state.timeout_for(job.agent)):
        raise BusinessException(
            "任务已超时中断（后台线程已丢失），无需取消，请直接重新组卷")

    res = agent_job_state.request_cancel(db, job)
    data = {"status": job.status}
    data.update({"accepted": res.get("accepted"), "message": res.get("message"),
                 "cancel_requested": int(job.cancel_requested or 0)})
    return ok(data, message=res.get("message") or "已处理")
