# 试卷模块遗留问题修复报告（第二轮）

> 承接 `PAPER_MODULE_FIX_AND_TEST_REPORT.md`（第一轮 D1~D6）。本文处理第一轮
> 结束时登记的 7 项「发现但未解决」问题。
>
> 时间：2026-10-30　范围：`backend/app/{api,services,agents,core}`、`frontend/src`、`tools`
> 基线：`f235d4f`（2.2.4）→ 本次回归全绿后发版

---

## 一、TL;DR

| # | 遗留问题（第一轮登记） | 本轮结论 | 修复位置 |
|---|---|---|---|
| 1 | 删除试卷**不递减** `Question.usage_count` | **已修**：不是"补一次递减"，而是把记账改成**幂等重算**，覆盖 7 条写入路径 + 一次性订正脚本 | `services/question_usage.py`（新）+ 7 个调用点 + `tools/fix_usage_count.py`（新） |
| 2 | `_normalize_paper_items` 允许**公共库待审题**入卷 | **已修**：判定收口为唯一函数，策略定为「本人题不限状态、他人公共题必须 published」 | `services/question_access.py`（新）+ 2 个调用点 |
| 3 | 无**单题详情**端点，题项编辑要整卷拉取 | **已修**：新增 `GET /question/questions/{q_id}`，支持 `include_answer=false` | `api/v1/question.py` |
| 4 | AI 补题后缩放出现 `6.67` 这类**非整数分** | **已修**：按「分值网格」最大余数分配（1 分 / 0.5 分两档），合计精确 | `services/paper_compose_service.py` |
| 5 | 42 个学科**无知识点数据** | **工具化 + 显式化**：巡检/补种/清理脚本落地，组卷与出题响应新增 `knowledge_point_missing` 标记；**真实考点仍需教研补齐**（数据问题，见第五节） | `tools/audit_knowledge_coverage.py`（新）+ 组卷/出题响应 |
| 6 | 前端 AI 模式仍显示「出题来源」下拉 | **已修**：AI 模式禁用下拉 + 值归位，payload 侧强制 `bank_first` | `frontend/src/views/teacher/PaperWizard.vue`、`utils/paperWizard.js` |
| 7 | 「仅 AI 生成」按大题**串行**调模型，耗时线性增长 | **已修**：按大题并行（默认并发 3），结果按缺口原序合并 | `api/v1/paper_compose.py`、`core/config.py` |

**新增测试**：`verify_paper_module.py` 从 80 → **106 项**（新增 H 组 26 项）；
新增 `verify_ai_fill_parallel.py`（10 项）；前端 `paperWizard.test.js` 从 19 → **22 项**。

---

## 二、逐项：表现 / 触发条件 / 预期行为 / 根因 / 修复

### 问题 1 · 题目引用计数（`usage_count`）与实际引用不一致

**具体表现**

- 手动组卷（`POST /questions/papers`）建出来的卷子，里面的题 `usage_count` 恒为 **0**；
- 复制一份试卷，源卷题目的计数**不变**；
- 删除一份试卷后，原卷题目的计数**不减**；批量删除同样不减；
- 从卷子里移除单题后，该题计数不变；
- 编辑卷子换题时反而会**凭空 +n**（首次给没有题项的卷子补题，`_write_items` 只做插新 +1，没有旧题可减）。

**触发条件**：任何一次手动组卷 / 复制 / 删卷 / 移题 / 首次补题。都不需要并发或异常输入。

**预期行为**：`usage_count` 恒等于「当前引用该题的题项数」——它唯一的消费者是组卷的
`ORDER BY usage_count ASC`（少用优先）。值虚高会让老题被反复抽中，排序策略实质失效。

**根因**：计数器由各写入口**各自记账**，7 条路径口径互不一致（详见
`services/question_usage.py` 模块文档里的矩阵）。记账法本身不可靠：只要有一条路径
漏了，误差就永久累积，而且无法从当前值反推"应该是什么"。

**修复**（不是补一条递减，而是换掉机制）

