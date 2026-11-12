"""组卷引擎主流程：参数归一 → 题库抽取 → AI 补题 → 报告（自 api/v1 下沉，Q-05）。

本模块只做「卷子怎么组出来」，不含任何 HTTP 语义：

- `_grade_subject` / `_resolve_standard` / `_parse_sections_input`：把前端或
  AI 给的松散参数收敛成引擎能吃的结构（年级学科必须真实存在、题型必须合法）。
- `_stem_key` / `_is_similar_stem` / `_existing_stem_keys`：题干归一与近似判重，
  模型每次换个说法就能绕过 fingerprint，精确哈希拦不住。
- `_fill_one_gap`：单个大题的补题循环，跑在自己的 Session 里（因此可并行）。
- `_ai_fill_gaps`：按大题并行补题并合并回 plan，熔断/冷却期直接早退。
- `_compose_from_payload`：两种组卷模式共用入口，返回 ctx 供上层拼响应。

`paper_compose.py` 通过同名再导出继续提供这些名字（`_regen_one`、`_ai_resolve_params`
与回归脚本仍照旧引用），行为不变。
"""
import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exception import BusinessException
from app.models import ExamStandard, Grade, KnowledgePoint, Question, Subject, User
from app.services import llm_breaker
from app.services import paper_compose_service as compose_svc
from app.services.ai_fill_batch import _fill_batch_cap
from app.services.paper_access import _is_sys_admin
from app.services.paper_items import _stage_of

logger = logging.getLogger(__name__)

TYPE_LABEL = compose_svc.TYPE_LABEL

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
