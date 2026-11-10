# 新芽学堂（edu-ai-platform）· 代码结构化评估报告

> **评估对象**：`E:/project/management/edu-ai-platform`，`VERSION = 2.5.19`，master @ `8abab94`，工作区干净
> **评估日期**：2026-11-10
> **评估方法**：全量静态扫描（目录、行数、端点、模型、路由、CI/门禁/部署配置）+ 六条核心链路代码精读 + 关键文件交叉验证
> **口径说明**：所有数字为磁盘实测，未运行应用、未做压测与线上流量观测；涉及并发与性能的结论为代码层推断
> **约束**：本报告所有建议均以「不改变产品核心目标、不更换现有技术栈、不突破单镜像 + SQLite + 单 worker 架构」为前提

---

## 0. 结论摘要

**一句话定性**：这是一个工程纪律显著高于同规模平均水平、但正处于「审计产出 > 修复吞吐」失衡点的单体应用。安全、降级、发版一致性三条线已形成可复制的机制；主要债务不在代码写法，而在**契约层缺失、行为回归真空、文件粒度失控、文档基线漂移**。

**本次评估最重要的三项发现**：

1. **版本 2.5.19 是一次「只提交报告」的版本**。最新提交 `8abab94` 仅含 `VERSION` 与 `audit-reports/paper-analysis-2026-11-10.md`（707 行），该报告记录的 **P0×4 / P1×11 / P2×20 = 35 项问题均未进入修复**，其中含 1 个 SSRF 面、3 个功能整体不可用、11 个数据一致性/契约断裂问题。当前最高优先级不是新增功能，而是把这 35 项转为带回归用例的修复批次。
2. **已有两份评估报告的基线均已过期**：`docs/ARCHITECTURE_ASSESSMENT_2026-11.md` 基于 2.2.19（端点 272 / 表 49 / 后端 0 单测），实测当前为 **端点 282 / 表 52 / 后端 58 个 pytest 用例**；`docs/RELEASE_CONSISTENCY.md §八` 仍写「当前状态 2.1.12」并引用已删除的 e2e 套件「863 项 / 通过 849」。读文档已无法替代读代码。
3. **行为回归保护仍然缺位**，但比 2026-10-29 更微妙：静态门禁 17 道 + pytest 58 + vitest 76 + 接口冒烟 114 + verify 脚本 145 项看似充分，但 `auto_ship.sh` 头部与 `docs/DELIVERY_RULES.md §3` 均明确「**后端行为回归已无自动化覆盖**」。现有断言绝大多数是「源码文本断言」与「GET 可达性」，写操作全链路（建题→组卷→发布→作答→批改）与真实 LLM 输出路径均无自动化保护。

**综合评分（沿用既有评估口径，便于对比）**：

| 维度 | 2.2.19（前次） | 2.5.19（本次） | 变化原因 |
|---|:---:|:---:|---|
| 架构一致性 | 7.0 | 7.0 | 分层形态未变，仍是「胖路由 + 空心服务层」 |
| 安全性 | 8.5 | 8.0 | 端点鉴权未退化，但新增 1 个已确认的导出 SSRF 面未修 |
| 可测试性 | 3.0 | 4.0 | 从 0 到 58 个后端用例 + 114 条接口冒烟；仍缺写链路 e2e |
| 可维护性 | 6.5 | 6.0 | 文件粒度继续恶化（`paper_compose.py` 2935 行），37 份文档漂移 |
| 可观测性 | 6.0 | 6.5 | 四层一致性巡检 + watchdog + 熔断快照 |
| 工程门禁 | — | 8.5 | 17 道静态门禁 + 棘轮 + 反向验证纪律 |
| 演进弹性 | 5.0 | 4.5 | 35 项已知问题积压，修复吞吐低于审计产出 |

---

## 1. 项目目录结构与模块划分

### 1.1 实测规模

| 区域 | 文件数 | 行数 | 说明 |
|---|---:|---:|---|
| `backend/app/*.py` | 92 | **36,993** | 8 个子包，52 张表，282 个路由装饰器 |
| `frontend/src/*.vue` | 54 | **23,103** | 47 个视图 + 5 个公共组件 + 布局/根组件 |
| `frontend/src/*.js` | 24 | 2,254 | 14 个 API 对象 / 268 个方法 |
| `tools/*.py` | 47 | 13,191 | 门禁 19 / 验证脚本 18 / 数据工具 10 |
| `docs/` + `audit-reports/` | 37 `.md` | — | 23 + 14，含 3 份互相重叠的评估报告 |

### 1.2 顶层结构

```
edu-ai-platform/
├── backend/app/                # 后端应用（唯一被 COPY 进镜像的业务代码）
│   ├── main.py                 # FastAPI 入口、lifespan、中间件、异常处理器
│   ├── core/                   # config / database / security / exception /
│   │                           # db_migrations / rate_limit / logger
│   ├── models/                # 10 个文件 / 52 张表，__init__.py 统一注册元数据
│   ├── schemas/                # 5 个文件，含 legacy_bodies.py（24 个历史请求体模型）
│   ├── services/              # 30 个文件，业务规则与事务边界
│   ├── agents/                 # 10 个文件，8 个 Agent + LLM 客户端 + RAG
│   ├── api/                    # deps.py / router.py / v1/（22 文件）/ v1/learning/
│   ├── middleware/            # audit.py：操作日志、脱敏、耗时
│   └── utils/                 # common / answer / options
├── frontend/src/
│   ├── views/{admin:14, teacher:11, student:15, agent:2, login:2}  # 47 视图
│   ├── components/            # 仅 5 个：EChart / ExportButton / TableEmpty /
│   │                           # PomodoroTimer / VersionInfo
│   ├── api/                    # index.js（268 方法）/ request.js（axios 拦截器）
│   ├── router/ store/ layout/ styles/ utils/ constants/ composables/
├── tools/                      # 发版、门禁、部署、验证、数据生成
├── deploy/                     # nginx / supervisord / fatal_guard / watchdog
├── docs/ audit-reports/        # 契约文档、评估与复审报告
├── Dockerfile                  # 5 阶段，unified 为默认产出
├── docker-compose.yml          # 单服务 app，命名卷 edu-data
└── start.{bat,ps1,sh} / dev.*  # 本地一键启动（7 个脚本，4 个是转发器）
```

### 1.3 模块划分评价

按业务域切分是清晰的：后端 21 个路由模块与前端 5 个视图域一一对应；`api/v1/learning/` 已按 notes/wrongbook/review/tools 二次拆分，并显式约束静态路由注册顺序。

但存在明显的**「加法式演进」**痕迹：同一资源被多个文件共管。

