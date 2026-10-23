# 修复记录（2026-10-23）

> 第二轮：在 P0/P1/P2 主体修复（2026-10-22，HEAD `25c18d4`）基础上继续处理遗留优化，
> 并按部署/启动行为变化修复本地一键脚本。每项独立提交，回归结果记录在对应小节。

---

## 本地一键启动脚本适配

### S-1 Docker 一键启动（start.bat / start.ps1 / stop.bat / start.sh）

- **状态**：✅ 已修复
- **背景变化**：`SECRET_KEY` 改为 fail-closed（弱/空密钥在 `DEBUG=false` 时拒绝启动），
  compose 使用 `${SECRET_KEY:?}` 强制注入；容器改为 uvicorn 降权 + `/app/BUILD_INFO` 记录构建 commit。
  旧脚本只识别旧占位符 `CHANGE_ME_...`，而新 `.env.example` 的 `SECRET_KEY=` 为空，
  会导致首次启动 compose 直接报错；`docker compose down/logs/status` 也会因变量插值失败。
- **改动**：
  - `start.ps1`：新增 `Ensure-EnvBase`（空/占位/过短/单字符重复密钥重新生成；旧 `.env` 补
    `DEBUG`、`SEED_DEMO_DATA`）；所有 compose 子命令（start/stop/logs/status/restart/rebuild）
    执行前先补 `.env`；读取镜像 `/app/BUILD_INFO` 的 commit 与当前 `git HEAD` 比对，不一致自动重建；
    构建时注入 `GIT_COMMIT`/`BUILD_TIME`；修复 `restart` 浏览器使用错误端口；成功提示按
    `SEED_DEMO_DATA` 显示/隐藏演示账号，并更新“首次登录强制改密”的错误文案。
  - `start.sh`：同样修复空密钥不生成（并在 `set -euo pipefail` 下 `grep` 缺行静默退出）、
    为所有 compose 子命令补 `ensure_env`、支持 `./start.sh 8081`、导出构建指纹、更新输出文案。
  - `docker-compose.yml`：build.args 增加 `GIT_COMMIT`/`BUILD_TIME`。
  - `start.bat`：转发位置参数（`start.bat 8081` 生效）；`stop.bat`：补充 `.env` 失败提示；
    `dev.bat`：更新说明。
  - `README.md` / `docs/QUICKSTART.md`：补充新脚本行为与 Docker `docker run` 的
    `SECRET_KEY`/`DEBUG`/`SEED_DEMO_DATA` 示例。
- **验证**（Windows PowerShell 实机）：
  - 用空的 `SECRET_KEY=` 与旧 `.env` 模拟：执行 `start.ps1 status` 自动生成 64 位密钥、补齐
    `DEBUG`/`SEED_DEMO_DATA`，`docker compose config --quiet` 退出码 0。
  - `start.ps1 help`、`dev.ps1` 语法解析通过（Windows PowerShell 5.1）。
  - 脚本编码符合 `.gitattributes`：`.ps1` 为 UTF-8 BOM + CRLF，`.bat` 为纯 ASCII + CRLF。
  - `start.sh` 本机无可用 bash/WSL，未做实机语法执行（仅静态检查）。

### S-2 本地开发启动（dev.bat / dev.ps1）

- **状态**：✅ 已修复
- **背景变化**：后端配置读取 `backend/.env`；`SECRET_KEY` 为空且 `DEBUG=true` 时每次进程重启
  生成临时密钥，`uvicorn --reload` 改代码会导致所有登录令牌失效。
- **改动**：`dev.ps1` 启动前调用 `Initialize-BackendEnv`：首次生成 `backend/.env`
  （64 位随机 `SECRET_KEY`、`DEBUG=true`、`SEED_DEMO_DATA=true`），已有弱/空密钥时自动补全。
- **验证**：抽取函数实机执行生成 `backend/.env`，密钥长度 64；文件被 `.gitignore` 忽略。

---

## 遗留 P2 优化

### P2-10 报表/试卷列表/任务提交列表 N+1 查询

