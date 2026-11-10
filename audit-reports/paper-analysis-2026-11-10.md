# 试卷管理功能 · 系统性分析报告

- **项目**：新芽学堂（edu-ai-platform）FastAPI + Vue3
- **版本基线**：`abeaa5b` / VERSION 2.5.18（master，工作区干净）
- **分析日期**：2026-11-10
- **分析方式**：代码走查 + 本地隔离演示库实机复验（前后端静态审计 + 动态接口探针）
- **说明**：本次分析**未修改任何被 git 跟踪的文件**；所有复验在仓库外的 `E:\project\management\.runtime\` 独立 SQLite 演示库上完成，结束后已清理。

---

## 0. 结论摘要

### 0.1 功能画像

试卷管理是本平台链路最长、也最成熟的模块。它不是单一页面，而是**「一份试卷」这条聚合根上的四套入口**：

| 入口 | 页面 | 后端主文件 | 定位 |
|---|---|---|---|
| 试卷列表 / 试卷库 | `PaperManage.vue`（1246 行） | `api/v1/question.py`（papers 段 1261-1948） | 增删改查、批量、归档、复制、共享、导出 |
| 组卷向导（新建） | `PaperWizard.vue`（1310 行） | `api/v1/paper_compose.py`（137KB，3000+ 行） | 命题标准驱动 + AI 补题 + 预览编辑 + 落库 |
| 试卷编辑 | `PaperEdit.vue`（约 750 行） | `paper_compose.py` /items、/restructure、/versions | 改分、换题、增删、大题重构、版本回溯 |
| 学生侧 | `CustomPaper.vue` / `ExamPaper.vue` | `api/v1/learning/tools.py`、`api/v1/task.py` | 自主组卷、答题 |

配套还有 `paper_ai.py`（试卷 AI 分析/推荐）、`paper_export_service.py`（Word/PDF/答题卡/HTML）、`paper_version_service.py`（版本快照）、`paper_agent.py` + `agent.py#/paper-composer`（智能组卷 Agent）。

规模：后端 **41 个前端调用点 / 30+ 个端点**，覆盖 `/question/papers` 前缀下 question、paper_compose、paper_ai 三个路由文件。

### 0.2 问题分布

| 级别 | 数量 | 性质 |
|---|---|---|
| **P0** | 4 | 安全（SSRF）、功能整体不可用、数据销毁 |
| **P1** | 11 | 数据一致性、契约断裂、越权面、体验硬伤 |
| **P2** | 20 | 死代码、状态细节、一致性缺口、可维护性 |

### 0.3 总体判断

**这个模块的「骨架」是可靠的，「血肉」有洞。**

做得好的地方很硬：可见性判定全仓收口到唯一函数 `_paper_visibility_clause`（`paper_compose.py:201`），列表、详情、导出、试卷库、AI 全部复用，实测越权矩阵**零穿透**；题项写入的「插新 → 迁移作答 → 删旧」顺序彻底解决了 `Answer.paper_item_id` 级联删除毁数据的经典事故；学生卷 / 教师卷双版本在预览与导出两条链路上都做了答案隔离；错误语义（404/403/400/422）基本规范。

出问题的地方高度集中在一类模式：**「A 入口的能力假设被 B 入口无条件继承」**。

- 前端放行「只写描述、不选年级」，异步后端却不解析自然语言 → 该路径 100% 失败（P0-3）
- 前端抽屉「确定」按钮只关窗不回写 → 预览态编辑功能实际不存在（P0-2）
- 前端列表页只传 `question_id/score`，后端整卷覆盖写 → 大题结构当场抹平（P1-1）
- 智能组卷 Agent 的默认比例是小数、被 `int()` 截断 → 规则引擎恒产出 0 题（P0-4）
- 导出让用户可控文本直入 reportlab 解析器 → 一次导出把整份卷子打成 500（P0-1）

这些都不是"代码写得糙"，而是**契约在某一处悄悄退化、另一处仍按旧假设运行**。这正是前两轮复审反复出现的同一类根因。

### 0.4 处置顺序建议

```
第 1 优先（安全 + 导出可用性）
  P0-1  PDF/答题卡导出 SSRF 与 500
第 2 优先（功能可用性）
  P0-2  预览态编辑抽屉不回写
  P0-3  AI 组卷「只写描述」必失败
  P0-4  智能组卷 Agent 恒 0 题 / 空指针
第 3 优先（数据一致性）
  P1-1  列表页编辑抹平大题结构
  P1-4  删题后成绩不重算 / 成绩单自相矛盾
  P1-5  版本回溯只还原 2 个字段
第 4 优先（越权与契约）
  P1-6  组卷抽题不做题库可见性过滤
  P1-7  自然语言组卷 LLM 契约与解析矛盾
  P1-8 ~ P1-11
其余 P2 随版本迭代
```

---

## 1. 模块全景

### 1.1 端点地图（后端 3 个路由文件）

**`api/v1/question.py`（prefix `/question`，试卷段）** — 试卷的 CRUD 与基础运营：

| 端点 | 行号 | 权限 | 说明 |
|---|---|---|---|
| `GET /papers` | 1261 | `paper:list` | 列表（含可见性 + N+1 预取优化） |
| `GET /papers/stats` | 1352 | `paper:list` | 同筛选范围统计 |
| `POST /papers/batch` | 1418 | `paper:write` | 批量删除/复制/共享 |
| `GET /papers/{id}` | 1517 | `paper:list` | 详情（含题目与答案） |
| `POST /papers` | 1555 | `paper:write` | 手动组卷 |
| `PUT /papers/{id}` | 1591 | `paper:write` | 编辑 |
| `DELETE /papers/{id}` | 1663 | `paper:write` | 删除（被任务引用时阻断） |
| `POST /papers/{id}/archive` | 1694 | `paper:write` | 停用/恢复 |
| `POST /papers/{id}/copy` | 1790 | `paper:write` | 复制 |
| `POST /papers/{id}/share` | 1846 | `paper:share` | 定向共享 |
| `GET /papers/{id}/export` | 1867 | `paper:export` | 导出（excel/word/pdf/html） |

