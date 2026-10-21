# 教育 AI 平台 · UI 端到端功能验证问题清单

- **被测地址**：http://localhost:5173（前端 Vite）→ http://127.0.0.1:8000/api/v1（后端 uvicorn）
- **版本**：v1.0.40
- **验证方式**：Playwright + Chrome 真实浏览器驱动，覆盖输入框 / 下拉框 / 搜索 / 删除四类交互
- **用例规模**：**142 项**，11 个阶段（phase1~phase11）
- **结果分布**：PASS **137**（96.5%）｜ 非 PASS **5**（P2×1 / P3×2 / ENV×2）
- **产品缺陷**：定位 **20 个**（P0×3、P1×11、P2×2、P3×4），已修复并复测通过 **17 个**，剩 3 个列入排期
- **截图证据**：`tests/ui_e2e/shots/`（185 张，全页截图）
- **原始数据**：`tests/ui_e2e/phase*.json`（逐条含复现步骤、预期、实际、证据）

### 各阶段通过情况

| 阶段 | 覆盖范围 | 用例 | 通过 |
|---|---|---|---|
| phase1 | 注册 / 登录 / 表单校验 | 6 | 5（ENV 1） |
| phase2 | 登录边界（验证码/锁定） | 4 | 4 |
| phase3 | 注册审批 | 5 | 4（P2 1） |
| phase4 | 用户管理 / 角色权限 | 8 | 8 |
| phase5 | 题库管理 | 12 | 11（P3 1） |
| phase6 | 试卷 / 作业考试 | 12 | 12 |
| phase7 | 学生端考试 / 笔记 | 13 | 12（P3 1） |
| phase8 | 定时任务 / 日志审计 / 系统配置 | 18 | 18 |
| phase9 | 批改中心 / 教案 / 学情 / AI 助手 | 23 | **23** |
| phase10 | 学生端 12 个页面全覆盖 | 34 | 33（ENV 1） |
| phase11 | 删除专项 | 7 | 7 |

### 剩余 5 项非 PASS 一览

| 级别 | 阶段 | 模块 | 用例 | 结论 |
|---|---|---|---|---|
| P2 | phase3 | 注册审批 | 搜索框筛选不存在的账号 | **真实缺功能**：审批页无账号搜索框 |
| P3 | phase5 | 题库管理 | 超长题干（5700 字） | **缺约束**：4003 字被接受落库，不 5xx |
| P3 | phase7 | 学生端-笔记 | 超长正文（2 万字） | **缺约束**：21000 字被接受，不 5xx |
| ENV | phase1 | 登录 | 未审批账号登录 | 验证码先拦，未能验证到审批层 |
| ENV | phase10 | 学习路径 | 去练习跳转 | 学生无数据，空态正确无按钮 |

> 严格来说只剩 **1 个 P2 功能缺失 + 2 个 P3 约束缺失**，其余 2 项是测试环境受限，非产品缺陷。

> 证据字段说明：`[console.error]` 控制台报错｜`[HTTP 4xx/5xx]` 网络响应｜`[netfail]` 请求失败｜`[console.warning]` 框架告警

---

## 一、总体结论

系统主流程可用：注册 → 审批 → 登录 → 建题 → 组卷 → 下发 → 作答 → 批改 → 成绩 → 学情分析，**全链路走通**。

本轮共定位 **20 个产品缺陷**（P0×3、P1×11、P2×2、P3×4），**已修复 17 个**，剩 3 个（1 个 P2 + 2 个 P3）列入排期；另修正 **9 处测试脚本自身的判据错误**（脚本缺陷不计入产品缺陷数）。

最值得注意的五个问题：

1. **存储型 XSS（P0）** —— 学习笔记、题干、AI 回复都走 `v-html`，后端原样存储，学生可注入脚本窃取他人 token。
2. **学科 id 跨年级错用（P1）** —— `Subject` 唯一键是 `(grade_id, name)`，「数学」在 9 个年级各有一条；前端下拉用去重后的代表 id，指向最低年级。表现是「筛选后结果为空」和「七年级学生拿到一年级题」，但界面**不报任何错**。
3. **成绩永远发不出去（P1）** —— 可发布状态集合里写了 `'graded'`，这个值在枚举里**根本不存在**，纯客观题判完停在 `auto_graded`，按钮永久灰。
4. **交卷固定卡 16.5 秒（P0）** —— 只要卷面含一道主观题，交卷就固定多等 16.5 秒，**与题目数量完全无关**（5 题 = 16.47s，32 题 = 16.48s）。原因是 AI 调用日志在业务事务持锁期间用另一个连接抢同一把 SQLite 写锁，抢不到就等满 `busy_timeout` 并重试 3 次。前端 30s 超时，32 题卷子直接判失败（详见 2.8）。
5. **写操作审计日志从未落库（P0）** —— 所有 POST/PUT/PATCH/DELETE 的操作日志一直是空的，只有 GET 能存。接口 `/logs/operation` 看着正常返回 200，实际库里没有一条写操作记录（详见 2.8）。

