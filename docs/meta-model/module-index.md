# 模块索引

- Output Language: zh-CN
- Status: in-progress

## MOD-backend-fastapi
- ID: MOD-backend-fastapi
- 类型: backend application
- 路径: backend/app
- 说明: FastAPI 业务服务、调度器与 API。

## SVC-auth-service
- ID: SVC-auth-service
- 所有者: MOD-backend-fastapi
- 职责: 注册、登录、JWT、密码、验证码、限流、流程注册审批编排

## SVC-knowledge-service
- ID: SVC-knowledge-service
- 所有者: MOD-backend-fastapi
- 职责: 知识点树、RAG、图谱、诊断、先修关系

## SVC-question-paper-service
- ID: SVC-question-paper-service
- 所有者: MOD-backend-fastapi
- 职责: 题库 CRUD、AI 生成、试卷组卷、版本、导出、收藏

## SVC-task-grading-service
- ID: SVC-task-grading-service
- 所有者: MOD-backend-fastapi
- 职责: 任务发布、作答、心跳、批改、成绩、错题、催交

## SVC-flow-service
- ID: SVC-flow-service
- 所有者: MOD-backend-fastapi
- 职责: 流程定义同步、实例、待办、审批、转办、催办

## SVC-agent-service
- ID: SVC-agent-service
- 所有者: MOD-backend-fastapi
- 职责: Agent 路由、LLM 调用、异步长任务、RAG、调用日志

## SVC-report-service
- ID: SVC-report-service
- 所有者: MOD-backend-fastapi
- 职责: 学生/教师/管理报表与导出

## MOD-frontend-vue
- ID: MOD-frontend-vue
- 类型: frontend SPA
- 路径: frontend/src
- 说明: Vue 3 SPA，Element Plus。

## MOD-docker-unified
- ID: MOD-docker-unified
- 类型: deployment unit
- 路径: Dockerfile, docker-compose.yml, deploy
- 说明: nginx + supervisord + uvicorn。

## MOD-ops-tooling
- ID: MOD-ops-tooling
- 类型: CI/CD and ops tooling
- 路径: tools, .github/workflows, start/manage/dev/stop scripts
- 说明: 质量门禁与部署脚本。
