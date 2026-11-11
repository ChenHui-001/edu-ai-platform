# 修复记录（2026-10-22）

> 本文件随每个修复提交增量更新，记录问题、改动、验证方式与回归结论。
> 修复顺序：P0 → P1 → P2；每个问题一个 commit，提交前跑对应验证，P0/P1 阶段结束后跑全量 E2E（`tests/run_all.py`）。

## 基线

- 版本：1.0.42；分支：master；修复前 HEAD：`e5bbcd7`
- 修复前基线验证：后端隔离实例可启动；自研全量 E2E 851 项 / 通过 837 / 失败 0 / 环境跳过 14；前端 `npm run build` 成功
- 修复分支工作区在每笔提交前保持 `git status` 干净

---

## P0

### P0-1 默认密钥与演示口令可导致系统被接管

- **状态**：✅ 已修复
- **问题**：`SECRET_KEY` 使用公开占位符且启动不校验；登录页明文展示 admin 默认口令；空库种子管理员口令固定且未强制改密。
- **改动**：
  - `backend/app/core/config.py`：默认 `SECRET_KEY` 置空；新增校验——生产（`DEBUG=false`）弱/缺失密钥直接拒绝启动，开发态生成进程内随机临时密钥并告警。
  - `docker-compose.yml`：`SECRET_KEY` 改为 `${SECRET_KEY:?...}` 强制注入，并显式传 `DEBUG=false`。
  - `.env.example`：`SECRET_KEY` 留空 + 生成命令说明；新增 `DEBUG=false`。
  - `frontend/src/views/login/Login.vue`：演示账号下拉默认隐藏，仅 `VITE_SHOW_DEMO_ACCOUNTS=true` 时显示；新增 `frontend/.env.example` 说明。
  - `backend/app/services/init_db.py`：启动时检测 admin 仍为默认口令并输出安全告警。
  - `README.md`：安全部署说明与修复记录入口。
- **验证**：
  - 未配置 `SECRET_KEY` + `DEBUG=false` 时应用导入即失败（fail-closed）。
  - 开发态（`DEBUG=true`）自动生成临时密钥，服务可正常启动与登录。
  - `python -m py_compile` 通过；前端 `npm run build` 待本批结束统一验证。
- **回归风险**：自动化 E2E 以 `DEBUG=true` 启动，不受影响；生产 compose 用户必须提供 `.env`（已写入 README）。

### P0-2 客观题答案口径不统一（判断题/导入多选系统性误判）

- **状态**：✅ 已修复
- **问题**：判分只对 JSON 数组做集合比较；页面建判断题标准答案存「正确」而学生提交选项 key「A」；导入的多选题答案常为 `"A,C"` 字符串，均被精确字符串比较判错。
- **改动**：
  - 新增 `backend/app/utils/answer.py`：`to_token_set` / `normalize_answer` / `answers_match`，支持判断题 `正确/错误/对/错/T/F/true/false/A/B` 互认、多选题 JSON 数组与 `A,C`/`A、C`/`AC` 归一化、空答案判错。
  - `backend/app/agents/grading_agent.py`：`_grade_objective` 改用统一比较器，错误提示输出归一化后的标准答案。
  - `backend/app/api/v1/question.py`：创建/编辑/导入判断题时若缺选项自动补齐 A（正确）/B（错误），导入的判断题不再无可点选项。
  - 新增 `tests/verify_answer_normalization.py`（stdlib 断言脚本，无 pytest 依赖）。
- **验证**：`python tests/verify_answer_normalization.py` 全部通过（判断题 5 种标准写法 × 4 种学生写法、多选题 4 种写法、单选/填空边界）；改动文件 `py_compile` 通过。
- **回归风险**：历史判断题的「正确/错误」数据无需迁移即可正确判分；E2E 现有 `T/F` + JSON 数组用例保持通过（将在 P0 批次末跑全量确认）。

### P0-3 删除试卷/学科/年级级联清空教学数据

