# 2026-11-20 修复与发布记录

> 本日两轮发布：
> - **2.5.49** —— M6 流程引擎 + 阶段 0 镜像瘦身（下文「一」～「四」）
> - **2.5.50** —— 固定验收账号（下文「六」）
>
> 当前线上版本见 [`STATUS.md`](STATUS.md)。本文只记历史，不作「当前版本」声明。

## 本轮目标

1. 完成 M6 流程引擎 + 待办页「转办 / 催办 / 超时 / 催交考试」（M1–M6 本体落地）。
2. 阶段 0 镜像瘦身（不换栈，只减体积）。
3. 提交并推送，保持「本地 == origin/master == 镜像 BUILD_INFO == 服务器容器」四位一体。
4. 建立三个长期固定、口令不变的验收账号（管理员 / 教师 / 学生）。

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
| 本轮发布版本 | `2.5.49`（历史发布） |
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

---

## 六、固定验收账号（2.5.50）

### 目标

三个**长期固定、口令不变**的私有账号（管理员 / 教师 / 学生），用于日常使用与测试。

### 为什么要有脚本，而不是手工建号

账号是**数据**，不是代码。换环境（阶段 1 迁 PostgreSQL、开发机重建库）后账号会丢；
手工重建最容易漏绑角色 / 班级 / 授课关系，症状是「能登录但页面上什么都看不到」；
口令写在代码里会泄露，写在文档里又容易和实际不符。

所以把「账号该长什么样」固化成脚本：

- **新增** `tools/ensure_acceptance_accounts.py`（唯一真源，`ACCOUNTS` 列表定义三账号）
- **新增** `docs/ACCEPTANCE_ACCOUNTS.md`（何时用、怎么执行、口令来源、安全边界）
- **改动** `docs/OPERATIONS.md`（新增「固定验收账号」一节）、`README.md`（加一行指引）

### 脚本做的四件事

1. **幂等**：可反复执行。已存在的账号只重置口令，不重复建。
2. **建全关联**：角色 + 班级 + 授课关系一次对齐。教师绑「一年级(1)班」的「数学」
   授课关系，学生绑同一个班 —— 这是教师能看到学生的前提。
3. **环境就绪**：先跑 `init_roles` / `init_grades_subjects`（都是幂等、只增不删），
   所以全新库 / 迁库后也能一键就绪，不依赖 `SEED_DEMO_DATA` 开关。
4. **重置锁定**：`must_change_password=False`、`locked_until=None`、
   `login_fail_count=0`。前两个保证「口令固定」这个用途成立
   （否则每次登录都被拦去改密），第三个避免测试输错一次就锁 15 分钟。

口令来源优先级：`--password-file` → `ACCEPTANCE_PASSWORD_FILE` → `ACCEPTANCE_PASSWORD`。
**刻意不内置默认口令** —— 拿不到口令就报错退出。脚本只重置哈希，**不回显**明文。

### 过程中修掉的两个真实缺陷

1. **脚本按自身位置推算后端根目录** → 被 `docker cp` 进容器跑时路径指错，
   报 `ModuleNotFoundError: No module named 'app.core'`。
   改为**按「哪个目录下真的存在 `app/core/database.py`」判定**，并把容器内 `/app` 加入候选。
2. **`init_db.init_grades_subjects` 受 `SEED_BASE_DATA` 开关控制** ——
   生产该开关为 `false`（空基线），学科表不播种。
   脚本因此**不依赖既有学科**：缺学科时按本班 `grade_id` 自建
   （`edu_subject` 唯一约束是 `(grade_id, name)`，`grade_id` 非空）。

### 生产验证（SSH 进容器内实测）

三个账号在生产库已就位，口令与本地保管文件**逐字节匹配**：

| 账号 | pwd_match | status | identity | must_change | locked | 角色 | 权限点 | 班级 | 授课关系 |
|---|---|---|---|---|---|---|---:|---|---|
| `owner_admin` | True | active | sys_admin | False | None | `sys_admin` | 65 | — | — |
| `owner_teacher` | True | active | teacher | False | None | `teacher` | 28 | 一年级(1)班 | 有（数学） |
| `owner_student` | True | active | student | False | None | `student` | 16 | 一年级(1)班 | — |

真实 HTTP 登录（走完整图形验证码流程）三个账号均 `HTTP 200`、拿到 access token。
角色边界正确，不是「都能登入但权限一样」：

