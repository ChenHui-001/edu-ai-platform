#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""离线单元回归：第一批性能修复的语义锁与复杂度锁（不经 HTTP）。

## 为什么这些断言必须放在单元层

e2e 跑的是「正常数据 + 正常流程」，它能证明接口还活着，但**证不了这一批
优化没把语义改掉**。四个修复里，有三个的性质在 e2e 数据形态下根本不会暴露：

1. **`_calc_rank` 的竞赛排名语义**（a9269bf + e79c9d4）
   原实现是「整行取回 → 降序排序 → `list.index(score)`」，注意它判的是
   **分值在不在列表里**，不是「本人这一行在不在 peers 里」。当交卷学生没有
   班级（`class_id IS NULL`，不会进入 peers）时：
     - 若全班没人同分 → 原实现落到 `len(scores)+1`（末位）
     - 若有人同分      → 原实现按分值定位，给出中间名次
   只算「比我高的人数 + 1」会把前者算成中间名次 —— 这是我在写修复方案时
   漏掉的语义，由实现方用 A/B 对拍发现（3732 例里 211 例不一致，全部是
   NULL 班级）。e2e 里的学生都有班级，永远碰不到这个分支。
   所以这里把**原实现逐字复制成 oracle**，用同一批数据对拍。
2. **`_calc_rank` 的语句数与班级规模无关**（a9269bf）
   这是性能修复本身的定义性性质。任何「顺手把行取回来再算」的改动都会让
   这个计数涨上去 —— 而结果仍然正确，语义断言抓不到。
3. **日报的时间窗边界**（076c086 + e79c9d4）
   左闭右开 `[昨日00:00, 今日00:00)` 与 `func.date(col) == 昨日` 在绝大多数
   数据上结果相同，只在**零点整**这一瞬间分道扬镳。
4. **日报不得再用 `func.date(col)` 包裹列**（076c086）
   函数包裹会让 `submit_time` 上的索引彻底失效（全表扫描 + 逐行求值），
   但它**不改变查询结果** —— 第 3 条断言抓不到，只能单独守。

## 与 e2e 的分工

| 性质 | e2e | 本文件 |
| --- | --- | --- |
| 心跳成功不再写操作日志 | ✅（`test_requirements` 15） | — |
| 心跳仍然改到业务字段 | ✅（`test_student` 3） | — |
| 排名与「原实现」逐例一致 | ❌ 碰不到 NULL 班级 | ✅ |
| 排名语句数不随 N 增长 | ❌ 看不出 | ✅ |
| 日报零点边界归属 | ❌ 依赖运行时刻 | ✅ |
| 日报索引可用 | ❌ 看不出 | ✅（源码守） |

用法：
    python tests/test_unit_perf_batch1.py

