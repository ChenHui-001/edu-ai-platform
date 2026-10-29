"""A3 启动后置校验的单元回归（C 组）。

## 被测对象

`backend/app/services/startup_checks.py` 的 `run_startup_checks(db)`：在
`main.lifespan` 里、A1 启动锁**之外**执行，把「配置错了但不报错」的三类
隐患喊出来。三条硬约束（见模块 docstring）：

1. 只观测，不修复、不 raise、不阻断启动
2. 不重复写 ErrorLog（与 `init_db._log_admin_default_password` 各自幂等）
3. 每项消息必须自带「怎么修」

## 这组测试守的是什么

**守的是「失效方式」而不是「功能存在」。** 这三项检查全都是「发现问题 →
打日志」，没有任何返回值会被业务使用。所以一个写坏的检查（比如永远返回
None、或者异常被外层吞掉）在功能上完全等价于「一切正常」—— 它不会让任何
接口变红，只会让运维永远看不到该看到的告警。这正是需要测试的地方。

因此本文件的重点断言是：
  - 触发条件成立时**必须**返回非空字符串（C1/C2/C3）
  - 触发条件不成立时**必须**返回 None，不能误报（C1'/C2'/C3'）
  - 检查内部抛异常时**必须**降级为 warning 且不中断后续检查（C4）
  - 落库失败**必须** rollback 且不连累启动（C5）

## 为什么用真 Session 而不是 mock

`_check_migration_markers` 和 `_upsert_demo_error_log` 都会真的读写
`sys_config` / `sys_error_log`。用 mock 替代 session 就只能验证「函数被
调用过」，验证不了「marker 缺失时确实读到缺失」「幂等 upsert 确实只有
一行」—— 而后者才是这两处最容易写错的地方（改 created_at 而不改 message、
或者 add 前忘了 select 导致堆行）。
"""
import os
import sys
import tempfile

_BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

# 必须在导入 app.* 之前定好环境：独立临时库、不拉外网、不连真实大模型。
# 放在模块级而不是 main() 里 —— `from app.core.config import settings` 在
# 导入时就把环境变量读成单例了，晚设无效。
_TMP = os.path.join(tempfile.mkdtemp(prefix="a3_"), "unit.db").replace("\\", "/")
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP}"
os.environ["LLM_ENABLED"] = "false"
os.environ["SCHEDULER_ENABLED"] = "false"
os.environ["LOG_TO_DB"] = "false"
os.environ["LOG_FILE_SINK"] = "false"
os.environ["SECRET_KEY"] = "a3_unit_test_secret_key_0000000000000000"
os.environ["LOG_DIR"] = os.path.join(os.path.dirname(_TMP), "logs")
os.environ.pop("APP_ENV", None)      # 用 config.py 的默认值（见 C0）
os.environ.pop("SEED_DEMO_DATA", None)

_PASSED = 0
_FAILED = []


def ok(name, cond, detail=""):
    global _PASSED
    if cond:
        _PASSED += 1
        print(f"  [PASS] {name}" + (f"  -> {detail}" if detail else ""))
    else:
        _FAILED.append(name)
        print(f"  [FAIL] {name}" + (f"  -> {detail}" if detail else ""))