| 资源 | 涉及文件 | 合计行数 | 影响 |
|---|---|---:|---|
| `/question/papers` | `question.py`(2005) + `paper_compose.py`(2935) + `paper_ai.py`(644) + `exam_standard.py`(561) + `question_ai.py`(810) | 6,955 | 改组卷需同时理解 5 个文件 |
| `/edu` | `edu.py`(1407) + `knowledge.py`(1820) + `knowledge_ai.py` | 3,400+ | 知识点 V2 与旧 edu 同前缀，靠注释保证不重复注册 |
| 学习中心 | `learning/tools.py`(651) 单文件承载 16 个端点 | — | 练习/收藏/目标/路径/闪卡/组卷混装 |

**6 个后端文件超过 1000 行**（`paper_compose.py` 2935、`question.py` 2005、`knowledge.py` 1820、`edu.py` 1407、`init_db.py` 1354、`task.py` 1259），**18 个 `.vue` 超过 400 行**，前四名均 >1300 行：`KnowledgeManage.vue` 2143、`QuestionBank.vue` 1723、`PaperManage.vue` 1336、`PaperWizard.vue` 1312。

---

## 2. 技术栈及其职责

| 层 | 选型 | 版本 | 承担职责 | 约束边界 |
|---|---|---|---|---|
| Web 框架 | FastAPI + Uvicorn | 0.115.6 | 282 端点、依赖注入式 RBAC、OpenAPI（仅 DEBUG 开放） | `supervisord.conf` 固定 `--workers 1` |
| ORM | SQLAlchemy（同步） | 2.0.36 | 52 表、86+ 外键、`joinedload/selectin` 加载策略 | 无 Alembic，靠 `create_all` + 手写 `db_migrations.py`（33 条补列 + 2 个破坏性 V2 迁移） |
| 配置 | pydantic-settings | 2.10.4 | `Settings` + `@lru_cache`；`sys_config` 在线覆盖 env | `LLM_MAX_TOKENS=8192` 为代码级硬顶，DB 更大值被收敛 |
| 数据校验 | Pydantic v2 | — | 24 个历史请求体模型集中在 `legacy_bodies.py` | 大量端点仍是 `Dict[str,Any] = Body(...)`，契约层薄 |
| 数据库 | SQLite WAL | — | 单文件、`foreign_keys=ON`、`busy_timeout=5000` | **单写者**；Docker Desktop Windows 9p 绑定挂载不兼容，必须用命名卷 |
| 认证 | JWT HS256 + PBKDF2 | — | 双令牌、jti 吊销落库、用户级水位、验证码一次性 | 进程内缓存已全部迁表，为多 worker 预留 |
| AI 编排 | LangChain / LangGraph | 0.3.14 / 0.2.60 | 8 个 Agent、`Orchestrator`、规则引擎 fallback | langgraph 未安装时降级顺序编排 |
| LLM 接入 | ChatOpenAI 兼容协议 | — | 5 种提供商预设、default/fast 场景路由、熔断冷却 | `invoke()` 同步阻塞 threadpool（默认 40 线程） |
| 检索 | ChromaDB + ONNX | 0.5.23 | 知识点/题目/笔记/附件索引，失败降级 SQL LIKE | 本地持久化目录，无独立服务 |
| 定时/长任务 | APScheduler + daemon Thread | 3.11.0 | 8 个内置 cron + `sys_agent_job` 异步任务 | 进程重启即丢，靠 `reap_orphan_jobs()` + 读时判定兜底 |
| 前端 | Vue 3 + Vite 6 | 3.5.13 / 6.0.7 | 47 视图、动态路由懒加载、按需引入 Element Plus | 无 TypeScript、无组件级单测 |
| UI 库 | Element Plus | 2.9.1 | 全站表单/表格/弹窗；`unplugin` 自动按需 | 主题令牌在 `styles/index.css` 单一定义 |
| 图表 | ECharts | 6.1.0 | 10 个页面，`utils/echarts.js` 按需注册 | `MasteryMap.vue` 直接 `import * as echarts`，绕过按需注册 |
| 状态 | Pinia | 2.3.0 | 单 store（`user.js`, 81 行），权限快照同步 localStorage | `permissions.menus` 声明但无消费点 |
| 交付 | Docker 多阶段 + nginx + supervisord | — | `unified` 单镜像，前后端同端口 80 | 无 Redis / MQ / 对象存储 / 独立 DB 进程 |

**运行时拓扑**：

```
浏览器 ──> nginx:80 ──/api/──> uvicorn:8000 (1 worker)
              │                    ├─ SQLite WAL（命名卷）
              └─/ 静态资源        ├─ Chroma（本地目录）
                                  ├─ APScheduler（进程内 + sys_job_lock）
                                  ├─ daemon Thread（AI 长任务）
                                  └─ sys_config（LLM 在线配置）
         supervisord 托管两者，fatal_guard 在进程 FATAL 时 kill PID 1 触发 restart
```

---

## 3. 已实现功能与核心业务流程

### 3.1 功能域全景（按端点分布）

| 业务域 | 端点数 | 代表能力 |
|---|---:|---|
| 教学资源 `/edu` | 31 + 21 | 年级/学科/班级/任课矩阵/建班申请；知识点树、导入、批量移动、RAG 检索、reindex |
| 题库与试卷 `/question` | 24 + 3 + 2 + 10 + 24 | 题目 CRUD、批量建题、导入导出、审核；命题标准；标准组卷 V3 预览/AI 补题/重生/保存/版本/导出 |
| 作业与考试 `/task` + `/grading` | 14 + 12 | 定时发布、下发范围、心跳切屏、交卷、自动判分、人工批改、批量发布/撤发、班级学情 |
| 学习中心 `/learning` | 37 | 笔记（AI 整理/共享）、错题本（错因/重做/导出）、艾宾浩斯复习、随机练习、收藏、目标打卡、学习路径、闪卡、自主组卷 |
| AI 中心 `/agent` | 14 | 统一对话（含 SSE）、6 个 Agent 端点、异步任务、调用日志 |
| 报表 `/report` | 14 | 学生/教师/管理员三视角 + Excel 导出 |
| 系统 `/system` `/auth` `/logs` | 23 + 12 + 13 | RBAC、注册审批、在线 AI 配置、通知、日志审计、定时任务 |
| 教案 `/lesson` | 18 | 教案 CRUD、附件、AI 生成（分头/正文两段） |

### 3.2 六条核心链路的调用序列

**① 出题入库 → 审核 → 知识点关联**