1. 新增 `services/question_usage.recount_usage(db, question_ids)`：值 = `COUNT(edu_paper_item WHERE question_id = q.id)`。**幂等**——重复调用结果相同，不依赖历史值，因此不会积累误差。
2. 7 个写入点统一改为「改完题项 → flush → 重算涉及的题目 id 并集」：
   `create_paper` / `update_paper`（经 `_write_items`）/ `copy_paper` / `delete_paper` /
   `batch_papers(delete)` / `remove_item` / `compose_save`（同 `_write_items`）+
   `paper_agent` 的两条 AI 落库路径。
3. 删除类路径必须**先快照题目 id 再删**（题项随试卷级联删除后无法反查），
   已封装成 `question_ids_of_paper` / `question_ids_of_papers`。
4. 存量数据用 `tools/fix_usage_count.py` 一次性订正（默认体检模式，`--apply` 才写库）。

**验证**

```
H1-0 新题初始引用数为 0
H1-1 手动组卷计入引用（修复前恒为 0）
H1-2 同一题进第二份卷 → 2
H1-3 删除试卷后引用数回落（修复前只增不减）
H1-4 复制试卷也计入引用
H1-5 移除单题后该题引用数 -1
H1-6 新卷引用题目 D → 1
H1-7 编辑换题：被移除的题归零、新加的题计入
H1-8 批量删除后引用数同步回落
```

订正脚本实测：造 3 题 / 2 卷（真实引用 2、1、0），手工写成 9、0、0 →
`--dry-run` 报「不一致 2 条，存储 9 → 实际 3」→ `--apply` 后复查剩余不一致 **0 条**。

---

### 问题 2 · 公共题库的待审 / 已下架题可以被放进试卷

**具体表现**：知道题目 id 就能把公共题库里 `status=draft`（AI 生成后待审核）或
`status=offline`（已下架）的题加进自己的卷子。卷子照常保存、照常发布，学生会在
考试里遇到一道**尚未审核通过**或**已被撤下**的题。

**触发条件**：`POST /questions/papers` 或 `POST /questions/papers/compose/save` 的
`items` 里带上这类题的 `question_id`。列表接口看不到它们（需靠 id 猜测或从别处获知），
所以不是随手能踩，但组卷引擎之外的人工编辑路径完全没有拦截。

**预期行为**：进入卷面的题必须是「当前用户可用的已发布题」。

**根因**：可用性判定在 `question._normalize_paper_items` 与
`paper_compose._normalize_items` 各写了一遍，两处都只判「公共库 或 本人私有」，
**都没有看 `status`**。这是项目里第二次出现"两套判定并存"（第一次是试卷可见性）。

**修复**

1. 新增 `services/question_access.question_usable_error(q, user_id, is_admin)` 作为唯一判定，
   两个入口都调它。策略按优先级：

   | 场景 | 是否可用 | 理由 |
   |---|---|---|
   | 系统管理员 | 可用 | 排障/修数据需要 |
   | 本人私有题 | 可用，**不限状态** | 教师编辑自己的草稿是合法备课流程，收紧会打断正常使用 |
   | 公共题库题 | 仅 `published` | 待审/下架题不该出现在卷面 |
   | 他人私有题 | 不可用 | 越权 |

2. 第一轮留下的"需要先定策略（是否允许本人 draft 入卷）"在这里给出结论：**允许**。
   理由：`private` 题的 `draft` 只表示"还没整理好"，没有审核语义；限制它没有收益。
3. 组卷的 AI 补题过滤（`_fill_one_gap`）也改用同一函数，保证"补进来的一定存得下"。

**验证**

```
H2-0 教师建公共题被降级为待审核
H2-1 他人待审题入卷被拒（修复前可静默通过）      → 400「题目尚未发布…公共题库仅可使用已发布题目」
H2-2 本人待审题仍可入卷（保留教师备课合法场景）  → 200
H2-3 管理员不受状态限制                          → 200
H2-4 保存组卷与手动组卷同一口径（都拒）          → 400
```

---

### 问题 3 · 没有单题详情端点

