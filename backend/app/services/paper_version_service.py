"""试卷版本快照服务。

原则：**版本只增不改**。每次结构变更写一条新快照，历史快照永不修改，
回溯操作本身也产生新版本。

快照里冗余存 stem/type/difficulty/answer/analysis，而不只存 question_id：
题库题目可能被后续编辑或删除，只存 id 会让历史版本回溯出「空壳卷」。
代价是每份快照几百 KB 量级——用 SQLite 文本字段完全可接受，
而且省掉了「回溯时反查历史题目快照」这套更复杂的机制。
"""
import json
import logging
from typing import Any, Dict, Optional

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exception import ConflictException
from app.models import Paper, PaperVersion

logger = logging.getLogger(__name__)

# 每份试卷保留的版本数上限。
#
# 快照里冗余存了题干/答案/解析全文，一条几十 KB。而 snapshot() 在每次「编辑题目 /
# 移除题目 / 重构大题 / 回溯」时都会写一条 —— 一份反复打磨的卷子很容易攒到几十个
# 版本，版本抽屉一次全量读出来会明显变慢，DB 也会持续膨胀。
#
# 只保留最近 N 条，外加 version 最小的那条（首次组卷的原始结构，回溯时常被当作
# 「回到最初」的锚点）。删除不影响版本号递增：后续仍按 max(version)+1 生成。
KEEP_RECENT_VERSIONS = 20

# 版本号撞车后的重试次数。3 次足够：撞车只在「同一份卷子被两处同时写」时发生，
# 每次重试都会读到更大的 max(version)，连续 3 次撞车说明不是偶发竞争而是真出问题。
_VERSION_RETRY = 3


def _prune_versions(db: Session, paper_id: int) -> int:
    """裁剪超出保留上限的历史版本，返回删除条数。

    保留策略：最近 KEEP_RECENT_VERSIONS 条 + version 最小的一条。
    早期版本连题干都被冗余保存过，删掉它们不会影响回溯到较新版本，
    因为每个版本的 snapshot 都是**自包含**的（不依赖前序版本）。
    """
    rows = db.scalars(
        select(PaperVersion)
        .where(PaperVersion.paper_id == paper_id)
        .order_by(PaperVersion.version.desc())
    ).all()
    if len(rows) <= KEEP_RECENT_VERSIONS:
        return 0
    keep_ids = {r.id for r in rows[:KEEP_RECENT_VERSIONS]}
    keep_ids.add(min(rows, key=lambda r: r.version).id)
    removed = 0
    for old in rows[KEEP_RECENT_VERSIONS:]:
        if old.id not in keep_ids:
            db.delete(old)
            removed += 1
    if removed:
        db.flush()
        logger.info(f"试卷 {paper_id} 版本裁剪：删除 {removed} 条历史快照")
    return removed


def build_snapshot(db: Session, paper: Paper) -> Dict[str, Any]:
    """构造整卷快照（标量字段 + 题目明细）。"""
    items = []
    for it in sorted(paper.items, key=lambda x: (x.section_sort or 0, x.sort_order or 0)):
        q = it.question
        items.append({
            "question_id": it.question_id,
            "sort_order": it.sort_order,
            "score": float(it.score or 0),
            "section_name": it.section_name,
            "section_code": it.section_code,
            "section_sort": it.section_sort or 0,
            "score_override": bool(it.score_override),
            # 冗余题目内容：题库改动/删除后仍能还原当时卷面
            "stem": q.stem if q else None,
            "type": q.type if q else None,
            "difficulty": q.difficulty if q else None,
            "answer": q.answer if q else None,
            "analysis": q.analysis if q else None,
            "knowledge_point_id": q.knowledge_point_id if q else None,
        })
    return {
        "paper": {
            "id": paper.id,
            "name": paper.name,
            "grade_id": paper.grade_id,
            "subject_id": paper.subject_id,
            "total_score": float(paper.total_score or 0),
            "duration": paper.duration,
            "difficulty_ratio": paper.difficulty_ratio,
            "exam_type": paper.exam_type,
            "standard_id": paper.standard_id,
            "status": paper.status,
            "description": paper.description,
        },
        "items": items,
    }


def load_snapshot(db: Session, paper_id: int, version: int) -> Optional[Dict[str, Any]]:
    """按版本号取快照内容（不存在返回 None）。"""
    row = db.scalar(select(PaperVersion).where(
        PaperVersion.paper_id == paper_id, PaperVersion.version == version))
    if not row:
        return None
    try:
        data = json.loads(row.snapshot or "{}")
    except (ValueError, TypeError):
        return None
    return data if isinstance(data, dict) else None