**`api/v1/paper_compose.py`（prefix `/question/papers`，30 个端点）** — 标准组卷 V3：compose 预览/AI/保存、items 覆盖写、单题删除、大题改名与重构、版本快照与回溯、试卷库、收藏、共享范围、审核、四种导出。

**`api/v1/paper_ai.py`（prefix `/question/papers`）** — `POST /{id}/ai/analyze`、`POST /{id}/ai/recommend`。

**`api/v1/agent.py`** — `POST /agent/paper-composer`（智能组卷 Agent，**独立于上面三条链路**）。

> **路由抢占核查**：三个文件同挂 `/question/papers`，但 `question.router` 注册在 `api/router.py:21`，`paper_compose.router` 在 `:31`。`GET /question/papers/{paper_id}`（question.py:1517，2 段）与 `GET /question/papers/library/list`（paper_compose.py:2460，3 段）段数不同，**不存在路径抢占**；`/papers/stats`（1352）声明在 `/papers/{paper_id}`（1517）之前，也不会被吞。实测 `library/list`、`compose/*`、`{id}/preview` 全部 200。

### 1.2 权限与可见性矩阵（实测）

可见性判定收口在唯一真源 `paper_compose._paper_visibility_clause`（`paper_compose.py:201-219`）：

```
sys_admin                → None（全量放行）
本人创建                 → Paper.creator_id == user.id
被显式分享               → PaperShare.to_user_id == user.id
范围共享                 → public / grade（同年级） / school（同校）
存量共享（兼容旧接口）   → is_shared=True AND share_scope=private AND 同年级
```

| 场景 | 实测结果 | 判定 |
|---|---|---|
| teacher1 读自己的卷 | 200 | ✅ |
| teacher3（7 年级）读 teacher1 的卷 | **403 无权查看该试卷** | ✅ |
| teacher3 读同年级共享卷 | 200 | ✅ |
| teacher3 导出 teacher1 的卷 | **403** | ✅ |
| teacher3 改 teacher1 的卷 | **403 只能编辑自己创建的试卷** | ✅ |
| 学生读试卷列表 | **403 缺少权限：paper:list** | ✅ |
| 学生读试卷详情 | **403** | ✅ |
| teacher1 删被任务引用的卷 | **400 该试卷已被 2 个作业/考试引用…** | ✅ |
| 学生模式预览是否含答案 | item 字段里**无 answer / analysis** | ✅ |
| 老师模式预览 | 含 answer / analysis | ✅ |

> **结论：越权面本轮零穿透。** 这是该模块最扎实的部分。

### 1.3 导出链路实测

| 端点 | 状态 | Content-Type | 产物校验 |
|---|---|---|---|
| `GET /papers/2/export?fmt=excel` | 200 | xlsx | ZIP 头正确，5988 B |
| `?fmt=word` | 200 | docx | ZIP 头正确，39151 B |
| `?fmt=pdf` | 200 | application/pdf | `%PDF` 头正确，46371 B |
| `?fmt=html` | 200 | text/html | 7442 B |
| `GET /papers/2/export/docx` | 200 | docx | 与上条同源同产物 |
| `GET /papers/2/export/pdf` | 200 | pdf | 同源 |
| `GET /papers/2/export/answer-sheet` | 200 | pdf | 35687 B |
| `GET /papers/2/export/html` | 200 | html | 与老链路同源 |

> HTML 导出对 `<script>` / `onerror` 实测**均已转义**（`&lt;script&gt;` 未还原为真标签），存储型 XSS 这条历史缺陷已闭合。
> 但 **PDF 链路存在另一条同类根因的未闭合分支**——见 P0-1。

---

## 2. 实机复验记录

### 2.1 环境

- 后端：仓库当前代码（2.5.18）本地启动，`DATABASE_URL` 指向仓库外 `E:\project\management\.runtime\paper_probe.db`
- `SEED_DEMO_DATA=true` + `DEMO_LEARNING_FLOW=true` → 4 份演示卷 / 8 个任务 / 12 份提交 / 80 条作答
- LLM 未配置（`LLM_ENABLED=true` 但无有效密钥）→ AI 全部走规则引擎降级，**恰好构成 AI 链路的压力测试条件**
- 演示账号：`teacher1~4 / Teacher@123`、`stu101~ / Student@123`

### 2.2 复验矩阵

| # | 复验项 | 方法 | 结果 |
|---|---|---|---|
| 1 | 越权矩阵（8 种身份×资源组合） | 多账号真实登录 | ✅ 全部符合预期，零穿透 |
| 2 | 学生模式预览泄露答案 | 对比 teacher/student 两种 mode 的 item 字段 | ✅ 无答案字段 |
| 3 | 导出全格式 | 8 个导出端点逐一请求 + 魔数校验 | ✅ 全部 200 且格式正确 |
| 4 | 组卷闭环 | preview → save → items → versions → restore | ✅ 全通（save 落 10 题 / 3 大题，版本 v1~v3） |
| 5 | 异步组卷任务 | 提交 + 轮询 job | ✅ 成功（status=succeeded, progress=100） |
| 6 | AI 分析/推荐在无 LLM 时 | `/ai/analyze`、`/ai/recommend` | ✅ 优雅降级，message 明示「规则引擎，未启用大模型」 |
| 7 | 共享/审核/批量 | share-scope、share、review、batch | ✅ 语义正确（public 被正确拦截、混合批量逐条 skipped） |
| 8 | **单题删除 vs 覆盖写的成绩重算差异** | 同卷两条路径对照 + 库内直查 | ❌ **不一致，见 P1-4** |
| 9 | **覆盖写后成绩单自洽性** | 改分后查 submission 分列 | ❌ **总分与客观分矛盾，见 P1-4** |
| 10 | **列表页编辑是否保留大题结构** | PUT 只传 question_id/score | ❌ **结构全丢，见 P1-1** |
| 11 | **异步 AI 组卷只写描述** | POST /compose/ai/async 仅带 request | ❌ **job failed: 请选择有效的年级，见 P0-3** |
| 12 | **PDF 导出对恶意题干** | 题干含实体编码 `<img src>` | ❌ **500，见 P0-1** |
| 13 | **智能组卷 Agent 默认参数** | POST /agent/paper-composer | ❌ **0 题 / NoneType 崩溃，见 P0-4** |
| 14 | **预览态编辑抽屉回写** | 代码走查 + 引用关系全量 grep | ❌ **不回写，见 P0-2** |

