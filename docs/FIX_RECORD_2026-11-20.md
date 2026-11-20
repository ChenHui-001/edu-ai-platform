# 2026-11-20 修复与发布记录（2.5.49）

## 本轮目标

1. 完成 M6 流程引擎 + 待办页「转办 / 催办 / 超时 / 催交考试」（M1–M6 本体落地）。
2. 阶段 0 镜像瘦身（不换栈，只减体积）。
3. 提交并推送，保持「本地 == origin/master == 镜像 BUILD_INFO == 服务器容器」四位一体。

## 一、M6 流程引擎（功能）

### 后端（新增）

| 文件 | 行数 | 职责 |
|---|---:|---|
| `backend/app/models/flow.py` | 170 | 5 张表：`flow_definition` / `flow_instance` / `flow_task` / `flow_history` / `flow_transfer` |
| `backend/app/services/flow_engine.py` | 1048 | 引擎主体：`start` / `claim` / `approve` / `reject` / `return_to` / `transfer` / `urge` / `overdue_tasks` / `set_deadline` 等 22 个公开方法 |
| `backend/app/services/flow_escalation.py` | 214 | 超时升级 mixin（与引擎解耦，避免循环导入） |
| `backend/app/services/flow_constants.py` | 69 | 常量单点（动作码 / 角色码 / 催办冷却） |
| `backend/app/services/flow_orchestration.py` | 118 | 编排层 |
| `backend/app/services/rule_engine.py` | 421 | M3 规则求值（`simpleeval` + 投影白名单 + 对抗防护） |
| `backend/app/services/task_urge.py` | 73 | 催办服务 |
| `backend/app/api/v1/flow.py` | 181 | 15 个端点 |
| `backend/app/api/v1/task_urge.py` | 132 | 2 个端点 |
| `backend/app/schemas/flow.py` | 67 | 请求/响应模型 |
| `backend/migrations/versions/0005_flow_engine.py` | — | 流程引擎建表 |
| `backend/migrations/versions/0006_flow_transfer_urge.py` | — | 转办 + 催办字段 |

### 本体（M1 / M2 / M6）

- `backend/app/ontology/m3-rule-model.yaml`（20451 B）
- `backend/app/ontology/m6-flow-model.yaml`（26071 B）
- `audit-reports/ontology-inventory/{m1,m2,m6,mu}` 同步

### 前端（新增）

- `frontend/src/views/admin/FlowTodo.vue`（602 行）——四标签页：我的待办 / 已办 / 我发起的 / 逾期
- `frontend/src/components/ExamUrgeDialog.vue`（148 行）——催交考试弹窗
- `frontend/src/utils/flowTodo.js`（177 行）+ 单测 `__tests__/flowTodo.test.js`

### 修掉的三个实质缺陷

1. **转办越权**：缺操作人角色校验 → 补齐。
2. **timeout 无数据源**：deadline 从不赋值 → 逾期查询永远为空 → 补 `set_deadline` 与超时升级链路。
3. **迁移 nullable 不一致**：0006 与模型定义冲突 → 对齐。

## 二、阶段 0：镜像瘦身

| 镜像 | 瘦身前 | 瘦身后 | 节省 |
|---|---:|---:|---:|
| `unified`（生产交付物） | 2.01GB | **1.39GB** | -620MB (-31%) |
| `backend`（纯后端） | 1.59GB | **1.32GB** | -270MB (-17%) |

剔除项与「不能删」的依赖图依据见 [`IMAGE_SLIMDOWN_2026-11-20.md`](IMAGE_SLIMDOWN_2026-11-20.md)。

### 顺带修掉的三个生产缺陷

1. **`rule_engine.py` 依赖 `simpleeval` 但 `requirements.txt` 未声明** —— 生产镜像里该包不存在，
   任何触达规则引擎的请求都会 `ImportError`。本地 venv 因被顺带安装才没暴露。
2. **`backend` 阶段未预置 ONNX 模型** —— 该镜像首次向量检索要现场下载 79MB，弱网必然超时。
3. **`ENV CHROMA_CACHE_DIR` 完全无效** —— chromadb 1.5.9 只认 `Path.home()`；
   真正生效的开关是 `HOME`（已设 `HOME=/home/app`）。

## 三、验证记录

