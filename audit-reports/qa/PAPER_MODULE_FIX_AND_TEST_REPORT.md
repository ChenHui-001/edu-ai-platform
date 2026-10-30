# 试卷管理模块 · 缺陷修复与完整功能校验报告

- 报告时间：2026-10-30
- 代码基线：`2.2.3`（本次发布 `2.2.4`）
- 范围：试卷管理的**创建 / 编辑 / 删除 / 查询 / 发布（共享·审核）/ 复制 / 组卷**，含正常流程、异常输入与边界值
- 结论：**定位并修复 5 个真实缺陷**；新建 78 项接口级功能校验，全部通过；既有 3 套回归（63 + 57 + 组卷引擎）全部通过，无回归。

---

## 一、TL;DR

| 项 | 结果 |
|---|---|
| 修复缺陷 | 5 项（1 项 P0 功能失效、2 项越权泄露、1 项状态/结构丢失、1 项列表越界）+ 1 项 CI 从未启动 |
| 新增校验脚本 | `tools/verify_paper_module.py`（80 项断言，自起服务自建库，可独立运行） |
| 覆盖维度 | 正常 30 项 / 异常 38 项 / 边界 8 项 / 越权与隔离 4 项 |
| 本次执行结果 | `verify_paper_module` 80/80、`verify_paper_v3` 63/63、`verify_paper_manage` 57/57、`verify_compose_engine` 全通过；CI（ubuntu-latest）上 80 项同样全通过 |
| 静态门禁 | 5 道全绿（硬编码地址 / 恒真断言 / 时间契约 / 模型写外键 / ruff F·E9） |
| 未解决（已登记） | 6 项，均不阻塞发布，见第五节 |

---

## 二、缺陷清单与修复

### D1 ·「仅使用 AI 生成」得到 0 题空卷（P0，功能不可用）

- **现象**：组卷时把「出题来源」选成 *仅使用 AI 生成*，接口返回 200 但 `items` 为空、`total_score=0`，保存时报「试卷没有题目」。
- **根因**：`paper_compose_service.compose()` 对 `ai_only` **刻意不抽题**，只按题型结构返回 `plan.gaps`（缺口清单），注释写着"由上层调 AI 生成"。而 `paper_compose.py` 的 `/compose/preview`、`/compose/ai`、`/compose/save` **没有任何一处**调用 AI 生成 —— 参数一路传对、校验一路通过，最后一步缺席。`bank_first` 在题库不足时同样只记缺口，缺口也从不补齐。
- **修复**（`backend/app/api/v1/paper_compose.py`）：
  - 新增 `_ai_fill_gaps()`：按**大题逐个**调用现成的 `QuestionGeneratorAgent`（`question_type` 取该大题题型、`count` 取该题缺口数），生成的题以 `draft` 入库并回填 id，再按该大题的分值/序号组装进 `plan.items`，刷新 `got`、保留未填满的缺口。
  - 为什么要"逐大题"而不是"按总题量一次性补"：Agent 单次调用只产一种题型，混着补会把单选题塞进"填空题"大题。填充时按 `question_type` 二次校验，题型不符直接丢弃。
  - 填充时校验题目可用性（`public` 或 `owner_id == 当前用户`），避免"预览看得到、保存报无权限"。
  - 缺口字典补上 `sort`（大题序号）：不带它时补题结果全部落到 `section_sort=0`，`_renumber` 只能退化为按题号排序，于是「二、填空题」可能因为题目 id 更小而变成「一、填空题」，大题顺序与命题标准不一致。
  - 降级 `fallback()` 补题型过滤：它原本不按 `question_type` 筛选，`limit(3)` 会把填空题也算进"3 道单选题"的配额，上层过滤后只剩 1~2 道（表现为"要 3 题只给 2 题"）。
  - 接线：`_compose_from_payload()` 在 `source != bank_only` 且存在缺口且调用方未自带 items 时触发补题；若 `total_score` 有指定值，补题后按比例 `_rescale_scores` 到目标总分。
  - `ai_only` 补完仍无题时，从"静默返回空卷"改为明确报错（含补题失败原因），提示改用「题库优先 + AI 补充」或先录题。
  - 补题过程说明（补了几题 / 哪一大题还缺几题 / 失败原因）随 `message` 透传到前端，不再静默。