退出码：0 = 全部通过，1 = 有失败。
"""

import os
import sys
import tempfile
from datetime import datetime

# ---- 必须在导入 app.* 之前定好环境：避免在仓库里建出脏库、避免拉外网 ----
_TMP = tempfile.mkdtemp(prefix="unit_perf_batch1_")
os.environ["DATABASE_URL"] = "sqlite:///" + os.path.join(_TMP, "unit.db").replace("\\", "/")
os.environ["LLM_ENABLED"] = "false"
os.environ["SCHEDULER_ENABLED"] = "false"
os.environ.setdefault("SECRET_KEY", "unit_test_secret_key_not_for_prod")

_BACKEND = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"
)
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

from sqlalchemy import event, select  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

import app.models  # noqa: F401,E402  确保全部表注册到 Base.metadata
from app.core.database import Base, engine  # noqa: E402
from app.models import (  # noqa: E402
    Class, Grade, IdentityType, Paper, Submission, Subject, Task, User, UserStatus,
)
from app.services.grading_service import _calc_rank  # noqa: E402

_FAILED = []
_PASSED = 0


def ok(name, cond, detail=""):
    """断言并打印。刻意不叫 check()：tools/check_weak_assertion.py 只扫
    e2e 的 check(...) 恒真写法，两边命名分开，扫描结果不会互相污染。"""
    global _PASSED
    if cond:
        _PASSED += 1
        print(f"  [PASS] {name}" + (f"  -> {detail}" if detail else ""))
    else:
        _FAILED.append(name)
        print(f"  [FAIL] {name}  -> {detail}")


# ---------------------------------------------------------------- 成本度量
# 只数 SQL 语句数**不足以**守住这次优化，但**数对象数也不可靠**：
# identity_map 是弱引用表，`_calc_rank` 里的局部变量在函数返回后立刻被回收，
# 漏掉的对象根本数不到（实测 6 人/60 人都统计成 0 行）。
# 所以改为直接看发出去的 SQL：新实现让数据库 COUNT 完只回一个整数，
# 旧实现必然有一条「取出 edu_submission 全部列」的 peers 查询。
# 这个判据不受 ORM 对象生命周期影响，也不受写法微调影响。
Session = sessionmaker(bind=engine)

_SQL = []


@event.listens_for(engine, "before_cursor_execute")
def _capture_sql(conn, cursor, statement, params, context, executemany):
    _SQL.append(statement)


def _actual(sid):
    """用当前实现算名次，返回 (名次, 本次发出的 SQL 列表)。"""
    db = Session()
    try:
        target = db.get(Submission, sid)
        del _SQL[:]
        rank = _calc_rank(db, target)
        return rank, list(_SQL)
    finally:
        db.close()


def _fetches_peer_rows(statements):
    """是否存在「把 edu_submission 全列取回内存」的语句（旧实现的形态）。

    判据只看 SELECT 列表里 `edu_submission.` 的**列引用个数**，不看
    `FROM edu_submission`：新实现里 `SELECT edu_submission.student_id
    FROM edu_submission WHERE ...` 这样的子查询是正常的（取学生 id），
    它也会命中 "from edu_submission"，但只取一列、不构成 O(N) 行回传。
    旧实现是 `SELECT edu_submission.id, edu_submission.task_id, ...` 全列。
    """
    hits = []
    for s in statements:
        low = s.lower()
        if "from edu_submission" not in low:
            continue
        # 聚合查询（新实现）在 SELECT 列表里也会多次引用 edu_submission.score，
        # 所以必须先按「有没有聚合函数」把它排除，否则会把 COUNT 语句误判成
        # 「全列取回」—— 这正是第一版判据写错的地方。
        if "count(" in low or "sum(" in low:
            continue
        head = low.split(" from edu_submission", 1)[0]
        if head.count("edu_submission.") >= 5:
            hits.append(s.split("\n")[0][:90])
    return hits


def _reference_rank(db, submission):
    """a9269bf **之前**的实现，逐字复制，作为语义基准（oracle）。

    不要"优化"这个函数：它的价值就在于它是旧行为本身。写成同一个算法就
    失去了对拍意义（两边一起错、一起绿）。
    """
    task = db.get(Task, submission.task_id)
    if not task:
        return None
    # 找出该任务下同班学生
    class_ids = db.scalars(
        select(User.class_id).where(
            User.class_id.isnot(None),
            User.id.in_(select(Submission.student_id).where(Submission.task_id == task.id)),
        )
    ).all()
    peers = db.scalars(
        select(Submission).where(
            Submission.task_id == task.id,
            Submission.student_id.in_(select(User.id).where(User.class_id.in_(class_ids))),
            Submission.score.isnot(None),
        )
    ).all()
    scores = sorted([s.score for s in peers if s.score is not None], reverse=True)
    if submission.score in scores:
        return scores.index(submission.score) + 1
    return len(scores) + 1


# ============================================================
# 造数据
# ============================================================
def _seed(prefix, plan):
    """建一套最小可用的「年级/学科/班级/教师/试卷」，再按 plan 建学生+作答。

    plan 的每一项是 `(班级标记, 分数)`：
      - 班级标记 "A"/"B" → 建在该班级下
      - 班级标记 None    → 学生有 grade 但没有 class_id（真实场景：转班中、
                           导入时班级未填），这正是原实现会走「末位兜底」的分支
    返回 `{标签: submission_id}`，标签形如 "A1"/"N0"。
    """
    db = Session()
    try:
        grade = Grade(name=f"{prefix}年级", stage="junior", grade_num=7)
        db.add(grade)
        db.flush()
        subject = Subject(name=f"{prefix}学科", grade_id=grade.id)
        db.add(subject)
        db.flush()
        teacher = User(
            username=f"{prefix}_teacher", password="x", real_name=f"{prefix}教师",
            identity=IdentityType.TEACHER.value, status=UserStatus.ACTIVE.value,
        )
        db.add(teacher)
        db.flush()
        klasses = {}
        for tag in sorted({p[0] for p in plan if p[0]}):
            k = Class(name=f"{prefix}班{tag}", grade_id=grade.id)
            db.add(k)
            db.flush()
            klasses[tag] = k.id
        paper = Paper(
            name=f"{prefix}试卷", grade_id=grade.id, subject_id=subject.id,
            creator_id=teacher.id,
        )
        db.add(paper)
        db.flush()
        task = Task(
            title=f"{prefix}任务", paper_id=paper.id, subject_id=subject.id,
            grade_id=grade.id, creator_id=teacher.id,
        )
        db.add(task)
        db.flush()

        out = {}
        counters = {}
        for tag, score in plan:
            # 无班级的分组用 N 作标签（tag 是 None，直接拼会得到 "None1"）
            key = tag or "N"
            counters[key] = counters.get(key, 0) + 1
            label = f"{key}{counters[key]}"
            stu = User(
                username=f"{prefix}_{label}", password="x", real_name=f"{prefix}{label}",
                identity=IdentityType.STUDENT.value, status=UserStatus.ACTIVE.value,
                grade_id=grade.id, class_id=klasses.get(tag),
            )
            db.add(stu)
            db.flush()
            sub = Submission(task_id=task.id, student_id=stu.id, score=score, attempt=1)
            db.add(sub)
            db.flush()
            out[label] = sub.id
        db.commit()
        return out
    finally:
        db.close()


def _expected(sid):
    """用 oracle 算出期望名次（独立会话，避免干扰对象计数）。"""
    db = Session()
    try:
        return _reference_rank(db, db.get(Submission, sid))
    finally:
        db.close()


# ============================================================
# 一、排名语义：与旧实现逐例对拍
# ============================================================
def case_rank_semantics():
    print("\n一、_calc_rank 语义与旧实现对拍（含 NULL 班级 / 并列 / 空分）")

    # 覆盖三类分支：
    #   A1/A2 同分 95 → 竞赛排名并列第 1，A3(90) 应为第 3（中间没有第 2）
    #   B1(80) 来自另一个班 → 仍与 A 班同池比较（原实现的 peers 用的是
    #        「本任务所有提交者的班级集合」，不是「我的班」）
    #   N1(92) 无班级、分数**落在池子中间且与谁都不重** → 旧实现走
    #        len(scores)+1 末位兜底（=5），而「只算比我高的人数 + 1」会给出
    #        3。这是唯一能区分两种算法的数据形态，分数取池子最低值（70）
    #        时两者碰巧都得 5，用例会失去判别力（第一版就是这样写的，
    #        注入错误规格后仍然全绿）。
    #   N2(90) 无班级但与 A3 同分 → 旧实现按分值定位到第 3
    #   A4(None) 分数为空 → 不参与 peers，旧实现同样末位兜底
    plan = [
        ("A", 95.0), ("A", 95.0), ("A", 90.0), ("A", None),
        ("B", 80.0),
        (None, 92.0), (None, 90.0),
    ]
    subs = _seed("rank1", plan)

    total = 0
    for label, sid in subs.items():
        exp = _expected(sid)
        got, _q = _actual(sid)
        total += 1
        ok(f"{label} 名次与旧实现一致", got == exp, f"新={got} 旧={exp}")

    # 单独把三个关键点再点名断言一次：只对上表的话，读者无法从「7/7 一致」
    # 看出究竟守住了什么；名次一旦整体偏移，上面会一起红、看不出是哪个语义。
    ok("并列第一（95/95/90 → 1/1/3）",
       _actual(subs["A1"])[0] == 1 and _actual(subs["A2"])[0] == 1
       and _actual(subs["A3"])[0] == 3,
       f"A1={_actual(subs['A1'])[0]} A2={_actual(subs['A2'])[0]} "
       f"A3={_actual(subs['A3'])[0]}")
    ok("跨班同池排名（B1 为第 4 名）", _actual(subs["B1"])[0] == 4,
       f"B1={_actual(subs['B1'])[0]}")
    # peers 池 = A 班 4 人 + B 班 1 人里有分的 4 条：95/95/90/80
    # （A4 分数为空、N1/N2 无班级，都不进池）。故末位兜底值是 4+1=5。
    ok("无班级且分数唯一 → 末位兜底（不是中间名次）",
       _actual(subs["N1"])[0] == 5, f"N1={_actual(subs['N1'])[0]}")
    ok("无班级但与他班同分 → 按分值定位（与其同分者同名次）",
       _actual(subs["N2"])[0] == _actual(subs["A3"])[0] == 3,
       f"N2={_actual(subs['N2'])[0]} A3={_actual(subs['A3'])[0]}")
    ok("分数为空 → 排在所有有分者之后", _actual(subs["A4"])[0] == 5,
       f"A4={_actual(subs['A4'])[0]}")
    print(f"  共对拍 {total} 例")


# ============================================================
# 二、排名复杂度：不把 peers 全量取回内存
# ============================================================
def case_rank_read_cost():
    print("\n二、_calc_rank 不把 peers 全量取回（O(N²) 回归防线）")

    small = _seed("rankS", [("A", float(90 - i)) for i in range(6)])
    big = _seed("rankB", [("A", float(100 - i * 0.5)) for i in range(60)])

    _v_small, sql_small = _actual(next(iter(small.values())))
    _v_big, sql_big = _actual(next(iter(big.values())))
    # 6 人 → 60 人，语句集合必须一致。旧实现同样是 3 条语句（所以这条抓不到
    # 退化），因此真正的判据是下一条。
    ok("语句数与班级规模无关（6 人 vs 60 人相同）",
       len(sql_small) == len(sql_big),
       f"6 人 {len(sql_small)} 条 / 60 人 {len(sql_big)} 条")
    # ★ 真正的防线：旧实现必然有一条「SELECT edu_submission.id, .task_id,
    #   .student_id, ... 全列」把 N 行读进内存。名次结果完全正确，语义对拍
    #   抓不到它 —— 只有看 SQL 形态才能守住。
    hits = _fetches_peer_rows(sql_big)
    ok("★ 60 人时不出现「全列取回 edu_submission」的查询",
       not hits, f"命中 {len(hits)} 条: {hits[:1]}")


# ============================================================
# 三、日报时间窗边界 + 只取一次时钟
# ============================================================
FIXED_NOW = datetime(2026, 3, 15, 8, 30, 0)


def _seed_daily():
    """按固定「当前时间」造交卷记录，专打零点两侧的边界。"""
    db = Session()
    try:
        stu = db.scalars(select(User).where(User.username == "rank1_A1")).first()
        task = db.scalars(select(Task).where(Task.title == "rank1任务")).first()
        rows = [
            # (提交时间, 分数, 是否应计入昨日)
            (datetime(2026, 3, 14, 0, 0, 0), 80.0, True),      # 左边界：计入
            (datetime(2026, 3, 14, 23, 59, 59), 90.0, True),   # 右边界前一秒：计入
            (datetime(2026, 3, 15, 0, 0, 0), 100.0, False),    # 右边界：不计入
            (datetime(2026, 3, 13, 23, 59, 59), 70.0, False),  # 前一天最后一秒：不计入
            (datetime(2026, 3, 14, 12, 0, 0), None, False),    # 分数为空：不计入
        ]
        for submit_time, score, _hit in rows:
            db.add(Submission(
                task_id=task.id, student_id=stu.id, attempt=1,
                score=score, submit_time=submit_time,
            ))
        db.commit()
        return len(rows)
    finally:
        db.close()


def case_daily_report_window():
    print("\n三、日报时间窗（左闭右开）与「只取一次时钟」")

    from app.services import task_jobs

    _seed_daily()

    calls = {"n": 0}

    def fake_now():
        calls["n"] += 1
        return FIXED_NOW

    origin = task_jobs.now_local
    task_jobs.now_local = fake_now
    del _SQL[:]
    try:
        report = task_jobs.generate_daily_report()
    finally:
        task_jobs.now_local = origin
    daily_sql = [s for s in _SQL if "edu_submission" in s.lower()]

    ok("日期标签取自固定时钟（昨日）", report.get("date") == "2026-03-14",
       f"date={report.get('date')}")
    ok("★ 零点边界归属正确（昨日 00:00 与 23:59:59 计入，今日 00:00 不计入）",
       report.get("submissions") == 2, f"submissions={report.get('submissions')}")
    ok("均分只统计窗口内有分记录", report.get("avg_score") == 85.0,
       f"avg_score={report.get('avg_score')}")
    # 标签与统计窗口必须来自同一瞬间：跨零点执行时若前一次取到昨日 23:59:59、
    # 后一次取到今日 00:00:00，标签写「昨日」而窗口落到了「前日」。
    ok("★ 只调用一次 now_local（标签与窗口同源）", calls["n"] == 1,
       f"调用 {calls['n']} 次")

    # 索引可用性：`func.date(submit_time) = '昨日'` 把列包进函数，SQLite 无法
    # 走 submit_time 索引（全表扫描 + 逐行求值），但**查询结果与半开区间
    # 完全一致** —— 上面三条断言全都抓不到这种退化。
    # 判据看**实际发出的 SQL**而不是源码文本：源码里注释也写着 func.date（说明
    # 历史），按文本匹配会把注释当成违规；而且改写法（比如换个函数包裹）也能
    # 绕过去。这里要求「查询 edu_submission 的语句里不出现被函数包裹的
    # submit_time」且「带上下界参数」。
    wrapped = [s for s in daily_sql if "date(edu_submission.submit_time)" in s.lower()]
    bounded = [s for s in daily_sql
               if "edu_submission.submit_time >=" in s.lower()
               and "edu_submission.submit_time <" in s.lower()]
    ok("★ 日报不再把 submit_time 包进函数（否则索引失效）",
       not wrapped, f"命中 {len(wrapped)} 条" if wrapped else "无函数包裹")
    ok("★ 日报改用半开区间（>= 昨日00:00 且 < 今日00:00）",
       bool(bounded), f"命中 {len(bounded)} 条" if bounded else f"{daily_sql[:1]}")


# ============================================================
# 四、心跳路径的写语句不变量（附诚实说明：本条无判别力）
# ============================================================
def case_heartbeat_noop():
    print("\n四、心跳路径只在该写时写（不变量 + 两条正向对照）")

    from app.api.v1.task import heartbeat as heartbeat_endpoint

    db = Session()
    try:
        sub = db.scalars(
            select(Submission).where(Submission.student_id.isnot(None))
            .order_by(Submission.id)
        ).first()
        stu = db.get(User, sub.student_id)
        sub.duration_seconds = 40
        db.commit()
        sub_id, task_id, stu_id = sub.id, sub.task_id, stu.id
    finally:
        db.close()

    def run_heartbeat(payload):
        s = Session()
        try:
            user = s.get(User, stu_id)
            del _SQL[:]
            out = heartbeat_endpoint(task_id, payload, s, user)
            writes = [x for x in _SQL
                      if x.lstrip().upper().startswith(("UPDATE", "INSERT"))]
            total = s.get(Submission, sub_id).switch_count
            return out, writes, total
        finally:
            s.close()

    # ⚠️ 诚实记录（不要被标题里的「零变更不写」误导）：
    # 实测 SQLAlchemy 对「赋了同值」的属性**不会**标记为脏，commit 时直接
    # 结束事务、不发任何 SQL。因此「零变更心跳不发 UPDATE」在这个 ORM 下
    # **新旧实现都成立** —— 49b5042 那次「按需 commit」并不带来写锁收益，
    # 它只是把意图显式化（防止将来有人往这条路径加字段时意外触发写）。
    # 保留这条断言是为了守住不变量本身，不把它当成该 commit 的判别器；
    # 真正的回归面是下面两条正向对照 —— 优化不得以「少写」换「丢数据」。
    _out, writes_noop, sw_noop = run_heartbeat({"switch": False, "duration_seconds": 40})
    ok("零变更心跳不产生写语句（不变量，非本次优化的判别器）", not writes_noop,
       f"写语句 {len(writes_noop)} 条")

    # 正向对照 1：真切屏必须落库，否则「省掉写」变成了「丢切屏记录」
    _out, writes_sw, sw_after = run_heartbeat({"switch": True, "duration_seconds": 41})
    ok("★ 真切屏心跳照常写库并累加切屏次数", len(writes_sw) >= 1 and sw_after == sw_noop + 1,
       f"写语句 {len(writes_sw)} 条，切屏次数 {sw_noop} -> {sw_after}")

    # 正向对照 2：只改时长也必须落库（前端持续上报累计时长，这是行为数据）
    _out, writes_dur, _sw = run_heartbeat({"duration_seconds": 99})
    ok("★ 仅时长变化仍需落库（防作弊行为数据不可丢）", len(writes_dur) >= 1,
       f"写语句 {len(writes_dur)} 条")


def main():
    print("=" * 72)
    print("离线单元回归：第一批性能修复（排名语义 / 排名复杂度 / 日报时间窗）")
    print("=" * 72)
    Base.metadata.create_all(bind=engine)
    case_rank_semantics()
    case_rank_read_cost()
    case_daily_report_window()
    case_heartbeat_noop()
    print("\n" + "-" * 72)
    total = _PASSED + len(_FAILED)
    print(f"单元回归完成：共 {total} 项 | 通过 {_PASSED} | 失败 {len(_FAILED)}")
    if _FAILED:
        for n in _FAILED:
            print(f"  ✘ {n}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