| 层 | 结果 |
|---|---|
| 静态门禁 `tools/check_*`（20 项） | 全绿 |
| 功能验证 `tools/verify_*`（10 项） | 全绿 |
| 后端 QA 套件（3 个） | 全绿 |
| `ruff check backend/app tools` | 全绿（本轮修了 20 处 F401/F841） |
| 前端 vitest | 187/187 通过 |
| 前端 eslint / build / check:bundle | 通过 |
| 冒烟（导库 + create_all + 路由数） | 339 路由 / 63 表（门槛 250/45） |
| 容器实机 | `/api/v1/health` healthy、`/api/v1/ready` ready、前端 HTTP 200 |
| 浏览器回归（26 步） | 含转办 / 催办 / 催交考试 / 逾期 / 窄屏，全过，无 console 错误 |
| 镜像内 M6 代码核对 | 10 个后端文件 SHA256 逐字节与工作区一致；本体 YAML、迁移一致 |

## 四、发布信息

| 项 | 值 |
|---|---|
| 版本 | 2.5.49 |
| commit | `ae76330a3130128db2ff98192d9cc396c043e81c` |
| 镜像 | `ghcr.io/chenhui-001/edu-ai-platform:2.5.49`（CI 多架构 amd64）+ `nanpo/edu-ai-platform:2.5.49` |
| digest | `sha256:bc7e3cd260077cbce138b86995e812334efe5f0bcbf6df5d8c0c0e07e4b8ba1a`（ghcr 与 Docker Hub **逐字节一致**） |
| 标签 | `2.5.49` / `latest` / `sha-ae76330`（三处同 digest） |
| 镜像体积 | 1.39GB（2.01GB → 1.39GB，-31%） |
| 生产备份 | `pre-20261120-110528-2.5.47.db`（13960 KB，容器内 sqlite3 backup API） |

### 提交历史（本轮 4 个提交）

| commit | 内容 |
|---|---|
| `a11284d` | feat(flow): M6 流程引擎 + 阶段 0 镜像瘦身 |
| `f7960b2` | fix(ci): 现状卡「镜像体积」改读 `IMAGE_SIZE` 文件 |
| `2f91cc6` | fix(meta-model): 修复被写成字面 `n` 的换行 |
| `ae76330` | fix(release): `check_release_consistency` 显式 UTF-8 解码 |

### 四位一体核验（`tools/check_four_layer.py`）

| 层 | 版本 | 指纹 | 判定 |
|---|---|---|---|
| 本地 worktree | 2.5.49 | ae76330 | OK（工作区干净） |
| 远端 origin/master | 2.5.49 | ae76330 | OK（已推送） |
| 镜像 :2.5.49 | 2.5.49 | ae76330 | OK（BUILD_INFO 自洽） |
| 服务器 :8081 | 2.5.49 | ae76330 | OK（容器 BUILD_INFO 一致） |

### 生产上线核验（SSH 进容器内实测）

- `/api/v1/health` → healthy v2.5.49，db=sqlite，llm=True
- `/api/v1/ready` → ready=true
- 容器内 `app.openapi()` → 339 路由 / 63 表；**16 个 M6 端点**全部注册
- `FlowEngine` 公开方法 23 个
- 数据库 5 张 flow 表已建出：`edu_flow_definition` / `edu_flow_instance` /
  `edu_flow_task` / `edu_flow_history` / `edu_flow_transfer`（空表，正常）
- 前端 dist 含 `FlowTodo-BGz_d02i.js` / `ExamUrgeDialog-DxR8gtl1.js`
- 容器内 `/app/IMAGE_SIZE` = 1.39GB，与镜像实测一致

> 注：生产的 `alembic_version` 停在 `0002_math_taxonomy` 是**既有设计** ——
> 运行时走 `create_all` + 幂等补列，不自动跑 Alembic（2.5.47 同样如此）。
> `check_alembic_sync` / `check_migration_columns` 两道门禁均通过，
> 迁移链与模型、create_all 三者一致。

## 五、后续

- **阶段 1**：数据库迁 PostgreSQL（`psycopg2` 已在依赖里，需清 SQLite 方言债）。
- **阶段 0 遗留**：ONNX 模型 90MB + onnxruntime 78MB 仍在镜像里；
  要彻底去掉必须换 embedding 后端（已实测 MiniMax `/v1/embeddings` 可用，
  参数名 `texts`、返回 `vectors`，**非 OpenAI 协议**），建议与阶段 1 的 pgvector 一起做。
