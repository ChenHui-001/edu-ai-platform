# -*- coding: utf-8 -*-
"""优化项 1：限流改 DB 共享存储 + 新增 Agent 异步任务表。

设计要点：
- 限流表 `sys_agent_rate`：主键 (user_id, window_minute)，UPSERT 原子累加，
  多实例部署时按 DB 共享计数（进程内 dict 在 k8s 多副本下会各自限额）。
- 任务表 `sys_agent_job`：长任务（出题/组卷）异步执行，客户端轮询结果，
  避免 HTTP 长连接挂 40-60s。
"""
import io

# ============================================================
# 1) 模型
# ============================================================
ops = "backend/app/models/ops.py"
s = io.open(ops, encoding="utf-8").read()

MODELS = '''

class AgentRate(Base):
    """AI 接口限流计数（按用户 + 分钟窗口，DB 共享以支持多实例）。

    选 DB 而非 Redis：本系统是单机 SQLite 部署形态，引入 Redis 成本高于收益；
    若未来切 PostgreSQL/多写入场景，此表同样适用（UPSERT 语义一致）。
    """

    __tablename__ = "sys_agent_rate"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    window_minute: Mapped[int] = mapped_column(Integer, primary_key=True,
                                               comment="epoch 分钟数，作窗口键")
    count: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now_local, onupdate=now_local)


class AgentJob(Base):
    """AI 长任务（异步执行 + 轮询）。

    出题/组卷在真实 LLM 下耗时 20-60s，同步 HTTP 容易被网关/代理截断；
    改为提交即返回 job_id，后台线程执行，前端轮询进度与结果。
    """

    __tablename__ = "sys_agent_job"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    agent: Mapped[str] = mapped_column(String(32), index=True, comment="question/paper")
    status: Mapped[str] = mapped_column(String(16), default="pending", index=True,
                                        comment="pending/running/success/failed")
    params: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="请求参数 JSON")
    result: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="结果 JSON")
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_local, index=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
'''
assert "class AgentRate" not in s
s = s.rstrip() + MODELS
io.open(ops, "w", encoding="utf-8", newline="\n").write(s)

# 导出
init = "backend/app/models/__init__.py"
s2 = io.open(init, encoding="utf-8").read()
if "AgentJob" not in s2:
    s2 = s2.replace("    Notification, OperationLog, ScheduledJob,",
                    "    AgentJob, AgentRate, Notification, OperationLog, ScheduledJob,")
io.open(init, "w", encoding="utf-8", newline="\n").write(s2)
print("[1] 模型 AgentRate / AgentJob 已添加")

# ============================================================
# 2) 限流实现改 DB
# ============================================================
rl = '''# -*- coding: utf-8 -*-
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
'''
io.open("backend/app/core/rate_limit.py", "w", encoding="utf-8", newline="\n").write(rl)
print("[2] rate_limit.py 改为 DB 实现")

# ============================================================
# 3) 调用点签名变更：check_agent_rate(user.id) -> check_agent_rate(db, user.id)
# ============================================================
f = "backend/app/api/v1/agent.py"
s3 = io.open(f, encoding="utf-8").read()
s3 = s3.replace("check_agent_rate(user.id)", "check_agent_rate(db, user.id)")
io.open(f, "w", encoding="utf-8", newline="\n").write(s3)
print(f"[3] 调用点已更新：{s3.count('check_agent_rate(db, user.id)')} 处")