| 接口 | owner_admin | owner_teacher | owner_student |
|---|---|---|---|
| `/auth/profile` | 200 | 200 | 200 |
| `/edu/classes` | 200，23 个班 | 200，1 个班 | 200，1 个班 |
| `/question/questions` | 200，3093 题 | 200，2520 题 | **403** |
| `/question/papers` | 200，3 套 | 200，0 套 | **403** |
| `/task/tasks`（布置作业） | 200 | 200 | **403** |
| `/task/my/tasks`（我的作业） | 200 | 200 | 200 |
| `/system/users`（用户管理） | 200，224 人 | **403** | **403** |

### 发布信息

| 项 | 值 |
|---|---|
| 本轮发布版本 | `2.5.50`（历史发布） |
| 新增文件 | `tools/ensure_acceptance_accounts.py`、`docs/ACCEPTANCE_ACCOUNTS.md` |
| 后端运行时代码 | **无变化** —— `tools/` 与 `docs/` 均被 `.dockerignore` 排除，不进镜像 |
| 镜像 | 需重建：`VERSION` 会被 `COPY` 进镜像并烧进 `/app/BUILD_INFO`，故版本号变化即镜像内容变化 |
| commit | `862f6e220d37227fc995d42a1d409ea193b26c4d` |
| digest | `sha256:e0d14cb5f721d38d50e77912a477d0eaf85c7069c70e9b09963a97c076378511`（ghcr 与 Docker Hub 六处标签同 digest） |
| 标签 | `2.5.50` / `latest` / `sha-862f6e2` |
| 口令文件（生产） | `/opt/edu-ai-platform/.acceptance_password`（0600 root:root） |
| 口令文件（本机） | 仓库外 `E:\project\management\PRIVATE_ACCOUNTS_PASSWORD_2026-11-20.txt` |
| 生产备份 | `pre-20261120-134548-2.5.50.db`（14108 KB） |

> **为何本轮仍要重建镜像**：`tools/` 与 `docs/` 不进镜像，**后端运行时代码逐字节未变**；
> 但 `VERSION` 会被 `Dockerfile` 的 `COPY VERSION ./VERSION` 带进镜像，
> 并由 `RUN printf` 写进 `/app/BUILD_INFO`。版本号一变，镜像字节就变 ——
> 按 `docs/DELIVERY_RULES.md` 第 1 条，凡改变镜像内容的提交都必须重建并同步。
> 重建后四位一体（本地 / `origin/master` / 镜像 / 服务器）统一指向同一个 commit。

### 四位一体核验（`tools/check_four_layer.py`）

| 层 | 版本 | 指纹 | 判定 |
|---|---|---|---|
| 本地 worktree | 2.5.50 | 862f6e2 | OK（工作区干净） |
| 远端 origin/master | 2.5.50 | 862f6e2 | OK（已推送） |
| 镜像 :2.5.50 | 2.5.50 | 862f6e2 | OK（BUILD_INFO 自洽） |
| 服务器 :8081 | 2.5.50 | 862f6e2 | OK（容器 BUILD_INFO 一致） |

### 部署后复验（2.5.50 容器内实测）

- `/api/v1/health` → healthy **v2.5.50**，db=sqlite，llm=True
- `/api/v1/ready` → ready=true（database / schema / uploads / exports / logs 全 true）
- 容器 `/app/BUILD_INFO` → `version=2.5.50` / `commit=862f6e2`
- 外网 `https://592587860.xyz:8443/api/v1/health` → healthy v2.5.50
- **三个验收账号在重建后的新容器里仍能真实 HTTP 登录**（走完整图形验证码），均 HTTP 200

### 顺带修掉的巡检缺陷

`tools/check_four_layer.py` 的服务器层此前只看 commit 字面是否等于 HEAD，不等就判
「版本号相同但 commit 不同（未走发版流程）」—— 与 `docs/DELIVERY_RULES.md` 第 1 条
（**仅文档/记录类提交不需要重建镜像**）直接冲突。实际后果是每发一笔发布记录，
四层巡检就报一次漂移，而规则恰恰允许文档提交不发版；发版链路与巡检链路
给出相反结论，且巡检那条是错的。

已改为复用 `check_release_consistency.commits_missing_from_image` 的同一套
「差异是否落在会被 COPY 的路径」判据，两条链路不再各说各话：

- 差异全在 `docs/`、`tools/`、`*.md` 等不进镜像的路径 → 判 OK，并注明
  「镜像出自 `<sha>`，HEAD `<sha>` 之后只有不影响镜像内容的改动」；
- 差异含 `backend/app/`、`frontend/`、`VERSION` 等会进镜像的路径 → 仍判 DRIFT，
  并列出差异文件。

实测：`137b589→032fbbe`（只改 docs/）判不影响镜像；`e1bd821→032fbbe`（含 VERSION）
判影响镜像 —— 两种情况都能正确分流。