```
POST /question/questions (question.py:513 create_question)
  → _prepare_question (:465)
      → normalize_question_type / _require_grade_subject
      → _validate_knowledge_point (:248，校验同 grade+subject，防 FK 失败)
      → _validate_q_status / _validate_bank_type
  → db.add(Question) + commit
  → rag.index_question(q)（失败仅告警）
输出：ok({...})；公共库 published 需审核，非审核人强制降 draft
批量：POST /question/questions/batch-create（≤50，逐条校验部分成功）
```

**② 标准组卷 V3（最复杂链路）**

```
POST /question/papers/compose/preview → _compose_from_payload (:1225)
  → _resolve_standard → exam_structures.sections_for（section_total 唯一小计口径）
  → paper_compose_service.compose (:410) → ComposePlan（纯内存，不写库）
  → 有 gaps 时 _ai_fill_gaps (:1088)
      → ThreadPoolExecutor(min(AI_FILL_CONCURRENCY, pending, 4))
      → ai_fill_batch._fill_batch_cap（题型分档 × hard 对折）
      → QuestionGeneratorAgent(save=True, source="ai_fill")  ← 例外：会落 draft 题
  → _plan_response + audit_paper（三份报告）
POST /compose/regenerate (:905) 保存前替换预览题，只覆盖内容字段，保留 score/槽位
POST /compose/save (:1597) → _normalize_items → _write_items (:1759)
  → 插新题项 → 迁移 Answer.paper_item_id → 删旧题项 → recount_usage
  → paper_version_service.snapshot（同事务，版本只增不改）
导出：/export/{docx,pdf,answer-sheet,html} → paper_export_service
```

`_write_items` 的顺序是全项目最关键的一致性约束：`Answer.paper_item_id` 为非空 FK + CASCADE，旧实现「先删后插」曾导致 80 条作答 / 920 分归零。

**③ 发布 → 答题 → 判分 → 错题 → 掌握度**

```
POST /task/tasks → publish_at 未来则 status=DRAFT（不通知）
  → task_jobs.publish_scheduled_tasks（* * * * * 每分钟激活并补发通知）
GET /task/tasks/{id}/paper → 下发范围 + start_at/publish_at 管控
POST /task/tasks/{id}/submit (task.py:994)
  → attempt 由服务端判定；core/rate_limit.check_agent_rate(cost)
  → grading_service.save_answers (:49)
      → _content_to_db（list 答案 JSON 序列化，防 Text 列绑定错误）
      → db.commit()  ← 主动释放 SQLite RESERVED 写锁，再调 LLM
  → _auto_grade_answers (:95) → GradingAgent.run() → res["data"]
      → _grade_objective (utils/answer.answers_match)
      → _grade_subjective_batch（首题探测熔断，ThreadPool + 共享 deadline）
  → 仅「已判定为错」的客观题 → _collect_wrong_question (:166)
  → 答对 → _update_mastery (:214)，答错 → 掌握度下降
  → finalize_submission (:278) → 重算分数/is_passed/pending_manual + _calc_rank（SQL 竞赛排名）
  → _record_study（只在 finalize 调一次）
```

**④ AI 调用与降级**

```
agent.py:/chat|/question-generator|... → check_agent_rate（sys_agent_rate UPSERT）
  → Orchestrator.run → RouterAgent（LLM 分类 / _guess_intent 关键词兜底）
  → AGENT_REGISTRY[intent].run() → BaseAgent.execute() / fallback()
  → BaseAgent.call_llm → llm_client.chat(biz_type)
      → resolve_scenario（default / fast，fast 注入 reasoning_effort=low）
      → llm_breaker.load()（进程内 _local ⊕ sys_llm_breaker 单行表）
      → _get_db_value()（sys_config > settings，llm_api_key 显式空串 = 关闭）
      → ChatOpenAI.invoke() → extract_json（_find_balanced 括号配对）
  → 失败：is_fallback=True + status="empty"/"skipped" 日志；auth 错误永久熔断，429 退避 30→300s
长任务：AgentJob 落库 + daemon Thread；agent_job_state.apply_timeout 读时判定
        （paper_compose 900s / 其余 300s）+ reap_orphan_jobs 启动收割
```

降级是一等状态：`Orchestrator` 用 `.get("is_fallback")` 读取（`AgentResult` 为 `TypedDict(total=False)`），前端 `fallback-tip` 样式已定义但**当前 0 处引用**。

**⑤ 权限认证**

```
登录：_check_captcha_rate + _check_login_fail_rate（进程内 IP 桶）
  → _verify_captcha_or_raise（sys_captcha 一次性消费）
  → auth_service.authenticate（账号锁定 5 次/15 分、PBKDF2 双格式兼容、
     登录机会式升级哈希、异地登录 → LoginLog + Notification）
  → create_access_token（含 iat_precise 浮点秒，解决整秒 iat 误杀）
  → build_permission_context（停用角色不下发，sys_admin perms=["*"] + 全菜单）
请求：deps.get_current_user → decode_token(token, db)（fail-closed 吊销检查）
  → is_user_token_revoked（水位 + iat_precise）
  → joinedload(roles→permissions) 一次取齐
  → must_change_password 白名单拦截
  → require_perm + get_data_scope（None=不限 / 空列表=拒绝）
前端：request.js 注入 Bearer → 401 单例收敛刷新 + 跨标签页竞态处理
  → router.beforeEach（roles/perm/perms）→ MainLayout 7 组菜单前缀过滤
```

**⑥ 知识点与学习数据**

```
知识点树（parent_id / level / level_path / code）
  → rag.index_knowledge → Chroma 集合（kp_/q_/note_/att_ 前缀）
  → 失败降级 SQL LIKE
答题 → edu_knowledge_mastery（mastery = correct/total × 100）
  → /learning/review/mastery（薄弱/精通分档）
  → study_agent 生成 ReviewPlan；complete_review 累计 2 轮 → is_mastered
  → task_jobs.push_review_reminders（0 8 * * *）
  → report.py knowledge_effect（KnowledgePoint ← Question ← Answer JOIN 聚合）
```

---

## 4. 关键实现、模块依赖与调用关系

### 4.1 包间依赖方向

```
main.py → api/router.py → api/v1/*（21 模块）
                            ├→ api/deps.py → core.{config,database,security,exception} + models
                            ├→ schemas/*（薄）
                            ├→ services/*  → models / core / utils /（少数）agents
                            ├→ agents/*     → models / core / utils / services.llm_breaker
                            └→ api/v1/* 互相引用（延迟导入为主）
services.scheduler → job_lock / task_jobs
agents.llm → services.llm_breaker（顶层）
services.ai_config_service →（函数内）agents.llm  ← 唯一的 services↔agents 反向边
frontend: request.js ⇄ store/user.js（函数内动态 import 打破初始化环）
```

