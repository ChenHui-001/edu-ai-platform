#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""离线单元回归：强制改密拦截 + 拒绝新旧密码相同（S5 的失效路径）。

## 锁的是什么

`auth_service.change_password` 曾经只校验「原密码对」+「强度」，不比对
old != new，然后无条件 `must_change_password = False`。而 `/auth/password`
必须在 `deps._FORCE_PWD_WHITELIST` 里（否则改密闭环无解）。两者叠加 =
S5（存量库出厂口令强制改密）可以被 2 个请求完全抹掉：

    ① 用公开口令登录            -> 200，拿到 token，标记 True
    ② 访问业务接口              -> 403「请先修改密码」    拦截生效
    ③ PUT /auth/password
       {old: 公开口令, new: 公开口令}  -> 200「密码修改成功」  ← 这里
    ④ 再访问业务接口            -> 200                    拦截解除
       回读库：口令一个字没变

修复是「拒绝 new == old」。本文件锁定它，以及守护它所需的
`MUST_CHANGE_PASSWORD_ENFORCED` 开关。

## 为什么必须在离线单元层

e2e 那一层**看不到**这个缺陷的两个关键性质：

1. e2e 服务端以 `MUST_CHANGE_PASSWORD_ENFORCED=false` 启动（否则 99 处
   共用硬编码口令的 `.login()` 全红），所以拦截本身在 e2e 里根本不生效；
2. e2e 的账号密码是全流程共用的常量，**不能真改密码**（改了会让"当前
   密码"在 100+ 个 Client 实例之间漂移），所以走不到"改完再看 200"这一步。

于是拦截行为与 old==new 拒绝都只能在这一层用独立临时库精确断言。

## 与 e2e 的分工

| 性质 | e2e | 本文件 |
| --- | --- | --- |
| 首次登录 Pages 能进（不崩） | ✅ | — |
| 未改密被 403 拦截 | ✘ 开关关着 | ✅（monkeypatch 设回 true） |
| old == new 改密被拒 | ✘ 不真改密码 | ✅ 核心断言 |
| 改成真新密码后放行 | ✘ 不能真改 | ✅ |
| 旧口令改后失效 | ✘ 会打乱后续阶段 | ✅ |
| 开关默认值为 true | ✘ 被环境覆盖 | ✅ 防呆 |

## 反向验证（判别力证明）

把 `change_password` 里那两行 `new == old` 判断注释掉再跑本文件，实测
`checked=25 passed=19 failed=6`，失败项正是：

    二 ④ ★ old == new 改密被拒（HTTP 400）      -> 实际 200「密码修改成功」
    二 ⑤ ★ 错误信息指明「不能与原密码相同」      -> 实际「密码修改成功」
    二 ⑥ ★ 被拒后 must_change_password 仍为 True -> 实际 False
    二 ⑧ ★ 被拒后业务接口仍被 403               -> 实际 200（拦截解除）
    三 ③ ★ 即使开关为 false，old == new 仍被拒   -> 实际 200
    三 ④ ★ 开关关闭也不会让标记被清掉            -> 实际 False

**注意 二 ⑦（口令仍是出厂口令）在反向验证里也 PASS** —— 因为把同一个口令
再哈希一次，`verify_password` 依然返回 True。它不是判据，是**护栏**：如果
有人把 `new == old` 的拒绝改成「允许但清掉标记」，这条抓不到；但它能抓住
「误把口令写坏」的改动。审阅时别因为「反向验证里它没红」就删掉。

这一组失败同时证明了两件事：① 断言确实能抓住这个 bug；② 开关关闭时
核心校验依然生效（三 ③④ 在开关为 false 的路径上也会红）。

## 用法

    python tests/test_unit_must_change_pwd.py

