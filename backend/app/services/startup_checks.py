"""启动后置校验：把「配置错了但不会报错」的隐患显式喊出来。

## 为什么必须有这一层

本项目的失效模式大量是**静默降级**而不是崩溃（见各处的 fallback 分支）：
LLM 密钥没配 → AI 功能退回题库复用；演示数据开关默认开启 → 生产库出现
已知口令账号；V2 迁移标记缺失 → 库停在半迁移状态。这些都不影响启动，
所以注释里写了也没人看得见 —— 唯一的暴露渠道是启动日志。

## 三条硬约束

1. **只观测，不修复、不 raise、不阻断启动。** 任一检查内部抛异常都必须
   被吞掉并降级为一条 warning，绝不能让启动失败。理由同
   `init_db._log_admin_default_password` 的 docstring：观测手段不能成为
   故障原因。

2. **不重复写 ErrorLog。** 「默认口令管理员」这条已经由
   `init_db._log_admin_default_password` 用固定 `module+path` 做了幂等 upsert
   （`path="/startup/enforce_default_admin_password"`）。本模块**不写**
   这一条，否则同一个问题在后台错误日志页出现两次。
   本模块**会写**的只有演示数据泄露那一条（`path="/startup/demo_data_enabled"`），
   因为它是独立的、更严重的问题（16 个**可登录**的已知口令账号 vs 1 个），
   而 `init_db` 不覆盖它。同样用固定 `module+path` 幂等，不会堆。

3. **每项检查的日志消息必须自带"怎么修"**。只说「知识库覆盖率为 0」对运维
   没有价值，必须说清改哪个环境变量 / 调哪个接口。

## 为什么不做「知识点覆盖率统计」

这是个诱人但错误的检查项：要 join 59 个学科 × 1354 个 level2 节点，是全表
聚合，每次启动跑一遍纯属浪费。更关键的是「覆盖率低」是**已知的长期现状**
（59 学科中 42 个无知识点），每次都报等于训练运维忽略告警。这类「已知且
不会立刻变」的问题应该进管理端看板，不是启动日志。

## 为什么检查 1 需要 `APP_ENV` 而不只是 `DEBUG`

判据本来可以只是 `SEED_DEMO_DATA and not DEBUG`——本地开发该有演示数据
（DEBUG=true），生产不该有（DEBUG=false）。但 **e2e 和 CI 也是 DEBUG=false
且 SEED_DEMO_DATA=true**（99 处 `.login()` 全用 `teacher1`/`stu731` 这类
演示账号，关掉就全线红）。若不区分，「每次 CI 都报一条 error 并在测试库写
一条 ErrorLog」，运维会对这条告警脱敏 —— 那比不告警更坏。

`DEBUG` 不能用来区分（e2e 服务端就是 DEBUG=false，而设成 true 会打开
`/docs` 并触发临时 SECRET_KEY 生成，副作用太大）。可用的硬信号只有显式
环境变量，故引入 `APP_ENV`：

    APP_ENV=production（默认，保守）  → 告警生效
    APP_ENV=test                      → e2e/CI，不告警
    APP_ENV=dev                       → 本地，不告警

默认 `production` 是**刻意保守**：现有部署都没有这一项，它们必须先看到告警
（确认自己确实在生产），而不是默默被豁免。
"""
from typing import Optional

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logger import get_logger
from app.utils.common import now_local

logger = get_logger("startup_checks")

# 检查 1 的 ErrorLog 幂等键。与 init_db 的 `/startup/enforce_default_admin_password`
# 并列但**不同 key** —— 两条是不同问题，各自幂等。
_DEMO_ERR_MODULE = "startup_checks"
_DEMO_ERR_PATH = "/startup/demo_data_enabled"

# V2 迁移标记的键名必须与 core/db_migrations.py 保持一致。
# 那两处是模块私有常量（`_KNOWLEDGE_V2_MARKER` / `_QUESTION_V2_MARKER`），
# 这里重新声明而不是导入：导入私有常量会让 db_migrations 的重命名/重构
# 直接打断启动校验（而校验本应 fail-soft），且私有名本就不该跨模块引用。
# 若 db_migrations 改了键名，本处必须同步 —— 由
# tests/test_unit_startup_checks.py 的守卫断言盯住（它断言这两个键在
# 当前 db_migrations.py 里确实作为标记常量存在）。
V2_MARKERS = ("knowledge_v2_migrated", "question_bank_v2_migrated")


