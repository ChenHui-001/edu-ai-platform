# AI 配置与 AI 智能模块优化（1.9.0）

## 1. AI 大模型配置（`AiConfig.vue` + `ai_config_service` / `system.py`）

### 后端
- `POST /system/ai-config/test` 接收 `db`；测试连接时若 `llm_api_key` 为空或含 `****`（已保存但前端不回显真实 key），自动读取 sys_config 中已保存的 key；凭据不回传。
- `test_ai_connection` 返回 `duration_ms`，便于 UI 展示响应耗时。
- `GET/POST /agent/list`、`GET /agent/status` 的 `provider/model` 必须读取 DB 配置（`_get_db_value`），不能再用 `settings` 环境变量，否则后台改了配置而 AI 页面仍显示旧值；补充 `key_configured`（DB 或 env 有 key）与 `llm_temperature/max_tokens`（可选）。
- 不改 LLM 调用/熔断/降级行为。

### 前端 `AiConfig.vue`
1. API Key 安全交互：
   - 加载时 **不把掩码 key 填进输入框**；显示占位「已保存（留空不修改）」与「未配置」状态；
   - 提供「清除已保存 Key」开关，勾选后保存发送空字符串；
   - 保存时：用户没输入且未勾选清除 → 不提交 `llm_api_key` 字段（避免空值误清）；输入新 key 才提交。
2. 测试连接：允许不填 key 直接测试（用已保存 key）；测试结果增加耗时（duration_ms），失败清晰提示。
3. 配置校验/提示：
   - 启用 AI 但未配置 Key（非 Ollama）时确认提示；
   - `custom` 提供商必须填写 API 地址；provider 变更填充默认 base_url/model（已有，保留）；
   - 展示当前配置来源（DB/env）、max_tokens 被上限收敛提示、最后保存时间（如 meta 可用）。
4. 视觉：状态卡展示启用状态/提供商/模型/Key 是否已配置；表单按钮沿用「测试连接/保存配置」。

## 2. AI 智能模块（`AgentChat.vue` / `AgentGenerate.vue`）

### AgentChat
- 删除重复的「参考」引用块（当前「引用来源」与「参考」重复展示）。
- 对话持久化：`localStorage`（键 `edu_chat_v2`）保存最近 50 条，刷新不丢；「新对话」清空并滚动到底。
- 消息操作：复制回答、重新生成最后一条问题、停止生成（AbortController）。
- 状态卡：显示 provider/model/key_configured；未启用时提示管理员到「AI 大模型配置」检查，管理员可点击跳转 `/admin/ai-config`。
- 保留流式、引用来源、错误提示；不引入新依赖。

### AgentGenerate
- 修复「一键保存到题库」：AI 结果可能给 `knowledge_point_ids` 数组，而题库 V2 只接受 `knowledge_point_id`；保存时映射第一个 id，并补齐 `grade_id/subject_id`（表单兜底），保存为 **private** 私有题（避免公共题默认草稿/审核语义）；逐条统计成功/失败并展示失败原因。
- 状态卡/提示：显示 DB 实际 provider/model 与 key 是否配置；未启用时给出配置入口（管理员）。
- 保留现有异步任务/轮询/结果渲染逻辑；不破坏题库 V2 创建校验。

## 3. 验收
- 后端：无需 key 的 config test 在已保存 key 场景可通过（mock 网络）；agent status/list 返回 DB provider/model；旧字段兼容。
- 前端：build/lint/test/check:bundle；浏览器 AI 配置页（保存/清空/测试按钮存在）、AI 助手页（引用来源仅一处、停止/复制/重新生成）、AI 出题页（保存逻辑无 JS 错）正常。
- E2E 全量 0 失败（AI 状态字段变化需回归 test_admin/agent 相关用例）。
- 版本 1.9.0；镜像构建推送（版本+latest+sha，内置模型缓存）。

## 4. 实现与验收（1.9.0）

- **AI 配置后端**：`test_ai_connection(data, db)` 空/掩码 Key 自动读 sys_config 已保存 Key（显式清空不回落 env），provider/model/base_url 同样 DB 优先，custom 缺 base_url 明确失败，所有返回补 `duration_ms`；`/system/ai-config/test` 注入 db。
- **Agent 状态**：`/agent/list`、`/agent/status` 的 provider/model 改读 DB 配置（DB>env），补 `key_configured/llm_temperature/llm_max_tokens`；`llm_enabled` 仍由 `is_available()` 决定；停用/未配 Key 的 tip 区分。
- **AI 配置 UI**：不再回填掩码 Key，空输入+占位提示；「清除已保存 Key」勾选显式清空；未输入且未勾选时保存不带 key 字段；测试连接允许空 Key 用已保存值，展示 duration/token；custom 地址必填、启用无 Key 确认、max_tokens capped/来源展示。
- **AgentChat**：删除重复引用块；localStorage `edu_chat_v2` 最多 50 条；新对话、复制回答、重新生成、停止生成（AbortController）；状态卡 provider/model/key 状态与管理员配置入口。
- **AgentGenerate**：saveAll 修复 `knowledge_point_ids→knowledge_point_id`、grade/subject 表单兜底、`bank_type=private`，逐条成功/失败统计并展示原因；状态卡/配置入口。
- **验证**：E2E 850/836/0/14；后端动态：保存假 key 后空 body 测试不报未配置（证明 DB key 生效）、agent status/list 返回 DB qwen/qwen-max + key_configured、清空 key 后 llm_enabled=false 但 provider/model 保留；前端 build/lint/test/bundle；浏览器三个 AI 页面无 console error。
- **镜像**：1.9.0 构建/推送后回填 digest。

