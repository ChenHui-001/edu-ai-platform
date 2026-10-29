"""安全缓存模型：验证码、JWT 吊销名单、找回密码验证码。

## 为什么落库而不是放进程内 dict

这三类状态有一个共同点：**写入与读取必须发生在同一个存储里**，
否则认证就是随机的。原先三处都是模块级 dict：

- `_CAPTCHA_STORE`：`GET /auth/captcha` 落在 A 进程，`POST /auth/login`
  被 nginx 轮询到 B 进程 → key 查不到 → 用户看到「验证码错误或已过期」，
  且重试仍然 50% 失败（用户会误以为自己输错了）。
- `_REVOKED_JTIS`：登出只在当前进程生效，另外 N-1 个进程仍认这个 token，
  登出实际不生效，token 泄露后 12h 内仍可用。
- `_RESET_CODE_STORE`：找回密码同理，5 分钟内随机失败。

因此这三张表是 `uvicorn --workers N` 的硬前置。

## 为什么不迁 `_RESET_RATE_STORE` / `_PUBLIC_UPLOAD_HITS`

它们守的是**滥用频率**而非**认证正确性**：多 worker 下限额变成 N 倍，
但 5×N 次/10min 仍远低于可用爆破量级（6 位码要 10^6 次），
风险是有界的、可接受的；而落库会给匿名端点引入无鉴权的写放大面。
详见 `api/v1/auth.py:_RESET_RATE_STORE` 与
`api/v1/attachment.py:_PUBLIC_UPLOAD_HITS` 处的注释。

## 时间比较的一个坑（务必遵守）

`expire_at` 一律由 Python 绑定 `datetime` 参数比较，**绝不与
`CURRENT_TIMESTAMP` 混用**：SQLite 的 DATETIME 列存的是字符串，
字典序比较 —— `now_local()` 写入带微秒（`YYYY-MM-DD HH:MM:SS.ffffff`），
`CURRENT_TIMESTAMP` 不带（`YYYY-MM-DD HH:MM:SS`）。同秒内比较时
`"...12.000000" < "...12"` 为真（`.` 的 ASCII 小于空格之外的正常字符序，
实际是短串为前缀时短串更小），过期判定会错。统一走 `now_local()`。
"""
from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.utils.common import now_local


class Captcha(Base):
    """图形验证码：一次性，校验即删。

    key 是随机 16 位十六进制（`secrets.token_hex(8)`），不承载任何用户信息，
    因此不需要与用户绑定；`text` 只存明文 4 位字符（大小写不敏感比较）。
    """

    __tablename__ = "sys_captcha"

    key: Mapped[str] = mapped_column(String(32), primary_key=True)
    text: Mapped[str] = mapped_column(String(8))
    expire_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_local)


class RevokedToken(Base):
    """已吊销 JWT 的 jti。

    `expire_at` 存的是令牌的**绝对过期时刻**（UTC，来自 payload.exp），
    不是「剩余时长」—— 存剩余时长的话它只是一个快照、永不递减，
    清理逻辑永远清不掉任何条目（旧实现即如此：`ttl.total_seconds() <= 0`
    恒为 False，名单只增不减）。

    过期行被清掉是**正确**行为：令牌本身已经 `exp` 失效，`jwt.decode`
    会先判过期并拒绝，吊销记录不再需要。
    """

    __tablename__ = "sys_revoked_token"

    jti: Mapped[str] = mapped_column(String(32), primary_key=True)
    expire_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_local)


class ResetCode(Base):
    """找回密码验证码：一次性。

    主键是 target（邮箱或手机号），语义是**同 target 覆盖写**：
    用户重复点击「发送验证码」时，旧码必须立刻失效，否则会同时存在
    多个有效码，爆破面随点击次数线性扩大。
    """

    __tablename__ = "sys_reset_code"

    target: Mapped[str] = mapped_column(String(128), primary_key=True)
    code: Mapped[str] = mapped_column(String(8))
    expire_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_local)
