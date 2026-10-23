# 交付规则（必须遵守）

> 适用于本项目所有代码改动。该规则优先于“只提交代码、稍后再发镜像”的习惯。

## 1. 每次代码改动提交后，必须同步 Docker Hub

- **凡是会改变镜像内容的改动**（`backend/`、`frontend/`、`Dockerfile`、`deploy/`、`docker-compose.yml`、`VERSION` 等），
  每完成一次提交，都必须重新构建并推送镜像到 Docker Hub，再结束该轮工作。
- 唯一例外：**仅文档/记录类提交**（`docs/`、`README.md` 等不进入镜像的内容）不会改变镜像内容，
  不需要重复构建；镜像继续对应最近一次运行时代码提交，需在发布记录中写明对应 commit。
- 不允许出现“代码已推送、Docker Hub 还是旧镜像”且未说明的情况。

## 2. 标签策略

| 标签 | 用途 | 何时推送 |
|---|---|---|
| `nanpo/edu-ai-platform:<VERSION>` | 可复现的版本发布 | `VERSION` 变更后 |
| `nanpo/edu-ai-platform:latest` | 最新可用镜像 | 每次代码镜像同步 |
| `nanpo/edu-ai-platform:sha-<short7>` | 按 commit 精确追溯 | 每次代码镜像同步 |

- 已发布的版本标签（如 `1.0.42`）**不允许覆盖**；运行时代码变化时升 `VERSION` 再发布。
- 构建必须带溯源参数：`APP_VERSION=<VERSION>`、`GIT_COMMIT=<HEAD>`、`BUILD_TIME=<UTC ISO>`，
  镜像内 `/app/BUILD_INFO` 必须可查。

## 3. 同步前必须验证

1. 代码已提交且工作区干净（不允许把未提交代码打进镜像）。
2. 后端全量 E2E：`python tests/run_all.py` 失败数为 0（允许既有环境跳过）。
3. 前端：`npm run build`、`npm run lint`、`npm run test`、`npm run check:bundle` 全部通过。
4. 新镜像实机运行：`/api/v1/health` 为 healthy、admin 可登录、非 root 运行；
   如改动涉及页面，再跑 `tests/ui_e2e/browser_smoke.py`。
5. 推送后用 `docker buildx imagetools inspect` 核对远端标签与 digest。

## 4. 发布记录

每次镜像同步后更新：

- `docs/RELEASE_CONSISTENCY.md`：版本、commit、digest、latest 指向、验证结果；
- `docs/FIX_RECORD_YYYY-MM-DD.md`：本轮改动与镜像发布结果；
- 记录中必须能回答：**这份镜像对应哪个 commit、什么时候构建、是否已验证**。

## 5. 当前状态

- 1.2.0 已发布（Docker Hub，manifest-list digest `sha256:09e77c17…`，对应 commit `adac1cf`）。
- 1.1.0 / 1.0.43 / 1.0.42 保留为历史版本，不再覆盖。
