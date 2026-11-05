# 全项目审计报告 · 新芽学堂（edu-ai-platform）

> **审计对象**：`E:/project/management/edu-ai-platform`　**版本**：2.5.5（master @ `cb9e792`，工作区干净）
> **审计日期**：2026-11-05　**审计类型**：代码 + 功能全量审计（静态精读 + 动态实测）
> **对比基线**：`docs/ARCHITECTURE_ASSESSMENT_2026-11.md`（2026-11-02，v2.2.19）
> **审计方法**：AST 路由枚举（280 条）+ 逐文件精读 + 前后端全量契约交叉比对 + **本地动态复现**（pytest 探针 / 起真实 uvicorn 跑接口级回归 / 8 道静态门禁 / 43 项前端断言 / 5 个 verify 脚本）
> **局限**：未访问生产服务器、未跑真实大模型（`LLM_ENABLED=false`）、未做压测与并发观测；并发类结论为代码层推断。

---

## 0. 结论摘要

**一句话定性：这仍是一个"工程纪律高于同规模平均水平"的系统——但纪律的覆盖面出现了新裂缝：过去 3 天新增的 30+ 个版本里，功能增长跑在了回归网前面。**

11-02 的评估指出三处结构性缺口：**没有后端自动化测试、没有请求契约层、没有版本化迁移**。本次审计的结论是：

- **三张网一张都没补上，且其中两张在恶化**（裸 `Dict Body` 94 → 99 处；API 层 SQL 437 → 465 处）。
- **测试体系反而被削减**：2026-10-29 的 `5062f18` 删除了整套后端 e2e（15 阶段 / 864 项 + 11 个离线单测 + UI 套件，371 文件 / 21MB）。幸存的 `backend/qa_audit_suite.py` **从未接入任何 CI 工作流**，且现已腐坏（30 项中 1 项失败）。
- **功能侧出现 6 个 P0**：其中 1 个是**已实测复现的不可逆数据丢失**，4 个是**用户点击即失败**，1 个是**改密不能止损**。

| 维度 | 11-02 评分 | 本次 | 判断 |
|---|---|---|---|
| 架构一致性 | 7.0 | **7.0** | 分层意图未变，"胖路由 + 瘦服务"进一步加剧 |
| 安全性 | 8.5 | **7.5** | 鉴权基座仍扎实（270/280 端点有认证），但令牌生命周期与数据删除保护各破一个口子 |
| 可测试性 | 3.0 | **2.5** | 后端自动化覆盖面下降；幸存套件已腐坏且未接线 |
| 可维护性 | 6.5 | **6.5** | 代码本身质量仍高，热点文件更集中（`paper_compose.py` 已 2584 行） |
| 可观测性 | 6.0 | **6.0** | 无变化 |
| 部署成熟度 | 8.5 | **8.5** | 四道发版闸门 + 四层一致性校验，未见退步 |
| 演进弹性 | 5.0 | **5.0** | 未变 |
| **综合** | **7.0** | **6.8** | 当前规模仍匹配；风险随迭代速度上升 |

**最需要立刻处理的三件事**

1. **P0-1**：教师在试卷上「移除一道题」→ 该题**全部学生作答与分数被数据库级联清空**，不可恢复，响应只说"题目已移除"。已用探针实测复现。
2. **P0-2 / P0-3 / P0-4 / P0-5**：四个 AI 组卷与导出功能**用户点击即失败**（解包错层、字段名错、响应类型未豁免、`URLSearchParams` 把 `null` 变 `"null"`）。修复成本均为个位数行。
3. **P1-1**：异步组卷任务的超时阈值（300s）是按旧同步组卷标定的，而新任务自身注释写明最坏"2 轮 × 240s"——**超过 5 分钟的正常组卷会被判超时**，前端立即弹错，而后台线程仍在跑并最终写"成功"，状态来回翻转。

---

## 1. 实况画像（2026-11-05 实测）

