# 缺陷与改进单一 Backlog（试卷域 + 全局）

> **本文件是唯一入口。** 其他 `audit-reports/*.md` 只作为「当时的证据与复现记录」保留，
> 新发现一律往这里加一行，不再新开报告。修复进度以本文件的「状态」列为准。
>
> 基线：`VERSION=2.5.22`，master（2026-11-10 第三轮：P1 收尾 + F-02/F-04）
> 来源：`paper-analysis-2026-11-10.md`（P0×4 / P1×11 / P2×20）+ `structured-assessment-2.5.19-2026-11-10.md`（§5.5）
> 状态图例：`已修` = 本轮已改并验证；`待修` = 确认存在未处理；`待评估` = 需先确认影响面

---

## P0 — 可在下一次操作中直接造成事故或数据损失

| # | 问题 | 位置 | 状态 | 本轮处置 |
|---|---|---|:---:|---|
| P0-1 | PDF/答题卡导出把用户可控文本交给 reportlab → SSRF + 导出 500 | `services/paper_export_service.py` | **已修** | 新增 `_pdf_text()`（`_plain` 后再转义 `& < >`），题干/选项/答案/解析/知识点/卷名/大题名统一走它；`_safe_build()` 把排版期异常收敛成 400。反向验证：旧写法实测 reportlab **真的去下载了** `http://127.0.0.1:<port>/`（拿到响应后 `UnidentifiedImageError` → 500），新实现连接数 0 |
| P0-2 | 向导「编辑题目」抽屉的「确定」不回写，预览态编辑不存在 | `views/teacher/PaperWizard.vue` | **已修** | 抽屉改为 `applyEdit` + `Object.assign` 回写（`editTarget` 改 ref，按 `question_id` 重定位）；另加保存前「内容改动不入题库」确认，消除「看起来改好了」 |
| P0-3 | AI 一键组卷「只写描述、不选年级学科」异步路径 100% 失败 | `api/v1/paper_compose.py` | **已修** | 抽出 `_ai_resolve_params()`，同步 `/compose/ai` 与异步 `/compose/ai/async` 共用；修正 `compose_ai_async` docstring。反向验证：`出一份一年级数学期中卷` → 解析出 grade=1 / subject=2（不依赖 LLM） |
| P0-4 | 智能组卷 Agent 默认比例被 `int()` 截断 → 恒 0 题 + `NoneType` 崩溃 | `agents/paper_agent.py` | **已修** | 新增 `_split_counts()` 区分「比例/题量」并保证合计对齐；难度权重按 float 归一；`_ai_fill` 的 `PaperItem` 写入加 `paper is not None` 守卫，逐题 commit 改为一轮。反向验证：默认参数 10 题、`save=False` 不崩 |
| P0-5 | 列表页「编辑试卷」整卷覆盖写 → 抹平标准卷大题结构；删题后成绩不重算 | `PaperManage.vue` / `question.py` / `paper_compose.py` | **已修** | 详情接口回传 `section_code/section_sort`；前端 `openDialog`/`save`/`applyRecommendations` 全链路透传；`_normalize_paper_items` 保留三件套 |
| P0-6 | 无自动化行为回归，35 项修复无用例护航 | `tools/` / `backend/qa_audit_suite.py` | **已补** | 新增 `tools/verify_p0_fixes.py`（43 条接口级断言，临时库 + TestClient 走真实 HTTP，约 22s），覆盖 P0-1/3/4、P1-1/4/9/10、F-02/03/04，已接入 `auto_ship.sh` 的「0.4 行为回归」段 |

## P1 — 限制迭代速度与规模

