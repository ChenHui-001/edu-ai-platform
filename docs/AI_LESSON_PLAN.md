# AI 教案生成

> 版本：1.0.41 ｜ 模块：教学管理 → 教案管理 ｜ 代码：`agents/lesson_agent.py` + `api/v1/lesson_ai.py` + `views/teacher/AiLessonDialog.vue`

输入教学主题、年级、学科、课时等条件，系统异步生成一份结构完整、可直接上课的教案：
教学目标（三维）、重难点、教学准备、分环节教学过程与时间分配、师生活动、课堂练习、
作业布置、板书设计。用户预览、修改、确认后存入教案库或导出 Markdown。

---

## 一、功能入口

| 入口 | 位置 | 说明 |
|---|---|---|
| **AI 生成教案** | 教学管理 → 教案管理，工具栏主按钮 | 打开四步向导，新建生成任务 |
| **生成记录** | 同页工具栏次按钮 | 右侧抽屉，列出本人历史任务（含失败/中断的） |
| **来源列** | 教案列表 | `AI` 橙色标签 / `人工` 灰色标签，一眼区分内容来源 |
| **恢复任务** | 生成记录抽屉 → 「查看」 | 传入 `resumeJobId` 重新进入向导，接着预览或保存 |

权限：`get_current_teacher`（teacher / grade_admin / sys_admin）。学生、家长无法进入。

---

## 二、交互流程

```
① 填写条件 ──▶ ② AI 生成中 ──▶ ③ 预览与编辑 ──▶ ④ 存入教案库
   表单校验      进度条+文案      四个 tab 可改      入库 / 导出
                可后台化        质量提示条        可跳转教案管理
```

### ① 填写条件

- **必填**：教学主题、年级、学科
- **可选**：知识点（随年级联动）、课时长度（默认 45，限 15–180）、第几课时、
  教材版本、教学目标的补充要求、难度倾向、其他要求
- 年级 → 学科 → 知识点三级联动，均由 `GET /lesson/ai/options?grade_id=` 提供，
  **学科按年级过滤**（学科按 `(grade_id, name)` 唯一，不做过滤会出现 60+ 同名选项）
- 提交前做同步校验：主题非空、年级/学科存在、**学科属于所选年级**、知识点属于所选年级、
  课时为 15–180 的整数。参数错误当场 400 返回，不让用户在轮询阶段才发现写错了

### ② AI 生成中

- 提交即返回 `job_id`，前端每 **2 秒**轮询 `GET /lesson/ai/jobs/{id}`
- 进度百分比 + 中文环节文案，六个节点：

  | 进度 | 文案 |
  |---|---|
  | 0 | 任务排队中 |
  | 15 | 解析教学条件 |
  | 45 | 拟定教学目标与重难点 |
  | 80 | 展开教学过程与师生活动 |
  | 95 | 校验并补全教案结构 |
  | 100 | 生成完成 |

- 「后台生成，稍后查看」按钮可关闭向导，任务继续跑，之后从生成记录回来

### ③ 预览与编辑

四个 tab 全部可编辑：

| Tab | 内容 |
|---|---|
| 基本信息 | 课题、教学目标、重点、难点、教学准备、教材版本、课时 |
| 教学过程 | 各环节名称/时长/概述/**教师活动**/**学生活动**，可增删排序 |
| 练习与作业 | 课堂练习（含答案）、作业布置、板书设计 |
| 预览 | 按 Markdown 版式通读全篇 |

实时校验与提示：

- 环节时长合计与课时不一致 → 警告条：「各环节合计 X 分钟，与设定的 Y 分钟不一致」
- 质量提示条按 `generation.quality` 变色：`high` 绿 / `medium` 黄 / `low` 红
- 明确列出 `generation.missing` —— **哪几节是系统补的**，提示重点核对，不假装生成完整
- 「重新生成」回到第 ② 步；「导出 Markdown」直接下载

### ④ 存入教案库

- 提交用户在编辑界面改过的全部字段（未改的取生成结果原值）
- 服务端重新校验年级/学科存在性与归属关系，避免写入跨年级脏数据
- 落库时标记 `ai_generated=1`、`ai_job_id=<任务 id>`，写一条 `OperationLog`（AI 产物入库审计）
- 成功后可「去教案管理继续编辑」，后续上传课件、共享、复制走既有教案流程

---

## 三、接口

前缀 `/api/v1/lesson/ai`，全部需教师身份。

### POST /generate — 提交生成任务

请求：

```json
{
  "topic": "分数的初步认识",          // 必填
  "grade_id": 3,                      // 必填
  "subject_id": 12,                   // 必填，须属于 grade_id
  "knowledge_point_id": 88,           // 可选，须属于 grade_id
  "duration_minutes": 45,             // 可选，默认 45，限 15~180
  "period": "第1课时",                 // 可选
  "objectives": "侧重动手操作",        // 可选，补充要求
  "textbook_version": "人教版",        // 可选
  "difficulty": "中等",                // 可选
  "extra_requirements": "需要小组活动"  // 可选
}
```

响应：

