"""AI 长任务（`sys_agent_job`）的**超时判据与僵尸收割**（B2）。

## 问题的形状

出题/组卷（`api/v1/agent.py`）与 AI 教案（`api/v1/lesson_ai.py`）都采用
「提交即返回 job_id，后台 daemon 线程执行，前端轮询」的模式。daemon 线程
的致命属性是：**进程退出时无线程收尾**。

于是进程重启（发布、OOM、`docker restart`、崩溃）之后：

    sys_agent_job.status = 'running'     ← 永远是 running
    finished_at          = NULL
    error                = NULL

前端按 status 轮询，看到 `running` 就一直转圈 —— 无上限、无超时、
无法自愈。用户只能刷新页面重来，且那条记录永远占着"运行中"。

## 修复前两个接口的不同表现（这是本次要修的核心不对称）

| 接口 | 超时判定 | 后果 |
| --- | --- | --- |
| `GET /lesson/ai/jobs/{id}` | 有（`_job_progress`） | 5 分钟后显示"生成超时" |
| `GET /agent/jobs/{id}` | **完全没有** | 永久 `running`，前端无限轮询 |
| `GET /agent/jobs`（列表） | **完全没有** | 列表里永久显示"运行中" |

同一个 `sys_agent_job` 表、同一个后台线程模式，两处判据不一致 ——
所以本模块把判据抽出来**单点定义**，两个接口都调它。留在各接口里各写一份
必然漂移（这已经是第二次：教案那边写了、出题这边没写）。

## 为什么是「读时判定」而不是「只在启动时收割」

两者都要，但职责不同：

- **读时判定**（`effective_status`）：不改库，只在响应里把僵尸任务
  呈现为 failed。好处是**跨进程安全** —— 本进程无法知道别的进程是不是
  真的在跑这个任务，但"创建超过 N 秒还没结束"这个事实足够判定给用户看。
- **启动收割**（`reap_orphan_jobs`）：进程刚启动时，**本进程内不可能有
  任何在跑的 AgentJob**（线程是随进程诞生的），所以启动瞬间把遗留的
  running/pending 标记为 failed 是安全的 —— 前提是给一个宽限期，
  见 `reap_orphan_jobs` 的 docstring。

只做启动收割不够：多 worker 下 worker B 启动时，worker A 手里可能真有
在跑的任务（那是 A 的线程，B 看不到）。只做读时判定也不够：库里的
脏状态永远不落定，列表页、统计、以及"是否还能重试"都无从判断。

## 阈值为什么是 300s

与 `lesson_ai.JOB_TIMEOUT_SECONDS` 对齐（同一个表、同一类任务，不该有
两套阈值）。实测真实 LLM 下出题 20~60s、组卷 30~90s、教案 25~60s，
300s 有 3~5 倍余量；而 `llm_timeout`（默认 60s）× `max_retries`(1)
最坏单次 120s，一道题失败重试后仍在 300s 内。取更小的值会误杀正常任务。
"""
from datetime import datetime
from typing import Any, Dict, Optional

from app.utils.common import now_local

# 任务从创建到允许被判"僵尸"的宽限秒数。
# 与 `api/v1/lesson_ai.py:JOB_TIMEOUT_SECONDS` 同值，两处必须一致 ——
# 该常量现在从这里导入，不要再在接口里各自定义。
JOB_TIMEOUT_SECONDS = 300

# 启动收割的**额外**宽限：在 JOB_TIMEOUT_SECONDS 之上再留一段时间。
# 理由见 `reap_orphan_jobs`：多 worker 场景下，别的 worker 可能刚接到任务。
REAP_GRACE_SECONDS = 600

STATUS_RUNNING = ("pending", "running")