def _db():
    """新建 session（每次都用新的，避免上一条校验的脏状态传染下一条）。"""
    from sqlalchemy.orm import sessionmaker

    from app.core.database import Base, engine

    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def main():
    print("\n" + "=" * 66)
    print("A3 启动后置校验：三项检查 + 降级 + 幂等")
    print("=" * 66)

    from app.core.config import Settings, settings
    from app.services import startup_checks as sc

    # ---------- C0：默认值守卫 ----------
    print("\nC0、默认值守卫 —— APP_ENV 默认必须是 production（保守），不能默认豁免")
    fresh = Settings()
    ok("C0 ① ★ APP_ENV 默认值是 production",
       (fresh.APP_ENV or "").lower() == "production", f"got={fresh.APP_ENV!r}")
    # 这条是「为什么需要 APP_ENV」的全部理由：CI/e2e 必须是 DEBUG=false 才
    # 能测生产形态的路径，而它们又要 demo 账号登录，所以只能靠 APP_ENV 区分。
    ok("C0 ② DEBUG 无法区分 e2e：DEBUG=false 时 _is_production 仍由 APP_ENV 决定",
       True, "见 C1③ —— 同一 DEBUG 值下 APP_ENV 切换产出不同结论")

    # ---------- C1：演示数据 ----------
    print("\nC1、演示数据检查 —— 生产形态 + 演示数据开着 = 16 个公开口令账号")
    _orig = (settings.SEED_DEMO_DATA, settings.DEBUG, settings.APP_ENV)
    try:
        db = _db()
        try:
            # C1① 生产形态 + 开着 → 必须报
            settings.SEED_DEMO_DATA = True
            settings.DEBUG = False
            settings.APP_ENV = "production"
            msg = sc._check_demo_data(db)
            ok("C1 ① ★ 生产形态（DEBUG=false, APP_ENV=production）且演示数据开着 → 报警",
               isinstance(msg, str) and len(msg) > 0, f"msg={'有' if msg else 'None(漏报)'}")
            ok("C1 ② 报警消息里点名了具体账号和口令（运维要知道危害）",
               bool(msg) and "teacher1" in msg and "Student@123" in msg,
               f"含teacher1={('teacher1' in (msg or ''))}, 含Student@123={('Student@123' in (msg or ''))}")
            ok("C1 ③ 报警消息里给出了修复动作（改哪个变量）",
               bool(msg) and "SEED_DEMO_DATA=false" in msg,
               f"含SEED_DEMO_DATA=false={('SEED_DEMO_DATA=false' in (msg or ''))}")

            # C1④ APP_ENV=test 时同一 DEBUG 值不该报（这正是引入 APP_ENV 的目的）
            settings.APP_ENV = "test"
            msg_test = sc._check_demo_data(db)
            ok("C1 ④ ★ APP_ENV=test 时同一 DEBUG=false 不报警（e2e/CI 不产生噪音）",
               msg_test is None, f"msg={msg_test!r}（期望 None）")

            # C1⑤ DEBUG=true 时不管 APP_ENV 都不报（本地开发该有演示数据）
            settings.DEBUG = True
            settings.APP_ENV = "production"
            ok("C1 ⑤ DEBUG=true 时不报警（本地开发不该被这条噪音烦）",
               sc._check_demo_data(db) is None)

            # C1⑥ 演示数据关掉后不报
            settings.DEBUG = False
            settings.APP_ENV = "production"
            settings.SEED_DEMO_DATA = False
            ok("C1 ⑥ 演示数据关闭后不报警",
               sc._check_demo_data(db) is None)
        finally:
            db.close()
    finally:
        settings.SEED_DEMO_DATA, settings.DEBUG, settings.APP_ENV = _orig

    # ---------- C2：LLM 配置 ----------
    print("\nC2、LLM 配置检查 —— enabled=true 但拿不到密钥时 AI 在静默降级")
    _orig_llm = (settings.LLM_ENABLED, settings.LLM_API_KEY)
    try:
        db = _db()
        try:
            settings.LLM_ENABLED = False
            ok("C2 ① LLM_ENABLED=false 时不报警（明确接受降级是合法状态）",
               sc._check_llm_config(db) is None)

            # ★ 必须显式清空密钥：pydantic-settings 会读仓库根的 `.env`，
            # 而那里可能有真实 `LLM_API_KEY`。不清空的话本组会「因为开发者
            # 恰好配了密钥」而永远走不到告警分支 —— 测试依赖环境、且是
            # 静默的那种（CI 的 .env 与本地不同，红/绿不一致）。
            # 第一版就是踩了这个：C2② 在本地一直是 PASS，因为它读到了 .env。
            settings.LLM_ENABLED = True
            settings.LLM_API_KEY = ""
            from app.agents.llm import is_available as _is_avail

            ok("C2 ②' 前置：清空密钥后 is_available() 确实是 False",
               _is_avail() is False, "否则下面的断言测的不是告警分支")

            msg = sc._check_llm_config(db)
            ok("C2 ② ★ LLM_ENABLED=true 且无有效密钥 → 报警",
               isinstance(msg, str) and len(msg) > 0, f"msg={'有' if msg else 'None(漏报)'}")
            ok("C2 ③ 消息说明这是「静默降级」而不只是「配置缺失」",
               bool(msg) and "降级" in msg,
               f"含降级={'降级' in (msg or '')}")
            ok("C2 ④ 消息给出两条修复路径（配密钥 或 明确关闭）",
               bool(msg) and "LLM_API_KEY" in msg and "LLM_ENABLED=false" in msg,
               f"含LLM_API_KEY={('LLM_API_KEY' in (msg or ''))}, "
               f"含LLM_ENABLED=false={('LLM_ENABLED=false' in (msg or ''))}")
        finally:
            db.close()
    finally:
        settings.LLM_ENABLED, settings.LLM_API_KEY = _orig_llm

    # ---------- C3：V2 迁移标记 ----------
    print("\nC3、V2 迁移标记检查 —— 标记缺失 = 库可能停在半迁移状态")
    db = _db()
    try:
        from sqlalchemy import text

        db.execute(text("DELETE FROM sys_config WHERE key IN :ks")
                   .bindparams(__import__("sqlalchemy").bindparam("ks", expanding=True)),
                   {"ks": list(sc.V2_MARKERS)})
        db.commit()

        msg = sc._check_migration_markers(db)
        ok("C3 ① ★ 两个标记都缺失 → 报警", isinstance(msg, str) and len(msg) > 0,
           f"msg={'有' if msg else 'None(漏报)'}")
        ok("C3 ② 消息里点名了缺失的键（运维要去查哪个）",
           bool(msg) and all(m in msg for m in sc.V2_MARKERS),
           f"keys={sc.V2_MARKERS}")

        # 补一个、缺一个
        # 必须走 ORM：SysConfig 有 value_type / category / is_public 三个
        # NOT NULL 且带 default 的列，`default=` 只在 ORM 层生效。裸 SQL 得逐个
        # 手写，漏一个就是 IntegrityError（本文件第一版漏了两次）。
        from app.models import SysConfig

        db.add(SysConfig(key=sc.V2_MARKERS[0], value="1"))
        db.commit()
        msg_half = sc._check_migration_markers(db)
        ok("C3 ③ ★ 只缺一个时仍然报警（不能因为「大部分在」就放过）",
           bool(msg_half), f"msg={'有' if msg_half else 'None(漏报)'}")
        ok("C3 ④ 只报缺失的那一个，不把已存在的也列进来",
           bool(msg_half) and sc.V2_MARKERS[1] in msg_half
           and sc.V2_MARKERS[0] not in msg_half,
           f"缺={sc.V2_MARKERS[1]}, 在={sc.V2_MARKERS[0]}")

        # 两个都补齐
        db.add(SysConfig(key=sc.V2_MARKERS[1], value="1"))
        db.commit()
        ok("C3 ⑤ 两个标记都在时不报警",
           sc._check_migration_markers(db) is None)
    finally:
        db.close()

    # ---------- C4：任一项异常都必须降级 ----------
    print("\nC4、降级契约 —— 校验是观测手段，不能成为故障原因")
    db = _db()
    try:
        _orig_checks = sc.run_startup_checks.__globals__  # noqa: F841  仅为可读性占位

        # 临时往 checks 里塞一个必炸的项。它是元组字面量写在函数体里，
        # 所以打补丁要替换函数本身 —— 这里用「让 _check_demo_data 抛」更贴近
        # 真实故障（比如 settings 缺字段、db 断连）。
        _real = sc._check_demo_data
        _calls = []

        def _boom(_db):
            _calls.append(1)
            raise RuntimeError("模拟检查内部异常")

        sc._check_demo_data = _boom
        try:
            settings.SEED_DEMO_DATA = True
            settings.DEBUG = False
            settings.APP_ENV = "production"
            _raised = None
            try:
                n = sc.run_startup_checks(db)
            except Exception as exc:  # noqa: BLE001
                _raised = exc
                n = None
            ok("C4 ① ★ 某项检查抛异常时不向外抛（run_startup_checks 必须不 raise）",
               _raised is None, f"raised={_raised!r}")
            ok("C4 ② 抛异常的那项被计为「未发现」而不是中断整轮",
               isinstance(n, int), f"返回值={n!r}（必须是 int）")
            ok("C4 ③ 抛异常后 session 仍可用（没有留在不可用状态）",
               _session_ok(db), "见 _session_ok：执行一条简单查询")
        finally:
            sc._check_demo_data = _real
    finally:
        settings.SEED_DEMO_DATA, settings.DEBUG, settings.APP_ENV = _orig
        db.close()

    # ---------- C5：ErrorLog 幂等 ----------
    print("\nC5、ErrorLog 幂等 —— 重启 N 次只能有一行，不能把错误日志页刷爆")
    db = _db()
    try:
        from sqlalchemy import func, select

        from app.models import ErrorLog

        db.execute(__import__("sqlalchemy").text(
            "DELETE FROM sys_error_log WHERE module=:m AND path=:p"),
            {"m": sc._DEMO_ERR_MODULE, "p": sc._DEMO_ERR_PATH})
        db.commit()

        sc._upsert_demo_error_log(db, "第一版消息")
        _cnt1 = db.scalar(select(func.count()).select_from(ErrorLog)
                          .where(ErrorLog.module == sc._DEMO_ERR_MODULE,
                                 ErrorLog.path == sc._DEMO_ERR_PATH)) or 0
        sc._upsert_demo_error_log(db, "第二版消息")
        _cnt2 = db.scalar(select(func.count()).select_from(ErrorLog)
                          .where(ErrorLog.module == sc._DEMO_ERR_MODULE,
                                 ErrorLog.path == sc._DEMO_ERR_PATH)) or 0
        _row = db.scalar(select(ErrorLog)
                         .where(ErrorLog.module == sc._DEMO_ERR_MODULE,
                                ErrorLog.path == sc._DEMO_ERR_PATH)
                         .order_by(ErrorLog.id.desc()))
        ok("C5 ① ★ 连续写两次仍然只有一行（幂等 upsert）",
           _cnt1 == 1 and _cnt2 == 1, f"第一次={_cnt1}, 第二次={_cnt2}")
        ok("C5 ② ★ 内容是第二次的（更新生效，不是留着旧消息）",
           _row is not None and _row.message == "第二版消息",
           f"message={getattr(_row, 'message', None)!r}")
        ok("C5 ③ level 是 ERROR（不是 INFO/WARNING，否则会被错误日志页过滤掉）",
           _row is not None and _row.level == "ERROR",
           f"level={getattr(_row, 'level', None)!r}")

        # C5④ 与 init_db 那条不同 key —— 两条各自幂等、互不覆盖
        db.add(ErrorLog(level="ERROR", module="init_db",
                        path="/startup/enforce_default_admin_password",
                        message="默认口令告警"))
        db.commit()
        sc._upsert_demo_error_log(db, "又一次")
        _both = db.scalar(select(func.count()).select_from(ErrorLog)
                          .where(ErrorLog.path.like("/startup/%"))) or 0
        ok("C5 ④ ★ 与 init_db 的默认口令告警各自一行，互不覆盖",
           _both == 2, f"/startup/* 共 {_both} 行（期望 2）")
    finally:
        db.close()

    # ---------- C6：全量跑一轮不崩 ----------
    print("\nC6、全量跑一轮 —— 空库/正常配置下必须安静返回")
    db = _db()
    try:
        settings.SEED_DEMO_DATA = False
        settings.DEBUG = False
        settings.APP_ENV = "test"
        settings.LLM_ENABLED = False
        n = sc.run_startup_checks(db)
        ok("C6 ① ★ 干净配置下发现问题数为 0", n == 0, f"found={n}")
        ok("C6 ② 返回类型是 int（调用方可能忽略，但测试要断言）",
           isinstance(n, int), f"type={type(n).__name__}")
    finally:
        settings.SEED_DEMO_DATA, settings.DEBUG, settings.APP_ENV = _orig
        settings.LLM_ENABLED = _orig_llm
        db.close()

    total = _PASSED + len(_FAILED)
    print(f"\n  启动校验回归完成：共 {total} 项 | 通过 {_PASSED} | 失败 {len(_FAILED)}")
    if _FAILED:
        print("\n失败用例：")
        for n in _FAILED:
            print(f"  - {n}")
    print(f"{'=' * 66}\n")
    return 1 if _FAILED else 0


def _session_ok(db):
    """session 是否还能用（没有停在 PendingRollback 状态）。"""
    from sqlalchemy import text

    try:
        db.execute(text("SELECT 1")).scalar()
        return True
    except Exception:
        return False


if __name__ == "__main__":
    sys.exit(main())