**延迟导入是刻意的架构手段**，共 20+ 处带明确成环注释：`core/security.py:535` 避免早期导入反向依赖；`paper_compose.py:531` 明确「question.py 与本模块互相引用，放模块顶层会形成循环导入」；`ai_config_service.py:286` 避免 services→agents 顶层环；`frontend/src/api/request.js:56` 说明 `request ← api ← store` 循环。

### 4.2 全局单例与多副本安全性

| 状态 | 位置 | 跨进程 | 备注 |
|---|---|:---:|---|
| `settings` / `engine` / `Base.metadata` | core | 否 | 各进程解析同一 env，值一致 |
| **`llm_client` + `get_llm()` 两份实例** | `agents/llm.py` | 否 | `_reload_llm_client` 必须遍历两个实例，否则「部分功能用新密钥、部分用旧连接」 |
| `orchestrator` / `AGENT_REGISTRY` | `agents/base.py` | 否 | 运行时装配 |
| `_scheduler` / `_OWNER` 任务锁 | services | 否 | 靠 `sys_job_lock` 跨进程去重 |
| `_local` 熔断镜像 / `_DENY_CACHE` | services | 否 | DB 侧 `sys_llm_breaker` / `sys_rate_limit` 为正确性来源 |
| `_CAPTCHA_HITS` / `_LOGIN_FAIL_HITS` | `auth.py` | **否** | 注释承认多 worker 下额度按进程翻倍 |
| `_collection` 等 5 个 RAG 全局 | `agents/rag.py` | 否 | 持久化目录共享 |
| 已落库：验证码、吊销 jti、水位、限流、熔断、任务锁、长任务、配置 | `security_cache.py` / `ops.py` | **是** | 明确的「多 worker 前置」迁移成果 |

### 4.3 被代码注释固化的「契约易错点」（评估中必须计入维护成本）

| 契约 | 位置 | 后果（历史事故） |
|---|---|---|
| 路由前缀单数（`/question`/`/task`/`/learning`） | 全站 | 测试脚本曾大面积 404 |
| `/system/config` 返回**小写键** | `SystemSetting.vue` | 按大写渲染导致整页静默空白 |
| axios 拦截器 `return res`（信封本身） | `request.js` | `res.data.data` 恒 undefined；blob/text 必须返回原 response |
| 题库筛选入参是 `qtype`，落库字段是 `type` | `question.py` | 字段漂移 |
| 批量新增走独立 `/batch-create`（`items`），`/batch` 走 `action`+ids | `question.py` | 契约混淆 |
| `difficulty_ratio` / `Answer.content` 必须 `Text` 且先 JSON 序列化 | models / `grading_service` | 多选题交卷 500、难度比例截断 |
| `section_total()` 是全系统唯一小计口径 | `exam_structures.py` | 卷面分与规范对不上 |
| `Answer.paper_item_id` 非空 + CASCADE | `paper_compose._write_items` | 曾 80 条作答 / 920 分归零；现「插新 → 迁移作答 → 删旧」 |
| `_resolve_kp_id` 三重校验 | `question_agent` | 模型给的 id 不可信，FK 失败会毁整批 INSERT |
| JWT `iat` 整秒精度 → `iat_precise` | `security.py` | 改密后同秒新令牌被误杀 |

这些契约目前靠 **17 道静态门禁 + 人工记忆 + 契约文档**共同维持，而不是靠类型系统。这是本项目的核心可维护性风险。

---

## 5. 优势、冗余、瓶颈、可维护性与风险

### 5.1 优势（有证据，可复制性排序）

1. **安全机制落到端点级且状态全部落库**：282 端点由 `require_perm` + `DataScope` 覆盖；JWT 吊销 fail-closed、用户级水位、验证码一次性、限流键加盐哈希、反代 IP 可信判定。进程内缓存已系统性迁表，为多 worker 预留了正确前提。
2. **AI 是可降级增强，不是硬依赖**：无 Key / 熔断 / 空正文 / JSON 解析失败均有明确分支，`status="empty"` 不伪装成功，`is_fallback` 作为一等状态回传。规则引擎保证离线部署可用。
3. **针对 SQLite 单写者做了正确的并发设计**：`db.commit()` 后再调 60s LLM、AI 调用日志 daemon 线程异步落库、`busy_timeout=5000`、单条 SQL 原子自增、`flock` 保护启动期破坏性迁移。每处都有事故复盘注释。
4. **发版一致性被当作架构问题处理**：`VERSION` 单一真源 → `BUILD_INFO` 烧 commit → CI `preflight/postflight` → `check_four_layer` 四层比对 → `deploy_release.py` 备份/健康门禁/回滚 → 服务器 watchdog 每 5 分钟巡检。
5. **门禁设计克制且做过反向验证**：`lint_gate` 只开 F/E9 并注释「全开会几百条告警，团队会直接关掉」；`check_schema_bodies` / `check_api_sql` 用棘轮只许变好；新门禁要求用「已知有 bug 的旧版」反向验证，识别了 4 类假绿。
6. **注释记录的是决策依据与反例**，不是「是什么」。这把踩坑记忆转成团队资产，是新人上手成本低的主因。

### 5.2 冗余（明确可削减项）

| 冗余 | 证据 | 影响 |
|---|---|---|
| **文档/报告堆积且基线漂移** | 37 份 `.md`；`RELEASE_CONSISTENCY §八` 写 2.1.12、`DELIVERY_RULES §5` 写 2.0.0、`FUNCTIONAL_TEST_REPORT` 写 2.2.3、架构评估写 2.2.19、试卷分析写 2.5.18；`E2E_STABILITY_REVIEW` 复盘的 `run_e2e.sh` 已删除 | 文档不能再作为评估依据，且每轮新报告都在叠加而非替换 |
| **审计报告链重复** | `full-project-audit`(11-05) → `reaudit`(11-06) → `reaudit3`(11-09) → `paper-analysis`(11-10)，加上 3 份 qa 修复报告主题重叠 | 35 项问题分散在多份报告，缺少单一可执行的 backlog |
| **试卷四套入口语义重叠** | `PaperManage` / `PaperWizard` / `PaperEdit` / `CustomPaper`（学生）；后端 `question.py` 与 `paper_compose.py` 各有一套 papers 逻辑 | 报告 §0.3 指出问题根因正是「A 入口的能力假设被 B 入口无条件继承」 |
| **两套 LLMClient 实例 + 两套配置读取** | `llm.py` 模块级单例 `llm_client` 与 `get_llm()`；`ai_config_service.get_ai_config` 与 `llm._get_db_value` 各读一次 `sys_config` | 每次 `chat()` 至少开一个新 Session；配置变更须遍历两个实例 |
| **18 个 `verify_*` + 17 道门禁 + 5 个未接入脚本** | `check_n_plus_one.py`、`verify_consistency.py` 未被任何流水线调用；`check_css_tokens` 只在 CI 不在 `auto_ship` | 工具存在但保护未生效（详见 §5.4） |
| **7 个本地启动脚本，4 个是转发器** | `start.bat` / `manage.bat` / `stop.bat` / `dev.bat` 仅转发到 `start.ps1`；`start.ps1`(614) 与 `start.sh`(326) 是同一逻辑双实现 | 跨平台重复维护，改动需同步两处 |
| **三套限流并存** | `core/rate_limit.py`（AI 按用户）、`services/rate_limit.py`（滥用 DB 窗口）、`auth.py` 进程内 IP 桶 | 语义不同但命名相近，易误用；IP 桶多进程额度翻倍 |
| **未使用的 UI 样式类** | `ai-badge` / `fallback-tip` 在 `index.css` 定义，全站 0 引用；`ExportButton` 注释称替代 38 处导出按钮，实际仅 1 个视图引用 | 抽取完成度不足，收益未兑现 |

