"""知识图谱诊断与先修关系的请求模型。"""
from typing import Any, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field


class DiagnosisSessionCreateIn(BaseModel):
    """创建诊断会话。

    同时兼容 `target_kp_ids` 与旧字段 `targets`；两者都为空时由业务层
    返回可读的 400，而不是在 Pydantic 层直接 422。
    """

    model_config = ConfigDict(extra="ignore")

    target_kp_ids: List[int] = Field(default_factory=list)
    targets: Optional[List[int]] = None
    student_id: Optional[int] = None
    subject_id: Optional[int] = None
    mode: str = "target"
    limit: Optional[int] = None
    confirm: Optional[int] = None
    seed: Optional[str] = None


class DiagnosisAnswerIn(BaseModel):
    model_config = ConfigDict(extra="ignore")

    knowledge_point_id: int
    question_id: Optional[Union[int, str]] = None
    answer: Any = None
    result: Optional[str] = None


class PrerequisiteCreateIn(BaseModel):
    model_config = ConfigDict(extra="ignore")

    prerequisite_id: int
    strength: str = "hard"
    reason: Optional[str] = None
    allow_cross_grade: bool = False
