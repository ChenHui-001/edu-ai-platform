"""安全组件：密码哈希、JWT 令牌、验证码。

## 状态存储：为什么从进程内 dict 改成 DB

本模块原先有两份模块级 dict（`_REVOKED_JTIS` / `_CAPTCHA_STORE`）。
进程内状态在 `uvicorn --workers N` 下**不共享**，后果是认证变成掷硬币：

- 验证码在 A 进程签发、B 进程校验 → 查不到 key → 随机 50% 登录失败；
- 登出只在 A 进程登记吊销 → B..N 进程仍认这个 token → 登出实际不生效。

现改为 `sys_captcha` / `sys_revoked_token` / `sys_reset_code` 三张表
（见 `app/models/security_cache.py`），语义仍是「带 TTL 的一次性缓存」，
但写入与读取共享同一个 SQLite。

**未迁移**的 `_RESET_RATE_STORE`（`api/v1/auth.py`）与
`_PUBLIC_UPLOAD_HITS`（`api/v1/attachment.py`）是滥用频率计数器，
不是认证正确性状态：多 worker 下限额变 N 倍仍远低于可用爆破量级，
而落库会给匿名端点引入无鉴权的写放大面。保留内存是权衡后的选择，
不是遗漏。
"""
import base64
import hashlib
import io
import random
import secrets
import string
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import jwt
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logger import get_logger
from app.models.security_cache import Captcha, ResetCode, RevokedToken
from app.utils.common import now_local

logger = get_logger("security")

ALGORITHM = settings.ALGORITHM


# ---------------------------------------------------------------- 密码
def hash_password(password: str) -> str:
    """PBKDF2-SHA256 加盐哈希（无需额外依赖，适合轻量化部署）。"""
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 100_000)
    return f"pbkdf2_sha256${salt}${dk.hex()}"


def verify_password(plain: str, hashed: str) -> bool:
    """校验密码。"""
    try:
        algo, salt, digest = hashed.split("$")
        if algo != "pbkdf2_sha256":
            return False
        dk = hashlib.pbkdf2_hmac("sha256", plain.encode(), bytes.fromhex(salt), 100_000)
        return secrets.compare_digest(dk.hex(), digest)
    except (ValueError, AttributeError):
        return False


