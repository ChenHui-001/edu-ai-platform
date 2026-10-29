# 新芽学堂（edu-ai-platform）代码结构分析与风险评估

> 分析方法：qa-test-strategy-design（六要素）+ qa-risk-intuition（五大信号 / 风险分数 = 业务影响 × 发生概率 × 技术复杂度，取值域 1/3/5）。
> 审计范围：backend/app 核心模块（agents / services / models / api/v1 / core）。前端与部署脚本仅做契约层面辅助核查。
> 审计日期：2026-10-29　基线版本：v2.1.x（仓库 VERSION 读取）

---

## 1. 项目背景（Strategy 要素一）

- **阶段/团队**：已上线生产、持续迭代的 AI 教育 SaaS。核心链路为「AI 出题 → 智能组卷 → 作答/批改 → 掌握度分析」。团队规模小、节奏快（记忆：曾多次 CI 红灯无人发现、交付纪律依赖四层一致性校验）。
- **技术栈熟悉度**：FastAPI + SQLAlchemy 2.0 + SQLite(WAL) 后端；Vue3 + ElementPlus + Vite 前端；Docker 单镜像（unified）。代码注释密度高、对"已修 bug"的前因后果记录详尽，但**多处关键逻辑依赖注释约束而非测试守护**（如 breaker 六条不变量、_write_items 顺序），注释漂移即回归风险。
- **历史质量**：门禁含 5 道静态检查（check_hardcoded_host / check_weak_assertion / check_time_contract / check_model_fk / lint_gate）+ pytest/e2e。但记忆显示门禁曾连续 3 版红灯无人发现，且反向验证存在 4 类"假绿"，说明**测试信度本身需要被测试**。

## 2. 代码结构与核心模块（Strategy 要素二：风险分析的基础）

```
backend/app/
├── agents/          业务 Agent（LLM 编排）
│   ├── llm.py            LLM 客户端：熔断/冷却、JSON 解析、异步日志
│   ├── base.py           Agent 基类 + call_llm（JSON 解析、降级桥接）+ Orchestrator
│   ├── question_agent.py AI 出题（知识点 FK 三重校验、指纹查重）
│   ├── paper_agent.py / grading_agent.py / lesson_agent.py / study_agent.py / tutor_agent.py / note_agent.py
├── services/        非 Agent 业务服务
│   ├── llm_breaker.py    熔断/冷却跨进程共享层（单行表 + 进程内镜像）
│   ├── agent_job_state.py 长任务超时判据 + 僵尸收割
│   ├── paper_compose_service.py 标准组卷引擎（纯函数式，不写库）
│   ├── paper_export_service.py / grading_service.py / auth_service.py / ai_config_service.py / scheduler.py ...
├── api/v1/         路由层（198 个接口）
│   ├── agent.py / paper_compose.py / question.py / question_ai.py / auth.py / lesson_ai.py / knowledge.py / task.py / report.py ...
├── models/         ORM（edu/question/paper_ext/ops/system/security_cache/task/learning）
├── core/           config / security(JWT+验证码) / database / exception / rate_limit / db_migrations
└── utils/          common(now_local) 等
```

**模块风险分级（按核心链路与已审计代码质量）：**

| 模块 | 复杂度 | 审计结论 | 风险基线 |
|------|--------|----------|----------|
| agents/llm.py + services/llm_breaker.py | 高（并发/状态/分布式） | 修复充分，6 条不变量有注释守护 | 中（残余：/health 不反映冷却） |
| agents/question_agent.py | 中（外键/数据校验） | FK 三重校验已落地，健壮 | 低 |
| services/paper_compose_service.py | 中（计算/算法） | 难度大但实现正确 | 低（normalize_difficulty 小数边界 bug） |
| api/v1/paper_compose.py `_write_items` | 高（数据一致性/CASCADE） | 顺序正确，但 usage_count 只增不减 | 中 |
| services/agent_job_state.py | 中（时序） | 读时判定 + 收割正确，时间可注入 | 低 |
| core/security.py | 高（安全） | JWT 吊销落库、验证码一次性均正确 | 中（decode_token(db=None) 跳过吊销） |
| 知识点数据（init_db / 种子） | 低（静态数据） | 42/59 学科无知识点、七年级物理死数据 | 中（业务影响高） |

## 3. 测试范围（Strategy 要素三）

**测什么**
- LLM 客户端：JSON 解析容错（截断/尾随逗号/噪声）、熔断（auth 永久 vs rate_limit 冷却自恢复）、/health 与真实可用性一致性。
- AI 出题：知识点 id 校验（编造 id→置空/回退）、grade_id 非空回落、指纹查重、落库失败兜底。
- 标准组卷：难度归一化与题量拆分边界、知识点过滤在"放宽"分支不被丢弃、_write_items 作答迁移零丢失、总分重算精度。
- 长任务：超时边界（严格 > 非 >=）、僵尸收割宽限、effective_status 呈现。
- 安全：JWT 吊销（必须传 db）、验证码一次性、密码强度、重置契约（new_password）。
- 数据完整性：usage_count 一致性、知识点缺口降级提示、SQLite 9p 配置回落。

**不测什么（明确排除）**
- 前端 Vue 组件交互（无组件级单测，依赖 e2e 冒烟）。
- LLM 真实模型输出质量（依赖外部 API，e2e 以 LLM_ENABLED=false 规避）。
- 第三方服务（Chroma/RAG、SMTP）正常路径，仅测失败降级。
- 性能压测（并发量级、WAL 锁竞争）仅做逻辑层并发正确性分析，不做基准压测。

## 4. 分层策略（Strategy 要素四）

