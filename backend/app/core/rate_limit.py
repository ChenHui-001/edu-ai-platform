# -*- coding: utf-8 -*-
"""AI 接口轻量限流（进程内固定窗口）。

部署形态是单机 SQLite，不引入 Redis：按 user_id 维护每分钟计数即可。
多实例部署时需替换为共享存储（Redis / DB），否则限流按实例独立生效。
"""
import threading
import time
from typing import Dict, Tuple

from app.core.config import settings
from app.core.exception import BusinessException

_lock = threading.Lock()
# {user_id: (window_start_epoch_minute, count)}
_buckets: Dict[int, Tuple[int, int]] = {}


def check_agent_rate(user_id: int, cost: int = 1) -> None:
    """校验并累加调用次数；超限抛 BusinessException。

    只在会触发 LLM 的接口上调用（出题/组卷/批改/规划/答疑/整理/对话），
    纯查询接口不限流。
    """
    limit = max(1, int(settings.AGENT_RATE_LIMIT_PER_MIN or 12))
    minute = int(time.time() // 60)
    with _lock:
        start, count = _buckets.get(user_id, (minute, 0))
        if start != minute:
            start, count = minute, 0
        count += cost
        _buckets[user_id] = (start, count)
        # 避免字典无限增长：条目超过 5000 时清理过期窗口
        if len(_buckets) > 5000:
            for uid in [u for u, (st, _) in _buckets.items() if st != minute]:
                _buckets.pop(uid, None)
    if count > limit:
        raise BusinessException(
            f"AI 调用过于频繁（每分钟上限 {limit} 次），请稍后再试")
