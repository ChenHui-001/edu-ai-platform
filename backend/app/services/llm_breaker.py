"""LLM 熔断/冷却状态的**跨进程共享层**（B1）。

状态本身极简单：一行表 + 三处读写。但它有六个「写错了不报错、只静默失效」
的点，全部写在下面 —— 改这个文件之前请先读完。

## ① 时间必须是绝对时间

旧实现把 `_cooldown_until` 存成 `time.monotonic()` 时间戳。monotonic 是
**进程内**单调时钟，各进程起点不同（实测同机两个 Python 进程的差值可达
数十万秒），跨进程比较毫无意义：A 进程写的 `984321.5` 在 B 进程看来可能
是"已经过期"，也可能是"还要冷却十年"。旧实现能用纯粹是因为它只在单进程
内比较。

所以这里一律 `now_local()` 绝对时间，且**绝不与 `CURRENT_TIMESTAMP` 混用**：
SQLite 的 DATETIME 列是字符串按字典序比较，`CURRENT_TIMESTAMP`（UTC、
19 字符、无微秒）与 `now_local()`（本地、26 字符、带微秒）放在一起比，
同秒内会得出反的结论（详见 `models/security_cache.py` 文件头）。

## ② 写异步落库，同时**必须有进程内即时镜像**

两条需求方向相反，缺一不可：

**为什么写要异步**：`log_agent_call` 的血泪教训 —— 交卷流程里
`save_answers()` 先 `flush()` 拿到 SQLite 的 RESERVED 写锁，直到
`finalize_submission()` 才 `commit()`；此时用**另一个 Session** 去写库必然
抢不到锁，等满 `busy_timeout`（5s）再抛 `database is locked`，重试 3 次
→ 一道简答题固定 +16.5s（实测 32 题卷子交卷 16.4s 全耗在这里，前端 30s
超时直接判失败）。而 LLM 的成功/失败回调**正好落在这个窗口里**（判分阶段
调模型）。所以写必须扔给 daemon 线程。

**为什么不能只有 DB**：熔断最初是为了解决「一份 6 道主观题的卷子，6 次
无谓 401 往返、每次 5~6 秒、单次交卷 0.5s 涨到 33s」。这 6 次调用发生在
**同一个请求的同一个循环里**，间隔是毫秒级；而异步写线程真正 commit 的
时刻不确定。若 `get_client()` 只读 DB，第 2 次调用很可能读不到第 1 次刚
写下的熔断 → 6 次 401 原样回来，B1 把 P1 修好的东西又改坏了。

因此：**进程内镜像负责"立刻生效"，DB 负责"跨进程生效"。** 镜像是模块级
的（不是实例属性）—— 这顺带修掉了历史上「模块级 `llm_client` 与
`get_llm()` 单例两个实例各熔各的」的鬼现象，现在全进程只有一份。

## ③ 读失败必须 fail-open（视为无熔断）

熔断表读不到（表还没建、DB 暂时不可用）时**不能**当作"已熔断"：那会让
整个系统的 AI 功能因为一张旁路表而集体降级，用户看到"AI 突然全废"，
而真实原因与 AI 毫无关系。所以读失败一律按"无熔断"处理，让真实调用去跑。
这是**唯一**正确的方向 —— 旁路状态坏了不能反噬主流程。

## ④ auth 熔断不能被 rate_limit 覆盖

多进程下存在这个竞争：A 进程撞 401 → 写 auth；B 进程同时撞 429 → 写
rate_limit，把 auth 覆盖掉 → auth 熔断消失，其它进程继续用无效密钥撞 401。

所以 rate_limit 的 UPSERT 带 `WHERE sys_llm_breaker.kind != 'auth'`：
auth 是**更强**的状态，只由管理员改配置来解除。反过来 auth 写入无条件覆盖
（密钥无效时谈冷却没有意义）。合并本地镜像与 DB 状态时同样按"auth 更强"。

## ⑤ 退避计数必须原子递增

`streak` 决定退避窗口：30s → 60s → 120s → 240s → 300s。若各进程各自
`streak += 1` 再回写，两个进程会来回覆盖成 1、2、1、2 —— 退避永远停在 30s，
指数退避名存实亡（配额打满时每 30s × N 进程重试一次 429）。

所以递增放在**一条 SQL** 里：`streak = streak + 1` 依赖旧值，
SQLite 单写者模型下天然原子。"自增 → 读回 → 算到期时刻 → 写 expire_at"
四步在同一事务内完成（读回必须能看见刚自增的值，故不能拆成两个事务）。

## ⑥ clear 不能连 auth 一起清

`clear_rate_limit` 只在「调用成功」或「冷却自然到期」时触发。若它顺手把
auth 熔断也清了，那么一份无效密钥下只要有一次调用"恰好成功"（例如降级
路径的规则引擎被误判为成功），永久熔断就会被静默解除，退回每次 401 等
5~6 秒的老状态。auth 只允许 `reset_all()` 清 —— 那是管理员改配置的专用入口。
"""
import threading
import time
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from sqlalchemy import text