def is_timed_out(
    status: Optional[str], created_at: Optional[datetime],
    *, timeout_seconds: int = JOB_TIMEOUT_SECONDS,
    now: Optional[datetime] = None,
) -> bool:
    """任务是否已超时（只对 pending/running 有意义）。

    `created_at` 而不是 `started_at`：僵尸任务的典型形态是
    **`started_at` 根本没写**（线程没起来就崩了），只有 `created_at` 一定存在
    （它是 default=now_local，INSERT 时就有）。用 started_at 判会漏掉最常见的那种。

    `created_at` 为空的脏数据**不判超时**：没有时间基准就无法断言它超时了，
    宁可继续显示 running（用户可以手动重试），也不能凭空把可能正常的任务
    判死。这类行由启动收割按 `REAP_GRACE_SECONDS` 兜底处理。

    Args:
        now: 基准时刻，默认取 `now_local()`。**仅供测试注入**。

            为什么必须可注入：判据的边界语义是「耗时 **严格大于** 阈值才算
            超时」（`>` 而非 `>=`）。若测试写成
            `is_timed_out("running", now_local() - timedelta(seconds=T))`，
            那么"构造 created_at"与"函数内部取 now"是两次独立调用，
            中间流逝的微秒会让耗时变成 `T + 0.000x` → 严格大于 T → 判超时。
            这个断言在本地（调用快）侥幸通过、在 CI（机器慢）稳定失败，
            属于典型的"测试自己有时序竞态"。实测确认过：CI 上 47/48，
            唯一红项就是它。注入固定 now 后边界变成确定的。
    """
    if status not in STATUS_RUNNING:
        return False
    if created_at is None:
        return False
    base = now if now is not None else now_local()
    return (base - created_at).total_seconds() > timeout_seconds


def effective_status(
    status: Optional[str], created_at: Optional[datetime],
    *, timeout_seconds: int = JOB_TIMEOUT_SECONDS,
    now: Optional[datetime] = None,
) -> str:
    """对外呈现的状态：僵尸任务呈现为 `failed`。

    `now` 与 `is_timed_out` 一致地可注入（BUG-018）：此前包装层不透传，超时
    边界只能依赖真实时钟，会在 CI 慢机上复现「构造 now 与内部取 now 微秒漂移」
    导致的偶发红。注入固定基准后边界可确定性断言。
    """
    if is_timed_out(status, created_at, timeout_seconds=timeout_seconds, now=now):
        return "failed"
    return status or "pending"


def timeout_message(timeout_seconds: int = JOB_TIMEOUT_SECONDS) -> str:
    """超时任务的面向用户文案（与教案侧口径统一）。"""
    return ("任务超时（超过 %d 秒未完成）。服务可能已重启，"
            "该后台任务已中断，请重试" % timeout_seconds)


def apply_timeout(job: Any, data: Dict[str, Any],
                  *, timeout_seconds: int = JOB_TIMEOUT_SECONDS,
                  now: Optional[datetime] = None) -> Dict[str, Any]:
    """把超时判定写进已 dict 化的任务响应（原地修改并返回）。

    只在真的超时时才覆盖 `status`/`error` —— 正常任务的自有 error
    （如"知识点不存在"）必须原样保留，不能被一句"超时"盖掉。
    """
    if is_timed_out(getattr(job, "status", None),
                    getattr(job, "created_at", None),
                    timeout_seconds=timeout_seconds, now=now):
        data["status"] = "failed"
        data["timed_out"] = True
        # 保留原始 error 到独立字段：超时是**呈现层结论**，库里其实没写 error，
        # 但万一有（例如线程写了 error 却没来得及改 status），不能丢失。
        if data.get("error"):
            data["error_before_timeout"] = data["error"]
        data["error"] = timeout_message(timeout_seconds)
    else:
        data["timed_out"] = False
    return data


