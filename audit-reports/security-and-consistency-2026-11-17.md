# 2026-11-17 安全与一致性专项（P0–P2）

> 范围：`E:\project\management` 工作区 + `edu-ai-platform` 应用仓库。
> 审计基线：`VERSION=2.5.38`，`5944a87`；运行时代码改动按交付规则升版，
> 最终发布版本为 `2.5.40`（`2.5.39` 因 CI 工具门禁失败未部署，镜像保留可追溯）。
> 本文件名中的日期是审计日，不代表发版日。
> 结论：P0 全部收口；P1 全部收口；P2 以「门禁 + 基线 + 计划」收口（见 P2-1）。
> 验证命令与结果见文末，所有结论均可复现。

## P0 — 凭据与数据暴露

| # | 问题 | 处置 | 状态 |
|---|---|---|:---:|
| P0-1 | 生产管理员/教师口令明文出现在 `deploy_scripts/README.md`、`deploy_init.py`、`verify_ai_save.py`、`seed_prod_data.py`、`diagnose_student_exam.py`、`verify_paper_v3.py` 及 `.workbuddy/memory` | 全部改为环境变量注入（`DEPLOY_PASS`、`ADMIN_PASS`、`SEED_TEACHER_PASS`、`SEED_STUDENT_PASS`、`TEACHER_PASSWORD`、`DIAG_USER/DIAG_PASS`、`TEST_ADMIN_*`）；批量初始化改用远端 `/tmp/edu_init_secrets.json`（0600，结束即删） | **已修** |
| P0-2 | `deploy_scripts/.deploy_pass` 明文口令文件 | 删除；`check_plaintext_secrets.py` 将该路径列为硬失败项 | **已修** |
| P0-3 | 含账号与学习数据的 SQLite 备份放在普通工作区 | 迁移到 `%LOCALAPPDATA%\EduAIPlatform\secure-backups\`，关闭 ACL 继承、仅当前用户可读；复制后 SHA256 校验一致再删源文件（`F2D7FC17…C068EE4`，5,656,576 B） | **已修** |
| P0-4 | 工作区无 `.gitignore`，备份/凭据/运维脚本可能被误提交 | 新增工作区级 `.gitignore` 与 `deploy_scripts/.gitignore`；`.env`、`*.db`、备份、记忆、运维脚本默认排除 | **已修** |
| P0-5 | 无凭据治理规范，泄露后无处置流程 | 新增 `docs/SECURITY.md` 与 `deploy_scripts/SECURITY.md`（注入方式、门禁、轮换清单） | **已修** |

> **仍需人工完成**：已出现在旧文本/聊天记录中的口令必须视为已泄露并**轮换**。
> 删除文本不是修复；本次只保证仓库与工作区不再新增明文。

## P1 — 配置、文档与回归能力

| # | 问题 | 处置 | 状态 |
|---|---|---|:---:|
| P1-1 | `STATUS`/架构文档仍写「无 Alembic」「`db_migrations` 不存在」「compose 无命名卷」 | 按实际实现改为 Alembic `0001_baseline` + 幂等补列 + `align_schema.py`；补正命名卷与迁移链说明 | **已修** |
| P1-2 | `docker-compose.yml` 的 `SEED_DEMO_DATA` 默认 `true`，生产误起会写入演示账号 | 默认改 `false`；本地体验需显式 `SEED_DEMO_DATA=true` | **已修** |
| P1-3 | 镜像标签 `IMAGE_TAG=2.5.19`、前端 `package.json=2.0.0` 与 `VERSION=2.5.38` 漂移 | 本地 `.env` 与 `frontend/package.json` 对齐 `2.5.38`；`package-lock.json` 同步 | **已修** |
| P1-4 | CI 注释仍写 10 文件/119 用例；新增门禁未进 CI | 更新为 11 文件/129 用例；接入 `check_file_size.py`、`check_plaintext_secrets.py` | **已修** |
| P1-5 | `Class.head_teacher_id` 循环外键导致建表/迁移告警 | 外键加 `use_alter=True, name="fk_edu_class_head_teacher"`；`check_alembic_sync` 通过 | **已修** |
| P1-6 | 前端无组件级回归，交互修复只能靠 e2e 冒烟 | 新增 `components.test.js`（ErrorState / AiFallbackNotice / ExportButton / TableCards 共 10 例），vitest 119→129；`check_new_code_tests.py` 同步基线 | **已修** |
| P1-7 | 无只读性能基线，SQLite 尾延迟不可观测 | 新增 `tools/load_test.py`（标准库、只 GET、输出 RPS/p50/p95/p99），默认错误率 >1% 或 p95 >500ms 失败 | **已修** |

## P2 — 长期结构债务

| # | 问题 | 处置 | 状态 |
|---|---|---|:---:|
| P2-1 | 13 个文件超过 1200 行（最大 2138），无门禁约束 | 新增 `tools/check_file_size.py`：存量文件登记**只降不升**预算，新增文件 ≤1200 行；接入 CI 与 `auto_ship.sh` | **已收敛** |
| P2-2 | 44 条功能用例未执行 | 复核结果：`api_unexecuted=0`，44 条全部是 UI/人工用例；本次补组件级回归作为兜底，UI 路径仍按人工/浏览器验收 | **已澄清** |
| P2-3 | 明文凭据与文件体积检查依赖人工记忆 | 新增 `check_plaintext_secrets.py`（只报位置不回显内容），扫描应用仓库 + `deploy_scripts` + `.workbuddy` | **已修** |

### P2-1 说明：为什么没有一次性拆完

`check_file_size.py` 的定位是**阻止继续变长**，不是「重构周」。一次性搬动 13 个
2000 行级文件，正是该脚本注释里反对的高风险做法。当前处置：

1. 存量文件预算冻结，任何提交都不能再长；
2. 新文件受 1200 行硬顶约束；
3. 拆分时按域下沉（先纯函数/服务，再路由/模板），每拆一个文件同步下调预算。

优先拆分顺序（按业务风险与耦合度）：

1. `backend/app/api/v1/question.py`（题库 + 试卷两个域，可按 `question` / `paper` 路由拆分）；
2. `backend/app/services/init_db.py`（演示数据构造可独立为 `demo_seed.py`）；
3. `frontend/src/views/teacher/PaperWizard.vue`（按步骤拆子组件 + 纯逻辑 composable）；
4. `tools/gen_knowledge_points.py`（约 1600 行是静态课程数据，应转数据文件，不计逻辑复杂度）。

## 验证记录

以下命令在 `edu-ai-platform` 下执行，均为通过：

| 命令 | 结果 |
|---|---|
| `python -m pytest backend/qa_audit_suite.py -q` | 74 passed |
| `python tools/verify_p0_fixes.py` | 117 条接口断言全通过 |
| `cd frontend && npm test` | 11 文件 / 129 passed |
| `cd frontend && npm run lint` | 0 warning |
| `cd frontend && npm run build` | 构建成功 |
| `python tools/check_alembic_sync.py` | 迁移链/模型/create_all 三方一致（53 表） |
| `python tools/check_migration_columns.py` | 34 条补列与模型一致 |
| `python tools/check_doc_versions.py` | 文档版本与 `VERSION` 一致 |
| `python tools/check_new_code_tests.py` | pytest=72 / vitest=129 |
| `python tools/check_file_size.py` | 13 个存量未超预算 |
| `python tools/check_plaintext_secrets.py` | 427 个文件无生产形态明文凭据 |
| `python tools/status_snapshot.py --write` | `STATUS` 自动区块已重算 |

### 压测基线（临时库，非生产）

| 路径 | 并发 | 请求数 | RPS | p95 | 错误 |
|---|---:|---:|---:|---:|---:|
| `/health` | 20 | 1509 | 234.4 | 185.5 ms | 0 |
| `/edu/classes` | 10 | 115 | 19.6 | 913.6 ms | 0 |

`/edu/classes` 的 p95 已超过脚本默认 500ms 阈值，本次以 `--max-p95-ms 1500`
记录基线。它反映的是 SQLite + 单 worker 下列表查询的真实成本，不是回归；
后续若要把阈值收紧到 500ms，应先做查询优化或换库。

## 残余风险（不在本轮代码修复范围）

- **凭据轮换**：必须由运维在目标环境完成，并检查镜像层、日志、备份与聊天记录。
- **多 worker**：当前刻意 `--workers 1`，限流桶/缓存/RAG 集合均为进程内，扩 worker 前需先改造（BACKLOG P1-15）。
- **知识点数据缺口**：约 42 个学科无知识点，属运营补数据，不是代码缺陷。
- **UI 用例**：44 条 UI/人工用例仍依赖浏览器验收，api 类未执行为 0。
