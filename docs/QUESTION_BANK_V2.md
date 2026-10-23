# 题库 V2 重构契约（1.7.0）

> 目标：功能/权限/UI 重构，支持批量操作与 AI；历史题库数据可全部清空（用户已确认）。

## 1. 数据与迁移
- 复用 `Question / QuestionKnowledge / PaperItem`，不新增表。
- 一次性迁移 `run_question_v2_migration`：标记 `question_bank_v2_migrated`，首次启动清空 `edu_question`（级联 `question_knowledge`/`paper_item`），不重新播种；之后不再清空。
- 迁移放在 `main.py` lifespan（知识库 V2 迁移之后）。

## 2. 权限
- 读取列表/统计：`question:bank:list`（teacher/grade_admin/sys_admin）。
- 新增/编辑/删除/批量写：`question:bank:write`；删除仅 owner、sys_admin、grade_admin（公共/本年级）可执行。
- 导入：`question:bank:import`；导出：`question:bank:export`；公共题库上架：`question:bank:audit`（sys_admin/grade_admin）。
- 可见性（修复越权）：无论是否显式传 `bank_type`，普通教师只能看到「公共题库 + 本人私有」；显式 private 也必须加 owner 条件。sys_admin 全量；grade_admin 公共+本人，必要时本年级。
- 学生访问仍 403。

## 3. 后端接口（`question.py` 扩展，保持旧响应兼容）

### 3.1 列表
`GET /question/questions`
- 保留现有参数；新增 `source`、`sort`（created_desc/usage_desc/updated_desc）。
- 返回 items/total/page/page_size/type_stats；`type_stats` 必须与当前筛选一致（修复全局统计）。
- item 增补 `knowledge_point_name/source/type_label/difficulty_label`（已有保留）。

### 3.2 统计
`GET /question/questions/stats`（同列表筛选，无分页）
返回：`{total, by_type, by_difficulty, by_status, by_bank, with_analysis, with_knowledge, ai_source}`。

### 3.3 批量
`POST /question/questions/batch`
body `{action, ids, payload}`：
- `delete`：逐题检查 PaperItem 引用，能删的删（含 RAG 清理），被引用进 skipped；
- `publish` / `offline` / `draft`：状态变更；公共题库 publish 需 audit；
- `move_bank`：payload.bank_type=private/public；公共→需 audit 才可直接 published，否则 draft；
- `assign_knowledge`：payload.knowledge_point_id（可 null），校验知识点；
- `set_difficulty`：easy/medium/hard。
返回 `{done:[ids], skipped:[{id,reason}]}`；同批无权限整体 403；部分业务失败进 skipped。
兼容旧 E2E：单条 CRUD/status/duplicates/import/export 行为不变。

### 3.4 校验
- create/update：stem 非空；grade_id/subject_id 必填且 subject.grade_id==grade_id；kp 存在且同 subject/grade；难度/题型/分值/状态合法；缺 grade 不再默认 0。
- 编辑仅 owner / sys_admin；grade_admin 可编辑公共题（审核场景）；删除按权限。
- 公共题库发布状态：非 audit 角色强制 draft。

## 4. AI 接口（新文件 `question_ai.py`，prefix `/question/questions/ai`）

统一：`question:bank:write` + 题目归属校验；`check_agent_rate`；ids≤50；无 LLM 时规则降级并返回 `is_fallback=true`，不 500；只返回预览，不落库。
- `POST /variants`：`{id,count=3,difficulty?}` → `{items:[{type,stem,options,answer,analysis,difficulty,score,knowledge_point_id}], is_fallback}`；LLM 生成同考点变式；降级为题干改写模板。
- `POST /enrich`：`{ids:[...]}` → `{items:[{id,analysis,knowledge_point_id,knowledge_point_name,difficulty}], is_fallback}`；补解析/知识点/难度建议。
- `POST /quality`：`{ids:[...]}` → `{items:[{id,issues:[{code,message,severity}]}], is_fallback}`；检查缺答案/解析/知识点、难度异常、完全重复指纹、AI 低质量题干。
- 复用 LLM/Agent 的 JSON 输出与降级方式；禁止修改既有 `question.py` 的 LLM 行为。

## 5. 前端（`QuestionBank.vue` 重写/大改）

- 顶部统计卡：题目总数/已发布/含解析/含知识点（来自 stats）。
- 筛选：年级→学科联动、知识点、题型、难度、状态、题库、来源、关键词；支持重置。
- 表格多选：
  - 列：题干（含题型/难度/分值标签）、知识点、题库、状态、来源、使用次数、操作；
  - 行点击/详情按钮打开详情抽屉：完整题干/选项/答案/解析/知识点/状态/来源，支持编辑、AI 变式。
- 批量栏（写权限）：发布/下架/删除/移动题库/分配知识点/修改难度/AI 补全/AI 质检；操作前确认，结果汇总 done/skipped。
- AI：
  - 保留「AI 智能出题」（现有对话框）；
  - 行/详情「AI 变式」：预览 N 道变式，勾选后创建；
  - 批量「AI 补全」：预览建议后应用到选中题；
  - 批量「AI 质检」：展示问题列表，可定位题目；
  - 无 LLM 显示 is_fallback 提示。
- 导入/导出/下载模板保留；导入结果明细保留。
- 权限：写/导入/导出/审核按钮按权限显隐；只读用户可看列表/详情。
- 不新增依赖；axios 走 api/index.js；build/lint/test/check:bundle 必须通过。

## 6. 验收
- 后端 E2E 全量 0 失败；旧 question API 兼容；新增批量/统计/AI 动态验证。
- 权限：学生 403；教师不能看/改他人私有题；grade_admin 公共审核；跨 scope 403。
- 前端 build/lint/test/bundle；浏览器题库列表/批量栏/AI 对话框正常。
- 版本 1.7.0；镜像构建推送（版本+latest+sha，内置模型缓存）。

## 7. 实现与验收（1.7.0）

- **迁移**：`run_question_v2_migration` 首次启动清空 `edu_question`（及 question_knowledge/paper_item），写 marker 后不再清空；用户已确认历史题库可删。
- **权限**：列表/统计/查重 `question:bank:list`；写/批量 `question:bank:write`；导入/模板 `question:bank:import`；导出 `question:bank:export`；公共题上架 `question:bank:audit`；grade_admin 补 `question:bank:write` 以便审核。修复显式 `bank_type=private` 拉取他人私有的越权。
- **后端**：严格校验 grade/subject/kp 一致性、题型/难度/分值/状态；公共题非 audit 创建/移动/发布强制 draft；批量 6 种 action；stats；source/sort；type_stats 与筛选一致；导入 Form 参数修复、逐行校验/去重；RAG 删除/索引同步保留。
- **AI**（`question_ai.py`）：`/variants`、`/enrich`、`/quality` 均只预览、无 LLM 规则降级 `is_fallback=true`；权限/归属/限流/ids≤50。
- **UI**：统计卡、完整筛选、多选批量栏（发布/下架/删除/移动题库/分配知识点/改难度/AI 补全/AI 质检）、详情抽屉、AI 变式/补全/质检、保留导入导出模板/查重/单题 CRUD。
- **E2E 适配**：`test_teacher` 知识点按年级+学科取；`test_teacher` 引用保护改用管理员删除；`test_learning` 前置题改 private；`test_requirements` kp 按年级+学科过滤。
- **验证**：E2E 850 项/通过 836/失败 0/跳过 14；API 动态验证创建/批量/统计/AI/越权；前端 build/lint/test/bundle；浏览器题库页统计/表格/详情正常。
- **镜像**：1.7.0 构建/推送后回填 digest。