### 5.3 瓶颈（按触发条件排序）

| 瓶颈 | 现状 | 触发条件 | 影响面 |
|---|---|---|---|
| **SQLite 单写者** | WAL + `busy_timeout=5000`；所有写串行 | 并发交卷 / AI 补题多线程写入 / 审计日志 | 全局写吞吐；已用 commit-before-LLM 缓解但天花板仍在 |
| **单 uvicorn worker** | `supervisord.conf` 固定 `--workers 1` | 任何 CPU 密集或长连接 | 无法利用多核；进程内 IP 限流桶在此前提下才准确 |
| **同步 LLM 占 threadpool** | `client.invoke()` timeout 60s，threadpool 默认 40 线程 | 10 个用户同时触发 AI 出题（各等 60s） | 吃掉 25% 线程池，登录/查题/交卷跟着变慢；**只有按用户 12/min 限流，无全局并发上限** |
| **daemon 线程长任务** | `sys_agent_job` + `threading.Thread(daemon=True)` | 容器重启 / 进程崩溃 | 任务状态永停 running；靠 `reap_orphan_jobs` + 读时判定兜底，但结果丢失 |
| **无版本化迁移** | `create_all` + 手写 33 条补列 + 2 个含 `DELETE` 的 V2 迁移，标记位仅 `sys_config` | 多实例同时启动（Windows 无 `fcntl`，直接放行） | 破坏性迁移可能重复执行；非 SQLite 分支仅告警 |
| **导出同步阻塞** | docx/pdf 在请求线程生成，前端 `timeout: 300000`，nginx `proxy_read_timeout 300s` | 大卷导出 | 长时间占线程；无进度、无法取消 |
| **前端全量 ECharts 引入** | `MasteryMap.vue` 用 `import * as echarts from 'echarts'`，绕过 `utils/echarts.js` 按需注册 | 首屏加载掌握图谱 | 抵消 `manualChunks` 的 charts 分包收益 |

### 5.4 可维护性

**结构性短板（沿用 2.2.19 评估且仍未闭环）**：

- **契约层薄**：`schemas/` 只有 5 个文件，`legacy_bodies.py` 集中 24 个历史请求体；大量 `Dict[str,Any] = Body(...)` 使 OpenAPI 请求体显示 `{}`、字段拼错不报 422。`check_schema_bodies` 用计数棘轮限制恶化，但只是止损不是补齐。
- **行为回归真空**：`qa_audit_suite.py` 58 个用例中相当比例是**源码文本断言**（检查某文件是否含某字符串）；`functional_runner` 114 条是 GET 可达性 + 越权 403；`ci.yml` 与 `auto_ship.sh` 明确 `LLM_ENABLED=false`，真实模型输出路径测不到。`docs/DELIVERY_RULES §3` 要求「改业务逻辑后人工点一遍相关页面并写进当天 FIX_RECORD」，这是当前唯一的行为了解手段。
- **门禁覆盖缺口**：`check_n_plus_one.py`（已实现 4 类 N+1 检测）和 `verify_consistency.py` 未接入任何流水线；`check_css_tokens.py` 仅在 CI 前端 job、`auto_ship.sh` 本地不含；`check_new_code_tests.py` 的棘轮只保证用例数不减，不保证用例覆盖新代码。
- **文件粒度**：API 层承担了约 70% 业务逻辑，`services/` 只在组卷/判分/导出/LLM 等「重」域存在，CRUD 域基本空心 → **无法在不启动 HTTP 的情况下测试业务规则**。
- **前端复用率低**：65 张 `el-table`、49 个 `el-dialog`、16 个 `el-pagination` 全部由 30 个视图各自书写，公共组件仅 5 个。`confirm.js` 是成功的例外（26 个文件引用、视图中裸 `ElMessageBox` 为 0）。

### 5.5 潜在风险（分级，含证据）

**P0 — 可在下一次操作中直接造成事故或数据损失**

| # | 风险 | 证据 |
|---|---|---|
| P0-1 | **试卷报告 35 项问题全部未修**，含 PDF/答题卡导出的 reportlab 用户可控文本 → SSRF + 500 | `audit-reports/paper-analysis-2026-11-10.md §3` 实机复现；`8abab94` 只提交报告 |
| P0-2 | 列表页「编辑试卷」整卷覆盖写 → 抹平标准卷大题结构；删题后成绩不重算 | 同上 §4 P1-1 / P1-4 |
| P0-3 | AI 一键组卷「只写描述、不选年级学科」100% 失败；智能组卷 Agent 比例语义错乱恒 0 题 | 同上 §3 P0-3 / P0-4 |
| P0-4 | **无自动化行为回归**，35 项修复若无用例护航，极易引入回归（历史上已连续 3 版 CI 红灯无人发现） | `auto_ship.sh` 头注释、`DELIVERY_RULES §3` |

**P1 — 限制迭代速度与规模**

- 工作区 `.env` 含明文 `SECRET_KEY` 与 `LLM_API_KEY`（未入库，`.gitignore` 正确），但 `deploy_release.py` 以运行中容器环境变量为基线、缺 `SECRET_KEY` 即中止，凭据轮换流程脆弱。
- 文档基线漂移让「读文档评估」失效；`README` 快速开始仍写 `nanpo/edu-ai-platform:2.0.0`，实际镜像主通道已是 ghcr。
- `MasteryMap.vue` 全量引入 ECharts；`index.html` 设 `user-scalable=no`（可访问性 + 移动端缩放受限）。
- 多 worker 前提未闭合：`auth.py` 进程内 IP 桶、`RateLimit._DENY_CACHE`、RAG 全局集合仍为进程内。