> 第 4、5 条特别值得记：两个都是「接口返回成功、界面看不出异常」的静默失效。第 4 条把日志这个旁路数据写在了主事务的临界区里，第 5 条则是异常被 `except` 吞掉——**吞异常是这类 bug 的共同温床**。

---

## 二、按模块汇总的问题清单

### 2.1 安全（跨模块）

| 编号 | 级别 | 问题 | 影响范围 | 状态 |
|---|---|---|---|---|
| SEC-01 | **P0** | 存储型 XSS：`v-html` 渲染未净化内容 | 学习笔记、题库题干、试卷、练习题、错题本、收藏、AI 对话 —— **10 处渲染点** | 已修复 |
| SEC-02 | P1 | **用户接口回传密码哈希**：`dictify(user)` 直出 ORM 全字段，`pbkdf2_sha256$<salt>$<digest>` 原样下发 | `/system/users`、`POST/PUT /system/users`、`/auth/registrations/audit` —— **4 处** | 已修复 |

**SEC-02 复现步骤**
1. 用 admin 登录
2. `GET /api/v1/system/users?page_size=2`
3. 响应的每个用户对象里都带 `password` 字段，值形如 `pbkdf2_sha256$7361eb83...$f2b5ec7b...`

**预期**：任何对外接口都不应返回密码哈希
**实际（修复前）**：4 处接口全部原样返回

**影响**：哈希不可逆，但拿到后可以离线爆破（尤其弱口令）；而且这是**无业务必要性**的暴露——前端用户管理页一个字段都用不到它。授权范围是所有 `admin` 与 `grade_admin`。

**修复**：在 `system.py` 里统一封装 `user_dict()`（剔除 `password` 后附带 `roles`），4 处调用点全部改用它；并在 `test_system.py` 增加断言「用户列表不回传密码哈希」，防止以后新增接口时再次遗漏。

**复现步骤**
1. 学生登录 → 学习笔记 → 新建笔记
2. 正文填入 `<img src=x onerror="window.__xss=1">` 或 `<script>alert(1)</script>`
3. 保存 → 打开该笔记详情

**预期**：脚本不执行，正文按纯文本/受限富文本展示
**实际（修复前）**：脚本执行，`window.__xss === 1`

**根因**：后端 `notes` 原样落库（仅导出 PDF 时做 `html.escape`），前端 `MyNotes.vue` 直接 `v-html`。项目未引入 DOMPurify。
**修复**：新增 `frontend/src/utils/sanitize.js`，`DOMParser` + 标签/属性双白名单（放行 `A/B/CODE/IMG/TABLE...`，整体丢弃 `SCRIPT/IFRAME/SVG/FORM...`，`href/src` 仅允许 `https?/mailto/tel/相对路径`）。10 处 `v-html` 统一接入。
**复测**：payload 净化后 `script=0 / img[onerror]=0 / a[href^=javascript]=0`，`window.__xss` 未被置位。

---

### 2.2 注册 / 登录 / 审批（phase1~phase3，10 项）

| 编号 | 级别 | 问题 | 影响范围 | 状态 |
|---|---|---|---|---|
| REG-01 | P1 | 前端密码规则（6 位）弱于后端（8 位 + 字母数字） | 注册页、个人中心改密 | **已修复** |
| REG-02 | P1 | 业务 400 被当成运行时错误，弹「页面出错：Request failed with status code 400」+ 顶部常驻红条 | **全站所有未 catch 的接口错误** | **已修复** |
| REG-03 | P2 | 注册审批页无账号搜索框，无法按账号筛选 | 管理员审批页 | **待处理** |

**REG-01 复现**：注册页密码填 `123` → 提交。
- 预期：前端即拦截，提示 8 位 + 字母数字
- 实际（修复前）：前端按「至少 6 位」放行，6-7 位密码提交后才被后端 400 打回

