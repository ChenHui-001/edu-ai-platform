# 配置索引

- Output Language: zh-CN
- 状态: in-progress

| CFG ID | 配置名 | 来源 | 默认值 | 消费者 | 控制行为 | 敏感性 | 证据 |
|---|---|---|---|---|---|---|---|
| CFG-APP_NAME | APP_NAME | env/settings | 新芽学堂 | system.py, version_info.py | 应用显示名 | low | backend/app/core/config.py |
| CFG-APP_VERSION | APP_VERSION | env/settings | 读取 VERSION | main.py, system.py, version_info.py | 版本一致性 | low | backend/app/core/config.py |
| CFG-IMAGE_TAG | IMAGE_TAG | env/settings | 未知 | Dockerfile/CI | 镜像标签 | low | backend/app/core/config.py |
| CFG-DEBUG | DEBUG | env/settings | true | startup_checks, readiness, system.py | 调试与生产校验 | high | backend/app/core/config.py |
| CFG-APP_ENV | APP_ENV | env/settings | production | startup_checks | 生产形态判断 | high | backend/app/core/config.py |
| CFG-HOST | HOST | env/settings | 0.0.0.0 | uvicorn | 监听地址 | medium | backend/app/core/config.py |
| CFG-PORT | PORT | env/settings | 8000 | uvicorn | 监听端口 | medium | backend/app/core/config.py |
| CFG-API_PREFIX | API_PREFIX | env/settings | /api/v1 | 全局路由 | API 前缀 | low | backend/app/core/config.py |
| CFG-CORS_ORIGINS | CORS_ORIGINS | env/settings | [] | FastAPI CORS | 跨域来源 | medium | backend/app/core/config.py |
| CFG-DATABASE_URL | DATABASE_URL | env/settings | sqlite:///./data/edu_platform.db | database.py, readiness | 数据库连接 | high | backend/app/core/config.py |
| CFG-DB_ECHO | DB_ECHO | env/settings | false | database.py | SQL 日志 | medium | backend/app/core/config.py |
| CFG-SQLITE_CHECK_SAME_THREAD | SQLITE_CHECK_SAME_THREAD | env/settings | false | database.py | 线程检查 | low | backend/app/core/config.py |
| CFG-SECRET_KEY | SECRET_KEY | env/settings | 未知 | security.py | JWT 签发 | critical | backend/app/core/config.py |
| CFG-ALGORITHM | ALGORITHM | env/settings | HS256 | security.py | JWT 算法 | medium | backend/app/core/config.py |
| CFG-ACCESS_TOKEN_EXPIRE_MINUTES | ACCESS_TOKEN_EXPIRE_MINUTES | env/settings | 720 | auth_service | 访问令牌有效期 | medium | backend/app/core/config.py |
| CFG-REFRESH_TOKEN_EXPIRE_DAYS | REFRESH_TOKEN_EXPIRE_DAYS | env/settings | 7 | auth_service | 刷新令牌有效期 | medium | backend/app/core/config.py |
| CFG-PASSWORD_MIN_LENGTH | PASSWORD_MIN_LENGTH | env/settings | 8 | security.py | 密码强度 | medium | backend/app/core/config.py |
| CFG-DEFAULT_USER_PASSWORD | DEFAULT_USER_PASSWORD | env/settings | Edu@2026Init | init_db/system.py | 初始密码 | critical | backend/app/core/config.py |
| CFG-MUST_CHANGE_PASSWORD_ENFORCED | MUST_CHANGE_PASSWORD_ENFORCED | env/settings | true | auth_service | 强制改密 | medium | backend/app/core/config.py |
| CFG-CAPTCHA_ENFORCED | CAPTCHA_ENFORCED | env/settings | true | auth.py | 验证码开关 | medium | backend/app/core/config.py |
| CFG-UPLOAD_DIR | UPLOAD_DIR | env/settings | ./data/uploads | attachment/knowledge/lesson | 附件目录 | medium | backend/app/core/config.py |
| CFG-EXPORT_DIR | EXPORT_DIR | env/settings | ./data/exports | export_job/report | 导出目录 | medium | backend/app/core/config.py |
| CFG-MAX_UPLOAD_SIZE | MAX_UPLOAD_SIZE | env/settings | 50 | attachment/knowledge/lesson | 上传大小限制 | medium | backend/app/core/config.py |
| CFG-ALLOWED_UPLOAD_TYPES | ALLOWED_UPLOAD_TYPES | env/settings | 未知 | attachment/knowledge/lesson | 允许扩展名 | medium | backend/app/core/config.py |
| CFG-CHROMA_PERSIST_DIR | CHROMA_PERSIST_DIR | env/settings | ./data/chroma | rag | Chroma 目录 | medium | backend/app/core/config.py |
| CFG-CHROMA_COLLECTION | CHROMA_COLLECTION | env/settings | edu_knowledge | rag | 集合名 | low | backend/app/core/config.py |
| CFG-EMBEDDING_MODEL | EMBEDDING_MODEL | env/settings | text-embedding-3-small | rag | 向量模型 | medium | backend/app/core/config.py |
| CFG-RAG_TOP_K | RAG_TOP_K | env/settings | 5 | rag | 检索条数 | low | backend/app/core/config.py |
| CFG-RAG_SCORE_THRESHOLD | RAG_SCORE_THRESHOLD | env/settings | 0.3 | rag | 相关性阈值 | low | backend/app/core/config.py |
| CFG-REINDEX_WARN_MS | REINDEX_WARN_MS | env/settings | 60000 | knowledge.py | 索引耗时告警 | low | backend/app/core/config.py |
| CFG-REINDEX_TIMEOUT_SEC | REINDEX_TIMEOUT_SEC | env/settings | 90 | knowledge.py | 索引超时 | medium | backend/app/core/config.py |
| CFG-LLM_PROVIDER | LLM_PROVIDER | env/settings | deepseek | llm | 模型厂商 | medium | backend/app/core/config.py |
| CFG-LLM_API_KEY | LLM_API_KEY | env/settings | 未知 | llm | API Key | critical | backend/app/core/config.py |
| CFG-LLM_BASE_URL | LLM_BASE_URL | env/settings | https://api.deepseek.com/v1 | llm | API 地址 | medium | backend/app/core/config.py |
| CFG-LLM_MODEL | LLM_MODEL | env/settings | deepseek-chat | llm | 主模型 | low | backend/app/core/config.py |
| CFG-LLM_TEMPERATURE | LLM_TEMPERATURE | env/settings | 0.7 | llm | 采样温度 | low | backend/app/core/config.py |
| CFG-LLM_MAX_TOKENS | LLM_MAX_TOKENS | env/settings | 8192 | llm | 输出上限 | low | backend/app/core/config.py |
| CFG-AGENT_RATE_LIMIT_PER_MIN | AGENT_RATE_LIMIT_PER_MIN | env/settings | 12 | rate_limit | Agent 限速 | medium | backend/app/core/config.py |
| CFG-LLM_TIMEOUT | LLM_TIMEOUT | env/settings | 60 | llm | 超时 | medium | backend/app/core/config.py |
| CFG-LLM_ENABLED | LLM_ENABLED | env/settings | true | llm | LLM 总开关 | medium | backend/app/core/config.py |
| CFG-LLM_MODEL_FAST | LLM_MODEL_FAST | env/settings | 未知 | llm | 快速模型 | low | backend/app/core/config.py |
| CFG-LLM_BASE_URL_FAST | LLM_BASE_URL_FAST | env/settings | 未知 | llm | 快速模型地址 | low | backend/app/core/config.py |
| CFG-LLM_FAST_BIZ_TYPES | LLM_FAST_BIZ_TYPES | env/settings | question_generate,question_variants | llm | 快速模型场景 | low | backend/app/core/config.py |
| CFG-LLM_FAST_REASONING_EFFORT | LLM_FAST_REASONING_EFFORT | env/settings | low | llm | 推理强度 | low | backend/app/core/config.py |
| CFG-AI_FILL_CONCURRENCY | AI_FILL_CONCURRENCY | env/settings | 3 | paper_compose | AI 补题并发 | medium | backend/app/core/config.py |
| CFG-LLM_MAX_CONCURRENCY | LLM_MAX_CONCURRENCY | env/settings | 8 | llm | LLM 并发 | medium | backend/app/core/config.py |
| CFG-RAG_WARMUP_ENABLED | RAG_WARMUP_ENABLED | env/settings | true | main.py | 启动预热 | low | backend/app/core/config.py |
| CFG-SEED_BASE_DATA | SEED_BASE_DATA | env/settings | true | init_db | 基础种子 | medium | backend/app/core/config.py |
| CFG-LOG_LEVEL | LOG_LEVEL | env/settings | INFO | logger | 日志级别 | low | backend/app/core/config.py |
| CFG-LOG_DIR | LOG_DIR | env/settings | ./data/logs | logger/readiness | 日志目录 | low | backend/app/core/config.py |
| CFG-LOG_RETENTION_DAYS | LOG_RETENTION_DAYS | env/settings | 30 | task_jobs.clean_old_logs | 日志保留 | medium | backend/app/core/config.py |
| CFG-LOG_TO_DB | LOG_TO_DB | env/settings | true | logger/middleware | 日志入库 | medium | backend/app/core/config.py |
| CFG-LOG_FILE_SINK | LOG_FILE_SINK | env/settings | false | logger | 文件日志 | low | backend/app/core/config.py |
| CFG-SCHEDULER_ENABLED | SCHEDULER_ENABLED | env/settings | true | scheduler | 调度开关 | medium | backend/app/core/config.py |
| CFG-JOB_LOCK_LEASE_SECONDS | JOB_LOCK_LEASE_SECONDS | env/settings | 1800 | scheduler/job_lock | 任务锁租约 | medium | backend/app/core/config.py |
| CFG-CRON_CLEAN_EXPIRED_EXAMS | CRON_CLEAN_EXPIRED_EXAMS | env/settings | 0 3 * * * | init_db | 清理任务 Cron | low | backend/app/core/config.py |
| CFG-CRON_DAILY_REPORT | CRON_DAILY_REPORT | env/settings | 0 7 * * * | init_db | 日报 Cron | low | backend/app/core/config.py |
| CFG-CRON_CLEAN_TEMP_FILES | CRON_CLEAN_TEMP_FILES | env/settings | 0 4 * * * | init_db | 临时附件清理 Cron | low | backend/app/core/config.py |
| CFG-CRON_REVIEW_REMINDER | CRON_REVIEW_REMINDER | env/settings | 0 8 * * * | init_db | 复习提醒 Cron | low | backend/app/core/config.py |
| CFG-REVIEW_INTERVALS | REVIEW_INTERVALS | env/settings | [1,2,4,7,15,30] | review/remediation | 复习周期 | low | backend/app/core/config.py |
| CFG-PASS_SCORE | PASS_SCORE | env/settings | 60.0 | task/grading/report | 默认及格线 | medium | backend/app/core/config.py |
| CFG-DEFAULT_PAGE_SIZE | DEFAULT_PAGE_SIZE | env/settings | 20 | API 分页 | 分页大小 | low | backend/app/core/config.py |
| CFG-MAX_PAGE_SIZE | MAX_PAGE_SIZE | env/settings | 200 | API 分页 | 最大分页 | low | backend/app/core/config.py |
| CFG-SEED_DEMO_DATA | SEED_DEMO_DATA | env/settings | false | init_db/startup_checks | 演示数据 | high | backend/app/core/config.py |
| CFG-DEMO_LEARNING_FLOW | DEMO_LEARNING_FLOW | env/settings | false | init_db | 演示学习流程 | low | backend/app/core/config.py |

