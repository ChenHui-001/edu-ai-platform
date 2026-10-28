#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""离线单元回归：真实 IP 取值 + 异地登录判定（不经 HTTP，不依赖 nginx）。

## 为什么必须单独有这一层

`get_client_ip` 的正确性有两个**互相独立**的验证面：

1. **取值优先级**（X-Real-IP → XFF 末段 → 对端地址）——纯函数，可精确断言；
2. **端到端效果**（审计日志里的 IP、按 IP 的限流桶、异地登录告警）——在真实拓扑里跑。

第 1 面**在 e2e 里无法验证**。CI 与被测容器之间隔着 nginx，
`deploy/nginx/default.conf` 里 ``proxy_set_header X-Real-IP $remote_addr``
会把客户端自带的头**覆盖**掉，测试塞进去的探针 IP 到不了应用层；
XFF 也会被 ``$proxy_add_x_forwarded_for`` 追加成 ``<伪造值>, <网关地址>``。
于是 e2e 只能断言「伪造值没被采信」，而「X-Real-IP 确实被优先读取」
必须在这里用构造的 Request 断言。

异地登录同理：告警判据是 ``user.last_login_ip != ip``，经 nginx 后所有
请求都是同一个容器网关地址，端到端**造不出「两地」**。正例只能在这里
直接调 ``authenticate()`` 换 IP 验证。

## 与 e2e 的分工

| 断言 | e2e（真实拓扑） | 本文件（纯函数/纯服务） |
| --- | --- | --- |
| 伪造的 XFF 首段不入库 | ✅ | ✅ |
| X-Real-IP 优先生效 | ⚠ 仅直连时成立 | ✅ 恒成立 |
| XFF 取末段而非首段 | ⚠ 仅直连时成立 | ✅ 恒成立 |
| IP 变化触发异常告警 | ⚠ 仅直连时成立 | ✅ 恒成立 |

用法：
    python tests/test_unit_ip_login.py

