# 新芽学堂（edu-ai-platform）Bug 报告

> 报告依据：qa-bug-reporting（七段式）。本次审计聚焦 backend/app 核心模块，结合代码精读与既有坑位记忆交叉验证。
> 严重程度 / 修复优先级采用 P0–P3。版本：仓库 VERSION；环境：生产 Ubuntu 24.04 / 本地 Windows Docker Desktop。
> 共 12 个待修复缺陷（BUG-001 ~ BUG-017 中 OPEN 项），另 9 项历史坑位已 VERIFIED-FIXED（见 CODE_STRUCTURE_AND_RISK.md，建议补 pytest 固化）。

---

## BUG-001 编辑试卷时 usage_count 只增不减，多次改卷后选题偏好失真

- **基本信息**
  - Bug标题：[组卷] 编辑试卷后题目 usage_count 只增不减导致去重排序失真
  - 严重程度：P2
  - Bug类型：数据一致性 / 计算
  - 发现版本：v2.1.x
  - 环境信息：所有环境（逻辑缺陷，与部署无关）
- **前置条件**
  1. 存在一份已下发/已组卷的试卷 P，含 N 道题。
  2. 这些题的 `usage_count` 已有基线值。
- **复现步骤**
  1. 教师首次组卷保存 P，`_write_items` 对每道新题 `q.usage_count += 1`（paper_compose.py:776）。
  2. 教师再次编辑 P（移除 2 题、新增 2 题），`_write_items` 对新增 2 题再 `+1`。
  3. 观察被移除的 2 题：`PaperItem` 被 `DELETE`（paper_compose.py:802-804），但**删除分支没有任何 `usage_count -= 1`**。
  4. 多次编辑后查看 `Question.usage_count`。
- **预期结果**
  `usage_count` 反映"当前被多少试卷引用"，编辑应与引用数一致增减。
- **实际结果**
  `usage_count` 单调递增，删除旧题项从不回退。编辑 5 次后计数虚高约 5×题量。
- **根因推测**
  `_write_items` 的删除分支（步骤 4）只做 `PaperItem.__table__.delete()`，未对对应 `Question.usage_count` 做对称递减。而 `compose()` 的"避免近 N 次重复 / 同知识点限流"均依赖 `order_by(Question.usage_count.asc())`，计数失真直接污染选题公平性。
- **影响评估**
  - 影响功能：智能组卷选题偏好、知识点限流。
  - 影响用户：教师（出卷质量下降，热门题被永久降权）。
  - 影响程度：一般（不丢数据、不越权，但长期累积后组卷结果不可信）。
  - 修复优先级：P2。

---

## BUG-014 难度归一化在小数占比下三档之和可能不等于 100

- **基本信息**
  - Bug标题：[组卷] normalize_difficulty 小数占比 rounds 后合计可能非 100
  - 严重程度：P3
  - Bug类型：计算 / 校验
  - 发现版本：v2.1.x
  - 环境信息：所有环境
- **前置条件**
  1. 前端传入难度分布为小数且近似合计 100，例如 `{"easy":33.34,"medium":33.33,"hard":33.33}`。
- **复现步骤**
  1. 调用 `paper_compose_service.normalize_difficulty({"easy":33.34,"medium":33.33,"hard":33.33})`。
  2. 对返回 dict 求和。
- **预期结果**
  三档之和为 100（如 34/33/33 或 33/34/33）。
- **实际结果**
  进入 `abs(total-100)<0.01` 分支后直接 `int(round(v))`：`round(33.34)=33`、`round(33.33)=33`、`round(33.33)=33`，合计 **99**。下游 `split_by_difficulty` 与前端展示的难度占比之和显示为 99%。
- **根因推测**
  `normalize_difficulty` 在"已是百分制"分支只做 `int(round(v))`，未像"非百分制"分支那样用余数补给补齐到 100。当小数四舍五入后各档损失凑成整数差时，合计漏 1 点。
- **影响评估**
  - 影响功能：难度分布报告、按难度抽题配额。
  - 影响用户：教师（看到 99% 占比，轻微但不符预期）。
  - 影响程度：轻微。
  - 修复优先级：P3。

---

## BUG-003 42/59 学科无任何知识点，AI 出题与掌握度分析整体失效

- **基本信息**
  - Bug标题：[知识点] 71% 学科无知识点数据，AI 出题无法挂靠、掌握度地图失效
  - 严重程度：P1
  - Bug类型：数据 / 业务
  - 发现版本：v2.1.x
  - 环境信息：生产数据（种子缺口）