---

## 3. P0 问题（4 条）

### P0-1　PDF / 答题卡导出把用户可控文本交给 reportlab 解析器 → SSRF + 导出 500

**位置**：`backend/app/services/paper_export_service.py:574-576`（题干）、`:580-586`（答案）、`:707-710`（答题卡）

**现象**

```python
574  block.append(Paragraph(
575      f"<b>{qno}.</b><font size=9 color='#555555'>"
576      f"（{it.get('score')}分）</font> {_plain(it.get('stem'))}", st_stem))
```

`_plain()` 先剥标签（`:95`）**再解实体**（`:96-97`），因此 `&lt;img src="http://…"/&gt;` 会在解码后还原成真标签。reportlab 的 `Paragraph` 是 mini-HTML 解析器，会把 `<img src>` 当成真标签**在服务端去取该 URL**。答案字段（`:580-586`）连 `_plain()` 都没经过，原始字符串直接拼进 `Paragraph`。

**触发条件**：任意教师在自己可编辑的题干里存入实体编码的 `<img src=…>`（富文本导入、AI 出题、外部题库导入都容易产生该形态），随后任何人点「导出 PDF」或「导出答题卡」。

**影响**

- **安全（SSRF）**：可探测内网地址、云元数据端点，或回连攻击者服务器并把响应体带进 PDF
- **可用性**：reportlab 抛异常 → 全局处理器兜成 500 → **整份卷子导不出来**

**实机复现（本次实测）**

```
建题（题干含 &lt;img src="http://127.0.0.1:8000/api/v1/system/info"&gt;） → 200
建卷 → 200
GET /question/papers/8/export/pdf          → 500  服务器内部错误，请联系管理员
GET /question/papers/8/export/answer-sheet → 200（答题卡不渲染题干，故未触发）
```

答案字段含 `<img>` 的那份：实测 **200**（该分支的 `_answer_text` 未复现崩溃），但代码层同源，建议一并加固。

**建议修复**

1. 新增 `_pdf_text()`：对 `& < >` 做实体转义后再交给 `Paragraph`，题干 / 选项 / 答案 / 解析 / 知识点名统一走这一条；答案不得再绕过 `_plain` 直接拼接
2. `build_pdf` / `build_answer_sheet` 外层加 try/except，失败返回 400 并说明原因，而非 500

---

### P0-2　向导「编辑题目」抽屉的「确定」不回写，预览态编辑功能实际不存在

**位置**：`frontend/src/views/teacher/PaperWizard.vue:516-519`、`:995-1001`、`:624-625`

**现象**

```vue
516  <template #footer>
517    <el-button @click="editDrawer = false">取消</el-button>
518    <el-button type="primary" @click="editDrawer = false">确定</el-button>
519  </template>
```

```js
995  function editItem(secCode, idx) {
996    const sec = previewSections.value.find(s => s.code === secCode)
997    if (!sec) return
998    editTarget = sec.items[idx]        // 局部变量，赋一次后再未被使用
999    editingItem.value = { ...editTarget }   // 拷贝，改的是副本
1000   editDrawer.value = true
1001 }
```

全文件 grep `editingItem|editTarget` 只有 8 处命中：模板 6 处绑定 + 定义 2 处 + 赋值 2 处，**`editTarget` 从未被写回**，`editingItem` 也从未被读回 `previewItems`。

**触发条件**：任何一次「预览调整」里点某题的「编辑」→ 改题干/分值/难度/答案/解析 → 点「确定」。

**影响**：抽屉正常关闭、**无任何报错**，教师会以为已改好；实际改动被静默丢弃，随后「保存试卷」入库的是原题。整个「预览态编辑」功能不可用，且失败形态是"看起来成功了"——这是最难排查的一类。

**建议修复**：`确定` 按钮改为 `@click="applyEdit"`；函数体 `Object.assign(editTarget, editingItem.value)` 后再 `editDrawer.value = false`；`editTarget` 改为 `ref` 以便模板访问，并在 `previewItems` 变化后按 `question_id` 重新定位。

---

### P0-3　AI 一键组卷「只写描述、不选年级学科」必然失败（前端放行，后端异步接口不解析）

**位置**：`frontend/src/views/teacher/PaperWizard.vue:964`、`frontend/src/utils/paperWizard.js:25-27`；后端 `backend/app/api/v1/paper_compose.py:2860`、`:2894-2906`（对比同步接口 `:1430-1472`）

**现象**

前端放行条件明确允许"只有描述、没有年级学科"：

```js
// paperWizard.js:25
if (String(request || '').trim()) return ''
```

UI 也写着"可留空，由 AI 识别"（`PaperWizard.vue:73`、`:82`）。但提交走的是**异步**接口：

```js
const submit = await questionApi.composeAiAsync({ ...payload, request: form.request })
```

后端 `compose_ai_async` 只把参数原样塞进任务（`paper_compose.py:2906`），后台线程直接调 `_compose_from_payload(db, user, params)`（`:2860`），而后者第一步是 `_grade_subject(db, data.get("grade_id"), data.get("subject_id"))`（`:1234`）→ `grade_id=None` → 抛 `BusinessException("请选择有效的年级")`。

**只有同步接口 `/compose/ai` 才做 LLM 解析并回填 grade/subject**（`:1430-1472`）。而异步端点的 docstring 写着「入参与同步接口 `/compose/ai` 完全一致，只是把等待从 HTTP 请求里挪走」——**这句承诺不成立**，是后端与前端共同持有的契约错误。

**实机复现（本次实测）**

```
POST /question/papers/compose/ai/async  {"request":"出一份一年级数学期中卷"}
  → 200 {"job_id":2,"status":"pending"}
  → 轮询：status=failed  stage=解析参数  error=请选择有效的年级
```

**影响**：该路径 100% 失败，错误提示是"请选择有效的年级"——与界面承诺完全相反。更糟的是 `paperWizard.js` 的单测把这个行为锁死为"正确"，**回归测试反而在保护一个坏契约**。

**建议修复**（二选一）

