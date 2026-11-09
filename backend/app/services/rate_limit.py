"""跨进程共享的滥用频率限流。

原先找回密码与匿名上传各有一份进程内 dict + threading.Lock：
`uvicorn --workers N` 下每个进程各算各的，实际额度是配置值的 N 倍。

这里用 `sys_rate_limit` 单行固定窗口计数，读改写走同一份 SQLite：
  * 窗口过期 → 重置计数；
  * 未超限 → SQL 原子自增（不依赖「先读后写」，多 worker 不丢计数）；
  * 并发窗口重置撞唯一键 → 保守拒绝这一次请求（限流场景宁可少放一次）。

只用于**频率**控制；验证码正确性、令牌吊销等状态仍由各自专用表管理。

## 三处必须守住的边界（2026-11-09 第三轮复审 P1-B）

1. **单语句判限**：`UPDATE ... WHERE hits < limit` 一条语句同时完成
   「窗口校验 + 未超限才自增」。旧实现先 `db.get()` 读、再 update，两个
   并发请求会读到同一个陈旧 hits，实际可放行 limit+N-1 次。
2. **拒绝态进程内缓存**：攻击者持续打被限流端点时，旧实现每次请求仍然
   要 UPDATE + commit —— 越是被攻击写压力越大。命中"已超限"缓存后直接
   拒绝、不再碰库；缓存按进程各自维护，最坏情况每个 worker 各多写一次。
3. **键不能是明文、也不能无界**：三个调用点都在匿名端点上，键由攻击者
   控制（任意邮箱 / 任意手机号 / 任意来源 IP）。因此：
   * `key_digest()` 对原始值做「加盐 SHA-256」再入库 —— 库里不留明文邮箱
     与手机号（`sys_rate_limit` 曾是事实上的无界 PII 表）；
   * 每次写入按概率顺带 `purge_expired_and_cap()`：先删过期行，行数超过
     `KEY_SOFT_CAP` 再按 `expire_at` 淘汰最旧的 20% —— 键空间有上界。

## 关于「每个正常请求仍是一次 UPDATE + commit」

这是**有意保留**的最小代价，不是漏改：固定窗口计数必须落库，否则多 worker
下退回进程内计数（P2-1 修的就是这个）。真正的写放大发生在「被拒绝的请求」，
已由拒绝态缓存消除；SQLite 在 WAL + `synchronous=NORMAL` 下这次 commit 只
追加 WAL 帧、不 fsync，单次成本在几十微秒量级，而三个调用点都是低频端点
（找回密码、验证码校验、注册材料上传）。若将来出现高频调用点，再考虑
「进程内聚合 + 定时批量落库」，不要为此提前牺牲跨进程准确性。
"""
import hashlib
import random
import threading
import time
from datetime import timedelta

from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import RateLimit
from app.utils.common import now_local

# key → 拒绝截止时间（epoch 秒）。只存"已超限"这一个状态，不存计数，
# 因此不存在与库内计数不一致的问题：缓存过期后回到数据库判断。
_DENY_CACHE = {}
_DENY_LOCK = threading.Lock()
_DENY_TTL_MAX = 30.0
_DENY_CACHE_MAX = 5000

# 键空间上界（行数）。20k 行 × 约 150 字节 ≈ 3MB，单文件 SQLite 完全可以承受；
# 超过后淘汰最旧的一批，攻击者无法把表撑爆。
KEY_SOFT_CAP = 20000
# 维护动作（清过期 + 淘汰）的概率：命中率 2%，即平均每 50 次限流写一次。
_MAINTENANCE_RATE = 0.02


def _salt() -> str:
    """哈希盐取自 SECRET_KEY：同一部署内多 worker 一致，换部署即失效。"""
    return str(getattr(settings, "SECRET_KEY", "") or "edu-ai-platform-rate-limit")


def key_digest(prefix: str, raw: str) -> str:
    """把攻击者可控的原始键（邮箱/手机号/IP）转成定长、不可逆的键。

    为什么要哈希：`sys_rate_limit.key` 曾被写入用户输入的明文邮箱，等于
    在库里长期留存一份「任意人可写入」的 PII 清单（无界、无清理）。
    邮箱熵低，裸 SHA-256 可被字典反查，所以加部署级盐。
    """
    material = f"{_salt()}|{prefix}|{(raw or '').strip().lower()}".encode("utf-8")
    return f"{prefix}:{hashlib.sha256(material).hexdigest()[:32]}"


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


def purge_expired_and_cap(db: Session) -> int:
    """删过期行；行数超过软上限时按 `expire_at` 淘汰最旧的一批。

    返回删除行数。由 `core/security.py` 的 `_PURGE_FUNCS` 与
    `check_and_hit()` 的按概率维护共同调用。
    """
    removed = db.execute(
        delete(RateLimit).where(RateLimit.expire_at < now_local())
    ).rowcount or 0
    total = db.scalar(select(func.count()).select_from(RateLimit)) or 0
    if total > KEY_SOFT_CAP:
        keep = int(KEY_SOFT_CAP * 0.8)
        doomed = (
            select(RateLimit.key)
            .order_by(RateLimit.expire_at.asc())
            .limit(max(1, total - keep))
        )
        removed += db.execute(
            delete(RateLimit).where(RateLimit.key.in_(doomed))
        ).rowcount or 0
    db.commit()
    return removed


def _maybe_maintain(db: Session) -> None:
    """按概率顺带清理：失败绝不能影响主流程（限流是防刷，不是正确性依赖）。"""
    if random.random() >= _MAINTENANCE_RATE:
        return
    try:
        purge_expired_and_cap(db)
    except Exception:  # noqa: BLE001 清理失败忽略
        try:
            db.rollback()
        except Exception:  # noqa: BLE001
            pass


def check_and_hit(db: Session, key: str, limit: int,
                  window_seconds: int = 600) -> bool:
    """在 key 的固定窗口内登记一次请求；未超限返回 True。

    `key` 必须是已归一化的键：业务侧请用 `key_digest()` 生成，不要直接把
    邮箱/手机号拼进键里（否则明文会落库）。
    """
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
        _maybe_maintain(db)
        return True
    db.commit()

    row = db.get(RateLimit, key)
    if row is None or float(row.window_start) < cutoff:
        # 首次访问或窗口已过期：重置为新窗口的第一次
        try:
            db.execute(delete(RateLimit).where(RateLimit.key == key))
            db.add(RateLimit(key=key, window_start=now, hits=1, expire_at=expire_at))
            db.commit()
            _maybe_maintain(db)
            return True
        except IntegrityError:
            # 另一个进程刚建了同一行：保守拒绝这一次
            db.rollback()
            _mark_denied(key, window_seconds)
            return False

    _mark_denied(key, window_seconds)
    return False