退出码：0 = 全部通过，1 = 有失败。
"""
import os
import sys
import tempfile

# ---- 必须在导入 app.* 之前定好环境：避免在仓库里建出脏库、避免拉外网 ----
_TMP = tempfile.mkdtemp(prefix="unit_ip_login_")
os.environ["DATABASE_URL"] = "sqlite:///" + os.path.join(_TMP, "unit.db").replace("\\", "/")
os.environ["LLM_ENABLED"] = "false"
os.environ["SCHEDULER_ENABLED"] = "false"
os.environ.setdefault("SECRET_KEY", "unit_test_secret_key_not_for_prod")

_BACKEND = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"
)
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

from starlette.requests import Request  # noqa: E402

from app.api.deps import get_client_ip  # noqa: E402

_FAILED = []
_PASSED = 0


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


def make_request(headers=None, client=("10.9.8.7", 4321)):
    """构造一个只带请求头和对端地址的最小 http scope。

    包头 key 必须小写：Starlette 的 Headers 查找是拿小写化后的 key 去比对
    raw 列表，混合大小写会导致「明明设了头却取不到」，把用例失败伪装成
    代码缺陷。
    """
    raw = [
        (str(k).lower().encode("latin-1"), str(v).encode("latin-1"))
        for k, v in (headers or {}).items()
    ]
    scope = {
        "type": "http",
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": "/api/v1/auth/login",
        "raw_path": b"/api/v1/auth/login",
        "query_string": b"",
        "root_path": "",
        "headers": raw,
        "server": ("testserver", 80),
        "client": client,
    }
    return Request(scope)


# ============================================================
# 一、get_client_ip 取值优先级
# ============================================================
def case_client_ip():
    print("\n一、真实 IP 取值优先级（直接调 get_client_ip）")

    # 1) X-Real-IP 优先，且 XFF 首段的伪造值不生效
    ip = get_client_ip(make_request({
        "X-Real-IP": "203.0.113.77",
        "X-Forwarded-For": "10.0.0.1, 10.0.0.2",
    }))
    ok("X-Real-IP 优先于 XFF", ip == "203.0.113.77", f"取到 {ip}")

    # 2) 仅 XFF：取最后一段（nginx 追加的真值在末尾）
    ip = get_client_ip(make_request({
        "X-Forwarded-For": "10.0.0.1, 198.51.100.9",
    }))
    ok("仅 XFF 时取最后一段", ip == "198.51.100.9", f"取到 {ip}")

    # 3) 只有一段 XFF
    ip = get_client_ip(make_request({"X-Forwarded-For": "198.51.100.10"}))
    ok("单段 XFF 原样返回", ip == "198.51.100.10", f"取到 {ip}")

    # 4) X-Real-IP 是空白串 → 不能当成有效值，必须回落到 XFF
    ip = get_client_ip(make_request({
        "X-Real-IP": "   ",
        "X-Forwarded-For": "10.0.0.1, 198.51.100.11",
    }))
    ok("X-Real-IP 空白时回落 XFF 末段", ip == "198.51.100.11", f"取到 {ip}")

    # 5) XFF 里有空段/多余空格（真实客户端会这么拼）→ trim 后取末段
    ip = get_client_ip(make_request({"X-Forwarded-For": "10.0.0.1, , 198.51.100.12"}))
    ok("XFF 空段被忽略后取末段", ip == "198.51.100.12", f"取到 {ip}")

    # 6) 两个头都没有 → 对端地址兜底（直连部署的生产路径）
    ip = get_client_ip(make_request(client=("192.0.2.44", 5555)))
    ok("无转发头时取对端地址", ip == "192.0.2.44", f"取到 {ip}")

    # 7) scope 里没有 client（ASGI 允许为 None）→ 不能抛异常
    ip = get_client_ip(make_request(client=None))
    ok("client 为 None 时返回 unknown 而非炸掉", ip == "unknown", f"取到 {ip}")


# ============================================================
# 二、异地登录判定
# ============================================================
def case_abnormal_login():
    print("\n二、异地登录告警判定（直接调 auth_service.authenticate）")

    import app.models  # noqa: F401  确保全部表注册到 Base.metadata
    from sqlalchemy import select
    from sqlalchemy.orm import sessionmaker

    from app.core.database import Base, engine
    from app.core.security import hash_password
    from app.models.ops import LoginLog, Notification
    from app.models.system import IdentityType, User, UserStatus
    from app.services.auth_service import authenticate

    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)

    db = Session()
    db.add(User(
        username="unit_teacher",
        password=hash_password("Unit@123456"),
        real_name="单元测试教师",
        identity=IdentityType.TEACHER.value,
        status=UserStatus.ACTIVE.value,
        must_change_password=False,
    ))
    db.commit()
    db.close()

    def login(ip):
        s = Session()
        try:
            authenticate(s, "unit_teacher", "Unit@123456", ip=ip, device="unit-test")
            last = s.scalars(
                select(LoginLog).where(LoginLog.username == "unit_teacher")
                .order_by(LoginLog.id.desc())
            ).first()
            alert = s.scalars(
                select(Notification).where(Notification.title == "异常登录提醒")
            ).all()
            return bool(last and last.is_abnormal), len(alert)
        finally:
            s.close()

    # 首次登录：没有历史 IP，不能算异常
    abnormal1, alert1 = login("10.0.0.100")
    ok("首次登录不判定为异常", abnormal1 is False and alert1 == 0,
       f"is_abnormal={abnormal1} 告警数={alert1}")

    # 换 IP 再登：判为异常并写通知
    abnormal2, alert2 = login("10.0.0.200")
    ok("IP 变化判定为异常登录", abnormal2 is True, f"is_abnormal={abnormal2}")
    ok("IP 变化写入异常登录提醒通知", alert2 == 1, f"告警数={alert2}")

    # 同 IP 再登：不能重复报警（否则每次登录都骚扰）
    abnormal3, alert3 = login("10.0.0.200")
    ok("同一 IP 重复登录不重复告警", abnormal3 is False and alert3 == 1,
       f"is_abnormal={abnormal3} 告警数={alert3}")

    # 换回旧 IP 仍是变化 → 还要报（判据只看相邻两次，不做白名单）
    abnormal4, alert4 = login("10.0.0.100")
    ok("回切到另一 IP 仍算异常", abnormal4 is True, f"is_abnormal={abnormal4}")


def main():
    print("=" * 72)
    print("离线单元回归：真实 IP 取值 / 异地登录判定")
    print("=" * 72)
    case_client_ip()
    case_abnormal_login()
    print("\n" + "-" * 72)
    total = _PASSED + len(_FAILED)
    print(f"单元回归完成：共 {total} 项 | 通过 {_PASSED} | 失败 {len(_FAILED)}")
    if _FAILED:
        for n in _FAILED:
            print(f"  ✘ {n}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