## 主定义索引

## CFG-APP_NAME
- ID: CFG-APP_NAME
- 配置名: APP_NAME
- 来源: env/settings
- 默认值: 新芽学堂
- 消费者: system.py, version_info.py
- 控制行为: 应用显示名
- 敏感性: low
- 证据: backend/app/core/config.py

## CFG-DATABASE_URL
- ID: CFG-DATABASE_URL
- 配置名: DATABASE_URL
- 来源: env/settings
- 默认值: sqlite:///./data/edu_platform.db
- 消费者: database.py, readiness.py
- 控制行为: 数据库连接
- 敏感性: high
- 证据: backend/app/core/config.py

## CFG-SECRET_KEY
- ID: CFG-SECRET_KEY
- 配置名: SECRET_KEY
- 来源: env/settings
- 默认值: 未知
- 消费者: security.py
- 控制行为: JWT 签发
- 敏感性: critical
- 证据: backend/app/core/config.py

## CFG-SCHEDULER_ENABLED
- ID: CFG-SCHEDULER_ENABLED
- 配置名: SCHEDULER_ENABLED
- 来源: env/settings
- 默认值: true
- 消费者: scheduler.py
- 控制行为: 调度开关
- 敏感性: medium
- 证据: backend/app/core/config.py

## 主定义索引

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 