- **状态**：✅ 已修复
- **问题**：`report.score-trend`、`knowledge-radar`、`student-detail` 在循环内逐条 `db.get(Task/KnowledgePoint)`；`question.papers` 逐卷查题量与创建者/学科/年级；`task.submissions` 逐条/逐班级查用户。
- **改动**：
  - `report.py`：三处改为一次 `IN` 批量预取建 map；`student-detail` 的 score_trend/summary 改用 map（旧实现每条提交每个字段各查一次 Task）。
  - `question.py`：试卷列表 `noload(Paper.items)` + 按 `paper_id` 分组聚合题量/题分；创建者/学科/年级批量预取；题目导出把逐题知识点查询改为一次批量（保留 5000 行上限）。
  - `task.py`：`task_submissions` 本页学生一次 IN、班级下发名单一次 IN、待交前 50 人姓名一次批量取。
- **验证**：`py_compile` 通过；队友用内存 SQLite 对新旧返回逐字段比对一致，并实测 SQL 次数：
  `student_detail` 236→14（与提交数无关）、`list_papers` page_size=10 48→9、`task_submissions` 10 行 70→14；空结果边界一致。全量 E2E 待最终回归。

### P2-11 仓库生成物入库治理

- **状态**：✅ 已修复
- **改动**：移除已入库的 `ui_shots/` 页面截图（40 个文件，约 2.68MB）、`.playwright-cli/` 页面快照、根目录 `login.yaml` 页面快照；`.gitignore` 增加对应规则。
- **验证**：`git status` 干净；E2E 用例定义 JSON（`tests/ui_e2e/phase*.json`）保留不动。

### P2-12 前端 Element Plus 全量引入与工程化缺口

- **状态**：✅ 已修复
- **问题**：Element Plus 全量 `app.use` + 全量 CSS + 全局图标注册，element 分包 1.09MB；无 ESLint/Vitest；`echarts-for-react`、`dayjs` 未使用。
- **改动**：
  - 引入 `unplugin-vue-components` + `unplugin-auto-import`，删除 `main.js` 的 ElementPlus 全量注册/全量 CSS/全局图标循环；`App.vue` 用 `el-config-provider` 保留中文语言包；函数式 `ElMessage/ElMessageBox` 样式显式引入。
  - 图标按需：6 个页面补齐缺失图标 import；`MainLayout` 用 40 项图标映射覆盖路由/菜单动态图标。
  - 关键坑：Element Plus 不能放进 `manualChunks`（会退化为全量），改为只固定 vendor/charts/zrender，交给 Vite 按路由拆分；`chunkSizeWarningLimit` 降为 600。
  - 移除未使用依赖 `echarts-for-react`、`dayjs`；新增 `eslint.config.js`、`vitest.config.js`、`src/utils/__tests__/{sanitize,date}.test.js`，`package.json` 增加 `lint`/`test`。
  - 顺带修复 `SmartReview` 使用不存在的 `<el-list>`（按需后会导致构建失败）、`Practice` 未定义变量、`StudentAnalysis` 重复 tooltip 键。
- **验证**：`npm run build` / `npm run lint` / `npm run test` / `npm ci --dry-run` 全部退出码 0（14 个单测通过）。构建体积：dist 约 2.90MB→2.51MB（-13.3%），全站 JS 2.53MB→2.17MB，最大 JS chunk 1.09MB→482KB（charts），入口 CSS 364KB→51KB，无 >600KB 告警。
- **风险**：未做真实浏览器逐页回归；图标 barrel 仍约 69KB；Element Plus 实解析版本 2.14.7（未变更，与修复前一致）。

### P2-13 AI 出题页「后台生成」分支引用未定义变量

- **状态**：✅ 已修复
- **问题**：`AgentGenerate.vue` 异步分支使用不存在的 `mode`/`pForm`，勾选「后台生成」必抛 ReferenceError；且所有 Agent 都显示后台开关，后端仅支持出题/组卷。
- **改动**：改用 `active`/`paperReq` 构造参数；`asyncSupported` 计算属性控制开关仅对出题/组卷可用；不支持时提示并回退同步；修复结果赋值变量遮蔽。
- **验证**：`npm run build` / `npm run lint` / `npm run test` 均通过。

### P2-14 Docker 镜像构建与运行验证（容器降权/构建指纹）

- **状态**：✅ 已验证
- **验证**（Docker Desktop 29.2.1）：
  - `docker compose build` 退出码 0（含 `npm ci`、非 root 用户创建、Chroma 缓存迁移）。
  - 以 `-e SECRET_KEY=<随机>`、`-e DEBUG=false`、`-e SEED_DEMO_DATA=true` + 临时数据卷启动测试容器：
    `/api/v1/health` 返回 `healthy` / version `1.0.42`，`admin/Admin@123456` 登录成功；
    `/app/data` 属主为 `app`（uid/gid 10001），非 root 运行生效；
    `/app/BUILD_INFO` 记录的 commit 与构建时 `git HEAD` 一致。
  - 测试容器与临时目录已清理。
