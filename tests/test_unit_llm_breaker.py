#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""离线单元回归：LLM 熔断/冷却状态**跨进程外置**（B1）。

## 锁的是什么

修复前，熔断状态是 `LLMClient` 的实例属性：

    self._disabled_reason = ""    # 鉴权熔断（401/403，永久）
    self._cooldown_until = 0.0    # 限流冷却（429，指数退避）—— time.monotonic()
    self._rate_limit_streak = 0

三个后果，第一个**今天就在生产成立**，第二三个是扩 worker 后成立：

1. **同进程两个实例各熔各的**。模块级 `llm_client = LLMClient()` 与
   `get_llm()` 单例是两个对象，`base.py` 的 Agent 走前者、部分接口走后者。
   一处熔断、另一处照旧拿无效密钥去撞 401。
2. **多 worker 各熔各的**。N 个进程 = N 倍无谓 401 往返（每次 5~6 秒）。
3. **`time.monotonic()` 无法跨进程比较**。monotonic 是进程内单调时钟，
   各进程起点不同（实测同机两进程差异可达数十万秒）→ A 进程写的截止时刻
   在 B 进程看来可能"早过期"也可能"还要冷却十年"。旧实现能用纯粹因为
   它只在单进程内比较。

修复后状态落在 `sys_llm_breaker` 单行表 + 模块级本地镜像。

## 为什么「本地镜像」和「DB」两者缺一不可（本文件最重要的一组断言）

- **只有 DB**（写全异步落库）：熔断最初是为了解决「6 道简答题 = 6 次无谓
  401，单次交卷 0.5s 涨到 33s」。这 6 次调用在**同一个循环里**，间隔毫秒级，
  异步写线程 commit 时刻不确定 → 第 2 次很可能读不到第 1 次写的熔断 →
  33 秒问题原样复活。**B 组就是这条的反向验证**（实测：去掉镜像后
  6 次循环真的发出 2 次、6 次真实往返）。
- **只有本地镜像**：跨进程完全不共享 → B1 等于没做。

## 与反向验证的对应关系

`tests/_tmp_reverse_breaker.py`（一次性脚本）逐道拆防线验证过本文件的
断言确实会红。对应关系：

    拆掉 auth 本地镜像        -> B 组 / F 组红（实测 6 次往返）
    拆掉 kind != 'auth' 保护  -> E② 红（DB 层被覆盖成 rate_limit）
    拆掉 cleared_at 墓碑      -> D⑥ 红（成功后仍判冷却中）
    reset_all 不清镜像        -> 多项红
    is_available 不看熔断     -> A⑥ 红
    get_client 不读共享状态   -> A④⑤ / B 组 / C② 红

## 为什么不走 e2e

e2e 固定 `LLM_ENABLED=false`（绝不触真实大模型），而本文件的被测对象是
**真实调用失败时**的状态机 —— e2e 里根本走不到 `_mark_disabled` /
`_start_rate_limit_cooldown`。`_cooldown_until` / `_disabled_reason` 这些
内部状态在现有 e2e 中**完全没有覆盖**。

## 用法

    python tests/test_unit_llm_breaker.py

