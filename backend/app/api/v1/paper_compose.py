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
import re
import threading
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Annotated, Any, Callable, Dict, List, Optional

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
from app.services import llm_breaker
from app.services.exam_structures import section_total, sections_for
from app.services.paper_export_service import (
    build_answer_sheet, build_docx, build_pdf,
)
from app.services import paper_version_service as version_svc
from app.utils.common import PageParams, dictify, now_local, ok

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

# 判据用词：命中即视为「输出预算被推理吃光」，值得减半重试（换别的失败原因
# 重试纯属浪费一次 60~90s 的模型往返）。
_BUDGET_FAILURE_HINTS = ("正文为空", "max_tokens", "截断", "tokens")


def _fill_fail_hint(data: Dict[str, Any]) -> str:
    """把补题失败翻译成一句教师能懂的原因（供缺口卡片逐条展示）。"""
    reason = str(data.get("reason") or "").strip()
    tip = str(data.get("tip") or "").strip()
    raw = reason or tip
    if not raw:
        return "模型未返回题目，题库也没有可复用的同题型题"
    if any(k in raw for k in ("未配置", "API_KEY", "鉴权", "熔断")):
        return f"AI 不可用：{raw}"
    if _is_budget_failure(raw):
        return "模型输出预算被推理过程耗尽，返回正文为空"
    return f"模型未返回可用题目：{raw}"


def _is_budget_failure(text: str) -> bool:
    """是否为「输出预算被推理 token 吃光」这一类可重试失败。"""
    return any(k in str(text or "") for k in _BUDGET_FAILURE_HINTS)


def _gap_action(reason: str, *, ai_tried: bool) -> str:
    """缺口卡片上的「下一步怎么办」——按真实原因给动作，别一句通用文案打发。

    旧实现无论什么原因都写「可切换到『题库优先 + AI 补充』」，而教师**很可能
    已经在这个策略下**（AI 也确实调用过、失败了），照着提示点来点去还是补不上。
    """
    r = str(reason or "")
    if not ai_tried:
        return "可切换到「题库优先 + AI 补充」由 AI 补题，或先在题库补充该题型的已发布题目。"
    if "预算" in r or "正文为空" in r:
        return ("AI 因单批题量过大未能返回题目。可稍后重试，或把该大题题量调小 / "
                "分两次组卷；也可改用「仅使用题库」。")
    if "不可用" in r or "鉴权" in r or "熔断" in r or "配额" in r:
        return "AI 当前不可用，请联系管理员检查模型密钥与配额，或改用「仅使用题库」。"
    return ("请先在题库补充该题型的**已发布**题目；若「待审核库」里已有 AI 生成的草稿题，"
            "审核通过后即可直接用于组卷。")


def _mark_gaps_reason(gaps: List[Dict[str, Any]], reason: str) -> None:
    """给整批缺口统一挂上失败原因（熔断/冷却这类"一个都没补"的早退路径用）。"""
    for g in gaps:
        g["miss"] = int(g["need"]) - int(g.get("got", 0))
        g["reason"] = reason
        g["ai_tried"] = True
        g["action"] = _gap_action(reason, ai_tried=True)


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


def _grade_subject(db: Session, grade_id: Any, subject_id: Any):
    try:
        gid = int(grade_id) if grade_id else 0
        sid = int(subject_id) if subject_id else 0
    except (TypeError, ValueError):
        raise BusinessException("请选择年级和学科")
    grade = db.get(Grade, gid) if gid else None
    subject = db.get(Subject, sid) if sid else None
    # 原实现未校验年级存在性，grade_id 不存在时 INSERT 触发 FK 约束 → 500。
    # 这里前置校验并给出可操作提示。
    if not grade:
        raise BusinessException("请选择有效的年级")
    if not subject:
        raise BusinessException("请选择有效的学科")
    if subject.grade_id != grade.id:
        raise BusinessException(
            f"学科「{subject.name}」不属于{grade.name}，请重新选择")
    return grade, subject


# ---------------------------------------------------------------- AI 参数可信化
# **模型给出的 id 一律当"猜测"处理**：提示词里只写了「学科ID」，而模型看不到我们的
# id 空间，只能瞎猜小整数。实测它给七年级数学卷返回 subject_id=2 —— 那是**一年级**
# 数学的 id，于是 `_grade_subject` 直接 400「学科「数学」不属于七年级」，
# 用户看到的就是"AI 组卷用不了"。模型能可靠输出的只有**名称**，因此这里按
# 「年级 + 学科名」重新解析，id 仅在没有名称时才作为线索使用。
_CN_NUM = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
           "六": 6, "七": 7, "八": 8, "九": 9}
_GRADE_ALIAS = {"小一": 1, "小二": 2, "小三": 3, "小四": 4, "小五": 5, "小六": 6,
                "初一": 7, "初二": 8, "初三": 9}


def _resolve_standard(
    db: Session, *, grade: Grade, subject: Subject, standard_id: Optional[int],
) -> Optional[ExamStandard]:
    """选定命题标准：显式指定 > 同学段学科默认 > 同学段学科任一启用标准。"""
    if standard_id:
        std = db.get(ExamStandard, int(standard_id))
        if not std:
            raise BusinessException("指定的命题标准不存在")
        if not std.is_active:
            raise BusinessException("指定的命题标准已停用")
        return std

    stage = _stage_of(grade)
    stmt = select(ExamStandard).where(
        ExamStandard.stage == stage,
        ExamStandard.subject_name == subject.name,
        ExamStandard.is_active.is_(True),
    )
    default = db.scalar(stmt.where(ExamStandard.is_default.is_(True)))
    if default:
        return default
    return db.scalar(stmt.order_by(ExamStandard.sort, ExamStandard.id))


# ---------------------------------------------------------------- 参数解析
def _parse_sections_input(raw: Any) -> Optional[List[Dict[str, Any]]]:
    """前端自定义题型结构：允许给 code/count/score_per，或 code/count/score_pattern。

    `score_pattern` 是「同一大题内每题分值不同」的分值序列（数学解答题
    6/6/6/8·、化学选择 8×1+5×2）。只给序列不给 score_per 时按平均值补上，
    因为下游多处只读 score_per（报告展示、补题默认分值）。
    """
    if raw in (None, "", []):
        return None
    if not isinstance(raw, list):
        raise BusinessException("题型结构格式错误")
    result: List[Dict[str, Any]] = []
    for idx, item in enumerate(raw, start=1):
        if not isinstance(item, dict):
            raise BusinessException("题型结构格式错误")
        code = str(item.get("code") or item.get("type") or "").strip().lower()
        if code not in TYPE_LABEL:
            raise BusinessException(f"题型不合法：{code!r}")
        try:
            count = int(item.get("count") or 0)
            score_per = float(item.get("score_per") or 0)
        except (TypeError, ValueError):
            raise BusinessException("题型题量/分值必须为数字")
        if count <= 0:
            continue  # 题量 0 视为不需要该题型，忽略而非报错
        pattern = compose_svc.parse_score_pattern(item.get("score_pattern"), count)
        if pattern:
            if score_per <= 0:
                score_per = round(sum(pattern) / count, 2)
        elif score_per <= 0:
            raise BusinessException(f"题型「{TYPE_LABEL[code]}」单题分值必须大于 0")
        result.append({
            "code": code,
            "name": str(item.get("name") or TYPE_LABEL[code])[:64],
            "count": count,
            "score_per": round(score_per, 2),
            **({"score_pattern": pattern} if pattern else {}),
            "difficulty": str(item.get("difficulty") or "medium"),
            "sort": idx,
        })
    return result or None


