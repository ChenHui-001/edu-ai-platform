"""日志框架：Loguru 控制台 + 文件切割归档 + 数据库落库。"""
import sys
from typing import Any, Dict, Optional

from loguru import logger

from app.core.config import settings


def setup_logging() -> None:
    """配置 Loguru。"""
    logger.remove()

    # 控制台：简洁格式
    logger.add(
        sys.stderr,
        level=settings.LOG_LEVEL,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>"
        ),
        backtrace=False,
        diagnose=False,
        enqueue=True,
    )

    # 文件：按天切割 + 自动归档
    if settings.LOG_DIR:
        logger.add(
            f"{settings.LOG_DIR}/app_{{time:YYYY-MM-DD}}.log",
            level=settings.LOG_LEVEL,
            rotation="00:00",
            retention=f"{settings.LOG_RETENTION_DAYS} days",
            compression="zip",
            enqueue=True,
            backtrace=True,
            diagnose=False,
        )


def get_logger(name: str):
    """获取带模块名的 logger。"""
    return logger.bind(module=name)


def log_audit(
    *,
    module: str,
    action: str,
    user_id: Optional[int] = None,
    username: Optional[str] = None,
    method: Optional[str] = None,
    path: Optional[str] = None,
    ip: Optional[str] = None,
    status: str = "success",
    detail: Optional[Dict[str, Any]] = None,
    duration_ms: Optional[int] = None,
) -> None:
    """记录审计日志（写入业务日志表）。"""
    logger.bind(
        audit=True,
        module=module,
        action=action,
        user_id=user_id,
        username=username,
        method=method,
        path=path,
        ip=ip,
        status=status,
        detail=detail or {},
        duration_ms=duration_ms,
    ).info(f"[AUDIT] {module}.{action} by {username or 'anonymous'}")


setup_logging()
