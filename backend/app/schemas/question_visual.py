"""Bounded, passive drawing specifications for shared question rendering."""
from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field, model_validator


class DrawingModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class NumberPoint(DrawingModel):
    value: float = Field(ge=-1000, le=1000)
    label: str = Field(default="", max_length=40)


class NumberLine(DrawingModel):
    kind: Literal["number_line"]
    min: float = Field(ge=-1000, le=999)
    max: float = Field(gt=-1000, le=1000)
    points: list[NumberPoint] = Field(default_factory=list, max_length=20)

    @model_validator(mode="after")
    def valid_range(self):
        if self.max - self.min < 0.001 or any(
            point.value < self.min or point.value > self.max for point in self.points
        ):
            raise ValueError("数轴范围或标记位置不正确")
        return self


class Fraction(DrawingModel):
    kind: Literal["fraction"]
    numerator: int = Field(ge=0, le=20)
    denominator: int = Field(ge=1, le=20)

    @model_validator(mode="after")
    def proper_fraction(self):
        if self.numerator > self.denominator:
            raise ValueError("示意图分子不能超过分母")
        return self


class PolygonPoint(DrawingModel):
    x: float = Field(ge=0, le=400)
    y: float = Field(ge=0, le=240)
    label: str = Field(default="", max_length=40)


class Polygon(DrawingModel):
    kind: Literal["polygon"]
    points: list[PolygonPoint] = Field(min_length=3, max_length=20)


Visual = Annotated[Union[NumberLine, Fraction, Polygon], Field(discriminator="kind")]


class VisualUpdate(BaseModel):
    visual: Visual | None
