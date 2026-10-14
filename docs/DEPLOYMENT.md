# 部署指南

本文档面向学校信息中心 / 系统运维人员，覆盖从裸机到生产环境的完整部署流程。

---

## 一、环境要求

| 项目 | 最低配置 | 推荐配置 |
|------|---------|---------|
| CPU | 2 核 | 4 核 |
| 内存 | 4 GB | 8 GB |
| 磁盘 | 40 GB | 100 GB SSD |
| 系统 | Linux x86_64 / Windows Server 2019+ | Ubuntu 22.04 LTS |
| Docker | 20.10+ | 24.0+ |

支持规模：单校 1000 人以内，500 人同时在线。

---

## 二、Docker 快速部署

### 2.1 准备

```bash
# 安装 Docker（Ubuntu 示例）
curl -fsSL https://get.docker.com | sh
systemctl enable --now docker

# 配置镜像加速（国内网络）
mkdir -p /etc/docker
cat > /etc/docker/daemon.json <<'EOF'
{
  "registry-mirrors": [
    "https://docker.m.daocloud.io",
    "https://dockerproxy.com"
  ]
}
EOF
systemctl restart docker
```

### 2.2 部署应用

```bash
# 拉取镜像
docker pull <your-dockerhub-user>/edu-ai-platform:latest

# 创建数据目录
mkdir -p /opt/edu-platform/data/{uploads,exports,logs,chroma}

# 创建环境变量
cd /opt/edu-platform
cp .env.example .env
vi .env   # 修改 SECRET_KEY、LLM_API_KEY、DOCKERHUB_REPO

# 启动
docker compose up -d
```

### 2.3 验证

```bash
# 查看状态
docker compose ps

# 健康检查
curl http://localhost:8080/api/v1/health

# 查看日志
docker compose logs -f app
```

访问 `http://服务器IP:8080`，使用 `admin / Admin@123456` 登录并立即修改密码。

---

## 三、生产环境配置

### 3.1 必须修改项

```env
# 1. 生成强随机密钥（必改）
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
SECRET_KEY=<生成的密钥>

# 2. 大模型 API Key（选填，不填则 AI 降级）
LLM_API_KEY=sk-xxxxxxxx

# 3. 服务端口
HOST_PORT=80
```

### 3.2 Nginx + HTTPS 反向代理

```nginx
server {
    listen 443 ssl http2;
    server_name edu.your-school.edu.cn;

    ssl_certificate     /etc/nginx/ssl/edu.crt;
    ssl_certificate_key /etc/nginx/ssl/edu.key;
    ssl_protocols       TLSv1.2 TLSv1.3;

    client_max_body_size 50m;

    location / {
        proxy_pass         http://127.0.0.1:8080;
        proxy_set_header   Host              $host;
        proxy_set_header   X-Real-IP         $remote_addr;
        proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
    }
}

server {
    listen 80;
    server_name edu.your-school.edu.cn;
    return 301 https://$host$request_uri;
}
```

> 应用已内置 Nginx 处理静态资源与 API 转发，外层 Nginx 仅负责 HTTPS 终止。若不需要独立域名，可直接使用容器暴露的 8080 端口。

---

## 四、数据备份与恢复

### 4.1 需要备份的内容

```
data/
├── edu_platform.db      # SQLite 主库（业务数据，最重要）
├── uploads/             # 用户上传附件（证明材料、导出文件）
├── chroma/              # 向量索引（可重建，非必须）
└── logs/                # 日志文件
```

### 4.2 备份脚本

```bash
#!/bin/bash
# /opt/edu-platform/backup.sh
BACKUP_DIR=/opt/backup/edu-platform
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p "$BACKUP_DIR"

# SQLite 在线备份（不中断服务）
sqlite3 /opt/edu-platform/data/edu_platform.db \
  ".backup '$BACKUP_DIR/db_$DATE.sqlite'"

# 附件打包
tar -czf "$BACKUP_DIR/uploads_$DATE.tar.gz" -C /opt/edu-platform/data uploads

# 保留最近 30 天
find "$BACKUP_DIR" -type f -mtime +30 -delete

echo "备份完成：$DATE"
```