**具体表现**：编辑卷子里的一道题，前端只能先 `GET /papers/{id}` 把整卷（含每题答案
与解析）拉下来再挑一条。一份 60 题的卷子改一道题要传回上百条记录。

**触发条件**：任何一次题项编辑。

**预期行为**：能按 id 取单题，且能区分"教师视角（带答案）"与"学生视角（不带答案）"。

**根因**：契约层面一直没设计这个端点（`/questions/{q_id}/duplicates` 有了，
但基础的 `GET /questions/{q_id}` 没有）。

**修复**：新增 `GET /question/questions/{q_id}`

- 鉴权与列表同一口径（公共题或本人私有，管理员不限），**不能出现"列表没有、猜 id 能读"**；
- `include_answer=false` 时把 `answer` / `analysis` 置空，供学生视角使用；
- 路由声明在所有具体 GET（`/questions/stats`、`/template`、`/export`）之后，
  避免 `stats` 被 `{q_id}` 吞掉变成 422。

**验证**

```
H3-1 公共题详情可读且含题干
H3-2 include_answer=false 时不返回答案与解析
H3-3 他人私有题详情 403（防猜 id 枚举）
H3-4 不存在的题目 404
```

---

### 问题 4 · 卷面分值出现 6.67 / 45.25 这类尾数

**具体表现**：组卷时把总分从 15 改成 100，3 道 5 分题被摊成 `33.33 / 33.33 / 33.34`
（或 `6.67` 这类）；把 100 分卷改成 90.5 分，2 道题变成 `45.25 / 45.25`。

**触发条件**：`total_score` 与「题量 × 单题分值」不成整数倍（含 AI 补题后按目标总分缩放）。

**预期行为**：卷面分值应落在教学上可读的网格上（1 分或 0.5 分），且**合计精确**
等于目标总分。

**根因**：`_rescale_scores` 直接按比例缩放再 `round(2)`，把误差丢给最后一题。

**修复**：改为「网格 + 最大余数法」两档：

- 原分值全为整数、目标也是整数 → 以 **1 分**为网格；
- 否则若都能落在 **0.5 分**上 → 以 **0.5 分**为网格（0.5 分小题是常见卷面口径，比强转整数更贴近教学）；
- 更细（0.25 等）或题量多于总分（网格分配必然出现 0 分题）→ 退回比例法。

先 `floor` 再按小数部分从大到小每个补一个网格单位，**合计精确**，不再"把误差丢给最后一题"。
余数相同按原顺序，保证同参数重复调用结果一致。

**验证**

```
H4-1 目标总分 100 时每题都是整数（修复前为 33.33/33.33/33.34）   → [34, 33, 33]
H4-2 合计精确等于目标总分                                        → 100
H4-3 90 分 2 题 → 45/45（无尾差）
H4-4 目标带小数时落在 0.5 分网格上（无 45.25 这类尾数）           → [45.5, 45.0]
H4-5 原分值 2.5 分时按 0.5 网格分配                               → [50.5, 50.0] 合计 100.5
```

---

### 问题 5 · 42 个学科没有知识点，掌握度/复习计划静默失效

**具体表现**：这些学科上 AI 出题的 `knowledge_point_id` 恒为空、题目挂不上考点；
学生掌握度图谱只有"综合"一个桶；复习计划排不出条目。**三者都不报错**。

**触发条件**：选择这 42 个学科中的任意一个做题/组卷/看学情。

**预期行为**：至少让用户知道"这门课还没有知识点数据"，而不是以为 AI 没识别出考点。

**根因**：种子数据 `init_db.KNOWLEDGE_POINTS` 只覆盖有教研积累的学科；
其余学科一条知识点都没有，属于**数据缺口而非代码缺陷**。

**修复（两件事，都不是造假数据）**

1. `tools/audit_knowledge_coverage.py`：巡检覆盖率、导出缺失清单 CSV、
   `--seed-placeholder` 补最小骨架（1 单元 + 2 知识点，`source='placeholder'`）、
   `--purge-placeholder` 一键清除重来。占位节点结构与真实知识点完全一致
   （level / path / code），补齐真实考点时可在同一单元下继续加子级，
   也可按 `source='placeholder'` 精确定位替换。