- **说明**：`start.ps1` 会根据镜像 `BUILD_INFO` 与当前 `HEAD` 自动重建；因此每次代码提交后首次 `start.bat` 会重新构建（Docker 层缓存可显著缩短时间）。

---

## 第四轮：收尾四个遗留项 + 全量回归 + 镜像发布

### P2-15 `student_comparison` 全站下发记录查询

- **状态**：✅ 已修复
- **问题**：`/report/teacher/student-comparison` 为计算完成率，把全站所有已发布非练习的 `TaskAssignment` 一次拉入内存再按学生归并；学校规模大时内存随全校数据线性增长（非 N+1）。
- **改动**：`report.py` 查询增加 `or_(student_id in 本班学生, class_id == 本班)` 过滤；结果与内存归并完全等价（完成率只关心本班学生）。
- **验证**：`py_compile`；全量 E2E 851 项 / 通过 837 / 失败 0。

### P2-16 生产依赖漏洞（npm audit）

- **状态**：✅ 已修复
- **问题**：`markdown-it@14.3.2`（high）与 `echarts@5.6.0`（moderate）命中 npm audit 公告。
- **改动**：升级 `markdown-it@^15.0.3`、`echarts@^6.1.0`（按需导入 API 兼容）；lock 同步。
- **验证**：`npm audit` → **0 vulnerabilities**；`npm run build` / `lint` / `test` 全部通过（ECharts 6 构建正常，charts 分包约 506KB）。

### P2-17 @element-plus/icons-vue barrel 图标体积

- **状态**：✅ 已确认并加回归保护
- **结论**：该包（2.3.2）只有一个 `dist/index.js` barrel，没有可按图标深导入的文件；但 Vite/Rollup 的 tree-shaking 已验证生效——产物中未使用的图标（Watermelon/Football/Basketball/IceCream/Mug 等）均不存在，仅打包实际使用的图标（约 69KB）。
- **改动**：新增 `frontend/scripts/check-bundle.mjs`：构建后断言未使用图标不出现、单个 JS chunk ≤650KB；`package.json` 增加 `check:bundle`。若未来有人改回全量导入/全局注册，构建检查会失败。
- **验证**：`npm run check:bundle` 通过（113 个 JS chunk，最大 charts ~506KB）。

### P2-18 真实浏览器逐页 E2E

- **状态**：✅ 已补上并执行
- **改动**：新增 `tests/ui_e2e/browser_smoke.py`（Python Playwright，使用本机 Chrome/Edge，无需下载浏览器）：通过 `/auth/login` API 注入 token/权限快照，三端分别遍历菜单路由，检查未被踢回 `/login`/`/403`、`#app` 文本非空、无 pageerror/console error，失败截图。
- **验证**（对最终 Docker 镜像真实浏览器执行）：
  - admin 18 页、teacher 12 页、student 16 页，共 **46 页全部 PASS**，耗时 60.1s；
  - 覆盖 Element Plus 按需组件、ECharts 6 图表页、markdown-it 15 渲染页。

### P2-19 镜像构建与推送 Docker Hub

- **状态**：✅ 已发布
- **构建**：`docker build --target unified`，镜像构建 commit=`1f0c2a7`（最终代码提交；此后仅文档提交），镜像内 `/app/BUILD_INFO` 已核对。
- **验证**：临时容器 health=`healthy`、admin 登录成功、`/app/data` 属主 `app`(10001)；浏览器逐页冒烟通过。
- **推送**：`nanpo/edu-ai-platform:1.0.42` 与 `:latest` 已推送 Docker Hub，manifest-list digest 均为 `sha256:0e3f853aa06da148993e386f1d2cc72afdf9e84120220fee6115f0323ec1d617`（`docker buildx imagetools inspect` 已核对）。

---

## 收尾状态

- 上一轮列出的 4 个遗留项（student_comparison 内存、图标 barrel、真实浏览器 E2E、npm audit）已全部处理；第 5 项「镜像未发布」已随本轮推送完成。
- 全量回归：后端 E2E 851/837/0/14；前端 build/lint/test/bundle 检查全绿；真实浏览器 46 页全绿；npm audit 0。
- 仍可选的长期事项（非缺陷）：前端未覆盖所有交互路径（仅逐页渲染冒烟）；图标总量受实际使用量决定；CI 可进一步接入浏览器冒烟与 `check:bundle`。

