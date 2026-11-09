"""跨进程共享的滥用频率限流（P2-7）。

原先找回密码与匿名上传各有一份进程内 dict + threading.Lock：
`uvicorn --workers N` 下每个进程各算各的，实际额度是配置值的 N 倍。

这里用 `sys_rate_limit` 单行固定窗口计数，读改写走同一份 SQLite：
  * 窗口过期 → 重置计数；
  * 未超限 → SQL 原子自增（不依赖「先读后写」，多 worker 不丢计数）；
  * 并发窗口重置撞唯一键 → 保守拒绝这一次请求（限流场景宁可少放一次）。

只用于**频率**控制；验证码正确性、令牌吊销等状态仍由各自专用表管理。

P2-1 的两个修正（限流不能自己变成新的写放大源）：
  1. **单语句判限**：`UPDATE ... WHERE hits < limit` 一条语句同时完成
     「窗口校验 + 未超限才自增」。旧实现先 `db.get()` 读、再 update，两个
     并发请求会读到同一个陈旧 hits，实际可放行 limit+N-1 次。
  2. **拒绝态进程内缓存**：攻击者持续打被限流端点时，旧实现每次请求仍然
     要 UPDATE + commit —— 越是被攻击写压力越大。命中"已超限"缓存后直接
     拒绝、不再碰库；缓存按进程各自维护，最坏情况每个 worker 各多写一次。
"""
import threading
import time
from datetime import timedelta

from sqlalchemy import delete, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import RateLimit
from app.utils.common import now_local

# key → 拒绝截止时间（epoch 秒）。只存"已超限"这一个状态，不存计数，
# 因此不存在与库内计数不一致的问题：缓存过期后回到数据库判断。
_DENY_CACHE = {}
_DENY_LOCK = threading.Lock()
_DENY_TTL_MAX = 30.0
_DENY_CACHE_MAX = 5000


def _deny_deadline(key: str) -> float:
    with _DENY_LOCK:
        return float(_DENY_CACHE.get(key, 0.0))


def _mark_denied(key: str, window_seconds: int) -> None:
    with _DENY_LOCK:
        _DENY_CACHE[key] = time.time() + min(float(window_seconds), _DENY_TTL_MAX)
        if len(_DENY_CACHE) > _DENY_CACHE_MAX:
            now = time.time()
            for stale in [k for k, v in _DENY_CACHE.items() if v <= now]:
                _DENY_CACHE.pop(stale, None)


def reset_cache(key: str = "") -> None:
    """清空拒绝缓存（测试用；key 为空清除全部）。"""
    with _DENY_LOCK:
        if key:
            _DENY_CACHE.pop(key, None)
        else:
            _DENY_CACHE.clear()


def check_and_hit(db: Session, key: str, limit: int,
                  window_seconds: int = 600) -> bool:
    """在 key 的固定窗口内登记一次请求；未超限返回 True。"""
    now = time.time()
    if _deny_deadline(key) > now:
        return False

    expire_at = now_local() + timedelta(seconds=window_seconds + 60)
    cutoff = now - window_seconds
    hit = db.execute(
        update(RateLimit)
        .where(RateLimit.key == key,
               RateLimit.window_start >= cutoff,
               RateLimit.hits < int(limit))
        .values(hits=RateLimit.hits + 1, expire_at=expire_at)
    )
    if hit.rowcount:
        db.commit()
        return True
    db.commit()

    row = db.get(RateLimit, key)
    if row is None or float(row.window_start) < cutoff:
        # 首次访问或窗口已过期：重置为新窗口的第一次
        try:
            db.execute(delete(RateLimit).where(RateLimit.key == key))
            db.add(RateLimit(key=key, window_start=now, hits=1, expire_at=expire_at))
            db.commit()
            return True
        except IntegrityError:
            # 另一个进程刚建了同一行：保守拒绝这一次
            db.rollback()
            _mark_denied(key, window_seconds)
            return False

    _mark_denied(key, window_seconds)
    return False
