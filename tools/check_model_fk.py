#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""扫描「模型输出直写外键字段」的危险模式。

## 为什么需要它

真实事故（2026-10-26，v2.0.5 生产）：AI 智能出题保存时整批失败，
报 `(sqlite3.IntegrityError) FOREIGN KEY constraint failed`。

链路是：

    Question(knowledge_point_id=it.get("knowledge_point_id"), ...)   # it 是模型输出

模型给的 `knowledge_point_id` 是**它自己编的**（实测编出库里不存在的 101），
而 `edu_question.knowledge_point_id` 有外键约束
（`PRAGMA foreign_keys=ON`）→ INSERT 直接失败 → **整批题目全军覆没**。

而这个缺陷在 CI 里测不出来：CI 的 e2e 跑 `LLM_ENABLED=false`，
走的是规则引擎降级分支，根本不会执行模型输出那条路径；
等真机上有人点「AI 出题并保存」才炸，且只看到一句 500 堆栈。

同类风险还有 `grade_id`（非空外键）、`owner_id`（指向 sys_user）——
都可能被模型输出或缺省值写成不存在的 id。

## 判定规则

扫描范围：`backend/app/agents/*.py`、`backend/app/api/v1/*_ai.py`、
`backend/app/api/v1/agent.py`（只有这些地方会消费模型输出）。

1. **BLOCK**：ORM 构造函数的 `*_id=` 实参，其值是**模型输出字典的直接 `.get()`**
   —— 典型如 `knowledge_point_id=it.get("knowledge_point_id")`。
   必须先经校验函数（存在性 + 归属学科）再落库。
2. **WARN**：`*_id = <模型输出>.get(...)` 的中间赋值。
   允许后续调用校验函数后再使用（如 study_agent 先 `db.get` 再 `continue`），
   但静态上看不出来，需要人工确认。

两级按**语法形态**区分（本仓库约定：构造函数关键字实参写成 `k=v` 不带空格，
普通赋值写成 `k = v` 带空格）：

    knowledge_point_id=it.get("knowledge_point_id")   → BLOCK（构造参数，最高危）
    kp_id = item.get("knowledge_point_id") or 0        → WARN（中间赋值，需复核）

出现校验函数标识符（`_resolve_` / `_existing_kp` / `_suggest_kp` / `_validate` /
`_normalize_` / `_safe_id` / `_int_or_none` / `_check_kp`）即视为已校验。

## 用法

    python tools/check_model_fk.py

退出码：0 = 无 BLOCK，1 = 存在 BLOCK。
"""
import os
import re
import sys
from typing import List, Tuple

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 只扫「会消费模型输出」的地方，避免误伤普通业务代码
SCAN_DIRS = [
    os.path.join(ROOT, "backend", "app", "agents"),
    os.path.join(ROOT, "backend", "app", "api", "v1"),
]
SCAN_FILES_EXTRA = [
    os.path.join(ROOT, "backend", "app", "api", "v1", "agent.py"),
]
# 只在这些文件里判定「模型输出变量」
MODEL_OUT_NAMES = {
    "it", "item", "items", "raw", "raw_item", "obj", "parsed", "parsed_item",
    "entry", "rec", "row", "gen", "generated", "gen_item", "ai_item", "model_out",
}
# 出现这些标识符即认为该语句已做校验
VALIDATOR_MARKERS = (
    "_resolve_", "_existing_kp", "_suggest_kp", "_validate", "_normalize_",
    "_safe_id", "_int_or_none", "_check_kp",
)

# 构造参数形态：xxx_id=it.get(...)   （等号无空格 = 关键字实参写法）
RE_KWARG_FK = re.compile(
    r"\b([a-zA-Z_]\w*_id)=([a-zA-Z_]\w*)\.get\("
)
# 中间赋值形态：xxx_id = it.get(...)  （等号两侧有空格）
RE_ASSIGN_FK = re.compile(
    r"\b([a-zA-Z_]\w*_id)\s+=\s+([a-zA-Z_]\w*)\.get\("
)


def _is_model_out(name: str) -> bool:
    return name in MODEL_OUT_NAMES


def _has_validator(line: str) -> bool:
    return any(m in line for m in VALIDATOR_MARKERS)


def _iter_files():
    seen = set()
    for d in SCAN_DIRS:
        if not os.path.isdir(d):
            continue
        for name in sorted(os.listdir(d)):
            if not name.endswith(".py"):
                continue
            path = os.path.join(d, name)
            # api/v1 下只有 *_ai.py 与 agent.py 会消费模型输出
            if d.endswith(os.path.join("api", "v1")) and not (
                name.endswith("_ai.py") or name == "agent.py"
            ):
                continue
            if path in seen:
                continue
            seen.add(path)
            yield path
    for path in SCAN_FILES_EXTRA:
        if os.path.isfile(path) and path not in seen:
            seen.add(path)
            yield path


def scan() -> Tuple[List[Tuple[str, int, str]], List[Tuple[str, int, str]]]:
    blocks: List[Tuple[str, int, str]] = []
    warns: List[Tuple[str, int, str]] = []
    for path in _iter_files():
        with open(path, encoding="utf-8") as f:
            lines = f.readlines()
        for idx, raw in enumerate(lines, start=1):
            line = raw.rstrip("\n")
            if ".get(" not in line:
                continue
            m = RE_KWARG_FK.search(line)
            if m and _is_model_out(m.group(2)) and not _has_validator(line):
                blocks.append((path, idx, line.strip()))
                continue
            m2 = RE_ASSIGN_FK.search(line)
            if m2 and _is_model_out(m2.group(2)) and not _has_validator(line):
                warns.append((path, idx, line.strip()))
    return blocks, warns


def main() -> int:
    blocks, warns = scan()
    rel = lambda p: os.path.relpath(p, ROOT)  # noqa: E731

    if warns:
        print(f"[WARN] 模型输出赋值给 *_id（{len(warns)} 处，需人工确认是否已校验）：\n")
        for path, lineno, line in warns:
            print(f"  {rel(path)}:{lineno}")
            print(f"    {line[:110]}")
        print()

    if not blocks:
        print("[OK] 未发现「模型输出直写外键字段」（*_id=<模型输出>.get(...)）")
        return 0

    print(f"[FAIL] 模型输出直写外键字段（{len(blocks)} 处）：\n")
    for path, lineno, line in blocks:
        print(f"  {rel(path)}:{lineno}")
        print(f"    {line[:110]}")
        print()
    print("修复方式：")
    print("  1) 先校验再落库：模型给的 id 必须确认「存在 + 属于当前学科」，")
    print("     例如 backend/app/agents/question_agent.py 的 _resolve_kp_id()；")
    print("  2) 校验不通过时回退到请求指定的 id / 按名称匹配 / 置空，")
    print("     宁可让题目不挂知识点，也不能让整批题目因外键失败而全军覆没。")
    return 1


if __name__ == "__main__":
    sys.exit(main())