- **前置条件**
  1. 59 个学科中 42 个（71%）在 `KnowledgePoint` 表无任何行。
  2. 这些学科由 AI 出题或学生练习产生作答。
- **复现步骤**
  1. 选择任一无知识点学科，调用 AI 出题 `QuestionGeneratorAgent.execute`。
  2. 观察返回题目 `knowledge_point_id` 与"掌握度地图 / 复习计划"统计。
- **预期结果**
  系统对"无知识点学科"有明确降级提示，且掌握度分析能给出合理兜底（如按章节/题型）。
- **实际结果**
  `knowledge_point_id` 恒为 0/None；掌握度地图与复习计划按知识点维度统计时整体为空，教师侧表现为"AI 生成成功但知识点全空 / 复习计划无内容"，无明确提示。
- **根因推测**
  种子数据 `init_db.KNOWLEDGE_POINTS` 仅覆盖 17 个学科、97 个知识点；level3 仅补有教研内容的 75 个章节。数据缺口未在前端/出题链路做兜底提示。
- **影响评估**
  - 影响功能：AI 出题挂靠、掌握度地图、复习计划（核心 AI 学习价值）。
  - 影响用户：全体使用这 42 个学科的教师与学生。
  - 影响程度：严重（核心链路业务价值受损，但不崩服务）。
  - 修复优先级：P1。

---

## BUG-005 限流冷却期 /health 仍报 llm_enabled=true，可观测性盲区

- **基本信息**
  - Bug标题：[LLM] 限流冷却期间 /health 不反映降级，运维误判 AI 正常
  - 严重程度：P2
  - Bug类型：可观测性 / 时序
  - 发现版本：v2.1.x
  - 环境信息：触发 429 限流后
- **前置条件**
  1. LLM 配置正确且 `is_available()` 返回 True。
  2. 连续触发 429，进入 `rate_limit` 冷却（breaker 状态为 rate_limit）。
- **复现步骤**
  1. 制造限流，使 `llm_breaker` 处于 rate_limit 冷却。
  2. `GET /api/v1/health` 观察 `llm_enabled`。
  3. 发起一次真实 AI 调用观察 `is_fallback`。
- **预期结果**
  /health 至少暴露冷却状态（如 `llm_cooldown_remaining`），使运维知道 Agent 正在降级。
- **实际结果**
  `is_available()` 不反映冷却态，`/health` 仍报 `llm_enabled=true`；但 `chat()` 实际返回 `is_fallback=true` 走规则引擎。状态接口与真实行为不一致。
- **根因推测**
  `is_available()` 设计上"已配置密钥即视为可用，冷却只让 get_client 短路"，/health 复用该语义，未读取 breaker 的 rate_limit 状态。
- **影响评估**
  - 影响功能：运维监控、告警。
  - 影响用户：运维（误判 AI 正常，延误限流处理）。
  - 影响程度：一般。
  - 修复优先级：P2。

---

## BUG-006 decode_token(db=None) 跳过吊销检查，漏传 db 致登出失效

- **基本信息**
  - Bug标题：[认证] decode_token 未传 db 跳过 JWT 吊销，存在登出失效契约风险
  - 严重程度：P0
  - Bug类型：安全 / 越权
  - 发现版本：v2.1.x
  - 环境信息：所有环境
- **前置条件**
  1. 用户已登出，其 jti 已写入 `sys_revoked_token`（expire_at >= now）。
  2. 某认证依赖调用 `decode_token(token)` 未传入 `db`。
- **复现步骤**
  1. 用户正常登录后登出（revoke_token 落库）。
  2. 用已被吊销的 access token 请求某仅依赖 `decode_token(token)`（无 db）的接口。
  3. 对比传入 db 的调用。
- **预期结果**
  无论是否传 db，已吊销令牌都应被拒绝（认证链路必须校验吊销）。
- **实际结果**
  `db is None` 分支直接返回 payload（代码注释明确"认证链路必须传 db"）。若存在任一依赖漏传 db，登出/改密后旧 token 仍可用，等于登出失效。
- **根因推测**
  `decode_token` 保留 `db=None` 兼容分支（纯解析场景），但认证依赖若误用该分支即绕过吊销。正确性是"调用方自觉"，无编译/运行期强制。
- **影响评估**
  - 影响功能：登录态吊销（登出、改密、异地登录处置）。
  - 影响用户：全体用户（账户安全）。
  - 影响程度：严重（潜在越权/会话冒用）。
  - 修复优先级：P0（建议回归全部认证依赖是否均传 db；或改为默认必须 db，纯解析另立函数）。

