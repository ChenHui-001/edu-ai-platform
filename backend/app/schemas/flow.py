"""流程引擎的请求契约。

新端点一律用 Pydantic 模型而非裸 `Dict[str, Any] = Body(...)`：
裸 Dict 下字段名拼错不会 422（后端静默当空值处理），OpenAPI 里请求体
也显示成 `{}`——前端因此踩过字段名漂移的坑（见 app/schemas/__init__.py）。

历史兼容：这些端点的 body 是**可选**的（客户端可能只发空 body 或完全不发），
因此模型一律 `default=None`，并且字段全部可选。
"""
from typing import Optional

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class FlowActionIn(BaseModel):
    """审批动作的通用请求体（通过 / 驳回 / 取消共用）。

    extra="ignore"：流程定义未来可能引入新字段，旧的客户端不应因此报错。
    """

    model_config = ConfigDict(extra="ignore", allow_inf_nan=False)

    comment: Optional[str] = Field(default=None, max_length=1000,
                                   description="审批意见。驳回与退回是否必填由流程规则强制。")


class FlowReturnIn(BaseModel):
    """退回重填的请求体。"""

    model_config = ConfigDict(extra="ignore", allow_inf_nan=False)

    target_activity_id: str = Field(min_length=1, max_length=64,
                                    description="要退回的活动 id")
    comment: Optional[str] = Field(default=None, max_length=1000,
                                   description="退回原因")


class FlowTransferIn(BaseModel):
    """转办请求体。"""

    model_config = ConfigDict(extra="ignore", allow_inf_nan=False)

    to_user_id: int = Field(gt=0, description="接收方用户 id")
    reason: Optional[str] = Field(default=None, max_length=500,
                                  description="转办理由")


class FlowUrgeIn(BaseModel):
    """催办请求体。"""

    model_config = ConfigDict(extra="ignore", allow_inf_nan=False)

    comment: Optional[str] = Field(default=None, max_length=500,
                                   description="催办留言")


class FlowDeadlineIn(BaseModel):
    """设置待办截止时间的请求体。"""

    model_config = ConfigDict(extra="ignore", allow_inf_nan=False)

    deadline: Optional[datetime] = Field(
        default=None,
        description="截止时间；传 null 表示清除截止时间（不再计入逾期待办）",
    )
