"""API 请求契约层。

历史上所有端点都用裸 `Dict[str, Any] = Body(...)`：字段拼错不会 422、
类型错误要到 SQL 层才炸、OpenAPI 里请求体显示成 `{}`。前端因此踩过
`requirement` / `request` 这类字段名漂移（见 P0-3，字段错了后端静默
当空值处理）。新端点一律从这里取 Pydantic 模型；存量按「写接口优先」
逐步迁移，迁移时保留宽松兼容（extra="ignore"）。
"""
from app.schemas.agent import PaperComposerRequest
from app.schemas.auth import RefreshTokenIn
from app.schemas.question import QuestionBatchCreateIn

__all__ = ["PaperComposerRequest", "QuestionBatchCreateIn", "RefreshTokenIn"]