**P2 — 长期债务**

- 无 Alembic；`db_migrations` 的两个 `DELETE` 迁移靠 `sys_config` 标记位，Windows 无 `flock`。
- `backend/VERSION` 是一个空目录（非文件），易误导。
- `deploy_scripts/` 仓库内仅剩 1 个验证脚本，仓库外同名目录承载凭据与历史脚本，「废弃」定性只散落在注释里。
- `permissions.menus` 字段声明但无消费点；`ai-badge` / `fallback-tip` 样式零引用。

---

## 6. 改进建议（按优先级 × 影响范围 × 改动成本组织）

> **成本口径**：低 = < 0.5 人日；中 = 0.5–3 人日；高 = > 3 人日。**影响范围**：单点 / 模块 / 全局。
> **优先级**：P0 立即、P1 本迭代、P2 计划、P3 观察。
> 所有建议均在现有 FastAPI + SQLAlchemy 2.0 + SQLite WAL + Vue3/Element Plus + 单镜像约束内，**不引入新框架、新中间件、新数据库**。

### 6.1 功能扩展（从已有数据/端点延伸，不新增架构层）

| 编号 | 优先级 | 建议 | 影响范围 | 成本 | 预期收益 | 适用场景 |
|---|:---:|---|---|:---:|---|---|
| F-01 | **P0** | 把试卷报告 35 项整理为**单一 backlog 文件**（按 P0/P1/P2 + 复现命令 + 关联端点），替代分散在 4 份报告里的描述 | 模块 | 低 | 消除「审计产出 > 修复吞吐」，修复进度可度量；35 项不再重复发现 | 每次审计后 |
| F-02 | **P1** | 试卷版本 **diff 可视化**：复用 `PaperVersion` 已冗余存储的 stem/answer/analysis，在现有版本列表页加「与上一版对比」 | 单点 | 中 | 回溯前可见差异，直接缓解 P1-5「版本回溯只还原 name/duration」 | 教师改卷、误操作回滚 |
| F-03 | **P1** | **班级维度薄弱知识点聚合**：复用 `KnowledgeMastery` + `DataScope`，在 `report.py` 增 1 个端点，教师端已有报表页加 1 个 Tab | 单点 | 低 | 无需新表；把学生个人掌握度升级为教学决策依据 | 备课、讲评课 |
| F-04 | **P1** | **AI 长任务可取消 + 结果持久化**：复用 `sys_agent_job`，给 `apply_timeout` 增加 `cancel_requested` 字段与取消端点，前端轮询响应 | 模块 | 中 | 解决「离开页面任务仍在跑 / 重启丢结果」；与现有僵尸收割共用一套状态机 | 长组卷、AI 教案 |
| F-05 | **P2** | **导出异步化**：把 docx/pdf/答题卡生成迁到 `sys_agent_job`，完成后生成短时效下载链接（现有 `sys_attachment` 或 `EXPORT_DIR`） | 模块 | 高 | 释放 300s 请求线程、支持进度与取消；消除 P0 导出面在请求内暴露 | 大卷 / 全年级导出 |
| F-06 | **P2** | **AI 配置按 biz_type 细化预算**：`sys_config` 已支持任意 key，扩展 `ai_config_service._FIELDS` 增加 `question_generate` / `grading` 各自的 max_tokens、temperature | 单点 | 中 | 不换模型即可缓解「hard 难度 8192 token 正文 0 字」；与现有 `_CAPS` 硬顶兼容 | 已接真实 LLM 且有质量投诉时 |
| F-07 | **P2** | **通知订阅偏好**：复用 `sys_notification` 的 `type` 字段，加一张偏好表或写 `sys_config` 用户级项 | 单点 | 中 | 减少「异常登录提醒 / 作业发布」对高频用户的打扰 | 用户量大后 |

### 6.2 性能优化（针对已确认的瓶颈，不做预防性改造）

| 编号 | 优先级 | 建议 | 影响范围 | 成本 | 预期收益 | 适用场景 |
|---|:---:|---|---|:---:|---|---|
| P-01 | **P1** | **LLM 全局并发闸门**：在 `llm.py` 用进程内 `threading.BoundedSemaphore(N)`（N 取 4–8，与 `AI_FILL_CONCURRENCY` 对齐）包裹 `invoke()`，超限快速返回 `is_fallback`，不排队 | 全局 | 低 | 直接封住「10 用户 × 60s 吃掉 25% threadpool」；非 AI 接口延迟不再被 AI 拖累 | 任意已接 LLM 的并发场景 |
| P-02 | **P1** | **把 `check_n_plus_one.py --strict` 接入 `auto_ship.sh` 与 `ci.yml`**（脚本已写好、只需加两行调用） | 全局 | 低 | 零开发成本，立即获得循环内查库/无分页端点/缺索引的持续检测 | 每次提交 |
| P-03 | **P1** | **`MasteryMap.vue` 改用 `utils/echarts.js` 按需注册**（与其余 9 个图表页一致） | 单点 | 低 | 消除全量 ECharts 打包，恢复 `manualChunks` 的 charts 分包收益 | 前端构建体积敏感时 |
| P-04 | **P1** | **收敛 `llm.py` 双实例为单一 `get_llm()`**，并把 `_get_db_value` 的每次调用开新 Session 改为按请求缓存（保留 `sys_config > settings` 优先级，配置保存时失效缓存） | 模块 | 中 | 消除「两个实例各熔各的」隐患；减少每次 chat 的额外连接开销 | 所有 AI 调用 |
| P-05 | **P2** | **统一 `check_css_tokens.py` 的接入位置**：补进 `auto_ship.sh` 本地门禁，消除「本地绿、CI 红」 | 全局 | 低 | 发版前即可发现 CSS 变量自引用回归（历史上曾致 primary 按钮透明） | 每次提交 |
| P-06 | **P2** | **把 `verify_paper_module.py`(106 项) 等 4 个高价值 verify 脚本纳入 `auto_ship.sh` 的回归段**（目前只在 CI 定时任务跑） | 全局 | 中 | 本地发版即覆盖写操作链路，部分填补行为回归真空 | 改组卷/判分/导出时 |
| P-07 | **P3** | 报表聚合端点加短 TTL 进程内缓存（按 `user_id + params`），不引入 Redis | 模块 | 中 | 管理员/教师报表重复查询降载 | 只读报表 QPS 上升后 |

> **明确不做**：不引入 Redis / Celery / 消息队列 / PostgreSQL / 读写分离。这些会破坏「2 核 4G 一键起」的产品前提，且在数百用户规模下收益为负。