- **验证**：`「仅使用 AI 生成」能出题`、`AI 补题后题型与大题一致`、`预览返回补题说明`、`仅 AI 生成的试卷可保存`。

### D2 · 组卷会抽到其他教师的私有题（P1，越权泄露 + 保存断裂）

- **现象**：教师 A 组卷预览里出现教师 B 的私有题（题干、答案、解析全部随预览返回）；若照预览保存，`_normalize_items` 报「无权使用题目」，出现"预览 3 题、保存报错"。
- **根因**：抽题 SQL 只过滤 `年级 + 学科 + 题型 + status=published`，**完全不看题库归属**；出题 Agent 的降级 `fallback()` 同样只按学科取 `published`。
- **修复**：
  - `backend/app/services/paper_compose_service.py`：新增 `_bank_visibility_clause(viewer_id, allow_all_banks)`，把「公共库 + 本人私有；管理员不限」下沉到 `_base_stmt()` —— **所有抽题分支（含放宽难度、忽略去重的兜底分支）都经过它**，不存在绕过路径。`compose()` 与 `_pick_for_section()` 逐层透传 `viewer_id / allow_all_banks`。
  - `backend/app/agents/question_agent.py`：`fallback()` 复用题库时按同一口径收窄（原来"从公共题库匹配"只是提示词里的一句话，实现上没做）。
  - `backend/app/agents/base.py`：`run()` 调用 `fallback()` 时补传 `user_id`——它不是 `execute` 的普通 kwarg，此前降级实现拿不到"当前用户"，无法做归属过滤。
  - 调用方 `paper_compose._compose_from_payload` 传入 `viewer_id=user.id, allow_all_banks=_is_sys_admin(user)`。
  - 不传 `viewer_id` 时默认只抽公共题（保守优先，宁可少抽不越权）。
- **验证**：`抽题不含他人私有题（越权抽题已修）`（测试里故意把他人私有题建成 id 最小的一张，旧实现必抽到它）。

### D3 · 复制试卷丢失状态与大题结构（P1）

- **现象**：复制一份**草稿**，副本变成"已发布"；复制标准卷，副本的大题分组与顺序被打平。
- **根因**：`_copy_paper_row()` 只搬 6 个字段。`Paper.status` 有默认值 `published`，不显式传就等于"复制即发布"；`PaperItem.section_code / section_sort / score_override` 没搬，预览只能退化成按题型猜分组。
- **修复**（`backend/app/api/v1/question.py`）：副本一律 `status=draft + share_scope=private + is_shared=False`（副本是未审核的派生物，要公开仍须走审核流，避免"复制公共卷=绕过审核"）；同时搬运 `section_code/section_sort/score_override` 与 `description/exam_type/stage/textbook_version/standard_id/generation_params/type_report`，`current_version=1`。
- **验证**：`副本状态为草稿且私有（不继承发布态）`、`副本题量与源卷一致`、`副本预览可正常按大题归组（不丢题）`。

### D4 · 试卷库「共享给我」跨年级/跨校泄露（P1，列表与详情判定不一致）

- **现象**：九年级教师能在「共享给我」里看到七年级某教师设为"同年级共享"的卷子（含标准答案），点进详情却被 403。
- **根因**：`library/list` 的 `shared` 分支自己写了一套条件 `share_scope in (grade, school)`，只看"是不是范围共享"，**没有按年级/学校逐级校验**，与全仓唯一的 `_paper_visibility_clause()` 漂移 —— 正是该函数注释里明令禁止的"列表看得到、详情打不开"。
- **修复**（`backend/app/api/v1/paper_compose.py`）：`shared` 改为「排除自己创建的」+ 复用 `_paper_visibility_clause()`；`favorite` 也补同一判定（收藏后共享范围可能被撤回，否则收藏夹会留下打不开的卷）。
- **验证**：`丙的「共享给我」不含跨年级卷（列表/详情一致）`、`同年级教师乙可读`、`跨年级教师丙不可读（403）`。