### P2-20 侧边栏无意义的「其他」分组

- **状态**：✅ 已删除
- **问题**：`MainLayout.vue` 的分组兜底逻辑会把未被分组覆盖、但有 `meta.title` 的路由收进「其他」。实际命中的只有 `/403`（无权访问）与 `/:pathMatch`（页面不存在）两个 public 页面；所有业务路由均已归入教学资源/题库试卷/教学管理/学情分析/学习中心/AI 智能/系统管理，因此「其他 → 无权访问/页面不存在」对用户没有意义。
- **改动**：
  - `allRoutes` 过滤增加 `!meta.public`，403/404 兜底页不再参与菜单构建；
  - 删除「其他」兜底分组渲染；开发态若仍有未归组授权路由，输出 `console.warn` 提示补 `menuGroups` 前缀（避免新增页面静默消失）；
  - 移除不再使用的 `Menu` 图标引用。
- **验证**（Vite dev + 真实 Chrome）：
  - admin 菜单：教学资源/题库试卷/教学管理/学情分析/AI 智能/系统管理；
  - teacher：教学资源/题库试卷/教学管理/学情分析/AI 智能；
  - student：学习中心/AI 智能；
  - 三端均无「其他/无权访问/页面不存在」；`npm run build`/`lint`/`test` 通过。
- **说明**：本地 `start.bat` 会因运行时代码 commit 与镜像 BUILD_INFO 不一致自动重建；Docker Hub `1.0.43` 已包含本修复。
- **后续规则**：见 `docs/DELIVERY_RULES.md` —— 每次运行时代码提交后必须同步 Docker Hub（版本标签 + latest + sha-<short>）。

### 1.0.43 发布与「每次提交同步 Docker Hub」规则

- **状态**：✅ 已发布并落规则
- **版本**：`VERSION` 1.0.42 → 1.0.43（菜单修复后运行时代码已变化，禁止覆盖已发布的 1.0.42）。
- **启动脚本优化**：`start.ps1` 的镜像过期判断改为比对「运行时代码最后一次提交」（`git log -1 -- backend frontend Dockerfile deploy docker-compose.yml VERSION`），纯文档提交不再触发本地重建。
- **规则文档**：新增 `docs/DELIVERY_RULES.md`：
  - 每次运行时代码提交必须构建并推送 Docker Hub；
  - 标签策略：`<VERSION>` + `latest` + `sha-<short7>`，版本标签不可覆盖；
  - 推送前必须跑后端 E2E、前端 build/lint/test/bundle、容器 health/login，涉及页面再跑浏览器冒烟；
  - 发布后更新 RELEASE_CONSISTENCY/FIX_RECORD 并核对 digest。
- **构建与验证**：镜像基于 commit `f9f256e`；容器 health=`healthy`、version=`1.0.43`、admin 登录成功、46 页浏览器冒烟全部通过。
- **Docker Hub**：`nanpo/edu-ai-platform:1.0.43`、`:latest`、`:sha-f9f256e` 已推送，manifest-list digest `sha256:e90ffede3847e9ed247bbc2278cc6c2aaa8ab63a0b2037fbee36bf5fc7bc429c`。

---

### 1.1.0 知识点管理 V2（阶段 1+2）

- **状态**：✅ 已实现（RAG/AI 为下一阶段）
- **数据模型**：`KnowledgePoint` 新增 `textbook_version/status/source/owner_id`；`level` 默认 1；增加 `(grade_id,subject_id,parent_id)` 索引与 `(grade_id,subject_id,code)` 唯一约束（NULL 不冲突）。
- **迁移**：`run_knowledge_v2_migration` 按用户确认**一次性清空旧平铺知识点**、建索引并写版本标记（旧库首次启动执行一次；新库空表不受影响）。`init_knowledge_points` 改为播种「学科 → 单元(level1) → 知识点(level2)」树，共 21 单元 + 72 知识点。
- **后端 API**（新 `backend/app/api/v1/knowledge.py`，14 个路由）：
  - 读：`tree`（嵌套 children + 题目数）、兼容旧 `GET /knowledge` / `list`（平铺）、详情（breadcrumb）、`stats`、`mastery-overview` 原路径保留；
  - 写：创建/编辑/删除（同级重名、跨年级 parent、环检测、子节点/题目/掌握度/复习计划引用守卫、level/path 服务端维护）；`batch`（publish/archive/update/delete/move，越权整体 403）；`import`（xlsx/csv，dry-run、按行容错、自动补建中间层）、`template`、`export`；`reindex` 保留原逻辑。
  - 权限：sys_admin 全量；grade_admin 本年级；teacher 仅 active `TeachingAssignment` 的 (grade_id,subject_id)；student 只读本年级 published。