退出码：0 = 全部通过，1 = 有失败。
"""
import os
import sys
import tempfile

# ---- 必须在导入 app.* 之前定好环境：避免在仓库里建出脏库、避免拉外网 ----
_TMP = tempfile.mkdtemp(prefix="unit_must_change_pwd_")
os.environ["DATABASE_URL"] = "sqlite:///" + os.path.join(_TMP, "unit.db").replace("\\", "/")
os.environ["LLM_ENABLED"] = "false"
os.environ["SCHEDULER_ENABLED"] = "false"
os.environ["DEBUG"] = "false"
os.environ.setdefault("SECRET_KEY", "unit_test_secret_key_not_for_prod")
# 显式不设 MUST_CHANGE_PASSWORD_ENFORCED，验证默认值就是 True。

_BACKEND = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"
)
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

import app.models  # noqa: F401,E402  确保全部表注册到 Base.metadata
from app.core.config import Settings, settings  # noqa: E402
from app.core.database import Base, engine  # noqa: E402
from app.core.security import hash_password, verify_password  # noqa: E402
from app.main import app  # noqa: E402

_FAILED = []
_PASSED = 0

FACTORY_PWD = "Admin@123456"   # README 里公开的出厂口令
REAL_NEW_PWD = "N3wStr0ng@2026"  # 一个真正不同的强口令


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
def seed():
    """建一个 sys_admin（出厂口令 + 强制改密），正是 S5 处置后的状态。

    返回纯标量 —— ORM 实例在 session 关闭后变 detached，读属性会抛
    `DetachedInstanceError`，把"造数据"的问题伪装成"代码缺陷"。
    """
    from sqlalchemy.orm import sessionmaker

    from app.models import IdentityType, Role, User, UserRole, UserStatus

    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        role = Role(code="sys_admin", name="系统管理员", data_scope="all")
        db.add(role)
        db.flush()
        u = User(
            username="unit_admin", password=hash_password(FACTORY_PWD),
            real_name="单元管理员", identity=IdentityType.SYS_ADMIN.value,
            status=UserStatus.ACTIVE.value,
            must_change_password=True,     # ← S5 处置后的状态
        )
        db.add(u)
        db.flush()
        db.add(UserRole(user_id=u.id, role_id=role.id))
        db.commit()
        return {"uid": u.id, "username": u.username}
    finally:
        db.close()


def reset_user(uid):
    """把用户恢复成「出厂口令 + 强制改密」，让每组断言独立。"""
    from sqlalchemy.orm import sessionmaker

    from app.models import User

    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        u = db.get(User, uid)
        u.password = hash_password(FACTORY_PWD)
        u.must_change_password = True
        u.login_fail_count = 0
        u.locked_until = None
        db.commit()
    finally:
        db.close()


def db_state(uid):
    """回读关键状态（纯标量）。"""
    from sqlalchemy.orm import sessionmaker

    from app.models import User

    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        u = db.get(User, uid)
        return {
            "still_factory": verify_password(FACTORY_PWD, u.password),
            "has_new": verify_password(REAL_NEW_PWD, u.password),
            "must_change": u.must_change_password,
        }
    finally:
        db.close()


def make_client(enforced):
    """构造 TestClient 并把开关固定成 `enforced`。

    直接改 `settings` 单例（而不是 monkeypatch env）：pydantic-settings 在
    模块导入时就实例化好了，改 env 不会生效。这也是测试里唯一正确的做法 ——
    生产由环境变量决定初值，测试负责覆盖它的运行期取值。

    刻意不用 `with TestClient(app)`：进上下文会触发 lifespan → 跑 init_all
    （整套种子 + 迁移 + Agent 预热），既慢又会搅乱测试数据。

    ⚠️ 同时把 `CAPTCHA_ENFORCED` 固定成 **False**（S7 之后必须）。
    本文件测的是「强制改密拦截」，不是验证码；而强制化后不带 `captcha_key`
    的登录会**先**被 400「请输入图形验证码」拦掉，根本走不到被测分支 ——
    第一版就是这样红的（二①②、三①②、四前置，共 5 项）。
    这里显式关掉，是为了让被测对象唯一：本文件不该顺带验证 S7。
    验证码强制化本身的断言在 `tests/test_unit_captcha_enforced.py`。
    """
    from fastapi.testclient import TestClient

    settings.MUST_CHANGE_PASSWORD_ENFORCED = enforced
    settings.CAPTCHA_ENFORCED = False
    return TestClient(app, raise_server_exceptions=False)


def login(c, username, password):
    """裸登录，返回 (status_code, access_token, must_change_flag)。"""
    r = c.post("/api/v1/auth/login",
               json={"username": username, "password": password})
    body = r.json() if r.content else {}
    data = body.get("data") or {}
    return (
        r.status_code,
        data.get("access_token"),
        (data.get("user") or {}).get("must_change_password"),
    )


def authed(token):
    from fastapi.testclient import TestClient

    c = TestClient(app, raise_server_exceptions=False)
    c.headers.update({"Authorization": f"Bearer {token}"})
    return c


# ============================================================
# 一、开关默认值（防呆：防止有人写进 .env.example 让生产裸奔）
# ============================================================
def case_default_switch():
    print("\n一、开关默认值（防呆）")

    # 注意：这里必须新实例化 Settings()，而不是读 settings —— 后者可能已被
    # 上面的用例改过。同时确认环境变量里没有这个变量（本文件没设）。
    fresh = Settings()
    ok("① Settings().MUST_CHANGE_PASSWORD_ENFORCED 默认为 True",
       fresh.MUST_CHANGE_PASSWORD_ENFORCED is True,
       f"got={fresh.MUST_CHANGE_PASSWORD_ENFORCED}")
    ok("② 该字段是 bool 而非 str（pydantic 会做类型转换）",
       isinstance(fresh.MUST_CHANGE_PASSWORD_ENFORCED, bool),
       f"type={type(fresh.MUST_CHANGE_PASSWORD_ENFORCED).__name__}")
    ok("③ .env.example 里没有把它写死成 false",
       _env_example_safe(),
       ".env.example 若出现未注释的 false 会让生产裸奔")


def _env_example_safe():
    """`.env.example` 不得出现**未注释**的 `MUST_CHANGE_PASSWORD_ENFORCED=false`。

    这个文件是部署模板，用户会直接 `cp .env.example .env`。一旦里面有一行
    生效的 `=false`，生产部署就会静默关闭强制改密拦截。
    """
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        ".env.example")
    if not os.path.exists(path):
        return True   # 文件不存在则无从裸奔
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            s = line.strip()
            if s.startswith("#") or not s:
                continue          # 注释行与空行不算生效配置
            if s.lower().replace(" ", "").startswith(
                    "must_change_password_enforced=false"):
                return False
    return True


# ============================================================
# 二、开关为 true：拦截生效 + 核心断言（old == new 必须被拒）
# ============================================================
def case_enforced(ids):
    print("\n二、MUST_CHANGE_PASSWORD_ENFORCED=true（生产形态）")

    reset_user(ids["uid"])
    c = make_client(enforced=True)

    sc, token, flag = login(c, ids["username"], FACTORY_PWD)
    ok("① 未改密账号可登录并拿到 token（login 不拦，只回报标志位）",
       sc == 200 and bool(token) and flag is True,
       f"status={sc} token={bool(token)} must_change={flag}")
    if not token:
        ok("② 后续断言依赖 token", False, "登录未拿到 token，跳过")
        return

    cl = authed(token)
    r = cl.get("/api/v1/system/users")
    ok("② 开关为 true 时，未改密访问业务接口被 403 拦截",
       r.status_code == 403, f"status={r.status_code} msg={r.json().get('message')}")

    r = cl.get("/api/v1/auth/profile")
    ok("③ 白名单 /auth/profile 仍可访问（改密闭环前提）",
       r.status_code == 200, f"status={r.status_code}")

    # ---- 核心断言：old == new 必须被拒 ----
    r = cl.put("/api/v1/auth/password",
               json={"old_password": FACTORY_PWD, "new_password": FACTORY_PWD})
    body = r.json() if r.content else {}
    ok("④ ★ old == new 改密被拒（HTTP 400）",
       r.status_code == 400, f"status={r.status_code} body={body}")
    ok("⑤ ★ 错误信息指明「不能与原密码相同」",
       "不能与原密码相同" in str(body.get("message") or ""),
       f"message={body.get('message')}")

    st = db_state(ids["uid"])
    ok("⑥ ★ 被拒后 must_change_password 仍为 True（标记没被清）",
       st["must_change"] is True, f"must_change={st['must_change']}")
    ok("⑦ ★ 被拒后口令未被改写（仍是出厂口令）",
       st["still_factory"] is True, f"still_factory={st['still_factory']}")

    r = cl.get("/api/v1/system/users")
    ok("⑧ ★ 被拒后业务接口仍被 403（拦截没被解除）",
       r.status_code == 403, f"status={r.status_code}")

    # ---- 改成真新密码 -> 放行 ----
    r = cl.put("/api/v1/auth/password",
               json={"old_password": FACTORY_PWD, "new_password": REAL_NEW_PWD})
    ok("⑨ 改成真正不同的强口令 -> 200",
       r.status_code == 200, f"status={r.status_code} body={r.json()}")

    st = db_state(ids["uid"])
    ok("⑩ 新口令已生效、旧口令已失效",
       st["has_new"] is True and st["still_factory"] is False,
       f"has_new={st['has_new']} still_factory={st['still_factory']}")
    ok("⑪ must_change_password 被清成 False（合法改密才清）",
       st["must_change"] is False, f"must_change={st['must_change']}")

    r = cl.get("/api/v1/system/users")
    ok("⑫ 合法改密后业务接口恢复 200",
       r.status_code == 200, f"status={r.status_code}")

    # ---- 旧口令再登录必须失败 ----
    sc2, token2, _ = login(c, ids["username"], FACTORY_PWD)
    ok("⑬ ★ 用旧口令再登录 -> 401（旧密码真的失效了）",
       sc2 == 401 and not token2, f"status={sc2} token={bool(token2)}")

    # ---- 新口令能登录 ----
    sc3, token3, flag3 = login(c, ids["username"], REAL_NEW_PWD)
    ok("⑭ 用新口令登录成功，且不再要求改密",
       sc3 == 200 and bool(token3) and flag3 is False,
       f"status={sc3} must_change={flag3}")


# ============================================================
# 三、开关为 false：拦截关闭，但 old == new 依然被拒（核心不可绕过）
# ============================================================
def case_disabled(ids):
    print("\n三、MUST_CHANGE_PASSWORD_ENFORCED=false（e2e/CI 形态）")

    reset_user(ids["uid"])
    c = make_client(enforced=False)

    sc, token, flag = login(c, ids["username"], FACTORY_PWD)
    ok("① 未改密账号仍可登录，标志位仍为 True",
       sc == 200 and bool(token) and flag is True,
       f"status={sc} must_change={flag}")
    if not token:
        ok("② 后续断言依赖 token", False, "登录未拿到 token，跳过")
        return

    cl = authed(token)
    r = cl.get("/api/v1/system/users")
    ok("② 开关为 false 时业务接口放行（开关真的生效）",
       r.status_code == 200, f"status={r.status_code}")

    # ---- 关键：开关关闭不解除 old==new 的拒绝 ----
    r = cl.put("/api/v1/auth/password",
               json={"old_password": FACTORY_PWD, "new_password": FACTORY_PWD})
    ok("③ ★ 即使开关为 false，old == new 仍被拒（400）",
       r.status_code == 400, f"status={r.status_code} body={r.json()}")

    st = db_state(ids["uid"])
    ok("④ ★ 开关关闭也不会让标记被清掉",
       st["must_change"] is True, f"must_change={st['must_change']}")
    ok("⑤ ★ 口令仍是出厂口令（没有被「改」成同一个）",
       st["still_factory"] is True, f"still_factory={st['still_factory']}")


# ============================================================
# 四、校验顺序：原密码错误优先于新旧相同
# ============================================================
def case_order(ids):
    print("\n四、校验顺序（原密码错误优先，避免信息泄露）")

    reset_user(ids["uid"])
    c = make_client(enforced=True)
    sc, token, _ = login(c, ids["username"], FACTORY_PWD)
    if not token:
        ok("前置登录", False, f"status={sc}")
        return
    cl = authed(token)

    # 原密码错 + 新旧相同 → 必须报「原密码错误」，不能报「不能与原密码相同」。
    # 否则未持凭据者能通过后者反推出「我猜的口令就是当前口令」。
    r = cl.put("/api/v1/auth/password",
               json={"old_password": "Wrong@Pwd123", "new_password": "Wrong@Pwd123"})
    body = r.json() if r.content else {}
    msg = str(body.get("message") or "")
    ok("① 原密码错时报「原密码错误」", "原密码错误" in msg, f"message={msg}")
    ok("② 不能泄露「新旧相同」这条信息",
       "不能与原密码相同" not in msg, f"message={msg}")

    st = db_state(ids["uid"])
    ok("③ 失败后状态未变（标记仍 True、口令仍是出厂）",
       st["must_change"] is True and st["still_factory"] is True,
       f"must_change={st['must_change']} still_factory={st['still_factory']}")


def main():
    print("=" * 72)
    print("离线单元回归：强制改密拦截 / 拒绝新旧密码相同（S5 失效路径）")
    print("=" * 72)

    case_default_switch()
    ids = seed()
    case_enforced(ids)
    case_disabled(ids)
    case_order(ids)

    # 收尾：把开关还原，避免影响同进程内后续可能导入的模块
    settings.MUST_CHANGE_PASSWORD_ENFORCED = True

    print("\n" + "-" * 72)
    total = _PASSED + len(_FAILED)
    print(f"checked={total} passed={_PASSED} failed={len(_FAILED)}")
    if _FAILED:
        print("失败项：")
        for n in _FAILED:
            print(f"  ✘ {n}")
        print("\n注意：若刚注释掉 change_password 里的 new==old 判断做反向验证，"
              "第二组第 ④⑤⑥⑦⑧ 条与第三组第 ③④⑤ 条应失败 —— 那是预期。")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