**修复**：新增 `frontend/src/utils/password.js`，`PASSWORD_MIN_LENGTH = 8` + 复杂度校验，注册页与改密页共用一份规则。
**复测**：`3 位密码在前端被拦，提示「密码至少 8 位」，未发起请求` ✅

**REG-02 复现**：用已注册账号再注册一次 → 提交。
- 预期：只提示「该账号已被注册」
- 实际（修复前）：`该账号已被注册 | 页面出错：Request failed with status code 400` + 顶部红条不消失

**根因**：拦截器已 `ElMessage` 提示过，组件 `await` 未 `try/catch`，rejection 冒泡到 `app.config.errorHandler`，被当成崩溃再报一次。
**修复**：`request.js` 给已提示错误打 `__handled` 标记；`main.js` 的 `isBusinessError()` 识别 `__handled / isAxiosError / err.response` 后只记 `console.warn`，不再弹窗插红条。
**复测**：`重复账号被拒绝，提示干净：「该账号已被注册」` ✅；题库删除被引用题目同样只提示后端文案 ✅

**REG-03 复现**：审批页尝试输入 `no_such_user_zzz` 搜索。
- 预期：列表为空 + 空态提示
- 实际：页面**没有账号搜索输入框**，只能翻页查找。40+ 待审批账号时操作成本高。
- 建议：补一个按账号/姓名/手机号的服务端搜索框。

---

### 2.3 学生端 · 学科筛选（phase7 / phase10，11 个页面）

| 编号 | 级别 | 问题 | 影响范围 | 状态 |
|---|---|---|---|---|
| SUB-01 | P1 | 学科下拉 57 条含 7 个「数学」，且去重后的代表 id 指向最低年级 | 错题本、学习报表、笔记、闪卡、智能复习、掌握图谱、学习路径、练习、试卷、AI 出题、题库管理 —— **11 个页面** | 已修复 |
| SUB-02 | P1 | AI 出题用去重代表 id → 知识点下拉装错年级 → 产生脏数据 | AI 出题组卷 | 已修复 |
| SUB-03 | P1 | 随机练习「放宽条件」把 `grade_id` 一起丢掉 → 七年级学生拿到一年级题 | 随机练习 | 已修复 |
| SUB-04 | P1 | 自主组卷的「年级」下拉完全失效（抽题语句里没有它） | 自主组卷 | 已修复 |
| SUB-05 | P1 | 学习报表 `score-trend` 忽略 `subject_id`；`wrong-analysis` 三块统计未复用过滤条件 | 学习报表 | 已修复 |
| SUB-06 | P1 | 知识点管理只选学科时按代表 id 过滤，漏掉其他年级 | 知识点管理 | 已修复 |

**SUB-01 复现**
1. 学生登录 → 错题本 → 打开「学科」下拉
2. 观察：出现 7 个「数学」（1~7 年级各一条），总计 57 项
3. 选中「数学」筛选 → 结果为空

**根因**：`Subject` 唯一约束 `(grade_id, name)`，学科按年级配置。`GET /edu/subjects` 不传 `grade_id` 返回全量；`distinct=true` 返回 12 条代表记录，但**代表 id 永远指向 sort 最小的那条（最低年级）**。

**修复**
- 新增 `frontend/src/utils/subject.js` 统一取数：`fetchSubjects()` 默认带 `distinct` + 当前年级
- `resolveSubjectId()` 用后端返回的 `same_name_ids` / `same_name_grade_ids` 把代表 id 还原成当前年级的精确 id
- 11 处页面全部改为经该工具取数

**SUB-02 复现**（本轮最严重的脏数据来源）
1. 教师 → AI 出题 → 年级选「七年级」、学科选「数学」
2. 知识点下拉里出现「20 以内加减法」（一年级内容）
3. 选中并生成 5 道题 → 题目落库时 `grade_id=7` 但 `knowledge_point_id=1`（一年级知识点）

**修复**：`AgentGenerate.vue` 去掉 `distinct`，按 `grade_id` 过滤学科；`onSubjectChange` 必须带 `grade_id` 查知识点；`question_agent.py` 增加知识点-学科归属校验，不匹配直接报错。**数据修正**：5 道题的 `knowledge_point_id` 1→23，清理错误 `knowledge_mastery` 记录。

