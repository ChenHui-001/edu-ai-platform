#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""胖路由守护：API 层直接 SQL 的数量不得继续增长（P2-1）。

业务编排、权限判断、SQL 组装全挤在 api/v1 路由文件里，
`paper_compose.py` 一个文件就 2500+ 行。一次性下沉 387 处 SQL 风险过高，
因此与契约层同一策略：**先锁住上限，再逐步下降**。每把一个内聚模块
抽到 services/，就把 BASELINE 同步减 1。

P2-8 的修正（旧口径可绕过）：
  * 按**出现次数**计数，不再按行：同一行写两个 `select(` 旧实现只算 1；
  * 补上 `db.query(` 这条 ORM 老写法（旧实现完全看不见）；
  * 补上 `execute(text(` 这条裸 SQL 写法。
扫描范围仍限定 `api/v1`：services 层本来就该写 SQL，把它算进来会让这个
指标失去意义（目标是"路由不写 SQL"，不是"全仓零 SQL"）。

用法：python tools/check_api_sql.py    # 0=通过 1=SQL 又长回 API 层
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API_DIR = os.path.join(ROOT, "backend", "app", "api", "v1")

# 按出现次数计（不再是行数），基线已按新口径重测。
# **棘轮语义**：BASELINE 既是上限也是当前实测值；实测下降时必须同步下调，
# 否则 CI 红（否则"下沉了几处、常量还停在老数字"，等于把额度还回去）。
BASELINE = 384
# 目的地：沉降到这个数算达标（services 层本来就该写 SQL，不必追到 0）。
TARGET = 300
PATTERN = re.compile(r"\bselect\s*\(|\bdb\.query\s*\(|\bexecute\s*\(\s*text\s*\(")


def main() -> int:
    total = 0
    for root, _dirs, files in os.walk(API_DIR):
        for name in files:
            if not name.endswith(".py"):
                continue
            with open(os.path.join(root, name), encoding="utf-8") as fh:
                for line in fh:
                    total += len(PATTERN.findall(line))
    if total > BASELINE:
        print(f"[FAIL] API 层直接 SQL = {total}，超过基线 {BASELINE}")
        print("新逻辑请放 services/；下沉存量后把本脚本 BASELINE 同步减 1。")
        return 1
    if total < BASELINE:
        print(f"[FAIL] API 层直接 SQL = {total}，低于基线 {BASELINE} —— 请同步收紧基线")
        print(f"       把 BASELINE 从 {BASELINE} 改成 {total} 后重跑。")
        return 1
    if total > TARGET:
        print(f"[OK] API 层直接 SQL = {total}（基线 {BASELINE}，未增长）；"
              f"距目标 {TARGET} 还差 {total - TARGET} 处")
    else:
        print(f"[OK] API 层直接 SQL = {total}，已达到目标 {TARGET}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