from app.core.database import SessionLocal
from app.core.logger import get_logger
from app.utils.common import now_local

logger = get_logger("llm_breaker")

# 单行表固定主键。只有一份全局熔断状态，不需要 key-value 结构；
# 固定主键避免"多行谁生效"的歧义（条件 UPSERT 永远命中同一行）。
BREAKER_ID = 1

KIND_AUTH = "auth"              # 鉴权失败（401/403），永久，只能管理员改配置解除
KIND_RATE_LIMIT = "rate_limit"  # 限流/配额（429），限时，到期自动恢复

# 进程内即时镜像（见文件头 ②）。只存"当前进程已知的最强状态"，
# 不存历史。读写都在这个锁内完成 —— 判分是单线程顺序调用，
# 但后台写线程与请求线程会同时碰它。
#
# `cleared_at` 是**清除墓碑**：本进程刚清掉 rate_limit 时记下时刻。
# 没有它就会出现「刚清完又被 DB 里的旧行盖回来」—— 因为删除是异步的，
# 而 `_merge` 看到 DB 有行就返回它。实测表现：`_reset_rate_limit()` 之后
# 立刻 `load()` 仍返回 rate_limit，下一次调用被误判为冷却中而短路
# （成功调用反而不生效，比熔断更糟）。墓碑只压制 `updated_at <= cleared_at`
# 的旧行，别的进程之后新写的熔断照常生效。
_LOCK = threading.Lock()
_local: Dict[str, Any] = {
    "kind": "", "reason": "", "streak": 0, "expire_at": None, "cleared_at": None,
}


def load() -> Optional[Dict[str, Any]]:
    """读取当前**生效**的熔断状态（本地镜像 + DB 合并，auth 优先）。

    Returns:
        None —— 无熔断。**也包括读失败**（见文件头 ③，fail-open）。
        `{"kind", "reason", "streak", "expire_at"}` —— `kind` 为 `auth` 时
        `expire_at` 恒为 None（不看它，语义上也不该看）。

    DB 里 `rate_limit` 已过期时顺手异步清掉那行，避免"库里说在冷却、
    实际已恢复"的观测困惑。
    """
    db_state = _load_db()
    local_state, cleared_at = _load_local()
    return _merge(local_state, db_state, cleared_at)


def auth_disabled() -> bool:
    """是否处于鉴权熔断（永久不可用）状态。"""
    state = load()
    return bool(state and state["kind"] == KIND_AUTH)


def save_auth(reason: str) -> None:
    """记录鉴权熔断（401/403）。

    本地镜像**同步**写（同循环内的后续调用立刻短路），DB **异步**写
    （其它进程稍后生效）。两者都在这里完成，调用方不需要知道区别。
    """
    text_reason = (reason or "")[:1000]
    with _LOCK:
        _local.update(kind=KIND_AUTH, reason=text_reason, streak=0, expire_at=None)
    _spawn(_write_auth, text_reason)


