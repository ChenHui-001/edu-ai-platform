# 项目现状卡（STATUS）

> **这是唯一声明"当前状态"的文档。** 其他文档里的版本号/端点数/表数若与本卡冲突，
> 一律以本卡 + 代码为准；历史文档已移入 [`archive/`](archive/)。
>
> 缺陷与改进的进度查 [`../audit-reports/BACKLOG.md`](../audit-reports/BACKLOG.md)，
> 不要另开报告。

## 一、实测数字

<!-- status:auto:begin -->
| 项 | 实测值 | 口径 |
|---|---:|---|
| 版本 | 2.5.46 | `VERSION` 文件 |
| 路由数 | 323 | `app.routes` |
| 数据表数 | 58 | `Base.metadata.tables` |
| 后端用例 | 74 | `pytest backend/qa_audit_suite.py --collect-only` |
| 前端用例 | 160 | `frontend/src/**/__tests__` 内 `it(` 计数 |
| 接口断言 | 117 | `tools/verify_p0_fixes.py` 实际通过条数 |
| 补列迁移 | 39 | `core/db_migrations._COLUMNS` |
| 发版门禁 | 23 | `tools/auto_ship.sh` 引用的 check_*/scan_vue_* 数 |

> 由 `python tools/status_snapshot.py --write` 生成。版本号另由 `tools/check_doc_versions.py` 门禁强制与 `VERSION` 一致。
<!-- status:auto:end -->

刷新：`python tools/status_snapshot.py --write`（只重写上面这块）。

## 二、运行时形态

| 项 | 值 | 为什么不能随便改 |
|---|---|---|
| 部署 | 单容器单镜像（Dockerfile `unified` 阶段），nginx + supervisord | 镜像即交付物，服务器只换镜像不动文件 |
| 后端 | FastAPI + SQLAlchemy 2.0（**同步** ORM）+ uvicorn `--workers 1` | 单写者假设贯穿限流/缓存/调度，改多 worker 需先看 `BACKLOG` P1-15 |
| 数据库 | SQLite WAL（`busy_timeout=5000`、`foreign_keys=ON`） | 数据库与日志必须在**命名卷**上，9p 绑定挂载只能建首个连接 |
| 前端 | Vue 3 + Vite + Element Plus（unplugin 按需） | 图表统一走 `utils/echarts.js` 按需注册，禁止全量引入 |
| 迁移 | Alembic 基线 `0001_baseline` + 存量库幂等补列 + `align_schema.py` 漂移对齐 | 新变更走 `alembic revision`；补列清单由 `check_migration_columns` 守，迁移链由 `check_alembic_sync` 守 |
| 生产 | `186.241.77.194:8081`，容器 `edu-platform`，数据 `/opt/edu-ai-platform/{data,logs}` | 勿动 Caddy(80/5010)、8080、gostc(7500+) |

## 三、四层一致性

发版后必须四层同指纹（版本 + 前 7 位 commit）：

```
本地 worktree  ==  origin/master  ==  镜像 BUILD_INFO  ==  服务器容器 BUILD_INFO
```

一条命令核对：`python tools/check_four_layer.py`。
服务器落后时只走 `python tools/deploy_release.py --yes`（备份 + 健康门禁 + 回滚）。

## 四、契约文档索引

改这些域之前先读对应文档，改完同步更新：

| 域 | 文档 |
|---|---|
| 试卷 V2（统计/批量/AI/版本/共享） | [`PAPER_V2.md`](PAPER_V2.md) |
| 题库 V2 | [`QUESTION_BANK_V2.md`](QUESTION_BANK_V2.md) |
| 知识点 V2（含 RAG） | [`KNOWLEDGE_V2.md`](KNOWLEDGE_V2.md) · [`KNOWLEDGE_V2_RAG_AI.md`](KNOWLEDGE_V2_RAG_AI.md) |
| 教学 V2（作业/考试/批改） | [`TEACHING_V2.md`](TEACHING_V2.md) |
| 教案 AI | [`AI_LESSON_PLAN.md`](AI_LESSON_PLAN.md) |
| 补弱计划、班级图谱、数学渲染、题库质检、分步答疑与上游同步 | [`LEARNING_EXTENSIONS.md`](LEARNING_EXTENSIONS.md) |
| 卷面结构规范 | [`EXAM_STRUCTURE_SPEC_JUNIOR.md`](EXAM_STRUCTURE_SPEC_JUNIOR.md) · [`EXAM_STRUCTURE_SPEC_PRIMARY.md`](EXAM_STRUCTURE_SPEC_PRIMARY.md) |
| 交付与发版 | [`DELIVERY_RULES.md`](DELIVERY_RULES.md) · [`RELEASE_CONSISTENCY.md`](RELEASE_CONSISTENCY.md) |
| 开发与部署 | [`DEVELOPMENT.md`](DEVELOPMENT.md) · [`DEPLOYMENT.md`](DEPLOYMENT.md) · [`QUICKSTART.md`](QUICKSTART.md) |

## 五、当前缺口（只列方向，明细在 BACKLOG）

- **功能扩展**：F-05 导出异步化 / F-06 AI 预算按 `biz_type` 细化 / F-07 通知订阅偏好
  均已完成，详见 [`../audit-reports/BACKLOG.md`](../audit-reports/BACKLOG.md)。
- **交互**：U-03 降级提示条统一（一律 `el-alert`，勿复活 `.fallback-tip`）/ U-04 导出按钮组件化 / U-05 页面级错误重试。
- **结构**：Q-05 `paper_compose.py` 已从 3000+ 行拆到约 1400 行，继续按域下沉；
  Q-06 Alembic 已引入 `0001_baseline`，生产已 `stamp` 且 `alembic check` 干净。
  13 个存量超长文件已纳入 `check_file_size.py` 的**只降不升**预算，新增文件硬顶 1200 行；
  只读性能基线由 `tools/load_test.py` 提供（临时库，不压生产）。
- **数据**：通过题库质量工作台查看缺项和题量缺口，通过上游同步补齐数学资料；其他学科仍需运营补题，准确数量以运行库查询为准。