**SUB-03 复现**
1. stu731（七年级）→ 随机练习 → 选「语文」
2. 修复前：卷面标着「七年级」，实际抽出 5 道 `grade_id=1` 的题，学生完全不会做
3. 修复后：明确返回「该学科在该年级暂无题目」；选「数学」自动纠正为七年级数学 id，题目 `grade_id` 全为 7 ✅

**SUB-05 复现**：学习报表切学科 → 趋势图纹丝不动；错题分析切学科 → 「错题总数」变 0 但饼图/排行不变（数据自相矛盾）。
**根因**：`score_trend` 没声明 `subject_id`，FastAPI 静默丢弃该 query 参数；`wrong_analysis` 只对 `total` 用了 `base`，三个统计块仍按全量算。
**验证**：`subject_id=999` 时 trend 3→0、wrong-analysis 全为 0 ✅

**SUB-06 复现**：知识点管理 → 只选学科「数学」不选年级 → 只能看到一年级数学知识点。
**修复**：`edu.py` 新增 `subject_name` 参数，按学科名跨年级过滤。验证：`subject_id=6` 返回 0 行 → `subject_name=数学` 返回 31 行 ✅

---

### 2.4 教师端 · 题库 / 试卷 / 作业（phase5~phase6，30 项）

| 编号 | 级别 | 问题 | 影响范围 | 状态 |
|---|---|---|---|---|
| Q-01 | P1 | 业务校验失败的错误呈现（同 REG-02 根因） | 全站 | **已修复** |
| Q-02 | P3 | 题干无长度上限：4003 字被 200 接受并落库 | 题库 | **待处理** |
| Q-03 | P3 | 笔记正文无长度上限：21000 字被接受 | 学生笔记 | **待处理** |

**Q-01 复测**：删除被 11 份试卷引用的题目 → 仅提示「该题目已被 11 份试卷引用，请先从相关试卷中移除」，无「页面出错」、无顶部红条 ✅

**Q-02 / Q-03 说明**：两者都**不触发 5xx**，属于「缺约束」而非「出错」。风险是列表页渲染超长文本时卡顿、导出 PDF 体积失控。
**建议**：题干 `VARCHAR(4000)` 上限 + 前端 `maxlength` 提示；笔记 20000 字上限。

---

### 2.5 批改中心（phase9，6 项）

| 编号 | 级别 | 问题 | 影响范围 | 状态 |
|---|---|---|---|---|
| G-01 | **P1** | 纯客观题判分后状态为 `auto_graded`，但可发布集合写的是 `'graded'`（枚举中不存在）→ **「发布成绩」永久 disabled** | 全体教师，所有纯客观题作业/考试 | **已修复** |
| G-02 | — | 「打回重做」用例判据错误（假设了不存在的 `can_reject` 字段） | 测试脚本 | **已修正** |
| G-03 | — | AI 助手「发送问题」用例固定等 6 秒 → 请求仍在飞行中被误判「无回复」 | 测试脚本 | **已修正** |

**G-03 说明**：截图显示点发送后页面确实进入「AI 思考中（最长约 60 秒）」，消息气泡已渲染；直接用 curl 打同一接口 **3.6 秒返回 200**。失败原因是 `e.calls` 只在响应返回后才记录，固定 sleep 6 秒不够，被误判成「压根没发请求」。已改为最多 45 秒轮询 + 状态区分，复测 **PASS**。
**不是产品缺陷**，但暴露一个体验问题：AI 回复期间前端只有「思考中」动画，没有流式输出 —— 建议后续接流式响应。

**G-01 复现步骤**
1. 教师 → 批改中心 → 打开一份纯客观题答卷
2. 状态显示「待人工确认」，分数已有（自动判分完成）
3. 观察「发布成绩」按钮 —— **灰色不可点**
4. 直接把题改满分 → 保存批改结果 → 按钮**仍是灰的**

**预期**：判分完成即可发布成绩
**实际**：按钮永久 disabled，成绩发不出去，学生永远看不到分数

**根因**：`GradingCenter.vue` 中 `PUBLISHABLE = new Set(['graded', 'fully_graded'])`。查 `backend/app/models/task.py::GradeStatus`，真实取值为 `not_graded / auto_graded / fully_graded / published` —— **`'graded'` 根本不存在**。纯客观题判完是 `auto_graded`，主观题全批完才是 `fully_graded`。

