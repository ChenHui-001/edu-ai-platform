# 开发指南

面向参与本项目二次开发的工程师。

---

## 一、本地环境搭建

### 1. 后端

```bash
cd backend

# Python 3.11+
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# 按需修改 .env

# 启动（热重载）
uvicorn app.main:app --reload --port 8000
```

启动后：
- 接口文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/api/v1/health

首次启动会自动完成：建表 → 初始化 5 种角色与权限点 → 创建 9 个年级及学科 → 创建默认管理员 → 注册 5 个默认定时任务 → 生成演示数据。

### 2. 前端

```bash
cd frontend
npm install
npm run dev
```

访问 http://localhost:5173，接口已通过 Vite 代理到 `localhost:8000`。

生产构建：`npm run build`，产物在 `frontend/dist`。

---

## 二、目录职责

### 后端分层

```
backend/app/
├── core/            基础设施层（不依赖业务）
│   ├── config.py    Pydantic Settings，全部配置来自环境变量
│   ├── database.py  引擎、会话、Base 声明
│   ├── security.py  密码哈希、JWT、验证码
│   ├── exception.py 统一异常与错误码
│   └── logger.py    Loguru 配置与审计辅助
│
├── models/          ORM 模型（对应数据库表）
├── schemas/         Pydantic 出入参模型
├── api/
│   ├── deps.py      依赖注入：认证、权限、数据范围
│   └── v1/          路由，按业务域拆分
│
├── services/        业务逻辑层
│   ├── auth_service.py     注册审批、登录、异常检测
│   ├── grading_service.py  判分、错题收录、掌握度更新
│   ├── scheduler.py        APScheduler 管理
│   ├── task_jobs.py        定时任务实现
│   └── init_db.py          种子数据
│
├── agents/          AI Agent 层
│   ├── base.py      BaseAgent 基类 + LangGraph 编排器
│   ├── llm.py       大模型接入（多厂商兼容 + 降级）
│   ├── rag.py       ChromaDB 检索 + SQL 降级
│   ├── question_agent.py / paper_agent.py / grading_agent.py
│   └── study_agent.py / tutor_agent.py / note_agent.py
│
└── middleware/audit.py  操作日志审计
```

**分层原则**：路由层只做参数校验与调用编排，不写业务逻辑；业务逻辑放 `services/`；AI 能力放 `agents/`，Agent 不直接依赖路由层。

---

## 三、开发一个 AI Agent

继承 `BaseAgent`，实现 `execute` 与可选的 `fallback`：

```python
from app.agents.base import BaseAgent

class MyAgent(BaseAgent):
    name = "my_agent"
    display_name = "我的智能体"
    description = "功能说明"
    system_prompt = """你是一个...只输出 JSON：{"result": "..."}"""

    def execute(self, db, user_id=None, **kwargs):
        result = self.call_llm(
            f"用户输入：{kwargs.get('query')}",
            db=db, user_id=user_id,
            biz_type="my_agent",
        )
        if not result["success"]:
            return {}   # 走 fallback
        return result.get("parsed") or {}

    def fallback(self, db, **kwargs):
        return {"result": "规则引擎兜底结果"}
```

然后在 `base.py` 的 `load_agents()` 中注册即可被路由 Agent 调度。

**约定**：
- `execute` 必须处理 `user_id=None` 的情况（定时任务无用户上下文）
- `fallback` 保证无 LLM 时功能可用，不要抛异常
- 所有 LLM 调用经 `call_llm`，会自动记录 Agent 调用日志

---

## 四、新增业务接口

### 路由文件分布

`api/v1/` 下按业务域拆分，新增接口请放进对应文件，不要往已有大文件里堆：

| 文件 | 负责范围 | 前缀 |
|------|---------|------|
| `grading.py` | 智能批改中心 | `/grading` |
| `learning/notes.py` | 学习笔记 | `/learning` |
| `learning/wrongbook.py` | 错题本 | `/learning` |
| `learning/review.py` | 智能复习 + 随机练习 | `/learning` |
| `learning/tools.py` | 收藏 / 自主组卷 / 学习目标 / 路径 / 闪卡 | `/learning` |
| `question.py` | 题库与试卷 | `/question` |
| `task.py` | 作业与考试 | `/task` |
| `system.py` | 用户 / 角色 / 通知 / 配置 | `/system` |
| `edu.py` | 学科 / 年级 / 班级 / 知识点 | `/edu` |
| `report.py` | 各类统计报表 | `/report` |
| `agent.py` | AI Agent 对话与生成 | `/agent` |