def _resolve_ai_grade(db: Session, parsed: Dict[str, Any], request: str) -> Optional[Grade]:
    """把 AI 解析结果归一到真实的 Grade 记录上（按年级序号，不按主键猜）。"""
    import re

    def by_num(num: Optional[int]) -> Optional[Grade]:
        if not num or not (1 <= int(num) <= 9):
            return None
        return db.scalar(select(Grade).where(Grade.grade_num == int(num)))

    # 1) 显式年级序号字段（提示词优先要求 grade_num）
    for key in ("grade_num", "grade"):
        val = parsed.get(key)
        if isinstance(val, (int, float)) or (isinstance(val, str) and val.isdigit()):
            hit = by_num(int(val))
            if hit:
                return hit
    # 2) grade_id 当年级序号用：`Grade.id` 与 `grade_num` 目前恰好同值，
    #    但按 grade_num 查才是语义正确的（主键顺序不保证）。
    raw = parsed.get("grade_id")
    if isinstance(raw, (int, float)) or (isinstance(raw, str) and str(raw).isdigit()):
        hit = by_num(int(raw))
        if hit:
            return hit
    # 3) 年级名称
    name = str(parsed.get("grade_name") or "").strip()
    if name:
        hit = db.scalar(select(Grade).where(Grade.name == name))
        if hit:
            return hit
    # 4) 从原始需求文本里抠「七年级 / 7年级 / 初一」
    text = str(request or "")
    m = re.search(r"([一二三四五六七八九1-9])\s*年级", text)
    if m:
        ch = m.group(1)
        hit = by_num(_CN_NUM.get(ch) or int(ch))
        if hit:
            return hit
    for alias, num in _GRADE_ALIAS.items():
        if alias in text:
            hit = by_num(num)
            if hit:
                return hit
    return None


def _resolve_ai_subject(
    db: Session, grade: Optional[Grade], parsed: Dict[str, Any], request: str,
) -> Optional[Subject]:
    """在**指定年级内**按名称解析学科；id 只在名称缺失时作线索。"""
    if not grade:
        return None
    subs = db.scalars(select(Subject).where(Subject.grade_id == grade.id)).all()
    if not subs:
        return None
    by_name = {s.name: s for s in subs}

    # 1) 名称字段（提示词优先要求 subject_name）
    for key in ("subject_name", "subject", "course", "subject_text"):
        val = str(parsed.get(key) or "").strip()
        if not val:
            continue
        if val in by_name:
            return by_name[val]
        for s in subs:               # 容忍「数学学科」「初中数学」这类写法
            if val in s.name or s.name in val:
                return s
    # 2) id 只有落在本年级内才可信
    raw = parsed.get("subject_id")
    if isinstance(raw, (int, float)) or (isinstance(raw, str) and str(raw).isdigit()):
        s = db.get(Subject, int(raw))
        if s and s.grade_id == grade.id:
            return s
    # 3) 需求文本里出现的学科名（长名优先，避免"数学"被"数学与生活"抢走）
    text = str(request or "")
    for s in sorted(subs, key=lambda x: -len(x.name)):
        if s.name and s.name in text:
            return s
    return None


# ---------------------------------------------------------------- 补题去重
def _stem_key(text: Any) -> str:
    """题干归一化：去 HTML 标签、空白、标点，只留中文/字母/数字。

    模型每次生成的题干措辞都不同（「下列关于…的说法正确的是」vs
    「以下关于…说法正确」），按 fingerprint 精确匹配完全拦不住，
    必须先归一化再做近似比较。
    """
    plain = re.sub(r"<[^>]+>", "", str(text or ""))
    return re.sub(r"[^\w\u4e00-\u9fff]", "", plain).lower()


def _is_similar_stem(a: str, b: str, threshold: float = 0.80) -> bool:
    """题干近似判重：**单字与二元组 Jaccard 取较大值**。

    为什么不能只用二元组：实测「下列关于声现象的说法，正确的是」与
    「以下关于声现象说法正确的是」的 bigram 相似度只有 0.56 —— 换了两个词
    就掉到阈值以下，而人一眼就知道是同一道题。单字集合对这种改写更敏感
    （0.857），但单字对长题干会因常用字大量重叠而误判。

    两者取 max 正好互补：短题改写靠单字识别，长题精确保留靠二元组。
    阈值 0.80：实测同考点不同题目在 0.6 以下，改写题在 0.85 以上。

    性能：集合运算，400 条对照 × 10 题 ≈ 几十毫秒，远快于编辑距离。
    """
    if not a or not b:
        return False
    if a == b:
        return True
    # 长度差超过一半基本不可能是同一道题的改写，先短路省掉集合运算
    if abs(len(a) - len(b)) > max(len(a), len(b)) * 0.5:
        return False

    uni_a, uni_b = set(a), set(b)
    uni = len(uni_a & uni_b) / len(uni_a | uni_b) if uni_a and uni_b else 0.0
    if uni >= threshold:
        return True

    bi_a = {a[i:i + 2] for i in range(len(a) - 1)}
    bi_b = {b[i:i + 2] for i in range(len(b) - 1)}
    bi = len(bi_a & bi_b) / len(bi_a | bi_b) if bi_a and bi_b else 0.0
    return bi >= threshold


def _existing_stem_keys(
    db: Session, grade_id: int, subject_id: int, qtype: str, limit: int = 400,
) -> List[str]:
    """取该学科该题型的既有题干（归一化后）作为对照集合。

    只取最近 N 条：更老的题与新生成题重合的概率很低，而全量扫描会随题库
    增长线性变慢（每次补题都要读一遍）。
    """
    rows = db.scalars(
        select(Question.stem).where(
            Question.grade_id == grade_id,
            Question.subject_id == subject_id,
            Question.type == qtype,
        ).order_by(Question.id.desc()).limit(limit)
    ).all()
    return [k for k in (_stem_key(x) for x in rows) if k]