| 指标 | 11-02 基线（v2.2.19） | 本次（v2.5.5） | 变化 |
|---|---|---|---|
| 后端代码 | 32,082 行 / 84 文件 | 28,545 非空行 / 84 文件 | 口径不同，基本持平 |
| 前端代码 | 22,943 行 / 68 文件 | 21,629 非空行 / 68 文件 | 基本持平 |
| API 路由 | 272 | **282**（`app.routes`）/ 280（业务端点） | +8~10 |
| 端点鉴权覆盖 | 262/272 = 96.3% | **270/280 = 96.4%** | 持平（10 个公开端点逐个核对均为设计需要） |
| 裸 `Dict[str,Any]=Body` | 94 | **99** | ⬆ 恶化 |
| Pydantic 模型 | 8 | 11（`schemas/` 仍为空目录） | ⬆ 恶化 |
| API 层直接 SQL | 437 | **465** | ⬆ 恶化 |
| 后端 pytest 文件 | 0 | 1（`qa_audit_suite.py`，30 项，**未接 CI**） | — |
| e2e 回归套件 | 15 阶段 / 864 项 | **已删除**（`5062f18`） | ⬇⬇ |
| 前端 vitest | 43 断言 | 43 断言（3 文件） | 持平 |
| 静态门禁 | 5 | 8（+数据确定性 + 2 前端普查 + res.data.data） | ⬆ |
| CI 工作流 | 3 | 3（`ci` / `functional-test` / `docker-publish`） | 持平 |

**热点文件**（非空行）：`paper_compose.py` 2584（较 11-02 的 1893 **+36%**，已成全项目第一热点）｜`question.py` 1684｜`knowledge.py` 1554｜`edu.py` 1168｜`task.py` 1031｜`report.py` 763｜`paper_compose_service.py` 738｜`rag.py` 727。
前端：`KnowledgeManage.vue` 1939｜`QuestionBank.vue` 1573｜`PaperManage.vue` 1200｜`PaperWizard.vue` 1179。

---

## 2. P0 — 必须立刻处理

### P0-1　移除试卷单题会级联清空学生作答（已实测复现）

**位置**：`backend/app/api/v1/paper_compose.py:2183-2219`（删除语句 `:2199`）｜外键：`backend/app/models/task.py:130`

```python
2197:    version_svc.snapshot(db, paper, user.id, change_note="移除题目")
2198:    removed_qid = int(item.question_id)
2199:    db.delete(item)                      # ← 裸删，无任何作答引用检查
...
2218:    return ok({"id": paper.id, "total_score": paper.total_score,
2219:               "item_count": len(items)}, message="题目已移除")
```

```python
# backend/app/models/task.py:129-131
submission_id: Mapped[int] = mapped_column(ForeignKey("edu_submission.id", ondelete="CASCADE"), index=True)
paper_item_id: Mapped[int] = mapped_column(ForeignKey("edu_paper_item.id", ondelete="CASCADE"), index=True)
```

**动态复现**（内存 SQLite + `PRAGMA foreign_keys=ON`，与生产一致）：

```
删除前 edu_answer 行数 = 1
删除后 edu_answer 行数 = 0 | 指向被删题项的作答 = 0
端点返回 message = 题目已移除
```

**影响**：教师删一道题 → 该题全部学生作答、得分、教师评语、AI 评语被数据库级联删除，**不可恢复**（版本快照只存卷面不含作答）。成绩单出现空洞。

**同文件已有正确实现**：`paper_compose.py:1762-1776` 的 `_write_items` 明确记录过这个坑（"实测一份卷 80 条作答、920 分全部归零"），并改为"插新 → 迁移作答 → 删旧"；`question.py:1501-1509` 的老入口也如实上报 `dropped_answers`。**唯独这条新入口退化成了裸删**，且响应文案"题目已移除"与实际后果完全不符。

**修复**：删前 `select count(Answer.id) where Answer.paper_item_id == item_id`，>0 时拒绝并提示走 `/items` 保存路径；或删除后统计并把"作废 N 条学生作答"写进响应 message。

---

### P0-2　试卷管理页「AI 智能组卷」恒判失败，但试卷已真实落库

**位置**：`frontend/src/views/teacher/PaperManage.vue:1191-1199`｜后端 `backend/app/api/v1/agent.py:429-450`

```js
1191:    const res = await agentApi.paperComposer({ request: aiReq.value, save: true, ... })
1195:    const envelope = res?.data || {}      // ← 这已是业务载荷（AgentResult.data）
1196:    const payload  = envelope.data || {}  // ← 又解一层，必然是 {}
1197:    if (!envelope.success) {              // ← 业务载荷没有 success 字段 → 恒为真
1198:      ElMessage.error(envelope.message || '组卷请求失败')
```

后端 `ok()` 信封为 `{code, message, success, data}`，`paper_composer` 返回 `ok(res.get("data"))` → 业务载荷是 `{paper:{...}, saved, tip}`，**既无 `success` 也无嵌套 `data`**。拦截器已把信封返回给组件，故 `res.success` 才是正确读法。

