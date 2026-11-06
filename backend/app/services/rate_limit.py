"""跨进程共享的滥用频率限流（P2-7）。

原先找回密码与匿名上传各有一份进程内 dict + threading.Lock：
`uvicorn --workers N` 下每个进程各算各的，实际额度是配置值的 N 倍。

这里用 `sys_rate_limit` 单行固定窗口计数，读改写走同一份 SQLite：
  * 窗口过期 → 重置计数；
  * 未超限 → SQL 原子自增（不依赖「先读后写」，多 worker 不丢计数）；
  * 并发窗口重置撞唯一键 → 保守拒绝这一次请求（限流场景宁可少放一次）。

只用于**频率**控制；验证码正确性、令牌吊销等状态仍由各自专用表管理。
"""
import time
from datetime import timedelta

from sqlalchemy import delete, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import RateLimit
from app.utils.common import now_local


def check_and_hit(db: Session, key: str, limit: int,
                  window_seconds: int = 600) -> bool:
    """在 key 的固定窗口内登记一次请求；未超限返回 True。"""
    now = time.time()
    expire_at = now_local() + timedelta(seconds=window_seconds + 60)
    row = db.get(RateLimit, key)

    if row is None or now - float(row.window_start) >= window_seconds:
        try:
            db.execute(delete(RateLimit).where(RateLimit.key == key))
            db.add(RateLimit(key=key, window_start=now, hits=1,
                             expire_at=expire_at))
            db.commit()
            return True
        except IntegrityError:
            db.rollback()
            return False

    if int(row.hits) >= int(limit):
        return False
    db.execute(update(RateLimit).where(RateLimit.key == key).values(
        hits=RateLimit.hits + 1, expire_at=expire_at))
    db.commit()
    return True