| # | 问题 | 位置 | 状态 |
|---|---|---|:---:|
| P1-1 | 列表页编辑抹平大题结构 | `views/teacher/PaperManage.vue` | **已修**（随 P0-5） |
| P1-2 | 编辑页改名称/时长后保存按钮恒灰 | `views/teacher/PaperEdit.vue` | **已修**（meta 基线快照 → 置 dirty） |
| P1-3 | 「重构大题」静默清空未保存修改 | `views/teacher/PaperEdit.vue` | **已修**（dirty 时二次确认） |
| P1-4 | 删题后成绩不重算；重算时总分与客观分矛盾 | `api/v1/paper_compose.py` | **已修**（`remove_item` 复用 `_recalculate_after_change`；重算 `objective/subjective`；无作答行的提交跳过并上报 `skipped_no_answer`） |
| P1-5 | 版本回溯只还原 `name`/`duration` | `api/v1/paper_compose.py` | **已修**（补 `description/difficulty_ratio/exam_type/standard_id`，`status` 刻意不回滚；回传 `restored_fields`/`kept_fields`/`total_score_note`，前端弹「回溯结果」逐项说明） |
| P1-6 | 组卷抽题不做题库可见性过滤 → 预览泄露他人私有题 | `agents/paper_agent.py` | **已修**（`_visible()` = public 或本人 owner） |
| P1-7 | 自然语言组卷 LLM 契约与解析代码矛盾 | `agents/paper_agent.py` | **已修**（`_resolve_grade_subject()` 名称/序号 → id 反查，不再强依赖 LLM 返回 id） |
| P1-8 | 异步轮询一次抖动即中断整条链路 | `views/teacher/PaperWizard.vue` | **已修**（连续 3 次才判失败、失败文案提示先去确认避免重复组卷；`onUnmounted` 置中止标志） |
| P1-9 | 编辑页保存无版本冲突检测，后写覆盖先写 | `api/v1/paper_compose.py` / `views/teacher/PaperEdit.vue` | **已修**（新增 `ConflictException`(409)；`update_items` 比对 `current_version` 并回传双方版本；前端带版本号保存，409 时给「重新载入 / 留在本页」二选一） |
| P1-10 | 学生自主组卷题型下拉重复 + 默认值导致填空题抽不到 | `views/student/CustomPaper.vue` / `learning/tools.py` | **已修**（只用 `QUESTION_TYPE_LABELS`，默认改 `blank`，提交前归一别名；`pick_practice_questions()` 逐级放宽并回传 `relaxations`；补回 `total_score`） |
| P1-11 | 「放宽难度」兜底查询丢掉知识点约束 | `agents/paper_agent.py` | **已修**（`_fallback_fill()` 分两轮：先放宽难度保留知识点，仍不足才放宽知识点，`relaxations` 写进返回体与 `tip`） |
| P1-12 | `llm.py` 双实例各熔各的 / `_get_db_value` 每次开新 Session | `agents/llm.py` | **已修**（`get_llm()` 返回模块级 `llm_client`，单实例；`_get_db_value` 加 2s TTL 缓存，`reset_clients()` 连带清空） |
| P1-13 | 文档基线漂移（README 仍写镜像 2.0.0、ARCHITECTURE_ASSESSMENT 停在 2.2.19） | `README.md` / `docs/` | **已修**（拉镜像命令改用 `VERSION` 变量不再写死；架构评估加「时点快照」声明并指向本 backlog） |
| P1-14 | `index.html` 锁 `user-scalable=no` | `frontend/index.html` | **已修** |
| P1-15 | 多 worker 前提未闭合（IP 桶 / 限流缓存 / RAG 集合均进程内） | `core/security.py` 等 | 待评估（当前刻意单 worker） |

## P2 — 长期债务

| # | 问题 | 位置 | 状态 |
|---|---|---|:---:|
| P2-1 | 试卷「说明」在 `PUT /papers/{id}` 被丢弃 | `question.py:1596` | 待修 |
| P2-2 | 列表页批量操作无 loading，连点会重复执行 | `PaperManage.vue` | 待修 |
| P2-3 | 列表页 AI 组卷对话框是死代码（约 180 行） | `PaperManage.vue` | 待修 |
| P2-4 | 列表页初始化 `Promise.all` 无兜底 → 列表永不加载 | `PaperManage.vue` | 待修 |
| P2-5 | 详情抽屉「加载失败」空态不可达 | `PaperManage.vue` | 待修 |
| P2-6 | 导出全局单锁，导出别的行静默无响应 | `PaperManage.vue` | 待修 |
| P2-7 | 「从题库添加」分页参数名错（`size` vs `page_size`） | `PaperEdit.vue` | 待修 |
| P2-8 | 编辑页「缺口提示」永不显示（`generation_params.gaps` 未写入） | `PaperEdit.vue` / `paper_compose.py` | 待修 |
| P2-9 | 后端卷面体检 `issues` 前端完全丢弃 | `PaperEdit.vue` | 待修 |
| P2-10 | 「丢弃草稿」实际不丢弃（`confirmAction` 取消返回 false 而非抛异常） | `PaperEdit.vue` | 待修 |
| P2-11 | 草稿防抖定时器离开页面不清理 | `PaperEdit.vue` | 待修 |
| P2-12 | 向导第 2 步「考试时长」不生效（`form.duration` ≠ `saveForm.duration`） | `PaperWizard.vue` | 待修 |
| P2-13 | 演示数据造出「有分无作答行」的提交 | `services/init_db.py` | 待修（P1-4 已不再放大该问题） |
| P2-14 | LLM 异常原文回显给用户 | `agents/base.py` → `api/v1/agent.py` | 待修 |
| P2-15 | `ComposePreviewIn` / `ComposeSaveIn` 全 `Any` + `extra=allow` → 参数被静默吞 | `schemas/legacy_bodies.py` | 待修 |
| P2-16 | 限流超限返回 400 而非 429 | `core/rate_limit.py` | 待修 |
| P2-17 | `paper_ai` 与 `paper_compose` 可读判定不是同一套 | `paper_ai.py` | 待修 |
| P2-18 | `question.py` 导出端点硬编码教师卷 | `question.py:1929` | 待修 |
| P2-19 | 版本号并发计算无保护 → 偶发 400 | `services/paper_version_service.py` | 待修 |
| P2-20 | `paper_ai` 提示词直接拼接用户可控题干（提示词注入） | `paper_ai.py` | 待修 |

