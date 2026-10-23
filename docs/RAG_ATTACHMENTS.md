# 附件文本解析 → Chroma 索引 → AI 引用来源（1.4.0）

## 目标

知识点资料附件进入 RAG：AI 答疑时可以检索附件正文，并在回答下方展示引用来源（文件名 + 知识点路径），**不改变、不阻塞原有大模型调用链路**。

## 一、文本解析（`backend/app/services/attachment_parser.py`）

- PDF：PyMuPDF（`fitz`），最多 40 页；
- xlsx：openpyxl（只读，最多 500 行/表）；
- docx/pptx：直接解析 zip 内 XML 文本节点（不新增 python-docx/python-pptx 依赖）；
- txt/md/csv：UTF-8/GB18030 解码；
- 图片、旧版 doc/xls/ppt 暂不解析，返回空字符串；
- 单附件最多 6 万字，失败只记录日志，不影响上传/下载/AI。

## 二、Chroma 索引（`backend/app/agents/rag.py`）

- chunk：按段落切分，约 900 字/块，最多 40 块；id 形如 `att_{attachment_id}_{chunk}`；
- metadata：`type=attachment, attachment_id, knowledge_point_id, filename, path, grade_id, subject_id, term, status, chunk_index, ext`；
- **只索引**：知识点 `published + is_active` 且附件 `visible_to_student=1`，避免隐藏附件进入学生 AI 上下文；
- 上传：`BackgroundTasks` 后台解析/入库，上传接口立即返回；
- 可见性开关：开启→后台重建，关闭→立即删除索引；
- 删除附件/知识点下架/删除知识点：清理对应附件向量；
- 全量重建 `reindex_all` 追加附件阶段与统计 `attachment/attachment_total/attachment_index_count/attachment_coverage_percent`；
- 检索时 `_filter_valid_attachment_results` 兜底过滤：已删除/隐藏/下架/停用知识点附件即使有残留向量也不会进入上下文。

## 三、AI 引用来源

- `tutor_agent.search` 默认类型增加 `attachment`；`build_context` 标记为「资料」；
- `TutorAgent._ref_meta` 输出附件来源：`{type:"附件", id, name:文件名, knowledge_point_id, knowledge_point_name, path}`；
- API `/agent/tutor`、`/agent/chat` 返回的 `data.references` 原样带到前端；
- `AgentChat.vue` 新增「引用来源」区块，展示类型/文件名/知识点。
- 原有 LLM 调用、JSON 输出解析、fallback 逻辑均未改动；索引失败只告警。

## 四、验证

- 容器真实 Chroma：上传 PDF → 后台索引 → `rag-status` attachment_total/index_count=1；学生 `/agent/tutor` 提问命中附件，`references` 包含「附件 + 文件名 + 知识点」；删除附件后索引数下降。
- 无 LLM（fallback）与有 LLM 均走同一参考来源结构；索引解析异常不影响 AI 调用。
- 后端全量 E2E 851/837/0/14；前端 build/lint/test/bundle；浏览器冒烟 47 页。