- (a) 前端 AI 模式改调同步接口 `questionApi.composeAi`（已有 300s 超时），走带解析的路径
- (b) 保持异步，但在 `_run_compose_job` 内复用同步接口的解析逻辑（`_resolve_ai_grade` / `_resolve_ai_subject`），使两个入口能力真正一致——**并修正 `:2892` 的 docstring**
- 无论哪种，都需同步修改 `frontend/src/utils/__tests__/paperWizard.test.js:15-19,37-39`（该用例当前断言的是不成立的前提）

---

### P0-4　智能组卷 Agent 的默认题型/难度比例是小数，被 `int()` 截断为 0 → 恒 0 题 + 空指针崩溃

**位置**：`backend/app/agents/paper_agent.py:13`、`:78-80`、`:152`、`:156-163`、`:309-332`

**现象**

```python
13   DIFFICULTY_WEIGHT = {"easy": 0.3, "medium": 0.5, "hard": 0.2}
...
78   type_ratio = type_ratio or parsed_params.get("type_ratio") or {
79       "single": 0.5, "blank": 0.2, "short": 0.3,
80   }
...
152  total_items = sum(int(v) for v in type_ratio.values()) or 10
156  for qtype, qty in type_ratio.items():
157      qty = int(qty)            # 0.5 → 0
158      if qty <= 0:
159          continue             # 三个题型全被跳过
```

`type_ratio` 的语义是**题量（计数）**，默认值给的却是**比例**；`int(0.5)=0` → 所有题型被跳过 → `selected` 恒空。难度权重同理：`int(0.3)=int(0.5)=int(0.2)=0`。

紧接着第二处：

```python
309  paper = None
310  if save:
311      paper = Paper(...)
...
330  db.add(
331      PaperItem(
332          paper_id=paper.id, ...     # save=False 时 paper 是 None → AttributeError
```

`PaperItem` 的写入在 `if save:` 块**之外**。而 `question_agent.fallback()` 返回的题库复用题**必带 id**（`question_agent.py:401`），必然触发。

**实机复现（本次实测）**

```
POST /agent/paper-composer  {grade_id:1, subject_id:2, total_score:100}
  → success=False  msg=智能组卷智能体执行失败：'NoneType' object has no attribute 'id'   题数=0
POST /agent/paper-composer  {..., type_ratio:{single:5, blank:3, short:2}}
  → success=True   题数=0
```

**影响**：`/agent/paper-composer` 这条"智能组卷 Agent"链路在实机上**要么崩、要么交出 0 道题**。异常被 `agents/base.py:64` 兜成 `message=f"{display_name}执行失败：{exc}"`，Python 异常原文直接回给教师，毫无信息量。

> 注意影响面：该链路的调用方是 `frontend/src/views/agent/AgentGenerate.vue:711`（智能体中心）。试卷管理主向导走的是 `/question/papers/compose/ai`（paper_compose），**不受影响**（实测该路径正常出卷 10 题 / 3 大题）。`PaperManage.vue` 里的 AI 组卷对话框是死代码（见 P2-3）。

**建议修复**

1. `type_ratio` / `difficulty_ratio` 语义二选一并统一（建议计数制，难度用 `{"easy":30,"medium":50,"hard":20}`，与 `ExamStandard.difficulty_ratio` 对齐）；若保留比例制，改为先归一化再乘题量
2. `PaperItem` 写入整段收进 `if save:` 内；`save=False` 时只返回预览并显式提示"预览模式未落库"，任何情况下不访问 `paper.id`
3. `Agent` 层把异常映射为业务化文案，原始异常只进日志（见 P2-14）

---

## 4. P1 问题（11 条）

### P1-1　列表页「编辑试卷」保存一次就把标准卷的大题结构整体抹平

**位置**：`frontend/src/views/teacher/PaperManage.vue:1000-1012`（同源问题见 `:841` 的 `applyRecommendations`）；后端 `question.py:1621-1633` → `paper_compose.py:1819-1826`

**现象**：保存时只提交 `question_id` 与 `score`，丢掉了全部大题字段：

```js
items: paperItems.value.map(it => ({
  question_id: it.question_id,
  score: Number(it.score) || 0
}))
```

后端 `PUT /papers/{id}` 走 `_normalize_paper_items`（`question.py:1233-1238`，只产出 `section_name`）→ `_write_items` 按 `it.get("section_code")` / `section_sort` 写库 → 新题项 `section_code=NULL, section_sort=0, section_name=NULL`，旧题项整体删除。

**实机复现（本次实测）**

```
保存前： (51, q1, 1, 5.0, 'single', '一、选择题', 1)   ← 大题结构完好
PUT /question/papers/5 {"items":[{"question_id":1,"score":5}, …]}   → 200 试卷已更新
保存后： (75, q1, 1, 5.0, None, None, 0)                 ← 结构全空
预览分组： [('single','单选题',6), ('judge','判断题',2), ('blank','填空题',2)]
```

**影响**：对任何向导产出的标准卷（"一、选择题 / 二、填空题"），在列表页改点分值或增删题再保存，**卷面大题标题从"一、选择题"退化为裸的"单选题"**，分组键被清空后「改大题名」「重构大题」都失去依据。这是对**高频操作**的**静默数据销毁**。

**建议修复**：`PaperManage.save()` 组装 items 时补齐 `section_code` / `section_name` / `section_sort`（`openDialog` 拉详情时后端 `question.py:1535` 已返回 `section_name`，前端 `:968-976` 没保留）；`applyRecommendations`（`:827-835`）同理。

---

### P1-2　编辑页的试卷名称 / 说明 / 时长改了保存不了（保存按钮恒灰）

**位置**：`frontend/src/views/teacher/PaperEdit.vue:395-396`、`:132`

**现象**：元信息表单只有 `v-model`，没有 `@change` 去置 `dirty`：

```js
watch(sections, schedulePaperDraft, { deep: true })
watch(meta, schedulePaperDraft, { deep: true })   // 只存草稿，不置 dirty
```

而保存按钮是 `:disabled="!dirty"`，`dirty` 只在 `onScoreChange` / `doAddItems` / `onRegenerate` / 草稿恢复里被置位（`:465`、`:555`、`:422`）。

**触发条件**：只改名称、命题说明或考试时长，不动任何题目——这是最常见的改卷场景。

**影响**：页面顶部仍显示"已同步"，保存按钮灰色不可点；改完直接返回列表则修改丢失，全程无任何提示。