# ---------------------------------------------------------------- JWT
def create_access_token(subject: str | int, role: str = "", extra: Optional[Dict[str, Any]] = None) -> str:
    """签发访问令牌。"""
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload: Dict[str, Any] = {
        "sub": str(subject),
        "role": role,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access",
        "jti": secrets.token_hex(8),
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(subject: str | int) -> str:
    """签发刷新令牌。

    带 jti 才能被登出吊销：此前 refresh token 无 jti，
    用户登出后仍可用它换出新 access token（7 天内无法止损）。
    """
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh",
        "jti": secrets.token_hex(8),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_token(
    token: str,
    db: Optional[Session] = None,
    *,
    check_revocation: bool = True,
) -> Optional[Dict[str, Any]]:
    """解析令牌，失败返回 None。已登出（吊销）的令牌同样返回 None。

    吊销检查是**默认开启且 fail-closed** 的：

    - `db` 已传且 `check_revocation=True` → 查 `sys_revoked_token`，被吊销即返回 None。
    - `db` 为 None 且 `check_revocation=True` → **直接返回 None**（fail-closed）。
      这是 BUG-006 的修复：此前 db=None 会**静默跳过**吊销检查，任何认证依赖
      一旦忘记传 db，登出/改密后旧 token 依然可用。静默放行比直接拒绝危险得多，
      所以拿不到 db 时宁可拒绝。
    - `check_revocation=False` → 仅校验签名/过期，**不查吊销**。仅供**登出**
      这类"本来就要把 token 拉黑"的场景显式使用（它需要对已吊销的 token 也能
      解出 jti），其余任何认证链路都不应使用。

    认证链路（`api/deps.get_current_user`、`auth.refresh_token`）必须走默认参数并传 db。
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        return None
    if check_revocation:
        if db is None:
            logger.warning(
                "decode_token 需要吊销校验但未传 db，按无效令牌拒绝（fail-closed）；"
                "仅登出等场景可显式传 check_revocation=False"
            )
            return None
        if _is_revoked_db(db, payload.get("jti")):
            return None
    return payload


def _is_revoked_db(db: Session, jti: Optional[str]) -> bool:
    """查吊销名单：只有**未过期**的吊销记录才算数。

    `expire_at >= now` 这个条件不能省。吊销记录的有效期就是令牌自身的
    有效期 —— 存的是令牌的 `exp` 绝对时刻。令牌 `exp` 一过，`jwt.decode`
    在上一行就拒绝了，吊销记录留着也没用；反过来，如果清理没跑、
    过期行还在表里却被当成"仍吊销"，语义就变成了"吊销永不过期"，
    与旧实现（`OrderedDict` 按 `expire_at` 清理）不一致。
    加这个条件后，读路径自身就是 TTL 语义的完整实现，
    清理逻辑退化成纯粹的「不让表变大」的优化，正确性不依赖它。
    """
    if not jti:
        return False
    return db.scalar(
        select(RevokedToken.jti).where(
            RevokedToken.jti == jti,
            RevokedToken.expire_at >= now_local(),
        )
    ) is not None


# ---------------------------------------------------------------- 令牌吊销
# JWT 本身无状态，登出后若不记录就仍可被冒用。
# 吊销记录落 `sys_revoked_token`（跨进程共享），配合同表清理。
def revoke_token(payload: Optional[Dict[str, Any]], db: Optional[Session] = None) -> bool:
    """把令牌加入吊销名单。payload 为 None 或未传 db 时静默返回 False。

    名单里存的是**绝对过期时刻**，不是剩余时长 —— 存剩余时长的话它只是
    一个快照、永不递减，清理逻辑永远清不掉任何条目（旧实现即如此：
    `ttl.total_seconds() <= 0` 恒为 False，名单只增不减）。

    幂等：同 jti 重复吊销（用户连点两次登出、access+refresh 同 jti 等）
    走"先删同 jti 再插"，不会因主键冲突抛 IntegrityError 把登出打成 500。
    """
    if not payload or db is None:
        return False
    jti = payload.get("jti")
    if not jti:
        return False
    db.execute(delete(RevokedToken).where(RevokedToken.jti == jti))
    db.add(RevokedToken(jti=jti, expire_at=_to_naive_local(_token_expiry(payload))))
    db.commit()
    _maybe_purge(db, RevokedToken)
    return True


def _token_expiry(payload: Dict[str, Any]) -> datetime:
    """取令牌的真实过期时刻（aware UTC）。

    必须优先用 payload 里的 exp：JWT decode 后 exp 是 **int 时间戳**，
    旧实现只判 `isinstance(exp, datetime)`，走不到该分支就一律回落成
    ACCESS_TOKEN_EXPIRE_MINUTES（12h）。于是 **refresh token（7 天）的
    吊销记录只保留 12h**：一旦清理逻辑修好，登出 12h 后那个 refresh
    就能重新换出 access —— 登出等于没登出。两个 bug 必须一起修。
    """
    exp = payload.get("exp")
    now = datetime.now(timezone.utc)
    if isinstance(exp, datetime):
        return exp if exp.tzinfo else exp.replace(tzinfo=timezone.utc)
    if isinstance(exp, (int, float)):
        return datetime.fromtimestamp(exp, timezone.utc)
    return now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)


def _to_naive_local(dt: datetime) -> datetime:
    """把 aware UTC 时刻转成库内统一的 naive 本地时间。

    `sys_revoked_token.expire_at` 与 `_purge` 的 `now_local()` 必须在**同一
    时基**上比较，否则容器 TZ=Asia/Shanghai 时差 8 小时：UTC 19:00 存成
    naive 会被当成"本地 19:00"，实际本地已是次日 03:00 —— 记录提前 8 小时
    被清掉，登出提前失效（正是本函数要防的回归）。
    """
    if dt.tzinfo is None:
        return dt
    return dt.astimezone().replace(tzinfo=None)


def is_revoked(payload: Optional[Dict[str, Any]], db: Optional[Session] = None) -> bool:
    """判断令牌是否已吊销。全仓当前无调用点，保留为薄封装以稳定对外契约。"""
    if not payload or db is None:
        return False
    return _is_revoked_db(db, payload.get("jti"))


def _purge_revoked(db: Session) -> int:
    """清理已过期（到期时刻已过）的吊销记录，避免表无限增长。"""
    result = db.execute(
        delete(RevokedToken).where(RevokedToken.expire_at < now_local())
    )
    db.commit()
    return result.rowcount or 0


# ---------------------------------------------------------------- 图形验证码
# 图片容器尺寸（前端 .captcha-img 的 CSS 尺寸，改这里需同步改 CSS）
_CAPTCHA_W, _CAPTCHA_H = 180, 56
# 验证码字符数
_CAPTCHA_LEN = 4

# 字体候选。**容器镜像里只有 Noto CJK 字体**（fonts-noto-cjk），
# 原先只列了 Windows arialbd 与 Linux DejaVu，在容器里两个都不存在，
# 会退化到 ImageFont.load_default() —— 那是位图默认字体，
# 墨迹仅 8px 高（图片高 56px），表现为「字符极小几乎看不清」。
# 这里把容器内真实存在的 Noto 放首位，并保留本地开发时的 Windows 字体。
_CAPTCHA_FONTS = (
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    "C:/Windows/Fonts/arial.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
)
# 字号：实测 Noto 在 44px 时墨迹高 35px，占图片高度 62%，可读性最佳
_CAPTCHA_FONT_SIZE = 44


def _load_captcha_font(size: int = _CAPTCHA_FONT_SIZE):
    """加载验证码字体；全部候选缺失时回退默认字体（并记录告警）。"""
    for path in _CAPTCHA_FONTS:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    logger.warning(
        "验证码字体全部候选不可用，回退 PIL 默认字体（字符会很小）。"
        "容器构建需包含 fonts-noto-cjk；本地可安装任意 ttf。"
    )
    return ImageFont.load_default()


def generate_captcha() -> tuple[str, str]:
    """生成图形验证码，返回 (base64图片, 验证码文本)。

    可读性要点（保持 180x56 容器尺寸不变）：
    - 字号 44px：墨迹高约 35px，占图片高度 62%
    - 4 字符等分布局，左右留边距，字符不挤边
    - 干扰线 3 条（从 5 条减少）且绘制在**字符下方**，不再压字
    - 噪点 60 个（从 180 个大幅减少），颜色更浅
    - 深色高对比配色，字符颜色明显暗于干扰线
    """
    chars = "".join(random.choices(string.ascii_uppercase + string.digits, k=_CAPTCHA_LEN))
    width, height = _CAPTCHA_W, _CAPTCHA_H
    img = Image.new("RGB", (width, height), (250, 251, 253))
    draw = ImageDraw.Draw(img)

    # ---- 干扰层（先画，保证被字符压住，不影响辨认）----
    # 浅色干扰线：3 条，颜色很淡
    for _ in range(3):
        x1, y1 = random.randint(0, width), random.randint(0, height)
        x2, y2 = random.randint(0, width), random.randint(0, height)
        draw.line([x1, y1, x2, y2], fill=(214, 222, 236), width=1)

    # 浅色噪点：60 个（原 180 个，过多会淹没字符）
    for _ in range(60):
        draw.point(
            (random.randint(0, width), random.randint(0, height)),
            fill=(226, 232, 242),
        )

    font = _load_captcha_font()

    # 按字形实测宽度做等分布局：左右各留 margin，字符间均匀分布
    try:
        char_w = max(draw.textlength(ch, font=font) for ch in chars)
    except Exception:
        char_w = _CAPTCHA_FONT_SIZE * 0.6
    if char_w <= 0:
        char_w = _CAPTCHA_FONT_SIZE * 0.6
    margin = 10
    span = width - margin * 2
    step = span / max(_CAPTCHA_LEN, 1)

    # 深色高对比配色：明显暗于干扰线/噪点
    palette = [
        (24, 58, 108), (168, 40, 32), (20, 106, 74),
        (108, 58, 152), (176, 96, 12),
    ]

    for i, ch in enumerate(chars):
        # 按每字符实际墨迹高度做垂直居中，视觉更整齐
        try:
            bbox = draw.textbbox((0, 0), ch, font=font)
            ink_h = bbox[3] - bbox[1]
            top_off = bbox[1]
        except Exception:
            ink_h = int(_CAPTCHA_FONT_SIZE * 0.75)
            top_off = 0
        base_y = (height - ink_h) // 2 - top_off
        # 轻微上下随机偏移，避免字符过于规整
        base_y += random.randint(-3, 3)
        x = margin + int(i * step + (step - char_w) / 2)
        draw.text(
            (x, base_y),
            ch,
            font=font,
            fill=random.choice(palette),
        )

    img = img.filter(ImageFilter.SMOOTH)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    img_b64 = base64.b64encode(buf.getvalue()).decode()
    return img_b64, chars


def store_captcha(text: str, db: Optional[Session] = None, ttl_seconds: int = 180) -> str:
    """保存验证码，返回 key。

    `db` 为 None 时不落库，只返回一个 key —— 该 key 后续校验必然 False，
    即**失败关闭**（fail-closed），不会出现"跳过存储就等于跳过校验"的放行。
    实际调用点 `api/v1/auth.get_captcha` 始终传 db，不会走到这个分支；
    保留可选形状纯为历史签名兼容（外部脚本可能按 `store_captcha(text)` 调）。
    """
    key = secrets.token_hex(8)
    if db is not None:
        db.add(Captcha(key=key, text=text, expire_at=now_local() + timedelta(seconds=ttl_seconds)))
        db.commit()
        _maybe_purge(db, Captcha)
    return key


def verify_captcha(db: Optional[Session], key: str, text: str) -> bool:
    """校验验证码（一次性）。

    **一次性语义必须保留**：先 SELECT 再 DELETE，同一会话同一事务。
    只 SELECT 不 DELETE 的话，同一个验证码可以被重放无数次 —— 等于取消
    了图形验证码，登录爆破可直接跳过这一层。

    用 SELECT+DELETE 而非 `DELETE ... RETURNING`：后者需要 SQLite ≥ 3.35，
    而本项目的开发机 / 容器 / CI 版本不统一，不给自己埋版本坑。
    """
    if db is None or not key:
        return False
    row = db.get(Captcha, key)
    if row is None:
        return False
    stored, expire_at = row.text, row.expire_at
    # 无论校验结果如何，这条记录都必须消失：否则"输错一次"可以无限重试，
    # 4 位码（36^4 ≈ 1.7M）在过期窗口内是可爆破的。
    db.execute(delete(Captcha).where(Captcha.key == key))
    db.commit()
    if now_local() > expire_at:
        return False
    return stored.upper() == (text or "").strip().upper()


def _purge_captcha(db: Session) -> int:
    """清理过期验证码。"""
    result = db.execute(delete(Captcha).where(Captcha.expire_at < now_local()))
    db.commit()
    return result.rowcount or 0


# ---------------------------------------------------------------- 找回密码验证码
def store_reset_code(db: Session, target: str, code: str, ttl_seconds: int = 300) -> None:
    """保存找回密码验证码。同 target 覆盖写：旧码立刻失效。

    不覆盖的话，用户连点 5 次「发送验证码」就会同时存在 5 个有效码，
    爆破面随点击次数线性扩大（每次点击都是新的一次 10^6 抽样）。
    """
    db.execute(delete(ResetCode).where(ResetCode.target == target))
    db.add(ResetCode(
        target=target, code=code,
        expire_at=now_local() + timedelta(seconds=ttl_seconds),
    ))
    db.commit()
    _maybe_purge(db, ResetCode)


def verify_reset_code(db: Session, target: str, code: str) -> bool:
    """校验并消费找回密码验证码（一次性）。

    与 `verify_captcha` 同理：先取后删，无论成败都消费掉。
    """
    row = db.get(ResetCode, target)
    if row is None:
        return False
    stored, expire_at = row.code, row.expire_at
    db.execute(delete(ResetCode).where(ResetCode.target == target))
    db.commit()
    if now_local() > expire_at:
        return False
    return stored == (code or "").strip()


def _purge_reset_code(db: Session) -> int:
    """清理过期找回码。"""
    result = db.execute(delete(ResetCode).where(ResetCode.expire_at < now_local()))
    db.commit()
    return result.rowcount or 0


# ---------------------------------------------------------------- 机会式清理
# 过期行不能靠 APScheduler 清：CI 里 SCHEDULER_ENABLED=false，定时任务根本
# 不跑；而这三张表的写入量都很小（验证码每次登录 1 行、吊销每次登出 1 行），
# 攒下来的过期行会一直占着主键与索引。改为「写入时按概率顺带清一次」：
# 写放大只有 5%，却保证无论调度器开没开，过期行都不会无界增长。
# 项目既有同范式：core/rate_limit.py 每分钟（minute % 5 == 0）顺带清旧窗口。
_OPPORTUNISTIC_PURGE_RATE = 0.05

_PURGE_FUNCS = {
    "Captcha": lambda db: _purge_captcha(db),
    "RevokedToken": lambda db: _purge_revoked(db),
    "ResetCode": lambda db: _purge_reset_code(db),
}


def _maybe_purge(db: Session, model: type) -> None:
    """按 `_OPPORTUNISTIC_PURGE_RATE` 概率顺带清理该模型的过期行。

    清理失败**不能**影响主流程：验证码已经写进去了，调用方拿到的 key 是有效的，
    此时若因为清理语句把请求打成 500，反而把可用功能弄坏。因此吞异常 + 回滚，
    留一行日志即可（清理是优化，不是正确性依赖 —— 正确性由每次读时的
    `expire_at` 判定保证）。
    """
    if random.random() >= _OPPORTUNISTIC_PURGE_RATE:
        return
    func = _PURGE_FUNCS.get(model.__name__)
    if func is None:
        return
    try:
        func(db)
    except Exception as exc:  # noqa: BLE001 清理失败不影响主流程
        logger.warning(f"安全缓存清理失败（已忽略）：{exc}")
        try:
            db.rollback()
        except Exception:  # noqa: BLE001
            pass


# 常见弱口令（命中即拒绝，避免 P@ssw0rd 这类"看起来合规"的密码）
_WEAK_PASSWORDS = {
    "12345678", "123456789", "password", "passw0rd", "qwerty123", "abc12345",
    "admin123", "admin@123", "a1234567", "11111111", "88888888", "edu@123456",
}


def validate_password_strength(password: str, *, min_length: int = 8) -> None:
    """密码强度校验：长度 + 字母数字组合 + 弱口令黑名单。

    此前仅 change_password 校验长度，创建用户/管理员重置密码完全不校验，
    实测可把密码设为 "1" 并直接登录。
    """
    from app.core.exception import BusinessException

    pwd = password or ""
    if len(pwd) < min_length:
        raise BusinessException(f"密码长度不能少于 {min_length} 位")
    if len(pwd) > 64:
        raise BusinessException("密码长度不能超过 64 位")
    if pwd.lower() in _WEAK_PASSWORDS:
        raise BusinessException("密码过于简单（常见弱口令），请更换")
    has_alpha = any(c.isalpha() for c in pwd)
    has_digit = any(c.isdigit() for c in pwd)
    if not (has_alpha and has_digit):
        raise BusinessException("密码需同时包含字母和数字")
