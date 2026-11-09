# -*- coding: utf-8 -*-
"""题目选项的统一形状：`[{"key": "A", "text": "7"}]`。

为什么需要这个模块：`options` 是全站复用最多的 JSON 字段，写入侧（建题、
批量新增、AI 出题、导入、演示造数）与读取侧（答题页、试卷 Excel 导出、
错题导出、AI 组卷）各自解析，任何一处形状不一致都会在生产上炸成 500。
第三轮复审 P1-C 就是演示数据写成 `["A. 7", "B. 8"]` 导致两处导出 500、
学生端渲染成 `undefined. undefined`。

因此约定：
* **写入**：`normalize_options()` 先归一化再落库 —— 脏形状进不来；
* **读取**：同样先归一化再输出/渲染 —— 历史脏数据也炸不了。
两边都用同一个函数，形状只有一个真源。
"""
import json
from typing import Any, Dict, List

# 选项前缀后可能出现的分隔符：`A.` / `A．` / `A、` / `A)` / `A）`
_SEPARATORS = ".．、)）"


def _split_prefixed(text: Any, idx: int) -> Dict[str, str]:
    raw = str(text if text is not None else "").strip()
    if len(raw) >= 2 and raw[0].isalpha() and raw[1] in _SEPARATORS:
        key = raw[0].upper()
        rest = raw[2:].lstrip(" " + _SEPARATORS)
        return {"key": key, "text": rest}
    return {"key": chr(ord("A") + idx), "text": raw}


def normalize_options(raw: Any) -> List[Dict[str, str]]:
    """把任意历史形状归一化为 `[{"key","text"}]`。

    接受：
      * `None` / 空串 / 非法 JSON → `[]`
      * JSON 文本（库里存的就是这种）
      * `[{"key","text"}]`（标准）
      * `["A. 7", "B. 8"]`（旧导入模板 / 第三轮演示数据）
      * `{"A": "7", "B": "8"}`（AI 早期返回的映射形状）
    其它类型返回 `[]`，绝不抛异常 —— 展示链路不能因为一条脏数据整页崩。
    """
    if raw is None:
        return []
    if isinstance(raw, (bytes, bytearray)):
        try:
            raw = raw.decode("utf-8")
        except UnicodeDecodeError:
            return []
    if isinstance(raw, str):
        text = raw.strip()
        if not text:
            return []
        try:
            raw = json.loads(text)
        except (ValueError, TypeError):
            return []
    if isinstance(raw, dict):
        items = [
            {"key": str(k).strip().upper(), "text": "" if v is None else str(v).strip()}
            for k, v in raw.items()
        ]
    elif isinstance(raw, (list, tuple)):
        items = []
        for i, item in enumerate(raw):
            if isinstance(item, dict):
                key = item.get("key") or item.get("value")
                key = str(key).strip().upper() if key else chr(ord("A") + i)
                text = item.get("text")
                if text is None:
                    text = item.get("label") or item.get("content") or ""
                items.append({"key": key, "text": str(text).strip()})
            else:
                items.append(_split_prefixed(item, i))
    else:
        return []

    out, seen = [], set()
    for it in items:
        key = it["key"]
        if not key and not it["text"]:
            continue
        if key in seen:
            continue
        seen.add(key)
        out.append(it)
    return out


def options_match_key(options: Any, key: Any) -> bool:
    """该 key 是否确实是这道题的选项之一（判分前用它兜住脏数据）。"""
    target = str(key or "").strip().upper()
    return any(o["key"] == target for o in normalize_options(options))