| 层 | 占比 | 说明 |
|----|------|------|
| 单元 | 60% | 纯函数（normalize_difficulty / split_by_difficulty / extract_json / is_timed_out / _resolve_kp_id）+ 服务层 mock DB |
| 接口 | 30% | FastAPI TestClient 覆盖出题/组卷/改卷/认证关键路径 |
| E2E | 10% | 仅复用既有 run_e2e.sh 阶段，不新增（避免双进程锁库） |

## 5. 手段选择（Strategy 要素五）

- 自动化：纯函数与边界用 pytest；接口用 TestClient + 内存 SQLite。
- 手动：部署脚本与四层一致性校验、Windows Docker 9p 挂载行为需人工/特定环境验证。
- 工具辅助：静态门禁（5 道）继续守护；新增"门禁反向验证"纪律（已知 bug 旧版先验证探针能红，再合并）。

## 6. 风险评估矩阵（qa-risk-intuition）

风险分数 = 业务影响(1/3/5) × 发生概率(1/3/5) × 技术复杂度(1/3/5)；≥45 高 / 15–44 中 / ≤14 低。
`STATUS` 列：`OPEN`=待修复；`VERIFIED-FIXED`=本次审计确认已修复。

### 高风险（≥45）

| 风险 ID | 功能模块 | 类型 | 业务 | 概率 | 复杂 | 分数 | 等级 | STATUS |
|---------|---------|------|------|------|------|------|------|--------|
| RISK-SEC-001 | 认证/JWT吊销 | SEC | 5 | 3 | 3 | 45 | 高 | OPEN |
| RISK-CONC-002 | 出题/落库id回填 | CONC | 3 | 3 | 5 | 45 | 高 | OPEN |

### 中风险（15–44）

| 风险 ID | 功能模块 | 类型 | 业务 | 概率 | 复杂 | 分数 | 等级 | STATUS |
|---------|---------|------|------|------|------|------|------|--------|
| RISK-DATA-003 | 知识点数据缺口 | DATA | 5 | 5 | 1 | 25 | 中 | OPEN |
| RISK-LLM-004 | 限流冷却不反映到/health | TIME/OBS | 3 | 3 | 3 | 27 | 中 | OPEN |
| RISK-DATA-005 | _write_items usage_count 只增不减 | CALC/DATA | 3 | 5 | 1 | 15 | 中 | OPEN |
| RISK-ENV-006 | Windows Docker 9p 下 sys_config 静默回落 | DATA/ENV | 3 | 3 | 3 | 27 | 中 | OPEN |
| RISK-OPS-007 | 部署脚本 LLM 配置与 DB 可能漂移 | VAL/OPS | 3 | 3 | 3 | 27 | 中 | OPEN(需核查) |
| RISK-MIG-008 | 无 alembic，历史库无法平滑迁移 | DATA/MIG | 3 | 3 | 3 | 27 | 中 | OPEN |
| RISK-LLM-009 | 推理模型 max_tokens 截断正文为空 | CALC | 5 | 5 | 3 | 75 | 高 | VERIFIED-FIXED(8192) |
| RISK-LLM-010 | breaker 多进程/monotonic/原子streak/auth优先 | CONC | 5 | 5 | 5 | 125 | 高 | VERIFIED-FIXED |
| RISK-FK-011 | 模型编造知识点id 触发整批外键失败 | VAL | 5 | 5 | 3 | 75 | 高 | VERIFIED-FIXED |
| RISK-CASC-012 | 改卷 Answer 级联清空（920分蒸发） | DATA | 5 | 3 | 5 | 75 | 高 | VERIFIED-FIXED |
| RISK-SEC-013 | 验证码强制化+一次性+JWT exp绝对时刻 | SEC | 5 | 3 | 3 | 45 | 高 | VERIFIED-FIXED |

### 低风险（≤14）

| 风险 ID | 功能模块 | 类型 | 业务 | 概率 | 复杂 | 分数 | 等级 | STATUS |
|---------|---------|------|------|------|------|------|------|--------|
| RISK-CALC-014 | normalize_difficulty 小数 rounds 和≠100 | CALC | 1 | 3 | 3 | 9 | 低 | OPEN |
| RISK-VAL-015 | 七年级物理死数据未落库 | VAL | 1 | 3 | 1 | 3 | 低 | OPEN |
| RISK-VAL-016 | GET /edu/subjects 不传grade_id 返回60+同名 | VAL | 1 | 3 | 1 | 3 | 低 | OPEN(已知契约) |
| RISK-TEST-017 | 无单题 GET 详情端点，e2e 仅靠 keyword | TEST | 1 | 3 | 1 | 3 | 低 | OPEN |

> 注：VERIFIED-FIXED 项仍保留为回归守护对象——其"正确性"当前仅靠注释约束，建议补 pytest 固化（见 TEST_CASES.csv 中对应 P0/P1 用例）。

---

## 7. 资源分配与准入准出（Strategy 要素六/七，仅列本项目采用值）

- **准入**：改动 `agents/llm.py` `services/llm_breaker.py` `api/v1/paper_compose.py` `core/security.py` 任一文件，必须新增/补充对应 pytest 且本地 `ruff check` 通过；纯 docs 不触发 CI。
- **准出（本项目采用值，非模板照抄）**：新增高风险模块单测覆盖率 ≥ 80%；`check_model_fk` 门禁对"模型输出直写外键"零 WARN；e2e 15 阶段全绿；CI 逐 job 确认 success（不依赖本机 curl 代理）。依据：历史 3 版 CI 红灯无人发现，故准出必须"人逐 job 确认"而非"CI 状态绿"。
- **外部依赖风险预案**：Windows Docker 9p 无法建立多连接的场景，本地仅用命名卷/内存库验证，9p 行为记入 ENV-006 待人工环境确认；真实 LLM 调用以 `LLM_ENABLED=false` 隔离，不在 CI 误触。