### D5 · 仓库自带的两套试卷回归脚本长期跑不起来（P2，测试基建）

- **现象**：`tools/verify_paper_v3.py`、`tools/verify_paper_manage.py` 一运行就在登录处 `FATAL 无法登录`。
- **根因**：脚本未设置 `CAPTCHA_ENFORCED=false` 与 `MUST_CHANGE_PASSWORD_ENFORCED=false`。S7 起登录强制图形验证码、出厂管理员强制改密，脚本既取不到验证码也不走改密，**在第一步就死**，看起来像"脚本过期没人维护"。
- **修复**：两个脚本的启动 env 显式注入这两个开关（仅测试进程内生效，不影响生产默认值）。
- **验证**：修复后 `verify_paper_v3` 63/63、`verify_paper_manage` 57/57 全部通过。

### D6 · 功能回归 CI 从未真正启动过（P1，红灯被当噪音）

- **现象**：`.github/workflows/functional-test.yml` 每次 push 都显示失败，但点进去**没有任何 job**，只有一句"workflow 配置有误"。此前连续 3 次推送（2.2.3 起）都是这个状态，被当成"测试本来就红"忽略。
- **根因**：workflow 级 `env` 里写了 `DATABASE_URL: sqlite:///${{ runner.temp }}/...`。**`runner.*` 上下文在 workflow 级 env 不可用**，GitHub 在解析阶段就返回 422，于是只留下一个 0 job 的 failure 记录。另外 `functional_runner` 改密用了 `POST /auth/password`，而该接口是 `PUT` → 405，强制改密闭环失效后所有业务接口 403，会进一步被误读成权限缺陷。
- **修复**：`DATABASE_URL` 改为绝对路径 `/tmp/func_regression.db`；执行器新增 `_put()` 并用于改密；工作流新增一步执行 `tools/verify_paper_module.py`（80 项），让这个 job 真正覆盖业务语义而不只是"路由存在"。
- **验证**：先在临时分支 `ci/selftest` 上用 `workflow_dispatch` 自检（dispatch 接口 422 → 204 即证明解析通过），两个 job 全部 success，其中「试卷模块完整功能校验」在 ubuntu-latest 上同样全部通过；确认后再推 master。

---

## 三、测试范围与覆盖矩阵

新增 `tools/verify_paper_module.py`：自动分配端口、建临时 SQLite、起 uvicorn（`LLM_ENABLED=false`、`CAPTCHA_ENFORCED=false`、`SEED_DEMO_DATA=false`、固定 `SECRET_KEY`），播完种子数据后跑完全部用例并清理临时目录。**不依赖任何已在运行的服务**，本地与 CI 结果一致。

### A. 创建（20 项）

| 类型 | 用例 |
|---|---|
| 正常 | 创建成功；总分由题分求和（客户端伪造 `total_score=999` 被忽略仍为 30）；详情 3 题且 `creator_name/subject_name/grade_name` 齐全；`source` 固定 `manual` |
| 异常 | 空名称；名称 129 字符；空题目列表；重复 `question_id`；不存在的题目；跨年级题目；单题分值 1001；全 0 分（永远发不出去）；时长 0；时长 301；不存在的年级；年级与学科错配（七年级 + 九年级数学）；学生令牌创建（403） |
| 边界 | 名称 128 字符通过；时长 1 通过 |

### B. 编辑（7 项）
改名生效；换题后题量与总分同步；返回 `dropped_answers` 作答作废计数；只改年级学科但卷内题目不一致被拒；改名为空被拒；非创建者 403；不存在 404。

### C. 查询（7 项）
关键词命中；年级+学科筛选；分页 `page_size` 生效；统计接口自洽（`total_items ≥ total`）；详情 404；他人私有卷不出现在列表；直接越权读 403。

