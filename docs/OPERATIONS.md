# 运维手册（入口 / 备份恢复 / 资源边界）

> 本文只写「线上怎么进、数据怎么保底、容器边界在哪」。发版流程见
> [`DELIVERY_RULES.md`](DELIVERY_RULES.md) 与 [`RELEASE_CONSISTENCY.md`](RELEASE_CONSISTENCY.md)。

## 一、访问入口

| 入口 | 地址 | 说明 |
|---|---|---|
| 生产（唯一对外） | `https://592587860.xyz:8443` | Caddy 终止 TLS 后反代到 `127.0.0.1:8081` |
| 本机 | `http://localhost:8080` | 本机容器，`docker compose` 管理 |

- 证书只签域名，**IP 直连 HTTPS 不可用**；`https://186.241.77.194:8443` 会握手指纹不匹配。
- 容器端口已改为 `-p 127.0.0.1:8081:80`（`tools/deploy_release.py`）。Caddy 走回环即可，
  **外部无法再直连 8081**。若临时需要外部直连排障，用 SSH 隧道而不是改回 `0.0.0.0`：
  `ssh -L 8081:127.0.0.1:8081 root@186.241.77.194`。
- Caddy 自身配置在服务器 `/etc/caddy/Caddyfile`，勿动同一文件里的企业微信反代与 80/5010 端口。

### 安全响应头

`deploy/nginx/default.conf` 统一输出（`always`，错误页也带）：

```
Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline';
  img-src 'self' data: blob:; font-src 'self' data:; connect-src 'self'; media-src 'self' blob:;
  worker-src 'self' blob:; frame-src 'self' blob:; object-src 'self' blob:;
  frame-ancestors 'self'; base-uri 'self'; form-action 'self'
X-Content-Type-Options: nosniff
X-Frame-Options: SAMEORIGIN
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: camera=(), microphone=(), geolocation=()
```

`blob:` 是附件预览与打印必需，不要为「更严格」而删掉，否则 PDF/图片预览白屏。

## 二、每日备份

两层都保留，互相独立：

| 层 | 位置 | 频率 | 保留 | 实现 |
|---|---|---|---|---|
| 服务器 | 容器内 `/app/data/backups/daily-YYYYMMDD.db` | 每天 02:00（北京时间，cron `0 18 * * *` UTC） | 7 天 | `/usr/local/bin/edu-daily-backup.sh` |
| 本机异地 | `E:\project\management\edu-data-backups\prod\daily-YYYYMMDD.db` | 每天 02:30 | 30 份 | Windows 计划任务 `EduProdDailyBackup` |

快照走 SQLite 在线备份 API（不是直接拷文件），写完立即 `PRAGMA integrity_check`；
下载后再校验 SHA-256 与完整性，报告落在 `E:\project\management\sync_reports\`。

手工补一份：

```powershell
python E:\project\management\deploy_scripts\backup_prod_daily.py
```

首次在服务器装 cron：

```powershell
python E:\project\management\deploy_scripts\backup_prod_daily.py --install-cron
```

> **已知限制**：`EduProdDailyBackup` 当前是「仅在用户登录时运行」（Interactive）。
> 注销后不会执行。要彻底后台运行，需在任务计划程序里改为
> 「不管用户是否登录都要运行」并保存凭据；或在服务器侧单独保留一份异地拉取。
> 服务器 cron 不受此限制，即使本机没开机也仍然每天出快照（只保留 7 天）。

## 三、恢复

恢复会覆盖现网数据，先停容器并留一份现场副本：

```bash
# 服务器上
docker stop edu-platform
cp /opt/edu-ai-platform/data/edu_platform.db \
   /opt/edu-ai-platform/data/edu_platform.db.before-restore-$(date +%Y%m%d%H%M)
```

把要恢复的快照放进容器可写目录（容器停止时 `docker cp` 仍可用）：

```bash
docker cp /opt/edu-ai-platform/data/backups/daily-20261118.db \
  edu-platform:/app/data/edu_platform.db
chown 10001:10001 /opt/edu-ai-platform/data/edu_platform.db
docker start edu-platform
curl -fsS http://127.0.0.1:8081/api/v1/ready
```

`ready` 返回 200 且 `checks.database=true` 才算恢复完成；随后登录抽查题库/成绩。
本机库恢复同理：停 `edu-platform` → 用备份覆盖 `data/edu_platform.db` → 启容器。

## 四、容器资源边界

`tools/deploy_release.py` 创建容器时固定：

```
--log-driver json-file --log-opt max-size=20m --log-opt max-file=5
--memory 2g --memory-swap 2g
```

- 日志上限 100MB，避免长期运行把磁盘写满（旧容器无上限）。
- 2GB 内存对单 worker + Chroma 足够；调大前先确认宿主机余量。
- 健康检查：`/api/v1/health`（存活）与 `/api/v1/ready`（数据库、扩展表、目录可写）。

## 五、依赖安全基线

每轮发版前跑：

```powershell
cd E:\project\management\edu-ai-platform
.\.venv\Scripts\python.exe -m pip_audit -r backend\requirements.txt `
  -f json -o E:\project\management\sync_reports\pip-audit-<version>.json
```

2026-11-19（2.5.47）基线：

- 后端：FastAPI 0.165 / Starlette 1.10 / LangChain 1.5 / LangGraph 1.2 / Chroma 1.5。
  0.3 线遗留的 35 项公告已随主版本升级消除；仍无修复版本的条目以 `pip-audit` 输出为准。
- 前端：`0 high / 0 critical`；剩余 4 个 moderate 全部在开发依赖链
  （`@vue/test-utils → js-beautify → editorconfig/glob/minimatch`、`eslint → minimatch`），
  不进生产包，待上游发版后随 `npm audit fix` 收敛。
- Chroma 1.x 的 ONNX 模型不再随包分发，镜像构建阶段已预置到
  `/home/app/.cache/chroma/onnx_models/all-MiniLM-L6-v2`；本机开发需保证同名缓存存在，
  否则首次向量检索会现场下载约 79MB。

## 六、上游数学数据同步

与业务库无关，只同步「外部数学知识点 / 先修关系 / 上游题目」：

```powershell
python E:\project\management\deploy_scripts\sync_math_taxonomy.py --check-only --target both
python E:\project\management\deploy_scripts\sync_math_taxonomy.py --target both --prune-stale
```

页面入口 `/admin/taxonomy-sync` 只记录页面发起的同步；脚本发起的不会出现在页面历史里。
细节见 [`../deploy_scripts/SYNC_MATH_TAXONOMY.md`](../../deploy_scripts/SYNC_MATH_TAXONOMY.md)
（该文件在仓库外，随运维目录保存）。
