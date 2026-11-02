# 架构评估报告 · 新芽学堂（edu-ai-platform）

> 评估对象：`E:/project/management/edu-ai-platform`，版本 **2.2.19**（master @ ec3f013）
> 评估日期：2026-11-02
> 评估方法：全量静态扫描（代码规模、端点、模型、依赖、CI 配置）+ 关键链路代码精读（认证、组卷、判分、Agent 编排、LLM 熔断、前端请求层）
> 局限：未做压测与线上流量观测，并发相关结论为代码层推断；未审计历史提交。

---

## 0. 结论摘要

**一句话定性：这是一个"工程纪律显著高于同规模平均水平"的单体应用，主要债务不在代码写法，而在三处结构性缺口——没有后端自动化测试、没有请求契约层、没有版本化数据库迁移。**

| 维度 | 评分 | 判断 |
|---|---|---|
| 架构一致性（设计 vs 实现） | 7.0 / 10 | 分层意图清晰，但路由层承担了 70% 业务逻辑，服务层被架空 |
| 安全性 | 8.5 / 10 | 双令牌 + 吊销落库 + fail-closed + 端点鉴权覆盖 96.3%，少数公开端点均属设计需要 |
| 可测试性 | **3.0 / 10** | 后端 0 个单测；核心算法（分数分配、难度归一、判分）无任何自动化保护 |
| 可维护性 | 6.5 / 10 | 函数粒度健康（911 函数，仅 18 个 ≥100 行），但文件粒度粗（5 个 API 文件 >1200 行） |
| 可观测性 | 6.0 / 10 | 有登录/操作/错误/AI 调用四类日志表，无 metrics / trace / 告警 |
| 部署成熟度 | 8.5 / 10 | 多阶段构建、四道发版闸门、健康检查、命名卷、非 root 运行 |
| 演进弹性 | 5.0 / 10 | 单体 + SQLite 单写者 + 单 worker + daemon 线程任务，横向扩展路径为零 |

**综合：7.0 / 10。** 当前规模（校内单点部署、数百用户）下这套架构是**匹配**的，不是过度设计也不是欠设计；真正的风险是当并发、团队人数、数据量任一维度上一个台阶时，会同时撞上"无测试网 + 无契约 + 无迁移"三堵墙。

---

## 1. 架构现状总结

### 1.1 系统画像（实测数据）

| 指标 | 数值 | 说明 |
|---|---|---|
| 后端代码 | 32,082 行 / 84 文件 | `backend/app` 下，不含工具脚本 |
| 前端代码 | 22,943 行 / 68 文件 | 52 个 `.vue` + 16 个 `.js`，无 TypeScript |
| 数据表 | **49 张** | `edu_*` 29 张 + `sys_*` 20 张 |
| API 端点 | **272 个**（+2 个基础端点） | 21 个路由模块，90% 集中在 6 个文件 |
| 后端函数 | 911 个 | 仅 18 个 ≥100 行，1 个 ≥200 行（`import_knowledge` 240 行） |
| AI Agent | 8 个 | 统一 `BaseAgent` 契约 + 规则引擎降级 |
| 部署形态 | 单镜像 unified | nginx + supervisord + uvicorn `--workers 1` |

### 1.2 运行时拓扑

```
客户端 ──HTTP──> nginx:80 ──/api/v1──> uvicorn:8000 (1 worker, 同步端点)
                   │                        │
                   │ 静态资源（SPA）          ├─ SQLite (WAL, busy_timeout=5s)
                   │                        ├─ Chroma（本地向量库 + ONNX 嵌入）
                   │                        ├─ APScheduler（进程内，DB 锁去重）
                   │                        └─ daemon Thread（AI 长任务）
                   └─ /docs 仅 DEBUG=true 开放
```

关键事实：**没有反向依赖外部服务**。没有 Redis、没有消息队列、没有对象存储、没有独立数据库进程。这是它能"2 核 4G 一键起"的原因，也是它的扩展上限。

### 1.3 分层设计的实际形态

设计意图（架构文档 §3）与代码实测存在偏移：

