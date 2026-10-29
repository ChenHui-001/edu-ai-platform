"""运维模型：登录日志、操作日志、错误日志、定时任务、附件、AI 调用日志。"""
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.utils.common import now_local


class LoginLog(Base):
    """登录日志。"""

    __tablename__ = "sys_login_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    username: Mapped[str] = mapped_column(String(64), index=True)
    login_type: Mapped[str] = mapped_column(String(16), default="password", comment="password/sms")
    status: Mapped[str] = mapped_column(String(16), default="success", index=True)
    message: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    ip: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    location: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    device: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, comment="浏览器/设备信息")
    os: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    is_abnormal: Mapped[bool] = mapped_column(Boolean, default=False, index=True, comment="异地登录等异常")
    login_at: Mapped[datetime] = mapped_column(DateTime, default=now_local, index=True)


class OperationLog(Base):
    """操作日志：全链路审计追溯。"""

    __tablename__ = "sys_operation_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    module: Mapped[str] = mapped_column(String(64), index=True)
    action: Mapped[str] = mapped_column(String(128), index=True)
    method: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    path: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    ip: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    params: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="请求参数 JSON")
    result: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="success")
    error_msg: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_local, index=True)


class ErrorLog(Base):
    """错误日志。"""

    __tablename__ = "sys_error_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    level: Mapped[str] = mapped_column(String(16), default="ERROR", index=True)
    module: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    path: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    message: Mapped[str] = mapped_column(Text)
    traceback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_local, index=True)


class ScheduledJob(Base):
    """定时任务配置（APScheduler）。"""

    __tablename__ = "sys_scheduled_job"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    func_path: Mapped[str] = mapped_column(String(255), comment="执行逻辑标识，如 module.func")
    cron_expression: Mapped[str] = mapped_column(String(64), comment="Cron 表达式")
    is_builtin: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    retry_times: Mapped[int] = mapped_column(Integer, default=2)
    last_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_status: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    run_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_local)


class JobExecutionLog(Base):
    """定时任务执行记录。"""

    __tablename__ = "sys_job_execution_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("sys_scheduled_job.id", ondelete="CASCADE"), index=True)
    job_name: Mapped[str] = mapped_column(String(128), index=True)
    status: Mapped[str] = mapped_column(String(16), default="running", index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=now_local, index=True)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    trigger_type: Mapped[str] = mapped_column(String(16), default="auto", comment="auto/manual")