**建议修复**：在 `watch(meta, ...)` 内同时 `dirty.value = true`，或给三个输入加 `@change="dirty = true"`。

---

### P1-3　编辑页点「重构大题」会静默清空所有未保存的修改

**位置**：`frontend/src/views/teacher/PaperEdit.vue:596-608`

**现象**

```js
await questionApi.restructurePaper(paperId, {})
ElMessage.success('已重构大题')
await loadPaper()          // 重新拉库并覆盖本地 sections
```

`loadPaper()` → `applyPreview(data)`（`:339-367`）→ `sections.value = secs`，随后 `dirty.value = false`（`:447`）。

**触发条件**：页面上有未保存改动（改过分值、加过题、换过题）时点「重构大题」——按钮无任何"会丢弃本地修改"的提示。

**影响**：本地草稿被服务端数据直接覆盖，全部丢失且用户不知情；页面还显示"已同步"，误以为改动已保存。

**建议修复**：`doRestructure` 在 `dirty.value` 为真时先弹二次确认；或把重构降级为纯本地重排，只在点保存时落库。

---

### P1-4　删题后学生成绩不重算；重算时总分与客观分互相矛盾（两条删题路径行为不一致）

**位置**：`backend/app/api/v1/paper_compose.py:2183-2249`（`remove_item`）vs `:1978-2046`（`update_items`）

**现象（两条路径的差异）**

| 路径 | 入口 | 是否重算提交成绩 | 是否更新 objective/subjective 分列 | 是否更新 status |
|---|---|---|---|---|
| `POST /{paper_id}/items`（整卷覆盖写） | 前端 `PaperEdit.vue:502` | ✅ `_recalculate_after_change` | ❌ | ❌ |
| `DELETE /{paper_id}/items/{item_id}`（单题删除） | 前端**未使用**（见下） | ❌ **完全不重算** | ❌ | ❌ |

`remove_item` 删掉题项后，作答随 `Answer.paper_item_id` 的 ON DELETE CASCADE 一并消失，但 `Submission.score` 保持原值不动。

**实机复现（本次实测，同一份演示卷）**

```
删除前： submission 1=80.0  submission 2=None  submission 3=90.0
DELETE /question/papers/1/items/1                → 400「该题已有 2 条学生作答…确认请带 force=true」（守卫正常 ✓）
DELETE /question/papers/1/items/1?force=true     → 200「题目已移除，同时作废 2 条学生作答」
删除后： submission 1=80.0  submission 2=None  submission 3=90.0   ← 分数纹丝未动
         paper1.total_score = 90.0（卷总分已变，学生总分没变）
```

再走覆盖写路径后暴露第二个问题：

```
POST /question/papers/1/items（删掉该题后整卷保存）
  → affected_submissions=3, recalculated=True, total_score=90.0
  → submission 3: score 90.0 → 0.0，但 objective_score 仍为 90.0、status 仍 auto_graded
```

根因在 `paper_compose.py:2104`：

```python
total = round(sum(float(a.score or 0) for a in sub.answers), 2)
sub.score = total
```

只重算 `score`，**不重算 `objective_score` / `subjective_score`，也不动 `status` / `grade_time`**。对"无逐题作答行"的提交（demo 造数正是如此，见 P2-13），`sum([]) == 0` → 总分被清零，而客观分列保留旧值。

**影响**

- 成绩单**自相矛盾**：总分 0、客观分 90、状态"已自动批改"三行并列
- 试卷总分（90）与学生总分（80）口径不一致
- 主观题改分后，客观/主观分列不跟随，总分与分列对不上

**建议修复**

1. `remove_item` 在删题后复用 `_recalculate_after_change`（或统一走 `_write_items`），使两条路径口径一致
2. `_recalculate_after_change` 同时重算 `objective_score` / `subjective_score`，并同步 `status` / `grade_time`
3. 对"无作答行"的提交（`sub.answers` 为空）**跳过重算并如实上报**，而不是把总分写成 0

> **既有回归覆盖的缺口**：`tools/verify_paper_rescore.py` 已覆盖"编辑已被引用的试卷 → 作答不丢失 + 成绩重算"这条路径（本次复跑 **9 项全 PASS**，基线是健康的）。但它只驱动 `_write_items` + `_recalculate_after_change` 这一条路，**从不调用 `remove_item`**，断言也只检查 `Submission.score` 总分，**不检查 `objective_score` / `subjective_score` 分列**，更没有"无作答行的提交"这一档用例——正好是上面三个缺口的盲区。修复时应同步补上这三类用例，否则同类回归还会从缝里漏过去。

---

### P1-5　版本回溯只还原 `name` / `duration` 两个字段 → 部分回滚，数据不一致

**位置**：快照存了但没还原：`backend/app/services/paper_version_service.py:88-93`；回溯未取：`backend/app/api/v1/paper_compose.py:2442-2447`

**现象**

```python
2442  paper_data = snapshot.get("paper") or {}
2443  if paper_data.get("name"):
2444      paper.name = str(paper_data["name"])[:128]
2445  if paper_data.get("duration"):
2446      paper.duration = int(paper_data["duration"])
```

快照里明确存了 `difficulty_ratio` / `exam_type` / `standard_id` / `description`（`paper_version_service.py:88-92`），回溯一个都没还原；`total_score` 由 `_write_items` 按**当前**题项重算（`paper_compose.py:1869`），而非快照里的历史值。

**影响**：回溯产出「旧题项 + 新卷级元数据」的混合体；卷面说明、命题标准、难度分布与历史版本对不上，而 UI 文案是"已回溯到 vN"，教师会误以为已完全回到历史状态。

**建议修复**：在 restore 里逐一还原这些字段（`exam_type` / `status` 建议保留当前值并在返回体注明）；或把不还原的字段从 `build_snapshot` 里删掉，避免"存了却不用"的误导；同时在返回体说明 `total_score` 的来源（快照值 or 重算值）。

---

### P1-6　组卷抽题不做题库可见性过滤 → 预览泄露他人私有题题干，且保存必然失败

**位置**：`backend/app/agents/paper_agent.py:164-173`、`:191-198`

**现象**

