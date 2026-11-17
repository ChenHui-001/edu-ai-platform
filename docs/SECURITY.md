# 凭据与敏感数据规范

## 禁止事项

- 禁止把生产口令、API Key、SSH 私钥写入源码、README、测试脚本、日志或命令行参数。
- 禁止把完整 SQLite 备份放进源码仓库或普通工作区。
- 禁止用 `git add -f` 绕过 `.gitignore` 提交 `.env`、备份或凭据文件。

## 注入方式

| 变量 | 用途 |
|---|---|
| `SECRET_KEY` | JWT 签名密钥，生产至少 32 位随机值 |
| `LLM_API_KEY` | 大模型密钥，未配置时自动降级规则引擎 |
| `DEPLOY_PASS` | 运维 SSH 口令（仅运维脚本使用） |
| `DEPLOY_KEY` | 部署私钥路径；未设置时依次尝试 `~/.ssh/id_ed25519`、`~/.ssh/id_rsa` |
| `ADMIN_PASS` | `seed_prod_data.py` 管理员口令 |
| `SEED_TEACHER_PASS` / `SEED_STUDENT_PASS` | 演示数据口令 |

CI/本地测试使用临时库与临时密钥；生产 `.env` 必须由部署环境注入，不得提交。

## 门禁

`tools/check_plaintext_secrets.py` 会扫描生产形态口令、长 API Key、私钥头和
`deploy_scripts/.deploy_pass`。命中只输出位置，不回显内容。

## 泄露后

按 `deploy_scripts/SECURITY.md` 的轮换清单执行。删除文本不是修复；必须轮换凭据，
并检查日志、备份、聊天记录与镜像层是否仍含旧值。