## 
- ID: 


## 主定义索引

## CFG-APP_VERSION
- ID: CFG-APP_VERSION
- 配置名: APP_VERSION
- 来源: env/settings
- 默认值: 读取 VERSION
- 消费者: main.py, system.py, version_info.py
- 控制行为: 版本一致性
- 敏感性: low
- 证据: backend/app/core/config.py

## CFG-IMAGE_TAG
- ID: CFG-IMAGE_TAG
- 配置名: IMAGE_TAG
- 来源: env/settings
- 默认值: 未知
- 消费者: Dockerfile/CI
- 控制行为: 镜像标签
- 敏感性: low
- 证据: backend/app/core/config.py

## CFG-DEBUG
- ID: CFG-DEBUG
- 配置名: DEBUG
- 来源: env/settings
- 默认值: true
- 消费者: startup_checks, readiness, system.py
- 控制行为: 调试与生产校验
- 敏感性: high
- 证据: backend/app/core/config.py

## CFG-APP_ENV
- ID: CFG-APP_ENV
- 配置名: APP_ENV
- 来源: env/settings
- 默认值: production
- 消费者: startup_checks
- 控制行为: 生产形态判断
- 敏感性: high
- 证据: backend/app/core/config.py

## CFG-HOST
- ID: CFG-HOST
- 配置名: HOST
- 来源: env/settings
- 默认值: 0.0.0.0
- 消费者: uvicorn
- 控制行为: 监听地址
- 敏感性: medium
- 证据: backend/app/core/config.py