# ---------------------------------------------------------------- 版本对比（F-02）
PAPER_FIELD_LABELS = {
    "name": "试卷名称", "duration": "考试时长", "description": "命题说明",
    "difficulty_ratio": "难度分布", "exam_type": "考试类型",
    "standard_id": "命题标准", "total_score": "总分", "status": "状态",
}

ITEM_FIELD_LABELS = {
    "score": "分值", "section_name": "所属大题", "section_sort": "大题序号",
    "stem": "题干", "answer": "答案", "analysis": "解析",
    "difficulty": "难度", "type": "题型",
}

# 长文本只回传摘要：一份卷子 20 道题的完整题干/答案/解析轻松上百 KB，
# 版本对比的用途是"看清改了什么"，不是"全文阅读器"。
SHORT_TEXT_CHARS = 80


def _short(value: Any) -> Any:
    """字符串截断；非字符串原样返回（分值/序号等要精确值）。"""
    if isinstance(value, str) and len(value) > SHORT_TEXT_CHARS:
        return value[:SHORT_TEXT_CHARS] + "…"
    return value


def _canon(value: Any, field: str) -> Any:
    """把值转成**可比较**的形式，避免"看起来没变却报变更"。

    - 浮点：分值 5 与 5.0 是同一次编辑的结果，不该显示成改动
    - `difficulty_ratio`：库里是 JSON 文本，键序不同也算相等
    """
    if value is None:
        return None
    if field in ("score", "total_score"):
        try:
            return round(float(value), 2)
        except (TypeError, ValueError):
            return value
    if field == "difficulty_ratio":
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except (ValueError, TypeError):
                return value
        if isinstance(value, dict):
            return json.dumps(value, sort_keys=True, ensure_ascii=False)
    return value


def _diff_scalar_fields(before: Dict[str, Any], after: Dict[str, Any],
                        labels: Dict[str, str]) -> list:
    changes = []
    for field, label in labels.items():
        b = _canon(before.get(field), field)
        a = _canon(after.get(field), field)
        if b == a:
            continue
        changes.append({
            "field": field, "label": label,
            "before": _short(before.get(field)), "after": _short(after.get(field)),
        })
    return changes


def _index_items(items: list) -> Dict[int, list]:
    """按 question_id 建索引。**同一道题可能在卷中出现多次**（重复题），
    所以值是一个列表，配对时按出现顺序消费，不能简单 dict 覆盖。"""
    idx: Dict[int, list] = {}
    for it in items or []:
        try:
            qid = int(it.get("question_id") or 0)
        except (TypeError, ValueError):
            continue
        idx.setdefault(qid, []).append(it)
    return idx


def diff_snapshots(before: Dict[str, Any], after: Dict[str, Any],
                   *, before_label: str, after_label: str) -> Dict[str, Any]:
    """对比两份快照，返回结构化差异（供「回溯前先看差异」用）。

    before/after 都是 `build_snapshot()` 的产物（历史版本来自库里的 JSON，
    当前版本现算），所以两侧字段完全同构，不需要兼容旧格式。
    """
    b_paper = (before or {}).get("paper") or {}
    a_paper = (after or {}).get("paper") or {}
    paper_changes = _diff_scalar_fields(b_paper, a_paper, PAPER_FIELD_LABELS)

    b_idx = _index_items((before or {}).get("items") or [])
    a_idx = _index_items((after or {}).get("items") or [])

    added, removed, changed = [], [], []
    matched = 0
    for qid, a_list in a_idx.items():
        b_list = b_idx.get(qid) or []
        # 两侧都有的份数：多出来的在 after 侧是"新增"，在 before 侧是"移除"
        common = min(len(a_list), len(b_list))
        matched += common
        for pos, a_item in enumerate(a_list):
            if pos >= common:
                added.append({
                    "question_id": qid,
                    "stem": _short(a_item.get("stem")),
                    "score": a_item.get("score"),
                    "section_name": a_item.get("section_name"),
                })
                continue
            b_item = b_list[pos]
            field_changes = _diff_scalar_fields(b_item, a_item, ITEM_FIELD_LABELS)
            # 排序变化单独提示：题号动了但内容没动，也是教师关心的
            if (b_item.get("section_sort"), b_item.get("sort_order")) != (
                    a_item.get("section_sort"), a_item.get("sort_order")):
                field_changes.append({
                    "field": "sort_order", "label": "题序",
                    "before": f"大题{b_item.get('section_sort') or 0}/第{b_item.get('sort_order')}题",
                    "after": f"大题{a_item.get('section_sort') or 0}/第{a_item.get('sort_order')}题",
                })
            if field_changes:
                changed.append({
                    "question_id": qid,
                    "stem": _short(a_item.get("stem") or b_item.get("stem")),
                    "section_name": a_item.get("section_name"),
                    "changes": field_changes,
                })
    for qid, b_list in b_idx.items():
        a_count = len(a_idx.get(qid) or [])
        for b_item in b_list[a_count:]:
            removed.append({
                "question_id": qid,
                "stem": _short(b_item.get("stem")),
                "score": b_item.get("score"),
                "section_name": b_item.get("section_name"),
            })

    unchanged = max(0, matched - len(changed))

    parts = []
    if added:
        parts.append(f"新增 {len(added)} 题")
    if removed:
        parts.append(f"移除 {len(removed)} 题")
    if changed:
        parts.append(f"{len(changed)} 题有改动")
    if paper_changes:
        parts.append("卷面信息有变动（" + "、".join(c["label"] for c in paper_changes) + "）")
    summary = f"{before_label} → {after_label}：" + ("；".join(parts) if parts else "无差异")

    return {
        "from": before_label,
        "to": after_label,
        "has_changes": bool(paper_changes or added or removed or changed),
        "summary": summary,
        "paper_changes": paper_changes,
        "items": {
            "added": added, "removed": removed, "changed": changed,
            "unchanged": max(0, unchanged),
        },
    }