def _fill_one_gap(
    gap: Dict[str, Any], *,
    user_id: int, is_admin: bool, grade_id: int, subject_id: int,
    default_diff: str,
    used_ids: Optional[set] = None,
    source: str = "ai_fill",
) -> Dict[str, Any]:
    """为**单个大题**补题，跑在自己的 Session 里（因此可并行）。

    为什么必须独立 Session：SQLAlchemy 的 `Session` 不是线程安全的，跨线程共用
    会撞出 "This session is in 'prepared' state" 之类的随机错误。这里只接受
    标量参数（id / bool / str），不接收 ORM 对象 —— 传对象就等于把某个线程的
    session 泄漏到另一个线程。

    不抛异常：单个大题失败（模型超时、无同题型题）不该拖垮整卷，原因通过
    `notes` 回传给调用方拼进 message，同时写进 `out["reason"]` 供缺口卡片
    逐条展示（P1：教师不必再从一长串 message 里找原因）。

    返回 `{"gap", "items", "notes", "filled", "reason"}`，`items` 已是可直接追加进 plan 的字典。
    """
    from app.agents.question_agent import QuestionGeneratorAgent
    # 函数内导入：question.py 与本模块互相引用，放模块顶层会形成循环导入
    from app.api.v1.question import normalize_question_type
    from app.core.database import SessionLocal
    from app.services.question_access import question_usable_error

    name = str(gap.get("name") or "未知大题")
    out: Dict[str, Any] = {"gap": gap, "items": [], "notes": [], "filled": 0,
                           "reason": "", "ai_tried": True}
    take = max(0, int(gap["need"]) - int(gap.get("got", 0)))
    if take <= 0:
        return out
    # 本函数自己采纳的 question_id 也要进禁复用集合：`used_ids` 是调用方传进来的
    # **快照**（`set(plan.used_question_ids)`），补题过程中不会回写，同一大题补
    # 多批时第二批还能把第一批已选中的 published 题再拿一次（跨批次重复）——
    # 反向验证时会表现为"题库只有 3 道题却硬凑出 8 道、gaps 归零"。
    #
    # 关键：**原地复用传入的 set，不要 copy**。并行补题时各线程拿到的是同一个
    # 对象引用，原地 `add` 才能让不同大题之间也互斥（copy 就退回各写各的）。
    # CPython 下 `set.add` / `in` 是原子的（GIL 保护），元素是 int，无需加锁。
    seen_ids: set = used_ids if isinstance(used_ids, set) else set(used_ids or ())

    gtype = str(gap.get("code") or "single")
    gdiff = str(gap.get("difficulty") or default_diff)

    # 单批题量上限按题型分档、困难题再对折（见 _fill_batch_cap 的实测依据）。
    # 缺口 20 题时一次调用会撞 LLM_MAX_TOKENS 导致 JSON 截断，必须拆成多批循环；
    # 而不同题型的单题正文量差一个量级，统一 10 道必然让重题型先撞墙。
    # 难度是**独立于题型**的第三个变量：困难题的推理开销会把预算吃光（正文 0 字）。
    batch_cap = _fill_batch_cap(gtype, gdiff)

    db = SessionLocal()
    try:
        # 补题去重：先把该学科该题型的既有题干取出来做对照。
        # 反复预览 / 反复组卷会把题库堆成几百道「考同一个点、只换了说法」的题，
        # 而 fingerprint 是精确哈希，拦不住改写。
        existing_keys = _existing_stem_keys(db, grade_id, subject_id, gtype)
        new_keys: List[str] = []
        skipped_dup = 0
        stall_retry = 0   # 返回了题但全被过滤（重复/无权/题型不符）
        budget_retried = False  # 模型返回空正文（输出预算被推理耗尽）已减半重试过

        while out["filled"] < take:
            batch = max(1, min(batch_cap, take - out["filled"]))
            try:
                res = QuestionGeneratorAgent().run(
                    db, user_id=user_id, grade_id=grade_id, subject_id=subject_id,
                    question_type=gtype, count=batch, difficulty=gdiff, save=True,
                    allow_all_banks=is_admin,
                    # 来源标记与「题库页主动出题」的 ai 区分开：
                    # 组卷补题是副产物，预览一次就会落一批 draft 题，
                    # 混在一起以后没法批量清理。
                    source=source,
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "AI 补题失败（grade=%s subject=%s type=%s need=%s）: %s",
                    grade_id, subject_id, gtype, take - out["filled"], exc)
                out["reason"] = f"补题调用异常：{exc}"
                out["notes"].append(f"{name}补题失败：{exc}")
                break

            if not (res or {}).get("success", True):
                out["reason"] = str(res.get("message") or "补题执行失败")
                out["notes"].append(f"{name}补题失败：{out['reason']}")
                break
            data = (res or {}).get("data") or {}
            got = data.get("questions") or []
            if not got:
                # 模型返回空正文，或规则引擎降级后题库里也没有可复用的同题型题。
                # 判据必须用**原始原因**：翻译后的文案会带「已重试」字样。
                raw_reason = str(data.get("reason") or data.get("tip") or "")
                # **只对「预算被推理吃光」这一类重试，且批次减半**：同一提示词
                # 原样重发几乎必然再撞同一个上限（生产实测 10 道单选的两次
                # 调用都是 out=8192 / 正文 0）；减半才有意义（10 → 5）。
                # 未配置 Key / 鉴权失败属于确定性失败，重试纯浪费时间。
                if not budget_retried and _is_budget_failure(raw_reason):
                    budget_retried = True
                    batch_cap = max(1, batch // 2)
                    logger.info(
                        "AI 补题空正文（type=%s count=%s），批次减半为 %s 重试",
                        gtype, batch, batch_cap)
                    continue
                hint = _fill_fail_hint(data)
                if budget_retried:
                    hint += "（已缩小批次重试仍失败）"
                out["reason"] = hint
                out["notes"].append(f"{name}补题失败：{hint}")
                break

            progressed = 0
            for q in got:
                if out["filled"] >= take:
                    break
                qid = q.get("id") or q.get("question_id")
                if not qid:
                    continue
                qid_int = int(qid)
                qrow = db.get(Question, qid_int)
                if not qrow:
                    continue
                # 1) 只接受当前用户可用的题：规则引擎 fallback 会复用「任意已发布题」，
                #    其中可能含他人私有题——若放进来，预览看得到、保存时却被
                #    `_normalize_items` 拒（"无权使用题目"），必须提前过滤。
                if question_usable_error(qrow, user_id=user_id, is_admin=is_admin):
                    continue
                # 2) 题型必须与本大题一致：fallback 不按题型筛选，混进来会让
                #    "填空题"大题里出现单选题。
                if normalize_question_type(qrow.type, strict=False) != gtype:
                    continue
                # 3) 题干近似去重：与题库已有题、本批已采纳的题都不能撞。
                #    跳过重复会让缺口补不满，但比把 10 道同义题塞进卷子好 ——
                #    缺题会如实上报，重复题打印出来是事故。
                #
                #    **只对 AI 新造的题（draft）做去重**：无 LLM 时
                #    `QuestionGeneratorAgent` 走 `fallback()`，它是从题库
                #    检索复用（只取 published），与题库必然 100% 相似 ——
                #    一律去重会让"AI 补题"在降级路径上永远补不到题，
                #    表现为"模型未启用 → 整卷缺口补不上"。
                #    published 的题由本卷已用集合（plan 级全局互斥）拦重复。
                if qrow.status != "draft":
                    if qid_int in seen_ids:
                        continue
                else:
                    stem_key = _stem_key(qrow.stem)
                    if any(_is_similar_stem(stem_key, k) for k in existing_keys) \
                            or any(_is_similar_stem(stem_key, k) for k in new_keys):
                        skipped_dup += 1
                        continue
                    new_keys.append(stem_key)
                # 采纳即登记：published 题在**同一大题的多批次**之间必须互斥，
                # 否则第二批会把第一批选中的题再补一遍（卷内出现两道同题）。
                seen_ids.add(qid_int)
                # 按位置取分：该大题在本题库中已抽到 got 道，本次补的是第
                # got+filled 道。阶梯分值（数学解答题 6/6/6/8…、化学选择
                # 8×1+5×2）靠这一步才能保住，否则补出来的题全是平均分，
                # 压轴题的 11、12 分会被抹成 8 分。
                pos = int(gap.get("got", 0)) + out["filled"]
                pattern = gap.get("score_pattern") or []
                if isinstance(pattern, (list, tuple)) and pos < len(pattern):
                    score_one = float(pattern[pos])
                else:
                    score_one = float(gap.get("score_per") or 0)
                out["filled"] += 1
                progressed += 1
                out["items"].append({
                    "question_id": int(qid),
                    "type": qrow.type,
                    "type_label": TYPE_LABEL.get(qrow.type, qrow.type),
                    "stem": qrow.stem,
                    "difficulty": qrow.difficulty or gdiff,
                    "score": round(score_one, 2),
                    # 卷面槽位：_renumber 按它排序，保证「第 N 题拿第 N 档分值」
                    "section_pos": pos,
                    "section_code": gtype,
                    "section_name": name,
                    "section_sort": gap.get("sort", 0),
                    "knowledge_point_id": qrow.knowledge_point_id,
                    "knowledge_point_name": "AI 生成",
                })

            if progressed == 0:
                # 这一批全被过滤（重复/无权/题型不符）。
                # 允许再换一批试一次：模型偶发把同一道题换个说法再出一遍很常见，
                # 直接放弃会让缺口变成"明明能补却报缺"。但最多重试一次，
                # 避免模型持续输出重复题时空转。
                stall_retry += 1
                if stall_retry > 1:
                    out["reason"] = "模型生成的题目与题库重复，未能选出可用题"
                    break
                continue

        if skipped_dup:
            # 说明「仍留在题库」：agent 落库发生在采纳之前，这里是事后过滤，
            # 重复题已经在库里（draft 态）。不说明的话老师会以为题没生成。
            out["notes"].append(
                f"{name}跳过 {skipped_dup} 道与题库重复的题（未选入试卷，仍留在题库待审核）")
        return out
    finally:
        db.close()


# ---------------------------------------------------------------- 预览态重新生成
# 组卷结果**保存之前**在前端是纯内存数组（`plan.items` 只活在响应里），
# 没有 paper_id / item_id 可用 —— 所以既有的
# `POST /{paper_id}/items/{item_id}/regenerate`（面向已落库的试卷）帮不上忙。
# 这里按「当前预览快照」重新出题：前端把整卷题目连同要替换的位置一起发上来，
# 后端只重算被点名的那几道，其余原样返回，教师改过的题干/分值不会被覆盖。
REGEN_MAX_COUNT = 20   # 单次最多重生 20 题（全为作文时已经要跑 10 轮模型）


def _regen_targets(items: List[Dict[str, Any]], section_code: str) -> List[int]:
    """取某大题内、题型与 section_code 一致的题目下标（保持卷面顺序）。"""
    code = str(section_code or "").strip().lower()
    return [i for i, it in enumerate(items)
            if str(it.get("section_code") or it.get("type") or "").lower() == code]


def _regen_forbid_ids(items: List[Dict[str, Any]]) -> set:
    """生成时禁止复用的 question_id = **本卷全部已有题目**。

    注意不能只排除「范围外」的题：被重生那道题自己也在卷面上，若允许复用它的
    id，点「重新生成」会原地返回同一道题（教师看到毫无变化，还以为按钮失效）。
    重生的新题在采纳后同样加入集合，保证整段重生时卷内不出现重复题。
    """
    out = set()
    for it in items:
        try:
            qid = int(it.get("question_id") or it.get("id") or 0)
        except (TypeError, ValueError):
            continue
        if qid:
            out.add(qid)
    return out


def _regen_stem_keys(
    db: Session, *, grade_id: int, subject_id: int, qtypes: set,
) -> List[str]:
    """已落库题干（用于近似去重）。

    与补题路径的 `_existing_stem_keys` 不同：这里一次要覆盖**多个题型**，
    且组卷预览还没入卷，无法用"本卷已用 id"兜住「换了个说法的同一道题」。
    """
    if not qtypes:
        return []
    rows = db.scalars(
        select(Question.stem).where(
            Question.grade_id == grade_id,
            Question.subject_id == subject_id,
            Question.type.in_(list(qtypes)),
        ).order_by(Question.id.desc()).limit(400)
    ).all()
    return [k for k in (_stem_key(x) for x in rows) if k]


def _regen_one(
    *,
    db_factory, user_id: int, is_admin: bool, grade_id: int, subject_id: int,
    qtype: str, difficulty: str, kp_ids: List[int], need: int = 1,
    forbid_ids: Optional[set] = None, forbid_keys: Optional[List[str]] = None,
    source: str = "ai_regen",
) -> Dict[str, Any]:
    """给单个（题型, 难度）组合生成 1~N 道新题，返回已落库的题目字典列表。

    与 `_fill_one_gap` 的区别：那个函数服务"补齐缺口"（按大题补到 need 道），
    这个服务"替换某几道"（只要 1 道就够，但题型/难度/知识点必须精确对齐）。

    三条硬约束，缺一条就会出问题：
    1. **难度精确**：模型常无视难度要求给"中等"，而重生成的目的往往就是
       "这道题太简单了换一道难的"。所以生成后按 difficulty 过滤，不匹配就重试一次。
    2. **题型精确**：混进别的题型会让「选择题」大题里出现填空题。
    3. **不重复**：与卷内其余题（id）和题库题干（近似）都不能撞。
    """
    from app.agents.question_agent import QuestionGeneratorAgent
    from app.api.v1.question import normalize_question_type
    from app.services.question_access import question_usable_error

    out: Dict[str, Any] = {"items": [], "reason": "", "skipped_dup": 0}
    forbid_ids = set(forbid_ids or ())
    keys = list(forbid_keys or [])
    # 单批上限与补题共用同一个函数：作文一题上千字、解答题要完整解题过程，
    # 一次 10 道必然把 max_tokens 烧在推理阶段（见 _fill_batch_cap 的实测依据）。
    # 重生时也要把**目标难度**带进来：困难题单批必须更小，否则一次都拿不到。
    cap = _fill_batch_cap(qtype, difficulty or "")
    # 空转保护：连续两轮"一点没多拿到"就停（模型持续给重复题 / 难度不符时
    # 单纯加轮次只会白烧 60~90s）。轮数上限按 need 动态算，否则 need=9、
    # cap=3 时 2 轮最多只拿到 6 题，剩下 3 题会被误报成"模型生成不了"。
    rounds = min(6, max(2, (need + cap - 1) // cap + 1))
    idle = 0
    # 减半标记必须落在**循环外**的 batch_cap 上：如果只在分支里改 batch，
    # 下一轮开头 `batch = min(cap, ...)` 会把它重新算回去，减半等于没做
    # （首版就踩了这个坑：三轮调用恒为 count=3）。
    batch_cap = cap
    budget_retried = False

    while len(out["items"]) < need and rounds > 0:
        rounds -= 1
        batch = max(1, min(batch_cap, need - len(out["items"])))
        before = len(out["items"])
        db = db_factory()
        try:
            try:
                res = QuestionGeneratorAgent().run(
                    db, user_id=user_id, grade_id=grade_id, subject_id=subject_id,
                    question_type=qtype, count=batch, difficulty=difficulty,
                    knowledge_point_ids=kp_ids or None, save=True,
                    allow_all_banks=is_admin, source=source,
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning("预览重生失败（type=%s diff=%s）: %s", qtype, difficulty, exc)
                out["reason"] = f"生成调用异常：{exc}"
                break

            if not (res or {}).get("success", True):
                out["reason"] = str(res.get("message") or "生成执行失败")
                break
            data = (res or {}).get("data") or {}
            got = data.get("questions") or []
            if not got:
                raw = str(data.get("reason") or data.get("tip") or "")
                out["reason"] = _fill_fail_hint(data)
                # 预算被推理吃光的，第二批自动减半（同补题口径：只减一次，
                # 否则会一路减到 1 道，白耗轮次）
                if _is_budget_failure(raw) and not budget_retried:
                    budget_retried = True
                    batch_cap = max(1, batch // 2)
                    out["reason"] += "（已缩小批次重试）"
                continue

            for q in got:
                if len(out["items"]) >= need:
                    break
                qid = q.get("id") or q.get("question_id")
                if not qid:
                    continue
                qid_int = int(qid)
                if qid_int in forbid_ids:
                    continue
                qrow = db.get(Question, qid_int)
                if not qrow:
                    continue
                if question_usable_error(qrow, user_id=user_id, is_admin=is_admin):
                    continue
                if normalize_question_type(qrow.type, strict=False) != qtype:
                    continue
                # 难度必须精确匹配：放宽就失去"换一道同难度的题"的意义
                if (qrow.difficulty or difficulty) != difficulty:
                    continue
                stem_key = _stem_key(qrow.stem)
                if any(_is_similar_stem(stem_key, k) for k in keys):
                    out["skipped_dup"] += 1
                    continue
                keys.append(stem_key)
                forbid_ids.add(qid_int)
                kp_name = None
                if qrow.knowledge_point_id:
                    kp_name = db.scalar(select(KnowledgePoint.name).where(
                        KnowledgePoint.id == qrow.knowledge_point_id))
                out["items"].append({
                    "question_id": qid_int,
                    "type": qrow.type,
                    "type_label": TYPE_LABEL.get(qrow.type, qrow.type),
                    "stem": qrow.stem,
                    "difficulty": qrow.difficulty or difficulty,
                    "options": _load_json(qrow.options),
                    "answer": _load_json(qrow.answer),
                    "analysis": qrow.analysis,
                    "knowledge_point_id": qrow.knowledge_point_id,
                    "knowledge_point_name": kp_name or "AI 生成",
                })
        finally:
            db.close()

        # 空转计数：本轮一道没多拿到就累加，连两轮没进展直接放弃（避免空烧模型）
        idle = 0 if len(out["items"]) > before else idle + 1
        if idle >= 2:
            if not out["items"] and not out["reason"]:
                out["reason"] = (f"未生成符合「{TYPE_LABEL.get(qtype, qtype)}·"
                                 f"{_diff_label(difficulty)}」要求的新题")
            break

    if not out["items"] and not out["reason"]:
        out["reason"] = f"未生成符合「{TYPE_LABEL.get(qtype, qtype)}·{_diff_label(difficulty)}」要求的新题"
    if out["skipped_dup"]:
        out["reason"] = (out["reason"] + "；" if out["reason"] else "") + \
            f"跳过 {out['skipped_dup']} 道与题库重复的题"
    return out


def _diff_label(diff: str) -> str:
    return {"easy": "简单", "medium": "中等", "hard": "困难"}.get(diff, diff)


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


def _ai_fill_gaps(
    db: Session, user: User, *, plan, grade: Grade, subject: Subject,
    difficulty_norm: Dict[str, int],
    on_progress: Optional[Callable[[int, int], None]] = None,
) -> str:
    """题库缺口 / 全 AI：调出题 Agent 生成缺失题目并追加进 plan。

    组卷引擎对 `ai_only` 只返回"缺口清单"（该策略不抽题），`bank_first` 在题库
    不足时也会留 gaps —— 二者都注明"由上层调 AI 生成"，但此前**没有任何上层
    真正实现**，"仅使用 AI 生成"最终拿到 0 题空卷。这里补上这一步：复用现成的
    QuestionGeneratorAgent（无 LLM 时自动走规则引擎 fallback），生成的题以 draft
    入库并回填 id，再按缺口的大题/分值组装进 plan。

    **按大题逐个补**而不是一次性按总题量补：Agent 一次调用只产出一种题型
    （`question_type`），混着补会把单选题塞进"填空题"大题，卷面直接错乱。

    **各大题并行**（`settings.AI_FILL_CONCURRENCY`，默认 3）：串行时总耗时 =
    大题数 × 单次模型耗时，4~5 个大题就能顶到 nginx 的 proxy_read_timeout。
    并行后最坏耗时 ≈ 单次最长耗时。结果按 gap 原始顺序合并（不是完成顺序），
    所以卷面大题顺序不受线程调度影响。

    返回提示串（空=无异常）。
    """
    default_diff = max(difficulty_norm, key=difficulty_norm.get) if difficulty_norm else "medium"
    notes: List[str] = []
    kept_gaps: List[Dict[str, Any]] = []
    filled_total = 0

    # 只提取标量，不把 ORM 对象带进工作线程
    user_id = int(user.id)
    is_admin = _is_sys_admin(user)
    grade_id = int(grade.id)
    subject_id = int(subject.id)

    pending = [g for g in plan.gaps
               if max(0, int(g["need"]) - int(g.get("got", 0))) > 0]
    if not pending:
        return ""

    # 结束主 Session 的只读事务：异步任务里 on_progress 会用独立连接写
    # sys_agent_job，SQLite 下主连接持有的读事务会让那次写入等锁（5s 后
    # 报 database is locked）。组卷引擎此前只有 SELECT，commit 无副作用。
    if on_progress:
        db.commit()

    # 熔断/冷却期直接跳过，不发请求。
    # 并行的意义是把 N 次串行调用压成 1 次等待，但**在限流冷却里并发只会
    # 加速熔断升级**：3 个线程同时撞 429，streak 一次涨 3，退避从 30s 跳到
    # 更长，整站 AI 冷却时间被自己拉长。这里先看一眼状态，冷却中就不再打上游，
    # 直接把原因写进 message 让教师改用题库（比"转圈 5 分钟后报错"好）。
    state = llm_breaker.snapshot()
    if state.get("breaker") == "auth":
        msg = ("AI 补题已跳过：模型鉴权失败处于熔断状态"
               f"（{state.get('reason') or '密钥无效'}），请先修复密钥或改用「仅使用题库」")
        _mark_gaps_reason(pending, "AI 鉴权失败处于熔断状态")
        return msg
    remaining = int(state.get("cooldown_remaining") or 0)
    if remaining > 0:
        msg = (f"AI 补题已跳过：模型限流冷却中（剩余 {remaining}s），"
               "请改用「仅使用题库」或稍后重试")
        _mark_gaps_reason(pending, f"模型限流冷却中（剩余 {remaining}s）")
        return msg

    workers = max(1, min(int(settings.AI_FILL_CONCURRENCY or 1), len(pending), 4))
    # 本卷已抽到的题：补题时用于拦住"复用题库时把同一道题再补一遍"。
    # 转成 set 是为了在子线程里做 O(1) 判断（只传标量/容器，不传 ORM 对象）。
    used_ids = set(plan.used_question_ids)
    tasks = [
        (g, dict(user_id=user_id, is_admin=is_admin, grade_id=grade_id,
                 subject_id=subject_id, default_diff=default_diff,
                 used_ids=used_ids))
        for g in pending
    ]
    total_gaps = len(tasks)
    if workers == 1:
        results = []
        for idx, (g, kw) in enumerate(tasks):
            results.append(_fill_one_gap(g, **kw))
            if on_progress:
                on_progress(idx + 1, total_gaps)
    else:
        with ThreadPoolExecutor(max_workers=workers,
                                thread_name_prefix="ai-fill") as pool:
            future_index = {
                pool.submit(_fill_one_gap, g, **kw): idx
                for idx, (g, kw) in enumerate(tasks)
            }
            # **用 as_completed 收结果才能实时报进度**：一批补题要等 1~2 分钟，
            # 等到全部完成才更新等于没有进度条。
            # 但合并时仍按 gap 原始顺序（done 字典按 idx 回填），否则大题顺序
            # 会随线程完成先后漂移，重复调用结果也不一致。
            done: Dict[int, Dict[str, Any]] = {}
            for fut in as_completed(future_index):
                done[future_index[fut]] = fut.result()
                if on_progress:
                    on_progress(len(done), total_gaps)
            results = [done[i] for i in range(total_gaps)]

    # 补题线程各自 commit（新题已落库），但主 Session 此时很可能还开着事务：
    # SQLite/PostgreSQL 的读快照在事务开始时确定，主 Session 看不到其他连接
    # 新提交的行 —— 后续 `db.get(Question, qid)` 会返回 None，表现为"补了几题、
    # 保存却报题目不存在"。这里结束主 Session 的当前事务以刷新快照。
    # 调用方此前只有只读操作（组卷引擎不写库），commit 不会提交任何半成品。
    db.commit()

    for res in results:
        g = res["gap"]
        notes.extend(res["notes"])
        if res["filled"]:
            plan.items.extend(res["items"])
            filled_total += res["filled"]
            g["got"] = int(g.get("got", 0)) + res["filled"]
        if int(g.get("got", 0)) < int(g["need"]):
            miss = int(g["need"]) - int(g.get("got", 0))
            # 逐条把原因挂到 gap 上：前端缺口卡片直接展示，教师不必再从下面
            # 那条又长又混的 message 里翻「到底为什么 AI 没补上」。
            g["miss"] = miss
            g["reason"] = str(res.get("reason") or "")
            g["ai_tried"] = bool(res.get("ai_tried"))
            g["action"] = _gap_action(g["reason"], ai_tried=g["ai_tried"])
            kept_gaps.append(g)
            # 原因可能已由 res["notes"] 带出去（补题失败 / 跳过重复题），这里只补
            # "还差几题"。不去重的话同一条原因会在 message 里原样出现两次。
            already = any(str(n).startswith(f"{g['name']}补题失败") for n in res["notes"])
            notes.append(
                f"{g['name']}仍缺 {miss} 题"
                + ("" if already else
                   (f"：{g['reason']}" if g["reason"] else "（题库无同题型已发布题）")))

    if plan.items:
        plan.gaps = kept_gaps
        compose_svc._renumber(plan.items)
    if filled_total:
        notes.insert(0, f"已调用 AI 补齐 {filled_total} 道题目")
    return "；".join(n for n in notes if n)


def _compose_from_payload(
    db: Session, user: User, data: Dict[str, Any],
    on_progress: Optional[Callable[[int, int], None]] = None,
) -> Dict[str, Any]:
    """两种组卷模式共用的参数解析与引擎调用。

    `on_progress(done, total)` 只在 AI 补题阶段回调，用于异步任务的进度条。
    同步调用（HTTP 请求内）不传即无副作用。
    """
    grade, subject = _grade_subject(db, data.get("grade_id"), data.get("subject_id"))
    standard = _resolve_standard(
        db, grade=grade, subject=subject, standard_id=data.get("standard_id"))
    sections = _parse_sections_input(data.get("sections")) or compose_svc.parse_sections(standard)
    # 没有任何可用结构（该学段学科没配命题标准、也没手填题型）时**不再直接报错**：
    # 旧行为是 400「请先在命题标准中配置」，把补配置的成本转嫁给一线教师，
    # 而引擎里本来就有兜底能力。改为用通用结构出卷，并明确标注结构来源，
    # 让教师先能拿到卷子，再由管理员补标准（B 提供一键生成草案）。
    standard_fallback = False
    if not sections:
        # 传学段/学科：结构按真实考试模板出（小学/初中各学科不同），
        # 而不是所有学科共用一套「单选+填空+解答」。
        sections = compose_svc.generic_sections(
            float(data.get("total_score") or 100),
            stage=_stage_of(grade), subject_name=subject.name)
        standard_fallback = True

    source_strategy = str(data.get("source") or compose_svc.SOURCE_BANK_FIRST).strip()
    if source_strategy not in compose_svc.VALID_SOURCES:
        raise BusinessException(f"出题来源仅支持 {'/'.join(sorted(compose_svc.VALID_SOURCES))}")

    kp_ids = data.get("knowledge_point_ids") or []
    if not isinstance(kp_ids, list):
        raise BusinessException("知识点参数格式错误")
    kp_ids = [int(k) for k in kp_ids if k]
    if kp_ids:
        # 知识点必须属于当前年级学科，否则抽题必然为空且无任何提示
        valid = set(db.scalars(
            select(KnowledgePoint.id).where(
                KnowledgePoint.id.in_(kp_ids),
                KnowledgePoint.grade_id == grade.id,
                KnowledgePoint.subject_id == subject.id,
            )).all())
        invalid = [k for k in kp_ids if k not in valid]
        if invalid:
            raise BusinessException(
                f"以下知识点不属于{grade.name}{subject.name}：{invalid}")

    difficulty = data.get("difficulty_ratio")
    try:
        difficulty_norm = compose_svc.normalize_difficulty(difficulty)
    except compose_svc.ComposeError as exc:
        raise BusinessException(str(exc))

    try:
        plan = compose_svc.compose(
            db,
            grade_id=grade.id, subject_id=subject.id,
            standard=standard, sections=sections,
            difficulty_ratio=difficulty_norm,
            kp_ids=kp_ids,
            source_strategy=source_strategy,
            avoid_recent=bool(data.get("avoid_recent", True)),
            recent_n=int(data.get("recent_n") or 3),
            avoid_duplicate_kp=bool(data.get("avoid_duplicate_kp", True)),
            exclude_paper_id=data.get("exclude_paper_id"),
            total_score_override=data.get("total_score") or None,
            # 题库可见范围：公共库 + 本人私有；管理员不限
            viewer_id=user.id, allow_all_banks=_is_sys_admin(user),
        )
    except compose_svc.ComposeError as exc:
        raise BusinessException(str(exc))

    # 题库缺口 / 全 AI：补上"上层调 AI 生成"这一步（否则 ai_only 得到空卷）。
    # 调用方自带最终题目（保存时前端已传 items）则跳过，避免重复生成污染草稿库。
    ai_note = ""
    if (source_strategy != compose_svc.SOURCE_BANK_ONLY
            and plan.gaps and not data.get("items")):
        ai_note = _ai_fill_gaps(
            db, user, plan=plan, grade=grade, subject=subject,
            difficulty_norm=difficulty_norm, on_progress=on_progress)
        if data.get("total_score") and plan.items:
            compose_svc._rescale_scores(plan.items, float(data["total_score"]))
    if source_strategy == compose_svc.SOURCE_AI_ONLY and not plan.items:
        raise BusinessException(
            "「仅使用 AI 生成」未能生成题目"
            + (f"（{ai_note}）" if ai_note else "")
            + "，请改用「题库优先 + AI 补充」或先在题库录入题目")

    reports = compose_svc.build_reports(plan.items, difficulty_norm, sections)
    # 知识点缺口只在"没有指定知识点"时判定：用户显式指定了知识点，
    # 说明该学科知识点存在且被选中，不需要再提示（指定必然已被上面的校验通过）。
    kp_missing = False
    if not kp_ids:
        kp_total = db.scalar(
            select(func.count()).select_from(KnowledgePoint).where(
                KnowledgePoint.grade_id == grade.id,
                KnowledgePoint.subject_id == subject.id,
                KnowledgePoint.is_active.is_(True),
            )
        ) or 0
        kp_missing = int(kp_total) == 0
    return {
        "grade": grade, "subject": subject, "standard": standard,
        "sections": sections, "difficulty": difficulty_norm,
        "plan": plan, "reports": reports,
        "source_strategy": source_strategy, "kp_ids": kp_ids,
        "standard_fallback": standard_fallback, "ai_note": ai_note,
        "kp_missing": kp_missing,
    }


def _plan_response(ctx: Dict[str, Any], *, ai_message: str = "") -> Dict[str, Any]:
    plan = ctx["plan"]
    std = ctx["standard"]
    # 卷面体检：期望总分按 sections 算（plan.total_score 是"已抽到题目之和"，
    # 用它当基准永远相等，等于没检查）。有缺口时合计天然小于总分，跳过该检查。
    expected_total = round(sum(
        section_total(s) for s in (ctx.get("sections") or [])
    ), 2) or None
    body = {
        "grade_id": ctx["grade"].id, "grade_name": ctx["grade"].name,
        "subject_id": ctx["subject"].id, "subject_name": ctx["subject"].name,
        "standard_id": std.id if std else None,
        "standard_name": std.name if std else None,
        "exam_type": std.exam_type if std else None,
        "sections": ctx["sections"],
        "difficulty_ratio": ctx["difficulty"],
        "source": ctx["source_strategy"],
        "knowledge_point_ids": ctx["kp_ids"],
        **plan.to_dict(),
        **ctx["reports"],
        "suggested_duration": std.duration if std else 90,
        "standard_total_score": std.total_score if std else None,
        # true = 该学段学科没有命题标准，结构来自通用模板（不是权威结构）
        "standard_fallback": bool(ctx.get("standard_fallback")),
        # true = 该学科一条知识点都没有：组卷仍可出题，但题目挂不上考点，
        # 掌握度图谱与复习计划在这门课上必然失效。让前端能明确提示，
        # 而不是让教师以为"AI 没识别出考点"。
        "knowledge_point_missing": bool(ctx.get("kp_missing")),
        # 卷面体检结果（空数组 = 通过）。前端在预览页顶部按 level 显示，
        # error 用红色（打印会出错），warn 用黄色（不合常规但可用）。
        "issues": compose_svc.audit_paper(
            plan.items, total_score=expected_total, has_gaps=bool(plan.gaps)),
    }
    if ai_message:
        body["message"] = ai_message
    if body.get("standard_fallback"):
        note = ("该学段学科尚未配置命题标准，本次已用通用结构（单选/填空/解答）生成卷面；"
                "建议管理员在「命题标准」中补配后再生成一次。")
        body["message"] = f"{body['message']}；{note}" if body.get("message") else note
    if body["knowledge_point_missing"]:
        note = (f"{ctx['grade'].name}{ctx['subject'].name}尚未维护知识点，本次组卷无法按考点选题，"
                "题目也不会进入掌握度图谱；请联系管理员补齐该学科知识点后重新组卷。")
        body["message"] = f"{body['message']}；{note}" if body.get("message") else note
    # 去重曾把整大题清空、已自动放宽：必须告诉教师，否则"复用了老题"是隐形的
    if getattr(plan, "relaxed_count", 0):
        note = (f"「避免近 3 次考试重复」把部分大题清空，已自动放宽去重并复用 "
                f"{plan.relaxed_count} 题；如需完全不重复，请先补充题库。")
        body["message"] = f"{body['message']}；{note}" if body.get("message") else note
    # AI 补题提示（失败原因 / 规则引擎兜底说明）如实透传到前端，便于诊断
    if ctx.get("ai_note"):
        note = ctx["ai_note"]
        body["message"] = f"{body['message']}；{note}" if body.get("message") else note
    return body


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


def _ai_resolve_params(
    db: Session, user: User, data: Dict[str, Any],
) -> tuple[Dict[str, Any], str, str]:
    """把「自然语言 + 少量显式参数」解析成完整组卷参数。

    同步接口 `/compose/ai` 与异步接口 `/compose/ai/async` **必须共用这一份**：
    旧实现只有同步路径做解析，异步路径把 `grade_id=None` 直接塞给
    `_compose_from_payload`，导致「只写描述、不选年级」在异步路径 100% 失败
    （错误提示还是"请选择有效的年级"，与界面承诺完全相反）——P0-3。

    **这里的解析允许失败**：AI 只负责翻译参数，翻译不出来就降级为规则组卷，
    但年级/学科一个都推不出来时必须报错（交给调用方判定），
    否则会在 `_grade_subject` 里抛出一句毫无信息量的错。

    返回 `(merged, parse_error, request)`。
    """
    from app.agents.paper_agent import PaperComposerAgent

    request = str(data.get("request") or "").strip()
    parsed: Dict[str, Any] = {}
    parse_error = ""
    if request:
        agent = PaperComposerAgent()
        try:
            res = agent.call_llm(
                request, db=db, user_id=user.id,
                biz_type="paper_parse", json_mode=True)
            if res.get("success") and isinstance(res.get("parsed"), dict):
                parsed = res["parsed"].get("params") or {}
            else:
                parse_error = res.get("reason") or res.get("message") or ""
        except Exception as exc:  # noqa: BLE001
            # AI 解析只是"翻译参数"，失败不该阻断组卷
            logger.warning("AI 组卷参数解析失败，降级为规则组卷: %s", exc)
            parse_error = str(exc)

    merged = dict(data)
    # 年级/学科单独处理：**客户端的显式选择优先**，只有没给的时候才用 AI 的推断，
    # 且推断结果必须按「年级+名称」落到真实记录上（模型给的 id 不可信）。
    merged.pop("grade_id", None)
    merged.pop("subject_id", None)
    anchor_grade = None
    if data.get("grade_id"):
        try:
            anchor_grade = db.get(Grade, int(data["grade_id"]))
        except (TypeError, ValueError):
            anchor_grade = None
    if anchor_grade is None:
        anchor_grade = _resolve_ai_grade(db, parsed, request)
    anchor_subject = None
    if data.get("subject_id"):
        # 用户明确选了学科就尊重它，交给 _grade_subject 给出精确的错配提示
        try:
            anchor_subject = db.get(Subject, int(data["subject_id"]))
        except (TypeError, ValueError):
            anchor_subject = None
    if anchor_subject is None:
        anchor_subject = _resolve_ai_subject(db, anchor_grade, parsed, request)
    if anchor_grade:
        merged["grade_id"] = anchor_grade.id
    if anchor_subject:
        merged["subject_id"] = anchor_subject.id
    for key in ("standard_id", "difficulty_ratio",
                "knowledge_point_ids", "source", "total_score"):
        if not merged.get(key) and parsed.get(key):
            merged[key] = parsed[key]
    # AI 给的 sections 只在用户没指定时采用，且**至少 2 个大题**才采纳 ——
    # 单一题型的结构不符合考试规范，几乎总是模型解析不完整的产物。
    # 不采纳时上层会回退到学科命题标准（多题型），比照残缺结构出卷好。
    if not merged.get("sections") and parsed.get("sections"):
        ai_sections = _parse_sections_input(parsed["sections"])
        if ai_sections and len(ai_sections) >= 2:
            merged["sections"] = ai_sections
        elif ai_sections:
            logger.warning("AI 仅解析出 %d 个大题，已忽略并改用命题标准结构",
                           len(ai_sections))
    # 题型分布（type_ratio）→ sections：AI 常用 {"single":10} 形式
    if not merged.get("sections") and parsed.get("type_ratio"):
        merged["sections"] = _type_ratio_to_sections(
            parsed["type_ratio"], merged.get("total_score") or 100,
            stage=getattr(anchor_grade, "stage", None),
            subject_name=getattr(anchor_subject, "name", None),
        )
    return merged, parse_error, request


def _type_ratio_to_sections(
    type_ratio: Any, total_score: float, *,
    stage: Optional[str] = None, subject_name: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """把 {"single":10,"blank":5} 转成 sections。

    **非法题型直接丢弃并记日志**——旧实现把 `fill`/`solve` 这类不在枚举里的
    key 静默忽略，导致"要求 10 题只出 4 题"且毫无提示。
    这里至少把丢弃行为写进日志，并在 sections 为空时由上层报错。

    分值分配优先沿用**学科标准模板的阶梯形状**（数学解答题 6/6/6/8/8/8/10/11/12、
    化学选择题 8×1+5×2）：AI 只解析出题型比例，没有每题分值，若一律均摊，
    真实卷面的难度梯度会被抹平，压轴题和送分题同分。
    只在「AI 给的题量与该大题模板题量一致」时套用形状，否则均摊
    —— 题量对不上还硬套形状会算出「第 9 题 11 分但只有 6 题」这类错位。
    """
    if not isinstance(type_ratio, dict):
        return []
    result: List[Dict[str, Any]] = []
    dropped: List[str] = []
    total_count = 0
    for code, qty in type_ratio.items():
        key = str(code or "").strip().lower()
        if key not in TYPE_LABEL:
            dropped.append(key)
            continue
        try:
            count = int(qty or 0)
        except (TypeError, ValueError):
            dropped.append(key)
            continue
        if count <= 0:
            continue
        result.append({"code": key, "name": TYPE_LABEL[key], "count": count,
                       "difficulty": "medium", "sort": len(result) + 1})
        total_count += count
    if dropped:
        logger.warning("AI 返回了非法题型，已丢弃：%s（合法值 %s）",
                       dropped, sorted(TYPE_LABEL))
    if not result or total_count <= 0:
        return []
    # 单一题型的结构不予采纳：整卷只有一种题型不符合考试规范，而且这几乎
    # 总是「模型照抄了 prompt 里的错误示例 / 只写了 single」的产物。
    # 返回空让上层回退到学科命题标准（多题型），比照着一条 type_ratio 出卷好。
    if len(result) < 2:
        logger.warning("AI 只给出 1 种题型（%s），已忽略并改用命题标准结构",
                       [s["code"] for s in result])
        return []

    try:
        ref = {s["code"]: s for s in sections_for(
            stage=stage, subject_name=subject_name, total_score=float(total_score or 100))}
    except Exception:  # noqa: BLE001 - 模板不可用不该阻断组卷
        logger.warning("取学科结构模板失败，分值按均摊处理", exc_info=True)
        ref = {}

    base = round(float(total_score or 100) / total_count, 2)
    acc = 0.0
    for pos, s in enumerate(result):
        count = int(s["count"])
        # 末档吸收舍入误差，保证合计精确等于试卷总分
        if pos == len(result) - 1:
            sec_total = round(float(total_score or 100) - acc, 2)
        else:
            sec_total = round(base * count, 2)
        pat = (ref.get(s["code"]) or {}).get("score_pattern")
        if isinstance(pat, (list, tuple)) and len(pat) == count:
            old = sum(float(x) for x in pat)
            if old > 0:
                ratio = sec_total / old
                new_pat = [round(float(x) * ratio, 2) for x in pat]
                drift = round(sec_total - sum(new_pat), 2)
                if drift:
                    new_pat[-1] = round(new_pat[-1] + drift, 2)
                s["score_pattern"] = new_pat
                s["score_per"] = round(sec_total / count, 2)
                acc = round(acc + sum(new_pat), 2)
                continue
        sec_total = round(sec_total / count, 2) * count
        sec_total = round(sec_total, 2)
        s["score_per"] = round(sec_total / count, 2)
        acc = round(acc + sec_total, 2)
    return result


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