退出码：0 = 全部通过，1 = 有失败。
"""
import os
import subprocess
import sys
import tempfile
import time

# ---- 必须在导入 app.* 之前定好环境：避免在仓库里建出脏库、避免拉外网 ----
_TMP = tempfile.mkdtemp(prefix="unit_breaker_")
_DB_PATH = os.path.join(_TMP, "unit.db").replace("\\", "/")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB_PATH
os.environ["LLM_ENABLED"] = "true"
os.environ["LLM_API_KEY"] = "sk-unit-test-fake-key-not-real"
os.environ["SCHEDULER_ENABLED"] = "false"
os.environ["DEBUG"] = "false"
# SECRET_KEY 必须 >=32 位：config.py 会拒绝"过于简单"的密钥。
os.environ.setdefault("SECRET_KEY", "unit_test_breaker_secret_key_32chars_ok")

_BACKEND = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"
)
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

import app.models  # noqa: F401,E402  确保全部表注册到 Base.metadata
from app.agents import llm as llm_mod  # noqa: E402
from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.services import llm_breaker  # noqa: E402

_FAILED = []
_PASSED = 0

# 异步落库要等多久才判定"已落库"。实测本机 daemon 线程写入 + commit 在
# 10ms 量级，200ms 已有 20 倍余量；取 400ms 是为了让 CI（慢盘）也稳。
ASYNC_SETTLE = 0.4


def ok(name, cond, detail=""):
    """断言并打印。刻意不叫 check()：tools/check_weak_assertion.py 只扫
    e2e 里的 `check(...)`，两边命名分开，扫描结果不互相污染。"""
    global _PASSED
    if cond:
        _PASSED += 1
        print(f"  [PASS] {name}" + (f"  -> {detail}" if detail else ""))
    else:
        _FAILED.append(name)
        print(f"  [FAIL] {name}  -> {detail}")


def db_kind():
    """直接查 DB 的 kind 列（绕过本地镜像），用于验证"另一进程"视角。"""
    from sqlalchemy import text

    with SessionLocal() as db:
        return db.scalar(text("SELECT kind FROM sys_llm_breaker WHERE id = 1"))


def db_streak():
    from sqlalchemy import text

    with SessionLocal() as db:
        return db.scalar(text("SELECT streak FROM sys_llm_breaker WHERE id = 1"))


def reset():
    """每个 case 开头复位：既有本地镜像也有 DB 行，且等异步删除落定。"""
    llm_breaker.reset_all()
    time.sleep(0.05)


def _strip_comments_and_docstrings(src: str) -> str:
    """剥掉注释与字符串/docstring，只留可执行 token（**无额外空格**）。

    H④⑤ 要断言「代码里没有 time.monotonic / CURRENT_TIMESTAMP」，但本模块
    大量注释在**解释**为什么不能用它们。直接扫原文会命中说明文字，
    变成「越认真写注释越红」的反向激励。这里用 tokenize 精确剥离。

    ⚠️ 拼接**不能加空格**。第一版用 `" ".join(...)` 是错的：tokenize 会把
    `time.monotonic` 切成 `time` `.` `monotonic` 三个 token，加空格拼回来
    变成 `time . monotonic`，于是 `"time.monotonic" in code` 恒为 False ——
    这条断言永远绿，等于没测（实测：往代码里注入 `_MONO = time.monotonic()`
    后测试仍然 53/53 全绿）。改成直接拼接后才能真正抓到。
    """
    import io
    import tokenize

    out = []
    try:
        for tok in tokenize.generate_tokens(io.StringIO(src).readline):
            if tok.type in (tokenize.COMMENT, tokenize.STRING):
                continue
            out.append(tok.string)
    except (tokenize.TokenError, IndentationError):
        # 剥离失败就退回原文（宁可误报也不放过真问题）
        return src
    return "".join(out)


# ============================================================
# A 组：鉴权熔断——本地立即生效 + 跨进程共享 + 对外状态
# ============================================================
def case_auth_breaker():
    print("\n" + "-" * 70)
    print("A 组：鉴权熔断（401/403，永久）")
    print("-" * 70)
    reset()

    c1 = llm_mod.LLMClient()
    c1._client = object()          # 假装连接池已建好（暴露"先判熔断再返回缓存"的顺序）
    ok("A① 初始无熔断", llm_breaker.load() is None)
    ok("A② 初始 get_client() 可用", c1.get_client() is not None)

    c1._mark_disabled(Exception("Error code: 401 - invalid_api_key"))
    ok("A③ 写后立刻 auth_disabled", llm_breaker.auth_disabled())
    ok("A④ 同一实例立刻短路（不等异步落库）", c1.get_client() is None,
       f"reason={c1._fallback_reason[:36]}")
    ok("A⑤ 另一实例也立刻短路（镜像是模块级，不是实例属性）",
       llm_mod.LLMClient().get_client() is None)
    ok("A⑥ is_available() 变 False", llm_mod.is_available() is False)

    time.sleep(ASYNC_SETTLE)
    ok("A⑦ 异步落库后 DB kind=auth", db_kind() == "auth", str(db_kind()))

    # 跨进程：起一个真子进程读同一个库
    child = subprocess.run(
        [sys.executable, "-c", (
            "import os,sys;"
            f"os.environ['DATABASE_URL']='sqlite:///{_DB_PATH}';"
            "os.environ['SECRET_KEY']='unit_test_breaker_secret_key_32chars_ok';"
            f"sys.path.insert(0, {_BACKEND!r});"
            "import app.models;"
            "from app.services import llm_breaker as b;"
            "s=b.load();"
            "print('KIND=', s['kind'] if s else 'none');"
            "print('AUTH=', b.auth_disabled())"
        )],
        capture_output=True, text=True, timeout=120,
    )
    out = child.stdout + child.stderr
    ok("A⑧ 子进程读到 auth（跨进程共享）", "KIND= auth" in out, out.strip()[-160:])
    ok("A⑨ 子进程 auth_disabled()=True", "AUTH= True" in out)


# ============================================================
# B 组：同循环内不得发出 N 次真实往返（B1 不能改坏 P1）
# ============================================================
def case_no_repeat_auth_calls():
    print("\n" + "-" * 70)
    print("B 组：6 次连续调用只允许 1 次真实往返（P1 的 33s 问题不能复发）")
    print("-" * 70)
    reset()

    c = llm_mod.LLMClient()

    class _Boom:
        """模拟无效密钥：每次 invoke 都抛 401。"""
        def invoke(self, _msgs):
            raise Exception("Error code: 401 - Incorrect API key provided")

    c._client = _Boom()
    real_calls = 0
    for _ in range(6):
        cl = c.get_client()
        if cl is None:
            continue
        real_calls += 1
        try:
            cl.invoke([])
        except Exception as exc:
            if c._is_auth_error(exc):
                c._mark_disabled(exc)
    ok("B① 6 次循环只 1 次拿到客户端", real_calls == 1, f"实际 {real_calls} 次")
    ok("B② 结束后处于熔断", llm_breaker.auth_disabled())


# ============================================================
# C 组：限流冷却——退避指数递增 + 到期自动恢复
# ============================================================
def case_rate_limit_cooldown():
    print("\n" + "-" * 70)
    print("C 组：限流冷却（429，指数退避 30→60→120→240→300）")
    print("-" * 70)
    reset()

    c = llm_mod.LLMClient()
    c._start_rate_limit_cooldown(Exception("Error code: 429 Too Many Requests"))
    s1 = llm_breaker.load()
    ok("C① 首次冷却 kind=rate_limit streak=1",
       s1 and s1["kind"] == "rate_limit" and s1["streak"] == 1, str(s1 and s1["streak"]))
    rem1 = c._cooldown_remaining()
    ok("C② 剩余冷却 30s 左右", 28 <= rem1 <= 31, f"{rem1}s")
    ok("C③ 冷却期内 get_client() 短路", c.get_client() is None)

    c._start_rate_limit_cooldown(Exception("Error code: 429 Too Many Requests"))
    s2 = llm_breaker.load()
    ok("C④ 第二次冷却 streak=2（指数退避）",
       s2 and s2["streak"] == 2, str(s2 and s2["streak"]))
    rem2 = c._cooldown_remaining()
    ok("C⑤ 剩余冷却约 60s（翻倍）", 58 <= rem2 <= 61, f"{rem2}s")

    time.sleep(ASYNC_SETTLE)
    ok("C⑥ 落库后 DB kind=rate_limit", db_kind() == "rate_limit", str(db_kind()))
    ok("C⑦ 落库后 DB streak=2（原子递增）", db_streak() == 2, str(db_streak()))

    # 到期自动恢复：**本地镜像与 DB 都要过期**看恢复。
    # 为什么不能只改 DB：`load()` 会合并"本地镜像 + DB"，本地镜像里还是
    # 未过期的 rate_limit 时，DB 那行被判过期也仍然返回冷却中 —— 这是
    # 有意的（本地镜像比 DB 新，见 llm_breaker._merge 的注释）。
    # 所以这里把两处都置为过去时刻，验证的是**两边的过期判定都生效**。
    from sqlalchemy import text
    with SessionLocal() as db:
        db.execute(text(
            "UPDATE sys_llm_breaker SET expire_at = :past WHERE id = 1"
        ), {"past": "2000-01-01 00:00:00.000000"})
        db.commit()
    from datetime import datetime
    llm_breaker._local["expire_at"] = datetime(2000, 1, 1, 0, 0, 0)
    ok("C⑧ 双方都到期后 load() 返回 None（自动恢复）", llm_breaker.load() is None,
       str(llm_breaker.load()))
    ok("C⑨ 到期后本地镜像被就地清空", llm_breaker._local["kind"] == "",
       str(llm_breaker._local["kind"]))


# ============================================================
# D 组：清除语义——成功只清冷却、不清鉴权熔断
# ============================================================
def case_clear_semantics():
    print("\n" + "-" * 70)
    print("D 组：清除语义（成功只清 cooling / 墓碑压制旧行 / 不误清 auth）")
    print("-" * 70)

    # D①-② 成功后冷却清空，且**立刻**清空（不等异步删除）
    reset()
    c = llm_mod.LLMClient()
    c._start_rate_limit_cooldown(Exception("429"))
    c._reset_rate_limit()
    ok("D① 成功后 load() 立刻为 None（墓碑压制 DB 旧行）",
       llm_breaker.load() is None, str(llm_breaker.load()))
    time.sleep(ASYNC_SETTLE)
    ok("D② 异步删除后 DB 里也没有 rate_limit 行",
       db_kind() is None, str(db_kind()))

    # D③-④ auth 不得被"成功"清掉
    reset()
    c2 = llm_mod.LLMClient()
    c2._mark_disabled(Exception("401 invalid_api_key"))
    c2._reset_rate_limit()
    ok("D③ auth 不被 _reset_rate_limit 清除", llm_breaker.auth_disabled())

    # D④ clear_rate_limit 只删 rate_limit 行，绝不连带 auth
    reset()
    llm_breaker.save_auth("auth 必须留存")
    time.sleep(ASYNC_SETTLE)
    llm_breaker.clear_rate_limit_async()
    time.sleep(ASYNC_SETTLE)
    ok("D④ clear_rate_limit 不清 auth", db_kind() == "auth", str(db_kind()))

    # D⑤ reset_all 是唯一能清 auth 的入口，且必须同步
    reset()
    llm_breaker.save_auth("准备被 reset")
    time.sleep(ASYNC_SETTLE)
    llm_breaker.reset_all()
    ok("D⑤ reset_all 同步解除 auth", llm_breaker.auth_disabled() is False)
    ok("D⑥ reset_all 同步删 DB 行", llm_breaker.load() is None, str(llm_breaker.load()))


# ============================================================
# E 组：auth 是更强状态，不得被 rate_limit 覆盖
# ============================================================
def case_auth_not_overridden():
    print("\n" + "-" * 70)
    print("E 组：auth 不被 rate_limit 覆盖（多进程竞争的关键不变量）")
    print("-" * 70)

    # E① API 路径：本地镜像层
    reset()
    llm_breaker.save_auth("auth 优先")
    time.sleep(ASYNC_SETTLE)
    llm_mod.LLMClient()._start_rate_limit_cooldown(Exception("429"))
    s = llm_breaker.load()
    ok("E① API 路径下仍是 auth", s and s["kind"] == "auth", str(s and s["kind"]))

    # E② **直接打 DB 层**：绕过本地镜像提前返回。
    # 这是真实的多进程竞争形态 —— A 进程已把 auth 写进 DB，B 进程（不知道）
    # 撞 429 后要写 rate_limit；若 DB 层没有 `kind != 'auth'` 保护，
    # 全局 auth 就被覆盖，所有进程回去继续用无效密钥撞 401。
    reset()
    llm_breaker._write_auth("DB 层 auth")
    ok("E② 前置：DB 里已是 auth", db_kind() == "auth", str(db_kind()))
    llm_breaker._bump_cooldown("另一进程撞 429", 30, 300)
    ok("E③ DB 层 auth 不被 rate_limit 覆盖", db_kind() == "auth", str(db_kind()))

    # E④ 反向：auth 写入可以覆盖 rate_limit（密钥无效时谈冷却没意义）
    reset()
    llm_breaker._bump_cooldown("先限流", 30, 300)
    ok("E④ 前置：DB 是 rate_limit", db_kind() == "rate_limit", str(db_kind()))
    llm_breaker._write_auth("再撞 401")
    ok("E⑤ auth 无条件覆盖 rate_limit", db_kind() == "auth", str(db_kind()))


# ============================================================
# F 组：可观测性——/agent/status 能看到熔断细节
# ============================================================
def case_observability():
    print("\n" + "-" * 70)
    print("F 组：状态快照（此前状态藏在实例属性里，运维只能靠日志猜）")
    print("-" * 70)
    reset()
    snap = llm_breaker.snapshot()
    ok("F① 无熔断时 breaker=none", snap["breaker"] == "none", str(snap))

    llm_mod.LLMClient()._mark_disabled(Exception("401 bad key"))
    snap2 = llm_breaker.snapshot()
    ok("F② 熔断后 breaker=auth", snap2["breaker"] == "auth", str(snap2["breaker"]))
    ok("F③ 快照带原因", "密钥无效" in snap2["reason"], snap2["reason"][:40])

    reset()
    llm_mod.LLMClient()._start_rate_limit_cooldown(Exception("429"))
    snap3 = llm_breaker.snapshot()
    ok("F④ 冷却中 breaker=rate_limit", snap3["breaker"] == "rate_limit",
       str(snap3["breaker"]))
    ok("F⑤ 快照带剩余秒数", snap3["cooldown_remaining"] > 0,
       f"{snap3['cooldown_remaining']}s")
    ok("F⑥ 快照带退避次数", snap3["streak"] == 1, str(snap3["streak"]))


# ============================================================
# G 组：fail-open——旁路状态读失败不能反噬主流程
# ============================================================
def case_fail_open():
    print("\n" + "-" * 70)
    print("G 组：读失败必须 fail-open（表坏了不能让 AI 集体降级）")
    print("-" * 70)
    reset()

    # 把表改名 → load() 会抛 sqlite 错误 → 必须按"无熔断"处理
    from sqlalchemy import text
    with SessionLocal() as db:
        db.execute(text("ALTER TABLE sys_llm_breaker RENAME TO sys_llm_breaker_bak"))
        db.commit()
    try:
        ok("G① 表不存在时 load() 返回 None（不抛异常）",
           llm_breaker.load() is None)
        ok("G② 表不存在时 auth_disabled()=False（fail-open）",
           llm_breaker.auth_disabled() is False)
        ok("G③ 表不存在时 snapshot() 不抛异常",
           llm_breaker.snapshot()["breaker"] == "none")
        # 写入也不该把调用方炸掉（异步 + 吞异常）
        llm_breaker.save_auth("表坏了也要能调用")
        ok("G④ 表不存在时 save_auth 不抛异常", True)
    finally:
        with SessionLocal() as db:
            db.execute(text(
                "ALTER TABLE sys_llm_breaker_bak RENAME TO sys_llm_breaker"))
            db.commit()
    time.sleep(0.2)
    reset()


# ============================================================
# H 组：数据契约——表结构与时间列（防回归到 monotonic）
# ============================================================
def case_schema():
    print("\n" + "-" * 70)
    print("H 组：表结构与时间列契约（防回归成 time.monotonic）")
    print("-" * 70)
    from app.models import LlmBreakerState

    cols = {c.name: c for c in LlmBreakerState.__table__.columns}
    ok("H① 表名 sys_llm_breaker", LlmBreakerState.__tablename__ == "sys_llm_breaker")
    ok("H② 主键是 id（单行表，autoincrement=False）",
       "id" in cols and cols["id"].primary_key
       and getattr(cols["id"], "autoincrement", None) is False)
    for col in ("kind", "reason", "streak", "expire_at", "updated_at"):
        ok(f"H③ 字段 {col} 存在", col in cols)

    import inspect

    src = inspect.getsource(llm_breaker)

    # ⚠️ 必须**剔除注释与 docstring 再看**。
    # 第一版直接 `"time.monotonic" in src` 是自相矛盾的断言：本模块的
    # docstring 里到处在解释「为什么不能用 time.monotonic」「为什么不能
    # 用 CURRENT_TIMESTAMP」，那些**说明文字**被当成违规命中，测试必红。
    # 这类"扫源码"的断言必须区分「代码」与「解释代码的文字」——
    # 否则唯一的修法是把最有价值的注释删掉，正好反了。
    code_only = _strip_comments_and_docstrings(src)
    ok("H④ 代码里不出现 time.monotonic（必须用绝对时间）",
       "time.monotonic" not in code_only,
       [ln.strip() for ln in code_only.splitlines() if "time.monotonic" in ln][:2])
    ok("H⑤ 代码里不出现 CURRENT_TIMESTAMP（SQLite 字典序比较的坑）",
       "CURRENT_TIMESTAMP" not in code_only.upper(),
       [ln.strip() for ln in code_only.splitlines()
        if "CURRENT_TIMESTAMP" in ln.upper()][:2])
    # 注意：tokenize 版会把 `now_local()` 拆成 `now_local ( )`，
    # 不能直接搜带括号的字符串。
    ok("H⑥ 使用 now_local 作为时间源", "now_local" in code_only)

    ok("H⑦ KIND_AUTH / KIND_RATE_LIMIT 常量正确",
       llm_breaker.KIND_AUTH == "auth"
       and llm_breaker.KIND_RATE_LIMIT == "rate_limit")
    ok("H⑧ BREAKER_ID 恒为 1（单行）", llm_breaker.BREAKER_ID == 1)


def main() -> int:
    Base.metadata.create_all(bind=engine)

    print("=" * 70)
    print("离线单元回归：LLM 熔断/冷却状态跨进程外置（B1）")
    print("=" * 70)

    case_auth_breaker()
    case_no_repeat_auth_calls()
    case_rate_limit_cooldown()
    case_clear_semantics()
    case_auth_not_overridden()
    case_observability()
    case_fail_open()
    case_schema()

    reset()
    print("\n" + "=" * 70)
    total = _PASSED + len(_FAILED)
    print(f"合计 {total} 项：通过 {_PASSED}，失败 {len(_FAILED)}")
    if _FAILED:
        print("\n失败项：")
        for n in _FAILED:
            print(f"  - {n}")
        print("=" * 70)
        return 1
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