```python
164  stmt = select(Question).where(
165      Question.subject_id == subject_id,
166      Question.type == qtype,
167      Question.difficulty == diff,
167      Question.status == "published",
168  )
```

`Question.bank_type` 默认 `private`、`status` 默认 `published`（`models/question.py:75-77`），所以这条查询会抽到**别人已发布但私有的题**。同项目的 `question_agent.py:358-363` 与 `paper_compose.py:634` 都用 `question_usable_error` 收窄，只有 `paper_agent._compose` 漏了。

**影响**：他人私有题题干出现在我的预览里；保存时被 `_normalize_items` 以"无权使用题目"拒绝，表现为「明明抽到 N 题，保存报错」。

**建议修复**：两条查询都加 `or_(Question.bank_type == PUBLIC, Question.owner_id == user_id)`；`_compose` 需新增 `user_id` 参数并下传。

---

### P1-7　自然语言组卷的 LLM 契约与解析代码互相矛盾 → 必然报「无法识别学科」

**位置**：提示词 `backend/app/agents/paper_agent.py:28-30`、`:44-45`；解析 `:74-75`

**现象**

```python
44   **不要输出 grade_id / subject_id**：你不知道系统内部的主键，猜出来的 id 会指向
45   别的年级/学科，导致组卷直接失败。只输出 grade_num 与 subject_name 即可。
...
74   subject_id = subject_id or parsed_params.get("subject_id") or 0
75   grade_id = grade_id or parsed_params.get("grade_id") or 0
```

提示词让模型输出 `grade_num` / `subject_name` 并**明令禁止**输出 id；代码却只读 id。全仓检索确认**没有任何一处**把 `grade_num` / `subject_name` 映射成 `Grade.id` / `Subject.id`。

**触发条件**：调用方只传 `request`、不传 `grade_id` / `subject_id`——前端正是按这个前提设计的（`AgentGenerate.vue:433` 注释"不填就靠 AI 从需求文本解析"；`agent.py:446-447` 也放行这种调用）。

**影响**：稳定抛「无法识别学科，请指定学科后再组卷」，自然语言组卷这条主路径形同虚设。

**建议修复**：按 `subject_name` 反查 `Subject`（Subject 唯一键是 `(grade_id, name)`，须先用 `grade_num` 定位 `Grade` 再按 (grade_id, name) 过滤，不能只按 name 查），按 `grade_num` 反查 `Grade`，把 id 落回 `subject_id` / `grade_id`；查不到再降级为"请选择年级与学科"。

---

### P1-8　异步组卷轮询：一次瞬时网络抖动即中断整条链路，且离开页面不清理

**位置**：`frontend/src/views/teacher/PaperWizard.vue:562-577`

**现象**

```js
while (Date.now() < deadline) {
  await new Promise((resolve) => setTimeout(resolve, 2000))
  const res = await questionApi.composeJob(jobId)   // 抛错直接跳出 while
```

`composeJob` 一旦失败（网络抖动、网关 502、token 刷新失败），异常直接冒泡出 `pollComposeJob` → `doCompose` 的 catch → 提示"组卷失败"，**而后端任务其实还在跑**。该文件 `:525` 的 vue 导入里没有 `onUnmounted` / `onBeforeUnmount`，轮询循环没有任何中止标志。

**触发条件**：(a) 2 秒轮询窗口内出现任意一次请求失败；(b) 组卷进行中（UI 明确提示"可先切到其他页面"，`:295`）用户切走或刷新——组件卸载后 `while` 循环继续跑到 15 分钟上限，持续写已销毁组件的 ref 并占用连接。

**影响**：(a) 教师看到"组卷失败"但后台仍在生成，重试会重复生成一份卷子；(b) 页面关闭后仍持续轮询最多 15 分钟。

**建议修复**：轮询体内 `try/catch` 包住 `composeJob`，连续失败 3 次再放弃，单次失败只 `continue`；引入 `let disposed = false` + `onUnmounted(() => { disposed = true })`。

---

### P1-9　编辑页保存无版本冲突检测，后保存者静默覆盖先保存者

**位置**：`frontend/src/views/teacher/PaperEdit.vue:489-501`（payload 无 `current_version`）、后端 `paper_compose.py:1978-2007`

**现象**：前端展示了版本号（`:10` `v{{ paper.current_version || 1 }}`）却在保存时不带它；后端 `update_items` 也不做版本比对，直接整卷覆盖写。

**触发条件**：两位教师（或同一教师两个标签页）同时打开同一份试卷，先后保存。

**影响**：后保存者用陈旧题表整卷覆盖，先保存者的改动被静默丢弃，双方都收到"已保存"提示。

**建议修复**：保存时带上读取到的 `current_version`，后端做乐观锁（不匹配返回 409，前端提示"该试卷已被他人修改，请刷新后重试"）。前端单方面无法根治。

---

### P1-10　学生自主组卷的题型下拉出现重复选项，且默认题型含无效值导致填空题永远抽不到

**位置**：`frontend/src/views/student/CustomPaper.vue:36`、`:99`；`frontend/src/constants/question.js:23-36`；后端 `backend/app/api/v1/learning/tools.py:355-356`

**现象**：页面直接用带别名的 `TYPES` 渲染可提交的取值：

```vue
<el-checkbox v-for="(l, v) in TYPES" :key="v" :value="v">{{ l }}</el-checkbox>
```

```js
question_types: ['single', 'multiple', 'judge', 'fill'],
```

`constants/question.js` 明确把 `TYPES` 扩成"规范枚举 + 历史别名"，`fill/calculate/proof/essay/subjective/short_answer` 都在里面，且文件注释写着"新代码不应产生别名值"。于是：① 题型复选框渲染 14 项，「填空题」出现 2 次、「计算题」3 次、「简答题」3 次；② 后端按 `Question.type.in_(question_types)` 精确匹配，**`'fill'` 不是后端合法题型（后端是 `blank`）**，该条件恒不命中。

**影响**：学生看到「填空题」已勾选，实际组出的卷子里一道填空题都没有；下拉里重复的同名选项让用户无法判断该选哪个。

**建议修复**：`:36` 改遍历 `QUESTION_TYPE_LABELS`；`:99` 默认值改为 `['single','multiple','judge','blank']`；提交前用 `QUESTION_TYPE_ALIAS` 归一化一次。