class JobLock(Base):
    """定时任务执行锁：保证同一任务同一时刻只有一个进程在跑。

    ## 为什么需要它

    `uvicorn --workers N` 下每个 worker 都会 `sync_all_jobs()` 并各自跑一份
    APScheduler —— N 个进程的 cron 在同一分钟同时触发同一个任务。所有 handler
    都是「扫描 + 批量写」（`publish_scheduled_tasks` 会给几百个学生插通知、
    `clean_old_logs` 会删几十万行），并发执行不是「多跑一遍」而是**写放大 N 倍**：
    实测 2 进程跑 `publish_scheduled_tasks` 得到 `notification=900`（应为 450）、
    `job_execution_log=2`。

    ## 表结构上的三个要点（写错不会报错，只会静默失效）

    1. **`expire_at` 必须由 Python 传 `now_local()`，绝不用 `CURRENT_TIMESTAMP`。**
       SQLite 的 DATETIME 列是字符串、按字典序比较，而
       `CURRENT_TIMESTAMP` 给的是 UTC 且不带微秒（19 字符），
       `now_local()` 是本地时间带微秒（26 字符）。实测同一瞬间：

           CURRENT_TIMESTAMP = '2026-10-29 03:15:20'
           now_local()       = '2026-10-29 11:15:20.993660'
           SQL 'a' < 'b'     -> True

       即用 `CURRENT_TIMESTAMP` 写的租约**写入瞬间就过期** → 永远抢得到、
       永不互斥、日志里毫无异常。详见 `models/security_cache.py` 顶部同类说明。

    2. **`job_id` 是主键**，一个任务一把锁。用 UPSERT + `WHERE expire_at < now`
       做条件抢占，这一条语句在 SQLite 单写者模型下天然原子（实测 8 进程
       屏障同时抢，5/5 轮均恰好 1 个成功、0 错误，无需 `BEGIN IMMEDIATE`）。

    3. **`owner` 必须按 `hostname:pid:uuid` 记录**，释放时用
       `WHERE owner = :me` 限定。无条件 DELETE 会让「崩溃遗留的未过期锁」
       被跳过者删掉，下一分钟两个进程又同时跑 —— 互斥退化成靠运气。
       带 uuid 是为了彻底绕开 pid 复用：容器里 pid 高度重复，只靠
       `hostname:pid` 会把「重启后的新进程」误认成「崩溃前的旧进程」，
       于是它能删掉别人的锁。

    ## 为什么不担心崩溃留下死锁

    租约 1800s（`JOB_LOCK_LEASE_SECONDS`），崩溃后最长 30 分钟自动失效。
    能容忍这个延迟的理由：**所有 handler 都是「补齐式扫描」**
    （`publish_at <= now`、`created_at < cutoff`、`end_at < deadline`），
    漏掉一个窗口不丢数据、只是延后。这条是租约期可以给到 1800s 的前提，
    如果将来有 handler 改成「只在某个精确时刻做一次、错过就永久丢失」，
    必须同步下调租约期。实测最慢的 `clean_old_logs`（3×30 万行）耗时 2592ms，
    1800s 有 694 倍余量。

    ## 行会堆积吗

    不会。`release_job_lock` 直接 DELETE 自己那行；崩溃遗留的行在
    下一次抢占时被同一句 UPSERT 覆盖（`WHERE expire_at < now` 命中）。
    所以表的最大行数 = 任务数，与运行时长无关。
    """

    __tablename__ = "sys_job_lock"

    job_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    owner: Mapped[str] = mapped_column(String(80), comment="hostname:pid:uuid[:8]")
    acquired_at: Mapped[datetime] = mapped_column(DateTime, default=now_local)
    expire_at: Mapped[datetime] = mapped_column(DateTime, index=True)


class LlmBreakerState(Base):
    """LLM 熔断/冷却状态（跨进程共享，B1）。

    ## 为什么必须落库

    修复前这两份状态是 `LLMClient` 的实例属性：

        self._disabled_reason = ""      # 鉴权熔断（401/403，永久）
        self._cooldown_until = 0.0      # 限流冷却（429，指数退避）
        self._rate_limit_streak = 0

    `--workers 1` 时进程内状态就够了。一旦扩到 N 个 worker，问题变成：

    - **熔断各熔各的**：worker A 撞到 401 熔断了，B/C 完全不知道，各自还要
      再用无效密钥撞一次 —— 每次都是一轮 5~6 秒的等 401。N 个 worker 就是
      N 倍无谓延迟，而"密钥无效"这个事实本该全局共享。
    - **冷却各退各的**：A 撞 429 进入 300s 冷却，B 仍在真实调用。配额已经被
      打满的情况下，B 的调用只会把 429 再刷一遍，退避窗口形同虚设。

    ## 为什么不用 sys_config 存

    熔断状态是**运行期高频写**（每次失败都写），而 `sys_config` 是配置表：
    混进去会污染 `updated_at`（配置页按它排序/缓存），且配置表的语义是
    "管理员设定的值"，运行态数据不该占用它的 key 空间。

    ## 单行表（id 恒为 1）

    只有一份全局熔断状态，不需要 key-value 结构。固定主键避免"多行谁生效"
    的歧义 —— 条件 UPSERT 永远命中同一行。

    ## `kind` 为什么不做成枚举

    当前只有 `auth`（永久）与 `rate_limit`（限时）两种，用字符串列足够。
    真正的区别体现在 `expire_at` 是否为空：`auth` 永不为空但**语义上不看它**
    （必须等管理员改配置），`rate_limit` 靠它到期自动恢复。把这条区别写在
    列注释里而不是靠枚举约束，是因为将来可能出现"半永久"类型（如账户欠费），
    那时只需读 `expire_at`，不用改表结构。
    """

    __tablename__ = "sys_llm_breaker"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False,
                                    comment="恒为 1，单行表")
    kind: Mapped[str] = mapped_column(String(16), default="",
                                      comment="空=auth 永久熔断 / rate_limit 限时冷却")
    reason: Mapped[str] = mapped_column(Text, default="",
                                        comment="面向用户的降级原因（含剩余秒数）")
    streak: Mapped[int] = mapped_column(Integer, default=0,
                                        comment="连续限流次数，用于指数退避")
    # ★ 必须是绝对时间（now_local()），不能用 time.monotonic()。
    # monotonic 是**进程内**单调时钟，各进程起点不同，跨进程比较无意义
    # （实测同机两个 Python 进程的 monotonic 差异可达数十万秒）。
    # 旧实现存 monotonic 是因为只在单进程内比较 —— 外置时这是必须先改掉的前提。
    expire_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True,
                                                          comment="冷却到期时刻；空表示永久熔断")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now_local,
                                                 onupdate=now_local)