| 层 | 设计职责 | 实际状况 | 证据 |
|---|---|---|---|
| 路由层 | HTTP 契约 + 鉴权注入 | **承担了大量业务逻辑与直接 SQL** | API 层 437 处 `db.query/db.execute/select`；`services` 仅被 API 引用 40 次 |
| 业务层 | 核心逻辑 + 事务边界 | 只在"重"域存在（组卷/判分/导出/LLM），CRUD 域基本空心 | `services/` 22 个文件，5 个文件 >20KB |
| 契约层 | Pydantic 请求/响应模型 | **基本不存在**：`schemas/` 空目录，94 处 `Dict[str, Any] = Body(...)` | `grep "class .*BaseModel"` 仅 8 处 |
| 模型层 | ORM 定义 | 健康：49 表 / 86 外键 / 184 处索引与唯一约束 | `models/*.py` |
| 数据层 | 连接、PRAGMA、迁移 | 连接层扎实；迁移层是手写补列清单（38 项） | `core/database.py`、`core/db_migrations.py` |

> 准确地说，这不是"分层崩塌"，而是 **"胖路由 + 瘦服务"**：每个端点函数本身不臃肿（中位数很小），但业务编排、权限判断、SQL 组装、响应拼装全挤在同一个文件里。后果不是读不懂，而是 **无法在不启动 HTTP 的情况下测试任何业务规则**。

### 1.4 模块划分

按业务域划分是清晰的，21 个路由模块与 7 个视图域（admin / teacher / student / agent / login）一一对应。但存在一个"加法式演进"留下的结构：**同一资源被多个文件操作**。

| 资源前缀 | 涉及文件 | 风险 |
|---|---|---|
| `/question` | `question.py`(1792) + `question_ai.py`(810) + `paper_ai.py`(644) + `paper_compose.py`(1893) + `exam_standard.py`(539) | 5 个文件、5678 行共管一个域，改一处需跨 5 文件确认 |
| `/edu` | `edu.py`(1198) + `knowledge.py`(1671) + `knowledge_ai.py`(423) | 3 个文件共管，知识点与教学资源边界模糊 |
| `/task` + `/grading` | `task.py`(1237) + `grading.py`(583) | 作答与判分分离，事务边界跨文件 |

这种拆法的**好处**是每次新增功能都不动存量文件（契约零破坏），**代价**是认知负担随版本线性增长。当前 2.2.19 已经到"改组卷要开 5 个文件"的临界点。

---

## 2. 技术栈选型与合理性

| 层次 | 选型 | 评价 | 匹配度 |
|---|---|---|---|
| Web 框架 | FastAPI 0.115 + Uvicorn | 正确。自动 OpenAPI、依赖注入适合做 RBAC | ★★★★★ |
| ORM | SQLAlchemy 2.0（同步） | 正确。**0 个 `async def` 端点是刻意选择**：同步 ORM 塞进事件循环才是灾难，交给 threadpool 是标准解法 | ★★★★☆ |
| 数据库 | SQLite + WAL | 当前规模正确（零运维、单文件备份）；单写者是天花板 | ★★★☆☆ |
| 认证 | PyJWT 双令牌 + PBKDF2 | 正确且实现严谨（吊销落库、fail-closed）；PBKDF2 10 万轮在现代硬件偏低但可接受 | ★★★★☆ |
| AI 编排 | LangChain + LangGraph + Chroma | **部分过度**：LangGraph 只用了 2 节点线性图（route→dispatch），等价于一次分类调用；LangChain 只用了 `ChatOpenAI.invoke` | ★★☆☆☆ |
| 定时任务 | APScheduler + 自建 DB 锁 | 单机正确，`JOB_LOCK_LEASE_SECONDS=1800` 配合"补齐式扫描"handler 是经过推导的设计 | ★★★★☆ |
| 前端 | Vue 3 + Vite 6 + Element Plus + Pinia | 正确。按需引入 + manualChunks 分包做得比多数项目细 | ★★★★☆ |
| 前端语言 | JavaScript（无 TS） | 小团队提速的合理取舍，但与"无契约层"叠加后放大了前后端漂移 | ★★★☆☆ |
| 部署 | 多阶段 Docker + ghcr | 成熟。四道发版闸门（VERSION / commit / 镜像标签 / 健康检查）+ BUILD_INFO 烧录，超出同规模项目水平 | ★★★★★ |

**三点选型层面的实质问题：**

