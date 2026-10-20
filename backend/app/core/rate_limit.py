# -*- coding: utf-8 -*-
"""AI 接口限流（DB 共享存储，支持多实例）。

实现：`sys_agent_rate` 表按 (user_id, window_minute) 做 UPSERT 原子累加。
- 相比进程内 dict：多副本部署时计数共享，不会出现「每个实例各 12 次」
- 相比 Redis：单机 SQLite 部署无需额外中间件，写入量极小（每次调用 1 行 UPSERT）

失败降级：DB 异常时**放行**（fail-open）。限流是防刷措施，
不应因存储抖动导致正常用户无法使用 AI 功能。
"""
import logging
import time

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exception import BusinessException

logger = logging.getLogger(__name__)


def check_agent_rate(db: Session, user_id: int, cost: int = 1) -> None:
    """校验并累加调用次数；超限抛 BusinessException。"""
    limit = max(1, int(settings.AGENT_RATE_LIMIT_PER_MIN or 12))
    minute = int(time.time() // 60)
    try:
        # SQLite / PostgreSQL 通用 UPSERT
        db.execute(
            text("""
                INSERT INTO sys_agent_rate (user_id, window_minute, count, updated_at)
                VALUES (:uid, :win, :cost, CURRENT_TIMESTAMP)
                ON CONFLICT (user_id, window_minute)
                DO UPDATE SET count = count + :cost, updated_at = CURRENT_TIMESTAMP
            """),
            {"uid": user_id, "win": minute, "cost": cost},
        )
        used = db.execute(
            text("SELECT count FROM sys_agent_rate WHERE user_id=:uid AND window_minute=:win"),
            {"uid": user_id, "win": minute},
        ).scalar() or 0
        db.commit()
        # 顺带清理过期窗口（每分钟最多清一次，代价可忽略）
        if minute % 5 == 0:
            db.execute(text("DELETE FROM sys_agent_rate WHERE window_minute < :old"),
                       {"old": minute - 10})
            db.commit()
    except Exception as exc:  # noqa: BLE001
        # fail-open：限流存储异常不应阻断业务
        logger.warning("限流计数失败（放行）：%s", exc)
        try:
            db.rollback()
        except Exception:  # noqa: BLE001
            pass
        return

    if used > limit:
        raise BusinessException(
            f"AI 调用过于频繁（每分钟上限 {limit} 次），请稍后再试")