def snapshot(db: Session, paper: Paper, user_id: Optional[int],
             change_note: str = "") -> PaperVersion:
    """写入一条版本快照，并把 paper.current_version 推进到该版本号。

    不 commit——由调用方统一提交，保证「改卷 + 快照」在同一事务里，
    不会出现"改了但没快照"或"有快照但没改"的中间态。

    **版本号必须重试**（P2-19）：`max(version)+1` 是「先读后写」，两个人同时
    编辑同一份卷子（同一老师的两个标签页、或协同场景）会算出同一个号，
    后写入的那个撞 `uq_paper_version` 唯一约束，表现为随机冒出的 400
    「数据冲突」。旧实现只做了一次 `existing >= current` 的兜底，
    只能挡住「同一请求里连续两次 snapshot」，挡不住并发。
    这里用 SAVEPOINT 包裹每次尝试：失败只回滚这条 INSERT，
    调用方在本次请求里已经做过的改卷操作不受影响。
    """
    db.flush()  # 保证 paper.items 读到最新
    # 快照内容与版本号无关，只在循环外算一次：循环里重算是纯浪费
    # （一份卷的 build_snapshot 要遍历全部题项并序列化）。
    data = build_snapshot(db, paper)

    last_exc: Optional[Exception] = None
    for _attempt in range(_VERSION_RETRY):
        version = _pick_version(db, paper)
        row = PaperVersion(
            paper_id=paper.id,
            version=version,
            snapshot=json.dumps(data, ensure_ascii=False),
            change_note=change_note[:255] or None,
            item_count=len(data["items"]),
            total_score=float(data["paper"]["total_score"] or 0),
            created_by=user_id,
        )
        try:
            with db.begin_nested():
                db.add(row)
                db.flush()
        except IntegrityError as exc:  # 唯一约束撞车 → 重新取号再试
            last_exc = exc
            logger.warning(
                "试卷 %s 版本号 %s 撞车，重试（%s）", paper.id, version, exc)
            continue
        paper.current_version = version
        db.flush()
        # 裁剪必须在 flush 之后：此时新版本已入库，按 version 倒序切片才是准的。
        _prune_versions(db, paper.id)
        return row

    logger.error("试卷 %s 版本号连续 %s 次撞车，放弃", paper.id, _VERSION_RETRY)
    raise ConflictException(
        "该试卷正在被其他操作修改，请刷新后重试",
        detail={"paper_id": paper.id, "retry_exhausted": True},
    ) from last_exc


def _pick_version(db: Session, paper: Paper) -> int:
    """算下一个版本号：取的 max 必须来自**库**，不能只用内存里的 current_version。

    内存值可能是本请求早先推进过的（一次保存会写两条快照：编辑题目 + 编辑完成），
    所以取两者较大值；再用库里实际的 max 兜住并发写入。
    """
    current = paper.current_version or 1
    existing = db.scalar(select(func.max(PaperVersion.version)).where(
        PaperVersion.paper_id == paper.id)) or 0
    return max(current, existing + 1)