1. **`langgraph` / `langchain` 的收益与体重不匹配。** 编排图只有两个节点、两条边、无条件分支：意图分类 → 分发。这层抽象带来的是"把 `db` Session 塞进 TypedDict state"这种反模式，而不是多步推理能力。真正的多步编排（工具调用循环、反思、重试）并未使用。建议保留但明确其定位为"兼容层"，不要在此基础上继续叠加图节点。

2. **`EMBEDDING_MODEL = "text-embedding-3-small"` 是死配置。** 全仓除 `config.py` 定义外**零引用**；实际向量化走 Chroma 默认的本地 ONNX `all-MiniLM-L6-v2`。运维改这个值不会有任何效果——这是"配置幻觉"，比没有配置更危险。

3. **`alembic==1.14.0` 在依赖里但从未初始化**，实际迁移靠 38 项手写 `ALTER TABLE` 清单。僵尸依赖本身无害，但它掩盖了"我们以为有迁移体系"的错觉。

---

## 3. 核心功能实现方案评估

### 3.1 认证授权（评分 A-）

链路：`HTTPBearer → decode_token(token, db) → 吊销检查 → 用户加载 → 强制改密拦截 → 角色/权限点/数据范围`。

值得肯定的三个决策：
- **fail-closed 的 `decode_token`**：不传 `db` 直接拒绝，而不是静默跳过吊销检查。这堵住了"某个依赖忘传 db → 登出后 token 仍有效"的整类漏洞。
- **验证码开关单向收紧**：`CAPTCHA_ENFORCED=false` 只允许"不传"，一旦传了就必须校验通过。不存在"关开关=空操作"的降级路径。
- **`DataScope` 把"数据范围"显式建模**：`None` 表示不受限、空列表表示无授权，且注释明确警告"绝不能用 None 表示无年级"。

端点鉴权覆盖率实测 **262/272 = 96.3%**，10 个未覆盖端点全部是设计上的公开端点（login/register/captcha/refresh/logout/forgot/reset/version/classes-public/public-upload）。这是本次评估中**最健康的一项指标**。

待改进：`get_current_user` 每请求 1 次用户查询 + roles(selectin) + roles.permissions(selectin)，即每请求 **≥4 次 SQL**。272 个端点全量叠加，在 SQLite 上是可测量的固定开销。用户权限快照适合放进程内 TTL 缓存（现有 `security_cache` 表可复用，或加 `lru_cache` + 版本号失效）。

### 3.2 标准组卷 V3（评分 A-）

`paper_compose_service.py` 是全项目设计最克制的一块：

- **纯函数式**：`compose()` 不 commit、不写库，只返回计划结构，预览与保存走同一条路径。
- **整数化难度配比**：`DEFAULT_DIFFICULTY = {"easy":70,"medium":20,"hard":10}` 百分制，配合 `split_by_difficulty` 用 `round()` 补余数，避免旧实现 `int(0.3)=0` 导致恒抽 0 题。
- **分数网格分配**：`_distribute_on_grid` / `_rescale_scores` 把分值约束到题型的步长网格（如单选 2 分/格），再 `_renumber` 重排大题号。

**这是最该有单测的模块，却是 0 单测覆盖的模块。** 难点在于它同时要满足"总分精确等于目标值""每题分值在网格上""题量不变"三个约束，属于典型的约束满足问题——任何一次"微调"都可能悄悄破坏其中一个，而 39 个 verify 脚本只能验证"某条路径能跑通"，不能验证"所有配比组合都不丢分"。

### 3.3 判分与交卷（评分 B+）

关键设计正确：**`save_answers` 在调用 LLM 前主动 `db.commit()` 释放 SQLite 写锁**。注释记录得很清楚：若事务持有 RESERVED 锁去等 60s 的模型响应，审计中间件、心跳、其他学生交卷会全部等满 `busy_timeout` 后报 `database is locked`。

这本质上是"用业务一致性换并发可用性"的取舍：作答先落库、判分可重试。方向正确，但**代价是部分失败状态**——若判分阶段抛异常，作答已提交而分数未生成，需要靠"重算"接口兜底。当前有 `finalize_submission` 重算路径，可接受。

### 3.4 AI 长任务（评分 C+）

