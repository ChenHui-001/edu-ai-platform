#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""契约层守护：裸 `Dict[str, Any] = Body(...)` 不得继续增长（P1-7）。

裸 Dict 让字段拼错静默生效、类型错误到 SQL 层才炸、OpenAPI 请求体显示
成 `{}`。存量 99 处一次性替换风险过高，因此采用「锁住上限、逐步下降」
的策略：新增端点必须从 `app.schemas` 取 Pydantic 模型；每迁移一处，
把 BASELINE 同步减 1。这样契约层只会变好，不会再恶化。

用法：python tools/check_schema_bodies.py    # 0=通过 1=新增裸 Dict
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API_DIR = os.path.join(ROOT, "backend", "app", "api", "v1")

# paper-composer 迁移到 schemas.agent.PaperComposerRequest 后的实测值。
BASELINE = 98
PATTERN = re.compile(r"Dict\s*\[\s*str\s*,\s*Any\s*\]\s*=\s*Body\s*\(")


def main() -> int:
    hits = []
    for root, _dirs, files in os.walk(API_DIR):
        for name in files:
            if not name.endswith(".py"):
                continue
            path = os.path.join(root, name)
            with open(path, encoding="utf-8") as fh:
                for lineno, line in enumerate(fh, 1):
                    if PATTERN.search(line):
                        hits.append((os.path.relpath(path, ROOT), lineno))
    if len(hits) > BASELINE:
        print(f"[FAIL] 裸 Dict Body = {len(hits)}，超过基线 {BASELINE}")
        for path, lineno in hits[:8]:
            print(f"  - {path}:{lineno}")
        print("新端点请使用 app.schemas 中的 Pydantic 模型；")
        print("迁移存量后请把本脚本 BASELINE 同步减 1。")
        return 1
    print(f"[OK] 裸 Dict Body = {len(hits)}（基线 {BASELINE}，未增长）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
