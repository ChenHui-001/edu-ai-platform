# 九年义务教育学习管理系统（AI Agent 版）

> 面向中国九年义务教育阶段（小学 1-6 年级 / 初中 7-9 年级）的轻量化校内学习管理系统。
> 覆盖「教 - 学 - 练 - 考 - 评 - 改」全教学流程，内置 6 大 AI Agent 协作智能引擎。
> 单体架构 + Docker 一键部署，2 核 4G 服务器即可支撑 500 人同时在线。

---

## 功能概览

### 教学全流程
| 模块 | 能力 |
|------|------|
| 系统基础 | 注册审批、RBAC 三级权限、登录/操作/错误三类日志、定时任务、附件管理 |
| 教学资源 | 1-9 年级学科体系、多级知识点树、班级管理、题库（8 种题型）、试卷管理 |
| 学生中心 | 随机练习、模拟考试、智能复习（艾宾浩斯）、错题本、学习笔记、成绩中心 |
| 教师教学 | 出题组卷、AI 智能组卷、作业考试发布、智能批改、班级学情分析 |
| 数据报表 | 学生端（学习总览/成绩趋势/知识雷达/错题分析）、教师端（班级学情/横向对比/教学效果）、管理员端（系统全景） |

### AI Agent 能力
| Agent | 说明 |
|-------|------|
| 路由 Agent | 识别自然语言需求，自动分发到最合适的专属 Agent（LangGraph 编排） |
| 题库生成 Agent | 按知识点 / 题型 / 难度生成原创题目，自动关联知识点并入待审核库 |
| 智能组卷 Agent | 平衡知识点分布与难度结构，自动抽题并输出难度分析与覆盖报告 |
| 智能批改 Agent | 客观题本地精准判分，主观题语义理解评分 + 错误点标注 + 个性化评语 |
| 学习规划 Agent | 分析学情定位薄弱知识点，生成每日学习清单与艾宾浩斯复习计划 |
| 答疑助教 Agent | RAG 知识库检索 + 题目解析 + 知识点讲解 + 同类练习推荐 |
| 笔记整理 Agent | 提炼核心知识点，生成结构化大纲与思维导图 |

> **降级保障**：未配置大模型 API Key 时，所有 Agent 自动切换为规则引擎，功能不中断。

---

## 技术栈

| 层次 | 技术选型 |
|------|---------|
| 后端框架 | FastAPI + Uvicorn（异步高性能 + 自动生成接口文档） |
| ORM / 数据库 | SQLAlchemy 2.0 + SQLite（可平滑切换 PostgreSQL） |
| 认证鉴权 | PyJWT + RBAC 三级权限（菜单 / 操作 / 数据） |
| AI Agent | LangChain + LangGraph + ChromaDB（嵌入式向量库） |
| 大模型 | 通义千问 / DeepSeek / OpenAI 兼容协议，支持本地 Ollama 私有化 |
| 定时任务 | APScheduler（无需额外中间件） |
| 日志 | Loguru（切割归档）+ 数据库审计日志 |
| 前端 | Vue 3 + Vite + Element Plus + Pinia + ECharts |
| 部署 | Docker + Docker Compose + Nginx（前后端一体镜像） |

---

## 快速开始

> **本地体验？直接双击 `start.bat`**（Docker 部署，macOS/Linux 用 `./start.sh`）；
> 写代码调试用 `dev.bat`（后端 :8000 + 前端 :5173，无 Docker）。
> 脚本会自动检查环境、生成 `.env` 与随机 `SECRET_KEY`、按需重建镜像并启动，最后自动打开浏览器。
> 完整说明见 [docs/QUICKSTART.md](docs/QUICKSTART.md)。

### 方式一（最快）：直接拉取已发布镜像

```bash
docker pull nanpo/edu-ai-platform:1.0.43
docker run -d --name edu-platform -p 8080:80 \
  -e SECRET_KEY="$(python -c 'import secrets;print(secrets.token_urlsafe(48))')" \
  -e DEBUG=false \
  -e SEED_DEMO_DATA=true \
  -v "$(pwd)/data:/app/data" \
  --restart unless-stopped \
  nanpo/edu-ai-platform:1.0.43

# 访问 http://localhost:8080
# 默认账号 admin / Admin@123456
```

镜像内含 nginx + FastAPI + Vue3 静态资源，单容器提供全部服务。
健康检查：`curl http://localhost:8080/api/v1/health`

> **镜像仓库说明**：本地发布通道推送到 Docker Hub `nanpo/edu-ai-platform`；
> CI（`.github/workflows/docker-publish.yml`）发布到 GitHub Container Registry
> `ghcr.io/chenhui-001/edu-ai-platform`。两个通道发布同一份 commit 的镜像，
> 可用镜像内 `/app/BUILD_INFO` 的 commit 指纹核对；拉取前先确认本次发布走的是
> 哪个通道（Docker Hub 不可达时可改用 ghcr 地址）。

**最低配置**：2 核 4G / 40GB 磁盘 | 镜像体积 ≤ 2GB | 启动 ≤ 30 秒

### 方式二：Docker Compose 部署

