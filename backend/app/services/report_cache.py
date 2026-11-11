"""报表聚合的短 TTL 进程内缓存（P-07）。

## 为什么需要

教师端几个报表（班级概览 / 班级薄弱知识点 / 教学效果）每次刷新都要把整班
提交与掌握度聚合一遍。当前部署是 **SQLite 单写者 + uvicorn --workers 1**：
这些只读聚合与交卷/批改共用同一条连接，报表页开着、老师每隔几秒点一次刷新，
就会持续抢占写者窗口，表现为「批改页卡一下」。

缓存 15 秒能把「连点 10 次」压成 1 次真实查询。

## 为什么不引 Redis

- 单容器单 worker，进程内缓存的命中率就等于全局命中率，不存在多副本不一致；
- 报表是只读视图，15 秒的陈旧窗口对「这节课讲哪几个知识点」没有决策影响；
- 引 Redis 会直接破坏「单镜像 + SQLite」的部署承诺（这是项目硬约束）。

多 worker 化那天，本模块的 `clear()` 需要在进程间广播 —— 见
`docs/` 里关于多 worker 前提未闭合的记录（P1-15）。

## 两条必须守住的正确性约束

1. **key 必须含 user_id**：报表受 `DataScope` 约束，跨用户共享 key 会把
   A 老师能看的班级数据泄给 B。这类缓存泄露在评审里极难看出来，所以
   `key()` 要求第一个参数就是 `user_id`，从签名上挡住误用。
2. **必须留 `refresh=1` 的后门**：教师刚批完 30 份作业点刷新，若还看到
   15 秒前的旧数字，会以为批改没生效。「缓存让用户怀疑数据」比性能更贵。

## 命中率可观测

`stats()` 返回 hits / misses，测试与运维都能验证缓存真的生效了
（否则很容易写出一个永远不命中的缓存，看起来性能优化了、实际白干）。
"""
import copy
import threading
import time
from typing import Any, Callable, Dict, Optional, Tuple

# 15 秒：短到「批改完刷新一下就能看到」，长到能挡住连点刷新。
# 不要调到 60s 以上 —— 报表数字对不上时，教师的第一反应是「系统坏了」。
CACHE_TTL_SECONDS = 15.0

# 容量上限：key 里带 user_id，用户越多条目越多，不设上限就是内存泄漏。
# 256 条 × 每条约几 KB，量级完全可接受。
MAX_ENTRIES = 256

_lock = threading.Lock()
_store: Dict[str, Tuple[float, Any]] = {}
_hits = 0
_misses = 0


def key(kind: str, user_id: int, *parts: Any) -> str:
    """构造缓存键。

    `kind` 是端点标识，`user_id` 强制第二参数（见模块 docstring 第 1 条），
    其余按端点入参依次拼接 —— **所有影响结果的参数都必须传进来**，
    漏一个就会串数据（例如漏了 subject_id，换学科仍然返回上一个学科的榜单）。
    """
    return "|".join([kind, str(user_id)] + [str(p) for p in parts])


def cached(k: str, producer: Callable[[], Any],
           ttl: float = CACHE_TTL_SECONDS) -> Any:
    """命中则返回缓存副本，否则调用 `producer()` 并写缓存。

    返回**深拷贝**：报表结果是 dict/list 嵌套结构，直接返回同一对象时，
    下游任何一处就地修改（比如 `items.sort()`）都会污染缓存，
    表现为「第一次看是对的，第二次顺序变了」这种极难复现的 bug。
    """
    global _hits, _misses
    now = time.monotonic()
    with _lock:
        row = _store.get(k)
        if row is not None and now < row[0]:
            _hits += 1
            return copy.deepcopy(row[1])
        _misses += 1

    value = producer()
    put(k, value, ttl)
    return value


def put(k: str, value: Any, ttl: float = CACHE_TTL_SECONDS) -> None:
    """写入缓存（`refresh=1` 重算后也走这里，让后续请求复用新值）。"""
    with _lock:
        if len(_store) >= MAX_ENTRIES:
            _evict_locked()
        _store[k] = (time.monotonic() + ttl, copy.deepcopy(value))


def _evict_locked() -> None:
    """淘汰：先清过期，仍满就丢最早插入的一半。

    不用 LRU 是刻意的：报表请求的模式是「同一批 key 反复命中」，
    FIFO 足够，而维护访问顺序要在每次 get 时写操作，反而增加锁竞争。
    """
    now = time.monotonic()
    expired = [k for k, (expire_at, _) in _store.items() if expire_at <= now]
    for k in expired:
        _store.pop(k, None)
    if len(_store) >= MAX_ENTRIES:
        for k in list(_store)[: max(1, MAX_ENTRIES // 2)]:
            _store.pop(k, None)


def clear() -> int:
    """清空缓存条目，返回清掉的条数。

    数据变更（批改、交卷、改掌握度）后如需立即反映，可调用它；
    但业务代码里**不要**到处埋 clear() —— 那等于放弃缓存，
    正确做法是让用户用 `refresh=1` 主动刷新。

    注意：**不清 hits/misses**。命中率是累计观测值，跟着数据一起被清零会让
    「本进程到底有没有生效」变得不可判断。要一起归零请用 `reset_stats()`。
    """
    with _lock:
        n = len(_store)
        _store.clear()
        return n


def reset_stats() -> None:
    """清空条目 + 归零命中计数（仅测试/排障用，业务代码不要调）。"""
    global _hits, _misses
    with _lock:
        _store.clear()
        _hits = 0
        _misses = 0


def stats() -> Dict[str, Any]:
    with _lock:
        total = _hits + _misses
        return {
            "entries": len(_store),
            "hits": _hits,
            "misses": _misses,
            "hit_rate": round(_hits / total * 100, 2) if total else 0.0,
            "ttl_seconds": CACHE_TTL_SECONDS,
            "max_entries": MAX_ENTRIES,
        }


def _lookup(k: str) -> Optional[Any]:  # pragma: no cover - 仅调试用
    with _lock:
        row = _store.get(k)
        return row[1] if row else None