def _is_production() -> bool:
    """当前进程是否应当按「生产」对待。

    默认 production 是保守选择：所有现有部署（含 docker compose 模板）
    都没有 `APP_ENV`，必须让它们先看到告警。
    """
    return (getattr(settings, "APP_ENV", "production") or "production").lower() == "production"


def _check_demo_data(db: Session) -> Optional[str]:
    """演示数据开关在生产开着 → 库里有已知口令账号。

    为什么这是最高优先级而不是提示：`init_demo_data` 会创建
    teacher1..4 / stu{年级}{班}{序} 共 16 个账号，口令硬编码为
    `Teacher@123` / `Student@123`，全部写在 README 里。这些是**真实可登录**
    的 teacher/student 账号 —— 不是演示占位符，能看班级、能提交作业。

    只在「生产形态」时告警：本地开发就该有演示数据，本地告警等于噪音
    （与 `_log_admin_default_password` 的 DEBUG 分级同一取向）。
    """
    if not settings.SEED_DEMO_DATA:
        return None
    # 双重判据：DEBUG=true 无论 APP_ENV 是什么都不报（本地开发）；
    # APP_ENV != production 也不报（e2e/CI 需要演示账号登录）。
    if settings.DEBUG or not _is_production():
        return None
    return (
        "当前以生产形态运行（DEBUG=false, APP_ENV=production）但 "
        f"SEED_DEMO_DATA={settings.SEED_DEMO_DATA} —— 空库初始化时会创建 "
        "teacher1..4（口令 Teacher@123）与 12 名学生（口令 Student@123），"
        "这些口令写在 README 里、是公开的，且是真实可登录的账号。"
        "修复：在 .env 设置 SEED_DEMO_DATA=false 并重启；"
        "已创建的账号请用管理端 /system/users 停用或改密。"
    )


def _check_llm_config(db: Session) -> Optional[str]:
    """LLM_ENABLED=true 但拿不到有效密钥 → AI 功能已静默降级。

    为什么不用 `settings.LLM_API_KEY` 判断：DB 里的 sys_config 优先于 .env
    （见 `agents/llm._get_db_value` 与 `/health` 的注释），管理员可能在后台
    填过密钥。必须走 `is_available()` 才是真实状态 —— 它同时考虑了
    DB 覆盖值与鉴权熔断（401/403 后持久标记为不可用）。

    不做 import 期的顶层导入：AI 模块会拉起 chroma / httpx 等重依赖，
    启动校验不该因此变慢或失败（同 `main.py` 的 /health 写法）。
    """
    if not getattr(settings, "LLM_ENABLED", False):
        return None
    try:
        from app.agents.llm import is_available

        if is_available():
            return None
    except Exception as exc:  # noqa: BLE001 AI 模块故障不能变成启动校验的故障
        return (
            f"LLM_ENABLED=true 但探测 LLM 可用性时异常：{exc}。"
            "请检查 LLM_PROVIDER / LLM_API_KEY / 网络连通性；"
            "在此之前所有 AI 功能会退回规则引擎。"
        )
    return (
        "LLM_ENABLED=true 但当前拿不到有效密钥（或鉴权已熔断），"
        "所有 AI 功能正在**静默降级**为规则引擎/题库复用。"
        "修复：配置 LLM_API_KEY（.env 或管理端 AI 设置页），"
        "或设 LLM_ENABLED=false 明确接受降级（这样 /health 会如实报 false）。"
    )