class Attachment(Base):
    """附件元数据。"""

    __tablename__ = "sys_attachment"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    filename: Mapped[str] = mapped_column(String(255), comment="原始文件名")
    stored_name: Mapped[str] = mapped_column(String(255), index=True, comment="加密存储名，防路径遍历")
    file_path: Mapped[str] = mapped_column(String(512))
    file_size: Mapped[int] = mapped_column(Integer, default=0)
    file_type: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True, comment="business 类型")
    biz_type: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, index=True, comment="业务类型")
    biz_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    uploader_id: Mapped[Optional[int]] = mapped_column(ForeignKey("sys_user.id", ondelete="SET NULL"), nullable=True)
    download_count: Mapped[int] = mapped_column(Integer, default=0)
    is_temp: Mapped[bool] = mapped_column(Boolean, default=True, index=True, comment="临时附件定时清理")
    visible_to_student: Mapped[bool] = mapped_column(
        Boolean, default=True, index=True, comment="关联知识点时是否允许学生查看/下载")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_local, index=True)


class AgentCallLog(Base):
    """AI Agent 调用日志。"""

    __tablename__ = "sys_agent_call_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    agent_name: Mapped[str] = mapped_column(String(64), index=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    input_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    output_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="success", index=True)
    error_msg: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_fallback: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否走了规则引擎降级")
    biz_type: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, index=True)
    biz_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_local, index=True)


class Notification(Base):
    """站内通知。"""

    __tablename__ = "sys_notification"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("sys_user.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(128))
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    type: Mapped[str] = mapped_column(String(32), default="system", comment="audit/exam/review/system")
    biz_type: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    biz_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_local, index=True)

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
    agent: Mapped[str] = mapped_column(String(32), index=True, comment="question/paper/lesson")
    status: Mapped[str] = mapped_column(String(16), default="pending", index=True,
                                        comment="pending/running/success/failed")
    # 进度提示：教案生成要跑多个环节（解析条件→拟定目标→展开过程→校验补全），
    # 前端需要在等待期给出「正在做什么」，否则 30s 空白页等同于卡死。
    progress: Mapped[int] = mapped_column(Integer, default=0, comment="进度百分比 0-100")
    stage: Mapped[Optional[str]] = mapped_column(String(64), nullable=True,
                                                 comment="当前环节名称（面向用户展示）")
    params: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="请求参数 JSON")
    result: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="结果 JSON")
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_local, index=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
