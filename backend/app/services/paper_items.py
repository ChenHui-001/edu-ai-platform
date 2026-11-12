"""题项写入与试卷预览 —— 自 api/v1/paper_compose.py 下沉（Q-05）。

- `_normalize_items`：校验/去重/规范化入参题目（含题目可用性、年级学科一致性）。
- `_write_items`：插新题项 → 迁移作答 → 删旧题项（顺序不可颠倒，否则作答被级联清空）。
- `_build_preview`：按大题分组生成教师卷/学生卷预览（学生卷不含答案与解析）。
- `_load_json` / `_stage_of`：随上述函数一并带上的小工具。

调用方（内部端点、`question.py` 的 `from app.api.v1.paper_compose import
_write_items/_build_preview`）通过 paper_compose 的同名再导出继续工作，行为不变。
"""
import json
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exception import BusinessException
from app.models import (
    Answer, Grade, KnowledgePoint, Paper, PaperItem, Question, Subject, User,
)
from app.services import paper_compose_service as compose_svc
from app.services.paper_access import _is_sys_admin
from app.services.question_access import question_usable_error
from app.utils.common import dictify

TYPE_LABEL = compose_svc.TYPE_LABEL
logger = logging.getLogger(__name__)


def _load_json(value: Optional[str]) -> Any:
    if not value:
        return None
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return value

def _stage_of(grade: Grade) -> str:
    return grade.stage or ("primary" if (grade.grade_num or 1) <= 6 else "junior")

def _normalize_items(
    db: Session, user: User, raw_items: List[Any], grade_id: int, subject_id: int,
) -> List[Dict[str, Any]]:
    """校验并规范化题目列表。

    比旧实现多做的三件事：
    1. 去重（同一题不能在一卷里出现两次）；
    2. 校验题目年级/学科归属，避免跨学科混排；
    3. 保留 section_code / section_sort，让大题分组稳定（旧实现只存名称，
       改名就散架）。
    """
    seen: set = set()
    result: List[Dict[str, Any]] = []
    for idx, raw in enumerate(raw_items, start=1):
        if not isinstance(raw, dict):
            raise BusinessException(f"第 {idx} 道题目数据格式错误")
        try:
            qid = int(raw.get("question_id") or raw.get("id"))
        except (TypeError, ValueError):
            raise BusinessException(f"第 {idx} 道题目的 question_id 无效")
        if qid in seen:
            raise BusinessException(f"试卷中题目重复（question_id={qid}）")
        seen.add(qid)
        q = db.get(Question, qid)
        if not q:
            raise BusinessException(
                f"题目不存在或已删除（id={qid}），无法保存到试卷。"
                f"请从试卷中移除该题，或在题库中确认题目状态后重新添加")
        # 与 question._normalize_paper_items 共用同一判定（含 status 校验），
        # 避免"预览能过、保存被拒"或两处口径漂移。
        err = question_usable_error(
            q, user_id=user.id, is_admin=_is_sys_admin(user))
        if err:
            raise BusinessException(err)
        if q.grade_id != grade_id or q.subject_id != subject_id:
            raise BusinessException(f"题目年级/学科与试卷不一致（id={qid}）")

        # 题型必须与所在大题一致：把填空题塞进「一、选择题」，
        # 卷面上会出现「选择题」下面是填空题的错版，打印出来即事故。
        # 组卷引擎按 qtype 抽题天然一致，这条拦的是手动保存 / 前端构造的入参。
        raw_code = str(raw.get("section_code") or "").strip().lower()
        if raw_code and raw_code in TYPE_LABEL and raw_code != q.type:
            raise BusinessException(
                f"第 {idx} 题是「{TYPE_LABEL.get(q.type, q.type)}」，"
                f"不能放进「{TYPE_LABEL[raw_code]}」大题（id={qid}）"
            )

        try:
            score = float(raw.get("score") if raw.get("score") is not None else (q.score or 5))
        except (TypeError, ValueError):
            raise BusinessException(f"题目分值必须为数字（id={qid}）")
        if score < 0 or score > 1000:
            raise BusinessException(f"题目分值需在 0~1000 之间（id={qid}）")

        result.append({
            "question_id": qid,
            "score": round(score, 2),
            "type": q.type,
            "section_code": str(raw.get("section_code") or q.type)[:32],
            "section_name": str(raw.get("section_name") or TYPE_LABEL.get(q.type, "综合题"))[:64],
            "section_sort": int(raw.get("section_sort") or 0),
            # 传入顺序即教师看到的卷面顺序，记成槽位。`_renumber` 优先按它排，
            # 否则保存时会按 question_id 重排 —— 阶梯分值（第 9 题 12 分）
            # 会和题目错位，教师改完卷一保存分值就乱了。
            "section_pos": idx - 1,
            "score_override": bool(raw.get("score_override", False)),
        })
    return result