**修复**
- 前端：`PUBLISHABLE` 加入 `auto_graded`（保留 `graded` 兼容历史脏数据）
- 前端：`canPublish` 增加「无可发布的主观题」判断，按 `type ∈ {short,calc,material,composition} && score == null` 判定
- 后端：`publish_score` 增加服务端复核 —— 还有未批主观题时返回 `400 还有 N 道主观题未批改，无法发布成绩`

**复测**
- `auto_graded` + 全部给分 → 发布成功 `{"code":200,"message":"成绩已发布"}`，状态转 `published` ✅
- 构造主观题未评分 → `{"code":400,"message":"还有 1 道主观题未批改，无法发布成绩"}`，状态未变 ✅

---

### 2.6 教案管理（phase9，5 项）

| 编号 | 级别 | 问题 | 影响范围 | 状态 |
|---|---|---|---|---|
| L-01 | — | 「新建教案空表单」用例 15s 超时（`BLOCKED`） | 测试脚本 | **已修正** |

**说明**：`LessonPlanManage.vue` 弹窗 footer 是「关闭」+「保存教案」两个按钮，**没有「确定」**。原用例按 `name="确定"` 定位，必然超时。这是脚本 bug，不是产品缺陷 —— 已在报告中明确标注，避免误记为产品问题。
**修正**：改用 `.el-dialog:visible` 内定位「保存教案」，并以 `has-text('确定'), has-text('保存')` 兜底，找不到时输出实际按钮文案而非直接超时。
**复测**：`PASS 空表单被拦：'请输入标题'` ✅

---

### 2.7 系统配置 / AI 密钥（回归阶段发现）

| 编号 | 级别 | 问题 | 影响范围 | 状态 |
|---|---|---|---|---|
| CFG-01 | **P2** | **API 无法清空已配置的密钥**：`save_ai_config` 用 `data.get(key) or data.get(key.upper())` 取值，空字符串被当成「未传」而 `continue`，接口仍返回 `success:true` 且 `updated` 里带着该 key | AI 配置页「清空 API Key」、任何需要把配置值置空的场景 | **已修复** |
| CFG-02 | P3 | `/health` 与 `/system/config` 的运行态字段只读 `.env`，管理员在「AI 配置」页改完 provider/model/key 后这两处仍显示旧值 | 健康检查、系统配置页 | **已修复** |
| CFG-03 | P3 | `/system/config` 的 `_mask()` 把空串渲染成 `****`，密钥清空后界面仍显示「已配置」 | 系统配置页密钥项 | **已修复** |
| CFG-04 | — | 回归用例把**线上真实密钥覆盖成假值且无法还原**（见下方事故说明） | 测试隔离性 | **已修正** |

**CFG-01 复现**
1. 管理员 → AI 配置 → 填入任意 Key 保存（`PUT /system/ai-config {"llm_api_key":"sk-xxx"}`）
2. 清空输入框再保存（`PUT /system/ai-config {"llm_api_key":""}`）
3. 回读配置 —— **密钥还在**

**预期**：置空即清除，`is_available()` 转为 false，AI 走规则引擎降级
**实际（修复前）**：请求返回 `{"success":true,"data":{"updated":["llm_api_key"]}}`，看着成功了，值却纹丝不动。管理员没有任何办法通过界面清掉一个填错的密钥。

**根因**：空字符串是合法入参（表示「清空」），但 `or` 短路把它当成了「字段未传」。

**修复**：改为按「键是否存在」判断（`if key in data: raw = data[key]`），`None` 才视为未传。

**CFG-04 事故说明（本轮最值得记录的一条）**
`tests/test_system.py` 的脱敏用例会往 `llm_api_key` 写 `sk-verify-ABCDEFGH-0001`，再用 `PUT {"llm_api_key": ""}` 还原。因为 CFG-01 这个 bug，**还原动作一直是空转**，假密钥就永久留在了库里。后果：

- `is_available()` 返回 true → 每次 AI 调用都真的去连第三方 `tokenrhythm.studio`
- 该假 key 必然 `401`，而失败前要先等 **6~7 秒**网络往返
- 于是：`/agent/study-planner` 连打 14 次跨过了两个统计窗口 → 限流用例失败；SSE 返回 `meta/error` 而非 `meta/delta/done`；22 题练习交卷耗时 28s 逼近客户端 30s 超时

**一轮回归里 6 条用例同时失败，根因是同一处**。教训：**测试里「用完还原」的代码必须有断言兜底**（本次已补 `★ 假密钥已清理干净`），否则还原失败永远是静默的。

