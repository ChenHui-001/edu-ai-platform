#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""离线单元回归：图形验证码强制化（S7）+ 开关的单向收紧语义。

## 锁的是什么

修复前，`api/v1/auth.py` 的登录与注册两处都是**同一个短路绕过**：

    if payload.captcha_key and not verify_captcha(...):
        raise BusinessException("验证码错误或已过期")

`and` 的左边一旦为假（请求**不写** `captcha_key` 这个字段），整个条件恒为
False，校验被完整跳过。这不是"兼容 API 调用"，而是把「要不要校验」的决定权
交给了调用方 —— 想绕过图形验证码，只要不传这个字段就行。图形验证码因此对
密码爆破完全不起作用，只剩一个失败次数锁定（5 次/15 分钟，且换账号即重置）。

修复后的行为矩阵（`_verify_captcha_or_raise`）：

| CAPTCHA_ENFORCED | 未带 key | 带 key 且正确 | 带 key 且错误/过期 |
| ---------------- | -------- | ------------- | ------------------ |
| `true`（默认）   | **400**  | 200           | **400**            |
| `false`（e2e）   | 200      | 200           | **400**            |

第三列两行**相同**是核心设计：关掉开关只降级到「无验证码」，绝不允许降级成
「带了错码也放行」。开关单向收紧，不存在"关掉即空操作"的路径。

## 为什么必须在离线单元层

e2e **看不到**这个缺陷的大部分性质：

1. e2e 服务端固定以 `CAPTCHA_ENFORCED=false` 启动（100 处 `.login()` + 26 处
   裸登录 + 7 处裸注册都不带验证码），所以 `true` 分支在 e2e 里根本不执行；
2. 验证码的正确答案只存在于 PNG 里（`sys_captcha` 存明文，接口只回图和 key），
   e2e 无法从响应里拿到答案，也就无法构造"带正确 key"的正例；
3. UI 层 `tests/ui_e2e/phase2_login.py` 靠**预先人工识别**的验证码池
   （`captcha_pool.json`）走真实页面，那验证的是前端交互，不是后端契约。

于是三分支矩阵、一次性语义、开关默认值都只能在这一层用独立临时库精确断言。

## 与 e2e 的分工

| 性质 | e2e | 本文件 |
| --- | --- | --- |
| 取码接口返回 base64 图 | ✅ | — |
| 传错码被拒（两种形态） | ✅ | ✅ |
| 不传码：true 拒 / false 放行 | ⚠ 仅 false 分支 | ✅ 两分支 |
| 传正确码可登录 | ✘ 拿不到答案 | ✅ 直接读库 |
| 验证码一次性（不可重放） | ✘ | ✅ |
| 开关默认值为 true | ✘ 被环境覆盖 | ✅ 防呆 |
| `.env.example` 没写死 false | ✘ | ✅ 防呆 |

## 用法

    python tests/test_unit_captcha_enforced.py