- **前端**：`KnowledgeManage.vue` 重写为「树视图（左树+右详情/编辑）/ 列表视图（多选 + 批量发布/归档/移动/删除）/ 统计卡 / 筛选（年级/学科/学期/状态/关键词）/ 导入（模板→dry-run→确认）/ 导出」；`api/index.js` 新增 `knowledgeApi`。
- **验证**：
  - 后端全量 E2E：851 项 / 通过 837 / 失败 0 / 环境跳过 14（含旧知识点/权限/引用删除用例）；
  - 动态 API：树 21 根/93 节点、学生仅本年级（跨年级 403）、教师任教学科可写/跨学科 403、同级重名 400、批量/导入 dry_run/模板导出通过；
  - 前端：build/lint/test/check:bundle 全部通过；真实 Chrome 打开新页面：94 个树节点、统计卡、树详情、列表多选与批量栏、导入弹窗均正常，无 console error。
- **数据说明**：旧知识点数据按用户确认不保留；启动时一次性清空并重新播种，题目知识点引用会被置空（需要重新挂载/AI 自动挂载）。
- **镜像**：1.1.0 已构建/推送：`nanpo/edu-ai-platform:1.1.0` / `:latest` / `:sha-591c2ad`，manifest-list digest `sha256:b2c8dfcdde0aff51f6f83cd0be201acc01a9e375d5ac1dbd1f9f875553909ca7`（基于 commit `591c2ad`）；容器 health=`healthy`、version=`1.1.0`、46 页浏览器冒烟全通过。
- **下一步**：RAG 生命周期/语义检索 + 知识点 AI 生成/补全（1.2.0），契约见 `docs/KNOWLEDGE_V2_RAG_AI.md`。

### 1.2.0 RAG 生命周期与知识点 AI

- **状态**：✅ 已实现（镜像构建/真库校验后发布）
- **RAG 生命周期**（`agents/rag.py` + 调用点）：
  - 新增 `delete_knowledge_index/delete_question_index/delete_note_index`；知识点单删/批量删/发布/归档/更新/移动，题目删除，笔记删除均同步索引；
  - `index_knowledge/index_question` 只索引 published；metadata 统一补 `knowledge_point_id/path/grade_id/subject_id/term/status/level/textbook_version`；
  - `RAG_SCORE_THRESHOLD` 在向量、SQL、search 三处生效；SQL 降级也只返回 published+active；
  - reindex 追加 `db_total/index_count/coverage_percent/chroma_available/purged`，并清理已删除/下架知识点的残留向量。
- **接口**：`GET /edu/knowledge/search`（语义检索，学生仅本年级 published、跨年级 403）、`GET /edu/knowledge/rag-status`（admin/teacher）；`POST /edu/knowledge/ai/generate`、`/ai/enrich`（scope 校验、限流、ids≤50；无 LLM 或 LLM 失败规则降级 `is_fallback=true`，只预览不落库）。
- **前端**：AI 生成弹窗（预览→逐条创建）、AI 补全（详情/批量，预览→逐条 PUT）、语义搜索（结果定位树节点）、RAG 状态标签（覆盖率/索引数，重建后刷新）。
- **验证**：后端 E2E 851/837/0/14；无 Chroma 环境 fallback 搜索/AI/状态通过；前端 build/lint/test/bundle 通过；真实 Chroma 在 1.2.0 容器内验证 reindex→搜索→删除索引→覆盖率（97→98→97，覆盖率 100%）。
- **镜像**：`nanpo/edu-ai-platform:1.2.0` / `:latest` / `:sha-adac1cf` 已推送，manifest-list digest `sha256:09e77c17ddef055cf06419131c4219663a1a2e8e53e5cc7c492e3f523695ac6b`（基于 commit `adac1cf`）；容器 health=`healthy`、version=`1.2.0`、46 页浏览器冒烟通过，管理页 AI/语义搜索/索引入口正常。

### 1.3.0 知识点资料附件（学生可预览/下载）

