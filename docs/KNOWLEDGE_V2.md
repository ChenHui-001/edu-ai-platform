# 知识点管理 V2 · 实现契约（阶段 1+2）

> 目标：树形结构、数据范围权限、批量操作、可用的管理工作台；RAG/AI 在后续阶段接入。
> 本文件是前后端并行实现的接口契约，字段名/路径不得随意改动。

## 1. 数据模型（KnowledgePoint）

新增列（`backend/app/models/edu.py`）：

| 列 | 类型 | 说明 |
|---|---|---|
| `textbook_version` | String(64) nullable | 教材版本 |
| `status` | String(16) default `published` | `draft/published/archived` |
| `source` | String(16) default `manual` | `manual/import/ai/seed` |
| `owner_id` | FK sys_user nullable | 创建者（保留操作人） |

保留 `grade_id/subject_id/term/parent_id/level/path/code/description/difficulty/keywords/sort/is_active`。
约束/规则：
- `parent_id` 必须同 `grade_id` + `subject_id`；根节点 `parent_id=NULL`、`level=1`、`path=str(id)`；
- 子节点 `level=parent.level+1`、`path=f"{parent.path}/{id}"`；服务端维护，不接受客户端伪造；
- 同级不允许重名；同一 `code` 不允许重复（非空时）；
- 删除：有子节点、被题目引用、有掌握度/复习计划引用时拒绝。

## 2. 权限

- `sys_admin`：所有年级/学科。
- `grade_admin`：仅 `grade_admin_grade_id`（缺省 `grade_id`）年级。
- `teacher`：仅 `TeachingAssignment` 中 active 的 `(grade_id, subject_id)` 组合；无任教安排的学科/年级禁止写。
- `student`：只读本年级 `published` 知识点；禁止任何写/导入/重建。
- 读取（tree/list/detail）：
  - 学生：强制 `grade_id == user.grade_id`；
  - 教师/年级管理员/管理员：默认可读全部已发布；`status=all` 仅管理员可见 draft/archived。
- 所有写接口在 `knowledge.py` 内用 helper 校验，越权返回 403。
- `POST /edu/knowledge/reindex` 保留教师可调用（E2E 既有契约），但需 `resource:knowledge:write`。

## 3. API（新文件 `backend/app/api/v1/knowledge.py`，前缀 `/edu`，tag `知识点`）

### 3.1 读取
`GET /edu/knowledge/tree`
- query：`grade_id?, subject_id?, term?, keyword?, status?`（默认 `published`；`status=all` 仅管理员）
- 返回：`ok({items:[node], total})`，node 嵌套 `children`；排序 `sort asc, id asc`。
- node 字段：`id,name,code,path,level,parent_id,grade_id,subject_id,grade_name,subject_name,textbook_version,term,description,difficulty,keywords,sort,status,source,owner_id,question_count,child_count,children`。
- student 强制本年级。

`GET /edu/knowledge`（兼容旧接口，平铺数组）
- 同过滤参数；返回 `ok([node...])`（无 children）。

`GET /edu/knowledge/list`（兼容旧接口）
- query：`grade_id?,subject_id?,level?,keyword?,status?,params_limit?`；返回平铺数组。

`GET /edu/knowledge/{id}`
- 返回 node + `breadcrumb:[{id,name}]` + `question_count`；不存在 404；学生无权年级 403。

`GET /edu/knowledge/stats`
- query 同 tree；返回 `{total,published,draft,archived,with_questions,by_grade:[{grade_id,grade_name,count}],by_subject:[{subject_id,subject_name,count}]}`。

### 3.2 写入
`POST /edu/knowledge`
- body 必填：`name,grade_id,subject_id`；可选 `parent_id,textbook_version,term,description,difficulty,keywords,code,sort,status,source`。
- 校验：名称非空≤128；年级/学科存在且 `subject.grade_id==grade_id`；parent 存在、同年级同学科、未形成环；同级重名 400；写权限 scope 校验（parent 所属 scope 与目标 scope 都校验）。
- 服务端设置 `owner_id=user.id`、`source`（默认 manual）、`level/path`。
- 创建后调用 `index_knowledge(kp)`（失败不阻断）。返回 node。

`PUT /edu/knowledge/{id}`
- 可改 `name,parent_id,textbook_version,term,description,difficulty,keywords,code,sort,status`（grade/subject 不允许改，避免历史数据错位；移动年级/学科走 batch move + 管理员）。
- parent 变更校验同创建 + 环检测；重算自身与所有后代的 `level/path`；返回 node。

