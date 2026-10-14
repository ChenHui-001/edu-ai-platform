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
A: 启动时执行 `Base.metadata.create_all`，只新增不修改已有表。开发期可删除 `data/edu_platform.db` 重建（会丢数据）。

**Q: 定时任务没执行？**
A: 检查 `GET /api/v1/jobs/status` 确认调度器 running，并核对 Cron 表达式格式（分 时 日 月 周）。
