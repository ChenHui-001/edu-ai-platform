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
    APP_NAME: str = "新芽学堂"
    # 留空则自动推导：环境变量 APP_VERSION > 根目录 VERSION 文件 > IMAGE_TAG > "dev"
    APP_VERSION: str = ""
    IMAGE_TAG: str = ""
    DEBUG: bool = True
    # 运行环境标识，供「只在生产才该告警」的启动校验使用
    # （见 services/startup_checks.py）。取值 production / test / dev。
    #
    # ## 为什么需要它：DEBUG 不足以区分「生产」和「CI」
    #
    # 判据本可以只是 `not DEBUG`，但 e2e 与 CI 都是 DEBUG=false 且
    # SEED_DEMO_DATA=true —— 99 处 `.login()` 全用 teacher1/stu731 这类
    # 演示账号，关掉演示数据就全线红。于是「生产开着演示数据」这条告警会在
    # 每次 CI 触发，运维很快对它脱敏，那比不告警更坏。
    #
    # DEBUG 也不能为了区分而设成 true：会打开 /docs 与 /openapi.json
    # （DEBUG=false 时刻意关闭，避免把 198 个接口全图暴露给匿名访问者），
    # 还会触发临时 SECRET_KEY 生成。副作用太大。
    #
    # ## 为什么默认 production 而不是 dev
    #
    # 保守优先：现有部署（含 docker compose 模板）都没有这一项，必须让它们
    # **先看到告警**、确认自己确实在生产，而不是默默被豁免。本地开发想要
    # 安静就显式写 APP_ENV=dev。
    APP_ENV: str = "production"
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

    # 强制改密拦截开关：`must_change_password=True` 的用户，除白名单外一律 403。
    #
    # 为什么需要这个开关（而不是硬编码为行为）：
    # e2e 有 99 处 `.login()` 共用硬编码口令常量，且**裸登录**（不走 `login()`
    # 自愈）的有 42 处直接读登录响应体。真让它们走一遍「改成新密码」的流程，
    # "当前密码"就会在 100+ 个 Client 实例之间漂移，裸登录那批也拿不到新密码。
    # 所以测试环境需要一个隔离开关。
    #
    # **默认 true，生产必须 true。** 这不是安全后门：开关只影响「是否拦截」，
    # 不影响「是否拒绝 new==old」（后者是 `change_password` 里无条件的硬校验）。
    # 也就是说，即使有人把开关设成 false，也依然无法用 old==new 清除标记再
    # 靠出厂口令长期使用 —— 因为 S5 每次启动还会把出厂口令账号重新标记。
    MUST_CHANGE_PASSWORD_ENFORCED: bool = True

    # 图形验证码强制化开关（S7）：登录 / 注册是否**必须**携带 `captcha_key`。
    #
    # 修复前的行为（已修）：`if payload.captcha_key and not verify_captcha(...)`。
    # 这是个**短路绕过**，不是"兼容"：攻击者只要提交时**不写这个字段**，
    # 整段校验就被跳过，图形验证码对爆破完全不设防。而同一行代码在
    # `register` 里也存在，注册接口同样裸奔。
    #
    # 为什么仍需要开关（而不是硬编码为强制）：
    # e2e 有 100 处 `.login()` + 26 处裸 `post("/auth/login")` + 7 处
    # 裸 `post("/auth/register")`，它们都不携带验证码；而验证码的正确答案
    # **只存在于 PNG 图片里**，脚本无法从 `GET /auth/captcha` 的响应中拿到
    # （响应只有 base64 图和 key，明文答案在服务端，这是刻意的）。
    # 让这一百多处调用全部走 OCR 识别是不现实的，所以测试环境需要一个开关。
    #
    # **默认 true，生产必须 true。** 这个开关是**单向收紧**的，两个保证：
    # 1. `true`  → 必须携带且必须正确，缺 key 直接 400；
    # 2. `false` → **只允许"不传"**；一旦传了 `captcha_key`，仍然必须校验通过。
    #    也就是说关掉开关可以让无验证码的 API 调用通过，但**永远无法**让
    #    "传一个错的验证码"通过 —— 不存在"关开关就把校验变成空操作"的路径。
    # 这个不对称是刻意的：它保证开关最坏情况下只降级到「无验证码」，而不是
    # 「有验证码但形同虚设」。
    #
    # 注意这个 true 分支平时不执行：本地调试与自动化回归都注入 false，
    # 所以「开关生效」这件事只能靠人工验证或临时脚本确认。
    CAPTCHA_ENFORCED: bool = True

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
    # 输出 token 预算决定**推理型模型能不能给出正文**，不能按非推理模型标定。
    # MiniMax-M3.1-Flash 这类 reasoning 模型的 thinking token 与正文**共享同一
    # max_tokens 预算**：实测 2048 时 reasoning 吃掉 2047，finish_reason=length
    # 且正文 content 为空 → JSON 解析失败 → AI 出题静默降级为题库复用，
    # 对外却报「模型不可用，请配置 LLM_API_KEY」（误导）。
    # 原来的 2048 是在 deepseek-chat（无推理）上实测「输出均在 2k 以内」定的，
    # 换成推理模型后该假设失效，故提高到 8192（实测 reasoning 1535 + 正文正常）。
    # 超时由 LLM_TIMEOUT 与 max_retries=1 兜底，不靠压低预算来省时间。
    LLM_MAX_TOKENS: int = 8192
    # AI 接口按用户限流（每分钟），防止高频触发生成刷 token
    AGENT_RATE_LIMIT_PER_MIN: int = 12
    LLM_TIMEOUT: int = 60
    LLM_ENABLED: bool = True  # 未配置 Key 时自动降级为规则引擎
    # AI 组卷「缺口补题」的并发度（按大题并行）。
    #
    # 每大题单独调一次模型是题型正确性的前提（混着补会把单选题塞进填空题），
    # 串行时耗时随大题数线性增长，4~5 个大题可能顶到 nginx proxy_read_timeout。
    # 并行后最坏耗时 ≈ 单次最长耗时。默认 3 而非更高：
    # - 上游模型普遍对并发有速率限制，且本项目有 429 熔断（触发后整站 AI 冷却 30~300s）；
    # - SQLite 写锁是库级的，并发写只会排队，再高也压不出吞吐。
    # 设为 1 即退回串行（排障用）。
    AI_FILL_CONCURRENCY: int = 3
    # Chroma 向量模型的后台预热（首次会下载 ~79MB onnx 模型）。
    #
    # 为什么要有开关：预热是 `daemon=True` 的线程，里面跑的是 onnxruntime 的
    # native 代码。进程正常退出时 Python 会**强杀** daemon 线程，Linux 上
    # onnxruntime 在 native 层 abort（`terminate called without an active
    # exception` → exit code 134）。命令行脚本 import app 并走 lifespan 后
    # 即使所有断言通过也会被这个退出码判成失败（CI 上实测）。
    # 测试/CI 用不到向量检索，直接关掉既避免崩溃也省掉 79MB 下载。
    RAG_WARMUP_ENABLED: bool = True
    # 是否播种「教学基础数据」：各年级的学科、知识点树、命题标准。
    #
    # 为什么必须单独一个开关：这三类都是**「表为空就播种」**，所以运维把表删空
    # 之后，容器一重启就被重建，"空环境"根本立不住。QA 需要一个可复现的空基线
    # （只有账号、没有学科），必须在启动阶段就能跳过播种，而不是每次重启后手工再删。
    #
    # ⚠️ 年级**不受此开关影响**，始终播种：`sys_user.grade_id` 是非空外键，
    #    没有年级连账号都建不出来（删年级会级联删账号）。
    # ⚠️ 关掉后教师端登录看不到学科，组卷/出题/布置作业全部不可用 ——
    #    这是"能登录"而不是"能体验功能"，只适合空基线测试。
    SEED_BASE_DATA: bool = True

    # ---------------- 日志 / 任务 ----------------
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "./data/logs"
    LOG_RETENTION_DAYS: int = 30
    LOG_TO_DB: bool = True  # 登录/操作/错误日志入库
    # 是否**额外**写一份日志文件（loguru FileSink）。默认关闭。
    #
    # 关闭的理由（三条，按重要性排序）：
    # ① 全仓没有任何代码读日志文件 —— 真实通道是 stdout（`docker logs`）
    #    和 `sys_error_log` 表（`/logs/error` 页面查的是那张表）。写文件是
    #    纯冗余，唯一的消费者是运维的 `tail`。
    # ② 多 worker 下会**直接报错**。loguru 的 FileSink 以独占方式打开文件，
    #    `uvicorn --workers 2` 时第二个进程拿到
    #    `PermissionError: [Errno 13] Permission denied: '.../app_2026-xx-xx.log'`。
    #    注意：**这个异常不会让进程退出** —— loguru 把 sink 的写入异常吞掉并
    #    打到 stderr，于是第二个 worker 全程没有文件日志，而第一个正常。
    #    「日志看起来没问题、只是少了几个进程的」这种缺失极难发现。
    # ③ 容器里双重落盘：同一份内容既进 `docker logs` 又进挂载卷，30 天 retention
    #    的 zip 归档在生产上会占几十 MB 无用空间。
    #
    # 什么时候该打开：单进程本地开发想 `tail -f` 看完整历史（容器 `docker logs`
    # 会丢历史）；或者接了个读文件的日志采集器。打开后文件名会自动带 pid
    # （见 logger.py），所以多 worker 也不会互相抢文件 —— 但也就意味着日志被
    # 拆成 N 份，排障时得 `cat app_*_*.log` 一起看。
    LOG_FILE_SINK: bool = False

    SCHEDULER_ENABLED: bool = True
    # 定时任务执行锁的租约时长（秒）。`uvicorn --workers N` 下 N 个进程各自
    # 跑一份 APScheduler，同一分钟会同时触发同一个任务；靠 sys_job_lock 表
    # 保证只有一个真正执行（见 services/job_lock.py）。
    #
    # 1800s 的依据是**实测**而非估计：最慢的 handler 是 clean_old_logs
    # （3×30 万过期行）2592ms，1800s 有 694 倍余量。
    #
    # ⚠️ 但真正的理由不是余量，而是**所有 handler 都是「补齐式扫描」**
    # （publish_at <= now / created_at < cutoff / end_at < deadline）：
    # 漏掉一个窗口不丢数据、只是延后。这才是能容忍「崩溃后最长停 30 分钟」
    # 的前提。如果将来加了「只在精确时刻做一次、错过即永久丢失」的 handler，
    # 必须同步下调这个值，否则那个窗口会被静默跳过。
    JOB_LOCK_LEASE_SECONDS: int = 1800
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
    # 空库是否播种演示班级/教师/学生（teacher1/Teacher@123 等已知口令账号）。
    # 生产环境建议设为 false，只保留 admin 与基础年级学科数据。
    SEED_DEMO_DATA: bool = True

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