## CFG-PORT
- ID: CFG-PORT
- 配置名: PORT
- 来源: env/settings
- 默认值: 8000
- 消费者: uvicorn
- 控制行为: 监听端口
- 敏感性: medium
- 证据: backend/app/core/config.py

## CFG-API_PREFIX
- ID: CFG-API_PREFIX
- 配置名: API_PREFIX
- 来源: env/settings
- 默认值: /api/v1
- 消费者: 全局路由
- 控制行为: API 前缀
- 敏感性: low
- 证据: backend/app/core/config.py

## CFG-CORS_ORIGINS
- ID: CFG-CORS_ORIGINS
- 配置名: CORS_ORIGINS
- 来源: env/settings
- 默认值: []
- 消费者: FastAPI CORS
- 控制行为: 跨域来源
- 敏感性: medium
- 证据: backend/app/core/config.py

## CFG-DB_ECHO
- ID: CFG-DB_ECHO
- 配置名: DB_ECHO
- 来源: env/settings
- 默认值: false
- 消费者: database.py
- 控制行为: SQL 日志
- 敏感性: medium
- 证据: backend/app/core/config.py

## CFG-SQLITE_CHECK_SAME_THREAD
- ID: CFG-SQLITE_CHECK_SAME_THREAD
- 配置名: SQLITE_CHECK_SAME_THREAD
- 来源: env/settings
- 默认值: false
- 消费者: database.py
- 控制行为: 线程检查
- 敏感性: low
- 证据: backend/app/core/config.py

## CFG-ALGORITHM
- ID: CFG-ALGORITHM
- 配置名: ALGORITHM
- 来源: env/settings
- 默认值: HS256
- 消费者: security.py
- 控制行为: JWT 算法
- 敏感性: medium
- 证据: backend/app/core/config.py

## CFG-ACCESS_TOKEN_EXPIRE_MINUTES
- ID: CFG-ACCESS_TOKEN_EXPIRE_MINUTES
- 配置名: ACCESS_TOKEN_EXPIRE_MINUTES
- 来源: env/settings
- 默认值: 720
- 消费者: auth_service
- 控制行为: 访问令牌有效期
- 敏感性: medium
- 证据: backend/app/core/config.py

