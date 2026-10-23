# 试卷管理 V2 重构契约（1.8.0）

> 基于题库 V2（权限/批量/AI），重构试卷管理：功能、权限、UI、批量、AI；不新增表、不删除历史试卷。

## 1. 权限
| 能力 | 权限点 |
|---|---|
| 列表/详情 | `paper:list` |
| 创建/编辑/删除/批量写 | `paper:write` |
| 分享 | `paper:share` |
| 导出 | `paper:export` |
| AI 分析/推荐 | `paper:ai` |

- 列表可见性：sys_admin 全量；其他用户 = 本人创建 / `is_shared=true` / `PaperShare.to_user_id=本人`。
- 详情/复制/导出：`_assert_paper_readable`（创建者、被共享者、公开共享、sys_admin）。
- 编辑/删除：创建者 / sys_admin；grade_admin 仅公共卷或本人。
- 学生全部 403。

## 2. 校验
- 创建/编辑：
  - name 非空≤128；
  - grade_id/subject_id 必填且 subject.grade_id==grade_id；
  - items 至少 1 题；question_id 必须存在且为当前用户可访问（公共或本人私有；共享卷不扩大题库权限）；
  - 每道题 grade/subject 必须与试卷一致；
  - 重复 question_id 拒绝；
  - score 0-1000；duration 1-300；总分由 items score 求和，忽略客户端伪造 total_score。
- 编辑其余字段（名称/时长/年级/学科）；不改变 creator/source。
- 分享：user_ids 至少 1，目标必须是教师；去重；通知保留。
- 删除：被 Task 引用时拒绝（保留旧行为）；批量删除跳过被引用项。
- 导出保留 excel/word/pdf/html。

## 3. 接口（question.py 的 paper 部分扩展，保持旧路径/响应兼容）
- `GET /question/papers`：保留筛选，新增 `source`、`shared`、`creator_id`（sys_admin）、`sort`（created_desc/updated_desc）；返回 items/total/page，item 增加 `subject_name/grade_name/creator_name/item_count/ai_source`。
- `GET /question/papers/stats`：总数/题量/平均分/科目分布/年级分布/来源分布/共享数/AI 卷数。
- `POST /question/papers/batch`：`{action, ids, payload}`：
  - `delete`：引用任务进 skipped；
  - `copy`：复制为当前用户新卷；
  - `share`：payload.user_ids，仅 owner/sys_admin，非 owner 进 skipped；
  - `export` 不做批量（前端逐个下载）。
  返回 `{done, skipped}`；同批无权限整体 403。
- `POST /question/papers/{id}/ai/analyze`（新 `paper_ai.py`）：`paper:ai` + readable；返回：
  `{analysis:{difficulty_ratio,type_distribution,knowledge_coverage,issues:[...]}, suggestions:[...], is_fallback}`；
  规则总是执行（题量/总分/重复题/缺答案/难度分布/知识点覆盖），LLM 可用时补充建议；LLM 失败只降级。
- `POST /question/papers/{id}/ai/recommend`：基于试卷薄弱知识点/难度缺口，从题库推荐候选题（不落库），返回 `{items:[{question_id,stem,type,difficulty,score,knowledge_point_name,reason}], is_fallback}`；候选必须当前用户可访问、同年级同学科、未在卷中。
- 旧接口保持：detail/create/update/delete/copy/share/export；`share` 兼容 `to_user_id` 单值；`create` 兼容旧 payload（不传 total_score 时自动算）。

## 4. 前端 `PaperManage.vue` 重构
- 顶部统计卡：试卷总数/总题量/平均分/共享卷。
- 筛选：年级→学科、来源、共享状态、关键词；分页。
- 表格多选 + 批量栏（写权限）：批量删除/复制/共享（共享选教师）；结果 done/skipped 汇总。
- 行操作：查看详情（抽屉）、编辑、复制、共享、导出、删除；按钮按 paper:write/share/export 显隐。
- 详情抽屉：试卷信息 + 题目列表（题型/难度/分值/知识点/题干），AI 分析按钮（展示规则+LLM 建议/is_fallback），AI 推荐题目（勾选后可加入试卷——通过编辑接口保存）。
- 手动组卷对话框增强：
  - 先选题（年级/学科/题型/难度/关键词筛选 + 多选），已选题列表支持上/下移/移除，分值可改，总分自动；
  - 试卷信息：名称/年级/学科/时长；
  - 保存调用现有 create/update。
- 保留 AI 智能组卷入口与使用结果。
- 权限按钮：write/share/export/ai 分别控制；只读用户可看列表/详情。
- 不新增依赖；API 走 api/index.js；build/lint/test/check:bundle 通过。

## 5. 验收
- 后端全量 E2E 0 失败；旧 paper API 兼容。
- 权限：学生 403；教师不能读/改/删他人未共享卷；共享卷可读；sys_admin 全量。
- 批量 delete/copy/share、stats、AI analyze/recommend 动态验证。
- 前端 build/lint/test/bundle；浏览器试卷列表/详情/批量/AI 正常。
- 版本 1.8.0；镜像构建推送（版本+latest+sha，内置模型缓存）。

## 6. 实现与验收（1.8.0）

- **权限**：list `paper:list`；create/update/delete/batch `paper:write`；share `paper:share`；export `paper:export`；AI `paper:ai`；grade_admin 补 `paper:write`（公共/本人卷）。列表可见性修复为「本人创建 / is_shared / PaperShare 接收」，sys_admin 全量；学生 403。
- **校验**：name≤128、grade/subject 必填匹配、items≥1、题目存在且可访问、题目同年级同学科、禁止重复、分值 0-1000、时长 1-300、总分由题分求和；编辑重建 items 同样校验。
- **接口**：新增 `GET /question/papers/stats`、`POST /question/papers/batch`（delete 引用 skipped/copy/share）；列表支持 source/shared/creator_id/sort；share 兼容 to_user_id；导出四格式保留。
- **AI**（`paper_ai.py`）：`/analyze`（难度/题型/知识点覆盖/问题/建议）、`/recommend`（薄弱知识点/难度缺口推荐候选题），无 LLM 规则降级 `is_fallback=true`，只读不落库。
- **UI**：PaperManage.vue 重构——统计卡、筛选、多选批量（复制/删除/共享）、详情抽屉、AI 分析/推荐、手动组卷选题器（筛选/多选/排序/改分/总分自动）、四格式导出，权限按钮控制。
- **验证**：E2E 850/836/0/14（旧 paper 路径兼容）；API 动态验证创建/越权/共享/批量/stats/AI；前端 build/lint/test/bundle；浏览器列表/详情/AI 按钮正常。
- **镜像**：1.8.0 构建/推送后回填 digest。

