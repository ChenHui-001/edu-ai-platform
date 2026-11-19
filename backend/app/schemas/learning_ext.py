"""Validated contracts for the learning extensions."""
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


class PlanCreate(BaseModel):
    diagnosis_id: int = Field(gt=0)


class QuizStart(BaseModel):
    step_id: int = Field(gt=0)
    stage: Literal["practice", "retest", "review"]
    version: int = Field(gt=0)


class QuizSubmit(BaseModel):
    quiz_id: str = Field(min_length=1, max_length=64)
    answers: Dict[str, Any] = Field(max_length=30)
    version: int = Field(gt=0)

    @field_validator("answers")
    @classmethod
    def bounded_answers(cls, values):
        for key, value in values.items():
            if not key.isdigit() or len(key) > 20:
                raise ValueError("题目标识必须为数字")
            if isinstance(value, list):
                if len(value) > 20 or any(not isinstance(item, str) or len(item) > 20 for item in value):
                    raise ValueError("多选答案超出限制")
            elif value is not None and (
                not isinstance(value, (str, int, float)) or len(str(value)) > 2000
            ):
                raise ValueError("答案格式不正确或超出限制")
        return values


class ClassAssignment(BaseModel):
    class_id: int = Field(gt=0)
    subject_id: int = Field(gt=0)
    knowledge_point_ids: List[int] = Field(min_length=1, max_length=20)
    count: int = Field(default=10, ge=1, le=30)
    due_days: int = Field(default=7, ge=1, le=30)


class TutorAsk(BaseModel):
    question_id: int = Field(gt=0)
    stage: Literal["hint", "steps", "answer"] = "hint"


class FeedbackCreate(BaseModel):
    question_id: int = Field(gt=0)
    stage: Literal["hint", "steps", "answer"] = "hint"
    content: str = Field(min_length=1, max_length=2000)


class FeedbackReview(BaseModel):
    correction: str = Field(min_length=1, max_length=4000)
    confirm_scope: bool = False


class QualityPublish(BaseModel):
    ids: List[int] = Field(min_length=1, max_length=50)


class SyncPreview(BaseModel):
    ref: str = Field(default="main", min_length=1, max_length=80, pattern=r"^[A-Za-z0-9_.-]+$")


class SyncApply(BaseModel):
    preview_id: int = Field(gt=0)
    version: Optional[str] = None
