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

