"""日志框架：Loguru 控制台（默认）+ 可选文件切割归档 + 数据库落库。"""
import os
import sys

from loguru import logger

from app.core.config import settings


def setup_logging() -> None:
    """配置 Loguru。

    **默认只加控制台 sink。** 文件 sink 需要显式开 `LOG_FILE_SINK=true`，
    理由见 `core/config.py:LOG_FILE_SINK` 的注释（简版：全仓没人读那个文件；
    多 worker 下第二个进程会 PermissionError 且不退出，只静默少一份日志）。
    """
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

    # 文件：按天切割 + 自动归档（默认关闭，见上方 docstring）
    if not getattr(settings, "LOG_FILE_SINK", False) or not settings.LOG_DIR:
        return

    # 文件名必须带 pid：loguru 的 FileSink 是**独占**打开的，`--workers N`
    # 时 N 个进程抢同一个路径 → 后到的报
    # `PermissionError: [Errno 13] Permission denied`。
    # ★ 关键坑：loguru 会把这个异常吞掉打到 stderr，**进程既不退出也不重试**，
    #   于是 N-1 个 worker 全程没有文件日志。带 pid 后各写各的，日志被拆成
    #   N 份 —— 排障时要 `cat app_*_*.log`，别只看最新那个文件。
    try:
        os.makedirs(settings.LOG_DIR, exist_ok=True)
    except OSError as exc:
        # 目录建不出来（只读挂载等）时也不该让应用起不来，退化成只有控制台。
        logger.warning(f"日志目录 {settings.LOG_DIR} 不可用，跳过文件日志: {exc}")
        return

    logger.add(
        f"{settings.LOG_DIR}/app_{os.getpid()}_{{time:YYYY-MM-DD}}.log",
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


setup_logging()