**影响**：`save:true` 时后端已 `db.commit()` 建好试卷，前端却 100% 弹「组卷请求失败」，结果面板空白、「使用结果」拿不到 `paper.id`——**谎报失败 + 诱导用户重复点击建出多份重复卷**。

**修复**：`if (!res.success) … else if (!res.data?.paper?.id) …`；`aiResult.value = res.data || {}`。

---

### P0-3　AI 出题页「智能组卷」必然报「无法识别学科」

**位置**：`frontend/src/views/agent/AgentGenerate.vue:438`（异步分支）、`:468`（同步分支）｜后端 `backend/app/api/v1/agent.py:436`

```js
438:          : { requirement: paperReq.value }      // ← 后端只认 request
468:      res = await agentApi.paperComposer({ requirement: paperReq.value })
```
```python
436:    request = _limited_text(data.get("request"), "组卷要求")
```

`_limited_text(None, ...)` 返回空串而不报错 → 需求被**静默丢弃**；前端又未传 `subject_id`/`grade_id` → `subject_id=0` → `paper_agent.py:83-84` 抛「无法识别学科，请指定学科后再组卷」。而该页面**只有文本框与模板按钮，没有学科选择框**，用户无法自救；异步分支还会把真实原因一并丢掉，只显示"生成失败"。

**修复**：`requirement` → `request`（两处）；并补传 `subject_id`/`grade_id`，或让后端在 `request` 为空时回「缺少组卷需求」而非「无法识别学科」。

---

### P0-4　试卷「打印视图（A3 双栏）」导出 100% 失败

**位置**：`frontend/src/api/request.js:93-101`｜`frontend/src/api/index.js:228-229`｜后端 `paper_compose.py:2753-2756`

```js
95:    if (response.config.responseType === 'blob') return response   // ← 只豁免 blob
97:    if (res.code !== 200) { ElMessage.error(res.message || '请求失败'); … }
```
```js
228:  exportPrintHtml: (id, params) => request.get(`/question/papers/${id}/export/html`,
229:    { params, responseType: 'text' }),
```

后端返回 `StreamingResponse(media_type="text/html")`。axios 在 `responseType:'text'` 下不做 JSON 解析，`response.data` 是 HTML 字符串 → `res.code === undefined !== 200` → 拦截器判错 → 弹「请求失败」。`PaperEdit.vue:679` 的 `typeof res === 'string' ? res : …` 分支永远走不到。

**修复**：`request.js:95` 改为豁免所有非 JSON 类型：`if (['blob','text','arraybuffer'].includes(response.config.responseType)) return response`。

---

### P0-5　错题本「导出」必然 422

**位置**：`frontend/src/views/student/WrongBook.vue:140, 250-254`｜后端 `learning/wrongbook.py:136-141`

```js
140:  const query = reactive({ page: 1, page_size: 20, subject_id: null, … })
251:  const res = await fetch(`/api/v1/learning/wrong-questions/export?${new URLSearchParams(query)}`, …)
```

axios 的 params 序列化会丢弃 `null`，但 **`new URLSearchParams` 会把它序列化成字符串 `"null"`** → `subject_id=null` → FastAPI 校验 `Optional[int]` 失败 → **422**。默认筛选（未选学科）必现。

附带问题：该处用原生 `fetch` 绕过 axios 拦截器（无 401 刷新、无统一错误提示），422 真实报文被丢弃只显示「导出失败」，且无 try/catch。

**修复**：改走 `learningApi`（axios 自动丢 null），并用页面已有的 `resolveSubjectId()` 还原真实学科 id。

---

### P0-6　改密 / 重置密码后既有令牌全部仍然有效（改密不能止损）

**位置**：`backend/app/services/auth_service.py:262-272`（自助改密）、`:275-284`（管理员重置）、`backend/app/api/v1/auth.py:535-560`（验证码找回）

```python
# auth_service.py:262-272
user.password = hash_password(new_password)
user.must_change_password = False
db.commit()
# ← 无 revoke_token()：已签发的 access / refresh token 一律继续有效
```

**影响**：用户怀疑被盗后改密码**不能止损**——旧 access token 仍可用满 12h（`ACCESS_TOKEN_EXPIRE_MINUTES`），旧 refresh token 仍可用 7 天无限续期，且 `sys_revoked_token` 里不会有它。管理员重置离职员工密码同理。

**修复**：三处成功后把该用户未过期令牌的 jti 写入 `sys_revoked_token`；更彻底的做法是给 `sys_user` 加 `token_epoch`，令牌内带 epoch，改密即 +1，`decode_token` 比对即可（避免全量扫表）。

---

## 3. P1 — 特定条件下触发