---

## BUG-007 Windows Docker 9p 挂载下 sys_config 读取失败静默回落

- **基本信息**
  - Bug标题：[配置] SQLite 9p 绑定挂载仅首个连接可用，sys_config 静默回落 env
  - 严重程度：P2
  - Bug类型：环境 / 数据
  - 发现版本：v2.1.x
  - 环境信息：Windows Docker Desktop 绑定挂载（非命名卷）
- **前置条件**
  1. 本地用 `docker run -v ./data:/app/data` 绑定挂载（9p 文件系统）。
  2. 多个独立 `SessionLocal()` 并发读 sys_config。
- **复现步骤**
  1. 在 Windows Docker 绑定挂载下启动服务。
  2. 触发 `_get_db_value`（每次新建 SessionLocal 读 sys_config）。
  3. 观察 LLM 配置是否读取到 DB 真实值。
- **预期结果**
  sys_config 读取失败应明确告警并区分"未配置"与"读取失败"，不得误以为 DB 配置生效。
- **实际结果**
  9p 仅允许首个物理连接，后续连接报 `unable to open database file`；`_get_db_value` 的 `except` 静默回落到 `settings`/env，LLM 配置可能与 DB 真实配置矛盾且无明显提示。
- **根因推测**
  SQLite WAL 需要 -wal/-shm 旁文件与 POSIX 锁，9p 不完整支持多连接。生产用命名卷（Linux ext4）不触发，但本地 Windows Docker 开发环境会静默误配。
- **影响评估**
  - 影响功能：AI 配置、系统参数读取。
  - 影响用户：本地开发者 / 本地部署。
  - 影响程度：一般（生产无影响）。
  - 修复优先级：P2。

---

## BUG-008 部署脚本 LLM 配置可能与 DB 真实配置漂移

- **基本信息**
  - Bug标题：[部署] 部署脚本 LLM 变量来源若与 DB 不一致将静默错配（需核查）
  - 严重程度：P2
  - Bug类型：运维 / 校验
  - 发现版本：v2.1.x
  - 环境信息：仓库外部署脚本（deploy_run.py，不在 git 内）
- **前置条件**
  1. 生产 DB 的 sys_config 已配置真实 LLM（provider/model/key）。
  2. 部署脚本读取的配置源与 DB 不一致。
- **复现步骤**
  1. 核查 `deploy_scripts/deploy_run.py` 当前 LLM 变量来源。
  2. 若脚本写死或读 .env 而 .env 与 DB 不同，部署后观察 `/agent/status` 与 DB 配置。
- **预期结果**
  部署后运行态 LLM 配置与 DB sys_config 完全一致（单一真源）。
- **实际结果**
  历史曾写死 `LLM_ENABLED=false`+deepseek，与 DB 真实配置矛盾（定时炸弹）。当前实现声称改读 .env，但 .env 与 DB 任何漂移都会让"AI 配置"页面与运行时行为不一致。
- **根因推测**
  LLM 配置存在"DB sys_config 优先、settings/.env 兜底"双来源，部署脚本若独立提供一份兜底值即可能覆盖/误导。
- **影响评估**
  - 影响功能：AI 配置一致性。
  - 影响用户：运维 / 生产可用性。
  - 影响程度：一般（依赖脚本当前实现，需现场核查确认）。
  - 修复优先级：P2（建议核查脚本并加部署后一致性自检）。

---

## BUG-009 并发 AI 出题落库后 id 回填按 id 倒序可能错配真实题目

- **基本信息**
  - Bug标题：[出题] 并发落库后按 Question.id desc 回填 id 易错配他请求题目
  - 严重程度：P1
  - Bug类型：并发 / 数据
  - 发现版本：v2.1.x
  - 环境信息：多 worker / 并发 AI 出题请求
- **前置条件**
  1. 两个 AI 出题请求几乎同时 `execute(save=True)` 并提交。
  2. 每个请求生成 saved 道题。
- **复现步骤**
  1. 并发发起两个出题请求 A、B（各 saved=5）。
  2. A 提交后、B 提交后，A 用 `select(Question.id).order_by(desc).limit(5)` 回填 id。
  3. 核对 A 返回的 `questions[].id` 是否都属于 A 生成的题目。
- **预期结果**
  A 返回的 id 精确对应 A 落库的题目（应改用 `db.refresh(q)` 逐对象取 id）。
