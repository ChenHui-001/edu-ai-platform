# 知识点 V2 · RAG 与 AI 阶段契约（1.2.0）

> 前置：1.1.0 已完成知识点树/权限/批量/导入导出/新工作台。
> 本阶段只做：RAG 索引生命周期与语义检索 + 知识点 AI 生成/补全 + 对应 UI。

## 1. RAG 生命周期修复（`backend/app/agents/rag.py`）

1. 新增索引删除能力：`delete_knowledge_index(kp_id)`、`delete_question_index(q_id)`、`delete_note_index(note_id)`（Chroma `col.delete(ids=[...])`，异常只告警不阻断业务）。
2. 调用点：
   - `knowledge.py`：删除知识点（单个/批量）、移动/改名等需更新索引的写操作后，重新 `index_knowledge` 或删除；删除时调用 delete。
   - `question.py`：删除题目（单个/批量）后删除索引。
   - `learning/notes.py`：删除笔记后删除索引。
3. 检索生效 `RAG_SCORE_THRESHOLD`：`_vector_search` 与 `_sql_search` 返回前过滤 `score >= settings.RAG_SCORE_THRESHOLD`（阈值默认 0.3）。
4. 索引写入字段统一：
   - knowledge document：`名称。描述。关键词：...`；metadata：`type=knowledge,id,knowledge_point_id,path,grade_id,subject_id,term,status,level,textbook_version`；
   - `reindex_all` 与 `index_knowledge` 使用同一套字段；只索引 `status='published'` 的知识点、已发布/正常题目、未删除笔记。
5. 新增接口（knowledge.py）：
   - `GET /edu/knowledge/search?q=...&grade_id=&subject_id=&limit=10`：调用 `rag.search(types=["knowledge"])`，按读权限过滤（学生仅本年级 published），返回：
     `{items:[{id,name,path,description,difficulty,score,grade_id,subject_id,question_count}]}`。
   - `GET /edu/knowledge/rag-status`：`{db_total,index_count,coverage_percent,chroma_available}`；admin/teacher 可读。
6. `POST /edu/knowledge/reindex` 返回中追加 `index_count`/`coverage_percent`，不改变原有 stats 字段。

## 2. AI 接口（新文件 `backend/app/api/v1/knowledge_ai.py`，前缀 `/edu/knowledge/ai`）

统一要求：需 `resource:knowledge:write` + 知识点 scope（sys_admin/grade_admin/teacher 按 1.1.0 规则）；调用 `check_agent_rate`；单次 ids ≤ 50；无 LLM（`llm.is_available()==False`）时返回**规则引擎降级结果**并标记 `is_fallback=true`，不报 500。

### 2.1 生成知识点预览
`POST /edu/knowledge/ai/generate`
body：`{grade_id,subject_id,topic?,unit_name?,textbook_version?,term?,count?}`（count 3~12，默认 5）
- LLM 可用：用 JSON 输出生成 `{"unit_name","unit_description","points":[{name,description,keywords,difficulty}]}`；prompt 要求符合九年义务教育该年级学科、名称简短、难度 easy/medium/hard。
- 降级：基于 topic/unit_name + 已有同级知识点名称做模板（如 `{topic}核心概念`、`{topic}典型例题`），并返回 `is_fallback=true`。
- **只返回预览，不落库**。

### 2.2 批量补全建议
`POST /edu/knowledge/ai/enrich`
body：`{ids:[...]}`
- 返回 `{items:[{id,name,description,keywords,difficulty}], is_fallback}`；不落库，前端确认后调用现有 PUT/batch update 应用。
- 校验 ids 都存在且在写 scope；越权整体 403。

### 2.3 AI 应用（可选简化）
前端直接复用现有 `POST /edu/knowledge`（生成结果逐条创建）与 `PUT /edu/knowledge/{id}`（补全应用），不新增 apply 接口。

## 3. 前端（KnowledgeManage.vue + api/index.js）

1. `knowledgeApi` 新增：`search(params)`、`ragStatus()`、`aiGenerate(data)`、`aiEnrich(ids)`。
2. 顶部按钮新增「AI 生成」（写权限）：弹窗选择年级/学科/单元主题/数量 → 调 generate → 预览表格（可勾选）→ 「创建选中」逐条建到当前选中单元/根节点下；显示 `is_fallback` 提示。
3. 详情/列表新增「AI 补全」按钮：对当前节点或选中节点调 enrich → 预览建议 → 「应用」逐条 PUT（只更新 description/keywords/difficulty）。
4. 筛选区新增「语义搜索」输入/按钮：调用 search，结果列表显示 名称/路径/得分/题目数，点击定位树节点。
5. 「重建索引」附近显示 RAG 状态（db_total/index_count/coverage），重建后刷新。
6. 全部走 axios；写按钮受 `resource:knowledge:write` 控制；lint/build/test/check:bundle 必须通过。

## 4. 验收

- py_compile；后端 E2E 全量 0 失败；前端 build/lint/test/bundle。
- 动态验证：删除知识点后 Chroma 数量下降（不再残留）；语义搜索返回相关知识点且低分被阈值过滤；无 LLM 时 generate/enrich 返回 is_fallback=true；有 LLM 时返回结构化预览；学生不能调 AI 写接口。
- 版本 1.2.0；镜像构建+推送 Docker Hub（版本 + latest + sha）。