### P1-1　异步组卷任务超时阈值按旧任务标定，长组卷会被误判失败并"状态翻转"

**位置**：`backend/app/services/agent_job_state.py:61`（阈值）｜`backend/app/api/v1/paper_compose.py:2899`（调用）｜`frontend/src/views/teacher/PaperWizard.vue:559-573`（前端）

```python
# agent_job_state.py:46-51（阈值标定依据，原文）
## 阈值为什么是 300s
… 实测真实 LLM 下出题 20~60s、组卷 30~90s、教案 25~60s，300s 有 3~5 倍余量
JOB_TIMEOUT_SECONDS = 300
```
```python
# paper_compose.py:2759-2763（异步组卷自己的耗时说明，原文）
# 一组标准卷（5 个大题）在题库空时要并发补 5~6 批题，
# 实测单批 60~100s（生产 sys_agent_call_log 平均 100.7s），最坏 2 轮 ×240s
```
```python
# paper_compose.py:2899 —— 没有按 agent 区分阈值
return ok(agent_job_state.apply_timeout(job, d))
```
```js
// PaperWizard.vue:559-573
const deadline = Date.now() + 10 * 60 * 1000        // 前端给了 10 分钟
if (d.status === 'failed') throw new Error(d.error || '组卷任务失败')   // ← 立即抛错
```

**时间线证据**：`0b76e06`（10-29）引入 300s 阈值；`efd9e66`（11-04）新增异步组卷任务，**未随之调整阈值**。全仓 grep 确认 `paper_compose` 无任何 `timeout_seconds` 特例。

**触发路径**：题库为空 + 标准卷 5~6 个大题 → `AI_FILL_CONCURRENCY=3` 下 2 波 × 2 轮 × 100s ≈ 400s+ → 后端 `apply_timeout` 判定 `failed`，前端立即抛错中断；后台线程随后仍写 `succeeded` → **教师看到"失败"后重试 → 卷子重复生成 + 草稿题翻倍**。

**修复**：`apply_timeout` 支持按 agent 取阈值（如 `paper_compose` 用 900s，与前端 10 分钟上限对齐），或把 `JOB_TIMEOUT_SECONDS` 改为按 agent 查表。

### P1-2　前后端角色漂移两处：系统报表整页空白 + 用户管理写操作必 403

**① 系统报表**：`backend/app/api/v1/report.py:756` 用 `get_current_admin`（仅 sys_admin），而 `frontend/src/router/index.js:48-49` 的 `admin/reports` 放行 `grade_admin`；`AdminReport.vue:147-151` 用 `Promise.all` 并行发 4 个请求 → 其中 1 个 403 → **另外 3 个 grade_admin 本可访问的报表也一起不显示**（整页空白）。

**② 用户管理**：`frontend/src/router/index.js:26-27` 的 `admin/users` 放行 `grade_admin`，但 `system.py:79/130/170/226`（新建/改/删/重置密码）全部是 `get_current_admin`（仅 sys_admin）；`UserManage.vue:7, 72-74` 的四个写按钮**无 `can()`、无 `isAdmin` 判断**（该文件全文未出现 `can(`），而项目其他管理页都用了 `can()`。

**修复**：① `system_runtime` 改用 `get_current_manager`，或前端对该请求单独 catch 降级，不要让它拖垮 `Promise.all`；② `UserManage.vue` 补 `v-if="isSysAdmin"` 门控，或路由收敛为 `['sys_admin']`。

### P1-3　功能回归的「越权 403」只记录不断言，且导出端点 500 也判 PASS（假绿）

**位置**：`audit-reports/qa/functional_runner.py:150-169`

```python
155:        if _is_export(path):
156:            reached = st != 404      # ← 导出端点：只要不是 404 就算通过
157:        else:
158:            reached = st in REACHABLE
159:        # 越权：用另一个角色令牌访问
163:            cross_st, _ = _get(f"{base}{path}", tokens[other])
166:            "own_status": st, "status": "PASS" if reached else "FAIL",
167:            "cross_role": other, "cross_status": cross_st,     # ← 只记录，不参与判定
```

实测（本次真实跑出的 `FUNCTIONAL_TEST_RESULTS.json`）：

| 现象 | 实测数据 |
|---|---|
| 16 条跨角色探测 | `cross_status` = **200×8 / 403×4 / -1×2 / 422×2** —— **8 条越权返回 200，但全部记 PASS** |
| 3 条导出端点 | `own_status = -1`（二进制响应被 `json.loads` 抛异常），因 `st != 404` 仍判 **PASS** |
| 文件自身约定 | `:82-83` 注释写明"仅 404(路径错)/500(服务端错误)/持续 -1(连接失败) 判 FAIL"——**导出分支完全绕过了这条约定，500 也会 PASS** |