同时修正了测试设计：读接口只回传掩码，测试拿不到原文，**一旦覆盖真实密钥就永久丢失**。现在的规则是——
- 库里已有密钥 → 只做只读脱敏断言，**绝不写入**
- 库里没有 → 才写假值验证，`finally` 里清空并断言清干净

---

### 2.8 性能 / 审计（回归阶段发现的两个 P0）

| 编号 | 级别 | 问题 | 影响范围 | 状态 |
|---|---|---|---|---|
| PERF-01 | **P0** | **含主观题的卷子交卷固定多等 16.5 秒**，与题目数量无关 | 所有含简答/计算/材料/作文题的作业与考试交卷 | **已修复** |
| AUD-01 | **P0** | **写操作（POST/PUT/PATCH/DELETE）审计日志从未落库**，只有 GET 能存 | 全站操作审计、合规追溯 | **已修复** |
| PERF-02 | P1 | 无效密钥导致主观题逐题串行重试（6 题 = 30 秒+） | AI 降级路径 | **已修复** |

**PERF-01 复现**

1. 学生登录 → 学习中心 → 随机练习，`count=5`（卷面含 1 道简答）
2. 作答后点交卷 → 请求耗时 **16472ms**

对照测量（同一环境、同一账号、无 LLM 密钥）：

| 卷面 | 主观题数 | 交卷耗时 |
|---|---|---|
| 5 题 | 1 | 16472 ms |
| 10 题 | 2 | 16485 ms |
| 20 题 | 5 | 16560 ms |
| 32 题 | 6 | 16478 ms |
| 26 题 | **0** | **7 ms** |

**耗时与题目数量、主观题数量完全无关**——这是「固定超时等待」的典型特征，不是计算量问题。

**定位方法**（可复用）：在端点内打分段计时，通过自定义响应头 `X-Trace` 回传。
`X-Process-Time` 只能切开「端点内 / 端点外」，`X-Trace` 才能切到函数级：

```
get_task=2;assert=2;time_check=2;query_last=2;get_sub=3;
save_answers=16428;finalize=16431;refresh=16432;build_resp=16432
```

100% 卡在 `save_answers`。但同一函数**进程内直调只要 0.02 秒**，说明差异来自运行时状态而非代码逻辑。

**根因**：`save_answers()` 先 `db.flush()` 写入 Answer，此时业务事务已持有 SQLite 的 RESERVED 写锁，要到 `finalize_submission()` 的 `db.commit()` 才释放。而主观题判分恰好发生在两者之间，`log_agent_call()` 用**另一个 Session** 去抢同一把写锁：

- 抢不到 → 等满 `busy_timeout`（5s）→ 抛 `database is locked`
- 上一轮为「日志不丢」加的重试逻辑再重试 3 次 → 又等 3×5s
- **16.5s = 3 次重试 × 5s + 退避 0.6s**

一道简答题就触发一次。日志是旁路数据，却让主流程替它等锁。日志文件里能直接看到佐证：

```
14:02:15.814  审计日志写入失败: Stream consumed
14:02:32.275  Agent 调用日志写入失败: (sqlite3.OperationalError) database is locked   ← 16.46s 后
14:02:48.774  Agent 调用日志写入失败: (sqlite3.OperationalError) database is locked   ← 16.50s 后
```

**修复**：`log_agent_call` 改为 daemon 线程异步落库，主流程立即返回。日志写成功与否都不再影响响应时间。

**验证**：交卷 **16472ms → 40ms**（32 题含 6 道简答 49ms），提升约 400 倍。

**AUD-01 复现**

1. 管理员登录 → 系统管理 → 操作日志
2. 在此之前做过大量写操作（建题、下发、交卷、改配置）
3. **列表里没有任何一条 POST/PUT/DELETE 记录**，只有 GET 的

**根因**：`BaseHTTPMiddleware` 会用 `_CachedRequest` 包装请求，只有**在 `dispatch` 里先读过 body**，它才会把内容缓存下来喂给下游 app。原实现在 `call_next()` 返回**之后**才 `await request.body()`——此时下游端点早已把流消费完毕，必然抛 `RuntimeError: Stream consumed`。而 `_log` 外层有 `except Exception` 兜底，异常被吞掉，只留一行 warning，表现为「接口 200 正常、日志一条没有」。

GET 请求没有 body，不走这个分支，所以一直正常——这也是 bug 藏了很久没被发现的原因。