def save_rate_limit(
    reason: str, base_seconds: int, max_seconds: int,
    *, streak: int, expire_at: datetime,
) -> None:
    """记录一次限流冷却（调用方已算好 streak 与到期时刻）。

    `streak` / `expire_at` 由调用方算，是因为本地镜像必须**立刻**知道
    正确的退避窗口，而 DB 侧的原子自增要等异步线程。两者的一致性靠
    「本地算的值与 DB 自增后的值同源」来保证：都从 `load()` 读到的
    streak 出发 +1（见 `agents/llm.py:_start_rate_limit_cooldown`）。
    """
    text_reason = (reason or "")[:1000]
    with _LOCK:
        # auth 优先：已是 auth 时不得被 rate_limit 降级（文件头 ④）。
        if _local["kind"] == KIND_AUTH:
            return
        _local.update(
            kind=KIND_RATE_LIMIT, reason=text_reason,
            streak=int(streak), expire_at=expire_at,
        )
    _spawn(_bump_cooldown, text_reason, base_seconds, max_seconds)


def clear_rate_limit_async() -> None:
    """清除限流冷却（调用成功后 / 冷却自然到期时）。**不动 auth**（文件头 ⑥）。"""
    _clear_local_rate_limit()
    _spawn(_delete, KIND_RATE_LIMIT)


def reset_all() -> None:
    """清空全部熔断状态（管理员改配置时调用）。

    这里**同步**执行：管理员点保存后，界面和后续调用必须立刻反映"已解除"，
    延迟几十毫秒就会让刚保存完就测试连接的运维看到"仍在熔断"，
    从而误以为配置没生效。改配置是低频人工操作，同步写库的代价无所谓。
    """
    with _LOCK:
        _local.update(
            kind="", reason="", streak=0, expire_at=None, cleared_at=None,
        )
    _delete(None)


def _load_db() -> Optional[Dict[str, Any]]:
    """读 DB 行。任何异常都 fail-open（文件头 ③）。"""
    try:
        from app.models import LlmBreakerState

        with SessionLocal() as db:
            row = db.get(LlmBreakerState, BREAKER_ID)
            if row is None or not (row.kind or ""):
                return None
            if row.kind == KIND_RATE_LIMIT:
                expire = row.expire_at
                # expire 为 None 的 rate_limit 是脏数据（不该存在），按已过期处理。
                if expire is None or expire <= now_local():
                    _spawn(_delete, KIND_RATE_LIMIT)
                    return None
            return {
                "kind": row.kind, "reason": row.reason or "",
                "streak": int(row.streak or 0), "expire_at": row.expire_at,
                "updated_at": row.updated_at,
            }
    except Exception as exc:  # noqa: BLE001  旁路状态读失败绝不能反噬主流程
        # debug 而非 warning：表不存在时每次调用都会走到这里，warning 会刷屏。
        logger.debug(f"读取 LLM 熔断状态失败（按无熔断处理）: {exc}")
        return None


def _load_local():
    """读本地镜像。

    Returns:
        `(state_or_None, cleared_at)` —— `cleared_at` 是最近一次本进程清除
        `rate_limit` 的时刻（墓碑），供 `_merge` 压制 DB 里的旧行。
    """
    with _LOCK:
        cleared_at = _local["cleared_at"]
        kind = _local["kind"]
        if not kind:
            return None, cleared_at
        if kind == KIND_RATE_LIMIT:
            expire = _local["expire_at"]
            if expire is None or expire <= now_local():
                _local.update(kind="", reason="", streak=0, expire_at=None)
                return None, cleared_at
        return ({
            "kind": kind, "reason": _local["reason"],
            "streak": int(_local["streak"]), "expire_at": _local["expire_at"],
        }, cleared_at)


