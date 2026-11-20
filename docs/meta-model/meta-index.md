# 元模型索引

- Output Language: zh-CN
- 模式: 全量基线 B
- 目标仓库: E:\project\management\edu-ai-platform
- 版本基线: VERSION=2.5.49，工作树含未提交变更
- 生成时间: 2026-11-20
- 状态: in-progress

## 范围
- 后端: backend/app
- 前端: frontend/src
- 部署与运维: Dockerfile, docker-compose.yml, deploy, start/manage/dev 脚本, tools, GitHub Actions
- 本体与种子: backend/app/ontology, seeds, data
- 数据库: SQLite WAL，模型与迁移是当前事实源，DDL 仅作交叉证据

## 排除
- .git, .venv, node_modules, dist, build, ui_shots, logs, data 运行数据， __pycache__ 等生成或运行产物
- E:\project\management 根下与运行系统无关的运维容器目录
- 敏感账号文件与真实密钥值，不复制到文档
- frontend/node_modules 与 package-lock 具体依赖树

## 文档
- 见 docs/meta-model 下方 24 个核心文件与两个子目录。
- 全局状态保持 in-progress，直到 B9 自动与人工校验 PASS 且 ERROR=0。

