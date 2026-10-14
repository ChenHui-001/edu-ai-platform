"""应用配置管理：所有配置通过环境变量注入，无需修改代码。"""
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """全局配置。"""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # ---------------- 基础 ----------------
    APP_NAME: str = "九年义务教育学习管理系统"
    APP_VERSION: str = "1.0.0"
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
    SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION_please_use_a_long_random_string"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 12
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PASSWORD_MIN_LENGTH: int = 8

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

    # ---------------- 大模型 ----------------
    # 兼容 OpenAI 协议：通义千问 / DeepSeek / 本地 vLLM 均可
    LLM_PROVIDER: str = "deepseek"  # deepseek | qwen | openai | ollama
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "https://api.deepseek.com/v1"
    LLM_MODEL: str = "deepseek-chat"
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 4096
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


@lru_cache()
def get_settings() -> Settings:
    """缓存配置实例，避免重复解析。"""
    return Settings()


settings = get_settings()