机制：`POST /agent/jobs` → 写 `AgentJob(status=pending)` → `threading.Thread(daemon=True)` 执行 → 前端轮询。

已知的三个补丁都在：
- 读时判定 `effective_status`（前端立刻看到超时，不等重启）
- 启动收割 `reap_orphan_jobs`（进程重启后清理脏状态）
- 宽限期 600s > 判据 300s（避免误杀慢任务）

但这是**"没有队列的队列"**：任务状态与执行绑定在同一进程生命周期，重启即丢执行、只留一条需要人工重试的记录。补齐手法已经很到位，架构层面仍属于"用补丁模拟缺失的基础设施"。

### 3.5 LLM 调用与熔断（评分 A）

`services/llm_breaker.py` 是全项目工程质量最高的一份代码，六个"写错了不报错、只静默失效"的坑全部被识别并注释：

| 坑 | 处理 |
|---|---|
| 用 `monotonic()` 做跨进程时间比较 | 改绝对时间 `now_local()`，且不与 `CURRENT_TIMESTAMP` 混用 |
| 只有 DB 状态 → 同请求内 6 次 401 原样重试 | 加进程内镜像（立刻生效）+ DB（跨进程） |
| 读失败当"已熔断" | fail-open，旁路状态坏了不反噬主流程 |
| rate_limit 覆盖 auth 熔断 | UPSERT 带 `WHERE kind != 'auth'` |
| 各进程 `streak += 1` 互相覆盖 | 单条 SQL 原子自增 |
| `clear` 顺手清 auth | auth 只允许管理员 `reset_all()` |

**唯一的结构性隐患**：`client.invoke()` 是同步阻塞调用（timeout 60s，生产 120s），跑在 FastAPI threadpool 线程里。threadpool 默认 40 线程，若 10 个用户同时触发 AI 出题且各自等待 60s，就吃掉 25% 的线程池——**非 AI 接口（登录、查题、交卷）会跟着变慢**。目前靠 `AGENT_RATE_LIMIT_PER_MIN=12`（按用户）限流，但没有**全局并发上限**。

---

## 4. 代码组织与质量

### 4.1 量化画像

| 指标 | 数值 | 判定 |
|---|---|---|
| 后端函数总数 | 911 | — |
| ≥100 行函数 | 18（2.0%） | **健康**（业界经验阈值约 5%） |
| ≥200 行函数 | 1 | 健康 |
| `except Exception` | 116 处 | 偏多，但多数带日志与降级理由 |
| TODO / FIXME / HACK | **2 处** | 异常干净（债务被写进注释而非标记） |
| 空 `schemas/` 目录 | 1 | 契约层缺位的直接证据 |
| 单文件最大 | 2037 行（`KnowledgeManage.vue`） | 前端主要痛点 |
| 公共组件 | **3 个**（EChart / PomodoroTimer / VersionInfo） | 52 个视图共享 3 个组件，复用率过低 |

**一个反直觉的结论**：这个项目的代码**不是"屎山"**。函数粒度、命名、异常分层都在正常水准之上。它的债务集中在**文件与层的边界**，而不是**语句与函数内部**——这意味着重构成本比典型遗留系统低得多，主要工作是"搬家"而非"重写"。

### 4.2 显著优点：注释记录"为什么"，而不是"是什么"

`config.py`、`database.py`、`llm_breaker.py`、`main.py`、`request.js` 的注释密度极高，且写的是**决策依据与反例**：

- 为什么启动钩子要用 `flock` 而不是 DB 锁表："建表之前还没有表可锁 —— 锁必须比被保护的操作更早存在"
- 为什么 `LOG_FILE_SINK` 默认关闭：多 worker 下 `PermissionError` 会被 loguru 吞掉，"日志看起来没问题、只是少了几个进程的"
- 为什么 `res.data.data` 要全站扫描："曾在线 18 文件 52+ 处踩坑"

这种注释的维护成本高，但**它把"踩坑记忆"从个人经验变成了团队资产**。这是本项目最被低估的竞争力，也是新人上手成本低的主要原因。

### 4.3 工程门禁：超出同规模项目水平

