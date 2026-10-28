"""安全组件：密码哈希、JWT 令牌、验证码。"""
import base64
import hashlib
import io
import random
import secrets
import string
from collections import OrderedDict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import jwt
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from app.core.config import settings
from app.core.logger import get_logger

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


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """解析令牌，失败返回 None。已登出（吊销）的令牌同样返回 None。"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        return None
    if payload.get("jti") and payload["jti"] in _REVOKED_JTIS:
        return None
    return payload


# ---------------------------------------------------------------- 令牌吊销
# JWT 本身无状态，登出后若不记录就仍可被冒用。
# 这里用进程内集合保存被吊销的 jti，配合 ACCESS_TOKEN_EXPIRE_MINUTES
# 自动过期清理；多副本部署时应替换为 Redis。
_REVOKED_JTIS: "OrderedDict[str, datetime]" = OrderedDict()


def revoke_token(payload: Optional[Dict[str, Any]]) -> bool:
    """把令牌加入吊销名单。payload 为 None 时静默返回 False。

    名单里存的是**绝对过期时刻**，不是剩余时长 —— 存剩余时长的话它只是
    一个快照、永不递减，清理逻辑永远清不掉任何条目（旧实现即如此：
    `ttl.total_seconds() <= 0` 恒为 False，名单只增不减）。
    """
    if not payload:
        return False
    jti = payload.get("jti")
    if not jti:
        return False
    _REVOKED_JTIS[jti] = _token_expiry(payload)
    _purge_revoked()
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


def is_revoked(payload: Optional[Dict[str, Any]]) -> bool:
    return bool(payload) and payload.get("jti") in _REVOKED_JTIS


def _purge_revoked() -> None:
    """清理已过期（到期时刻已过）的吊销记录，避免集合无限增长。"""
    if not _REVOKED_JTIS:
        return
    now = datetime.now(timezone.utc)
    dead = [j for j, expires_at in _REVOKED_JTIS.items() if expires_at <= now]
    for j in dead:
        _REVOKED_JTIS.pop(j, None)


# ---------------------------------------------------------------- 图形验证码
_CAPTCHA_STORE: Dict[str, tuple[str, datetime]] = {}

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


def store_captcha(text: str, ttl_seconds: int = 180) -> str:
    """保存验证码，返回 key。"""
    key = secrets.token_hex(8)
    _CAPTCHA_STORE[key] = (text, datetime.now() + timedelta(seconds=ttl_seconds))
    _purge_captcha()
    return key


def verify_captcha(key: str, text: str) -> bool:
    """校验验证码（一次性）。"""
    item = _CAPTCHA_STORE.pop(key, None)
    if not item:
        return False
    stored, expire = item
    if datetime.now() > expire:
        return False
    return stored.upper() == text.strip().upper()


def _purge_captcha() -> None:
    now = datetime.now()
    for k in [k for k, (_, exp) in _CAPTCHA_STORE.items() if exp < now]:
        _CAPTCHA_STORE.pop(k, None)


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