退出码：0 = 全部通过，1 = 有失败。
"""
import os
import sys
import tempfile

# ---- 必须在导入 app.* 之前定好环境：避免在仓库里建出脏库、避免拉外网 ----
_TMP = tempfile.mkdtemp(prefix="unit_captcha_")
os.environ["DATABASE_URL"] = "sqlite:///" + os.path.join(_TMP, "unit.db").replace("\\", "/")
os.environ["LLM_ENABLED"] = "false"
os.environ["SCHEDULER_ENABLED"] = "false"
os.environ["DEBUG"] = "false"
os.environ.setdefault("SECRET_KEY", "unit_test_secret_key_not_for_prod")
# 显式不设 CAPTCHA_ENFORCED：验证默认值就是 True（A 组①直接读 Settings()）。
# ⚠️ 但 e2e / CI 会在外部注入 CAPTCHA_ENFORCED=false，本文件若在那种环境下被
# 调起，A 组①会红。这不是缺陷 —— 说明那一次运行的形态确实不是生产形态。
# run_e2e.sh 里本文件在导出 CAPTCHA_ENFORCED=false **之后**执行，故 A 组①
# 用 `_fresh_settings()` 强制剥离该变量后再实例化，见其 docstring。

_BACKEND = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"
)
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

import app.models  # noqa: F401,E402  确保全部表注册到 Base.metadata
from app.core.config import Settings, settings  # noqa: E402
from app.core.database import Base, engine  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.main import app  # noqa: E402

_FAILED = []
_PASSED = 0

PWD = "Cap@2026Test"     # 测试账号口令（强度达标，避免被 validate_password_strength 拦）
SEED_CAPTCHA_TEXT = "AB3D"   # 直接写库的正例答案


def ok(name, cond, detail=""):
    """断言并打印。刻意不叫 check()：tools/check_weak_assertion.py 只扫
    e2e 的 check(...) 恒真写法，两边命名分开，扫描结果不会互相污染。"""
    global _PASSED
    if cond:
        _PASSED += 1
        print(f"  [PASS] {name}" + (f"  -> {detail}" if detail else ""))
    else:
        _FAILED.append(name)
        print(f"  [FAIL] {name}  -> {detail}")


# ============================================================
# 造数据 / 工具
# ============================================================
def seed_user():
    """建一个可登录的 active 用户，返回纯标量（ORM 实例关 session 后会 detached）。"""
    from sqlalchemy.orm import sessionmaker

    from app.models import IdentityType, Role, User, UserRole, UserStatus

    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        role = Role(code="teacher", name="教师", data_scope="self")
        db.add(role)
        db.flush()
        u = User(
            username="cap_teacher",
            password=hash_password(PWD),
            real_name="验证码测试教师",
            identity=IdentityType.TEACHER.value,
            status=UserStatus.ACTIVE.value,
            must_change_password=False,
        )
        db.add(u)
        db.flush()
        db.add(UserRole(user_id=u.id, role_id=role.id))
        db.commit()
        return {"uid": u.id, "username": u.username}
    finally:
        db.close()


def put_captcha(key, text=SEED_CAPTCHA_TEXT, ttl=180):
    """直接往 `sys_captcha` 写一条**已知明文**的验证码。

    这是本文件能测「带正确码可通过」的唯一途径：`GET /auth/captcha` 的响应
    只有图（base64）和 key，明文只存在服务端表里，没有别的读法。
    """
    from datetime import timedelta

    from sqlalchemy.orm import sessionmaker

    from app.models import Captcha
    from app.utils.common import now_local

    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        db.merge(Captcha(
            key=key, text=text,
            expire_at=now_local() + timedelta(seconds=ttl),
        ))
        db.commit()
    finally:
        db.close()


def captcha_row_exists(key):
    from sqlalchemy.orm import sessionmaker

    from app.models import Captcha

    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        return db.get(Captcha, key) is not None
    finally:
        db.close()


def make_client(enforced):
    """构造 TestClient 并把开关固定成 `enforced`。

    直接改 `settings` 单例而不是改 env：pydantic-settings 在模块导入时就
    实例化好了，改 env 不会生效。生产由环境变量决定初值，测试负责覆盖运行期
    取值 —— 与 test_unit_must_change_pwd.py 同一做法。

    刻意不用 `with TestClient(app)`：进上下文会触发 lifespan → 跑 init_all
    （整套种子 + 迁移 + Agent 预热），既慢又会搅乱测试数据。
    """
    from fastapi.testclient import TestClient

    settings.CAPTCHA_ENFORCED = enforced
    return TestClient(app, raise_server_exceptions=False)


def login(c, username=os.environ.get("_CAP_USER", "cap_teacher"), password=PWD,
          captcha_key=None, captcha=None):
    """登录，返回 (status_code, message, has_token)。"""
    body = {"username": username, "password": password}
    if captcha_key is not None:
        body["captcha_key"] = captcha_key
    if captcha is not None:
        body["captcha"] = captcha
    r = c.post("/api/v1/auth/login", json=body)
    payload = r.json() if r.content else {}
    data = payload.get("data") or {}
    return r.status_code, payload.get("message", ""), bool(data.get("access_token"))


def register(c, username, captcha_key=None, captcha=None):
    """注册，返回 (status_code, message)。"""
    body = {
        "username": username, "password": PWD,
        "real_name": "验证码测试注册", "identity": "teacher",
    }
    if captcha_key is not None:
        body["captcha_key"] = captcha_key
    if captcha is not None:
        body["captcha"] = captcha
    r = c.post("/api/v1/auth/register", json=body)
    payload = r.json() if r.content else {}
    return r.status_code, payload.get("message", "")


def _fresh_settings():
    """在**剥离 `CAPTCHA_ENFORCED` 环境变量**的前提下实例化 Settings。

    为什么不能直接 `Settings()`：pydantic-settings 会读环境变量，而
    `tools/run_e2e.sh` 会 `export CAPTCHA_ENFORCED=false`（e2e 服务端必须
    关掉强制化）。本文件在 run_e2e.sh 的离线阶段被调用，若这里直接实例化，
    读到的就是 false —— A 组「默认值必须为 true」会假红，而且红得莫名其妙。

    这是**测试自身依赖外部环境**的典型形态，必须显式切断，否则「本地绿/CI 红」
    或者反过来。切断后再读 config.py 里写的字面默认值，那才是要防呆的东西。
    """
    saved = os.environ.pop("CAPTCHA_ENFORCED", None)
    try:
        return Settings()
    finally:
        if saved is not None:
            os.environ["CAPTCHA_ENFORCED"] = saved


def _env_example_safe():
    """`.env.example` 不得出现**未注释**的 `CAPTCHA_ENFORCED=false`。

    这个文件是部署模板，用户会直接 `cp .env.example .env`。一旦里面有一行
    生效的 false，生产部署就会静默关闭验证码强制化 —— 正是 S7 要修的那个洞。
    """
    path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env.example")
    if not os.path.exists(path):
        return True
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            if s.lower().replace(" ", "").startswith("captcha_enforced=false"):
                return False
    return True


# ============================================================
# A、开关默认值（防呆）
# ============================================================
def case_default_switch():
    print("\nA、开关默认值（防呆）")

    fresh = _fresh_settings()
    ok("① Settings().CAPTCHA_ENFORCED 默认为 True",
       fresh.CAPTCHA_ENFORCED is True, f"got={fresh.CAPTCHA_ENFORCED}")
    ok("② 该字段是 bool 而非 str（pydantic 会做类型转换）",
       isinstance(fresh.CAPTCHA_ENFORCED, bool),
       f"type={type(fresh.CAPTCHA_ENFORCED).__name__}")
    ok("③ .env.example 里没有把它写死成 false",
       _env_example_safe(),
       ".env.example 若出现未注释的 false 会让生产裸奔")


# ============================================================
# B、CAPTCHA_ENFORCED = true（生产形态）
# ============================================================
def case_enforced_true(u):
    print("\nB、CAPTCHA_ENFORCED=true（生产形态）")
    c = make_client(True)

    # ① 缺 captcha_key —— 这一条就是 S7 本身
    sc, msg, tok = login(c)
    ok("① ★ 不传 captcha_key 登录被拒（原短路绕过点）",
       sc == 400 and "验证码" in msg and not tok, f"status={sc} msg={msg!r}")

    # ② 传了 key 但库里没有（伪造 key）
    sc, msg, tok = login(c, captcha_key="deadbeefdeadbeef", captcha="AB3D")
    ok("② 伪造 captcha_key 登录被拒",
       sc == 400 and "验证码" in msg and not tok, f"status={sc} msg={msg!r}")

    # ③ 正确 key + 错误明文
    put_captcha("k_true_wrong_text")
    sc, msg, tok = login(c, captcha_key="k_true_wrong_text", captcha="ZZZZ")
    ok("③ 正确 key 但验证码输错，登录被拒",
       sc == 400 and "验证码" in msg and not tok, f"status={sc} msg={msg!r}")

    # ④ 正确 key + 正确明文 → 必须放行（否则等于把登录打死）
    put_captcha("k_true_ok")
    sc, msg, tok = login(c, captcha_key="k_true_ok", captcha=SEED_CAPTCHA_TEXT)
    ok("④ ★ 正确 key + 正确验证码可登录",
       sc == 200 and tok, f"status={sc} msg={msg!r}")

    # ⑤ 大小写不敏感（用户看到的图不区分大小写，verify_captcha 已 upper 比较）
    put_captcha("k_true_case", text="AB3D")
    sc, msg, tok = login(c, captcha_key="k_true_case", captcha="ab3d")
    ok("⑤ 验证码大小写不敏感",
       sc == 200 and tok, f"status={sc} msg={msg!r}")

    # ⑥ 注册端点同一条防线（修复前这里是同一个 `and` 短路）
    sc, msg = register(c, "cap_reg_missing")
    ok("⑥ ★ 注册不传 captcha_key 被拒",
       sc == 400 and "验证码" in msg, f"status={sc} msg={msg!r}")

    put_captcha("k_reg_ok")
    sc, msg = register(c, "cap_reg_ok", captcha_key="k_reg_ok", captcha=SEED_CAPTCHA_TEXT)
    ok("⑦ 注册带正确验证码可通过",
       sc == 200, f"status={sc} msg={msg!r}")

    # ⑧ 缺 key 的错误提示要与"输错"区分开：前者是客户端没取到码，
    #    后者是用户看错图。两者的补救动作不同（刷新 vs 重输）。
    sc1, msg1, _ = login(c, captcha_key=None)
    sc2, msg2, _ = login(c, captcha_key="nonexistent_key", captcha="XXXX")
    ok("⑧ 缺 key 与输错码的提示文案不同",
       msg1 != msg2 and "请输入" in msg1 and "过期" in msg2 or "错误" in msg2,
       f"missing={msg1!r} wrong={msg2!r}")


# ============================================================
# C、CAPTCHA_ENFORCED = false（e2e / CI 形态）
# ============================================================
def case_enforced_false(u):
    print("\nC、CAPTCHA_ENFORCED=false（e2e/CI 形态）")
    c = make_client(False)

    # ① 缺 key 放行 —— 这是开关存在的唯一目的
    sc, msg, tok = login(c)
    ok("① 不传 captcha_key 可登录（开关生效）",
       sc == 200 and tok, f"status={sc} msg={msg!r}")

    # ② ★ 核心：关掉开关**不能**让错误验证码通过。
    #    如果哪天有人把 `_verify_captcha_or_raise` 简化成
    #    `if not settings.CAPTCHA_ENFORCED: return`（在函数最开头），这一条会红。
    put_captcha("k_false_wrong")
    sc, msg, tok = login(c, captcha_key="k_false_wrong", captcha="ZZZZ")
    ok("② ★ 开关为 false 时，带错误验证码仍被拒（单向收紧）",
       sc == 400 and "验证码" in msg and not tok, f"status={sc} msg={msg!r}")

    # ③ 伪造 key 同样被拒
    sc, msg, tok = login(c, captcha_key="fake_key_xxxx", captcha="AB3D")
    ok("③ 开关为 false 时，伪造 key 仍被拒",
       sc == 400 and "验证码" in msg and not tok, f"status={sc} msg={msg!r}")

    # ④ 带正确码当然通过
    put_captcha("k_false_ok")
    sc, msg, tok = login(c, captcha_key="k_false_ok", captcha=SEED_CAPTCHA_TEXT)
    ok("④ 开关为 false 时，带正确码可登录",
       sc == 200 and tok, f"status={sc} msg={msg!r}")

    # ⑤ 注册端点同语义：缺 key 放行，错码被拒
    sc, msg = register(c, "cap_reg_false_missing")
    ok("⑤ 开关为 false 时，注册不传 key 放行",
       sc == 200, f"status={sc} msg={msg!r}")

    put_captcha("k_reg_false_wrong")
    sc, msg = register(c, "cap_reg_false_wrong",
                       captcha_key="k_reg_false_wrong", captcha="ZZZZ")
    ok("⑥ 开关为 false 时，注册带错误码仍被拒",
       sc == 400 and "验证码" in msg, f"status={sc} msg={msg!r}")


# ============================================================
# D、一次性语义（不可重放）
# ============================================================
def case_one_time(u):
    print("\nD、一次性语义（不可重放）")
    c = make_client(True)

    put_captcha("k_once")
    sc1, _, tok1 = login(c, captcha_key="k_once", captcha=SEED_CAPTCHA_TEXT)
    ok("① 首次使用正确码登录成功", sc1 == 200 and tok1, f"status={sc1}")

    # 不做这层保护的话，同一个码可以无限重放 —— 等于图形验证码没有一次性，
    # 攻击者识别一次就能拿它打几千次密码。
    sc2, msg2, tok2 = login(c, captcha_key="k_once", captcha=SEED_CAPTCHA_TEXT)
    ok("② ★ 同一个码第二次使用被拒（一次性）",
       sc2 == 400 and not tok2, f"status={sc2} msg={msg2!r}")

    # 输错也消耗：否则"输错一次"可以无限重试，4 位码（36^4≈1.7M）在 3 分钟
    # 窗口内是可爆破的。
    put_captcha("k_once_wrong")
    sc3, _, _ = login(c, captcha_key="k_once_wrong", captcha="ZZZZ")
    ok("③ 输错一次，该 key 已被消费", sc3 == 400, f"status={sc3}")
    sc4, msg4, tok4 = login(c, captcha_key="k_once_wrong", captcha=SEED_CAPTCHA_TEXT)
    ok("④ ★ 输错后不能再拿正确值复用同一个 key（防爆破）",
       sc4 == 400 and not tok4, f"status={sc4} msg={msg4!r}")

    # 键已从库里删掉（不是仅标记失效）
    put_captcha("k_once_gone")
    login(c, captcha_key="k_once_gone", captcha="ZZZZ")
    ok("⑤ 校验后该验证码记录已从库中删除", not captcha_row_exists("k_once_gone"),
       "verify_captcha 应 SELECT + DELETE 同事务")


# ============================================================
# E、过期验证码
# ============================================================
def case_expired(u):
    print("\nE、过期验证码")
    c = make_client(True)

    # ttl 为负 → 写入即过期
    put_captcha("k_expired", ttl=-1)
    sc, msg, tok = login(c, captcha_key="k_expired", captcha=SEED_CAPTCHA_TEXT)
    ok("① 过期验证码即使明文正确也被拒",
       sc == 400 and "验证码" in msg and not tok, f"status={sc} msg={msg!r}")
    ok("② 过期记录同样被删除（不留垃圾）", not captcha_row_exists("k_expired"), "")


# ============================================================
# F、校验顺序：验证码必须在账号状态之前
# ============================================================
def case_order(u):
    print("\nF、校验顺序（验证码先于账号状态）")

    # 这是一条容易被忽略但很关键的性质：如果 `authenticate` 先跑，
    # 那么"用错密码登录"会给该账号 login_fail_count +1，攻击者只要知道用户名，
    # 发 5 个不带验证码的错密码请求就能把账号锁 15 分钟 —— 拒绝服务。
    # 验证码前置后，没有有效码的流量根本碰不到账号状态。
    c = make_client(True)

    from sqlalchemy.orm import sessionmaker

    from app.models import User

    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        u_row = db.get(User, u["uid"])
        u_row.login_fail_count = 0
        u_row.locked_until = None
        db.commit()
    finally:
        db.close()

    # 连发 6 次「不传验证码 + 错密码」，超过 MAX_LOGIN_FAIL=5
    for _ in range(6):
        login(c, password="wrong-password-zzz")

    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        u_row = db.get(User, u["uid"])
        fails, locked = u_row.login_fail_count, u_row.locked_until
    finally:
        db.close()

    ok("★ 无验证码的请求不会累加 login_fail_count（防账号锁死 DoS）",
       fails == 0, f"login_fail_count={fails}")
    ok("★ 无验证码的请求不会触发账号锁定",
       locked is None, f"locked_until={locked}")

    # 带正确码但不是密码错误 → 应该正常累加（证明计数逻辑本身没被改坏）
    put_captcha("k_order_ok")
    sc, _, _ = login(c, password="wrong-password-zzz", captcha_key="k_order_ok",
                     captcha=SEED_CAPTCHA_TEXT)
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        u_row = db.get(User, u["uid"])
        fails2 = u_row.login_fail_count
    finally:
        db.close()
    ok("带正确验证码 + 错误密码仍会累加失败计数（计数逻辑完好）",
       sc == 401 and fails2 == 1, f"status={sc} login_fail_count={fails2}")

    # 复位，避免影响后续
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        u_row = db.get(User, u["uid"])
        u_row.login_fail_count = 0
        u_row.locked_until = None
        db.commit()
    finally:
        db.close()


# ============================================================
# G、登录失败 IP 限流（S7 配套：堵住换账号撞库）
# ============================================================
def case_login_ip_rate(u):
    print("\nG、登录失败 IP 限流")
    c = make_client(True)

    from sqlalchemy.orm import sessionmaker

    from app.api.v1 import auth as auth_mod
    from app.core.security import hash_password as _hp
    from app.models import IdentityType, User, UserStatus

    TEST_IP = "198.51.100.42"   # TEST-NET-2，不会被真实流量污染
    OTHER_IP = "198.51.100.99"

    # ★ 必须**换用户名**才能测到 IP 限流。
    # 用同一个账号连发 30 次错密码，第 5 次就会触发**按账号**的锁定
    # （MAX_LOGIN_FAIL=5），后续请求变成「账号已锁定」，走不到 IP 计数
    # —— 第一版就是这么红的（第 31 次仍返回 401「账号已锁定」）。
    # 这也正是 IP 限流存在的理由：撞库是**换账号**的，按账号锁定对它无效。
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        for i in range(40):
            db.add(User(
                username=f"iprate_{i}", password=_hp("Never@Match1"),
                real_name=f"限流探针{i}", identity=IdentityType.TEACHER.value,
                status=UserStatus.ACTIVE.value, must_change_password=False,
            ))
        db.commit()
    finally:
        db.close()

    _seq = {"n": 0}

    def reset_ip_bucket():
        auth_mod._LOGIN_FAIL_HITS.pop(TEST_IP, None)
        auth_mod._LOGIN_FAIL_HITS.pop(OTHER_IP, None)

    def login_from_ip(user=None, password=None, captcha_ok=True,
                      ip=TEST_IP):
        """从指定 IP 发一次登录。captcha_ok=False 时不带 key（验证码层就拒）。"""
        if not captcha_ok:
            key = None
        else:
            _seq["n"] += 1
            key = f"k_ip_{_seq['n']}"
            put_captcha(key, text=SEED_CAPTCHA_TEXT)
        # 默认每次换一个用户名：避免撞上按账号的 5 次锁定
        if user is None:
            user = f"iprate_{_seq['n'] % 40}"
        if password is None:
            password = "definitely-wrong-pwd"
        body = {"username": user, "password": password}
        if key:
            body["captcha_key"] = key
            body["captcha"] = SEED_CAPTCHA_TEXT
        r = c.post("/api/v1/auth/login", json=body, headers={"X-Real-IP": ip})
        payload = r.json() if r.content else {}
        return r.status_code, payload.get("message", "")

    # ---- ① 凭据错误会计数 ----
    reset_ip_bucket()
    sc, msg = login_from_ip()
    ok("① 验证码有效 + 密码错误 → 401 且计入该 IP",
       sc == 401 and len(auth_mod._LOGIN_FAIL_HITS.get(TEST_IP, [])) == 1,
       f"status={sc} hits={len(auth_mod._LOGIN_FAIL_HITS.get(TEST_IP, []))}")

    # ---- ② ★ 关键：验证码错误**不**计数 ----
    # 如果这里也计数，攻击者可以对着任意用户名狂发错码，把**受害者所在 IP**
    # （校园网/公司 NAT 出口）刷进冷却 —— 几次请求就能让一栋楼登不上。
    reset_ip_bucket()
    for _ in range(50):
        sc, _m = login_from_ip(captcha_ok=False)
        assert sc == 400, f"预期验证码层拒绝，实际 {sc}"
    ok("② ★ 验证码错误不累加 IP 失败计数（防区域性拒绝服务）",
       len(auth_mod._LOGIN_FAIL_HITS.get(TEST_IP, [])) == 0,
       f"50 次错码后 hits={len(auth_mod._LOGIN_FAIL_HITS.get(TEST_IP, []))}")

    # ---- ③ 达到阈值后进入冷却（换账号，单账号锁定不参与）----
    reset_ip_bucket()
    limit = auth_mod._LOGIN_FAIL_IP_LIMIT
    bad = []
    for i in range(limit):
        sc, _m = login_from_ip()
        if sc != 401:
            bad.append((i + 1, sc))
    ok(f"③ 前 {limit} 次凭据错误（轮换账号）均返回 401，未被提前拦",
       not bad, f"提前拦截={bad[:3]}")

    sc, msg = login_from_ip()
    ok("★ 超过阈值后该 IP 被冷却（400 且提示失败频繁）",
       sc == 400 and "频繁" in msg, f"status={sc} msg={msg!r}")

    # ---- ④ 冷却期内即使密码正确也拒绝（否则攻击者照样消耗 PBKDF2）----
    sc, msg = login_from_ip(user=u["username"], password=PWD)
    ok("★ 冷却期内即使密码正确也被拒（限流在比密码之前）",
       sc == 400 and "频繁" in msg, f"status={sc} msg={msg!r}")

    # ---- ⑤ 登录成功清零该 IP ----
    reset_ip_bucket()
    for _ in range(limit - 1):
        login_from_ip()
    before = len(auth_mod._LOGIN_FAIL_HITS.get(TEST_IP, []))
    sc, msg = login_from_ip(user=u["username"], password=PWD)
    after = len(auth_mod._LOGIN_FAIL_HITS.get(TEST_IP, []))
    ok("⑤ ★ 登录成功清空该 IP 的失败记录",
       sc == 200 and before == limit - 1 and after == 0,
       f"before={before} status={sc} after={after}")

    # 不清零的话，NAT 后几十人共用同一 IP 时，一个人输错几次就能把整栋楼锁死：
    # 「刚输对密码的人也进不来」。这一条守的就是这个。
    ok("⑥ 清零后可继续正常登录（不会累积到永久锁死）",
       login_from_ip(user=u["username"], password=PWD)[0] == 200, "")

    # ---- ⑦ 其他 IP 不受影响 ----
    reset_ip_bucket()
    for _ in range(limit + 1):
        login_from_ip()
    sc_other, msg_other = login_from_ip(user=u["username"], password=PWD, ip=OTHER_IP)
    ok("⑦ 限流按 IP 隔离，另一个 IP 不受影响",
       sc_other == 200, f"status={sc_other} msg={msg_other!r}")

    # ---- ⑧ 账号状态类失败不计入 IP 限流 ----
    # 「正在审批中」「账号已锁定」是**已知账号状态**，不是猜测结果。
    # 把它们算进 IP 限流会让「点了 30 次待审批账号」把整个 NAT 出口拉黑。
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        row = db.get(User, u["uid"])
        row.status = UserStatus.PENDING.value
        row.login_fail_count = 0
        row.locked_until = None
        db.commit()
    finally:
        db.close()
    reset_ip_bucket()
    key = f"k_pending_{_seq['n']}"
    _seq["n"] += 1
    put_captcha(key, text=SEED_CAPTCHA_TEXT)
    sc_p, msg_p = None, ""
    r_p = c.post("/api/v1/auth/login",
                 json={"username": u["username"], "password": PWD,
                       "captcha_key": key, "captcha": SEED_CAPTCHA_TEXT},
                 headers={"X-Real-IP": TEST_IP})
    sc_p = r_p.status_code
    msg_p = (r_p.json() if r_p.content else {}).get("message", "")
    pending_hits = len(auth_mod._LOGIN_FAIL_HITS.get(TEST_IP, []))
    ok("⑧ 账号状态类失败（审批中）不计入 IP 限流",
       sc_p == 401 and "审批" in msg_p and pending_hits == 0,
       f"status={sc_p} msg={msg_p!r} hits={pending_hits}")

    # 复原
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        row = db.get(User, u["uid"])
        row.status = UserStatus.ACTIVE.value
        row.login_fail_count = 0
        row.locked_until = None
        db.commit()
    finally:
        db.close()

    # ---- ⑨ 不存在账号的失败照常计数（防用户名枚举）----
    reset_ip_bucket()
    for _ in range(3):
        key = f"k_nouser_{_seq['n']}"
        _seq["n"] += 1
        put_captcha(key, text=SEED_CAPTCHA_TEXT)
        c.post("/api/v1/auth/login",
               json={"username": "no_such_user_zzz", "password": "x",
                     "captcha_key": key, "captcha": SEED_CAPTCHA_TEXT},
               headers={"X-Real-IP": TEST_IP})
    nouser_hits = len(auth_mod._LOGIN_FAIL_HITS.get(TEST_IP, []))
    ok("⑨ 不存在账号的失败照常计数（防用户名枚举）",
       nouser_hits == 3, f"3 次后 hits={nouser_hits}")

    reset_ip_bucket()



# ============================================================
# 主流程
# ============================================================
def main():
    print("=" * 70)
    print("离线单元回归：图形验证码强制化（S7）")
    print("=" * 70)

    u = seed_user()
    print(f"\n已建测试用户 uid={u['uid']} username={u['username']}")

    case_default_switch()
    case_enforced_true(u)
    case_enforced_false(u)
    case_one_time(u)
    case_expired(u)
    case_order(u)
    case_login_ip_rate(u)

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