`learning/` 是子包，各子模块导出 `router = APIRouter()`（不带前缀），
由 `learning/__init__.py` 统一 `include_router` 到 `learning_router`。

> **include 顺序敏感**：`/learning/__init__.py` 中的 include 顺序不可随意调整。
> 静态路由必须早于同前缀参数路由注册，否则被抢先匹配返回 422
> （例：`/practice/history` 需在 `/practice/{task_id}` 之前）。

### 开发步骤

1. 在 `models/` 定义 ORM 模型（继承 `Base`）
2. 在 `api/v1/` 对应文件加路由
3. 权限控制在路由依赖上声明：

```python
@router.post("/xxx", summary="功能说明")
def create_xxx(
    data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_teacher),          # 角色校验
    scope: DataScope = Depends(get_data_scope),         # 数据权限
):
    if not scope.is_super:
        allowed = scope.class_ids()                      # 数据隔离
        if allowed is not None and data["class_id"] not in allowed:
            raise BusinessException("无权操作该班级数据")
    ...
```

4. 在 `init_db.py` 补充权限点（若需要按钮级控制）
5. 前端在 `router/index.js` 加路由，meta 里声明 `roles` 或 `perm`

---

## 五、权限体系扩展

### 新增权限点
在 `init_db.py` 的 `PERMISSIONS` 列表添加，然后在对应角色的 `perms` 中引用权限编码。

### 数据权限范围
`DataScope` 类提供三种范围，由角色的 `data_scope` 字段决定：

| scope | 范围 | 实现 |
|-------|------|------|
| `all` | 全校全部数据 | 返回 `None`（不限制） |
| `grade` | 本年级数据 | 年级管理员 |
| `taught_class` | 授课班级 | 教师，查 `TeachingAssignment` |
| `self` | 仅本人 | 学生 |
| `none` | 无业务数据 | 访客 |

---

## 六、代码规范

- **命名**：模块/函数 `snake_case`，类 `PascalCase`，常量 `UPPER_CASE`
- **注释**：中文注释，解释「为什么」而非「做了什么」
- **类型标注**：函数签名尽量完整标注
- **错误处理**：业务异常抛 `AppException` 子类，不要裸 `raise Exception`
- **日志**：用 `get_logger(__name__)` 获取 logger，不用 `print`
- **SQL**：用 SQLAlchemy 2.0 风格（`select()` + `db.scalars()`），不用旧版 `query()`

---

## 七、测试

```bash
# 健康检查冒烟测试
curl http://localhost:8000/api/v1/health

# 登录流程
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"Admin@123456"}'

# AI 引擎状态
curl http://localhost:8000/api/v1/agent/status \
  -H "Authorization: Bearer <token>"
```

接口文档 `/docs` 提供了所有接口的在线调试能力。

---

## 八、常见开发问题

**Q: ChromaDB 报错导致启动失败？**
A: 不会。`rag.py` 捕获异常后自动降级为 SQL LIKE 检索，日志会有警告但不影响启动。

**Q: LangGraph 没装会怎样？**
A: `Orchestrator` 检测后降级为顺序编排，`orchestrator_mode` 字段显示为 `sequential`，功能不变。

**Q: 改了模型但表没变？**
A: 分三种情况。**新库/测试库**：`Base.metadata.create_all` 只建缺失的表，已存在的表不加列，
开发期可直接删 `data/edu_platform.db` 重建（丢数据）。**存量库/生产的新变更**：必须
生成 Alembic 迁移（见第九节）。**存量库的历史漂移**（列可空性/外键/索引/类型与模型不一致）：
跑 `tools/align_schema.py`（见第九节末），`MIGRATION_COLUMNS` 那条路只会加列，
补不了 NOT NULL、外键和索引。

**Q: 定时任务没执行？**
A: 检查 `GET /api/v1/jobs/status` 确认调度器 running，并核对 Cron 表达式格式（分 时 日 月 周）。

---

## 九、结构变更与迁移（Alembic）

结构演进有三套机制，**新变更一律走 Alembic**：

| 机制 | 作用 | 边界 |
|------|------|------|
| `migrations/versions/*.py`（Alembic） | 有版本号、可回退的真实迁移 | 改类型/删列/建索引 |
| `db_migrations.MIGRATION_COLUMNS` | 启动时对存量库幂等补列 | **只会加列**，老库追平用 |
| `tools/align_schema.py` | 把存量库结构**整体**对齐到模型 | 一次性/运维用，不是发版流程 |

### 三条命令

