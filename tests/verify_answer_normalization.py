# -*- coding: utf-8 -*-
"""客观题答案规范化回归验证（stdlib，无需 pytest）。

运行：cd backend && python ../tests/verify_answer_normalization.py
背景：页面新建判断题标准答案存「正确」，学生提交选项 key「A」；
导入多选题答案常见 "A,C" 字符串。判分必须等价识别。
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"))

from app.agents.grading_agent import GradingAgent  # noqa: E402
from app.models import Question  # noqa: E402
from app.utils.answer import answers_match  # noqa: E402


def expect(question_type: str, std, stu, want: bool) -> None:
    got = answers_match(question_type, std, stu)
    assert got == want, f"{question_type} std={std!r} stu={stu!r} => {got}, want {want}"
    q = Question(type=question_type, answer=None, score=5)
    # 模拟数据库中的 JSON 文本答案（create/import 会先 json.dumps）
    import json
    q.answer = json.dumps(std, ensure_ascii=False) if not isinstance(std, str) else json.dumps(std, ensure_ascii=False)
    res = GradingAgent._grade_objective(q, stu)
    assert res["is_correct"] is want, f"grading_agent {question_type} {std!r} -> {res}"


def main() -> None:
    # 判断题：中文 / 字母 / 布尔 / 选项 key 互认
    for std in ("正确", "对", "T", "true", "A"):
        for stu in ("A", "正确", "T", "true"):
            expect("judge", std, stu, True)
    assert answers_match("judge", "正确", "B") is False
    assert answers_match("judge", "错误", "B") is True
    assert answers_match("judge", "正确", "错误") is False

    # 多选题：JSON 数组 / 字符串 / 连续选项
    assert answers_match("multiple", ["A", "C"], ["A", "C"]) is True
    assert answers_match("multiple", "A,C", ["A", "C"]) is True
    assert answers_match("multiple", "A、C", ["A", "C"]) is True
    assert answers_match("multiple", "AC", ["A", "C"]) is True
    assert answers_match("multiple", ["A", "C"], ["A"]) is False
    assert answers_match("multiple", ["A", "C"], []) is False

    # 单选 / 填空：大小写、列表提交、空答案
    assert answers_match("single", "A", "a") is True
    assert answers_match("single", "A", ["A"]) is True
    assert answers_match("single", "A", "B") is False
    assert answers_match("blank", "4", "4") is True
    assert answers_match("blank", "4", " 4 ") is True
    assert answers_match("blank", "4", "") is False

    print("OK: answer normalization cases all passed")


if __name__ == "__main__":
    main()
