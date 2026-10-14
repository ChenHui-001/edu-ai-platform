# 本地一键启动指南

无需敲任何命令，双击即可在本地跑起整个系统。

---

## 三十秒上手

### Windows

| 步骤 | 操作 |
|------|------|
| 1 | 双击 **`start.bat`** |
| 2 | 等待 3-15 分钟（首次要构建镜像，之后约 30 秒） |
| 3 | 浏览器自动打开 http://localhost:8080 |
| 4 | 用默认账号登录看效果 |

**用完关服务**：双击 `stop.bat`，或在 `start.bat` 窗口按 `Ctrl+C`。

> 关闭启动窗口**不会**停止服务（容器在后台跑）。要停服务请用 `stop.bat`。

### macOS / Linux

```bash
./start.sh              # 启动
./start.sh logs         # 看日志
./start.sh stop         # 停止
```

---

## 默认账号

| 角色 | 账号 | 密码 | 能看到什么 |
|------|------|------|-----------|
| **系统管理员** | `admin` | `Admin@123456` | 全部功能：用户、角色、日志、报表、附件、系统配置 |
| **年级管理员** | — | — | 本年级教学资源与数据 |
| **教师** | `teacher1` ~ `teacher4` | `Teacher@123` | 题库、组卷、发布作业、批改、学情分析 |
| **学生** | `stu7*` / `stu1*` | `Student@123` | 答题、错题本、笔记、智能复习、成绩中心 |

> 首次登录会强制修改密码。生产部署请立即改掉所有默认密码。

**建议的体验路线**：先用 `admin` 看系统全貌 → 再用 `teacher1` 建题组卷 → 最后用 `stu731` 答题，看 AI 批改和错题本自动收录的效果。

---

## 命令一览

### `start.bat`（双击即用）

```bat
start.bat              启动服务（默认 8080）
start.bat 8081         换端口启动
start.bat help         查看所有命令
```

### `manage.bat`（命令管理）

```bat
manage.bat logs        实时日志（Ctrl+C 退出）
manage.bat status      服务状态 + 健康检查
manage.bat restart     重启
manage.bat stop        停止
manage.bat reset       清空全部数据，恢复初始状态
manage.bat rebuild     清除缓存重新构建镜像
```

### `start.ps1`（推荐，彩色输出）

```powershell
.\start.ps1                          # 启动
.\start.ps1 -Port 8081               # 换端口
.\start.ps1 -NoBrowser               # 不自动开浏览器
.\start.ps1 -Command logs            # 看日志
.\start.ps1 -Command status          # 看状态
.\start.ps1 -Command reset           # 清空数据重启
```

---

## 脚本做了什么

`start.bat` / `start.ps1` 的启动流程：

1. **检查 Docker** —— 没装或没运行会给出明确指引
2. **检查端口** —— 被占用时自动找下一个空闲端口，并把结果写回 `.env`
3. **准备 `.env`** —— 首次自动生成，顺手做三件事：
   - 生成 64 位随机 `SECRET_KEY`（不是明文默认值）
   - 修正 `DOCKERHUB_REPO` 的占位符名
   - 把实际使用的端口写入 `HOST_PORT`
4. **构建并启动容器**
5. **轮询健康接口** —— 直到真的返回 `"status":"healthy"` 才算就绪（不是"端口能连上"）
6. **显示访问信息**并自动打开浏览器

---

## 常见问题

**Q：提示「端口 8080 已被占用」**
脚本会自动改用 8081/8082…，并把端口写回 `.env`。也可以手动指定：`start.bat 9090`。

**Q：构建很慢或卡在拉镜像**
国内网络访问 Docker Hub 不稳。在 Docker Desktop → Settings → Docker Engine 里配置镜像加速：
```json
{ "registry-mirrors": ["https://docker.m.daocloud.io", "https://dockerproxy.cn"] }
```
然后点 Apply & Restart。

**Q：想重新体验「全新用户」的感觉**
```bat
manage.bat reset
```
会清空数据库，回到种子数据状态（管理员、4 个班级、12 名学生、演示题库）。

**Q：想启用真实大模型 AI**
编辑 `.env`：
```env
LLM_ENABLED=true
LLM_PROVIDER=deepseek        # 或 qwen / openai / ollama
LLM_API_KEY=sk-xxxxxxxx
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL=deepseek-chat
```
然后 `manage.bat restart`。

不配置也能用 —— AI 会降级为规则引擎，出题、组卷、判分、复习计划全部可用，只是不如大模型灵活。

**Q：中文显示乱码**
`start.bat` 已内置 `chcp 65001`。若仍乱码，改用 `start.ps1`（PowerShell 版对编码处理更稳）。

**Q：数据存在哪**
`./data/` 目录（SQLite 数据库 + 附件 + 向量索引 + 日志），删掉即彻底重置。

**Q：想用已发布的镜像，不重新构建**
```powershell
.\start.ps1 -Command rebuild   # 会重新构建
```
或手动：
```bat
docker compose down
docker pull nanpo/edu-ai-platform:1.0.0
docker compose up -d
```

---

## 文件说明

| 文件 | 用途 |
|------|------|
| `start.bat` | 主启动器，双击即用（无参数交互 / 带子命令） |
| `start.ps1` | PowerShell 版，彩色输出，支持 `-Port` / `-NoBrowser` / `-Command` |
| `start.sh` | macOS / Linux 版 |
| `stop.bat` | 一键停止（等价于 `manage.bat stop`） |
| `manage.bat` | 服务管理：logs / status / restart / stop / reset / rebuild |
| `push_dockerhub.sh` | 构建并推送到 Docker Hub |