另：跨角色探测固定取 `("admin","teacher","student")` 中的下一个角色 → 只测"低权→高权"，**永不测"高权→低权"**（最需要数据隔离的方向）。

**修复**：`cross_status` 纳入判定（按用例声明的期望码）；导出分支改为 `st in REACHABLE or st == 200`；把角色配对改为按用例显式声明。

### P1-4　幸存的唯一后端 pytest 套件未接 CI，且已经腐坏

**位置**：`backend/qa_audit_suite.py`

- **未接线**：三个 workflow 全库 grep `pytest` / `qa_audit` → **0 处命中**。唯一在 CI 里跑的是前端 `npm test`。
- **已腐坏**：实测 `python -m pytest qa_audit_suite.py -q` → **`1 failed, 29 passed`**。
  - 失败项 `test_write_items_symmetric_usage_count`（`:175-206`）断言的是**旧语义**（`usage_count` 按 +1/-1 记账，期望 `q1==5`）。
  - 实际实现早已改为幂等重算（`b8e3093` 引入 `services/question_usage.recount_usage`，`paper_compose.py:1859-1867` 明确弃用记账法），语义是"usage_count = 当前真实引用数"。
  - **探针实测**：真实值 `{q1:1, q2:0, q3:1}`，与实际题项引用数 `{q1:1, q2:0, q3:1}` **完全一致** → **实现正确，断言过期**。
  - 时间线：`qa_audit_suite.py` 最后修改于 `cfdff44`（2.2.1 前后），**早于** `b8e3093` 的实现变更 → 断言腐烂的根因正是"测试不在 CI 里跑"。

**修复**：把该用例改为断言重算语义（`q1==1, q2==0, q3==1`），并把 `python -m pytest qa_audit_suite.py -q` 加入 `ci.yml` 的 backend job。若当时就接了 CI，`b8e3093` 会**假红**一次并顺带暴露这条腐烂——这正是它本该发挥的作用。

### P1-5　功能回归只执行 156 条用例中的 20 条

**位置**：`audit-reports/qa/functional_runner.py:139-144`

```python
get_cases = [c for c in cases
             if c["automation"]["type"] == "api" and c["automation"]["method"] == "GET"
             and c["automation"]["path"] and "{" not in c["automation"]["path"]
             and c["role"] in ("admin", "teacher", "student")]
```

用例集 156 条（admin 75 / teacher 45 / student 31 / public 5），执行器只挑**无路径占位符的 GET** → 实测 `--run` 只执行 **20 条**（auth 2 / reach 16 / public 1 / contract 1）。**所有 POST/PUT/DELETE 业务写入路径（含组卷、交卷、判分、审核）一条都没有被自动执行**——最易出事故的那类改动恰恰在覆盖之外。

**修复**：把核心写路径（组卷保存、交卷、批改）各补 5~10 条幂等用例并纳入 `--run`。

### P1-6　迁移机制：手写补列清单无守护、失败静默降级、alembic 是僵尸依赖

**位置**：`backend/app/core/db_migrations.py:22-69`（`MIGRATION_COLUMNS`，21 条）、`:352-381`、`backend/app/core/database.py:86-103`

- `Base.metadata.create_all` 只建缺失的表，**不给已存在的表加列**；模型加字段若忘记登记 `MIGRATION_COLUMNS`，老库上该列读写直接 500。
- **CI 没有任何守护**（`ci.yml` 只跑 5 道静态门禁，均不校验"模型列 vs 补列清单"）。
- 单条 `ALTER TABLE` 失败 → `rollback` + `logger.error` → **继续执行下一条** → 启动照常完成 → 进程带着缺失列对外服务 → 运行时随机 500。
- `alembic==1.14.0` 在依赖里但**从未初始化**（全仓无 `alembic.ini` / `versions/`），属僵尸依赖。
- 非 SQLite 路径整段跳过并告警"请改用 Alembic"——而 Alembic 又没初始化，切 PostgreSQL 必然踩坑。

**修复**：加一道 CI 脚本，用 `Base.metadata` 反射列集合与 `MIGRATION_COLUMNS` 求差集，差集非空即失败（成本极低，直接封死"漏登记"整类事故）；补列失败从"记日志继续"改为"记 ErrorLog + 阻断启动"。

### P1-7　契约层继续恶化：99 处裸 `Dict Body`，`schemas/` 仍空