- **状态**：✅ 已实现
- **需求确认**：学生允许下载附件。
- **后端**：`sys_attachment` 新增 `visible_to_student`（迁移默认 1）；复用附件体系，`category=knowledge` / `biz_type=knowledge_point`；新增知识点附件列表/上传/可见性更新/删除接口；扩展 `_assert_attachment_visible`：学生仅本年级 published + 学生可见，跨年级/隐藏附件 403；教师按知识点读权限；上传/删除复用知识点写 scope。
- **安全**：沿用类型/50MB 限制、随机存储名、鉴权 blob 预览/下载、不暴露物理路径；修复中文文件名预览 Header 编码导致的 500。
- **前端**：知识点详情新增「资料附件」表格（上传/预览/下载/学生可见开关/删除）；学生端新增「学习中心 → 知识资料」页面（本年级知识点树 + 附件预览/下载）；新增 `student:knowledge` 权限。
- **验证**：管理员上传 PDF → 学生列表/预览(200, application/pdf)/下载(200)；教师跨年级上传 403；隐藏后学生列表为空且下载 403；教师本学科上传/删除 200；后端 E2E 851/837/0/14；前端 build/lint/test/bundle 通过。
- **镜像**：`nanpo/edu-ai-platform:1.3.0` / `:latest` / `:sha-6be18dd` 已推送，manifest-list digest `sha256:7f39504c180b9e484d0e471015473da069d502fb6ae21d1b9d612d764bdd8e25`（基于 commit `6be18dd`）；容器 health=`healthy`、version=`1.3.0`、学生预览/下载、教师越权 403、可见性开关、47 页浏览器冒烟均通过。

### 1.4.0 附件文本解析 → Chroma → AI 引用来源

- **状态**：✅ 已实现
- **解析**：新增 `app/services/attachment_parser.py`：PDF(PyMuPDF)、xlsx(openpyxl)、docx/pptx(zip XML，无新依赖)、txt/md/csv；图片/旧版 Office 跳过；失败只告警。
- **索引**：`rag.py` 新增附件 chunk 索引（900 字/块、最多 40 块）、`attachment_id/knowledge_point_id/filename/path/...` metadata；只索引 published+active 知识点 + 学生可见附件；上传/可见性切换走 BackgroundTasks，删除/下架/知识点删除清理索引；reindex 增加附件阶段与 attachment 统计；检索兜底过滤失效附件，防止隐藏/草稿内容进 LLM。
- **引用**：TutorAgent 默认检索增加 attachment，`references` 返回「附件 + 文件名 + 知识点」；AgentChat 新增「引用来源」展示；原 LLM 调用/解析/fallback 未改动。
- **验证**：真实 Chroma 容器上传 PDF → 后台索引 → 学生 AI 答疑命中附件并展示引用；删除附件索引数下降；无 Chroma 环境下上传/AI 仍正常（索引降级跳过）。
- **不阻塞 AI 调用**：新增 Chroma 后台预热（`start_chroma_warmup`），预热期间 `search` 直接走 SQL 降级，AI 请求不被 79MB embedding 下载阻塞；镜像内置已验证的 ONNX 模型缓存（88MB），首次容器无需联网下载；流式 `/agent/chat/stream` 的 chat 意图兜底走 TutorAgent，并透传 `data`，引用来源在流式降级下也能展示。
- **镜像**：`nanpo/edu-ai-platform:1.4.0` / `:latest` / `:sha-c08bd8f` 已推送，manifest-list digest `sha256:a24051f680a63b049fa516436d23ed7c3ae210598fb6992c9213564544dfb1d7`（基于 commit `c08bd8f`，含模型缓存层）；容器 AI 答疑 0.34s 返回并带「附件 + 文件名 + 知识点」引用，47 页浏览器冒烟通过。

### 1.5.0 UI 优化（知识点附件上传区 + 班级管理）

- **知识点附件 UI**：独立资料区块（标题/数量/提示 + 上传/刷新工具栏）；多文件上传、扩展名/50MB 前端校验、上传计数；类型 tag、文件名点击预览、图标操作按钮 + tooltip、学生可见 tooltip、空态上传 CTA。
- **班级管理**：
  - 后端新增/增强：分页 class 列表（兼容旧数组）、stats、班级学生分页/搜索、CSV 导出、批量移出学生、批量启停/删除；班主任教师校验；编辑年级同步学生年级；description/remark 兼容。
  - 前端重写：统计卡、状态筛选、服务端分页、批量操作、状态快捷启停、学生抽屉（搜索/分页/导入模板/导出 CSV/批量移出）、班级表单增强；保留教师建班申请/审核。
