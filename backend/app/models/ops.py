"""运维模型：登录日志、操作日志、错误日志、定时任务、附件、AI 调用日志。"""
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.utils.common import utcnow


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
    login_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)


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
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)


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
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)


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
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class JobExecutionLog(Base):
    """定时任务执行记录。"""

    __tablename__ = "sys_job_execution_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("sys_scheduled_job.id", ondelete="CASCADE"), index=True)
    job_name: Mapped[str] = mapped_column(String(128), index=True)
    status: Mapped[str] = mapped_column(String(16), default="running", index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    trigger_type: Mapped[str] = mapped_column(String(16), default="auto", comment="auto/manual")


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
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)


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
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)


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
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)

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
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


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
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
