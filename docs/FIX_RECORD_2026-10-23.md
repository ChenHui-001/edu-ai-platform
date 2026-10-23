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