def _clear_local_rate_limit() -> None:
    """清本地镜像的 rate_limit，并记下墓碑时刻（见 `_local` 注释）。"""
    with _LOCK:
        _local["cleared_at"] = now_local()
        if _local["kind"] == KIND_RATE_LIMIT:
            _local.update(kind="", reason="", streak=0, expire_at=None)


def _merge(local: Optional[Dict[str, Any]],
           remote: Optional[Dict[str, Any]],
           cleared_at: Optional[datetime] = None) -> Optional[Dict[str, Any]]:
    """合并本地镜像与 DB 状态，按「auth 优先、否则取更晚到期」的规则。

    `cleared_at` 墓碑处理：本进程刚清过 rate_limit，而异步删除尚未落到 DB 时，
    DB 里那行旧 rate_limit 会被 `updated_at <= cleared_at` 认出来并忽略。
    **只压制 rate_limit** —— auth 熔断即使被本进程"清过"也必须照旧生效
    （`clear_rate_limit_async` 本来就不碰 auth，这里是第二道保险）。
    """
    if (remote is not None and remote["kind"] == KIND_RATE_LIMIT
            and cleared_at is not None
            and remote.get("updated_at") is not None
            and remote["updated_at"] <= cleared_at):
        remote = None
    if local is None:
        return remote
    if remote is None:
        return local
    if local["kind"] == KIND_AUTH or remote["kind"] == KIND_AUTH:
        # 两者都可能是 auth，取有 reason 的那个（本地通常更新）。
        return local if local["kind"] == KIND_AUTH else remote
    # 两个都是 rate_limit：退避计数取大者、到期时刻取晚者。
    # 取小者会让"某个进程刚重置过"把别的进程的冷却抹掉 —— 反向不安全。
    streak = max(local["streak"], remote["streak"])
    expire = local["expire_at"]
    if remote["expire_at"] and (expire is None or remote["expire_at"] > expire):
        expire = remote["expire_at"]
    return {
        "kind": KIND_RATE_LIMIT,
        "reason": local["reason"] or remote["reason"],
        "streak": streak,
        "expire_at": expire,
    }


def _spawn(fn, *args) -> None:
    """后台 daemon 线程执行写操作（见文件头 ②）。"""
    try:
        threading.Thread(
            target=fn, args=args, daemon=True, name="llm-breaker-write",
        ).start()
    except Exception as exc:  # noqa: BLE001  起线程失败也不能让调用方炸
        logger.warning(f"LLM 熔断状态写线程启动失败（状态未落库）: {exc}")


def _run_with_retry(fn, *, action: str) -> None:
    """执行一次写操作，仅在**锁冲突**时重试（非锁错误重试无意义）。"""
    last: Optional[Exception] = None
    for attempt in range(3):
        try:
            fn()
            return
        except Exception as exc:  # noqa: BLE001
            last = exc
            msg = str(exc).lower()
            if "locked" not in msg and "busy" not in msg:
                break
            time.sleep(0.1 * (attempt + 1))
    # 落库失败不影响**本进程**正确性（本地镜像仍然生效），但跨进程共享失效 ——
    # 值得一条 warning 让运维知道表有问题。
    logger.warning(f"LLM 熔断状态{action}落库失败: {last}")


def _write_auth(reason: str) -> None:
    """写 auth 熔断。**无条件覆盖**（auth 是最强状态，见文件头 ④）。"""
    def _do() -> None:
        with SessionLocal() as db:
            db.execute(
                text("""
                    INSERT INTO sys_llm_breaker
                        (id, kind, reason, streak, expire_at, updated_at)
                    VALUES (:id, 'auth', :reason, 0, NULL, :now)
                    ON CONFLICT (id) DO UPDATE SET
                        kind = 'auth',
                        reason = :reason,
                        streak = 0,
                        expire_at = NULL,
                        updated_at = :now
                """),
                {"id": BREAKER_ID, "reason": reason, "now": now_local()},
            )
            db.commit()

    _run_with_retry(_do, action="写入鉴权熔断")