def _write_items(db: Session, paper: Paper, items: List[Dict[str, Any]],
                 *, migrate_answers: bool = True,
                 renumber: bool = True) -> Dict[str, int]:
    """写入题项（插入新 → 迁移作答 → 删旧），并重排大题序号。

    **顺序至关重要**：`Answer.paper_item_id` 是 ON DELETE CASCADE。
    旧实现直接 `DELETE FROM edu_paper_item` 再插新行，学生的作答会随旧题项
    一起被数据库级联清空（实测一份卷 80 条作答、920 分全部归零）。
    正确顺序是：
      1. 记下旧题项 id（question_id → [item_id]）
      2. 插入新题项（拿到新 id）
      3. 把旧作答的 paper_item_id 改指向新题项（按 question_id 对应）
      4. 最后才删除旧题项——此时已无作答指向它们，级联删除无害

    返回 `{"migrated": 保住的作答数, "dropped": 随题目移除而作废的作答数}`。
    **被移除题目的作答无法保留**：`paper_item_id` 非空且 CASCADE，
    题项删除后作答必然被级联清除。这里不假装保住，而是如实计数上报，
    让调用方能告诉教师「这次修改作废了 N 条作答」。

    `renumber=False` 供旧入口（`PUT /papers/{id}`）复用：那条路径按**入参顺序**
    决定题序、原样保留大题名，若套用 `_renumber` 会按 question_id 重排题目
    并把大题名改写成「一、…」，属于破坏既有契约的副作用。
    """
    # 0) 按 question_id 去重（保留首次出现）。
    # 同一道题在一份卷子里出现两次，打印出来就是两张一模一样的题目，
    # 学生和阅卷老师都会当成事故。来源可能是：前端编辑时重复添加、
    # AI 补题后重复插入、或历史组卷的两个同题型大题各抽中一次
    # （引擎侧已改为全局互斥，这里再兜一层，保证任何入口写库都不重复）。
    deduped: List[Dict[str, Any]] = []
    _seen_qids: set = set()
    for it in items:
        try:
            qid = int(it.get("question_id") or 0)
        except (TypeError, ValueError):
            qid = 0
        if qid and qid in _seen_qids:
            continue
        if qid:
            _seen_qids.add(qid)
        deduped.append(it)
    deduped_count = len(items) - len(deduped)
    if deduped_count:
        logger.warning(f"试卷 {paper.id} 写入前去除 {deduped_count} 道重复题目")
    items = deduped

    # 1) 旧题项快照：question_id → 旧 item id 列表
    old_rows = db.execute(
        select(PaperItem.id, PaperItem.question_id).where(
            PaperItem.paper_id == paper.id)
    ).all()
    old_by_question: Dict[int, List[int]] = {}
    for item_id, qid in old_rows:
        old_by_question.setdefault(int(qid), []).append(int(item_id))
    old_ids = [r[0] for r in old_rows]

    # 2) 插入新题项
    if renumber:
        compose_svc._renumber(items)
    new_map: Dict[int, int] = {}   # question_id → 新 item id
    for idx, it in enumerate(items, start=1):
        row = PaperItem(
            paper_id=paper.id, question_id=it["question_id"],
            sort_order=idx, score=it["score"],
            section_name=it.get("section_name"),
            section_code=it.get("section_code"),
            section_sort=it.get("section_sort") or 0,
            score_override=bool(it.get("score_override", False)),
        )
        db.add(row)
        db.flush()
        new_map[int(it["question_id"])] = int(row.id)

    # 3) 迁移作答：把旧 item 上的 Answer 改挂到同 question_id 的新 item
    migrated = 0
    dropped = 0
    if migrate_answers and old_ids:
        for qid, new_item_id in new_map.items():
            for old_item_id in old_by_question.get(qid, []):
                if old_item_id == new_item_id:
                    continue
                res = db.execute(
                    Answer.__table__.update()
                    .where(Answer.paper_item_id == old_item_id)
                    .values(paper_item_id=new_item_id)
                )
                migrated += res.rowcount or 0
        # 未能迁移的（题目已被移除）：作答即将随旧题项级联删除，先计数
        kept_new_ids = set(new_map.values())
        orphans = [i for i in old_ids if i not in kept_new_ids]
        if orphans:
            dropped = int(db.scalar(
                select(func.count()).select_from(Answer)
                .where(Answer.paper_item_id.in_(orphans))) or 0)
        db.flush()

    # 4) 删除旧题项（此时已无作答指向，级联删除安全）
    if old_ids:
        db.execute(PaperItem.__table__.delete().where(PaperItem.id.in_(old_ids)))
        db.flush()

    # 5) 重算引用计数：本次涉及的题目 = 新题项 ∪ 旧题项。
    # **不能沿用「插新 +1 / 删旧 -1」的记账法**：首次给一份没有题项的卷子补题时
    # 没有"旧题"可减，净效果是凭空 +n；配合删除试卷不减，同一道题的计数会朝
    # 相反方向漂移且无法追溯。重算幂等，值恒等于真实引用数。
    from app.services.question_usage import recount_usage
    touched = set(new_map.keys()) | set(old_by_question.keys())
    if touched:
        recount_usage(db, touched)
        db.flush()

    paper.total_score = round(sum(float(i["score"]) for i in items), 2)
    return {"migrated": migrated, "dropped": dropped, "deduped": deduped_count}