11-02 基线 94 处 → 本次 **99 处**；Pydantic 模型 8 → 11，但 `backend/app/schemas/` **仍是空目录**。后果：字段拼错不会 422、类型错误到 SQL 层才炸、OpenAPI 里请求体是 `{}`。前端全量交叉比对显示路径层零漂移，但**字段层**已出现 4 处真实不一致（P0-2/3/4/5 即其表征）。

### P1-8　演示账号公开硬编码口令且默认开启，`must_change_password` 默认 False

**位置**：`backend/app/services/init_db.py:466-467`（`Teacher@123`）、`:487-488`（`Student@123`）、`backend/app/core/config.py:261`（`SEED_DEMO_DATA=True`）、`docker-compose.yml:55`

`init_demo_data` 建账号时**不传** `must_change_password`，模型默认 `False`（`models/system.py:54`）→ 16 个公开口令账号可登录且不被强制改密。超管已有 `enforce_default_admin_password`（`init_db.py:652-720`）的强制处置，**演示账号没有对应机制**。`startup_checks.py:90-114` 只告警不阻断。

> 缓解现状：本机根 `.env` 已设 `SEED_DEMO_DATA=false`，当前这台机器是安全的；风险在"换环境 / 清空数据卷 / 漏配 .env"时重新打开。

---

## 4. P2 — 纵深防御与工程债

| # | 问题 | 位置 | 说明 |
|---|---|---|---|
| P2-1 | 胖路由加剧 | `api/` 层 SQL 437→465 处 | 业务编排、权限判断、SQL 组装全挤在路由文件；`services/` 仅被 API 引用 46 处 |
| P2-2 | 巨型视图 | `KnowledgeManage.vue` 1939 / `QuestionBank.vue` 1573 / `PaperManage.vue` 1200 / `PaperWizard.vue` 1179 | 各含 8~10 个职责域；AI 子流程在两个文件里同构重复约 200 行 |
| P2-3 | 公共组件仅 3 个 | `components/`（EChart / PomodoroTimer / VersionInfo） | 52 视图重复实现：成功提示 135 处、确认弹窗 48 处、导出 38 处、批量条 36 处、分页 16 处 |
| P2-4 | 刷新令牌不轮换、无重放检测 | `api/v1/auth.py:344-356` | refresh token 7 天有效、可无限续期，无"已使用"痕迹；与 P0-6 叠加后极难止损 |
| P2-5 | PBKDF2 迭代仅 10 万 | `core/security.py:49,59` | OWASP 对 PBKDF2-HMAC-SHA256 建议 ≥600,000；盐（16B）与 `compare_digest` 正确 |
| P2-6 | CORS 默认通配 | `core/config.py:76` | 鉴权走 Authorization 头故非 Cookie 场景风险有限，生产仍应显式收敛 |
| P2-7 | 关键限流是进程内计数 | `auth.py` 验证码/找回码桶、`attachment.py` 公开上传桶 | 多 worker 下额度 ×N；验证码/找回码本身已正确落库，这几处是遗漏 |
| P2-8 | `class_overview` 人数统计未过滤学生 | `api/v1/report.py:226` | 同文件 `:324-325` 过滤了，两处口径不一致 |
| P2-9 | 11 个后端端点前端无入口 | 见下表 | 后端已实现但用户用不到，其中"找回密码/重置密码"缺失最影响学生自助 |
| P2-10 | 4 个权限码前端从不使用 | `init_db.py:182-190` | `agent:generate` / `agent:logs` / `agent:plan` / `report:admin` 授予了角色却无任何页面使用，管理员勾选后无效果 |
| P2-11 | 10 个裸 URL 导出 helper 是死代码 | `api/index.js:141,142,218,226,230,347,358,388,389,429` | 同文件 `:165-167` 注释明确警告"用 window.open 必 401"——留下即陷阱 |
| P2-12 | 时间契约门禁扫全仓库，易误杀 | `tools/check_time_contract.py:57-62` | `os.walk(ROOT)` 只按精确相对路径豁免自身，仓内任何 .py 含 `utcnow` 即 FAIL（本次审计的临时目录就触发过一次假红）。建议把扫描范围收窄到 `backend/app` + `tools` |
| P2-13 | AI 草稿无清理任务 | `services/init_db.py:272-278`（6 个默认定时任务） | `source=ai_fill` / `ai_regen` 的草稿只增不减（每次组卷预览/重生都落一批），无任何定时任务清理 |
| P2-14 | `paperLibrary` 的 `size` 参数被忽略 | `PaperEdit.vue:434` vs `paper_compose.py:2430` | 后端用 `PageParams(page/page_size)`，`size` 非声明参数 → 收藏列表只回 20 条 |
| P2-15 | 「额外要求」输入框被后端忽略 | `AgentGenerate.vue:102-104` vs `agent.py:404-416` | 用户填的要求静默丢弃 |
| P2-16 | 「智能批改」Agent 空跑仍提示「生成完成」 | `AgentGenerate.vue:331,478-481` vs `agent.py:465` | `items` 缺失 → 空列表 → 提示成功但一条没批（又一次谎报成功） |
| P2-17 | `verify_student_retake.py` 已不可能通过 | `tools/verify_student_retake.py:98` | 脚本硬编码 `admin/Admin@123456`，而 `init_admin` / `enforce_default_admin_password` 现已把该账号标记 `must_change_password=True` → 登录成功但后续请求全 403 → `g_items[0]` IndexError。同目录 CI 脚本（`verify_paper_module` / `verify_kp_import` / `verify_empty_baseline`）都处理了强制改密，唯独它没有。**不是 CI 断链（它不在 CI 里），但本地复现不了** |