def reap_orphan_jobs(db: Any, *, grace_seconds: int = REAP_GRACE_SECONDS) -> int:
    """**启动时**收割遗留的 pending/running 任务，返回收割条数。

    ## 为什么启动瞬间可以直接判死

    AgentJob 的执行方式只有一种：`threading.Thread(..., daemon=True)`，
    线程随进程生随进程死。所以**本进程刚启动时，本进程内绝对没有任何
    在跑的 AgentJob**。库里遗留的 running 一定是上一个进程的遗骸。

    ## 为什么还要 grace_seconds

    多 worker（`uvicorn --workers N`）下每个 worker 都会跑启动钩子。
    worker B 启动时，worker A 手里可能有**真的在跑**的任务 —— B 看不到
    A 的线程，只能看库。若 B 无条件把 running 判死，A 那份正常任务就被
    误杀了（前端看到 failed，而 A 稍后还会写 success，状态来回跳）。

    所以判据是 `created_at < now - (JOB_TIMEOUT_SECONDS + REAP_GRACE_SECONDS)`：
    即"已经超过正常超时阈值、再等一个宽限期还没结束"。这个时间窗内
    正常的任务（20~90s）早就结束了，留下来的必然是遗骸。

    单 worker（当前生产形态，`--workers 1`）下这个宽限期是保守的，
    代价只是"重启后最长 15 分钟才清理"，而**读时判定**会立刻让前端
    看到"超时"，用户侧无感。宁可晚清理，也不误杀。

    ## 为什么也要清 JobExecutionLog

    定时任务（`sys_job_execution_log`）同样写 `status="running"` 后跑任务体，
    进程在任务体中崩溃就留下永久 running。它的执行锁 `sys_job_lock` 会
    按租约（1800s）自动失效，但执行记录不会自愈 —— 运维在"任务执行记录"
    页看到一条永远跑着的记录，会误判"任务卡死正在抢救"。

    与 AgentJob 的区别：`JobExecutionLog` 没有"前端无限轮询"的放大效应，
    但它进统计（成功率/耗时），永久 running 会污染报表。

    ## 失败不阻断启动

    调用方（`main.lifespan`）必须容忍本函数抛错：收割是旁路维护，
    让它阻断启动是本末倒置。本函数内部已 try/except 兜住，返回 0。
    """
    from sqlalchemy import text

    from app.core.logger import get_logger

    logger = get_logger("agent_job")
    now = now_local()
    from datetime import timedelta

    cutoff = (now - timedelta(seconds=int(JOB_TIMEOUT_SECONDS + grace_seconds))
              ).strftime("%Y-%m-%d %H:%M:%S.%f")
    now_str = now.strftime("%Y-%m-%d %H:%M:%S.%f")
    msg = timeout_message()

    total = 0
    # 两张表的名字不同、时间列不同（AgentJob 用 created_at，执行记录用
    # started_at —— 后者是 INSERT 时写的，一定存在），所以分开两条明确的
    # SQL，不拼动态字符串：拼接式的 `SET` 片段在改表时极易漏改一处，
    # 而且读的人得在脑子里求值三元表达式。
    statements = (
        (
            "sys_agent_job",
            "UPDATE sys_agent_job"
            "   SET status = 'failed', error = :msg, progress = 100,"
            "       finished_at = :now"
            " WHERE status IN ('pending', 'running')"
            "   AND created_at < :cutoff",
        ),
        (
            "sys_job_execution_log",
            # duration_ms = 0：报表里 NULL 会让"平均耗时"的分母与分子不一致，
            # 写 0 至少让那一行在统计上是自洽的（且它确实没跑完）。
            "UPDATE sys_job_execution_log"
            "   SET status = 'failed', message = :msg,"
            "       finished_at = :now, duration_ms = 0"
            " WHERE status IN ('pending', 'running')"
            "   AND started_at < :cutoff",
        ),
    )
    for table, sql in statements:
        try:
            result = db.execute(
                text(sql), {"now": now_str, "cutoff": cutoff, "msg": msg}
            )
            db.commit()
            n = int(result.rowcount or 0)
            total += n
            if n:
                logger.warning(
                    f"启动收割：{table} 有 {n} 条遗留 running/pending 任务"
                    f"（进程重启导致后台线程丢失），已标记为 failed"
                )
        except Exception as exc:  # noqa: BLE001  收割失败不能阻断启动
            db.rollback()
            logger.warning(f"启动收割 {table} 失败（不影响启动）: {exc}")
    return total