def _build_preview(db: Session, paper: Paper, *, mode: str = "teacher") -> Dict[str, Any]:
    grade = db.get(Grade, paper.grade_id)
    subject = db.get(Subject, paper.subject_id)

    # 按 section_code 归组（缺失时回落到题型），保持 section_sort 顺序
    groups: Dict[str, Dict[str, Any]] = {}
    order: List[str] = []
    for it in sorted(paper.items, key=lambda x: (x.section_sort or 0, x.sort_order or 0)):
        q = it.question
        if not q:
            continue
        code = it.section_code or q.type
        if code not in groups:
            groups[code] = {
                "section_code": code,
                "section_name": it.section_name or TYPE_LABEL.get(code, "综合题"),
                "section_sort": it.section_sort or 0,
                "items": [],
            }
            order.append(code)
        kp = db.get(KnowledgePoint, q.knowledge_point_id) if q.knowledge_point_id else None
        entry = {
            "paper_item_id": it.id,
            "question_id": q.id,
            "sort_order": it.sort_order,
            "score": it.score,
            "type": q.type,
            "type_label": TYPE_LABEL.get(q.type, q.type),
            "difficulty": q.difficulty,
            "difficulty_label": {"easy": "简单", "medium": "中等", "hard": "困难"}.get(
                q.difficulty, q.difficulty),
            "stem": q.stem,
            "options": _load_json(q.options),
            "knowledge_point_id": q.knowledge_point_id,
            "knowledge_point_name": kp.name if kp else None,
        }
        if mode == "teacher":
            entry["answer"] = _load_json(q.answer)
            entry["analysis"] = q.analysis
        groups[code]["items"].append(entry)

    sections = [groups[c] for c in order]
    for idx, sec in enumerate(sections, start=1):
        sec["section_index"] = idx
        sec["item_count"] = len(sec["items"])
        sec["section_score"] = round(sum(float(i["score"]) for i in sec["items"]), 2)

    d = dictify(paper)
    d.update({
        "grade_name": grade.name if grade else None,
        "subject_name": subject.name if subject else None,
        "stage": paper.stage or (_stage_of(grade) if grade else None),
        "sections": sections,
        "item_count": sum(s["item_count"] for s in sections),
        "score_sum": round(sum(float(i["score"]) for s in sections for i in s["items"]), 2),
        "mode": mode,
        "difficulty_report": _load_json(paper.difficulty_report),
        "knowledge_coverage": _load_json(paper.knowledge_coverage),
        "type_report": _load_json(paper.type_report),
        "generation_params": _load_json(paper.generation_params),
        "creator_name": db.scalar(select(User.real_name).where(User.id == paper.creator_id)),
    })
    # 卷面体检：把 sections 摊平后复核一遍，让教师在打印前看到缺陷。
    # 这里检查的是**已落库的真实数据**，能暴露历史试卷的问题
    # （早期生成器留下的重复题、作文错位），不只是新生成的卷子。
    flat: List[Dict[str, Any]] = []
    for sec in sections:
        for it in sec["items"]:
            flat.append({
                "question_id": it.get("question_id"),
                "type": it.get("type"),
                "section_code": sec.get("code"),
                "section_name": sec.get("name"),
                "score": it.get("score"),
                "sort_order": it.get("sort_order"),
            })
    d["issues"] = compose_svc.audit_paper(
        flat, total_score=float(paper.total_score or 0) or None)
    return d