**修复**：把 body 读取移到 `call_next()` **之前**；并且只对 `application/json` 生效（multipart 文件上传若整段读进内存会撑爆，且审计本就不记录二进制）。

**验证**：同一个 `/logs/operation` 接口，修复前 POST 日志 **0 条**，修复后 **12 条**，且 body 内容正确入库、`password` 字段已脱敏为 `******`。

**这两条的共同教训**：两个 bug 都是「接口返回成功、界面看不出异常」的静默失效。PERF-01 是把旁路数据（日志）写进了主事务的临界区；AUD-01 是吞异常。**凡是有 `except: pass` 兜底的地方，都必须有一个「产出确实存在」的断言**，否则失败永远是静默的。

---

### 2.9 环境受限 / 未能验证（ENV）

| 编号 | 用例 | 原因 | 是否产品缺陷 |
|---|---|---|---|
| E-01 | 未审批账号登录拦截 | 验证码先被拦截（图形码不可编程识别），未能验证到审批拦截这一层 | 否 |
| E-02 | 学习路径「去练习」跳转 | 新注册学生无学习数据，页面正确显示「暂无学习数据，先去练习几道题吧」，无按钮可点 | 否（空态正确） |

> 「打回重做」原为 ENV（队列记录已被前序用例发布），修正判据后已 **PASS**，不再属于受限项。

---

## 三、修复清单（代码变更）

| 文件 | 变更 | 对应问题 |
|---|---|---|
| `frontend/src/utils/sanitize.js` | **新增** 白名单 HTML 净化器 | SEC-01 |
| `frontend/src/utils/subject.js` | **新增** 学科取数 + id 还原 | SUB-01 |
| `frontend/src/utils/password.js` | **新增** 统一密码规则 | REG-01 |
| `frontend/src/api/request.js` | 业务错误打 `__handled` 标记 | REG-02 |
| `frontend/src/main.js` | `isBusinessError()` 识别已处理错误 | REG-02 |
| `frontend/src/views/teacher/GradingCenter.vue` | 可发布状态补 `auto_graded` + 主观题复核 | G-01 |
| `backend/app/api/v1/grading.py` | 发布前服务端复核未批主观题 | G-01 |
| `backend/app/services/grading_service.py` | 放宽条件时保留 `grade_id` | SUB-03 |
| `backend/app/api/v1/report.py` | 补 `subject_id` 声明 + 三块统计复用过滤 | SUB-05 |
| `backend/app/api/v1/edu.py` | 新增 `subject_name` 过滤 | SUB-06 |
| `backend/app/api/v1/learning/review.py` | 学科-年级配对纠正 | SUB-03 |
| `backend/app/api/v1/learning/tools.py` | 组卷年级筛选生效 + 学科纠正 | SUB-04 |
| `backend/app/agents/question_agent.py` | 知识点-学科归属校验 | SUB-02 |
| `frontend/src/views/agent/AgentGenerate.vue` | 去掉 distinct，按年级过滤学科 | SUB-02 |
| **10 个 Vue 文件** | `v-html` 接入净化 | SEC-01 |
| **11 个 Vue 文件** | 学科取数改用 `subject.js` | SUB-01 |
| `backend/app/services/ai_config_service.py` | 空串可清空配置（`or` 短路修复） | CFG-01 |
| `backend/app/api/v1/system.py` | 运行态字段改读 `sys_config`；`_mask` 空值不伪装 | CFG-02 / CFG-03 |
| `backend/app/main.py` | `/health` 的 `llm_enabled` 走 `is_available()` | CFG-02 |
| `backend/app/agents/grading_agent.py` | 判分批量取题，消除 N+1（22 题 22 次查询 → 1 次）；主观题并发批改 | 性能 |
| `backend/app/agents/llm.py` | **`log_agent_call` 改 daemon 线程异步落库** —— 日志不参与主事务锁竞争 | PERF-01 |
| `backend/app/agents/llm.py` | 鉴权失败（401/403/429）立即熔断，不再逐题重试 | PERF-02 |
| `backend/app/middleware/audit.py` | **请求体在 `call_next` 之前读取** —— 修复 `Stream consumed` 导致写操作日志全丢 | AUD-01 |
| `backend/app/api/v1/system.py` | 新增 `user_dict()` 统一剔除密码哈希（4 处调用点） | SEC-02 |
| `backend/app/api/v1/auth.py` | 注册审批响应剔除密码哈希 | SEC-02 |
| `backend/app/core/database.py` | `PRAGMA busy_timeout=5000` + `connect_args timeout` | PERF-01 |
| `tests/test_system.py` | 脱敏用例不覆盖真实密钥 + `finally` 清空并断言 | CFG-04 |