2. 后端显式化：组卷响应新增 `knowledge_point_missing`，并在 `message` 里给出
   可操作提示（"…尚未维护知识点，本次组卷无法按考点选题…请联系管理员补齐"）；
   `QuestionGeneratorAgent` 的 `execute` / `fallback` 返回值同样带该字段。

**实测数据（临时库，播种后）**

```
年级学科组合总数 : 59
已有知识点的学科 : 17
缺失的学科       : 42
覆盖率           : 28.8%
--seed-placeholder → 已为 42 个学科补占位骨架，共 126 个节点，复查剩余缺失 0
再跑一次           → 没有缺失学科，无需补种（幂等）
--purge-placeholder → 已删除占位知识点 126 条（真实教研数据未受影响）
```

**验证**

```
H5-1 无知识点学科组卷返回 knowledge_point_missing=true
H5-2 同步给出可操作提示（含"尚未维护知识点"）
H5-3 有知识点学科不误报
```

---

### 问题 6 · AI 模式下「出题来源」仍可选，选了 ai_only 会等很久还缺题

**具体表现**：AI 一键组卷页面上，「出题来源」下拉可正常操作。用户选「仅使用 AI 生成」
后提交，同一请求里发生两轮模型调用（解析描述 + 逐大题造题），耗时随大题数线性增长；
而题库里明明有同题型的题也不会用，用户看到的是"等了很久，还缺题"。

**触发条件**：AI 模式 + 把来源选成 `ai_only`（或先在自定义模式选好再切过来）。

**预期行为**：AI 模式的语义是"模型只负责把描述翻译成参数，抽题走确定性引擎"，
来源不应在这里可配。

**根因**：`form.source` 默认 `bank_first` 但下拉没有按模式禁用；`buildComposePayload`
原样透传 `form.source`。

**修复**

1. `PaperWizard.vue`：AI 模式禁用下拉，并在下方给出说明文案；
2. `utils/paperWizard.js`：新增 `AI_MODE_SOURCE='bank_first'`，`buildComposePayload`
   在 AI 模式**强制**发送该值（防止"控件禁用了但残留值仍被提交"）；
3. 切换模式时 `watch` 把 `form.source` 归位，避免"禁用控件显示 ai_only、实际提交 bank_first"
   的界面/行为不一致；
4. 纯 AI 造题能力保留在「自定义参数组卷」模式里。

**验证**（`frontend/src/utils/__tests__/paperWizard.test.js`，vitest）

```
AI 模式固定发送 bank_first，即使表单残留 ai_only
AI 模式残留 bank_only 同样被归位（不能靠"只在选 ai_only 时才改"）
自定义模式原样透传来源（含 ai_only，纯 AI 造题仍可用）
```

---

### 问题 7 · 「仅 AI 生成」耗时随大题数线性增长

**具体表现**：4~5 个大题的卷子选 `ai_only`，最坏耗时可能接近 nginx
`proxy_read_timeout 300s`，请求被网关切断。

**触发条件**：`source=ai_only`（或 `bank_first` 缺口多）且大题数 ≥ 3，生产开启真实大模型。

**预期行为**：总耗时 ≈ **单次最长调用**，而不是"大题数 × 单次耗时"。

**根因**：`_ai_fill_gaps` 用 `for g in plan.gaps` 串行调 Agent。每大题单独调用是
**必须的**（Agent 一次只产一种题型，混着补会把单选题塞进填空题大题），所以不能靠
"合并成一次调用"来优化，只能并行。

**修复**

1. 抽出 `_fill_one_gap(gap, *, user_id, is_admin, grade_id, subject_id, default_diff)`：
   在**独立 `SessionLocal`** 里执行（SQLAlchemy Session 非线程安全），只接收标量参数，
   不把 ORM 对象带进工作线程；异常不外抛，原因通过 `notes` 回传。
2. `_ai_fill_gaps` 用 `ThreadPoolExecutor` 并发执行，**按提交顺序取结果**合并
   （`f.result()` 顺序等待，不是 `as_completed`），因此卷面大题顺序不受线程调度影响。