- **验证**：E2E 851/837/0/14；前端 build/lint/test/bundle；真实浏览器完成附件上传→预览→删除，班级页统计/分页/学生抽屉正常。
- **镜像**：`nanpo/edu-ai-platform:1.5.0` / `:latest` / `:sha-0b3b8f7` 已推送，manifest-list digest `sha256:f4845667a2caa808a749b12d2037adfe802cee53769908dbfe9471a223fdf831`（基于 commit `0b3b8f7`，内置模型缓存）；容器 health=`healthy`、version=`1.5.0`、47 页浏览器冒烟通过。

### 1.6.0 年级管理检查与优化

- **发现**：排序字段 `sort_order` 与模型 `sort` 错位（排序失效）；新增年级默认序号 9、缺名称/学段/序号/重名校验；编辑无重名校验；删除漏查用户；年级写权限过宽（grade_admin 可改/删年级）；学科写未限本年级；前端无权限控制；年级页缺学段/序号/统计列。
- **修复**：新增 `resource:grade:write`（仅 sys_admin）与 `resource:subject:write`；年级写接口收紧为 sys_admin，学科写按年级 scope；补齐名称/学段/序号/重名校验、删除用户引用检查；年级列表补班级/学科/学生数与学段标签、关键词筛选；前端新增统计卡、学段筛选、学段/序号列，弹窗补齐字段，按钮按权限/行 scope 显隐，跨年级复制仅 sys_admin；年级/学科排序字段统一为 `sort`。
- **验证**：E2E 851/837/0/14；权限矩阵 teacher/student 年级/学科写 403、grade_admin 年级写 403 但本年级学科 200/跨年级 403、sys_admin 年级 CRUD 200；前端 build/lint/test/bundle；浏览器年级页统计/列/弹窗正常。
- **镜像**：`nanpo/edu-ai-platform:1.6.0` / `:latest` / `:sha-797dc72` 已推送，manifest-list digest `sha256:d5834920b0193f04d4285bddee210e63a230b3b537e45acf28a8826fac9811fa`（基于 commit `797dc72`，内置模型缓存）；容器 health=`healthy`、version=`1.6.0`、年级页统计/列正常、47 页浏览器冒烟通过。

### 1.6.1 年级/班级名称规则

- **年级**：新增/编辑不再手填名称，按「学段 + 年级序号」自动生成（小学 1-6、初中 7-9）；后端 `auto_name=true` 强制按规则命名并校验学段/序号/重名/序号唯一。
- **班级**：默认自动命名 `{年级}({序号})班`，只填班级序号（1-99）；新建自动建议下一个序号；特殊班级可开启「自定义名称」，限制长度 2-32 与允许字符，后端 `strict_name=true` 同步校验。
- **验证**：班级自动命名忽略乱写名生成 `一年级(9)班`；`乱写@@@` 400、`一年级兴趣班` 200；年级自动命名重复/学段序号不匹配 400；前端弹窗自动预览/只读/自定义开关正常。
- **镜像**：`nanpo/edu-ai-platform:1.6.1` / `:latest` / `:sha-1edf9c1` 已推送，manifest-list digest `sha256:82575ea6008c8d076e5a04e8bb992bb3c2fe1efb286746a8243f3ad91a330887`（基于 commit `1edf9c1`）；容器 health=`healthy`、version=`1.6.1`、47 页浏览器冒烟通过。

### 1.7.0 题库 V2 重构（权限/批量/AI/UI）