`DELETE /edu/knowledge/{id}`
- 引用检查：`children` >0 → 400「请先删除子级」；`Question.knowledge_point_id` >0 → 400；`KnowledgeMastery`/`ReviewPlan` >0 → 400。
- 成功删除；返回 `ok(message)`。

### 3.3 批量
`POST /edu/knowledge/batch`
body：
```json
{"action":"delete|publish|archive|update|move","ids":[1,2],
 "payload":{"parent_id":3,"status":"published","difficulty":"easy","keywords":"..."}}
```
- `delete`：逐个引用检查，能删的删，不能删的进 `skipped`；
- `publish/archive`：改 status；
- `update`：批量改 `status/difficulty/keywords/textbook_version/term`；
- `move`：payload.parent_id（可为 null 表示移到根）；只允许同 grade/subject；管理员额外允许 payload.grade_id/subject_id 整树移动到目标年级学科（同时改所有后代）；
- 返回 `{done:[ids], skipped:[{id,reason}]}`；无权限的节点进 skipped 或整体 403？**同批只要有一个越权节点，整体 403**（防部分写入歧义）。

### 3.4 导入导出
`GET /edu/knowledge/template`：xlsx 模板，列：
`年级,学科,教材版本,学期,单元,章节,知识点,难度,关键词,说明,编码`
（单元=一级节点，章节=二级节点，知识点=三级；为空则按层级自动归并到上一级）。

`POST /edu/knowledge/import`（multipart）
- form：`file`（xlsx/csv）、`dry_run`（bool，默认 false）。
- 校验：每行年级/学科必须存在且匹配；按（年级,学科,单元,章节）自动建中间层；同级重名跳过；难度枚举 easy/medium/hard。
- 返回：`{dry_run,created,updated,skipped:[{row,reason}],errors:[{row,message}]}`。
- 写权限按行校验，任何行越权 → 该行进 errors（不写入），不要整体 500。

`GET /edu/knowledge/export`：query 同 tree；xlsx，列与模板一致，按树展平并带层级前缀。

### 3.5 兼容/旧接口
- 保留 `GET /edu/knowledge/mastery-overview` 原路径不变（保留在 edu.py 或迁移到 knowledge.py 均可，路径必须不变）。
- 旧 `GET /edu/knowledge`/`list` 行为保持“平铺数组”，现有 E2E 依赖。

## 4. 前端（`KnowledgeManage.vue` 重写）

- 顶部：标题、统计（总数/已发布/关联题目数）、按钮：刷新、新增根节点、导入、导出、AI 生成（先占位禁用或后续接入）。
- 筛选：年级、学科、学期、状态、关键词；树/列表视图切换。
- 左树：`el-tree`（`node-key=id`, `default-expand-all`, `filter-node-method` 按名称/keywords）；节点显示名称 + Lx + 题目数 badge；支持右键/悬停菜单（新增子级、复制、移动、删除）。
- 右详情：选中节点显示面包屑、状态/年级/学科/教材/编码、表单（名称/描述/关键词/难度/学期/排序/状态）；保存/删除/新增子级。
- 列表视图：`el-table` 多选，列：名称、层级、年级、学科、学期、难度、状态、题目数、操作；工具栏批量发布/归档/删除/移动。
- 导入对话框：下载模板、上传、dry-run 预览错误、确认导入、结果汇总。
- 导出：按当前筛选下载 xlsx。
- 权限：`can('resource:knowledge:write')` 控制写按钮；学生无菜单/无写按钮；后端仍强制 scope。
- 所有接口走 `frontend/src/api/index.js` 新增 `knowledgeApi`（不要用裸 URL）。
- 不引入新依赖；保持现有 Element Plus 按需组件（unplugin）用法；lint/test/build 必须通过。

## 5. 迁移与种子（阶段 1）

- 旧库一次性清空知识点数据（用户已确认不需要保留），补列 + 建索引后重新种子化为树：
  `年级 -> 学科 -> 单元(level1) -> 知识点(level2)`，每个学科至少 1 单元 + 2 个知识点。
- 新库 `create_all` 直接建新结构并种子。
- 旧接口/E2E：`/edu/knowledge?grade_id&subject_id` 仍返回平铺数组且非空；教师可创建/删除自己的知识点；学生创建被拒。

## 6. 验收

- 后端 `py_compile`；E2E 全量 0 失败；前端 build/lint/test/bundle 通过；浏览器冒烟 `/admin/knowledge` 正常。
- 动态验证：学生不能写、教师只能写自己任教学科/年级、跨年级 parent 被拒、重复同级名被拒、批量删除/发布、导入 dry-run 与真实导入。