## CFG-REFRESH_TOKEN_EXPIRE_DAYS
- ID: CFG-REFRESH_TOKEN_EXPIRE_DAYS
- 配置名: REFRESH_TOKEN_EXPIRE_DAYS
- 来源: env/settings
- 默认值: 7
- 消费者: auth_service
- 控制行为: 刷新令牌有效期
- 敏感性: medium
- 证据: backend/app/core/config.py

## CFG-PASSWORD_MIN_LENGTH
- ID: CFG-PASSWORD_MIN_LENGTH
- 配置名: PASSWORD_MIN_LENGTH
- 来源: env/settings
- 默认值: 8
- 消费者: security.py
- 控制行为: 密码强度
- 敏感性: medium
- 证据: backend/app/core/config.py

## CFG-DEFAULT_USER_PASSWORD
- ID: CFG-DEFAULT_USER_PASSWORD
- 配置名: DEFAULT_USER_PASSWORD
- 来源: env/settings
- 默认值: Edu@2026Init
- 消费者: init_db/system.py
- 控制行为: 初始密码
- 敏感性: critical
- 证据: backend/app/core/config.py

## CFG-MUST_CHANGE_PASSWORD_ENFORCED
- ID: CFG-MUST_CHANGE_PASSWORD_ENFORCED
- 配置名: MUST_CHANGE_PASSWORD_ENFORCED
- 来源: env/settings
- 默认值: true
- 消费者: auth_service
- 控制行为: 强制改密
- 敏感性: medium
- 证据: backend/app/core/config.py

## CFG-CAPTCHA_ENFORCED
- ID: CFG-CAPTCHA_ENFORCED
- 配置名: CAPTCHA_ENFORCED
- 来源: env/settings
- 默认值: true
- 消费者: auth.py
- 控制行为: 验证码开关
- 敏感性: medium
- 证据: backend/app/core/config.py

## CFG-UPLOAD_DIR
- ID: CFG-UPLOAD_DIR
- 配置名: UPLOAD_DIR
- 来源: env/settings
- 默认值: ./data/uploads
- 消费者: attachment/knowledge/lesson
- 控制行为: 附件目录
- 敏感性: medium
- 证据: backend/app/core/config.py

## CFG-EXPORT_DIR
- ID: CFG-EXPORT_DIR
- 配置名: EXPORT_DIR
- 来源: env/settings
- 默认值: ./data/exports
- 消费者: export_job/report
- 控制行为: 导出目录
- 敏感性: medium
- 证据: backend/app/core/config.py

## CFG-MAX_UPLOAD_SIZE
- ID: CFG-MAX_UPLOAD_SIZE
- 配置名: MAX_UPLOAD_SIZE
- 来源: env/settings
- 默认值: 50
- 消费者: attachment/knowledge/lesson
- 控制行为: 上传大小限制
- 敏感性: medium
- 证据: backend/app/core/config.py

## CFG-ALLOWED_UPLOAD_TYPES
- ID: CFG-ALLOWED_UPLOAD_TYPES
- 配置名: ALLOWED_UPLOAD_TYPES
- 来源: env/settings
- 默认值: 未知
- 消费者: attachment/knowledge/lesson
- 控制行为: 允许扩展名
- 敏感性: medium
- 证据: backend/app/core/config.py

## CFG-CHROMA_PERSIST_DIR
- ID: CFG-CHROMA_PERSIST_DIR
- 配置名: CHROMA_PERSIST_DIR
- 来源: env/settings
- 默认值: ./data/chroma
- 消费者: rag
- 控制行为: Chroma 目录
- 敏感性: medium
- 证据: backend/app/core/config.py

## CFG-CHROMA_COLLECTION
- ID: CFG-CHROMA_COLLECTION
- 配置名: CHROMA_COLLECTION
- 来源: env/settings
- 默认值: edu_knowledge
- 消费者: rag
- 控制行为: 集合名
- 敏感性: low
- 证据: backend/app/core/config.py