- **历史数据**：按用户确认，首次启动一次性清空 `edu_question`（级联 question_knowledge/paper_item），不重新播种；旧试卷可能变为空卷。
- **权限**：list/stats/duplicate → `question:bank:list`；create/update/delete/batch → `question:bank:write`；import/template → import；export → export；公共题上架 → audit；grade_admin 补 write；修复 `bank_type=private` 越权；学生 403；编辑/删除 owner/admin/grade_admin 规则。
- **功能**：严格 create/update 校验（年级/学科/知识点一致、题型/难度/分值/状态）；公共题非 audit 强制 draft；批量 delete/publish/offline/draft/move_bank/assign_knowledge/set_difficulty（引用题 delete 进 skipped、越权整体 403）；`/questions/stats`；列表 source/sort、type_stats 与筛选一致；导入表单参数修复/逐行校验/文件内去重；RAG 索引同步保留。
- **AI**：新增 `question_ai.py`：AI 变式/补全/质检，只预览；权限+归属+限流+ids≤50；无 LLM 规则降级 `is_fallback=true`，不影响原 LLM 调用。
- **UI**：QuestionBank.vue 重写：统计卡、完整筛选、多选批量栏、详情抽屉、AI 变体/补全/质检、导入导出模板/查重/单题 CRUD 保留。
- **E2E 适配**：test_teacher kp 按年级+学科过滤、引用保护改管理员；test_learning 前置题 bank_type=private；test_requirements kp 过滤。
- **验证**：E2E 850/836/0/14；API 动态验证批量/统计/AI/越权；前端 build/lint/test/bundle；浏览器题库页正常。
- **镜像**：`nanpo/edu-ai-platform:1.7.0` / `:latest` / `:sha-645980c` 已推送，manifest-list digest `sha256:eb27e89f7856f7d58431759ae22a92576441471cafb25c462e56144eb22d2f7e`（基于 commit `645980c`）；容器 health=`healthy`、version=`1.7.0`、47 页浏览器冒烟通过、题库批量/AI 接口正常。

### 1.8.0 试卷管理 V2（权限/批量/AI/UI）

- **权限**：list `paper:list`；create/update/delete/batch `paper:write`；share/export/AI 分别 `paper:share/export/ai`；grade_admin 补 `paper:write`。列表可见性修复为「本人创建 / is_shared / PaperShare 接收」，sys_admin 全量；学生 403。
- **校验**：名称/年级/学科/题量/题目可访问/同年级同学科/禁止重复/分值/时长/总分求和；编辑重建 items 同样校验。
- **接口**：`/papers/stats`、`/papers/batch`（delete 任务引用 skipped、copy、share）；列表 source/shared/creator_id/sort；share 兼容 to_user_id；四格式导出保留。
- **AI**：新增 `paper_ai.py`：AI 试卷分析（难度/题型/知识点覆盖/问题/建议）与 AI 推荐题目（薄弱知识点/难度缺口），无 LLM 规则降级、只读不落库。
- **UI**：PaperManage.vue 重构：统计卡、筛选、批量复制/删除/共享、详情抽屉、AI 分析/推荐、手动组卷选题器、权限按钮。
- **验证**：E2E 850/836/0/14；API 动态验证；前端 build/lint/test/bundle；浏览器列表/详情/AI 正常。
- **镜像**：`nanpo/edu-ai-platform:1.8.0` / `:latest` / `:sha-0724382` 已推送，manifest-list digest `sha256:a600a178f148e36e54644aa6efb50142cc04ce1b5d2e06a7c96ed5d147ebb68d`（基于 commit `0724382`）；容器 health=`healthy`、version=`1.8.0`、47 页浏览器冒烟通过、试卷 AI/批量接口正常。

### 1.9.0 AI 大模型配置与 AI 智能模块优化

- **配置后端**：`test_ai_connection(data, db)` 空/掩码 Key 自动读已保存 Key（显式清空不回落 env），provider/model/base_url DB 优先，返回 duration_ms；`/system/ai-config/test` 传 db。
- **Agent 状态**：`/agent/list`、`/agent/status` provider/model 改读 DB 配置，补 `key_configured/llm_temperature/llm_max_tokens`，修复后台改配置后 AI 页面仍显示 env 旧值的问题。
- **AI 配置 UI**：Key 不回填掩码、留空不修改、勾选清除、空 Key 测试、duration/usage、custom 必填、启用无 Key 确认、max_tokens capped/来源展示。
- **AI 模块**：AgentChat 删除重复引用块、localStorage 持久化、复制/重新生成/停止生成、状态卡与配置入口；AgentGenerate 修复 AI 题保存到题库（kp 数组→单值、年级学科兜底、private），逐条失败原因；状态卡配置提示。
- **验证**：E2E 850/836/0/14；后端动态 key/status 验证；前端 build/lint/test/bundle；浏览器 AI 三页无 console error。
- **镜像**：`nanpo/edu-ai-platform:1.9.0` / `:latest` / `:sha-4bbc904` 已推送，manifest-list digest `sha256:03a66939f0bfceffd4b051b253bdddb17b3550d65eee6d8af1c871d5922f2351`（基于 commit `4bbc904`）；容器 health=`healthy`、version=`1.9.0`、47 页浏览器冒烟通过、AI 配置 DB key/状态验证通过。