- **状态**：✅ 已修复
- **问题**：`edu_task.paper_id` 等外键为 `ON DELETE CASCADE`，删除试卷会物理删除任务、提交、作答；删除学科/年级会级联清空整科/整年级题目、试卷、任务与成绩，且接口无任何引用检查。
- **改动**：
  - `backend/app/api/v1/question.py` `delete_paper`：删除前统计引用任务，存在则 400 阻断并提示先处理任务。
  - `backend/app/api/v1/edu.py` `delete_subject`：检查题目/试卷/任务/知识点/教案引用。
  - `backend/app/api/v1/edu.py` `delete_grade`：检查班级/学科/知识点/题目/试卷/任务引用。
- **验证**（隔离 DB 实例，真实数据副本）：
  - 删除被任务引用的试卷 → 400「该试卷已被 1 个作业/考试引用…」；
  - 删除有数据的学科 → 400 并列出「题目 31 个、试卷 39 个、作业/考试 41 个、知识点 2 个、教案 5 个」；
  - 删除有数据的年级 → 400 并列出各类引用；
  - 新建空学科后删除 → 成功（不误伤正常清理）。
- **回归风险**：E2E 资源管理用例只删除无引用的新建实体，预期不受影响；P0 批次末全量确认。

### P0-4 交卷 AI 批改持有 SQLite 写事务

- **状态**：✅ 已修复
- **问题**：`save_answers` 先 flush 作答即持有写锁，随后同步调用 LLM 批改（可能分钟级），期间全站其他写操作等满 `busy_timeout(5s)` 后报 `database is locked`；LLM 客户端默认重试 2 次，进一步放大耗时。
- **改动**：
  - `backend/app/services/grading_service.py`：作答 `flush` 后立即 `commit` 释放写锁，再进入 `_auto_grade_answers` 执行判分与短事务写回；判分失败时作答仍已保存、可重试。
  - `backend/app/agents/llm.py`：`ChatOpenAI(max_retries=1)`，避免 60s×3 的最坏耗时。
  - `backend/app/agents/grading_agent.py`：主观题并发批改改为整批共享截止时间，`fut.cancel()` + `shutdown(wait=False, cancel_futures=True)`，超时不再等待全部任务。
- **验证**：`py_compile` 通过；P0 批次全量 E2E 覆盖交卷/自动判分/错题收录链路（LLM 关闭场景），确认行为不变。
- **回归风险**：作答与判分不再原子提交；若判分阶段进程崩溃，答卷保留为未交卷态可由学生重试，优于原先全站写入阻塞。

---

## P1

### P1-1 批改详情越权读取他人答卷

- **状态**：✅ 已修复
- **问题**：`grading_detail` 只校验登录态与教师角色，不校验任务归属，遍历自增 `submission_id` 可读取全校学生答卷、标准答案与 AI 评语。
- **改动**：`backend/app/api/v1/grading.py` 增加 `DataScope` 依赖，非超管且 `task.creator_id != user.id` 时返回 403，与批改/打回/发布接口口径一致。
- **验证**：`py_compile` 通过；P1 批次末动态越权矩阵验证 teacher2 读取 teacher1 提交被 403。

### P1-2 附件预览/下载按 id 越权

- **状态**：✅ 已修复
- **问题**：`/attachments/{id}/preview|download` 仅校验登录，任意用户可枚举下载他人附件（注册证明材料、教案课件）。
- **改动**：`backend/app/api/v1/attachment.py` 新增 `_assert_attachment_visible`：上传者本人 / `sys_admin` / 共享教案的同科教师（按 TeachingAssignment）/ 匿名上传仅管理端可读；授权通过后才累加下载次数。
- **验证**：`py_compile` 通过；P1 批次末动态验证学生下载他人附件 403、上传者本人 200。

### P1-3 报表导出越权