| 门禁 | 拦截的问题 |
|---|---|
| `check_hardcoded_host` | 测试写死 `localhost:8000`，换端口即假失败 |
| `check_weak_assertion` | `assert True` / `assert resp` 这类恒真断言 |
| `check_time_contract` | CI(UTC) 与容器(Asia/Shanghai) 时区耦合 |
| `check_model_fk` | 把模型返回的 id 直接写外键 → 整批 INSERT 失败 |
| `lint_gate` | 只启用 F/E9（真缺陷），不掺风格 |
| `scan_vue_refs` | 模板引用未定义标识符 → 整页白屏 |
| `scan_vue_dup` | replace_all 误操作 → 两个同名按钮 |
| `check_data_data` | `res.data.data` 恒 undefined → 列表空 |
| `check_gen_data_determinism` | 测试数据两次生成指纹不一致 |

一个值得警惕的细节：`lint_gate` 的注释明确写了"不启用 E501/I001，否则一次接入就几百条告警，团队会直接关掉"。这是**对门禁可持续性的正确判断**——比"一把梭全开然后被绕过"成熟。

### 4.4 质量短板

1. **后端 0 单测。** CI 里三个 job（backend / frontend / docker）跑的是编译、静态门禁、导入建表、前端构建与 3 个 vitest 文件。**没有任何一个断言覆盖业务规则**。`docs/` 下 39 个 `verify_*.py` 是手工脚本，不在 CI 中执行。
2. **请求契约缺失。** 94 处 `Dict[str, Any] = Body(...)` 意味着：字段拼错不会 422、类型错误到 SQL 层才炸、OpenAPI 文档里请求体是 `{}`。前后端契约全靠人工记忆与文档同步（`docs/QUESTION_BANK_V2.md` 等）。
3. **文档漂移。** `docs/架构设计文档.md` 标称"18 个路由模块 / 198 个端点 / 2.0.4"，实际为 21 个模块 / 272 端点 / 2.2.19。漂移本身不致命，但它让"读文档评估系统"这条路失效——本次评估不得不全程以代码为准。
4. **前端复用率低。** 3 个公共组件对应 52 个视图；分页、导出、权限按钮、弹窗确认这四类逻辑在各视图重复实现。`KnowledgeManage.vue` 单文件 2037 行（模板 742 行 + 脚本约 1290 行），是典型"一个页面长成一个应用"。

---

## 5. 关键优势（按可复制性排序）

1. **权限纪律落地到了端点级，且有量化证据**（96.3% 覆盖）。多数同类项目只做到"菜单隐藏"，这里做到了后端强制。
2. **AI 是可选增强而非硬依赖**：`BaseAgent.fallback` 让无 Key / 模型故障时业务仍可用，且 `AgentResult.is_fallback` 把"降级"作为一等状态暴露给前端，而不是伪装成成功。
3. **针对 SQLite 的并发特性做了正确优化**，而不是"先写完再说"：先 commit 释放写锁、`busy_timeout=5000`、WAL、审计日志异步落库、单写者假设下的原子自增。
4. **发版一致性被当成架构问题处理**：VERSION 单一真源 + BUILD_INFO 烧 commit + 四道闸门 + 四层比对（本地 HEAD / origin / 镜像 / 容器）。这解决了"同版本号不同内容"这类最难排查的线上问题。
5. **注释承载决策记忆**，新人可在 1 天内理解"为什么这么写"，而不是只知道"这么写"。
6. **门禁可持续**：只拦真缺陷、不掺风格，避免了"告警淹没 → 全员忽略"的常见死法。

---

## 6. 潜在风险点

### P0（会在下一次大改时直接造成生产事故）

| # | 风险 | 证据 | 触发场景 | 影响 |
|---|---|---|---|---|
| R1 | **核心算法零测试** | 后端 0 单测；`paper_compose_service` 726 行纯函数无覆盖 | 调整分值分配/难度配比/题量规则 | 组卷静默丢题或总分对不上，教师端到考场才发现 |
| R2 | **请求契约缺失** | 94 处裸 `Dict`，`schemas/` 空 | 前端改字段名 / 后端改校验 | 契约漂移，表现为 500 或字段静默丢失（历史上已多次发生） |
| R3 | **手写迁移无版本表、无回滚** | 38 项 `MIGRATION_COLUMNS` 清单；alembic 未初始化 | 新增模型字段但忘记登记清单 | 老库缺列 → 该字段相关读写全部 500，且只能手写 SQL 修 |