```json
{
  "code": 0, "message": "任务已提交，请轮询生成进度",
  "data": {
    "job_id": 128, "status": "pending", "progress": 0,
    "stage": "任务排队中", "poll_url": "/api/v1/lesson/ai/jobs/128"
  }
}
```

### GET /jobs/{job_id} — 轮询进度

```json
{
  "job_id": 128, "status": "success",   // pending/running/success/failed
  "progress": 100, "stage": "生成完成", "error": null,
  "created_at": "2026-10-22 15:20:11", "finished_at": "2026-10-22 15:20:53",
  "result": { /* 完整教案，结构见第四节 */ }
}
```

### GET /jobs — 生成记录

`?limit=20`（1–100）。返回 `items[]`，**不含 `result`**（避免响应体过大），
额外带 `topic` / `duration_minutes` 便于列表展示。

### POST /jobs/{job_id}/save — 保存到教案库

请求体可覆盖任意字段，未传的取生成结果原值（前端只提交改动部分）：

```json
{ "title": "...", "objectives": "...", "stages": [ { "name": "...", "duration_minutes": 5,
  "content": "...", "teacher_activity": "...", "student_activity": "..." } ] }
```

响应：`{"plan_id": 302, "title": "..."}`
副作用：`LessonPlan.ai_generated=1`、`ai_job_id=job_id`，写 `OperationLog`。

### GET /jobs/{job_id}/export — 导出

返回 `text/markdown; charset=utf-8`，`Content-Disposition` 用 RFC 5987
（`filename*=UTF-8''...`）保证**中文文件名不乱码**，非法字符替换为 `_`，截断 60 字。
Markdown 可用 Word 直接打开，也可粘贴到教研平台。

### GET /options — 表单候选

`?grade_id=3` → `{ grades, subjects, knowledge_points }`。
不传 `grade_id` 时 `subjects`/`knowledge_points` 为空（避免全量同名学科）。

---

## 四、数据结构

### 存储：`edu_lesson_plan` / `edu_lesson_stage`

新增列（均已登记进 `db_migrations.MIGRATION_COLUMNS`，老库自动补列）：

| 表 | 列 | 类型 | 用途 |
|---|---|---|---|
| `edu_lesson_plan` | `teaching_preparation` | TEXT | 教学准备（教具/课件/学具/课前任务） |
| | `class_exercise` | TEXT | 课堂练习（随堂检测题，含答案） |
| | `ai_generated` | INTEGER DEFAULT 0 | 是否 AI 生成（兼容 SQLite 用 0/1） |
| | `ai_job_id` | INTEGER | 来源任务 `sys_agent_job.id` |
| `edu_lesson_stage` | `teacher_activity` | TEXT | 教师活动 |
| | `student_activity` | TEXT | 学生活动 |
| `sys_agent_job` | `progress` | INTEGER DEFAULT 0 | 进度百分比 |
| | `stage` | VARCHAR(64) | 当前环节名 |

复用列：`title`(128) / `topic`(128) / `subject_id` / `grade_id` / `textbook_version`(64) /
`knowledge_point_id` / `duration_minutes` / `period`(32) / `objectives` / `key_points` /
`difficulties` / `board_design` / `homework` / `reflection` / `creator_id` / `is_shared`。

`copy_plan` **不继承 `ai_job_id`**（那条任务属原作者，与副本无溯源关系），但保留
`ai_generated`，教案库仍能区分来源。

### 生成结果（`result`）

```json
{
  "title": "分数的初步认识", "topic": "分数的初步认识",
  "grade_id": 3, "grade_name": "三年级",
  "subject_id": 12, "subject_name": "数学",
  "textbook_version": "人教版", "knowledge_point_id": 88, "knowledge_point_name": "分数的意义",
  "duration_minutes": 45, "period": "第1课时",
  "objectives": "1. ...\n2. ...", "key_points": "...", "difficulties": "...",
  "teaching_preparation": "...",
  "stages": [
    { "name": "导入新课", "duration_minutes": 5, "content": "设计意图...",
      "teacher_activity": "出示...提问「...」", "student_activity": "观察并回答...",
      "sort_order": 0 }
  ],
  "class_exercise": "...", "homework": "...", "board_design": "...",
  "generation": {
    "mode": "llm",                    // llm / rule
    "is_fallback": false,
    "missing": ["教学准备"],           // 系统补齐的章节中文名
    "warnings": ["各环节时长合计 60 分钟，与课时 45 分钟不一致，已按原占比缩放"],
    "stage_total_minutes": 45,
    "llm_enabled_hint": true,
    "quality": "medium"               // high / medium / low
  }
}
```

`generation` 是**可信度账本**，不是装饰字段：

- `mode=rule` 表示没走 LLM（未配 `LLM_API_KEY` 或调用失败），产物来自规则引擎
- `missing` 列出被模板补齐的章节，前端必须明确提示
- `quality`：`rule` 模式或缺失 ≥3 章 → `low`；有任何缺失/告警 → `medium`；全清 → `high`

---

## 五、异常处理

