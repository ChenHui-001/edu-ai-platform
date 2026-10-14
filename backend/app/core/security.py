"""安全组件：密码哈希、JWT 令牌、验证码。"""
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

from app.core.config import settings

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
    """签发刷新令牌。"""
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """解析令牌，失败返回 None。"""
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        return None


# ---------------------------------------------------------------- 图形验证码
_CAPTCHA_STORE: Dict[str, tuple[str, datetime]] = {}


def generate_captcha() -> tuple[str, str]:
    """生成图形验证码，返回 (base64图片, 验证码文本)。"""
    chars = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
    width, height = 120, 40
    img = Image.new("RGB", (width, height), (246, 248, 252))
    draw = ImageDraw.Draw(img)

    # 干扰线
    for _ in range(5):
        x1, y1 = random.randint(0, width), random.randint(0, height)
        x2, y2 = random.randint(0, width), random.randint(0, height)
        draw.line([x1, y1, x2, y2], fill=(190, 200, 220), width=1)

    # 噪点
    for _ in range(180):
        draw.point((random.randint(0, width), random.randint(0, height)), fill=(215, 220, 230))

    font = None
    for candidate in [
        "C:/Windows/Fonts/arialbd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]:
        try:
            font = ImageFont.truetype(candidate, 28)
            break
        except OSError:
            continue
    if font is None:
        font = ImageFont.load_default()

    # 每个字符随机偏移与颜色
    palette = [(46, 89, 132), (176, 58, 46), (35, 118, 84), (122, 74, 165)]
    for i, ch in enumerate(chars):
        draw.text(
            (12 + i * 26, random.randint(4, 10)),
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