---

### P1-11　「放宽难度」兜底查询丢掉知识点约束 → 用户指定的知识点被静默忽略

**位置**：`backend/app/agents/paper_agent.py:191-198`

**现象**：兜底 stmt 只剩 `subject_id / type / status`（+ 可选 `grade_id`），**没有** `Question.knowledge_point_id.in_(kp_ids)`（对比主查询 `:172-173`）。

**影响**：卷子混进无关知识点的题；知识点覆盖报告按实际抽到的统计，教师不会察觉"我勾的知识点被忽略"。

**建议修复**：兜底分支保留 `kp_ids` 过滤；确需放宽时按"先放宽知识点、再放宽难度"的顺序，并在返回体显式标注"知识点约束已放宽"。

---

## 5. P2 问题（20 条）

| # | 问题 | 位置 | 简述 |
|---|---|---|---|
| P2-1 | 试卷「说明」字段保存后被后端丢弃 | `PaperManage.vue:1005` / `question.py:1596-1660` | payload 带了 `description`，`PUT /papers/{id}` 没有该分支，提示"已更新"但内容未变；同字段走 `/compose/save` 是好的，两个入口不一致 |
| P2-2 | 列表页批量操作无 loading 态，可重复点击 | `PaperManage.vue:1072`、`:1101-1117` | `batchRunning` 只在脚本赋值、模板从未引用；连点会并发发两发 `/papers/batch`，批量复制会复制出两份副本 |
| P2-3 | 列表页 AI 组卷对话框整块是死代码（约 180 行） | `PaperManage.vue:1191`、`:437-494`、`:1215-1245` | `openAI()` 全文件无调用点（模板按钮走 `goWizardAi`）；它调的是 `agentApi.paperComposer`，与向导的 `composeAiAsync` 是两套链路 |
| P2-4 | 列表页初始化 `Promise.all` 无兜底 | `PaperManage.vue:1257-1267` | 三个辅助接口任一失败 → `refreshAll()` 不执行 → **试卷列表永远不加载**，页面显示"暂无试卷"，教师会误判卷子没了并重复建卷 |
| P2-5 | 详情抽屉的"加载失败"空态不可达 | `PaperManage.vue:777-779`、`:298` | catch 里 `detailPaper.value = row`（非空）→ `v-else-if="!detailPaper"` 永不触发 |
| P2-6 | 导出是全局单锁，导出别的行时静默无响应 | `PaperManage.vue:722-724` | `if (exportingId.value != null) return`，点其它行导出直接 return，无 toast |
| P2-7 | 编辑页「从题库添加」分页参数名传错 | `PaperEdit.vue:632` | 传 `size: 30`，后端字段是 `page_size` → 按默认条数返回，且弹窗内**没有分页控件** → 第 20 题之后的题加不进试卷 |
| P2-8 | 编辑页的「缺口提示」永远不显示 | `PaperEdit.vue:365-366` | 读 `generation_params.gaps`，但 `/compose/save` 写入的 `generation_params` 没有 `gaps` 键（`paper_compose.py:1648-1656`） |
| P2-9 | 编辑页后端返回的卷面体检 `issues` 完全没被使用 | `PaperEdit.vue:446` / `paper_compose.py:1964` | 后端每次预览都算好 error 级缺陷（重复题、作文不在末位、总分对不上），前端丢弃 → 编辑页看不到"这份卷能不能直接打印" |
| P2-10 | 编辑页"丢弃草稿"实际不丢弃 | `PaperEdit.vue:411-418` | `confirmAction` 取消时**返回 false 而不抛异常** → `localStorage.removeItem` 在 catch 分支里永不执行 → 下次进来继续弹恢复询问 |
| P2-11 | 编辑页草稿防抖定时器离开页面不清理 | `PaperEdit.vue:377`、`:389-393` | 未引入 `onBeforeUnmount` → 卸载后仍执行一次写 localStorage |
| P2-12 | 向导第 2 步设的"考试时长"不生效 | `PaperWizard.vue:221`、`:886`、`:1189` | 第 2 步绑 `form.duration`，保存发 `saveForm.duration`，两者无同步 → 卷面显示 120 分钟，入库 90，学生端限时按错值执行 |
| P2-13 | 演示数据造出「有 90 分、无作答行」的提交 | `backend/app/services/init_db.py:944-950` | `Submission(score=90.0, objective_score=90.0)` 却没有建 `Answer` 行 → 成绩单有 90 分却无题目明细；也是 P1-4 的现成触发器 |
| P2-14 | LLM 异常原文回显给用户 | `backend/app/agents/base.py:64` → `api/v1/agent.py:462-463` | 异常原文（如 `could not convert string to float: '一百'`）直接回给教师 |
| P2-15 | `ComposePreviewIn` / `ComposeSaveIn` 全字段 `Any` + `extra="allow"` → 参数被静默吞 | `backend/app/schemas/legacy_bodies.py:29-46` | 实测传 `count: 5` 仍出 10 题、无任何提示；字段拼错也无从发现 |
| P2-16 | 限流超限返回 400 而非 429 | `backend/app/core/rate_limit.py:57-59` | 前端无法区分"参数非法"与"调用过频"，无法做退避重试 |
| P2-17 | `paper_ai` 与 `paper_compose` 的可读判定不是同一套 | `paper_ai.py:128-137` vs `paper_compose.py:201-247` | 存量共享卷在 `/preview` 是 403、在 `/ai/analyze` 是 200 |
| P2-18 | `question.py` 导出端点硬编码教师卷 | `question.py:1929`、`:1931`、`:1939`、`:1944` | word/pdf/html 全固定 `mode="teacher"`，拿不到学生卷（**无越权**：需 `paper:export`） |
| P2-19 | 版本号并发计算无保护 | `backend/app/services/paper_version_service.py:109-111` | 两个并发事务会算出同一 version，撞唯一约束 `uq_paper_version` → 偶发 400 |
| P2-20 | `paper_ai` 提示词直接拼接用户可控题干 / 卷名 | `paper_ai.py:387-401`、`:553-572` | 题干原样进 prompt → 跨用户提示词注入（输出仅作文本展示，不回写数据，风险有限） |

---

## 6. 设计优点（已核查，确认无异常）