### 提交/查询边界（15 条，已逐条实测）

| 场景 | 返回 |
|---|---|
| 教学主题为空 | 400 教学主题不能为空 |
| 未选年级 / 学科 | 400 请选择年级 / 请选择学科 |
| 年级不存在 / 学科不存在 | 400 |
| 学科不属于所选年级 | 400，并提示改用 `/edu/subjects?grade_id=` 重选 |
| 知识点不属于所选年级 | 400 该知识点不属于所选年级 |
| 课时非数字 | 400 课时长度必须是分钟数 |
| 课时 < 15 或 > 180 | 400 课时长度应在 15~180 分钟之间 |
| 学生身份调用任一端点 | 403 |
| 读/存/导出**他人**任务 | 403 无权查看/保存/导出该任务 |
| 任务不存在 | 404 任务不存在 |
| 对非 `lesson` 任务（如出题）操作 | 404 任务不存在 |
| 任务未成功就保存/导出 | 400 该任务尚未生成成功，无法保存/导出 |
| 超频（默认 12 次/分钟） | 400「AI 调用过于频繁（每分钟上限 12 次），请稍后再试」 |

> 注意：限流走的也是 `BusinessException`，因此状态码是 **400** 而非 429。
> 前端若要区分限流，请匹配 `message` 内容，不要按状态码判断。

### 生成失败

`job.status=failed` + `job.error` 存面向用户的中文原因（截断 500 字），
`stage` 置为「生成失败」。前端在向导内展示错误并提供「重新生成」。
**失败不落库** —— 教案库不会被半成品污染（生成与保存分离的核心目的）。

### 内容不完整

LLM 输出不可信（漏章节、环节时长合计 60 分钟但课时只有 45、返回空数组），
因此无论 LLM 成功与否都过一遍 `_assemble()` 结构校验：

| 缺陷 | 处理 |
|---|---|
| 章节短于 8 字（空壳） | 先用规则引擎内容回填，仍空则写「（生成内容缺失，请补充）」并记入 `missing` |
| 环节数组为空 | 按模板补足 5 个环节，记入 `missing` |
| 环节数不足 | 按 `STAGE_FILL_ORDER` 补：**课堂小结 → 作业布置 → 巩固练习 → 导入新课 → 新课讲授**（先保收尾，没有小结与作业的课无法收口） |
| 环节名重复/包含（「导入」vs「导入新课」） | 用包含关系归并，不并存 |
| 时长合计 ≠ 课时 | 按原占比缩放，记入 `warnings` |
| 时长分配被截断偏短（45 分钟给导入仅 4 分） | 四舍五入 + 差额补偿，15–180 分钟全区间精确 |
| 师生活动缺失 | 记入 `warnings`：这篇教案退化为「教学流程提纲」 |

**降级策略**：未配 `LLM_API_KEY` 或 LLM 调用失败时，`fallback()` 用规则引擎按学段/
学科/知识点套模板并注入具体内容，是一件**真正能用的教案**，不是占位空壳；
离线部署下依然可交付，但 `quality` 标为 `low`。

### 超时与僵尸任务

后台是 `daemon` 线程，进程重启后不会恢复，`status` 会永久停在 `running`。
因此轮询接口做双重判定：**超过 300 秒仍是 pending/running** 即视为僵尸任务，
对外返回 `status=failed` + 「生成超时（超过 300 秒未完成），请重试或减少课时后重试」。
没有这个判定，前端会永久转圈。

### 为什么是异步任务

真实 LLM 下教案分两段生成（目标+重难点 / 过程+练习），实测 25–60 秒。同步 HTTP 在这个
时长上不可靠：nginx 默认 `proxy_read_timeout` 60s、中间网关常见 30s 上限，超时后前端
拿到 502/Network Error，而服务端其实还在写库 —— 用户看到「生成失败」，后端却产生了
重复教案。故沿用出题/组卷的 `AgentJob` 模式（`agent="lesson"`，复用 `sys_agent_job`，
不新建表）。

### 两段式生成

教案正文一次生成会超出 `LLM_MAX_TOKENS=2048`，表现为 JSON 被截断（前端只看到「生成失败」，
实际是模型没说完）。拆成两次调用后每段约 800/1500 token，超限风险显著下降，
两次调用之间天然是一个进度节点。

---

## 六、验证情况

| 项目 | 结果 |
|---|---|
| `lesson_plan` 阶段 | 79 项 / 通过 78 / 失败 0 |
| `agent` 阶段 | 24 项 / 通过 23 / 失败 0 |
| `teacher + teaching` | 146 项 / 通过 143 / 失败 0 |
| **全量回归** | **850 项 / 通过 836 / 失败 0 / 跳过 14** |
| 异常路径 | 15/15 符合预期 |
| 僵尸任务 | 10 分钟前 running → `failed` + 超时文案 |
| 限流 | 连发 20 次 → 成功 12、限流 8，精确卡上限 |
| `ruff --select F,E9 backend/app/` | All checks passed |
| 静态门禁 | `check_weak_assertion` / `check_hardcoded_host` 均 OK |
