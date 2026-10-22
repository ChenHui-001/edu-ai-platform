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