## CFG-EMBEDDING_MODEL
- ID: CFG-EMBEDDING_MODEL
- 配置名: EMBEDDING_MODEL
- 来源: env/settings
- 默认值: text-embedding-3-small
- 消费者: rag
- 控制行为: 向量模型
- 敏感性: medium
- 证据: backend/app/core/config.py

## CFG-RAG_TOP_K
- ID: CFG-RAG_TOP_K
- 配置名: RAG_TOP_K
- 来源: env/settings
- 默认值: 5
- 消费者: rag
- 控制行为: 检索条数
- 敏感性: low
- 证据: backend/app/core/config.py

## CFG-RAG_SCORE_THRESHOLD
- ID: CFG-RAG_SCORE_THRESHOLD
- 配置名: RAG_SCORE_THRESHOLD
- 来源: env/settings
- 默认值: 0.3
- 消费者: rag
- 控制行为: 相关性阈值
- 敏感性: low
- 证据: backend/app/core/config.py

## CFG-REINDEX_WARN_MS
- ID: CFG-REINDEX_WARN_MS
- 配置名: REINDEX_WARN_MS
- 来源: env/settings
- 默认值: 60000
- 消费者: knowledge.py
- 控制行为: 索引耗时告警
- 敏感性: low
- 证据: backend/app/core/config.py

## CFG-REINDEX_TIMEOUT_SEC
- ID: CFG-REINDEX_TIMEOUT_SEC
- 配置名: REINDEX_TIMEOUT_SEC
- 来源: env/settings
- 默认值: 90
- 消费者: knowledge.py
- 控制行为: 索引超时
- 敏感性: medium
- 证据: backend/app/core/config.py

## CFG-LLM_PROVIDER
- ID: CFG-LLM_PROVIDER
- 配置名: LLM_PROVIDER
- 来源: env/settings
- 默认值: deepseek
- 消费者: llm
- 控制行为: 模型厂商
- 敏感性: medium
- 证据: backend/app/core/config.py

## CFG-LLM_API_KEY
- ID: CFG-LLM_API_KEY
- 配置名: LLM_API_KEY
- 来源: env/settings
- 默认值: 未知
- 消费者: llm
- 控制行为: API Key
- 敏感性: critical
- 证据: backend/app/core/config.py

## CFG-LLM_BASE_URL
- ID: CFG-LLM_BASE_URL
- 配置名: LLM_BASE_URL
- 来源: env/settings
- 默认值: https://api.deepseek.com/v1
- 消费者: llm
- 控制行为: API 地址
- 敏感性: medium
- 证据: backend/app/core/config.py

## CFG-LLM_MODEL
- ID: CFG-LLM_MODEL
- 配置名: LLM_MODEL
- 来源: env/settings
- 默认值: deepseek-chat
- 消费者: llm
- 控制行为: 主模型
- 敏感性: low
- 证据: backend/app/core/config.py

## CFG-LLM_TEMPERATURE
- ID: CFG-LLM_TEMPERATURE
- 配置名: LLM_TEMPERATURE
- 来源: env/settings
- 默认值: 0.7
- 消费者: llm
- 控制行为: 采样温度
- 敏感性: low
- 证据: backend/app/core/config.py

## CFG-LLM_MAX_TOKENS
- ID: CFG-LLM_MAX_TOKENS
- 配置名: LLM_MAX_TOKENS
- 来源: env/settings
- 默认值: 8192
- 消费者: llm
- 控制行为: 输出上限
- 敏感性: low
- 证据: backend/app/core/config.py

## CFG-AGENT_RATE_LIMIT_PER_MIN
- ID: CFG-AGENT_RATE_LIMIT_PER_MIN
- 配置名: AGENT_RATE_LIMIT_PER_MIN
- 来源: env/settings
- 默认值: 12
- 消费者: rate_limit
- 控制行为: Agent 限速
- 敏感性: medium
- 证据: backend/app/core/config.py

## CFG-LLM_TIMEOUT
- ID: CFG-LLM_TIMEOUT
- 配置名: LLM_TIMEOUT
- 来源: env/settings
- 默认值: 60
- 消费者: llm
- 控制行为: 超时
- 敏感性: medium
- 证据: backend/app/core/config.py