def _bump_cooldown(reason: str, base_seconds: int, max_seconds: int) -> None:
    """限流冷却落库：原子自增 streak → 读回 → 算到期时刻 → 写 expire_at。

    四步在**同一个事务**内：读回要能看见自己刚自增的值，
    拆成两个事务就会读到别人写入的旧值（见文件头 ⑤）。
    """
    def _do() -> None:
        now = now_local()
        with SessionLocal() as db:
            # 首次 429（无行）→ 插入 streak=1；已有 rate_limit → streak+1；
            # 已有 auth → 整句被 WHERE 挡住、行保持 auth 不变（文件头 ④）。
            db.execute(
                text("""
                    INSERT INTO sys_llm_breaker
                        (id, kind, reason, streak, expire_at, updated_at)
                    VALUES (:id, 'rate_limit', :reason, 1, NULL, :now)
                    ON CONFLICT (id) DO UPDATE SET
                        streak = CASE
                            WHEN sys_llm_breaker.kind = 'rate_limit'
                                THEN sys_llm_breaker.streak + 1
                            ELSE 1
                        END,
                        kind = 'rate_limit',
                        reason = :reason,
                        updated_at = :now
                    WHERE sys_llm_breaker.kind != 'auth'
                """),
                {"id": BREAKER_ID, "reason": reason, "now": now},
            )
            streak = db.scalar(
                text("SELECT streak FROM sys_llm_breaker WHERE id = :id"),
                {"id": BREAKER_ID},
            )
            # streak 为 0/None 说明上面那句被 WHERE 挡了（当前是 auth 状态），
            # 不该去改 expire_at —— auth 不看它。
            if streak:
                backoff = min(
                    int(max_seconds),
                    int(base_seconds) * (2 ** (int(streak) - 1)),
                )
                db.execute(
                    text("""
                        UPDATE sys_llm_breaker
                        SET expire_at = :expire, updated_at = :now
                        WHERE id = :id AND kind = 'rate_limit'
                    """),
                    {
                        "expire": now + timedelta(seconds=backoff),
                        "now": now, "id": BREAKER_ID,
                    },
                )
                logger.warning(
                    f"LLM 限流/配额不足，冷却退避 {backoff}s"
                    f"（全局连续第 {streak} 次），冷却期内走规则引擎降级"
                )
            db.commit()

    _run_with_retry(_do, action="写入限流冷却")


def _delete(kind: Optional[str]) -> None:
    """删除熔断行。`kind=None` 删整行（含 auth），否则只删指定类型。"""
    def _do() -> None:
        with SessionLocal() as db:
            if kind is None:
                db.execute(
                    text("DELETE FROM sys_llm_breaker WHERE id = :id"),
                    {"id": BREAKER_ID},
                )
            else:
                db.execute(
                    text("DELETE FROM sys_llm_breaker WHERE id = :id AND kind = :kind"),
                    {"id": BREAKER_ID, "kind": kind},
                )
            db.commit()

    _run_with_retry(_do, action="清除熔断状态")


def snapshot() -> Dict[str, Any]:
    """当前状态快照（供 `/agent/status` 等观测接口展示，不参与判定）。

    加这个函数是为了让运维能直接看到"到底熔断没有、退避第几次"，
    否则只能靠日志猜测 —— 这正是当初把状态藏在实例属性里时的最大不便。
    """
    state = load()
    if state is None:
        return {"breaker": "none", "reason": "", "streak": 0, "cooldown_remaining": 0}
    remaining = 0
    if state["kind"] == KIND_RATE_LIMIT and state["expire_at"]:
        remaining = max(0, int((state["expire_at"] - now_local()).total_seconds() + 0.999))
    return {
        "breaker": state["kind"],
        "reason": state["reason"],
        "streak": state["streak"],
        "cooldown_remaining": remaining,
    }