- **实际结果**
  若 B 的提交发生在 A 的 `commit()` 与 A 的回填查询之间，A 取到的 5 个最高 id 可能包含 B 的题目，导致 A 的 `questions[].id` 与真实题目错配，后续 `index_question` 索引错乱、组卷引用错位。
- **根因推测**
  `question_agent.execute` 落库后未用 ORM `db.refresh` 取主键，而是用"最近 N 个最高 id"反推，依赖"本请求独占最高 id"的不变量，并发下不成立。
- **影响评估**
  - 影响功能：AI 出题结果正确性、向量索引、智能组卷引用。
  - 影响用户：教师（偶发但题目错乱，难排查）。
  - 影响程度：严重（数据错配，需并发触发）。
  - 修复优先级：P1。

---

## BUG-010 无 alembic，历史库无法平滑迁移（如 difficulty_ratio 列类型变更）

- **基本信息**
  - Bug标题：[迁移] 仅依赖 create_all+贴源迁移，历史库升级存在风险
  - 严重程度：P2
  - Bug类型：数据迁移
  - 发现版本：v2.1.x
  - 环境信息：需升级的历史 SQLite 库
- **前置条件**
  1. 历史库 `Paper.difficulty_ratio` 为 `varchar(64)` 且已存超长值。
  2. 新代码模型改为 `Text`。
- **复现步骤**
  1. 对历史库执行 `create_all` / `db_migrations`。
  2. 观察列类型是否平滑变为 Text、超长值是否保留。
- **预期结果**
  列类型变更可平滑执行，存量数据不丢。
- **实际结果**
  alembic 未初始化，仅靠 `create_all`（对已有表不 alter）+ 手写 `db_migrations` 贴源迁移。新库自动生效，但历史库若已有 `varchar(64)` 且含超长 JSON，迁移脚本若未覆盖该 alter 则残留旧类型或迁移失败。
- **根因推测**
  项目早期未引入迁移框架，`create_all` 对既有表惰性，演进依赖人工补迁移。
- **影响评估**
  - 影响功能：版本升级、数据兼容性。
  - 影响用户：运维 / 升级过程。
  - 影响程度：一般（当前新建库无碍，历史库升级需人工核验）。
  - 修复优先级：P2。

---

## BUG-015 七年级物理为死数据，从未落库却误导维护

- **基本信息**
  - Bug标题：[数据] init_db 七年级物理知识点因 sub_map 取不到学科而从未落库
  - 严重程度：P3
  - Bug类型：数据完整性 / 校验
  - 发现版本：v2.1.x
  - 环境信息：种子初始化
- **前置条件**
  1. 国家课程物理自八年级起，七年级本无物理。
  2. `init_db.KNOWLEDGE_POINTS[7]["物理"]` 存在死数据。
- **复现步骤**
  1. 检查 `KnowledgePoint` 表中 grade_id=7 且学科为物理的行。
  2. 检查 `sub_map.get()` 是否能取到七年级物理。
- **预期结果**
  七年级不应有物理知识点；若有应经正常学科映射落库。
- **实际结果**
  `sub_map.get()` 取不到学科，该行从未落库，成为死数据，误导维护者以为"七年级有物理"。
- **根因推测**
  种子数据未随"七年级无物理"的国家课程规则清理；`sub_map` 仅含真实配置学科。
- **影响评估**
  - 影响功能：种子数据正确性、维护可读性。
  - 影响用户：维护者。
  - 影响程度：轻微。
  - 修复优先级：P3。

---

## BUG-016 GET /edu/subjects 不传 grade_id 返回 60+ 同名学科

- **基本信息**
  - Bug标题：[契约] 学科列表不传 grade_id 返回大量同名，前端须传 distinct
  - 严重程度：P3
  - Bug类型：契约 / 校验
  - 发现版本：v2.1.x
  - 环境信息：前端下拉场景
- **前置条件**
  1. 多年级配置了同名学科（如各年级都有"数学"）。
- **复现步骤**
  1. `GET /api/v1/edu/subjects`（不带 grade_id）。
  2. 对比 `GET /api/v1/edu/subjects?distinct=true`。
- **预期结果**
  纯下拉场景应有去重开关，且契约明确。
- **实际结果**
  不传 grade_id 返回 60+ 同名学科；纯下拉必须显式 `?distinct=true`，前端若漏传则渲染重复学科。
- **根因推测**
  `Subject` 唯一键为 `(grade_id, name)`，学科名跨年级重复；接口未对"精确场景"默认去重。
