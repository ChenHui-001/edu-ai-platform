"""Only display fields may leave private question extensions."""
import json

from pydantic import TypeAdapter, ValidationError

from app.schemas.question_visual import Visual
from app.utils.options import normalize_options

_visual_adapter = TypeAdapter(Visual)


def presentation_fields(extra):
    try:
        extra = json.loads(extra) if isinstance(extra, str) else extra
    except (ValueError, TypeError):
        extra = {}
    if not isinstance(extra, dict):
        return {}
    result = {}
    try:
        if extra.get("visual"):
            result["visual"] = _visual_adapter.validate_python(extra["visual"]).model_dump()
    except ValidationError:
        pass
    figure = extra.get("figure")
    if isinstance(figure, str) and len(figure) <= 100000:
        result["figure"] = figure
    return result


def presentation_options(raw, extra=None):
    options = normalize_options(raw)
    try:
        data = json.loads(raw) if isinstance(raw, str) else raw
        extra = json.loads(extra) if isinstance(extra, str) else extra
    except (ValueError, TypeError):
        data, extra = [], {}
    figures = (extra or {}).get("option_figures", {}) if isinstance(extra or {}, dict) else {}
    if not isinstance(figures, dict):
        figures = {}
    if isinstance(data, list):
        for index, item in enumerate(data):
            if isinstance(item, dict) and isinstance(item.get("figure"), str):
                figures = {**figures, str(item.get("key") or chr(65 + index)): item["figure"]}
    for option in options:
        option.update(presentation_fields({"figure": figures.get(option["key"])}))
    return options
