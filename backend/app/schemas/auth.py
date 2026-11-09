"""认证类端点的请求模型。"""
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class RefreshTokenIn(BaseModel):
    """刷新令牌入参。

    原先是 `Dict[str, str] = Body(...)`：字段名拼错、类型写错都静默通过，
    OpenAPI 里请求体显示成 `{}`。这处恰好是契约门禁的盲区 —— 旧正则只认
    `Dict[str, Any]`，换个内层类型（`Dict[str, str]`）就绕过去了。

    `refresh_token` 用默认空串而不是必填：空串会走到 decode_token 失败分支，
    返回「刷新令牌无效或已过期」这条既有业务提示；改成必填会让这类调用变成
    422，错误语义反而更模糊。
    """

    model_config = ConfigDict(extra="ignore")

    refresh_token: str = ""
    # 老调用方可能显式传 rotate=false / "0" / "no" 保持「只换 access」的旧行为，
    # 因此不收紧成 bool：字符串形态会被 str() 后按白名单判断。
    rotate: Optional[Any] = None
