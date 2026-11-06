#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""胖路由守护：API 层直接 SQL 的数量不得继续增长（P2-1）。

业务编排、权限判断、SQL 组装全挤在 api/v1 路由文件里，
`paper_compose.py` 一个文件就 2500+ 行。一次性下沉 387 处 SQL 风险过高，
因此与契约层同一策略：**先锁住上限，再逐步下降**。每把一个内聚模块
抽到 services/，就把 BASELINE 同步减 1。

用法：python tools/check_api_sql.py    # 0=通过 1=SQL 又长回 API 层
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API_DIR = os.path.join(ROOT, "backend", "app", "api", "v1")

# 抽出 services/ai_fill_batch.py 后的实测值（同步下调，防止倒退）。
BASELINE = 383
PATTERN = re.compile(r"\bselect\s*\(|db\.execute\s*\(\s*text")


def main() -> int:
    total = 0
    for root, _dirs, files in os.walk(API_DIR):
        for name in files:
            if not name.endswith(".py"):
                continue
            with open(os.path.join(root, name), encoding="utf-8") as fh:
                total += sum(1 for line in fh if PATTERN.search(line))
    if total > BASELINE:
        print(f"[FAIL] API 层直接 SQL = {total}，超过基线 {BASELINE}")
        print("新逻辑请放 services/；下沉存量后把本脚本 BASELINE 同步减 1。")
        return 1
    print(f"[OK] API 层直接 SQL = {total}（基线 {BASELINE}，未增长）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
