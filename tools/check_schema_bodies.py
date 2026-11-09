#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""契约层守护：裸 `Dict[...] = Body(...)` 不得继续增长（P1-7）。

裸 Dict 让字段拼错静默生效、类型错误到 SQL 层才炸、OpenAPI 请求体显示
成 `{}`。存量几十处一次性替换风险过高，因此采用「锁住上限、逐步下降」
的策略：新增端点必须从 `app.schemas` 取 Pydantic 模型；每迁移一处，
把 BASELINE 同步减 1。这样契约层只会变好，不会再恶化。

P2-8 的修正（旧口径可绕过）：旧正则只认 `Dict[str, Any] = Body(`，
`Dict[str, str] = Body(...)`、`Dict[str, List[int]] = Body(...)` 完全在视野
之外 —— 换个内层类型就绕过去了。现在匹配任意 `Dict[<任意>] = Body(`，
且按**出现次数**计数（同一行两个也分别算）。

用法：python tools/check_schema_bodies.py    # 0=通过 1=新增裸 Dict
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API_DIR = os.path.join(ROOT, "backend", "app", "api", "v1")

# 按新口径（任意 Dict 内层类型 + 出现次数）重测后的基线。
BASELINE = 98
PATTERN = re.compile(r"Dict\s*\[[^\[\]]*\]\s*=\s*Body\s*\(")


def main() -> int:
    hits = []
    total = 0
    for root, _dirs, files in os.walk(API_DIR):
        for name in files:
            if not name.endswith(".py"):
                continue
            path = os.path.join(root, name)
            with open(path, encoding="utf-8") as fh:
                for lineno, line in enumerate(fh, 1):
                    found = PATTERN.findall(line)
                    if found:
                        total += len(found)
                        hits.append((os.path.relpath(path, ROOT), lineno, len(found)))
    if total > BASELINE:
        print(f"[FAIL] 裸 Dict Body = {total}，超过基线 {BASELINE}")
        for path, lineno, _n in hits[:8]:
            print(f"  - {path}:{lineno}")
        print("新端点请使用 app.schemas 中的 Pydantic 模型；")
        print("迁移存量后请把本脚本 BASELINE 同步减 1。")
        return 1
    print(f"[OK] 裸 Dict Body = {total}（基线 {BASELINE}，未增长）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