- **状态**：✅ 已修复
- **问题**：`/report/export/excel` 统一用 `get_current_user`，学生传 `report_type=admin_overview` 即可导出全校统计（内部直接调用 `admin_overview` 绕过了其依赖）。
- **改动**：`backend/app/api/v1/report.py` 按报表类型分别校验：个人报表任意登录用户（仅本人）；班级报表需教师；系统报表需 `sys_admin/grade_admin`；非法 report_type 返回 400。
- **验证**：`py_compile` 通过；P1 批次末动态验证学生导出 admin_overview 返回 403。

### P1-4 移出班级越权

- **状态**：✅ 已修复
- **问题**：`remove_student` 的 `class_id` 参数完全未使用，任意教师可把任意班级学生 `class_id` 置空。
- **改动**：`backend/app/api/v1/edu.py` 校验班级存在、班级在 `DataScope.class_ids()` 内、学生确实属于该班级。
- **验证**：`py_compile` 通过；P1 批次末动态验证 teacher2 操作非任教班级被 403。

### P1-5 年级管理员数据范围失效

- **状态**：✅ 已修复
- **问题**：`DataScope.class_ids()` 对 grade_admin 直接返回 `None`（视为全校），用户列表也可拉全校 PII。
- **改动**：`backend/app/api/deps.py`：grade_admin 的班级按 `grade_admin_grade_id`（缺省 grade_id）查本年级；无管辖年级返回空列表（拒绝）；`grade_ids` 不再用 None 表示"无授权"；`student_ids` 同步收敛。`backend/app/api/v1/system.py` 用户列表对 grade_admin 追加年级过滤。
- **验证**：`py_compile` 通过；E2E 三端权限矩阵在批次末回归。

### P1-6 审计日志无操作人 + 密钥明文

- **状态**：✅ 已修复
- **问题**：中间件读取 `request.state.user` 但全仓无赋值，16k+ 条操作日志 `user_id` 全为 NULL；脱敏只认 password 三键，`llm_api_key` 明文入库且 grade_admin 可读。
- **改动**：`backend/app/api/deps.py` 在 `get_current_user` 中写入 `request.state.user`；`backend/app/middleware/audit.py` 新增按关键字递归脱敏（password/secret/token/api_key/authorization 等），查询参数与请求体统一处理。
- **验证**：`py_compile` 通过；P1 批次末动态验证新写操作日志带 user_id、ai-config 请求体 `llm_api_key` 落库为 `******`。

### P1-7 Token 生命周期

- **状态**：✅ 已修复（后端；前端登出传 refresh_token 在 P1-16 接入）
- **问题**：JWT 过期时间戳用 UTC 却与本地时间比较，12h token 实际 4h 失效；refresh token 无 jti，登出后仍可换新 access token。
- **改动**：`backend/app/api/deps.py` 两侧统一 UTC 比较；`backend/app/core/security.py` refresh token 增加 jti；`backend/app/api/v1/auth.py` logout 支持同时吊销请求体中的 refresh token。
- **验证**：`py_compile` 通过；P1 批次末动态验证 `exp=+1h` token 可用、登出后 refresh 被拒。

### P1-8 找回密码安全缺陷

- **状态**：✅ 已修复
- **问题**：验证码直接写入应用日志；未真实发送邮件却提示已发送；重置接口只校验 ≥6 位，可把密码改成 `123456` 绕过强度策略；无请求频率限制。
- **改动**：`backend/app/api/v1/auth.py`：接入 `sys_config` 的 SMTP 发送（smtp_host/port/user/password/from），未配置时失败关闭且不生成/记录验证码；移除验证码日志；按目标账号 10 分钟 5 次限流；重置密码复用 `validate_password_strength`。
- **验证**：`py_compile` 通过；动态验证未配置邮件时响应 `sent=false` 且日志无验证码；弱口令重置返回 400。

### P1-17 审计写放大与日志无界增长

- **状态**：✅ 已修复
- **问题**：审计中间件对每个 GET（含轮询）都同步写库；操作/错误/任务/AI 日志与已读通知无保留策略。
- **改动**：`backend/app/middleware/audit.py` 读请求（GET/HEAD/OPTIONS）不再写操作日志（5xx 仍落错误日志）；`backend/app/services/task_jobs.py` 新增 `clean_old_logs` 按保留期清理；`backend/app/services/init_db.py` 注册每日 04:30 清理任务。
- **验证**：`py_compile` 通过；E2E 日志审计用例仍可读；P1 批次末确认健康检查/轮询不再产生操作日志行。