### P1（限制规模与迭代速度）

| # | 风险 | 证据 | 影响 |
|---|---|---|---|
| R4 | **SQLite 单写者 + 单 worker** | `--workers 1`，WAL，写写互斥 | 全班同时交卷时写操作排队；`busy_timeout` 用尽即 500。当前靠"先 commit 再判分"缓解，但**并发上限是个位数 TPS** |
| R5 | **LLM 同步调用占 threadpool** | `client.invoke()` 阻塞 60–120s；无全局并发信号量 | 少量并发 AI 请求即可拖慢全站非 AI 接口 |
| R6 | **daemon 线程任务无持久化** | `Thread(daemon=True)` + `AgentJob` 表 | 重启丢执行；用户需手动重提。已有读时判定 + 启动收割兜底，但只是"把失败显性化" |
| R7 | **胖路由导致业务不可测** | API 层 437 处 SQL；services 仅 40 处引用 | 任何业务规则验证都要起 HTTP + 造库，回归成本高 → 反过来强化 R1 |
| R8 | **前端巨型视图** | 4 个视图 >1000 行；52 视图 / 3 组件 | 改一处影响一片；同类逻辑多份实现，修一个漏三个 |

### P2（长期债务）

| # | 风险 | 说明 |
|---|---|---|
| R9 | 文档与代码漂移 | 端点 198→272，版本 2.0.4→2.2.19，文档未跟 |
| R10 | 死配置 / 僵尸依赖 | `EMBEDDING_MODEL` 无引用；`alembic` 未初始化；`langgraph` 用 2 节点 |
| R11 | 无 metrics / trace / 告警 | 只有日志表，故障发现依赖用户反馈 |
| R12 | 权限查询每请求 ≥4 次 SQL | 无缓存，272 端点全量叠加 |

---

## 7. 改进建议

### 阶段一：补三张网（1–2 周，低风险，不动业务代码）

**① 后端单测（对应 R1，最高优先级）**

引入 `pytest` + `pytest-cov`，先只覆盖**纯函数与安全边界**，不追求覆盖率数字：

| 目标模块 | 用例要点 | 预计用例数 |
|---|---|---|
| `paper_compose_service.normalize_difficulty` | 合计=100、小数 round 后补最大档、非法输入 | 8 |
| `split_by_difficulty` | 任意 count × 任意配比，`sum(result) == count` 恒成立（参数化） | 20 |
| `_distribute_on_grid` / `_rescale_scores` | 总分精确等于目标、每题落在步长网格、题量不变 | 15 |
| `compose` | 题库不足时缺口如实上报、知识点过滤在所有分支生效 | 10 |
| `security.decode_token` | 无 db / 有 db / 吊销 / 过期 / type 不符 的 5×2 矩阵 | 10 |
| `grading_service._auto_grade_answers` | 客观题判分、多选半对策略、主观题不进自动分 | 10 |

验收：`pytest` 通过 + CI 新增 `pytest` job + 阻止 PR 合并。**不要求覆盖 API 层**——先把"算错了没人知道"这一类堵住。

**② 契约层（对应 R2）**

- 新建 `backend/app/schemas/`，按域建 `task.py` / `question.py` / `paper.py`。
- 策略：**新端点强制 Pydantic；存量按"写接口优先"替换**（POST/PUT/PATCH 先做，GET 响应最后做）。
- 加一道门禁：`tools/check_body_dict.py` 统计裸 `Body(...)` 数量，**只允许下降不允许上升**（棘轮机制），比"一次性全改"现实得多。

**③ 迁移体系（对应 R3）**

- `alembic init` → `alembic stamp head` 建立基线（不改表）→ 后续变更走 `autogenerate`。
- `MIGRATION_COLUMNS` 保留为 SQLite 启动兜底（双保险），但新字段必须走 alembic revision。
- 给迁移加一个 CI 检查：`alembic upgrade head` 在空库上跑通 + `alembic downgrade -1` 可回滚。

### 阶段二：拆边界（3–4 周，需要回归网就位后再做）

**④ 巨型 API 文件拆分（对应 R7）**

以 `/question` 域为试点（5 文件 5678 行 → 目标 3 文件）：

