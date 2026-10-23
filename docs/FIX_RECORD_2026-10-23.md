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