---

## 四、测试脚本资产

| 文件 | 说明 |
|---|---|
| `tests/ui_e2e/harness.py` | 浏览器驱动基座（Playwright + Chrome），含网络/控制台证据采集 |
| `tests/ui_e2e/session.py` | 会话注入（API 取真实 token 写 localStorage，规避验证码） |
| `tests/ui_e2e/phase1~phase11_*.py` | 11 个阶段用例，共 142 项 |
| `tests/ui_e2e/phase*.json` | 逐条结果（步骤/预期/实际/证据/截图路径） |
| `tests/ui_e2e/shots/` | 185 张全页截图 |

**已知测试陷阱**（已在脚本中处理，避免后续误判）
- `Client.get(path, **kw)` 只接受关键字参数，位置传参会被吞成「阶段异常中断」
- `.el-select-dropdown__item` 会抓到**所有已渲染过（含隐藏）**的下拉 → 必须用 `:visible` 限定；否则 6 个学科会被数成 15 项
- 表格第 1 列可能是展开图标，不能直接取 `td:first-child`
- 页面根节点不统一：`/agent/chat` 是 `.chat-page`，其余多为 `.page-container`
- **弹窗按钮文案不可猜**：教案弹窗 footer 是「关闭」+「保存教案」，**没有「确定」** → 按 `name="确定"` 定位必然超时，必须按真实文案定位并输出实际按钮列表
- **`first.get("can_reject", True)` 恒真**：「打回重做」用例假设了一个后端根本不返回的字段 → 判据要落在真实状态（`status not in (published, fully_graded)`）
- **网络记录有延迟**：`e.calls` 只在响应返回后才写入，AI 类用例固定 `sleep 6s` 会误判「没发请求」→ 改轮询到出现该请求或用时上限
- **数据稀疏要区分「正确拒绝」**：变式练习在「该知识点每题仅 1 道」时返回 `400 暂无可用的变式题目` 是**正确行为**，用例应双判据（出卷成功 或 明确提示无同类题），不能按单判据记 FAIL
- **学科 id 必须用「学生自己年级」的**：`distinct=true` 的代表 id 永远指向最低年级；`test_learning.py` 曾硬编码 `subject_id=1`（一年级语文）后给七年级学生用

---

## 五、尚未处理项（建议排期）

| 优先级 | 项 | 建议 |
|---|---|---|
| P2 | 注册审批页无账号搜索框 | 补服务端搜索（账号/姓名/手机号） |
| P3 | 题干、笔记无长度上限 | 后端加 `max_length`，前端加计数器 |
| — | `alembic` 已进 requirements 但未初始化 | 表结构变更无法平滑迁移，建议尽快落地 |
| — | 令牌吊销名单是单进程内存 | 多副本部署需换 Redis |

---

## 六、回归基线

```bash
# 后端（脚本式 E2E，不是 pytest —— `pytest tests/` 会收集到 0 个用例）
python tests/run_all.py                       # 全量，约 35 分钟
python tests/run_all.py learning              # 只跑学习中心阶段
python tests/run_all.py admin teacher student learning learning_hub

# UI 端到端（需系统 Python 3.12 + 本机 Chrome）
cd tests/ui_e2e
python phase1_register.py && python phase2_login.py && ... && python phase11_delete_ops.py
```

**跑测试前的三条硬检查**（本轮踩过，代价是整轮全 FAIL）
1. **确认 8000 端口跑的是当前代码**。本地常见情况是旧进程占端口 → 全部用例 FAIL 且原因看不出来。查真实端口用 `docker port`，别信 `.env` 的 `HOST_PORT`。
2. **确认运行时数据库路径**。`settings.DATABASE_URL` 是相对路径 —— 在项目根启动读 `./data/`，在 `backend/` 启动读 `backend/data/`。两个库数据完全不同，接口行为和直接查库的结果会对不上。
3. **确认 `sys_config` 里没有测试残留**（尤其 `llm_api_key`）。留着一个无效 key 会让每次 AI 调用先等 6~7 秒再失败，限流/SSE/超时类用例会以「莫名其妙」的方式失败。
