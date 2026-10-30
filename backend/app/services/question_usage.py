"""题目引用计数（`Question.usage_count`）的唯一维护口。

## 为什么不在各入口自己 `+1` / `-1`

`usage_count` 的语义是「该题当前被多少份试卷引用」，唯一的消费者是组卷的
「少用优先」排序（`ORDER BY usage_count ASC`）—— 值一旦虚高，新题永远排在
前面，老题被反复抽中，排序策略形同失效。

历史实现是四条写入路径各自记账，口径互不一致，实测形成如下矩阵：

| 入口 | 旧行为 | 后果 |
|---|---|---|
| `POST /papers`（手动组卷） | 不加 | 手工卷里的题永远算"没用过" |
| `POST /papers/{id}/copy` | 不加 | 复制 N 次也不计入 |
| `PUT /papers/{id}`（编辑） | `_write_items` 插新 +1 / 删旧 -1 | 首次为卷子补题时凭空 +n |
| `DELETE /papers/{id}` | 不减 | 删卷后计数永久虚高 |
| `POST /papers/batch`（delete） | 不减 | 同上，批量删更明显 |
| `DELETE /{paper_id}/items/{item_id}` | 不减 | 逐题移除后残留 |
| `POST /compose/save` | +n | 唯一"正确"的一条 |

于是「编辑一次卷子」和「删掉一份卷子」会让同一道题的计数朝相反方向漂移，
且没有任何一处能说明当前值是怎么来的。

**改为幂等重算**：任何改动 `edu_paper_item` 的入口，在 flush 之后把涉及的
题目 id 集合交给 `recount_usage()`，值就等于「当前真实引用数」。重算不依赖
历史值，所以不会积累误差，重复调用结果相同（幂等），也天然覆盖了并发下
"两次记账只成功一次"的问题。

调用约定：
- 必须在题项 INSERT / DELETE **flush 之后**调用，否则子查询计数是旧值；
- 参数传「本次涉及的题目 id 并集」（新增的 ∪ 被移除的），漏掉被移除的题会
  让它们停在旧值上；
- 传 `None` 表示全量重算，仅供订正脚本与运维使用（会扫全表）。
"""
from typing import Iterable, Optional, Set

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.models import PaperItem, Question


def recount_usage(db: Session, question_ids: Optional[Iterable[int]] = None) -> int:
    """把 `usage_count` 重算为「当前引用该题的题项数」。

    返回实际被检查的题目数（非变更数）。传 `None` 时全量重算。

    ## 为什么用一条 SQL 而不是"查出来再逐条赋值"

    逐条赋值是「读 → 算 → 写」三步，两次并发重算可能都基于同一份旧快照，
    后写者覆盖前写者（在 PostgreSQL 这类读已提交隔离级别下真实存在）。
    改成 `UPDATE ... SET usage_count = (SELECT COUNT(*) ...)` 之后，
    读与写发生在同一条语句里，由数据库自己保证原子性：SQLite 下被库级写锁
    序列化，PostgreSQL 下是行级原子更新。极端并发下也不再需要"下次写入修正"。

    ## 为什么必须 expire

    `synchronize_session=False` 不刷新 ORM 身份映射里已加载的 `Question`。
    若同一 Session 之前 `db.get(Question, qid)` 过，对象上仍是旧 `usage_count`，
    后续 `commit()` 的脏检查会把**旧值写回去**，等于把刚算对的值覆盖掉。
    这里精确过期这些对象（而不是 `expire_all()`，那会连带把 `paper.items`
    等关系全部失效）。
    """
    ids: Set[int] = set()
    if question_ids is not None:
        for qid in question_ids:
            try:
                ids.add(int(qid))
            except (TypeError, ValueError):
                continue
        # 空集合代表"本次没有涉及任何题目"，直接返回：不能退化成全量重算，
        # 否则一次空操作会意外扫全表并把所有题的计数改掉。
        if not ids:
            return 0

    # 关联子查询：计数只针对外层正在更新的那一道题
    counter = (
        select(func.count(PaperItem.id))
        .where(PaperItem.question_id == Question.id)
        .correlate(Question)
        .scalar_subquery()
    )
    stmt = update(Question).values(usage_count=counter)
    if ids:
        stmt = stmt.where(Question.id.in_(ids))
    db.execute(stmt.execution_options(synchronize_session=False))

    touched = ids if ids else None
    for obj in list(db.identity_map.values()):
        if not isinstance(obj, Question):
            continue
        if touched is None or obj.id in touched:
            db.expire(obj)
    return len(ids) if ids else -1


def question_ids_of_paper(db: Session, paper_id: int) -> Set[int]:
    """取某份试卷当前引用的题目 id 集合（删除前快照用）。"""
    rows = db.execute(
        select(PaperItem.question_id).where(PaperItem.paper_id == paper_id)
    ).all()
    return {int(r[0]) for r in rows if r[0] is not None}


def question_ids_of_papers(db: Session, paper_ids: Iterable[int]) -> Set[int]:
    """批量版本：多份试卷的题目 id 并集。"""
    ids = [int(p) for p in paper_ids]
    if not ids:
        return set()
    rows = db.execute(
        select(PaperItem.question_id).where(PaperItem.paper_id.in_(ids))
    ).all()
    return {int(r[0]) for r in rows if r[0] is not None}
