"""Agent 类端点的请求模型。"""
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class PaperComposerRequest(BaseModel):
    """智能组卷入参（POST /agent/paper-composer）。

    旧实现是裸 Dict：前端把 `request` 写成 `requirement` 后，后端
    `data.get("request")` 静默拿到 None，再把 subject_id=0 传给 Agent，
    抛出「无法识别学科」这种与真实原因无关的报错。

    `extra="ignore"` 是**刻意保留的兼容策略**：存量调用方可能多传字段
    （如模板参数），迁移到 Pydantic 不能让它们一夜之间变成 422。
    `difficulty_ratio` / `type_ratio` / `knowledge_point_ids` 的形态由
    Agent 内部归一化，这里不做强约束，避免把校验责任从 Agent 里拽出来。
    """
    model_config = ConfigDict(extra="ignore")

    request: str = ""
    grade_id: Optional[int] = None
    subject_id: Optional[int] = None
    total_score: float = 100
    difficulty_ratio: Any = None
    type_ratio: Any = None
    knowledge_point_ids: Any = None
    paper_name: Optional[str] = None
    save: bool = False