### 6.3 代码质量（优先补保护网，再动结构）

| 编号 | 优先级 | 建议 | 影响范围 | 成本 | 预期收益 | 适用场景 |
|---|:---:|---|---|:---:|---|---|
| Q-01 | **P0** | **为 35 项问题中的 P0×4 与 P1 中的数据一致性项（P1-1/4/5/6/9/11）各补 1 条接口级回归用例**，写入现有 `functional_cases.py` / `qa_audit_suite.py`，不引入新框架 | 模块 | 中 | 修复有网可依；直接针对「契约在某一处悄悄退化」这一反复出现的根因 | 修复 35 项之前 |
| Q-02 | **P1** | **建立单一「现状卡」文档**（版本 / 端点数 / 表数 / 测试数 / 四层状态），并用一道门禁校验关键文档不引用过期版本号 | 全局 | 低 | 终结 37 份文档基线漂移；新评估只需更新一张卡 | 每次发版 |
| Q-03 | **P1** | **归档过期文档**：把 4 份历史评估报告、`E2E_STABILITY_REVIEW`、3 份 FIX_RECORD 移入 `docs/archive/`，README 只链接现状卡与契约文档 | 全局 | 低 | 新人不再被「2.1.12 当前状态」误导 | 立即 |
| Q-04 | **P1** | **补全 `check_schema_bodies` 的目标收敛路径**：按域分批把 `Dict[str,Any] = Body(...)` 迁到 `schemas/legacy_bodies.py` 同款 Pydantic 模型，每批同步下调 `BASELINE` 棘轮（门禁已强制） | 模块 | 高 | 让 OpenAPI 请求体可读、字段错误 422 前置；从根上减少契约漂移 | 每次改该域端点时顺带做 |
| Q-05 | **P2** | **拆分 `paper_compose.py`**：按「预览/保存 / 重生 / 版本 / 导出 / 异步任务」切成 5 个子模块，保持 `router` 前缀与函数名不变（前端零改动） | 模块 | 高 | 2935 行 → 单文件 <700 行；降低「改组卷要开 5 个文件」的认知负担 | 35 项修复完成、回归网就位之后 |
| Q-06 | **P2** | **引入 Alembic 作为版本化迁移**（与 SQLAlchemy 2.0 同源，不换栈），先把现有 33 条补列与 2 个 V2 迁移固化为 baseline，再逐步退役手写脚本 | 全局 | 高 | 消除 Windows 无 `flock` 时破坏性迁移重复执行风险 | 多实例部署或团队人数上升时 |
| Q-07 | **P2** | **统一 `sys_agent_job.status` 词表**：`agent.py` 写 `success`、`paper_compose.py` 写 `succeeded`，统一为单一常量并补一条静态断言 | 模块 | 低 | 消除状态判定漏网 | 长任务改造时 |
| Q-08 | **P3** | 清理零引用资产：`ai-badge` / `fallback-tip` 样式、`permissions.menus`、`backend/VERSION` 空目录、仓库内 `deploy_scripts/` 残留脚本 | 单点 | 低 | 减少误读 | 低优先级窗口 |

### 6.4 交互体验

| 编号 | 优先级 | 建议 | 影响范围 | 成本 | 预期收益 | 适用场景 |
|---|:---:|---|---|:---:|---|---|
| U-01 | **P0** | 修复试卷报告中的**交互硬伤**：预览态编辑抽屉「确定」不回写（P0-2）、编辑页保存按钮恒灰（P1-2）、「重构大题」静默清空未保存修改（P1-3） | 模块 | 中 | 直接恢复 3 个「看起来能用实际不可用」的功能 | 教师组卷 |
| U-02 | **P1** | **长任务离开页面保护**：`AgentGenerate` / `PaperWizard` / `LessonPlanManage` 增加 `beforeunload` + 路由离开确认（复用 `confirm.js`），并在返回后恢复轮询 | 模块 | 低 | 消除「切走就丢进度」；配合 F-04 | AI 长任务 |
| U-03 | **P1** | **把已定义的 `fallback-tip` 真正用起来**：所有读 `is_fallback` 的页面统一渲染「AI 降级为规则引擎」提示条，避免用户把降级结果误认为 AI 产出 | 全局 | 低 | 样式已存在，零新增设计；提升 AI 结果可信度 | 未配 Key / 熔断时 |
| U-04 | **P1** | **导出按钮统一走 `ExportButton`**（当前 1/38 引用），内置 loading、禁用重复点击、失败 `toastIfUnhandled` | 全局 | 中 | 消除 38 处重复实现；导出 300s 期间界面不再「无反馈」 | 所有导出入口 |
| U-05 | **P2** | **错误状态页内重试**：已有全局错误红条与 `humanizeError`，补一个页面级 `<ErrorState>`（重试按钮 + 错误码），用于报表/图表加载失败 | 全局 | 中 | 减少「整页空白只能刷新」 | 弱网、后端 500 |
| U-06 | **P2** | **AI 结果「空正文」显式提示**：后端 `status="empty"` 已在日志区分，前端需展示「模型未返回内容，可重试或切换模型」而非空卡片 | 模块 | 低 | 让预算耗尽/难度过高的问题对用户可见 | 已接 LLM |

### 6.5 UI 布局专项

**当前基准**：40 个页面统一 `.page-container / .page-header / .filter-card / .stat-card` 三段式；主题令牌集中在 `styles/index.css`（`--el-color-primary: #2f6fd0`、`--page-bg`、`--card-shadow`）；7 组菜单按前缀匹配；`@media` 仅 11 处 / 10 个文件；无暗色主题；`index.html` 禁用缩放。