def _check_migration_markers(db: Session) -> Optional[str]:
    """V2 迁移标记缺失 → 库处于半迁移状态。

    正常情况下 A1 的启动锁保证迁移单点执行且一定会写标记；标记缺失意味着
    迁移被跳过过（如手工删过 sys_config、或从更老的库直接拷贝）。知识点树 /
    题库结构与代码预期不一致时，AI 出题与掌握度地图会大面积失效，
    但接口全部返回 200 —— 正是本模块要抓的那类静默故障。

    读不到 sys_config 表本身（如空库还没建表）时返回 None 而不是报错：
    create_all 在启动锁内先于本函数执行，理论上表一定存在；但如果顺序被
    改动，这不该变成一条噪音告警。
    """
    try:
        # 用 SQLAlchemy 的 expanding bindparam 处理 IN 列表，避免字符串拼接。
        from sqlalchemy import bindparam

        stmt = text("SELECT key FROM sys_config WHERE key IN :keys").bindparams(
            bindparam("keys", expanding=True)
        )
        rows = db.execute(stmt, {"keys": list(V2_MARKERS)}).all()
    except Exception:
        # 表不存在 / 查询语法差异：交给外层 try 降级为 warning。
        raise
    present = {r[0] for r in rows}
    missing = [m for m in V2_MARKERS if m not in present]
    if not missing:
        return None
    return (
        f"V2 迁移标记缺失：{', '.join(missing)}。"
        "库可能处于「半迁移」状态：知识点树/题库结构与代码预期不一致时，"
        "AI 出题与掌握度地图会大面积失效但接口仍返回 200。"
        "修复：确认 data/ 下的库是从哪个版本升级来的；"
        "若是旧库请从空库重建（run_knowledge_v2_migration / "
        "run_question_v2_migration 是破坏性 DELETE，只应在升级时执行一次）。"
    )


def _upsert_demo_error_log(db: Session, message: str) -> None:
    """把演示数据泄露写进后台错误日志，同 module+path 幂等。

    与 `init_db._upsert_error_log` 同一个套路：固定 path 作逻辑主键，
    重启 N 次只留最新一条，不会把「错误日志」页刷爆。
    独立实现而不复用 init_db 的那个，是因为后者是模块私有函数且带
    `level` 参数语义耦合；这两处各自幂等、互不影响更安全。
    """
    from app.models import ErrorLog

    row = db.scalar(
        select(ErrorLog)
        .where(ErrorLog.module == _DEMO_ERR_MODULE, ErrorLog.path == _DEMO_ERR_PATH)
        .order_by(ErrorLog.id.desc())
    )
    if row is None:
        db.add(ErrorLog(level="ERROR", module=_DEMO_ERR_MODULE,
                        path=_DEMO_ERR_PATH, message=message))
    else:
        row.level = "ERROR"
        row.message = message
        row.created_at = now_local()
    db.commit()


def run_startup_checks(db: Session) -> int:
    """逐项检查，返回发现问题数。任一项内部异常都降级为 warning，不抛出。

    Args:
        db: 调用方提供的 session（`main.lifespan` 里新建、校验后 close）。

    Returns:
        发现的问题数（0 = 全部正常）。调用方可以忽略返回值 —— 本函数
        **不改变启动行为**，返回计数只为测试可断言。
    """
    checks = (
        ("演示数据", _check_demo_data),
        ("LLM 配置", _check_llm_config),
        ("V2 迁移标记", _check_migration_markers),
    )
    found = 0
    for name, fn in checks:
        try:
            problem = fn(db)
        except Exception as exc:  # noqa: BLE001 校验失败绝不能阻断启动
            logger.warning(f"启动校验「{name}」执行失败（已跳过该项）: {exc}")
            continue
        if not problem:
            continue
        found += 1
        # 用 error 而不是 warning：这些是真错，不是提示。
        logger.error(f"启动校验「{name}」：{problem}")

        # 只有演示数据这一项落库（理由见模块 docstring 约束 2）。
        if fn is _check_demo_data:
            try:
                _upsert_demo_error_log(db, problem)
            except Exception as exc:  # noqa: BLE001 落库失败不能连累启动
                logger.warning(f"启动校验「{name}」结果落库失败（已降级为日志）: {exc}")
                # 必须 rollback：落库失败后 session 可能停在不可用状态，
                # 不收拾干净会让调用方复用这个 session 时继续报
                # PendingRollbackError —— 把局部故障放大成整个 session 报废。
                # 这与 init_db._log_admin_default_password 的处理一致。
                try:
                    db.rollback()
                except Exception:  # noqa: BLE001
                    pass

    # found=0 时也打 info：让「校验跑过了、确实没问题」这件事可被观测到。
    # 否则日志里什么都没有，运维无法区分「没问题」和「校验没执行」。
    logger.info(f"启动校验完成：{found} 项需关注")
    return found