### P1-9 判分结果落库的数据一致性

- **状态**：✅ 已修复
- **问题**：掌握度错把题目 id 当知识点 id；错题本 `wrong_answer` 恒空；学习记录在 save/finalize 双计且时长从不累加；未批主观题被标 auto_graded 且可按 0 分发布；客观题得分用 `q.score` 而非试卷项分值。
- **改动**：`grading_service.py`（掌握度按题目反查知识点、错题答案查 Answer.content、`_record_study` 只在 finalize 记一次并累加时长、按残留 auto 主观题置 not_graded）；`grading_agent.py`（`_grade_objective` 支持 `full_score`、结果补 `student_answer`）；`grading.py`（发布前按「主观题且 score=None 或 grader_type=auto」阻断；batch_grade 采纳时主观 auto→manual）。
- **验证**：`py_compile` + 归一化脚本通过；队友用内存 SQLite 断言覆盖掌握度/错题文本/学习记录/状态流转/发布口径；全量 E2E 851 项 0 失败。

### P1-10 打回后学生无法重新提交

- **状态**：✅ 已修复
- **问题**：reject 只清分数不改 attempt，`allow_retake=1` 时学生再交必报「次数已用完」。
- **改动**：`task.py` `submit_answers`：`last.status=="not_graded"` 且 `score is None` 时复用同一 attempt 覆盖重交；含待人工主观题（score 非空）的 not_graded 不放行，避免绕过次数限制。
- **验证**：`py_compile`；E2E 次数限制用例仍 PASS；批次末 E2E 0 失败。

### P1-11 LLM 429 永久熔断与交卷入口限流缺失

- **状态**：✅ 已修复
- **问题**：429/配额被当成永久鉴权失败，一次瞬时限流导致 AI 长期不可用；交卷自动判分不计数、单请求可放大 N 次调用。
- **改动**：`llm.py` 拆分鉴权/限流错误，限流改指数退避冷却（30→…→300s，成功即清零），`is_available` 不受冷却影响；`ai_config_service.py` 保存配置复位冷却；`task.py` 在 LLM 可用时按答题数计费限流；`agent.py`/`lesson_ai.py` 增加文本长度、列表数量、天数上限。
- **验证**：`py_compile`；队友脚本验证冷却/熔断/入参边界；全量 E2E 0 失败。

### P1-12 RAG 跨用户笔记泄漏

- **状态**：✅ 已修复
- **问题**：SQL 与向量检索的笔记分支均无 student_id 过滤，学生私密笔记可能进入他人 AI 上下文。
- **改动**：`rag.py` 新增 `student_id` 参数，笔记强制本人过滤、无归属时跳过 note；向量按「非笔记组/本人笔记组」分组查询；`tutor_agent.py`、`question_agent.py` 调用点传当前用户。
- **验证**：`py_compile`；队友用内存 SQLite + FakeCol 验证隔离与 where 结构；chromadb 缺失时异常自动降级 SQL。

### P1-13 AI 入参无上限

- **状态**：✅ 已修复
- **问题**：AI 接口 message/topic/items/days 无上限，单账号可放大 token 成本与内存。
- **改动**：`agent.py` 文本 ≤8000、items ≤50、count/days 范围校验（覆盖同步与异步 jobs 入口，校验先于限流与写库）；`lesson_ai.py` topic ≤200、长文本 ≤8000。
- **验证**：`py_compile`；队友边界脚本验证超限抛业务异常、边界值放行；E2E 正常值不受影响。

### P1-14 前端下载/预览/导出 401