```bash
cd backend

# 1) 空库建到最新结构（等价于 create_all，但带 alembic_version 记录）
ALEMBIC_DB_URL="sqlite:///./data/edu_platform.db" python -m alembic upgrade head

# 2) 存量库认领基线（只在引入 Alembic 时做一次；生产库必须先 stamp 再 upgrade）
python -m alembic stamp 0001_baseline

# 3) 改了模型 → 生成迁移，然后**读一遍** up/downgrade
python -m alembic revision --autogenerate -m "add xxx_column to edu_question"
```

生成后必须跑一次守卫，它会用临时库把迁移真的执行一遍：

```bash
python tools/check_alembic_sync.py    # 0=通过；也在 auto_ship 与 CI 里
```

### 三个坑（都是踩过的）

1. **`backend/alembic.ini` 必须保持纯 ASCII。** alembic 用
   `configparser.read(..., encoding="locale")` 读它，中文注释在 GBK 环境的
   Windows 上会让**所有** alembic 命令直接 `UnicodeDecodeError: 'gbk' codec can't
   decode byte 0x80`。中文说明写在 `migrations/env.py`（.py 文件不受影响）。
2. **`migrations/env.py` 里的 `import app.models` 不能删。** 少了它
   `Base.metadata` 是空壳，`--autogenerate` 会生成一个「删掉所有表」的迁移。
3. **SQLite 必须用 batch 模式**（env.py 已设 `render_as_batch=True`）。
   SQLite 不支持 `ALTER COLUMN`，非 batch 生成的迁移在本地和 CI 都会直接报错。

`autogenerate` 对「改列类型」「删索引」「重命名列」猜不准（重命名会被识别成
删+加，数据丢失），这几类要手工改 up/downgrade 再跑守卫确认。

### 存量库结构漂移：`tools/align_schema.py`

`MIGRATION_COLUMNS` 用 `ALTER TABLE ADD COLUMN` 追平老库，而 SQLite 的 ADD COLUMN
**只能加「可空或带默认值」的列** —— 补不了 NOT NULL、补不了 FOREIGN KEY、补不了索引、
也改不了类型。长期滚下来的库于是和模型「差一口气」，而 `create_all` 对此完全无能为力。

实测（2026-11）生产库有 4 张表漂移，都是这条路径留下的：

| 表 | 漂移 |
| --- | --- |
| `edu_paper` | 缺 5 个索引；缺 `review_by → sys_user.id` 外键；`status`/`share_scope`/`current_version` 可空；`difficulty_ratio` 仍是 `VARCHAR(64)` |
| `edu_paper_item` | 缺 `section_code` 索引；`section_sort` 可空 |
| `edu_paper_share` | 缺 `uq_paper_share_target` 唯一约束；`permission` 可空 |
| `sys_agent_job` | `cancel_requested` 可空 |

**这不是风格问题**：可空性不一致意味着 `paper.status is None` 之类的判定会踩空；
缺索引意味着试卷列表按 `status`/`exam_type` 过滤走全表扫描；缺外键意味着删用户后
`review_by` 指向不存在的 id。

修法**不是** autogenerate —— 基线已经 stamp 过的库，剩下的差异是「历史遗留」而不是
「新变更」，autogenerate 只会吐出一堆含义不明的操作。用对齐工具：

```bash
python tools/align_schema.py                 # 只看差异（默认 dry-run）
python tools/align_schema.py --apply --yes --drop-extra-indexes
```

- 判定复用 `alembic.autogenerate.compare_metadata()` —— 和守卫同源，保证「工具说齐了」
  与「`alembic check` 说齐了」是同一件事。
- 修复是 SQLite 唯一可行的方式：**按元数据重建表**（建 `_<表>__align` → 拷数据 →
  删旧表 → 改名 → 按元数据建索引）。全程单事务，行数不一致或重建表出现孤儿外键就
  整体 `ROLLBACK`，执行前自动用 sqlite backup API 备份到数据目录。
- 默认**拒绝删**「库里多出来的列/表/约束」（那是数据丢失），只报告；索引是纯派生物，
  要显式 `--drop-extra-indexes` 才删。

对齐后生产库才真正「认得自己是谁」：

```bash
cd backend && python -m alembic stamp 0001_baseline     # 首次接入时
python -m alembic check                                 # 必须输出 No new upgrade operations detected
```

⚠️ **不要再手工写 `CREATE INDEX` 兜底**。`run_knowledge_v2_migration` 里曾建过一个
`ux_kp_subject_code` 部分唯一索引，与模型 `uq_kp_subject_code` UNIQUE 约束完全重复
（SQLite 唯一索引本就把多个 NULL 视为互不相同），结果 `alembic check` 永久报一个
`remove_index`。结构对齐只认模型，DDL 不写在迁移脚本以外的业务代码里。
