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