- **状态**：✅ 已修复
- **问题**：报表/日志/附件/教案导出与预览使用裸 URL，浏览器无法携带 Authorization；AI 教案导出取错 token 键。
- **改动**：新增 `frontend/src/utils/download.js`（axios blob + Content-Disposition 文件名 + objectURL 管理）；`AdminReport/TeacherReport/LogManage/AttachmentManage/LessonPlanManage/AiLessonDialog` 全部改走带鉴权 blob 请求（报表补 `report_type` 参数）；`api/index.js` 增加 blob helper。
- **验证**：`npm run build` 成功（3.11MB dist）；grep 确认页面不再直开 API 裸地址；E2E 后端导出用例保持通过。

### P1-15 考试计时可绕过

- **状态**：✅ 已修复
- **问题**：前端倒计时用 `setInterval` 递减，后台/休眠暂停；后端不校验单次作答时长。
- **改动**：`ExamPaper.vue` 改为 `endTs` 墙钟 + `visibilitychange` 重算，到 0 自动交卷行为不变；`task.py` 提交时按 `task.duration*60+300s` 容差校验 `duration_seconds`。
- **验证**：`npm run build` 成功；`py_compile`；E2E 时间窗/交卷用例 0 失败。

### P1-16 会话/权限快照与登出

- **状态**：✅ 已修复
- **问题**：登出只清本地不调后端；refresh 只写 localStorage 不更新 Pinia；路由守卫只信可篡改的 localStorage。
- **改动**：`store/user.js` 新增 `applyPermission`、`logout` 先调后端并携带 refresh_token；`request.js` 刷新后动态同步 store；`MainLayout.vue` 启动 fetchProfile、退出 await；`router/index.js` 守卫优先 Pinia、localStorage 兜底。
- **验证**：`npm run build` 成功；动态验证后端 logout 后 refresh 返回 400；E2E 鉴权/登录链路 0 失败。

### P1-18 容器与构建可复现性

- **状态**：✅ 已修复
- **问题**：容器全程 root；前端构建用 `npm install` 未使用 lock；构建上下文包含测试/截图/文档；compose 无最小加固。
- **改动**：Dockerfile 建固定 UID/GID 的 app 用户、`npm ci`、Chroma 缓存迁到 `/home/app`、启动时修正 bind-mount 属主；supervisord 仅 uvicorn 降权（nginx master 保持 root）；compose 增加 `no-new-privileges`；`.dockerignore` 排除 tests/docs/tools/ui_shots/openapi 等。
- **验证**：静态审查 + `py_compile`（环境无 docker，未实机 build）；不影响本地启动与 E2E。

### P1-19 版本/文档/OpenAPI 对齐

- **状态**：✅ 已修复
- **问题**：VERSION=1.0.42 但前端 package 为 1.0.8、README/QUICKSTART 拉 1.0.8 镜像；openapi.json 仅 144 operations 且 version=1.0.0。
- **改动**：前端版本与 lock 同步 1.0.42；README/QUICKSTART/DEPLOYMENT/RELEASE_CONSISTENCY 的版本号、镜像通道、退出码描述修正；重新生成 openapi.json（version=1.0.42、paths=166、operations=203）。
- **验证**：JSON 解析通过；openapi 覆盖 `/lesson/ai` 与 `/learning` 全部端点；E2E 不受影响。

### P1-20 测试断言假绿

- **状态**：✅ 已修复
- **问题**：`expect_denied` 只判 `success is not True`，500/422/405 也算拦截；一处 AI 用例对 POST 接口发 GET，405 仍 PASS；`/job/jobs` 路径笔误把 404 当拦截。
- **改动**：`e2e_framework.py` 收紧为 401/403（或显式 allow_statuses），FAIL 输出实际状态码与响应；`test_learning_hub.py` 显式 method 映射；`test_requirements.py` 修正路径、学生上传改为真实文件并断言 401/403；`test_learning.py`/`test_analysis.py` 适配真实 404/400 语义。
- **验证**：全量 E2E 851 项 / 通过 837 / 失败 0 / 环境跳过 14，收紧后未出现假绿掩盖。

---

## P2

