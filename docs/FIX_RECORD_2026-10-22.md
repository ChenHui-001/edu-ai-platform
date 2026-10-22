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

