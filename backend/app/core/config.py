"""应用配置管理：所有配置通过环境变量注入，无需修改代码。"""
import os
import re
import secrets
from functools import lru_cache
from typing import List, Optional

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# 版本号候选路径。开发态为<仓库根>/VERSION，容器内为 /app/VERSION。
_VERSION_CANDIDATES = (
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "VERSION")),
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "VERSION")),
    "/app/VERSION",
    os.path.abspath("VERSION"),
    os.path.abspath(os.path.join(".", "VERSION")),
)


def _read_version_file() -> Optional[str]:
    """读取 VERSION 文件，作为版本号的唯一真源。

    本地开发时文件位于仓库根（backend/app/core 上溯三级）；容器内镜像把
    VERSION 放在 /app。逐个候选探测，均不存在则返回 None，交由
    APP_VERSION / IMAGE_TAG 环境变量兜底。
    """
    for path in _VERSION_CANDIDATES:
        try:
            with open(path, encoding="utf-8") as fp:
                value = fp.read().strip()
            if value:
                return value
        except OSError:
            continue
    return None


class Settings(BaseSettings):
    """全局配置。"""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # ---------------- 基础 ----------------
    APP_NAME: str = "九年义务教育学习管理系统"
    # 留空则自动推导：环境变量 APP_VERSION > 根目录 VERSION 文件 > IMAGE_TAG > "dev"
    APP_VERSION: str = ""
    IMAGE_TAG: str = ""
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    API_PREFIX: str = "/api/v1"
    # 允许的前端来源（CORS）
    CORS_ORIGINS: List[str] = ["*"]

    # ---------------- 数据库 ----------------
    # 默认为 SQLite，切换 PostgreSQL 只需改 DATABASE_URL
    DATABASE_URL: str = "sqlite:///./data/edu_platform.db"
    DB_ECHO: bool = False
    SQLITE_CHECK_SAME_THREAD: bool = False

    # ---------------- 安全 ----------------
    # 默认留空，由 _resolve_secret_key 校验/生成：
    # - 开发态（DEBUG=true）生成进程内随机密钥并告警，保证本地开箱即用；
    # - 生产态（DEBUG=false）未配置或仍是公开占位符时直接拒绝启动。
    # 绝不能再用公开默认值签发 JWT——那等于把 admin token 的签发权交给所有人。
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 12
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PASSWORD_MIN_LENGTH: int = 8
    # 创建用户时的默认初始密码（满足强度要求：字母+数字+长度）
    DEFAULT_USER_PASSWORD: str = "Edu@2026Init"

    # ---------------- 文件 / 附件 ----------------
    UPLOAD_DIR: str = "./data/uploads"
    EXPORT_DIR: str = "./data/exports"
    MAX_UPLOAD_SIZE: int = 50  # MB
    ALLOWED_UPLOAD_TYPES: List[str] = [
        ".jpg", ".jpeg", ".png", ".gif", ".webp",
        ".pdf", ".doc", ".docx", ".xls", ".xlsx",
        ".ppt", ".pptx", ".txt", ".csv", ".md",
    ]

    # ---------------- 向量库 / RAG ----------------
    CHROMA_PERSIST_DIR: str = "./data/chroma"
    CHROMA_COLLECTION: str = "edu_knowledge"
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    RAG_TOP_K: int = 5
    RAG_SCORE_THRESHOLD: float = 0.3
    # 向量重建耗时告警阈值（ms），超过则接口提示分批执行
    REINDEX_WARN_MS: int = 60_000
    # 向量重建硬超时（秒），到点中断并返回部分结果，避免拖死调用方
    REINDEX_TIMEOUT_SEC: int = 90

    # ---------------- 大模型 ----------------
    # 兼容 OpenAI 协议：通义千问 / DeepSeek / 本地 vLLM 均可
    LLM_PROVIDER: str = "deepseek"  # deepseek | qwen | openai | ollama
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "https://api.deepseek.com/v1"
    LLM_MODEL: str = "deepseek-chat"
    LLM_TEMPERATURE: float = 0.7
    # 输出 token 是 LLM 耗时的主要来源：4096 会让单次调用接近 60s 超时边界。
    # 实测出题 5 题 / 笔记整理 / 组卷等任务输出均在 2k token 以内，
    # 故默认调整为 2048（可通过系统配置 llm_max_tokens 覆盖）。
    LLM_MAX_TOKENS: int = 2048
    # AI 接口按用户限流（每分钟），防止高频触发生成刷 token
    AGENT_RATE_LIMIT_PER_MIN: int = 12
    LLM_TIMEOUT: int = 60
    LLM_ENABLED: bool = True  # 未配置 Key 时自动降级为规则引擎

    # ---------------- 日志 / 任务 ----------------
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "./data/logs"
    LOG_RETENTION_DAYS: int = 30
    LOG_TO_DB: bool = True  # 登录/操作/错误日志入库

    SCHEDULER_ENABLED: bool = True
    # 内置默认任务（cron: 分 时 日 月 周）
    CRON_CLEAN_EXPIRED_EXAMS: str = "0 3 * * *"
    CRON_DAILY_REPORT: str = "0 7 * * *"
    CRON_CLEAN_TEMP_FILES: str = "0 4 * * *"
    CRON_REVIEW_REMINDER: str = "0 8 * * *"

    # ---------------- 业务 ----------------
    REVIEW_INTERVALS: List[int] = [1, 2, 4, 7, 15, 30]  # 艾宾浩斯复习节点（天）
    PASS_SCORE: float = 60.0
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 200

    @model_validator(mode="after")
    def _resolve_secret_key(self) -> "Settings":
        """校验 SECRET_KEY：生产环境 fail-closed，开发环境生成临时随机密钥。"""
        raw = (self.SECRET_KEY or "").strip()
        weak = (
            not raw
            or raw == "CHANGE_ME_IN_PRODUCTION_please_use_a_long_random_string"
            or len(raw) < 32
        )
        if not weak:
            self.SECRET_KEY = raw
            return self
        if not self.DEBUG:
            raise ValueError(
                "SECRET_KEY 未配置或过于简单（至少 32 位随机字符）。"
                "请先在 .env 或环境变量中设置 SECRET_KEY；"
                "本地开发可设置 DEBUG=true 让系统生成临时密钥。"
            )
        self.SECRET_KEY = secrets.token_urlsafe(48)
        print(
            "[config] SECRET_KEY 未配置或过弱，已生成进程内临时密钥；"
            "重启后令牌会失效。生产环境必须显式设置 SECRET_KEY。"
        )
        return self

    @model_validator(mode="after")
    def _resolve_version(self) -> "Settings":
        """版本号单一真源：根目录 VERSION 文件。

        优先级：
          1. 显式 APP_VERSION **且形如版本号**（x.y[.z]）—— 允许 CI 注入 ci-<sha> 之类
          2. VERSION 文件（镜像内 /app/VERSION）
          3. 其余情况退化为 "dev"

        刻意不使用 IMAGE_TAG：它是镜像命名标签，常为 `latest` 这类浮动值，
        拿去当 version 会让 /health 返回无意义的结果。
        """
        raw = (self.APP_VERSION or "").strip()
        if re.match(r"^v?\d+\.\d+", raw):
            return self
        # 非法/空的 APP_VERSION（含 Docker 缓存残留的 "latest"）→ 回落到 VERSION 文件
        file_ver = _read_version_file()
        if raw or file_ver != self.APP_VERSION:
            print(f"[config] APP_VERSION={raw!r} 非版本号，回落为 "
                  f"{file_ver or 'dev'}")
        self.APP_VERSION = file_ver or "dev"
        return self


@lru_cache()
def get_settings() -> Settings:
    """缓存配置实例，避免重复解析。"""
    return Settings()


settings = get_settings()