```
api/v1/question/__init__.py      # 聚合 router
api/v1/question/crud.py          # 题目 CRUD（约 600 行）
api/v1/question/paper.py         # 试卷 CRUD + 导出（约 700 行）
api/v1/question/import_export.py # Excel 导入导出（约 500 行）
```
业务规则下沉到 `services/question_service.py`；路由只做"解析入参 → 调服务 → 拼响应"。
验收：`question` 域端点响应与改造前逐字段一致（用现有 e2e 用例做黄金对比）。

**⑤ 前端抽 composables（对应 R8）**

先抽 4 个，覆盖 80% 重复：

| composable | 替代的重复逻辑 | 首批改造页面 |
|---|---|---|
| `useTableQuery` | 查询参数 + 分页 + loading + 重置 | KnowledgeManage / QuestionBank |
| `useBlobDownload` | `responseType: 'blob'` + 文件名解析 + 错误处理 | 所有导出按钮 |
| `usePermission` | `can()` + 按钮级显隐 | 全部 |
| `useConfirm` | `ElMessageBox.confirm` + 成功提示 | 全部 |

`KnowledgeManage.vue` 拆为：树（`KnowledgeTree`）+ 列表（`KnowledgeTable`）+ 详情抽屉（`KnowledgeDetail`）+ 附件面板（`AttachmentPanel`）。

**⑥ AI 调用收敛（对应 R5）**

- 所有耗时 AI 操作统一走已有的 `/agent/jobs` 异步通道（机制已具备，只是部分端点仍在请求内同步调用）。
- 加**全局并发信号量**（`BoundedSemaphore(AI_MAX_CONCURRENCY=4)`），超出直接返回"队列繁忙，请稍后"，而不是占着线程等 60s。
- 短期收益：非 AI 接口 P95 延迟不再被 AI 请求拖累。

### 阶段三：按规模演进（有明确触发信号再做，不要提前）

| 触发信号 | 阈值 | 动作 |
|---|---|---|
| 交卷并发 | > 20 同时提交 | SQLite → PostgreSQL（`database.py` 已兼容，需数据迁移 + 索引复核 + 重跑 e2e） |
| 日活 / 在线 | > 300 同时在线 | 多 worker + 引入 Redis（验证码 / 吊销 / 限流 / 缓存） |
| AI 并发 | > 8 同时请求 | 引入任务队列（arq / RQ），daemon 线程退役 |
| 团队规模 | > 2 人并行改同一域 | 强制契约层 + 模块 owner 制 |
| 端点总数 | > 350 | 按域拆分为独立 APIRouter 包（`api/v1/question/`、`api/v1/task/`） |

**明确不建议现在做的**：微服务拆分、引入 Kubernetes、上消息队列、改 TypeScript。当前规模下这些都是负收益。

---

## 8. 附：本次评估的核查清单

| 核查项 | 方法 | 结果 |
|---|---|---|
| 代码规模 | `find + wc -l`、`ast` 解析函数边界 | 后端 32,082 行 / 911 函数；前端 22,943 行 |
| 端点与鉴权 | 正则切分装饰器 + 依赖扫描 | 272 端点，262 含鉴权（96.3%） |
| 数据模型 | `grep __tablename__ / ForeignKey / Index` | 49 表 / 86 外键 / 184 索引 |
| 分层偏移 | `grep db.query\|select(` vs `from app.services` | 437 : 40 |
| 契约缺口 | `grep "Dict\[str, Any\] = Body"` | 94 处；`schemas/` 空 |
| 迁移机制 | 精读 `core/db_migrations.py` | 38 项补列清单，无版本表 |
| 并发模型 | 统计 `async def` / 精读 `supervisord.conf` / `llm.py` | 0 async；1 worker；`client.invoke()` 阻塞 |
| 门禁有效性 | 精读 `.github/workflows/*.yml` + `tools/` | 3 workflow / 9 道静态门禁 / 0 后端单测 |
| 文档一致性 | 对比 `docs/架构设计文档.md` 与实测 | 端点 198 vs 272，版本 2.0.4 vs 2.2.19 |

**未覆盖**：运行时性能（未压测）、线上错误率（未取生产日志）、依赖安全漏洞（未跑 `pip-audit`）、浏览器兼容性。若需要，这三项可作为下一轮评估的输入。
