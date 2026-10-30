"""一次性订正 `Question.usage_count`（题目被引用次数）。

背景：`usage_count` 历史上由各写入口自行 `+1` / `-1` 维护，而手动组卷、复制、
删除、批量删除、移除单题五条路径根本没记账，值早已偏离真实引用数。修复方式
是把维护口径改成「改完题项后幂等重算」（`services/question_usage.recount_usage`），
但**存量数据仍是错的**，需要跑一次本脚本对齐。

判定基准唯一且可复核：`COUNT(edu_paper_item WHERE question_id = q.id)`，
即"当前有多少份试卷引用该题"。不含历史引用（试卷已删的引用本就该消失）。

用法：
    # 只体检，不写库（默认）
    python tools/fix_usage_count.py
    # 实际写库
    python tools/fix_usage_count.py --apply
    # 只看漂移最大的 N 条
    python tools/fix_usage_count.py --top 50

退出码：0 = 正常（无论是否有漂移）；1 = 连库/参数错误。
"""
import argparse
import os
import sys

BACKEND = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
sys.path.insert(0, BACKEND)

from sqlalchemy import func, select  # noqa: E402

from app.core.database import SessionLocal  # noqa: E402
from app.models import PaperItem, Question  # noqa: E402
from app.services.question_usage import recount_usage  # noqa: E402


def collect(db):
    """返回 [(qid, stored, actual)]，actual 为真实引用数。"""
    counts = {
        int(qid): int(cnt or 0)
        for qid, cnt in db.execute(
            select(PaperItem.question_id, func.count(PaperItem.id))
            .group_by(PaperItem.question_id)
        ).all()
    }
    rows = db.execute(select(Question.id, Question.usage_count)).all()
    result = []
    for qid, stored in rows:
        actual = counts.get(int(qid), 0)
        if int(stored or 0) != actual:
            result.append((int(qid), int(stored or 0), actual))
    return result, counts


def main() -> int:
    parser = argparse.ArgumentParser(description="订正 Question.usage_count")
    parser.add_argument("--apply", action="store_true", help="实际写库（默认只体检）")
    parser.add_argument("--top", type=int, default=20, help="展示前 N 条漂移（默认 20）")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        total = int(db.scalar(select(func.count()).select_from(Question)) or 0)
        drift, counts = collect(db)
        print(f"题目总数            : {total}")
        print(f"被试卷引用的题目数  : {len(counts)}")
        print(f"计数与实际不一致    : {len(drift)}")

        if not drift:
            print("结论：usage_count 已与真实引用数一致，无需订正。")
            return 0

        stored_sum = sum(s for _, s, _ in drift)
        actual_sum = sum(a for _, _, a in drift)
        print(f"漂移量合计          : 存储 {stored_sum} → 实际 {actual_sum} "
              f"（差 {stored_sum - actual_sum:+d}）")

        # 按偏差绝对值排序，先看污染最严重的题（它们直接决定「少用优先」的排序结果）
        ordered = sorted(drift, key=lambda r: -abs(r[1] - r[2]))[: max(1, args.top)]
        print(f"\n前 {len(ordered)} 条：")
        print(f"  {'题目id':>8}  {'存储值':>6}  {'实际值':>6}  {'偏差':>6}")
        for qid, stored, actual in ordered:
            print(f"  {qid:>8}  {stored:>6}  {actual:>6}  {stored - actual:>+6}")

        if not args.apply:
            print("\n当前为体检模式（未写库）。确认无误后加 --apply 执行订正。")
            return 0

        recount_usage(db, None)   # None = 全量重算
        db.commit()
        after, _ = collect(db)
        print(f"\n已订正 {len(drift)} 条；复查剩余不一致：{len(after)} 条")
        return 0 if not after else 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
