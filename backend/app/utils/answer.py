# -*- coding: utf-8 -*-
"""客观题答案规范化与比较。

同一道题在历史数据/导入模板/页面建题中可能存在多种答案写法：

- 判断题：``正确/错误``、``对/错``、``T/F``、``true/false``、``A/B``
- 多选题：JSON 数组 ``["A","C"]``、字符串 ``"A,C"`` / ``"A、C"`` / ``"AC"``
- 单选题/填空题：普通字符串

判分前必须统一为「选项 key 集合」再比较。此前 grading_agent 只对 JSON 数组
做集合比较，而页面新建判断题时标准答案保存的是「正确」（选项 key 是 A/B），
导致学生选 A 永远判错；导入的多选题答案若是 "A,C" 字符串也永远判错。
"""
import json
import re
from typing import Any, Set

# 判断题标准答案的等价写法（统一映射到选项 key A/B）
_JUDGE_TRUE = {"T", "TRUE", "正确", "对", "√", "是", "A", "YES", "Y"}
_JUDGE_FALSE = {"F", "FALSE", "错误", "错", "×", "否", "B", "NO", "N"}

_MULTI_TYPES = {"multiple"}
_ANSWER_SEPARATORS = re.compile(r"[\s、,，;；/|]+")


def _norm_token(value: Any) -> str:
    """把单个答案片段规范化为可比较的 token（去空白/标点、转大写）。"""
    return _ANSWER_SEPARATORS.sub("", str(value if value is not None else "").strip().upper())


def to_token_set(value: Any) -> Set[str]:
    """把任意答案值拆成 token 集合。"""
    if value is None:
        return set()

    parsed: Any = value
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return set()
        if text.startswith("[") or text.startswith("{"):
            try:
                parsed = json.loads(text)
            except (TypeError, ValueError):
                parsed = text

    if isinstance(parsed, str):
        return {t for part in _ANSWER_SEPARATORS.split(parsed) if (t := _norm_token(part))}

    if isinstance(parsed, (list, tuple, set)):
        return {t for item in parsed if (t := _norm_token(item))}

    token = _norm_token(parsed)
    return {token} if token else set()


def normalize_answer(question_type: str, value: Any) -> Set[str]:
    """按题型把答案归一化为选项 key 集合。"""
    tokens = to_token_set(value)

    if question_type == "judge":
        normalized: Set[str] = set()
        for token in tokens:
            if token in _JUDGE_TRUE:
                normalized.add("A")
            elif token in _JUDGE_FALSE:
                normalized.add("B")
            else:
                normalized.add(token)
        return normalized

    if question_type in _MULTI_TYPES:
        # "AC" 这类连续选项串拆成 {"A","C"}；其余 token 原样保留
        expanded: Set[str] = set()
        for token in tokens:
            if len(token) > 1 and token.isalpha() and all(c in "ABCDEFGH" for c in token):
                expanded.update(token)
            else:
                expanded.add(token)
        return expanded

    return tokens


def answers_match(question_type: str, standard: Any, student: Any) -> bool:
    """判断学生答案与标准答案是否一致（空答案一律判错）。"""
    std = normalize_answer(question_type, standard)
    if not std:
        return False
    return std == normalize_answer(question_type, student)