3. 并发度 `settings.AI_FILL_CONCURRENCY`（默认 3，上限 4，设 1 退回串行）：
   上游模型普遍有速率限制、本项目还有 429 熔断（触发后整站 AI 冷却 30~300s），
   而 SQLite 写锁是库级的，并发再高也压不出吞吐。
4. 并行结束后 `db.commit()` 刷新主 Session 的事务快照 —— 否则主 Session 看不到
   其他连接新提交的题目，后续 `db.get(Question, qid)` 返回 None，表现为
   "补了几题、保存却报题目不存在"。

**验证**（`tools/verify_ai_fill_parallel.py`，注入 0.35s 固定延迟的假 Agent）

```
准备：ai_only 产出 3 个缺口
串行（并发=1）耗时约 3×0.35s                    → 1.42s，补满 6 题
并行（并发=3）耗时接近单次调用而非 3 倍          → 0.36s（加速 4.0×）
并行补满 6 题（结果与串行一致）
合并顺序按大纲原序（不看线程完成顺序）           → single×2, multiple×2, judge×2
大题序号随缺口排序（1→2→3）                      → [1,1,2,2,3,3]
重复调用结果顺序稳定
单大题失败不影响其余大题补齐                     → single×2 + judge×2，multiple 缺席
失败原因如实回传（含大题名）
失败的大题仍留在缺口清单
```

---

## 三、测试覆盖矩阵

| 组 | 主题 | 正常路径 | 边界 | 异常/越权 |
|---|---|---|---|---|
| H1 | 引用计数 | 建卷/复制计入 | 多卷累加到 2、移除后归 1 | 删卷/批量删回落、编辑换题对称 |
| H2 | 待审题入卷 | 本人题 200、管理员 200 | 引导：教师建公共题被降级 | 他人待审题 400（手动 + 组卷保存两条路径） |
| H3 | 单题详情 | 公共题 200 | `include_answer=false` 置空 | 他人私有题 403、不存在 404 |
| H4 | 分值分配 | 100 分 3 题整数 | 90.5 分 → 0.5 网格；2.5 分原值 → 50.5/50.0 | 合计精确校验（含小数场景） |
| H5 | 知识点缺口 | 无知识点学科标记为 true | 有知识点学科不误报 | 提示文案可操作性 |
| — | AI 并行 | 串行基线 / 并行加速 4× | 重复调用顺序稳定 | 单大题失败隔离、原因回传 |
| — | 前端来源 | AI 模式强制 bank_first | 残留 bank_only 也归位 | 自定义模式保留 ai_only |

### 执行结果

| 套件 | 项数 | 结果 |
|---|---|---|
| `tools/verify_paper_module.py` | **106** | 全通过（原 80 + H 组 26） |
| `tools/verify_ai_fill_parallel.py` | **10** | 全通过（加速 4.0×） |
| `tools/verify_paper_v3.py` | 63 | 全通过 |
| `tools/verify_paper_manage.py` | 57 | 全通过 |
| `tools/verify_compose_engine.py` | 全项 | 全通过 |
| 前端 vitest | 36（paperWizard 22） | 全通过 |
| 前端 eslint / build | — | 通过 |
| 五道静态门禁 | 5 | 全绿 |

---

## 四、怎么验证（可复现命令）

```bash
# 后端依赖装好后，全部无需先起服务
export PYTHON_BIN="C:/Program Files/Python312/python.exe"   # Windows

# 1. 功能回归（自起临时服务 + 临时库，106 项）
python tools/verify_paper_module.py

# 2. AI 补题并行（临时库 + 假 Agent，10 项，含耗时对比）
python tools/verify_ai_fill_parallel.py

# 3. 既有三套回归
python tools/verify_paper_v3.py
python tools/verify_paper_manage.py
python tools/verify_compose_engine.py

# 4. 前端
cd frontend && npm run test && npm run lint && npm run build

# 5. 五道静态门禁
python tools/check_hardcoded_host.py && python tools/check_weak_assertion.py \
  && python tools/check_time_contract.py && python tools/check_model_fk.py \
  && python tools/lint_gate.py
```