```bash
chmod +x backup.sh

# 每天凌晨 2 点自动备份
crontab -e
# 加入：
0 2 * * * /opt/edu-platform/backup.sh >> /var/log/edu-backup.log 2>&1
```

### 4.3 恢复

```bash
docker compose down
cp $BACKUP_DIR/db_20260114_020000.sqlite /opt/edu-platform/data/edu_platform.db
tar -xzf $BACKUP_DIR/uploads_20260114_020000.tar.gz -C /opt/edu-platform/data
docker compose up -d
```

---

## 五、升级

```bash
cd /opt/edu-platform

# 备份（升级前必做）
./backup.sh

# 拉取新镜像并重建
docker compose pull
docker compose up -d --build

# 确认健康
curl http://localhost:8080/api/v1/health
```

> 数据库表结构在应用启动时自动同步（`create_all`），新增字段无损升级。涉及字段变更时建议先在测试环境验证。

---

## 六、数据库切换到 PostgreSQL

适用于数据量增长或需要更高并发的场景。

```env
DATABASE_URL=postgresql+psycopg2://edu_user:密码@localhost:5432/edu_platform
```

```bash
# 安装并初始化 PostgreSQL
apt-get install -y postgresql
su - postgres -c "createuser -s edu_user"
su - postgres -c "psql -c \"ALTER USER edu_user WITH PASSWORD '密码';\""
su - postgres -c "createdb -O edu_user edu_platform"

# 重启应用，表结构自动创建
docker compose restart app
```

---

## 七、监控与运维

### 7.1 内置运维能力

| 能力 | 位置 |
|------|------|
| 登录日志 / 操作日志 / 错误日志 | 管理后台 → 日志审计 |
| 定时任务状态与执行记录 | 管理后台 → 定时任务 |
| 系统运行报表（AI 调用、错误率） | 管理后台 → 系统报表 |
| 附件管理 | 管理后台 → 附件管理 |

### 7.2 日志查看

```bash
docker compose logs -f app              # 实时日志
docker exec edu-platform tail -f /app/data/logs/app_$(date +%F).log
```

### 7.3 磁盘监控

向量库与附件会持续增长，建议：

```bash
# 定期清理临时附件（系统已内置每日 4 点自动清理任务）
docker exec edu-platform ls -lh /app/data/chroma
du -sh /opt/edu-platform/data/*
```

---

## 八、常见问题

**Q: 启动后访问显示 502？**
A: 后端尚未就绪。查看 `docker compose logs app`，首次启动需要初始化数据库与依赖，通常 30 秒内完成。

**Q: AI 功能提示"规则引擎降级"？**
A: 未配置 `LLM_API_KEY`。这是正常降级行为，不影响出题、判分、错题本等核心功能。配置后重启即可启用完整 AI 能力。

**Q: 图片验证码不显示？**
A: 确认 Pillow 依赖正常：`docker exec edu-platform python -c "import PIL; print(PIL.__version__)"`。

**Q: 500 人考试提交很慢？**
A: 检查服务器 IO 与日志。SQLite 已开启 WAL 模式；如仍不足，切换 PostgreSQL。

**Q: 如何修改默认管理员密码？**
A: 登录后在「个人中心 → 修改密码」修改，或由其他管理员在用户管理中重置。

**Q: 学生数据是否会出域？**
A: 使用 `LLM_PROVIDER=ollama` + 本地大模型时，全部数据在本机处理，不出域。调用公有云大模型时，建议先做数据脱敏。

---

## 九、安全建议

1. **立即修改** `SECRET_KEY` 与所有默认账号密码
2. 启用 HTTPS，关闭 8080 端口的外网访问
3. `.env` 文件权限设为 `chmod 600 .env`
4. 定期检查操作日志，留存审计追溯记录
5. 敏感数据（学生身份信息）加密存储在受限卷中
6. 定期更新镜像：`docker compose pull && docker compose up -d`