**11 个前端无入口的后端端点**：`POST /auth/forgot-password`、`POST /auth/reset-password`、`POST /grading/unpublish`、`GET /grading/submissions`、`GET /question/questions/{q_id}`、`GET /task/tasks/{task_id}`、`GET /system/users/{user_id}/teachings`、`PUT /system/config`、`DELETE /system/config/{key}`、`GET /learning/notes/shared`、`PUT /learning/notes/{note_id}/share`、`GET /learning/notes/{note_id}/export`。

---

## 5. 功能验收实测结果

全部在本机执行（Python 3.12.7 / Node 22.3.0 / 依赖齐备，`LLM_ENABLED=false`）。

| 验收项 | 命令 | 结果 |
|---|---|---|
| 应用可构建 | `from app.main import app` | ✅ 282 路由，启动无异常 |
| 初中考纲结构 | `tools/verify_exam_structure_spec.py` | ✅ 全通过 |
| 小学考纲结构 | `tools/verify_primary_structure_spec.py` | ✅ 全通过 |
| 组卷引擎 | `tools/verify_compose_engine.py` | ✅ 全通过 |
| 试卷 V3 | `tools/verify_paper_v3.py` | ✅ 通过 63 项，失败 0 |
| 试卷管理 | `tools/verify_paper_manage.py` | ✅ 通过 58 项 |
| 前端单元测试 | `npm test` | ✅ 3 文件 / 43 断言全过 |
| 后端 pytest | `pytest qa_audit_suite.py` | ⚠️ **1 failed, 29 passed**（断言过期，见 P1-4） |
| 接口级功能回归 | 起 uvicorn → `functional_cases.py --run` | ✅ 20/20 通过，但覆盖面仅 20/156 且含假绿（P1-3/P1-5） |
| 静态门禁 ×8 | `check_hardcoded_host` / `check_weak_assertion` / `check_time_contract` / `check_model_fk` / `lint_gate` / `check_data_data` / `scan_vue_refs` / `scan_vue_dup` | ✅ 8/8 通过（`check_time_contract` 曾因审计临时目录假红一次，已清理，现 exit=0） |

> **结论**：核心业务逻辑（组卷、考纲结构、判分）功能实现**是可靠的**，回归脚本与门禁基本可用。**问题集中在"接口与页面之间的接缝"**——P0-2/3/4/5 全部属于此类，静态门禁与现有回归脚本都覆盖不到它们（因为它们不违反任何现有规则，只是字段名/解包层级写错了）。

---

## 6. 扎实的地方（不应在整改中破坏）