- **影响评估**
  - 影响功能：前端学科下拉。
  - 影响用户：教师（下拉重复）。
  - 影响程度：轻微。
  - 修复优先级：P3。

---

## BUG-017 无单题 GET 详情端点，e2e 只能 keyword 筛选

- **基本信息**
  - Bug标题：[可测试性] 缺单题详情端点，回归只能 keyword 筛选且易脆
  - 严重程度：P3
  - Bug类型：可测试性 / 契约
  - 发现版本：v2.1.x
  - 环境信息：测试 / 接口
- **前置条件**
  1. 需要按 id 精确获取某题详情。
- **复现步骤**
  1. 尝试 `GET /api/v1/question/{id}`。
  2. 观察是否存在。
- **预期结果**
  提供单题详情端点，便于精确断言与前端详情页。
- **实际结果**
  仅有列表 + keyword 筛选；e2e 用列表 keyword 筛选替代，精确场景脆弱。
- **根因推测**
  接口设计偏列表，未补单资源 GET。
- **影响评估**
  - 影响功能：测试稳定性、前端详情。
  - 影响用户：开发 / 测试。
  - 影响程度：轻微。
  - 修复优先级：P3。

---

## BUG-018 effective_status / apply_timeout 不透传 now 注入，边界判定可重现 CI 时序抖动

- **基本信息**
  - Bug标题：[长任务] effective_status 未转发 now 参数，超时边界判定不可确定性测试
  - 严重程度：P3
  - Bug类型：可测试性 / 一致性
  - 发现版本：v2.1.x
  - 环境信息：运行 pytest / CI（实测发现）
- **前置条件**
  1. `is_timed_out(status, created_at, *, now=None)` 支持 `now` 注入（边界严格 > 语义依赖注入）。
  2. `effective_status(status, created_at, *, timeout_seconds=300)` 与 `apply_timeout(job, data)` 是 API 实际使用的包装层。
- **复现步骤**
  1. 试图对 `effective_status` 注入固定 `now` 做边界断言。
  2. 观察调用签名。
- **预期结果**
  `effective_status` / `apply_timeout` 与底层 `is_timed_out` 一致地支持 `now` 注入，使超时边界可被确定性测试（避免 CI 慢机偶发红，记忆中曾 47/48）。
- **实际结果**
  `effective_status(status, created_at, *, timeout_seconds=300)` 不接受 `now`；内部 `is_timed_out(...)` 调用使用真实 `now_local()`，边界只能靠真实时钟，存在时序抖动类偶发失败风险。
- **根因推测**
  `effective_status` 包装 `is_timed_out` 时未透传 `now`（原函数新增 `now` 注入时未同步到包装层），属于"修复只做了一半"的遗漏。
- **影响评估**
  - 影响功能：长任务超时判据的测试确定性。
  - 影响用户：CI 稳定性（维护者）。
  - 影响程度：轻微。
  - 修复优先级：P3（建议补 `now` 形参透传，零行为变更）。

---

## 附录：已 VERIFIED-FIXED 的高风险历史坑位（建议补 pytest 固化）

以下项本次审计确认代码已实现修复，但其正确性目前主要靠注释约束，建议补对应 P0/P1 用例（见 TEST_CASES.csv）以防回归：

| Bug(历史) | 现象 | 修复位置 | 对应用例 |
|-----------|------|----------|----------|
| 推理模型 max_tokens 截断正文为空 | AI 出题静默降级为题库复用 | config.LLM_MAX_TOKENS=8192 | TC_LLM_JSON_001 |
| breaker 多进程/monotonic/原子streak | 冷却失效、跨进程不同步 | services/llm_breaker.py | TC_LLM_BRK_004~007 |
| 模型编造知识点 id 触发整批外键失败 | 出题 500 | question_agent._resolve_kp_id | TC_QGEN_FK_009~011 |
| 改卷 Answer 级联清空（920 分蒸发） | 学生作答全丢 | paper_compose._write_items | TC_COMP_WRITE_019 |
| 验证码可短路绕过 / 非一次性 | 登录爆破 | security.verify_captcha + CAPTCHA_ENFORCED | TC_AUTH_CAP_029/032 |
| JWT 吊销 exp 误用 12h / 刷新令牌无 jti | 登出等于没登出 | security.revoke_token/_token_expiry | TC_AUTH_JWT_027/028 |
| 密码重置传 password 而非 new_password → 422 | 前端改密失败 | auth.reset_password 读 new_password | TC_AUTH_PWD_030 |