## CFG-LLM_ENABLED
- ID: CFG-LLM_ENABLED
- 配置名: LLM_ENABLED
- 来源: env/settings
- 默认值: true
- 消费者: llm
- 控制行为: LLM 总开关
- 敏感性: medium
- 证据: backend/app/core/config.py

## CFG-LLM_MODEL_FAST
- ID: CFG-LLM_MODEL_FAST
- 配置名: LLM_MODEL_FAST
- 来源: env/settings
- 默认值: 未知
- 消费者: llm
- 控制行为: 快速模型
- 敏感性: low
- 证据: backend/app/core/config.py

## CFG-LLM_BASE_URL_FAST
- ID: CFG-LLM_BASE_URL_FAST
- 配置名: LLM_BASE_URL_FAST
- 来源: env/settings
- 默认值: 未知
- 消费者: llm
- 控制行为: 快速模型地址
- 敏感性: low
- 证据: backend/app/core/config.py

## CFG-LLM_FAST_BIZ_TYPES
- ID: CFG-LLM_FAST_BIZ_TYPES
- 配置名: LLM_FAST_BIZ_TYPES
- 来源: env/settings
- 默认值: question_generate,question_variants
- 消费者: llm
- 控制行为: 快速模型场景
- 敏感性: low
- 证据: backend/app/core/config.py

## CFG-LLM_FAST_REASONING_EFFORT
- ID: CFG-LLM_FAST_REASONING_EFFORT
- 配置名: LLM_FAST_REASONING_EFFORT
- 来源: env/settings
- 默认值: low
- 消费者: llm
- 控制行为: 推理强度
- 敏感性: low
- 证据: backend/app/core/config.py

## CFG-AI_FILL_CONCURRENCY
- ID: CFG-AI_FILL_CONCURRENCY
- 配置名: AI_FILL_CONCURRENCY
- 来源: env/settings
- 默认值: 3
- 消费者: paper_compose
- 控制行为: AI 补题并发
- 敏感性: medium
- 证据: backend/app/core/config.py

## CFG-LLM_MAX_CONCURRENCY
- ID: CFG-LLM_MAX_CONCURRENCY
- 配置名: LLM_MAX_CONCURRENCY
- 来源: env/settings
- 默认值: 8
- 消费者: llm
- 控制行为: LLM 并发
- 敏感性: medium
- 证据: backend/app/core/config.py

## CFG-RAG_WARMUP_ENABLED
- ID: CFG-RAG_WARMUP_ENABLED
- 配置名: RAG_WARMUP_ENABLED
- 来源: env/settings
- 默认值: true
- 消费者: main.py
- 控制行为: 启动预热
- 敏感性: low
- 证据: backend/app/core/config.py

## CFG-SEED_BASE_DATA
- ID: CFG-SEED_BASE_DATA
- 配置名: SEED_BASE_DATA
- 来源: env/settings
- 默认值: true
- 消费者: init_db
- 控制行为: 基础种子
- 敏感性: medium
- 证据: backend/app/core/config.py

## CFG-LOG_LEVEL
- ID: CFG-LOG_LEVEL
- 配置名: LOG_LEVEL
- 来源: env/settings
- 默认值: INFO
- 消费者: logger
- 控制行为: 日志级别
- 敏感性: low
- 证据: backend/app/core/config.py

## CFG-LOG_DIR
- ID: CFG-LOG_DIR
- 配置名: LOG_DIR
- 来源: env/settings
- 默认值: ./data/logs
- 消费者: logger/readiness
- 控制行为: 日志目录
- 敏感性: low
- 证据: backend/app/core/config.py

## CFG-LOG_RETENTION_DAYS
- ID: CFG-LOG_RETENTION_DAYS
- 配置名: LOG_RETENTION_DAYS
- 来源: env/settings
- 默认值: 30
- 消费者: task_jobs.clean_old_logs
- 控制行为: 日志保留
- 敏感性: medium
- 证据: backend/app/core/config.py

## CFG-LOG_TO_DB
- ID: CFG-LOG_TO_DB
- 配置名: LOG_TO_DB
- 来源: env/settings
- 默认值: true
- 消费者: logger/middleware
- 控制行为: 日志入库
- 敏感性: medium
- 证据: backend/app/core/config.py