### D. 发布 / 共享 / 审核（19 项）
直设 `public` 被拒（必须走审核）；非法 scope；设为年级共享；同年级可读；跨年级不可读；共享库不越界；提交审核 → `pending`；重复提交被拒；教师审核 403；管理员通过 → `published + public`；跨年级此后可读；公共库列表可见；已进公共库不可再提交；驳回未填意见被拒；驳回记录意见；收藏 / 收藏夹可见 / 取消收藏。

### E. 复制（5 项）
公共卷可被他人复制；副本题量一致；副本 `draft + private`；副本预览分组不丢题；复制 404。

### F. 删除（7 项）
非创建者 403；被任务引用的卷拒绝删除（并提示引用数）；删除无引用副本成功 + 后续 404；批量删除含非本人卷整体 403；批量删除中被引用卷进 `skipped` 而非静默删除；非法 action 400。

### G. 组卷（11 项）
题库优先抽到 3 题；不抽他人私有题；保存落库；**仅 AI 生成能出 3 题**；AI 补题题型与大题一致；补题说明透传；仅 AI 生成可保存；非法来源 400；**多题型 AI 补题后大题顺序与请求一致**；**大题序号按结构生成（一、二、而非全是一、）**；跨年级知识点 400；保存后可按大题预览。

> 顺序相关的两条断言用"填空题 id 小于单选题"的数据布局来构造：缺口若丢失 `sort`，题号排序必然把填空题顶到前面，断言立即失败——不依赖运气。

---

## 四、执行结果

```
tools/verify_paper_module.py    全部通过：80 项
tools/verify_paper_v3.py        通过 63 项，失败 0 项
tools/verify_paper_manage.py    全部通过：57 项（试卷管理缺陷回归）
tools/verify_compose_engine.py  全部通过（含 ai_only/bank_only 来源策略、分值缩放、跨年级隔离）
静态门禁                         5/5 PASS（含 ruff --select F,E9 无告警）
GitHub Actions「功能回归测试」    validate-cases + run-suite 两个 job 全绿
                                 （run-suite 内 20 项接口冒烟 + 80 项试卷模块校验，Linux 环境）
GitHub Actions「CI」             后端检查 / 前端构建 全绿
```

---

## 五、发现但未解决的问题

| # | 问题 | 影响 | 为什么不本次修 |
|---|---|---|---|
| 1 | 删除试卷时**不递减** `Question.usage_count`（换题路径已对称递减） | 长期运行后"少用优先"排序被污染，同批题更易反复出现 | 需同时改单删/批量删/历史数据修复三处，且要配套一次性订正脚本；影响是排序偏好而非功能正确性，单独排期更稳 |
| 2 | `_normalize_paper_items` 允许把**公共题库 `draft`（待审核）题**手工加进试卷 | 理论上可引用他人待审题（需已知 id）；列表接口不可见、组卷引擎只抽 `published`，实操无法触达 | 属纵深防御缺口，收紧会波及"教师编辑自己草稿题"的合法场景，需要先定策略（是否允许本人 draft 入卷） |
| 3 | 无"单题详情"端点，题项编辑需整卷拉取 | 大题量卷编辑时多传一些数据 | 契约层面设计如此，改接口影响面大于收益 |
| 4 | AI 补题后按目标总分缩放，可能产生 `6.67` 这类非整数分 | 前端按两位小数展示，阅卷合计无误差 | 属可接受的产品口径，改成整数分配会与命题标准的 `score_per` 冲突 |
| 5 | 42 个学科仍无知识点数据 | AI 出题挂不上知识点，这些学科的掌握度图谱/复习计划失效 | **数据运营问题**，非代码缺陷；需按学科补齐知识点 |
| 6 | 前端组卷向导在 AI 模式下仍显示"出题来源"下拉 | 用户可能选 `ai_only` 后因题库无同题型题而拿不满题量 | 后端已能正确处理三种来源并在 `message` 里说明缺口；前端交互调整属另一条产品线，本次只修后端语义 |

---

## 六、复现方式

```bash
# 试卷模块完整功能校验（自起服务、自建库，无需外部依赖）
python tools/verify_paper_module.py

# 既有回归
python tools/verify_paper_v3.py
python tools/verify_paper_manage.py
python tools/verify_compose_engine.py
```