- **鉴权基座**：280 端点中 270 挂认证依赖；未挂的 10 个逐个核对**全部是设计上必须公开**的（登录/注册/验证码/刷新/登出/找回/重置/公开上传/公开班级/版本号）。`decode_token` 全程 fail-closed，`check_revocation=False` 全仓仅 2 处且都在登出场景。
- **数据隔离**：`DataScope` 语义正确（`class_ids()` 对非超管永不返回 None）；报表族逐个校验 `class_id ∈ scope.class_ids()`；任务族列表/详情/改/删/提交/读卷六条路径口径一致；`attempt` 由服务端判定，客户端传 `attempt=99` 无法绕过重考次数限制。
- **破坏性操作保护**：删用户/年级/学科/班级/题目/试卷/任务**全部有引用检查且拒绝而非静默级联**（P0-1 是唯一漏网，且是新端点）。
- **凭据与错误处理**：JWT 固定 HS256、显式算法白名单；密码 PBKDF2 + 16B 随机盐 + `compare_digest`；强度校验覆盖四条入口；验证码与找回码均一次性；`SECRET_KEY` 生产弱值/缺省**拒绝启动**；异常不外泄栈；审计日志递归脱敏；`.env` 未入库；全仓无硬编码口令/密钥/内网 IP。
- **SQL 注入面**：全仓字符串拼接 SQL 仅 3 处，全在 `db_migrations.py` 且插值来自模块内硬编码元组；其余全部参数化。
- **工程质量**：`services/llm_breaker.py` 的六类"写错了不报错"坑全部被识别并注释；注释普遍记录"为什么"与反例；发版四道闸门 + 四层一致性校验（本地 HEAD = origin = 镜像 BUILD_INFO = 容器）成熟度超出同规模项目水平。
- **`question_usage.recount_usage`** 把四条入口各自记账统一成幂等重算，是本次审计中看到的最有价值的一次重构。

---

## 7. 建议路线图

**阶段一（1~2 天，零业务风险，改动量小）**
1. P0-1：`remove_item` 加作答引用检查 + 如实上报作废条数（照抄 `_write_items` 语义）。
2. P0-2：`PaperManage.vue` 解包层级改 `res.success` / `res.data`。
3. P0-3：`requirement` → `request`（两处）。
4. P0-4：`request.js:95` 豁免 `['blob','text','arraybuffer']`。
5. P0-5：`WrongBook.vue` 改走 axios + `resolveSubjectId()`。
6. P1-1：`apply_timeout` 按 agent 取阈值，`paper_compose` 用 900s，与前端 10 分钟对齐。
7. P1-4：修正 `qa_audit_suite.py` 过期断言，并把 `pytest` 接入 `ci.yml`。
8. P1-3：`functional_runner.py` 让 `cross_status` 参与判定、导出分支改用 `REACHABLE`。

**阶段二（1 周，结构性）**
9. P1-6：加"模型列 vs 补列清单"差集门禁（成本最低、收益最高的一项新门禁）；补列失败改为阻断启动。
10. P1-5：为核心写路径补 10~20 条幂等用例并纳入 `--run`。
11. P1-2：前后端角色矩阵对齐（系统报表 + 用户管理两处）。
12. P0-6 / P2-4：令牌吊销体系（`token_epoch` 或改密即全量吊销 + refresh 轮换）。
13. P1-8：演示账号纳入强制改密机制。

**阶段三（1~2 月，架构债）**
14. P1-7：建 `backend/app/schemas/`，新端点强制 Pydantic，存量按"写接口优先"替换。
15. P2-1：把 `paper_compose.py`（2584 行）按域拆开——它已同时承担补题/重生/预览/编辑/版本/共享/审核/导出 8 类职责。
16. P2-2 / P2-3：抽 `<PageTable>` / `<ConfirmButton>` / `<BatchBar>` / `<ExportButton>` 四个公共件。
17. 补后端单测覆盖 `paper_compose_service.compose` / `_distribute_on_grid` / `_rescale_scores` 与 `exam_structures`（11-02 评估点名的"最该有单测却零覆盖"的模块，至今仍是 0）。

---

## 附：本次审计的复现方法

```powershell
cd E:\project\management\edu-ai-platform\backend
# 后端断言套件
python -m pytest qa_audit_suite.py -q

# 静态门禁
cd .. ; python tools\check_time_contract.py ; python tools\lint_gate.py ; …

# 接口级功能回归（会写 audit-reports/qa/FUNCTIONAL_TEST_RESULTS.json，跑完建议 git checkout 还原）
$env:DATABASE_URL="sqlite:///../.audit_tmp/func.db"; $env:CAPTCHA_ENFORCED="false"
$env:LLM_ENABLED="false"; $env:SEED_DEMO_DATA="true"; $env:SCHEDULER_ENABLED="false"
$env:SECRET_KEY="audit-functional-regression-secret-0123456789"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8899   # 另开一个终端
$env:BASE_URL="http://127.0.0.1:8899/api/v1"
python audit-reports\qa\functional_cases.py --run
```

P0-1 的复现探针（内存 SQLite + `PRAGMA foreign_keys=ON`）：造 grade/subject/双用户/双题/双题项/task/submission/answer 各 1 行 → 调用 `paper_compose.remove_item(paper_id, item_id, db, creator)` → 断言 `edu_answer` 行数由 1 变 0。
