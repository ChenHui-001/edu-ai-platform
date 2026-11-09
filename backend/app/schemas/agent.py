"""Agent 类端点的请求模型。"""
from typing import Any, Optional

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class PaperComposerRequest(BaseModel):
    """智能组卷入参（POST /agent/paper-composer）。

    旧实现是裸 Dict：前端把 `request` 写成 `requirement` 后，后端
    `data.get("request")` 静默拿到 None，再把 subject_id=0 传给 Agent，
    抛出「无法识别学科」这种与真实原因无关的报错。

    ## 为什么「迁移到 Pydantic」本身不够

    只声明 `request: str = ""` + `extra="ignore"` 时，`requirement` 会被
    当成未知字段**静默丢弃**，`request` 仍是空串 —— 报错从「无法识别学科」
    换成「请填写组卷需求」，根因（字段名漂移）一点没解决。因此：

    - `validation_alias=AliasChoices("request", "requirement")`：显式接住
      历史的错误字段名，两个名字都归一化到 `request`；
    - `total_score` 加 `ge/le`：0 或负数会让组卷引擎按 0 分卷面凑题，
      产出不可用的卷子；现在在 422 阶段就拒绝；
    - `save` / `total_score` 用 Optional 兜 `null`：旧 Dict 路径遇到 `null`
      会走 `or` 默认值，收紧成非 Optional 反而制造新的 422 面。

    `difficulty_ratio` / `type_ratio` / `knowledge_point_ids` 的形态由
    Agent 内部归一化（支持 dict / list / 百分数 / 小数），这里不做强约束，
    避免把校验责任从 Agent 里拽出来。`extra="ignore"` 同样保留：存量调用方
    可能多传模板参数，迁移不应让它们一夜之间全部 422。
    """
    model_config = ConfigDict(extra="ignore")

    request: str = Field(
        default="",
        validation_alias=AliasChoices("request", "requirement"),
        description="自然语言组卷需求；与 grade_id+subject_id 二选一",
    )
    grade_id: Optional[int] = None
    subject_id: Optional[int] = None
    total_score: Optional[float] = Field(default=100, ge=1, le=1000)
    difficulty_ratio: Any = None
    type_ratio: Any = None
    knowledge_point_ids: Any = None
    paper_name: Optional[str] = None
    save: Optional[bool] = False
