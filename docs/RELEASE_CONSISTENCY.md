# 发版一致性工作流说明

> 目标：**本地代码 == 远程仓库 == Docker 镜像**，且版本号在三处始终统一。
> 本文说明各环节的版本来源、同步节点、校验方式，以及已消除的漂移隐患。

---

## 一、五个版本落点与各自的真源

版本号不是"一个值"，而是沿发布链路被**复制五次**的一个值。每次复制都可能与源头脱节。

| # | 落点 | 是什么 | 由谁写入 | 出错后果 |
|---|---|---|---|---|
| ① | `VERSION`（仓库根目录） | **唯一真源**，单行 `x.y.z` | 人工 / `auto_ship.sh --bump` | 一切下游取值的源头 |
| ② | `commit -> origin/master` | 代码离开本机的唯一通道 | `git commit` + `git push` | 镜像对应 commit 在远端不存在 → 无法溯源、无法复现 |
| ③ | 镜像内 `/app/VERSION` + `/app/BUILD_INFO` | 镜像内的版本与 commit 快照 | `Dockerfile` 的 `COPY VERSION` + `RUN printf` | 镜像里的代码与标签不符 |
| ④ | 镜像标签 `repo:1.0.42` | 人为命名的自由文本 | `docker build -t` / metadata-action | 标签指向错误内容，且**不会报错** |
| ⑤ | `/api/v1/health` 的 `version` | 运行时可观测值 | `config.py:_resolve_version()` | 线上显示的版本与实际不符 |

`_resolve_version()` 的优先级：显式 `APP_VERSION`（须匹配 `^v?\d+\.\d+`）→ `/app/VERSION` → `"dev"`。

> ⚠️ 不要设 `ENV APP_VERSION=""`：buildx 缓存会让上一轮的值（如 `latest`）残留到新镜像，
> 导致 `/health` 返回错误版本号。因此 Dockerfile 里保留 `ARG APP_VERSION=""` 但不主动置空 ENV。

---

## 二、关键认知：版本号相同 ≠ 代码相同

这是本次改造的出发点，也是原工作流最大的盲区。

**实测案例（本次改造前）**：

```
镜像 nanpo/edu-ai-platform:1.0.40   构建于 2026-10-20 15:46
仓库 HEAD                            2026-10-22（含 20 项缺陷修复 + 4 个提交）
```

版本号**完全一致**，代码**差两天**。而原来的校验只比对版本号字符串，判定"通过"。
`1.0.40` 可以被构建十次、每次内容都不同 —— 版本号根本无法证明内容。

**解法**：构建时把 commit 烧进镜像，用 commit 而非版本号作为"代码身份"。

```dockerfile
ARG GIT_COMMIT=""
ARG BUILD_TIME=""
LABEL org.opencontainers.image.version=${APP_VERSION} \
      org.opencontainers.image.revision=${GIT_COMMIT} \
      org.opencontainers.image.created=${BUILD_TIME}
RUN printf 'version=%s\ncommit=%s\nbuilt_at=%s\n' \
        "$(cat /app/VERSION 2>/dev/null || echo unknown)" \
        "${GIT_COMMIT:-unknown}" "${BUILD_TIME:-unknown}" \
        > /app/BUILD_INFO
```

写入两处，各有用途：

- **`/app/BUILD_INFO`** — 校验的**首选来源**。版本与 commit 同源同批写入，不会分裂。
- **OCI label** — 可 `docker inspect` 直读、无需启动容器，适合远程 registry 回查。

> 为什么 BUILD_INFO 优先：`LABEL` 无法从文件取值，只能靠构建命令主动传 `ARG APP_VERSION`。
> 漏传时会出现"label 有 revision 但 version 为空"的半残状态（本次实测已遇到）。

---

## 三、一致性判定标准

三者对齐的**充分条件**是以下三条同时为真：

```bash
# 1. 本地 == 远程
git rev-parse HEAD == git rev-parse origin/master

# 2. 镜像内的 commit == HEAD
docker inspect --format '{{index .Config.Labels "org.opencontainers.image.revision"}}' repo:VERSION
#   == git rev-parse HEAD

# 3. 镜像内的 version == VERSION 文件
docker run --rm --entrypoint cat repo:VERSION /app/VERSION
#   == cat VERSION
```

**只满足第 3 条是"假一致"** —— 这正是镜像落后两天却被判为通过的原因。

---

## 四、同步节点与四道闸门