| 维度 | 现状问题（证据） | 建议 | 优先级 | 成本 | 预期收益 |
|---|---|---|:---:|:---:|---|
| **信息层级** | `MainLayout` 面包屑只显示当前 `meta.title`，无父子层级；7 组菜单平铺，**学生端 15 个页面全挤在「学习中心」一组**；`stat-card` 在 25 个页面被 scoped 重定义 | ① 面包屑改为「分组 / 当前页」两级；② 学习中心按「学 → 练 → 测 → 评」拆 4 个二级分组（沿用 `prefixes` 机制，不动路由）；③ 把 `.stat-card` 也收敛为全局唯一来源（`.stat-value` 已成功收敛，同法复用） | **P1** | 中 | 学生端菜单从 15 项平铺降为 4×3~4 项；消除 61 处 `.stat-card` 分散定义 |
| **页面结构** | 4 个页面 >1300 行，单页塞「列表 + 筛选 + 表单弹窗 + AI 抽屉」；试卷域 4 套入口语义重叠 | ① 超长页按「主列表 / 详情抽屉」拆成独立子组件（不改路由、不改接口）；② 试卷域明确四入口职责边界：`PaperManage`=列表与批量、`PaperWizard`=新建、`PaperEdit`=编辑、`CustomPaper`=学生自测，并在页头用一行文案说明；③ 高频筛选区折叠，默认只露 2 个条件 | **P1** | 中 | 降低单页认知负荷；直接缓解「A 入口能力假设被 B 入口继承」 |
| **视觉一致性** | `#2f6fd0` 字面值在 8 个视图的 ECharts 色值中重复；`MasteryMap.vue` 仍用 Element 默认 `#409eff`；侧栏 `#1f2d3d` 硬编码在 `MainLayout` 常量与样式两处；`check_css_tokens` 只拦自引用，不拦硬编码重复 | ① 扩展 `--chart-primary/weak/strong` 与 `--menu-bg` 令牌，ECharts 用 `getComputedStyle` 取色；② 给 `check_css_tokens.py` 增加「品牌色字面量白名单外命中即告警」规则（沿用其现有失败条件，不新写脚本） | **P1** | 中 | 一次换色无需改 10 个文件；避免 CSS 自引用事故重演 |
| **响应式适配** | 47 视图仅 10 个有断点；65 张 `el-table` 无移动端策略；`user-scalable=no` 违反可访问性；断点值分散（768 / 900 / 991 / 992px） | ① 定义 3 个断点 token（`<768` / `768–1024` / `>1024`）并统一到 `index.css`；② 表格在 `<768` 切换为卡片列表（可用 `TableEmpty` 同款插槽思路新增 `TableCards`）；③ 移除 `maximum-scale/user-scalable` 限制；④ 优先补学生端 15 页（移动使用概率最高） | **P2** | 中 | 移动端从「侧栏收起但表格溢出」变为可用；消除 4 套不一致断点 |
| **操作流程** | 组卷向导多步无草稿保存 / 离开确认（报告 P1-8）；破坏性操作已统一 `confirm.js`（26 文件引用、裸 `ElMessageBox`=0，这是优点）；导出无进度反馈 | ① 向导增加 `localStorage` 草稿 + 「继续上次组卷」入口（数据不出本机，符合现有前端状态方案）；② 每步显示「第 N/共 M 步」进度；③ 导出按钮统一 loading（U-04） | **P1** | 中 | 长流程中断不再从头开始；与 P0-2 抽屉回写修复配套 |

---

## 7. 分批实施路线（每批有明确准入条件）

**第 1 批 · 止血（P0，准入：无）**
`Q-01 补回归用例` → `F-01 单一 backlog` → 按试卷报告 §0.4 顺序修 P0-1（SSRF/导出 500）、P0-2、P0-3、P0-4 → `U-01 交互硬伤` → `P-01 全局并发闸门`。
**验收**：35 项中 P0×4 全部有对应用例且通过；`npm test` / `pytest` / `functional_runner` 全绿；四层一致性 OK。

**第 2 批 · 补网（P1，准入：第 1 批通过）**
`P-02 / P-05 / P-06 门禁接线`、`Q-02 / Q-03 文档治理`、`P-03 / P-04 收敛`、`F-02 / F-03 / F-04`、`U-02 / U-03 / U-04`、UI 布局五项中的「信息层级 / 视觉一致性」。
**验收**：`auto_ship.sh` 本地一次运行即等同 CI；行为回归从 0 提升到覆盖 P0/P1 数据一致性链路。

**第 3 批 · 拆边界（P2，准入：第 2 批稳定运行一个版本）**
`Q-04 契约层`、`Q-05 拆 paper_compose.py`、`Q-06 Alembic`、`F-05 导出异步化`、`Q-07 / Q-08`、响应式改造。
**注意**：`Q-05/Q-06` 必须在回归网就位后再做，否则「改一处、跑全量」会重演 `docs/E2E_STABILITY_REVIEW.md` 记录的循环。

---

## 8. 明确排除的方案（避免引入无关方案）

| 排除项 | 理由（与现有约束冲突） |
|---|---|
| 后端迁移 Go / Rust（已有 ADR-001 讨论） | 推翻 FastAPI + SQLAlchemy 全栈，35 项已知问题未修时迁移等于带着债务重写 |
| 换 PostgreSQL / 引入 Redis / MQ | 破坏「2 核 4G 单镜像一键起」的产品前提；当前瓶颈是单 worker 与同步 LLM，不是数据库类型 |
| 服务拆分 / 多副本 / K8s | 现有 `supervisord + nginx + 1 worker` 是刻意设计；进程内限流桶与 RAG 全局集合尚未为多副本就绪 |
| 前端整体 TypeScript 化 / 换 UI 库 | 47 个视图重写成本极高，且与「保持现有技术栈」冲突；`unplugin` 按需引入已稳定运行 |
| 恢复已删除的 864 项 e2e 套件 | `docs/E2E_STABILITY_REVIEW.md` 已复盘其「改一处、跑全量」的不可持续性；应改用 Q-01 的定向接口级用例 |
| 一次性开启全部 lint 规则 / 全量补契约 | `lint_gate` 注释已论证「一次接入几百条告警，团队会直接关掉」；应沿棘轮逐批收敛 |
| 引入新的图表库 / 状态管理库 / 组件库 | ECharts 按需注册、Pinia 单 store、`confirm.js` 已够用；问题是复用率而非选型 |

---

## 9. 附：核查口径

| 指标 | 实测值 | 取证方式 |
|---|---:|---|
| 后端 `.py` / 行数 | 92 / 36,993 | `os.walk` + 逐行计数 |
| 前端 `.vue` / 行数 | 54 / 23,103 | 同上 |
| ORM 表 | 52 | `grep __tablename__ backend/app/models/*.py` |
| 路由装饰器 | 282 | `grep -E "@(router\|...)\.(get\|post\|put\|delete)"` |
| 前端 API 方法 | 268 / 14 个对象 | `api/index.js` 逐行核对 |
| 静态门禁 | 17 道源码扫描（19 个脚本，含 2 个未接入） | `tools/` 清单 + CI/auto_ship 调用点比对 |
| 自动化断言 | pytest 58 / vitest 76 / 接口冒烟 114 / verify 145 项 | `qa_audit_suite.py`、`__tests__/`、`FUNCTIONAL_TEST_RESULTS.json`、CI |
| 文档 | 37 份 `.md`（docs 23 + audit-reports 14） | `find` |
| 版本状态 | 2.5.19，`8abab94` 仅 VERSION + 1 份报告 | `git show --stat` |