---

## 功能扩展进度（评估报告 §6.1）

| 编号 | 内容 | 状态 |
|---|---|:---:|
| F-01 | 35 项整理为单一 backlog（本文件） | **已完成** |
| F-03 | 班级维度薄弱知识点聚合（`GET /report/teacher/class-weak-points` + 教学报表页新卡片） | **已完成** |
| F-02 | 试卷版本 diff 可视化 | **已完成** |
| F-04 | AI 长任务可取消 + 结果持久化 | **已完成**（组卷全链路 + 教案后端，见下） |
| F-05 | 导出异步化 | 待做（第 3 批） |
| F-06 | AI 配置按 biz_type 细化预算 | 待做 |
| F-07 | 通知订阅偏好 | 待做 |

> F-03 实现要点：不新增表，直接聚合 `edu_knowledge_mastery`（学生 × 知识点的累计正确率），
> 按班级学生集合做 `sum(正确)/sum(总数)`；`min_answers` 挡住「1 人 1 题」的噪声；
> 正确率分档给出讲评建议。与 `knowledge-effect` 的区别是**不依赖 task_id**，
> 选完班级即可看，直接服务备课。

> **F-02 实现要点**：`GET /papers/{id}/versions/{v}/diff?against=current`，逻辑在
> `paper_version_service.diff_snapshots()`。`against=current` 走**现算**快照
> （`build_snapshot`）而不是读最新版本行 —— 最新一行可能是「回溯前」这类中间快照，
> 与用户看到的卷面不一致。差异含卷面字段 + 题目新增/移除/改动（分值、大题、题序、
> 题干、答案、解析、难度），长文本只回传 80 字摘要（一份卷的全文轻松上百 KB）。
> 不虚报变更：分值 5/5.0 视为相等，`difficulty_ratio` 按 JSON 键序归一后比较。
> 前端版本抽屉每行加「对比」，对比框里可直接「回溯到此版本」（复用同一套二次确认）。

> **F-04 实现要点**：`sys_agent_job` 加 `cancel_requested`（补列迁移 + DEFAULT 0），
> `agent_job_state` 增加 `request_cancel()/cancel_requested()/JobCancelled`。
> **取消是协作式的，不是杀线程**：LLM 往返是同步 HTTP 调用不可中断，接口只登记标志，
> worker 在批次边界（`on_progress`）看到才中止，落 `status='cancelled'` 且**不写 error**
> （取消不是故障，不能被算进失败率）。接口只改 `cancel_requested` 与 `stage`，
> **不改 status** —— 单一写入者是 worker，避免"接口写 cancelled、worker 又写回 running"。
> 组卷：`POST /question/papers/compose/jobs/{id}/cancel` + 前端「停止」按钮（点完继续轮询到终态）。
> 教案：`POST /lesson/ai/jobs/{id}/cancel`，检查点在开工前与出结果前（实际效果是**不落结果**，
> token 已花掉）；**该端点目前没有前端消费方**（教案 AI 生成页未接线），仅后端可用。
> 结果持久化本已具备（`job.result` 落库），无需改动。

## 验证脚本（可重跑，用于反向验证修复）

| 脚本 | 覆盖 | 运行 |
|---|---|---|
| `tools/verify_p0_fixes.py` | **接口级**：P0-1 导出 / P0-3 异步组卷 / P0-4 Agent 组卷 / P1-1 大题结构 / P1-4 成绩重算 / F-03 班级薄弱点（21 条断言） | `python tools/verify_p0_fixes.py` |
| `tools/verify_pdf_export_safety.py` | P0-1 恶意题干导出 PDF/答题卡不崩、输出合法 PDF | `python tools/verify_pdf_export_safety.py` |
| `tools/probe_pdf_ssrf.py` | P0-1 SSRF 实证：旧写法会连接外部 URL，新实现 0 次连接 | `python tools/probe_pdf_ssrf.py` |
| `tools/verify_compose_async_parse.py` | P0-3 异步路径复用解析；只写描述可推出年级学科；显式选择优先 | `python tools/verify_compose_async_parse.py` |
| `tools/verify_paper_agent_ratio.py` | P0-4 比例/题量归一、默认参数出题、`_ai_fill` 不崩 | `python tools/verify_paper_agent_ratio.py` |

> `tools/verify_p0_fixes.py` 已进 `auto_ship.sh`（每发版必跑，约 17s）；
> 其余四个是「临时库 + 直调函数」的定向验证，不依赖 LLM、不写项目 `data/`，
> 可安全重跑，但不进流水线（避免为逐个用例付建库开销）。

## 维护约定

1. **新发现先加行**，不要新开 `audit-reports/*.md`；报告只用于记录证据截图/复现日志。
2. 修完把「状态」改 `已修` 并补一句「怎么修的」，**不要删行**——删了下次还会重复发现。
3. 每批修复后跑一次 `bash tools/auto_ship.sh --bump patch`，让静态门禁兜住回归。
4. 数量约束：P0 必须归零才能发版；P1 允许存量但**不许新增**。