### P2-1 编辑任务缺少参数校验

- **状态**：✅ 已修复
- **改动**：`task.py` `update_task` 复用创建时的范围校验：标题/说明长度、时长 >0、作答次数 ≥1、及格分 ≤ 试卷总分、时间格式与先后关系、布尔字段类型；非法输入 400 而非 500/脏数据。
- **验证**：`py_compile`；全量 E2E 中「教师可编辑任务」「非法参数」用例 0 失败。

### P2-2 成绩中心汇总只统计当前页

- **状态**：✅ 已修复
- **改动**：`task.py` `my_scores` 的 count/avg/max/min/pass_rate 改为对全量已评分记录做 SQL 聚合（`count/avg/max/min/sum(case)`），不再用当前页 rows。
- **验证**：`py_compile`；E2E 成绩中心/排序用例通过。

### P2-3 内置角色初始化覆盖管理员定制

- **状态**：✅ 已修复
- **改动**：`init_db.py` `init_roles` 只新建时写种子元数据；已有角色只补缺失权限、不删除新增权限、不覆盖 `is_active/data_scope/name`，重启不再静默回滚定制。
- **验证**：`py_compile`；E2E 角色保护/权限矩阵用例通过。

### P2-4 CORS 通配来源 + credentials 无效组合

- **状态**：✅ 已修复
- **改动**：`main.py` 当 `CORS_ORIGINS` 含 `*` 时 `allow_credentials=False`（本项目鉴权走 Bearer，无 Cookie），避免浏览器拒绝该组合。
- **验证**：`py_compile`；E2E 不受影响。

### P2-5 切换 PostgreSQL 时轻量迁移静默失效

- **状态**：✅ 已修复
- **改动**：`db_migrations.py` 非 SQLite 环境显式跳过 PRAGMA 补列并提示使用 Alembic（依赖已内置），不再逐列报错/制造「已迁移」假象。
- **验证**：`py_compile`；SQLite 启动迁移日志正常。

### P2-6 AI 配置缺少范围校验、清空 Key 不生效

- **状态**：✅ 已修复
- **改动**：`ai_config_service.py` 对 temperature 0~2、max_tokens 64~8192、timeout 5~600 与 provider 白名单做入口校验；`llm.py` `_get_db_value` 对 `llm_api_key` 的显式空串返回空（关闭 AI），不再回落到 .env 旧密钥。
- **验证**：`py_compile`；E2E AI 配置脱敏/保存用例通过。

### P2-7 前端 ECharts 全量引入

- **状态**：✅ 已修复
- **改动**：新增 `frontend/src/utils/echarts.js` 按需注册折线/柱状/饼图/雷达及必要组件；`EChart.vue`、`MasteryMap.vue` 改用该入口；`vite.config.js` 移除 `echarts-for-react` 分包引用、告警阈值恢复为 800KB。
- **验证**：`npm run build` 成功；charts 分包 1036KB→667KB、gzip 343KB→225KB；构建仅提示 element 1.09MB 超阈值（已知待按需化）。

### P2-8 前端日期/时区处理不统一

- **状态**：✅ 已修复
- **改动**：新增 `frontend/src/utils/date.js`（`parseServerDate` 把空格转 T 兼容 Safari，`formatLocalDate` 按本地时区取日期）；`StudyGoals.vue` 打卡日历不再用 `toISOString()`（修复东八区 0-8 点错格）；`MyFavorites.vue` 「最近一周」不再因 Safari Invalid Date 恒为 0。
- **验证**：`npm run build` 成功。

### P2-9 生产环境播种已知口令演示账号

- **状态**：✅ 已修复
- **改动**：新增 `SEED_DEMO_DATA` 配置（默认 true 保留本地体验）；`init_db.init_demo_data` 关闭时跳过；compose/`.env.example` 暴露该开关，生产建议设为 false，只保留 admin 与基础数据。
- **验证**：`py_compile`；默认 true 时全量 E2E 种子数据正常；README 与 `.env.example` 的演示账号说明已同步。