**运维侧（生产容器内）**

```bash
# 引用计数订正：先体检，确认后再写库
docker exec edu-platform python /app/tools/fix_usage_count.py
docker exec edu-platform python /app/tools/fix_usage_count.py --apply

# 知识点覆盖巡检（先看缺口清单，再决定是否补占位骨架）
docker exec edu-platform python /app/tools/audit_knowledge_coverage.py
docker exec edu-platform python /app/tools/audit_knowledge_coverage.py --csv /tmp/kp_gap.csv
# 只想让链路先跑通（source=placeholder，可一键清除重来）：
docker exec edu-platform python /app/tools/audit_knowledge_coverage.py --seed-placeholder
```

> `--apply` 与 `--seed-placeholder` 都会写库，**执行前先按项目规范做 WAL 热备**
> （`sqlite3` backup API，不能直接 cp）。

---

## 五、仍未解决 / 需运营介入

| # | 事项 | 性质 | 说明 |
|---|---|---|---|
| 1 | 42 个学科的**真实考点** | 数据运营 | 本轮只做到"巡检 + 占位骨架 + 接口显式提示"。占位节点 `source='placeholder'`，不是教研内容；补齐真实知识点后应 `--purge-placeholder` 再补，避免同一学科同时存在两套。 |
| 2 | 知识点无**批量导入模板校验** | 功能增强 | 现有 `/knowledge/template` 只给模板，导入侧对"单元-知识点层级错配"校验较弱，补齐 42 学科时会踩到。建议单独排期。 |
| 3 | `usage_count` 的**并发重算** | 设计取舍 | 重算是幂等的，但两个请求同时改同一道题的引用时，后提交者以自己的快照为准（最终一致）。SQLite 库级写锁下实际是串行，PostgreSQL 上极端并发可能短暂不一致，下一次写入自动修正。 |
| 4 | `ai_only` 仍受**上游限流**约束 | 外部依赖 | 并发 3 是保守值。若上游允许更高并发，可调 `AI_FILL_CONCURRENCY`，但需同时确认熔断阈值（429 → 全站 AI 冷却 30~300s）。 |
| 5 | `_ai_fill_gaps` 并行时**每题一个 Session** | 资源 | 大题很多（>4）时分批执行，峰值连接数 = 并发度，可控；但每次补题都是一个新的 SQLite 写事务，写放大比串行略高。 |

---

## 六、变更文件

**后端**

- `backend/app/services/question_usage.py`（新）· 引用计数唯一维护口
- `backend/app/services/question_access.py`（新）· 题目可用性唯一判定
- `backend/app/api/v1/question.py` · 建卷/复制/删卷/批量删重算；新增 `GET /questions/{q_id}`
- `backend/app/api/v1/paper_compose.py` · `_write_items` 去记账改重算、`remove_item` 重算、`_fill_one_gap` 并行化、`knowledge_point_missing`、可用性判定收口
- `backend/app/services/paper_compose_service.py` · `_rescale_scores` 网格分配
- `backend/app/agents/paper_agent.py` · 两条 AI 落库路径改重算
- `backend/app/agents/question_agent.py` · `subject_kp_missing` + 出题响应标记
- `backend/app/core/config.py` · `AI_FILL_CONCURRENCY`

**前端**

- `frontend/src/views/teacher/PaperWizard.vue` · AI 模式禁用来源下拉 + 值归位
- `frontend/src/utils/paperWizard.js` · `AI_MODE_SOURCE` + payload 强制
- `frontend/src/utils/__tests__/paperWizard.test.js` · +3 项

**工具 / CI**

- `tools/fix_usage_count.py`（新）· 引用计数订正
- `tools/audit_knowledge_coverage.py`（新）· 知识点覆盖巡检 / 补种 / 清理
- `tools/verify_ai_fill_parallel.py`（新）· 并行化验证
- `tools/verify_paper_module.py` · 新增 H 组 26 项
- `.github/workflows/functional-test.yml` · 纳入新脚本、断言数更新
