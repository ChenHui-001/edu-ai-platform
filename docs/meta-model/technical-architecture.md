# 技术架构

- ID: SYS-edu-ai-platform
- Output Language: zh-CN
- Status: in-progress

## 架构类型
- 单体 B/S 系统，前后端同容器部署。
- 后端 FastAPI + SQLAlchemy 2.0（同步） + SQLite WAL。
- 前端 Vue 3 + Vite + Element Plus。
- 部署 Docker 单镜像 unified，容器内 nginx + supervisord。

## 关键链路
- 前端 axios -> deploy/nginx -> FastAPI /api/v1 -> Service -> SQLAlchemy -> SQLite。
- APScheduler -> JOB_HANDLERS -> Service -> DB / Notification / Export。
- Agent -> LLM Client -> ChromaDB / LLM Provider，失败时规则引擎降级。
- 导出与报表 -> sys_agent_job / sys_job_execution_log -> export_job -> 文件。