```
改代码
  │
  ├─[节点1] 改 VERSION（唯一真源）────────────┐
  ├─[节点2] git commit                        │  auto_ship.sh --bump patch
  ├─[节点3] git push origin master            │  会自动做 1→2→3
  │        ↓                                  │
  │   [闸门 A] --pre 校验                     │
  │      · VERSION 格式 x.y.z                 │
  │      · 工作区干净（否则镜像含未入库代码）  │
  │      · 已推送（否则镜像无法溯源）          │
  │      · git tag 与 VERSION 自洽             │
  │        ↓                                  │
  ├─[节点4] docker build --build-arg GIT_COMMIT=$(git rev-parse HEAD)
  │        ↓  （commit 烧入镜像）
  ├─[节点5] docker push repo:VERSION + :latest
  │        ↓
  │   [闸门 B] --post 校验
  │      · 远端镜像存在                        │
  │      · 镜像内 version == VERSION           │
  │      · 镜像内 commit == HEAD               │
  │      · latest 指向本次版本                  │
  └────────────────────────────────────────────┘
```

### CI 侧（`docker-publish.yml`）的三 job 结构

| Job | 职责 | 不过时的行为 |
|---|---|---|
| `preflight` | 校验并导出发布元数据；tag/VERSION 自洽；工作区干净；版本号未重复发布 | **不构建** |
| `build-push` | 登录 ghcr、生成标签、构建多架构、注入 commit 指纹 | 中断 |
| `postflight` | **回查 registry**：拉 manifest → config → 校验 label 与 BUILD_INFO | 报错失败 |

> `postflight` 的存在理由：`docker push` 的退出码只说明**字节传上去了**，
> 不说明传上去的是**不是这次的代码**。必须回查 registry 才算闭环。

### 闸门清单

| 闸门 | 位置 | 拦截的漂移 |
|---|---|---|
| A. `--pre` | `auto_ship.sh` 构建前 | 脏工作区、未推送、tag 与版本不符 |
| B. `--post` | `auto_ship.sh` 推送后 | 远端内容与本地不符、latest 指错 |
| C. `preflight` | CI 构建前 | 同上 + 重复发布同版本号 |
| D. `postflight` | CI 推送后 | 从 registry 侧独立复核 |

---

## 五、用法

### 本地交付

```bash
# 完整流程：改动检测 → 回归 → commit → push → 校验 → 构建镜像
bash tools/auto_ship.sh

# 升版 + 全流程 + 推 Docker Hub
bash tools/auto_ship.sh --bump patch --push

# 不推 git（离线/临时验证）
bash tools/auto_ship.sh --no-push
```

退出码：`0` 成功 / `1` 测试或环境失败 / `2` git 提交或推送失败 / `3` 构建或镜像推送失败 / `4` 无改动（发布后核对未通过也返回 `4`）。

### 单独跑一致性校验

```bash
python tools/check_release_consistency.py --pre     # 发布前（严格）
python tools/check_release_consistency.py --post    # 发布后（含远端回查）
python tools/check_release_consistency.py           # 静态，不联网
python tools/check_release_consistency.py --no-image  # 跳过 docker
```

退出码：`0` 通过 / `1` 不一致（含 VERSION 缺失、git 或 docker 等环境不可用导致校验无法完成的情况）。

### 手工发版（不推荐，仅在必要时）

```bash
echo "1.0.42" > VERSION
git commit -am "chore(release): 1.0.42" && git push origin master
python tools/check_release_consistency.py --pre        # 必须先过
./push_dockerhub.sh nanpo                              # 内部已带指纹参数
python tools/check_release_consistency.py --post
```

---

## 六、已消除的漂移隐患

| 隐患 | 原状 | 现在 |
|---|---|---|
| **工作流从不触发** | `branches: [main]`，而主分支是 `master` → 一次都没跑过 | 改为 `master`，实测已触发并跑通 |
| **镜像推到两个仓库** | `IMAGE_NAME: ${{ github.repository }}` = `ChenHui-001/`，与手工推的 `nanpo/` 分裂 | CI 走 `ghcr.io/chenhui-001/`，本地走 `nanpo/`，**明确分工** |
| **latest 死步骤** | 第 57-59 行只 `echo "推送 latest 标签"` | 删除，改由 metadata-action 条件生成 |
| **CI 缺凭据必失败** | 依赖 2 个从未配置的 secret → 首次运行即 `Username and password required` | 改用 `GITHUB_TOKEN`，无需任何手工 secret |
| **代码从不自动推送** | `auto_ship.sh` 只有 `git commit`，没有 `git push` | 补 `2b/5` 步骤，失败即中止（阶段解耦） |
| **版本号相同但代码不同** | 无任何检测手段 | commit 指纹比对，严格模式硬失败 |
| **tag 与 VERSION 脱钩** | `v1.0.42` 会静默产出 `:1.0.41` 镜像 | `preflight` + `push_dockerhub.sh` 双重校验 |
| **补发旧版本回退 latest** | 无保护 | 手动发布时可勾 `skip_latest` |

---

## 七、验证方式

### 门禁必须能抓到真 bug（反向验证）

新写门禁**先用"已知有 bug 的旧版本"验证**，否则可能对真 bug 报"0 隐患"。
本次已做的反向验证：