## CFG-LOG_FILE_SINK
- ID: CFG-LOG_FILE_SINK
- 配置名: LOG_FILE_SINK
- 来源: env/settings
- 默认值: false
- 消费者: logger
- 控制行为: 文件日志
- 敏感性: low
- 证据: backend/app/core/config.py

## CFG-JOB_LOCK_LEASE_SECONDS
- ID: CFG-JOB_LOCK_LEASE_SECONDS
- 配置名: JOB_LOCK_LEASE_SECONDS
- 来源: env/settings
- 默认值: 1800
- 消费者: scheduler/job_lock
- 控制行为: 任务锁租约
- 敏感性: medium
- 证据: backend/app/core/config.py

## CFG-CRON_CLEAN_EXPIRED_EXAMS
- ID: CFG-CRON_CLEAN_EXPIRED_EXAMS
- 配置名: CRON_CLEAN_EXPIRED_EXAMS
- 来源: env/settings
- 默认值: 0 3 * * *
- 消费者: init_db
- 控制行为: 清理任务 Cron
- 敏感性: low
- 证据: backend/app/core/config.py

## CFG-CRON_DAILY_REPORT
- ID: CFG-CRON_DAILY_REPORT
- 配置名: CRON_DAILY_REPORT
- 来源: env/settings
- 默认值: 0 7 * * *
- 消费者: init_db
- 控制行为: 日报 Cron
- 敏感性: low
- 证据: backend/app/core/config.py

## CFG-CRON_CLEAN_TEMP_FILES
- ID: CFG-CRON_CLEAN_TEMP_FILES
- 配置名: CRON_CLEAN_TEMP_FILES
- 来源: env/settings
- 默认值: 0 4 * * *
- 消费者: init_db
- 控制行为: 临时附件清理 Cron
- 敏感性: low
- 证据: backend/app/core/config.py

## CFG-CRON_REVIEW_REMINDER
- ID: CFG-CRON_REVIEW_REMINDER
- 配置名: CRON_REVIEW_REMINDER
- 来源: env/settings
- 默认值: 0 8 * * *
- 消费者: init_db
- 控制行为: 复习提醒 Cron
- 敏感性: low
- 证据: backend/app/core/config.py

## CFG-REVIEW_INTERVALS
- ID: CFG-REVIEW_INTERVALS
- 配置名: REVIEW_INTERVALS
- 来源: env/settings
- 默认值: [1,2,4,7,15,30]
- 消费者: review/remediation
- 控制行为: 复习周期
- 敏感性: low
- 证据: backend/app/core/config.py

## CFG-PASS_SCORE
- ID: CFG-PASS_SCORE
- 配置名: PASS_SCORE
- 来源: env/settings
- 默认值: 60.0
- 消费者: task/grading/report
- 控制行为: 默认及格线
- 敏感性: medium
- 证据: backend/app/core/config.py

## CFG-DEFAULT_PAGE_SIZE
- ID: CFG-DEFAULT_PAGE_SIZE
- 配置名: DEFAULT_PAGE_SIZE
- 来源: env/settings
- 默认值: 20
- 消费者: API 分页
- 控制行为: 分页大小
- 敏感性: low
- 证据: backend/app/core/config.py

## CFG-MAX_PAGE_SIZE
- ID: CFG-MAX_PAGE_SIZE
- 配置名: MAX_PAGE_SIZE
- 来源: env/settings
- 默认值: 200
- 消费者: API 分页
- 控制行为: 最大分页
- 敏感性: low
- 证据: backend/app/core/config.py

## CFG-SEED_DEMO_DATA
- ID: CFG-SEED_DEMO_DATA
- 配置名: SEED_DEMO_DATA
- 来源: env/settings
- 默认值: false
- 消费者: init_db/startup_checks
- 控制行为: 演示数据
- 敏感性: high
- 证据: backend/app/core/config.py

## CFG-DEMO_LEARNING_FLOW
- ID: CFG-DEMO_LEARNING_FLOW
- 配置名: DEMO_LEARNING_FLOW
- 来源: env/settings
- 默认值: false
- 消费者: init_db
- 控制行为: 演示学习流程
- 敏感性: low
- 证据: backend/app/core/config.py