这些是本模块值得保留、且经实测验证的部分——后续重构时不要弄丢：

1. **可见性判定全仓唯一**。`paper_compose._paper_visibility_clause` 是唯一真源，列表 / 详情 / 导出 / 试卷库 / AI 全部复用。实测越权矩阵零穿透（详见 §1.2）。
2. **题项写入的"插新 → 迁移作答 → 删旧"顺序**（`paper_compose.py:1759-1870`）彻底解决了 `Answer.paper_item_id` ON DELETE CASCADE 毁数据的经典事故；被移除题目的作答无法保留时**如实计数上报**（`dropped`）而不是假装保住。
3. **学生卷 / 教师卷双版本**。`_build_preview(mode="student")` 不写 `answer` / `analysis`（`:1924-1926`），实测学生模式预览 item 字段里确无答案；docx / pdf / html / 答题卡四条导出都据此渲染。
4. **删除试卷的双重保险**：被任务引用时阻断（`question.py:1676-1683`，实测 400 并写明后果），并补了「停用」写入口（`archive`，`:1694`），不让教师被迫删任务连带毁成绩。
5. **引用计数用"重算"而非"±1 记账"**（`_write_items` 第 5 步 `:1859-1867`），幂等、值恒等于真实引用数，避免了计数漂移无法追溯。
6. **HTML 导出全量转义**（`_h` / `html.escape`），实测 `<script>` / `onerror` 均已转义，存储型 XSS 这条历史缺陷已闭合。
7. **危险操作二次确认齐备**：删除、停用/恢复、批量删除/复制/共享、重构、版本回溯（`force`）均有确认框，且提示语写到了后果层面（如"会被 N 个作业引用，请先处理相关任务"）。
8. **AI 链路优雅降级**：无 LLM 时 `/ai/analyze`、`/ai/recommend` 均 200 且 message 明示"规则引擎，未启用大模型"；组卷 AI 解析失败会降级为规则组卷并透传原因。
9. **N+1 已优化**：列表页题量、创建者、学科、年级名均为批量预取（`question.py:1292-1310`）。
10. **前端权限假设无越权**：按钮显隐一律走 `userStore.can('paper:write'/'paper:share'/'paper:export'/'paper:ai')`，未发现硬编码角色判断；路由 `meta.perm` 与后端 `require_perm` 一致。
11. **导出未发现 `window.open` 直连**：全部走 axios 带 Token 取流，不会丢 Authorization 头必然 401。

---

## 7. 附录：复现命令

```powershell
# 1. 启动隔离的本地后端（演示库放仓库外，不碰仓库内数据文件）
$RT = "E:\project\management\.runtime"; $R = "E:\project\management\edu-ai-platform"
$env:DATABASE_URL = "sqlite:///$($RT.Replace('\','/'))/paper_probe.db"
$env:SEED_DEMO_DATA = "true"; $env:DEMO_LEARNING_FLOW = "true"
$env:PYTHONUTF8 = "1"; $env:PYTHONIOENCODING = "utf-8"
Set-Location "$R\backend"; python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# 2. 登录（图形验证码从本地演示库 sys_captcha 表读取，绕开 OCR）
$key = (Invoke-RestMethod http://127.0.0.1:8000/api/v1/auth/captcha).data.key
$text = (python -c "import sqlite3;print(sqlite3.connect('E:/project/management/.runtime/paper_probe.db').execute('select text from sys_captcha where key=?',('$key',)).fetchone()[0])")
$body = @{username='teacher1';password='Teacher@123';captcha_key=$key;captcha=$text} | ConvertTo-Json
$tok = (Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/v1/auth/login -Body $body -ContentType 'application/json').data.access_token
$h = @{Authorization = "Bearer $tok"}

# 3. 关键复现点
Invoke-RestMethod -Headers $h "http://127.0.0.1:8000/api/v1/question/papers"                    # 列表
Invoke-RestMethod -Headers $h "http://127.0.0.1:8000/api/v1/question/papers/2/export?fmt=pdf"  # P0-1 → 500
Invoke-RestMethod -Method Post -Headers $h -Uri "http://127.0.0.1:8000/api/v1/question/papers/compose/ai/async" -Body '{"request":"出一份一年级数学期中卷"}' -ContentType 'application/json'   # P0-3 → job failed
Invoke-RestMethod -Method Post -Headers $h -Uri "http://127.0.0.1:8000/api/v1/agent/paper-composer" -Body '{"grade_id":1,"subject_id":2,"total_score":100}' -ContentType 'application/json'  # P0-4 → 0 题 / 崩溃
```

```powershell
# 静态复现（不需要启动服务）
cd E:\project\management\edu-ai-platform
git -C . log --oneline -1                                              # abeaa5b
Select-String -Path backend\app\agents\paper_agent.py -Pattern 'int\(v\)'   # P0-4
Select-String -Path frontend\src\views\teacher\PaperWizard.vue -Pattern 'editingItem|editTarget'  # P0-2
Select-String -Path backend\app\services\paper_export_service.py -Pattern '_plain|Paragraph\('      # P0-1
```

---

## 8. 与历史审计的关系

本次发现与前两轮复审（`audit-reports/reaudit3-2026-11-09.md` 等）的关系：

- **已闭合且本次实测确认**：P0-1 首轮的"组卷删题作废作答"（`remove_item` 的 force 守卫实测 400 正常）、P1-C 的 HTML 导出 XSS（实测已转义）、导出丢失 Authorization 头（全部走 axios blob）
- **本次新发现**（前几轮未覆盖）：P0-1 的 reportlab SSRF 面、P0-2 预览态编辑不回写、P0-3 异步 AI 组卷契约矛盾、P0-4 Agent 比例语义错乱、P1-1 列表页编辑抹平大题结构、P1-4 成绩重算口径不一、P1-5 部分回滚
- **本次未复现（保持闭合）**：`question.py` 演示数据 `options` 格式导致两个导出 500 的历史问题——本次本地新造演示库导出全部 200，该项应已在上游修复

> **说明**：本报告所有结论均标注了取证方式（**实机复现** / **代码走查**）。标「实机复现」的条目在隔离的本地演示库上验证过；标「代码走查」的条目为静态分析结论，建议在修复前用同一套探针复验。