**① tag 漂移检测** — 造 `VERSION=1.0.41` 但 HEAD 上有 `v1.0.42` 的仓库：

```
[FAIL] git tag 与 VERSION 一致  -> ['v1.0.42 != 1.0.41']；该 tag 的发布会打出错误版本号的镜像
EXIT=1
```

**② commit 指纹比对** — 5 个场景全部符合预期：

| 场景 | 期望 | 实际 |
|---|---|---|
| 指纹 == HEAD（完整 40 位） | PASS | PASS |
| 指纹 == HEAD 前 7 位 | PASS | PASS |
| 指纹 == HEAD 前 12 位 | PASS | PASS |
| 指纹是别的 commit | FAIL | FAIL |
| 无指纹（绕开 `--build-arg`） | FAIL | FAIL |

**③ 真实漂移捕获** — 改造过程中真实施工触发：

```
[FAIL] 本地镜像内 commit == HEAD  -> 镜像出自 ce96316，当前代码是 512e0ec；
       镜像里**不是**当前这份代码 —— 版本号相同也会骗人，必须重建
```

### 日常核对

```bash
# 一条命令看全貌
python tools/check_release_consistency.py

# 直接问容器（部署现场排查用）
docker exec <container> cat /app/BUILD_INFO
curl -s http://localhost/api/v1/health | jq .version
```

### CI 侧

`Docker 镜像发布` 的 `发布后一致性核对` job 会从 registry 侧独立复核；
结果写入该 run 的 Summary 表格（版本 / commit / digest / latest）。

---

## 八、当前状态（1.3.0）

| 项 | 值 |
|---|---|
| VERSION | `1.3.0` |
| commit | `6be18dd`（知识点资料附件/学生知识资料页；镜像基于该 commit） |
| 本地镜像 | `nanpo/edu-ai-platform:1.3.0` / `:latest` / `:sha-6be18dd`（digest `sha256:7f39504c…`） |
| ghcr | 未推送（手动发布 Docker Hub；未触发 CI） |
| Docker Hub | 已推送 `1.3.0`（manifest-list digest `sha256:7f39504c180b9e484d0e471015473da069d502fb6ae21d1b9d612d764bdd8e25`） |
| latest | 已推送，与 `1.3.0` 同一 digest |
| 发布后校验 | 容器 health=`healthy`、version=`1.3.0`；学生附件预览/下载、教师越权 403、可见性开关、47 页浏览器冒烟通过 |
| CI | 未触发（手动发布）；后续遵循 `docs/DELIVERY_RULES.md` |

> 最近一次发布（1.0.41）的四闸门结果作为流程有效性参照：
> 发布后校验 **10 通过 / 0 失败 / 0 警告 / 0 跳过**（EXIT=0），
> CI 两个 run 全 success（`6bac8a6`、`67e7e3e`，含 postflight）。

### 关于 `commit` 与 `镜像内 commit` 不完全相同（1.0.41 发布时实例）

这是**预期状态**，不是漂移。`6bac8a6..85cff22` 之间的提交只改了
`docs/`、`.github/`、`tools/` —— 这些路径**不进镜像**，镜像字节未变。

工具据此判定"等价"：

```
[PASS] 本地镜像内 commit 与 HEAD 等价
       镜像出自 6bac8a6，HEAD 是 85cff22，
       但 6bac8a6..85cff22 无影响镜像内容的改动（仅文档/CI）
```

若差异落在 `backend/app/`、`frontend/`、`deploy/`、`requirements.txt`、
`VERSION`、`Dockerfile` 等会被 `COPY` 的路径，则**立即判 FAIL 并要求重建**。

### 两条发布通道

| 通道 | 目标 | 凭据 | 触发 |
|---|---|---|---|
| CI（`docker-publish.yml`） | `ghcr.io/chenhui-001/edu-ai-platform` | `GITHUB_TOKEN`（自动） | push master / `v*` tag / 手动 |
| 本地（`push_dockerhub.sh`） | `nanpo/edu-ai-platform` | `docker login` 本地凭据 | 手工执行 / `auto_ship.sh --push` |

部署端拉取时确认用的是哪个。如需统一到 Docker Hub，设仓库变量
`IMAGE_NAME=nanpo/edu-ai-platform` 即可（须先配好 `DOCKERHUB_USERNAME` /
`DOCKERHUB_TOKEN` 两个 secret）。

### 已知网络限制

本机到 Docker Hub 的 `auth.docker.io` 经常超时（`curl` 返回 `000`），
而 `registry-1.docker.io` 返回 `401` 属正常。表现为 `docker push` 长时间
停在 `Waiting`（实测一次耗时 43 分钟才完成）。

应对：`docker push` 支持断点续传——已上传的分层会命中
`Layer already exists`，中断后直接重跑即可，不必从头开始。
若某次推送后远端只见 `latest` 不见版本号标签，单独补推版本号即可
（分层已全部就位，通常数秒完成）。