```bash
# 1. 克隆项目
git clone https://github.com/ChenHui-001/edu-ai-platform.git
cd edu-ai-platform

# 2. 配置环境（可选：不填 LLM_API_KEY 也能跑，功能自动降级）
cp .env.example .env
# 编辑 .env，设置 SECRET_KEY 和 LLM_API_KEY

# 3. 启动
docker compose up -d --build

# 4. 访问
# 系统首页：http://localhost:8080
# 接口文档：http://localhost:8080/docs
```

### 方式三：本地开发

```bash
# 后端
cd backend
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000

# 前端（另开终端）
cd frontend
npm install
npm run dev
```

---

## 默认账号

| 角色 | 账号 | 密码 |
|------|------|------|
| 系统管理员 | `admin` | `Admin@123456` |
| 教师（演示） | `teacher1` ~ `teacher4` | `Teacher@123` |
| 学生（演示） | `stu7*` / `stu1*` | `Student@123` |

> **安全提示（v1.0.42 起）**：
> - 生产环境必须在 `.env` 中显式设置至少 32 位随机 `SECRET_KEY`，否则应用会拒绝启动；`DEBUG` 请保持 `false`。
> - 默认账号仅用于本地体验/首次初始化，部署后请立即修改管理员口令；登录页默认不再展示演示账号口令（`VITE_SHOW_DEMO_ACCOUNTS=false`）。
> - 生产环境请设置 `SEED_DEMO_DATA=false`：空库不会创建 teacher1/stu731 等已知口令演示账号，只保留 admin 与基础数据。
> - 详细修复记录见 [docs/FIX_RECORD_2026-10-22.md](docs/FIX_RECORD_2026-10-22.md)。
> - 交付规则：每次运行时代码提交后必须同步 Docker Hub（版本标签 + latest + sha），见 [docs/DELIVERY_RULES.md](docs/DELIVERY_RULES.md)。

---

## 配置大模型

不配置时系统正常运行（规则引擎降级），配置后 AI 能力完整启用。

**通义千问**
```env
LLM_PROVIDER=qwen
LLM_API_KEY=sk-xxxxxxxxxxxxxxxx
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen-plus
```

**DeepSeek**
```env
LLM_PROVIDER=deepseek
LLM_API_KEY=sk-xxxxxxxxxxxxxxxx
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL=deepseek-chat
```

**本地私有化（Ollama）** —— 学生数据不出域
```env
LLM_PROVIDER=ollama
LLM_API_KEY=ollama
LLM_BASE_URL=http://localhost:11434/v1
LLM_MODEL=qwen2:7b
```

---

## 项目结构

```
edu-ai-platform/
├── backend/
│   ├── app/
│   │   ├── agents/          # AI Agent 层（6 大 Agent + LangGraph 编排 + RAG）
│   │   ├── api/v1/          # REST API 路由
│   │   ├── core/            # 配置、数据库、安全、异常、日志
│   │   ├── models/          # SQLAlchemy 模型
│   │   ├── services/        # 业务服务（认证、批改、调度、任务、初始化）
│   │   ├── middleware/      # 审计中间件
│   │   └── main.py          # 应用入口
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   └── src/
│       ├── api/             # API 封装
│       ├── components/      # 公共组件
│       ├── layout/          # 主布局
│       ├── router/          # 路由与权限守卫
│       ├── store/           # Pinia 状态
│       └── views/           # 页面（admin / teacher / student / agent / login）
├── deploy/
│   ├── nginx/default.conf   # Nginx 配置
│   └── supervisord.conf     # 进程管理
├── docs/                    # 部署与运维文档
├── Dockerfile               # 多阶段构建（前后端一体）
├── docker-compose.yml
└── README.md
```

---

## 核心设计

### 权限体系
「角色 - 权限 - 用户」三级 RBAC，从三个维度管控：
- **菜单权限**：控制导航入口可见性，无权限直接隐藏
- **操作权限**：控制按钮级增删改查导出，无权限置灰
- **数据权限**：严格数据隔离 —— 教师仅见授课班级，学生仅见本人

预置 5 种角色：系统管理员（全校）、年级管理员（本年级）、任课教师（授课班级）、学生（个人）、访客（无业务数据）。

### AI 生成内容治理
- AI 生成的题目**一律进入待审核库**，管理员审核通过后方可上架
- 批改以题库标准答案为准，AI 仅做辅助讲解与建议评分，教师可一键采纳或手动覆盖
- 答疑采用「题库 RAG」方案，检索到相关内容才作答，降低幻觉风险
- 所有 AI 调用记录耗时、Token、是否降级，支持审计追溯

### 性能保障
- 客观题判分完全本地计算，不调用大模型，100 人考试自动批改 < 1 分钟
- SQLite 开启 WAL 模式 + 连接池
- 答题过程本地草稿保存 + 定时心跳同步，切屏次数可追踪

---

## 文档

- [部署指南](docs/DEPLOYMENT.md) —— 生产环境部署、反向代理、HTTPS、备份
- [API 文档](http://localhost:8080/docs) —— 启动后在线查看
- [开发指南](docs/DEVELOPMENT.md) —— 本地开发、代码规范

---

## 许可

MIT License
