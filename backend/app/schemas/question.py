"""题库类端点的请求模型。"""
from typing import Any, Dict, List

from pydantic import BaseModel, ConfigDict


class QuestionBatchCreateIn(BaseModel):
    """批量新增题目入参（POST /question/questions/batch-create）。

    `items` 里每道题的结构与单题新增完全一致，因此这里**不**逐字段建模：
    逐字段建模会让单题与批量两条路径各有一份校验，口径迟早漂移。
    真正的字段校验统一在 `api.v1.question._prepare_question` 里做，
    失败按条进 skipped（这是本接口的核心语义，不能变成整体 422）。

    `extra="ignore"` 与 `PaperComposerRequest` 保持同一策略：存量调用方
    多传字段不应变成 422。
    """
    model_config = ConfigDict(extra="ignore")

    items: List[Dict[str, Any]] = []
